"""
E-ComSight — Reviews Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import csv
import io
from app.database import get_db, Review, Alert
from app.routers.auth import get_current_user, User
from app.services import nlp_service, alert_service
from app.config import settings

router = APIRouter(prefix="/reviews", tags=["reviews"])


# ─── Schemas ──────────────────────────────────────────────────────────────────
class ReviewCreate(BaseModel):
    comment: str
    rating_star: int = 0
    platform: str = "manual"
    product_name: str = ""


class ReviewUpdate(BaseModel):
    sentiment_label: Optional[str] = None
    aspect_label: Optional[str] = None
    urgency_label: Optional[str] = None
    is_labeled: Optional[bool] = None


class ReviewResponse(BaseModel):
    id: int
    platform: str = ""
    product_name: str = ""
    comment: str
    rating_star: int = 0
    sentiment_label: str = ""
    sentiment_score: float = 0.0
    sentiment_source: str = ""
    aspect_label: str = ""
    urgency_label: str = ""
    is_labeled: bool = False
    author_username: str = ""
    review_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Background task: analyze + alert ─────────────────────────────────────────
def analyze_and_alert(review_id: int, db_url: str, user_id: int):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Review, Alert, User

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    LocalSession = sessionmaker(bind=engine)
    db = LocalSession()

    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        if not review or not user:
            return

        # Analyze
        result = nlp_service.analyze_review(review.comment)
        review.sentiment_label = result["sentiment_label"]
        review.sentiment_score = result["sentiment_score"]
        review.sentiment_source = result["sentiment_source"]
        review.aspect_label = result["aspect_label"]
        review.urgency_label = result["urgency_label"]
        review.analyzed_at = datetime.utcnow()
        db.commit()

        # Check if should alert
        threshold_map = {"critical": ["critical"], "high": ["critical", "high"], "medium": ["critical", "high", "medium"]}
        trigger_urgencies = threshold_map.get(user.alert_threshold or "high", ["critical", "high"])

        if review.urgency_label in trigger_urgencies and review.sentiment_label == "negative":
            # Create alert
            alert = Alert(
                user_id=user_id,
                review_id=review_id,
                title=f"Phát hiện review tiêu cực: {review.product_name or 'Sản phẩm'}",
                message=f"Review trên {review.platform} có dấu hiệu '{review.urgency_label}' cần xử lý ngay.",
                urgency=review.urgency_label,
                product_name=review.product_name,
                platform=review.platform,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)

            # Send email
            if user.alert_enabled and user.alert_email:
                alert_service.send_alert_email(
                    to_email=user.alert_email,
                    alert_title=alert.title,
                    alert_message=alert.message,
                    urgency=alert.urgency,
                    review_comment=review.comment,
                    product_name=review.product_name,
                    platform=review.platform,
                )
                alert.is_email_sent = True
                db.commit()
    finally:
        db.close()


# ─── Routes ───────────────────────────────────────────────────────────────────
@router.get("/", response_model=dict)
def list_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    platform: Optional[str] = None,
    sentiment: Optional[str] = None,
    aspect: Optional[str] = None,
    urgency: Optional[str] = None,
    search: Optional[str] = None,
    product_name: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_stars: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Review).filter(Review.user_id == current_user.id)

    if platform:
        query = query.filter(Review.platform == platform)
    if sentiment:
        query = query.filter(Review.sentiment_label == sentiment)
    if aspect:
        query = query.filter(Review.aspect_label == aspect)
    if urgency:
        query = query.filter(Review.urgency_label == urgency)
    if search:
        query = query.filter(Review.comment.ilike(f"%{search}%"))
    if product_name:
        query = query.filter(Review.product_name.ilike(f"%{product_name}%"))
    if min_stars:
        query = query.filter(Review.rating_star >= min_stars)
    if max_stars:
        query = query.filter(Review.rating_star <= max_stars)
    if date_from:
        query = query.filter(Review.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Review.created_at <= datetime.combine(date_to, datetime.max.time()))

    total = query.count()
    reviews = query.order_by(desc(Review.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": [ReviewResponse.from_orm(r) for r in reviews]
    }


@router.post("/", response_model=ReviewResponse)
def create_review(
    req: ReviewCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = Review(
        user_id=current_user.id,
        comment=req.comment,
        rating_star=req.rating_star,
        platform=req.platform,
        product_name=req.product_name,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # Analyze in background
    background_tasks.add_task(
        analyze_and_alert, review.id, settings.DATABASE_URL, current_user.id
    )

    return ReviewResponse.from_orm(review)


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    req: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(
        Review.id == review_id, Review.user_id == current_user.id
    ).first()
    if not review:
        raise HTTPException(404, "Review không tìm thấy")

    if req.sentiment_label is not None:
        review.sentiment_label = req.sentiment_label
        review.sentiment_source = "manual"
    if req.aspect_label is not None:
        review.aspect_label = req.aspect_label
    if req.urgency_label is not None:
        review.urgency_label = req.urgency_label
    if req.is_labeled is not None:
        review.is_labeled = req.is_labeled

    db.commit()
    db.refresh(review)
    return ReviewResponse.from_orm(review)


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(
        Review.id == review_id, Review.user_id == current_user.id
    ).first()
    if not review:
        raise HTTPException(404, "Review không tìm thấy")
    db.delete(review)
    db.commit()
    return {"message": "Đã xóa"}


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import reviews từ CSV file"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Chỉ chấp nhận file CSV")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0

    for row in reader:
        comment = row.get("comment", "") or row.get("Nội dung review", "")
        if not comment or len(comment.strip()) < 5:
            skipped += 1
            continue

        review = Review(
            user_id=current_user.id,
            comment=comment.strip(),
            rating_star=int(float(row.get("rating_star", row.get("Số sao", 0)) or 0)),
            platform=row.get("platform", row.get("Nền tảng", "import")).lower(),
            product_name=row.get("product_name", row.get("Tên sản phẩm", "")),
            sentiment_label=row.get("sentiment_label", ""),
            aspect_label=row.get("aspect_label", ""),
            urgency_label=row.get("urgency_label", ""),
            is_labeled=bool(row.get("sentiment_label", "")),
        )
        db.add(review)
        created += 1

        if created % 100 == 0:
            db.commit()

    db.commit()

    # Analyze unlabeled reviews in background
    unlabeled = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.sentiment_label == ""
    ).all()

    for r in unlabeled:
        background_tasks.add_task(
            analyze_and_alert, r.id, settings.DATABASE_URL, current_user.id
        )

    return {
        "message": f"Import thành công {created} reviews ({skipped} bỏ qua)",
        "created": created,
        "skipped": skipped,
        "analyzing": len(unlabeled),
    }

"""
E-ComSight — Export & Analysis Routers
"""
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import io
from app.database import get_db, Review
from app.routers.auth import get_current_user, User
from app.services import export_service, nlp_service

export_router = APIRouter(prefix="/export", tags=["export"])
analysis_router = APIRouter(prefix="/analysis", tags=["analysis"])


# ─── Export Routes ─────────────────────────────────────────────────────────────
def _get_reviews_for_export(db: Session, user_id: int, days: int = 30, platform: str = None):
    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(Review).filter(
        Review.user_id == user_id,
        Review.created_at >= since
    )
    if platform:
        query = query.filter(Review.platform == platform)
    return query.order_by(desc(Review.created_at)).all()


@export_router.get("/csv")
def export_csv(
    days: int = Query(30),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reviews = _get_reviews_for_export(db, current_user.id, days, platform)
    if not reviews:
        raise HTTPException(404, "Không có dữ liệu để xuất")

    content = export_service.export_csv(reviews)
    filename = f"ecomsight_reviews_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    return StreamingResponse(
        io.BytesIO(content),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@export_router.get("/excel")
def export_excel(
    days: int = Query(30),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reviews = _get_reviews_for_export(db, current_user.id, days, platform)
    if not reviews:
        raise HTTPException(404, "Không có dữ liệu để xuất")

    content = export_service.export_excel(reviews)
    filename = f"ecomsight_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@export_router.get("/pdf")
def export_pdf(
    days: int = Query(30),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reviews = _get_reviews_for_export(db, current_user.id, days, platform)
    if not reviews:
        raise HTTPException(404, "Không có dữ liệu để xuất")

    content = export_service.export_pdf(reviews, shop_name=current_user.shop_name or "E-ComSight")
    filename = f"ecomsight_bao_cao_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ─── Live Analysis Routes ──────────────────────────────────────────────────────
class TextAnalysisRequest(BaseModel):
    text: str
    platform: str = "manual"
    product_name: str = ""


class URLAnalysisRequest(BaseModel):
    url: str


@analysis_router.post("/text")
def analyze_text(
    req: TextAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Phân tích text review trực tiếp"""
    if len(req.text.strip()) < 3:
        raise HTTPException(400, "Text quá ngắn")

    result = nlp_service.analyze_review(req.text, use_phobert=True)

    # Optionally save to DB
    review = Review(
        user_id=current_user.id,
        comment=req.text,
        platform=req.platform,
        product_name=req.product_name,
        sentiment_label=result["sentiment_label"],
        sentiment_score=result["sentiment_score"],
        sentiment_source=result["sentiment_source"],
        aspect_label=result["aspect_label"],
        urgency_label=result["urgency_label"],
        analyzed_at=datetime.utcnow(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # Check if need to alert
    from app.routers.reviews import analyze_and_alert
    if result["urgency_label"] in ("critical", "high"):
        background_tasks.add_task(
            analyze_and_alert, review.id, db.get_bind().url.__str__(), current_user.id
        )

    # Explanation
    sentiment_label = result["sentiment_label"]
    explanations = {
        "positive": "Review có nhiều từ ngữ tích cực, khách hàng hài lòng với sản phẩm/dịch vụ.",
        "negative": "Review có dấu hiệu tiêu cực, cần theo dõi và phản hồi sớm.",
        "neutral": "Review trung lập, không thể hiện cảm xúc rõ ràng.",
    }

    return {
        **result,
        "review_id": review.id,
        "explanation": explanations.get(sentiment_label, ""),
        "sentiment_vi": {"positive": "Tích cực", "neutral": "Trung lập", "negative": "Tiêu cực"}.get(sentiment_label, ""),
        "aspect_vi": {"product": "Chất lượng SP", "shipping": "Vận chuyển", "service": "Dịch vụ", "price": "Giá cả"}.get(result["aspect_label"], ""),
        "urgency_vi": {"critical": "Nghiêm trọng", "high": "Cao", "medium": "Trung bình", "low": "Thấp"}.get(result["urgency_label"], ""),
    }


@analysis_router.post("/url")
async def analyze_url(
    req: URLAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Phân tích URL sản phẩm Shopee/TikTok"""
    url = req.url.strip()
    if not url.startswith("http"):
        raise HTTPException(400, "URL không hợp lệ")

    if "shopee.vn" not in url and "tiktok.com" not in url and "tiktokshop" not in url:
        raise HTTPException(400, "Chỉ hỗ trợ URL Shopee và TikTok Shop")

    result = nlp_service.analyze_url(url)

    if not result["reviews"]:
        return {
            "platform": result["platform"],
            "status": "no_reviews",
            "message": "Không lấy được reviews từ URL này. Vui lòng nhập text thủ công.",
            "reviews": [],
            "summary": {}
        }

    # Save reviews to DB
    saved = 0
    for r_data in result["reviews"][:50]:  # Max 50
        review = Review(
            user_id=current_user.id,
            comment=r_data["comment"],
            platform=result["platform"],
            rating_star=r_data.get("rating_star", 0),
            sentiment_label=r_data.get("sentiment_label", ""),
            sentiment_score=r_data.get("sentiment_score", 0),
            aspect_label=r_data.get("aspect_label", ""),
            urgency_label=r_data.get("urgency_label", ""),
            analyzed_at=datetime.utcnow(),
        )
        db.add(review)
        saved += 1

    db.commit()

    return {
        **result,
        "saved_to_db": saved,
        "status": "success"
    }

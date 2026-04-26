"""
E-ComSight — Analytics Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta, date
from app.database import get_db, Review
from app.routers.auth import get_current_user, User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def get_overview(
    days: int = Query(30, ge=1, le=365),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """KPI cards: tổng reviews, % tích cực, cảnh báo"""
    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.created_at >= since
    )
    if platform:
        query = query.filter(Review.platform == platform)

    all_reviews = query.all()
    total = len(all_reviews)

    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    urgency_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    platform_counts = {}
    avg_score = 0.0
    avg_stars = 0.0

    for r in all_reviews:
        if r.sentiment_label in sentiment_counts:
            sentiment_counts[r.sentiment_label] += 1
        if r.urgency_label in urgency_counts:
            urgency_counts[r.urgency_label] += 1
        p = r.platform or "unknown"
        platform_counts[p] = platform_counts.get(p, 0) + 1
        avg_score += r.sentiment_score or 0
        avg_stars += r.rating_star or 0

    pos_rate = round(sentiment_counts["positive"] / total * 100, 1) if total else 0
    alerts_total = urgency_counts["critical"] + urgency_counts["high"]

    return {
        "total_reviews": total,
        "positive_rate": pos_rate,
        "negative_count": sentiment_counts["negative"],
        "alerts_count": alerts_total,
        "sentiment_distribution": sentiment_counts,
        "urgency_distribution": urgency_counts,
        "platform_distribution": platform_counts,
        "avg_confidence": round(avg_score / total, 3) if total else 0,
        "avg_stars": round(avg_stars / total, 2) if total else 0,
        "period_days": days,
    }


@router.get("/trend")
def get_trend(
    days: int = Query(30, ge=7, le=180),
    granularity: str = Query("day", regex="^(day|week)$"),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trend sentiment theo ngày/tuần"""
    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.created_at >= since
    )
    if platform:
        query = query.filter(Review.platform == platform)

    reviews = query.order_by(Review.created_at).all()

    # Group by date
    trend = {}
    for r in reviews:
        if granularity == "day":
            key = r.created_at.strftime("%Y-%m-%d")
        else:
            # Week number
            key = r.created_at.strftime("%Y-W%W")

        if key not in trend:
            trend[key] = {"date": key, "positive": 0, "neutral": 0, "negative": 0, "total": 0}

        sentiment = r.sentiment_label or "neutral"
        if sentiment in trend[key]:
            trend[key][sentiment] += 1
        trend[key]["total"] += 1

    result = sorted(trend.values(), key=lambda x: x["date"])
    return {"data": result, "granularity": granularity}


@router.get("/aspects")
def get_aspects(
    days: int = Query(30),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Phân tích sentiment theo từng aspect"""
    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.created_at >= since
    )
    if platform:
        query = query.filter(Review.platform == platform)

    reviews = query.all()
    aspects = {}

    for r in reviews:
        aspect = r.aspect_label or "product"
        if aspect not in aspects:
            aspects[aspect] = {"aspect": aspect, "positive": 0, "neutral": 0, "negative": 0, "total": 0}
        sentiment = r.sentiment_label or "neutral"
        if sentiment in aspects[aspect]:
            aspects[aspect][sentiment] += 1
        aspects[aspect]["total"] += 1

    # Thêm satisfaction score
    for aspect_data in aspects.values():
        total = aspect_data["total"]
        if total > 0:
            aspect_data["satisfaction"] = round(
                (aspect_data["positive"] - aspect_data["negative"]) / total * 100, 1
            )

    aspect_order = ["product", "shipping", "service", "price"]
    result = sorted(aspects.values(), key=lambda x: aspect_order.index(x["aspect"]) if x["aspect"] in aspect_order else 99)

    return {"data": result}


@router.get("/top-products")
def get_top_products(
    days: int = Query(30),
    limit: int = Query(10, le=50),
    sort_by: str = Query("negative", regex="^(negative|positive|total)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Top sản phẩm có nhiều review tích cực/tiêu cực"""
    since = datetime.utcnow() - timedelta(days=days)
    reviews = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.created_at >= since,
        Review.product_name != None,
        Review.product_name != ""
    ).all()

    products = {}
    for r in reviews:
        name = r.product_name or "Không rõ"
        if name not in products:
            products[name] = {"name": name, "positive": 0, "neutral": 0, "negative": 0, "total": 0}
        sentiment = r.sentiment_label or "neutral"
        if sentiment in products[name]:
            products[name][sentiment] += 1
        products[name]["total"] += 1

    result = sorted(products.values(), key=lambda x: x.get(sort_by, 0), reverse=True)[:limit]
    return {"data": result, "sort_by": sort_by}


@router.get("/keywords")
def get_keywords(
    days: int = Query(30),
    sentiment: Optional[str] = None,
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Top keywords xuất hiện nhiều nhất"""
    from collections import Counter
    import re

    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.created_at >= since
    )
    if sentiment:
        query = query.filter(Review.sentiment_label == sentiment)

    reviews = query.all()

    # Stopwords tiếng Việt
    stopwords = {
        "và", "của", "là", "được", "có", "cho", "với", "trong", "này", "đã",
        "không", "tôi", "mình", "thì", "một", "rất", "còn", "như", "đến",
        "từ", "về", "các", "những", "nên", "hay", "hoặc", "nhưng", "vì",
        "khi", "vẫn", "cũng", "sẽ", "ra", "lại", "đó", "thấy", "mua",
        "hàng", "sản", "phẩm", "shop", "đơn", "lần",
    }

    word_counts = Counter()
    for r in reviews:
        if not r.comment:
            continue
        words = re.findall(r"\b[\w]+\b", r.comment.lower())
        for w in words:
            if len(w) > 2 and w not in stopwords:
                word_counts[w] += 1

    top_words = [{"word": w, "count": c} for w, c in word_counts.most_common(limit)]
    return {"data": top_words, "sentiment": sentiment}

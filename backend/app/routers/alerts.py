"""
E-ComSight — Alerts Router
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db, Alert
from app.routers.auth import get_current_user, User

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/")
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    urgency: Optional[str] = None,
    is_read: Optional[bool] = None,
    days: int = Query(30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.created_at >= since
    )
    if urgency:
        query = query.filter(Alert.urgency == urgency)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)

    total = query.count()
    alerts = query.order_by(desc(Alert.created_at)).offset((page-1)*page_size).limit(page_size).all()

    return {
        "total": total,
        "unread": db.query(Alert).filter(Alert.user_id == current_user.id, Alert.is_read == False).count(),
        "items": [
            {
                "id": a.id,
                "title": a.title,
                "message": a.message,
                "urgency": a.urgency,
                "product_name": a.product_name,
                "platform": a.platform,
                "is_read": a.is_read,
                "is_email_sent": a.is_email_sent,
                "created_at": a.created_at,
                "review_id": a.review_id,
            }
            for a in alerts
        ]
    }


@router.put("/{alert_id}/read")
def mark_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(404, "Không tìm thấy cảnh báo")
    alert.is_read = True
    db.commit()
    return {"message": "Đã đánh dấu đã đọc"}


@router.put("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "Đã đánh dấu tất cả là đã đọc"}


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(404, "Không tìm thấy")
    db.delete(alert)
    db.commit()
    return {"message": "Đã xóa"}

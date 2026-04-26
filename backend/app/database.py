"""
E-ComSight — Database Models (SQLAlchemy)
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    shop_name = Column(String(100))  # Tên cửa hàng
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Email alert settings
    alert_email = Column(String(100))
    alert_enabled = Column(Boolean, default=True)
    alert_threshold = Column(String(20), default="high")  # critical, high, medium

    reviews = relationship("Review", back_populates="owner")
    alerts = relationship("Alert", back_populates="owner")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Nguồn dữ liệu
    platform = Column(String(20), index=True)  # shopee, tiktok
    product_name = Column(String(255), index=True)
    shopid = Column(String(50))
    itemid = Column(String(50))

    # Nội dung
    comment = Column(Text, nullable=False)
    rating_star = Column(Integer, default=0)  # 1-5
    like_count = Column(Integer, default=0)
    has_media = Column(Boolean, default=False)
    author_username = Column(String(100))
    review_date = Column(DateTime)

    # Sentiment Analysis
    sentiment_label = Column(String(20), index=True)  # positive, neutral, negative
    sentiment_score = Column(Float, default=0.0)  # confidence 0-1
    sentiment_source = Column(String(20), default="model")  # model, rule, manual

    # Aspect Analysis
    aspect_label = Column(String(30), index=True)  # product, shipping, service, price
    urgency_label = Column(String(20), index=True)  # critical, high, medium, low

    # Metadata
    is_labeled = Column(Boolean, default=False)  # user đã gán nhãn thủ công
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime)

    owner = relationship("User", back_populates="reviews")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=True)

    # Nội dung cảnh báo
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    urgency = Column(String(20), default="medium")  # critical, high, medium, low
    alert_type = Column(String(30))  # fake_product, skin_reaction, late_delivery, etc.

    # Keywords trigger
    trigger_keywords = Column(String(500))  # JSON list
    product_name = Column(String(255))
    platform = Column(String(20))

    # Trạng thái
    is_read = Column(Boolean, default=False)
    is_email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="alerts")


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    job_type = Column(String(20))  # url, keyword
    input_url = Column(String(500))
    platform = Column(String(20))
    status = Column(String(20), default="pending")  # pending, running, done, failed
    total_reviews = Column(Integer, default=0)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class TrackedProduct(Base):
    __tablename__ = "tracked_products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    platform = Column(String(20), index=True)  # shopee, tiktok
    shopid = Column(String(50))
    itemid = Column(String(50))
    name = Column(String(255))
    
    # scheduler fields
    priority = Column(String(20), default="normal") # hot, normal
    last_review_ctime = Column(Integer, default=0) # timestamp để crawl incremental
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_crawled_at = Column(DateTime)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)

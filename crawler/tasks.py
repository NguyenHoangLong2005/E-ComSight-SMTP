import asyncio
import logging
from celery_app import celery_app
from playwright.async_api import async_playwright
import redis
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, TrackedProduct, Review

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kết nối Redis để cache realtime
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# ===== SCHEDULER TASKS =====
@celery_app.task
def schedule_hot_products():
    db: Session = SessionLocal()
    products = db.query(TrackedProduct).filter(
        TrackedProduct.is_active == True,
        TrackedProduct.priority == "hot"
    ).all()
    for p in products:
        crawl_product_shopee.delay(p.id)
    db.close()
    logger.info(f"Đã lập lịch {len(products)} sản phẩm HOT.")

@celery_app.task
def schedule_normal_products():
    db: Session = SessionLocal()
    products = db.query(TrackedProduct).filter(
        TrackedProduct.is_active == True,
        TrackedProduct.priority == "normal"
    ).all()
    for p in products:
        crawl_product_shopee.delay(p.id)
    db.close()
    logger.info(f"Đã lập lịch {len(products)} sản phẩm NORMAL.")

# ===== WORKER TASKS =====
@celery_app.task
def crawl_product_shopee(tracked_product_id: int):
    """Worker job dùng Playwright để crawl"""
    # Celery tasks mặc định chạy đồng bộ (sync), để dùng Playwright async ta phải bọc lại
    asyncio.run(_crawl_shopee_async(tracked_product_id))

async def _crawl_shopee_async(product_id: int):
    db: Session = SessionLocal()
    product = db.query(TrackedProduct).filter(TrackedProduct.id == product_id).first()
    if not product:
        db.close()
        return

    logger.info(f"Bắt đầu crawl sản phẩm: {product.name}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Vượt tường bảo mật ban đầu
        await page.goto("https://shopee.vn/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        offset = 0
        limit = 50
        max_ctime = product.last_review_ctime # Lưu ctime lớn nhất trong lần chạy này
        stop_crawling = False
        
        new_reviews_count = 0

        while not stop_crawling:
            api_url = f"https://shopee.vn/api/v2/item/get_ratings?itemid={product.itemid}&shopid={product.shopid}&offset={offset}&limit={limit}&type=0&language_filter=vi"
            
            resp = await page.request.get(api_url)
            if not resp.ok:
                logger.warning(f"Lỗi API Shopee: {resp.status}")
                break
                
            data = await resp.json()
            ratings = data.get("data", {}).get("ratings", [])
            
            if not ratings:
                break
                
            for r in ratings:
                ctime = r.get("ctime", 0)
                # Kỹ thuật Incremental Crawling: Chỉ lấy review mới hơn ctime đã lưu
                if ctime <= product.last_review_ctime:
                    stop_crawling = True
                    break
                    
                if ctime > max_ctime:
                    max_ctime = ctime
                    
                comment = r.get("comment", "").strip()
                if len(comment.split()) < 3:
                    continue
                    
                # Gọi Model NLP gán nhãn ở đây (giả lập)
                sentiment_label = "NEUTRAL" # Chỗ này tích hợp sau với mô hình NLP
                
                new_review = Review(
                    platform="shopee",
                    product_name=product.name,
                    shopid=product.shopid,
                    itemid=product.itemid,
                    comment=comment,
                    rating_star=r.get("rating_star", 0),
                    review_date=datetime.fromtimestamp(ctime),
                    sentiment_label=sentiment_label,
                    author_username=r.get("author_username", "")
                )
                db.add(new_review)
                new_reviews_count += 1
                
                # Push vào Redis để "fake realtime" trên giao diện UI
                try:
                    redis_client.lpush("realtime_reviews", json.dumps({
                        "product_name": product.name,
                        "comment": comment,
                        "rating_star": r.get("rating_star", 0),
                        "sentiment": sentiment_label,
                        "time": str(new_review.review_date)
                    }))
                    redis_client.ltrim("realtime_reviews", 0, 99) # Giữ 100 review mới nhất
                except Exception as e:
                    pass
            
            if stop_crawling:
                break
                
            offset += limit
            await page.wait_for_timeout(2000)

        # Cập nhật thông tin tracking sau khi crawl xong
        if max_ctime > product.last_review_ctime:
            product.last_review_ctime = max_ctime
            
        product.last_crawled_at = datetime.utcnow()
        db.commit()
        db.close()
        await browser.close()
        
    logger.info(f"✅ Crawl xong {product.name} | Cập nhật: {new_reviews_count} review mới.")

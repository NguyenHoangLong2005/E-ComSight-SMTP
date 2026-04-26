"""
E-ComSight — Shopee Crawler
Thu thập reviews mỹ phẩm từ Shopee Vietnam
Output: data/shopee_reviews_raw.csv
"""

import requests
import pandas as pd
import time
import random
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("crawler.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "shopee_reviews_raw.csv"
TARGET_REVIEWS = 5000

# Shopee API headers (browser-like)
HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://shopee.vn/",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": "",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "vi-VN,vi;q=0.9",
        "Referer": "https://shopee.vn/",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "application/json",
        "Accept-Language": "vi-VN,vi;q=0.9",
        "Referer": "https://shopee.vn/",
    }
]

# Các cửa hàng mỹ phẩm chính hãng trên Shopee (shopid, itemid)
COSMETIC_PRODUCTS = [
    # CeraVe Official Store
    {"shopid": 8783579, "itemid": 17069001025, "name": "CeraVe Hydrating Cleanser"},
    {"shopid": 8783579, "itemid": 12345678901, "name": "CeraVe Moisturizing Cream"},
    # La Roche-Posay
    {"shopid": 9876543, "itemid": 23456789012, "name": "La Roche Posay Effaclar"},
    # Innisfree
    {"shopid": 3456789, "itemid": 34567890123, "name": "Innisfree Green Tea Serum"},
    # Some Hanbok
    {"shopid": 12345678, "itemid": 45678901234, "name": "Some By Mi AHA BHA"},
    # Generic search-based
]

# Shopee search endpoints
SHOPEE_SEARCH_URL = "https://shopee.vn/api/v4/search/search_items"
SHOPEE_RATINGS_URL = "https://shopee.vn/api/v2/item/get_ratings"
SHOPEE_ITEM_URL = "https://shopee.vn/api/v4/item/get"


def get_random_headers():
    return random.choice(HEADERS_POOL)


def random_delay(min_sec=1.5, max_sec=4.0):
    time.sleep(random.uniform(min_sec, max_sec))


def search_cosmetic_items(keyword: str, limit: int = 60) -> list[dict]:
    """Tìm kiếm sản phẩm mỹ phẩm trên Shopee"""
    items = []
    try:
        params = {
            "by": "relevancy",
            "keyword": keyword,
            "limit": limit,
            "newest": 0,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2
        }
        resp = requests.get(
            SHOPEE_SEARCH_URL,
            params=params,
            headers=get_random_headers(),
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            raw_items = data.get("items", []) or []
            for item in raw_items:
                item_basic = item.get("item_basic", {})
                if item_basic:
                    items.append({
                        "shopid": item_basic.get("shopid"),
                        "itemid": item_basic.get("itemid"),
                        "name": item_basic.get("name", ""),
                        "rating_star": item_basic.get("item_rating", {}).get("rating_star", 0),
                        "total_sold": item_basic.get("sold", 0),
                    })
            logger.info(f"Tìm thấy {len(items)} sản phẩm cho từ khóa: '{keyword}'")
        else:
            logger.warning(f"Search failed: {resp.status_code}")
    except Exception as e:
        logger.error(f"Search error: {e}")
    return items


def fetch_reviews_for_item(shopid: int, itemid: int, product_name: str = "") -> list[dict]:
    """Lấy tất cả reviews của một sản phẩm"""
    reviews = []
    offset = 0
    limit = 50
    max_pages = 10  # Giới hạn 500 reviews/sản phẩm

    while offset < max_pages * limit:
        try:
            params = {
                "itemid": itemid,
                "shopid": shopid,
                "limit": limit,
                "offset": offset,
                "type": 0,  # 0 = all ratings
                "language_filter": "vi",
            }
            resp = requests.get(
                SHOPEE_RATINGS_URL,
                params=params,
                headers=get_random_headers(),
                timeout=15
            )

            if resp.status_code != 200:
                logger.warning(f"Reviews fetch {resp.status_code} for item {itemid}")
                break

            data = resp.json()
            if data.get("error"):
                logger.warning(f"API error for item {itemid}: {data.get('error_msg')}")
                break

            ratings = data.get("data", {}).get("ratings", []) or []
            if not ratings:
                break

            for r in ratings:
                comment = r.get("comment", "").strip()
                if not comment or len(comment.split()) < 3:
                    continue  # Bỏ review quá ngắn

                review = {
                    "platform": "shopee",
                    "product_name": product_name,
                    "shopid": shopid,
                    "itemid": itemid,
                    "rating_star": r.get("rating_star", 0),
                    "comment": comment,
                    "like_count": r.get("like_count", 0),
                    "ctime": datetime.fromtimestamp(r.get("ctime", 0)).strftime("%Y-%m-%d %H:%M:%S") if r.get("ctime") else "",
                    "author_username": r.get("author_username", ""),
                    "has_media": len(r.get("images", []) or []) > 0,
                    "tags": json.dumps(r.get("tags", []) or [], ensure_ascii=False),
                    # Label sẽ do user tự gán
                    "sentiment_label": "",
                    "aspect_label": "",
                    "urgency_label": "",
                }
                reviews.append(review)

            logger.info(f"  Item {itemid} | offset {offset} → +{len(ratings)} reviews (tổng: {len(reviews)})")
            offset += limit

            if len(ratings) < limit:
                break  # Hết trang

            random_delay(1.5, 3.5)

        except requests.exceptions.ConnectionError:
            logger.error("Connection error — đợi 10s...")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Error fetching reviews: {e}")
            break

    return reviews


def crawl_all(keywords: list[str] = None):
    """Main crawler function"""
    if keywords is None:
        keywords = [
            "sữa rửa mặt mỹ phẩm",
            "kem dưỡng ẩm mặt",
            "serum vitamin c mặt",
            "kem chống nắng mỹ phẩm",
            "toner nước hoa hồng",
            "mặt nạ dưỡng da",
            "kem trị mụn mặt",
            "essence serum dưỡng",
        ]

    all_reviews = []
    all_products = []

    logger.info("=" * 60)
    logger.info("E-ComSight Shopee Crawler — Bắt đầu")
    logger.info(f"Mục tiêu: {TARGET_REVIEWS} reviews")
    logger.info("=" * 60)

    # Bước 1: Tìm kiếm sản phẩm
    for keyword in keywords:
        if len(all_products) >= 80:
            break
        items = search_cosmetic_items(keyword, limit=40)
        # Lọc sản phẩm có nhiều lượt bán (chắc có nhiều reviews)
        items = [i for i in items if i.get("total_sold", 0) > 100]
        all_products.extend(items)
        random_delay(2, 5)

    # Deduplicate products
    seen_ids = set()
    unique_products = []
    for p in all_products:
        key = (p["shopid"], p["itemid"])
        if key not in seen_ids and p["shopid"] and p["itemid"]:
            seen_ids.add(key)
            unique_products.append(p)

    logger.info(f"Tổng sản phẩm unique: {len(unique_products)}")

    # Bước 2: Lấy reviews từng sản phẩm
    for i, product in enumerate(unique_products):
        if len(all_reviews) >= TARGET_REVIEWS:
            logger.info(f"Đã đạt mục tiêu {TARGET_REVIEWS} reviews!")
            break

        logger.info(f"\n[{i+1}/{len(unique_products)}] {product['name'][:50]}")
        reviews = fetch_reviews_for_item(
            shopid=product["shopid"],
            itemid=product["itemid"],
            product_name=product["name"]
        )
        all_reviews.extend(reviews)
        logger.info(f"→ Tổng tích lũy: {len(all_reviews)} reviews")

        # Save checkpoint mỗi 500 reviews
        if len(all_reviews) % 500 < 50:
            _save_checkpoint(all_reviews)

        random_delay(3, 7)

    # Bước 3: Lưu kết quả
    _save_final(all_reviews)
    return all_reviews


def _save_checkpoint(reviews: list):
    df = pd.DataFrame(reviews)
    checkpoint_file = OUTPUT_DIR / f"shopee_checkpoint_{len(reviews)}.csv"
    df.to_csv(checkpoint_file, index=False, encoding="utf-8-sig")
    logger.info(f"💾 Checkpoint: {len(reviews)} reviews → {checkpoint_file}")


def _save_final(reviews: list):
    if not reviews:
        logger.warning("Không có reviews để lưu!")
        return

    df = pd.DataFrame(reviews)
    # Bỏ duplicate comments
    df.drop_duplicates(subset=["comment"], inplace=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    logger.info(f"\n✅ Hoàn thành! {len(df)} reviews → {OUTPUT_FILE}")
    logger.info(f"Phân phối sao: {df['rating_star'].value_counts().to_dict()}")


if __name__ == "__main__":
    crawl_all()

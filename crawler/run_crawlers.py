"""
E-ComSight — Main Crawler Runner
Chạy đồng thời cả Shopee + TikTok Shop
Merge output thành file duy nhất: data/all_reviews_raw.csv
"""
import sys
import threading
import pandas as pd
from pathlib import Path

# Run crawlers
def run_shopee():
    print("\n[SHOPEE] Bắt đầu crawl...")
    from shopee_crawler import crawl_all as shopee_crawl
    try:
        shopee_crawl()
    except Exception as e:
        print(f"[SHOPEE] Lỗi: {e}")

def run_tiktok():
    print("\n[TIKTOK] Bắt đầu crawl...")
    from tiktok_crawler import crawl_all as tiktok_crawl
    try:
        tiktok_crawl()
    except Exception as e:
        print(f"[TIKTOK] Lỗi: {e}")

def merge_results():
    data_dir = Path("data")
    dfs = []

    shopee_file = data_dir / "shopee_reviews_raw.csv"
    tiktok_file = data_dir / "tiktok_reviews_raw.csv"

    if shopee_file.exists():
        df_s = pd.read_csv(shopee_file, encoding="utf-8-sig")
        dfs.append(df_s)
        print(f"✅ Shopee: {len(df_s)} reviews")

    if tiktok_file.exists():
        df_t = pd.read_csv(tiktok_file, encoding="utf-8-sig")
        dfs.append(df_t)
        print(f"✅ TikTok: {len(df_t)} reviews")

    if dfs:
        df_all = pd.concat(dfs, ignore_index=True)
        df_all.drop_duplicates(subset=["comment"], inplace=True)
        output = data_dir / "all_reviews_raw.csv"
        df_all.to_csv(output, index=False, encoding="utf-8-sig")
        print(f"\n🎯 Tổng hợp: {len(df_all)} reviews → {output}")
        print(f"Phân phối sao:")
        print(df_all["rating_star"].value_counts().sort_index())
        print(f"\nPhân phối platform:")
        print(df_all["platform"].value_counts())
    else:
        print("❌ Không có dữ liệu để merge")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "shopee":
        run_shopee()
    elif mode == "tiktok":
        run_tiktok()
    elif mode == "merge":
        merge_results()
    else:
        # Chạy song song
        t1 = threading.Thread(target=run_shopee)
        t2 = threading.Thread(target=run_tiktok)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print("\n--- Đang merge kết quả ---")
        merge_results()

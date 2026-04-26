import os
from celery import Celery
from celery.schedules import crontab

# Đảm bảo PYTHONPATH trỏ đến thư mục chứa backend
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

# Cấu hình Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ecomsight_crawler",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"]
)

# Cấu hình timezone
celery_app.conf.timezone = 'Asia/Ho_Chi_Minh'

# Cấu hình Lập Lịch (Scheduler / Beat)
celery_app.conf.beat_schedule = {
    "crawl-hot-products-every-5-mins": {
        "task": "tasks.schedule_hot_products",
        "schedule": crontab(minute="*/5"), # Chạy mỗi 5 phút
    },
    "crawl-normal-products-every-30-mins": {
        "task": "tasks.schedule_normal_products",
        "schedule": crontab(minute="*/30"), # Chạy mỗi 30 phút
    },
}

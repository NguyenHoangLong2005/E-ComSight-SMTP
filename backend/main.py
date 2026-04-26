"""
E-ComSight — FastAPI Main App
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_tables
from app.routers.auth import router as auth_router
from app.routers.reviews import router as reviews_router
from app.routers.analytics import router as analytics_router
from app.routers.alerts import router as alerts_router
from app.routers.export_analysis import export_router, analysis_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 E-ComSight đang khởi động...")
    create_tables()
    logger.info("✅ Database tables đã sẵn sàng")

    # Preload NLP model in background
    import threading
    def preload():
        from app.services.nlp_service import load_phobert_model
        load_phobert_model()
    threading.Thread(target=preload, daemon=True).start()

    yield
    # Shutdown
    logger.info("👋 E-ComSight đang tắt...")


app = FastAPI(
    title="E-ComSight API",
    description="Nền tảng Phân tích Cảm xúc Khách hàng TMĐT",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(auth_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# Serve React frontend (production)
frontend_build = Path(__file__).parent / "frontend" / "dist"
if not frontend_build.exists():
    frontend_build = Path(__file__).parent.parent / "frontend" / "dist"

if frontend_build.exists():
    app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="static")
    logger.info(f"✅ Serving frontend từ {frontend_build}")
else:
    logger.info(f"ℹ️ Frontend build chưa có tại {frontend_build} — chạy React dev server riêng")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import init_db
from backend.app.news.ingestion import NewsIngestionService

# Routers
from backend.app.api.health import router as health_router
from backend.app.api.inventory import router as inventory_router
from backend.app.api.timeline import router as timeline_router
from backend.app.api.events import router as events_router
from backend.app.api.prediction import router as prediction_router
from backend.app.api.news import router as news_router
from backend.app.api.live_market import router as live_router
from backend.app.api.models import router as models_router

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} on {settings.API_HOST}:{settings.API_PORT}...")
    init_db()

    # Initial news poll in background
    try:
        service = NewsIngestionService()
        scheduler.add_job(service.run_ingestion, "interval", minutes=settings.NEWS_POLL_MINUTES, id="news_poll")
        scheduler.start()
        logger.info(f"Scheduled news ingestion every {settings.NEWS_POLL_MINUTES} minutes.")
    except Exception as e:
        logger.warning(f"Could not start news scheduler: {e}")

    yield

    # Shutdown
    if scheduler.running:
        scheduler.shutdown()
    logger.info(f"Shutting down {settings.APP_NAME}...")

app = FastAPI(
    title="PolitiTrade LK API",
    description="AI-Powered Political Event Stock Market Impact Prediction Platform for Colombo Stock Exchange (CSE)",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Configuration
origins = [
    settings.FRONTEND_URL,
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:8001",
    "http://localhost:8001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers
app.include_router(health_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(timeline_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(prediction_router, prefix="/api")
app.include_router(news_router, prefix="/api")
app.include_router(live_router, prefix="/api")
app.include_router(models_router, prefix="/api")

@app.get("/")
def get_root():
    """PolitiTrade LK API Root Index."""
    return {
        "service": "PolitiTrade LK API",
        "description": "Predicting the Impact of Government Policy Changes and Political Arrests on the Colombo Stock Exchange",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "status": "online"
    }

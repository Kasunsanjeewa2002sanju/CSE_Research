from fastapi import APIRouter
from datetime import datetime
from backend.app.core.config import settings

router = APIRouter(tags=["System"])

@router.get("/health")
def get_health():
    """Health check endpoint for PolitiTrade LK backend."""
    return {
        "status": "healthy",
        "service": "PolitiTrade LK API",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.utcnow().isoformat()
    }

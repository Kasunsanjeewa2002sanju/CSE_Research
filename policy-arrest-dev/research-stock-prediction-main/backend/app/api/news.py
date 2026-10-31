from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.news.ingestion import NewsIngestionService
from backend.app.news.verification import NewsVerifier
from backend.app.news.providers import NewsProviders

router = APIRouter(prefix="/news", tags=["News & Verification"])

ingestion_service = NewsIngestionService()
verifier = NewsVerifier()
providers = NewsProviders()

class VerificationRequest(BaseModel):
    headline_or_text: str = Field(default="", description="News headline or paragraph to verify")
    article_url: Optional[str] = Field(default=None, description="Optional URL of article to verify")

@router.get("/latest")
def get_latest_news(
    limit: int = Query(30, ge=1, le=100),
    family: Optional[str] = None
):
    """Returns recently ingested political and economic news articles."""
    articles = ingestion_service.get_latest_news(limit=limit, family=family)
    return {
        "count": len(articles),
        "articles": articles
    }

@router.post("/poll")
def poll_news_now():
    """Triggers immediate poll of active RSS sources and updates database."""
    count = ingestion_service.run_ingestion()
    return {
        "status": "success",
        "new_articles_ingested": count
    }

@router.get("/sources")
def get_sources_registry():
    """Lists configured trusted sources and their reliability tiers."""
    return providers.sources_config

@router.post("/verify")
def verify_user_news(req: VerificationRequest):
    """
    Verifies user-submitted news claim against trusted publishers and CSE history.
    Includes SSRF validation, claim extraction, evidence matching, and conditional market scenarios.
    """
    if not req.headline_or_text and not req.article_url:
        raise HTTPException(status_code=400, detail="Must provide either text or article URL to verify.")

    result = verifier.verify_claim(
        user_input_text=req.headline_or_text,
        user_input_url=req.article_url
    )
    return result

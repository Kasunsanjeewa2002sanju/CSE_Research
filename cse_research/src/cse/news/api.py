"""
FastAPI Service for CSE Econometric Platform & Dashboard Integration.

Provides Stage 11 scenario engine predictions alongside full empirical pipeline
endpoints for market series, data quality audit, political events, and live news.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from cse.scenario.engine import get_scenario_engine
from cse.api.router import api_v1_router
from cse_live.scheduler import get_live_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager starting and stopping the CSE live ingestion scheduler."""
    scheduler = get_live_scheduler()
    app.state.cse_scheduler = scheduler
    await scheduler.start()
    yield
    await scheduler.stop()


app = FastAPI(
    title="CSE Political Event & News Scenario Engine API",
    version="1.0.0",
    description="Full econometrics and scenario prediction REST API for Sri Lankan political events & CSE ASPI research.",
    lifespan=lifespan,
)

# CORS Middleware (Rule FR2 & Dashboard Origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers (under /api/v1, /api, and at root for proxy flexibility)
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v1_router, prefix="/api")
app.include_router(api_v1_router)


class NewsPredictRequest(BaseModel):
    headline: str = Field(..., description="News headline text")
    description: str = Field("", description="Optional body or context")
    publication_date: str = Field("", description="Date string YYYY-MM-DD")
    source: Optional[str] = Field(None, description="Optional news source name")
    current_aspi: Optional[float] = Field(None, description="Optional live ASPI index level")


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint (backwards-compatible)."""
    return {"status": "healthy", "service": "cse_news_scenario_api"}


@app.post("/predict")
def predict_scenario(payload: NewsPredictRequest) -> Dict[str, Any]:
    """
    Execute conditional counterfactual scenario forecast for incoming news (backwards-compatible).
    """
    try:
        engine = get_scenario_engine()
        result = engine.run(
            headline=payload.headline,
            description=payload.description,
            publication_date=payload.publication_date,
            source=payload.source,
            current_aspi=payload.current_aspi,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
Master APIRouter uniting all research platform endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from cse.api.meta import router as meta_router
from cse.api.market import router as market_router
from cse.api.audit import router as audit_router
from cse.api.events import router as events_router
from cse.api.news import router as news_router
from cse.api.event_study import router as event_study_router
from cse.api.models import router as models_router
from cse.api.protocol import router as protocol_router
from cse.api.scenario import router as scenario_router
from cse.api.research import router as research_router
from cse.api.favorites import router as favorites_router

api_v1_router = APIRouter()

api_v1_router.include_router(meta_router)
api_v1_router.include_router(market_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(news_router)
api_v1_router.include_router(event_study_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(protocol_router)
api_v1_router.include_router(scenario_router)
api_v1_router.include_router(research_router)
api_v1_router.include_router(favorites_router)

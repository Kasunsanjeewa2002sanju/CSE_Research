from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query

from backend.app.live.cse_adapter import CSELiveAdapter

router = APIRouter(prefix="/live", tags=["Live CSE Market"])
adapter = CSELiveAdapter()

@router.get("/status")
def get_live_market_status():
    """Current market open/closed status, session phase, and timestamp."""
    return adapter.provider.get_market_status()

@router.get("/indices")
def get_live_indices():
    """Real-time ASPI and S&P SL20 index values, daily changes, and percentages."""
    return adapter.provider.get_indices()

@router.get("/overview")
def get_live_overview():
    """Comprehensive snapshot combining indices, market status, and turnover."""
    return adapter.get_market_overview()

@router.get("/gainers")
def get_live_gainers():
    """Top price gainers on the Colombo Stock Exchange."""
    return adapter.provider.get_top_gainers()

@router.get("/losers")
def get_live_losers():
    """Top price losers on the Colombo Stock Exchange."""
    return adapter.provider.get_top_losers()

@router.get("/active")
def get_most_active():
    """Most active listed securities by volume/turnover."""
    movers = adapter.get_top_movers()
    return movers

@router.get("/securities")
def get_all_securities(search: Optional[str] = Query(None, description="Search symbol or company name")):
    """Searchable list of all listed CSE securities with last trade prices."""
    return adapter.get_securities_list(search=search)

@router.get("/securities/{symbol}")
def get_security_quote(symbol: str):
    """Detailed price quote for a single CSE listed company."""
    sec = adapter.get_security_detail(symbol)
    if not sec:
        raise HTTPException(status_code=404, detail=f"Security symbol '{symbol}' not found.")
    return sec

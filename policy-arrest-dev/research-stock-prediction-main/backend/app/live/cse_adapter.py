from typing import Dict, Any, List, Optional
from backend.app.live.providers import get_live_provider, LivePriceProvider

class CSELiveAdapter:
    """Service layer coordinating live CSE data retrieval, fallback management, and caching."""

    def __init__(self, provider: Optional[LivePriceProvider] = None):
        self.provider = provider or get_live_provider()

    def get_market_overview(self) -> Dict[str, Any]:
        """Combines market status, top indices, and turnover summary."""
        status = self.provider.get_market_status()
        indices = self.provider.get_indices()
        summary = self.provider.get_market_summary()

        return {
            "status": status,
            "indices": indices,
            "summary": summary
        }

    def get_top_movers(self) -> Dict[str, Any]:
        """Returns top gainers and losers."""
        gainers = self.provider.get_top_gainers()
        losers = self.provider.get_top_losers()
        return {
            "gainers": gainers,
            "losers": losers
        }

    def get_securities_list(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all listed securities with optional symbol/name search filter."""
        all_sec = self.provider.get_all_securities()
        if not search:
            return all_sec
        s = search.lower()
        return [sec for sec in all_sec if s in sec["symbol"].lower() or s in sec["name"].lower()]

    def get_security_detail(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Returns details for a single quoted security."""
        all_sec = self.provider.get_all_securities()
        for sec in all_sec:
            if sec["symbol"].lower() == symbol.lower():
                return sec
        return None

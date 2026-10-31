from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.live.cache import live_cache

class LivePriceProvider(ABC):
    """Abstract Base Class for Live Colombo Stock Exchange Price Providers."""
    
    @abstractmethod
    def get_market_status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_indices(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_top_gainers(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_top_losers(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_market_summary(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_all_securities(self) -> List[Dict[str, Any]]:
        pass


class CSEUnofficialProvider(LivePriceProvider):
    """
    Direct live integration with public CSE JSON endpoints via HTTP POST.
    Server-side cached with 30-second TTL to avoid load on exchange servers.
    """
    BASE_URL = "https://www.cse.lk/api"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.cse.lk",
        "Referer": "https://www.cse.lk/"
    }

    def _post(self, endpoint: str, timeout: float = 6.0) -> Optional[Any]:
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            resp = httpx.post(url, headers=self.HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.warning(f"CSE endpoint {endpoint} returned status {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"CSE request failed for {endpoint}: {e}")
            return None

    def get_market_status(self) -> Dict[str, Any]:
        cached = live_cache.get("market_status")
        if cached:
            return cached

        res = self._post("marketStatus")
        now_str = datetime.now(timezone.utc).isoformat()
        if res and isinstance(res, dict):
            status_text = res.get("status", "Market Closed")
            data = {
                "market_status": status_text,
                "is_open": "open" in status_text.lower(),
                "timestamp": now_str,
                "provider": "cse_unofficial",
                "is_demo": False,
                "is_stale": False
            }
            live_cache.set("market_status", data, ttl_seconds=settings.LIVE_CACHE_SECONDS)
            return data

        # Check stale
        stale = live_cache.get_stale("market_status")
        if stale:
            stale_data = stale["data"]
            stale_data["is_stale"] = True
            return stale_data

        return {
            "market_status": "Market Closed (Fallback)",
            "is_open": False,
            "timestamp": now_str,
            "provider": "cse_unofficial",
            "is_demo": False,
            "is_stale": True
        }

    def get_indices(self) -> Dict[str, Any]:
        cached = live_cache.get("indices")
        if cached:
            return cached

        aspi_res = self._post("aspiData")
        snp_res = self._post("snpData")
        now_str = datetime.now(timezone.utc).isoformat()

        if aspi_res and isinstance(aspi_res, dict):
            aspi_val = float(aspi_res.get("value", 0.0))
            aspi_chg = float(aspi_res.get("change", 0.0))
            aspi_pct = float(aspi_res.get("percentage", 0.0))
            aspi_high = float(aspi_res.get("highValue", aspi_val))
            aspi_low = float(aspi_res.get("lowValue", aspi_val))

            sp20_val = float(snp_res.get("value", 0.0)) if snp_res and isinstance(snp_res, dict) else 0.0
            sp20_chg = float(snp_res.get("change", 0.0)) if snp_res and isinstance(snp_res, dict) else 0.0
            sp20_pct = float(snp_res.get("percentage", 0.0)) if snp_res and isinstance(snp_res, dict) else 0.0

            data = {
                "timestamp": now_str,
                "provider": "cse_unofficial",
                "is_demo": False,
                "is_stale": False,
                "aspi": {
                    "symbol": "ASPI",
                    "name": "All Share Price Index",
                    "value": round(aspi_val, 2),
                    "change": round(aspi_chg, 2),
                    "change_pct": round(aspi_pct, 2),
                    "high": round(aspi_high, 2),
                    "low": round(aspi_low, 2)
                },
                "sp_sl20": {
                    "symbol": "SP_SL20",
                    "name": "S&P Sri Lanka 20",
                    "value": round(sp20_val, 2),
                    "change": round(sp20_chg, 2),
                    "change_pct": round(sp20_pct, 2)
                }
            }
            live_cache.set("indices", data, ttl_seconds=settings.LIVE_CACHE_SECONDS)
            return data

        stale = live_cache.get_stale("indices")
        if stale:
            stale_data = stale["data"]
            stale_data["is_stale"] = True
            return stale_data

        return {
            "timestamp": now_str,
            "provider": "cse_unofficial",
            "is_demo": False,
            "is_stale": True,
            "aspi": {"symbol": "ASPI", "name": "All Share Price Index", "value": 13462.39, "change": 0.0, "change_pct": 0.0},
            "sp_sl20": {"symbol": "SP_SL20", "name": "S&P Sri Lanka 20", "value": 4120.50, "change": 0.0, "change_pct": 0.0}
        }

    def get_top_gainers(self) -> List[Dict[str, Any]]:
        cached = live_cache.get("top_gainers")
        if cached:
            return cached

        res = self._post("topGainers")
        if res and isinstance(res, list):
            gainers = []
            for item in res[:10]:
                gainers.append({
                    "symbol": item.get("symbol", ""),
                    "price": float(item.get("price", 0.0)),
                    "change": float(item.get("change", 0.0)),
                    "change_pct": float(item.get("changePercentage", 0.0)),
                    "trade_date": item.get("tradeDate")
                })
            live_cache.set("top_gainers", gainers, ttl_seconds=settings.LIVE_CACHE_SECONDS)
            return gainers

        stale = live_cache.get_stale("top_gainers")
        return stale["data"] if stale else []

    def get_top_losers(self) -> List[Dict[str, Any]]:
        cached = live_cache.get("top_losers")
        if cached:
            return cached

        res = self._post("topLooses")
        if res and isinstance(res, list):
            losers = []
            for item in res[:10]:
                losers.append({
                    "symbol": item.get("symbol", ""),
                    "price": float(item.get("price", 0.0)),
                    "change": float(item.get("change", 0.0)),
                    "change_pct": float(item.get("changePercentage", 0.0)),
                    "trade_date": item.get("tradeDate")
                })
            live_cache.set("top_losers", losers, ttl_seconds=settings.LIVE_CACHE_SECONDS)
            return losers

        stale = live_cache.get_stale("top_losers")
        return stale["data"] if stale else []

    def get_market_summary(self) -> Dict[str, Any]:
        cached = live_cache.get("market_summary")
        if cached:
            return cached

        res = self._post("marketSummery")
        if res and isinstance(res, dict):
            data = {
                "turnover_lkr": float(res.get("tradeVolume", 0.0)),
                "share_volume": int(res.get("shareVolume", 0)),
                "trades_count": int(res.get("trades", 0)),
                "trade_date": res.get("tradeDate")
            }
            live_cache.set("market_summary", data, ttl_seconds=settings.LIVE_CACHE_SECONDS)
            return data

        stale = live_cache.get_stale("market_summary")
        return stale["data"] if stale else {"turnover_lkr": 0.0, "share_volume": 0, "trades_count": 0}

    def get_all_securities(self) -> List[Dict[str, Any]]:
        cached = live_cache.get("all_securities")
        if cached:
            return cached

        res = self._post("tradeSummary")
        if res and isinstance(res, dict) and "reqTradeSummery" in res:
            securities = []
            for item in res["reqTradeSummery"]:
                symbol = item.get("symbol", "")
                name = item.get("name", "")
                price = float(item.get("price", 0.0)) if item.get("price") is not None else 0.0
                change = float(item.get("change", 0.0)) if item.get("change") is not None else 0.0
                change_pct = float(item.get("changePercentage", 0.0)) if item.get("changePercentage") is not None else 0.0
                vol = int(item.get("volume", 0)) if item.get("volume") is not None else 0
                
                securities.append({
                    "symbol": symbol,
                    "name": name,
                    "price": price,
                    "change": change,
                    "change_pct": change_pct,
                    "volume": vol
                })
            live_cache.set("all_securities", securities, ttl_seconds=60)
            return securities

        stale = live_cache.get_stale("all_securities")
        return stale["data"] if stale else []


class DemoPriceProvider(LivePriceProvider):
    """Fallback demonstration provider strictly for local testing when network is disabled."""
    def get_market_status(self) -> Dict[str, Any]:
        return {
            "market_status": "Market Closed (DEMO DATA)",
            "is_open": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "demo",
            "is_demo": True,
            "is_stale": False
        }

    def get_indices(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "demo",
            "is_demo": True,
            "is_stale": False,
            "aspi": {"symbol": "ASPI", "name": "All Share Price Index (DEMO)", "value": 13450.0, "change": 15.2, "change_pct": 0.11},
            "sp_sl20": {"symbol": "SP_SL20", "name": "S&P Sri Lanka 20 (DEMO)", "value": 4110.0, "change": -5.4, "change_pct": -0.13}
        }

    def get_top_gainers(self) -> List[Dict[str, Any]]:
        return [
            {"symbol": "DEMO.N0000", "price": 45.0, "change": 4.5, "change_pct": 11.11, "trade_date": "DEMO"}
        ]

    def get_top_losers(self) -> List[Dict[str, Any]]:
        return [
            {"symbol": "TEST.N0000", "price": 22.0, "change": -2.0, "change_pct": -8.33, "trade_date": "DEMO"}
        ]

    def get_market_summary(self) -> Dict[str, Any]:
        return {"turnover_lkr": 500000000.0, "share_volume": 15000000, "trades_count": 8500}

    def get_all_securities(self) -> List[Dict[str, Any]]:
        return [
            {"symbol": "JKH.N0000", "name": "John Keells Holdings PLC (DEMO)", "price": 195.0, "change": 1.5, "change_pct": 0.78, "volume": 1200000},
            {"symbol": "COMB.N0000", "name": "Commercial Bank of Ceylon (DEMO)", "price": 112.0, "change": -0.5, "change_pct": -0.44, "volume": 850000}
        ]


def get_live_provider() -> LivePriceProvider:
    mode = settings.LIVE_PROVIDER.lower()
    if mode == "demo":
        return DemoPriceProvider()
    elif mode == "disabled":
        return DemoPriceProvider()  # Fallback gracefully
    return CSEUnofficialProvider()

"""Parser module for raw CSE API and WebSocket response payloads.

Extracts, normalizes, and packages data into typed models.
Handles missing/null fields during pre-open and trading halts.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from cse_live.models import (
    MarketStatus,
    MarketStatusType,
    IntradayPoint,
    DailyBar,
    COLOMBO_TZ,
)


class CSEDataParser:
    """Parses raw JSON and form-encoded data structures from CSE feeds."""

    @staticmethod
    def parse_market_status(data: Dict[str, Any]) -> MarketStatus:
        """Parse response from POST /api/marketStatus or STOMP /topic/status."""
        raw_status = data.get("status") or "Unknown"
        return MarketStatus(
            raw_status=str(raw_status),
            status=str(raw_status),
            message=data.get("message")
        )

    @staticmethod
    def parse_aspi_tick(data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ASPI object from STOMP /topic/aspi."""
        # {"id": 37201800, "value": 19984.84, "lowValue": 19944.67, "highValue": 20108.03, "change": -74.58, "percentage": -0.37, "sectorId": 1.0, "timestamp": 1792481325548}
        raw_val = data.get("value")
        val = float(raw_val) if raw_val is not None else None
        chg = float(data.get("change") or 0.0)
        pct = float(data.get("percentage") or 0.0)
        low = float(data.get("lowValue") or val) if val is not None else None
        high = float(data.get("highValue") or val) if val is not None else None
        raw_ts = data.get("timestamp")
        dt = (
            datetime.fromtimestamp(raw_ts / 1000.0, tz=COLOMBO_TZ)
            if raw_ts
            else datetime.now(COLOMBO_TZ)
        )
        prev = (val - chg) if val is not None else None
        return {
            "value": val,
            "change": chg,
            "percentage": pct,
            "previous_close": prev,
            "low": low,
            "high": high,
            "timestamp": dt,
        }

    @staticmethod
    def parse_sp20_tick(data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse S&P SL 20 object from STOMP /topic/snp."""
        raw_val = data.get("value")
        val = float(raw_val) if raw_val is not None else None
        chg = float(data.get("change")) if data.get("change") is not None else None
        pct = float(data.get("percentage")) if data.get("percentage") is not None else None
        raw_ts = data.get("timestamp")
        dt = (
            datetime.fromtimestamp(raw_ts / 1000.0, tz=COLOMBO_TZ)
            if raw_ts
            else datetime.now(COLOMBO_TZ)
        )
        return {
            "value": val,
            "change": chg,
            "percentage": pct,
            "timestamp": dt,
        }

    @staticmethod
    def parse_summary(data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse market turnover, share volume, and trade count from /topic/summary."""
        # {"tradeVolume": 512922744.85, "shareVolume": 15091123, "trades": 7357, "tradeDate": 1792481325548}
        turnover = float(data.get("tradeVolume") or 0.0)
        shares = int(data.get("shareVolume") or 0)
        trades = int(data.get("trades") or 0)
        raw_date = data.get("tradeDate")
        return {
            "turnover_lkr": turnover,
            "shares_traded": shares,
            "trades_count": trades,
            "trade_date": raw_date,
        }

    @staticmethod
    def parse_chart_data_intraday(points: List[Dict[str, Any]]) -> List[IntradayPoint]:
        """Parse intraday tick array from POST /api/chartData (period=1)."""
        result = []
        for p in points:
            raw_val = p.get("v")
            raw_ts = p.get("d")
            if raw_val is not None and raw_ts is not None:
                dt = datetime.fromtimestamp(raw_ts / 1000.0, tz=COLOMBO_TZ)
                pc = float(p.get("pc")) if p.get("pc") is not None else None
                result.append(IntradayPoint(
                    timestamp=dt,
                    value=float(raw_val),
                    percent_change=pc
                ))
        return result

    @staticmethod
    def parse_chart_data_daily(bars: List[Dict[str, Any]]) -> List[DailyBar]:
        """Parse daily closing bars from POST /api/chartData (period=2, 3, or 5)."""
        result = []
        for b in bars:
            raw_val = b.get("v")
            raw_ts = b.get("d")
            if raw_val is not None and raw_ts is not None:
                dt = datetime.fromtimestamp(raw_ts / 1000.0, tz=COLOMBO_TZ)
                pc = float(b.get("pc")) if b.get("pc") is not None else None
                result.append(DailyBar(
                    trade_date=dt.date(),
                    close=float(raw_val),
                    percent_change=pc
                ))
        return result

    @staticmethod
    def parse_all_sectors_asi(sectors: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract All Share Price Index (ASI) record from POST /api/allSectors."""
        for item in sectors:
            symbol = item.get("symbol") or ""
            sec_id = item.get("sectorId")
            name = item.get("name") or item.get("indexName") or ""
            if symbol.upper() == "ASI" or sec_id == 1 or "ALL SHARE" in name.upper():
                val = float(item["indexValue"]) if item.get("indexValue") is not None else None
                chg = float(item.get("change") or 0.0)
                pct = float(item.get("percentage") or 0.0)
                prev = float(item.get("sectorPreviousClose") or val) if val is not None else None
                raw_ts = item.get("transactionTime")
                dt = (
                    datetime.fromtimestamp(raw_ts / 1000.0, tz=COLOMBO_TZ)
                    if raw_ts
                    else datetime.now(COLOMBO_TZ)
                )
                return {
                    "value": val,
                    "change": chg,
                    "percentage": pct,
                    "previous_close": prev,
                    "timestamp": dt,
                }
        return None

    @staticmethod
    def parse_all_sectors_sp20(sectors: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract S&P Sri Lanka 20 record from POST /api/allSectors."""
        for item in sectors:
            symbol = item.get("symbol") or ""
            sec_id = item.get("sectorId")
            name = item.get("name") or item.get("indexName") or ""
            if symbol.upper() == "S&P SL20" or sec_id == 40 or "S&P SL20" in name.upper() or "S&P SL 20" in name.upper():
                val = float(item["indexValue"]) if item.get("indexValue") is not None else None
                chg = float(item.get("change") or 0.0)
                pct = float(item.get("percentage") or 0.0)
                prev = float(item.get("sectorPreviousClose") or val) if val is not None else None
                raw_ts = item.get("transactionTime")
                dt = (
                    datetime.fromtimestamp(raw_ts / 1000.0, tz=COLOMBO_TZ)
                    if raw_ts
                    else datetime.now(COLOMBO_TZ)
                )
                return {
                    "value": val,
                    "change": chg,
                    "percentage": pct,
                    "previous_close": prev,
                    "timestamp": dt,
                }
        return None

    @staticmethod
    def parse_all_sectors_aggregates(sectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate market turnover, volume, and trades across sectors."""
        tot_turnover = sum(float(item.get('sectorTurnoverToday') or 0.0) for item in sectors if item.get('sectorId') not in (1, 40))
        tot_volume = sum(int(item.get('sectorVolumeToday') or 0) for item in sectors if item.get('sectorId') not in (1, 40))
        tot_trades = sum(int(item.get('sectorTradeToday') or 0) for item in sectors if item.get('sectorId') not in (1, 40))
        return {
            "turnover_lkr": tot_turnover,
            "shares_traded": tot_volume,
            "trades_count": tot_trades,
        }

    @staticmethod
    def parse_trade_summary(data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse total turnover, shares traded, and trades from POST /api/tradeSummary."""
        stocks = data.get("reqTradeSummery") or []
        turnover = sum(float(s.get("turnover") or 0.0) for s in stocks)
        shares = sum(int(s.get("sharevolume") or 0) for s in stocks)
        trades = sum(int(s.get("tradevolume") or 0) for s in stocks)
        return {
            "turnover_lkr": turnover,
            "shares_traded": shares,
            "trades_count": trades,
        }


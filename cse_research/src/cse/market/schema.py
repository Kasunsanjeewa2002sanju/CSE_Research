"""Pydantic schemas and domain models for CSE live market data contracts.

Adheres strictly to the verified data contract discovered from cse.lk.
Units, ranges, and consistency are validated at runtime.
"""

from __future__ import annotations

from datetime import datetime, date, timezone
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, field_validator, model_validator

COLOMBO_TZ = ZoneInfo("Asia/Colombo")


class FreshnessState(str, Enum):
    """Data freshness indicator relative to market session and SLA."""
    LIVE = "LIVE"          # Active session, tick received within freshness SLA (< 60s)
    DELAYED = "DELAYED"    # Active session, but tick is delayed (> 60s)
    CLOSED = "CLOSED"      # Market session officially closed; official closing snapshot
    STALE = "STALE"        # Feed offline, cache expired, or disconnected


class MarketStatusType(str, Enum):
    """Standardized CSE market session statuses."""
    OPENING_AUCTION = "Opening Auction Call"
    REGULAR_TRADING = "Regular Trading"
    MARKET_HALTED = "Market Halted"
    CLOSING_AUCTION = "Closing Auction Call"
    STATISTICS_FINALIZING = "Market Close (Statistics Being Finalized)"
    MARKET_CLOSED = "Market Closed"
    PRE_TRADING = "Pre-Trading"
    UNKNOWN = "Unknown"


class MarketStatus(BaseModel):
    """Status of the CSE market trading session."""
    raw_status: str = Field(..., description="Raw status string from CSE feed")
    status: MarketStatusType = Field(..., description="Normalized market status")
    is_open: bool = Field(False, description="Whether continuous regular trading is active")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(COLOMBO_TZ))
    message: Optional[str] = Field(None, description="Optional exchange announcement/message")

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: str) -> MarketStatusType:
        if isinstance(v, MarketStatusType):
            return v
        v_clean = str(v).strip()
        mapping = {
            "Opening Auction Call": MarketStatusType.OPENING_AUCTION,
            "Open Auction Call": MarketStatusType.OPENING_AUCTION,
            "Regular Trading": MarketStatusType.REGULAR_TRADING,
            "open": MarketStatusType.REGULAR_TRADING,
            "Open": MarketStatusType.REGULAR_TRADING,
            "Market Close (Statistics Being Finalized)": MarketStatusType.STATISTICS_FINALIZING,
            "Market Closed": MarketStatusType.MARKET_CLOSED,
            "closed": MarketStatusType.MARKET_CLOSED,
            "Closed": MarketStatusType.MARKET_CLOSED,
            "Pre-Trading": MarketStatusType.PRE_TRADING,
            "Pre Trading": MarketStatusType.PRE_TRADING,
            "Market Halted": MarketStatusType.MARKET_HALTED,
            "Halt": MarketStatusType.MARKET_HALTED,
        }
        return mapping.get(v_clean, MarketStatusType.UNKNOWN)

    @model_validator(mode="after")
    def set_is_open(self) -> MarketStatus:
        self.is_open = (self.status == MarketStatusType.REGULAR_TRADING)
        return self


class IntradayPoint(BaseModel):
    """Single intraday index tick."""
    timestamp: datetime = Field(..., description="Colombo local timestamp")
    value: float = Field(..., ge=1000.0, le=100000.0, description="Index level in points")
    percent_change: Optional[float] = Field(None, ge=-50.0, le=50.0, description="% change vs prev close")
    volume: Optional[float] = Field(None, ge=0.0, description="Intraday trade volume if available")


class DailyBar(BaseModel):
    """End-of-day summary bar for historical reconciliation."""
    trade_date: date = Field(..., description="Trading date")
    close: float = Field(..., ge=1000.0, le=100000.0, description="Official closing level (ASPI)")
    aspi: Optional[float] = Field(None, description="ASPI close alias")
    sp20: Optional[float] = Field(None, description="S&P SL 20 close level if available")
    change: Optional[float] = Field(None, description="Absolute change vs previous day close")
    percent_change: Optional[float] = Field(None, ge=-50.0, le=50.0, description="% change vs previous close")
    turnover: Optional[float] = Field(None, ge=0.0, description="Turnover in LKR")
    turnover_equity_mn: Optional[float] = Field(None, ge=0.0, description="Turnover in Million LKR")
    share_volume: Optional[int] = Field(None, ge=0, description="Total shares traded in units")
    shares_traded_equity_k: Optional[float] = Field(None, ge=0.0, description="Shares traded in thousands")
    trades: Optional[int] = Field(None, ge=0, description="Total number of trades")
    aspi_log_return: Optional[float] = Field(None, description="Official daily continuous log return")

    @model_validator(mode="after")
    def populate_aliases(self) -> DailyBar:
        if self.aspi is None:
            self.aspi = self.close
        if self.turnover is not None and self.turnover_equity_mn is None:
            self.turnover_equity_mn = round(self.turnover / 1_000_000.0, 2)
        elif self.turnover_equity_mn is not None and self.turnover is None:
            self.turnover = round(self.turnover_equity_mn * 1_000_000.0, 2)
        if self.share_volume is not None and self.shares_traded_equity_k is None:
            self.shares_traded_equity_k = round(self.share_volume / 1000.0, 1)
        elif self.shares_traded_equity_k is not None and self.share_volume is None:
            self.share_volume = int(self.shares_traded_equity_k * 1000.0)
        return self


class SourceHealth(BaseModel):
    """Operational health telemetry for an upstream source."""
    source_name: str = Field(..., description="Identifier of the upstream source")
    is_healthy: bool = Field(True, description="Whether the source is currently reachable and responding")
    latency_ms: float = Field(..., ge=0.0, description="Round-trip request latency in milliseconds")
    last_success: Optional[datetime] = Field(None, description="Timestamp of last successful response")
    last_error: Optional[str] = Field(None, description="Last error message if failed")
    error_count: int = Field(0, ge=0, description="Consecutive failure count")


class MarketSnapshot(BaseModel):
    """Complete consolidated market snapshot from CSE.
    
    Verifications:
    - aspi_value: float index points (e.g., 20059.42).
    - market_turnover: RAW LKR (Rupees), not '000 and not millions.
    - shares_traded: RAW share unit count, not '000.
    - total_trades: integer trade execution count.
    - timestamps: Asia/Colombo timezone.
    """
    # ASPI Metrics (Primary Index)
    aspi_value: float = Field(
        ...,
        ge=1000.0,
        le=100000.0,
        description="All Share Price Index current level in points"
    )
    aspi_change: float = Field(
        ...,
        ge=-10000.0,
        le=10000.0,
        description="ASPI point change relative to previous close"
    )
    aspi_percent_change: float = Field(
        ...,
        ge=-50.0,
        le=50.0,
        description="ASPI percentage change relative to previous close"
    )
    aspi_previous_close: float = Field(
        ...,
        ge=1000.0,
        le=100000.0,
        description="ASPI official previous close level in points"
    )

    # S&P Sri Lanka 20 Metrics (Liquid Blue-Chip Index)
    sp20_value: Optional[float] = Field(
        None,
        ge=500.0,
        le=50000.0,
        description="S&P SL 20 index level in points (null during opening auction)"
    )
    sp20_change: Optional[float] = Field(
        None,
        ge=-5000.0,
        le=5000.0,
        description="S&P SL 20 point change"
    )
    sp20_percent_change: Optional[float] = Field(
        None,
        ge=-50.0,
        le=50.0,
        description="S&P SL 20 percentage change"
    )
    sp20_previous_close: Optional[float] = Field(
        None,
        ge=500.0,
        le=50000.0,
        description="S&P SL 20 previous close level in points"
    )

    # Market Activity (Resolved to raw units)
    market_turnover: float = Field(
        ...,
        ge=0.0,
        description="Total market turnover in Sri Lankan Rupees (LKR) - verified raw currency"
    )
    shares_traded: int = Field(
        ...,
        ge=0,
        description="Total shares traded in units - verified raw share count"
    )
    total_trades: int = Field(
        ...,
        ge=0,
        description="Total number of trade transactions executed"
    )

    # Status & Telemetry
    market_status: MarketStatus = Field(..., description="Current market operational state")
    freshness: FreshnessState = Field(..., description="Data freshness assessment")
    source_timestamp: datetime = Field(..., description="Timestamp provided by CSE source (Colombo TZ)")
    ingest_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when data was ingested by our backend"
    )
    source: str = Field(..., description="Data origin identifier (e.g., 'websocket_stomp', 'rest_api')")
    health: Optional[SourceHealth] = Field(None, description="Health metrics of the feeding source")

    @model_validator(mode="after")
    def validate_index_consistency(self) -> MarketSnapshot:
        """Validate mathematical consistency between index, previous close, and change."""
        # Check ASPI consistency: change ~ aspi_value - aspi_previous_close
        expected_change = self.aspi_value - self.aspi_previous_close
        diff = abs(self.aspi_change - expected_change)
        # Allow tolerance of 0.05 points for floating point / rounding
        if diff > 0.05:
            # If percentage change indicates 0, CSE might send change=0 before first tick
            if abs(self.aspi_change) > 0.01:
                raise ValueError(
                    f"ASPI change mismatch: reported {self.aspi_change}, "
                    f"expected {expected_change:.2f} (value={self.aspi_value}, prev_close={self.aspi_previous_close})"
                )
        return self


# ============================================================================
# STAGE 3: REST API RESPONSE CONTRACTS
# All responses must include: freshness_state, source_timestamp, fetched_at
# ============================================================================

class MarketLatestResponse(BaseModel):
    """Payload returned by GET /api/market/latest."""
    aspi_value: float = Field(..., description="Latest ASPI index level")
    aspi_change: float = Field(..., description="ASPI point change vs previous close")
    aspi_percent_change: float = Field(..., description="ASPI percentage change vs previous close")
    aspi_previous_close: float = Field(..., description="Previous confirmed closing level of ASPI")
    sp20_value: Optional[float] = Field(None, description="Latest S&P SL 20 index level")
    sp20_change: Optional[float] = Field(None, description="S&P SL 20 point change")
    sp20_percent_change: Optional[float] = Field(None, description="S&P SL 20 percentage change")
    sp20_previous_close: Optional[float] = Field(None, description="Previous confirmed closing level of S&P SL 20")
    market_turnover: float = Field(..., description="Turnover in LKR")
    shares_traded: int = Field(..., description="Total volume in shares")
    total_trades: int = Field(..., description="Total trade count")
    market_status: MarketStatus = Field(..., description="Current market operational state")
    freshness_state: FreshnessState = Field(..., description="Data freshness indicator")
    source_timestamp: datetime = Field(..., description="Timestamp of underlying source data (Colombo TZ)")
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when response was built (UTC)"
    )
    source: str = Field("in_memory_cache", description="Data provenance (e.g. 'rest_api', 'disk_recovery')")
    persisted_recovery: bool = Field(False, description="True if loaded from disk persistence upon restart")

    # Convenience aliases for frontend backwards compatibility
    aspi_level: Optional[float] = None
    daily_return: Optional[float] = None
    equity_turnover_lkr: Optional[float] = None

    @model_validator(mode="after")
    def set_compatibility_aliases(self) -> MarketLatestResponse:
        if self.aspi_level is None:
            self.aspi_level = self.aspi_value
        if self.daily_return is None:
            self.daily_return = self.aspi_percent_change
        if self.equity_turnover_lkr is None:
            self.equity_turnover_lkr = self.market_turnover
        return self


class IntradaySeriesPoint(BaseModel):
    """Aggregated intraday point for a downsampled bucket."""
    timestamp: datetime = Field(..., description="Bucket boundary timestamp (Colombo TZ)")
    value: float = Field(..., description="Latest/closing metric value for the bucket")
    open: Optional[float] = Field(None, description="Opening value in the bucket")
    high: Optional[float] = Field(None, description="High value in the bucket")
    low: Optional[float] = Field(None, description="Low value in the bucket")
    close: Optional[float] = Field(None, description="Close value in the bucket")
    turnover: Optional[float] = Field(None, description="Turnover in LKR at this bucket")
    volume: Optional[int] = Field(None, description="Shares volume at this bucket")


class MarketIntradayResponse(BaseModel):
    """Payload returned by GET /api/market/intraday."""
    metric: str = Field(..., description="Metric identifier: aspi, sp20, turnover, shares_traded")
    session: str = Field(..., description="Session date (YYYY-MM-DD) or 'current'")
    points: list[IntradaySeriesPoint] = Field(default_factory=list, description="Downsampled bucketed points")
    count: int = Field(0, description="Total points returned")
    downsample_interval: str = Field("1m", description="Bucket window length (e.g., '1m')")
    freshness_state: FreshnessState = Field(..., description="Data freshness indicator")
    source_timestamp: Optional[datetime] = Field(None, description="Latest point timestamp")
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response generation timestamp (UTC)"
    )


class MarketHistoryPoint(BaseModel):
    """Daily historical bar combining research panel and live appends."""
    date: str = Field(..., description="Session date YYYY-MM-DD")
    aspi: float = Field(..., description="ASPI closing level")
    sp20: Optional[float] = Field(None, description="S&P SL 20 closing level")
    turnover_equity_mn: Optional[float] = Field(None, description="Turnover in million LKR")
    shares_traded_equity_k: Optional[float] = Field(None, description="Shares traded in thousands")
    aspi_log_return: Optional[float] = Field(None, description="Daily continuous log return")
    turnover_lkr: Optional[float] = Field(None, description="Turnover in LKR")
    volume_shares: Optional[int] = Field(None, description="Shares volume in units")
    return_pct: Optional[float] = Field(None, description="Daily log return expressed in %")


class MarketHistoryResponse(BaseModel):
    """Payload returned by GET /api/market/history."""
    metric: Optional[str] = Field(None, description="Queried metric filter or 'all'")
    from_date: Optional[str] = Field(None, description="Start date filter YYYY-MM-DD")
    to_date: Optional[str] = Field(None, description="End date filter YYYY-MM-DD")
    count: int = Field(..., description="Number of bars returned")
    data: list[MarketHistoryPoint] = Field(default_factory=list, description="Historical bars")
    freshness_state: FreshnessState = Field(..., description="Data freshness indicator")
    source_timestamp: Optional[datetime] = Field(None, description="Timestamp of latest bar in view")
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response generation timestamp (UTC)"
    )


class MarketStatsResponse(BaseModel):
    """Payload returned by GET /api/market/stats."""
    panel_size_days: int = Field(..., description="Total trading sessions in merged research panel (e.g. 7635)")
    as_of_date: str = Field(..., description="Latest session date YYYY-MM-DD")
    daily_return_pct: float = Field(..., description="Latest 1D continuous log return in percent (e.g. 0.7917%)")
    daily_log_return: float = Field(..., description="Latest 1D continuous log return")
    five_day_return_pct: float = Field(..., description="5-day return in percent")
    five_day_log_return: float = Field(..., description="5-day continuous log return")
    realized_volatility_annualized: float = Field(
        ...,
        description="Annualized 20D rolling realized volatility in percent (e.g. 15.70%)"
    )
    volatility_window_days: int = Field(20, description="Rolling window size in trading days")
    annualization_factor: float = Field(240.0, description="Trading days per year used for annualization (sqrt(240))")
    baseline_aspi: float = Field(..., description="Current baseline ASPI level driving econometric models")
    baseline_sp20: Optional[float] = Field(None, description="Current baseline S&P SL 20 level")
    equity_turnover_lkr: Optional[float] = Field(None, description="Latest session turnover in LKR")
    shares_traded: Optional[int] = Field(None, description="Latest session shares traded")
    freshness_state: FreshnessState = Field(..., description="Data freshness indicator")
    source_timestamp: Optional[datetime] = Field(None, description="Source data timestamp")
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response generation timestamp (UTC)"
    )


class AuditLogEntry(BaseModel):
    """Audit log record for historical end-of-day appends."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    date: str = Field(..., description="Bar session date YYYY-MM-DD")
    action: str = Field(..., description="INSERT, UPDATE, or NOOP")
    source: str = Field(..., description="Data source (e.g. cse_live_eod, cse_reconcile)")
    aspi: float = Field(..., description="Appended ASPI value")
    sp20: Optional[float] = Field(None, description="Appended S&P SL 20 value")
    turnover_equity_mn: Optional[float] = None
    shares_traded_equity_k: Optional[float] = None
    aspi_log_return: Optional[float] = None
    reconciled: bool = Field(False, description="Whether compared against official history")
    discrepancy: Optional[str] = Field(None, description="Description of any discrepancy found")


class ErrorResponse(BaseModel):
    """Standardized API error response format."""
    detail: str = Field(..., description="Human-readable error description")
    error_code: str = Field("MARKET_ERROR", description="Machine-readable error classification code")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


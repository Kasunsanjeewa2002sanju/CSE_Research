"""Domain models for CSE live market ingestion and telemetry.

Re-exports core contracts from Stage 1 (MarketSnapshot, etc.)
and defines ingestion-specific telemetry models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

# Re-export core Stage 1 and Stage 3 schemas
from cse.market.schema import (
    MarketSnapshot,
    IntradayPoint,
    DailyBar,
    MarketStatus,
    MarketStatusType,
    FreshnessState,
    SourceHealth,
    COLOMBO_TZ,
    MarketLatestResponse,
    IntradaySeriesPoint,
    MarketIntradayResponse,
    MarketHistoryPoint,
    MarketHistoryResponse,
    MarketStatsResponse,
    AuditLogEntry,
    ErrorResponse,
)


class ClockState(str, Enum):
    """Trading session state determined by exchange status and market clock."""
    PRE_OPEN = "PRE_OPEN"                     # 09:00 - 09:30 auction call
    OPEN = "OPEN"                             # 09:30 - 14:30 regular trading
    CLOSED = "CLOSED"                         # Post-close or before pre-open
    HOLIDAY_OR_NO_TRADING = "HOLIDAY"         # Weekend or recognized market holiday


class CircuitState(str, Enum):
    """Circuit breaker operational state."""
    CLOSED = "CLOSED"       # Normal operation; requests pass through
    OPEN = "OPEN"           # Tripped; requests rejected immediately / fallback invoked
    HALF_OPEN = "HALF_OPEN" # Testing recovery with a single probe request


class TickAnomaly(BaseModel):
    """Record of an upstream tick rejected by the validation pipeline."""
    timestamp: datetime = Field(..., description="Timestamp of rejection event")
    reason: str = Field(..., description="Validation failure explanation")
    aspi_value: float = Field(..., description="Rejected ASPI candidate value")
    last_accepted_value: Optional[float] = Field(None, description="Previous accepted ASPI value")
    jump_pct: Optional[float] = Field(None, description="Computed percentage jump if jump check failed")
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Raw unmarshalled payload")


class PollMetrics(BaseModel):
    """Structured telemetry emitted after each ingestion poll cycle."""
    timestamp: datetime = Field(..., description="Poll execution timestamp (UTC)")
    endpoint: str = Field(..., description="Target URL or endpoint path")
    status_code: Optional[int] = Field(None, description="HTTP response code")
    latency_ms: float = Field(..., description="Round-trip latency in milliseconds")
    accepted: bool = Field(..., description="Whether the poll resulted in an accepted snapshot")
    rejection_reason: Optional[str] = Field(None, description="Reason if tick was rejected")
    aspi_value: Optional[float] = Field(None, description="Current ASPI value if available")
    market_status: Optional[str] = Field(None, description="Reported market status string")
    freshness: FreshnessState = Field(..., description="Evaluated freshness state")
    circuit_state: CircuitState = Field(..., description="Current circuit breaker state")


__all__ = [
    "MarketSnapshot",
    "IntradayPoint",
    "DailyBar",
    "MarketStatus",
    "MarketStatusType",
    "FreshnessState",
    "SourceHealth",
    "COLOMBO_TZ",
    "ClockState",
    "CircuitState",
    "TickAnomaly",
    "PollMetrics",
    "MarketLatestResponse",
    "IntradaySeriesPoint",
    "MarketIntradayResponse",
    "MarketHistoryPoint",
    "MarketHistoryResponse",
    "MarketStatsResponse",
    "AuditLogEntry",
    "ErrorResponse",
]

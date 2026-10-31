"""CSE Live Ingestion Service Package.

Provides robust, real-time polling, validation, circuit breaking,
market clock scheduling, and internal pub/sub event broadcasting.
"""

from __future__ import annotations

# Process-wide alias for httpx if httpx2 is present
try:
    import httpx2
    httpx2.alias_httpx()
except Exception:
    pass

from cse_live.config import IngestionConfig
from cse_live.models import (
    MarketSnapshot,
    IntradayPoint,
    DailyBar,
    MarketStatus,
    MarketStatusType,
    FreshnessState,
    SourceHealth,
    ClockState,
    CircuitState,
    TickAnomaly,
    PollMetrics,
    COLOMBO_TZ,
)
from cse_live.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from cse_live.market_clock import MarketClock
from cse_live.parser import CSEDataParser
from cse_live.validator import TickValidator, ValidationResult
from cse_live.events import (
    EventBus,
    default_event_bus,
    EVENT_SNAPSHOT_ACCEPTED,
    EVENT_TICK_REJECTED,
    EVENT_STATUS_CHANGED,
    EVENT_CIRCUIT_STATE_CHANGED,
    EVENT_HEALTH_UPDATED,
)
try:
    from cse_live.client import AsyncCSEClient
except Exception:
    AsyncCSEClient = None

try:
    from cse_live.scheduler import (
        CSEScheduler,
        SingleFlightLock,
        FreshnessStateMachine,
        SnapshotPersistenceStub,
        get_live_scheduler,
    )
except Exception:
    CSEScheduler = None
    SingleFlightLock = None
    SnapshotPersistenceStub = None
    get_live_scheduler = None

try:
    from cse_live.streaming import (
        SSEEvent,
        SSEClient,
        SSEManager,
        get_sse_manager,
    )
except Exception:
    SSEEvent = None
    SSEClient = None
    SSEManager = None
    get_sse_manager = None

__all__ = [
    "IngestionConfig",
    "MarketSnapshot",
    "IntradayPoint",
    "DailyBar",
    "MarketStatus",
    "MarketStatusType",
    "FreshnessState",
    "SourceHealth",
    "ClockState",
    "CircuitState",
    "TickAnomaly",
    "PollMetrics",
    "COLOMBO_TZ",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "MarketClock",
    "CSEDataParser",
    "TickValidator",
    "ValidationResult",
    "EventBus",
    "default_event_bus",
    "EVENT_SNAPSHOT_ACCEPTED",
    "EVENT_TICK_REJECTED",
    "EVENT_STATUS_CHANGED",
    "EVENT_CIRCUIT_STATE_CHANGED",
    "EVENT_HEALTH_UPDATED",
    "AsyncCSEClient",
    "CSEScheduler",
    "SingleFlightLock",
    "FreshnessStateMachine",
    "SnapshotPersistenceStub",
    "get_live_scheduler",
    "SSEEvent",
    "SSEClient",
    "SSEManager",
    "get_sse_manager",
]

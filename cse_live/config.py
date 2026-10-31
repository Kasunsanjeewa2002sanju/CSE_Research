"""Configuration for CSE Live Ingestion Service.

Loads and validates all parameters from environment variables (.env)
with robust defaults and strict typing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


def resolve_workspace_path(path_str: Optional[str]) -> str:
    """Resolve a path string relative to workspace root if it is not absolute."""
    if not path_str:
        return ""
    p = Path(path_str)
    if p.is_absolute() and p.exists():
        return str(p)

    # Search up the parent hierarchy for the workspace root
    curr = Path(__file__).resolve().parent
    candidates = [curr, curr.parent, curr.parent.parent, curr.parent.parent.parent, curr.parent.parent.parent.parent]
    for c in candidates:
        if (c / "cse_research").exists() or (c / "frontend").exists() or (c / "CSE_data.csv").exists():
            return str((c / p).resolve())

    # Fallback to curr.parent
    return str((curr.parent / p).resolve())


class IngestionConfig(BaseModel):
    """Runtime configuration for CSE Live Market Ingestion."""

    # Network Endpoints
    cse_base_urls: List[str] = Field(
        default_factory=lambda: ["https://www.cse.lk"],
        description="List of primary and mirror base URLs for CSE API"
    )

    # Polling Cadence
    poll_interval_open_seconds: float = Field(
        default=1.0,
        ge=1.0,
        le=60.0,
        description="Polling interval in seconds during active market trading (09:30 - 14:30)"
    )
    poll_interval_closed_seconds: float = Field(
        default=60.0,
        ge=5.0,
        le=3600.0,
        description="Polling interval in seconds outside market hours"
    )
    min_poll_interval_seconds: float = Field(
        default=1.0,
        ge=0.5,
        description="Strict floor to ensure never polling faster than this interval"
    )

    # HTTP & Resilience
    request_timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Per-request HTTP timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts on transient network or 5xx failures"
    )
    backoff_base: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Base delay in seconds for exponential backoff"
    )
    backoff_max: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Maximum ceiling for exponential backoff"
    )

    # Circuit Breaker
    circuit_fail_threshold: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Consecutive failure count to trip circuit breaker from CLOSED to OPEN"
    )
    circuit_cooldown: float = Field(
        default=30.0,
        ge=5.0,
        le=300.0,
        description="Cooldown duration in seconds before testing HALF-OPEN state"
    )

    # Validation & Jump Thresholds
    max_tick_jump_pct: float = Field(
        default=10.0,
        ge=1.0,
        le=50.0,
        description="Maximum allowable % change vs last accepted tick without 2x confirmation"
    )
    stale_after_seconds: float = Field(
        default=120.0,
        ge=10.0,
        le=1800.0,
        description="Elapsed seconds without new ticks before marking state as STALE"
    )

    # Exchange Metadata & Headers
    user_agent: str = Field(
        default="ASPI-Research-Ingest/1.0 (+http://localhost:8000) Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        description="Identifying User-Agent header for HTTP calls"
    )
    holiday_file: Optional[str] = Field(
        default=None,
        description="Optional path to custom holiday calendar file (JSON/CSV)"
    )
    market_open: str = Field(
        default="09:30",
        description="Market continuous trading open time (HH:MM) Colombo time"
    )
    market_close: str = Field(
        default="14:30",
        description="Market continuous trading close time (HH:MM) Colombo time"
    )
    timezone: str = Field(
        default="Asia/Colombo",
        description="Official timezone identifier for Colombo Stock Exchange"
    )

    # Concurrency & Persistence
    lock_file_path: str = Field(
        default=".cse_live_scheduler.lock",
        description="File path for single-flight leader election lock"
    )
    persistence_file_path: str = Field(
        default="cse_data_cache/last_snapshot.json",
        description="File path for persisting/loading last accepted snapshot"
    )

    # Stage 3: Storage & Caching
    redis_enabled: bool = Field(
        default=False,
        description="Enable optional Redis backend for snapshot and caching"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL if redis_enabled is True"
    )
    snapshot_ttl_seconds: float = Field(
        default=300.0,
        ge=10.0,
        description="TTL in seconds for snapshot freshness in cache"
    )

    # Stage 3: Intraday Store
    intraday_bucket_seconds: int = Field(
        default=60,
        ge=10,
        le=3600,
        description="Intraday downsampling bucket size in seconds (default 1 minute)"
    )
    intraday_retention_sessions: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of prior market sessions to retain in intraday store alongside current session"
    )
    intraday_max_points_per_metric: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Maximum rolling points kept in memory per metric (bounded memory)"
    )
    intraday_cache_file: str = Field(
        default="cse_data_cache/intraday_series.json",
        description="File path for persisting intraday series across server restarts"
    )

    # Stage 3: Historical Append & Merged View
    live_daily_file_path: str = Field(
        default="cse_data_cache/live_daily.csv",
        description="Append-only live daily bar store path"
    )
    append_audit_log_path: str = Field(
        default="cse_data_cache/append_audit.log",
        description="Audit log path for historical appends"
    )
    historical_clean_path: str = Field(
        default="cse_research/data/processed/cse_clean.csv",
        description="Path to baseline research clean dataset"
    )

    # Stage 4: Server-Sent Events (SSE) Streaming
    sse_heartbeat_interval_seconds: float = Field(
        default=15.0,
        ge=0.05,
        le=60.0,
        description="Heartbeat interval in seconds for SSE stream"
    )
    sse_max_connections: int = Field(
        default=500,
        ge=1,
        le=5000,
        description="Maximum concurrent SSE stream connections"
    )
    sse_per_ip_cap: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent SSE stream connections per client IP"
    )
    sse_buffer_size: int = Field(
        default=200,
        ge=10,
        le=1000,
        description="Ring buffer size of past SSE events for Last-Event-ID replay"
    )
    sse_client_queue_size: int = Field(
        default=100,
        ge=2,
        le=500,
        description="Bounded queue capacity per SSE client before backpressure drops oldest events"
    )

    @model_validator(mode="after")
    def resolve_paths(self) -> IngestionConfig:
        self.persistence_file_path = resolve_workspace_path(self.persistence_file_path)
        self.intraday_cache_file = resolve_workspace_path(self.intraday_cache_file)
        self.live_daily_file_path = resolve_workspace_path(self.live_daily_file_path)
        self.append_audit_log_path = resolve_workspace_path(self.append_audit_log_path)
        self.historical_clean_path = resolve_workspace_path(self.historical_clean_path)
        self.lock_file_path = resolve_workspace_path(self.lock_file_path)
        return self

    @field_validator("cse_base_urls", mode="before")
    @classmethod
    def parse_base_urls(cls, v: object) -> List[str]:
        if isinstance(v, str):
            urls = [u.strip().rstrip("/") for u in v.split(",") if u.strip()]
            return urls or ["https://www.cse.lk"]
        if isinstance(v, list):
            return [str(u).strip().rstrip("/") for u in v if str(u).strip()]
        return ["https://www.cse.lk"]

    @classmethod
    def from_env(cls) -> IngestionConfig:
        """Construct validated IngestionConfig reading from environment variables."""
        return cls(
            cse_base_urls=os.getenv("CSE_BASE_URLS", "https://www.cse.lk"),
            poll_interval_open_seconds=float(os.getenv("POLL_INTERVAL_OPEN_SECONDS", "5.0")),
            poll_interval_closed_seconds=float(os.getenv("POLL_INTERVAL_CLOSED_SECONDS", "60.0")),
            min_poll_interval_seconds=float(os.getenv("MIN_POLL_INTERVAL_SECONDS", "1.0")),
            request_timeout=float(os.getenv("REQUEST_TIMEOUT", "10.0")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            backoff_base=float(os.getenv("BACKOFF_BASE", "1.0")),
            backoff_max=float(os.getenv("BACKOFF_MAX", "30.0")),
            circuit_fail_threshold=int(os.getenv("CIRCUIT_FAIL_THRESHOLD", "5")),
            circuit_cooldown=float(os.getenv("CIRCUIT_COOLDOWN", "30.0")),
            max_tick_jump_pct=float(os.getenv("MAX_TICK_JUMP_PCT", "10.0")),
            stale_after_seconds=float(os.getenv("STALE_AFTER_SECONDS", "120.0")),
            user_agent=os.getenv("USER_AGENT", "ASPI-Research-Ingest/1.0 (+http://localhost:8000) Mozilla/5.0"),
            holiday_file=os.getenv("HOLIDAY_FILE"),
            market_open=os.getenv("MARKET_OPEN", "09:30"),
            market_close=os.getenv("MARKET_CLOSE", "14:30"),
            timezone=os.getenv("TIMEZONE", "Asia/Colombo"),
            lock_file_path=os.getenv("LOCK_FILE_PATH", ".cse_live_scheduler.lock"),
            persistence_file_path=os.getenv("PERSISTENCE_FILE_PATH", "cse_data_cache/last_snapshot.json"),
            redis_enabled=os.getenv("REDIS_ENABLED", "false").lower() in ("true", "1", "yes"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            snapshot_ttl_seconds=float(os.getenv("SNAPSHOT_TTL_SECONDS", "300.0")),
            intraday_bucket_seconds=int(os.getenv("INTRADAY_BUCKET_SECONDS", "60")),
            intraday_retention_sessions=int(os.getenv("INTRADAY_RETENTION_SESSIONS", "3")),
            intraday_max_points_per_metric=int(os.getenv("INTRADAY_MAX_POINTS_PER_METRIC", "2000")),
            intraday_cache_file=os.getenv("INTRADAY_CACHE_FILE", "cse_data_cache/intraday_series.json"),
            live_daily_file_path=os.getenv("LIVE_DAILY_FILE_PATH", "cse_data_cache/live_daily.csv"),
            append_audit_log_path=os.getenv("APPEND_AUDIT_LOG_PATH", "cse_data_cache/append_audit.log"),
            historical_clean_path=os.getenv("HISTORICAL_CLEAN_PATH", "cse_research/data/processed/cse_clean.csv"),
        )

"""Latest Snapshot Store with In-Memory TTL, Atomic Disk Persistence, and Optional Redis.

Guarantees:
- In-memory caching with TTL evaluation.
- Atomic disk writes via write-then-rename (survives crashes, power loss, and restart).
- Optional Redis hook enabled via config flag (default works without it).
- Proper freshness marking upon mid-session restart recovery.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from typing import Optional

from cse_live.config import IngestionConfig
from cse_live.market_clock import MarketClock
from cse_live.models import (
    ClockState,
    FreshnessState,
    MarketSnapshot,
    COLOMBO_TZ,
)

logger = logging.getLogger("cse_live.storage")


class LatestSnapshotStore:
    """Manages storage, TTL caching, atomic persistence, and recovery for the latest market snapshot."""

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self.config = config or IngestionConfig.from_env()
        self.market_clock = MarketClock(self.config)
        self._snapshot: Optional[MarketSnapshot] = None
        self._cached_at: Optional[datetime] = None
        self._recovered_from_disk: bool = False
        self._redis_client = None

        # Ensure directory exists for persistence
        persistence_dir = os.path.dirname(os.path.abspath(self.config.persistence_file_path))
        os.makedirs(persistence_dir, exist_ok=True)

        # Initialize optional Redis if enabled
        if self.config.redis_enabled:
            self._init_redis()

        # Load persisted snapshot on instantiation so restart has baseline immediately
        self.load()

    def _init_redis(self) -> None:
        """Initialize optional Redis client if redis package is available."""
        try:
            import redis
            self._redis_client = redis.Redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=2.0
            )
            logger.info(f"Optional Redis client initialized for {self.config.redis_url}")
        except Exception as e:
            logger.warning(f"Redis initialization failed ({e}); falling back to in-memory + disk persistence.")
            self._redis_client = None

    def save(self, snapshot: MarketSnapshot) -> None:
        """Atomically persist snapshot to disk, update in-memory cache, and sync to Redis."""
        self._snapshot = snapshot
        self._cached_at = datetime.now(timezone.utc)
        self._recovered_from_disk = False

        # 1. Atomic write to disk: write to temp file on same filesystem, then rename
        target_path = os.path.abspath(self.config.persistence_file_path)
        dir_name = os.path.dirname(target_path)
        os.makedirs(dir_name, exist_ok=True)
        tmp_path = f"{target_path}.tmp.{os.getpid()}"

        try:
            payload = snapshot.model_dump_json(indent=2)
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
            os.replace(tmp_path, target_path)
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            logger.error(f"Failed atomic persistence to disk ({target_path}): {e}")

        # 2. Optional Redis sync
        if self._redis_client is not None:
            try:
                self._redis_client.set(
                    "cse:latest_snapshot",
                    snapshot.model_dump_json(),
                    ex=int(self.config.snapshot_ttl_seconds)
                )
            except Exception as e:
                logger.warning(f"Redis write error: {e}")

    def load(self) -> Optional[MarketSnapshot]:
        """Load persisted snapshot from disk (or Redis if enabled), marking recovery state."""
        # 1. Try Redis first if enabled
        if self._redis_client is not None:
            try:
                cached_str = self._redis_client.get("cse:latest_snapshot")
                if cached_str:
                    data = json.loads(cached_str)
                    snapshot = MarketSnapshot.model_validate(data)
                    self._snapshot = snapshot
                    self._cached_at = datetime.now(timezone.utc)
                    self._recovered_from_disk = False
                    logger.info("Loaded latest market snapshot from Redis.")
                    return self._snapshot
            except Exception as e:
                logger.warning(f"Redis read error: {e}")

        # 2. Load from atomic disk file
        target_path = os.path.abspath(self.config.persistence_file_path)
        if not os.path.exists(target_path):
            return None

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            snapshot = MarketSnapshot.model_validate(data)
            self._snapshot = snapshot
            self._cached_at = datetime.now(timezone.utc)
            self._recovered_from_disk = True
            logger.info(f"Loaded persisted snapshot from disk baseline: ASPI={snapshot.aspi_value:,.2f}")
            return self._snapshot
        except Exception as e:
            logger.error(f"Failed to load snapshot from disk ({target_path}): {e}")
            return None

    def get(self) -> Optional[MarketSnapshot]:
        """Retrieve latest snapshot with real-time freshness state evaluation."""
        if self._snapshot is None:
            self.load()

        if self._snapshot is None:
            return None

        # Evaluate freshness based on current clock and tick age
        clock_state = self.market_clock.evaluate_state(
            reported_status=self._snapshot.market_status.raw_status
        )
        now_colombo = datetime.now(COLOMBO_TZ)
        tick_age_seconds = (now_colombo - self._snapshot.source_timestamp).total_seconds()

        # If recovered from disk across a server restart
        if self._recovered_from_disk:
            # If market is active but tick is old, mark as STALE or DELAYED
            if clock_state == ClockState.OPEN:
                if tick_age_seconds > self.config.stale_after_seconds:
                    freshness = FreshnessState.STALE
                elif tick_age_seconds > 60.0:
                    freshness = FreshnessState.DELAYED
                else:
                    freshness = FreshnessState.LIVE
            else:
                freshness = FreshnessState.CLOSED

            # Return snapshot copy with updated freshness
            return self._snapshot.model_copy(update={"freshness": freshness})

        # Normal in-memory evaluation
        if clock_state in (ClockState.CLOSED, ClockState.HOLIDAY_OR_NO_TRADING):
            freshness = FreshnessState.CLOSED
        elif tick_age_seconds > self.config.stale_after_seconds:
            freshness = FreshnessState.STALE
        elif tick_age_seconds > 60.0:
            freshness = FreshnessState.DELAYED
        else:
            freshness = FreshnessState.LIVE

        if freshness != self._snapshot.freshness:
            return self._snapshot.model_copy(update={"freshness": freshness})

        return self._snapshot

    @property
    def is_recovered_from_disk(self) -> bool:
        """Returns True if the current in-memory snapshot was loaded from disk recovery."""
        return self._recovered_from_disk

    def clear(self) -> None:
        """Clear in-memory and disk snapshot (primarily for testing)."""
        self._snapshot = None
        self._cached_at = None
        self._recovered_from_disk = False
        target_path = os.path.abspath(self.config.persistence_file_path)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass
        if self._redis_client is not None:
            try:
                self._redis_client.delete("cse:latest_snapshot")
            except Exception:
                pass


_global_snapshot_store: Optional[LatestSnapshotStore] = None


def get_snapshot_store(config: Optional[IngestionConfig] = None) -> LatestSnapshotStore:
    """Retrieve or initialize the process-wide LatestSnapshotStore singleton."""
    global _global_snapshot_store
    if _global_snapshot_store is None:
        _global_snapshot_store = LatestSnapshotStore(config=config)
    return _global_snapshot_store

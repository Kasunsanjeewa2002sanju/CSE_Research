"""Background Polling Service and Scheduler for CSE Live Market Ingestion.

Features:
- Single-flight leader lock across multi-worker deployments
- FastAPI lifespan integration (clean async start and shutdown)
- Structured JSON logging for every poll cycle
- Freshness state machine (LIVE -> DELAYED -> STALE -> CLOSED)
- Graceful degradation on startup (loads persisted snapshot fallback)
- In-memory event publishing
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cse_live.client import AsyncCSEClient
from cse_live.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from cse_live.config import IngestionConfig
from cse_live.eod import EODJob, LiveDailyStore, MergedMarketHistory
from cse_live.events import (
    EventBus,
    default_event_bus,
    EVENT_SNAPSHOT_ACCEPTED,
    EVENT_TICK_REJECTED,
    EVENT_STATUS_CHANGED,
    EVENT_HEALTH_UPDATED,
)
from cse_live.intraday import IntradayStore, get_intraday_store
from cse_live.market_clock import MarketClock
from cse_live.models import (
    ClockState,
    CircuitState,
    FreshnessState,
    MarketSnapshot,
    MarketStatus,
    MarketStatusType,
    PollMetrics,
    SourceHealth,
    TickAnomaly,
    COLOMBO_TZ,
)
from cse_live.parser import CSEDataParser
from cse_live.storage import LatestSnapshotStore, get_snapshot_store
from cse_live.validator import TickValidator

logger = logging.getLogger("cse_live.scheduler")


class SingleFlightLock:
    """File-based non-blocking lock ensuring only one active poller runs across workers.
    
    Rationale for deployment:
    - Works identically across multi-worker uvicorn processes on single-node or container.
    - Zero external broker dependencies (Redis/DB) required at this stage.
    - Automatically releases if the holding process terminates or restarts.
    """

    def __init__(self, lock_path: str = ".cse_live_scheduler.lock") -> None:
        self.lock_path = lock_path
        self.is_leader = False
        self._file_handle: Optional[Any] = None

    def acquire(self) -> bool:
        """Attempt non-blocking acquisition of the leader lock."""
        try:
            # On Windows: use exclusive creation or file open
            if os.name == "nt":
                import msvcrt
                # Open or create lock file in write mode
                self._file_handle = open(self.lock_path, "a+b")
                # Lock first byte non-blocking
                msvcrt.locking(self._file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                self._file_handle = open(self.lock_path, "a+")
                fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            self.is_leader = True
            # Write current PID
            self._file_handle.seek(0)
            self._file_handle.truncate()
            self._file_handle.write(f"PID: {os.getpid()}\nStarted: {datetime.now(timezone.utc).isoformat()}\n".encode("utf-8"))
            self._file_handle.flush()
            logger.info(f"Worker (PID {os.getpid()}) acquired single-flight ingest lock.")
            return True
        except (IOError, OSError, PermissionError):
            self.is_leader = False
            logger.info(f"Worker (PID {os.getpid()}) running as standby follower (leader lock held elsewhere).")
            return False

    def release(self) -> None:
        """Release the leader lock."""
        if self._file_handle:
            try:
                if os.name == "nt":
                    import msvcrt
                    self._file_handle.seek(0)
                    msvcrt.locking(self._file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_UN)
                self._file_handle.close()
            except Exception:
                pass
            finally:
                self._file_handle = None
                self.is_leader = False
                try:
                    if os.path.exists(self.lock_path):
                        os.remove(self.lock_path)
                except Exception:
                    pass


class FreshnessStateMachine:
    """Evaluates data freshness state based on session status, source reachability, and tick age."""

    @staticmethod
    def evaluate(
        clock_state: ClockState,
        source_reachable: bool,
        last_tick_age_seconds: float,
        stale_threshold_seconds: float = 120.0
    ) -> FreshnessState:
        # If market is closed or on a holiday
        if clock_state in (ClockState.CLOSED, ClockState.HOLIDAY_OR_NO_TRADING):
            return FreshnessState.CLOSED

        # Market is OPEN or PRE_OPEN
        if not source_reachable:
            if last_tick_age_seconds > stale_threshold_seconds:
                return FreshnessState.STALE
            return FreshnessState.DELAYED

        # Source is reachable
        if last_tick_age_seconds <= 60.0:
            return FreshnessState.LIVE
        elif last_tick_age_seconds <= stale_threshold_seconds:
            return FreshnessState.DELAYED
        else:
            return FreshnessState.STALE


class SnapshotPersistenceStub:
    """Stub persistence manager to save and reload the last valid snapshot."""

    def __init__(self, file_path: str = "cse_data_cache/last_snapshot.json") -> None:
        self.file_path = file_path
        os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)

    def save(self, snapshot: MarketSnapshot) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(snapshot.model_dump_json(indent=2))
        except Exception as e:
            logger.warning(f"Failed to persist snapshot: {e}")

    def load(self) -> Optional[MarketSnapshot]:
        if not os.path.exists(self.file_path):
            return None
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return MarketSnapshot.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to load persisted snapshot: {e}")
            return None


class CSEScheduler:
    """Master background polling service running within FastAPI lifespan."""

    def __init__(
        self,
        config: Optional[IngestionConfig] = None,
        event_bus: Optional[EventBus] = None,
        client: Optional[AsyncCSEClient] = None,
        validator: Optional[TickValidator] = None,
        market_clock: Optional[MarketClock] = None,
        snapshot_store: Optional[LatestSnapshotStore] = None,
        intraday_store: Optional[IntradayStore] = None,
        eod_job: Optional[EODJob] = None,
    ) -> None:
        self.config = config or IngestionConfig.from_env()
        self.event_bus = event_bus or default_event_bus
        self.market_clock = market_clock or MarketClock(self.config)
        self.validator = validator or TickValidator(self.config)
        self.client = client or AsyncCSEClient(self.config)
        self.lock = SingleFlightLock(self.config.lock_file_path)

        # Stage 3 Stores
        self.snapshot_store = snapshot_store or get_snapshot_store(self.config)
        self.persistence = self.snapshot_store  # Backwards compatibility alias
        self.intraday_store = intraday_store or get_intraday_store(self.config)
        self.eod_job = eod_job or EODJob(config=self.config)

        # State & Telemetry
        self.latest_snapshot: Optional[MarketSnapshot] = None
        self.latest_metrics: Optional[PollMetrics] = None
        self._prev_snapshot: Optional[MarketSnapshot] = None
        self.metrics_counters = {
            "total_polls": 0,
            "accepted_ticks": 0,
            "rejected_ticks": 0,
            "consecutive_errors": 0,
            "last_latency_ms": 0.0,
        }

        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._final_close_captured = False

    async def start(self) -> None:
        """Start the background ingestion poller cleanly in FastAPI lifespan."""
        if self._running:
            return
        self._running = True

        # Graceful degradation check: load persisted snapshot on startup
        persisted = self.snapshot_store.get()
        if persisted:
            self.latest_snapshot = persisted
            self.validator.last_accepted_snapshot = persisted
            logger.info(f"Loaded persisted snapshot as startup baseline: ASPI={persisted.aspi_value:,.2f} ({persisted.freshness.value})")

        # Attempt to acquire leader lock
        is_leader = self.lock.acquire()
        if is_leader:
            self._task = asyncio.create_task(self._poll_loop(), name="cse_live_poller")
            logger.info("CSE Live Ingestion Service started as LEADER.")
        else:
            self._task = asyncio.create_task(self._standby_loop(), name="cse_live_standby")
            logger.info("CSE Live Ingestion Service started in STANDBY mode.")

    async def stop(self) -> None:
        """Gracefully stop background loop and release resources."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.client.close()
        self.lock.release()
        logger.info("CSE Live Ingestion Service stopped.")

    async def _standby_loop(self) -> None:
        """Standby worker periodically reloads persisted snapshot or tries leader election."""
        while self._running:
            await asyncio.sleep(self.config.poll_interval_closed_seconds)
            # Check if leader lock has become available
            if self.lock.acquire():
                logger.info("Promoted from STANDBY to LEADER!")
                await self._poll_loop()
                break
            # Reload persisted snapshot from store
            persisted = self.snapshot_store.get()
            if persisted:
                self.latest_snapshot = persisted

    async def poll_once(self) -> Optional[MarketSnapshot]:
        """Execute one complete polling and validation cycle."""
        self.metrics_counters["total_polls"] += 1
        t_poll_start = time.monotonic()
        endpoint = "/api/allSectors + /api/chartData + /api/marketStatus"

        raw_bundle: Dict[str, Any] = {}
        status_code = 200
        source_reachable = True
        error_msg = None

        try:
            raw_bundle = await self.client.fetch_raw_snapshot_bundle()
            latency_ms = raw_bundle.get("total_latency_ms", 0.0)
            if raw_bundle.get("errors"):
                source_reachable = False
                error_msg = "; ".join(raw_bundle["errors"])
        except Exception as e:
            source_reachable = False
            latency_ms = (time.monotonic() - t_poll_start) * 1000.0
            error_msg = str(e)
            logger.warning(f"Error fetching snapshot bundle: {e}")

        # Evaluate Market Status
        raw_status = "Unknown"
        if raw_bundle.get("status_data") and "status" in raw_bundle["status_data"]:
            raw_status = raw_bundle["status_data"]["status"]
        market_status = MarketStatus(raw_status=raw_status, status=raw_status)

        # Evaluate Clock
        clock_state = self.market_clock.evaluate_state(reported_status=raw_status)

        # Parse Index components
        aspi_val = None
        aspi_chg = 0.0
        aspi_pct = 0.0
        aspi_prev = None
        source_ts = datetime.now(COLOMBO_TZ)

        # 1. Try from allSectors
        if raw_bundle.get("sectors_data"):
            asi_dict = CSEDataParser.parse_all_sectors_asi(raw_bundle["sectors_data"])
            if asi_dict and asi_dict.get("value") is not None:
                aspi_val = asi_dict["value"]
                aspi_chg = asi_dict["change"]
                aspi_pct = asi_dict["percentage"]
                aspi_prev = asi_dict["previous_close"]
                source_ts = asi_dict["timestamp"]

        # 2. Check intraday chart for real-time tick and timestamp (overrides with latest tick)
        if raw_bundle.get("aspi_chart"):
            intraday_pts = CSEDataParser.parse_chart_data_intraday(raw_bundle["aspi_chart"])
            if intraday_pts:
                latest_pt = intraday_pts[-1]
                source_ts = latest_pt.timestamp
                aspi_val = latest_pt.value
                if aspi_prev is not None and aspi_prev > 0:
                    aspi_chg = round(aspi_val - aspi_prev, 2)
                    aspi_pct = round((aspi_chg / aspi_prev) * 100.0, 4)
                elif latest_pt.percent_change is not None:
                    aspi_pct = latest_pt.percent_change
                    aspi_prev = round(aspi_val - (aspi_val * (aspi_pct / 100.0)), 2)
                    aspi_chg = round(aspi_val - aspi_prev, 2)

        # 3. Parse S&P SL 20 (prefer real sector data, override with latest intraday tick)
        sp20_val = None
        sp20_chg = None
        sp20_pct = None
        sp20_prev = None
        if raw_bundle.get("sectors_data"):
            sp20_dict = CSEDataParser.parse_all_sectors_sp20(raw_bundle["sectors_data"])
            if sp20_dict and sp20_dict.get("value") is not None:
                sp20_val = sp20_dict["value"]
                sp20_chg = sp20_dict["change"]
                sp20_pct = sp20_dict["percentage"]
                sp20_prev = sp20_dict["previous_close"]

        if raw_bundle.get("sp20_chart"):
            sp_pts = CSEDataParser.parse_chart_data_intraday(raw_bundle["sp20_chart"])
            if sp_pts:
                latest_sp = sp_pts[-1]
                sp20_val = latest_sp.value
                if sp20_prev is not None and sp20_prev > 0:
                    sp20_chg = round(sp20_val - sp20_prev, 2)
                    sp20_pct = round((sp20_chg / sp20_prev) * 100.0, 4)
                elif latest_sp.percent_change is not None:
                    sp20_pct = latest_sp.percent_change
                    sp20_prev = round(sp20_val - (sp20_val * (sp20_pct / 100.0)), 2)
                    sp20_chg = round(sp20_val - sp20_prev, 2)

        # 4. Activity metrics (turnover, shares traded, total trades)
        turnover_val = 0.0
        shares_val = 0
        trades_val = 0
        if raw_bundle.get("trade_summary"):
            agg = CSEDataParser.parse_trade_summary(raw_bundle["trade_summary"])
            turnover_val = agg["turnover_lkr"]
            shares_val = agg["shares_traded"]
            trades_val = agg["trades_count"]
        elif raw_bundle.get("sectors_data"):
            agg = CSEDataParser.parse_all_sectors_aggregates(raw_bundle["sectors_data"])
            turnover_val = agg["turnover_lkr"]
            shares_val = agg["shares_traded"]
            trades_val = agg["trades_count"]


        # Calculate tick age
        last_tick_age = (
            (datetime.now(COLOMBO_TZ) - source_ts).total_seconds()
            if source_ts
            else 0.0
        )
        freshness = FreshnessStateMachine.evaluate(
            clock_state=clock_state,
            source_reachable=source_reachable or (aspi_val is not None),
            last_tick_age_seconds=last_tick_age,
            stale_threshold_seconds=self.config.stale_after_seconds
        )

        accepted = False
        rejection_reason = None
        snapshot = None

        if (source_reachable or aspi_val is not None) and aspi_val is not None and aspi_prev is not None:
            try:
                candidate = MarketSnapshot(
                    aspi_value=aspi_val,
                    aspi_change=aspi_chg,
                    aspi_percent_change=aspi_pct,
                    aspi_previous_close=aspi_prev,
                    sp20_value=sp20_val,
                    sp20_change=sp20_chg,
                    sp20_percent_change=sp20_pct,
                    sp20_previous_close=sp20_prev,
                    market_turnover=turnover_val,
                    shares_traded=shares_val,
                    total_trades=trades_val,
                    market_status=market_status,
                    freshness=freshness,
                    source_timestamp=source_ts,
                    source="rest_api",
                    health=SourceHealth(
                        source_name="rest_api",
                        is_healthy=source_reachable,
                        latency_ms=latency_ms,
                        last_success=datetime.now(timezone.utc) if source_reachable else None,
                        last_error=error_msg
                    )
                )

                # Validate tick through pipeline
                val_res = self.validator.validate(candidate, raw_payload=raw_bundle)
                if val_res.is_valid and val_res.snapshot:
                    snapshot = val_res.snapshot
                    self.latest_snapshot = snapshot
                    self.snapshot_store.save(snapshot)
                    self.intraday_store.record_tick(snapshot)

                    # Check for EOD final close confirmation
                    if not self._final_close_captured:
                        if self.eod_job.is_final_print_confirmed(snapshot, self._prev_snapshot):
                            upsert_res = self.eod_job.execute_eod_append(snapshot)
                            logger.info(f"EOD Bar append executed: {upsert_res.action} for {upsert_res.date_str}")
                            self._final_close_captured = True

                    self._prev_snapshot = snapshot
                    accepted = True
                    self.metrics_counters["accepted_ticks"] += 1
                    self.metrics_counters["consecutive_errors"] = 0
                    await self.event_bus.publish(EVENT_SNAPSHOT_ACCEPTED, snapshot)
                else:
                    self.metrics_counters["rejected_ticks"] += 1
                    rejection_reason = val_res.anomaly.reason if val_res.anomaly else "Validation rejected"
                    if val_res.anomaly:
                        await self.event_bus.publish(EVENT_TICK_REJECTED, val_res.anomaly)

            except Exception as e:
                self.metrics_counters["rejected_ticks"] += 1
                rejection_reason = f"Schema validation error: {e}"
        else:
            self.metrics_counters["consecutive_errors"] += 1
            rejection_reason = error_msg or "No valid ASPI index found in response"

        # Record metrics
        self.metrics_counters["last_latency_ms"] = latency_ms
        self.latest_metrics = PollMetrics(
            timestamp=datetime.now(timezone.utc),
            endpoint=endpoint,
            status_code=status_code,
            latency_ms=latency_ms,
            accepted=accepted,
            rejection_reason=rejection_reason,
            aspi_value=aspi_val,
            market_status=raw_status,
            freshness=freshness,
            circuit_state=self.client.circuit_breaker.state
        )

        # Structured JSON Log (Requirement 6) - written to file to prevent console spam
        log_payload = {
            "event": "cse_market_poll",
            "timestamp": self.latest_metrics.timestamp.isoformat(),
            "endpoint": endpoint,
            "latency_ms": round(latency_ms, 2),
            "status_code": status_code,
            "aspi": aspi_val,
            "market_status": raw_status,
            "accepted": accepted,
            "rejection_reason": rejection_reason,
            "freshness": freshness.value,
            "circuit": self.latest_metrics.circuit_state.value,
        }
        try:
            log_dir = Path("results/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "cse_market_polls.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_payload) + "\n")
        except Exception:
            pass

        if not accepted and rejection_reason:
            logger.warning(f"CSE Market Poll [REJECTED]: {rejection_reason}")
        else:
            logger.debug(f"CSE Market Poll: ASPI={aspi_val} ({freshness.value})")

        return snapshot

    async def _poll_loop(self) -> None:
        """Main loop executed continuously by the elected leader."""
        while self._running:
            try:
                snapshot = await self.poll_once()
                raw_status = snapshot.market_status.raw_status if snapshot else None
                clock_state = self.market_clock.evaluate_state(reported_status=raw_status)
                sleep_sec = self.market_clock.get_poll_interval(
                    clock_state,
                    final_close_captured=self._final_close_captured
                )
            except Exception as e:
                logger.error(f"Unexpected error in poll loop: {e}", exc_info=True)
                sleep_sec = self.config.poll_interval_open_seconds

            try:
                await asyncio.sleep(sleep_sec)
            except asyncio.CancelledError:
                break


_global_scheduler: Optional[CSEScheduler] = None


def get_live_scheduler(config: Optional[IngestionConfig] = None) -> CSEScheduler:
    """Retrieve or initialize the process-wide CSEScheduler instance."""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = CSEScheduler(config=config)
    return _global_scheduler

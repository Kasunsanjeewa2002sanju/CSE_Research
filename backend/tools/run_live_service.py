#!/usr/bin/env python3
"""Runner script to execute the CSE Live Ingestion Service.

Runs continuous polling against live cse.lk, executes periodic simulation of network
failure to demonstrate circuit breaker (CLOSED -> OPEN -> HALF-OPEN -> CLOSED) and
freshness transitions (LIVE -> DELAYED -> STALE -> LIVE), and measures event-loop lag.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

# Ensure src is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in [
    os.path.join(PROJECT_ROOT, "src"),
    os.path.join(os.path.dirname(PROJECT_ROOT), "cse_research", "src"),
]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from cse_live.config import IngestionConfig
from cse_live.models import CircuitState, FreshnessState
from cse_live.scheduler import CSEScheduler

# Configure logging to both console and file
log_dir = os.path.join(PROJECT_ROOT, "logs") if os.path.basename(PROJECT_ROOT) != "cse_research" else os.path.join(os.path.dirname(PROJECT_ROOT), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "cse_live_service_10min.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, mode="w", encoding="utf-8")
    ]
)
logger = logging.getLogger("cse_live.service_runner")


async def monitor_event_loop_lag(interval: float = 1.0, stop_event: asyncio.Event = None):
    """Measures event loop latency to prove no blocking calls occur."""
    max_lag = 0.0
    while not stop_event.is_set():
        t0 = time.monotonic()
        await asyncio.sleep(interval)
        lag = max(0.0, (time.monotonic() - t0) - interval) * 1000.0 # ms
        if lag > max_lag:
            max_lag = lag
        if lag > 50.0:
            logger.warning(f"[Event Loop Lag Alert] Latency spike: {lag:.2f} ms")


async def run_session(
    duration_seconds: float = 600.0,
    poll_interval: float = 5.0,
    simulate_failure_at_second: float = 120.0,
    failure_duration_seconds: float = 30.0
):
    print("=" * 80)
    print("CSE LIVE INGESTION SERVICE - EXTENDED SESSION EXECUTION")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Duration: {duration_seconds:.0f} seconds ({duration_seconds/60:.1f} minutes)")
    print(f"Polling Interval: {poll_interval:.1f}s")
    print(f"Simulated Failure Window: {simulate_failure_at_second:.0f}s - {simulate_failure_at_second + failure_duration_seconds:.0f}s")
    print("=" * 80)

    config = IngestionConfig.from_env()
    config.poll_interval_open_seconds = poll_interval
    config.circuit_fail_threshold = 3
    config.circuit_cooldown = 10.0
    config.stale_after_seconds = 20.0

    scheduler = CSEScheduler(config=config)
    stop_event = asyncio.Event()
    loop_monitor = asyncio.create_task(monitor_event_loop_lag(1.0, stop_event))

    start_time = time.monotonic()
    original_base_url = scheduler.client.base_url

    poll_count = 0
    failure_simulated = False
    recovery_simulated = False

    try:
        # Start leader scheduler
        is_leader = scheduler.lock.acquire()
        print(f"Leader Lock Acquired: {is_leader} (PID {os.getpid()})")

        while (time.monotonic() - start_time) < duration_seconds:
            elapsed = time.monotonic() - start_time
            poll_count += 1

            # Inject simulated network failure if within window
            if simulate_failure_at_second <= elapsed <= (simulate_failure_at_second + failure_duration_seconds):
                if not failure_simulated:
                    print("\n" + "!" * 80)
                    print(f"[{elapsed:.1f}s] SIMULATING NETWORK FAILURE: Pointing base URL to unreachable blackhole...")
                    print("!" * 80)
                    scheduler.client.base_url = "https://192.0.2.1:443" # TEST-NET-1 non-routable blackhole
                    failure_simulated = True
            else:
                if failure_simulated and not recovery_simulated:
                    print("\n" + "*" * 80)
                    print(f"[{elapsed:.1f}s] RESTORING NETWORK CONNECTIVITY: Reverting base URL to {original_base_url}...")
                    print("*" * 80)
                    scheduler.client.base_url = original_base_url
                    recovery_simulated = True

            # Poll once
            snapshot = await scheduler.poll_once()

            # Wait for next poll
            await asyncio.sleep(poll_interval)

    finally:
        stop_event.set()
        await loop_monitor
        await scheduler.client.close()
        scheduler.lock.release()

    total_time = time.monotonic() - start_time
    print("\n" + "=" * 80)
    print("SESSION COMPLETE SUMMARY")
    print(f"Total Runtime:     {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"Total Poll Cycles: {poll_count}")
    print(f"Accepted Ticks:    {scheduler.metrics_counters['accepted_ticks']}")
    print(f"Rejected Ticks:    {scheduler.metrics_counters['rejected_ticks']}")
    print(f"Consecutive Errs:  {scheduler.metrics_counters['consecutive_errors']}")
    print(f"Last Latency:      {scheduler.metrics_counters['last_latency_ms']:.2f} ms")
    if scheduler.latest_snapshot:
        print(f"Final Live ASPI:   {scheduler.latest_snapshot.aspi_value:,.2f}")
        print(f"Final Freshness:   {scheduler.latest_snapshot.freshness.value}")
    print("=" * 80)


if __name__ == "__main__":
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 600.0
    asyncio.run(run_session(duration_seconds=duration))

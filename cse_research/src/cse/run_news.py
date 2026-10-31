"""
CLI Runner for Stage 12 Live Sri Lankan News Ingestion & Scenario Evaluation.

Usage:
    # Immediate one-shot crawl across verified RSS and API feeds:
    python -m cse.run_news --poll-now

    # Launch continuous polling daemon (polls every 30 minutes):
    python -m cse.run_news --interval-mins 30

    # Run once for the last 24 hours:
    python -m cse.run_news --since 24h --out results/predictions/news_*.csv

    # Health check mode (verify all feeds and save feed status table):
    python -m cse.run_news --health-check

    # With explicit latest ASPI level override:
    python -m cse.run_news --since 24h --aspi 12850.50

    # Scheduled mode (run every 30 minutes via APScheduler):
    python -m cse.run_news --since 24h --schedule "interval:30m"
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def ensure_virtualenv() -> None:
    """Ensure script is running inside the project's virtual environment."""
    file_path = Path(__file__).resolve()
    venv_dir = None
    project_root = None
    for parent in [file_path.parent, *file_path.parents]:
        cand = parent / ".venv"
        if cand.exists() and cand.is_dir():
            venv_dir = cand
            project_root = parent
            break

    if venv_dir:
        if sys.platform == "win32":
            venv_python = venv_dir / "Scripts" / "python.exe"
        else:
            venv_python = venv_dir / "bin" / "python"

        if venv_python.exists():
            try:
                current_exe = Path(sys.executable).resolve()
                target_exe = venv_python.resolve()
                if current_exe != target_exe:
                    print(f"[ENV] Switching to virtual environment Python: {target_exe}")
                    env = os.environ.copy()
                    src_dir = str(project_root / "src")
                    root_dir = str(project_root)
                    paths = [src_dir, root_dir]
                    existing_pythonpath = env.get("PYTHONPATH", "")
                    if existing_pythonpath:
                        paths.append(existing_pythonpath)
                    env["PYTHONPATH"] = os.pathsep.join(paths)

                    cmd = [str(target_exe), "-m", "cse.run_news"] + sys.argv[1:]
                    result = subprocess.run(cmd, env=env)
                    sys.exit(result.returncode)
            except Exception as e:
                print(f"[ENV WARNING] Could not verify virtualenv transition: {e}")

    # Set up PYTHONPATH for current process
    if project_root:
        src_dir = str(project_root / "src")
        root_dir = str(project_root)
        for p in [src_dir, root_dir]:
            if p not in sys.path:
                sys.path.insert(0, p)
        existing = os.environ.get("PYTHONPATH", "")
        if existing:
            os.environ["PYTHONPATH"] = os.pathsep.join([src_dir, root_dir, existing])
        else:
            os.environ["PYTHONPATH"] = os.pathsep.join([src_dir, root_dir])


ensure_virtualenv()

from cse.news.pipeline import NewsPipeline
from cse.utils.config import find_project_root
from cse.utils.logger import get_logger, setup_logger

logger = get_logger("cse.run_news")


def setup_cli_logging() -> None:
    """Initialize console and file logger for Stage 12 run."""
    root = find_project_root()
    log_dir = root / "results" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "news_ingest.log"
    setup_logger(name="cse.run_news", log_file=str(log_file))
    setup_logger(name="cse.news", log_file=str(log_file))


def run_scheduled_loop(
    pipeline: NewsPipeline,
    schedule_arg: str,
    since: str,
    out_path: Optional[str],
    aspi_override: Optional[float],
) -> None:
    """Run pipeline repeatedly using APScheduler or interval loop."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BlockingScheduler()
        s_lower = schedule_arg.strip().lower()

        if s_lower.startswith("interval:"):
            interval_str = s_lower.split(":", 1)[1]
            m = re.match(r"^(\d+)([mhd])$", interval_str)
            if m:
                val = int(m.group(1))
                unit = m.group(2)
                kw = {"minutes": val} if unit == "m" else ({"hours": val} if unit == "h" else {"days": val})
                trigger = IntervalTrigger(**kw)
            else:
                trigger = IntervalTrigger(minutes=30)
        elif s_lower.startswith("cron:"):
            cron_expr = schedule_arg.split(":", 1)[1].strip()
            parts = cron_expr.split()
            if len(parts) == 5:
                trigger = CronTrigger(
                    minute=parts[0], hour=parts[1], day=parts[2], month=parts[3], day_of_week=parts[4]
                )
            else:
                trigger = IntervalTrigger(hours=1)
        else:
            trigger = IntervalTrigger(minutes=30)

        def job_wrapper():
            logger.info("Executing scheduled news ingestion run...")
            try:
                pipeline.run(
                    since=since,
                    out_predictions_path=Path(out_path) if out_path else None,
                    current_aspi_override=aspi_override,
                )
            except Exception as e:
                logger.error(f"Scheduled run encountered error: {e}", exc_info=True)

        scheduler.add_job(job_wrapper, trigger=trigger, id="news_pipeline_job")
        print(f"\n[Scheduler] Started scheduled news ingestion with trigger: {trigger}")
        print("[Scheduler] Press Ctrl+C to terminate.")
        # Execute immediately on start
        job_wrapper()
        scheduler.start()

    except ImportError:
        logger.warning("APScheduler not installed. Falling back to sleep interval loop.")
        while True:
            try:
                pipeline.run(
                    since=since,
                    out_predictions_path=Path(out_path) if out_path else None,
                    current_aspi_override=aspi_override,
                )
                time.sleep(1800)  # 30 min
            except KeyboardInterrupt:
                print("\nScheduler stopped by user.")
                break


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CSE Research Stage 12: Live Sri Lankan News Ingestion & Scenario Evaluation CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--since",
        type=str,
        default="24h",
        help="Lookback window for news publication date (e.g. '24h', '48h', '7d').",
    )
    parser.add_argument(
        "--poll-now",
        action="store_true",
        help="Immediate one-shot crawl across verified RSS and API feeds.",
    )
    parser.add_argument(
        "--interval-mins",
        type=int,
        default=None,
        help="Launch continuous polling daemon with specified interval in minutes (e.g. 30).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="results/predictions/news_*.csv",
        help="Output path template for per-run summary file.",
    )
    parser.add_argument(
        "--feeds-config",
        type=str,
        default=None,
        help="Optional custom path to feeds.yaml.",
    )
    parser.add_argument(
        "--storage-path",
        type=str,
        default=None,
        help="Optional custom path to results/tables/news_ingested.csv.",
    )
    parser.add_argument(
        "--aspi",
        type=float,
        default=None,
        help="Explicit latest live ASPI level override (required if news date > 2025-12-31).",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Execute live HTTP & parse verification of all feeds and update feed_status.csv without running full ingestion.",
    )
    parser.add_argument(
        "--schedule",
        type=str,
        default=None,
        help="Schedule periodic execution (e.g. 'interval:30m', 'interval:1h', 'cron:0 * * * *').",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ingest and evaluate without saving rows to news_ingested.csv.",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Optional explicit API key override for NewsData or GNews.",
    )

    args = parser.parse_args()
    setup_cli_logging()

    if args.interval_mins is not None and not args.schedule:
        args.schedule = f"interval:{args.interval_mins}m"

    if args.api_key:
        os.environ["NEWSDATA_API_KEY"] = args.api_key

    root = find_project_root()
    cfg_path = Path(args.feeds_config) if args.feeds_config else (root / "config" / "feeds.yaml")
    storage_path = Path(args.storage_path) if args.storage_path else (root / "results" / "tables" / "news_ingested.csv")

    try:
        pipeline = NewsPipeline(config_path=cfg_path, storage_path=storage_path)
    except Exception as e:
        logger.error(f"Failed to initialize NewsPipeline: {e}", exc_info=True)
        print(f"Error initializing pipeline: {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Health check only mode
    if args.health_check:
        print("\n--- Running Live Feed Discovery & Verification Probe (Rule R11) ---")
        results = pipeline.run_health_check()
        print(f"\nCompleted verification for {len(results)} candidate feeds:")
        for r in results:
            status_symbol = "✅" if r.is_active else "❌"
            print(
                f"  {status_symbol} [{r.feed_type:10}] {r.feed_name:30} | "
                f"Status: {r.status_code:3} | Entries: {r.entry_count:3} | "
                f"Latency: {r.response_time_sec:0.2f}s | {r.error_message or 'OK'}"
            )
        print(f"\nFeed status saved to: {root / 'results' / 'tables' / 'feed_status.csv'}\n")
        sys.exit(0)

    # 2. Scheduled mode
    if args.schedule:
        run_scheduled_loop(
            pipeline=pipeline,
            schedule_arg=args.schedule,
            since=args.since,
            out_path=args.out,
            aspi_override=args.aspi,
        )
        sys.exit(0)

    # 3. Single execution mode
    print(f"\n--- Executing Live Sri Lankan News Ingestion Pipeline (Since: {args.since}) ---")
    out_target = Path(args.out) if args.out else None
    summary = pipeline.run(
        since=args.since,
        out_predictions_path=out_target,
        current_aspi_override=args.aspi,
        dry_run=args.dry_run,
    )

    print("\n--- Pipeline Execution Summary ---")
    for k, v in summary.items():
        print(f"  {k:24}: {v}")
    print()

    if summary.get("status") == "FAILED_ALL_FEEDS":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

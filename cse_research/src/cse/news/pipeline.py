"""
Stage 12 News Pipeline Orchestrator.

Integrates:
- Live RSS / API Ingestion (feedparser, ETag, timeouts, backoff)
- Pre-filtering, Language Detection & Fuzzy Deduplication
- Stage 10 Event Classification & Semantic Structuring
- Stage 11 Counterfactual Scenario Forecasting (TRUE vs FALSE, Conformal Intervals, Evidence)
- Flat CSV Storage at results/tables/news_ingested.csv (append-only)
- Per-run predictions export at results/predictions/news_<timestamp>.csv
- Feed health check status at results/tables/feed_status.csv
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import yaml

from cse.news.api_client import NewsApiClient
from cse.news.feed_verifier import FeedStatusResult, verify_feed, write_feed_status_table
from cse.news.ingest import (
    COLOMBO_TZ,
    NewsFeedIngester,
    canonicalize_url,
    check_prefilter_relevance,
    detect_language,
    parse_publication_date_to_colombo,
)
from cse.news.schema import ElectionStage, EventCategory, ExpectedDirection, NewsExtraction
from cse.news.storage import STORAGE_COLUMNS, NewsStorage
from cse.scenario.engine import ScenarioEngine, get_scenario_engine
from cse.utils.config import find_project_root

logger = logging.getLogger("cse.news.pipeline")


def parse_since_window(since_str: str) -> timedelta:
    """Parse time window string (e.g. '24h', '48h', '7d', '30m') into timedelta."""
    s = since_str.strip().lower()
    m = re.match(r"^(\d+)([hdm])$", s)
    if not m:
        logger.warning(f"Unrecognized since format '{since_str}'. Defaulting to 24 hours.")
        return timedelta(hours=24)
    val = int(m.group(1))
    unit = m.group(2)
    if unit == "h":
        return timedelta(hours=val)
    elif unit == "d":
        return timedelta(days=val)
    elif unit == "m":
        return timedelta(minutes=val)
    return timedelta(hours=24)


class NewsPipeline:
    """End-to-end live news ingestion and scenario evaluation pipeline."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        storage_path: Optional[Path] = None,
        scenario_engine: Optional[ScenarioEngine] = None,
    ) -> None:
        self.root = find_project_root()
        self.config_path = config_path or (self.root / "config" / "feeds.yaml")
        self.storage_path = storage_path or (self.root / "results" / "tables" / "news_ingested.csv")
        
        # Load configuration
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        ingest_cfg = self.config.get("ingestion", {})
        timeout = float(ingest_cfg.get("timeout_sec", 8.0))
        user_agent = ingest_cfg.get("user_agent")

        self.ingester = NewsFeedIngester(timeout=timeout, user_agent=user_agent)
        self.storage = NewsStorage(storage_path=self.storage_path)
        
        # News API client
        api_cfg = self.config.get("news_api", {})
        self.api_client = NewsApiClient(
            provider=api_cfg.get("provider", "newsdata"),
            timeout=timeout,
        )

        # Scenario Engine
        self.scenario_engine = scenario_engine or get_scenario_engine()

    def run_health_check(self, output_csv_path: Optional[Path] = None) -> List[FeedStatusResult]:
        """
        Verify all candidate feeds and query feeds live; write status table.
        """
        out_path = output_csv_path or (self.root / "results" / "tables" / "feed_status.csv")
        results: List[FeedStatusResult] = []

        # 1. Verified active feeds
        for f in self.config.get("verified_active_feeds", []):
            logger.info(f"Health check: verifying active feed '{f['name']}'...")
            res = verify_feed(
                feed_name=f["name"],
                url=f["url"],
                feed_type=f.get("feed_type", "rss"),
                timeout=float(self.config.get("ingestion", {}).get("timeout_sec", 8.0)),
            )
            results.append(res)

        # 2. Query feeds
        for f in self.config.get("query_feeds", []):
            logger.info(f"Health check: verifying query feed '{f['name']}'...")
            res = verify_feed(
                feed_name=f["name"],
                url=f["url"],
                feed_type=f.get("feed_type", "query_rss"),
                timeout=float(self.config.get("ingestion", {}).get("timeout_sec", 8.0)),
            )
            results.append(res)

        # 3. Inactive candidate feeds
        for f in self.config.get("inactive_candidate_feeds", []):
            logger.info(f"Health check: probing candidate feed '{f['name']}'...")
            res = verify_feed(
                feed_name=f["name"],
                url=f["url"],
                feed_type=f.get("feed_type", "rss"),
                timeout=float(self.config.get("ingestion", {}).get("timeout_sec", 8.0)),
            )
            results.append(res)

        write_feed_status_table(results, out_path)
        return results

    def run(
        self,
        since: str = "24h",
        out_predictions_path: Optional[Path] = None,
        current_aspi_override: Optional[float] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute full ingestion, classification, scenario evaluation, and storage.
        """
        now_colombo = datetime.now(COLOMBO_TZ)
        now_utc = datetime.now(timezone.utc).isoformat()
        window = parse_since_window(since)
        cutoff_dt = now_colombo - window

        logger.info(f"[Pipeline] Starting live news run. Since: {since} (cutoff: {cutoff_dt.isoformat()})")

        raw_items: List[Dict[str, Any]] = []

        # 1. Ingest verified active feeds
        active_feeds = self.config.get("verified_active_feeds", [])
        for f in active_feeds:
            items = self.ingester.fetch_feed(feed_name=f["name"], feed_url=f["url"])
            raw_items.extend(items)

        # 2. Ingest query feeds
        query_feeds = self.config.get("query_feeds", [])
        for f in query_feeds:
            items = self.ingester.fetch_feed(feed_name=f["name"], feed_url=f["url"])
            raw_items.extend(items)

        # 3. Ingest from News API (if enabled & configured)
        if self.config.get("news_api", {}).get("enabled", True):
            api_items = self.api_client.fetch_news(query="Sri Lanka")
            for item in api_items:
                raw_items.append({
                    "headline": item["headline"],
                    "url": item["url"],
                    "description": item["description"],
                    "raw_date": item["publication_date"],
                    "parsed_time": None,
                    "source": item["source"],
                })

        total_fetched = len(raw_items)
        logger.info(f"[Pipeline] Total raw news items collected across sources: {total_fetched}")

        # Check for catastrophic feed failure
        if total_fetched == 0:
            msg = "CRITICAL: All configured feeds failed to return news items. Check internet connectivity or feed status."
            logger.error(msg)
            print(f"\n⚠️  {msg}\n")
            return {
                "status": "FAILED_ALL_FEEDS",
                "total_fetched": 0,
                "total_raw_fetched": 0,
                "processed_count": 0,
                "error": msg,
            }


        # Counters
        non_english_skipped = 0
        duplicates_skipped = 0
        outside_window_skipped = 0
        relevant_count = 0
        irrelevant_count = 0
        appended_count = 0
        updated_count = 0

        processed_rows: List[Dict[str, Any]] = []

        for item in raw_items:
            headline = str(item.get("headline", "")).strip()
            desc = str(item.get("description", "")).strip()
            url = canonicalize_url(str(item.get("url", "")))
            source = str(item.get("source", "Unknown"))

            if not headline:
                continue

            # Deterministic Item ID
            item_id = hashlib.sha256(f"{url}|{headline}".encode("utf-8")).hexdigest()[:16]

            # Language Detection
            lang = detect_language(f"{headline} {desc}")
            if lang != "en":
                non_english_skipped += 1
                logger.debug(f"Skipping non-English ({lang}) item: {headline[:40]}")
                continue

            # Publication Date Normalisation (Asia/Colombo)
            pub_date_iso = parse_publication_date_to_colombo(
                raw_date=item.get("raw_date"),
                parsed_time=item.get("parsed_time"),
            )

            # Window check
            try:
                item_dt = datetime.fromisoformat(pub_date_iso)
                if item_dt < cutoff_dt:
                    outside_window_skipped += 1
                    continue
            except Exception:
                pass

            # Deduplication Check
            is_dup, dup_reason = self.storage.is_duplicate(
                canonical_url=url,
                headline=headline,
                similarity_threshold=float(self.config.get("ingestion", {}).get("dedup_similarity_threshold", 0.85)),
            )
            if is_dup:
                duplicates_skipped += 1
                logger.debug(f"Skipping duplicate ({dup_reason}): {headline[:40]}")
                continue

            # Relevance Pre-filter
            is_prefilter_rel = check_prefilter_relevance(headline, desc)

            # Stage 10 extraction & Stage 11 scenario engine
            if not is_prefilter_rel:
                # Fast-path for clearly irrelevant items (e.g. local crime, sports)
                irrelevant_count += 1
                extraction_override = NewsExtraction(
                    is_relevant=False,
                    event_category=EventCategory.NOT_RELEVANT.value,
                    stage=ElectionStage.NONE.value,
                    expected_direction=ExpectedDirection.NEUTRAL.value,
                    expected_direction_reason="Article content has negligible macroeconomic relevance to Colombo equities.",
                    affected_sectors=[],
                    entities=[],
                    confidence=1.0,
                    language="en",
                )
                scenario_res = self.scenario_engine.run(
                    headline=headline,
                    description=desc,
                    publication_date=pub_date_iso[:10],
                    source=source,
                    current_aspi=current_aspi_override,
                    extraction_override=extraction_override,
                )

            else:
                relevant_count += 1
                scenario_res = self.scenario_engine.run(
                    headline=headline,
                    description=desc,
                    publication_date=pub_date_iso[:10],
                    source=source,
                    current_aspi=current_aspi_override,
                )

            # Extract fields matching exact STORAGE_COLUMNS schema
            ext = scenario_res["extraction"]
            scen_true = scenario_res["scenarios"]["TRUE"]["horizons"]
            scen_false = scenario_res["scenarios"]["FALSE"]["horizons"]
            impact = scenario_res["impact"]["horizons"]
            evidence = scenario_res["historical_evidence"]
            is_stale = scenario_res["market_context"]["is_stale"]

            notes_val = "STALE_DATE" if is_stale else ("IRRELEVANT" if not ext["is_relevant"] else "")

            row_dict: Dict[str, Any] = {
                "item_id": item_id,
                "url": url,
                "headline": headline,
                "description": desc,
                "publication_date": pub_date_iso,
                "source": source,
                "language": lang,
                "fetched_at": now_utc,
                "event_category": ext["event_category"],
                "stage": ext["stage"],
                "expected_direction": ext["expected_direction"],
                "confidence": ext["confidence"],
                "entities": json.dumps(ext["entities"]),
                "affected_sectors": json.dumps(ext["affected_sectors"]),
                "is_relevant": ext["is_relevant"],
                # Evidence
                "evidence_strength": evidence.get("evidence_strength", "weak"),
                "evidence_n": evidence.get("n_events", 0),
                "evidence_mean_car": evidence.get("mean_car", 0.0),
                "processed": True,
                "notes": notes_val,
            }

            # Populate horizons 1, 2, 5, 10
            for h in [1, 2, 5, 10]:
                h_str = str(h)
                ht = scen_true.get(h_str, {})
                hf = scen_false.get(h_str, {})
                hi = impact.get(h_str, {})

                row_dict[f"if_true_aspi_h{h}"] = ht.get("expected_aspi_level", 0.0)
                row_dict[f"if_false_aspi_h{h}"] = hf.get("expected_aspi_level", 0.0)
                row_dict[f"diff_h{h}"] = hi.get("diff_aspi_level", 0.0)
                row_dict[f"trend_h{h}"] = ht.get("trend_direction", "neutral")
                row_dict[f"prob_up_h{h}"] = ht.get("prob_up", 0.5)
                row_dict[f"interval_80_lo_h{h}"] = ht.get("interval_80", {}).get("aspi_lower", 0.0)
                row_dict[f"interval_80_hi_h{h}"] = ht.get("interval_80", {}).get("aspi_upper", 0.0)
                row_dict[f"interval_95_lo_h{h}"] = ht.get("interval_95", {}).get("aspi_lower", 0.0)
                row_dict[f"interval_95_hi_h{h}"] = ht.get("interval_95", {}).get("aspi_upper", 0.0)

            # Save to storage (append-only)
            if not dry_run:
                saved, action = self.storage.append_or_update_item(row_dict)
                if action == "APPENDED":
                    appended_count += 1
                elif action == "UPDATED":
                    updated_count += 1
            else:
                appended_count += 1

            processed_rows.append(row_dict)

        # Write per-run summary to results/predictions/news_<timestamp>.csv
        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if out_predictions_path:
            run_out_path = Path(out_predictions_path)
            # Support wildcard expansion or directory/file
            if "*" in str(run_out_path):
                run_out_path = Path(str(run_out_path).replace("*", ts_str))
        else:
            run_out_path = self.root / "results" / "predictions" / f"news_{ts_str}.csv"

        run_out_path.parent.mkdir(parents=True, exist_ok=True)
        if not dry_run:
            with open(run_out_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=STORAGE_COLUMNS)
                writer.writeheader()
                for r in processed_rows:
                    writer.writerow(r)
            logger.info(f"[Pipeline] Saved per-run summary ({len(processed_rows)} rows) to {run_out_path}")

        # Update feed status table
        self.run_health_check()

        summary: Dict[str, Any] = {
            "status": "SUCCESS",
            "timestamp_utc": now_utc,
            "total_raw_fetched": total_fetched,
            "non_english_skipped": non_english_skipped,
            "duplicates_skipped": duplicates_skipped,
            "outside_window_skipped": outside_window_skipped,
            "total_processed": len(processed_rows),
            "relevant_count": relevant_count,
            "irrelevant_count": irrelevant_count,
            "appended_to_storage": appended_count,
            "updated_in_storage": updated_count,
            "per_run_output_file": str(run_out_path),
            "master_storage_file": str(self.storage_path),
        }
        logger.info(f"[Pipeline] Run completed: {summary}")
        return summary

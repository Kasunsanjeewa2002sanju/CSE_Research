"""
Unit Tests for Stage 12 Live News Ingestion, Verification, and Scenario Pipeline.

Tests:
- URL canonicalisation and tracking parameter removal
- Language detection (English vs Sinhala vs Tamil)
- Timezone normalisation to Asia/Colombo ISO 8601
- Fuzzy title deduplication (>0.85 threshold)
- Storage append-only invariant, duplicate protection, and update-on-missing-Stage11
- Offline fixture parsing (no network required)
- Catastrophic feed failure handling and health check
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import feedparser
import pytest

from cse.news.feed_verifier import FeedStatusResult, verify_feed
from cse.news.ingest import (
    COLOMBO_TZ,
    NewsFeedIngester,
    canonicalize_url,
    check_prefilter_relevance,
    detect_language,
    parse_publication_date_to_colombo,
)
from cse.news.pipeline import NewsPipeline, parse_since_window
from cse.news.storage import (
    STORAGE_COLUMNS,
    NewsStorage,
    compute_title_similarity,
    normalize_title,
)
from cse.utils.config import find_project_root

FIXTURES_DIR = find_project_root() / "tests" / "fixtures"


# ---------------------------------------------------------------------------
# 1. URL Canonicalisation Tests
# ---------------------------------------------------------------------------

def test_canonicalize_url_strips_tracking_params():
    raw_url = "https://www.adaderana.lk/news.php?nid=12345&utm_source=twitter&utm_medium=social&utm_campaign=breaking#top"
    clean = canonicalize_url(raw_url)
    assert clean == "https://www.adaderana.lk/news.php?nid=12345"
    assert "utm_source" not in clean
    assert "#top" not in clean


def test_canonicalize_url_normalizes_case_and_trailing_slash():
    raw_url = "HTTP://ISLAND.LK/category/business/article-101/"
    clean = canonicalize_url(raw_url)
    assert clean == "http://island.lk/category/business/article-101"


# ---------------------------------------------------------------------------
# 2. Language Detection Tests
# ---------------------------------------------------------------------------

def test_detect_language_english():
    text = "Central Bank maintains policy interest rates steady at 8.25 percent."
    assert detect_language(text) == "en"


def test_detect_language_sinhala():
    text = "පාර්ලිමේන්තුව විසුරුවා හැරීමේ ගැසට් නිවේදනය නිකුත් කෙරේ"
    assert detect_language(text) == "si"


def test_detect_language_tamil():
    text = "பாராளுமன்றம் கலைக்கப்படுவதற்கான வர்த்தமானி அறிவித்தல் வெளியானது"
    assert detect_language(text) == "ta"


# ---------------------------------------------------------------------------
# 3. Timezone Normalisation to Asia/Colombo Tests
# ---------------------------------------------------------------------------

def test_parse_publication_date_from_utc_rfc():
    # 05:30 UTC -> 11:00 in Asia/Colombo (+05:30)
    rfc_date = "Tue, 13 Oct 2026 05:30:00 +0000"
    colombo_iso = parse_publication_date_to_colombo(raw_date=rfc_date)
    assert "+05:30" in colombo_iso
    assert "2026-10-13T11:00:00+05:30" in colombo_iso


def test_parse_publication_date_missing_falls_back_to_current_colombo():
    colombo_iso = parse_publication_date_to_colombo(raw_date=None, parsed_time=None)
    assert "+05:30" in colombo_iso
    dt = datetime.fromisoformat(colombo_iso)
    assert dt.tzinfo is not None


# ---------------------------------------------------------------------------
# 4. Fuzzy Title Similarity Tests
# ---------------------------------------------------------------------------

def test_fuzzy_title_similarity():
    t1 = "President dissolves parliament ahead of general elections"
    t2 = "President Dissolves Parliament Ahead of General Election!"
    sim = compute_title_similarity(t1, t2)
    assert sim > 0.90

    t3 = "Sri Lanka national cricket team wins match against Australia"
    assert compute_title_similarity(t1, t3) < 0.40


# ---------------------------------------------------------------------------
# 5. Relevance Pre-filter Tests
# ---------------------------------------------------------------------------

def test_relevance_prefilter_political_macro():
    assert check_prefilter_relevance("Parliament passes 2025 budget bill", "Fiscal reforms enacted.") is True
    assert check_prefilter_relevance("CBSL announces monetary policy review", "Interest rates adjusted.") is True
    assert check_prefilter_relevance("Colombo Stock Exchange ASPI surges 120 points", "Turnover high.") is True


def test_relevance_prefilter_irrelevant():
    assert check_prefilter_relevance("Heavy rain and localized flooding in Galle district", "Met department weather report.") is False
    assert check_prefilter_relevance("Local football club wins championship cup", "Sports division results.") is False


# ---------------------------------------------------------------------------
# 6. Flat CSV Storage & Append-Only Invariant Tests
# ---------------------------------------------------------------------------

def test_storage_schema_and_deduplication(tmp_path: Path):
    csv_file = tmp_path / "test_news.csv"
    storage = NewsStorage(storage_path=csv_file)

    sample_row = {
        "item_id": "test_001",
        "url": "https://island.lk/news/sample-1",
        "headline": "CBSL Governor addresses financial summit",
        "description": "Monetary policy update.",
        "publication_date": "2026-10-13T12:00:00+05:30",
        "source": "The Island",
        "language": "en",
        "fetched_at": "2026-10-13T06:30:00Z",
        "event_category": "central_bank_or_monetary_policy",
        "stage": "none",
        "expected_direction": "positive",
        "confidence": 0.8,
        "entities": '["CBSL"]',
        "affected_sectors": '["Banking"]',
        "is_relevant": True,
        "if_true_aspi_h1": 12500.0,
        "if_false_aspi_h1": 12490.0,
        "diff_h1": 10.0,
        "trend_h1": "positive",
        "prob_up_h1": 0.65,
        "interval_80_lo_h1": 12450.0,
        "interval_80_hi_h1": 12550.0,
        "interval_95_lo_h1": 12400.0,
        "interval_95_hi_h1": 12600.0,
        "if_true_aspi_h2": 12510.0,
        "if_false_aspi_h2": 12495.0,
        "diff_h2": 15.0,
        "trend_h2": "positive",
        "prob_up_h2": 0.64,
        "interval_80_lo_h2": 12440.0,
        "interval_80_hi_h2": 12560.0,
        "interval_95_lo_h2": 12380.0,
        "interval_95_hi_h2": 12620.0,
        "if_true_aspi_h5": 12530.0,
        "if_false_aspi_h5": 12500.0,
        "diff_h5": 30.0,
        "trend_h5": "positive",
        "prob_up_h5": 0.62,
        "interval_80_lo_h5": 12400.0,
        "interval_80_hi_h5": 12600.0,
        "interval_95_lo_h5": 12350.0,
        "interval_95_hi_h5": 12680.0,
        "if_true_aspi_h10": 12550.0,
        "if_false_aspi_h10": 12500.0,
        "diff_h10": 50.0,
        "trend_h10": "positive",
        "prob_up_h10": 0.60,
        "interval_80_lo_h10": 12380.0,
        "interval_80_hi_h10": 12650.0,
        "interval_95_lo_h10": 12300.0,
        "interval_95_hi_h10": 12750.0,
        "evidence_strength": "moderate",
        "evidence_n": 8,
        "evidence_mean_car": 0.015,
        "processed": True,
        "notes": "",
    }

    # 1. First append succeeds
    saved, action = storage.append_or_update_item(sample_row)
    assert saved is True
    assert action == "APPENDED"

    # 2. Duplicate URL is rejected
    dup_saved, dup_action = storage.append_or_update_item(sample_row)
    assert dup_saved is False
    assert "DUPLICATE" in dup_action

    # 3. Fuzzy headline duplicate with different URL is rejected
    similar_row = dict(sample_row)
    similar_row["url"] = "https://island.lk/news/sample-1-mirror"
    similar_row["headline"] = "CBSL Governor Addresses Financial Summit!"
    fuzz_saved, fuzz_action = storage.append_or_update_item(similar_row)
    assert fuzz_saved is False
    assert "DUPLICATE" in fuzz_action

    # 4. Verify CSV on disk has exactly STORAGE_COLUMNS
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == STORAGE_COLUMNS
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["item_id"] == "test_001"


# ---------------------------------------------------------------------------
# 7. Recorded Fixture Parsing Tests (No Network Needed)
# ---------------------------------------------------------------------------

def test_parse_recorded_fixture_ada_derana():
    fixture_path = FIXTURES_DIR / "sample_ada_derana.xml"
    content = fixture_path.read_bytes()
    parsed = feedparser.parse(content)
    assert len(parsed.entries) == 2
    assert "Supreme Court" in parsed.entries[0].title


def test_parse_recorded_fixture_the_island():
    fixture_path = FIXTURES_DIR / "sample_the_island.xml"
    content = fixture_path.read_bytes()
    parsed = feedparser.parse(content)
    assert len(parsed.entries) == 2
    assert "Central Bank" in parsed.entries[0].title
    assert parsed.entries[0].published is not None


def test_parse_recorded_fixture_sinhala_detected():
    fixture_path = FIXTURES_DIR / "sample_sinhala_feed.xml"
    content = fixture_path.read_bytes()
    parsed = feedparser.parse(content)
    assert len(parsed.entries) == 1
    lang = detect_language(parsed.entries[0].title)
    assert lang == "si"


def test_parse_recorded_fixture_tamil_detected():
    fixture_path = FIXTURES_DIR / "sample_tamil_feed.xml"
    content = fixture_path.read_bytes()
    parsed = feedparser.parse(content)
    assert len(parsed.entries) == 1
    lang = detect_language(parsed.entries[0].title)
    assert lang == "ta"


# ---------------------------------------------------------------------------
# 8. All Feeds Failure & Reliability Tests
# ---------------------------------------------------------------------------

def test_all_feeds_failure_handling(tmp_path: Path):
    """Pipeline outputs clear error message and status when all feeds fail."""
    dummy_config = tmp_path / "empty_feeds.yaml"
    dummy_config.write_text("""
ingestion:
  timeout_sec: 1.0
verified_active_feeds: []
query_feeds: []
news_api:
  enabled: false
""", encoding="utf-8")

    pipeline = NewsPipeline(config_path=dummy_config, storage_path=tmp_path / "out.csv")
    res = pipeline.run(since="24h")

    assert res["status"] == "FAILED_ALL_FEEDS"
    assert res["total_raw_fetched"] == 0
    assert "CRITICAL" in res["error"]

"""
Live News Ingestion Engine for Stage 12.

Features:
- Feedparser with timeouts, ETag/Last-Modified caching, retries with backoff.
- Publication time normalisation to Asia/Colombo ISO 8601 (handles missing pubDates).
- URL canonicalisation and tracking parameter removal.
- Language detection (Sinhala / Tamil detection, skip & count).
- Fuzzy title deduplication (>0.85 similarity threshold).
- Relevance pre-filter using curated macroeconomic and political keyword lexicons.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from zoneinfo import ZoneInfo

import dateutil.parser
import feedparser
import requests

from cse.news.storage import NewsStorage, compute_title_similarity, normalize_title
from cse.utils.config import find_project_root

logger = logging.getLogger("cse.news.ingest")

COLOMBO_TZ = ZoneInfo("Asia/Colombo")
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 CSE-Research-Bot/1.0"
)

PREFILTER_KEYWORDS: List[str] = [
    # Politics & Elections
    "election", "presidential", "parliament", "parliamentary", "cabinet",
    "minister", "prime minister", "president", "dissolution", "gazette",
    "nomination", "polling", "vote", "voters", "ballot", "supreme court",
    "constitutional", "referendum", "npp", "sjb", "slpp", "unp", "itak",
    "dissanayake", "wickremesinghe", "rajapaksa", "premadasa", "government",
    # Macroeconomics, Monetary, Debt
    "central bank", "cbsl", "monetary board", "interest rate", "policy rate",
    "inflation", "ccpi", "deflation", "rupee", "lkr", "exchange rate",
    "forex", "reserves", "foreign reserves", "imf", "extended fund facility",
    "debt restructuring", "external debt", "default", "bondholders", "isb",
    "treasury bill", "treasury bond", "yield", "haircut", "bilateral debt",
    # Capital Markets
    "colombo stock exchange", "cse", "aspi", "s&p sl20", "sp sl 20", "stock market",
    "share price", "turnover", "equities", "foreign investors", "listed company",
    # Fiscal & Trade
    "budget", "tax", "vat", "tariff", "fiscal deficit", "revenue", "privatization",
    "state-owned", "ceb", "cpc", "srilankan airlines", "trade deficit", "remittances",
]


@dataclass
class IngestedItem:
    """Normalized ingested news item before stage processing."""
    item_id: str
    url: str
    headline: str
    description: str
    publication_date: str  # Asia/Colombo ISO 8601
    source: str
    language: str
    fetched_at: str  # UTC ISO 8601
    is_prefiltered_relevant: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def canonicalize_url(url: str) -> str:
    """
    Canonicalize a URL: lowercase scheme/host, strip trailing slash, strip tracking params.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()
        path = parsed.path
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        # Filter out common marketing/tracking parameters
        tracking_keys = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "fbclid", "gclid", "_ga", "ref", "source", "oc",
        }
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        clean_pairs = [
            (k, v) for k, v in query_pairs
            if k.lower() not in tracking_keys and not k.lower().startswith("utm_")
        ]
        clean_query = urlencode(clean_pairs)

        return urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))
    except Exception as e:
        logger.debug(f"Error canonicalizing URL {url}: {e}")
        return url.strip()


def detect_language(text: str) -> str:
    """
    Detect whether text is English, Sinhala, or Tamil.

    Uses Unicode block character matching:
    - Sinhala: U+0D80 to U+0DFF
    - Tamil: U+0B80 to U+0BFF
    """
    if not text:
        return "en"
    sinhala_matches = len(re.findall(r"[\u0D80-\u0DFF]", text))
    if sinhala_matches > 3:
        return "si"
    tamil_matches = len(re.findall(r"[\u0B80-\u0BFF]", text))
    if tamil_matches > 3:
        return "ta"
    return "en"


def parse_publication_date_to_colombo(
    raw_date: Optional[str],
    parsed_time: Optional[Any] = None,
    fallback_utc: Optional[datetime] = None,
) -> str:
    """
    Normalise any publication time to Asia/Colombo ISO 8601 (+05:30).

    Gracefully handles missing or malformed time zones, struct_time, or empty fields.
    """
    if fallback_utc is None:
        fallback_utc = datetime.now(timezone.utc)

    # 1. Try feedparser's published_parsed (struct_time in UTC)
    if parsed_time is not None:
        try:
            ts = time.mktime(parsed_time) - time.timezone
            dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt_utc.astimezone(COLOMBO_TZ).isoformat()
        except Exception:
            pass

    # 2. Try raw_date string
    if raw_date and str(raw_date).strip():
        try:
            dt = dateutil.parser.parse(str(raw_date))
            if dt.tzinfo is None:
                # Naive date assumed to be Asia/Colombo local time
                dt = dt.replace(tzinfo=COLOMBO_TZ)
            else:
                dt = dt.astimezone(COLOMBO_TZ)
            return dt.isoformat()
        except Exception:
            pass

    # 3. Fallback: current time in Asia/Colombo
    return fallback_utc.astimezone(COLOMBO_TZ).isoformat()


def check_prefilter_relevance(headline: str, description: str) -> bool:
    """Fast keyword pre-filter before Stage 10 extraction."""
    combo = f"{headline} {description}".lower()
    for kw in PREFILTER_KEYWORDS:
        if kw in combo:
            return True
    return False


class NewsFeedIngester:
    """
    Polite RSS feed ingester with ETag/Last-Modified caching and backoff.
    """

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        timeout: float = 10.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        root = find_project_root()
        self.cache_path = cache_path or (root / "data" / "interim" / "feed_cache.json")
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.user_agent = user_agent
        self.cache: Dict[str, Dict[str, str]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, str]]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self) -> None:
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to persist feed cache: {e}")

    def fetch_feed(
        self,
        feed_name: str,
        feed_url: str,
        use_cache: bool = True,
        max_retries: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Fetch and parse a single RSS feed with ETag/Last-Modified and retries.
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml, application/atom+xml, */*",
        }
        cached_info = self.cache.get(feed_url, {}) if use_cache else {}
        if cached_info.get("etag"):
            headers["If-None-Match"] = cached_info["etag"]
        if cached_info.get("last_modified"):
            headers["If-Modified-Since"] = cached_info["last_modified"]

        backoff = 1.0
        resp: Optional[requests.Response] = None

        for attempt in range(max_retries):
            try:
                resp = requests.get(feed_url, headers=headers, timeout=self.timeout)
                break
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Fetch error for {feed_name} ({feed_url}) attempt {attempt + 1}/{max_retries}: {e}"
                )
                time.sleep(backoff)
                backoff *= 2.0

        if resp is None:
            logger.error(f"All retries failed for feed {feed_name} ({feed_url})")
            return []

        if resp.status_code == 304:
            logger.info(f"Feed {feed_name} unchanged (HTTP 304 Not Modified).")
            return []

        if resp.status_code != 200:
            logger.warning(f"Feed {feed_name} returned HTTP {resp.status_code}.")
            return []

        # Update cache headers
        etag = resp.headers.get("ETag")
        last_mod = resp.headers.get("Last-Modified")
        if etag or last_mod:
            self.cache[feed_url] = {"etag": etag or "", "last_modified": last_mod or ""}
            self._save_cache()

        # Parse entries via feedparser
        parsed = feedparser.parse(resp.content)
        entries = getattr(parsed, "entries", [])
        logger.info(f"Fetched {len(entries)} raw entries from {feed_name}.")

        normalized_entries: List[Dict[str, Any]] = []
        for entry in entries:
            headline = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", "") or entry.get("description", "")
            # Clean HTML tags from summary if present
            clean_summary = re.sub(r"<[^>]+>", " ", summary).strip()
            clean_summary = re.sub(r"\s+", " ", clean_summary)

            raw_date = entry.get("published") or entry.get("updated")
            parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")

            normalized_entries.append({
                "headline": headline,
                "url": link,
                "description": clean_summary,
                "raw_date": raw_date,
                "parsed_time": parsed_time,
                "source": feed_name,
            })

        return normalized_entries

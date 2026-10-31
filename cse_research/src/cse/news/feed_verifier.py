"""
Feed Verification Module for Sri Lankan News Sources (Rule R11).

Discovers and verifies live English-language Sri Lankan RSS feeds, query feeds,
and APIs with HTTP and parse checks. Never hard-codes an unverified URL.
"""

from __future__ import annotations

import csv
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import feedparser
import requests
import yaml

from cse.utils.config import find_project_root

logger = logging.getLogger("cse.news.feed_verifier")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 CSE-Research-Bot/1.0"
)


@dataclass
class FeedStatusResult:
    """Outcome of live verification probe on a candidate news source."""
    feed_name: str
    url: str
    feed_type: str  # rss, query_rss, api, html
    status_code: int
    is_active: bool
    entry_count: int
    last_checked_utc: str
    response_time_sec: float
    error_message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def check_robots_txt(url: str, user_agent: str = DEFAULT_USER_AGENT) -> Tuple[bool, str]:
    """
    Check if robots.txt on domain allows fetching the specified URL.

    Returns:
        (is_allowed, reason_or_status)
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        resp = requests.get(robots_url, headers={"User-Agent": user_agent}, timeout=5)
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
            allowed = rp.can_fetch(user_agent, url)
            return allowed, f"robots.txt status 200: {'allowed' if allowed else 'disallowed'}"
        elif resp.status_code == 404:
            return True, "robots.txt not found (allowed by default)"
        else:
            return True, f"robots.txt status {resp.status_code} (assumed allowed)"
    except Exception as e:
        logger.debug(f"robots.txt check failed for {url}: {e}")
        return True, f"robots.txt check error: {str(e)}"


def verify_feed(
    feed_name: str,
    url: str,
    feed_type: str = "rss",
    timeout: float = 8.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> FeedStatusResult:
    """
    Perform live HTTP and parse check on an RSS feed or query endpoint.

    Strictly satisfies Rule R11: validates status code and entry count.
    """
    t0 = time.time()
    now_utc = datetime.now(timezone.utc).isoformat()

    headers = {
        "User-Agent": user_agent,
        "Accept": "application/rss+xml, application/xml, text/xml, application/atom+xml, */*",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        elapsed = round(time.time() - t0, 3)
        status_code = resp.status_code

        if status_code != 200:
            return FeedStatusResult(
                feed_name=feed_name,
                url=url,
                feed_type=feed_type,
                status_code=status_code,
                is_active=False,
                entry_count=0,
                last_checked_utc=now_utc,
                response_time_sec=elapsed,
                error_message=f"HTTP {status_code}",
            )

        # Parse feed content
        parsed = feedparser.parse(resp.content)
        entry_count = len(parsed.entries) if hasattr(parsed, "entries") else 0

        # An active RSS feed must have valid XML/Atom entries and not just an HTML error page
        is_active = (entry_count > 0)
        err = "" if is_active else "No RSS entries parsed (empty feed or HTML returned)"

        return FeedStatusResult(
            feed_name=feed_name,
            url=url,
            feed_type=feed_type,
            status_code=status_code,
            is_active=is_active,
            entry_count=entry_count,
            last_checked_utc=now_utc,
            response_time_sec=elapsed,
            error_message=err,
        )

    except requests.exceptions.Timeout:
        elapsed = round(time.time() - t0, 3)
        return FeedStatusResult(
            feed_name=feed_name,
            url=url,
            feed_type=feed_type,
            status_code=0,
            is_active=False,
            entry_count=0,
            last_checked_utc=now_utc,
            response_time_sec=elapsed,
            error_message="Connection timed out",
        )
    except Exception as e:
        elapsed = round(time.time() - t0, 3)
        return FeedStatusResult(
            feed_name=feed_name,
            url=url,
            feed_type=feed_type,
            status_code=0,
            is_active=False,
            entry_count=0,
            last_checked_utc=now_utc,
            response_time_sec=elapsed,
            error_message=str(e),
        )


def write_feed_status_table(results: List[FeedStatusResult], out_path: Path) -> None:
    """Persist feed verification results to results/tables/feed_status.csv."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "feed_name",
        "url",
        "feed_type",
        "status_code",
        "is_active",
        "entry_count",
        "last_checked_utc",
        "response_time_sec",
        "error_message",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r.to_dict())
    logger.info(f"Saved feed status table ({len(results)} rows) to {out_path}")

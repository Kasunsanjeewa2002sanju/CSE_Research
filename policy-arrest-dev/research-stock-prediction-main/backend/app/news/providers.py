import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from pathlib import Path
import yaml
import feedparser
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger

class NewsProviders:
    """Manages news acquisition from verified RSS feeds and NewsAPI."""

    def __init__(self, sources_file: Optional[Path] = None):
        self.sources_file = sources_file or (Path(__file__).parent / "trusted_sources.yml")
        self.sources_config = self._load_sources()

    def _load_sources(self) -> Dict[str, Any]:
        if not self.sources_file.exists():
            return {}
        try:
            with open(self.sources_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load trusted_sources.yml: {e}")
            return {}

    def fetch_rss_feeds(self) -> List[Dict[str, Any]]:
        """Fetches and normalizes articles from configured trusted RSS feeds."""
        articles = []
        tiers = self.sources_config.get("tiers", {})

        for tier_key, tier_data in tiers.items():
            tier_num = 1 if "1" in tier_key else (2 if "2" in tier_key else 3)
            sources = tier_data.get("sources", [])

            for src in sources:
                rss_url = src.get("rss")
                if not rss_url:
                    continue

                src_name = src.get("name", "Unknown Publisher")
                try:
                    # Fetch feed content with short timeout
                    resp = httpx.get(rss_url, timeout=5.0, headers={"User-Agent": "PolitiTradeLK/1.0 NewsAggregator"})
                    if resp.status_code == 200:
                        feed = feedparser.parse(resp.text)
                        for entry in feed.entries[:10]:
                            headline = getattr(entry, "title", "").strip()
                            link = getattr(entry, "link", "").strip()
                            summary = getattr(entry, "summary", "").strip()
                            
                            if not headline or not link:
                                continue

                            # Deterministic news_id based on url hash
                            news_id = f"NEWS-{hashlib.sha256(link.encode('utf-8')).hexdigest()[:12]}"
                            
                            # Published date parsing
                            pub_time = None
                            if hasattr(entry, "published_parsed") and entry.published_parsed:
                                pub_time = datetime(*entry.published_parsed[:6])
                            else:
                                pub_time = datetime.utcnow()

                            domain = urlparse(link).hostname or ""

                            articles.append({
                                "news_id": news_id,
                                "headline": headline,
                                "summary": summary,
                                "source_name": src_name,
                                "source_url": link,
                                "source_domain": domain,
                                "source_tier": tier_num,
                                "published_at": pub_time,
                                "retrieved_at": datetime.utcnow()
                            })
                except Exception as e:
                    logger.debug(f"RSS fetch skipped for {src_name} ({rss_url}): {e}")

        logger.info(f"Retrieved {len(articles)} articles from active RSS sources.")
        return articles

    def fetch_newsapi(self, query: str = "Sri Lanka politics economy") -> List[Dict[str, Any]]:
        """Fetches from NewsAPI if configured."""
        if not settings.NEWS_API_KEY:
            return []

        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=20&apiKey={settings.NEWS_API_KEY}"
        try:
            resp = httpx.get(url, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                articles = []
                for item in data.get("articles", []):
                    title = item.get("title", "")
                    link = item.get("url", "")
                    if not title or not link:
                        continue
                    articles.append({
                        "news_id": f"NEWS-{hashlib.sha256(link.encode('utf-8')).hexdigest()[:12]}",
                        "headline": title,
                        "summary": item.get("description", ""),
                        "source_name": item.get("source", {}).get("name", "NewsAPI"),
                        "source_url": link,
                        "source_domain": urlparse(link).hostname or "",
                        "source_tier": 2,
                        "published_at": datetime.fromisoformat(item.get("publishedAt").replace("Z", "+00:00")) if item.get("publishedAt") else datetime.utcnow(),
                        "retrieved_at": datetime.utcnow()
                    })
                return articles
        except Exception as e:
            logger.warning(f"NewsAPI fetch error: {e}")
        return []

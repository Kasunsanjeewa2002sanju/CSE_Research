"""
News API Source Client with Rate-Limit Handling and Configurable Providers.

Supports NewsData.io and GNews with API keys loaded from environment variables.
Provides exponential backoff, rate limiting, and graceful fallback when keys are absent.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger("cse.news.api_client")


class NewsApiClient:
    """Configurable News API client with rate-limiting and quota handling."""

    def __init__(
        self,
        provider: str = "newsdata",
        api_key: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        self.provider = provider.lower()
        self.timeout = timeout
        
        # Load API key from environment variable if not supplied
        if api_key:
            self.api_key = api_key
        elif self.provider == "newsdata":
            self.api_key = os.environ.get("NEWSDATA_API_KEY", "")
        elif self.provider == "gnews":
            self.api_key = os.environ.get("GNEWS_API_KEY", "")
        else:
            self.api_key = os.environ.get("NEWS_API_KEY", "")

        self._last_request_time = 0.0
        self._min_interval = 2.0  # seconds between requests to prevent hitting rate limits

    def is_configured(self) -> bool:
        """Return True if an API key is available."""
        return bool(self.api_key and self.api_key.strip())

    def fetch_news(self, query: str = "Sri Lanka", max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch news articles from the configured API provider.

        Returns:
            List of normalized article dicts with keys:
            ['headline', 'description', 'url', 'publication_date', 'source']
        """
        if not self.is_configured():
            logger.info(
                f"[NewsAPI] No API key found for provider '{self.provider}'. "
                "Skipping News API source gracefully."
            )
            return []

        # Enforce polite client-side rate limit
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

        if self.provider == "newsdata":
            return self._fetch_newsdata(query=query, max_retries=max_retries)
        elif self.provider == "gnews":
            return self._fetch_gnews(query=query, max_retries=max_retries)
        else:
            logger.warning(f"[NewsAPI] Unsupported provider '{self.provider}'.")
            return []

    def _fetch_newsdata(self, query: str, max_retries: int) -> List[Dict[str, Any]]:
        url = "https://newsdata.io/api/1/news"
        params = {
            "apikey": self.api_key,
            "q": query,
            "country": "lk",
            "language": "en",
        }
        backoff = 2.0

        for attempt in range(max_retries):
            self._last_request_time = time.time()
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    articles = []
                    for item in results:
                        articles.append({
                            "headline": item.get("title", "").strip(),
                            "description": item.get("description", "").strip() if item.get("description") else "",
                            "url": item.get("link", "").strip(),
                            "publication_date": item.get("pubDate", ""),
                            "source": item.get("source_id", "NewsData.io"),
                        })
                    logger.info(f"[NewsAPI] NewsData.io returned {len(articles)} articles.")
                    return articles

                elif resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", backoff))
                    logger.warning(
                        f"[NewsAPI] Rate limit hit (429) on NewsData.io. Retrying after {retry_after}s..."
                    )
                    time.sleep(retry_after)
                    backoff *= 2.0

                elif resp.status_code == 401:
                    logger.error("[NewsAPI] NewsData.io API key is unauthorized or invalid.")
                    return []
                else:
                    logger.warning(
                        f"[NewsAPI] NewsData.io returned status {resp.status_code}: {resp.text[:100]}"
                    )
                    return []

            except requests.exceptions.RequestException as e:
                logger.warning(f"[NewsAPI] Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(backoff)
                backoff *= 2.0

        return []

    def _fetch_gnews(self, query: str, max_retries: int) -> List[Dict[str, Any]]:
        url = "https://gnews.io/api/v4/search"
        params = {
            "token": self.api_key,
            "q": query,
            "lang": "en",
            "country": "lk",
            "max": 10,
        }
        backoff = 2.0

        for attempt in range(max_retries):
            self._last_request_time = time.time()
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    articles_raw = data.get("articles", [])
                    articles = []
                    for item in articles_raw:
                        articles.append({
                            "headline": item.get("title", "").strip(),
                            "description": item.get("description", "").strip() if item.get("description") else "",
                            "url": item.get("url", "").strip(),
                            "publication_date": item.get("publishedAt", ""),
                            "source": item.get("source", {}).get("name", "GNews"),
                        })
                    logger.info(f"[NewsAPI] GNews returned {len(articles)} articles.")
                    return articles

                elif resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", backoff))
                    logger.warning(
                        f"[NewsAPI] Rate limit hit (429) on GNews. Retrying after {retry_after}s..."
                    )
                    time.sleep(retry_after)
                    backoff *= 2.0

                else:
                    logger.warning(
                        f"[NewsAPI] GNews returned status {resp.status_code}: {resp.text[:100]}"
                    )
                    return []

            except requests.exceptions.RequestException as e:
                logger.warning(f"[NewsAPI] Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(backoff)
                backoff *= 2.0

        return []

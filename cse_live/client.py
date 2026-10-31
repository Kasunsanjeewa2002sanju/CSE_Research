"""Asynchronous HTTP Client for Colombo Stock Exchange API.

Resilience features:
- Per-request timeouts
- Exponential backoff with full jitter
- Circuit breaker protection
- Honouring 429 Retry-After headers
- Minimum poll interval enforcement
- Conditional request support (ETag / If-None-Match, Last-Modified)
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any, Dict, List, Optional, Tuple

# Enable httpx process-wide alias
try:
    import httpx2
    httpx2.alias_httpx()
except Exception:
    pass

try:
    import httpx
    _HTTPX_EXCEPTIONS: Tuple[type, ...] = (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)
except ImportError:
    import urllib.error
    httpx = None
    _HTTPX_EXCEPTIONS = (urllib.error.URLError, TimeoutError, ConnectionError)

from cse_live.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from cse_live.config import IngestionConfig

logger = logging.getLogger("cse_live.client")


class _UrllibResponseAdapter:
    """Lightweight adapter mimicking httpx.Response when httpx is unavailable."""
    def __init__(self, status_code: int, headers: Dict[str, str], body: bytes) -> None:
        self.status_code = status_code
        self.headers = headers
        self._body = body

    def json(self) -> Any:
        import json
        return json.loads(self._body.decode("utf-8"))

    def raise_for_status(self) -> None:
        if 400 <= self.status_code < 600:
            raise RuntimeError(f"HTTP Error {self.status_code}: {self._body.decode('utf-8', errors='replace')}")


class AsyncCSEClient:
    """Async HTTP client querying official CSE REST endpoints."""

    def __init__(
        self,
        config: Optional[IngestionConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self.config = config or IngestionConfig.from_env()
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            fail_threshold=self.config.circuit_fail_threshold,
            cooldown_seconds=self.config.circuit_cooldown,
            name="cse_http_client"
        )
        self.base_url = self.config.cse_base_urls[0]

        # Conditional request caching: endpoint -> value
        self._etags: Dict[str, str] = {}
        self._last_modified: Dict[str, str] = {}
        self._cached_responses: Dict[str, Any] = {}

        # Enforce rate limits
        self._last_request_time: float = 0.0
        self._client: Optional[Any] = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> Optional[Any]:
        if httpx is None:
            return None
        if self._client is None or getattr(self._client, "is_closed", False):
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            timeout = httpx.Timeout(self.config.request_timeout, connect=5.0)
            headers = {
                "User-Agent": self.config.user_agent,
                "Accept": "application/json, text/plain, */*",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/",
            }
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=timeout,
                limits=limits,
                follow_redirects=True
            )
        return self._client

    async def close(self) -> None:
        """Gracefully close underlying connection pool."""
        if self._client and not getattr(self._client, "is_closed", False):
            await self._client.aclose()
            self._client = None

    async def _rate_limit_throttle(self) -> None:
        """Ensure minimum polling interval is never violated."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self.config.min_poll_interval_seconds:
            sleep_needed = self.config.min_poll_interval_seconds - elapsed
            await asyncio.sleep(sleep_needed)
        self._last_request_time = time.monotonic()

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs: Any
    ) -> Tuple[int, Any, float]:
        """Execute HTTP request with circuit breaker, conditional headers, and backoff retries."""
        # 1. Circuit breaker pre-flight check
        await self.circuit_breaker.before_call()
        await self._rate_limit_throttle()

        client = await self._get_client()
        url = path if path.startswith("http") else f"{self.base_url}{path}"

        # 2. Add conditional request headers if cached
        headers = dict(kwargs.get("headers") or {})
        if path in self._etags:
            headers["If-None-Match"] = self._etags[path]
        if path in self._last_modified:
            headers["If-Modified-Since"] = self._last_modified[path]
        kwargs["headers"] = headers

        start_time = time.monotonic()
        attempt = 0

        while attempt <= self.config.max_retries:
            try:
                if client is not None:
                    resp = await client.request(method, url, **kwargs)
                else:
                    def _do_urllib():
                        import urllib.request
                        import urllib.error
                        import json
                        req_headers = dict(kwargs.get("headers") or {})
                        req_headers.setdefault("User-Agent", self.config.user_agent)
                        req_headers.setdefault("Accept", "application/json, text/plain, */*")
                        req_headers.setdefault("Origin", self.base_url)
                        req_headers.setdefault("Referer", f"{self.base_url}/")

                        data_bytes = None
                        if "json" in kwargs:
                            data_bytes = json.dumps(kwargs["json"]).encode("utf-8")
                            req_headers["Content-Type"] = "application/json"
                        elif "data" in kwargs:
                            raw_data = kwargs["data"]
                            if isinstance(raw_data, dict):
                                import urllib.parse
                                data_bytes = urllib.parse.urlencode(raw_data).encode("utf-8")
                                req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
                            elif isinstance(raw_data, bytes):
                                data_bytes = raw_data
                            else:
                                data_bytes = str(raw_data).encode("utf-8")
                        elif "content" in kwargs:
                            raw_content = kwargs["content"]
                            data_bytes = raw_content if isinstance(raw_content, bytes) else str(raw_content).encode("utf-8")

                        req = urllib.request.Request(url, data=data_bytes, headers=req_headers, method=method)
                        try:
                            with urllib.request.urlopen(req, timeout=self.config.request_timeout) as u_resp:
                                return _UrllibResponseAdapter(u_resp.status, dict(u_resp.headers), u_resp.read())
                        except urllib.error.HTTPError as e:
                            return _UrllibResponseAdapter(e.code, dict(e.headers), e.read())

                    resp = await asyncio.to_thread(_do_urllib)

                latency_ms = (time.monotonic() - start_time) * 1000.0

                # Check 304 Not Modified
                if resp.status_code == 304 and path in self._cached_responses:
                    await self.circuit_breaker.record_success()
                    return 304, self._cached_responses[path], latency_ms

                # Check 429 Rate Limit
                if resp.status_code == 429:
                    retry_after_str = resp.headers.get("Retry-After")
                    delay = self._compute_delay(attempt, retry_after_str)
                    logger.warning(f"HTTP 429 Rate Limited on {path}. Backing off for {delay:.2f}s")
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(delay)
                        attempt += 1
                        continue
                    else:
                        await self.circuit_breaker.record_failure()
                        resp.raise_for_status()

                # Check Server Error 5xx
                if resp.status_code >= 500:
                    delay = self._compute_delay(attempt)
                    logger.warning(f"HTTP {resp.status_code} on {path}. Retry attempt {attempt+1}/{self.config.max_retries} in {delay:.2f}s")
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(delay)
                        attempt += 1
                        continue
                    else:
                        await self.circuit_breaker.record_failure()
                        resp.raise_for_status()

                # Successful 2xx response
                resp.raise_for_status()
                data = resp.json()

                # Update conditional request metadata
                if "ETag" in resp.headers:
                    self._etags[path] = resp.headers["ETag"]
                if "Last-Modified" in resp.headers:
                    self._last_modified[path] = resp.headers["Last-Modified"]
                self._cached_responses[path] = data

                await self.circuit_breaker.record_success()
                return resp.status_code, data, latency_ms

            except _HTTPX_EXCEPTIONS as err:
                delay = self._compute_delay(attempt)
                logger.warning(f"Network error on {path}: {err}. Retry attempt {attempt+1} in {delay:.2f}s")
                if attempt < self.config.max_retries:
                    await asyncio.sleep(delay)
                    attempt += 1
                else:
                    await self.circuit_breaker.record_failure()
                    raise

        raise RuntimeError(f"Exceeded max retries ({self.config.max_retries}) for {path}")

    def _compute_delay(self, attempt: int, retry_after: Optional[str] = None) -> float:
        """Compute exponential backoff with full jitter or honour Retry-After."""
        if retry_after:
            try:
                val = float(retry_after)
                return min(val, self.config.backoff_max)
            except ValueError:
                pass
        # Full jitter: Uniform(0, min(max_backoff, base * 2^attempt))
        upper = min(self.config.backoff_max, self.config.backoff_base * (2.0 ** attempt))
        return random.uniform(0.1, upper)

    async def fetch_market_status(self) -> Tuple[int, Dict[str, Any], float]:
        """Fetch market session status from POST /api/marketStatus."""
        headers = {"Content-Type": "application/json"}
        return await self._request_with_retry("POST", "/api/marketStatus", json={}, headers=headers)

    async def fetch_chart_data(self, chart_id: int = 1, period: str = "1") -> Tuple[int, List[Dict[str, Any]], float]:
        """Fetch chart ticks from POST /api/chartData."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = f"chartId={chart_id}&period={period}"
        return await self._request_with_retry("POST", "/api/chartData", content=body, headers=headers)

    async def fetch_all_sectors(self) -> Tuple[int, List[Dict[str, Any]], float]:
        """Fetch sector summary records from POST /api/allSectors."""
        headers = {"Content-Type": "application/json"}
        return await self._request_with_retry("POST", "/api/allSectors", json={}, headers=headers)

    async def fetch_trade_summary(self) -> Tuple[int, Dict[str, Any], float]:
        """Fetch all stock trades summary from POST /api/tradeSummary."""
        headers = {"Content-Type": "application/json"}
        return await self._request_with_retry("POST", "/api/tradeSummary", json={}, headers=headers)

    async def fetch_raw_snapshot_bundle(self) -> Dict[str, Any]:
        """Coordinate concurrent queries to build full market snapshot payload."""
        t0 = time.monotonic()
        results = await asyncio.gather(
            self.fetch_market_status(),
            self.fetch_chart_data(chart_id=1, period="1"),
            self.fetch_all_sectors(),
            self.fetch_chart_data(chart_id=40, period="1"),
            self.fetch_trade_summary(),
            return_exceptions=True
        )
        total_latency_ms = (time.monotonic() - t0) * 1000.0

        status_res = results[0] if not isinstance(results[0], Exception) else None
        aspi_res = results[1] if not isinstance(results[1], Exception) else None
        sectors_res = results[2] if not isinstance(results[2], Exception) else None
        sp20_res = results[3] if not isinstance(results[3], Exception) else None
        trade_res = results[4] if len(results) > 4 and not isinstance(results[4], Exception) else None

        return {
            "status_data": status_res[1] if status_res else None,
            "aspi_chart": aspi_res[1] if aspi_res else None,
            "sectors_data": sectors_res[1] if sectors_res else None,
            "sp20_chart": sp20_res[1] if sp20_res else None,
            "trade_summary": trade_res[1] if trade_res else None,
            "total_latency_ms": total_latency_ms,
            "errors": [str(r) for r in results if isinstance(r, Exception)],
        }


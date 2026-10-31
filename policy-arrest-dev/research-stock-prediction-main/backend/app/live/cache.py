from datetime import datetime, timezone
from typing import Any, Optional, Dict
import time
import threading

class LiveMarketCache:
    """Thread-safe in-memory cache for live market quotes with TTL."""
    def __init__(self, default_ttl_seconds: int = 30):
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            
            # Check expiration
            if time.time() > entry["expires_at"]:
                return None
                
            return entry["data"]

    def get_stale(self, key: str) -> Optional[Dict[str, Any]]:
        """Returns last cached value even if expired, marked with is_stale=True."""
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            return {
                "data": entry["data"],
                "cached_at": entry["cached_at"],
                "is_stale": time.time() > entry["expires_at"]
            }

    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        with self._lock:
            self._cache[key] = {
                "data": data,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": now + ttl
            }

live_cache = LiveMarketCache()

"""Server-Sent Events (SSE) Real-Time Delivery Manager for CSE Live Ingestion.

Stage 4 Delivery Architecture:
- Event types: "snapshot", "tick", "status", "heartbeat", "error"
- Monotonically increasing sequence IDs (seq) and Last-Event-ID resume support
- Backpressure: Per-client bounded queue with non-blocking drop/coalescing for slow consumers
- Concurrency & DOS protection: Global max connection cap and per-IP cap
- Proxy friendly headers: Content-Type: text/event-stream, no-buffering, no-cache
- Zero-leak client deregistration on disconnect / tab close
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import uuid

from fastapi import HTTPException, Request

from cse_live.config import IngestionConfig
from cse_live.events import (
    EventBus,
    default_event_bus,
    EVENT_SNAPSHOT_ACCEPTED,
    EVENT_STATUS_CHANGED,
    EVENT_TICK_REJECTED,
    EVENT_CIRCUIT_STATE_CHANGED,
)
from cse_live.models import (
    FreshnessState,
    MarketSnapshot,
    MarketStatus,
    COLOMBO_TZ,
)
from cse_live.storage import get_snapshot_store

logger = logging.getLogger("cse_live.streaming")


@dataclass
class SSEEvent:
    """Immutable Server-Sent Event representation with wire-protocol encoder."""
    event_type: str  # "snapshot" | "tick" | "status" | "heartbeat" | "error"
    data: Dict[str, Any]
    seq: int
    id: str
    timestamp: datetime

    def encode(self) -> str:
        """Encode to compliant W3C Server-Sent Events text/event-stream wire format."""
        data_str = json.dumps(self.data, default=str)
        # Format: id: <id>\nevent: <event_type>\ndata: <json>\n\n
        return f"id: {self.id}\nevent: {self.event_type}\ndata: {data_str}\n\n"


class SSEClient:
    """Active client connection handle with bounded queue backpressure."""

    def __init__(self, client_id: str, ip: str, queue_size: int = 100) -> None:
        self.client_id = client_id
        self.ip = ip
        self.queue: asyncio.Queue[SSEEvent] = asyncio.Queue(maxsize=queue_size)
        self.connected_at = time.time()
        self.last_sent = time.time()
        self.is_active = True
        self.dropped_events_count = 0

    def enqueue(self, event: SSEEvent) -> bool:
        """Non-blocking enqueue with backpressure.
        
        If the queue is full (slow consumer), drop the oldest pending tick so the
        client receives newest ticks and the server event loop is never blocked.
        """
        if not self.is_active:
            return False

        if self.queue.full():
            try:
                # Drop oldest event to relieve backpressure
                dropped = self.queue.get_nowait()
                self.dropped_events_count += 1
                logger.warning(
                    f"Backpressure: Dropped oldest {dropped.event_type} (seq={dropped.seq}) "
                    f"for slow client {self.client_id} (total dropped: {self.dropped_events_count})"
                )
            except (asyncio.QueueEmpty, ValueError):
                pass

        try:
            self.queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            self.dropped_events_count += 1
            return False


class SSEManager:
    """Central manager for Server-Sent Events stream delivery."""

    def __init__(self, config: Optional[IngestionConfig] = None, event_bus: Optional[EventBus] = None) -> None:
        self.config = config or IngestionConfig()
        self.event_bus = event_bus or default_event_bus
        self._clients: Dict[str, SSEClient] = {}
        self._ip_counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._seq = 0
        self._event_buffer: deque[SSEEvent] = deque(maxlen=self.config.sse_buffer_size)

        # State tracking for deduplication & diffs
        self._last_snapshot: Optional[MarketSnapshot] = None
        self._last_status_raw: Optional[str] = None
        self._last_freshness: Optional[str] = None

        # Wire up pub/sub event listeners
        self._subscribed = False
        self._setup_event_listeners()

    def _setup_event_listeners(self) -> None:
        """Register listeners on the internal EventBus."""
        if not self._subscribed:
            self.event_bus.subscribe(EVENT_SNAPSHOT_ACCEPTED, self.on_snapshot_accepted)
            self.event_bus.subscribe(EVENT_STATUS_CHANGED, self.on_status_changed)
            self.event_bus.subscribe(EVENT_TICK_REJECTED, self.on_tick_rejected)
            self.event_bus.subscribe(EVENT_CIRCUIT_STATE_CHANGED, self.on_circuit_changed)
            self._subscribed = True

    @property
    def current_seq(self) -> int:
        return self._seq

    @property
    def active_connection_count(self) -> int:
        return len(self._clients)

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _snapshot_to_dict(self, snapshot: MarketSnapshot) -> Dict[str, Any]:
        """Convert a MarketSnapshot to a JSON-ready dictionary."""
        d = snapshot.model_dump() if hasattr(snapshot, "model_dump") else snapshot.dict()
        # Ensure enums and datetime are converted
        if "freshness" in d and hasattr(d["freshness"], "value"):
            d["freshness"] = d["freshness"].value
        if "market_status" in d and isinstance(d["market_status"], dict):
            if "status" in d["market_status"] and hasattr(d["market_status"]["status"], "value"):
                d["market_status"]["status"] = d["market_status"]["status"].value
        return d

    def _get_current_snapshot_dict(self) -> Dict[str, Any]:
        """Retrieve current latest snapshot from store or return fallback."""
        snap_store = get_snapshot_store()
        snap = snap_store.get()
        if snap is not None:
            self._last_snapshot = snap
            self._last_status_raw = snap.market_status.raw_status if snap.market_status else "Market Closed"
            self._last_freshness = snap.freshness.value if hasattr(snap.freshness, "value") else str(snap.freshness)
            return self._snapshot_to_dict(snap)

        # Baseline fallback
        self._last_status_raw = "Market Closed"
        self._last_freshness = "CLOSED"
        return {
            "aspi_value": 22624.31,
            "aspi_change": 177.58,
            "aspi_percent_change": 0.7917,
            "aspi_previous_close": 22446.73,
            "sp20_value": 6157.38,
            "sp20_change": 45.8,
            "sp20_percent_change": 0.75,
            "sp20_previous_close": 6111.58,
            "market_turnover": 9309760000.0,
            "shares_traded": 245620000,
            "total_trades": 0,
            "market_status": {
                "raw_status": "Market Closed",
                "status": "Market Closed",
                "is_open": False,
            },
            "freshness": "CLOSED",
            "source_timestamp": datetime.now(COLOMBO_TZ).isoformat(),
            "source": "baseline_recovery",
        }

    async def register_client(self, ip: str, last_event_id: Optional[str] = None) -> SSEClient:
        """Register client, enforce connection limits, and replay missed events or send fresh snapshot."""
        async with self._lock:
            # 1. Total connection limit check
            if len(self._clients) >= self.config.sse_max_connections:
                logger.warning(f"Connection rejected: max concurrent connections ({self.config.sse_max_connections}) reached.")
                raise HTTPException(status_code=503, detail="Max concurrent stream connections reached")

            # 2. Per-IP connection limit check
            current_ip_count = self._ip_counts.get(ip, 0)
            if current_ip_count >= self.config.sse_per_ip_cap:
                logger.warning(f"Connection rejected for {ip}: per-IP cap ({self.config.sse_per_ip_cap}) reached.")
                raise HTTPException(status_code=429, detail="Too many concurrent stream connections from this IP")

            client_id = str(uuid.uuid4())
            client = SSEClient(client_id=client_id, ip=ip, queue_size=self.config.sse_client_queue_size)
            self._clients[client_id] = client
            self._ip_counts[ip] = current_ip_count + 1

            # 3. Check Last-Event-ID for missed event replay
            replayed = False
            if last_event_id is not None and last_event_id.strip():
                try:
                    last_id_num = int(last_event_id.strip())
                    if self._event_buffer:
                        min_seq = self._event_buffer[0].seq
                        max_seq = self._event_buffer[-1].seq
                        if min_seq <= last_id_num <= max_seq:
                            # Client's last_event_id is within our ring buffer window
                            replayed = True
                            missed = [ev for ev in self._event_buffer if ev.seq > last_id_num]
                            for ev in missed:
                                client.enqueue(ev)
                            if missed:
                                logger.info(f"Replayed {len(missed)} missed events to client {client_id} (Last-Event-ID: {last_id_num})")
                            else:
                                logger.info(f"Client {client_id} reconnecting already up-to-date at seq {last_id_num}")
                except ValueError:
                    pass

            # 4. If not replaying, send fresh initial "snapshot" event
            if not replayed:
                snap_dict = self._get_current_snapshot_dict()
                seq = self._next_seq()
                snap_event = SSEEvent(
                    event_type="snapshot",
                    data=snap_dict,
                    seq=seq,
                    id=str(seq),
                    timestamp=datetime.now(timezone.utc),
                )
                self._event_buffer.append(snap_event)
                client.enqueue(snap_event)

            logger.info(f"Client {client_id} connected from {ip}. Active connections: {len(self._clients)}")
            return client

    async def deregister_client(self, client: SSEClient) -> None:
        """Deregister client and release IP cap slot."""
        async with self._lock:
            if client.client_id in self._clients:
                del self._clients[client.client_id]
            client.is_active = False

            count = self._ip_counts.get(client.ip, 0)
            if count <= 1:
                self._ip_counts.pop(client.ip, None)
            else:
                self._ip_counts[client.ip] = count - 1

            logger.info(f"Client {client.client_id} disconnected. Remaining active connections: {len(self._clients)}")

    def broadcast(self, event: SSEEvent) -> None:
        """Record event in ring buffer and dispatch non-blocking to all active clients."""
        self._event_buffer.append(event)
        # Snapshot clients list to avoid locking during dispatch
        active_clients = list(self._clients.values())
        for client in active_clients:
            client.enqueue(event)

    async def on_snapshot_accepted(self, snapshot: MarketSnapshot) -> None:
        """Pub/Sub listener: Evaluate validated snapshot, publish 'status' and/or 'tick' events."""
        raw_status = snapshot.market_status.raw_status if snapshot.market_status else "Unknown"
        freshness_str = snapshot.freshness.value if hasattr(snapshot.freshness, "value") else str(snapshot.freshness)

        # 1. Check for Market Status or Freshness State change
        status_changed = (
            self._last_status_raw is not None and self._last_status_raw != raw_status
        ) or (
            self._last_freshness is not None and self._last_freshness != freshness_str
        )

        if status_changed:
            seq = self._next_seq()
            status_ev = SSEEvent(
                event_type="status",
                data={
                    "market_status": snapshot.market_status.model_dump() if hasattr(snapshot.market_status, "model_dump") else snapshot.market_status.dict(),
                    "freshness_state": freshness_str,
                    "source_timestamp": snapshot.source_timestamp.isoformat() if snapshot.source_timestamp else None,
                    "seq": seq,
                },
                seq=seq,
                id=str(seq),
                timestamp=datetime.now(timezone.utc),
            )
            self.broadcast(status_ev)

        # Always update tracked status and freshness state
        self._last_status_raw = raw_status
        self._last_freshness = freshness_str

        # 2. Check for value changes (Tick Diffing)
        if self._last_snapshot is not None:
            diff: Dict[str, Any] = {}
            fields_to_check = [
                "aspi_value",
                "aspi_change",
                "aspi_percent_change",
                "aspi_previous_close",
                "sp20_value",
                "sp20_change",
                "sp20_percent_change",
                "sp20_previous_close",
                "market_turnover",
                "shares_traded",
                "total_trades",
            ]
            for field in fields_to_check:
                old_val = getattr(self._last_snapshot, field, None)
                new_val = getattr(snapshot, field, None)
                if old_val != new_val:
                    diff[field] = new_val

            # Only publish "tick" if validated values actually changed
            if diff:
                seq = self._next_seq()
                diff["source_timestamp"] = snapshot.source_timestamp.isoformat() if snapshot.source_timestamp else None
                diff["seq"] = seq
                tick_ev = SSEEvent(
                    event_type="tick",
                    data=diff,
                    seq=seq,
                    id=str(seq),
                    timestamp=datetime.now(timezone.utc),
                )
                self.broadcast(tick_ev)

        self._last_snapshot = snapshot

    async def on_status_changed(self, payload: Any) -> None:
        """Pub/Sub listener for external status changes."""
        seq = self._next_seq()
        ev = SSEEvent(
            event_type="status",
            data={"status": payload, "seq": seq},
            seq=seq,
            id=str(seq),
            timestamp=datetime.now(timezone.utc),
        )
        self.broadcast(ev)

    async def on_tick_rejected(self, anomaly: Any) -> None:
        """Pub/Sub listener: Broadcast non-fatal source anomalies as 'error' events."""
        seq = self._next_seq()
        reason = getattr(anomaly, "reason", str(anomaly))
        ev = SSEEvent(
            event_type="error",
            data={"error_type": "tick_rejected", "reason": reason, "seq": seq},
            seq=seq,
            id=str(seq),
            timestamp=datetime.now(timezone.utc),
        )
        self.broadcast(ev)

    async def on_circuit_changed(self, circuit_info: Any) -> None:
        """Pub/Sub listener: Broadcast circuit breaker trips as non-fatal 'error' events."""
        seq = self._next_seq()
        ev = SSEEvent(
            event_type="error",
            data={"error_type": "circuit_breaker", "info": str(circuit_info), "seq": seq},
            seq=seq,
            id=str(seq),
            timestamp=datetime.now(timezone.utc),
        )
        self.broadcast(ev)

    async def stream_events(self, client: SSEClient, request: Request) -> AsyncGenerator[str, None]:
        """Async generator yielding SSE events and heartbeats until client disconnects."""
        heartbeat_interval = self.config.sse_heartbeat_interval_seconds
        try:
            while client.is_active:
                if await request.is_disconnected():
                    break

                try:
                    # Wait for an event with a timeout equal to heartbeat_interval
                    event = await asyncio.wait_for(client.queue.get(), timeout=heartbeat_interval)
                    client.last_sent = time.time()
                    yield event.encode()
                except asyncio.TimeoutError:
                    # No data event within interval -> issue heartbeat event
                    now_utc = datetime.now(timezone.utc)
                    client.last_sent = time.time()
                    hb = SSEEvent(
                        event_type="heartbeat",
                        data={"timestamp": now_utc.isoformat()},
                        seq=self._seq,
                        id=str(self._seq),
                        timestamp=now_utc,
                    )
                    yield hb.encode()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Error in SSE stream for client {client.client_id}: {e}")
        finally:
            await self.deregister_client(client)


# Global singleton instance
_global_sse_manager: Optional[SSEManager] = None


def get_sse_manager(config: Optional[IngestionConfig] = None) -> SSEManager:
    """Retrieve or initialize the process-wide SSEManager instance."""
    global _global_sse_manager
    if _global_sse_manager is None:
        _global_sse_manager = SSEManager(config=config)
    return _global_sse_manager

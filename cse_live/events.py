"""Internal asynchronous Pub/Sub Event Bus for CSE Live Ingestion.

Decouples ingestion, validation, scenario forecasting, and WebSocket broadcasting.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger("cse_live.events")

# Standard event names
EVENT_SNAPSHOT_ACCEPTED = "snapshot_accepted"
EVENT_TICK_REJECTED = "tick_rejected"
EVENT_STATUS_CHANGED = "status_changed"
EVENT_CIRCUIT_STATE_CHANGED = "circuit_state_changed"
EVENT_HEALTH_UPDATED = "health_updated"


class EventBus:
    """Lightweight in-memory asynchronous event bus."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Any], Any]]] = {}
        self._lock = asyncio.Lock()

    def subscribe(self, event_name: str, handler: Callable[[Any], Any]) -> None:
        """Register a callback for an event."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[[Any], Any]) -> None:
        """Remove a callback from an event."""
        if event_name in self._subscribers and handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)

    async def publish(self, event_name: str, payload: Any) -> None:
        """Broadcast payload to all registered subscribers."""
        handlers = list(self._subscribers.get(event_name, []))
        if not handlers:
            return

        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)
            except Exception as e:
                logger.error(f"Error in event handler for {event_name}: {e}", exc_info=True)


# Global singleton event bus instance
default_event_bus = EventBus()

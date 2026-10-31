"""Asynchronous Circuit Breaker implementation for upstream CSE services.

Transitions:
- CLOSED: Normal operation; passes calls. Trips to OPEN after failure_threshold consecutive errors.
- OPEN: Fails fast for cooldown_seconds without calling upstream. Transitions to HALF_OPEN when cooldown expires.
- HALF_OPEN: Allows a single probe call. On success, resets to CLOSED. On failure, returns to OPEN.
"""

from __future__ import annotations

import asyncio
import time
from typing import Callable, Optional
from cse_live.models import CircuitState


class CircuitBreakerOpenError(Exception):
    """Raised when an operation is attempted while the circuit breaker is OPEN."""
    def __init__(self, message: str = "Circuit breaker is OPEN", retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after


class CircuitBreaker:
    """Async circuit breaker with state transition callbacks."""

    def __init__(
        self,
        fail_threshold: int = 5,
        cooldown_seconds: float = 30.0,
        name: str = "cse_circuit_breaker",
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None,
    ) -> None:
        self.fail_threshold = fail_threshold
        self.cooldown_seconds = cooldown_seconds
        self.name = name
        self.on_state_change = on_state_change

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current state, auto-transitioning from OPEN to HALF_OPEN if cooldown elapsed."""
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if (time.monotonic() - self._opened_at) >= self.cooldown_seconds:
                return CircuitState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def success_count(self) -> int:
        return self._success_count

    async def before_call(self) -> None:
        """Pre-flight check before executing an external network call."""
        async with self._lock:
            current = self.state
            if current == CircuitState.OPEN:
                elapsed = time.monotonic() - (self._opened_at or 0.0)
                remaining = max(0.0, self.cooldown_seconds - elapsed)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. Cooldown remaining: {remaining:.1f}s",
                    retry_after=remaining
                )
            elif current == CircuitState.HALF_OPEN and self._state == CircuitState.OPEN:
                # Transitioned to HALF_OPEN
                self._transition_to(CircuitState.HALF_OPEN)

    async def record_success(self) -> None:
        """Record a successful upstream response."""
        async with self._lock:
            self._success_count += 1
            if self._state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
                self._failure_count = 0
                self._opened_at = None
                self._transition_to(CircuitState.CLOSED)
            else:
                self._failure_count = 0

    async def record_failure(self) -> None:
        """Record an upstream failure (timeout, network drop, HTTP 5xx)."""
        async with self._lock:
            self._failure_count += 1
            if self._state == CircuitState.HALF_OPEN:
                # Probe failed; immediately re-open
                self._opened_at = time.monotonic()
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.fail_threshold:
                    self._opened_at = time.monotonic()
                    self._transition_to(CircuitState.OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        old_state = self._state
        if old_state != new_state:
            self._state = new_state
            if self.on_state_change:
                try:
                    self.on_state_change(old_state, new_state)
                except Exception:
                    pass

    async def reset(self) -> None:
        """Manually reset the breaker to CLOSED state."""
        async with self._lock:
            self._failure_count = 0
            self._opened_at = None
            self._transition_to(CircuitState.CLOSED)

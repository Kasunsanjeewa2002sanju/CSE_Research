"""Unit tests for Circuit Breaker state transitions."""

import asyncio
import time
import pytest

from cse_live.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from cse_live.models import CircuitState


def test_circuit_breaker_normal_closed_operation():
    async def _test():
        cb = CircuitBreaker(fail_threshold=3, cooldown_seconds=1.0)
        assert cb.state == CircuitState.CLOSED
        await cb.before_call()
        await cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 1
    asyncio.run(_test())


def test_circuit_breaker_trips_to_open_on_threshold():
    async def _test():
        cb = CircuitBreaker(fail_threshold=3, cooldown_seconds=1.0)
        
        await cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1

        await cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2

        # 3rd consecutive failure trips to OPEN
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

        # Subsequent call must raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await cb.before_call()
        assert "Circuit breaker" in str(exc_info.value)
    asyncio.run(_test())


def test_circuit_breaker_cooldown_and_half_open_probe_success():
    async def _test():
        cb = CircuitBreaker(fail_threshold=2, cooldown_seconds=0.2)
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for cooldown to expire
        await asyncio.sleep(0.25)
        assert cb.state == CircuitState.HALF_OPEN

        # Probe call allowed through
        await cb.before_call()

        # On success, resets to CLOSED
        await cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    asyncio.run(_test())


def test_circuit_breaker_half_open_probe_failure_reopens():
    async def _test():
        cb = CircuitBreaker(fail_threshold=2, cooldown_seconds=0.2)
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN

        await asyncio.sleep(0.25)
        assert cb.state == CircuitState.HALF_OPEN

        await cb.before_call()
        # Probe fails, trips back to OPEN immediately
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN
    asyncio.run(_test())

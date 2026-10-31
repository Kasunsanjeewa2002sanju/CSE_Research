"""Tick Validator Pipeline for CSE Ingestion Service.

Enforces strict data quality rules:
1. Schema check (Pydantic model integrity)
2. Type and range bounds
3. Unit normalisation
4. Monotonic timestamp verification
5. Jump check (rejects |Δ%| > MAX_TICK_JUMP_PCT unless confirmed across 2 consecutive polls)
6. Cross-field mathematical sanity (reported change ≈ value - previous_close)

Rejected ticks are recorded as anomalies and never published.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from cse_live.config import IngestionConfig
from cse_live.models import MarketSnapshot, TickAnomaly

logger = logging.getLogger("cse_live.validator")


@dataclass
class ValidationResult:
    """Outcome of validating an incoming market tick."""
    is_valid: bool
    snapshot: Optional[MarketSnapshot] = None
    anomaly: Optional[TickAnomaly] = None


class TickValidator:
    """Stateful validation engine for incoming CSE market snapshots."""

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self.config = config or IngestionConfig.from_env()
        self.last_accepted_snapshot: Optional[MarketSnapshot] = None
        # Stores (candidate_aspi_value, confirmation_count)
        self._pending_jump_candidate: Optional[Tuple[float, int]] = None

    def reset_state(self) -> None:
        """Clear historical state (used in testing or session reset)."""
        self.last_accepted_snapshot = None
        self._pending_jump_candidate = None

    def validate(
        self,
        snapshot: MarketSnapshot,
        raw_payload: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Execute full validation pipeline on incoming MarketSnapshot."""
        payload = raw_payload or {}
        now = datetime.now()

        # Step 1 & 2: Range & Type checks
        if not (1000.0 <= snapshot.aspi_value <= 100000.0):
            anomaly = TickAnomaly(
                timestamp=now,
                reason=f"ASPI value {snapshot.aspi_value} out of bounds [1000, 100000]",
                aspi_value=snapshot.aspi_value,
                last_accepted_value=self.last_accepted_snapshot.aspi_value if self.last_accepted_snapshot else None,
                raw_payload=payload
            )
            logger.warning(f"Validation failure: {anomaly.reason}")
            return ValidationResult(is_valid=False, anomaly=anomaly)

        if not (1000.0 <= snapshot.aspi_previous_close <= 100000.0):
            anomaly = TickAnomaly(
                timestamp=now,
                reason=f"ASPI previous close {snapshot.aspi_previous_close} out of bounds [1000, 100000]",
                aspi_value=snapshot.aspi_value,
                last_accepted_value=self.last_accepted_snapshot.aspi_value if self.last_accepted_snapshot else None,
                raw_payload=payload
            )
            logger.warning(f"Validation failure: {anomaly.reason}")
            return ValidationResult(is_valid=False, anomaly=anomaly)

        if snapshot.market_turnover < 0.0:
            anomaly = TickAnomaly(
                timestamp=now,
                reason=f"Negative turnover: {snapshot.market_turnover}",
                aspi_value=snapshot.aspi_value,
                raw_payload=payload
            )
            return ValidationResult(is_valid=False, anomaly=anomaly)

        if snapshot.shares_traded < 0:
            anomaly = TickAnomaly(
                timestamp=now,
                reason=f"Negative shares traded: {snapshot.shares_traded}",
                aspi_value=snapshot.aspi_value,
                raw_payload=payload
            )
            return ValidationResult(is_valid=False, anomaly=anomaly)

        # Step 3: Unit Normalisation Check
        # Turnover must be in raw LKR; if trades > 100 and turnover is < 1,000, it was likely scaled down incorrectly
        if snapshot.total_trades > 100 and 0.0 < snapshot.market_turnover < 1000.0:
            anomaly = TickAnomaly(
                timestamp=now,
                reason=f"Turnover {snapshot.market_turnover} appears erroneously scaled down (expected raw LKR)",
                aspi_value=snapshot.aspi_value,
                raw_payload=payload
            )
            logger.error(f"Unit validation anomaly: {anomaly.reason}")
            return ValidationResult(is_valid=False, anomaly=anomaly)

        # Step 4: Monotonic Timestamp Check
        if self.last_accepted_snapshot is not None:
            prev_ts = self.last_accepted_snapshot.source_timestamp
            curr_ts = snapshot.source_timestamp
            # If same trading day, source timestamp should not regress backwards by more than 2s
            if curr_ts.date() == prev_ts.date():
                if curr_ts < (prev_ts - timedelta(seconds=2)):
                    anomaly = TickAnomaly(
                        timestamp=now,
                        reason=f"Non-monotonic timestamp regression: {curr_ts} < previous {prev_ts}",
                        aspi_value=snapshot.aspi_value,
                        last_accepted_value=self.last_accepted_snapshot.aspi_value,
                        raw_payload=payload
                    )
                    logger.warning(f"Timestamp anomaly: {anomaly.reason}")
                    return ValidationResult(is_valid=False, anomaly=anomaly)

        # Step 5: Jump Check
        if self.last_accepted_snapshot is not None:
            last_val = self.last_accepted_snapshot.aspi_value
            jump_pct = abs(snapshot.aspi_value - last_val) / last_val * 100.0
            
            if jump_pct > self.config.max_tick_jump_pct:
                # Check if this jump is justified by previous-close relation (e.g. overnight regime shift)
                # If the current tick's difference from previous close is consistent with the jump
                prev_close = snapshot.aspi_previous_close
                jump_vs_prev_close = abs(snapshot.aspi_value - prev_close) / prev_close * 100.0

                # If jump is confirmed across two consecutive polls with similar candidate value:
                if self._pending_jump_candidate is not None:
                    cand_val, count = self._pending_jump_candidate
                    if abs(snapshot.aspi_value - cand_val) / cand_val < 0.005: # within 0.5%
                        # Confirmed by 2nd consecutive poll!
                        logger.info(
                            f"Large tick jump of {jump_pct:.2f}% accepted after 2 consecutive matching polls: "
                            f"{snapshot.aspi_value}"
                        )
                        self._pending_jump_candidate = None
                    else:
                        # Value shifted again, still unconfirmed
                        self._pending_jump_candidate = (snapshot.aspi_value, 1)
                        anomaly = TickAnomaly(
                            timestamp=now,
                            reason=f"Unconfirmed tick jump of {jump_pct:.2f}% (max allowable: {self.config.max_tick_jump_pct}%)",
                            aspi_value=snapshot.aspi_value,
                            last_accepted_value=last_val,
                            jump_pct=jump_pct,
                            raw_payload=payload
                        )
                        logger.warning(f"Jump anomaly rejected: {anomaly.reason}")
                        return ValidationResult(is_valid=False, anomaly=anomaly)
                else:
                    # First observation of a large jump: hold as candidate and reject current tick
                    self._pending_jump_candidate = (snapshot.aspi_value, 1)
                    anomaly = TickAnomaly(
                        timestamp=now,
                        reason=f"Potential tick jump of {jump_pct:.2f}% flagged (awaiting 2nd confirmation poll)",
                        aspi_value=snapshot.aspi_value,
                        last_accepted_value=last_val,
                        jump_pct=jump_pct,
                        raw_payload=payload
                    )
                    logger.warning(f"Jump anomaly held: {anomaly.reason}")
                    return ValidationResult(is_valid=False, anomaly=anomaly)
            else:
                # Normal jump percentage within tolerance
                self._pending_jump_candidate = None

        # Step 6: Cross-Field Sanity Check
        # change should approximately equal aspi_value - aspi_previous_close
        expected_change = snapshot.aspi_value - snapshot.aspi_previous_close
        diff = abs(snapshot.aspi_change - expected_change)
        # Allow 0.05 points tolerance for rounding in display feeds
        if diff > 0.05:
            # If exchange sends change=0 during auction or pre-trade before first trade
            if abs(snapshot.aspi_change) > 0.01:
                anomaly = TickAnomaly(
                    timestamp=now,
                    reason=f"Cross-field inconsistency: reported change {snapshot.aspi_change} != value - prev_close ({expected_change:.2f})",
                    aspi_value=snapshot.aspi_value,
                    raw_payload=payload
                )
                logger.error(f"Sanity check failure: {anomaly.reason}")
                return ValidationResult(is_valid=False, anomaly=anomaly)

        # All checks passed! Accept tick and update state
        self.last_accepted_snapshot = snapshot
        return ValidationResult(is_valid=True, snapshot=snapshot)

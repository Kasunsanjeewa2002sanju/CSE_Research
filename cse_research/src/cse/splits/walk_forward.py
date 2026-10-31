"""Walk-forward expanding window cross-validation splits with embargo enforcement.

Adheres strictly to:
- Rule R2: No lookahead bias, strict chronological splitting, no random splits.
- Protocol: 5 phases (P1-P5), 10 trading-day embargo gap before validation,
  and 15% inner tuning split within training with its own 10-day embargo.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cse.utils.config import find_project_root, load_config
from cse.utils.logger import get_logger

logger = get_logger("cse.splits")


@dataclass
class SplitWindow:
    """Represents an indexed slice of the time-series panel."""
    start_idx: int
    end_idx: int
    start_date: str
    end_date: str
    n_days: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PhaseSplit:
    """Represents a complete expanding-window validation phase."""
    phase: str
    description: str
    train: SplitWindow
    embargo: SplitWindow
    val: SplitWindow
    inner_train: SplitWindow
    inner_embargo: SplitWindow
    inner_val: SplitWindow

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "description": self.description,
            "train": self.train.to_dict(),
            "embargo": self.embargo.to_dict(),
            "val": self.val.to_dict(),
            "inner_train": self.inner_train.to_dict(),
            "inner_embargo": self.inner_embargo.to_dict(),
            "inner_val": self.inner_val.to_dict(),
        }


class ExpandingWindowSplitter:
    """Config-driven expanding-window walk-forward splitter.
    
    Generates chronological training, embargo, and validation splits for the
    5 defined phases (P1-P5) and inner hyperparameter tuning splits.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        embargo_days: int = 10,
        inner_tune_ratio: float = 0.15,
        inner_embargo_days: int = 10,
        phases_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the splitter with a cleaned price/returns panel.
        
        Args:
            df: DataFrame containing at least a 'date' column, sorted chronologically.
            embargo_days: Trading days embargo between train and validation.
            inner_tune_ratio: Fraction of training window allocated to inner tuning validation.
            inner_embargo_days: Trading days embargo for inner tuning split.
            phases_config: Optional custom phase dictionary from config.yaml.
        """
        if "date" not in df.columns:
            raise ValueError("Input DataFrame must contain a 'date' column.")

        self.df = df.copy().reset_index(drop=True)
        self.df["date"] = pd.to_datetime(self.df["date"]).dt.strftime("%Y-%m-%d")
        
        # Verify chronological order
        dates = pd.to_datetime(self.df["date"])
        if not dates.is_monotonic_increasing:
            raise ValueError("DataFrame dates must be strictly monotonic increasing.")
        if dates.duplicated().any():
            raise ValueError("DataFrame contains duplicate dates.")

        self.embargo_days = embargo_days
        self.inner_tune_ratio = inner_tune_ratio
        self.inner_embargo_days = inner_embargo_days

        # Default 5-phase dates if not provided
        self.phases_config = phases_config or {
            "P1": {
                "val_start": "2012-01-01",
                "val_end": "2014-12-31",
                "description": "Validate 2012-2014, train before 2012-01-01",
            },
            "P2": {
                "val_start": "2015-01-01",
                "val_end": "2017-12-31",
                "description": "Validate 2015-2017, train before 2015-01-01",
            },
            "P3": {
                "val_start": "2018-01-01",
                "val_end": "2020-12-31",
                "description": "Validate 2018-2020, train before 2018-01-01",
            },
            "P4": {
                "val_start": "2021-01-01",
                "val_end": "2023-12-31",
                "description": "Validate 2021-2023, train before 2021-01-01",
            },
            "P5": {
                "val_start": "2024-01-01",
                "val_end": "2025-12-31",
                "description": "Validate 2024-2025, train before 2024-01-01",
            },
        }

        self.splits: Dict[str, PhaseSplit] = self._build_all_splits()

    def _build_window(self, start_idx: int, end_idx: int) -> SplitWindow:
        """Construct a SplitWindow slice."""
        if start_idx > end_idx or start_idx < 0 or end_idx >= len(self.df):
            raise IndexError(
                f"Invalid slice indices [{start_idx}, {end_idx}] for DataFrame of length {len(self.df)}."
            )
        start_date = str(self.df.loc[start_idx, "date"])
        end_date = str(self.df.loc[end_idx, "date"])
        n_days = end_idx - start_idx + 1
        return SplitWindow(
            start_idx=start_idx,
            end_idx=end_idx,
            start_date=start_date,
            end_date=end_date,
            n_days=n_days,
        )

    def _build_phase_split(self, phase_name: str, p_cfg: Dict[str, Any]) -> PhaseSplit:
        """Construct a single PhaseSplit with outer and inner windows."""
        val_start = p_cfg["val_start"]
        val_end = p_cfg["val_end"]
        desc = p_cfg.get("description", f"Phase {phase_name}")

        val_mask = (self.df["date"] >= val_start) & (self.df["date"] <= val_end)
        val_indices = np.where(val_mask)[0]

        if len(val_indices) == 0:
            raise ValueError(f"No trading days found in validation range [{val_start}, {val_end}].")

        first_val_idx = int(val_indices[0])
        last_val_idx = int(val_indices[-1])

        val_window = self._build_window(first_val_idx, last_val_idx)

        # Embargo window: exactly embargo_days immediately preceding validation start
        embargo_end_idx = first_val_idx - 1
        embargo_start_idx = first_val_idx - self.embargo_days
        if embargo_start_idx < 0:
            raise ValueError(
                f"Not enough historical data for {self.embargo_days} embargo days before {val_start}."
            )
        embargo_window = self._build_window(embargo_start_idx, embargo_end_idx)

        # Outer training window: [0, embargo_start_idx - 1]
        train_end_idx = embargo_start_idx - 1
        train_start_idx = 0
        train_window = self._build_window(train_start_idx, train_end_idx)

        # Inner tuning split within train window
        n_train = train_window.n_days
        n_inner_val = int(np.floor(n_train * self.inner_tune_ratio))
        if n_inner_val <= 0:
            raise ValueError(f"Inner validation size is non-positive for {phase_name}.")

        inner_val_end_idx = train_end_idx
        inner_val_start_idx = train_end_idx - n_inner_val + 1
        inner_val_window = self._build_window(inner_val_start_idx, inner_val_end_idx)

        # Inner embargo window: exactly inner_embargo_days preceding inner validation
        inner_emb_end_idx = inner_val_start_idx - 1
        inner_emb_start_idx = inner_val_start_idx - self.inner_embargo_days
        inner_emb_window = self._build_window(inner_emb_start_idx, inner_emb_end_idx)

        # Inner train window: [0, inner_emb_start_idx - 1]
        inner_train_end_idx = inner_emb_start_idx - 1
        inner_train_start_idx = 0
        inner_train_window = self._build_window(inner_train_start_idx, inner_train_end_idx)

        return PhaseSplit(
            phase=phase_name,
            description=desc,
            train=train_window,
            embargo=embargo_window,
            val=val_window,
            inner_train=inner_train_window,
            inner_embargo=inner_emb_window,
            inner_val=inner_val_window,
        )

    def _build_all_splits(self) -> Dict[str, PhaseSplit]:
        """Build all phase splits."""
        splits = {}
        for phase_name, p_cfg in self.phases_config.items():
            splits[phase_name] = self._build_phase_split(phase_name, p_cfg)
        return splits

    def get_phase(self, phase_name: str) -> PhaseSplit:
        """Retrieve a specific phase split by name ('P1'..'P5')."""
        if phase_name not in self.splits:
            raise KeyError(f"Phase '{phase_name}' not found. Available: {list(self.splits.keys())}")
        return self.splits[phase_name]

    def summary_table(self) -> pd.DataFrame:
        """Generate a summary table of row counts and date ranges across all phases."""
        rows = []
        for phase_name, split in self.splits.items():
            rows.append({
                "phase": phase_name,
                "train_dates": f"{split.train.start_date} to {split.train.end_date}",
                "train_days": split.train.n_days,
                "embargo_dates": f"{split.embargo.start_date} to {split.embargo.end_date}",
                "embargo_days": split.embargo.n_days,
                "val_dates": f"{split.val.start_date} to {split.val.end_date}",
                "val_days": split.val.n_days,
                "inner_train_days": split.inner_train.n_days,
                "inner_embargo_days": split.inner_embargo.n_days,
                "inner_val_days": split.inner_val.n_days,
            })
        return pd.DataFrame(rows)

    def plot_timeline(self, output_path: Optional[Union[str, Path]] = None) -> plt.Figure:
        """Generate a professional timeline visualization of expanding windows, embargoes, and validation blocks."""
        fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

        phase_names = list(self.splits.keys())
        y_positions = np.arange(len(phase_names))[::-1]

        # Colors adhering to professional financial UI palette
        c_train = "#2563eb"     # Royal Blue
        c_embargo = "#f59e0b"   # Amber
        c_val = "#10b981"       # Emerald Green
        c_inner_val = "#8b5cf6" # Violet

        # Use dates as matplotlib datetimes
        for idx, phase_name in enumerate(phase_names):
            y = y_positions[idx]
            split = self.splits[phase_name]

            d_train_start = pd.to_datetime(split.train.start_date)
            d_train_end = pd.to_datetime(split.train.end_date)
            d_emb_start = pd.to_datetime(split.embargo.start_date)
            d_emb_end = pd.to_datetime(split.embargo.end_date)
            d_val_start = pd.to_datetime(split.val.start_date)
            d_val_end = pd.to_datetime(split.val.end_date)

            d_inner_val_start = pd.to_datetime(split.inner_val.start_date)
            d_inner_val_end = pd.to_datetime(split.inner_val.end_date)

            # Bar height
            h = 0.55

            # Outer Train bar
            ax.barh(
                y,
                (d_train_end - d_train_start).days,
                left=d_train_start,
                height=h,
                color=c_train,
                alpha=0.85,
                edgecolor="none",
                label="Training Window" if idx == 0 else "",
            )

            # Inner val indicator strip
            ax.barh(
                y,
                (d_inner_val_end - d_inner_val_start).days,
                left=d_inner_val_start,
                height=h * 0.45,
                color=c_inner_val,
                alpha=0.9,
                edgecolor="none",
                label="Inner Tuning Val (15%)" if idx == 0 else "",
            )

            # Embargo bar
            ax.barh(
                y,
                (d_emb_end - d_emb_start).days + 1,
                left=d_emb_start,
                height=h,
                color=c_embargo,
                alpha=0.95,
                edgecolor="none",
                label="Embargo Gap (10 TD)" if idx == 0 else "",
            )

            # Validation bar
            ax.barh(
                y,
                (d_val_end - d_val_start).days,
                left=d_val_start,
                height=h,
                color=c_val,
                alpha=0.9,
                edgecolor="none",
                label="Validation Block (Out-of-Sample)" if idx == 0 else "",
            )

            # Annotation text
            ax.text(
                d_val_end + pd.Timedelta(days=25),
                y,
                f"Train: {split.train.n_days:,}d | Val: {split.val.n_days:,}d",
                va="center",
                fontsize=9,
                fontweight="bold",
                color="#1e293b",
            )

        ax.set_yticks(y_positions)
        ax.set_yticklabels(phase_names, fontsize=11, fontweight="bold")
        ax.set_xlabel("Calendar Year", fontsize=11, fontweight="bold", labelpad=10)
        ax.set_title(
            "Colombo Stock Exchange (ASPI) - 5-Phase Walk-Forward Validation Protocol\n"
            "Expanding Training Windows with 10-Trading-Day Embargo Gaps & 15% Inner Tuning Splits",
            fontsize=12,
            fontweight="bold",
            pad=15,
        )

        ax.grid(axis="x", linestyle="--", alpha=0.5)
        ax.legend(loc="lower left", framealpha=0.95, fontsize=9)
        plt.tight_layout()

        if output_path is not None:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(out_p, dpi=300, bbox_inches="tight")
            logger.info("Saved validation splits timeline figure to %s", out_p)

        return fig

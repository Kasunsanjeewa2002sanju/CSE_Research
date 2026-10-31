"""Event Study methodology for Colombo Stock Exchange ASPI around electoral event stages.

Adheres strictly to:
- Rule R1: Real data only from cse_clean and events_stage_level.
- Rule R2: Zero lookahead bias. Estimation windows precede event windows.
- Rule R6: Full persistence of tables and figures to disk.
- Rule R7: Pinned seed (42) and reproducibility.
- Proposal: 2/7/15/30-day windows, mean-adjusted return model, Brown-Warner test,
  placebo permutation test (10,000 draws), and cross-event aggregation.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from cse.utils.config import find_project_root, load_config
from cse.utils.logger import get_logger

logger = get_logger("cse.events.study")

EVENT_WINDOWS = {
    # Post-event reaction windows
    "[0,+2]": (0, 2),
    "[0,+7]": (0, 7),
    "[0,+15]": (0, 15),
    "[0,+30]": (0, 30),
    # Pre-event anticipation windows
    "[-7,-1]": (-7, -1),
    "[-15,-1]": (-15, -1),
    "[-30,-1]": (-30, -1),
    # Symmetric pre/post windows
    "[-2,+2]": (-2, 2),
    "[-7,+7]": (-7, 7),
}


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """Compute Benjamini-Hochberg (1995) False Discovery Rate (FDR) adjusted p-values."""
    p_vals = np.asarray(p_values, dtype=float)
    n = len(p_vals)
    if n == 0:
        return p_vals

    valid_mask = ~np.isnan(p_vals)
    adj_p = np.full(n, np.nan)
    if not np.any(valid_mask):
        return adj_p

    valid_p = p_vals[valid_mask]
    m = len(valid_p)
    sort_idx = np.argsort(valid_p)
    sorted_p = valid_p[sort_idx]

    # Adjusted p-value formula: p * m / rank
    ranks = np.arange(1, m + 1)
    adj_sorted = sorted_p * (m / ranks)

    # Monotonicity adjustment backward
    adj_sorted = np.minimum.accumulate(adj_sorted[::-1])[::-1]
    adj_sorted = np.clip(adj_sorted, 0.0, 1.0)

    # Invert sorting
    valid_adj = np.empty_like(adj_sorted)
    valid_adj[sort_idx] = adj_sorted
    adj_p[valid_mask] = valid_adj
    return adj_p


class EventStudyEngine:
    """Core event study calculation engine supporting mean-adjusted and market models."""

    def __init__(
        self,
        df_cse: pd.DataFrame,
        df_stages: pd.DataFrame,
        estimation_window_len: int = 15,
        model_type: str = "mean_adjusted",
        n_permutations: int = 10000,
        seed: int = 42,
    ) -> None:
        """Initialize event study engine.
        
        Args:
            df_cse: Clean daily CSE panel with 'date', 'aspi', and optional 'sp20'.
            df_stages: Stage-level event dataset with 'trading_day_index', 'election_type', 'stage'.
            estimation_window_len: Estimation window length in trading days (default 15).
            model_type: 'mean_adjusted' or 'market_model'.
            n_permutations: Number of non-event placebo draws (default 10,000).
            seed: Random seed for placebo sampling.
        """
        self.df_cse = df_cse.copy().reset_index(drop=True)
        self.df_cse["date"] = pd.to_datetime(self.df_cse["date"]).dt.strftime("%Y-%m-%d")
        
        # Calculate daily log returns
        aspi = self.df_cse["aspi"].astype(float).values
        self.returns = np.zeros(len(self.df_cse))
        self.returns[1:] = np.log(aspi[1:] / aspi[:-1])

        # S&P SL 20 returns for market model if present
        if "sp20" in self.df_cse.columns:
            sp20 = self.df_cse["sp20"].astype(float).values
            self.sp20_returns = np.full(len(self.df_cse), np.nan)
            valid_sp = ~np.isnan(sp20[1:]) & ~np.isnan(sp20[:-1]) & (sp20[:-1] > 0)
            self.sp20_returns[1:][valid_sp] = np.log(sp20[1:][valid_sp] / sp20[:-1][valid_sp])
        else:
            self.sp20_returns = np.full(len(self.df_cse), np.nan)

        self.df_stages = df_stages.copy().reset_index(drop=True)
        self.estimation_window_len = estimation_window_len
        self.model_type = model_type
        self.n_permutations = n_permutations
        self.seed = seed

        # Precompute clean non-event candidate indices
        self.non_event_pool = self._identify_non_event_pool()
        # Precompute placebo distribution across all windows
        self.placebo_car_distributions = self._generate_placebo_distributions()

    def _identify_non_event_pool(self) -> np.ndarray:
        """Identify trading days that do not fall within +/- 30 trading days of ANY event."""
        valid_indices = self.df_stages["trading_day_index"].dropna().astype(int).unique()
        event_buffer = set()
        for idx in valid_indices:
            for offset in range(-30, 31):
                event_buffer.add(idx + offset)

        n_total = len(self.df_cse)
        # Margin for estimation window (up to 120 days) and event window (+30 days)
        min_margin = 30 + 120 + 5
        max_margin = 35

        candidates = [
            i for i in range(min_margin, n_total - max_margin)
            if i not in event_buffer
        ]
        if len(candidates) < 500:
            raise RuntimeError(f"Insufficient non-event days in pool: {len(candidates)}")
        logger.info("Identified %d clean non-event candidate trading days for placebo pool.", len(candidates))
        return np.array(candidates)

    def _compute_single_event_window(
        self,
        t0: int,
        w_start: int,
        w_end: int,
        est_len: int,
    ) -> Tuple[float, float, float]:
        """Compute CAR, Brown-Warner standard error, and Brown-Warner t-stat for one event and window.
        
        Returns:
            Tuple of (CAR, BW_SE, BW_t_stat)
        """
        # Estimation window ends 1 day before the event window start: [w_start - est_len, w_start - 1]
        est_start_idx = t0 + w_start - est_len
        est_end_idx = t0 + w_start - 1
        
        if est_start_idx < 1 or est_end_idx >= len(self.returns):
            return float("nan"), float("nan"), float("nan")

        r_est = self.returns[est_start_idx : est_end_idx + 1]
        if len(r_est) < est_len or np.any(np.isnan(r_est)):
            return float("nan"), float("nan"), float("nan")

        # Event window
        evt_start_idx = t0 + w_start
        evt_end_idx = t0 + w_end
        if evt_start_idx < 1 or evt_end_idx >= len(self.returns):
            return float("nan"), float("nan"), float("nan")

        r_evt = self.returns[evt_start_idx : evt_end_idx + 1]
        if len(r_evt) == 0 or np.any(np.isnan(r_evt)):
            return float("nan"), float("nan"), float("nan")

        L_evt = w_end - w_start + 1

        if self.model_type == "mean_adjusted":
            # Constant mean return model
            r_bar = float(np.mean(r_est))
            s_ar = float(np.std(r_est, ddof=1))
            ar_evt = r_evt - r_bar
            car = float(np.sum(ar_evt))
            bw_se = s_ar * np.sqrt(L_evt)
            bw_t = car / bw_se if bw_se > 0 else 0.0
            return car, bw_se, bw_t

        elif self.model_type == "market_model":
            # OLS regression on S&P SL 20
            sp_est = self.sp20_returns[est_start_idx : est_end_idx + 1]
            sp_evt = self.sp20_returns[evt_start_idx : evt_end_idx + 1]
            if np.any(np.isnan(sp_est)) or np.any(np.isnan(sp_evt)):
                return float("nan"), float("nan"), float("nan")

            cov_mat = np.cov(r_est, sp_est)
            var_sp = cov_mat[1, 1]
            if var_sp <= 1e-12:
                beta = 0.0
            else:
                beta = cov_mat[0, 1] / var_sp
            alpha = float(np.mean(r_est) - beta * np.mean(sp_est))
            residuals = r_est - (alpha + beta * sp_est)
            s_ar = float(np.std(residuals, ddof=2))

            ar_evt = r_evt - (alpha + beta * sp_evt)
            car = float(np.sum(ar_evt))
            bw_se = s_ar * np.sqrt(L_evt)
            bw_t = car / bw_se if bw_se > 0 else 0.0
            return car, bw_se, bw_t

        else:
            raise ValueError(f"Unknown model_type: {self.model_type}")

    def _generate_placebo_distributions(self) -> Dict[str, np.ndarray]:
        """Draw 10,000 non-event pseudo-dates and compute empirical null CAR distributions."""
        rng = np.random.default_rng(self.seed)
        sampled_indices = rng.choice(self.non_event_pool, size=self.n_permutations, replace=True)

        dist: Dict[str, List[float]] = {w_name: [] for w_name in EVENT_WINDOWS.keys()}

        for w_name, (w_start, w_end) in EVENT_WINDOWS.items():
            for t0 in sampled_indices:
                car, _, _ = self._compute_single_event_window(
                    t0=t0,
                    w_start=w_start,
                    w_end=w_end,
                    est_len=self.estimation_window_len,
                )
                if not np.isnan(car):
                    dist[w_name].append(car)

        out_dist = {w_name: np.array(vals) for w_name, vals in dist.items()}
        logger.info("Generated placebo null distributions across %d windows (10,000 draws).", len(out_dist))
        return out_dist

    def run_per_event_analysis(self) -> pd.DataFrame:
        """Compute CAR, Brown-Warner t-stat, and placebo empirical p-value for every event stage and window."""
        rows = []
        valid_stages = self.df_stages[self.df_stages["trading_day_index"].notna()].copy()

        for _, stage_row in valid_stages.iterrows():
            t0 = int(stage_row["trading_day_index"])
            event_id = str(stage_row["event_id"])
            elec_type = str(stage_row["election_type"])
            stage_name = str(stage_row["stage"])
            raw_date = str(stage_row["raw_date"])
            mapped_date = str(stage_row["mapped_date"])
            province = str(stage_row["province"]) if stage_row["province"] is not None else "All"
            is_overlap = bool(stage_row["is_overlapping_30td"])
            sample_period = bool(stage_row["sample_2009_2025"])

            for w_name, (w_start, w_end) in EVENT_WINDOWS.items():
                car, bw_se, bw_t = self._compute_single_event_window(
                    t0=t0,
                    w_start=w_start,
                    w_end=w_end,
                    est_len=self.estimation_window_len,
                )

                if np.isnan(car):
                    p_bw = float("nan")
                    p_perm = float("nan")
                    pct_perm = float("nan")
                else:
                    df_t = self.estimation_window_len - 1
                    p_bw = float(2.0 * (1.0 - stats.t.cdf(np.abs(bw_t), df=df_t)))

                    # Placebo empirical two-sided p-value & percentile
                    null_cars = self.placebo_car_distributions[w_name]
                    p_perm = float(np.mean(np.abs(null_cars) >= np.abs(car)))
                    pct_perm = float(stats.percentileofscore(null_cars, car))

                rows.append({
                    "event_id": event_id,
                    "election_type": elec_type,
                    "stage": stage_name,
                    "raw_date": raw_date,
                    "mapped_date": mapped_date,
                    "province": province,
                    "trading_day_index": t0,
                    "window": w_name,
                    "w_start": w_start,
                    "w_end": w_end,
                    "estimation_len": self.estimation_window_len,
                    "model_type": self.model_type,
                    "car": car,
                    "bw_se": bw_se,
                    "bw_t_stat": bw_t,
                    "bw_p_val": p_bw,
                    "placebo_p_val": p_perm,
                    "placebo_percentile": pct_perm,
                    "is_overlapping_30td": is_overlap,
                    "sample_2009_2025": sample_period,
                })

        df_out = pd.DataFrame(rows)
        # Apply Benjamini-Hochberg FDR correction across all events and windows
        df_out["bw_p_val_bh"] = benjamini_hochberg(df_out["bw_p_val"].values)
        df_out["placebo_p_val_bh"] = benjamini_hochberg(df_out["placebo_p_val"].values)
        return df_out

    def aggregate_caar(
        self,
        df_per_event: pd.DataFrame,
        group_by_cols: List[str],
        sample_scope: str = "all",
    ) -> pd.DataFrame:
        """Aggregate cross-event Cumulative Average Abnormal Return (CAAR) with parametric and non-parametric tests.
        
        Args:
            df_per_event: DataFrame produced by run_per_event_analysis.
            group_by_cols: Grouping columns (e.g. ['election_type', 'window']).
            sample_scope: 'all' or 'non_overlapping'.
        """
        df_sub = df_per_event.copy()
        if sample_scope == "non_overlapping":
            df_sub = df_sub[~df_sub["is_overlapping_30td"]]

        records = []
        for group_keys, grp in df_sub.groupby(group_by_cols):
            if not isinstance(group_keys, tuple):
                group_keys = (group_keys,)
            grp_dict = dict(zip(group_by_cols, group_keys))

            cars = grp["car"].dropna().values
            n = len(cars)

            if n == 0:
                continue

            caar = float(np.mean(cars))
            med_car = float(np.median(cars))
            std_car = float(np.std(cars, ddof=1)) if n > 1 else 0.0

            # 1. One-sample t-test (parametric)
            if n > 1 and std_car > 1e-12:
                t_stat = caar / (std_car / np.sqrt(n))
                t_pval = float(2.0 * (1.0 - stats.t.cdf(np.abs(t_stat), df=n - 1)))
            else:
                t_stat = 0.0
                t_pval = 1.0

            # 2. Wilcoxon signed-rank test (non-parametric)
            if n >= 5 and np.any(cars != 0):
                try:
                    w_res = stats.wilcoxon(cars, alternative="two-sided")
                    w_stat = float(w_res.statistic)
                    w_pval = float(w_res.pvalue)
                except Exception:
                    w_stat, w_pval = float("nan"), float("nan")
            else:
                w_stat, w_pval = float("nan"), float("nan")

            # 3. Sign test (non-parametric)
            n_pos = int(np.sum(cars > 0))
            n_nonzero = int(np.sum(cars != 0))
            if n_nonzero > 0:
                st_res = stats.binomtest(k=n_pos, n=n_nonzero, p=0.5, alternative="two-sided")
                sign_pval = float(st_res.pvalue)
            else:
                sign_pval = 1.0

            records.append({
                **grp_dict,
                "sample_scope": sample_scope,
                "n": n,
                "warn_small_sample": (n < 5),
                "caar": caar,
                "median_car": med_car,
                "std_car": std_car,
                "t_stat": t_stat,
                "t_pval": t_pval,
                "wilcoxon_stat": w_stat,
                "wilcoxon_pval": w_pval,
                "n_positive": n_pos,
                "sign_test_pval": sign_pval,
            })

        df_agg = pd.DataFrame(records)
        if len(df_agg) > 0:
            df_agg["t_pval_bh"] = benjamini_hochberg(df_agg["t_pval"].values)
            df_agg["sign_pval_bh"] = benjamini_hochberg(df_agg["sign_test_pval"].values)
            if "wilcoxon_pval" in df_agg.columns:
                df_agg["wilcoxon_pval_bh"] = benjamini_hochberg(df_agg["wilcoxon_pval"].values)
        return df_agg

    def compute_daily_car_trajectories(
        self,
        valid_stages: pd.DataFrame,
        est_len: int = 15,
    ) -> pd.DataFrame:
        """Compute full daily abnormal return path for each event stage from tau = -30 to +30."""
        trajectories = []
        tau_range = np.arange(-30, 31)

        for _, stage_row in valid_stages.iterrows():
            t0 = int(stage_row["trading_day_index"])
            event_id = str(stage_row["event_id"])
            elec_type = str(stage_row["election_type"])
            stage_name = str(stage_row["stage"])

            # Estimation window ending 1 day before tau = -30: [t0 - 30 - est_len, t0 - 31]
            est_start = t0 - 30 - est_len
            est_end = t0 - 31
            if est_start < 1 or (t0 + 30) >= len(self.returns):
                continue

            r_est = self.returns[est_start : est_end + 1]
            if len(r_est) < est_len:
                continue

            r_bar = float(np.mean(r_est))

            # Daily abnormal returns from -30 to +30
            daily_ar = []
            for tau in tau_range:
                r_tau = float(self.returns[t0 + tau])
                daily_ar.append(r_tau - r_bar)

            daily_car = np.cumsum(daily_ar)

            for tau, ar, car in zip(tau_range, daily_ar, daily_car):
                trajectories.append({
                    "event_id": event_id,
                    "election_type": elec_type,
                    "stage": stage_name,
                    "tau": int(tau),
                    "ar": float(ar),
                    "car": float(car),
                })

        return pd.DataFrame(trajectories)

    def generate_car_curve_figures(
        self,
        output_dir: Union[str, Path],
    ) -> List[Path]:
        """Generate high-resolution CAR curve plots (-30 to +30) with 95% permutation bands."""
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        valid_stages = self.df_stages[self.df_stages["trading_day_index"].notna()].copy()
        df_traj = self.compute_daily_car_trajectories(valid_stages, est_len=self.estimation_window_len)

        # Precompute placebo trajectories across 2,000 sampled dates for the 95% null band
        rng = np.random.default_rng(self.seed)
        sampled_sub = rng.choice(self.non_event_pool, size=min(2000, len(self.non_event_pool)), replace=False)
        tau_range = np.arange(-30, 31)

        null_trajs = []
        for t0 in sampled_sub:
            est_start = t0 - 30 - self.estimation_window_len
            est_end = t0 - 31
            if est_start < 1 or (t0 + 30) >= len(self.returns):
                continue
            r_est = self.returns[est_start : est_end + 1]
            r_bar = float(np.mean(r_est))
            ar_path = self.returns[t0 - 30 : t0 + 31] - r_bar
            car_path = np.cumsum(ar_path)
            null_trajs.append(car_path)

        null_arr = np.array(null_trajs)  # shape (N_sub, 61)
        p025 = np.percentile(null_arr, 2.5, axis=0)
        p975 = np.percentile(null_arr, 97.5, axis=0)
        p50 = np.percentile(null_arr, 50.0, axis=0)

        created_files = []

        # 1. Overall CAAR by Election Type (Polling Stage)
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        ax.fill_between(tau_range, p025 * 100, p975 * 100, color="#94a3b8", alpha=0.25, label="95% Placebo Null Band")
        ax.plot(tau_range, p50 * 100, color="#64748b", linestyle="--", linewidth=1.2, label="Placebo Median")

        colors = {"Presidential": "#dc2626", "Parliamentary": "#2563eb", "Provincial Council": "#059669"}
        df_poll = df_traj[df_traj["stage"] == "polling"]

        for e_type, grp in df_poll.groupby("election_type"):
            caar_path = grp.groupby("tau")["car"].mean().reindex(tau_range).values * 100
            n_events = grp["event_id"].nunique()
            ax.plot(
                tau_range,
                caar_path,
                linewidth=2.2,
                color=colors.get(e_type, "#111827"),
                label=f"{e_type} Polls (n={n_events})",
            )

        ax.axvline(0, color="#000000", linestyle=":", linewidth=1.5, alpha=0.8, label="Polling Day (t=0)")
        ax.axhline(0, color="#9ca3af", linestyle="-", linewidth=0.8)
        ax.set_title("Colombo Stock Exchange (ASPI) - Cumulative Abnormal Return (CAR)\nPolling Date Event Trajectory (-30 to +30 Trading Days) vs 95% Permutation Band", fontsize=11, fontweight="bold")
        ax.set_xlabel("Event Time (Trading Days Relative to Poll Date)", fontsize=10, fontweight="bold")
        ax.set_ylabel("Cumulative Abnormal Return (%)", fontsize=10, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper left", framealpha=0.95, fontsize=9)
        plt.tight_layout()

        p1 = out_p / "car_curves_polling_by_election_type.png"
        fig.savefig(p1, dpi=300)
        plt.close(fig)
        created_files.append(p1)

        # 2. CAAR across Electoral Stages (Presidential Elections)
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        ax.fill_between(tau_range, p025 * 100, p975 * 100, color="#94a3b8", alpha=0.25, label="95% Placebo Null Band")

        stage_colors = {
            "announcement": "#f59e0b",
            "polling": "#dc2626",
            "result": "#10b981",
            "government_formation": "#8b5cf6",
        }
        df_pres = df_traj[df_traj["election_type"] == "Presidential"]

        for s_name in ["announcement", "polling", "result", "government_formation"]:
            grp = df_pres[df_pres["stage"] == s_name]
            if len(grp) == 0:
                continue
            caar_path = grp.groupby("tau")["car"].mean().reindex(tau_range).values * 100
            n_events = grp["event_id"].nunique()
            ax.plot(
                tau_range,
                caar_path,
                linewidth=2.0,
                color=stage_colors.get(s_name, "#4b5563"),
                label=f"Stage: {s_name.replace('_', ' ').title()} (n={n_events})",
            )

        ax.axvline(0, color="#000000", linestyle=":", linewidth=1.5, alpha=0.8)
        ax.axhline(0, color="#9ca3af", linestyle="-", linewidth=0.8)
        ax.set_title("Presidential Elections: Cumulative Abnormal Return (CAR) by Electoral Stage\nComparison Across Announcement, Polling, Result, and Government Formation", fontsize=11, fontweight="bold")
        ax.set_xlabel("Event Time (Trading Days Relative to Stage Date)", fontsize=10, fontweight="bold")
        ax.set_ylabel("Cumulative Abnormal Return (%)", fontsize=10, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper left", framealpha=0.95, fontsize=9)
        plt.tight_layout()

        p2 = out_p / "car_curves_presidential_stages.png"
        fig.savefig(p2, dpi=300)
        plt.close(fig)
        created_files.append(p2)

        return created_files

    def generate_caar_heatmap(
        self,
        df_agg_type_stage: pd.DataFrame,
        output_path: Union[str, Path],
        target_window: str = "[0,+7]",
    ) -> Path:
        """Generate a heatmap of CAAR across Election Type x Stage for a target window."""
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        df_w = df_agg_type_stage[
            (df_agg_type_stage["window"] == target_window) &
            (df_agg_type_stage["sample_scope"] == "all")
        ].copy()

        pivot_caar = df_w.pivot(index="election_type", columns="stage", values="caar") * 100.0
        pivot_n = df_w.pivot(index="election_type", columns="stage", values="n").fillna(0).astype(int)

        stages_order = ["announcement", "nomination_start", "nomination_end", "polling", "result", "government_formation"]
        types_order = ["Presidential", "Parliamentary", "Provincial Council"]

        pivot_caar = pivot_caar.reindex(index=types_order, columns=[s for s in stages_order if s in pivot_caar.columns])
        pivot_n = pivot_n.reindex(index=types_order, columns=[s for s in stages_order if s in pivot_n.columns])

        fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
        cax = ax.imshow(pivot_caar.values, cmap="coolwarm", vmin=-5.0, vmax=5.0, aspect="auto")

        cbar = fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("CAAR (%)", fontsize=10, fontweight="bold")

        ax.set_xticks(np.arange(len(pivot_caar.columns)))
        ax.set_yticks(np.arange(len(pivot_caar.index)))
        ax.set_xticklabels([c.replace("_", "\n").title() for c in pivot_caar.columns], fontsize=9, fontweight="bold")
        ax.set_yticklabels(pivot_caar.index, fontsize=10, fontweight="bold")

        # Annotate cells with CAAR% and sample size n
        for i in range(len(pivot_caar.index)):
            for j in range(len(pivot_caar.columns)):
                val = pivot_caar.iloc[i, j]
                n_val = pivot_n.iloc[i, j]
                if np.isnan(val):
                    text = "N/A"
                else:
                    text = f"{val:+.2f}%\n(n={n_val})"
                text_color = "white" if (not np.isnan(val) and abs(val) > 2.5) else "black"
                ax.text(j, i, text, ha="center", va="center", color=text_color, fontsize=8, fontweight="bold")

        ax.set_title(f"Colombo Stock Exchange (ASPI) - CAAR Heatmap by Election Type × Stage\nEvent Window {target_window} (Constant-Mean Model, 15-Day Estimation)", fontsize=11, fontweight="bold", pad=15)
        plt.tight_layout()

        fig.savefig(out_p, dpi=300)
        plt.close(fig)
        logger.info("Saved CAAR heatmap figure to %s", out_p)
        return out_p

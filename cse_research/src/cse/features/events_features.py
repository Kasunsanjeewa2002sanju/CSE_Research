"""Strictly causal event and calendar feature engineering (Feature Set C = Set B + Event & Calendar Features).

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead bias. Every indicator at date t uses ONLY observations up to the close of t.
- Event features causality invariants:
  * An election is strictly 'unknown' before its announcement_date_mapped.
  * For each date t:
    - current_stage (one-hot, 'none' if no known event is active)
    - election_type (one-hot, 'none' if no known event is active)
    - days_to_next_known_event (trading days to next known stage, -1 if none known)
    - days_since_last_stage (trading days elapsed since most recent stage, -1 if none)
    - in_window flags for [0,+2], [0,+7], [0,+15], [0,+30] around the most recent stage
    - prior_mean_CAR, prior_median_CAR, prior_n from prior_event_stats as of date t
  * Calendar features:
    - day of week (0=Mon, 4=Fri)
    - month (1=Jan, 12=Dec)
    - session_gap_days (calendar days since previous trading session)
  * FORBIDDEN:
    - No forward-looking AR/CAR or return data after date t.
    - No subjective or post-hoc political direction or outcome sentiment labels.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from cse.events.prior_stats import PriorEventStatsCalculator
from cse.features.market_activity import build_feature_set_b
from cse.utils.config import find_project_root
from cse.utils.logger import get_logger

logger = get_logger("cse.features.events")

# Canonical stage progression ordering
STAGE_ORDER: Dict[str, int] = {
    "none": 0,
    "announcement": 1,
    "nomination_start": 2,
    "nomination_end": 3,
    "polling": 4,
    "result": 5,
    "government_formation": 6,
}

ELECTION_TYPE_PRIORITY: Dict[str, int] = {
    "none": 0,
    "Provincial Council": 1,
    "Parliamentary": 2,
    "Presidential": 3,
}

ALL_STAGES: List[str] = [
    "none",
    "announcement",
    "nomination_start",
    "nomination_end",
    "polling",
    "result",
    "government_formation",
]

ALL_ELECTION_TYPES: List[str] = [
    "none",
    "Presidential",
    "Parliamentary",
    "Provincial Council",
]


def build_calendar_features(df_cse: pd.DataFrame) -> pd.DataFrame:
    """Build calendar features strictly computable at date t close.
    
    Returns DataFrame with columns:
    - cal_day_of_week: Day of week integer (0=Monday, ..., 4=Friday)
    - cal_month: Month integer (1=January, ..., 12=December)
    - cal_session_gap_days: Calendar days elapsed since previous trading session
    """
    df_cal = pd.DataFrame(index=df_cse.index)
    dates = pd.to_datetime(df_cse["date"])

    df_cal["cal_day_of_week"] = dates.dt.dayofweek
    df_cal["cal_month"] = dates.dt.month

    # Calendar days gap since previous trading session: date[t] - date[t-1]
    gaps = (dates - dates.shift(1)).dt.days
    # For the first trading day in 1994, default to 1 day
    df_cal["cal_session_gap_days"] = gaps.fillna(1.0).astype(float)

    return df_cal


def build_causal_event_features(
    df_cse: pd.DataFrame,
    df_events_event: Optional[pd.DataFrame] = None,
    df_events_stage: Optional[pd.DataFrame] = None,
    df_event_study_per_event: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Build strictly causal, as-of event features for every trading day in df_cse.
    
    Guarantees strict zero lookahead (Rule R2):
    - An election is only known on or after its announcement_date_mapped.
    - Future stages of known elections are only known if proclaimed/scheduled.
    - prior_event_stats queries strictly prior completed event windows (window_end_date < t).
    """
    root = find_project_root()

    if df_events_event is None:
        p_event = root / "data" / "processed" / "events_event_level.parquet"
        df_events_event = pd.read_parquet(p_event)
    if df_events_stage is None:
        p_stage = root / "data" / "processed" / "events_stage_level.parquet"
        df_events_stage = pd.read_parquet(p_stage)

    # Initialize PriorEventStatsCalculator
    calc = PriorEventStatsCalculator(
        df_per_event=df_event_study_per_event,
        df_cse=df_cse,
    )

    n_days = len(df_cse)
    df_cse_dates = pd.to_datetime(df_cse["date"]).dt.strftime("%Y-%m-%d").values

    # Pre-parse election stages metadata
    # Map event_id -> announcement trading day index
    event_announcements: Dict[str, int] = {}
    for _, row in df_events_event.iterrows():
        eid = row["event_id"]
        ann_date = str(row["announcement_date_mapped"])
        # Find index in cse panel
        matches = np.where(df_cse_dates == ann_date)[0]
        if len(matches) > 0:
            event_announcements[eid] = int(matches[0])
        else:
            event_announcements[eid] = -1

    # Extract all valid mapped stages with their event_id, stage, election_type, and trading_day_index
    valid_stages = []
    for _, row in df_events_stage.iterrows():
        s_idx = int(row["trading_day_index"])
        if s_idx >= 0:
            eid = row["event_id"]
            stg = row["stage"]
            etype = row["election_type"]
            ann_idx = event_announcements.get(eid, -1)
            valid_stages.append({
                "event_id": eid,
                "stage": stg,
                "election_type": etype,
                "trading_day_index": s_idx,
                "announcement_trading_day_index": ann_idx,
                "stage_order": STAGE_ORDER.get(stg, 0),
                "type_priority": ELECTION_TYPE_PRIORITY.get(etype, 0),
            })

    # Prepare feature storage arrays
    current_stages: List[str] = []
    current_types: List[str] = []
    days_to_next: List[float] = []
    days_since: List[float] = []
    in_win_2: List[int] = []
    in_win_7: List[int] = []
    in_win_15: List[int] = []
    in_win_30: List[int] = []

    prior_mean_active: List[float] = []
    prior_median_active: List[float] = []
    prior_n_active: List[int] = []

    # Window-specific prior caches to avoid redundant computations
    prior_cache: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}

    def get_cached_prior(as_of: str, etype: str, stg: str, win: str) -> Dict[str, Any]:
        key = (as_of, etype, stg, win)
        if key not in prior_cache:
            prior_cache[key] = calc.get_stats(
                as_of_date=as_of,
                election_type=etype,
                stage=stg,
                window=win,
            )
        return prior_cache[key]

    # Pre-index stages by event for final stage identification
    final_stage_per_event: Dict[str, int] = {}
    for stg_item in valid_stages:
        eid = stg_item["event_id"]
        s_idx = stg_item["trading_day_index"]
        if eid not in final_stage_per_event or s_idx > final_stage_per_event[eid]:
            final_stage_per_event[eid] = s_idx

    # Process day by day strictly chronologically
    for t in range(n_days):
        date_t = df_cse_dates[t]

        # 1. Filter known stages: Election must have been announced on or before t
        known_stages_past = []
        known_stages_future = []

        for stg_info in valid_stages:
            ann_idx = stg_info["announcement_trading_day_index"]
            # Strictly causal condition: Election must be announced on or before t
            if ann_idx >= 0 and ann_idx <= t:
                s_idx = stg_info["trading_day_index"]
                if s_idx <= t:
                    known_stages_past.append(stg_info)
                else:
                    known_stages_future.append(stg_info)

        # 2. Determine days to next known event stage
        if len(known_stages_future) > 0:
            earliest_future_idx = min(stg["trading_day_index"] for stg in known_stages_future)
            d_next = float(earliest_future_idx - t)
        else:
            d_next = -1.0  # No known future event stage

        # 3. Determine active / most recent stage
        if len(known_stages_past) == 0:
            # No stage has ever occurred as of date t
            active_stage = "none"
            active_type = "none"
            d_since = -1.0
            w2, w7, w15, w30 = 0, 0, 0, 0
            p_mean, p_median, p_n = np.nan, np.nan, 0
        else:
            # Sort past stages to find the most recent
            # Priority: 1. latest trading day index, 2. highest stage order, 3. election type priority
            known_stages_past.sort(
                key=lambda x: (x["trading_day_index"], x["stage_order"], x["type_priority"]),
                reverse=True,
            )
            top_stg = known_stages_past[0]
            eid = top_stg["event_id"]
            stg_name = top_stg["stage"]
            etype_name = top_stg["election_type"]
            stg_idx = top_stg["trading_day_index"]
            delta_t = t - stg_idx

            final_idx = final_stage_per_event.get(eid, stg_idx)
            is_past_final = (t > final_idx)
            days_past_final = t - final_idx

            # If all stages of this election have concluded and more than 30 trading days passed
            # AND no other election is active, event is no longer active
            if is_past_final and days_past_final > 30:
                active_stage = "none"
                active_type = "none"
                d_since = -1.0
                w2, w7, w15, w30 = 0, 0, 0, 0
                p_mean, p_median, p_n = np.nan, np.nan, 0
            else:
                active_stage = stg_name
                active_type = etype_name
                d_since = float(delta_t)
                w2 = 1 if 0 <= delta_t <= 2 else 0
                w7 = 1 if 0 <= delta_t <= 7 else 0
                w15 = 1 if 0 <= delta_t <= 15 else 0
                w30 = 1 if 0 <= delta_t <= 30 else 0

                # Determine active window matching delta_t
                if delta_t <= 2:
                    active_window = "[0,+2]"
                elif delta_t <= 7:
                    active_window = "[0,+7]"
                elif delta_t <= 15:
                    active_window = "[0,+15]"
                else:
                    active_window = "[0,+30]"

                # Query historical prior stats strictly as of date_t
                stat = get_cached_prior(date_t, active_type, active_stage, active_window)
                p_mean = float(stat["mean"])
                p_median = float(stat["median"])
                p_n = int(stat["n"])

        current_stages.append(active_stage)
        current_types.append(active_type)
        days_to_next.append(d_next)
        days_since.append(d_since)
        in_win_2.append(w2)
        in_win_7.append(w7)
        in_win_15.append(w15)
        in_win_30.append(w30)
        prior_mean_active.append(p_mean)
        prior_median_active.append(p_median)
        prior_n_active.append(p_n)

    # Build DataFrame
    df_events_out = pd.DataFrame(index=df_cse.index)

    # One-hot encoding of current_stage
    for s in ALL_STAGES:
        df_events_out[f"stage_{s}"] = [1 if stg == s else 0 for stg in current_stages]

    # One-hot encoding of election_type
    for etype in ALL_ELECTION_TYPES:
        col_name = "type_" + etype.lower().replace(" ", "_")
        df_events_out[col_name] = [1 if t_name == etype else 0 for t_name in current_types]

    df_events_out["days_to_next_known_event"] = days_to_next
    df_events_out["days_since_last_stage"] = days_since
    df_events_out["in_window_0_2"] = in_win_2
    df_events_out["in_window_0_7"] = in_win_7
    df_events_out["in_window_0_15"] = in_win_15
    df_events_out["in_window_0_30"] = in_win_30

    df_events_out["prior_mean_car"] = prior_mean_active
    df_events_out["prior_median_car"] = prior_median_active
    df_events_out["prior_n"] = prior_n_active

    return df_events_out


def build_feature_set_c(
    df_cse: pd.DataFrame,
    df_events_event: Optional[pd.DataFrame] = None,
    df_events_stage: Optional[pd.DataFrame] = None,
    df_event_study_per_event: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Build Feature Set C (Feature Set B + Calendar Features + Event Features).
    
    Guarantees strict zero lookahead (Rule R2).
    """
    # 1. Feature Set B (Set A + Market Activity)
    feats_b = build_feature_set_b(df_cse)

    # 2. Calendar Features
    feats_cal = build_calendar_features(df_cse)

    # 3. Causal Event Features
    feats_evt = build_causal_event_features(
        df_cse=df_cse,
        df_events_event=df_events_event,
        df_events_stage=df_events_stage,
        df_event_study_per_event=df_event_study_per_event,
    )

    # Combine into unified Set C DataFrame
    feats_c = pd.concat([feats_b, feats_cal, feats_evt], axis=1)
    return feats_c

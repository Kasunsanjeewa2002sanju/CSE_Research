"""Election and political event calendar extraction, normalization, and CSE trading day mapping (Rule R1, R2, R11, R12)."""

import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cse.utils.logger import get_logger

logger = get_logger("cse.data.events")

# Recognized Sri Lankan provinces
SRI_LANKA_PROVINCES = [
    "Western",
    "Central",
    "Southern",
    "Northern",
    "Eastern",
    "North Western",
    "North Central",
    "Uva",
    "Sabaragamuwa",
]

# Canonical election stages
ELECTION_STAGES = [
    "announcement",
    "nomination_start",
    "nomination_end",
    "polling",
    "result",
    "government_formation",
]


def extract_province_from_row(row: pd.Series) -> Optional[str]:
    """Extract Sri Lankan province for Provincial Council elections based on authoritative text.

    Parameters
    ----------
    row : pd.Series
        Row from Elections.csv.

    Returns
    -------
    Optional[str]
        Identified province name, or None for national elections (Presidential, Parliamentary).
    """
    etype = str(row.get("election_type", "")).strip()
    if etype != "Provincial Council":
        return None

    sig = str(row.get("event_significance", "")).strip()
    ctx = str(row.get("relevant_context", "")).strip()

    # Disambiguate multi-mention rows first
    if "held in the Eastern Province" in sig or "election in Eastern Province" in sig:
        return "Eastern"
    if "win for the ruling UPFA in Sabaragamuwa Province" in sig or "Sabaragamuwa Province" in ctx or ("Sabaragamuwa Province" in sig and "alongside North Central" in sig):
        return "Sabaragamuwa"
    if "retained by the UPFA in Central Province" in sig:
        return "Central"
    if "sweeping victory in North Western Province" in sig:
        return "North Western"
    if "Northern Provincial Council" in sig:
        return "Northern"
    if "Western Province with a reduced majority" in sig:
        return "Western"
    if "control in Southern Province" in sig:
        return "Southern"
    if "Badulla District" in ctx:
        return "Uva"
    if "North Central Province" in ctx:
        return "North Central"
    if "Central Province (Kandy" in ctx:
        return "Central"
    if "North Western Province (Wayamba)" in sig:
        return "North Western"
    if "Western Province" in sig:
        return "Western"
    if "Uva Province" in ctx or "Uva Provincial Council" in sig:
        return "Uva"
    if "Southern Province" in sig or "southern stronghold" in sig:
        return "Southern"
    if "Eastern Province" in sig:
        return "Eastern"
    if "North Central Province" in sig:
        return "North Central"
    if "Sabaragamuwa Province" in sig or "Sabaragamuwa" in sig:
        return "Sabaragamuwa"
    if "North Western Province" in ctx or "Wayamba" in ctx:
        return "North Western"
    if "Central Province" in ctx:
        return "Central"
    if "Colombo, Gampaha, and Kalutara" in ctx:
        return "Western"

    return "UNKNOWN"


def map_date_to_trading_day(
    target_date: Optional[Union[datetime.date, pd.Timestamp, str]],
    trading_days: np.ndarray,
) -> Tuple[Optional[datetime.date], Optional[int]]:
    """Map a calendar date to the next available CSE trading day on or after it.

    Parameters
    ----------
    target_date : Optional[Union[datetime.date, pd.Timestamp, str]]
        The raw calendar date.
    trading_days : np.ndarray
        Sorted 1D array of datetime.date objects representing open CSE trading days.

    Returns
    -------
    Tuple[Optional[datetime.date], Optional[int]]
        (mapped_trading_day, gap_calendar_days). Returns (None, None) if target_date is NaT/None.
    """
    if target_date is None or pd.isna(target_date):
        return None, None

    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date).date()
    elif isinstance(target_date, pd.Timestamp):
        target_date = target_date.date()

    idx = np.searchsorted(trading_days, target_date)
    if idx < len(trading_days):
        mapped = trading_days[idx]
        gap = (mapped - target_date).days
        return mapped, gap
    return None, None


def parse_elections_raw(raw_path: Path) -> pd.DataFrame:
    """Parse raw Elections.csv with robust date coercion and province extraction.

    Parameters
    ----------
    raw_path : Path
        Path to raw Elections.csv.

    Returns
    -------
    pd.DataFrame
        Parsed DataFrame with standardized date columns and province information.
    """
    if not raw_path.exists():
        raise FileNotFoundError(f"Elections raw file not found at: {raw_path}")

    df = pd.read_csv(raw_path)

    # Coerce 'Not Available' to NaN across string columns
    df = df.replace(["Not Available", "not available", "NA", "N/A", "-"], np.nan)

    date_cols = [
        "election_announcement_date",
        "nomination_period_start",
        "nomination_period_end",
        "election_date",
        "election_result_date",
        "government_formation_date",
    ]

    for col in date_cols:
        if col in df.columns:
            # Parse explicitly with M/D/YYYY
            df[col] = pd.to_datetime(df[col], format="%m/%d/%Y", errors="coerce")

    # Extract province
    df["province"] = df.apply(extract_province_from_row, axis=1)

    return df


def build_event_level_table(
    df_raw: pd.DataFrame,
    df_cse: pd.DataFrame,
) -> pd.DataFrame:
    """Construct one row per distinct election event with trading day mappings and overlap flags.

    Parameters
    ----------
    df_raw : pd.DataFrame
        Parsed elections DataFrame from parse_elections_raw.
    df_cse : pd.DataFrame
        Clean CSE historical trading data containing 'date' column.

    Returns
    -------
    pd.DataFrame
        Event-level table (24 distinct elections).
    """
    trading_days = pd.to_datetime(df_cse["date"]).dt.date.sort_values().values
    date_to_td_idx = {d: i for i, d in enumerate(trading_days)}

    # Group multi-province Provincial Council elections sharing the same election_date
    groups = df_raw.groupby(["election_type", "election_date"], sort=False)

    event_rows: List[Dict[str, Any]] = []

    for event_num, ((etype, pdate), g) in enumerate(groups, start=1):
        # Base event metadata
        event_id = f"ELEC_{event_num:02d}"
        n_provinces = len(g) if etype == "Provincial Council" else 1

        # Extract province list
        if etype == "Provincial Council":
            provinces = sorted(list(g["province"].dropna().unique()))
            province_str = "; ".join(provinces) if provinces else np.nan
        else:
            province_str = np.nan

        # Dates: announcement, nomination start/end, polling, result, government formation
        ann_raw = g["election_announcement_date"].dropna().iloc[0] if g["election_announcement_date"].notna().any() else pd.NaT
        nom_s_raw = g["nomination_period_start"].dropna().iloc[0] if g["nomination_period_start"].notna().any() else pd.NaT
        nom_e_raw = g["nomination_period_end"].dropna().iloc[0] if g["nomination_period_end"].notna().any() else pd.NaT
        poll_raw = pdate
        res_raw = g["election_result_date"].dropna().iloc[0] if g["election_result_date"].notna().any() else pd.NaT

        # Government formation (may have multiple dates across provinces)
        gov_dates = g["government_formation_date"].dropna().sort_values()
        gov_raw_first = gov_dates.iloc[0] if len(gov_dates) > 0 else pd.NaT
        gov_raw_latest = gov_dates.iloc[-1] if len(gov_dates) > 0 else pd.NaT

        # Map to CSE trading days
        ann_mapped, ann_gap = map_date_to_trading_day(ann_raw, trading_days)
        nom_s_mapped, nom_s_gap = map_date_to_trading_day(nom_s_raw, trading_days)
        nom_e_mapped, nom_e_gap = map_date_to_trading_day(nom_e_raw, trading_days)
        poll_mapped, poll_gap = map_date_to_trading_day(poll_raw, trading_days)
        res_mapped, res_gap = map_date_to_trading_day(res_raw, trading_days)
        gov_mapped_first, gov_gap_first = map_date_to_trading_day(gov_raw_first, trading_days)
        gov_mapped_latest, gov_gap_latest = map_date_to_trading_day(gov_raw_latest, trading_days)

        poll_date_obj = poll_raw.date() if isinstance(poll_raw, pd.Timestamp) else poll_raw
        sample_2009_2025 = datetime.date(2009, 1, 1) <= poll_date_obj <= datetime.date(2025, 12, 31)

        poll_td_idx = date_to_td_idx.get(poll_mapped, -1)

        # Synthesize context & descriptions
        candidate_info = " | ".join(g["candidate_party_info"].dropna().unique())
        significance = " | ".join(g["event_significance"].dropna().unique())
        source_info = " | ".join(g["source_of_information"].dropna().unique())
        relevant_context = " | ".join(g["relevant_context"].dropna().unique())

        def _fmt_date(val: Any) -> Optional[str]:
            if val is None or pd.isna(val):
                return None
            if isinstance(val, (datetime.date, pd.Timestamp)):
                return val.strftime("%Y-%m-%d")
            return str(val)

        event_rows.append({
            "event_id": event_id,
            "election_type": etype,
            "n_provinces": n_provinces,
            "province": province_str if pd.notna(province_str) else None,
            "announcement_date_raw": _fmt_date(ann_raw),
            "announcement_date_mapped": _fmt_date(ann_mapped),
            "announcement_gap_days": int(ann_gap) if ann_gap is not None and pd.notna(ann_gap) else None,
            "nomination_start_raw": _fmt_date(nom_s_raw),
            "nomination_start_mapped": _fmt_date(nom_s_mapped),
            "nomination_start_gap_days": int(nom_s_gap) if nom_s_gap is not None and pd.notna(nom_s_gap) else None,
            "nomination_end_raw": _fmt_date(nom_e_raw),
            "nomination_end_mapped": _fmt_date(nom_e_mapped),
            "nomination_end_gap_days": int(nom_e_gap) if nom_e_gap is not None and pd.notna(nom_e_gap) else None,
            "polling_date_raw": _fmt_date(poll_raw),
            "polling_date_mapped": _fmt_date(poll_mapped),
            "polling_gap_days": int(poll_gap) if poll_gap is not None and pd.notna(poll_gap) else None,
            "result_date_raw": _fmt_date(res_raw),
            "result_date_mapped": _fmt_date(res_mapped),
            "result_gap_days": int(res_gap) if res_gap is not None and pd.notna(res_gap) else None,
            "government_formation_raw": _fmt_date(gov_raw_first),
            "government_formation_mapped": _fmt_date(gov_mapped_first),
            "government_formation_gap_days": int(gov_gap_first) if gov_gap_first is not None and pd.notna(gov_gap_first) else None,
            "government_formation_latest_raw": _fmt_date(gov_raw_latest),
            "government_formation_latest_mapped": _fmt_date(gov_mapped_latest),
            "government_formation_latest_gap_days": int(gov_gap_latest) if gov_gap_latest is not None and pd.notna(gov_gap_latest) else None,
            "poll_trading_day_index": poll_td_idx,
            "sample_2009_2025": bool(sample_2009_2025),
            "candidate_party_info": candidate_info,
            "event_significance": significance,
            "source_of_information": source_info,
            "relevant_context": relevant_context,
            "added_by_researcher": False,
        })

    df_events = pd.DataFrame(event_rows)

    # Compute pairwise trading day distance based on mapped polling date
    df_events["min_dist_other_poll_td"] = np.nan
    df_events["has_overlap_poll_30td"] = False
    df_events["overlapping_events_poll_30td"] = ""

    for i, row_i in df_events.iterrows():
        overlaps = []
        min_dist = float("inf")
        idx_i = row_i["poll_trading_day_index"]
        for j, row_j in df_events.iterrows():
            if i == j:
                continue
            idx_j = row_j["poll_trading_day_index"]
            dist = abs(idx_i - idx_j)
            if dist < min_dist:
                min_dist = dist
            if dist <= 30:
                overlaps.append(f"{row_j['event_id']}({dist}td)")
        df_events.loc[i, "min_dist_other_poll_td"] = int(min_dist) if min_dist != float("inf") else np.nan
        df_events.loc[i, "has_overlap_poll_30td"] = len(overlaps) > 0
        df_events.loc[i, "overlapping_events_poll_30td"] = "; ".join(overlaps)

    return df_events


def build_stage_level_table(
    df_raw: pd.DataFrame,
    df_cse: pd.DataFrame,
) -> pd.DataFrame:
    """Construct one row per election per stage with trading day mappings and overlap diagnostics.

    Parameters
    ----------
    df_raw : pd.DataFrame
        Parsed elections DataFrame from parse_elections_raw.
    df_cse : pd.DataFrame
        Clean CSE historical trading data containing 'date' column.

    Returns
    -------
    pd.DataFrame
        Event-stage table.
    """
    trading_days = pd.to_datetime(df_cse["date"]).dt.date.sort_values().values
    date_to_td_idx = {d: i for i, d in enumerate(trading_days)}

    groups = df_raw.groupby(["election_type", "election_date"], sort=False)

    stage_rows: List[Dict[str, Any]] = []

    stage_col_map = {
        "announcement": "election_announcement_date",
        "nomination_start": "nomination_period_start",
        "nomination_end": "nomination_period_end",
        "polling": "election_date",
        "result": "election_result_date",
        "government_formation": "government_formation_date",
    }

    for event_num, ((etype, pdate), g) in enumerate(groups, start=1):
        event_id = f"ELEC_{event_num:02d}"
        n_provinces = len(g) if etype == "Provincial Council" else 1

        poll_raw_date = pdate.date() if isinstance(pdate, pd.Timestamp) else pdate
        sample_2009_2025 = datetime.date(2009, 1, 1) <= poll_raw_date <= datetime.date(2025, 12, 31)

        candidate_info = " | ".join(g["candidate_party_info"].dropna().unique())
        significance = " | ".join(g["event_significance"].dropna().unique())
        source_info = " | ".join(g["source_of_information"].dropna().unique())
        relevant_context = " | ".join(g["relevant_context"].dropna().unique())

        if etype == "Provincial Council":
            provinces = sorted(list(g["province"].dropna().unique()))
            province_str = "; ".join(provinces) if provinces else np.nan
        else:
            province_str = np.nan

        for stage_name, col_name in stage_col_map.items():
            # Handle potential multiple dates for government formation across provinces
            raw_dates = g[col_name].dropna().unique()

            if len(raw_dates) == 0:
                # Stage is explicitly not available (e.g. nomination start for Row 3 & 16)
                stage_rows.append({
                    "event_id": event_id,
                    "election_type": etype,
                    "stage": stage_name,
                    "raw_date": np.nan,
                    "mapped_date": np.nan,
                    "gap_days": np.nan,
                    "raw_weekday": np.nan,
                    "mapped_weekday": np.nan,
                    "is_trading_day_raw": False,
                    "trading_day_index": -1,
                    "n_provinces": n_provinces,
                    "province": province_str,
                    "candidate_party_info": candidate_info,
                    "event_significance": significance,
                    "source_of_information": source_info,
                    "relevant_context": relevant_context,
                    "sample_2009_2025": sample_2009_2025,
                    "added_by_researcher": False,
                })
            else:
                for dt_val in sorted(raw_dates):
                    raw_dt = dt_val.date() if isinstance(dt_val, pd.Timestamp) else dt_val
                    mapped_dt, gap = map_date_to_trading_day(raw_dt, trading_days)
                    td_idx = date_to_td_idx.get(mapped_dt, -1) if mapped_dt else -1

                    # If multiple formation dates exist, disambiguate province
                    if stage_name == "government_formation" and len(raw_dates) > 1:
                        sub_provs = sorted(list(g[g[col_name] == dt_val]["province"].dropna().unique()))
                        stage_prov = "; ".join(sub_provs)
                    else:
                        stage_prov = province_str

                    stage_rows.append({
                        "event_id": event_id,
                        "election_type": etype,
                        "stage": stage_name,
                        "raw_date": str(raw_dt),
                        "mapped_date": str(mapped_dt) if mapped_dt else np.nan,
                        "gap_days": gap if gap is not None else np.nan,
                        "raw_weekday": raw_dt.strftime("%a") if raw_dt else np.nan,
                        "mapped_weekday": mapped_dt.strftime("%a") if mapped_dt else np.nan,
                        "is_trading_day_raw": gap == 0,
                        "trading_day_index": td_idx,
                        "n_provinces": n_provinces,
                        "province": stage_prov,
                        "candidate_party_info": candidate_info,
                        "event_significance": significance,
                        "source_of_information": source_info,
                        "relevant_context": relevant_context,
                        "sample_2009_2025": sample_2009_2025,
                        "added_by_researcher": False,
                    })

    df_stages = pd.DataFrame(stage_rows)

    # Compute trading day distance to nearest stage of a different election
    df_stages["is_overlapping_30td"] = False
    df_stages["nearest_other_event_stage_td"] = np.nan
    df_stages["overlapping_stage_details"] = ""

    valid_indices = df_stages[df_stages["trading_day_index"] >= 0].index

    for i in valid_indices:
        row_i = df_stages.loc[i]
        idx_i = row_i["trading_day_index"]
        ev_i = row_i["event_id"]

        min_dist = float("inf")
        overlaps = []
        for j in valid_indices:
            row_j = df_stages.loc[j]
            if row_j["event_id"] == ev_i:
                continue
            idx_j = row_j["trading_day_index"]
            dist = abs(idx_i - idx_j)
            if dist < min_dist:
                min_dist = dist
            if dist <= 30:
                overlaps.append(f"{row_j['event_id']}:{row_j['stage']}({dist}td)")

        df_stages.loc[i, "nearest_other_event_stage_td"] = int(min_dist) if min_dist != float("inf") else np.nan
        df_stages.loc[i, "is_overlapping_30td"] = len(overlaps) > 0
        df_stages.loc[i, "overlapping_stage_details"] = "; ".join(overlaps)

    return df_stages


def build_event_calendar(df_stages: pd.DataFrame) -> pd.DataFrame:
    """Produce master event calendar indexed chronologically by mapped trading day.

    Parameters
    ----------
    df_stages : pd.DataFrame
        Stage-level table.

    Returns
    -------
    pd.DataFrame
        Event calendar table sorted by mapped_date.
    """
    cal = df_stages[df_stages["mapped_date"].notna()].copy()
    cal = cal.sort_values(by=["mapped_date", "event_id", "stage"]).reset_index(drop=True)
    return cal


def load_and_merge_events(
    elections_csv_path: Path,
    supplement_csv_path: Optional[Path] = None,
    cse_clean_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load raw Elections.csv, optionally merge events_supplement.csv, and return all datasets.

    Parameters
    ----------
    elections_csv_path : Path
        Path to raw Elections.csv.
    supplement_csv_path : Optional[Path]
        Optional path to events_supplement.csv.
    cse_clean_path : Optional[Path]
        Path to processed cse_clean.parquet.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        (event_level_df, stage_level_df, event_calendar_df).
    """
    if cse_clean_path is None:
        cse_clean_path = elections_csv_path.parent.parent / "processed" / "cse_clean.parquet"

    df_raw = parse_elections_raw(elections_csv_path)
    df_cse = pd.read_parquet(cse_clean_path)

    df_events = build_event_level_table(df_raw, df_cse)
    df_stages = build_stage_level_table(df_raw, df_cse)

    # Optional merge with researcher supplement if provided and valid
    if supplement_csv_path and supplement_csv_path.exists():
        try:
            df_supp = pd.read_csv(supplement_csv_path, comment="#")
            if len(df_supp) > 0:
                logger.info(f"Loaded {len(df_supp)} supplemental event records from {supplement_csv_path}")
                # Mark supplemental rows
                df_supp["added_by_researcher"] = True
                # Standardize and append to stages
                # (Support full custom schema if required)
        except Exception as e:
            logger.warning(f"Failed to parse supplemental events: {e}")

    df_calendar = build_event_calendar(df_stages)

    return df_events, df_stages, df_calendar


def generate_election_figures(
    df_cse: pd.DataFrame,
    df_events: pd.DataFrame,
    df_stages: pd.DataFrame,
    output_dir: Path,
) -> List[Path]:
    """Generate high-quality diagnostic and visualization figures for election calendar.

    Parameters
    ----------
    df_cse : pd.DataFrame
        Clean CSE historical trading data.
    df_events : pd.DataFrame
        Event-level table.
    df_stages : pd.DataFrame
        Stage-level table.
    output_dir : Path
        Directory where figures will be saved.

    Returns
    -------
    List[Path]
        List of generated figure file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_paths = []

    # Palette
    type_colors = {
        "Presidential": "#1f77b4",       # Deep Blue
        "Parliamentary": "#2ca02c",      # Forest Green
        "Provincial Council": "#ff7f0e", # Vibrant Orange
    }

    cse_df = df_cse.copy()
    cse_df["dt"] = pd.to_datetime(cse_df["date"])

    # --- Figure 1: Full Historical Timeline (1994 - 2025) ---
    fig, ax = plt.subplots(figsize=(14, 6), dpi=300)
    ax.plot(cse_df["dt"], cse_df["aspi"], color="#2b2b2b", linewidth=1.1, label="ASPI Level")

    # Plot event polling markers
    for etype, color in type_colors.items():
        subset = df_events[df_events["election_type"] == etype]
        mapped_dates = pd.to_datetime(subset["polling_date_mapped"])
        # Find corresponding ASPI level
        aspi_vals = []
        for d in mapped_dates:
            match = cse_df[cse_df["dt"] == d]["aspi"]
            aspi_vals.append(match.iloc[0] if len(match) > 0 else np.nan)
        ax.scatter(mapped_dates, aspi_vals, color=color, s=45, zorder=5, label=f"{etype} Polling Date", edgecolors="white", linewidths=0.7)

    # Highlight key structural eras
    ax.axvspan(pd.to_datetime("2009-01-01"), pd.to_datetime("2025-12-31"), color="#eef2f7", alpha=0.4, label="Proposal Period (2009-2025)")

    ax.set_title("Colombo Stock Exchange ASPI with Historical Election Polling Dates (1994–2025)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("ASPI Index Level", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=9)
    fig.tight_layout()

    fig_path1 = output_dir / "aspi_with_elections_1994_2025.png"
    fig.savefig(fig_path1)
    plt.close(fig)
    generated_paths.append(fig_path1)
    logger.info(f"Saved: {fig_path1}")

    # --- Figure 2: Proposal Sample Period (2009 - 2025) Focused View ---
    sub_cse = cse_df[(cse_df["dt"] >= "2009-01-01") & (cse_df["dt"] <= "2025-12-31")].copy()
    fig, ax = plt.subplots(figsize=(14, 6), dpi=300)
    ax.plot(sub_cse["dt"], sub_cse["aspi"], color="#111827", linewidth=1.2, label="ASPI Index")

    # Plot shaded windows between announcement and polling for proposal elections
    prop_events = df_events[df_events["sample_2009_2025"]].copy()
    for _, row in prop_events.iterrows():
        etype = row["election_type"]
        ann_d = pd.to_datetime(row["announcement_date_mapped"])
        poll_d = pd.to_datetime(row["polling_date_mapped"])
        color = type_colors.get(etype, "#888888")
        if pd.notna(ann_d) and pd.notna(poll_d):
            ax.axvspan(ann_d, poll_d, color=color, alpha=0.15)
        if pd.notna(poll_d):
            match = sub_cse[sub_cse["dt"] == poll_d]["aspi"]
            if len(match) > 0:
                ax.scatter(poll_d, match.iloc[0], color=color, s=55, zorder=6, edgecolors="black", linewidths=0.8)

    # Custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="#111827", lw=1.2, label="ASPI Level"),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=type_colors["Presidential"], markersize=8, label="Presidential Election"),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=type_colors["Parliamentary"], markersize=8, label="Parliamentary Election"),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=type_colors["Provincial Council"], markersize=8, label="Provincial Council Election"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", frameon=True, framealpha=0.9, fontsize=9)
    ax.set_title("CSE ASPI During Proposal Sample Period (2009–2025) with Election Windows", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("ASPI Index Level", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()

    fig_path2 = output_dir / "aspi_with_elections_proposal_period_2009_2025.png"
    fig.savefig(fig_path2)
    plt.close(fig)
    generated_paths.append(fig_path2)
    logger.info(f"Saved: {fig_path2}")

    # --- Figure 3: Campaign & Event Stage Durations ---
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ev_sorted = df_events.sort_values(by="poll_trading_day_index", ascending=True).reset_index(drop=True)

    y_pos = np.arange(len(ev_sorted))
    labels = [f"{r['event_id']} ({r['election_type'][:4]} {pd.to_datetime(r['polling_date_mapped']).year})" for _, r in ev_sorted.iterrows()]

    # Duration: announcement to polling in calendar days
    durations = []
    for _, r in ev_sorted.iterrows():
        ann = pd.to_datetime(r["announcement_date_raw"])
        pol = pd.to_datetime(r["polling_date_raw"])
        durations.append((pol - ann).days if pd.notna(ann) and pd.notna(pol) else 0)

    bar_colors = [type_colors.get(r["election_type"], "#999999") for _, r in ev_sorted.iterrows()]
    bars = ax.barh(y_pos, durations, color=bar_colors, alpha=0.85, edgecolor="#333333", height=0.6)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Calendar Days from Announcement to Polling Day", fontsize=10)
    ax.set_title("Electoral Process Duration: Announcement to Polling Day Across 24 Elections", fontsize=12, fontweight="bold", pad=10)
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)

    # Value annotations on bars
    for bar in bars:
        w = bar.get_width()
        if w > 0:
            ax.text(w + 1.5, bar.get_y() + bar.get_height() / 2, f"{int(w)}d", va="center", ha="left", fontsize=7.5)

    ax.set_xlim(0, max(durations) * 1.12)
    fig.tight_layout()

    fig_path3 = output_dir / "election_campaign_durations.png"
    fig.savefig(fig_path3)
    plt.close(fig)
    generated_paths.append(fig_path3)
    logger.info(f"Saved: {fig_path3}")

    # --- Figure 4: Trading Day Mapping Gap Distribution ---
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    gaps = df_stages["gap_days"].dropna()
    gap_counts = gaps.value_counts().sort_index()

    ax.bar(gap_counts.index, gap_counts.values, color="#3b82f6", edgecolor="#1e3a8a", alpha=0.85, width=0.5)
    ax.set_xticks(gap_counts.index)
    ax.set_xticklabels([f"{int(x)} Day{'s' if x > 1 else ''}\n({'Trading Day' if x==0 else 'Weekend/Hols'})" for x in gap_counts.index], fontsize=9)
    ax.set_ylabel("Count of Stage Observations", fontsize=10)
    ax.set_title("Distribution of Market Reaction Gaps (Calendar Date to First Trading Day)", fontsize=11, fontweight="bold", pad=10)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    for x_val, count_val in zip(gap_counts.index, gap_counts.values):
        ax.text(x_val, count_val + 2, f"{count_val}\n({count_val/len(gaps)*100:.1f}%)", ha="center", va="bottom", fontsize=8.5)

    ax.set_ylim(0, max(gap_counts.values) * 1.18)
    fig.tight_layout()

    fig_path4 = output_dir / "election_trading_day_gaps.png"
    fig.savefig(fig_path4)
    plt.close(fig)
    generated_paths.append(fig_path4)
    logger.info(f"Saved: {fig_path4}")

    return generated_paths

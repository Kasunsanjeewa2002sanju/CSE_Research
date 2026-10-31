"""
Scenario Feature Vector Builder for Stage 11.

Builds feature vectors for Scenario TRUE and Scenario FALSE adhering to strict
zero-lookahead causal rules and Stage 4 event-study priors.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from cse.events.prior_stats import prior_event_stats
from cse.news.prior_calculator import get_prior_calculator
from cse.news.schema import NewsExtraction
from cse.utils.config import find_project_root


ROOT_DIR = find_project_root()
FEATURES_C_PATH = ROOT_DIR / "data" / "processed" / "features_set_c.parquet"
CSE_CLEAN_PATH = ROOT_DIR / "data" / "processed" / "cse_clean.parquet"
FEATURE_COLS_PATH = ROOT_DIR / "models" / "final" / "feature_columns.json"


class ScenarioFeatureBuilder:
    """Constructs X_TRUE and X_FALSE feature rows for news scenarios."""

    def __init__(self) -> None:
        self.df_features_c = pd.read_parquet(FEATURES_C_PATH)
        self.df_cse = pd.read_parquet(CSE_CLEAN_PATH)
        self.df_cse["date_str"] = pd.to_datetime(self.df_cse["date"]).dt.strftime("%Y-%m-%d")
        
        with open(FEATURE_COLS_PATH, "r", encoding="utf-8") as f:
            self.feature_cols: List[str] = json.load(f)

    def resolve_date_and_aspi(
        self,
        news_date: Optional[str] = None,
        override_aspi: Optional[float] = None,
    ) -> Tuple[str, float, int, bool]:
        """
        Locate the latest available trading date on or before news_date.
        
        Returns:
            (resolved_date, aspi_level, row_idx, is_stale)
        """
        max_db_date = self.df_cse["date_str"].max()

        if not news_date:
            row_idx = len(self.df_cse) - 1
            res_date = self.df_cse.loc[row_idx, "date_str"]
            aspi = override_aspi if override_aspi is not None else float(self.df_cse.loc[row_idx, "aspi"])
            return res_date, aspi, row_idx, False

        # Format input date
        clean_date = news_date.strip()[:10]
        is_stale = False

        if clean_date > max_db_date:
            is_stale = True
            row_idx = len(self.df_cse) - 1
            res_date = max_db_date
            aspi = override_aspi if override_aspi is not None else float(self.df_cse.loc[row_idx, "aspi"])
            return clean_date, aspi, row_idx, is_stale

        # Find closest date on or before clean_date
        past_dates = self.df_cse[self.df_cse["date_str"] <= clean_date]
        if past_dates.empty:
            row_idx = 0
            res_date = self.df_cse.loc[0, "date_str"]
        else:
            row_idx = int(past_dates.index[-1])
            res_date = self.df_cse.loc[row_idx, "date_str"]

        aspi = override_aspi if override_aspi is not None else float(self.df_cse.loc[row_idx, "aspi"])
        return res_date, aspi, row_idx, is_stale

    def build_scenario_features(
        self,
        news_item: NewsExtraction,
        row_idx: int,
        as_of_date: str,
        headline: Optional[str] = None,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Build X_TRUE and X_FALSE vectors for the model.
        
        Returns:
            (x_true, x_false, event_metadata)
        """
        # Start from base row market technical features
        base_series = self.df_features_c.iloc[row_idx].copy()

        # 1. Build X_FALSE (inert baseline: no event active)
        false_series = base_series.copy()
        for col in [
            "stage_announcement",
            "stage_nomination_start",
            "stage_nomination_end",
            "stage_polling",
            "stage_result",
            "stage_government_formation",
            "type_presidential",
            "type_parliamentary",
            "type_provincial_council",
            "in_window_0_2",
            "in_window_0_7",
            "in_window_0_15",
            "in_window_0_30",
        ]:
            if col in false_series:
                false_series[col] = 0.0

        if "stage_none" in false_series:
            false_series["stage_none"] = 1.0
        if "type_none" in false_series:
            false_series["type_none"] = 1.0
        if "days_to_next_known_event" in false_series:
            false_series["days_to_next_known_event"] = -1.0
        if "days_since_last_stage" in false_series:
            false_series["days_since_last_stage"] = -1.0
        if "prior_mean_car" in false_series:
            false_series["prior_mean_car"] = 0.0
        if "prior_median_car" in false_series:
            false_series["prior_median_car"] = 0.0
        if "prior_n" in false_series:
            false_series["prior_n"] = 0.0

        # 2. Build X_TRUE
        true_series = base_series.copy()
        event_meta: Dict[str, Any] = {}

        if not news_item.is_relevant or news_item.event_category == "not_relevant":
            # Sanity rule: Irrelevant news yields X_TRUE == X_FALSE
            true_series = false_series.copy()
            event_meta = {"is_active_event": False, "category": "not_relevant"}
        else:
            event_meta = {
                "is_active_event": True,
                "category": news_item.event_category,
                "stage": news_item.stage,
                "expected_direction": news_item.expected_direction,
            }

            # Zero out all stages first
            for stg_col in [
                "stage_none",
                "stage_announcement",
                "stage_nomination_start",
                "stage_nomination_end",
                "stage_polling",
                "stage_result",
                "stage_government_formation",
            ]:
                if stg_col in true_series:
                    true_series[stg_col] = 0.0

            # Zero out all types first
            for type_col in ["type_none", "type_presidential", "type_parliamentary", "type_provincial_council"]:
                if type_col in true_series:
                    true_series[type_col] = 0.0

            target_headline = headline or getattr(news_item, "headline", "") or ""
            target_date = as_of_date or "2025-01-01"
            elec_type_query = None

            # Stage 5: Enhanced Multi-Label Event and Stage Extraction with continuous confidence scores
            if target_headline:
                try:
                    from cse.news.enhanced_extractor import get_enhanced_extractor
                    enhanced_ext = get_enhanced_extractor()
                    enhanced_info = enhanced_ext.extract(
                        headline=target_headline,
                        published_at=target_date,
                    )
                    event_meta["enhanced_extraction"] = enhanced_info

                    if enhanced_info.get("primary_category") == "not_relevant":
                        true_series = false_series.copy()
                        event_meta = {"is_active_event": False, "category": "not_relevant", "enhanced_extraction": enhanced_info}
                        x_true = true_series[self.feature_cols].values.astype(float).reshape(1, -1)
                        x_false = false_series[self.feature_cols].values.astype(float).reshape(1, -1)
                        return x_true, x_false, event_meta

                    conf_feats = enhanced_ext.map_to_feature_columns(enhanced_info, self.feature_cols)
                    for col_name, col_val in conf_feats.items():
                        if col_name in true_series:
                            true_series[col_name] = float(col_val)

                    if conf_feats.get("type_presidential", 0.0) >= 0.5:
                        elec_type_query = "Presidential"
                    elif conf_feats.get("type_parliamentary", 0.0) >= 0.5:
                        elec_type_query = "Parliamentary"
                    elif conf_feats.get("type_provincial_council", 0.0) >= 0.5:
                        elec_type_query = "Provincial Council"
                except Exception as e:
                    logger.warning("Enhanced extraction failed (%s). Using categorical fallback.", e)
                    target_headline = ""

            if not target_headline:
                # Categorical fallback if no headline was provided
                stg = (news_item.stage or "").lower()
                if "announce" in stg:
                    true_series["stage_announcement"] = 1.0
                elif "nominat" in stg and "start" in stg:
                    true_series["stage_nomination_start"] = 1.0
                elif "nominat" in stg:
                    true_series["stage_nomination_end"] = 1.0
                elif "poll" in stg or "voting" in stg:
                    true_series["stage_polling"] = 1.0
                elif "result" in stg:
                    true_series["stage_result"] = 1.0
                elif "formation" in stg or "sworn" in stg:
                    true_series["stage_government_formation"] = 1.0
                else:
                    true_series["stage_announcement"] = 1.0

                cat = news_item.event_category
                if cat == "presidential_election":
                    true_series["type_presidential"] = 1.0
                    elec_type_query = "Presidential"
                elif cat == "parliamentary_election":
                    true_series["type_parliamentary"] = 1.0
                    elec_type_query = "Parliamentary"
                elif cat in {"provincial_council_election", "local_government_election"}:
                    true_series["type_provincial_council"] = 1.0
                    elec_type_query = "Provincial Council"
                else:
                    true_series["type_none"] = 1.0
                    elec_type_query = None

            # Set dynamic proximity variables via Stage 4 Proximity Calculator
            from cse.news.proximity_calculator import calculate_proximity_features
            prox_info = calculate_proximity_features(
                headline=target_headline,
                news_date=target_date,
            )
            event_meta["proximity_info"] = prox_info

            true_series["days_to_next_known_event"] = float(prox_info["days_to_next_known_event"])
            true_series["days_since_last_stage"] = 0.0
            true_series["in_window_0_2"] = float(prox_info["in_window_0_2"])
            true_series["in_window_0_7"] = float(prox_info["in_window_0_7"])
            true_series["in_window_0_15"] = float(prox_info["in_window_0_15"])
            true_series["in_window_0_30"] = float(prox_info["in_window_0_30"])

            # Query Stage 3 prior calculator using kNN event study if headline is provided
            prior_calc = get_prior_calculator()
            if target_headline:
                p_info = prior_calc.get_prior(
                    headline=target_headline,
                    horizon=5,
                    k=10,
                    category_filter=True,
                )
                m_car = float(p_info["prior_mean_car"])
                med_car = float(p_info["prior_median_car"])
                n_car = float(p_info["n_effective"])
                event_meta["prior_knn_info"] = p_info
            else:
                p_stats = prior_event_stats(as_of_date=as_of_date, election_type=elec_type_query)
                m_car = float(p_stats["mean"]) if not np.isnan(p_stats["mean"]) else 0.0
                med_car = float(p_stats["median"]) if not np.isnan(p_stats["median"]) else 0.0
                n_car = float(p_stats["n"])
                event_meta["prior_event_stats"] = p_stats

            true_series["prior_mean_car"] = m_car
            true_series["prior_median_car"] = med_car
            true_series["prior_n"] = n_car

        # Reorder to exact feature columns
        x_true = true_series[self.feature_cols].values.astype(float).reshape(1, -1)
        x_false = false_series[self.feature_cols].values.astype(float).reshape(1, -1)

        return x_true, x_false, event_meta

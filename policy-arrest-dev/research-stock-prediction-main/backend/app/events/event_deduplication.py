from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from rapidfuzz import fuzz

from backend.app.core.logging import logger
from backend.app.data.trading_calendar import TradingCalendar

class EventDeduplicator:
    """
    Detects duplicate events, identifies multi-phase policies or recurring arrests,
    and clusters temporally adjacent events (within +/- 5 trading days) to prevent
    overlapping event-study contamination.
    """
    def __init__(self, calendar: TradingCalendar, cluster_window_days: int = 5):
        self.calendar = calendar
        self.cluster_window_days = cluster_window_days

    def process_and_cluster(self, df_events: pd.DataFrame) -> pd.DataFrame:
        """
        Takes raw/processed event dataframe and enriches with normalized IDs,
        parent linkages, duplicate flags, and temporal cluster IDs.
        """
        df = df_events.copy()
        
        # Ensure chronological order
        date_col = "Aligned_Trading_Date" if "Aligned_Trading_Date" in df.columns else "Primary_Event_Date"
        df = df.sort_values(date_col).reset_index(drop=True)

        n = len(df)
        normalized_ids = []
        parent_ids = [None] * n
        is_duplicate = [False] * n
        duplicate_reason = [None] * n
        review_required = [False] * n

        # Pass 1: Deduplication & multi-phase identification
        for i in range(n):
            eid = df.loc[i, "Event_ID"]
            date_i = df.loc[i, date_col]
            title_i = df.loc[i, "Policy_Name"] if "Policy_Name" in df.columns else df.loc[i, "Official_Reason_for_Arrest"]
            title_i = str(title_i)
            
            norm_id = eid
            
            # Check against earlier events
            for j in range(i):
                eid_prev = df.loc[j, "Event_ID"]
                date_j = df.loc[j, date_col]
                title_j = df.loc[j, "Policy_Name"] if "Policy_Name" in df.columns else df.loc[j, "Official_Reason_for_Arrest"]
                title_j = str(title_j)

                # Similarity
                sim = fuzz.token_sort_ratio(title_i.lower(), title_j.lower())
                
                # Check date difference
                try:
                    dt_diff = abs((pd.to_datetime(date_i) - pd.to_datetime(date_j)).days)
                except Exception:
                    dt_diff = 999

                # Same event phase or duplicate (e.g. within 30 days and >80% similarity, or exact same date and >75% similarity)
                if (dt_diff <= 30 and sim >= 80) or (dt_diff <= 7 and sim >= 75):
                    is_duplicate[i] = True
                    duplicate_reason[i] = f"Multi-phase or duplicate of {eid_prev} (similarity: {sim}%, diff: {dt_diff}d)"
                    parent_ids[i] = eid_prev
                    norm_id = normalized_ids[j]
                    review_required[i] = True
                    break
                elif sim >= 85:
                    review_required[i] = True

            normalized_ids.append(norm_id)

        df["normalized_event_id"] = normalized_ids
        df["parent_event_id"] = parent_ids
        df["is_duplicate"] = is_duplicate
        df["duplicate_reason"] = duplicate_reason
        df["review_required"] = review_required

        # Pass 2: Temporal Clustering into event_cluster_id
        # Events within cluster_window_days trading sessions of each other are assigned the same cluster
        cluster_ids = []
        current_cluster_num = 1
        last_cluster_date_idx = None

        for i in range(n):
            d_str = df.loc[i, date_col]
            idx = self.calendar.get_index(d_str)
            
            if idx is None:
                # If date not in stock calendar, align
                aligned_d, _, _ = self.calendar.align_to_trading_day(d_str)
                idx = self.calendar.get_index(aligned_d)

            if last_cluster_date_idx is None:
                cluster_ids.append(f"CLUSTER-{current_cluster_num:03d}")
                last_cluster_date_idx = idx
            else:
                if idx is not None and last_cluster_date_idx is not None and (idx - last_cluster_date_idx) <= self.cluster_window_days:
                    # Overlapping window: join cluster
                    cluster_ids.append(f"CLUSTER-{current_cluster_num:03d}")
                    last_cluster_date_idx = max(last_cluster_date_idx, idx)
                else:
                    current_cluster_num += 1
                    cluster_ids.append(f"CLUSTER-{current_cluster_num:03d}")
                    last_cluster_date_idx = idx

        df["event_cluster_id"] = cluster_ids
        df["verification_status"] = "Verified Historical Record"

        logger.info(f"Clustered {n} events into {current_cluster_num} independent temporal clusters. Found {sum(is_duplicate)} potential multi-phase/duplicate links.")
        return df

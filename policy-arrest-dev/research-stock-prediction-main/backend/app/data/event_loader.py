from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import json

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.stock_loader import StockDataLoader
from backend.app.events.policy_processor import PolicyProcessor
from backend.app.events.arrest_processor import ArrestProcessor
from backend.app.events.event_deduplication import EventDeduplicator
from backend.app.events.event_study import EventStudyEngine

class EventDataLoader:
    """Orchestrates loading, cleaning, deduplication, and event-study calculations for all political events."""

    def __init__(self, stock_loader: Optional[StockDataLoader] = None):
        self.stock_loader = stock_loader or StockDataLoader()
        self.calendar = self.stock_loader.get_trading_calendar()
        self.policy_processor = PolicyProcessor(self.calendar)
        self.arrest_processor = ArrestProcessor(self.calendar)
        self.deduplicator = EventDeduplicator(self.calendar)
        
        self.artifacts_dir = settings.ARTIFACT_DIR / "event_study"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.study_parquet = self.artifacts_dir / "all_events_study.parquet"
        self.study_json = self.artifacts_dir / "all_events_study.json"
        self.policy_parquet = settings.ARTIFACT_DIR / "clean" / "processed_policies.parquet"
        self.arrest_parquet = settings.ARTIFACT_DIR / "clean" / "processed_arrests.parquet"
        self.all_events_parquet = settings.ARTIFACT_DIR / "clean" / "all_events.parquet"
        
        self._df_policies: Optional[pd.DataFrame] = None
        self._df_arrests: Optional[pd.DataFrame] = None
        self._df_all_events: Optional[pd.DataFrame] = None
        self._event_study_cache: Optional[Dict[str, Any]] = None

    def load_policies(self) -> pd.DataFrame:
        if self._df_policies is not None:
            return self._df_policies
        if self.policy_parquet.exists():
            try:
                self._df_policies = pd.read_parquet(self.policy_parquet)
                return self._df_policies
            except Exception:
                pass
        raw_policies = self.policy_processor.load_and_process()
        self._df_policies = self.deduplicator.process_and_cluster(raw_policies)
        try:
            self.policy_parquet.parent.mkdir(parents=True, exist_ok=True)
            self._df_policies.to_parquet(self.policy_parquet, index=False)
        except Exception:
            pass
        return self._df_policies

    def load_arrests(self) -> pd.DataFrame:
        if self._df_arrests is not None:
            return self._df_arrests
        if self.arrest_parquet.exists():
            try:
                self._df_arrests = pd.read_parquet(self.arrest_parquet)
                return self._df_arrests
            except Exception:
                pass
        raw_arrests = self.arrest_processor.load_and_process()
        self._df_arrests = self.deduplicator.process_and_cluster(raw_arrests)
        try:
            self.arrest_parquet.parent.mkdir(parents=True, exist_ok=True)
            self._df_arrests.to_parquet(self.arrest_parquet, index=False)
        except Exception:
            pass
        return self._df_arrests

    def load_all_events(self) -> pd.DataFrame:
        """Returns unified dataframe of all 104 historical events."""
        if self._df_all_events is not None:
            return self._df_all_events
        if self.all_events_parquet.exists():
            try:
                self._df_all_events = pd.read_parquet(self.all_events_parquet)
                return self._df_all_events
            except Exception:
                pass

        df_p = self.load_policies().copy()
        df_a = self.load_arrests().copy()

        # Align common schema
        common_cols = [
            "Event_ID", "Event_Family", "Aligned_Trading_Date", "Primary_Event_Date",
            "event_cluster_id", "normalized_event_id", "parent_event_id",
            "is_duplicate", "duplicate_reason", "review_required"
        ]

        df_p["title"] = df_p["Policy_Name"]
        df_p["event_subtype"] = df_p["Derived_Policy_Category"]
        df_p["summary"] = df_p["Policy_Summary"]
        df_p["sources"] = df_p.apply(lambda r: [
            {"name": str(r.get("Source_1_Name", "")), "url": str(r.get("Source_1_URL", ""))},
            {"name": str(r.get("Source_2_Name", "")), "url": str(r.get("Source_2_URL", ""))}
        ], axis=1)

        df_a["title"] = df_a["Official_Reason_for_Arrest"]
        df_a["event_subtype"] = df_a["Derived_Arrest_Subtype"]
        df_a["summary"] = df_a["Political_Context"]
        df_a["sources"] = df_a.apply(lambda r: [
            {"name": str(r.get("Source_1_Name", "")), "url": str(r.get("Source_1_URL", ""))},
            {"name": str(r.get("Source_2_Name", "")), "url": str(r.get("Source_2_URL", ""))}
        ], axis=1)

        shared = ["Event_ID", "Event_Family", "event_subtype", "title", "summary", "Aligned_Trading_Date", "Primary_Event_Date", "event_cluster_id", "normalized_event_id", "parent_event_id", "is_duplicate", "sources"]
        
        df_all = pd.concat([df_p[shared], df_a[shared]], ignore_index=True)
        df_all = df_all.sort_values("Aligned_Trading_Date").reset_index(drop=True)
        self._df_all_events = df_all
        return df_all

    def get_event_study_results(self, force_recompute: bool = False) -> pd.DataFrame:
        """Computes or loads precomputed event study metrics for all events."""
        if not force_recompute and self.study_parquet.exists():
            try:
                return pd.read_parquet(self.study_parquet)
            except Exception:
                pass

        logger.info("Computing event study abnormal returns for all historical events...")
        stock_df = self.stock_loader.load_stock_data()
        engine = EventStudyEngine(stock_df, self.calendar)
        
        df_all = self.load_all_events()
        study_df = engine.run_full_event_study(df_all)
        
        # Save artifacts
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        study_df.to_parquet(self.study_parquet, index=False)
        study_df.to_json(self.study_json, orient="records", indent=2)
        logger.info(f"Saved event study results for {len(study_df)} events to {self.study_parquet}")
        return study_df

    def get_event_detail_with_path(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves complete event metadata, abnormal return metrics, and price trajectory."""
        df_all = self.load_all_events()
        matched = df_all[df_all["Event_ID"] == event_id]
        if matched.empty:
            return None

        row = matched.iloc[0]
        stock_df = self.stock_loader.load_stock_data()
        engine = EventStudyEngine(stock_df, self.calendar)
        
        study_result = engine.analyze_event(
            event_id=row["Event_ID"],
            aligned_date=str(row["Aligned_Trading_Date"]),
            event_family=str(row["Event_Family"]),
            event_subtype=str(row["event_subtype"]),
            title=str(row["title"])
        )
        if not study_result:
            return None

        # Add rich event fields
        study_result["summary"] = row.get("summary")
        study_result["sources"] = row.get("sources")
        study_result["cluster_id"] = row.get("event_cluster_id")
        study_result["is_duplicate"] = bool(row.get("is_duplicate", False))
        
        # Add family specific fields
        if row["Event_Family"] == "Government Policy":
            pol = self.load_policies()[self.load_policies()["Event_ID"] == event_id].iloc[0]
            study_result["affected_sectors"] = pol.get("Affected_Sectors")
            study_result["expected_channel"] = pol.get("Expected_Economic_Channel")
            study_result["temporary_or_permanent"] = pol.get("Temporary_or_Permanent")
            study_result["implementing_authority"] = pol.get("Implementing_Authority")
        else:
            arr = self.load_arrests()[self.load_arrests()["Event_ID"] == event_id].iloc[0]
            study_result["main_person"] = arr.get("Main_Person")
            study_result["political_party"] = arr.get("Political_Party")
            study_result["government_or_opposition"] = arr.get("Government_or_Opposition")
            study_result["arresting_authority"] = arr.get("Arresting_Authority")
            study_result["legal_category"] = arr.get("Legal_or_Investigation_Category")

        return study_result

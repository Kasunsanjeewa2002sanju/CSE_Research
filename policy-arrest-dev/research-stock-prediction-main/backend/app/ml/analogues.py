from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.data.event_loader import EventDataLoader

class HistoricalAnaloguePredictor:
    """
    Primary Interpretable Machine-Learning Model (Model 1).
    Discovers closest historical analogue political events based on semantic similarity,
    policy/legal taxonomy matching, and prevailing market regimes.
    Strictly enforces chronological cutoff filtering during backtesting.
    """
    def __init__(self, event_loader: Optional[EventDataLoader] = None):
        self.event_loader = event_loader or EventDataLoader()
        self._cached_study_df: Optional[pd.DataFrame] = None
        self._tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self._tfidf_matrix = None
        self._init_corpus()

    def _init_corpus(self):
        study_df = self.event_loader.get_event_study_results().copy()
        study_df = study_df.sort_values("aligned_date").reset_index(drop=True)
        self._cached_study_df = study_df
        
        # Build TF-IDF over event titles and subtypes
        corpus = (study_df["title"] + " " + study_df["event_subtype"]).fillna("").tolist()
        self._tfidf_vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=500)
        self._tfidf_matrix = self._tfidf_vectorizer.fit_transform(corpus)

    def find_analogues(
        self,
        event_family: str,
        event_subtype: str,
        query_text: str,
        market_volatility: Optional[float] = None,
        historical_cutoff: Optional[str] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Finds top K historical analogue events matching query attributes.
        If historical_cutoff is given, only events strictly prior to cutoff are considered.
        """
        if self._cached_study_df is None or self._cached_study_df.empty:
            return []

        df = self._cached_study_df.copy()

        # Enforce chronological filter
        if historical_cutoff:
            df = df[df["aligned_date"] <= historical_cutoff].copy()

        # Filter by family
        df_family = df[df["event_family"].str.lower() == event_family.lower()].copy()
        if df_family.empty:
            df_family = df.copy()  # Fallback if unknown family

        # Compute text TF-IDF similarity
        query_vec = self._tfidf_vectorizer.transform([f"{query_text} {event_subtype}"])
        family_indices = df_family.index.tolist()
        family_matrix = self._tfidf_matrix[family_indices]
        text_sims = cosine_similarity(query_vec, family_matrix).flatten()

        analogues = []
        for idx, (_, row) in enumerate(df_family.iterrows()):
            # 1. Subtype exact / partial match
            sub_score = 1.0 if row["event_subtype"].lower() == event_subtype.lower() else (
                0.5 if any(w in row["event_subtype"].lower() for w in event_subtype.lower().split()) else 0.1
            )
            
            # 2. Text semantic similarity
            tfidf_score = float(text_sims[idx]) if idx < len(text_sims) else 0.0
            fuzzy_title_score = fuzz.token_set_ratio(query_text.lower(), str(row["title"]).lower()) / 100.0
            combined_text_score = 0.6 * tfidf_score + 0.4 * fuzzy_title_score

            # 3. Market regime similarity (volatility proximity)
            vol_sim = 1.0
            if market_volatility is not None and "estimation_volatility" in row and pd.notna(row["estimation_volatility"]):
                diff = abs(market_volatility - float(row["estimation_volatility"]))
                vol_sim = max(0.2, 1.0 - (diff / 0.15))

            # Composite similarity score (0 to 100%)
            final_similarity = (0.45 * sub_score + 0.40 * combined_text_score + 0.15 * vol_sim) * 100.0

            analogues.append({
                "event_id": row["event_id"],
                "title": row["title"],
                "aligned_date": row["aligned_date"],
                "event_family": row["event_family"],
                "event_subtype": row["event_subtype"],
                "similarity_score": round(final_similarity, 1),
                "car_1d": round(float(row.get("car_0_1", 0.0)) * 100.0, 2),
                "car_5d": round(float(row.get("car_0_5", 0.0)) * 100.0, 2),
                "car_20d": round(float(row.get("car_0_20", 0.0)) * 100.0, 2),
                "raw_return_5d": round(float(row.get("raw_return_5d", 0.0)) * 100.0, 2),
                "impact_direction": row.get("impact_direction", "Neutral")
            })

        analogues.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_analogues = analogues[:top_k]

        # Attach mini price paths
        for item in top_analogues:
            detail = self.event_loader.get_event_detail_with_path(item["event_id"])
            if detail and "price_path" in detail:
                item["mini_price_path"] = [
                    {"relative_day": p["relative_day"], "pct_change": p["pct_change_from_event"]}
                    for p in detail["price_path"] if -5 <= p["relative_day"] <= 10
                ]
            else:
                item["mini_price_path"] = []

        return top_analogues

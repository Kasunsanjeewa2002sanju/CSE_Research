"""Enhanced Multi-Label Event and Stage Extractor for CSE News.

Provides Stage 5 Advanced NLP & Feature Structuring:
- Multi-label event extraction with confidence scores (0.0 to 1.0)
- Expanded stage taxonomy: rumor, speculation, official_statement, implementation,
  deadline, postponement, cancellation, escalation, resolution, polling, result,
  nomination, government_formation, announcement, none
- Direction (-1.0 to +1.0) via FinBERT sentiment and domain polarity heuristics
- Intensity (0.0 to 1.0) combining keyword strength, headline length, and source reliability
- Novelty (0.0 to 1.0) based on 1 - max semantic similarity to past 7 days news
- Continuous confidence mapping to existing model feature columns (feature_columns.json)
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

from cse.news.embedder import EmbeddingEngine, LexiconSentimentAnalyzer
from cse.news.schema import (
    EventCategory,
    ExpectedDirection,
    NewsExtraction,
    VALID_EVENT_CATEGORIES,
)
from cse.utils.config import find_project_root

logger = logging.getLogger("cse.news.enhanced_extractor")

# Tier-1 reputable financial and news publications in Sri Lanka
TIER_1_SOURCES: Set[str] = {
    "reuters",
    "bloomberg",
    "central bank of sri lanka",
    "cbsl",
    "colombo stock exchange",
    "cse",
    "daily ft",
    "economynext",
    "sunday times",
    "the island",
    "daily mirror",
    "ada derana",
    "imf",
}

# High-urgency/crisis shock keywords for intensity scoring
INTENSITY_KEYWORDS: Set[str] = {
    "crisis",
    "emergency",
    "slashes",
    "hikes",
    "dissolves",
    "impeachment",
    "default",
    "bailout",
    "sweeping",
    "landslide",
    "historic",
    "collapse",
    "war",
    "unrest",
    "surge",
    "plummet",
    "crackdown",
    "curfew",
    "paralyzed",
    "strike",
    "hartal",
    "standstill",
    "sovereign default",
    "resigns",
    "resignation",
}

# Expanded stage detection patterns with priority and confidence weights
STAGE_TAXONOMY: List[Dict[str, Any]] = [
    {
        "stage": "rumor",
        "patterns": [r"\brumou?rs?\b", r"\bhearsay\b", r"\btalks of\b", r"\breportedly\b", r"\balleged\b", r"\binsiders? (?:say|claim)\b", r"\bunconfirmed\b"],
        "confidence": 0.85,
        "base_feature": "stage_announcement",
        "feature_factor": 0.50,
    },
    {
        "stage": "speculation",
        "patterns": [r"\bspeculat(?:ion|es?|ing)\b", r"\blikely to\b", r"\bmay call\b", r"\bcould announce\b", r"\bmulls?\b", r"\bweighing\b", r"\bexpected to\b", r"\bpoised to\b", r"\banticipat(?:ed|ion)\b", r"\bconsidering\b"],
        "confidence": 0.85,
        "base_feature": "stage_announcement",
        "feature_factor": 0.70,
    },
    {
        "stage": "official_statement",
        "patterns": [r"\bofficially\b", r"\bofficial statement\b", r"\bgazette[ds]?\b", r"\bdecree\b", r"\bcommission confirms\b", r"\bformal(?:ly)? announced?\b", r"\bpress release\b", r"\bdeclared by\b"],
        "confidence": 0.95,
        "base_feature": "stage_announcement",
        "feature_factor": 1.00,
    },
    {
        "stage": "implementation",
        "patterns": [r"\bimplement(?:ed|s|ation)\b", r"\benacts?\b", r"\beffective from\b", r"\bin effect\b", r"\brolled out\b", r"\bcommenced\b", r"\benforcement\b", r"\btakes? effect\b"],
        "confidence": 0.90,
        "base_feature": "stage_announcement",
        "feature_factor": 0.85,
    },
    {
        "stage": "deadline",
        "patterns": [r"\bdeadline\b", r"\bexpir(?:y|ed|es)\b", r"\blast date\b", r"\bfinal day\b", r"\bcut-?off\b", r"\btimeframe ends\b", r"\blast hours\b"],
        "confidence": 0.90,
        "base_feature": "stage_nomination_end",
        "feature_factor": 0.80,
    },
    {
        "stage": "postponement",
        "patterns": [r"\bpostpon(?:ed|ing|ement)\b", r"\bdelayed?\b", r"\bdeferred?\b", r"\bput on hold\b", r"\brescheduled?\b", r"\badjourned?\b"],
        "confidence": 0.90,
        "base_feature": "stage_announcement",
        "feature_factor": 0.75,
    },
    {
        "stage": "cancellation",
        "patterns": [r"\bcancell?ed?\b", r"\bscrapped\b", r"\bannulled?\b", r"\bwithdrawn?\b", r"\brevoked?\b", r"\bsuspended indefinitely\b", r"\babandoned\b"],
        "confidence": 0.95,
        "base_feature": "stage_announcement",
        "feature_factor": 0.75,
    },
    {
        "stage": "escalation",
        "patterns": [r"\bescalat(?:es?|ing|ion)\b", r"\bclashes?\b", r"\bdeepens\b", r"\bintensif(?:ies|ied)\b", r"\bcrackdown\b", r"\bemergency declared\b", r"\bboycott\b", r"\bstrike begins\b"],
        "confidence": 0.90,
        "base_feature": "stage_announcement",
        "feature_factor": 0.80,
    },
    {
        "stage": "resolution",
        "patterns": [r"\bresolved?\b", r"\bsettled?\b", r"\bagreement reached\b", r"\bconsensus\b", r"\bpact signed\b", r"\btreaty concluded\b", r"\bdeal concluded\b", r"\bdispute resolved\b"],
        "confidence": 0.90,
        "base_feature": "stage_result",
        "feature_factor": 0.90,
    },
    {
        "stage": "polling",
        "patterns": [r"\bpolling\b", r"\bvoting\b", r"\bballots?\b", r"\bpolls open\b", r"\bvoters cast\b", r"\bpoll day\b"],
        "confidence": 0.95,
        "base_feature": "stage_polling",
        "feature_factor": 1.00,
    },
    {
        "stage": "result",
        "patterns": [r"\bresults?\b", r"\boutcomes?\b", r"\bwon\b", r"\blost\b", r"\bvictory\b", r"\bdefeat(?:ed)?\b", r"\bmajority secured\b", r"\bclear winner\b", r"\blandslide\b"],
        "confidence": 0.95,
        "base_feature": "stage_result",
        "feature_factor": 1.00,
    },
    {
        "stage": "nomination",
        "patterns": [r"\bnominations?\b", r"\bfiled papers\b", r"\bcandidacy\b", r"\bcontestants?\b", r"\bhand in nominations\b"],
        "confidence": 0.88,
        "base_feature": "stage_nomination_start",
        "feature_factor": 0.85,
    },
    {
        "stage": "government_formation",
        "patterns": [r"\bsworn in\b", r"\bcabinet appointed\b", r"\btakes? oath\b", r"\bnew administration formed\b", r"\bnew prime minister appointed\b"],
        "confidence": 0.95,
        "base_feature": "stage_government_formation",
        "feature_factor": 1.00,
    },
    {
        "stage": "announcement",
        "patterns": [r"\bannounced?\b", r"\bcalls? (?:election|poll)\b", r"\bsets? date\b", r"\bpropos(?:ed|es|al)\b", r"\bscheduled?\b", r"\bplans? to\b", r"\bgazetted\b"],
        "confidence": 0.85,
        "base_feature": "stage_announcement",
        "feature_factor": 0.90,
    },
]

# Multi-label category definition rules
CATEGORY_RULES: List[Dict[str, Any]] = [
    {
        "category": "presidential_election",
        "aliases": ["election", "presidential"],
        "primary_keywords": ["presidential election", "executive president", "presidential poll", "presidential ballot", "presidency race"],
        "secondary_keywords": ["president", "presidency"],
        "base_confidence": 0.92,
    },
    {
        "category": "parliamentary_election",
        "aliases": ["election", "parliamentary"],
        "primary_keywords": ["parliamentary election", "general election", "dissolves parliament", "parliament dissolution", "snap poll", "parliamentary poll"],
        "secondary_keywords": ["parliament", "mps", "legislature"],
        "base_confidence": 0.92,
    },
    {
        "category": "provincial_council_election",
        "aliases": ["election", "provincial"],
        "primary_keywords": ["provincial council election", "provincial council", "pc poll", "pc election", "chief minister poll"],
        "secondary_keywords": ["provincial", "provincial administration"],
        "base_confidence": 0.88,
    },
    {
        "category": "local_government_election",
        "aliases": ["election", "local_government"],
        "primary_keywords": ["local government election", "lg poll", "pradeshiya sabha", "municipal council election", "local council election"],
        "secondary_keywords": ["local authority", "municipal council"],
        "base_confidence": 0.85,
    },
    {
        "category": "central_bank_or_monetary_policy",
        "aliases": ["monetary", "cbsl"],
        "primary_keywords": ["central bank", "cbsl", "monetary policy", "policy rate", "interest rate", "sdfr", "slfr", "rate cut", "rate hike", "statutory reserve"],
        "secondary_keywords": ["monetary board", "policy corridor", "corridor", "central banker"],
        "base_confidence": 0.90,
    },
    {
        "category": "government_policy_or_budget_or_tax",
        "aliases": ["fiscal", "budget", "tax"],
        "primary_keywords": ["budget", "appropriation bill", "tax hike", "tax cut", "vat revision", "fiscal policy", "customs tariff", "revenue proposal", "social security levy"],
        "secondary_keywords": ["fiscal", "taxation", "tariff", "subsidies", "treasury"],
        "base_confidence": 0.90,
    },
    { 
        "category": "debt_restructuring_or_IMF",
        "aliases": ["imf", "debt"],
        "primary_keywords": ["imf", "extended fund facility", "eff", "tranche", "bailout", "debt restructuring", "isb bondholder", "official creditor committee", "sovereign debt"],
        "secondary_keywords": ["international monetary fund", "creditor agreement", "bondholders"],
        "base_confidence": 0.92,
    },
    {
        "category": "cabinet_or_ministry_change",
        "aliases": ["cabinet", "reshuffle"],
        "primary_keywords": ["cabinet reshuffle", "sworn in as minister", "new minister appointed", "resigns from cabinet", "ministry portfolio", "prime minister appointed"],
        "secondary_keywords": ["cabinet", "ministry change"],
        "base_confidence": 0.85,
    },
    {
        "category": "political_arrest_or_imprisonment",
        "aliases": ["arrest", "judiciary"],
        "primary_keywords": ["arrested", "remanded", "supreme court order", "high court warrant", "bribery commission", "cid custody", "corruption probe"],
        "secondary_keywords": ["warrant", "indictment", "custody"],
        "base_confidence": 0.85,
    },
    {
        "category": "protest_or_unrest",
        "aliases": ["protest", "unrest"],
        "primary_keywords": ["protest", "nationwide strike", "hartal", "tear gas", "curfew imposed", "state of emergency", "civil unrest", "aragalaya", "demonstration"],
        "secondary_keywords": ["trade union action", "public disruption"],
        "base_confidence": 0.85,
    },
    {
        "category": "not_relevant",
        "aliases": ["irrelevant", "sports", "entertainment"],
        "primary_keywords": ["cricket", "sports match", "tournament", "bollywood", "cinema", "entertainment", "lottery", "weather forecast", "cyclone rainfall", "fashion award"],
        "secondary_keywords": ["horoscope", "celebrity gossip", "shopping festival"],
        "base_confidence": 0.95,
    },
]


class EnhancedEventExtractor:
    """Multi-label, confidence-weighted event and stage extraction engine."""

    def __init__(
        self,
        embedder: Optional[EmbeddingEngine] = None,
        db_conn: Optional[Any] = None,
    ) -> None:
        self.embedder: Optional[EmbeddingEngine] = embedder
        self.db_conn = db_conn
        self._lexicon_analyzer = LexiconSentimentAnalyzer()

    def _get_embedder(self) -> Optional[EmbeddingEngine]:
        """Lazy load embedder."""
        if self.embedder is None:
            try:
                self.embedder = EmbeddingEngine()
            except Exception as e:
                logger.warning("Could not instantiate full EmbeddingEngine (%s). Using lexicon.", e)
        return self.embedder

    def extract_categories(self, text: str) -> Tuple[Dict[str, float], str]:
        """Extract multi-label event categories with confidence scores (0.0 to 1.0).

        Returns
        -------
        Tuple[Dict[str, float], str]
            (event_categories, primary_category)
        """
        text_lower = text.lower()
        cat_scores: Dict[str, float] = {}

        # First check not_relevant triggers
        irrelevant_rule = next(r for r in CATEGORY_RULES if r["category"] == "not_relevant")
        matched_irrel = [kw for kw in irrelevant_rule["primary_keywords"] if re.search(r"\b" + re.escape(kw) + r"\b", text_lower)]
        if matched_irrel:
            # Check if there is an explicit political or macro keyword overriding sports/weather
            has_macro = any(
                any(re.search(r"\b" + re.escape(kw) + r"\b", text_lower) for kw in r["primary_keywords"])
                for r in CATEGORY_RULES if r["category"] != "not_relevant"
            )
            if not has_macro:
                return {"not_relevant": 0.95}, "not_relevant"

        for rule in CATEGORY_RULES:
            if rule["category"] == "not_relevant":
                continue

            pri_matches = [kw for kw in rule["primary_keywords"] if re.search(r"\b" + re.escape(kw) + r"\b", text_lower)]
            sec_matches = [kw for kw in rule["secondary_keywords"] if re.search(r"\b" + re.escape(kw) + r"\b", text_lower)]

            if pri_matches:
                conf = rule["base_confidence"]
                if len(pri_matches) > 1:
                    conf = min(0.99, conf + 0.05)
                cat_scores[rule["category"]] = round(conf, 2)
                # Map friendly aliases
                for alias in rule["aliases"]:
                    cat_scores[alias] = max(cat_scores.get(alias, 0.0), round(conf, 2))
            elif sec_matches:
                conf = round(rule["base_confidence"] * 0.75, 2)
                cat_scores[rule["category"]] = conf
                for alias in rule["aliases"]:
                    cat_scores[alias] = max(cat_scores.get(alias, 0.0), conf)

        # Fallback to election if 'election' or 'poll' appears without specific prefix
        if re.search(r"\b(elections?|polls?|ballots?)\b", text_lower) and not any("election" in k for k in cat_scores):
            cat_scores["election"] = 0.85
            cat_scores["presidential_election"] = 0.70  # Default assumption in national media

        if not cat_scores:
            return {"not_relevant": 0.60}, "not_relevant"

        # Determine primary category (preferring official enum categories over aliases)
        enum_matches = {k: v for k, v in cat_scores.items() if k in VALID_EVENT_CATEGORIES}
        if enum_matches:
            primary = max(enum_matches.items(), key=lambda x: x[1])[0]
        else:
            primary = max(cat_scores.items(), key=lambda x: x[1])[0]

        return cat_scores, primary

    def extract_stage(self, text: str) -> Tuple[str, float]:
        """Extract fine-grained stage sub-type and stage confidence."""
        text_lower = text.lower()

        for item in STAGE_TAXONOMY:
            for pat in item["patterns"]:
                if re.search(pat, text_lower):
                    return item["stage"], float(item["confidence"])

        return "none", 0.0

    def compute_direction(self, text: str) -> float:
        """Derive directional sentiment scalar between -1.0 and +1.0."""
        engine = self._get_embedder()
        score = engine.sentiment(text) if engine and hasattr(engine, "sentiment") else self._lexicon_analyzer.score(text)
        compound = float(score.get("compound", 0.0))

        # Financial market rules
        lower = text.lower()
        if any(k in lower for k in ["cuts rate", "reduces rate", "rate cut", "slashes rate", "lowers rate", "monetary easing"]):
            compound = max(compound, 0.70)
        elif any(k in lower for k in ["hikes rate", "raises rate", "rate hike", "increases rate", "monetary tightening"]):
            compound = min(compound, -0.70)
        elif any(k in lower for k in ["approves tranche", "unlocks funds", "bailout approved", "debt relief", "agreement reached"]):
            compound = max(compound, 0.75)
        elif any(k in lower for k in ["delays tranche", "stalls bailout", "rejects loan", "debt default", "strike begins"]):
            compound = min(compound, -0.75)
        elif any(k in lower for k in ["tax hike", "increased vat", "levy imposed"]):
            compound = min(compound, -0.40)
        elif any(k in lower for k in ["tax cut", "stimulus", "incentives"]):
            compound = max(compound, 0.50)
        elif any(k in lower for k in ["two-thirds majority", "decisive victory", "landslide victory"]):
            compound = max(compound, 0.65)
        elif any(k in lower for k in ["hung parliament", "deadlock", "coalition collapse"]):
            compound = min(compound, -0.65)

        return float(round(compound, 4))

    def compute_intensity(
        self,
        headline: str,
        source: Optional[str] = None,
    ) -> float:
        """Compute headline intensity in range [0.0, 1.0].

        Combines:
        1. Keyword strength (urgency / impact verbs)
        2. Headline substantive length
        3. Source reliability
        """
        words = re.findall(r"\b\w+\b", headline.lower())
        word_count = len(words)

        # 1. Keyword strength
        kw_matches = sum(1 for kw in INTENSITY_KEYWORDS if kw in headline.lower())
        s_kw = min(0.45, 0.15 + (kw_matches * 0.10))

        # 2. Headline length (peak informativeness between 8-20 words)
        s_len = min(0.30, max(0.10, word_count / 30.0 + 0.08))

        # 3. Source reliability
        s_src = 0.15
        if source:
            src_clean = source.strip().lower()
            if any(t in src_clean for t in TIER_1_SOURCES):
                s_src = 0.25
            else:
                s_src = 0.18

        intensity = round(float(np.clip(s_kw + s_len + s_src, 0.10, 1.00)), 4)
        return intensity

    def compute_novelty(
        self,
        headline: str,
        published_at: Optional[Union[str, date, datetime]] = None,
        past_headlines: Optional[List[str]] = None,
    ) -> float:
        """Compute novelty score in range [0.0, 1.0].

        novelty = 1.0 - max_similarity_to_past_7_days_news.
        If no past news is available, returns 1.0.
        """
        if past_headlines is not None:
            reference_headlines = [h for h in past_headlines if h and h.strip() and h.strip() != headline.strip()]
        else:
            reference_headlines = self._fetch_recent_headlines(published_at)

        if not reference_headlines:
            return 1.0

        engine = self._get_embedder()
        if engine is None:
            # Lexicon token overlap fallback
            current_tokens = set(re.findall(r"\b\w+\b", headline.lower()))
            if not current_tokens:
                return 1.0
            max_jaccard = 0.0
            for ref in reference_headlines:
                ref_tokens = set(re.findall(r"\b\w+\b", ref.lower()))
                if ref_tokens:
                    jaccard = len(current_tokens & ref_tokens) / len(current_tokens | ref_tokens)
                    if jaccard > max_jaccard:
                        max_jaccard = jaccard
            return float(round(1.0 - max_jaccard, 4))

        try:
            head_vec = engine.embed(headline).reshape(1, -1)
            ref_vecs = engine.embed_batch(reference_headlines[:50])
            sims = np.dot(ref_vecs, head_vec.T).flatten()
            max_sim = float(np.max(sims)) if len(sims) > 0 else 0.0
            novelty = float(np.clip(1.0 - max_sim, 0.0, 1.0))
            return float(round(novelty, 4))
        except Exception as e:
            logger.warning("Novelty computation failed (%s). Returning 1.0.", e)
            return 1.0

    def _fetch_recent_headlines(
        self,
        published_at: Optional[Union[str, date, datetime]],
    ) -> List[str]:
        """Fetch headlines from cse_history.db published in the 7 days prior to published_at."""
        if not published_at:
            return []

        if isinstance(published_at, datetime):
            pub_date = published_at.date()
        elif isinstance(published_at, date):
            pub_date = published_at
        else:
            try:
                pub_date = date.fromisoformat(str(published_at).split("T")[0].split(" ")[0])
            except Exception:
                return []

        start_date = (pub_date - timedelta(days=7)).isoformat()
        end_date = pub_date.isoformat()

        # Try database connection
        conn = self.db_conn
        close_after = False
        if conn is None:
            try:
                from cse.news.historical_db import get_db_connection
                conn = get_db_connection()
                close_after = True
            except Exception:
                return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT headline FROM news_history 
                WHERE published_at >= ? AND published_at <= ?
                ORDER BY published_at DESC LIMIT 100
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()
            return [r[0] if isinstance(r, (tuple, list)) else r["headline"] for r in rows]
        except Exception:
            return []
        finally:
            if close_after and conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def extract(
        self,
        headline: str,
        published_at: Optional[Union[str, date, datetime]] = None,
        source: Optional[str] = None,
        past_headlines: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Extract multi-label categories, fine-grained stage, confidence, direction, intensity, and novelty.

        Parameters
        ----------
        headline : str
            Financial news headline.
        published_at : Optional[Union[str, date, datetime]]
            Publication timestamp.
        source : Optional[str]
            Publication / news source.
        past_headlines : Optional[List[str]]
            Headlines from past 7 days for novelty calculation.

        Returns
        -------
        dict
            {
                "event_categories": dict{category: confidence},
                "primary_category": str,
                "stage": str,
                "stage_confidence": float,
                "direction": float,
                "intensity": float,
                "novelty": float,
            }
        """
        event_categories, primary_cat = self.extract_categories(headline)
        stage, stage_conf = self.extract_stage(headline)
        direction = self.compute_direction(headline)
        intensity = self.compute_intensity(headline, source=source)
        novelty = self.compute_novelty(
            headline=headline,
            published_at=published_at,
            past_headlines=past_headlines,
        )

        return {
            "event_categories": event_categories,
            "primary_category": primary_cat,
            "stage": stage,
            "stage_confidence": float(stage_conf),
            "direction": float(direction),
            "intensity": float(intensity),
            "novelty": float(novelty),
        }

    def map_to_feature_columns(
        self,
        extraction_result: Dict[str, Any],
        feature_cols: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Map extraction result to continuous confidence scores for existing feature columns.

        Parameters
        ----------
        extraction_result : dict
            Result from extract().
        feature_cols : Optional[list of str]
            List of feature columns from feature_columns.json.

        Returns
        -------
        dict
            Mapping of column_name -> float value.
        """
        cats = extraction_result.get("event_categories", {})
        stage = extraction_result.get("stage", "none")
        stage_conf = float(extraction_result.get("stage_confidence", 0.0))

        # 1. Election type confidences
        p_pres = float(cats.get("presidential_election", 0.0))
        p_parl = float(cats.get("parliamentary_election", 0.0))
        p_pc = float(max(cats.get("provincial_council_election", 0.0), cats.get("local_government_election", 0.0)))
        # General election keyword boost if specific subtype was not explicitly resolved
        if "election" in cats and p_pres == 0.0 and p_parl == 0.0 and p_pc == 0.0:
            p_pres = float(cats.get("election", 0.0)) * 0.70

        type_max = max(p_pres, p_parl, p_pc)
        type_none = round(float(np.clip(1.0 - type_max, 0.0, 1.0)), 4) if type_max > 0 else 1.0

        # 2. Stage continuous confidences
        stage_vals: Dict[str, float] = {
            "stage_announcement": 0.0,
            "stage_nomination_start": 0.0,
            "stage_nomination_end": 0.0,
            "stage_polling": 0.0,
            "stage_result": 0.0,
            "stage_government_formation": 0.0,
        }

        # Find matching stage rule
        matched_rule = next((r for r in STAGE_TAXONOMY if r["stage"] == stage), None)
        if matched_rule and stage != "none":
            target_feat = matched_rule["base_feature"]
            factor = matched_rule["feature_factor"]
            val = round(float(stage_conf * factor), 4)
            stage_vals[target_feat] = val

        max_stage_val = max(stage_vals.values()) if stage_vals else 0.0
        stage_none = round(float(np.clip(1.0 - max_stage_val, 0.0, 1.0)), 4)

        result_feats: Dict[str, float] = {
            "type_presidential": p_pres,
            "type_parliamentary": p_parl,
            "type_provincial_council": p_pc,
            "type_none": type_none,
            "stage_none": stage_none,
            "stage_announcement": stage_vals["stage_announcement"],
            "stage_nomination_start": stage_vals["stage_nomination_start"],
            "stage_nomination_end": stage_vals["stage_nomination_end"],
            "stage_polling": stage_vals["stage_polling"],
            "stage_result": stage_vals["stage_result"],
            "stage_government_formation": stage_vals["stage_government_formation"],
        }

        if feature_cols:
            return {k: result_feats.get(k, 0.0) for k in feature_cols if k in result_feats}

        return result_feats


# Class aliases for module compatibility
EnhancedExtractor = EnhancedEventExtractor

# Singleton instance
_ENHANCED_EXTRACTOR: Optional[EnhancedEventExtractor] = None


def get_enhanced_extractor() -> EnhancedEventExtractor:
    """Return singleton EnhancedEventExtractor instance."""
    global _ENHANCED_EXTRACTOR
    if _ENHANCED_EXTRACTOR is None:
        _ENHANCED_EXTRACTOR = EnhancedEventExtractor()
    return _ENHANCED_EXTRACTOR


def extract_enhanced(
    headline: str,
    published_at: Optional[Union[str, date, datetime]] = None,
    source: Optional[str] = None,
    past_headlines: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Top-level helper for enhanced event extraction."""
    extractor = get_enhanced_extractor()
    return extractor.extract(
        headline=headline,
        published_at=published_at,
        source=source,
        past_headlines=past_headlines,
    )

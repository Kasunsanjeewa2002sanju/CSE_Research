"""
Deterministic offline event extraction fallback for Stage 10.

Leverages TF-IDF prototype cosine similarity, Sri Lankan political/macroeconomic
domain lexicons, and rule-based market direction logic.
Operates with ZERO external network dependencies, 0 API costs, and executes in ~2ms.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

from cse.news.schema import (
    ElectionStage,
    EventCategory,
    ExpectedDirection,
    NewsExtraction,
)

# Prototype semantic descriptions representing each of the 12 categories
CATEGORY_PROTOTYPES: Dict[str, str] = {
    EventCategory.PRESIDENTIAL_ELECTION.value: (
        "presidential election president presidential candidate polls executive presidency run-off "
        "head of state election commission ballot voter candidacy national election"
    ),
    EventCategory.PARLIAMENTARY_ELECTION.value: (
        "parliamentary general election parliament dissolution of parliament MPs seats majority "
        "snap poll coalition general election national list legislative assembly"
    ),
    EventCategory.PROVINCIAL_COUNCIL_ELECTION.value: (
        "provincial council elections PC polls chief minister western province sabaragamuwa "
        "southern province north western wayamba northern council provincial administration"
    ),
    EventCategory.LOCAL_GOVERNMENT_ELECTION.value: (
        "local government elections LG polls pradeshiya sabha municipal council urban council "
        "mayor wards local authority election delimitation"
    ),
    EventCategory.CABINET_OR_MINISTRY_CHANGE.value: (
        "cabinet reshuffle new minister portfolio sworn in resignation prime minister appointed "
        "deputy minister ministry change state minister sworn administration"
    ),
    EventCategory.GOVERNMENT_POLICY_OR_BUDGET_OR_TAX.value: (
        "budget appropriation bill tax vat social security levy policy gazette tariff fiscal reform "
        "subsidy fuel pricing formula government spending revenue proposal"
    ),
    EventCategory.CENTRAL_BANK_OR_MONETARY_POLICY.value: (
        "central bank cbsl monetary policy rate cut rate hike policy rates sdfr slfr statutory reserve "
        "ratio inflation deflation policy corridor interest rates governor"
    ),
    EventCategory.POLITICAL_ARREST_OR_IMPRISONMENT.value: (
        "arrest remanded cid supreme court high court magistrate warrant attorney general bail "
        "corruption probe custody bribery commission financial crimes fcid"
    ),
    EventCategory.PROTEST_OR_UNREST.value: (
        "protest strike hartal curfew state of emergency tear gas demonstration trade union "
        "aragalaya civil unrest clashes road block public disruption"
    ),
    EventCategory.DEBT_RESTRUCTURING_OR_IMF.value: (
        "imf debt restructuring sovereign debt default bailout international monetary fund isb "
        "advisory official creditor committee staff level agreement tranche external debt sustainability"
    ),
    EventCategory.OTHER_POLITICAL.value: (
        "bilateral diplomatic talks treaty geopolitical agreement constitution 21st amendment "
        "unhrc resolution bilateral visit foreign delegation diplomatic relations"
    ),
    EventCategory.NOT_RELEVANT.value: (
        "cricket sports match tournament bollywood cinema entertainment lottery weather cyclone "
        "rainfall festival holiday celebrity award horoscope shopping fashion"
    ),
}

# Prototype semantic descriptions for election stages
STAGE_PROTOTYPES: Dict[str, str] = {
    ElectionStage.ANNOUNCEMENT.value: (
        "election announced gazette issued poll scheduled date declared president dissolves "
        "proclamation formal notice timeline revealed"
    ),
    ElectionStage.NOMINATIONS.value: (
        "nominations close deposits accepted candidates submit nomination lists parties hand over "
        "objections rejected returning officer"
    ),
    ElectionStage.CAMPAIGN.value: (
        "campaign rallies election manifesto speeches public meetings propaganda tour advertising "
        "postal voting stage political rallies"
    ),
    ElectionStage.VOTING.value: (
        "polling begins voters cast ballots polling stations open voting day voter turnout ballot "
        "tight security queue polling concluded"
    ),
    ElectionStage.RESULTS.value: (
        "election results declared winner victory seats won landslide victory official count "
        "elections department announces winner tally"
    ),
    ElectionStage.FORMATION.value: (
        "sworn in takes oath forms government prime minister appointment new cabinet assumed "
        "office swearing ceremony alliance formed"
    ),
}

# Domain Entity Keywords
KEY_ENTITIES: List[str] = [
    "CBSL", "Central Bank", "IMF", "Election Commission", "Supreme Court",
    "President", "Prime Minister", "Cabinet", "Parliament",
    "Ranil Wickremesinghe", "Mahinda Rajapaksa", "Gotabaya Rajapaksa",
    "Anura Kumara Dissanayake", "Sajith Premadasa", "Maithripala Sirisena",
    "Chandrika Kumaratunga", "Ceylon Chamber of Commerce", "Treasury",
]

# CSE Sector mappings
SECTOR_KEYWORDS: Dict[str, List[str]] = {
    "Banking & Finance": ["bank", "interest rate", "lending", "cbsl", "liquidity", "monetary", "debt", "isb", "imf", "credit"],
    "Manufacturing & Industry": ["tariff", "export", "import", "customs", "factory", "raw material", "production"],
    "Consumer & Retail": ["vat", "tax", "inflation", "food", "subsidy", "cost of living", "pricing", "supermarket"],
    "Tourism & Hospitality": ["tourist", "travel", "hotels", "airlines", "curfew", "emergency", "unrest", "visas"],
    "Energy & Utilities": ["ceb", "fuel", "power", "electricity", "cpc", "tariffs", "solar", "petroleum"],
    "Plantations & Agriculture": ["tea", "rubber", "fertilizer", "crop", "agriculture", "paddy", "harvest"],
    "Telecom & IT": ["telecom", "spectrum", "dialog", "slt", "broadband", "digital tax"],
}


class OfflineEventExtractor:
    """Pre-fitted TF-IDF prototype classifier for 12 event categories and 6 stages."""

    def __init__(self) -> None:
        self.cat_names = list(CATEGORY_PROTOTYPES.keys())
        self.cat_corpus = [CATEGORY_PROTOTYPES[k] for k in self.cat_names]
        self.stg_names = list(STAGE_PROTOTYPES.keys())
        self.stg_corpus = [STAGE_PROTOTYPES[k] for k in self.stg_names]
        self.has_sklearn = HAS_SKLEARN

        if self.has_sklearn:
            try:
                self.cat_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
                self.cat_tfidf = self.cat_vectorizer.fit_transform(self.cat_corpus)
                self.stg_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
                self.stg_tfidf = self.stg_vectorizer.fit_transform(self.stg_corpus)
            except Exception:
                self.has_sklearn = False

        if not self.has_sklearn:
            self.cat_tokens = {k: set(v.lower().split()) for k, v in CATEGORY_PROTOTYPES.items()}
            self.stg_tokens = {k: set(v.lower().split()) for k, v in STAGE_PROTOTYPES.items()}

    def extract(
        self,
        headline: str,
        description: str = "",
        publication_date: str = "",
        source: Optional[str] = None,
    ) -> NewsExtraction:
        """Extract structured event representation from raw news text."""
        combined_text = f"{headline} {description}".strip()
        if not combined_text:
            return NewsExtraction(
                is_relevant=False,
                event_category=EventCategory.NOT_RELEVANT.value,
                stage="none",
                expected_direction=ExpectedDirection.NEUTRAL.value,
                expected_direction_reason="No content provided in news item.",
                affected_sectors=[],
                event_date_mentioned=publication_date if publication_date else None,
                entities=[],
                confidence=0.0,
                language="en",
            )

        # 1. Category Classification
        if self.has_sklearn:
            vec = self.cat_vectorizer.transform([combined_text])
            sims = cosine_similarity(vec, self.cat_tfidf)[0]
            best_cat_idx = int(np.argmax(sims))
            best_cat_score = float(sims[best_cat_idx])
            predicted_cat = self.cat_names[best_cat_idx]
        else:
            text_tokens = set(re.findall(r"\w+", combined_text.lower()))
            scores = []
            for k in self.cat_names:
                overlap = len(text_tokens & self.cat_tokens[k])
                scores.append(overlap / max(1, len(self.cat_tokens[k])))
            best_cat_idx = int(np.argmax(scores))
            best_cat_score = float(scores[best_cat_idx])
            predicted_cat = self.cat_names[best_cat_idx] if best_cat_score > 0 else EventCategory.NOT_RELEVANT.value

        # Default threshold: if lowest similarity, classify as not_relevant
        if best_cat_score < 0.05:
            predicted_cat = EventCategory.NOT_RELEVANT.value
            is_relevant = False
            confidence = 0.50
        else:
            is_relevant = (predicted_cat != EventCategory.NOT_RELEVANT.value)
            confidence = min(0.95, max(0.50, round(best_cat_score * 1.8, 2)))

        # 2. Stage Classification (Applicable for election categories)
        is_election = predicted_cat in {
            EventCategory.PRESIDENTIAL_ELECTION.value,
            EventCategory.PARLIAMENTARY_ELECTION.value,
            EventCategory.PROVINCIAL_COUNCIL_ELECTION.value,
            EventCategory.LOCAL_GOVERNMENT_ELECTION.value,
        }

        if is_election:
            if self.has_sklearn:
                stg_vec = self.stg_vectorizer.transform([combined_text])
                stg_sims = cosine_similarity(stg_vec, self.stg_tfidf)[0]
                best_stg_idx = int(np.argmax(stg_sims))
                best_stg_score = float(stg_sims[best_stg_idx])
                stage = self.stg_names[best_stg_idx] if best_stg_score > 0.05 else "none"
            else:
                text_tokens = set(re.findall(r"\w+", combined_text.lower()))
                stg_scores = []
                for k in self.stg_names:
                    overlap = len(text_tokens & self.stg_tokens[k])
                    stg_scores.append(overlap / max(1, len(self.stg_tokens[k])))
                best_stg_idx = int(np.argmax(stg_scores))
                best_stg_score = float(stg_scores[best_stg_idx])
                stage = self.stg_names[best_stg_idx] if best_stg_score > 0 else "none"
        else:
            stage = "none"

        # 3. Market Direction & Sector Heuristics
        direction, direction_reason = self._infer_direction(predicted_cat, stage, combined_text)
        sectors = self._infer_sectors(combined_text)
        entities = self._extract_entities(combined_text)

        # Event date mentioned: ISO regex or fall back to publication_date
        date_match = re.search(r"\b(19\d\d|20\d\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b", combined_text)
        event_date = date_match.group(0) if date_match else (publication_date if publication_date else None)

        return NewsExtraction(
            is_relevant=is_relevant,
            event_category=predicted_cat,
            stage=stage,
            expected_direction=direction,
            expected_direction_reason=direction_reason,
            affected_sectors=sectors,
            event_date_mentioned=event_date,
            entities=entities,
            confidence=confidence,
            language="en",
        )

    def _infer_direction(self, category: str, stage: str, text: str) -> Tuple[str, str]:
        """Infer expected directional impact on Colombo Stock Exchange."""
        lower = text.lower()

        # Protests / civil unrest
        if category == EventCategory.PROTEST_OR_UNREST.value:
            return ExpectedDirection.NEGATIVE.value, "Civil unrest and emergency measures disrupt business continuity and investor sentiment."

        # Central Bank
        if category == EventCategory.CENTRAL_BANK_OR_MONETARY_POLICY.value:
            if any(w in lower for w in ["rate cut", "easing", "reduces rates", "lower policy"]):
                return ExpectedDirection.POSITIVE.value, "Monetary easing lowers corporate borrowing costs and stimulates equity valuation."
            elif any(w in lower for w in ["rate hike", "tightening", "hikes rate", "higher rates"]):
                return ExpectedDirection.NEGATIVE.value, "Monetary tightening raises discount rates and compresses corporate equity margins."
            return ExpectedDirection.UNCERTAIN.value, "Monetary policy stance depends on forthcoming inflation expectations."

        # IMF / Debt Restructuring
        if category == EventCategory.DEBT_RESTRUCTURING_OR_IMF.value:
            if any(w in lower for w in ["agreement", "approved", "tranche", "deal reached", "completed"]):
                return ExpectedDirection.POSITIVE.value, "IMF agreement or creditor deal reduces sovereign default risk and bolsters market liquidity."
            elif any(w in lower for w in ["default", "collapse", "delayed", "suspended"]):
                return ExpectedDirection.NEGATIVE.value, "Debt restructuring impasse heightens macroeconomic risk and currency vulnerability."
            return ExpectedDirection.UNCERTAIN.value, "Outcome of complex sovereign creditor negotiations remains pending."

        # Government Policy / Tax
        if category == EventCategory.GOVERNMENT_POLICY_OR_BUDGET_OR_TAX.value:
            if any(w in lower for w in ["tax hike", "increased vat", "levy imposed"]):
                return ExpectedDirection.NEGATIVE.value, "Tax hikes compress corporate disposable earnings and discretionary consumer demand."
            elif any(w in lower for w in ["incentive", "tax cut", "stimulus", "deregulation"]):
                return ExpectedDirection.POSITIVE.value, "Fiscal incentives enhance corporate cash flows and stimulate capital formation."
            return ExpectedDirection.UNCERTAIN.value, "Net impact of fiscal proposals depends on sector-specific implementation details."

        # Political arrest
        if category == EventCategory.POLITICAL_ARREST_OR_IMPRISONMENT.value:
            return ExpectedDirection.NEGATIVE.value, "High-profile political detentions elevate perceived governance risk and political tension."

        # Elections
        if stage in {"announcement", "campaign"}:
            return ExpectedDirection.UNCERTAIN.value, "Pre-election uncertainty typically leads institutional capital to defer commitments."
        elif stage == "results":
            if any(w in lower for w in ["majority", "landslide", "clear victory"]):
                return ExpectedDirection.POSITIVE.value, "Decisive electoral outcome removes political uncertainty and enables policy momentum."
            elif any(w in lower for w in ["hung", "deadlock", "coalition dispute"]):
                return ExpectedDirection.NEGATIVE.value, "Fragmented electoral outcome risks political paralysis and delayed economic reforms."
            return ExpectedDirection.UNCERTAIN.value, "Market assessing policy direction and stability of new parliamentary configuration."
        elif stage == "formation":
            return ExpectedDirection.POSITIVE.value, "Formal swearing in of government signals political transition completion and cabinet stability."

        if category == EventCategory.NOT_RELEVANT.value:
            return ExpectedDirection.NEUTRAL.value, "Article content has negligible macroeconomic relevance to Colombo equities."

        return ExpectedDirection.UNCERTAIN.value, "Impact on equity market indices is contingent on broader policy execution."

    def _infer_sectors(self, text: str) -> List[str]:
        """Detect affected CSE GICS sectors from domain keywords."""
        lower = text.lower()
        matched = []
        for sector, kws in SECTOR_KEYWORDS.items():
            if any(kw in lower for kw in kws):
                matched.append(sector)
        return matched[:4]

    def _extract_entities(self, text: str) -> List[str]:
        """Extract key Sri Lankan political and macroeconomic entities."""
        found = []
        for ent in KEY_ENTITIES:
            if re.search(rf"\b{re.escape(ent)}\b", text, re.IGNORECASE):
                found.append(ent)
        return found


# Singleton instance for high efficiency
_extractor = OfflineEventExtractor()


def extract_offline(
    headline: str,
    description: str = "",
    date: str = "",
    source: Optional[str] = None,
) -> NewsExtraction:
    """Primary offline extraction function."""
    return _extractor.extract(headline, description, publication_date=date, source=source)


def classify_offline(
    headline: str,
    description: str = "",
    date: str = "",
    source: Optional[str] = None,
) -> NewsExtraction:
    """Alias for classify_offline."""
    return extract_offline(headline, description, date=date, source=source)


def classify(headline: str, description: str = "") -> NewsExtraction:
    """Convenience alias for classify."""
    return extract_offline(headline, description)


def predict_offline(headline: str, description: str = "") -> NewsExtraction:
    """Convenience alias for predict_offline."""
    return extract_offline(headline, description)

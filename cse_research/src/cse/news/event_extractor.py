"""Event Mention Extractor for CSE Financial News.

Extracts:
- Event types: election, fiscal/budget, monetary policy (CBSL), IMF review, earnings
- Event stages: result, polling, nomination, announcement, none
- Confidence score (0.0 to 1.0)
- Sentiment direction scalar (-1.0 to +1.0) via FinBERT / domain sentiment engine
- Mapping to nearest calendar event type
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from cse.news.embedder import LexiconSentimentAnalyzer

logger = logging.getLogger("cse.news.event_extractor")

# Cache sentiment analyzer instance
_SENTIMENT_ANALYZER: Optional[Any] = None


def get_sentiment_analyzer() -> Any:
    """Lazy-load sentiment analyzer (FinBERT if available, else Lexicon)."""
    global _SENTIMENT_ANALYZER
    if _SENTIMENT_ANALYZER is None:
        try:
            from cse.news.embedder import EmbeddingEngine
            _SENTIMENT_ANALYZER = EmbeddingEngine()
        except Exception as e:
            logger.warning("Could not initialize full EmbeddingEngine for extractor (%s). Using lexicon.", e)
            _SENTIMENT_ANALYZER = LexiconSentimentAnalyzer()
    return _SENTIMENT_ANALYZER


# Mapping rules: keywords -> (event_type, calendar_type, category, base_confidence)
KEYWORD_RULES: List[Dict[str, Any]] = [
    # 1. Election types
    {
        "category": "election",
        "keywords": ["election", "poll", "vote", "ballot", "voting", "electoral", "referendum"],
        "sub_rules": [
            (["presidential"], "presidential_election", "presidential_election", 0.95),
            (["parliament", "parliamentary", "general election"], "parliamentary_election", "parliamentary_election", 0.95),
            (["provincial", "provincial council"], "provincial_councils", "provincial_councils", 0.90),
            (["local government", "pradeshiya", "municipal"], "local_government_election", "local_government_election", 0.85),
        ],
        "default_type": "election",
        "calendar_type": "election",
        "base_confidence": 0.90,
    },
    # 2. Fiscal / Budget
    {
        "category": "fiscal",
        "keywords": ["budget", "fiscal", "tax", "appropriation", "revenue bill", "customs tariff", "vat revision", "taxation"],
        "sub_rules": [
            (["appropriation", "budget"], "budget", "budget", 0.95),
            (["tax", "tariff", "vat"], "fiscal_tax", "budget", 0.85),
        ],
        "default_type": "budget",
        "calendar_type": "budget",
        "base_confidence": 0.90,
    },
    # 3. Monetary policy / Central Bank
    {
        "category": "monetary",
        "keywords": ["rate", "monetary", "policy", "cbsl", "central bank", "corridor", "sdfr", "slfr", "policy rate", "interest rate"],
        "sub_rules": [
            (["cbsl", "central bank"], "monetary_policy", "monetary_policy", 0.95),
            (["monetary policy", "policy rate"], "monetary_policy", "monetary_policy", 0.95),
        ],
        "default_type": "monetary_policy",
        "calendar_type": "monetary_policy",
        "base_confidence": 0.90,
    },
    # 4. IMF / Debt restructuring
    {
        "category": "imf",
        "keywords": ["imf", "tranche", "review", "bailout", "eff", "extended fund facility", "debt restructuring", "bondholder"],
        "sub_rules": [
            (["tranche", "bailout", "eff"], "imf_review", "imf_review", 0.95),
            (["debt restructuring", "bondholder"], "debt_restructuring", "imf_review", 0.85),
        ],
        "default_type": "imf_review",
        "calendar_type": "imf_review",
        "base_confidence": 0.90,
    },
    # 5. Earnings season / corporate
    {
        "category": "corporate",
        "keywords": ["earnings", "quarterly results", "financial results", "interim results", "q1 results", "q2 results", "q3 results", "q4 results", "dividend"],
        "sub_rules": [],
        "default_type": "earnings_season",
        "calendar_type": "earnings_season",
        "base_confidence": 0.85,
    },
]

# Stage keywords mapping
STAGE_RULES: List[Tuple[List[str], str]] = [
    (["result", "outcome", "won", "lost", "victory", "defeated", "concluded"], "result"),
    (["poll", "polling", "voting", "ballot day", "voting underway"], "polling"),
    (["nomination", "nominations", "candidate", "filed papers"], "nomination"),
    (["announce", "announced", "scheduling", "gazetted", "slated", "proposed"], "announcement"),
]


def extract_stage(headline: str) -> str:
    """Extract event stage from headline keywords."""
    text_lower = headline.lower()
    for kw_list, stage_name in STAGE_RULES:
        for kw in kw_list:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                return stage_name
    return "none"


def compute_direction(headline: str) -> float:
    """Extract sentiment direction in range [-1.0, 1.0] from FinBERT/Lexicon."""
    analyzer = get_sentiment_analyzer()
    score_dict = analyzer.sentiment(headline) if hasattr(analyzer, "sentiment") else analyzer.score(headline)
    compound = float(score_dict.get("compound", 0.0))

    # Domain adjustments for monetary policy & macroeconomic shocks
    t = headline.lower()
    if any(k in t for k in ["cuts rate", "reduces rate", "rate cut", "slashes rate", "lowers rate"]):
        compound = max(compound, 0.65)
    elif any(k in t for k in ["hikes rate", "raises rate", "rate hike", "increases rate"]):
        compound = min(compound, -0.65)
    elif any(k in t for k in ["approves tranche", "unlocks funds", "bailout approved", "debt relief"]):
        compound = max(compound, 0.70)
    elif any(k in t for k in ["delays tranche", "stalls bailout", "rejects loan", "debt default"]):
        compound = min(compound, -0.70)

    return float(round(compound, 4))


def extract_event_mentions(headline: str) -> List[Dict[str, Any]]:
    """Extract event mentions from headline with rule-based and keyword matching.

    Parameters
    ----------
    headline : str
        The financial news headline text.

    Returns
    -------
    list of dict
        [
            {
                "event_type": str,
                "confidence": float,
                "calendar_type": str,
                "category": str,
                "stage": str,
                "direction": float
            },
            ...
        ]
    """
    if not headline or not headline.strip():
        return []

    text_lower = headline.lower()
    stage = extract_stage(headline)
    direction = compute_direction(headline)
    mentions: List[Dict[str, Any]] = []

    for rule in KEYWORD_RULES:
        matched_kws = [kw for kw in rule["keywords"] if re.search(r"\b" + re.escape(kw) + r"\b", text_lower)]
        if not matched_kws:
            continue

        # Determine specific sub-rule match
        event_type = rule["default_type"]
        calendar_type = rule["calendar_type"]
        confidence = rule["base_confidence"]

        for sub_kws, sub_type, sub_cal_type, sub_conf in rule["sub_rules"]:
            if any(re.search(r"\b" + re.escape(sk) + r"\b", text_lower) for sk in sub_kws):
                event_type = sub_type
                calendar_type = sub_cal_type
                confidence = sub_conf
                break

        # Boost confidence if multiple keywords match
        if len(matched_kws) > 1:
            confidence = min(0.99, confidence + 0.05)

        mentions.append({
            "event_type": event_type,
            "confidence": round(confidence, 2),
            "calendar_type": calendar_type,
            "category": rule["category"],
            "stage": stage,
            "direction": direction,
        })

    # Sort by confidence descending
    mentions.sort(key=lambda x: x["confidence"], reverse=True)
    return mentions

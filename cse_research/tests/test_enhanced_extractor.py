"""Unit and Integration Tests for Stage 5 Enhanced Multi-Label Event Extractor."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Ensure cse_research/src is on sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cse.news.enhanced_extractor import (
    EnhancedEventExtractor,
    extract_enhanced,
    get_enhanced_extractor,
)
from cse.news.schema import NewsExtraction
from cse.scenario.feature_builder import ScenarioFeatureBuilder

# 20 diverse test headlines spanning elections, policy, multi-event, fine-grained stages, and irrelevant news
SAMPLE_HEADLINES_20: List[Dict[str, Any]] = [
    # --- Group A: Pure Election News ---
    {
        "id": 1,
        "headline": "Presidential election gazetted for November as election commission accepts nominations",
        "expected_primary": "presidential_election",
        "expected_stage_family": ["official_statement", "announcement", "nomination"],
        "min_confidence": 0.70,
    },
    {
        "id": 2,
        "headline": "President dissolves parliament, calling parliamentary general election for next month",
        "expected_primary": "parliamentary_election",
        "expected_stage_family": ["announcement", "official_statement"],
        "min_confidence": 0.70,
    },
    {
        "id": 3,
        "headline": "Provincial council elections slated for next year following delimitation review",
        "expected_primary": "provincial_council_election",
        "expected_stage_family": ["announcement"],
        "min_confidence": 0.70,
    },
    # --- Group B: Pure Policy News ---
    {
        "id": 4,
        "headline": "Central Bank cuts policy interest rate by 50 basis points to stimulate private sector credit",
        "expected_primary": "central_bank_or_monetary_policy",
        "expected_direction_sign": 1,  # Positive
        "min_confidence": 0.70,
    },
    {
        "id": 5,
        "headline": "CBSL raises statutory reserve ratio and policy corridor rates amid inflation concerns",
        "expected_primary": "central_bank_or_monetary_policy",
        "expected_direction_sign": -1,  # Negative
        "min_confidence": 0.70,
    },
    {
        "id": 6,
        "headline": "Cabinet approved revised Value Added Tax appropriation bill and customs tariff reform",
        "expected_primary": "government_policy_or_budget_or_tax",
        "min_confidence": 0.70,
    },
    {
        "id": 7,
        "headline": "IMF executive board completes fourth review under EFF program, unlocking USD 336 million tranche",
        "expected_primary": "debt_restructuring_or_IMF",
        "expected_direction_sign": 1,  # Positive
        "min_confidence": 0.70,
    },
    # --- Group C: Multi-Event News ---
    {
        "id": 8,
        "headline": "President calls parliamentary election as IMF approves crucial loan tranche",
        "is_multi_event": True,
        "required_categories": ["parliamentary_election", "debt_restructuring_or_IMF"],
    },
    {
        "id": 9,
        "headline": "Central Bank eases policy rates while government unveils national budget revenue proposals",
        "is_multi_event": True,
        "required_categories": ["central_bank_or_monetary_policy", "government_policy_or_budget_or_tax"],
    },
    {
        "id": 10,
        "headline": "Cabinet reshuffle announced amid ongoing debt restructuring negotiations with bondholders",
        "is_multi_event": True,
        "required_categories": ["cabinet_or_ministry_change", "debt_restructuring_or_IMF"],
    },
    # --- Group D: Rumor vs Official vs Result vs Special Stages ---
    {
        "id": 11,
        "headline": "Rumors circulate that election commission mulls postponing provincial polls",
        "expected_stage": "rumor",
        "min_stage_conf": 0.70,
    },
    {
        "id": 12,
        "headline": "Market speculates CBSL likely to reduce policy corridor rates at upcoming monetary meeting",
        "expected_stage": "speculation",
        "min_stage_conf": 0.70,
    },
    {
        "id": 13,
        "headline": "Election Commission officially declares polling date for presidential poll via special gazette",
        "expected_stage": "official_statement",
        "min_stage_conf": 0.85,
    },
    {
        "id": 14,
        "headline": "Government enacts new revenue and VAT legislation effective from next Monday",
        "expected_stage": "implementation",
        "min_stage_conf": 0.80,
    },
    {
        "id": 15,
        "headline": "Final deadline expires for presidential candidates to file nomination papers",
        "expected_stage": "deadline",
        "min_stage_conf": 0.80,
    },
    {
        "id": 16,
        "headline": "Supreme Court orders postponement of local council elections until funds released",
        "expected_stage": "postponement",
        "min_stage_conf": 0.80,
    },
    {
        "id": 17,
        "headline": "Finance Ministry cancels proposed super gains tax following private sector outcry",
        "expected_stage": "cancellation",
        "min_stage_conf": 0.80,
    },
    {
        "id": 18,
        "headline": "Nationwide trade union strike escalates with tear gas fired during demonstration",
        "expected_stage": "escalation",
        "min_stage_conf": 0.80,
    },
    {
        "id": 19,
        "headline": "Official election results confirm ruling coalition secured decisive two-thirds parliamentary majority",
        "expected_stage": "result",
        "min_stage_conf": 0.85,
    },
    # --- Group E: Irrelevant News ---
    {
        "id": 20,
        "headline": "Sri Lanka national cricket team defeats Australia in thrilling second test match in Galle",
        "expected_primary": "not_relevant",
        "is_irrelevant": True,
    },
]


@pytest.fixture
def extractor() -> EnhancedEventExtractor:
    return get_enhanced_extractor()


def test_20_headlines_structure_and_extraction(extractor: EnhancedEventExtractor) -> None:
    """Validate all 20 sample headlines return complete structured outputs with expected bounds."""
    assert len(SAMPLE_HEADLINES_20) == 20

    for item in SAMPLE_HEADLINES_20:
        headline = item["headline"]
        res = extractor.extract(headline, source="Reuters")

        # 1. Verification of dictionary schema
        assert "event_categories" in res
        assert "primary_category" in res
        assert "stage" in res
        assert "stage_confidence" in res
        assert "direction" in res
        assert "intensity" in res
        assert "novelty" in res

        # 2. Bounded metric assertions
        assert 0.0 <= res["stage_confidence"] <= 1.0
        assert -1.0 <= res["direction"] <= 1.0
        assert 0.0 <= res["intensity"] <= 1.0
        assert 0.0 <= res["novelty"] <= 1.0

        for cat, conf in res["event_categories"].items():
            assert 0.0 <= conf <= 1.0, f"Confidence for {cat} must be in [0, 1], got {conf}"

        # 3. Primary category check
        if "expected_primary" in item:
            assert res["primary_category"] == item["expected_primary"], (
                f"Headline #{item['id']}: Expected primary '{item['expected_primary']}', got '{res['primary_category']}'"
            )

        # 4. Stage check
        if "expected_stage" in item:
            assert res["stage"] == item["expected_stage"], (
                f"Headline #{item['id']}: Expected stage '{item['expected_stage']}', got '{res['stage']}'"
            )
            assert res["stage_confidence"] >= item.get("min_stage_conf", 0.70)

        # 5. Multi-event check
        if item.get("is_multi_event"):
            cats = res["event_categories"]
            for req_cat in item["required_categories"]:
                assert req_cat in cats, f"Headline #{item['id']}: Multi-event missing '{req_cat}' in {cats}"
                assert cats[req_cat] >= 0.50

        # 6. Direction check
        if "expected_direction_sign" in item:
            expected_sign = item["expected_direction_sign"]
            if expected_sign > 0:
                assert res["direction"] > 0.0, f"Headline #{item['id']} should be positive, got {res['direction']}"
            elif expected_sign < 0:
                assert res["direction"] < 0.0, f"Headline #{item['id']} should be negative, got {res['direction']}"

        # 7. Irrelevant news check
        if item.get("is_irrelevant"):
            assert res["primary_category"] == "not_relevant"
            assert res["event_categories"].get("presidential_election", 0.0) == 0.0
            assert res["event_categories"].get("parliamentary_election", 0.0) == 0.0


def test_multi_label_event_extraction(extractor: EnhancedEventExtractor) -> None:
    """Test Requirement 1: 'President calls election; IMF approves tranche'
    produces multi-label confidences for both election and IMF.
    """
    headline = "President calls election; IMF approves tranche"
    res = extractor.extract(headline)

    cats = res["event_categories"]
    assert "election" in cats or "presidential_election" in cats
    assert "imf" in cats or "debt_restructuring_or_IMF" in cats

    elec_conf = max(cats.get("election", 0.0), cats.get("presidential_election", 0.0))
    imf_conf = max(cats.get("imf", 0.0), cats.get("debt_restructuring_or_IMF", 0.0))

    assert elec_conf >= 0.60
    assert imf_conf >= 0.75
    assert res["primary_category"] in ("debt_restructuring_or_IMF", "presidential_election")


def test_fine_grained_stage_types(extractor: EnhancedEventExtractor) -> None:
    """Test Requirement 1: Stage sub-types beyond announcement/polling/result:
    rumor, speculation, official_statement, implementation, deadline,
    postponement, cancellation, escalation, resolution.
    """
    stage_samples = {
        "rumor": "Reportedly insiders claim cabinet considering tax revision",
        "speculation": "Market speculates central bank poised to lower borrowing rates",
        "official_statement": "Official gazette statement confirms parliament dissolved",
        "implementation": "New customs tariff regulations effective from midnight",
        "deadline": "Final cut-off deadline expires for candidate filing",
        "postponement": "Provincial elections postponed indefinitely pending census",
        "cancellation": "Cabinet announces proposed super levy cancelled completely",
        "escalation": "Port strike escalates as trade unions intensify protest action",
        "resolution": "Government and official creditors sign debt restructuring pact reaching consensus",
    }

    for expected_stage, text in stage_samples.items():
        stg, conf = extractor.extract_stage(text)
        assert stg == expected_stage, f"Expected stage '{expected_stage}', got '{stg}' for '{text}'"
        assert conf >= 0.75


def test_continuous_confidence_mapping(extractor: EnhancedEventExtractor) -> None:
    """Test Requirement 2: Map to existing feature columns with continuous values (not hard 0/1)."""
    # 1. Official statement election
    h1 = "Election commission officially declares presidential poll date"
    res1 = extractor.extract(h1)
    feats1 = extractor.map_to_feature_columns(res1)

    assert "type_presidential" in feats1
    assert "type_parliamentary" in feats1
    assert "type_none" in feats1
    assert "stage_announcement" in feats1
    assert "stage_none" in feats1

    # Continuous confidence checks
    assert 0.0 < feats1["type_presidential"] <= 1.0
    assert 0.0 < feats1["stage_announcement"] <= 1.0
    assert feats1["type_parliamentary"] == 0.0
    assert 0.0 <= feats1["stage_none"] < 1.0

    # 2. Rumor headline should produce a lower stage_announcement than official statement
    h2 = "Rumors circulate that election commission mulls election date"
    res2 = extractor.extract(h2)
    feats2 = extractor.map_to_feature_columns(res2)

    assert feats2["stage_announcement"] < feats1["stage_announcement"]
    assert feats2["stage_none"] > feats1["stage_none"]


def test_novelty_and_intensity_computation(extractor: EnhancedEventExtractor) -> None:
    """Verify intensity and novelty metrics with custom past headlines."""
    headline = "Central Bank unexpectedly slashes policy corridor rates by 100 bps in emergency session"

    # Higher intensity due to 'emergency', 'slashes' and reputable source
    res_high = extractor.extract(headline, source="Reuters")
    res_low = extractor.extract("Bank meets", source="UnknownBlog")

    assert res_high["intensity"] > res_low["intensity"]

    # Novelty: headline identical to past news should have novelty ≈ 0.0
    identical_past = [headline, "Some other news"]
    nov_dup = extractor.compute_novelty(headline, past_headlines=identical_past)
    assert nov_dup <= 0.15

    # Novelty: unique headline with no semantic matches should have novelty ≈ 1.0
    completely_different_past = [
        "Tea exports rise in Q2",
        "Fisheries ministry distributes modern trawlers",
    ]
    nov_fresh = extractor.compute_novelty(headline, past_headlines=completely_different_past)
    assert nov_fresh > nov_dup
    assert nov_fresh >= 0.50


def test_feature_builder_with_enhanced_extractor() -> None:
    """Verify ScenarioFeatureBuilder produces valid feature row using Stage 5 extraction."""
    builder = ScenarioFeatureBuilder()
    news = NewsExtraction(
        is_relevant=True,
        event_category="presidential_election",
        stage="announcement",
        expected_direction="positive",
    )

    headline = "Presidential election poll announced for November as candidate nominations open"
    x_true, x_false, meta = builder.build_scenario_features(
        news_item=news,
        row_idx=0,
        as_of_date="2026-11-12",
        headline=headline,
    )

    assert "enhanced_extraction" in meta
    enh = meta["enhanced_extraction"]
    assert enh["primary_category"] == "presidential_election"
    assert enh["stage"] in ("official_statement", "announcement", "nomination")

    pres_col = builder.feature_cols.index("type_presidential")
    ann_col = builder.feature_cols.index("stage_announcement")

    # Values in vector are continuous floats between 0 and 1
    assert 0.0 < x_true[0, pres_col] <= 1.0
    assert 0.0 < x_true[0, ann_col] <= 1.0

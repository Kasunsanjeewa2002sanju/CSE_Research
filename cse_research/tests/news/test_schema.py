"""
Unit tests for Stage 10 news schema and data model validation.
"""

import pytest
from cse.news.schema import (
    EventCategory,
    ElectionStage,
    ExpectedDirection,
    NewsExtraction,
    validate_structured_event_dict,
)


def test_valid_payload():
    payload = {
        "is_relevant": True,
        "event_category": "presidential_election",
        "stage": "announcement",
        "expected_direction": "uncertain",
        "expected_direction_reason": "Timing unclear",
        "affected_sectors": ["banking"],
        "event_date_mentioned": "2024-09-21",
        "entities": ["President"],
        "confidence": 0.85,
        "language": "en",
    }
    extracted = NewsExtraction(**payload)
    assert extracted.is_relevant is True
    assert extracted.event_category == "presidential_election"
    assert extracted.confidence == 0.85
    assert extracted.to_dict()["stage"] == "announcement"
    assert extracted.dict()["expected_direction"] == "uncertain"
    assert extracted.model_dump()["entities"] == ["President"]


def test_invalid_event_category_rejected():
    payload = {
        "is_relevant": True,
        "event_category": "INVALID_CATEGORY_XYZ",
        "stage": "announcement",
        "expected_direction": "uncertain",
        "expected_direction_reason": "Test",
        "affected_sectors": [],
        "event_date_mentioned": None,
        "entities": [],
        "confidence": 0.8,
        "language": "en",
    }
    with pytest.raises(ValueError):
        NewsExtraction(**payload)


def test_out_of_range_confidence_rejected():
    payload = {
        "is_relevant": True,
        "event_category": "presidential_election",
        "stage": "announcement",
        "expected_direction": "uncertain",
        "expected_direction_reason": "Test",
        "affected_sectors": [],
        "event_date_mentioned": None,
        "entities": [],
        "confidence": 2.5,
        "language": "en",
    }
    with pytest.raises(ValueError):
        NewsExtraction(**payload)

    payload["confidence"] = -0.5
    with pytest.raises(ValueError):
        NewsExtraction(**payload)


def test_invalid_stage_rejected():
    payload = {
        "is_relevant": True,
        "event_category": "presidential_election",
        "stage": "non_existent_stage",
        "expected_direction": "uncertain",
        "expected_direction_reason": "Test",
        "affected_sectors": [],
        "event_date_mentioned": None,
        "entities": [],
        "confidence": 0.9,
        "language": "en",
    }
    with pytest.raises(ValueError):
        NewsExtraction(**payload)


def test_validate_structured_event_dict_missing_fields():
    incomplete = {
        "is_relevant": True,
        "event_category": "presidential_election",
    }
    with pytest.raises(ValueError):
        validate_structured_event_dict(incomplete)

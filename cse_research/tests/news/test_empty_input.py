"""
Unit tests for empty, whitespace, and edge-case inputs in Stage 10 news extraction.
"""

from cse.news.llm_extract import extract_event
from cse.news.offline import extract_offline
from cse.news.schema import EventCategory, NewsExtraction


def test_empty_input_offline_extractor():
    result = extract_offline("", "")
    assert isinstance(result, NewsExtraction)
    assert result.is_relevant is False
    assert result.event_category == EventCategory.NOT_RELEVANT.value
    assert result.confidence == 0.0
    assert result.stage == "none"


def test_whitespace_input_offline_extractor():
    result = extract_offline("   \n\t  ", "   ")
    assert isinstance(result, NewsExtraction)
    assert result.is_relevant is False
    assert result.event_category == EventCategory.NOT_RELEVANT.value
    assert result.confidence == 0.0


def test_empty_input_llm_extract_function():
    result = extract_event("", "", publication_date="2024-01-01", use_cache=False)
    assert isinstance(result, NewsExtraction)
    assert result.is_relevant is False
    assert result.event_category == EventCategory.NOT_RELEVANT.value
    assert result.confidence == 0.0
    assert result.expected_direction == "neutral"


def test_none_parameters_handled_safely():
    result = extract_offline(headline="", description="", date="", source=None)
    assert isinstance(result, NewsExtraction)
    assert result.is_relevant is False

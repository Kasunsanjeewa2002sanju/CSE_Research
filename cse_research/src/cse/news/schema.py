"""
Schema and data models for Stage 10 news event extraction and structuring.

This module defines strict enum constraints, dataclasses, and JSON schema
validation for transforming raw unstructured financial and political news items
into validated qualitative macro-event representations for the Colombo Stock Exchange.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EventCategory(str, Enum):
    """Enumeration of recognized political and macroeconomic event categories."""
    PRESIDENTIAL_ELECTION = "presidential_election"
    PARLIAMENTARY_ELECTION = "parliamentary_election"
    PROVINCIAL_COUNCIL_ELECTION = "provincial_council_election"
    LOCAL_GOVERNMENT_ELECTION = "local_government_election"
    CABINET_OR_MINISTRY_CHANGE = "cabinet_or_ministry_change"
    GOVERNMENT_POLICY_OR_BUDGET_OR_TAX = "government_policy_or_budget_or_tax"
    CENTRAL_BANK_OR_MONETARY_POLICY = "central_bank_or_monetary_policy"
    POLITICAL_ARREST_OR_IMPRISONMENT = "political_arrest_or_imprisonment"
    PROTEST_OR_UNREST = "protest_or_unrest"
    DEBT_RESTRUCTURING_OR_IMF = "debt_restructuring_or_IMF"
    OTHER_POLITICAL = "other_political"
    NOT_RELEVANT = "not_relevant"


class ElectionStage(str, Enum):
    """Six formal stages of Sri Lankan election lifecycles plus none."""
    ANNOUNCEMENT = "announcement"
    NOMINATIONS = "nominations"
    CAMPAIGN = "campaign"
    VOTING = "voting"
    RESULTS = "results"
    FORMATION = "formation"
    NONE = "none"


class ExpectedDirection(str, Enum):
    """Expected directional impact on Colombo Stock Exchange (ASPI/S&P SL20)."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"


VALID_EVENT_CATEGORIES = {e.value for e in EventCategory}
VALID_ELECTION_STAGES = {e.value for e in ElectionStage} | {"none", None}
VALID_EXPECTED_DIRECTIONS = {e.value for e in ExpectedDirection}


@dataclass
class NewsItemInput:
    """Raw incoming news item provided for semantic structuring."""
    headline: str
    description: str = ""
    publication_date: str = ""
    source: Optional[str] = None


@dataclass
class NewsExtraction:
    """
    Validated structured event representation extracted from news.
    
    Fields comply with strict research constraints and are validated upon instantiation.
    """
    is_relevant: bool
    event_category: str
    stage: Optional[str] = "none"
    expected_direction: str = "uncertain"
    expected_direction_reason: str = ""
    affected_sectors: List[str] = field(default_factory=list)
    event_date_mentioned: Optional[str] = None
    entities: List[str] = field(default_factory=list)
    confidence: float = 1.0
    language: str = "en"

    def __post_init__(self) -> None:
        # 1. Type validation
        if not isinstance(self.is_relevant, bool):
            raise TypeError(f"is_relevant must be a boolean, got {type(self.is_relevant).__name__}")

        # 2. Enum check for event_category
        cat_val = self.event_category.value if isinstance(self.event_category, Enum) else str(self.event_category)
        if cat_val not in VALID_EVENT_CATEGORIES:
            raise ValueError(
                f"Invalid event_category '{self.event_category}'. Must be one of: {sorted(VALID_EVENT_CATEGORIES)}"
            )
        self.event_category = cat_val

        # 3. Enum check for stage
        if self.stage is not None:
            stg_val = self.stage.value if isinstance(self.stage, Enum) else str(self.stage)
            if stg_val not in VALID_ELECTION_STAGES:
                raise ValueError(
                    f"Invalid stage '{self.stage}'. Must be one of: {sorted(s for s in VALID_ELECTION_STAGES if s)}"
                )
            self.stage = stg_val
        else:
            self.stage = "none"

        # 4. Enum check for expected_direction
        dir_val = self.expected_direction.value if isinstance(self.expected_direction, Enum) else str(self.expected_direction)
        if dir_val not in VALID_EXPECTED_DIRECTIONS:
            raise ValueError(
                f"Invalid expected_direction '{self.expected_direction}'. Must be one of: {sorted(VALID_EXPECTED_DIRECTIONS)}"
            )
        self.expected_direction = dir_val

        # 5. Range check for confidence
        try:
            self.confidence = float(self.confidence)
        except (ValueError, TypeError):
            raise TypeError(f"confidence must be a float, got {self.confidence}")

        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

        # 6. Normalize list fields
        if not isinstance(self.affected_sectors, list):
            self.affected_sectors = list(self.affected_sectors) if self.affected_sectors else []
        if not isinstance(self.entities, list):
            self.entities = list(self.entities) if self.entities else []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard dictionary."""
        return asdict(self)

    def dict(self) -> Dict[str, Any]:
        """Pydantic v1 compatibility alias."""
        return self.to_dict()

    def model_dump(self) -> Dict[str, Any]:
        """Pydantic v2 compatibility alias."""
        return self.to_dict()

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


# Alias for backward compatibility with previous design
StructuredEventOutput = NewsExtraction


STRUCTURED_EVENT_JSON_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "NewsExtraction",
    "type": "object",
    "required": [
        "is_relevant",
        "event_category",
        "stage",
        "expected_direction",
        "expected_direction_reason",
        "affected_sectors",
        "event_date_mentioned",
        "entities",
        "confidence",
        "language",
    ],
    "properties": {
        "is_relevant": {
            "type": "boolean",
            "description": "True if the article relates to Sri Lankan macroeconomic or political events influencing CSE."
        },
        "event_category": {
            "type": "string",
            "enum": sorted(list(VALID_EVENT_CATEGORIES)),
            "description": "Category of macro/political event."
        },
        "stage": {
            "type": ["string", "null"],
            "enum": [
                "announcement",
                "nominations",
                "campaign",
                "voting",
                "results",
                "formation",
                "none",
                None,
            ],
            "description": "Election cycle stage if applicable, or 'none'."
        },
        "expected_direction": {
            "type": "string",
            "enum": sorted(list(VALID_EXPECTED_DIRECTIONS)),
            "description": "Theoretical expectation of stock market impact."
        },
        "expected_direction_reason": {
            "type": "string",
            "description": "One-sentence rationalization grounded in market mechanics."
        },
        "affected_sectors": {
            "type": "array",
            "items": {"type": "string"},
            "description": "CSE GICS sectors directly exposed to policy/event shock."
        },
        "event_date_mentioned": {
            "type": ["string", "null"],
            "description": "ISO date (YYYY-MM-DD) or explicit date string mentioned in news, or null."
        },
        "entities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Named political leaders, institutions, regulators, or parties mentioned."
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Model confidence in classification (0.0 to 1.0)."
        },
        "language": {
            "type": "string",
            "default": "en",
            "description": "Language code of the source news item."
        }
    },
    "additionalProperties": False
}


def validate_structured_event_dict(payload: Dict[str, Any]) -> NewsExtraction:
    """
    Validate a raw dictionary against the strict schema and return a NewsExtraction instance.
    """
    import jsonschema

    try:
        jsonschema.validate(instance=payload, schema=STRUCTURED_EVENT_JSON_SCHEMA)
    except jsonschema.ValidationError as err:
        raise ValueError(f"Schema validation error: {err.message} at path {list(err.path)}") from err

    return NewsExtraction(**payload)

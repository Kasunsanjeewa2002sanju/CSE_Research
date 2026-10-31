"""
Prompt injection defense and adversarial input containment for Stage 10.

Treats all incoming article text strictly as inert data. Defangs attempts
to override system instructions, break out of JSON delimiters, or inject
adversarial command tokens.
"""

from __future__ import annotations

import html
import re
from typing import List, Tuple

# Patterns commonly used in prompt injection, jailbreaking, or delimiter breakout
INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\s+(?:(?:all|any|prior|previous)\s+)*instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(?:(?:all|any|prior|previous)\s+)*(?:instructions?|prompts?|rules?)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"assistant\s*:\s*", re.IGNORECASE),
    re.compile(r"override\s+(?:all\s+|previous\s+)?rules", re.IGNORECASE),
    re.compile(r"return\s+(?:only\s+)?(?:is_relevant\s*=\s*true|valid\s+json)", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"output\s+the\s+following\s+json", re.IGNORECASE),
    re.compile(r"forget\s+(?:all\s+|everything)", re.IGNORECASE),
    re.compile(r"<\s*/?\s*untrusted_news_data\s*>", re.IGNORECASE),
    re.compile(r"```(?:json)?", re.IGNORECASE),
]


def is_suspicious_text(text: str) -> bool:
    """Check if input text triggers any prompt injection heuristics."""
    if not text:
        return False
    return any(p.search(text) is not None for p in INJECTION_PATTERNS)


def sanitize_text(text: str) -> str:
    """
    Sanitize untrusted news text by stripping breakout tokens, neutralizing
    adversarial instructional patterns, and normalizing characters.
    """
    if not text or not isinstance(text, str):
        return ""

    sanitized = text

    # Defang adversarial instructional phrases
    for pattern in INJECTION_PATTERNS:
        if pattern.search(sanitized):
            sanitized = pattern.sub("[REDACTED_PROMPT_INJECTION]", sanitized)

    # Strip control characters except newline and tab
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", sanitized)

    # Escape HTML/XML tags that could attempt markup breakout
    sanitized = re.sub(r"<[^>]+>", " ", sanitized)

    # Normalize excessive whitespace
    sanitized = re.sub(r"[ \t]+", " ", sanitized).strip()

    return sanitized


def wrap_untrusted_input(headline: str, description: str = "") -> str:
    """
    Wrap sanitized headline and description in strong semantic XML fencing,
    explicitly instructing downstream models to treat the content as data only.
    """
    clean_headline = sanitize_text(headline)
    clean_description = sanitize_text(description)

    return (
        "<untrusted_news_data>\n"
        f"  <headline>{clean_headline}</headline>\n"
        f"  <description>{clean_description}</description>\n"
        "</untrusted_news_data>"
    )


class PromptInjectionGuard:
    """Stateful wrapper for prompt injection inspection and sanitation."""

    def __init__(self, reject_on_injection: bool = False):
        self.reject_on_injection = reject_on_injection

    def inspect(self, text: str) -> Tuple[bool, str]:
        """
        Inspect text and return (is_malicious, sanitized_text).
        """
        flagged = is_suspicious_text(text)
        cleaned = sanitize_text(text)
        return flagged, cleaned

"""
User bookmarks and System Usability Scale (SUS) survey endpoints.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter(tags=["User Favorites & SUS Survey"])


@router.get("/user/favorites")
def get_user_favorites() -> Dict[str, Any]:
    """Returns saved favorite events, models, figures, and tables."""
    return {
        "favorites": [
            {
                "id": "fav_01",
                "item_type": "event",
                "title": "2015 Presidential General Election",
                "target_url": "/events/ELEC_13",
                "saved_at": "2026-10-14T10:00:00Z",
            },
            {
                "id": "fav_02",
                "item_type": "model",
                "title": "CatBoostRegressor (Horizon h=5)",
                "target_url": "/model-lab",
                "saved_at": "2026-10-14T10:05:00Z",
            },
        ]
    }


@router.get("/survey/sus")
def get_sus_survey() -> Dict[str, Any]:
    """Returns standard 10-item System Usability Scale (Brooke 1996) questionnaire."""
    questions = [
        {"id": 1, "prompt": "I think that I would like to use this platform frequently.", "polarity": "positive"},
        {"id": 2, "prompt": "I found the platform unnecessarily complex.", "polarity": "negative"},
        {"id": 3, "prompt": "I thought the platform was easy to use.", "polarity": "positive"},
        {"id": 4, "prompt": "I think that I would need the support of a technical person to be able to use this system.", "polarity": "negative"},
        {"id": 5, "prompt": "I found the various functions in this system were well integrated.", "polarity": "positive"},
        {"id": 6, "prompt": "I thought there was too much inconsistency in this system.", "polarity": "negative"},
        {"id": 7, "prompt": "I would imagine that most people would learn to use this system very quickly.", "polarity": "positive"},
        {"id": 8, "prompt": "I found the system very cumbersome to use.", "polarity": "negative"},
        {"id": 9, "prompt": "I felt very confident using the system.", "polarity": "positive"},
        {"id": 10, "prompt": "I needed to learn a lot of things before I could get going with this system.", "polarity": "negative"},
    ]
    return {
        "version": "1.0",
        "questions": questions,
    }

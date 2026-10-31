import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
import httpx
import numpy as np
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import validate_url_safety, sanitize_text
from backend.app.core.database import SessionLocal, NewsArticle, VerificationLog
from backend.app.news.classifier import NewsClassifier
from backend.app.data.event_loader import EventDataLoader
from backend.app.ml.predict import UnifiedPredictor
from backend.app.ml.forecasting import FanChartForecaster

class NewsVerifier:
    """
    Evidence-based news verification engine.
    Extracts core political/economic claims from submitted text or URLs,
    matches claims against stored news feeds and official events,
    and applies transparent verification rules.
    """
    def __init__(self):
        self.classifier = NewsClassifier()
        self.event_loader = EventDataLoader()
        self.predictor = UnifiedPredictor()
        self.forecaster = FanChartForecaster()

    def fetch_url_content(self, url: str) -> Tuple[bool, str, str]:
        """Safely fetches headline and summary text from a submitted URL with SSRF checks."""
        is_safe, msg = validate_url_safety(url)
        if not is_safe:
            return False, "", msg

        try:
            resp = httpx.get(
                url,
                timeout=5.0,
                headers={"User-Agent": "PolitiTradeLK/1.0 VerificationBot"},
                follow_redirects=True
            )
            if resp.status_code != 200:
                return False, "", f"Publisher returned HTTP status {resp.status_code}"

            text = resp.text[:20000]
            # Extract simple title
            m_title = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
            title = m_title.group(1).strip() if m_title else ""
            title = re.sub(r"\s+", " ", title)

            # Strip html tags for plain text snippet
            clean_body = re.sub(r"<[^>]+>", " ", text)
            clean_body = re.sub(r"\s+", " ", clean_body).strip()[:1000]

            return True, f"{title}. {clean_body}", "Success"
        except Exception as e:
            return False, "", f"Unable to fetch URL: {str(e)}"

    def extract_claim(self, raw_text: str) -> Dict[str, Any]:
        """Extracts structured entities, event category, and action keywords from text."""
        sanitized = sanitize_text(raw_text, max_length=2000)
        family, subtype, rel = self.classifier.classify(sanitized)

        # Entity discovery
        entities_found = []
        known_political_figures = [
            "Anura Kumara Dissanayake", "Ranil Wickremesinghe", "Mahinda Rajapaksa",
            "Gotabaya Rajapaksa", "Sajith Premadasa", "Harsha de Silva", "Ali Sabry",
            "Nandalal Weerasinghe", "Sarath Fonseka", "Basil Rajapaksa", "Vijitha Herath"
        ]
        for fig in known_political_figures:
            if fig.lower() in sanitized.lower():
                entities_found.append(fig)

        institutions_found = []
        known_inst = ["Central Bank", "CBSL", "Ministry of Finance", "IMF", "CID", "Supreme Court", "Parliament", "CSE"]
        for inst in known_inst:
            if inst.lower() in sanitized.lower():
                institutions_found.append(inst)

        return {
            "raw_text": sanitized,
            "event_family": family,
            "event_subtype": subtype,
            "entities": entities_found,
            "institutions": institutions_found,
            "summary_claim": sanitized[:250] + ("..." if len(sanitized) > 250 else "")
        }

    def verify_claim(self, user_input_text: str, user_input_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes complete verification pipeline:
        Input validation -> Claim extraction -> Evidence search -> Verdict -> Scenarios.
        """
        target_text = user_input_text.strip() if user_input_text else ""
        fetch_notice = None

        if user_input_url:
            ok, fetched, msg = self.fetch_url_content(user_input_url)
            if ok:
                target_text = f"{target_text} {fetched}".strip()
                fetch_notice = f"Successfully extracted text from {urlparse(user_input_url).hostname}"
            else:
                fetch_notice = f"URL retrieval error: {msg}"

        if len(target_text) < 10:
            return {
                "verdict": "Unverified",
                "confidence_score": 0.0,
                "claim_summary": "Input text too brief to extract verifiable claims.",
                "matched_evidence": [],
                "explanation": "Please provide a more descriptive headline or paragraph to verify.",
                "scenarios": None
            }

        claim = self.extract_claim(target_text)

        # Search Evidence in SQLite News Database and Historical Events
        db: Session = SessionLocal()
        matched_evidence = []
        try:
            articles = db.query(NewsArticle).all()
            for art in articles:
                clean_summary = re.sub(r"<[^>]+>", " ", art.summary or "")
                h_sort = fuzz.token_sort_ratio(claim["raw_text"].lower(), art.headline.lower())
                h_set = fuzz.token_set_ratio(claim["raw_text"].lower(), art.headline.lower())
                score_h = max(h_sort, (h_set * 0.85 + h_sort * 0.15))
                
                sentences = [s.strip() for s in re.split(r'[\.\n]+', clean_summary) if len(s.strip()) > 15]
                score_body = max([fuzz.token_sort_ratio(claim["raw_text"].lower(), s.lower()) for s in sentences] or [0.0])
                
                sim = max(score_h, score_body)
                if sim >= 55:
                    matched_evidence.append({
                        "source_name": art.source_name,
                        "source_url": art.source_url,
                        "source_tier": art.source_tier,
                        "headline": art.headline,
                        "published_at": art.published_at.strftime("%Y-%m-%d %H:%M") if art.published_at else "Recent",
                        "similarity_score": round(sim, 1),
                        "evidence_type": "Current News Article"
                    })
        finally:
            db.close()

        # Also search historical verified events
        study_events = self.event_loader.load_all_events()
        for _, ev in study_events.iterrows():
            clean_ev_summary = re.sub(r"<[^>]+>", " ", str(ev.get("summary", "")))
            ev_title = str(ev["title"])
            e_sort = fuzz.token_sort_ratio(claim["raw_text"].lower(), ev_title.lower())
            e_set = fuzz.token_set_ratio(claim["raw_text"].lower(), ev_title.lower())
            score_e = max(e_sort, (e_set * 0.85 + e_sort * 0.15))
            
            sentences = [s.strip() for s in re.split(r'[\.\n]+', clean_ev_summary) if len(s.strip()) > 15]
            score_ev_body = max([fuzz.token_sort_ratio(claim["raw_text"].lower(), s.lower()) for s in sentences] or [0.0])
            sim = max(score_e, score_ev_body)
            if sim >= 60:
                matched_evidence.append({
                    "source_name": "PolitiTrade LK Historical Dataset",
                    "source_url": ev["sources"][0]["url"] if ev.get("sources") and len(ev["sources"]) > 0 else "#",
                    "source_tier": 1,
                    "headline": ev["title"],
                    "published_at": str(ev["Aligned_Trading_Date"]),
                    "similarity_score": round(sim, 1),
                    "evidence_type": "Verified Historical Record"
                })

        matched_evidence.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_matches = matched_evidence[:4]

        # Formulate Verdict
        max_sim = top_matches[0]["similarity_score"] if top_matches else 0.0
        has_tier_1 = any(m["source_tier"] == 1 for m in top_matches if m["similarity_score"] >= 70)
        
        if max_sim >= 80 and (has_tier_1 or any(m["source_tier"] <= 2 for m in top_matches)):
            verdict = "Confirmed by credible reporting"
            heuristic_score = min(0.95, 0.70 + (max_sim / 350.0))
            explanation = (
                f"The reported claim is corroborated by high-confidence coverage from "
                f"'{top_matches[0]['source_name']}' with a match score of {max_sim}%."
            )
        elif max_sim >= 65:
            verdict = "Partially corroborated"
            heuristic_score = min(0.70, 0.40 + (max_sim / 250.0))
            explanation = (
                f"Related reporting was identified from '{top_matches[0]['source_name']}', "
                f"corroborating general entities and themes, but exact claim details require independent primary confirmation."
            )
        else:
            verdict = "Unverified"
            heuristic_score = max(0.10, max_sim / 200.0)
            explanation = (
                "We could not find enough independent evidence to verify this claim across official portals "
                "or established news publishers. This does not prove the story is fabricated, but indicates lack of published corroboration."
            )

        # Generate True vs False Market Prediction Scenarios (Section 13)
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Scenario A: If Event Occurs
        scenario_a_pred = self.predictor.predict(
            event_family=claim["event_family"],
            event_subtype=claim["event_subtype"],
            headline_or_title=claim["summary_claim"],
            event_date=current_date_str,
            forecast_horizon=5
        )
        scenario_a_fan = self.forecaster.generate_fan_forecast(
            base_date=current_date_str,
            expected_car_5d=float(scenario_a_pred["expected_return_pct"]) / 100.0,
            horizon_days=10
        )

        # Scenario B: If Event Does Not Occur (Strict No-Event Market Baseline)
        scenario_b_fan = self.forecaster.generate_fan_forecast(
            base_date=current_date_str,
            expected_car_5d=0.0,  # Zero political event shock
            horizon_days=10
        )

        return {
            "verdict": verdict,
            "heuristic_evidence_score": round(heuristic_score, 2),
            "claim_summary": claim["summary_claim"],
            "detected_event_family": claim["event_family"],
            "detected_event_subtype": claim["event_subtype"],
            "entities_detected": claim["entities"],
            "institutions_detected": claim["institutions"],
            "fetch_notice": fetch_notice,
            "matched_evidence": top_matches,
            "explanation": explanation,
            "scenarios": {
                "scenario_a_true": {
                    "label": "Scenario A: If Reported Event is True / Occurs",
                    "expected_return_pct": scenario_a_pred["expected_return_pct"],
                    "interval_lower_pct": scenario_a_pred["interval_lower_pct"],
                    "interval_upper_pct": scenario_a_pred["interval_upper_pct"],
                    "predicted_direction": scenario_a_pred["predicted_direction"],
                    "forecast_points": scenario_a_fan["forecast_path"]
                },
                "scenario_b_false": {
                    "label": "Scenario B: No-Event Baseline (If False or Does Not Occur)",
                    "expected_return_pct": 0.0,
                    "interval_lower_pct": round(-1.96 * scenario_b_fan["daily_volatility_pct"] * np.sqrt(5), 2),
                    "interval_upper_pct": round(1.96 * scenario_b_fan["daily_volatility_pct"] * np.sqrt(5), 2),
                    "predicted_direction": "Baseline Drift",
                    "forecast_points": [
                        {
                            "trading_day": p["trading_day"],
                            "date": p["date"],
                            "projected_close": p["baseline_no_event"],
                            "lower_95": p["lower_95"],
                            "upper_95": p["upper_95"]
                        }
                        for p in scenario_b_fan["forecast_path"]
                    ],
                    "scientific_notice": "Scenario B represents the unshocked market baseline, not an empirical model of market reactions to misinformation."
                }
            }
        }

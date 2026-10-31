import pytest
from backend.app.core.security import validate_url_safety, sanitize_text
from backend.app.news.classifier import NewsClassifier
from backend.app.news.verification import NewsVerifier

def test_ssrf_protection():
    # Loopback and internal private IP blocks
    safe, msg = validate_url_safety("http://127.0.0.1:8000/admin")
    assert safe is False

    safe, msg = validate_url_safety("http://localhost:5000/secret")
    assert safe is False

    safe, msg = validate_url_safety("http://169.254.169.254/latest/meta-data")
    assert safe is False

    safe, msg = validate_url_safety("http://192.168.1.1/router")
    assert safe is False

    # Valid public domain
    safe, msg = validate_url_safety("https://www.reuters.com/business")
    assert safe is True

def test_news_classifier():
    classifier = NewsClassifier()
    fam, sub, rel = classifier.classify("Central Bank hikes policy rates to stabilize inflation")
    assert fam == "Government Policy"
    assert sub == "Monetary Policy and Interest Rates"

    fam2, sub2, rel2 = classifier.classify("Former Minister remanded by Teldeniya Magistrate Court")
    assert fam2 == "Political Arrest"
    assert sub2 == "Detention or Remand"

def test_news_verifier_unverified_fallback():
    verifier = NewsVerifier()
    # Fictitious or uncorroborated event
    res = verifier.verify_claim("Aliens land in Colombo and nationalize stock exchange on Tuesday")
    assert res["verdict"] == "Unverified"
    assert "We could not find enough independent evidence" in res["explanation"]
    assert "scenarios" in res
    assert "scenario_a_true" in res["scenarios"]
    assert "scenario_b_false" in res["scenarios"]

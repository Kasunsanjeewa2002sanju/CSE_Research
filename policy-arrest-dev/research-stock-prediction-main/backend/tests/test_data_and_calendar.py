import pytest
import pandas as pd
from backend.app.data.trading_calendar import TradingCalendar
from backend.app.events.policy_processor import derive_policy_category
from backend.app.events.arrest_processor import parse_person_entities, derive_arrest_subtype

def test_trading_calendar_basic():
    dates = ["2022-01-03", "2022-01-04", "2022-01-05", "2022-01-07"]
    cal = TradingCalendar(dates)
    
    assert cal.is_trading_day("2022-01-03") is True
    assert cal.is_trading_day("2022-01-06") is False  # Holiday / gap
    
    # Align holiday
    aligned_date, align_type, lag = cal.align_to_trading_day("2022-01-06")
    assert aligned_date == "2022-01-07"
    assert align_type == "Next-Session (Weekend/Holiday)"
    assert lag == 1

def test_policy_taxonomy_derivation():
    cat1 = derive_policy_category(
        "Value Added Tax (VAT) Act", "Tax Reform", "VAT rate increased to 15%", "Fiscal Policy"
    )
    assert cat1 == "Tax Changes"
    
    cat2 = derive_policy_category(
        "Central Bank Floats Rupee", "Forex Policy", "Exchange rate floated", "Foreign Exchange Policy"
    )
    assert cat2 == "Foreign Exchange Policy"

    cat3 = derive_policy_category(
        "IMF Extended Fund Facility", "Debt Restructuring", "SLA approved by IMF", "Fiscal Policy"
    )
    assert cat3 == "IMF and Debt Restructuring"

def test_arrest_parsing_and_subtypes():
    parsed = parse_person_entities(
        "General Anuruddha Ratwatte, Criminal Investigation Department (CID), Teldeniya Magistrate Court"
    )
    assert "Ratwatte" in parsed["main_person"]
    assert any("CID" in inst for inst in parsed["institutions"])

    sub_pardon = derive_arrest_subtype(
        "Presidential Pardon and Release", "Pardoned by President", "Corruption", "Remanded"
    )
    assert sub_pardon == "Pardon or Release"

    sub_sentencing = derive_arrest_subtype(
        "Sentenced to 3 years imprisonment", "High court ruling", "Subversion", "Remanded"
    )
    assert sub_sentencing == "Sentencing"

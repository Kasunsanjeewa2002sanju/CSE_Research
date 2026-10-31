import re
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.trading_calendar import TradingCalendar

# 10 Policy Taxonomy Categories from Section 4.2
POLICY_TAXONOMY = [
    "Budget Changes",
    "Tax Changes",
    "Monetary Policy and Interest Rates",
    "Foreign Exchange Policy",
    "IMF and Debt Restructuring",
    "Investment and Privatisation",
    "Trade and Import Restrictions",
    "Price Controls and Subsidies",
    "Security and Emergency Economic Measures",
    "Political and Constitutional Policy Decisions",
]

def derive_policy_category(policy_name: str, subcategory: str, summary: str, raw_type: str) -> str:
    """
    Deterministically maps raw policy attributes into the standard 10-category policy taxonomy.
    Preserves precision rather than collapsing into generic 'Fiscal Policy'.
    """
    text = f"{policy_name} {subcategory} {summary} {raw_type}".lower()
    
    # 1. IMF & Debt Restructuring
    if any(k in text for k in ["imf", "debt restructuring", "external debt", "extended fund facility", "debt moratorium", "isb restructuring", "debt default"]):
        return "IMF and Debt Restructuring"
        
    # 2. Foreign Exchange Policy
    if any(k in text for k in ["foreign exchange", "float", "floating of the sri lankan rupee", "currency float", "rupee peg", "forex surrender", "lkr depreciation"]):
        return "Foreign Exchange Policy"
        
    # 3. Monetary Policy and Interest Rates
    if any(k in text for k in ["monetary policy", "interest rate", "policy rate", "sdfr", "slfr", "standing deposit", "statutory reserve ratio", "srr", "central bank rate"]):
        return "Monetary Policy and Interest Rates"
        
    # 4. Budget Changes
    if any(k in text for k in ["national budget", "budget presentation", "annual budget", "interim budget", "appropriation bill", "reform-oriented national budget"]):
        return "Budget Changes"
        
    # 5. Tax Changes
    if any(k in text for k in ["tax", "vat", "value added tax", "nsl", "national security levy", "income tax", "corporate tax", "withholding", "sscl", "social security contribution", "customs duty surcharge", "tax package", "tax cut", "tax reform"]):
        return "Tax Changes"
        
    # 6. Investment and Privatisation
    if any(k in text for k in ["privatisation", "privatization", "ipo", "state equity", "divestment", "entry and privatization", "sri lanka telecom", "lanka ioc entry"]):
        return "Investment and Privatisation"
        
    # 7. Trade and Import Restrictions
    if any(k in text for k in ["import ban", "import restriction", "customs tariff", "export ban", "import surcharges", "trade restriction"]):
        return "Trade and Import Restrictions"
        
    # 8. Price Controls and Subsidies
    if any(k in text for k in ["price control", "price regulation", "subsidy", "fuel price formula", "electricity tariff", "kerosene subsidy", "cost of living relief"]):
        return "Price Controls and Subsidies"
        
    # 9. Security and Emergency Economic Measures
    if any(k in text for k in ["emergency", "war footing", "public security", "curfew", "ceasefire", "peace accord", "cfa", "easter attacks", "state of emergency"]):
        return "Security and Emergency Economic Measures"
        
    # 10. Political and Constitutional Decisions
    if any(k in text for k in ["constitutional", "cabinet", "prorogation", "parliamentary majority", "regaining sri lanka", "manifesto", "election pledge"]):
        return "Political and Constitutional Policy Decisions"
        
    # Fallback to Budget Changes if fiscal
    if "budget" in text or "fiscal" in text:
        return "Budget Changes"
        
    return "Budget Changes"

class PolicyProcessor:
    """Processes, cleans, validates, and aligns government policy records."""

    def __init__(self, calendar: TradingCalendar):
        self.calendar = calendar

    def load_and_process(self, csv_path: Optional[Path] = None) -> pd.DataFrame:
        if csv_path is None:
            p1 = settings.EVENT_DATASET_DIR / "Government_Policies.csv"
            p2 = settings.EVENT_DATASET_DIR / "Government_Policies(1).csv"
            csv_path = p1 if p1.exists() else p2

        logger.info(f"Loading government policies from {csv_path}")
        df = pd.read_csv(csv_path)

        # Strip whitespace
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", np.nan)

        # Standardize dates to YYYY-MM-DD
        date_fields = ["Primary_Event_Date", "Announcement_Date", "Approval_Date", "Effective_Date", "Next_CSE_Trading_Date"]
        for c in date_fields:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce").dt.strftime("%Y-%m-%d")

        # Derive 10-category policy taxonomy
        derived_cats = []
        for _, row in df.iterrows():
            cat = derive_policy_category(
                str(row.get("Policy_Name", "")),
                str(row.get("Policy_Subcategory", "")),
                str(row.get("Policy_Summary", "")),
                str(row.get("Policy_Type", ""))
            )
            derived_cats.append(cat)
        df["Derived_Policy_Category"] = derived_cats
        df["Event_Family"] = "Government Policy"

        # Align to CSE Trading Calendar
        aligned_dates = []
        alignment_types = []
        lags = []

        for _, row in df.iterrows():
            # Use announcement date if present, otherwise primary event date
            target_date = row.get("Announcement_Date")
            if not target_date or pd.isna(target_date):
                target_date = row.get("Primary_Event_Date")

            aligned_date, align_type, lag_days = self.calendar.align_to_trading_day(str(target_date))
            aligned_dates.append(aligned_date)
            alignment_types.append(align_type)
            lags.append(lag_days)

        df["Aligned_Trading_Date"] = aligned_dates
        df["Alignment_Type"] = alignment_types
        df["Calendar_Lag_Days"] = lags
        df["Is_Direct_Trading_Day"] = (df["Alignment_Type"] == "Same-Day Trading")

        return df

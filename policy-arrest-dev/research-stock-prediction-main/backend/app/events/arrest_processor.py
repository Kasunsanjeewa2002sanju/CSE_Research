import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.trading_calendar import TradingCalendar

# 7 Legal Action Subtypes from Section 4.3
ARREST_SUBTYPES = [
    "Arrest",
    "Detention or Remand",
    "Sentencing",
    "Court Proceedings",
    "Pardon or Release",
    "Parliamentary Action",
    "Other Legal Development"
]

KNOWN_INSTITUTIONS = [
    "CID", "TID", "FCID", "Criminal Investigation Department",
    "Terrorist Investigation Division", "Supreme Court", "High Court",
    "Magistrate Court", "Court Martial", "Military Police", "Police",
    "Attorney General's Department", "Bribery Commission", "CIABOC",
    "Parliament", "Ministry of Defence", "European Union"
]

def parse_person_entities(raw_person_str: str) -> Dict[str, Any]:
    """
    Parses 'Person_Name' field which may contain multiple entities, persons, and institutions.
    E.g. "General Anuruddha Ratwatte, Criminal Investigation Department (CID), Teldeniya Magistrate Court"
    """
    if not raw_person_str or pd.isna(raw_person_str):
        return {
            "main_person": "Unspecified Political Figure",
            "other_persons": [],
            "institutions": []
        }
        
    parts = [p.strip() for p in re.split(r"[,/]", str(raw_person_str)) if p.strip()]
    
    institutions = []
    persons = []
    
    for part in parts:
        is_inst = any(inst.lower() in part.lower() for inst in KNOWN_INSTITUTIONS)
        if is_inst:
            institutions.append(part)
        else:
            persons.append(part)
            
    main_person = persons[0] if persons else (parts[0] if parts else "Unspecified Political Figure")
    other_persons = persons[1:] if len(persons) > 1 else []
    
    return {
        "main_person": main_person,
        "other_persons": other_persons,
        "institutions": institutions
    }

def derive_arrest_subtype(reason: str, context: str, raw_category: str, raw_detained: str) -> str:
    """
    Classifies the event into one of the 7 legal action subtypes based on factual actions.
    Distinguishes arrests from releases/pardons, court martial sentencings, and parliamentary unseatings.
    """
    text = f"{reason} {context} {raw_category} {raw_detained}".lower()
    
    # 1. Pardon or Release
    if any(k in text for k in ["pardon", "presidential pardon", "released", "freedom of prisoner", "bail granted", "discharge"]):
        return "Pardon or Release"
        
    # 2. Parliamentary Action
    if any(k in text for k in ["stripped of parliamentary", "unseated", "parliamentary seat", "privileges committee", "expelled from parliament"]):
        return "Parliamentary Action"
        
    # 3. Sentencing
    if any(k in text for k in ["sentenced", "rigorous imprisonment", "court martial convicts", "court martial sentences", "convicted", "jail term"]):
        return "Sentencing"
        
    # 4. Court Proceedings
    if any(k in text for k in ["contempt of court", "filed charges", "indictment", "court order", "trial begins", "magistrate court hearings", "bail hearing"]):
        return "Court Proceedings"
        
    # 5. Detention or Remand
    if "detained" in text or "remanded" in text or "detention order" in text or "emergency detention" in text:
        return "Detention or Remand"
        
    # 6. Direct Arrest
    if "arrest" in text or "custody" in text or "apprehended" in text:
        return "Arrest"
        
    return "Other Legal Development"

class ArrestProcessor:
    """Processes, validates, enriches, and aligns political arrest & legal events."""

    def __init__(self, calendar: TradingCalendar):
        self.calendar = calendar

    def load_and_process(self, csv_path: Optional[Path] = None) -> pd.DataFrame:
        if csv_path is None:
            csv_path = settings.EVENT_DATASET_DIR / "Political_Arrests.csv"

        logger.info(f"Loading political arrests from {csv_path}")
        df = pd.read_csv(csv_path)

        # Strip whitespace
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", np.nan)

        # Standardize dates
        date_fields = ["Primary_Event_Date", "Arrest_Date", "Released_Date_if_Available", "Next_CSE_Trading_Date"]
        for c in date_fields:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce").dt.strftime("%Y-%m-%d")

        # Parse person and institution entities
        main_persons = []
        other_persons_list = []
        institutions_list = []
        derived_subtypes = []

        for _, row in df.iterrows():
            entities = parse_person_entities(str(row.get("Person_Name", "")))
            main_persons.append(entities["main_person"])
            other_persons_list.append(", ".join(entities["other_persons"]) if entities["other_persons"] else None)
            institutions_list.append(", ".join(entities["institutions"]) if entities["institutions"] else None)

            subtype = derive_arrest_subtype(
                str(row.get("Official_Reason_for_Arrest", "")),
                str(row.get("Political_Context", "")),
                str(row.get("Legal_or_Investigation_Category", "")),
                str(row.get("Detained_or_Remanded", ""))
            )
            derived_subtypes.append(subtype)

        df["Main_Person"] = main_persons
        df["Other_Named_Persons"] = other_persons_list
        df["Institutions_Involved"] = institutions_list
        df["Derived_Arrest_Subtype"] = derived_subtypes
        df["Event_Family"] = "Political Arrest"

        # Align to CSE Trading Calendar
        aligned_dates = []
        alignment_types = []
        lags = []

        for _, row in df.iterrows():
            target_date = row.get("Arrest_Date")
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

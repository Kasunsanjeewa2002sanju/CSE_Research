from typing import Tuple, Dict, Any
import re

POLICY_KEYWORDS = [
    "budget", "tax", "vat", "nsl", "sscl", "imf", "debt restructuring",
    "central bank", "cbsl", "interest rate", "monetary policy", "policy rate",
    "sdfr", "slfr", "rupee", "currency float", "customs duty", "import ban",
    "tariff", "price formula", "subsidy", "privatisation", "privatization",
    "state equity", "treasury", "ministry of finance", "cabinet decision"
]

ARREST_KEYWORDS = [
    "arrest", "arrested", "custody", "detained", "remand", "remanded",
    "sentenced", "imprisonment", "court martial", "convicted", "bail",
    "pardon", "presidential pardon", "cid", "tid", "fcid", "police",
    "attorney general", "supreme court", "high court", "magistrate",
    "warrant", "unseated", "privileges committee", "indictment"
]

class NewsClassifier:
    """
    Transparent, lightweight text classifier for incoming Sri Lankan news articles.
    Classifies content into 'Government Policy', 'Political Arrest', or 'Other News'.
    """
    def classify(self, headline: str, summary: str = "") -> Tuple[str, str, float]:
        """
        Returns (event_family, event_subtype, relevance_score)
        """
        text = f"{headline} {summary}".lower()
        
        policy_matches = sum(1 for kw in POLICY_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", text))
        arrest_matches = sum(1 for kw in ARREST_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", text))
        
        # Check specific arrest patterns
        if arrest_matches > 0 and arrest_matches >= policy_matches:
            if any(k in text for k in ["pardon", "released", "bail"]):
                subtype = "Pardon or Release"
            elif any(k in text for k in ["sentenced", "convicted", "rigorous imprisonment"]):
                subtype = "Sentencing"
            elif any(k in text for k in ["remand", "remanded", "detained"]):
                subtype = "Detention or Remand"
            elif any(k in text for k in ["parliament", "unseated", "expelled"]):
                subtype = "Parliamentary Action"
            else:
                subtype = "Arrest"
                
            relevance = min(1.0, 0.4 + (0.15 * arrest_matches))
            return "Political Arrest", subtype, round(relevance, 2)
            
        elif policy_matches > 0:
            if any(k in text for k in ["imf", "debt restructuring"]):
                subtype = "IMF and Debt Restructuring"
            elif any(k in text for k in ["tax", "vat", "sscl"]):
                subtype = "Tax Changes"
            elif any(k in text for k in ["interest rate", "monetary policy", "policy rate", "srr"]):
                subtype = "Monetary Policy and Interest Rates"
            elif any(k in text for k in ["rupee", "forex", "float"]):
                subtype = "Foreign Exchange Policy"
            elif any(k in text for k in ["budget", "appropriation"]):
                subtype = "Budget Changes"
            elif any(k in text for k in ["privatisation", "privatize", "divestment"]):
                subtype = "Investment and Privatisation"
            elif any(k in text for k in ["tariff", "import ban"]):
                subtype = "Trade and Import Restrictions"
            else:
                subtype = "Budget Changes"
                
            relevance = min(1.0, 0.4 + (0.15 * policy_matches))
            return "Government Policy", subtype, round(relevance, 2)
            
        return "Other News", "General News", 0.10

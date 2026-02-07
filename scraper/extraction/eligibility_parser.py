"""
Eligibility parsing for Public Safety, Law & Justice schemes.

Takes raw eligibility text and converts it into the structured schema
expected by the Public Safety detail scraper.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def _detect_age_range(text: str) -> str:
    for pat, fmt in [
        (r"(\d+)\s*(?:to|-|and)\s*(\d+)\s*years?", lambda m: f"{m.group(1)}-{m.group(2)}"),
        (r"(?:above|over|more than)\s*(\d+)\s*years?", lambda m: f"{m.group(1)}+"),
        (r"(?:below|under|less than)\s*(\d+)\s*years?", lambda m: f"<{m.group(1)}"),
        (r"between\s*(\d+)\s*and\s*(\d+)\s*years?", lambda m: f"{m.group(1)}-{m.group(2)}"),
    ]:
        m = re.search(pat, text, flags=re.I)
        if m:
            return fmt(m)
    return "any"


def _detect_gender(text: str) -> str:
    t = text.lower()
    if re.search(r"\b(women|woman|female|girl|mahila|widow)\b", t):
        return "female"
    if re.search(r"\b(men|male|boy)\b", t):
        return "male"
    return "any"


def _detect_state(text: str) -> str:
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
        "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
        "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
        "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh",
    ]
    for state in states:
        if re.search(rf"\b{re.escape(state)}\b", text, re.I):
            return state
    if re.search(r"all\s+india|nationwide|throughout\s+india|pan[-\s]?india", text, re.I):
        return "All India"
    return "All India"


def _detect_victim_type(text: str) -> str:
    t = text.lower()
    patterns = [
        ("acid attack victims", r"acid\s+attack"),
        ("domestic violence survivors", r"domestic\s+violence|dv\s+act"),
        ("sexual assault / rape survivors", r"rape|sexual\s+assault|pocso"),
        ("crime victims", r"crime\s+victim|victim\s+of\s+crime"),
        ("child abuse victims", r"child\s+abuse|child\s+sexual|pocso"),
        ("trafficking victims", r"traffick"),
        ("road accident victims", r"road\s+accident|motor\s+vehicle\s+act"),
        ("terrorism victims", r"terror|militant"),
    ]
    for label, pat in patterns:
        if re.search(pat, t):
            return label
    return "crime victims"


def _detect_case_type(text: str) -> str:
    t = text.lower()
    if "under trial" in t or "under-trial" in t:
        return "under-trial"
    if "convicted" in t:
        return "convicted"
    if "acquitted" in t:
        return "acquitted"
    if "fir" in t or "first information report" in t:
        return "FIR filed"
    return "any"


def _detect_flags(text: str) -> Dict[str, bool]:
    t = text.lower()
    return {
        "requires_police_report": bool(re.search(r"\bfir\b|first information report|police\s+report", t)),
        "requires_court_order": bool(re.search(r"court\s+order|order\s+of\s+court|judgment", t)),
        "requires_medical_certificate": bool(re.search(r"medical\s+certificate|injury\s+certificate|doctor['’]s\s+certificate", t)),
    }


def _detect_time_limits(text: str) -> List[str]:
    out: List[str] = []
    patterns = [
        r"within\s+\d+\s+(?:days|day|months|month|years|year)\s+of\s+the\s+incident",
        r"within\s+\d+\s+(?:days|day|months|month|years|year)\s+from\s+the\s+date",
        r"not\s+later\s+than\s+\d+\s+(?:days|day|months|month|years|year)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.I):
            out.append(m.group(0))
    return out


def parse_eligibility(raw_text: str) -> Dict[str, Any]:
    """
    Parse raw eligibility section text into structured fields.
    Always returns the full `raw_eligibility_text`.
    """
    text = raw_text or ""
    cleaned = " ".join(text.split())

    age_range = _detect_age_range(cleaned)
    gender = _detect_gender(cleaned)
    state = _detect_state(cleaned)
    victim_type = _detect_victim_type(cleaned)
    case_type = _detect_case_type(cleaned)
    flags = _detect_flags(cleaned)
    time_limits = _detect_time_limits(cleaned)

    other_conditions: List[str] = []
    if "bpl" in cleaned.lower() or "below poverty line" in cleaned.lower():
        other_conditions.append("BPL (Below Poverty Line)")
    if "resident of" in cleaned.lower() or "domicile" in cleaned.lower():
        other_conditions.append("State/district domicile required")

    checklist: List[str] = []
    if flags["requires_police_report"]:
        checklist.append("✓ FIR / police report available")
    if flags["requires_medical_certificate"]:
        checklist.append("✓ Medical certificate available")
    if time_limits:
        checklist.append(f"✓ Application within time limit(s): {', '.join(time_limits)}")

    return {
        "age_range": age_range,
        "gender": gender,
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "any",
        "state": state,
        "district": "",
        "victim_type": victim_type,
        "case_type": case_type,
        "requires_police_report": flags["requires_police_report"],
        "requires_court_order": flags["requires_court_order"],
        "requires_medical_certificate": flags["requires_medical_certificate"],
        "other_conditions": other_conditions,
        "checklist": checklist,
        "raw_eligibility_text": cleaned,
    }


"""
Benefits parsing for Public Safety, Law & Justice schemes.

Extracts structured benefit information, especially compensation amounts.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


AMOUNT_RE = re.compile(r"(₹|Rs\.?|INR)\s*([\d,]+(\.\d+)?)", re.I)


def _extract_amounts(text: str) -> List[str]:
    out: List[str] = []
    for m in AMOUNT_RE.finditer(text):
        amt = m.group(0)
        if amt not in out:
            out.append(amt)
    return out


def _detect_benefit_type(text: str) -> str:
    t = text.lower()
    if "compensation" in t or "victim compensation" in t:
        return "Compensation"
    if "legal aid" in t or "legal assistance" in t or "free lawyer" in t:
        return "Legal Aid"
    if "protection" in t or "shelter home" in t or "rehabilitation" in t:
        return "Protection / Rehabilitation"
    if "insurance" in t:
        return "Insurance"
    return "Other"


def parse_benefits(raw_text: str) -> Dict[str, Any]:
    """
    Parse benefits/assistance section text into structured fields.
    """
    text = raw_text or ""
    cleaned = " ".join(text.split())

    amounts = _extract_amounts(cleaned)
    benefit_type = _detect_benefit_type(cleaned)

    summary = cleaned[:500] if cleaned else ""

    additional_benefits: List[str] = []
    if "counselling" in cleaned.lower() or "counseling" in cleaned.lower():
        additional_benefits.append("Counselling support")
    if "rehabilitation" in cleaned.lower():
        additional_benefits.append("Rehabilitation support")
    if "education" in cleaned.lower():
        additional_benefits.append("Educational support for victim/family")

    frequency = "One-time"
    if "monthly" in cleaned.lower() or "per month" in cleaned.lower():
        frequency = "Monthly"

    financial_benefit = amounts[0] if amounts else ""

    return {
        "summary": summary,
        "financial_benefit": financial_benefit,
        "benefit_type": benefit_type,
        "frequency": frequency,
        "additional_benefits": additional_benefits,
        "raw_benefits_text": cleaned,
    }


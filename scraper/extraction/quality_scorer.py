"""
Quality scoring for Public Safety, Law & Justice scheme extraction.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def score_scheme(s: Dict[str, Any]) -> Tuple[int, List[str]]:
    """
    Compute a quality score (0-100) and a list of missing/weak fields.
    """
    score = 0
    missing: List[str] = []

    # TIER 1 (critical)
    if s.get("scheme_name"):
        score += 10
    else:
        missing.append("scheme_name")

    benefits = s.get("benefits") or {}
    if benefits.get("summary"):
        score += 15
    else:
        missing.append("benefits.summary")

    elig = s.get("eligibility_criteria") or {}
    if elig.get("raw_eligibility_text"):
        score += 15
    else:
        missing.append("eligibility_criteria.raw_eligibility_text")

    docs = s.get("required_documents") or []
    if isinstance(docs, list) and len(docs) >= 2:
        score += 10
    else:
        missing.append("required_documents(>=2)")

    app_process = s.get("application_process") or []
    if isinstance(app_process, list) and len(app_process) >= 3:
        score += 10
    else:
        missing.append("application_process(>=3 steps)")

    # TIER 2
    if s.get("crime_types_covered"):
        score += 10
    else:
        missing.append("crime_types_covered")

    if benefits.get("financial_benefit"):
        score += 10
    else:
        missing.append("benefits.financial_benefit")

    # TIER 3
    if s.get("legal_provisions") or s.get("relevant_acts"):
        score += 5
    else:
        missing.append("legal_provisions/relevant_acts")

    if s.get("contact_details"):
        score += 5
    else:
        missing.append("contact_details")

    score = max(0, min(score, 100))
    return score, missing


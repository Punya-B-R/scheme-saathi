"""
Scheme matching & filtering logic.
"""

from typing import Any, Dict, List, Optional


def filter_schemes(
    schemes: List[Dict[str, Any]],
    category: Optional[str] = None,
    state: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter schemes by category and/or state (eligibility state).
    """
    out = schemes
    if category:
        cat_lower = category.strip().lower()
        out = [s for s in out if (s.get("category") or "").lower() == cat_lower]
    if state:
        state_lower = state.strip().lower()
        out = [
            s
            for s in out
            if _scheme_matches_state(s, state_lower)
        ]
    return out


def _scheme_matches_state(scheme: Dict[str, Any], state: str) -> bool:
    """Check if scheme is applicable to the given state."""
    elig = scheme.get("eligibility_criteria") or {}
    if not isinstance(elig, dict):
        return True
    scheme_state = (elig.get("state") or "").lower()
    if not scheme_state or scheme_state == "all india":
        return True
    return state in scheme_state or scheme_state in state


def to_summary(scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full scheme dict to a short summary for API response."""
    elig = scheme.get("eligibility_criteria") or {}
    if isinstance(elig, dict):
        elig_text = elig.get("raw_eligibility_text") or ""
    else:
        elig_text = str(elig)[:200]
    benefits = scheme.get("benefits") or {}
    if isinstance(benefits, dict):
        benefit_summary = benefits.get("summary") or benefits.get("raw_benefits_text") or ""
    else:
        benefit_summary = str(benefits)[:200]
    return {
        "scheme_id": scheme.get("scheme_id", ""),
        "scheme_name": scheme.get("scheme_name", ""),
        "category": scheme.get("category", ""),
        "brief_description": (scheme.get("brief_description") or "")[:500],
        "eligibility_summary": elig_text[:300] if elig_text else None,
        "benefits_summary": benefit_summary[:300] if benefit_summary else None,
    }

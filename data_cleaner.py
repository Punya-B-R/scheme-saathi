"""
Scheme Saathi - Data cleaning and validation for scraped scheme data.
Validates required fields, removes duplicates, checks URLs, ensures machine-readable eligibility.
"""

import json
import logging
import re
from datetime import date
from typing import Any
from urllib.parse import urlparse

REQUIRED_TOP_LEVEL = [
    "scheme_id",
    "scheme_name",
    "category",
    "brief_description",
    "detailed_description",
    "eligibility_criteria",
    "benefits",
    "required_documents",
    "application_process",
    "application_deadline",
    "official_website",
    "last_updated",
]

REQUIRED_ELIGIBILITY_KEYS = [
    "age_range",
    "gender",
    "caste_category",
    "income_limit",
    "occupation",
    "state",
    "land_ownership",
    "other_conditions",
]

VALID_CATEGORIES = {
    "Agriculture",
    "Education",
    "Healthcare",
    "Senior Citizens",
    "Women & Children",
    "Business & Employment",
}

logger = logging.getLogger(__name__)


def _is_valid_url(url: str) -> bool:
    """Check if string looks like a valid HTTP/HTTPS URL."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    try:
        result = urlparse(url)
        return bool(result.scheme in ("http", "https") and result.netloc)
    except Exception:
        return False


def _normalize_eligibility_value(val: Any) -> Any:
    """Ensure eligibility values are machine-readable (string or list)."""
    if val is None:
        return "any"
    if isinstance(val, list):
        return [str(x).strip() for x in val if x is not None]
    return str(val).strip() if val else "any"


def validate_and_fix_scheme(scheme: dict[str, Any], index: int) -> tuple[dict[str, Any], list[str]]:
    """
    Validate one scheme and fix common issues. Returns (fixed_scheme, list of warning messages).
    """
    warnings: list[str] = []
    fixed = dict(scheme)

    # Required top-level fields
    for key in REQUIRED_TOP_LEVEL:
        if key not in fixed:
            warnings.append(f"Scheme {index}: missing required field '{key}'")
            if key == "eligibility_criteria":
                fixed[key] = {k: "any" for k in REQUIRED_ELIGIBILITY_KEYS}
                fixed[key]["other_conditions"] = []
            elif key in ("required_documents", "application_process", "other_conditions"):
                fixed[key] = []
            elif key == "last_updated":
                fixed[key] = date.today().isoformat()
            else:
                fixed[key] = ""

    # Type fixes
    if not isinstance(fixed.get("required_documents"), list):
        fixed["required_documents"] = list(fixed["required_documents"]) if fixed.get("required_documents") else []
    if not isinstance(fixed.get("application_process"), list):
        fixed["application_process"] = [fixed["application_process"]] if fixed.get("application_process") else []

    # Eligibility criteria: must be dict with required keys
    ec = fixed.get("eligibility_criteria")
    if not isinstance(ec, dict):
        ec = {}
    for k in REQUIRED_ELIGIBILITY_KEYS:
        if k not in ec:
            ec[k] = "any" if k != "other_conditions" else []
        else:
            ec[k] = _normalize_eligibility_value(ec[k])
    fixed["eligibility_criteria"] = ec

    # Category validation
    cat = (fixed.get("category") or "").strip()
    if cat and cat not in VALID_CATEGORIES:
        warnings.append(f"Scheme {index}: category '{cat}' not in standard list; keeping as-is")
    if not cat:
        fixed["category"] = "Other"

    # URL validation
    url = fixed.get("official_website") or ""
    if url and not _is_valid_url(url):
        warnings.append(f"Scheme {index}: invalid official_website '{url}'")
    fixed["official_website"] = url.strip() if isinstance(url, str) else ""

    # scheme_id: alphanumeric and hyphens
    sid = fixed.get("scheme_id") or ""
    if sid and not re.match(r"^[A-Za-z0-9\-_]+$", sid):
        fixed["scheme_id"] = re.sub(r"[^A-Za-z0-9\-_]", "-", sid)
        warnings.append(f"Scheme {index}: scheme_id normalized to '{fixed['scheme_id']}'")

    return fixed, warnings


def remove_duplicates(schemes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Remove schemes with duplicate scheme_id; keep first. Returns (deduplicated list, count removed)."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for s in schemes:
        sid = (s.get("scheme_id") or "").strip()
        if not sid:
            unique.append(s)
            continue
        if sid in seen:
            continue
        seen.add(sid)
        unique.append(s)
    removed = len(schemes) - len(unique)
    if removed:
        logger.info("Removed %d duplicate scheme(s) by scheme_id", removed)
    return unique, removed


def clean_and_validate(schemes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Run full cleaning pipeline: validate each scheme, fix issues, remove duplicates.
    Logs warnings and returns cleaned list.
    """
    all_warnings: list[str] = []
    validated: list[dict[str, Any]] = []
    for i, s in enumerate(schemes):
        fixed, warnings = validate_and_fix_scheme(s, i)
        validated.append(fixed)
        all_warnings.extend(warnings)
    for w in all_warnings:
        logger.warning(w)
    validated, dup_removed = remove_duplicates(validated)
    return validated


def load_and_clean_json(path: str) -> list[dict[str, Any]]:
    """Load JSON from file (expecting {'schemes': [...]} or [...]) and return cleaned schemes list."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "schemes" in data:
        schemes = data["schemes"]
    elif isinstance(data, list):
        schemes = data
    else:
        raise ValueError("JSON must be {'schemes': [...]} or [...]")
    return clean_and_validate(schemes)


def save_schemes_json(schemes: list[dict[str, Any]], path: str) -> None:
    """Save schemes to JSON file in standard format."""
    payload = {"schemes": schemes}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def get_summary_stats(schemes: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate summary statistics: schemes per category, total, etc."""
    by_category: dict[str, int] = {}
    for s in schemes:
        cat = s.get("category") or "Other"
        by_category[cat] = by_category.get(cat, 0) + 1
    return {
        "total_schemes": len(schemes),
        "by_category": by_category,
        "categories": sorted(by_category.keys()),
    }


def search_schemes(
    schemes: list[dict[str, Any]],
    query: str = "",
    category: str = "",
    occupation: str = "",
) -> list[dict[str, Any]]:
    """Search schemes by text query, category, and/or occupation. Returns list of matching schemes."""
    query = (query or "").strip().lower()
    category = (category or "").strip()
    occupation = (occupation or "").strip().lower()
    results: list[dict[str, Any]] = []
    for s in schemes:
        if category and (s.get("category") or "").strip() != category:
            continue
        ec = s.get("eligibility_criteria") or {}
        occ = (ec.get("occupation") or "").strip().lower()
        if occupation and occ != "any" and occupation not in occ:
            continue
        if query:
            text = " ".join(
                [
                    str(s.get("scheme_name", "")),
                    str(s.get("brief_description", "")),
                    str(s.get("category", "")),
                ]
            ).lower()
            if query not in text:
                continue
        results.append(s)
    return results


def update_scheme(
    schemes: list[dict[str, Any]], scheme_id: str, updates: dict[str, Any]
) -> list[dict[str, Any]]:
    """Update a single scheme by scheme_id. Returns new list (or same if not found)."""
    scheme_id = scheme_id.strip()
    out: list[dict[str, Any]] = []
    for s in schemes:
        if (s.get("scheme_id") or "").strip() == scheme_id:
            new_s = {**s, **updates}
            if "eligibility_criteria" in updates and isinstance(updates["eligibility_criteria"], dict):
                ec = {**(s.get("eligibility_criteria") or {}), **updates["eligibility_criteria"]}
                new_s["eligibility_criteria"] = ec
            new_s["last_updated"] = date.today().isoformat()
            out.append(new_s)
        else:
            out.append(s)
    return out

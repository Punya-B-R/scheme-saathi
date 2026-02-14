"""
data_cleaner.py - Clean, validate, and deduplicate government scheme data.

Reads scraped JSON files from data/from_urls/*/ and produces a single,
validated schemes_data.json output with consistent structure.

Usage:
    python -m scraper.data_cleaner          # clean all
    python -m scraper.data_cleaner --stats  # stats only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

# ============================================================
# Config
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "from_urls"
OUTPUT_FILE = ROOT_DIR / "scraper" / "schemes_data.json"
BACKEND_OUTPUT = ROOT_DIR / "backend" / "data_f" / "all_schemes.json"
MIN_QUALITY_SCORE = 25  # floor for inclusion

REQUIRED_FIELDS = ["scheme_id", "scheme_name", "category"]
IMPORTANT_FIELDS = [
    "brief_description",
    "eligibility_criteria",
    "benefits",
    "required_documents",
]

# Canonical category mapping (folder name -> display category)
CATEGORY_MAP = {
    "all_schemes": "Government Schemes",
    "agriculture_rural_environment": "Agriculture",
    "education_learning": "Education",
    "health_wellness": "Healthcare",
    "social_welfare_empowerment": "Social Welfare",
    "women_child": "Women & Children",
    "banking_financial_insurance": "Financial Inclusion",
    "business_entrepreneurship": "Business & Employment",
    "skills_employment": "Skills & Employment",
    "housing_shelter": "Housing",
    "science_it_communications": "Science & IT",
    "transport_infrastructure": "Transport & Infrastructure",
    "travel_tourism": "Travel & Tourism",
    "utility_sanitation": "Utility & Sanitation",
    "sports_culture": "Sports & Culture",
    "public_safety_schemes": "Public Safety",
}

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


# ============================================================
# Loading
# ============================================================


def load_all_scraped_schemes() -> List[Dict[str, Any]]:
    """Walk data/from_urls/*/ and collect every scheme across all categories."""
    all_schemes: List[Dict[str, Any]] = []

    if not DATA_DIR.exists():
        logger.error("Data directory not found: %s", DATA_DIR)
        return all_schemes

    for category_dir in sorted(DATA_DIR.iterdir()):
        if not category_dir.is_dir():
            continue
        scheme_file = None
        for f in category_dir.iterdir():
            if f.name.endswith("_schemes.json") and f.is_file():
                scheme_file = f
                break
        if not scheme_file:
            logger.warning("No schemes file in %s", category_dir.name)
            continue

        try:
            with scheme_file.open(encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as e:
            logger.error("JSON error in %s: %s", scheme_file, e)
            continue

        schemes = data.get("schemes", []) if isinstance(data, dict) else data
        cat_name = CATEGORY_MAP.get(category_dir.name, category_dir.name.replace("_", " ").title())

        for s in schemes:
            if isinstance(s, dict):
                s.setdefault("category", cat_name)
                all_schemes.append(s)

        logger.info("Loaded %d schemes from %s", len(schemes), category_dir.name)

    logger.info("Total raw schemes loaded: %d", len(all_schemes))
    return all_schemes


# ============================================================
# Cleaning functions
# ============================================================


def _clean_text(text: str) -> str:
    """Collapse whitespace, strip."""
    if not text:
        return ""
    return " ".join(text.split()).strip()


def _normalize_eligibility(elig: Any) -> Dict[str, Any]:
    """Ensure eligibility dict has all expected keys with defaults."""
    if not isinstance(elig, dict):
        return {
            "age_range": "any",
            "gender": "any",
            "caste_category": "any",
            "income_limit": "any",
            "occupation": "any",
            "state": "All India",
            "land_ownership": "any",
            "other_conditions": [],
            "raw_eligibility_text": str(elig) if elig else "",
        }

    defaults = {
        "age_range": "any",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "any",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [],
    }
    for k, v in defaults.items():
        elig.setdefault(k, v)
    return elig


def _normalize_benefits(benefits: Any) -> Any:
    """Ensure benefits has at least a summary."""
    if isinstance(benefits, str):
        return {
            "summary": benefits,
            "financial_benefit": "",
            "benefit_type": "Other",
            "frequency": "",
            "additional_benefits": [],
            "raw_benefits_text": benefits,
        }
    if isinstance(benefits, dict):
        benefits.setdefault("summary", "")
        benefits.setdefault("raw_benefits_text", benefits.get("summary", ""))
        return benefits
    return {
        "summary": "",
        "financial_benefit": "",
        "benefit_type": "Other",
        "frequency": "",
        "additional_benefits": [],
        "raw_benefits_text": "",
    }


def _normalize_documents(docs: Any) -> List[Dict[str, Any]]:
    """Ensure documents list is well-structured."""
    if not isinstance(docs, list):
        return []
    result = []
    for d in docs:
        if isinstance(d, str):
            result.append({
                "document_name": d,
                "mandatory": True,
                "specifications": "",
                "notes": "",
                "validity": "",
            })
        elif isinstance(d, dict):
            d.setdefault("document_name", "Unknown")
            d.setdefault("mandatory", True)
            result.append(d)
    return result


def _normalize_application_process(proc: Any) -> List[str]:
    """Ensure application_process is a list of strings."""
    if isinstance(proc, list):
        return [_clean_text(str(step)) for step in proc if step]
    if isinstance(proc, str):
        return [_clean_text(s) for s in proc.split("\n") if s.strip()]
    return []


def _validate_url(url: str) -> bool:
    """Quick check that URL is plausibly valid."""
    if not url:
        return False
    try:
        r = urlparse(url)
        return bool(r.scheme and r.netloc)
    except Exception:
        return False


def clean_scheme(scheme: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Clean a single scheme dict:
    - Normalize text fields
    - Normalize nested structures
    - Add missing defaults
    - Reject garbage entries
    """
    name = _clean_text(scheme.get("scheme_name", ""))
    if not name or len(name) < 5:
        return None

    # Reject obvious garbage
    garbage = ["Sign In", "Something went wrong", "Enter scheme name", "myScheme"]
    if any(g.lower() in name.lower() for g in garbage):
        return None

    cleaned = {
        "scheme_id": scheme.get("scheme_id", ""),
        "scheme_name": name,
        "scheme_name_local": _clean_text(scheme.get("scheme_name_local", "")),
        "category": scheme.get("category", "Uncategorized"),
        "brief_description": _clean_text(scheme.get("brief_description", "")),
        "detailed_description": _clean_text(scheme.get("detailed_description", "")),
        "eligibility_criteria": _normalize_eligibility(scheme.get("eligibility_criteria")),
        "benefits": _normalize_benefits(scheme.get("benefits")),
        "required_documents": _normalize_documents(scheme.get("required_documents")),
        "application_process": _normalize_application_process(scheme.get("application_process")),
        "application_deadline": scheme.get("application_deadline", "Rolling basis"),
        "official_website": scheme.get("source_url", "") or scheme.get("official_website", ""),
        "source_url": scheme.get("source_url", ""),
        "last_updated": scheme.get("last_updated", datetime.now().strftime("%Y-%m-%d")),
        "data_quality_score": scheme.get("data_quality_score", 0),
    }

    # Ensure scheme_id is present
    if not cleaned["scheme_id"]:
        h = hashlib.md5(name.encode()).hexdigest()[:8].upper()
        prefix = cleaned["category"][:3].upper()
        cleaned["scheme_id"] = f"{prefix}-{h}"

    return cleaned


# ============================================================
# Deduplication
# ============================================================


def _fingerprint(scheme: Dict[str, Any]) -> str:
    """Create a fingerprint from scheme name for dedup."""
    name = scheme.get("scheme_name", "").lower()
    name = re.sub(r"[^a-z0-9 ]", "", name)
    name = " ".join(name.split())
    return name


def deduplicate(schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicates, keeping the highest quality version."""
    seen: Dict[str, Dict[str, Any]] = {}
    duplicates = 0

    for s in schemes:
        fp = _fingerprint(s)
        if not fp:
            continue
        existing = seen.get(fp)
        if existing:
            duplicates += 1
            # Keep the one with better quality
            if s.get("data_quality_score", 0) > existing.get("data_quality_score", 0):
                seen[fp] = s
        else:
            seen[fp] = s

    logger.info("Removed %d duplicates -> %d unique schemes", duplicates, len(seen))
    return list(seen.values())


# ============================================================
# Validation
# ============================================================


def validate_scheme(scheme: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a scheme has minimum required fields.
    Returns (is_valid, list_of_issues).
    """
    issues = []

    for field in REQUIRED_FIELDS:
        if not scheme.get(field):
            issues.append(f"missing {field}")

    if not scheme.get("brief_description") and not scheme.get("detailed_description"):
        issues.append("no description")

    benefits = scheme.get("benefits", {})
    if isinstance(benefits, dict) and not benefits.get("summary"):
        issues.append("no benefit summary")

    quality = scheme.get("data_quality_score", 0)
    if quality < MIN_QUALITY_SCORE:
        issues.append(f"low quality score ({quality})")

    return len(issues) == 0, issues


def validate_all(schemes: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """Split schemes into valid and invalid."""
    valid = []
    invalid = []

    for s in schemes:
        ok, issues = validate_scheme(s)
        if ok:
            valid.append(s)
        else:
            invalid.append({"scheme_id": s.get("scheme_id"), "name": s.get("scheme_name"), "issues": issues})

    logger.info("Validation: %d valid, %d invalid", len(valid), len(invalid))
    return valid, invalid


# ============================================================
# Statistics
# ============================================================


def generate_statistics(schemes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics about the cleaned dataset."""
    if not schemes:
        return {"total": 0}

    cat_counter = Counter(s.get("category", "Unknown") for s in schemes)
    state_counter: Counter = Counter()
    quality_scores = []
    has_benefits = 0
    has_docs = 0
    has_process = 0

    for s in schemes:
        elig = s.get("eligibility_criteria", {})
        if isinstance(elig, dict):
            state = elig.get("state", "Unknown")
            state_counter[state] += 1

        quality_scores.append(s.get("data_quality_score", 0))

        benefits = s.get("benefits", {})
        if isinstance(benefits, dict) and benefits.get("summary"):
            has_benefits += 1
        elif isinstance(benefits, str) and benefits:
            has_benefits += 1

        docs = s.get("required_documents", [])
        if isinstance(docs, list) and len(docs) >= 1:
            has_docs += 1

        proc = s.get("application_process", [])
        if isinstance(proc, list) and len(proc) >= 1:
            has_process += 1

    total = len(schemes)
    avg_q = sum(quality_scores) / total if total else 0

    # Quality distribution
    q_dist = {
        "excellent_80_plus": sum(1 for q in quality_scores if q >= 80),
        "good_60_79": sum(1 for q in quality_scores if 60 <= q < 80),
        "fair_40_59": sum(1 for q in quality_scores if 40 <= q < 60),
        "poor_below_40": sum(1 for q in quality_scores if q < 40),
    }

    return {
        "total_schemes": total,
        "schemes_per_category": dict(cat_counter.most_common()),
        "schemes_per_state": dict(state_counter.most_common(20)),
        "average_quality_score": round(avg_q, 2),
        "quality_distribution": q_dist,
        "completeness": {
            "has_benefits": has_benefits,
            "has_documents": has_docs,
            "has_application_process": has_process,
            "benefits_pct": round(has_benefits / total * 100, 1) if total else 0,
            "documents_pct": round(has_docs / total * 100, 1) if total else 0,
            "process_pct": round(has_process / total * 100, 1) if total else 0,
        },
        "generated_at": datetime.now().isoformat(),
    }


def print_statistics(stats: Dict[str, Any]) -> None:
    """Pretty-print statistics."""
    print("\n" + "=" * 60)
    print("  SCHEME DATA STATISTICS")
    print("=" * 60)
    print(f"  Total schemes: {stats['total_schemes']}")
    print(f"  Average quality: {stats['average_quality_score']}")

    print("\n  Schemes per Category:")
    for cat, count in stats.get("schemes_per_category", {}).items():
        print(f"    {cat}: {count}")

    q = stats.get("quality_distribution", {})
    print("\n  Quality Distribution:")
    print(f"    Excellent (80+): {q.get('excellent_80_plus', 0)}")
    print(f"    Good (60-79):    {q.get('good_60_79', 0)}")
    print(f"    Fair (40-59):    {q.get('fair_40_59', 0)}")
    print(f"    Poor (<40):      {q.get('poor_below_40', 0)}")

    c = stats.get("completeness", {})
    print("\n  Data Completeness:")
    print(f"    With benefits:    {c.get('benefits_pct', 0)}%")
    print(f"    With documents:   {c.get('documents_pct', 0)}%")
    print(f"    With app process: {c.get('process_pct', 0)}%")

    print("\n  Top States:")
    for state, count in list(stats.get("schemes_per_state", {}).items())[:10]:
        print(f"    {state}: {count}")
    print("=" * 60)


# ============================================================
# Search (test data quality)
# ============================================================


def search_schemes(
    schemes: List[Dict[str, Any]],
    query: str,
    category: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Simple keyword search to test data quality."""
    q = query.lower()
    results = []

    for s in schemes:
        if category and s.get("category", "").lower() != category.lower():
            continue
        if state:
            elig = s.get("eligibility_criteria", {})
            s_state = elig.get("state", "") if isinstance(elig, dict) else ""
            if state.lower() not in s_state.lower() and s_state != "All India":
                continue

        # Score based on text match
        score = 0
        name = (s.get("scheme_name") or "").lower()
        desc = (s.get("brief_description") or "").lower()
        detailed = (s.get("detailed_description") or "").lower()

        if q in name:
            score += 10
        if q in desc:
            score += 5
        if q in detailed:
            score += 3

        if score > 0:
            results.append((score, s))

    results.sort(key=lambda x: (-x[0], -x[1].get("data_quality_score", 0)))
    return [r[1] for r in results[:limit]]


# ============================================================
# Update specific scheme
# ============================================================


def update_scheme(
    schemes: List[Dict[str, Any]],
    scheme_id: str,
    updates: Dict[str, Any],
) -> bool:
    """Update a specific scheme by scheme_id. Returns True if found."""
    for s in schemes:
        if s.get("scheme_id") == scheme_id:
            s.update(updates)
            s["last_updated"] = datetime.now().strftime("%Y-%m-%d")
            logger.info("Updated scheme: %s", scheme_id)
            return True
    logger.warning("Scheme not found: %s", scheme_id)
    return False


# ============================================================
# Output
# ============================================================


def save_output(
    schemes: List[Dict[str, Any]],
    stats: Dict[str, Any],
    output_path: Path = OUTPUT_FILE,
) -> None:
    """Save cleaned schemes and statistics to schemes_data.json only.

    Does NOT overwrite backend/data_f/all_schemes.json (that is the source of truth).
    """
    output = {
        "metadata": {
            "total_schemes": len(schemes),
            "generated_at": datetime.now().isoformat(),
            "source": "backend/data_f/all_schemes.json",
            "quality_threshold": MIN_QUALITY_SCORE,
        },
        "statistics": stats,
        "schemes": schemes,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d schemes to %s", len(schemes), output_path)


# ============================================================
# Pipeline
# ============================================================


def run_pipeline(stats_only: bool = False) -> None:
    """Full cleaning pipeline using only backend/data_f/all_schemes.json."""
    # 1. Load from backend data (single source of truth)
    logger.info("Loading from %s", BACKEND_OUTPUT)
    if not BACKEND_OUTPUT.exists():
        logger.error("Backend data not found: %s", BACKEND_OUTPUT)
        sys.exit(1)

    with BACKEND_OUTPUT.open(encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, dict):
        raw = data.get("schemes", [])
    elif isinstance(data, list):
        raw = data
    else:
        raw = []

    if not raw:
        logger.error("No schemes found in %s", BACKEND_OUTPUT)
        sys.exit(1)

    logger.info("Loaded %d schemes from backend data", len(raw))

    # 2. Clean
    logger.info("Cleaning %d raw schemes...", len(raw))
    cleaned = []
    for s in raw:
        c = clean_scheme(s)
        if c:
            cleaned.append(c)
    logger.info("After cleaning: %d schemes", len(cleaned))

    # 3. Deduplicate
    unique = deduplicate(cleaned)

    # 4. Validate
    valid, invalid = validate_all(unique)
    if invalid:
        logger.warning("First 5 invalid schemes:")
        for inv in invalid[:5]:
            logger.warning("  %s: %s", inv["name"], ", ".join(inv["issues"]))

    # 5. Statistics
    stats = generate_statistics(valid)
    print_statistics(stats)

    if stats_only:
        return

    # 6. Sort by quality
    valid.sort(key=lambda s: -s.get("data_quality_score", 0))

    # 7. Save to schemes_data.json only (do NOT overwrite backend source)
    save_output(valid, stats)

    print(f"\n[DONE] {len(valid)} schemes saved to {OUTPUT_FILE}")
    print(f"[SOURCE] {BACKEND_OUTPUT} (untouched)")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and validate scheme data")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    args = parser.parse_args()
    run_pipeline(stats_only=args.stats)

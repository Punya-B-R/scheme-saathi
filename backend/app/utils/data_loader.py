"""
Load schemes from all_schemes.json.
Handles both single JSON object and concatenated multiple JSON objects (e.g. one per category).
Resilient to one or more malformed blocks: skips bad blocks and merges the rest.
Provides validation, embedding-text preparation, and statistics.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

# Backend root is parent of app/
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
logger = logging.getLogger(__name__)


def _split_top_level_objects(content: str) -> List[str]:
    r"""
    Split content into top-level JSON objects by boundary '}\s*{'.
    Each segment is then wrapped to form a valid single object (add missing } or {).
    """
    # Boundary: closing brace of one object, optional whitespace, opening brace of next
    parts = re.split(r"\}\s*\{", content.strip())
    if not parts:
        return []
    segments = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        if i == 0:
            if not part.endswith("}"):
                part = part + "}"
        else:
            part = "{" + part
            if not part.endswith("}"):
                part = part + "}"
        segments.append(part)
    return segments


def _parse_concatenated_json(content: str) -> List[Dict[str, Any]]:
    """
    Parse multiple concatenated JSON objects. Uses boundary split so one bad
    object doesn't break the rest. Skips and logs any segment that fails to parse.
    """
    segments = _split_top_level_objects(content)
    objects = []
    for i, segment in enumerate(segments):
        try:
            obj = json.loads(segment)
            if isinstance(obj, dict):
                objects.append(obj)
        except json.JSONDecodeError as e:
            logger.warning(
                "Skipping malformed JSON block %s (char ~%s): %s",
                i + 1,
                getattr(e, "pos", "?"),
                e,
            )
    return objects


def load_schemes_json(data_path: Path) -> Dict[str, Any]:
    """
    Load and parse the schemes JSON file.
    Supports single object or multiple concatenated {"metadata":..., "schemes": [...]} objects.
    Returns a single dict with merged 'metadata' and 'schemes'.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Schemes data not found: {data_path}")
    with data_path.open(encoding="utf-8") as f:
        content = f.read()
    # Try single-object parse first (fast path)
    try:
        single = json.loads(content)
        if isinstance(single, dict) and ("schemes" in single or "metadata" in single):
            return single
    except json.JSONDecodeError as e:
        if "Extra data" not in str(e):
            raise
        # File has multiple concatenated JSON objects
        pass
    # Multiple concatenated JSON objects
    objects = _parse_concatenated_json(content)
    if not objects:
        return {"metadata": {}, "schemes": []}
    all_schemes: List[Dict[str, Any]] = []
    all_metadata: List[Dict[str, Any]] = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if "schemes" in obj and isinstance(obj["schemes"], list):
            all_schemes.extend(obj["schemes"])
        if "metadata" in obj and isinstance(obj["metadata"], dict):
            all_metadata.append(obj["metadata"])
    # Merge metadata (e.g. sum totals, keep first scraping_date)
    merged_meta: Dict[str, Any] = {}
    if all_metadata:
        merged_meta = all_metadata[0].copy()
        total_schemes = sum(m.get("total_schemes", 0) for m in all_metadata)
        merged_meta["total_schemes"] = total_schemes
        merged_meta["sources_merged"] = len(objects)
    return {"metadata": merged_meta, "schemes": all_schemes}


def get_schemes_list(data_path: Path) -> List[Dict[str, Any]]:
    """Return the list of scheme objects from the JSON file."""
    data = load_schemes_json(data_path)
    schemes = data.get("schemes", [])
    if not isinstance(schemes, list):
        return []
    return schemes


def get_metadata(data_path: Path) -> Dict[str, Any]:
    """Return metadata from the schemes file."""
    data = load_schemes_json(data_path)
    return data.get("metadata", {})


def load_schemes_from_json(filepath: str) -> List[Dict]:
    """
    Load all schemes from the consolidated JSON file.
    Supports concatenated JSON; filters out schemes with data_quality_score < 30.

    Args:
        filepath: Path to all_schemes.json (str or path-like)

    Returns:
        List of scheme dictionaries
    """
    try:
        path = Path(filepath)

        if not path.exists():
            logger.error("Schemes file not found: %s", filepath)
            return []

        # Use shared loader (handles single or concatenated JSON)
        data = load_schemes_json(path)
        schemes = data.get("schemes", [])

        if not schemes:
            logger.warning("No schemes found in JSON file")
            return []

        logger.info("Loaded %s schemes from %s", len(schemes), filepath)

        metadata = data.get("metadata", {})
        if metadata:
            logger.info("  Total schemes: %s", metadata.get("total_schemes", "unknown"))

        # Filter out very low quality schemes
        valid_schemes = [s for s in schemes if s.get("data_quality_score", 0) >= 30]

        if len(valid_schemes) < len(schemes):
            logger.warning(
                "Filtered out %s low-quality schemes (quality < 30)",
                len(schemes) - len(valid_schemes),
            )

        return valid_schemes

    except FileNotFoundError:
        logger.error("Schemes file not found: %s", filepath)
        return []
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", filepath, e)
        return []
    except Exception as e:
        logger.error("Error loading schemes: %s", e)
        return []


def prepare_scheme_text_for_embedding(scheme: Dict) -> str:
    """
    Create a rich text representation of scheme for vector embedding.

    Combines all relevant searchable information into a single text
    that will be converted to a vector for semantic search.

    Args:
        scheme: Scheme dictionary

    Returns:
        Combined text for embedding
    """
    text_parts = []

    # Scheme name (high importance)
    name = scheme.get("scheme_name", "")
    if name and name != "Scheme name not clearly specified":
        text_parts.append(f"Scheme: {name}")

    # Category
    category = scheme.get("category", "")
    if category:
        text_parts.append(f"Category: {category}")

    # Descriptions
    brief_desc = scheme.get("brief_description", "")
    if brief_desc and len(brief_desc) > 50:
        text_parts.append(f"Description: {brief_desc}")

    detailed_desc = scheme.get("detailed_description", "")
    if detailed_desc and len(detailed_desc) > len(brief_desc):
        text_parts.append(f"Details: {detailed_desc}")

    # Benefits (very important for matching)
    benefits = scheme.get("benefits", {})
    if isinstance(benefits, dict):
        benefit_summary = benefits.get("summary", "")
        if benefit_summary:
            text_parts.append(f"Benefits: {benefit_summary}")
        financial = benefits.get("financial_benefit", "")
        if financial:
            text_parts.append(f"Financial Benefit: {financial}")

    # Eligibility (critical for matching)
    eligibility = scheme.get("eligibility_criteria", {})
    if isinstance(eligibility, dict):
        raw_elig = eligibility.get("raw_eligibility_text", "")
        if raw_elig and raw_elig not in (
            "Check Eligibility",
            "Eligibility criteria not clearly specified",
        ):
            text_parts.append(f"Eligibility: {raw_elig}")
        for field in ["occupation", "state", "caste_category", "income_limit", "age_range"]:
            value = eligibility.get(field, "")
            if value and value not in ("any", "unknown", ""):
                text_parts.append(f"{field.replace('_', ' ').title()}: {value}")

    # Target beneficiaries
    target = scheme.get("target_beneficiaries", "")
    if target:
        text_parts.append(f"For: {target}")

    # Scheme type and ministry
    scheme_type = scheme.get("scheme_type", "")
    if scheme_type:
        text_parts.append(f"Type: {scheme_type}")

    ministry = scheme.get("ministry_department", "")
    if ministry and "Ministry of Electronics" not in ministry:
        text_parts.append(f"Ministry: {ministry}")

    geo_coverage = scheme.get("geographical_coverage", "")
    if geo_coverage and geo_coverage != "All India":
        text_parts.append(f"Coverage: {geo_coverage}")

    combined_text = " | ".join(filter(None, text_parts))
    return combined_text


def validate_scheme(scheme: Dict) -> bool:
    """
    Validate that a scheme has minimum required fields and useful content.

    Args:
        scheme: Scheme dictionary

    Returns:
        True if valid, False otherwise
    """
    required = ["scheme_id", "scheme_name", "category"]
    for field in required:
        if field not in scheme or not scheme[field]:
            logger.warning("Scheme missing required field: %s", field)
            return False

    benefits = scheme.get("benefits") or {}
    eligibility = scheme.get("eligibility_criteria") or {}
    has_benefits = bool(benefits.get("summary") if isinstance(benefits, dict) else False)
    has_eligibility = bool(
        eligibility.get("raw_eligibility_text") if isinstance(eligibility, dict) else False
    )
    has_description = bool(scheme.get("brief_description"))

    if not (has_benefits or has_eligibility or has_description):
        logger.warning(
            "Scheme %s has no useful content (no benefits, eligibility, or description)",
            scheme.get("scheme_id"),
        )
        return False

    return True


def get_scheme_statistics(schemes: List[Dict]) -> Dict:
    """
    Generate statistics about loaded schemes.

    Args:
        schemes: List of scheme dictionaries

    Returns:
        Dictionary with statistics
    """
    if not schemes:
        return {
            "total": 0,
            "categories": {},
            "states": {},
            "avg_quality": 0,
            "quality_distribution": {
                "high (70-100)": 0,
                "medium (50-69)": 0,
                "low (30-49)": 0,
            },
        }

    categories: Dict[str, int] = {}
    for scheme in schemes:
        cat = scheme.get("category", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1

    states: Dict[str, int] = {}
    for scheme in schemes:
        elig = scheme.get("eligibility_criteria") or {}
        state = elig.get("state", "All India") if isinstance(elig, dict) else "All India"
        states[state] = states.get(state, 0) + 1

    quality_scores = [s.get("data_quality_score", 0) for s in schemes]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    return {
        "total": len(schemes),
        "categories": categories,
        "states": states,
        "avg_quality": round(avg_quality, 2),
        "quality_distribution": {
            "high (70-100)": sum(1 for q in quality_scores if q >= 70),
            "medium (50-69)": sum(1 for q in quality_scores if 50 <= q < 70),
            "low (30-49)": sum(1 for q in quality_scores if 30 <= q < 50),
        },
    }


# ---------------------------------------------------------------------------
# Built-in test (run: python app/utils/data_loader.py from backend/)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Relative to backend cwd when run as python app/utils/data_loader.py
    test_path = BACKEND_ROOT / "data_f" / "all_schemes.json"
    if not test_path.exists():
        test_path = Path("data_f/all_schemes.json")

    schemes = load_schemes_from_json(str(test_path))

    print(f"\n{'='*60}")
    print("DATA LOADER TEST")
    print(f"{'='*60}\n")

    if schemes:
        print(f"[OK] Successfully loaded {len(schemes)} schemes\n")

        stats = get_scheme_statistics(schemes)
        print("Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Average Quality: {stats['avg_quality']}/100")
        print("\nCategories:")
        for cat, count in list(stats["categories"].items())[:10]:
            print(f"  - {cat}: {count}")
        if len(stats["categories"]) > 10:
            print(f"  ... and {len(stats['categories']) - 10} more")

        print("\nQuality Distribution:")
        for level, count in stats["quality_distribution"].items():
            print(f"  - {level}: {count}")

        print(f"\n{'='*60}")
        print("EMBEDDING TEXT TEST")
        print(f"{'='*60}\n")

        sample_scheme = schemes[0]
        embedding_text = prepare_scheme_text_for_embedding(sample_scheme)
        print(f"Sample Scheme: {sample_scheme.get('scheme_name')}")
        print(f"\nEmbedding text (first 500 chars):")
        print(f"{embedding_text[:500]}...")
        print(f"\nTotal length: {len(embedding_text)} characters")

        print(f"\n{'='*60}")
        print("VALIDATION TEST")
        print(f"{'='*60}\n")

        valid_count = sum(1 for s in schemes if validate_scheme(s))
        print(f"Valid schemes: {valid_count}/{len(schemes)}")

    else:
        print("[FAIL] Failed to load schemes")

    print(f"\n{'='*60}")
    print("Data loader test complete!")
    print(f"{'='*60}\n")

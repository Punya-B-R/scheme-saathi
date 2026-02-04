"""
Merge scraped scheme data (agriculture_schemes_data.json, etc.) into main Scheme Saathi
schemes_data.json. Deduplicates by scheme_id, runs validation, and backs up the existing file.
"""

import json
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

MAIN_SCHEMES_PATH = "schemes_data.json"
BACKUP_PATH = "schemes_data_backup.json"
SCRAPED_SOURCES = [
    "agriculture_schemes_data.json",
    "all_schemes_data.json",  # if you ran detail scraper on all_scheme_urls.json
]


def load_schemes(path: str) -> list[dict]:
    """Load list of schemes from a JSON file (main format: {schemes: [...]} or scraped: {schemes: [...]})."""
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "schemes" in data:
        return data["schemes"]
    if isinstance(data, list):
        return data
    return []


def _clean_description(text: str, fallback: str) -> str:
    """Use fallback if text looks like scraped UI boilerplate."""
    if not text or not isinstance(text, str):
        return fallback or ""
    t = text.strip()
    if "Are you sure you want to sign out" in t or "Enter scheme name to search" in t:
        return fallback or ""
    return t


def scraped_to_main_schema(s: dict) -> dict:
    """
    Map a scraped scheme (agriculture_detail_scraper / all_schemes_data) to Scheme Saathi main schema.
    Keeps required fields; drops or keeps extra fields (source_url, data_quality_score kept for reference).
    """
    ec = s.get("eligibility_criteria") or {}
    # Ensure eligibility has only the keys expected by data_cleaner (other_conditions list)
    eligibility = {
        "age_range": ec.get("age_range", "any"),
        "gender": ec.get("gender", "any"),
        "caste_category": ec.get("caste_category", "any"),
        "income_limit": ec.get("income_limit", "any"),
        "occupation": ec.get("occupation", "any"),
        "state": ec.get("state", "All India"),
        "land_ownership": ec.get("land_ownership", "any"),
        "other_conditions": ec.get("other_conditions") if isinstance(ec.get("other_conditions"), list) else [],
    }
    cat = (s.get("category") or "Agriculture").strip()
    if cat == "Agriculture, Rural & Environment":
        cat = "Agriculture"
    brief = (s.get("brief_description") or "").strip()
    out = {
        "scheme_id": s.get("scheme_id", ""),
        "scheme_name": s.get("scheme_name", ""),
        "category": cat,
        "brief_description": brief or "",
        "detailed_description": _clean_description(s.get("detailed_description", ""), brief),
        "eligibility_criteria": eligibility,
        "benefits": s.get("benefits", "") or "",
        "required_documents": s.get("required_documents") if isinstance(s.get("required_documents"), list) else [],
        "application_process": s.get("application_process") if isinstance(s.get("application_process"), list) else [],
        "application_deadline": s.get("application_deadline", "Rolling") or "Rolling",
        "official_website": s.get("official_website", "") or "",
        "last_updated": s.get("last_updated", ""),
    }
    # Optional: keep source_url and data_quality_score for debugging/analytics
    if s.get("source_url"):
        out["source_url"] = s["source_url"]
    if "data_quality_score" in s:
        out["data_quality_score"] = s["data_quality_score"]
    return out


def merge_and_dedupe(main_list: list[dict], scraped_list: list[dict], dedupe_key: str = "scheme_id") -> list[dict]:
    """Merge scraped into main; deduplicate by dedupe_key (keep first occurrence)."""
    seen = {s.get(dedupe_key): i for i, s in enumerate(main_list) if s.get(dedupe_key)}
    out = list(main_list)
    for s in scraped_list:
        kid = s.get(dedupe_key)
        if kid and kid not in seen:
            seen[kid] = len(out)
            out.append(s)
    return out


def main() -> None:
    # 1) Load main Scheme Saathi schemes
    main_schemes = load_schemes(MAIN_SCHEMES_PATH)
    logger.info("Loaded %s schemes from %s", len(main_schemes), MAIN_SCHEMES_PATH)

    merged = list(main_schemes)

    # 2) Load each scraped source and merge (map to main schema, then dedupe)
    for path in SCRAPED_SOURCES:
        raw = load_schemes(path)
        if not raw:
            continue
        mapped = [scraped_to_main_schema(s) for s in raw]
        before = len(merged)
        merged = merge_and_dedupe(merged, mapped)
        added = len(merged) - before
        logger.info("Merged %s schemes from %s (added %s new)", len(mapped), path, added)

    # 3) Validate and clean (data_cleaner)
    try:
        from data_cleaner import clean_and_validate

        merged = clean_and_validate(merged)
        logger.info("Cleaned and validated: %s schemes", len(merged))
    except Exception as e:
        logger.warning("Validation step failed: %s. Saving unvalidated merge.", e)

    # 4) Backup existing main file
    if os.path.isfile(MAIN_SCHEMES_PATH):
        with open(MAIN_SCHEMES_PATH, "r", encoding="utf-8") as f:
            backup_content = f.read()
        with open(BACKUP_PATH, "w", encoding="utf-8") as f:
            f.write(backup_content)
        logger.info("Backed up %s to %s", MAIN_SCHEMES_PATH, BACKUP_PATH)

    # 5) Write merged result to main file
    output = {"schemes": merged}
    with open(MAIN_SCHEMES_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s schemes to %s", len(merged), MAIN_SCHEMES_PATH)

    # 6) Summary
    from data_cleaner import get_summary_stats

    stats = get_summary_stats(merged)
    logger.info("Summary: %s", json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

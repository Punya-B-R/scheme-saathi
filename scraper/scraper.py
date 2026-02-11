"""
scraper.py - Main scraping logic for MyScheme.gov.in government schemes.

Combines three data sources:
1. Web scraping (Selenium + BeautifulSoup for JS-rendered pages)
2. Existing scraped data files (data/from_urls/*)
3. Manual fallback data (manual_data.py)

Usage:
    python -m scraper.scraper                           # full pipeline
    python -m scraper.scraper --mode manual              # manual data only
    python -m scraper.scraper --mode existing             # existing + manual
    python -m scraper.scraper --mode scrape --limit 10   # scrape 10 schemes from web
    python -m scraper.scraper --stats                    # statistics only
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ============================================================
# Config
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "from_urls"
OUTPUT_FILE = ROOT_DIR / "scraper" / "schemes_data.json"
BACKEND_OUTPUT = ROOT_DIR / "backend" / "data_f" / "all_schemes.json"
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

MYSCHEME_BASE = "https://www.myscheme.gov.in"
MYSCHEME_API = "https://www.myscheme.gov.in/api"

# Rate limiting
REQUEST_DELAY = 2.0  # seconds between requests
MAX_RETRIES = 3
TIMEOUT = 30  # seconds

# User agent
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Target scheme URLs for the top 50-100 schemes
TARGET_SCHEME_SLUGS = [
    # Agriculture
    "pm-kisan",
    "pmfby",
    "kcc",
    "soil-health-card",
    "enam",
    "pm-kisan-maandhan",
    "pkvy",
    "nmsa",
    "rkvy",
    # Education
    "post-matric-scholarship-sc",
    "post-matric-scholarship-obc",
    "central-sector-scholarship",
    "pm-scholarship-scheme",
    "national-means-cum-merit-scholarship",
    "begum-hazrat-mahal-national-scholarship",
    "pre-matric-scholarship-sc",
    "pre-matric-scholarship-obc",
    "pm-vidyalaxmi",
    "pm-usp",
    # Healthcare
    "ab-pmjay",
    "pmmvy",
    "jsy",
    "pmsby",
    "national-health-mission",
    "ayushman-bharat-health-account",
    # Senior Citizens
    "ignoaps",
    "apy",
    "pmvvy",
    "national-pension-scheme",
    "igndps",
    # Women & Children
    "ssy",
    "bbbp",
    "one-stop-centre",
    "ujjwala",
    "pm-ujjwala-yojana",
    "mahila-shakti-kendra",
    # Business & Employment
    "pmmy",
    "pmegp",
    "standup-india",
    "pm-svanidhi",
    "startup-india-seed-fund",
    "pm-vishwakarma",
    # Housing
    "pmay-urban",
    "pmay-gramin",
    # Financial Inclusion
    "pmjdy",
    "pmjjby",
    # Skills
    "pmkvy",
    "ddugky",
    "naps",
    # Others
    "pm-gram-sadak-yojana",
    "swachh-bharat-mission",
]

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================
# HTTP Session with retry
# ============================================================


def _create_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    session.headers.update(HEADERS)

    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _rate_limited_get(session: requests.Session, url: str) -> Optional[requests.Response]:
    """GET with rate limiting and error handling."""
    try:
        time.sleep(REQUEST_DELAY)
        resp = session.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        logger.error("Request failed for %s: %s", url, e)
        return None


# ============================================================
# BeautifulSoup extraction helpers
# ============================================================


def _extract_text(soup: BeautifulSoup, selector: str, default: str = "") -> str:
    """Extract cleaned text from a CSS selector."""
    tag = soup.select_one(selector)
    if tag:
        return " ".join(tag.get_text(separator=" ").split()).strip()
    return default


def _extract_list(soup: BeautifulSoup, selector: str) -> List[str]:
    """Extract list items from a selector."""
    items = soup.select(selector)
    return [" ".join(item.get_text(separator=" ").split()).strip() for item in items if item.get_text(strip=True)]


def _extract_scheme_name(soup: BeautifulSoup) -> str:
    """Extract scheme name from page."""
    # Try multiple selectors
    for sel in ["h1.scheme-title", "h1", ".scheme-name", "h2.scheme-title"]:
        name = _extract_text(soup, sel)
        if name and len(name) > 5 and "Sign In" not in name and "myScheme" not in name:
            return name
    return ""


def _extract_description(soup: BeautifulSoup) -> str:
    """Extract scheme description."""
    for sel in [".scheme-description", ".scheme-details p", ".details-section p", "article p"]:
        text = _extract_text(soup, sel)
        if text and len(text) > 30:
            return text
    return ""


def _extract_eligibility_text(soup: BeautifulSoup) -> str:
    """Extract eligibility section text."""
    # Look for eligibility section
    for header in soup.find_all(["h2", "h3", "h4"]):
        if "eligib" in header.get_text(strip=True).lower():
            sibling = header.find_next_sibling()
            texts = []
            while sibling and sibling.name not in ["h2", "h3", "h4"]:
                texts.append(sibling.get_text(separator=" ").strip())
                sibling = sibling.find_next_sibling()
            return " ".join(texts)
    return ""


def _extract_benefits_text(soup: BeautifulSoup) -> str:
    """Extract benefits section text."""
    for header in soup.find_all(["h2", "h3", "h4"]):
        if "benefit" in header.get_text(strip=True).lower():
            sibling = header.find_next_sibling()
            texts = []
            while sibling and sibling.name not in ["h2", "h3", "h4"]:
                texts.append(sibling.get_text(separator=" ").strip())
                sibling = sibling.find_next_sibling()
            return " ".join(texts)
    return ""


def _extract_documents_list(soup: BeautifulSoup) -> List[str]:
    """Extract required documents list."""
    for header in soup.find_all(["h2", "h3", "h4"]):
        if "document" in header.get_text(strip=True).lower():
            # Look for list items after this header
            sibling = header.find_next_sibling()
            docs = []
            while sibling and sibling.name not in ["h2", "h3", "h4"]:
                if sibling.name in ["ul", "ol"]:
                    for li in sibling.find_all("li"):
                        t = li.get_text(strip=True)
                        if t:
                            docs.append(t)
                sibling = sibling.find_next_sibling()
            if docs:
                return docs
    return []


def _extract_application_steps(soup: BeautifulSoup) -> List[str]:
    """Extract application process steps."""
    for header in soup.find_all(["h2", "h3", "h4"]):
        text = header.get_text(strip=True).lower()
        if "application" in text or "how to apply" in text or "process" in text:
            sibling = header.find_next_sibling()
            steps = []
            while sibling and sibling.name not in ["h2", "h3", "h4"]:
                if sibling.name in ["ul", "ol"]:
                    for li in sibling.find_all("li"):
                        t = li.get_text(strip=True)
                        if t:
                            steps.append(t)
                elif sibling.name == "p":
                    t = sibling.get_text(strip=True)
                    if t:
                        steps.append(t)
                sibling = sibling.find_next_sibling()
            if steps:
                return steps
    return []


# ============================================================
# Eligibility parsing (lightweight version)
# ============================================================


def _parse_age(text: str) -> str:
    t = text.lower()
    for pat, fmt in [
        (r"(\d+)\s*(?:to|-|and)\s*(\d+)\s*years?", lambda m: f"{m.group(1)}-{m.group(2)}"),
        (r"(?:above|over|more than)\s*(\d+)\s*years?", lambda m: f"{m.group(1)}+"),
        (r"(?:below|under|less than)\s*(\d+)\s*years?", lambda m: f"<{m.group(1)}"),
    ]:
        m = re.search(pat, t, re.I)
        if m:
            return fmt(m)
    return "any"


def _parse_gender(text: str) -> str:
    t = text.lower()
    if re.search(r"\b(women|woman|female|girl|widow|mahila)\b", t):
        return "female"
    if re.search(r"\b(men only|male only|boy only)\b", t):
        return "male"
    return "any"


def _parse_state(text: str) -> str:
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
    return "All India"


def _parse_caste(text: str) -> str:
    t = text.lower()
    if "scheduled caste" in t or "sc student" in t or "sc category" in t:
        return "SC"
    if "scheduled tribe" in t or "st student" in t:
        return "ST"
    if "sc/st" in t or "sc & st" in t:
        return "SC/ST"
    if "obc" in t or "other backward" in t:
        return "OBC"
    if "minority" in t:
        return "Minority"
    return "any"


def _parse_income(text: str) -> str:
    # Look for income limits
    m = re.search(r"(?:income|earning).{0,40}(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac)?", text, re.I)
    if m:
        return f"< Rs {m.group(0).strip()}"
    m = re.search(r"(?:BPL|below poverty)", text, re.I)
    if m:
        return "BPL"
    return "any"


def _build_eligibility(raw_text: str) -> Dict[str, Any]:
    """Parse raw eligibility text into structured format."""
    return {
        "age_range": _parse_age(raw_text),
        "gender": _parse_gender(raw_text),
        "caste_category": _parse_caste(raw_text),
        "income_limit": _parse_income(raw_text),
        "occupation": "any",
        "state": _parse_state(raw_text),
        "land_ownership": "any",
        "other_conditions": [],
        "raw_eligibility_text": raw_text[:1000],
    }


def _build_benefits(raw_text: str) -> Dict[str, Any]:
    """Parse raw benefits text into structured format."""
    amounts = re.findall(r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakh|crore))?", raw_text, re.I)
    return {
        "summary": raw_text[:500],
        "financial_benefit": amounts[0] if amounts else "",
        "benefit_type": "Other",
        "frequency": "",
        "additional_benefits": [],
        "raw_benefits_text": raw_text[:1000],
    }


def _build_documents(doc_list: List[str]) -> List[Dict[str, Any]]:
    """Convert document names to structured format."""
    return [
        {
            "document_name": d,
            "mandatory": True,
            "specifications": "",
            "notes": "",
            "validity": "",
        }
        for d in doc_list
    ]


# ============================================================
# Scheme scraping from MyScheme.gov.in
# ============================================================


def scrape_scheme_page(session: requests.Session, slug: str) -> Optional[Dict[str, Any]]:
    """
    Scrape a single scheme page from MyScheme.gov.in.

    Note: MyScheme pages are heavily JS-rendered, so this works for
    pages that have server-side content. For full rendering, use
    Selenium-based scrapers in the scraper/ directory.
    """
    url = f"{MYSCHEME_BASE}/schemes/{slug}"
    logger.info("Scraping: %s", url)

    resp = _rate_limited_get(session, url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Extract fields
    name = _extract_scheme_name(soup)
    if not name:
        logger.warning("Could not extract scheme name from %s", url)
        return None

    description = _extract_description(soup)
    eligibility_text = _extract_eligibility_text(soup)
    benefits_text = _extract_benefits_text(soup)
    documents = _extract_documents_list(soup)
    application_steps = _extract_application_steps(soup)

    # Generate scheme ID from slug
    prefix = slug[:4].upper().replace("-", "")
    scheme_id = f"{prefix}-{slug.replace('-', '').upper()[:8]}"

    scheme = {
        "scheme_id": scheme_id,
        "scheme_name": name,
        "scheme_name_local": "",
        "category": "Uncategorized",  # Will be assigned by data_cleaner
        "brief_description": description[:300] if description else "",
        "detailed_description": description,
        "eligibility_criteria": _build_eligibility(eligibility_text) if eligibility_text else {
            "age_range": "any", "gender": "any", "caste_category": "any",
            "income_limit": "any", "occupation": "any", "state": "All India",
            "land_ownership": "any", "other_conditions": [], "raw_eligibility_text": "",
        },
        "benefits": _build_benefits(benefits_text) if benefits_text else {
            "summary": "", "financial_benefit": "", "benefit_type": "Other",
            "frequency": "", "additional_benefits": [], "raw_benefits_text": "",
        },
        "required_documents": _build_documents(documents),
        "application_process": application_steps,
        "application_deadline": "Rolling basis",
        "official_website": url,
        "source_url": url,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "data_quality_score": _score_scheme(name, description, eligibility_text, benefits_text, documents, application_steps),
    }

    logger.info("  -> Extracted: %s (quality: %d)", name[:60], scheme["data_quality_score"])
    return scheme


def _score_scheme(name, desc, elig, benefits, docs, steps) -> int:
    """Quick quality score for scraped scheme."""
    score = 0
    if name and len(name) > 5:
        score += 15
    if desc and len(desc) > 50:
        score += 20
    if elig and len(elig) > 30:
        score += 15
    if benefits and len(benefits) > 20:
        score += 15
    if len(docs) >= 2:
        score += 15
    if len(steps) >= 2:
        score += 10
    if desc and len(desc) > 200:
        score += 10
    return min(score, 100)


def scrape_multiple(slugs: List[str], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Scrape multiple scheme pages."""
    session = _create_session()
    schemes = []
    targets = slugs[:limit] if limit else slugs
    total = len(targets)

    logger.info("Starting scrape of %d schemes from MyScheme.gov.in", total)

    for i, slug in enumerate(targets, 1):
        logger.info("[%d/%d] Processing: %s", i, total, slug)
        try:
            scheme = scrape_scheme_page(session, slug)
            if scheme:
                schemes.append(scheme)
                logger.info("  [OK] %s", scheme["scheme_name"][:50])
            else:
                logger.warning("  [SKIP] No data extracted for %s", slug)
        except Exception as e:
            logger.error("  [FAIL] Error scraping %s: %s", slug, e)

    logger.info("Scraping complete: %d/%d successful", len(schemes), total)
    return schemes


# ============================================================
# Load existing scraped data
# ============================================================


def load_existing_data() -> List[Dict[str, Any]]:
    """Load all previously scraped data from data/from_urls/."""
    from scraper.data_cleaner import load_all_scraped_schemes
    return load_all_scraped_schemes()


# ============================================================
# Full pipeline
# ============================================================


def load_backend_data() -> List[Dict[str, Any]]:
    """Load schemes from backend/data_f/all_schemes.json (single source of truth)."""
    if not BACKEND_OUTPUT.exists():
        logger.error("Backend data not found: %s", BACKEND_OUTPUT)
        return []

    logger.info("Loading from %s", BACKEND_OUTPUT)
    with BACKEND_OUTPUT.open(encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        schemes = data.get("schemes", [])
    elif isinstance(data, list):
        schemes = data
    else:
        schemes = []

    logger.info("Loaded %d schemes from backend data", len(schemes))
    return schemes


def run_full_pipeline(
    mode: str = "backend",
    scrape_limit: Optional[int] = None,
    stats_only: bool = False,
) -> None:
    """
    Run the full scraping + cleaning + output pipeline.

    Modes:
      - 'backend'  : Use only backend/data_f/all_schemes.json (default, recommended)
      - 'scrape'   : Web scrape from MyScheme.gov.in -> schemes_data.json only
    """
    from scraper.data_cleaner import (
        clean_scheme,
        deduplicate,
        generate_statistics,
        print_statistics,
        validate_all,
    )

    all_schemes: List[Dict[str, Any]] = []

    if mode == "backend":
        # Single source of truth: backend/data_f/all_schemes.json
        logger.info("=== Loading from backend/data_f/all_schemes.json ===")
        all_schemes = load_backend_data()

    elif mode == "scrape":
        # Web scrape only
        logger.info("=== Web Scraping ===")
        scraped = scrape_multiple(TARGET_SCHEME_SLUGS, limit=scrape_limit)
        all_schemes.extend(scraped)
        logger.info("Scraped %d schemes from web", len(scraped))

    if not all_schemes:
        logger.error("No schemes loaded. Exiting.")
        sys.exit(1)

    # Clean
    logger.info("=== Cleaning ===")
    cleaned = []
    for s in all_schemes:
        c = clean_scheme(s)
        if c:
            cleaned.append(c)
    logger.info("After cleaning: %d schemes", len(cleaned))

    # Deduplicate
    logger.info("=== Deduplication ===")
    unique = deduplicate(cleaned)

    # Validate
    logger.info("=== Validation ===")
    valid, invalid = validate_all(unique)

    # Statistics
    stats = generate_statistics(valid)
    print_statistics(stats)

    if stats_only:
        return

    # Sort by quality
    valid.sort(key=lambda s: -s.get("data_quality_score", 0))

    # Save to schemes_data.json ONLY (do NOT overwrite backend source)
    output = {
        "metadata": {
            "total_schemes": len(valid),
            "generated_at": datetime.now().isoformat(),
            "source": "backend/data_f/all_schemes.json",
        },
        "statistics": stats,
        "schemes": valid,
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info("\n=== Pipeline Complete ===")
    logger.info("Total schemes: %d", len(valid))
    logger.info("Output: %s", OUTPUT_FILE)
    logger.info("Source: %s (untouched)", BACKEND_OUTPUT)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Scheme Saathi - Government Scheme Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scraper.scraper                          # use backend/data_f/all_schemes.json
  python -m scraper.scraper --mode scrape --limit 10  # web scrape 10 schemes
  python -m scraper.scraper --stats                   # statistics only
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["backend", "scrape"],
        default="backend",
        help="Data source: 'backend' = use backend/data_f/all_schemes.json only (default), 'scrape' = web scrape",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of schemes to scrape (only for --mode scrape)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics only, don't save output",
    )

    args = parser.parse_args()
    run_full_pipeline(mode=args.mode, scrape_limit=args.limit, stats_only=args.stats)


if __name__ == "__main__":
    main()

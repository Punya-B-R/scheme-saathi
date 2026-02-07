"""
Core extraction logic for Public Safety, Law & Justice schemes.

Given a Selenium driver and a scheme URL, returns a rich scheme dictionary.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from bs4 import BeautifulSoup

from scraper.extraction.benefits_parser import parse_benefits
from scraper.extraction.documents_extractor import extract_documents
from scraper.extraction.eligibility_parser import parse_eligibility
from scraper.extraction.quality_scorer import score_scheme
from scraper.utils.selenium_helper import get_soup

logger = logging.getLogger(__name__)


CATEGORY_NAME = "Public Safety, Law & Justice"

# Menu/nav patterns that indicate we captured wrong content
INVALID_DESCRIPTION_PATTERNS = [
    "DetailsBenefitsEligibility",
    "Application ProcessDocuments",
    "Sources And References",
    "Frequently Asked Questions",
    "DetailsBenefitsEligibilityExclusions",
    "Check Eligibility",  # button label, not content
]


def generate_scheme_id(url: str) -> str:
    """Generate a stable scheme_id from URL."""
    h = hashlib.md5(url.encode("utf-8")).hexdigest()[:8].upper()
    return f"PS-{h}"


def _clean_text(text: str) -> str:
    return " ".join((text or "").split())


def _is_garbage(text: str) -> bool:
    """Detect obvious UI/error garbage text."""
    if not text:
        return True
    garbage_phrases = [
        "Something went wrong",
        "Are you sure you want to sign out",
        "Enter scheme name to search",
        "Sign In",
        "Sign Out",
        "Digital India Corporation",
        "©2026",
    ]
    head = text[:500]
    return any(p in head for p in garbage_phrases)


def is_valid_scheme_name(name: str) -> bool:
    """Check if extracted name is real, not garbage."""
    if not name or len(name) < 5:
        return False
    garbage_phrases = [
        "Sign In",
        "Something went wrong",
        "Digital India",
        "Enter scheme name",
        "Please try again",
        "Cancel",
        "Ok",
        "myScheme",
    ]
    return not any(p in name for p in garbage_phrases)


def is_valid_description(text: str) -> bool:
    """Check if description is real content (not menu items or nav)."""
    if not text or len(text) < 50:
        return False
    if _is_garbage(text):
        return False
    if any(pattern in text for pattern in INVALID_DESCRIPTION_PATTERNS):
        return False
    ui_keywords = [
        "Something went wrong",
        "Sign In",
        "Sign Out",
        "Enter scheme name to search",
        "You're being redirected",
    ]
    head = text[:400]
    return not any(kw in head for kw in ui_keywords)


def _extract_description_from_details_section(soup: BeautifulSoup) -> Tuple[str, str]:
    """
    Find the Details section by id/class and extract paragraph content only.
    Returns (brief_description, detailed_description).
    """
    # Try common MyScheme / React patterns: id="details", class containing "details", section with Details heading
    selectors = [
        soup.find("div", id="details"),
        soup.find("section", id="details"),
        soup.find("div", class_=re.compile(r"details", re.I)),
        soup.find("section", class_=re.compile(r"details", re.I)),
    ]
    for section in selectors:
        if not section:
            continue
        paragraphs: List[str] = []
        for p in section.find_all("p"):
            t = _clean_text(p.get_text())
            if len(t) > 20 and not _is_garbage(t) and not any(pat in t for pat in INVALID_DESCRIPTION_PATTERNS):
                paragraphs.append(t)
        if not paragraphs:
            # Fallback: get all text from section but skip if it looks like nav
            block = _clean_text(section.get_text(separator=" "))
            if len(block) > 80 and is_valid_description(block):
                return (block[:300], block)
            continue
        detailed = " ".join(paragraphs)
        brief = " ".join(paragraphs[:2])[:400] if len(paragraphs) >= 2 else detailed[:400]
        if is_valid_description(detailed):
            return (brief, detailed)
    # Fallback: find heading "Details" and take following <p> siblings
    for h in soup.find_all(["h2", "h3", "h4"]):
        if "detail" not in h.get_text(strip=True).lower():
            continue
        parent = h.find_parent(["div", "section"])
        if not parent:
            continue
        paragraphs = []
        for p in parent.find_all("p"):
            t = _clean_text(p.get_text())
            if len(t) > 20 and is_valid_description(t):
                paragraphs.append(t)
        if paragraphs:
            detailed = " ".join(paragraphs)
            brief = " ".join(paragraphs[:2])[:400] if len(paragraphs) >= 2 else detailed[:400]
            return (brief, detailed)
    return ("", "")


def _extract_eligibility_content(soup: BeautifulSoup) -> str:
    """
    Find the eligibility CONTENT section (not the button) and return full text.
    Rejects button label 'Check Eligibility' as sole content.
    """
    selectors = [
        soup.find("div", id="eligibility"),
        soup.find("section", id="eligibility"),
        soup.find("div", class_=re.compile(r"eligib", re.I)),
        soup.find("section", class_=re.compile(r"eligib", re.I)),
    ]
    for section in selectors:
        if not section:
            continue
        content = _clean_text(section.get_text(separator=" "))
        if len(content) < 30:
            continue
        if content.strip().lower() == "check eligibility":
            continue
        if "check eligibility" in content.lower() and len(content) < 80:
            continue
        if is_valid_description(content) or len(content) > 100:
            return content
    # Heading-based: find "Eligibility" heading and get following content
    for h in soup.find_all(["h2", "h3", "h4", "strong"]):
        if "eligib" not in h.get_text(strip=True).lower() and "who can" not in h.get_text(strip=True).lower():
            continue
        parent = h.find_parent(["div", "section"])
        if parent:
            content = _clean_text(parent.get_text(separator=" "))
            if len(content) > 80 and "check eligibility" != content.strip().lower():
                return content
        parts = [h.get_text(separator=" ", strip=True)]
        sib = h.find_next_sibling()
        while sib and sib.name in ("p", "ul", "ol", "li", "div"):
            parts.append(sib.get_text(separator=" ", strip=True))
            sib = sib.find_next_sibling()
        content = " ".join(parts)
        if len(content) > 80 and "check eligibility" != content.strip().lower():
            return content
    return ""


def _extract_ministry_department(page_text: str) -> str:
    """Extract ministry/department from page text using common patterns."""
    patterns = [
        r"(Department of [^,\n\.]{3,80})",
        r"(Ministry of [^,\n\.]{3,80})",
        r"(Implemented by [^,\n\.]{3,80})",
    ]
    for pat in patterns:
        m = re.search(pat, page_text, re.I)
        if m:
            candidate = _clean_text(m.group(1))
            if 5 <= len(candidate) <= 120:
                return candidate
    return ""


def _extract_scheme_type(page_text: str) -> str:
    """Infer Central vs State from page text."""
    if re.search(r"Government of India|Central Government|GoI\b|Union Government", page_text, re.I):
        return "Central"
    if re.search(r"Government of (?:Goa|Gujarat|Bihar|Maharashtra|Karnataka|Tamil Nadu|Kerala|West Bengal|Rajasthan|Madhya Pradesh|Uttar Pradesh|Punjab|Odisha|Assam|Delhi|Jharkhand|Chhattisgarh|Uttarakhand|Telangana|Andhra Pradesh|Haryana)", page_text, re.I):
        return "State"
    return ""


def _extract_heading_and_body(soup: BeautifulSoup) -> Tuple[str, str]:
    # Name: usually main <h1>
    name = ""
    for h1 in soup.find_all("h1"):
        candidate = _clean_text(h1.get_text())
        if is_valid_scheme_name(candidate):
            name = candidate
            break

    # Description: prefer Details section content; fallback to first valid long paragraph
    brief, detailed = _extract_description_from_details_section(soup)
    if not detailed:
        for tag in soup.find_all(["p", "div"]):
            text = _clean_text(tag.get_text())
            if len(text) > 120 and is_valid_description(text):
                detailed = text
                brief = text[:300]
                break
    return name, brief or "", detailed or ""


def _find_section_text(soup: BeautifulSoup, keywords: list[str]) -> str:
    """
    Try to find a section by heading keywords and return its text (content under heading).
    """
    lowered = [k.lower() for k in keywords]
    for heading_tag in ["h2", "h3", "h4", "strong", "b"]:
        for h in soup.find_all(heading_tag):
            title = h.get_text(strip=True).lower()
            if any(k in title for k in lowered):
                parts = []
                sib = h.find_next_sibling()
                while sib and sib.name in ("p", "ul", "ol", "li", "div"):
                    parts.append(sib.get_text(separator=" ", strip=True))
                    sib = sib.find_next_sibling()
                content = " ".join(parts)
                if len(content) > 30:
                    return content
    return ""


def extract_scheme(driver, url: str) -> Dict[str, Any]:
    """
    Extract a full scheme record from a Public Safety scheme URL.
    """
    soup = get_soup(driver, url)
    page_text = _clean_text(soup.get_text(separator=" "))

    scheme_id = generate_scheme_id(url)
    scheme_name, brief_description, detailed_description = _extract_heading_and_body(soup)

    if not is_valid_scheme_name(scheme_name):
        raise ValueError(f"Invalid scheme name extracted from {url}: {scheme_name!r}")
    if not is_valid_description(detailed_description):
        raise ValueError(f"Invalid description extracted from {url}")

    # Eligibility: prefer content section, then heading-based section (never use button text)
    raw_elig = _extract_eligibility_content(soup)
    if not raw_elig or raw_elig.strip().lower() == "check eligibility":
        raw_elig = _find_section_text(soup, ["Eligibility", "Who can apply", "Who is eligible"])
    eligibility = parse_eligibility(raw_elig or "Eligibility criteria not clearly specified on the page.")

    # Benefits
    raw_benefits = _find_section_text(soup, ["Benefits", "Assistance", "Compensation"])
    benefits = parse_benefits(raw_benefits or detailed_description)

    # Documents
    documents = extract_documents(soup)

    # Application process
    raw_process = _find_section_text(soup, ["Application Process", "How to Apply"])
    application_steps: list[str] = []
    if raw_process:
        for line in raw_process.split("."):
            line = _clean_text(line)
            if len(line) > 10:
                application_steps.append(line)

    official_website = ""
    application_link = ""
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if not official_website and ("gov.in" in href or href.startswith("http")):
            official_website = href
        if not application_link and any(k in text.lower() for k in ["apply", "application"]):
            application_link = href

    ministry_department = _extract_ministry_department(page_text)
    scheme_type = _extract_scheme_type(page_text)

    # Simple crime types based on page text
    crime_types = []
    for label, pat in [
        ("Murder", "murder"),
        ("Rape / Sexual assault", "rape|sexual assault|pocso"),
        ("Acid attack", "acid attack"),
        ("Domestic violence", "domestic violence|dv act"),
        ("Child abuse", "child abuse|child sexual"),
        ("Trafficking", "traffick"),
        ("Accidents", "accident|motor vehicle"),
        ("Terrorism", "terror"),
    ]:
        if re_search(pat, page_text):
            crime_types.append(label)

    # Build scheme record
    scheme: Dict[str, Any] = {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name or "Scheme name not clearly specified",
        "scheme_name_local": "",
        "category": CATEGORY_NAME,
        "brief_description": (brief_description or detailed_description[:300] if detailed_description else ""),
        "detailed_description": detailed_description or "",
        "benefits": benefits,
        "eligibility_criteria": eligibility,
        "required_documents": documents,
        "application_process": application_steps,
        "official_website": official_website,
        "application_link": application_link,
        "helpline_number": "",
        "helpline_email": "",
        # Tier 2
        "scheme_type": scheme_type,
        "scheme_code": "",
        "ministry_department": ministry_department,
        "implementing_agency": ministry_department or "",
        "nodal_officer": "",
        "target_beneficiaries": "",
        "beneficiary_type": "Individual",
        "funding_pattern": "",
        "compensation_amount": benefits.get("financial_benefit", ""),
        "scheme_duration": "",
        "launch_date": "",
        "application_deadline": "",
        "processing_time": "",
        "geographical_coverage": eligibility.get("state", "All India"),
        "urban_rural": "Both",
        "covered_states": [eligibility.get("state", "All India")],
        "crime_types_covered": crime_types,
        "compensation_matrix": {},
        # Tier 3
        "key_features": [],
        "scheme_objectives": [],
        "payment_mode": "",
        "payment_timeline": "",
        "appeal_process": "",
        "grievance_redressal": "",
        "tracking_mechanism": "",
        "legal_provisions": "",
        "relevant_acts": [],
        "faqs": [],
        "contact_details": {},
        "related_schemes": [],
        "success_stories": "",
        # Metadata
        "source_url": url,
        "source_domain": "myscheme.gov.in",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "scraper_version": "public_safety_1.0",
        "scraping_success": True,
        "page_load_successful": True,
    }

    quality, missing = score_scheme(scheme)
    scheme["data_quality_score"] = quality
    scheme["fields_missing"] = missing

    return scheme


def re_search(pattern: str, text: str) -> bool:
    import re as _re
    return bool(_re.search(pattern, text, flags=_re.I))


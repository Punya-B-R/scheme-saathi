"""
Detail scraper: extract COMPLETE scheme information from Agriculture scheme URLs
(collected in agriculture_urls.json). Saves to agriculture_schemes_data.json with
checkpointing for crash recovery.
"""

import hashlib
import json
import logging
import os
import random
import re
import time
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agriculture_detail_scraping.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

CATEGORY_NAME = "Agriculture, Rural & Environment"
DEFAULT_INPUT_JSON = "agriculture_urls.json"
DEFAULT_OUTPUT_JSON = "agriculture_schemes_data.json"
ALL_URLS_INPUT = "all_scheme_urls.json"
ALL_SCHEMES_OUTPUT = "all_schemes_data.json"
CHECKPOINT_DIR = "checkpoints"
BATCH_SIZE = 50
DELAY_MIN, DELAY_MAX = 3, 6


def setup_driver(headless: bool = True):
    """Setup Chrome with webdriver-manager (matches your Chrome 144)."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(45)
    driver.implicitly_wait(5)
    return driver


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = text.replace("\xa0", " ").replace("\n", " ")
    return text.strip()


def generate_scheme_id(url: str) -> str:
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"AGRI-{url_hash.upper()}"


# ---------------------------------------------------------------------------
# Eligibility: find section + parse into structured fields
# ---------------------------------------------------------------------------
def find_eligibility_section(soup: BeautifulSoup) -> str:
    keywords = ["eligibility", "eligible", "who can", "criteria", "qualification", "beneficiary"]
    sections = soup.find_all(
        ["div", "section", "article"],
        class_=re.compile(r"eligib|criteria|beneficiary", re.I),
    )
    sections += soup.find_all(["div", "section", "article"], id=re.compile(r"eligib|criteria", re.I))
    for section in sections:
        text = section.get_text(strip=True)
        if len(text) > 30:
            return text
    for heading in soup.find_all(["h2", "h3", "h4", "h5"]):
        if any(kw in heading.get_text(strip=True).lower() for kw in keywords):
            parent = heading.find_parent(["div", "section", "article"])
            if parent:
                return parent.get_text(strip=True)
            content = [s.get_text(strip=True) for s in heading.find_next_siblings() if s.name and not s.name.startswith("h")]
            if content:
                return " ".join(content)
    return "Eligibility criteria not found"


def parse_eligibility_text(text: str) -> dict:
    result = {}
    if not text or text == "Eligibility criteria not found":
        return result
    t = text.lower()

    # Age
    for pat, fmt in [
        (r"(\d+)\s*(?:to|-|and)\s*(\d+)\s*years?", lambda m: f"{m.group(1)}-{m.group(2)}"),
        (r"(?:above|over|more than)\s*(\d+)\s*years?", lambda m: f"{m.group(1)}+"),
        (r"(?:below|under|less than)\s*(\d+)\s*years?", lambda m: f"<{m.group(1)}"),
        (r"between\s*(\d+)\s*and\s*(\d+)", lambda m: f"{m.group(1)}-{m.group(2)}"),
    ]:
        m = re.search(pat, text, re.I)
        if m:
            result["age"] = fmt(m)
            break

    # Gender
    if re.search(r"\b(women|woman|female|girl|ladies|mahila|widow)\b", t):
        result["gender"] = "female"
    elif re.search(r"\b(men|male|boy)\b", t):
        result["gender"] = "male"

    # Caste
    for cat, pat in [
        ("SC", r"\b(SC|Scheduled Caste)\b"),
        ("ST", r"\b(ST|Scheduled Tribe)\b"),
        ("OBC", r"\b(OBC|Other Backward Class|Backward Caste)\b"),
        ("EWS", r"\b(EWS|Economically Weaker Section)\b"),
        ("Minority", r"\b(minority|muslim|christian|sikh|buddhist|jain|parsi)\b"),
        ("General", r"\b(general category|unreserved)\b"),
    ]:
        if re.search(pat, text, re.I):
            result["caste"] = cat
            break

    # Income
    for pat, fmt in [
        (r"(?:below|less than|under)\s*₹?\s*([\d,\.]+)\s*(?:lakh|lac)", lambda m: f"< ₹{m.group(1)} lakh/year"),
        (r"BPL|Below Poverty Line", lambda m: "BPL (Below Poverty Line)"),
        (r"APL|Above Poverty Line", lambda m: "APL (Above Poverty Line)"),
    ]:
        m = re.search(pat, text, re.I)
        if m:
            result["income"] = fmt(m)
            break

    # Occupation / land
    for occ, pat in [
        ("small farmer", r"\b(small.*farmer|marginal.*farmer)\b"),
        ("farmer", r"\b(farmer|agricultur|kisaan|krishi|cultivator)\b"),
        ("landless", r"\b(landless|agricultural.*labour)\b"),
        ("tenant farmer", r"\b(tenant.*farmer|sharecropper)\b"),
    ]:
        if re.search(pat, t):
            result["occupation"] = occ
            break
    if "occupation" not in result:
        result["occupation"] = "farmer"

    for pat, fmt in [
        (r"(?:less than|below|up to|maximum)\s*([\d\.]+)\s*(?:hectare|ha|acre)", lambda m: f"< {m.group(1)} hectares"),
        (r"([\d\.]+)\s*(?:to|-)\s*([\d\.]+)\s*(?:hectare|ha|acre)", lambda m: f"{m.group(1)}-{m.group(2)} hectares"),
        (r"landless", lambda m: "landless"),
        (r"small.*marginal", lambda m: "< 2 hectares"),
    ]:
        m = re.search(pat, t)
        if m:
            result["land"] = fmt(m)
            break

    # State
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
        "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
        "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
        "West Bengal", "Delhi",
    ]
    for state in states:
        if re.search(rf"\b{re.escape(state)}\b", text, re.I):
            result["state"] = state
            break
    if "state" not in result and re.search(r"all.*india|nationwide|central.*scheme", t):
        result["state"] = "All India"

    # Other conditions
    other = []
    if re.search(r"BPL|Below Poverty Line", text, re.I):
        other.append("BPL card holder")
    if re.search(r"Aadhaar|UIDAI|Aadhar", text, re.I):
        other.append("Aadhaar required")
    if re.search(r"bank.*account|savings.*account", t):
        other.append("Bank account required")
    if re.search(r"domicile|resident of", t):
        other.append("State/district domicile required")
    if re.search(r"land.*record|land.*ownership|khasra", t):
        other.append("Land ownership documents required")
    result["other"] = other

    return result


# ---------------------------------------------------------------------------
# Extractors (Tier 1, 2, 3)
# ---------------------------------------------------------------------------
def extract_scheme_name(driver, soup: BeautifulSoup) -> str:
    for elem in [
        soup.find("h1"),
        soup.find("h1", class_=re.compile(r"title|name|heading", re.I)),
        soup.find("div", class_=re.compile(r"scheme.*title|scheme.*name", re.I)),
        soup.find("span", class_=re.compile(r"scheme.*name", re.I)),
    ]:
        if elem and elem.get_text(strip=True):
            name = re.sub(r"\s+", " ", elem.get_text(strip=True)).strip()
            if len(name) > 5:
                return name
    meta = soup.find("meta", property="og:title")
    if meta and meta.get("content"):
        return meta["content"].strip()
    return "Unknown Scheme"


def extract_benefits(driver, soup: BeautifulSoup) -> str:
    keywords = ["benefit", "assistance", "grant", "subsidy", "amount", "financial", "support", "incentive"]
    for section in soup.find_all(["div", "section", "article"], class_=re.compile(r"benefit|assistance|grant", re.I)):
        text = section.get_text(strip=True)
        if len(text) > 20:
            return clean_text(text)[:1500]
    for heading in soup.find_all(["h2", "h3", "h4", "h5"]):
        if any(kw in heading.get_text(strip=True).lower() for kw in keywords):
            parent = heading.find_parent(["div", "section", "article"])
            if parent:
                text = parent.get_text(strip=True)
                if len(text) > 20:
                    return clean_text(text)[:1500]
    for para in soup.find_all("p"):
        text = para.get_text(strip=True)
        if re.search(r"₹[\d,]+|Rs\.?\s*[\d,]+|\d+\s*(?:lakh|crore|thousand|rupees)", text, re.I):
            return clean_text(text)[:1500]
    return "Benefits information not found on page"


def extract_eligibility_criteria(driver, soup: BeautifulSoup) -> dict:
    raw = find_eligibility_section(soup)
    parsed = parse_eligibility_text(raw)
    return {
        "age_range": parsed.get("age", "any"),
        "gender": parsed.get("gender", "any"),
        "caste_category": parsed.get("caste", "any"),
        "income_limit": parsed.get("income", "any"),
        "occupation": parsed.get("occupation", "farmer"),
        "state": parsed.get("state", "All India"),
        "land_ownership": parsed.get("land", "any"),
        "other_conditions": parsed.get("other", []),
        "raw_eligibility_text": raw,
    }


def extract_required_documents(driver, soup: BeautifulSoup) -> list:
    documents = []
    for section in soup.find_all(["div", "section", "ul", "ol"], class_=re.compile(r"document|required|checklist", re.I)):
        for li in section.find_all("li"):
            doc = li.get_text(strip=True)
            if 3 < len(doc) < 200:
                documents.append(doc)
        text = section.get_text()
        for doc in ["Aadhaar", "Aadhar", "PAN", "Voter ID", "Income Certificate", "Caste Certificate", "Bank Account", "Land Records", "Passport Photo", "Ration Card"]:
            if re.search(rf"\b{doc}\b", text, re.I) and doc not in documents:
                documents.append(doc)
    return list(dict.fromkeys(documents)) if documents else ["Check official website for document requirements"]


def extract_brief_description(driver, soup: BeautifulSoup) -> str:
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return (meta["content"] or "")[:300]
    p = soup.find("p")
    if p:
        t = p.get_text(strip=True)
        if len(t) > 20:
            return t[:300]
    return "Description not available"


def extract_detailed_description(driver, soup: BeautifulSoup) -> str:
    for section in soup.find_all(["div", "section"], class_=re.compile(r"about|description|overview|detail", re.I)):
        text = section.get_text(strip=True)
        if len(text) > 100:
            return clean_text(text)[:2000]
    paras = soup.find_all("p")
    if paras:
        return clean_text(" ".join(p.get_text(strip=True) for p in paras[:5]))[:2000]
    return "Detailed description not available"


def extract_application_process(driver, soup: BeautifulSoup) -> list:
    steps = []
    for section in soup.find_all(["div", "section", "ol", "ul"], class_=re.compile(r"apply|process|procedure|steps", re.I)):
        for li in section.find_all("li"):
            step = li.get_text(strip=True)
            if len(step) > 10:
                steps.append(step)
    if not steps:
        text = soup.get_text()
        for m in re.finditer(r"(?:Step\s*)?(\d+)[.:\)]\s*([^\n]+)", text, re.I):
            s = m.group(2).strip()
            if len(s) > 10:
                steps.append(s)
    return steps[:10] if steps else ["Visit official website for application procedure"]


def extract_official_website(driver, soup: BeautifulSoup) -> str:
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if href.startswith("http") and any(k in (a.get_text(strip=True) or "").lower() for k in ["apply", "registration", "portal", "official"]):
            return href
    urls = re.findall(r"https?://[^\s<>\"']+", soup.get_text())
    for url in urls:
        if any(k in url.lower() for k in ["apply", "registration", "portal"]):
            return url
    return "Check MyScheme.gov.in for application link"


def extract_application_deadline(driver, soup: BeautifulSoup) -> str:
    text = soup.get_text()
    for pat in [r"deadline[:\s]*([\d/\-]+)", r"last date[:\s]*([\d/\-]+)", r"before[:\s]*([\d/\-]+)", r"by[:\s]*([\d/\-]+)"]:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1).strip()
    if re.search(r"rolling|year.*round|anytime|continuous", text, re.I):
        return "Rolling basis"
    return "Check official website"


def extract_scheme_type(driver, soup: BeautifulSoup) -> str:
    t = soup.get_text().lower()
    if "central" in t or "pradhan mantri" in t or "pm-" in t:
        return "Central"
    if any(s in t for s in ["state government", "rajasthan", "bihar", "up", "maharashtra"]):
        return "State"
    return "Central"


def extract_ministry_department(driver, soup: BeautifulSoup) -> str:
    text = soup.get_text()
    for pat in [r"Ministry of ([A-Z][^.,\n]+)", r"Department of ([A-Z][^.,\n]+)", r"Implemented by ([A-Z][^.,\n]+)"]:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return "Ministry of Agriculture & Farmers Welfare"


def extract_beneficiary_type(driver, soup: BeautifulSoup) -> str:
    t = soup.get_text().lower()
    if "fpo" in t or "farmer producer organization" in t or "group" in t:
        return "Group/FPO"
    if "institution" in t or "organization" in t:
        return "Institution"
    return "Individual"


def extract_funding_pattern(driver, soup: BeautifulSoup) -> str:
    text = soup.get_text()
    m = re.search(r"(\d+):(\d+)", text)
    if m:
        return m.group(0)
    if re.search(r"100%.*Central", text, re.I):
        return "100% Central"
    return "Not specified"


# ---------------------------------------------------------------------------
# Validation, quality score, partial/failed entries
# ---------------------------------------------------------------------------
def validate_minimum_data(scheme_data: dict) -> bool:
    has_name = len(scheme_data.get("scheme_name", "")) > 5
    has_benefits = len(scheme_data.get("benefits", "")) > 20
    ec = scheme_data.get("eligibility_criteria") or {}
    has_eligibility = (ec.get("raw_eligibility_text") or "") != "Eligibility criteria not found"
    return has_name and (has_benefits or has_eligibility)


def calculate_quality_score(scheme_data: dict) -> int:
    score = 0
    if len(scheme_data.get("scheme_name", "")) > 5:
        score += 10
    if len(scheme_data.get("benefits", "")) > 50:
        score += 15
    ec = scheme_data.get("eligibility_criteria") or {}
    if (ec.get("raw_eligibility_text") or "") != "Eligibility criteria not found":
        score += 15
    if len(scheme_data.get("required_documents", [])) > 0:
        score += 10
    if len(scheme_data.get("detailed_description", "")) > 100:
        score += 10
    if len(scheme_data.get("application_process", [])) > 0:
        score += 10
    if "http" in (scheme_data.get("official_website") or ""):
        score += 10
    if scheme_data.get("scheme_type") in ("Central", "State"):
        score += 5
    if len(scheme_data.get("ministry_department", "")) > 5:
        score += 5
    if (scheme_data.get("application_deadline") or "") != "Check official website":
        score += 5
    if (scheme_data.get("funding_pattern") or "") != "Not specified":
        score += 5
    return min(score, 100)


def create_partial_scheme_data(url: str, soup: BeautifulSoup, category_name: str = None) -> dict:
    return {
        "scheme_id": generate_scheme_id(url),
        "scheme_name": extract_scheme_name(None, soup),
        "category": category_name or CATEGORY_NAME,
        "benefits": "Data extraction incomplete",
        "eligibility_criteria": {
            "age_range": "any", "gender": "any", "caste_category": "any", "income_limit": "any",
            "occupation": "farmer", "state": "All India", "land_ownership": "any",
            "other_conditions": [], "raw_eligibility_text": "Incomplete data",
        },
        "required_documents": ["Check official website"],
        "brief_description": "Partial data only",
        "detailed_description": "Visit source URL for complete information",
        "application_process": ["Visit official website"],
        "official_website": "Check MyScheme.gov.in",
        "application_deadline": "Check official website",
        "scheme_type": "Central",
        "ministry_department": "Agriculture",
        "beneficiary_type": "Individual",
        "funding_pattern": "Not specified",
        "source_url": url,
        "last_updated": datetime.now().isoformat(),
        "data_quality_score": 30,
        "scraping_success": False,
    }


def create_failed_scheme_data(url: str, error: str, category_name: str = None) -> dict:
    return {
        "scheme_id": generate_scheme_id(url),
        "scheme_name": "Failed to extract",
        "category": category_name or CATEGORY_NAME,
        "source_url": url,
        "scraping_error": error,
        "scraping_success": False,
        "data_quality_score": 0,
        "last_updated": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Single scheme scrape + batch with checkpoints
# ---------------------------------------------------------------------------
def scrape_scheme_detail(driver, scheme_url: str, retry_count: int = 3, category_name: str = None) -> dict | None:
    cat = category_name or CATEGORY_NAME
    for attempt in range(retry_count):
        try:
            logger.info("Loading: %s (attempt %s/%s)", scheme_url, attempt + 1, retry_count)
            driver.get(scheme_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            time.sleep(3)
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            scheme_data = {
                "scheme_id": generate_scheme_id(scheme_url),
                "scheme_name": extract_scheme_name(driver, soup),
                "category": cat,
                "benefits": extract_benefits(driver, soup),
                "eligibility_criteria": extract_eligibility_criteria(driver, soup),
                "required_documents": extract_required_documents(driver, soup),
                "brief_description": extract_brief_description(driver, soup),
                "detailed_description": extract_detailed_description(driver, soup),
                "application_process": extract_application_process(driver, soup),
                "official_website": extract_official_website(driver, soup),
                "application_deadline": extract_application_deadline(driver, soup),
                "scheme_type": extract_scheme_type(driver, soup),
                "ministry_department": extract_ministry_department(driver, soup),
                "beneficiary_type": extract_beneficiary_type(driver, soup),
                "funding_pattern": extract_funding_pattern(driver, soup),
                "source_url": scheme_url,
                "last_updated": datetime.now().isoformat(),
                "scraping_success": True,
            }
            scheme_data["data_quality_score"] = calculate_quality_score(scheme_data)

            if validate_minimum_data(scheme_data):
                logger.info("✓ Success: %s... (Quality: %s/100)", scheme_data["scheme_name"][:50], scheme_data["data_quality_score"])
                return scheme_data
            logger.warning("⚠ Incomplete data for: %s", scheme_url)
            if attempt < retry_count - 1:
                time.sleep(5)
                continue
            return create_partial_scheme_data(scheme_url, soup, cat)
        except Exception as e:
            logger.error("Error scraping %s (attempt %s): %s", scheme_url, attempt + 1, e)
            if attempt < retry_count - 1:
                time.sleep(5)
            else:
                return create_failed_scheme_data(scheme_url, str(e), cat)
    return None


def save_checkpoint(schemes: list, filename: str) -> None:
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    path = os.path.join(CHECKPOINT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schemes, f, indent=2, ensure_ascii=False)
    logger.info("Checkpoint saved: %s", path)


def scrape_all_schemes(urls: list[str], batch_size: int = BATCH_SIZE, headless: bool = True, category_name: str = None) -> tuple[list, list]:
    driver = None
    all_schemes = []
    failed_urls = []
    total = len(urls)
    cat = category_name or CATEGORY_NAME

    try:
        driver = setup_driver(headless=headless)
        logger.info("=" * 70)
        logger.info("Starting detail scraping for %s schemes (category=%s)", total, cat)
        logger.info("=" * 70)

        for idx, url in enumerate(urls, 1):
            logger.info("\n[%s/%s] %s", idx, total, url)
            scheme = scrape_scheme_detail(driver, url, category_name=cat)
            if scheme:
                all_schemes.append(scheme)
                if not scheme.get("scraping_success"):
                    failed_urls.append(url)
            else:
                failed_urls.append(url)

            if idx % batch_size == 0:
                save_checkpoint(all_schemes, f"checkpoint_{idx}.json")
                ok = len(all_schemes) - len(failed_urls)
                logger.info("✓ Checkpoint: %s schemes | Success rate: %.1f%%", idx, (ok / len(all_schemes) * 100) if all_schemes else 0)

            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        logger.info("\n" + "=" * 70)
        logger.info("SCRAPING COMPLETE! Total: %s | Failed/partial: %s", len(all_schemes), len(failed_urls))
        logger.info("=" * 70)
    finally:
        if driver:
            driver.quit()

    return all_schemes, failed_urls


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Scrape scheme details from MyScheme URLs. Supports agriculture_urls.json or all_scheme_urls.json."
    )
    parser.add_argument("--input", "-i", default=DEFAULT_INPUT_JSON, help="Input JSON with 'urls' array (e.g. all_scheme_urls.json)")
    parser.add_argument("--output", "-o", default=None, help="Output JSON path (default: from input name)")
    parser.add_argument("--category", "-c", default=None, help="Category label for all scraped schemes (default: Agriculture for agriculture_urls, else Government Schemes)")
    parser.add_argument("--start", type=int, default=0, help="Skip first N URLs (for resumable/chunked runs)")
    parser.add_argument("--limit", type=int, default=0, help="Max URLs to scrape (0 = all)")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser headless")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Show browser")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    urls = data.get("urls", data) if isinstance(data, dict) else data
    if not isinstance(urls, list):
        urls = list(urls)

    # Slice for chunked/resumable runs
    start = max(0, args.start)
    limit = args.limit
    if limit > 0:
        urls = urls[start : start + limit]
    else:
        urls = urls[start:]

    output_path = args.output
    if not output_path:
        output_path = ALL_SCHEMES_OUTPUT if args.input == ALL_URLS_INPUT else DEFAULT_OUTPUT_JSON

    category_name = args.category
    if not category_name:
        category_name = CATEGORY_NAME if "agriculture" in args.input.lower() else "Government Schemes"

    logger.info("Loaded %s URLs from %s (using start=%s, limit=%s) -> category=%s", len(urls), args.input, start, limit or "all", category_name)
    schemes, failed = scrape_all_schemes(urls, batch_size=BATCH_SIZE, headless=args.headless, category_name=category_name)

    avg_quality = sum(s.get("data_quality_score", 0) for s in schemes) / len(schemes) if schemes else 0
    high_quality = sum(1 for s in schemes if s.get("data_quality_score", 0) >= 70)
    logger.info("Total: %s | High quality (70+): %s | Avg score: %.1f", len(schemes), high_quality, avg_quality)

    output = {
        "category": category_name,
        "total_schemes": len(schemes),
        "schemes": schemes,
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "input_file": args.input,
            "success_count": len(schemes) - len(failed),
            "failed_count": len(failed),
            "average_quality_score": round(avg_quality, 2),
        },
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info("✓ Saved to %s", output_path)

    if failed:
        failed_path = "failed_urls_all.json" if "all_scheme" in args.input else "failed_urls.json"
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed, f, indent=2)
        logger.info("✓ Failed URLs saved to %s", failed_path)


if __name__ == "__main__":
    main()

"""
Scheme Saathi - Web scraper for government schemes from MyScheme.gov.in.
Uses Selenium (headless Chrome) for JavaScript-rendered content.
Falls back to manual data if scraping fails after retries.
"""

import json
import logging
import random
import re
import time
from datetime import date
from typing import Any
from urllib.parse import urljoin, urlparse

from data_cleaner import clean_and_validate, save_schemes_json
from manual_data import get_manual_schemes

# Re-export for convenience
from data_cleaner import search_schemes, update_scheme  # noqa: F401

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

    # Scraping log and result files
SCRAPING_LOG_PATH = "scraping_log.txt"
SCRAPE_RESULT_PATH = "scrape_result.json"
_log_entries: list[str] = []


def _log(msg: str) -> None:
    """Log to logger and append to scraping log buffer."""
    logger.info("%s", msg)
    _log_entries.append(msg)


def _flush_scraping_log() -> None:
    """Write scraping log buffer to file."""
    try:
        with open(SCRAPING_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(_log_entries))
        logger.info("Scraping log written to %s", SCRAPING_LOG_PATH)
    except Exception as e:
        logger.warning("Could not write scraping log: %s", e)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "https://www.myscheme.gov.in"
SEARCH_URL = f"{BASE_URL}/search"

# Page behaviour
PAGE_LOAD_TIMEOUT = 30  # allow slower loads
ELEMENT_WAIT_TIMEOUT = 25

# Rate limiting / politeness
RATE_LIMIT_DETAIL_MIN = 5
RATE_LIMIT_DETAIL_MAX = 7
RATE_LIMIT_BETWEEN_CATEGORIES_MIN = 3
RATE_LIMIT_BETWEEN_CATEGORIES_MAX = 7

# Retries and thresholds
MAX_RETRIES = 3
MIN_SCHEMES_FROM_SCRAPE = 30  # below this, use manual fallback
TARGET_SCHEMES = 120  # aim for ~100–150, hard cap
TEST_MODE_LIMIT = 5

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Categories as visible on MyScheme (may evolve over time)
CATEGORIES: list[str] = [
    "Agriculture, Rural & Environment",
    "Banking, Financial Services and Insurance",
    "Business & Entrepreneurship",
    "Education & Learning",
    "Health & Wellness",
    "Housing & Shelter",
    "Public Safety, Law & Justice",
    "Science, IT & Communications",
    "Skills & Employment",
    "Social Welfare & Empowerment",
    "Sports & Culture",
    "Transport & Infrastructure",
    "Travel & Tourism",
    "Utility & Sanitation",
    "Women & Child",
]


# ---------------------------------------------------------------------------
# Selenium WebDriver setup (uses webdriver-manager, no undetected_chromedriver)
# ---------------------------------------------------------------------------
def setup_driver(headless: bool = True):
    """
    Initialize Chrome WebDriver using webdriver-manager.

    This will download a ChromeDriver that matches your installed Chrome
    (e.g. 144.x), avoiding the version-mismatch error you saw.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument("--ignore-certificate-errors")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ---------------------------------------------------------------------------
# Helpers for listing pages: extract URLs, scrolling, load-more, categories
# ---------------------------------------------------------------------------
def _extract_scheme_urls(driver) -> set[str]:
    """Extract scheme detail URLs from current page."""
    from selenium.webdriver.common.by import By

    urls: set[str] = set()
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/schemes/"]')
    for a in links:
        try:
            href = a.get_attribute("href") or ""
            if not href or "/schemes/" not in href:
                continue
            parsed = urlparse(href)
            path = parsed.path.strip("/")
            if not path.startswith("schemes/") or path == "schemes":
                continue
            urls.add(href)
        except Exception:
            continue
    return urls


def _scroll_and_collect_schemes(driver, max_scrolls: int = 10) -> set[str]:
    """
    Handle infinite scroll / load-more style pages.
    Scrolls and/or clicks 'Load More' buttons, collecting scheme URLs until no new content.
    """
    from selenium.webdriver.common.by import By

    urls: set[str] = set()
    last_height = 0

    for _ in range(max_scrolls):
        # Collect whatever is visible now
        urls.update(_extract_scheme_urls(driver))

        # Try clicking a 'Load More' style button if present
        clicked = False
        try:
            load_more = driver.find_element(
                By.XPATH,
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
            )
            driver.execute_script("arguments[0].click();", load_more)
            clicked = True
        except Exception:
            clicked = False

        # If no load-more, fallback to scrolling
        if not clicked:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            except Exception:
                break

        time.sleep(3)
        try:
            new_height = driver.execute_script("return document.body.scrollHeight") or 0
        except Exception:
            new_height = 0
        if new_height == last_height:
            break
        last_height = new_height

    urls.update(_extract_scheme_urls(driver))
    return urls


def _scrape_category(
    driver,
    category_label: str,
    global_seen_urls: set[str],
    limit_remaining: int,
) -> list[dict[str, Any]]:
    """
    Scrape all schemes for a single category using filters + scroll/load-more.
    Returns list of scheme dicts (detail pages scraped).
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    schemes: list[dict[str, Any]] = []
    if limit_remaining <= 0:
        return schemes

    try:
        _log(f"Navigating to search page for category: {category_label}")
        driver.get(SEARCH_URL)
        WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        time.sleep(2)

        # Try to click the category filter checkbox/label
        try:
            category_el = driver.find_element(
                By.XPATH, f"//label[contains(normalize-space(.), '{category_label}')]"
            )
            driver.execute_script("arguments[0].click();", category_el)
            _log(f"Clicked category filter: {category_label}")
            time.sleep(3)
        except Exception as e:
            _log(f"Category filter not found / not clickable for '{category_label}': {e}")

        # Collect scheme URLs for this category view (scroll + load more)
        urls = _scroll_and_collect_schemes(driver)
        new_urls = [u for u in urls if u not in global_seen_urls]
        for u in new_urls:
            global_seen_urls.add(u)

        _log(
            f"Category '{category_label}': found {len(urls)} URLs, "
            f"{len(new_urls)} new (global unique)"
        )

        # Scrape detail pages for this category
        for i, url in enumerate(new_urls):
            if len(schemes) >= limit_remaining:
                break
            _log(
                f"[{category_label}] Scraping scheme {len(schemes)+1}/{limit_remaining}: {url}"
            )
            try:
                scheme = scrape_scheme_detail(
                    driver, url, title="", category_hint=category_label
                )
                if scheme:
                    schemes.append(scheme)
            except Exception as e:
                _log(f"Skipped {url}: {e}")
                logger.exception("Detail scrape failed: %s", url)

            time.sleep(random.uniform(RATE_LIMIT_DETAIL_MIN, RATE_LIMIT_DETAIL_MAX))

        _log(
            f"Category '{category_label}': successfully scraped {len(schemes)} scheme(s) "
            f"(limit for this category was {limit_remaining})"
        )
        return schemes

    except Exception as e:
        _log(f"Category '{category_label}' scrape failed: {e}")
        logger.exception("Category scrape failed: %s", category_label)
        return schemes


# ---------------------------------------------------------------------------
# Eligibility text parsing (regex / smart matching)
# ---------------------------------------------------------------------------
def parse_eligibility(eligibility_text: str) -> dict[str, Any]:
    """
    Parse eligibility paragraph into structured fields.
    Uses regex and keyword matching; stores original text in other_conditions if unclear.
    """
    text = (eligibility_text or "").strip().lower()
    result = {
        "age_range": "any",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "any",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [],
    }

    # Age: "18-40", "above 60", "60+", "18 to 45", "below 18", "between 18 and 40"
    age_patterns = [
        r"(\d+)\s*-\s*(\d+)\s*(?:years?)?",
        r"above\s*(\d+)",
        r"(\d+)\s*\+",
        r"below\s*(\d+)",
        r"between\s*(\d+)\s*and\s*(\d+)",
        r"(\d+)\s*to\s*(\d+)\s*(?:years?)?",
        r"minimum\s*age\s*(\d+)",
        r"maximum\s*age\s*(\d+)",
        r"aged?\s*(\d+)\s*(?:years?)?\s*(?:and)?\s*above?",
        r"senior\s*citizen",
    ]
    for pat in age_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            if "senior" in pat:
                result["age_range"] = "60+"
                break
            groups = m.groups()
            if len(groups) == 2 and groups[0].isdigit() and groups[1].isdigit():
                result["age_range"] = f"{groups[0]}-{groups[1]}"
                break
            if len(groups) == 1 and groups[0].isdigit():
                if "above" in pat or "and above" in text:
                    result["age_range"] = f"{groups[0]}+"
                elif "below" in pat:
                    result["age_range"] = f"0-{groups[0]}"
                else:
                    result["age_range"] = f"{groups[0]}+"
                break

    # Gender: women, female, girls, male, men
    if re.search(r"\b(women|female|girls|ladies)\b", text):
        result["gender"] = "female"
    elif re.search(r"\b(men|male|boys)\b", text) and "female" not in text and "women" not in text:
        result["gender"] = "male"

    # Caste: SC/ST, OBC, Scheduled Caste, General
    if re.search(r"\b(sc|st|scheduled\s*caste|scheduled\s*tribe)\b", text):
        if re.search(r"\b(st|scheduled\s*tribe)\b", text):
            result["caste_category"] = "ST"
        else:
            result["caste_category"] = "SC"
    if re.search(r"\bobc\b|other\s*backward\s*class", text):
        result["caste_category"] = "OBC"
    if re.search(r"\bgeneral\b", text) and result["caste_category"] == "any":
        result["caste_category"] = "General"
    if re.search(r"\bminority\b", text):
        result["caste_category"] = "Minority"

    # Income: "below 2.5 lakh", "BPL", "annual income", "income limit"
    income_patterns = [
        r"(?:annual\s*)?income\s*(?:below|less than|up to|under)\s*[₹rs.]?\s*([\d.,]+)\s*(?:lakh|lac)",
        r"bpl|below\s*poverty",
        r"([\d.,]+)\s*lakh\s*(?:per\s*annum|p\.?a\.?)?",
        r"income\s*limit\s*[₹rs.]?\s*([\d.,]+)",
    ]
    for pat in income_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            if "bpl" in pat or "poverty" in pat:
                result["income_limit"] = "BPL"
                break
            if m.lastindex and m.group(1):
                result["income_limit"] = f"< {m.group(1).strip()} lakhs/year"
                break

    # Occupation: farmer, student, senior citizen, self-employed, entrepreneur
    if re.search(r"\bfarmer|agricultur", text):
        result["occupation"] = "farmer"
    elif re.search(r"\bstudent|scholarship|education\b", text):
        result["occupation"] = "student"
    elif re.search(r"\bsenior\s*citizen|old\s*age|pension\b", text):
        result["occupation"] = "senior citizen"
    elif re.search(r"\bentrepreneur|self\s*employed|business\b|msme", text):
        result["occupation"] = "entrepreneur"
    elif re.search(r"\bwoman|pregnant|lactating|mother\b", text):
        result["occupation"] = "any"

    # State: "All India", "Bihar", "UP", "specific states"
    if re.search(r"\ball\s*india|pan\s*india|nationwide\b", text):
        result["state"] = "All India"
    else:
        state_match = re.search(
            r"\b(bihar|up|uttar\s*pradesh|maharashtra|rajasthan|west\s*bengal|madhya\s*pradesh|tamil\s*nadu|gujarat|karnataka|andhra|telangana|kerala|punjab|haryana|odisha|assam|jharkhand|chhattisgarh)\b",
            text,
            re.IGNORECASE,
        )
        if state_match:
            result["state"] = state_match.group(1).title()

    # Land: "landholding", "hectares", "acre"
    land_match = re.search(r"(\d+)\s*(?:hectare|acre|ha\.?)", text, re.IGNORECASE)
    if land_match:
        result["land_ownership"] = f"< {land_match.group(1)} hectares"
    elif re.search(r"\blandholding|land\s*owner|marginal\s*farmer\b", text):
        result["land_ownership"] = "small/marginal (as per scheme)"

    # Store first 2 sentences as other_conditions if we have raw text and little else
    if eligibility_text and len(text) > 100:
        sentences = re.split(r"[.!?]+", eligibility_text.strip())[:3]
        result["other_conditions"] = [s.strip() for s in sentences if len(s.strip()) > 20][:5]

    return result


# ---------------------------------------------------------------------------
# Scrape scheme list from search/listing page
# ---------------------------------------------------------------------------
def scrape_scheme_list(driver, category: str | None = None, max_schemes: int = 100) -> list[tuple[str, str, str]]:
    """
    Load search/listing page, wait for scheme cards, extract (title, brief, detail_url).
    Returns list of (title, brief_description, detail_url).
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    results: list[tuple[str, str, str]] = []
    seen_urls: set[str] = set()

    for list_url in LISTING_URLS:
        if len(results) >= max_schemes:
            break
        _log(f"Loading listing: {list_url}")
        try:
            driver.get(list_url)
            WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            time.sleep(2)
            # Also wait for links that might be scheme links
            time.sleep(1 + random.uniform(0, 1))
        except Exception as e:
            _log(f"Listing page failed {list_url}: {e}")
            continue

        # Find all links pointing to /schemes/
        try:
            links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/schemes/"]')
            for a in links:
                try:
                    href = a.get_attribute("href") or ""
                    if not href or "/schemes/" not in href:
                        continue
                    parsed = urlparse(href)
                    path = parsed.path.strip("/")
                    if not path.startswith("schemes/") or path == "schemes":
                        continue
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)
                    title = (a.text or "").strip() or "Scheme"
                    if len(title) < 3:
                        title = path.split("/")[-1].replace("-", " ").title()
                    results.append((title, "", href))
                    if len(results) >= max_schemes:
                        break
                except Exception:
                    continue
        except Exception as e:
            _log(f"Error extracting links from {list_url}: {e}")

        if results:
            _log(f"Found {len(results)} scheme URLs from listing")
            break

    # If no /schemes/ links, try any link that might be a scheme (e.g. /scheme/ or detail path)
    if not results:
        try:
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for a in all_links:
                href = a.get_attribute("href") or ""
                if BASE_URL in href and ("scheme" in href.lower() or "schemes" in href):
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)
                    title = (a.text or "").strip() or "Scheme"
                    if len(title) < 3:
                        title = urlparse(href).path.strip("/").replace("-", " ").title()
                    results.append((title, "", href))
                    if len(results) >= max_schemes:
                        break
        except Exception as e:
            _log(f"Fallback link extraction failed: {e}")

    return results[:max_schemes]


# ---------------------------------------------------------------------------
# Scrape single scheme detail page
# ---------------------------------------------------------------------------
def scrape_scheme_detail(driver, scheme_url: str, title: str = "", category_hint: str = "Other") -> dict[str, Any] | None:
    """
    Scrape full details from a scheme's detail page.
    Returns scheme dict or None on failure.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    slug = scheme_url.rstrip("/").split("/")[-1] or "unknown"
    scheme_id = re.sub(r"[^A-Za-z0-9\-_]", "-", slug)[:50]

    try:
        driver.get(scheme_url)
        WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        time.sleep(1 + random.uniform(0.5, 1.5))
    except Exception as e:
        _log(f"Detail page load failed {scheme_url}: {e}")
        return None

    try:
        page_source = driver.page_source
    except Exception as e:
        _log(f"Could not get page source {scheme_url}: {e}")
        return None

    # Parse with BeautifulSoup for reliable extraction
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        BeautifulSoup = None

    if not BeautifulSoup:
        return _minimal_scheme(scheme_id, title or slug, scheme_url)

    soup = BeautifulSoup(page_source, "html.parser")

    def text_of(selectors: list[str]) -> str:
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                return (el.get_text(strip=True) or "").strip()
        return ""

    def all_text(selectors: list[str]) -> list[str]:
        for sel in selectors:
            nodes = soup.select(sel)
            if nodes:
                return [n.get_text(strip=True) for n in nodes if n.get_text(strip=True)]
        return []

    # Title
    scheme_name = title or text_of(["h1", ".scheme-title", "[data-testid='scheme-title']", "title"])
    if not scheme_name or len(scheme_name) < 2:
        scheme_name = slug.replace("-", " ").title()

    # Description (brief + detailed)
    brief = text_of([".scheme-description", ".brief-description", "[data-testid='description']"])
    meta = soup.select_one("meta[name='description']")
    if meta and meta.get("content"):
        brief = meta.get("content", "").strip() or brief
    if not brief:
        first_p = soup.select_one("main p") or soup.select_one("article p") or soup.select_one("p")
        brief = (first_p.get_text(strip=True) if first_p else "")[:500]
    detailed = brief
    long_p = soup.select("main p") or soup.select("article p") or soup.select("p")
    if long_p:
        detailed = " ".join(p.get_text(strip=True) for p in long_p[:15] if p.get_text(strip=True))[:3000]

    # Sections: Eligibility, Benefits, Documents, Application
    full_text = soup.get_text(separator=" ", strip=True)
    eligibility_text = ""
    benefits_text = ""
    docs_text = ""
    app_process_text = ""

    for heading in ["Eligibility", "Benefits", "Documents Required", "Application Process", "How to Apply"]:
        for tag in ["h2", "h3", "h4", "strong"]:
            els = soup.find_all(tag, string=re.compile(heading, re.I))
            for el in els:
                next_sibling = el.find_next_sibling()
                if next_sibling:
                    block = next_sibling.get_text(strip=True) if next_sibling else ""
                else:
                    block = ""
                    for s in el.find_all_next():
                        if s.name in ("h2", "h3", "h4") and s != el:
                            break
                        block += " " + (s.get_text(strip=True) if s else "")
                block = block.strip()[:2000]
                if "eligibility" in heading.lower():
                    eligibility_text = block or eligibility_text
                elif "benefit" in heading.lower():
                    benefits_text = block or benefits_text
                elif "document" in heading.lower():
                    docs_text = block or docs_text
                elif "application" in heading.lower() or "how to apply" in heading.lower():
                    app_process_text = block or app_process_text

    if not eligibility_text and "eligibility" in full_text.lower():
        idx = full_text.lower().find("eligibility")
        eligibility_text = full_text[max(0, idx - 20) : idx + 800]

    # Parse eligibility into structured data
    eligibility = parse_eligibility(eligibility_text) if eligibility_text else parse_eligibility("")

    # Required documents: list items or comma/semicolon split
    required_documents = []
    if docs_text:
        required_documents = re.split(r"[,;]|\n", docs_text)
        required_documents = [d.strip() for d in required_documents if len(d.strip()) > 2][:15]
    if not required_documents:
        required_documents = all_text(["li"])[:10]
        if not required_documents:
            required_documents = ["Aadhaar", "Bank account details"]  # default

    # Application process: numbered steps or list items
    application_process = []
    if app_process_text:
        for line in re.split(r"\n|(?:\d+[.)]\s*)", app_process_text):
            line = line.strip()
            if len(line) > 15:
                application_process.append(line)
        application_process = application_process[:12]
    if not application_process and all_text(["ol li", "ul li"]):
        application_process = all_text(["ol li", "ul li"])[:12]

    # Official website / apply link
    official_website = scheme_url
    apply_link = soup.select_one('a[href*="apply"]') or soup.select_one('a[href*="portal"]') or soup.select_one('a[href*="gov.in"]')
    if apply_link and apply_link.get("href"):
        official_website = urljoin(BASE_URL, apply_link.get("href", ""))

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "category": category_hint,
        "brief_description": (brief or scheme_name)[:500],
        "detailed_description": (detailed or brief or "")[:3000],
        "eligibility_criteria": eligibility,
        "benefits": (benefits_text or "See official scheme page.")[:1000],
        "required_documents": required_documents[:15],
        "application_process": application_process if application_process else ["Visit official website for application process."],
        "application_deadline": "Rolling",
        "official_website": official_website,
        "last_updated": date.today().isoformat(),
    }


def _minimal_scheme(scheme_id: str, scheme_name: str, url: str) -> dict[str, Any]:
    """Build minimal scheme when parsing fails."""
    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "category": "Other",
        "brief_description": "",
        "detailed_description": "",
        "eligibility_criteria": {
            "age_range": "any",
            "gender": "any",
            "caste_category": "any",
            "income_limit": "any",
            "occupation": "any",
            "state": "All India",
            "land_ownership": "any",
            "other_conditions": [],
        },
        "benefits": "",
        "required_documents": [],
        "application_process": [],
        "application_deadline": "Rolling",
        "official_website": url,
        "last_updated": date.today().isoformat(),
    }


# ---------------------------------------------------------------------------
# Main Selenium scrape (multi-category, scroll/pagination aware)
# ---------------------------------------------------------------------------
def scrape_with_selenium(
    limit: int = TARGET_SCHEMES,
    test_mode: bool = False,
    headless: bool = True,
) -> list[dict[str, Any]]:
    """
    Run full Selenium scrape:
    - Iterates over visible categories
    - For each, applies filter, handles scroll/load-more, collects URLs
    - Visits each detail page with strong rate limiting
    - Deduplicates across categories

    On repeated failure, returns [] and fallback will kick in.
    """
    global _log_entries
    _log_entries = []

    if test_mode:
        limit = min(limit, TEST_MODE_LIMIT)
        _log(f"Test mode: scraping at most {limit} schemes")

    driver = None
    schemes: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for attempt in range(MAX_RETRIES):
        _log(f"Scrape attempt {attempt + 1}/{MAX_RETRIES}")
        try:
            driver = setup_driver(headless=headless)

            for category in CATEGORIES:
                if len(schemes) >= limit:
                    break

                remaining = limit - len(schemes)
                cat_schemes = _scrape_category(
                    driver,
                    category_label=category,
                    global_seen_urls=seen_urls,
                    limit_remaining=remaining,
                )
                schemes.extend(cat_schemes)

                # Politeness: wait a bit between categories
                time.sleep(
                    random.uniform(
                        RATE_LIMIT_BETWEEN_CATEGORIES_MIN,
                        RATE_LIMIT_BETWEEN_CATEGORIES_MAX,
                    )
                )

            if schemes:
                break
        except Exception as e:
            _log(f"Attempt {attempt + 1} failed: {e}")
            logger.exception("Selenium scrape failed")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = None

    _flush_scraping_log()
    return schemes


# ---------------------------------------------------------------------------
# Pipeline: Selenium first, then fallback
# ---------------------------------------------------------------------------
def _write_scrape_result(
    source: str,
    scraped_count: int,
    target: int,
    final_scheme_count: int,
) -> None:
    """Write scrape_result.json so you can tell if scraping worked and what percent of target was reached."""
    percent = round((scraped_count / target * 100), 1) if target else 0
    if source == "scraped":
        message = f"Scraping succeeded: {scraped_count} schemes scraped ({percent}% of target {target}). Data in schemes_data.json is from MyScheme.gov.in."
    else:
        message = f"Scraping failed or insufficient: {scraped_count} schemes scraped. Fallback to manual data ({final_scheme_count} schemes). Data in schemes_data.json is from manual_data.py."
    result = {
        "source": source,
        "scraped_count": scraped_count,
        "target": target,
        "percent_of_target": percent,
        "final_scheme_count": final_scheme_count,
        "message": message,
    }
    try:
        with open(SCRAPE_RESULT_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception as e:
        logger.warning("Could not write scrape result: %s", e)


def run_scraper_pipeline(
    output_path: str = "schemes_data.json",
    test_mode: bool = False,
    headless: bool = True,
) -> list[dict[str, Any]]:
    """
    Try Selenium scraping first. If we get enough schemes, save to output_path and do NOT create manual_schemes.json.
    If scraping fails or yields < MIN_SCHEMES_FROM_SCRAPE, use manual data and save manual_schemes.json.
    Writes scrape_result.json so you can check if scraping worked and what percent of target was reached.
    """
    schemes = scrape_with_selenium(limit=TARGET_SCHEMES, test_mode=test_mode, headless=headless)
    scraped_count = len(schemes)

    if scraped_count < MIN_SCHEMES_FROM_SCRAPE:
        _log(f"Scraping yielded {scraped_count} schemes; using manual fallback ({len(get_manual_schemes())} schemes)")
        schemes = get_manual_schemes()
        save_schemes_json(schemes, "manual_schemes.json")
        logger.info("Saved fallback data to manual_schemes.json")
        source = "manual"
    else:
        logger.info("Scraping succeeded: %d schemes; not creating manual_schemes.json", scraped_count)
        source = "scraped"

    schemes = clean_and_validate(schemes)
    save_schemes_json(schemes, output_path)
    logger.info("Saved %d schemes to %s", len(schemes), output_path)

    _write_scrape_result(
        source=source,
        scraped_count=scraped_count,
        target=TARGET_SCHEMES,
        final_scheme_count=len(schemes),
    )
    return schemes


# ---------------------------------------------------------------------------
# Load / save (for CLI and pipeline)
# ---------------------------------------------------------------------------
def load_schemes(path: str = "schemes_data.json") -> list[dict[str, Any]]:
    """Load schemes from JSON file."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("schemes", data) if isinstance(data, dict) else data
    except FileNotFoundError:
        logger.warning("File not found: %s; returning manual schemes", path)
        return get_manual_schemes()
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", path, e)
        return get_manual_schemes()


def save_schemes(schemes: list[dict[str, Any]], path: str = "schemes_data.json") -> None:
    """Save schemes to JSON file."""
    save_schemes_json(schemes, path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    test_mode = "--test" in sys.argv or "-t" in sys.argv
    argv = [a for a in sys.argv[1:] if a not in ("--test", "-t")]
    out = argv[0] if argv else "schemes_data.json"

    schemes = run_scraper_pipeline(output_path=out, test_mode=test_mode, headless=True)
    from data_cleaner import get_summary_stats

    stats = get_summary_stats(schemes)
    logger.info("Summary: %s", json.dumps(stats, indent=2))

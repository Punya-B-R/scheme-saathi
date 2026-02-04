"""
Collect ALL scheme detail URLs from the
`Agriculture, Rural & Environment` category on MyScheme.gov.in
using undetected-chromedriver + pagination.
"""

import json
import logging
import random
import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agriculture_scraping.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def setup_driver(headless: bool = False):
    """
    Setup Chrome with anti-detection-style options using webdriver-manager.

    We avoid undetected_chromedriver here because it bundles a fixed
    ChromeDriver (145) that mismatches your installed Chrome (144),
    causing the `session not created` error you saw. webdriver-manager
    instead downloads the matching driver for your Chrome version.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()

    if headless:
        options.add_argument("--headless=new")

    # Anti-detection measures (keep same flags)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    user_agents = [
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(45)  # Longer timeout for slow pages
    driver.implicitly_wait(5)

    return driver


def extract_scheme_urls_from_current_page(driver) -> set[str]:
    """
    Extract all scheme detail page URLs from the current page.
    Try multiple selector strategies to ensure we catch all URLs.
    """
    urls: set[str] = set()

    # Strategy 1: Direct href matching for scheme URLs
    selectors = [
        "//a[contains(@href, '/schemes/')]",
        "//a[contains(@href, '/scheme/')]",
        "//a[contains(@href, 'scheme-details')]",
        "//a[contains(@href, 'myscheme.gov.in/schemes')]",
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                href = elem.get_attribute("href")
                if href and "scheme" in href.lower() and "myscheme.gov.in" in href:
                    clean_url = href.split("?")[0].split("#")[0]
                    urls.add(clean_url)
        except Exception as e:
            logger.debug("Selector '%s' failed: %s", selector, e)
            continue

    # Strategy 2: Find scheme cards/containers and extract links
    card_selectors = [
        "//div[contains(@class, 'scheme')]//a",
        "//div[contains(@class, 'card')]//a",
        "//article//a",
        "//li[contains(@class, 'scheme')]//a",
    ]

    for selector in card_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                href = elem.get_attribute("href")
                if href and "scheme" in href.lower() and "myscheme.gov.in" in href:
                    clean_url = href.split("?")[0].split("#")[0]
                    urls.add(clean_url)
        except Exception:
            continue

    # Strategy 3: Get all links on page and filter for scheme URLs
    try:
        all_links = driver.find_elements(By.TAG_NAME, "a")
        for link in all_links:
            href = link.get_attribute("href")
            if href and "/schemes/" in href and "myscheme.gov.in" in href:
                clean_url = href.split("?")[0].split("#")[0]
                urls.add(clean_url)
    except Exception:
        pass

    return urls


def wait_for_scheme_links(driver, timeout: int = 15) -> None:
    """Wait until at least one scheme link is present (SPA may render after load)."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/schemes/']"))
        )
    except Exception:
        pass
    time.sleep(3)  # Extra for lazy-loaded cards


def build_page_url(base_url: str, page_number: int) -> str:
    """Build URL for a given page (MyScheme may use ?page= or &page= or /page/N)."""
    if page_number <= 1:
        return base_url
    if "?" in base_url:
        return f"{base_url}&page={page_number}"
    return f"{base_url}?page={page_number}"


def navigate_to_next_page(driver, current_page: int, base_url: str) -> bool:
    """
    Navigate to the next pagination page.
    Prefer URL-based navigation so we actually load new content; fallback to Next click.
    Returns True if we navigated, False if no next page.
    """
    next_page_number = current_page + 1

    # Strategy 1 (preferred for this site): Click specific page number (e.g. "2", "3")
    # Your DOM uses <li>2</li> for page buttons, so we target that explicitly.
    page_number_selectors = [
        f"//a[text()='{next_page_number}']",
        f"//button[text()='{next_page_number}']",
        f"//a[@aria-label='Page {next_page_number}']",
        f"//a[contains(@class, 'page') and text()='{next_page_number}']",
        f"//li//a[text()='{next_page_number}']",
        # Your actual DOM: <li ...>2</li>
        f"//li[normalize-space(text())='{next_page_number}']",
    ]
    for selector in page_number_selectors:
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", next_button
            )
            time.sleep(1)
            next_button.click()
            logger.info("✓ Clicked page %s button", next_page_number)
            time.sleep(5)
            wait_for_scheme_links(driver, timeout=15)
            return True
        except Exception:
            continue
    # Strategy 2: Click "Next" arrow/button
    next_arrow_selectors = [
        "//a[@aria-label='Next']",
        "//button[@aria-label='Next']",
        "//a[contains(@class, 'next')]",
        "//button[contains(@class, 'next')]",
        "//a[contains(., 'Next')]",
        "//button[contains(., 'Next')]",
        "//a[contains(., '›')]",
        "//button[contains(., '›')]",
        "//li[contains(@class, 'next')]//a",
    ]
    for selector in next_arrow_selectors:
        try:
            next_arrow = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            classes = next_arrow.get_attribute("class") or ""
            disabled = next_arrow.get_attribute("disabled") or next_arrow.get_attribute(
                "aria-disabled"
            )
            if "disabled" in classes.lower() or disabled:
                logger.info("Next button is disabled - reached last page")
                return False
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", next_arrow
            )
            time.sleep(1)
            next_arrow.click()
            logger.info("✓ Clicked 'Next' arrow button")
            time.sleep(5)
            wait_for_scheme_links(driver, timeout=15)
            return True
        except Exception:
            continue

    # Strategy 3 (fallback): URL-based pagination – may or may not be supported
    url_variants = [
        build_page_url(base_url, next_page_number),  # ?page=N or &page=N
        f"{base_url.rstrip('/')}/page/{next_page_number}",  # /page/N
    ]
    for next_url in url_variants:
        try:
            logger.info("Loading page %s via URL: %s", next_page_number, next_url)
            driver.get(next_url)
            time.sleep(5)
            wait_for_scheme_links(driver, timeout=15)
            return True
        except Exception as e:
            logger.debug("URL variant %s failed: %s", next_url, e)
            continue

    logger.info("✗ No next page navigation found")
    return False


def _category_name_to_slug(name: str) -> str:
    """Convert category display name to URL slug (e.g. 'Rural & Environment' -> 'Rural%20&%20Environment')."""
    return name.replace(", ", ",").replace(" ", "%20")


# MyScheme category URL slugs (path after /search/category/)
CATEGORY_SLUGS: dict[str, str] = {
    "Agriculture, Rural & Environment": "Agriculture,Rural%20&%20Environment",
    "Education & Learning": "Education%20%26%20Learning",
    "Health & Wellness": "Health%20&%20Wellness",
    "Social Welfare & Empowerment": "Social%20Welfare%20%26%20Empowerment",
    "Women & Child": "Women%20%26%20Child",
    "Business & Entrepreneurship": "Business%20%26%20Entrepreneurship",
    "Skills & Employment": "Skills%20%26%20Employment",
    "Housing & Shelter": "Housing%20&%20Shelter",
    "Banking, Financial Services and Insurance": "Banking%2C%20Financial%20Services%20and%20Insurance",
    "Science, IT & Communications": "Science,%20IT%20&%20Communications",
    "Public Safety, Law & Justice": "Public%20Safety,Law%20&%20Justice",
    "Utility & Sanitation": "Utility%20&%20Sanitation",
    "Travel & Tourism": "Travel%20&%20Tourism",
    "Transport & Infrastructure": "Transport%20&%20Infrastructure",
    "Sports & Culture": "Sports%20&%20Culture",
}


def collect_urls_for_category(
    driver,
    base_url: str,
    *,
    start_page: int = 1,
    end_page: int = 100,
    delay_between_pages: float = 15.0,
    max_consecutive_empty: int = 3,
) -> set[str]:
    """
    Collect scheme URLs from a category listing with pagination.
    Uses click-based pagination (li with page number). Optional start_page/end_page for chunked runs.
    """
    collected_urls: set[str] = set()
    page_number = 1
    consecutive_empty_pages = 0

    logger.info("Starting URL collection from: %s (pages %s-%s)", base_url, start_page, end_page)

    driver.get(base_url)
    time.sleep(5)

    # If start_page > 1, click through to that page first (don't collect until we're there)
    while page_number < start_page:
        next_page_found = navigate_to_next_page(driver, page_number, base_url)
        if not next_page_found:
            logger.warning("Could not reach start_page %s; starting collection from page %s", start_page, page_number)
            break
        page_number += 1
        time.sleep(max(2, delay_between_pages * 0.5))

    while page_number <= end_page:
        logger.info("=" * 60)
        logger.info("Processing Page %s", page_number)
        logger.info("=" * 60)

        try:
            wait_for_scheme_links(driver, timeout=15)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            time.sleep(2)

            page_urls = extract_scheme_urls_from_current_page(driver)
            new_urls_count = len(page_urls - collected_urls)
            collected_urls.update(page_urls)

            logger.info(
                "✓ Page %s: Found %s URLs on page, %s new URLs",
                page_number,
                len(page_urls),
                new_urls_count,
            )
            logger.info("✓ Total unique URLs so far: %s", len(collected_urls))
            if len(page_urls) == 0:
                logger.info("Current URL (no scheme links): %s", driver.current_url)

            if new_urls_count == 0:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= max_consecutive_empty:
                    logger.info("Stopping: %s consecutive pages with no new URLs", max_consecutive_empty)
                    break
            else:
                consecutive_empty_pages = 0

            next_page_found = navigate_to_next_page(driver, page_number, base_url)
            if not next_page_found:
                logger.info("No more pagination. Collection complete.")
                break

            page_number += 1
            delay = random.uniform(delay_between_pages * 0.8, delay_between_pages * 1.2)
            logger.info("Waiting %.1fs before next page...", delay)
            time.sleep(delay)

        except Exception as e:
            logger.error("Error on page %s: %s", page_number, e)
            try:
                driver.refresh()
                time.sleep(5)
            except Exception:
                break

    logger.info("Category collection complete: %s unique URLs from %s pages", len(collected_urls), page_number)
    return collected_urls


def collect_agriculture_urls_with_pagination(driver) -> set[str]:
    """Collect from Agriculture category (default 1–100, delay 15s). Kept for backward compatibility."""
    base_url = (
        "https://www.myscheme.gov.in/search/category/"
        "Agriculture,Rural%20&%20Environment"
    )
    return collect_urls_for_category(
        driver, base_url, start_page=1, end_page=100, delay_between_pages=15.0
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Collect scheme URLs from MyScheme.gov.in category")
    parser.add_argument("--start-page", type=int, default=1, help="First page to collect (default 1)")
    parser.add_argument("--end-page", type=int, default=100, help="Last page to collect (default 100)")
    parser.add_argument("--delay", type=float, default=15.0, help="Seconds between pages (default 15)")
    parser.add_argument("--category", type=str, default="Agriculture, Rural & Environment", help="Category name")
    parser.add_argument("--output", type=str, default="agriculture_urls.json", help="Output JSON path")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    args = parser.parse_args()

    category_name = args.category
    slug = CATEGORY_SLUGS.get(category_name)
    if not slug:
        slug = _category_name_to_slug(category_name)
    base_url = f"https://www.myscheme.gov.in/search/category/{slug}"

    logger.info("=" * 70)
    logger.info("SCHEME URL COLLECTION - MyScheme.gov.in")
    logger.info("=" * 70)
    logger.info("Category: %s | Pages %s–%s | Delay %.1fs", category_name, args.start_page, args.end_page, args.delay)
    logger.info("=" * 70)

    driver = None
    collected: set[str] = set()

    try:
        driver = setup_driver(headless=args.headless)
        logger.info("✓ Browser initialized")

        collected = collect_urls_for_category(
            driver,
            base_url,
            start_page=args.start_page,
            end_page=args.end_page,
            delay_between_pages=args.delay,
        )

        logger.info("")
        logger.info("=" * 70)
        logger.info("COLLECTION COMPLETE!")
        logger.info("=" * 70)
        logger.info("Total URLs collected: %s", len(collected))
        logger.info("=" * 70)

        output_data = {
            "category": category_name,
            "collected_count": len(collected),
            "urls": sorted(list(collected)),
            "collected_at": datetime.now().isoformat(),
            "collection_metadata": {
                "start_page": args.start_page,
                "end_page": args.end_page,
                "base_url": base_url,
            },
        }

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info("✓ URLs saved to: %s", args.output)
        logger.info("Sample URLs (first 5):")
        for i, url in enumerate(sorted(list(collected))[:5], 1):
            logger.info("  %s. %s", i, url)

    except KeyboardInterrupt:
        logger.info("")
        logger.warning("⚠ Collection interrupted by user")
        logger.info("Partial results: %s URLs collected", len(collected))

        if collected:
            with open("agriculture_urls_partial.json", "w", encoding="utf-8") as f:
                json.dump(
                    {"urls": list(collected), "count": len(collected), "status": "interrupted"},
                    f,
                    indent=2,
                )
            logger.info("✓ Partial results saved to: agriculture_urls_partial.json")

    except Exception as e:  # noqa: BLE001
        logger.error("✗ Fatal error during collection: %s", e)
        import traceback

        logger.error("%s", traceback.format_exc())

    finally:
        if driver:
            logger.info("Closing browser...")
            try:
                driver.quit()
                logger.info("✓ Browser closed")
            except Exception:
                pass


if __name__ == "__main__":
    main()


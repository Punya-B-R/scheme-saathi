"""
Selenium helper utilities for Scheme Saathi scrapers.

Reuses the existing `setup_driver` from agriculture_detail_scraper so that
all scrapers share the same Chrome / webdriver-manager configuration.
"""

import logging
import time
from typing import Optional

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from agriculture_detail_scraper import setup_driver  # type: ignore

logger = logging.getLogger(__name__)


def create_driver(headless: bool = True):
    """Create a Selenium driver using the shared setup."""
    return setup_driver(headless=headless)


def get_soup(driver, url: str, wait_selector: Optional[tuple] = None, timeout: int = 25) -> BeautifulSoup:
    """
    Navigate to URL and return a BeautifulSoup of the rendered page.

    wait_selector: optional (By, locator) tuple to wait for before parsing.
    For MyScheme scheme pages we want to wait for a real scheme title,
    not just the shell / nav.
    """
    logger.info("Loading URL: %s", url)
    driver.get(url)

    # Default: wait for an <h1> that is NOT the generic 'Sign In' header
    default_selector = (By.XPATH, "//h1[not(contains(., 'Sign In'))]")
    selector = wait_selector or default_selector

    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located(selector))
    except TimeoutException:
        logger.error("Timeout waiting for scheme content on %s", url)
        raise
    except Exception:
        logger.warning("Timeout waiting for selector %s on %s", selector, url)

    # Extra time for JS to render details
    time.sleep(8)

    # Scroll a bit to trigger any lazy-loading
    try:
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(1.5)
        driver.execute_script("window.scrollTo(0, 1200);")
        time.sleep(1.5)
    except Exception:
        pass

    html = driver.page_source

    # Detect shell / error page and signal failure so caller can retry
    head = html[:2000]
    if ("Something went wrong" in head) or ("Enter scheme name to search" in head):
        logger.error("Page appears to be error/shell content on %s", url)
        raise RuntimeError("MyScheme shell / error page, scheme not loaded")

    return BeautifulSoup(html, "html.parser")


def safe_find_text(soup: BeautifulSoup, selectors: list[tuple[str, str]]) -> str:
    """
    Try multiple CSS selectors / XPATH-like queries and return first non-empty text.
    selectors: list of (method, selector) where method is 'css' or 'xpath'.
    """
    from selenium.webdriver.remote.webdriver import WebDriver  # only for type hints

    # This helper is mainly for Selenium-based extraction; for now for BS4 we only support CSS.
    for method, sel in selectors:
        if method != "css":
            continue
        el = soup.select_one(sel)
        if el:
            text = " ".join(el.get_text(separator=" ").split())
            if text:
                return text
    return ""


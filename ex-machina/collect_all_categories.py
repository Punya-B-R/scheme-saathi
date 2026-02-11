"""
Collect scheme URLs from MULTIPLE MyScheme.gov.in categories to reach 750+ schemes.
Runs one category at a time with long delays to reduce rate limiting.
Merge results into all_scheme_urls.json.
"""

import json
import logging
import time
from datetime import datetime

from agriculture_url_collector import (
    CATEGORY_SLUGS,
    collect_urls_for_category,
    setup_driver,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("all_categories_scraping.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

BASE = "https://www.myscheme.gov.in/search/category"
TARGET_TOTAL = 750
PAGES_PER_CATEGORY = 25   # cap pages per category to avoid rate limit
DELAY_BETWEEN_PAGES = 18  # seconds
DELAY_BETWEEN_CATEGORIES = 180  # 3 minutes between categories


def main() -> None:
    logger.info("=" * 70)
    logger.info("MULTI-CATEGORY URL COLLECTION - Target %s+ schemes", TARGET_TOTAL)
    logger.info("=" * 70)

    all_urls: set[str] = set()
    categories_done: list[tuple[str, int]] = []

    driver = None
    try:
        driver = setup_driver(headless=False)
        logger.info("✓ Browser initialized")

        for category_name, slug in CATEGORY_SLUGS.items():
            if len(all_urls) >= TARGET_TOTAL:
                logger.info("✓ Reached target %s URLs. Stopping.", TARGET_TOTAL)
                break

            base_url = f"{BASE}/{slug}"
            logger.info("")
            logger.info(">>> Category: %s", category_name)
            logger.info(">>> Total unique URLs so far: %s", len(all_urls))

            try:
                urls = collect_urls_for_category(
                    driver,
                    base_url,
                    start_page=1,
                    end_page=PAGES_PER_CATEGORY,
                    delay_between_pages=DELAY_BETWEEN_PAGES,
                    max_consecutive_empty=3,
                )
                new_count = len(urls - all_urls)
                all_urls.update(urls)
                categories_done.append((category_name, len(urls)))
                logger.info(">>> Category %s: collected %s URLs (%s new). Total: %s", category_name, len(urls), new_count, len(all_urls))
            except Exception as e:
                logger.error(">>> Category %s failed: %s", category_name, e)
                continue

            if len(all_urls) >= TARGET_TOTAL:
                logger.info("✓ Reached target %s URLs.", TARGET_TOTAL)
                break

            logger.info("Waiting %s seconds before next category...", DELAY_BETWEEN_CATEGORIES)
            time.sleep(DELAY_BETWEEN_CATEGORIES)

    except KeyboardInterrupt:
        logger.warning("⚠ Interrupted by user. Saving partial results.")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    # Save merged result
    out = {
        "target_total": TARGET_TOTAL,
        "collected_count": len(all_urls),
        "categories_scraped": categories_done,
        "urls": sorted(list(all_urls)),
        "collected_at": datetime.now().isoformat(),
    }
    with open("all_scheme_urls.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    logger.info("")
    logger.info("=" * 70)
    logger.info("MULTI-CATEGORY COLLECTION COMPLETE")
    logger.info("=" * 70)
    logger.info("Total unique URLs: %s", len(all_urls))
    logger.info("Target was: %s+", TARGET_TOTAL)
    logger.info("Saved to: all_scheme_urls.json")
    for name, count in categories_done:
        logger.info("  %s: %s URLs", name, count)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()

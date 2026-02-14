"""
Collect scheme URLs from MyScheme.gov.in for the pipeline.

Parameterized version of collect_all_categories: accepts --output, --max-categories,
--pages-per-category for pipeline runs.

Usage:
    python collect_urls_for_pipeline.py --output data/pipeline_urls/all_scheme_urls.json --max-categories 2 --pages-per-category 3 --headless
"""

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from agriculture_url_collector import (
    CATEGORY_SLUGS,
    collect_urls_for_category,
    setup_driver,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

BASE = "https://www.myscheme.gov.in/search/category"
DELAY_BETWEEN_PAGES = 18
DELAY_BETWEEN_CATEGORIES = 120


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect scheme URLs from MyScheme.gov.in for pipeline"
    )
    parser.add_argument("--output", "-o", required=True, help="Output JSON path")
    parser.add_argument("--max-categories", type=int, default=16)
    parser.add_argument("--pages-per-category", type=int, default=25)
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-headless", action="store_false", dest="headless")
    args = parser.parse_args()

    all_urls: set[str] = set()
    categories_done: list[tuple[str, int]] = []
    driver = None

    try:
        driver = setup_driver(headless=args.headless)
        logger.info("Browser initialized")

        categories = list(CATEGORY_SLUGS.items())[: args.max_categories]
        for i, (category_name, slug) in enumerate(categories):
            base_url = f"{BASE}/{slug}"
            logger.info(">>> Category %s/%s: %s", i + 1, len(categories), category_name)

            try:
                urls = collect_urls_for_category(
                    driver,
                    base_url,
                    start_page=1,
                    end_page=args.pages_per_category,
                    delay_between_pages=DELAY_BETWEEN_PAGES,
                    max_consecutive_empty=3,
                )
                new_count = len(urls - all_urls)
                all_urls.update(urls)
                categories_done.append((category_name, len(urls)))
                logger.info(
                    ">>> Collected %s URLs (%s new). Total: %s",
                    len(urls),
                    new_count,
                    len(all_urls),
                )
            except Exception as e:
                logger.error(">>> Category %s failed: %s", category_name, e)

            if i < len(categories) - 1:
                logger.info("Waiting %s s before next category...", DELAY_BETWEEN_CATEGORIES)
                time.sleep(DELAY_BETWEEN_CATEGORIES)

    except KeyboardInterrupt:
        logger.warning("Interrupted. Saving partial results.")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "collected_count": len(all_urls),
        "categories_scraped": categories_done,
        "urls": sorted(list(all_urls)),
        "collected_at": datetime.now().isoformat(),
        "source": "selenium",
        "config": {
            "max_categories": args.max_categories,
            "pages_per_category": args.pages_per_category,
        },
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    logger.info("Saved %s URLs to %s", len(all_urls), out_path)


if __name__ == "__main__":
    main()

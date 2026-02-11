"""
Collect scheme URLs for the category "Banking,Financial Services and Insurance" from MyScheme.gov.in (32 pages).
Saves to data/banking_financial_services_insurance_urls.json.

Run from project root:
  python collect_banking_financial_urls.py
"""

import json
import os
import sys
from datetime import datetime

os.makedirs("data", exist_ok=True)

from agriculture_url_collector import (
    collect_urls_for_category,
    setup_driver,
)

CATEGORY_NAME = "Banking,Financial Services and Insurance"
# Use your exact category URL
BASE_URL = "https://www.myscheme.gov.in/search/category/Banking,Financial%20Services%20and%20Insurance"
OUTPUT_PATH = "data/banking_financial_services_insurance_urls.json"


def main():
    base_url = BASE_URL

    print(f"Category: {CATEGORY_NAME}")
    print(f"URL: {base_url}")
    print(f"Output: {OUTPUT_PATH}")
    print("Starting browser...")

    driver = None
    collected = set()
    try:
        driver = setup_driver(headless=False)
        collected = collect_urls_for_category(
            driver,
            base_url,
            start_page=1,
            end_page=50,          # enough to cover 32 pages
            delay_between_pages=12.0,
            max_consecutive_empty=1,
        )
        urls = sorted(set(collected))

        out = {
            "category": CATEGORY_NAME,
            "collected_count": len(urls),
            "urls": urls,
            "collected_at": datetime.now().isoformat(),
        }
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

        print(f"\nDone. Collected {len(urls)} URLs -> {OUTPUT_PATH}")
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted.")
        if collected:
            out_path = "data/banking_financial_services_insurance_urls_partial.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "category": CATEGORY_NAME,
                        "urls": sorted(collected),
                        "count": len(collected),
                        "status": "interrupted",
                    },
                    f,
                    indent=2,
                )
            print(f"Partial results ({len(collected)} URLs) saved to {out_path}")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    sys.exit(main())
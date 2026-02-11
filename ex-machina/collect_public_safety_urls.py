"""
Collect scheme URLs for the category "Public Safety, Law & Justice" from MyScheme.gov.in
(29 schemes). Saves to data/public_safety_law_justice_urls.json.

Run from project root:
  python collect_public_safety_urls.py

If the category page does not load or returns 0 URLs, the site may use a different slug.
In that case, open MyScheme.gov.in, select "Public Safety, Law & Justice", copy the
URL from the address bar, and share it so we can fix the slug.
"""

import json
import os
import sys
from datetime import datetime

# Ensure data/ exists
os.makedirs("data", exist_ok=True)

from agriculture_url_collector import (
    CATEGORY_SLUGS,
    collect_urls_for_category,
    setup_driver,
)

CATEGORY_NAME = "Public Safety, Law & Justice"
BASE_URL = "https://www.myscheme.gov.in/search/category"
OUTPUT_PATH = "data/public_safety_law_justice_urls.json"


def main():
    slug = CATEGORY_SLUGS.get(CATEGORY_NAME)
    if not slug:
        from agriculture_url_collector import _category_name_to_slug
        slug = _category_name_to_slug(CATEGORY_NAME)
    base_url = f"{BASE_URL}/{slug}"

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
            end_page=3,
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
        if len(urls) != 29:
            print(f"(Expected 29 schemes; if count is wrong, the category slug may need to be updated.)")
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted.")
        if collected:
            out_path = "data/public_safety_law_justice_urls_partial.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump({"category": CATEGORY_NAME, "urls": sorted(collected), "count": len(collected), "status": "interrupted"}, f, indent=2)
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

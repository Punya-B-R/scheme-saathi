"""
Validation script for agriculture_urls.json
Checks count, duplicates, domain, and basic URL pattern.
"""

import json


def validate_urls() -> None:
    """
    Validate the collected URLs for quality and correctness.
    """
    with open("agriculture_urls.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    urls: list[str] = data.get("urls", [])

    print(f"Total URLs: {len(urls)}")
    print("Target: 824")
    if 824:
        print(f"Success rate: {len(urls) / 824 * 100:.1f}%")
    print("")

    # Check for duplicates
    unique_urls = set(urls)
    if len(urls) != len(unique_urls):
        print(f"⚠ Warning: {len(urls) - len(unique_urls)} duplicate URLs found")
    else:
        print("✓ No duplicates")

    # Check URL patterns
    scheme_urls = [u for u in urls if "/schemes/" in u or "/scheme/" in u]
    print(f"✓ URLs with 'scheme' pattern: {len(scheme_urls)}")

    # Check domain
    myscheme_urls = [u for u in urls if "myscheme.gov.in" in u]
    print(f"✓ URLs from myscheme.gov.in: {len(myscheme_urls)}")

    # Sample URLs
    print("\nFirst 10 URLs:")
    for i, url in enumerate(urls[:10], 1):
        print(f"{i}. {url}")


if __name__ == "__main__":
    validate_urls()


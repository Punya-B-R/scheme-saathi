"""
Fetch scheme URLs from MyScheme.gov.in for the auto-update pipeline.

Stage 1 of the pipeline: discovers new scheme URLs, writes to data/pipeline_urls/all_scheme_urls.json.
Stage 2 (scraping) uses these URLs to scrape scheme details.

Modes:
- requests: Try HTTP requests to category pages (fast, may fail on SPA).
- selenium: Use ex-machina Selenium collector (reliable, requires Chrome).

Usage:
    python -m backend.pipeline.fetch_scheme_urls [--config path] [--test-mode]
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
CONFIG_PATH = BACKEND_ROOT / "pipeline" / "pipeline_config.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "pipeline_urls" / "all_scheme_urls.json"
EX_MACHINA_ROOT = PROJECT_ROOT / "ex-machina"
COLLECT_SCRIPT = EX_MACHINA_ROOT / "collect_urls_for_pipeline.py"

# MyScheme category slugs (mirrors ex-machina/agriculture_url_collector)
CATEGORY_SLUGS = {
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

logger = logging.getLogger("pipeline.fetch_urls")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


def _load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as f:
        return json.load(f)


def _extract_urls_from_html(html: str) -> set[str]:
    """Extract scheme URLs from MyScheme HTML (works if page is server-rendered)."""
    urls: set[str] = set()
    # Pattern for scheme detail URLs
    pattern = re.compile(
        r'https?://(?:www\.)?myscheme\.gov\.in/schemes/[^\s"\'<>?#]+',
        re.IGNORECASE
    )
    for m in pattern.finditer(html):
        raw = m.group(0)
        clean = raw.split("?")[0].split("#")[0].rstrip("/")
        if "/schemes/" in clean and len(clean) > 50:
            urls.add(clean)
    return urls


def fetch_via_requests(
    max_categories: int,
    pages_per_category: int,
) -> set[str]:
    """Try to fetch scheme URLs via HTTP requests (no Selenium)."""
    if not HAS_REQUESTS:
        logger.warning("requests not installed; skipping requests-based fetch")
        return set()

    base = "https://www.myscheme.gov.in/search/category"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    all_urls: set[str] = set()
    categories = list(CATEGORY_SLUGS.items())[:max_categories]

    for cat_name, slug in categories:
        logger.info("Fetching category: %s", cat_name)
        try:
            for page in range(1, pages_per_category + 1):
                if page == 1:
                    url = f"{base}/{slug}"
                else:
                    url = f"{base}/{slug}?page={page}"
                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                page_urls = _extract_urls_from_html(r.text)
                new = page_urls - all_urls
                all_urls.update(page_urls)
                logger.info("  Page %s: %s URLs (%s new) | Total: %s", page, len(page_urls), len(new), len(all_urls))
                if not page_urls:
                    break
        except Exception as e:
            logger.warning("  Error: %s", e)
            continue

    return all_urls


def fetch_via_selenium(
    max_categories: int,
    pages_per_category: int,
    headless: bool = True,
) -> set[str]:
    """Fetch scheme URLs via ex-machina Selenium collector."""
    if not COLLECT_SCRIPT.exists():
        logger.error("Selenium collector not found: %s", COLLECT_SCRIPT)
        return set()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_out = EX_MACHINA_ROOT / "all_scheme_urls_pipeline.json"

    cmd = [
        sys.executable,
        str(COLLECT_SCRIPT),
        "--output", str(temp_out),
        "--max-categories", str(max_categories),
        "--pages-per-category", str(pages_per_category),
    ]
    if headless:
        cmd.append("--headless")

    logger.info("Running Selenium collector: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            cwd=str(EX_MACHINA_ROOT),
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hours max
            check=False,
        )
        if result.returncode != 0:
            logger.warning("Collector stderr: %s", (result.stderr or "")[-1000:])
            logger.warning("Collector stdout: %s", (result.stdout or "")[-1000:])

        if temp_out.exists():
            with temp_out.open(encoding="utf-8") as f:
                data = json.load(f)
            urls = set(data.get("urls", []))
            # Copy to pipeline output location
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            data["collected_at"] = datetime.now().isoformat()
            data["source"] = "selenium"
            with OUTPUT_PATH.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            try:
                temp_out.unlink()
            except OSError:
                pass
            return urls
    except subprocess.TimeoutExpired:
        logger.error("Selenium collector timed out")
    except Exception as e:
        logger.exception("Selenium fetch failed: %s", e)

    return set()


def run(config_path: Path, test_mode: bool = False) -> dict:
    """Run URL fetch stage. Returns summary dict."""
    config = _load_config(config_path)
    uf = config.get("url_fetch", {})
    if not uf.get("run", False):
        return {"skipped": True, "reason": "url_fetch.run=false"}

    max_cat = uf.get("max_categories", 16)
    pages_per = uf.get("pages_per_category", 25)
    use_selenium = uf.get("use_selenium", True)
    try_requests_first = uf.get("try_requests_first", True)
    headless = uf.get("headless", True)

    if test_mode:
        max_cat = min(2, max_cat)
        pages_per = min(3, pages_per)
        logger.info("Test mode: max_categories=%s, pages_per_category=%s", max_cat, pages_per)

    all_urls: set[str] = set()

    if try_requests_first and HAS_REQUESTS:
        logger.info("Attempting requests-based fetch...")
        all_urls = fetch_via_requests(max_cat, pages_per)
        if len(all_urls) < 10:
            logger.warning("Requests fetched few URLs (%s); will use Selenium if configured", len(all_urls))
            all_urls = set()

    if (not all_urls or len(all_urls) < 10) and use_selenium:
        logger.info("Using Selenium-based fetch...")
        sel_urls = fetch_via_selenium(max_cat, pages_per, headless=headless)
        all_urls = sel_urls if sel_urls else all_urls

    if not all_urls:
        return {
            "skipped": False,
            "status": "no_urls",
            "count": 0,
            "output_path": str(OUTPUT_PATH),
        }

    # Ensure output exists (Selenium path writes it; requests path does not)
    if not OUTPUT_PATH.exists() and all_urls:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        out_data = {
            "urls": sorted(list(all_urls)),
            "collected_count": len(all_urls),
            "collected_at": datetime.now().isoformat(),
            "source": "requests",
        }
        with OUTPUT_PATH.open("w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2, ensure_ascii=False)

    return {
        "skipped": False,
        "status": "ok",
        "count": len(all_urls),
        "output_path": str(OUTPUT_PATH),
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Fetch scheme URLs from MyScheme.gov.in")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Pipeline config path")
    parser.add_argument("--test-mode", action="store_true", help="Limit categories and pages")
    args = parser.parse_args()

    result = run(Path(args.config), test_mode=args.test_mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("status") in ("ok", "skipped") else 1)


if __name__ == "__main__":
    main()

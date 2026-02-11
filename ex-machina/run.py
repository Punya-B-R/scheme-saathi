"""
Scheme Saathi - Main runner: run pipeline, search, update scheme, summary statistics.
Usage:
  python run.py                    # Run full pipeline and print stats
  python run.py --search "farmer"  # Search schemes
  python run.py --stats            # Load and print stats only
  python run.py --update PM-KISAN-001 --field benefits --value "..."  # Update one scheme (example)
"""

import argparse
import json
import sys

from data_cleaner import clean_and_validate, get_summary_stats, save_schemes_json
from manual_data import get_manual_schemes

SCRAPE_RESULT_PATH = "scrape_result.json"


def _print_scrape_status() -> None:
    """Print last scraping result (from scrape_result.json) so user knows if scraping worked and percent."""
    try:
        with open(SCRAPE_RESULT_PATH, encoding="utf-8") as f:
            r = json.load(f)
    except FileNotFoundError:
        print("No scrape result yet. Run: python run.py --scrape")
        return
    except json.JSONDecodeError:
        print("scrape_result.json is invalid or empty.")
        return

    source = r.get("source", "?")
    scraped = r.get("scraped_count", 0)
    target = r.get("target", 50)
    percent = r.get("percent_of_target", 0)
    final = r.get("final_scheme_count", 0)
    msg = r.get("message", "")

    print("\n" + "=" * 60)
    print("SCRAPING RESULT")
    print("=" * 60)
    if source == "scraped":
        print("Status:  SUCCESS (data from MyScheme.gov.in)")
    else:
        print("Status:  FALLBACK (data from manual_data.py)")
    print(f"Scraped: {scraped} schemes")
    print(f"Target:  {target} schemes")
    print(f"Percent: {percent}% of target")
    print(f"Final:   {final} schemes in schemes_data.json")
    print("-" * 60)
    print(msg)
    print("=" * 60 + "\n")


def _load_schemes(path: str) -> list:
    """Load schemes from JSON file; fall back to manual data if file missing or invalid."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("schemes", data) if isinstance(data, dict) else data
    except (FileNotFoundError, json.JSONDecodeError):
        return get_manual_schemes()


def main() -> None:
    # Ensure UTF-8 stdout on Windows for JSON with Unicode (e.g. ₹)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    parser = argparse.ArgumentParser(description="Scheme Saathi - Run pipeline, search, update, stats")
    parser.add_argument("--output", "-o", default="schemes_data.json", help="Output JSON path")
    parser.add_argument("--scrape", action="store_true", help="Run scraper pipeline (scrape or fallback, clean, save)")
    parser.add_argument("--search", "-q", type=str, help="Search schemes by text query")
    parser.add_argument("--category", "-c", type=str, help="Filter by category (for search)")
    parser.add_argument("--occupation", type=str, help="Filter by occupation (for search)")
    parser.add_argument("--stats", action="store_true", help="Load schemes and print summary statistics")
    parser.add_argument("--update", type=str, metavar="SCHEME_ID", help="Update scheme by scheme_id")
    parser.add_argument("--field", type=str, help="Field to update (with --update)")
    parser.add_argument("--value", type=str, help="Value (string or JSON for object/array; with --update)")
    parser.add_argument("--manual-only", action="store_true", help="Skip scraping; build from manual data only")
    parser.add_argument("--test", "-t", action="store_true", help="Scrape only 5 schemes (test mode)")
    parser.add_argument("--scrape-status", action="store_true", help="Show last scraping result (from scrape_result.json)")
    args = parser.parse_args()

    data_path = args.output

    # Show last scrape result (from file)
    if args.scrape_status:
        _print_scrape_status()
        return

    # Build/load schemes
    if args.scrape:
        from scraper import run_scraper_pipeline

        schemes = run_scraper_pipeline(output_path=data_path, test_mode=args.test, headless=True)
        _print_scrape_status()
    elif args.manual_only:
        schemes = get_manual_schemes()
        schemes = clean_and_validate(schemes)
        save_schemes_json(schemes, data_path)
        save_schemes_json(schemes, "manual_schemes.json")
        print(f"Saved {len(schemes)} manual schemes to {data_path} and manual_schemes.json")
    else:
        schemes = _load_schemes(data_path)

    # Search
    if args.search is not None:
        from data_cleaner import search_schemes

        results = search_schemes(schemes, query=args.search, category=args.category or "", occupation=args.occupation or "")
        # Use ensure_ascii=True so Unicode (e.g. ₹) prints on Windows cp1252
        out = json.dumps({"query": args.search, "count": len(results), "schemes": results}, indent=2, ensure_ascii=True)
        print(out)
        return

    # Update one scheme
    if args.update:
        from data_cleaner import update_scheme

        if not args.field or args.value is None:
            print("--update requires --field and --value", file=sys.stderr)
            sys.exit(1)
        try:
            if args.value.strip().startswith(("[", "{")):
                value = json.loads(args.value)
            else:
                value = args.value
            updates = {args.field: value}
            schemes = update_scheme(schemes, args.update, updates)
            save_schemes_json(schemes, data_path)
            print(f"Updated {args.update} field '{args.field}' and saved to {data_path}")
        except json.JSONDecodeError as e:
            print(f"Invalid --value JSON: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Summary statistics
    if args.stats or (not args.scrape and not args.search and not args.update):
        stats = get_summary_stats(schemes)
        print("Summary statistics:")
        print(json.dumps(stats, indent=2))
        print(f"\nTotal schemes: {stats['total_schemes']}")


if __name__ == "__main__":
    main()

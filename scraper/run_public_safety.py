"""
CLI entrypoint for Public Safety, Law & Justice detail scraper.

Usage:
  python scraper/run_public_safety.py           # full run
  python scraper/run_public_safety.py --test    # first 5 URLs only
  python scraper/run_public_safety.py --resume  # resume from latest checkpoint
"""

from __future__ import annotations

import argparse

from .public_safety_scraper import run_scraper


def main() -> None:
    parser = argparse.ArgumentParser(description="Public Safety, Law & Justice - detail scraper")
    parser.add_argument("--test", action="store_true", help="Scrape only first 5 URLs")
    parser.add_argument("--resume", action="store_true", help="Resume from latest checkpoint")
    args = parser.parse_args()

    run_scraper(test_mode=args.test, resume=args.resume)


if __name__ == "__main__":
    main()


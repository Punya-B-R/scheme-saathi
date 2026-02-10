"""
Transport & Infrastructure detail scraper.

Reads URLs from `data/transport_infrastructure_urls.json`, scrapes each scheme page,
and writes to:

- data/from_urls/transport_infrastructure/transport_infrastructure_schemes.json
- data/from_urls/transport_infrastructure/transport_infrastructure_failed_urls.json
- data/from_urls/transport_infrastructure/transport_infrastructure_stats.json

Checkpoints every 25 schemes under `checkpoints/transport_infrastructure_checkpoint_*.json`.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .extraction.extractor import extract_scheme
from .utils.selenium_helper import create_driver

logger = logging.getLogger(__name__)

CATEGORY_NAME = "Transport & Infrastructure"
INPUT_PRIMARY = Path("data/transport_infrastructure_urls.json")
OUT_DIR = Path("data/from_urls/transport_infrastructure")
CHECKPOINT_DIR = Path("checkpoints")
LOG_DIR = Path("logs")
SCHEME_ID_PREFIX = "TI"


@dataclass
class FailedURL:
    url: str
    error: str
    attempts: int
    last_attempt: str


def _load_urls() -> List[str]:
    if not INPUT_PRIMARY.exists():
        raise FileNotFoundError(f"URL file not found: {INPUT_PRIMARY}")

    with INPUT_PRIMARY.open(encoding="utf-8") as f:
        data = json.load(f)
    urls = data.get("urls", data)
    if not isinstance(urls, list):
        urls = list(urls)
    return urls


def _ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _save_checkpoint(
    schemes: List[Dict[str, Any]], processed_indices: List[int], idx: int
) -> None:
    ck = {
        "scraped_count": len(schemes),
        "processed_indices": processed_indices,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    path = CHECKPOINT_DIR / f"transport_infrastructure_checkpoint_{idx}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(ck, f, indent=2, ensure_ascii=False)
    logger.info("Checkpoint saved: %s", path)


def _load_latest_checkpoint(total_urls: int) -> Tuple[set[int], int]:
    ck_files = sorted(CHECKPOINT_DIR.glob("transport_infrastructure_checkpoint_*.json"))
    if not ck_files:
        return set(), -1
    latest = ck_files[-1]
    with latest.open(encoding="utf-8") as f:
        data = json.load(f)
    processed = set(data.get("processed_indices", []))
    last_idx = max(processed) if processed else -1
    logger.info(
        "Resuming from checkpoint %s (last index %s of %s)", latest, last_idx, total_urls
    )
    return processed, last_idx


def run_scraper(test_mode: bool = False, resume: bool = False) -> None:
    _ensure_dirs()

    log_path = LOG_DIR / "transport_infrastructure_scraping.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    urls = _load_urls()
    if test_mode:
        urls = urls[:5]
    total = len(urls)
    logger.info("Loaded %s %s URLs", total, CATEGORY_NAME)

    processed_indices: set[int] = set()
    start_index = 0
    if resume:
        processed_indices, last_idx = _load_latest_checkpoint(total)
        start_index = last_idx + 1

    driver = None
    schemes: List[Dict[str, Any]] = []
    failed: List[FailedURL] = []

    try:
        driver = create_driver(headless=True)
        logger.info("Driver initialised (headless).")

        for idx, url in enumerate(urls):
            if idx < start_index or idx in processed_indices:
                continue

            logger.info("[%s/%s] %s", idx + 1, total, url)
            attempts = 0
            success = False
            while attempts < 3 and not success:
                attempts += 1
                try:
                    scheme = extract_scheme(
                        driver,
                        url,
                        category=CATEGORY_NAME,
                        scheme_id_prefix=SCHEME_ID_PREFIX,
                    )
                    schemes.append(scheme)
                    processed_indices.add(idx)
                    success = True
                except Exception as e:
                    logger.error("Error scraping %s (attempt %s): %s", url, attempts, e)
                    if attempts >= 3:
                        failed.append(
                            FailedURL(
                                url=url,
                                error=str(e),
                                attempts=attempts,
                                last_attempt=datetime.utcnow().isoformat() + "Z",
                            )
                        )

            if (len(processed_indices) % 25) == 0 and processed_indices:
                _save_checkpoint(schemes, sorted(processed_indices), idx)

        logger.info(
            "Scraping complete. Total schemes scraped: %s; failed: %s",
            len(schemes),
            len(failed),
        )

    finally:
        if driver:
            driver.quit()

    total_urls = len(urls)
    success_count = len(schemes)
    failed_count = len(failed)
    avg_quality = (
        sum(s.get("data_quality_score", 0) for s in schemes) / success_count
        if success_count
        else 0
    )

    main_out = {
        "metadata": {
            "category": CATEGORY_NAME,
            "total_schemes": success_count,
            "total_urls": total_urls,
            "successfully_scraped": success_count,
            "failed": failed_count,
            "average_quality_score": round(avg_quality, 2),
            "scraping_date": datetime.utcnow().date().isoformat(),
        },
        "schemes": schemes,
    }
    with (OUT_DIR / "transport_infrastructure_schemes.json").open("w", encoding="utf-8") as f:
        json.dump(main_out, f, indent=2, ensure_ascii=False)

    failed_out = {
        "failed_count": failed_count,
        "urls": [asdict(fu) for fu in failed],
    }
    with (OUT_DIR / "transport_infrastructure_failed_urls.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(failed_out, f, indent=2, ensure_ascii=False)

    stats = {
        "total_urls": total_urls,
        "scraped": success_count,
        "failed": failed_count,
        "success_rate": f"{(success_count / total_urls * 100):.1f}%" if total_urls else "0.0%",
        "average_quality": round(avg_quality, 2),
    }
    with (OUT_DIR / "transport_infrastructure_stats.json").open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logger.info("Outputs written under %s", OUT_DIR)

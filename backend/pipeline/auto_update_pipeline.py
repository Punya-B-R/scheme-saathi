"""
Auto-update pipeline for Scheme Saathi data.

Builds a full offline pipeline (NOT auto-enabled):
1) Scrape category URLs/pages (via existing scraper modules)
2) Merge new scraped schemes into backend/data_f/all_schemes.json
3) Re-run enrichment to fix structured fields
4) Rebuild ChromaDB vectors
5) Write report to backend/pipeline/reports/

Run manually:
    python run_data_update_pipeline.py
    python run_data_update_pipeline.py --dry-run
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
CONFIG_PATH = BACKEND_ROOT / "pipeline" / "pipeline_config.json"
REPORT_DIR = BACKEND_ROOT / "pipeline" / "reports"
LOCK_FILE = BACKEND_ROOT / "pipeline" / ".update.lock"

DATA_PATH = BACKEND_ROOT / "data_f" / "all_schemes.json"
BACKUP_DIR = BACKEND_ROOT / "pipeline" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("pipeline.auto_update")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


@dataclass
class MergeStats:
    existing_count: int = 0
    scraped_raw_count: int = 0
    scraped_clean_count: int = 0
    updated_by_id: int = 0
    replaced_by_name: int = 0
    inserted_new: int = 0
    untouched_existing: int = 0
    final_count: int = 0


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _normalize_name(name: str) -> str:
    name = (name or "").lower().strip()
    out = []
    for ch in name:
        if ch.isalnum() or ch.isspace():
            out.append(ch)
    return " ".join("".join(out).split())


def _parse_date(s: str) -> str:
    # Keep as YYYY-MM-DD string if possible; otherwise empty.
    if not s:
        return ""
    s = str(s).strip()
    if len(s) >= 10:
        return s[:10]
    return ""


def _is_newer(new_item: Dict[str, Any], old_item: Dict[str, Any], prefer_newer: bool) -> bool:
    new_q = int(new_item.get("data_quality_score", 0) or 0)
    old_q = int(old_item.get("data_quality_score", 0) or 0)
    if new_q > old_q:
        return True
    if new_q < old_q:
        return False
    if not prefer_newer:
        return False
    new_d = _parse_date(new_item.get("last_updated", ""))
    old_d = _parse_date(old_item.get("last_updated", ""))
    return bool(new_d and old_d and new_d > old_d)


def run_scraping_modules(config: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scraping = config.get("scraping", {})
    if not scraping.get("run", True):
        return {"skipped": True, "reason": "scraping.run=false"}

    modules = scraping.get("category_modules", [])
    resume = bool(scraping.get("resume", True))
    test_mode = bool(scraping.get("test_mode", False))
    results: List[Dict[str, Any]] = []

    for mod in modules:
        logger.info("Scrape module: %s", mod)
        if dry_run:
            results.append({"module": mod, "status": "dry_run"})
            continue
        try:
            m = importlib.import_module(mod)
            if not hasattr(m, "run_scraper"):
                results.append({"module": mod, "status": "skipped", "reason": "run_scraper not found"})
                continue
            m.run_scraper(test_mode=test_mode, resume=resume)
            results.append({"module": mod, "status": "ok"})
        except Exception as e:
            logger.exception("Scraper failed: %s", mod)
            results.append({"module": mod, "status": "error", "error": str(e)})

    return {"skipped": False, "results": results}


def merge_new_data(config: Dict[str, Any], dry_run: bool) -> Tuple[MergeStats, List[Dict[str, Any]]]:
    from scraper.data_cleaner import load_all_scraped_schemes, clean_scheme, deduplicate

    stats = MergeStats()

    current_data = _load_json(DATA_PATH)
    current = current_data.get("schemes", []) if isinstance(current_data, dict) else current_data
    if not isinstance(current, list):
        current = []
    stats.existing_count = len(current)

    raw_scraped = load_all_scraped_schemes()
    stats.scraped_raw_count = len(raw_scraped)

    cleaned = []
    min_q = int(config.get("merge", {}).get("min_quality_score", 25))
    for s in raw_scraped:
        c = clean_scheme(s)
        if c and int(c.get("data_quality_score", 0) or 0) >= min_q:
            cleaned.append(c)
    cleaned = deduplicate(cleaned)
    stats.scraped_clean_count = len(cleaned)

    by_id: Dict[str, Dict[str, Any]] = {}
    by_name: Dict[str, Dict[str, Any]] = {}
    for s in current:
        sid = (s.get("scheme_id") or "").strip()
        if sid:
            by_id[sid] = s
        fp = _normalize_name(s.get("scheme_name", ""))
        if fp:
            by_name[fp] = s

    prefer_newer = bool(config.get("merge", {}).get("prefer_newer_last_updated", True))

    for s in cleaned:
        sid = (s.get("scheme_id") or "").strip()
        fp = _normalize_name(s.get("scheme_name", ""))

        if sid and sid in by_id:
            old = by_id[sid]
            if _is_newer(s, old, prefer_newer):
                by_id[sid] = s
                if fp:
                    by_name[fp] = s
                stats.updated_by_id += 1
            continue

        if fp and fp in by_name:
            old = by_name[fp]
            old_sid = (old.get("scheme_id") or "").strip()
            if _is_newer(s, old, prefer_newer):
                by_name[fp] = s
                if old_sid and old_sid in by_id:
                    by_id[old_sid] = s
                elif sid:
                    by_id[sid] = s
                stats.replaced_by_name += 1
            continue

        # New addition
        if sid:
            by_id[sid] = s
        if fp:
            by_name[fp] = s
        stats.inserted_new += 1

    # Build final list preserving original order where possible.
    final: List[Dict[str, Any]] = []
    seen_names = set()
    for s in current:
        sid = (s.get("scheme_id") or "").strip()
        fp = _normalize_name(s.get("scheme_name", ""))
        chosen = by_id.get(sid) if sid else by_name.get(fp)
        if chosen:
            cfp = _normalize_name(chosen.get("scheme_name", ""))
            if cfp and cfp in seen_names:
                continue
            final.append(chosen)
            if cfp:
                seen_names.add(cfp)
        else:
            stats.untouched_existing += 1

    # Append brand-new records not seen above
    for s in by_name.values():
        fp = _normalize_name(s.get("scheme_name", ""))
        if fp and fp not in seen_names:
            final.append(s)
            seen_names.add(fp)

    stats.final_count = len(final)

    if not dry_run:
        backup_path = BACKUP_DIR / f"all_schemes_before_merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        _save_json(backup_path, current_data)
        merged_out = current_data if isinstance(current_data, dict) else {"schemes": final}
        merged_out["schemes"] = final
        if "metadata" in merged_out and isinstance(merged_out["metadata"], dict):
            merged_out["metadata"]["last_pipeline_merge_at"] = datetime.now().isoformat()
        _save_json(DATA_PATH, merged_out)
        logger.info("Merged data saved: %s", DATA_PATH)
        logger.info("Backup saved: %s", backup_path)

    return stats, final


def _run_python_script(script_name: str, dry_run: bool) -> Dict[str, Any]:
    script_path = BACKEND_ROOT / script_name
    if not script_path.exists():
        return {"status": "skipped", "reason": f"{script_name} not found"}
    if dry_run:
        return {"status": "dry_run"}

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout_tail": (result.stdout or "")[-2000:],
            "stderr_tail": (result.stderr or "")[-2000:],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_pipeline(config_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    if LOCK_FILE.exists():
        raise RuntimeError(f"Pipeline lock exists: {LOCK_FILE}. Another run may be active.")

    config = _load_json(config_path)
    LOCK_FILE.write_text(datetime.now().isoformat(), encoding="utf-8")
    logger.info("Pipeline started. dry_run=%s", dry_run)

    report: Dict[str, Any] = {
        "started_at": datetime.now().isoformat(),
        "dry_run": dry_run,
        "config_path": str(config_path),
        "stages": {},
    }

    try:
        report["stages"]["scraping"] = run_scraping_modules(config, dry_run=dry_run)

        merge_stats, _ = merge_new_data(config, dry_run=dry_run)
        report["stages"]["merge"] = merge_stats.__dict__

        if config.get("enrichment", {}).get("run", True):
            report["stages"]["enrichment"] = _run_python_script("enrich_data.py", dry_run=dry_run)
        else:
            report["stages"]["enrichment"] = {"status": "skipped", "reason": "enrichment.run=false"}

        if config.get("vectordb", {}).get("rebuild", True):
            report["stages"]["vectordb"] = _run_python_script("build_vectordb.py", dry_run=dry_run)
        else:
            report["stages"]["vectordb"] = {"status": "skipped", "reason": "vectordb.rebuild=false"}

        report["status"] = "ok"
        return report
    except Exception as e:
        logger.exception("Pipeline failed")
        report["status"] = "error"
        report["error"] = str(e)
        return report
    finally:
        report["finished_at"] = datetime.now().isoformat()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORT_DIR / f"run_{ts}.json"
        _save_json(report_path, report)
        _save_json(REPORT_DIR / "latest.json", report)
        logger.info("Report written: %s", report_path)
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scheme Saathi data auto-update pipeline (manual, not scheduled)."
    )
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Path to pipeline config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Plan and report only; no writes")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    report = run_pipeline(config_path=config_path, dry_run=args.dry_run)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()


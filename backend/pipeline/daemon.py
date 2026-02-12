"""
24h pipeline daemon (built, disabled by default).

This module provides a long-running loop that can execute the data update
pipeline every N hours. It is safe by default because:
- scheduler.enabled is false in config
- nothing starts automatically
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from pipeline.auto_update_pipeline import run_pipeline


logger = logging.getLogger("pipeline.daemon")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _resolve_path(raw: str, backend_root: Path) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    # allow "backend/..." paths in config
    parts = list(p.parts)
    if parts and parts[0].lower() == "backend":
        return backend_root.parent.joinpath(*parts)
    return backend_root / p


def run_daemon(config_path: Path, dry_run: bool = False, once: bool = False) -> None:
    backend_root = config_path.resolve().parent.parent
    cfg = _load_json(config_path)
    scheduler = cfg.get("scheduler", {})

    if not scheduler.get("enabled", False):
        logger.info("Scheduler is disabled in config (scheduler.enabled=false). Exiting.")
        return

    interval_hours = max(1, int(scheduler.get("interval_hours", 24)))
    interval_seconds = interval_hours * 3600

    stop_file = _resolve_path(str(scheduler.get("stop_file", "backend/pipeline/.stop_daemon")), backend_root)
    heartbeat_file = _resolve_path(
        str(scheduler.get("heartbeat_file", "backend/pipeline/reports/daemon_status.json")),
        backend_root,
    )

    logger.info("Daemon started. Interval=%sh dry_run=%s once=%s", interval_hours, dry_run, once)
    logger.info("Stop file: %s", stop_file)

    def update_heartbeat(status: str, last_run_at: str | None = None, next_run_at: str | None = None) -> None:
        _write_json(
            heartbeat_file,
            {
                "status": status,
                "interval_hours": interval_hours,
                "dry_run": dry_run,
                "last_run_at": last_run_at,
                "next_run_at": next_run_at,
                "updated_at": datetime.now().isoformat(),
                "config_path": str(config_path),
            },
        )

    def run_once() -> Dict[str, Any]:
        return run_pipeline(config_path=config_path, dry_run=dry_run)

    # Optional immediate run
    if scheduler.get("run_on_startup", False):
        report = run_once()
        last_run = datetime.now()
        next_run = last_run + timedelta(seconds=interval_seconds)
        update_heartbeat(
            status=f"startup_run_{report.get('status', 'unknown')}",
            last_run_at=last_run.isoformat(),
            next_run_at=next_run.isoformat(),
        )
        if once:
            return
    else:
        now = datetime.now()
        next_run = now + timedelta(seconds=interval_seconds)
        update_heartbeat(status="idle_waiting_first_run", next_run_at=next_run.isoformat())
        if once:
            report = run_once()
            update_heartbeat(status=f"single_run_{report.get('status', 'unknown')}", last_run_at=datetime.now().isoformat())
            return

    # Loop forever until stop file exists
    while True:
        if stop_file.exists():
            logger.info("Stop file detected. Shutting down daemon.")
            update_heartbeat(status="stopped_by_stop_file")
            return

        now = datetime.now()
        next_run = now + timedelta(seconds=interval_seconds)
        update_heartbeat(status="sleeping", next_run_at=next_run.isoformat())
        time.sleep(interval_seconds)

        if stop_file.exists():
            logger.info("Stop file detected before run. Exiting.")
            update_heartbeat(status="stopped_before_run")
            return

        report = run_once()
        status = report.get("status", "unknown")
        last_run = datetime.now()
        next_run = last_run + timedelta(seconds=interval_seconds)
        update_heartbeat(
            status=f"last_run_{status}",
            last_run_at=last_run.isoformat(),
            next_run_at=next_run.isoformat(),
        )


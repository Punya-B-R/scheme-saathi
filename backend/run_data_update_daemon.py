"""
Manual daemon runner for 24-hour auto-update loop.

IMPORTANT:
- This does NOT auto-start.
- It runs only when you execute this file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.daemon import run_daemon


def main() -> None:
    backend_root = Path(__file__).resolve().parent
    default_config = backend_root / "pipeline" / "pipeline_config.json"

    parser = argparse.ArgumentParser(description="Run Scheme Saathi data update daemon manually.")
    parser.add_argument("--config", default=str(default_config), help="Path to pipeline config")
    parser.add_argument("--dry-run", action="store_true", help="Daemon will run dry-run pipeline only")
    parser.add_argument("--once", action="store_true", help="Run one scheduled cycle and exit")
    args = parser.parse_args()

    run_daemon(config_path=Path(args.config), dry_run=args.dry_run, once=args.once)


if __name__ == "__main__":
    main()


"""
Manual entrypoint for data auto-update pipeline.

IMPORTANT:
- This does NOT auto-run on a schedule.
- It only runs when you execute this script manually.
"""

from pathlib import Path
import argparse

from pipeline.auto_update_pipeline import run_pipeline


def main() -> None:
    backend_root = Path(__file__).resolve().parent
    default_config = backend_root / "pipeline" / "pipeline_config.json"

    parser = argparse.ArgumentParser(description="Run Scheme Saathi data auto-update pipeline manually.")
    parser.add_argument("--config", default=str(default_config), help="Pipeline config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Run planning/report only, no writes")
    args = parser.parse_args()

    report = run_pipeline(config_path=Path(args.config), dry_run=args.dry_run)
    print("\nPipeline status:", report.get("status"))
    print("Latest report:", backend_root / "pipeline" / "reports" / "latest.json")


if __name__ == "__main__":
    main()


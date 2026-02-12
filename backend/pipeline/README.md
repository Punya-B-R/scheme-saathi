# Data Auto-Update Pipeline (Manual)

This pipeline is built for **continuous data refresh** but is **NOT turned on automatically**.

## What it does

When you run it manually, it executes:

1. Category scraping via existing scraper modules (`scraper/*.py`)
2. Merge new scraped schemes into `backend/data_f/all_schemes.json`
3. Enrichment (`enrich_data.py`) to re-extract structured eligibility/benefit fields
4. Vector DB rebuild (`build_vectordb.py`) — uses **OpenAI text-embedding-3-large**; requires `OPENAI_API_KEY` in `.env`
5. Report generation in `backend/pipeline/reports/`

## Run manually

From `backend/`:

```bash
python run_data_update_pipeline.py
```

Dry-run (no writes, no DB changes):

```bash
python run_data_update_pipeline.py --dry-run
```

## 24-hour daemon (built, still manual)

A daemon loop is included for 24-hour periodic updates, but it is **disabled by default**.

Config (default disabled):
- `backend/pipeline/pipeline_config.json`
- `scheduler.enabled: false`
- `scheduler.interval_hours: 24`

Run daemon manually (only if you want it):

```bash
python run_data_update_daemon.py
```

Run one daemon cycle and exit:

```bash
python run_data_update_daemon.py --once
```

Stop a running daemon by creating stop file:

```bash
type nul > backend\pipeline\.stop_daemon
```

Heartbeat/status file:
- `backend/pipeline/reports/daemon_status.json`

## Config

File: `backend/pipeline/pipeline_config.json`

- `enabled_by_default` is set to `false`
- You can toggle stage flags (`scraping.run`, `enrichment.run`, `vectordb.rebuild`)
- You can customize scraper module list

## Reports

- Latest: `backend/pipeline/reports/latest.json`
- Historical: `backend/pipeline/reports/run_YYYYMMDD_HHMMSS.json`

## Important

No cron, task scheduler, or service is installed by this pipeline.
It only runs when you execute the command manually.


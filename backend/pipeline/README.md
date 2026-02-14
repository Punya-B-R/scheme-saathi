# Data Auto-Update Pipeline (Manual)

This pipeline is built for **continuous data refresh** but is **NOT turned on automatically**.

## What it does

When you run it manually, it executes:

1. **url_fetch** (optional): Discover new scheme URLs from MyScheme.gov.in. Set `url_fetch.run: true` in config to enable. Uses requests first; falls back to Selenium (ex-machina) if needed.
2. **scraping_from_fetched** (optional): Scrape details from URLs found by url_fetch. Runs when `run_from_fetched_urls: true` and url_fetch produced URLs.
3. Category scraping via existing scraper modules (`scraper/*.py`)
4. Merge new scraped schemes into `backend/data_f/all_schemes.json`
5. Enrichment (`enrich_data.py`) to re-extract structured eligibility/benefit fields
6. Vector DB rebuild (`build_vectordb.py`) — requires `OPENAI_API_KEY` in `.env`
7. Report generation in `backend/pipeline/reports/`

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
- **url_fetch**: Set `run: true` to discover new scheme URLs from MyScheme.gov.in before scraping. Requires Chrome/Selenium for fallback.
- **run_from_fetched_urls**: Scrape schemes from URLs discovered by url_fetch (writes to `data/from_urls/all_schemes/`).
- You can toggle stage flags (`scraping.run`, `enrichment.run`, `vectordb.rebuild`)
- You can customize scraper module list

## Reports

- Latest: `backend/pipeline/reports/latest.json`
- Historical: `backend/pipeline/reports/run_YYYYMMDD_HHMMSS.json`

## Important

No cron, task scheduler, or service is installed by this pipeline.
It only runs when you execute the command manually.


# Scheme Saathi

AI-powered government scheme finder for Indian citizens. Scrapes and structures scheme data from MyScheme.gov.in and official sources.

## Setup (recommended: virtual environment)

Using a virtual environment keeps dependencies isolated and avoids conflicts with other projects.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run commands as below. Make sure your prompt shows `(.venv)` so you know the venv is active.

## Quick start

```bash
# Build from manual data (no scraping; no network needed)
python run.py --manual-only

# Try scraping MyScheme.gov.in (falls back to manual if needed)
python run.py --scrape

# Summary stats
python run.py --stats

# Search
python run.py --search farmer
python run.py --search scholarship --category Education
```

Output: `schemes_data.json`, and `manual_schemes.json` when fallback is used.

## Checking if scraping worked

After running `python run.py --scrape`, you get a **SCRAPING RESULT** block that shows:

- **Status:** SUCCESS = data came from MyScheme.gov.in; FALLBACK = data came from manual_data.py
- **Scraped:** number of schemes actually scraped
- **Target:** 50 schemes
- **Percent:** scraped ÷ target (e.g. 0% = fallback, 100% = full target)

You can also check anytime:

```bash
python run.py --scrape-status
```

This reads `scrape_result.json` (written after each `--scrape` run) and prints the same summary. So you can tell at a glance whether scraping worked and what percent of the target was reached.

## Project structure

| File | Purpose |
|------|--------|
| `scraper.py` | MyScheme.gov.in scraping, rate limiting, fallback |
| `data_cleaner.py` | Validation, deduplication, search, update_scheme, stats |
| `manual_data.py` | 20 hand-curated schemes (fallback) |
| `run.py` | CLI: pipeline, search, update, stats |
| `scrape_result.json` | Last scrape result (source, count, percent) – written after `--scrape` |
| `scraping_log.txt` | Log of last Selenium run (URLs, errors) |
| `requirements.txt` | selenium, webdriver-manager, beautifulsoup4, requests |

## Deactivate venv

When you're done:
```bash
deactivate
```

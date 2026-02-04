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

## Scraping all 677 URLs and merging

You have **677 URLs** in `all_scheme_urls.json`. To scrape details for all of them and merge into `schemes_data.json`:

### 1. Run the detail scraper on all URLs

From the project root (with venv active):

```bash
# All 677 URLs → all_schemes_data.json (takes ~1–2 hours with rate limiting)
python agriculture_detail_scraper.py --input all_scheme_urls.json --output all_schemes_data.json --category "Government Schemes"
```

**Chunked / resumable runs** (e.g. 200 at a time):

```bash
# First 200
python agriculture_detail_scraper.py -i all_scheme_urls.json -o all_schemes_data.json -c "Government Schemes" --start 0 --limit 200

# Next 200 (then merge partial outputs or run again with --start 200 --limit 200 and append)
python agriculture_detail_scraper.py -i all_scheme_urls.json -o all_schemes_data_part2.json -c "Government Schemes" --start 200 --limit 200
```

Checkpoints are saved under `checkpoints/` every 50 schemes. Failed URLs go to `failed_urls_all.json`.

### 2. Merge into main schemes data

After scraping (either full or chunked; if chunked, merge the part files into one `all_schemes_data.json` first, or run the merge script with each part and then dedupe):

```bash
python merge_scraped_to_schemes.py
```

This:

- Loads `schemes_data.json` (current 108 schemes)
- Loads `agriculture_schemes_data.json` and `all_schemes_data.json` (if present)
- Deduplicates by `scheme_id`, validates, backs up to `schemes_data_backup.json`
- Writes merged result to `schemes_data.json`

### 3. Use in the backend

Copy the updated file into the backend:

```bash
copy schemes_data.json backend\data\schemes_data.json
```

Then restart the Scheme Saathi backend so it uses the new scheme count.

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

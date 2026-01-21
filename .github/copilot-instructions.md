# Copilot Instructions for spidershop-historical-analysis

## ⚠️ CRITICAL: Testing Workflow (BLOCKING) ⚠️

**A CODE CHANGE IS NOT COMPLETE UNTIL ALL STEPS BELOW PASS.**

For ANY file edit in `src/`, you MUST immediately execute:

1. `.venv/bin/python -m pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=json`
2. `.venv/bin/python scripts/check_coverage.py --module=<edited_file>.py`

**DO NOT respond "done" to the user until both commands execute successfully.**

**New functionality requires new tests BEFORE you call it done.** Never assume existing tests cover new code.

Tests validate logic, content, structure, formatting, and output. Coverage thresholds (80%) are minimums. Even documentation changes need test validation. Tests run in <1 second - there is NO excuse to skip them.

---

## GitHub Workflows Troubleshooting
- **Fetching Workflow Logs**: Use the GitHub API to download logs as a zip file, not `gh run view` which opens a pager:
  ```bash
  gh api repos/christianacca/web-api-starter/actions/runs/<RUN_ID>/logs > /tmp/workflow-logs.zip
  unzip -o /tmp/workflow-logs.zip -d /tmp
  cat /tmp/<job-log-file>.txt
  ```
  Search for errors: `cat /tmp/<job-log-file>.txt | grep -A 20 -i "error\|fail"`

---

## Project Overview

This is a Python web scraper that captures pricing data for tarantula spiderlings from The Spider Shop UK website. The scraper runs on a weekly schedule via GitHub Actions and maintains historical pricing data as artifacts.

## Project Purpose

- Scrape tarantula spiderling listings including scientific name, common name, size, price, and wishlist count
- Track pricing history over time for market analysis
- Generate opportunity matrices for breeders and dealers
- Generate a static website with interactive tables deployed to GitHub Pages
- Store data as CSV files uploaded to GitHub Actions artifacts

## Project Structure

The project uses a modular architecture with focused modules in the `src/` directory. Key modules include:
- Main scraper orchestration and entry point
- HTTP and browser clients for web scraping
- Text parsing and data extraction utilities
- Historical data management
- Analysis engines (breeder/dealer opportunity matrices)
- Static website generation

Explore the `src/` directory for the complete list of modules.

## Dependencies

Dependencies are defined in:
- **requirements.txt**: Production dependencies (HTTP client, HTML parsing, browser automation, markdown)
- **requirements-dev.txt**: Development/testing dependencies (pytest, coverage tools)

Install with:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Coding Conventions

1. **Python Version**: Python 3.11
2. **Style**: Follow PEP 8 conventions
3. **Imports**: Use absolute imports from src modules
4. **String handling**: Use UTF-8 encoding for file operations
5. **Error handling**: Use assertions for validation with descriptive messages
6. **CSV format**: Use the CSV_HEADER defined in config.py for consistency
7. **Whitespace normalization**: Use the normalize_whitespace() function from parsing.py
8. **Regex patterns**: Define regex patterns in config.py for reusability
9. **Browser cleanup**: Always use try/finally to ensure driver cleanup

## Web Scraping Guidelines

- **User-Agent**: Use the configured User-Agent string in config.py
- **Pagination**: Handle pagination by incrementing page numbers until 404
- **URLs**: Use urljoin() for proper URL construction
- **Selectors**: Use CSS selectors with BeautifulSoup for HTML parsing
- **Error handling**: Catch HTTPError and handle 404s gracefully for pagination
- **Rate limiting**: Be respectful of the target website (no rate limiting currently implemented)
- **JavaScript content**: Use browser_client.py for pages requiring JavaScript execution
- **Headless Chrome**: Uses headless Chrome via Selenium for dynamic content
- **Explicit waits**: Wait for specific selectors with configurable timeouts (default 10 seconds)

## Data Management

- **Snapshot file**: Current scrape results saved as `spidershop_spiderlings_scrape.csv`
- **History file**: Accumulated historical data in `spidershop_spiderlings_history.csv`
- **Matrix files**: Analysis outputs in `breeder_opportunity_table.csv` and `dealer_supply_risk_table.csv`
- **Analysis summary**: Markdown summary saved as `analysis_summary.md`
- **Static website**: Generated HTML files in `website/` directory
- **Artifacts**: Files are uploaded to GitHub Actions artifacts (branch-scoped for history)

### CSV Schema

The CSV files use the following header (defined in config.CSV_HEADER):
```
scrape_datetime, scientific_name, common_name, size_cm, price_gbp, wishlist_count, page_url
```

**Note**: The `wishlist_count` column was added between `price_gbp` and `page_url`. Historical data migration logic exists in the main script to add this field with default value "0" to old rows.

## Workflow and CI/CD

- **Schedule**: Weekly execution (Wednesday 06:10 UTC)
- **Trigger**: Manual workflow_dispatch also supported
- **History management**: Branch-scoped artifacts with fallback to default branch
- **Artifact lifecycle**: History artifacts persist between runs; snapshots are per-run
- **Workflows**:
  - **scrape.yml**: Main scraping and analysis workflow
  - **deploy-pages.yml**: Triggered on successful scrape completion (master branch only), generates and deploys static website to GitHub Pages

### Scrape Workflow Steps
1. Checkout repository
2. Set up Python 3.11
3. Install Chrome (stable)
4. Install dependencies (requests, beautifulsoup4, selenium)
5. Resolve branch-scoped artifact names
6. Download previous history artifact (branch-scoped with fallback to default)
7. Run scraper and analysis
8. Save job summary as `analysis_summary.md`
9. Upload artifacts: snapshot, history, breeder table, dealer table, analysis summary

### Deploy Workflow Steps
1. Checkout repository
2. Set up Python 3.11
3. Download all artifacts from scrape workflow
4. Generate static HTML website using `generate_website.py`
5. Upload website to GitHub Pages
6. Deploy to GitHub Pages

## Testing

The project uses pytest for testing with comprehensive coverage tracking.

### Running Tests

> **⚠️ Important:** Make sure your virtual environment is activated before running tests!
> 
> ```sh
> # Activate virtual environment first
> source .venv/bin/activate          # macOS/Linux
> .venv\Scripts\activate.bat         # Windows (CMD)
> .venv\Scripts\Activate.ps1         # Windows (PowerShell)
> ```
> 
> Your terminal prompt should show `(.venv)` at the beginning when activated.

```bash
# Run all tests
pytest

# Run with coverage (REQUIRED after any code change)
pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=json

# Check specific module coverage
python scripts/check_coverage.py --module=breeder_matrix.py
```

### Test Coverage for Agent Mode

1. **Write tests for new code** following patterns in existing test files:
   - Use synthetic data to simulate scraping results
   - Cover all code branches and edge cases
   - Use descriptive test names

2. **Verify coverage after changes**:
   ```bash
   python scripts/check_coverage.py --module=your_new_module.py --threshold=80
   ```

3. **Coverage artifacts**:
   - `tmp/coverage/coverage.json` - Machine-readable coverage data
   - `tmp/coverage/html/` - Visual HTML report
   - Use `scripts/view_coverage.py` for formatted summary

### Coverage Requirements

- Minimum threshold: 80% per module
- New code must include explicit tests (never assume existing tests cover it)
- Tests should use synthetic data, not live web scraping
- Follow patterns in existing test files

## Common Tasks

### Adding a new parsing function
1. Add the function to parsing.py
2. Add any regex patterns to config.py
3. Use normalize_whitespace() for text processing
4. Handle edge cases with empty/None values

### Modifying scraper logic
1. Update scraper.py for extraction changes
2. Keep functions focused and single-purpose
3. Test with actual web pages before deploying
4. If JavaScript is required, use browser_client.py instead of http_client.py

### Adding new analysis
1. Create a new module in src/ (e.g., new_analysis.py)
2. Follow the pattern of breeder_matrix.py or dealer_matrix.py
3. Import and call from scrape_spidershop_spiderlings.py main()
4. Update workflow to upload new artifact files
5. Update generate_website.py if the analysis should appear on the website

### Modifying website generation
1. Edit generate_website.py
2. Test locally by running: `python src/generate_website.py`
3. Check generated HTML files in `website/` directory
4. Ensure CSV files are copied to output directory
5. Verify markdown-to-HTML conversion for analysis sections

## Domain Context

- **Scientific names**: Genus + species (e.g., "Aphonopelma seemanni")
- **Common names**: Descriptive names (e.g., "Costa Rican Zebra")
- **Size**: Typically in cm, extracted from parenthetical notation
- **Price**: In GBP (£), decimal format
- **Spiderlings**: Juvenile tarantulas, distinct from adults
- **Wishlist count**: Number of users who have added the item to their wishlist

## Important Constraints

- Do not add rate limiting or delays that would significantly slow down the scraper
- Maintain CSV format compatibility for historical data
- Keep modules focused and avoid creating monolithic files
- Preserve existing workflow artifact naming conventions for backward compatibility

## Market Analysis Design Intent (Critical Context)

This project is not a generic scraper or dashboard.
It is a **conservative market-signal system** designed to avoid noise and false positives.

All analysis must prioritise **signal stability over early detection**.

---

## Core Analysis Philosophy

1. **Supply signals dominate**
   - Out-of-stock behaviour, persistence, and restock speed are the primary drivers
   - Demand metrics (wishlist, price) only *modify* supply-based conclusions

2. **Conservative by default**
   - Neutral (`→`) is preferred over guessing
   - Single-run changes must not trigger strong signals
   - Missing or ambiguous data must not be inferred

3. **Weekly cadence awareness**
   - All thresholds assume weekly execution
   - Short-term volatility (±1 run) is treated as noise

---

## Wishlist Metrics — Implementation Rules

### Wishlist Pressure
- Represents **relative interest within the current run**
- Must be computed per-run (no absolute thresholds)
- Includes:
  - Small-N flattening (flat distributions → ⚠️)
  - Bounded carryover for OUT species (≤ 5 runs)
- Acts as a **confidence amplifier**, never a trigger

### Wishlist Delta (Momentum)
- Measures **meaningful change in wishlist interest**
- Thresholds are intentionally conservative:
  - Δ ≥ +5 → ↑
  - −4 ≤ Δ ≤ +4 → →
  - Δ ≤ −5 → ↓
- Must compare **two recent IN-stock observations**
- BOTH values must be **time-bounded**
  - OUT carryover ≤ 3 runs
  - Previous comparison bounded (default ≤ 12 runs)
- If a comparable value cannot be found → return neutral (`→`)

Wishlist Delta is a **modifier**, not a standalone signal.

---

## Breeder Opportunity Matrix — Rules

Audience: **Breeders**

- Pattern (supply) is primary
- Price Trend confirms or weakens signals
- Wishlist Pressure & Delta only escalate *emerging* opportunities

Hard rules:
- Sustained scarcity is never downgraded
- Emerging signals may escalate only with demand confirmation
- Always-available species remain ❌ regardless of demand spikes

Sorting priority:
1. Signal (🔥 > ⚠️ > ❌)
2. Wishlist Pressure
3. Wishlist Delta
4. OOS Runs (descending)

---

## Dealer Supply Risk Matrix — Rules

Audience: **Dealers**

- Stock Reliability and Restock Speed are primary
- Wishlist metrics adjust urgency, not classification

Hard rules:
- Low reliability + rising demand reinforces 🔥
- High reliability + falling demand reinforces ❌
- Wishlist metrics must never override healthy supply

Sorting priority:
1. Dealer Risk (🔥 > ⚠️ > ❌)
2. Wishlist Pressure
3. Wishlist Delta
4. Avg OOS Duration (descending)

---

## Non-Negotiable Constraints

- No unbounded historical comparisons
- No inference of missing data
- No single metric may dominate decisions
- All logic must be explainable in plain English
- Prefer fewer signals over noisy signals

If unsure, choose the **more conservative interpretation**.


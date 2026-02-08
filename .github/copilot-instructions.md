# Copilot Instructions for spidershop-historical-analysis

## Python Code Hygiene Guidelines

**Descriptive Naming**: Use clear, descriptive names for variables and functions (snake_case) and classes (PascalCase). Avoid nonstandard abbreviations or single-letter names.

**Small, Focused Functions**: Write short functions that each serve a single purpose. Avoid deep nesting or high cyclomatic complexity—split complex logic into helper functions if needed.

**Minimize Side Effects**: Prefer pure functions and immutability whenever possible. Avoid global state or hidden side effects that make code harder to reason about.

**Clean OOP Structure**: Design classes with a single responsibility and clear purpose. Favor composition over deep inheritance to reduce tight coupling and keep logic easy to follow.

**Avoid Duplicate Code**: Do not copy-paste or duplicate logic. Refactor common functionality into reusable functions or methods to keep code DRY.

**Use Type Annotations**: Add Python type hints for function parameters, return values, and important variables. This improves code clarity and catches many issues early.

**Consistent Style and Formatting**: Format code with an auto-formatter (e.g. Black) to enforce PEP 8 standards, and use a linter (like Ruff) to detect issues and ensure consistent style.

**Self-Documenting Code**: Write code that is clear by itself, minimizing the need for inline comments.

## ⚠️ CRITICAL: Testing Workflow (BLOCKING) ⚠️

**A code change is complete only when all tests pass and coverage meets thresholds (80%).**

### ✅ MANDATORY: Always Use Make Commands

**NEVER run pytest directly.** Make commands ensure proper working directory and artifact management.

**For ANY edit in `src/`:**
1. `make test` (all tests with coverage)
2. `.venv/bin/python scripts/check_coverage.py --module=<edited_file>.py`

### Playwright E2E Smoke Tests (When Required)

This repo includes **opt-in** Playwright E2E smoke tests (browser-based). They are designed to catch regressions that unit tests can miss, especially around:
- broken relative links from nested pages (e.g. `website/species/*.html`)
- missing/incorrect asset references (CSS/JS)
- basic navigation and UI state driven by URL params

**Run E2E tests in addition to `make test` when you change:**
- Anything in `src/website/`
- Anything in `templates/` (including `templates/scripts/`)
- Any generated URL/path logic (e.g. `path_prefix`, link building)
- Any bugfix or feature that is specifically “works in a browser” / interaction-based

**You may skip E2E tests when you change only:**
- `src/scrape/` or `src/shared/` logic unrelated to website output
- Documentation-only changes
- Pure unit-test refactors

**Commands (always use make):**
```bash
# Install Playwright browser binary (one-time; cached by Playwright)
make e2e-install

# Run the smoke suite
make test-e2e
```

Note: E2E tests are intentionally not part of the default `make test` run.

**Individual test files:**
```bash
make test-file FILE=tests/website_module/test_csv.py
make test-file FILE=tests/scrape_module/test_breeder_matrix.py
```

**Why make commands?** Direct pytest execution causes:
- CSV files in wrong directories (project root vs `tmp/local-testing/`)
- Scattered artifacts outside designated folders
- Incorrect working directory context

**Key rules:**
- New functionality requires new tests FIRST (TDD)
- Never assume existing tests cover new code
- DO NOT respond "done" until tests pass and coverage verified
- Tests run in <1 second — no excuse to skip

### Test-Driven Development (TDD) Protocol — MANDATORY

**RED-GREEN CYCLE REQUIRED**

For ANY feature or bug fix, follow this exact sequence:

1. **RED Phase — Write Failing Test First**:
   - Write the test for the feature/fix BEFORE implementing the code
   - Run the test to confirm it FAILS with the expected failure message
   - Document what failure you expect to see (e.g., "AttributeError", "AssertionError with specific message")
   - **DO NOT proceed to implementation until you have confirmed the test fails correctly**

2. **GREEN Phase — Implement Quality Code**:
   - Write clean, idiomatic code to make the test pass
   - Aim for the best implementation from the start (no "quick hacks")
   - Run the test again to confirm it now PASSES
   - Verify coverage meets threshold (80%)

3. **REFACTOR Phase — Optional**:
   - Only needed if the initial implementation has structural issues
   - Re-run tests after any refactoring to ensure they remain green

### ⛔ Snapshot Test Protocol (MANDATORY)

**NEVER blindly update snapshot files.**

Snapshot tests are regression detectors. When a snapshot test fails:

1. **STOP** - Do not immediately run `--snapshot-update`
2. **INVESTIGATE** - Run the test with `-vv` to see the full diff
3. **ANALYZE** - Review EVERY line that changed:
   - Are the changes intentional from your code modifications?
   - Do they match the expected behavior?
   - Are there unexpected changes that indicate a bug?
4. **EXPLAIN** - Document what changed and why it's correct
5. **ONLY THEN** - Update the snapshot if changes are verified as intentional

Snapshot files are located in module-specific subdirectories (`tests/scrape_module/__snapshots__/*.ambr`, `tests/website_module/__snapshots__/*.ambr`). They catch:
- Unintended changes to output format
- Logic regressions that alter analysis results
- Documentation changes that affect generated content

**If you cannot explain why a snapshot changed, DO NOT update it.**

### Test Style Selection Guide

Choose the appropriate test style based on what you're validating:

#### 1. **HTML Snapshot Testing** (`syrupy` fixtures)
- **Use when**: Testing small, focused HTML fragments for regressions
- **Pattern**: Capture minimal necessary HTML, detect any change
- **Important**: Keep snapshots small. Large/complex outputs → use Structure Validation
- **Update protocol**: MUST follow "Snapshot Test Protocol" above

#### 2. **CSS Validation Tests** (Targeted checks)
- **Use when**: Verifying specific CSS classes, styles, or attributes
- **Pattern**: Parse HTML, assert specific class names or styles present
- **Example**: Checks for `risk-high`, `table-container`

#### 3. **HTML Structure Validation** (Classic unit tests)
- **Use when**: Testing logic/data processing OR when snapshots would be too large
- **Pattern**: Arrange data → Act (call function) → Assert expected output
- **Best for**: Business logic, calculations, most maintainable approach

**Decision tree:**
```
Are you testing HTML generation?
  ├─ YES: Small/focused HTML fragment? → Snapshot Test
  │       Large/complex HTML output? → Structure Validation + CSS Validation
  │       Only care about specific elements? → CSS Validation
  └─ NO: Testing data transformation/logic? → Structure Validation
```

### Testing JavaScript Behavior (E2E Required)

**CRITICAL RULE:** Client-side JavaScript can ONLY be tested via E2E (Playwright) tests.

**When to write E2E tests:**
- User interactions: clicking buttons, typing in inputs, selecting options
- DOM mutations: showing/hiding elements, updating classes/attributes
- Browser APIs: `window.history`, `localStorage`, `fetch`
- Visual feedback: animations, transitions, dynamic content
- Multi-filter interactions: verifying combined behavior of multiple JS functions
- URL state management: query parameters, pushState/popState

**When to keep unit tests:**
- HTML structure: verify correct elements exist with correct attributes
- Data attributes: verify `data-signal`, `data-stock-pattern`, `onclick` presence
- Template logic: loops, conditionals, data transformation
- JS file existence: verify external JS files are referenced correctly

**Anti-pattern examples (DO NOT WRITE THESE):**
- ❌ Unit test checking `onclick="sortTable(0, 'breeder-table')"` exact string content
- ❌ Grep for function names inside `table-interactions.js` (e.g., checking for `isNumeric`)
- ❌ Verify JS variable names or implementation details in generated HTML
- ❌ Test CSS class changes without actually running JS in a browser

**Correct approach examples:**
- ✅ Unit test: Button has `onclick` attribute (any value) + `data-signal` attribute
- ✅ E2E test: Click button, verify rows are filtered correctly in browser
- ✅ Unit test: Table rows have `data-stock-pattern` attribute
- ✅ E2E test: Click "Emerging" filter, verify only Emerging rows visible
- ✅ Unit test: Search input has `onkeyup` handler
- ✅ E2E test: Type in search input, verify filtering works with signal filter

**E2E tests location:** `tests/e2e/` with shared utilities in `helpers.py`

### Modifying vs. Creating Tests

**Default approach: MODIFY existing tests**

Before creating a new test function, ask:
1. Does an existing test already cover this code path?
2. Can I add a test case to an existing parametrized test?
3. Would adding assertions to an existing test be clearer?

**Create a NEW test only when:**
- Testing a genuinely new code path or module
- Existing test has a fundamentally different setup or fixture
- New test would make the existing test too complex

**Example — prefer to modify:**
```python
# ❌ DON'T create duplicate test
def test_parse_price_with_pence():
    assert parse_price("£12.99") == 12.99

def test_parse_price_with_whole_pounds():  # NEW - duplicates above
    assert parse_price("£15.00") == 15.00

# ✅ DO extend existing parametrized test
@pytest.mark.parametrize("input,expected", [
    ("£12.99", 12.99),
    ("£15.00", 15.00),  # ADD to existing test
])
def test_parse_price(input, expected):
    assert parse_price(input) == expected
```

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
# Run all unit tests (fast, ~1 second)
make test

# Run individual test file (REQUIRED when testing specific functionality)
make test-file FILE=tests/website_module/test_csv.py
make test-file FILE=tests/scrape_module/test_breeder_matrix.py

# Run E2E tests (requires Playwright, ~10-20 seconds)
make e2e-install  # one-time setup to install Playwright browsers
make test-e2e     # run all E2E tests (opt-in)

# Debug E2E tests (show browser window with slow motion)
PWHEADED=1 PWSLOW=500 make test-e2e

# Check specific module coverage
python scripts/check_coverage.py --module=scrape/breeder_matrix.py
```

### Test Coverage Requirements

**Process:**
1. **Write tests FIRST** (TDD: RED → GREEN → optional REFACTOR)
2. **Choose test style** based on what you're validating (snapshot/CSS/structure/E2E)
3. **Modify existing tests** when possible instead of creating duplicates
4. **Use synthetic data** to simulate scraping, not live web scraping
5. **Cover all branches** and edge cases with descriptive test names

**JavaScript behavior:** E2E tests required for all user interactions. Unit tests verify HTML structure only.

**Verification:**
```bash
python scripts/check_coverage.py --module=scrape/breeder_matrix.py --threshold=80
python scripts/check_coverage.py --module=shared/parsing.py --threshold=80
python scripts/check_coverage.py --module=website/generate_website.py --threshold=80
```

**Artifacts:** `tmp/coverage/coverage.json`, `tmp/coverage/html/`, use `scripts/view_coverage.py` for summary

**Threshold:** 80% minimum per module

---

## GitHub Workflows Troubleshooting
- **Fetching Workflow Logs**: Use the GitHub API to download logs as a zip file, not `gh run view` which opens a pager:
  ```bash
  gh api repos/christianacca/spidershop-historical-analysis/actions/runs/<RUN_ID>/logs > /tmp/workflow-logs.zip
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

The project is organized into three main modules:

**`src/scrape/`** - Main scraping and analysis:
- Main scraper orchestration and entry point (scrape_spidershop_spiderlings.py)
- HTTP and browser clients for web scraping
- Historical data management
- Analysis engines (breeder_matrix.py, dealer_matrix.py, wishlist_analysis.py)
- Pricing summary and legend generation

**`src/shared/`** - Shared utilities used by both scrape and website:
- Configuration (config.py)
- Text parsing utilities (parsing.py)
- Validation helpers (assertions.py)
- Sparkline generation (sparkline_helpers.py)
- History utilities (history_utils.py)

**`src/website/`** - Static website generation:
- HTML page generation
- Markdown to HTML conversion
- CSV processing and table rendering
- Sparkline conversion to SVG

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
6. **CSV format**: Use the CSV_HEADER defined in shared.config for consistency
7. **Whitespace normalization**: Use the normalize_whitespace() function from shared.parsing
8. **Regex patterns**: Define regex patterns in shared.config for reusability
9. **Browser cleanup**: Always use try/finally to ensure driver cleanup

## Test Utilities

Common test helper functions are available in `tests/helpers/test_helpers.py` and exported via `tests/conftest.py`:

- **File creation helpers**:
  - `create_temp_markdown_file(content)` - Create temporary markdown file
  - `create_temp_csv_file(content)` - Create temporary CSV file
  - `write_csv_file(path, headers, rows)` - Write CSV to path
  - `read_file_content(path)` - Read file with UTF-8 encoding

- **CSV content generators with dataclasses**:
  - `create_csv_content(headers, rows)` - Generate CSV string
  - `create_breeder_csv_content(entries)` - Breeder CSV from `List[BreederEntry]`
  - `create_dealer_csv_content(entries)` - Dealer CSV from `List[DealerEntry]`
  - `create_history_csv_content(entries)` - Historical scrape data from `List[HistoryEntry]`

- **CSV entry dataclasses**:
  - `HistoryEntry` - Historical scrape data (scientific_name, scrape_datetime, common_name, size_cm, price_gbp, wishlist_count, page_url)
  - `BreederEntry` - Breeder opportunity data with all CSV columns as proper fields (species, size_cm, signal, oos, oos_runs, stock_pattern, price_trend, price_history, wishlist_pressure, wishlist_delta, wishlist_history, recommendation)
  - `DealerEntry` - Dealer supply risk data with all CSV columns as proper fields (species, size_cm, risk, stock_reliability, avg_oos_duration, restock_speed, price_pressure, price_history, wishlist_pressure, wishlist_delta, wishlist_history, stock_availability, dealer_recommendation)

**Usage in tests:**
```python
from conftest import create_temp_csv_file, BreederEntry, create_breeder_csv_content

def test_example():
    # Simple approach
    csv_path = create_temp_csv_file("Header1,Header2\nValue1,Value2\n")
    
    # Or use dataclass with generator
    content = create_breeder_csv_content([
        BreederEntry(
            species="Test Spider",
            size_cm="1.5",
            signal="🔥",
            oos_runs="4",
            price_trend="↑"
        )
    ])
    csv_path = create_temp_csv_file(content)
    
    try:
        # Test code here
        pass
    finally:
        os.unlink(csv_path)
```

Use these helpers to reduce boilerplate and improve test readability.

## Web Scraping Guidelines

- **User-Agent**: Use the configured User-Agent string in shared.config
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

### Website Generation Output Location

**Key principle:** `OUTPUT_DIR = Path("website")` is relative to the current working directory.

**Location by context:**
- **Direct execution** (`python -m website` from root) → `website/` at project root
- **GitHub workflow** (runs from root) → `website/` at project root
- **Make commands** (`make generate-website`) → `tmp/local-testing/website/`

**When verifying output:**
- Check project root if you/workflow ran the module directly
- Check `tmp/local-testing/website/` if user ran make command
- Don't assume location without checking execution context

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
4. Generate static HTML website using the `website.generate_website` module
5. Upload website to GitHub Pages
6. Deploy to GitHub Pages

## Common Tasks

### Adding a new parsing function
1. Add the function to src/shared/parsing.py
2. Add any regex patterns to src/shared/config.py
3. Use normalize_whitespace() for text processing
4. Handle edge cases with empty/None values

### Modifying scraper logic
1. Update src/scrape/scraper.py for extraction changes
2. Keep functions focused and single-purpose
3. Test with actual web pages before deploying
4. If JavaScript is required, use src/scrape/browser_client.py instead of http_client.py

### Adding new analysis
1. Create a new module in src/scrape/ (e.g., new_analysis.py)
2. Follow the pattern of src/scrape/breeder_matrix.py or dealer_matrix.py
3. Import and call from src/scrape/scrape_spidershop_spiderlings.py main()
4. Update workflow to upload new artifact files
5. Update `src/website/generate_website.py` if the analysis should appear on the website

### Modifying website generation
1. Edit `src/website/generate_website.py`
2. Test locally by running: `python -m website` (with PYTHONPATH set to src/)
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


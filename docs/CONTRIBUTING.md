# Contributing to spidershop-historical-analysis

This guide walks you through setting up a local development environment from scratch, even if you've never used Python before.

## Table of Contents

- [Setup by Operating System](#setup-by-operating-system)
- [Running Tests](#running-tests)
- [Local Development Workflows](#local-development-workflows)
- [Deactivating the Virtual Environment](#deactivating-the-virtual-environment)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Questions or Issues?](#questions-or-issues)

---

## Setup by Operating System

<details>
<summary><strong>🍎 macOS Setup</strong></summary>

### Step 1: Install Python

This project requires **Python 3.11 or higher**.

```sh
# Using Homebrew (recommended)
brew install python@3.11

# Verify installation
python3 --version
```

### Step 2: Install Git

```sh
brew install git
```

### Step 3: Install Make (Optional but Recommended)

Make provides convenient shortcuts for common tasks.

**macOS**: Usually pre-installed! Try `make --version` to check. If not found, macOS will prompt you to install Command Line Tools automatically, or run:
```sh
xcode-select --install
```

**Note:** If you don't have `make`, you can use the Python commands directly throughout this guide.

### Step 4: Install Chrome

Download from [google.com/chrome](https://www.google.com/chrome/)

### Step 5: Clone the Repository

```sh
cd ~/Documents  # or wherever you keep projects
git clone https://github.com/christianacca/spidershop-historical-analysis.git
cd spidershop-historical-analysis
```

### Step 6: Create a Virtual Environment

A virtual environment isolates this project's dependencies from your system Python.

```sh
python3 -m venv .venv
```

This creates a `.venv/` directory (which is gitignored).

### Step 7: Activate the Virtual Environment

```sh
source .venv/bin/activate
```

After activation, your terminal prompt should show `(.venv)` at the beginning.

### Step 8: Install Dependencies

```sh
# Install all production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

### Step 9: Verify Installation

```sh
python --version   # Should show 3.11+
pip list           # Should show installed packages
```

✅ You're ready! Continue to [Running Tests](#running-tests)

</details>

<details>
<summary><strong>🪟 Windows Setup</strong></summary>

### Step 1: Install Python

This project requires **Python 3.11 or higher**.

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
4. Verify installation:

```sh
python --version
```

### Step 2: Install Git

Download from [git-scm.com](https://git-scm.com/download/win) and run the installer.

### Step 3: Install Chrome

Download from [google.com/chrome](https://www.google.com/chrome/)

### Step 4: Clone the Repository

```sh
cd %USERPROFILE%\Documents  # or wherever you keep projects
git clone https://github.com/christianacca/spidershop-historical-analysis.git
cd spidershop-historical-analysis
```

### Step 5: Create a Virtual Environment

A virtual environment isolates this project's dependencies from your system Python.

```sh
python -m venv .venv
```

This creates a `.venv\` directory (which is gitignored).

### Step 6: Activate the Virtual Environment

**Command Prompt:**
```sh
.venv\Scripts\activate.bat
```

**PowerShell:**
```sh
.venv\Scripts\Activate.ps1
```

After activation, your terminal prompt should show `(.venv)` at the beginning.

### Step 7: Install Dependencies

```sh
# Install all production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

### Step 8: Verify Installation

```sh
python --version   # Should show 3.11+
pip list           # Should show installed packages
```

✅ You're ready! Continue to [Running Tests](#running-tests)

</details>

<details>
<summary><strong>🐧 Linux Setup</strong></summary>

### Step 1: Install Python

This project requires **Python 3.11 or higher**.

```sh
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Verify installation
python3 --version
```

### Step 2: Install Git

```sh
sudo apt install git
```

### Step 3: Install Make (Optional but Recommended)

Make provides convenient shortcuts for common tasks.

**Linux**: Usually pre-installed! Try `make --version` to check. If not:
```sh
sudo apt install make  # Debian/Ubuntu
```

**Note:** If you don't have `make`, you can use the Python commands directly throughout this guide.

### Step 4: Install Chrome/Chromium

```sh
sudo apt install chromium-browser
```

### Step 5: Clone the Repository

```sh
cd ~/Documents  # or wherever you keep projects
git clone https://github.com/christianacca/spidershop-historical-analysis.git
cd spidershop-historical-analysis
```

### Step 6: Create a Virtual Environment

A virtual environment isolates this project's dependencies from your system Python.

```sh
python3 -m venv .venv
```

This creates a `.venv/` directory (which is gitignored).

### Step 7: Activate the Virtual Environment

```sh
source .venv/bin/activate
```

After activation, your terminal prompt should show `(.venv)` at the beginning.

### Step 8: Install Dependencies

```sh
# Install all production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

### Step 9: Verify Installation

```sh
python --version   # Should show 3.11+
pip list           # Should show installed packages
```

✅ You're ready! Continue to [Running Tests](#running-tests)

</details>

---

## Running Tests

### ⚠️ Always Use Make Commands

**CRITICAL**: Always use `make` commands for testing. Never run pytest or test files directly.

**Why?** Running pytest directly (e.g., `pytest tests/...`) causes:

- CSV files created in wrong directories (project root instead of `tmp/local-testing/`)
- Artifacts scattered outside designated folders
- Tests failing due to incorrect working directory context

### Run all tests with coverage (recommended)
```sh
make test
```

This runs pytest with full coverage reporting, showing:
- Overall coverage percentage
- Coverage per module
- **Missing column**: Specific line numbers that aren't tested (e.g., "15-22, 34-40")

### Run individual test file

```sh
make test-file FILE=tests/website_module/test_csv.py
make test-file FILE=tests/scrape_module/test_breeder_matrix.py
```

Use this when working on specific functionality to get faster feedback.

### Playwright E2E smoke tests (optional)

These are lightweight browser-based checks that catch issues unit tests can miss (e.g. broken relative links, missing assets, basic navigation regressions).

They are **opt-in** so they don't slow down the default test suite.

```sh
make test-e2e
```

On first run, this will download the Playwright Chromium binary. You can also install it explicitly:

```sh
make e2e-install
```

Notes:
- These tests run headless Chromium via Playwright.
- Browser binaries are cached by Playwright (first run may take a minute).
- If you only want the fast Python/unit suite, stick to `make test` / `make test-file`.

### View interactive HTML coverage report
```sh
make coverage
```

Opens the HTML coverage report in your browser, providing:
- Visual coverage with color-coded lines (green = tested, red = not tested)
- Module-by-module breakdown
- Easy navigation through source files

### Snapshot Testing

This project uses [pytest-syrupy](https://github.com/tophat/syrupy) for snapshot testing. Snapshots capture expected outputs and detect regressions.

**When a snapshot test fails:**

1. **Review the diff** - See what changed:
   ```sh
   make test-snapshots-diff
   ```

2. **Investigate** - Determine if changes are intentional or indicate a bug

3. **Update if correct** - Regenerate snapshots only after verifying changes:
   ```sh
   make test-update-snapshots
   ```

**⚠️ Critical:** Never blindly update snapshots. Always review diffs first. See [Snapshot Test Protocol](../.github/copilot-instructions.md#snapshot-test-protocol-mandatory) for detailed guidelines.

**Learn more:** [pytest-syrupy documentation](https://github.com/tophat/syrupy)

### Additional Testing Options

**Learn more:** [pytest-syrupy documentation](https://github.com/tophat/syrupy)

### Advanced Coverage Tools

For detailed coverage analysis, use the helper scripts:

```sh
# View formatted coverage summary
python scripts/view_coverage.py

# Check specific module coverage with threshold
python scripts/check_coverage.py --module=scrape/breeder_matrix.py --verbose
```

---

## Local Development Workflows

This section covers testing website changes and running the scraper locally without pushing to GitHub.

### Quick Start

Choose your complete workflow:

```sh
# Option 1: Fresh scrape + build + serve (requires Chrome)
make scrape-website-serve

# Option 2: Download from GitHub + build + serve (requires GitHub CLI)
make download-website-serve

# Option 3: Rebuild from existing data + serve (data must already exist)
make website-serve

# Just run tests
make test
```

### Option 1: Using Remote Data (GitHub Actions)

**Prerequisites:** Install GitHub CLI (`gh`)

```bash
# macOS
brew install gh

# Windows (using winget)
winget install --id GitHub.cli

# Linux (Debian/Ubuntu)
sudo apt install gh

# Authenticate (all platforms)
gh auth login
```

**Workflow:**

```bash
# Download from GitHub Actions and generate website
make download-website

# Or: Download, generate, and serve locally at http://localhost:8000
make download-website-serve

# Individual steps (if needed):
make download-artifacts  # Just download
make generate-website    # Just build from existing data
```

This downloads the latest scrape results from GitHub Actions, generates the static website in `tmp/local-testing/website/`, and optionally starts a local server.

### Option 2: Using Local Data (Run Scraper)

**Prerequisites:** Chrome already installed (from setup section above)

**Workflow:**

```bash
# Scrape locally and generate website
make scrape-website

# Scrape locally, generate website, and serve at http://localhost:8000
make scrape-website-serve

# Or just run the scraper without generating the website
make scrape-only
```

This runs the scraper to generate fresh data, creates the website, and optionally serves it locally.

> **💡 Note on historical data:** When scraping locally, the historical CSV will either:
> - Append to existing history in `tmp/local-testing/` (if present from a previous scrape or download)
> - Create a new history file with just the current scrape
> 
> To maintain continuity with production history, download it first:
> ```bash
> make download-artifacts  # Get production history
> make scrape-website      # Append new scrape to downloaded history
> ```

### Available Commands

For a complete list of available commands, run:

```bash
make help
```

This displays all workflow commands with descriptions.

### Advanced Usage

**Iterative development workflow** - When making changes to `generate_website.py`:

```bash
# 1. Get data (only needed once)
make download-artifacts  # OR: make scrape-only

# 2. Generate and start server (keep running in this terminal)
make website-serve
# Open http://localhost:8000

# 3. In a NEW terminal: make changes to src/generate_website.py
# ... edit files ...

# 4. Regenerate website (in the new terminal)
make generate-website

# 5. Refresh browser to see changes

# 6. Repeat steps 3-5 as needed
```

**Python bytecode cache:** Python automatically generates `.pyc` files and `__pycache__/` directories to speed up module loading. During development, this cache can sometimes prevent updated code from running. All Python-executing targets (`make scrape-only`, `make generate-website`, and their dependent workflows) automatically clear the cache before execution. If you encounter issues where code changes aren't reflected:

```bash
# Clear cache manually
make clean-cache

# Or use any workflow - they all clear cache automatically
make scrape-only         # Clears cache before scraping
make generate-website    # Clears cache before website generation
make download-website    # Clears cache (via generate-website)
```

**Using a custom port** (requires active virtual environment):

```bash
source .venv/bin/activate  # Activate first
python3 scripts/test_website_locally.py --serve --port 3000
```

**Compare downloaded vs scraped data:**

```bash
make download-website
mv tmp/local-testing/website tmp/local-testing/website-downloaded

make scrape-website
mv tmp/local-testing/website tmp/local-testing/website-scraped

diff -r tmp/local-testing/website-downloaded tmp/local-testing/website-scraped
```

### Workflow Comparison

| Task | Download (GitHub Actions) | Scrape (Local) |
|------|--------------------------|----------------|
| **Data Source** | Latest successful workflow run | Fresh scrape from website |
| **Speed** | Fast (download only) | Slower (full scrape) |
| **Requirements** | GitHub CLI (`gh`) | Chrome/Chromium (already installed) |
| **Network** | GitHub API only | Full website scraping |
| **Use Case** | Quick testing with real data | Testing scraper changes, no GitHub dependency |
| **Command** | `make download-website-serve` | `make scrape-website-serve` |

### Files and Directories

All local development files are stored in `tmp/local-testing/` (gitignored):
- `*.csv` - Scraper output or downloaded CSV files
- `analysis_summary.md` - Analysis summary (downloaded or generated)
- `website/` - Generated HTML files

**Scripts:**
- `scripts/test_website_locally.py` - Website generation script
- `scripts/download_artifact.sh` - GitHub artifact downloader (called by Makefile)
- `Makefile` - Orchestrates all workflows

---

## Deactivating the Virtual Environment

When you're done working:

```sh
deactivate
```

---

## Troubleshooting

### Python Issues

#### `command not found: python`
- **macOS/Linux**: Try `python3` instead of `python`
- **Windows**: Reinstall Python and ensure "Add Python to PATH" is checked

#### `python3: command not found` (Windows)
On Windows, use `python` instead of `python3`:
```cmd
python scripts/test_website_locally.py --serve
```

Or add a Python 3 alias in PowerShell:
```powershell
Set-Alias python3 python
```

#### ModuleNotFoundError
Make sure your virtual environment is activated **before** running scripts.

**Activate command:**
- **macOS/Linux**: `source .venv/bin/activate`
- **Windows CMD**: `.venv\Scripts\activate.bat`
- **Windows PowerShell**: `.venv\Scripts\Activate.ps1`

### Chrome and Selenium Issues

#### Chrome/ChromeDriver version mismatch
Selenium should auto-download the correct ChromeDriver. If you encounter issues:
```sh
pip install --upgrade selenium
```

#### Permission denied when activating virtual environment (macOS/Linux)
```sh
chmod +x .venv/bin/activate
```

### Make and Command Issues

#### `make: command not found` (Windows)

You have several options:

1. **Use Git Bash** (recommended):
   - Install Git for Windows from https://git-scm.com/download/win
   - Git Bash includes `make` and a Unix-like environment
   - Run commands in Git Bash instead of CMD/PowerShell

2. **Install make via Chocolatey**:
   ```powershell
   choco install make
   ```

3. **Use WSL** (Windows Subsystem for Linux):
   ```powershell
   wsl --install
   ```

4. **Use Python commands directly** (no `make` needed) - see individual workflow sections above

### GitHub and Workflow Issues

#### "GitHub CLI (gh) is not installed"

Install and authenticate:
```bash
# macOS
brew install gh

# Windows (using winget or Chocolatey - see above)

# Linux (Debian/Ubuntu)
sudo apt install gh

# Authenticate (all platforms)
gh auth login
```

#### "No successful runs found"

Make sure the scrape workflow has run successfully at least once. You can trigger it manually:
```bash
gh workflow run "Spider Shop Spiderlings Scrape" --repo christianacca/spidershop-historical-analysis
```

Or use local scraper instead:
```bash
make local-website-serve
```

#### "Artifact not found"

Some artifacts may not exist on older runs. The script will skip missing artifacts and continue. For guaranteed fresh data:
```bash
make local-website-serve
```

### Website Generation Issues

#### "CSV files not found"

If you see this when running `make generate-website`, you need to obtain CSV files first:
```bash
# Option 1: Download from GitHub Actions
make download-artifacts

# Option 2: Run scraper locally
make scrape-local

# Then generate website
make generate-website
```

#### Port already in use

Change the port:
```bash
python3 scripts/test_website_locally.py --serve --port 3000
```

---

## Project Structure

```
spidershop-historical-analysis/
├── src/
│   ├── scrape/            # Scraping and analysis modules
│   ├── shared/            # Shared utilities (config, parsing, etc.)
│   └── website/           # Static website generation
├── tests/                 # Test suite
│   ├── scrape_module/     # Tests for src/scrape/
│   ├── shared_module/     # Tests for src/shared/
│   ├── website_module/    # Tests for src/website/
│   └── helpers/           # Test utility functions
├── .github/workflows/     # CI/CD workflows
├── docs/                  # Documentation
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pytest.ini            # Pytest configuration
└── Makefile              # Build automation
```

The codebase is organized around two main tasks:
- **Scraping/Analysis** (`src/scrape/`) - Weekly data collection and matrix generation
- **Website Generation** (`src/website/`) - Static site from analysis outputs
- **Shared utilities** (`src/shared/`) - Common code used by both modules

For detailed module information, see the project's main README or explore the `src/` directory.

---

## Code Style

- Follow **PEP 8** conventions
- Use absolute imports with module prefixes (`from shared.config import ...`)
- Use UTF-8 encoding for file operations
- Use assertions from `shared.assertions` for validation
- Normalize whitespace with `shared.parsing.normalize_whitespace()`
- Define regex patterns in `shared.config` for reusability

---

## Questions or Issues?

Open an issue on [GitHub](https://github.com/christianacca/spidershop-historical-analysis/issues) or reach out to the maintainer.

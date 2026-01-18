# Contributing to spidershop-historical-analysis

This guide walks you through setting up a local development environment from scratch, even if you've never used Python before.

**Quick Links:**
- 🧪 [Running Tests & Coverage](#running-tests)
- 🌐 [Local Development Workflows](#local-development-workflows) - Website testing and scraper usage
- 🐛 [Troubleshooting](#troubleshooting)

**Choose your operating system below and follow all steps in order:**

- [macOS Setup](#macos-setup)
- [Windows Setup](#windows-setup)
- [Linux Setup](#linux-setup)

---

## macOS Setup

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

---

## Windows Setup

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

---

## Linux Setup

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

---

## Running Tests

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

### Run all tests
```sh
pytest
```

### Run with verbose output
```sh
pytest -v
```

### Run a specific test file
```sh
pytest tests/test_breeder_matrix.py
```

### Run tests with coverage
```sh
pytest --cov=src --cov-report=term-missing
```

This shows in the terminal:
- Overall coverage percentage
- Coverage per module
- **Missing column**: Specific line numbers that aren't tested (e.g., "15-22, 34-40")

### View interactive HTML coverage report
```sh
# Generate HTML report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

The HTML report provides:
- Visual coverage with color-coded lines (green = tested, red = not tested)
- Module-by-module breakdown
- Easy navigation through source files

### Check coverage for a specific module
```sh
# Using built-in coverage tool
pytest tests/test_breeder_matrix.py --cov=src.breeder_matrix --cov-report=term-missing

# Using helper script (faster)
python check_coverage.py --module=breeder_matrix.py --verbose
```

### View coverage summary
```sh
python view_coverage.py
```

This displays a formatted table showing coverage for all modules.

---

## Local Development Workflows

This section covers testing website changes and running the scraper locally without pushing to GitHub.

> **⚠️ Remember:** Activate your virtual environment before running any commands!
> ```sh
> source .venv/bin/activate          # macOS/Linux
> .venv\Scripts\activate.bat         # Windows (CMD)
> .venv\Scripts\Activate.ps1         # Windows (PowerShell)
> ```

### Quick Start

Choose your workflow based on your needs:

```sh
# Using GitHub Actions data (fast, requires GitHub CLI)
make remote-website-serve

# Using local scraper (no GitHub dependency, requires Chrome)
make local-website-serve

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
# Download artifacts and generate website
make remote-website

# Download artifacts, generate website, and serve locally at http://localhost:8000
make remote-website-serve
```

This downloads the latest scrape results from GitHub Actions, generates the static website in `tmp/local-testing/website/`, and optionally starts a local server.

### Option 2: Using Local Data (Run Scraper)

**Prerequisites:** Chrome already installed (from setup section above)

**Workflow:**

```bash
# Scrape locally and generate website
make local-website

# Scrape locally, generate website, and serve at http://localhost:8000
make local-website-serve

# Or just run the scraper without generating the website
make scrape-local
```

This runs the scraper to generate fresh data, creates the website, and optionally serves it locally.

### Available Makefile Commands

Run `make help` to see all available commands:

**Main Workflows:**
- `make local-website` - Run scraper locally → generate website
- `make local-website-serve` - Run scraper locally → generate website → serve
- `make remote-website` - Download from GitHub Actions → generate website
- `make remote-website-serve` - Download from GitHub Actions → generate website → serve

**Individual Steps:**
- `make scrape-local` - Run scraper locally (outputs CSV to `tmp/local-testing/`)
- `make download-artifacts` - Download latest artifacts from GitHub Actions
- `make generate-website` - Generate website from existing CSV files

**Testing:**
- `make test` - Run pytest with coverage
- `make coverage` - View coverage report in browser

**Cleanup:**
- `make clean-artifacts` - Remove `tmp/local-testing/` directory
- `make clean-all` - Clean artifacts + test cache + coverage reports

### Advanced Usage

**Iterative development workflow** - When making changes to `generate_website.py`:

```bash
# 1. Get data (only needed once)
make download-artifacts  # OR: make scrape-local

# 2. Make changes to src/generate_website.py
# ... edit files ...

# 3. Regenerate website (CSV files already exist)
make generate-website

# 4. Preview in browser
cd tmp/local-testing/website && python3 -m http.server 8000
# Open http://localhost:8000

# 5. Repeat steps 2-4 as needed
```

**Using a custom port:**

```bash
python3 test_website_locally.py --serve --port 3000
```

**Compare local vs remote data:**

```bash
make remote-website
mv tmp/local-testing/website tmp/local-testing/website-remote

make local-website
mv tmp/local-testing/website tmp/local-testing/website-local

diff -r tmp/local-testing/website-remote tmp/local-testing/website-local
```

### Workflow Comparison

| Task | Remote (GitHub Actions) | Local (Scraper) |
|------|------------------------|-----------------|
| **Data Source** | Latest successful workflow run | Fresh scrape from website |
| **Speed** | Fast (download only) | Slower (full scrape) |
| **Requirements** | GitHub CLI (`gh`) | Chrome/Chromium (already installed) |
| **Network** | GitHub API only | Full website scraping |
| **Use Case** | Quick testing with real data | Testing scraper changes, no GitHub dependency |
| **Command** | `make remote-website-serve` | `make local-website-serve` |

### Files and Directories

All local development files are stored in `tmp/local-testing/` (gitignored):
- `*.csv` - Scraper output or downloaded CSV files
- `analysis_summary.md` - Analysis summary (downloaded or generated)
- `website/` - Generated HTML files

**Scripts:**
- `test_website_locally.py` - Website generation script
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
python test_website_locally.py --serve
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
python3 test_website_locally.py --serve --port 3000
```

---

## Project Structure

```
spidershop-historical-analysis/
├── src/                   # Source code modules
├── tests/                 # Test suite
├── .github/workflows/     # CI/CD workflows
├── docs/                  # Documentation
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pytest.ini            # Pytest configuration
└── Makefile              # Build automation
```

For a complete list of modules and their purposes, see the project's main README or explore the `src/` directory.

---

## Code Style

- Follow **PEP 8** conventions
- Use absolute imports from `src/` modules
- Use UTF-8 encoding for file operations
- Use assertions from `assertions.py` for validation
- Normalize whitespace with `parsing.normalize_whitespace()`
- Define regex patterns in `config.py` for reusability

---

## Questions or Issues?

Open an issue on [GitHub](https://github.com/christianacca/spidershop-historical-analysis/issues) or reach out to the maintainer.

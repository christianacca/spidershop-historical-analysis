# Contributing to spidershop-historical-analysis

This guide walks you through setting up a local development environment from scratch, even if you've never used Python before.

**Quick Links:**
- 🧪 [Running Tests & Coverage](#running-tests) - Jump directly to testing

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

### Step 3: Install Chrome

Download from [google.com/chrome](https://www.google.com/chrome/)

### Step 4: Clone the Repository

```sh
cd ~/Documents  # or wherever you keep projects
git clone https://github.com/christianacca/spidershop-historical-analysis.git
cd spidershop-historical-analysis
```

### Step 5: Create a Virtual Environment

A virtual environment isolates this project's dependencies from your system Python.

```sh
python3 -m venv .venv
```

This creates a `.venv/` directory (which is gitignored).

### Step 6: Activate the Virtual Environment

```sh
source .venv/bin/activate
```

After activation, your terminal prompt should show `(.venv)` at the beginning.

### Step 7: Install Dependencies

```sh
# Install production dependencies
pip install requests beautifulsoup4 selenium

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

### Step 3: Install Chrome/Chromium

```sh
sudo apt install chromium-browser
```

### Step 4: Clone the Repository

```sh
cd ~/Documents  # or wherever you keep projects
git clone https://github.com/christianacca/spidershop-historical-analysis.git
cd spidershop-historical-analysis
```

### Step 5: Create a Virtual Environment

A virtual environment isolates this project's dependencies from your system Python.

```sh
python3 -m venv .venv
```

This creates a `.venv/` directory (which is gitignored).

### Step 6: Activate the Virtual Environment

```sh
source .venv/bin/activate
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

## Running the Scraper

### Full scraper execution
```sh
python src/scrape_spidershop_spiderlings.py
```

This will:
1. Scrape current spiderling listings
2. Update historical data
3. Generate analysis matrices
4. Output CSV files and markdown summaries

### Generate website locally
```sh
python src/generate_website.py
```

The static website will be generated in the `website/` directory.

---

## Deactivating the Virtual Environment

When you're done working:

```sh
deactivate
```

---

## Troubleshooting

### `command not found: python`
- **macOS/Linux**: Try `python3` instead of `python`
- **Windows**: Reinstall Python and ensure "Add Python to PATH" is checked

### Chrome/ChromeDriver version mismatch
Selenium should auto-download the correct ChromeDriver. If you encounter issues:
```sh
pip install --upgrade selenium
```

### Permission denied when activating virtual environment (macOS/Linux)
```sh
chmod +x .venv/bin/activate
```

### ModuleNotFoundError
Make sure your virtual environment is activated **before** running scripts.

**Activate command:**
- **macOS/Linux**: `source .venv/bin/activate`
- **Windows CMD**: `.venv\Scripts\activate.bat`
- **Windows PowerShell**: `.venv\Scripts\Activate.ps1`

---

## Project Structure

```
spidershop-historical-analysis/
├── src/                          # Source code modules
│   ├── scrape_spidershop_spiderlings.py  # Main entry point
│   ├── scraper.py               # Core scraping logic
│   ├── browser_client.py        # Selenium wrapper
│   ├── http_client.py           # HTTP requests
│   ├── parsing.py               # Text parsing utilities
│   ├── config.py                # Configuration constants
│   ├── history.py               # Historical data management
│   ├── breeder_matrix.py        # Breeder analysis
│   ├── dealer_matrix.py         # Dealer analysis
│   ├── pricing_summary.py       # Pricing summaries
│   ├── legend.py                # Legend generation
│   ├── wishlist_analysis.py     # Wishlist metrics
│   └── generate_website.py      # Static site generator
├── tests/                        # Test suite
│   └── test_example.py
├── .github/workflows/            # CI/CD workflows
├── pytest.ini                    # pytest configuration
├── requirements-dev.txt          # Development dependencies
└── docs/
    └── CONTRIBUTING.md           # This file
```

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

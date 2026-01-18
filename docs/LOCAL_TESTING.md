# Local Website Testing Guide

This guide explains how to test `generate_website.py` changes locally without pushing to GitHub.

> **Prerequisites:** This guide assumes you've already completed the setup in [CONTRIBUTING.md](CONTRIBUTING.md) (Python, virtual environment, Git, Make, and project dependencies installed).

## Additional Tool Required

### GitHub CLI (`gh`)

Required to download artifacts from GitHub Actions workflow runs.

```bash
# macOS
brew install gh

# Windows (using winget)
winget install --id GitHub.cli

# Windows (using Chocolatey)
choco install gh

# Linux (Debian/Ubuntu)
sudo apt install gh

# Authenticate (all platforms)
gh auth login
```

---

## Quick Start

> **⚠️ Remember:** Activate your virtual environment first!
> ```bash
> source .venv/bin/activate          # macOS/Linux
> .venv\Scripts\activate.bat         # Windows (CMD)
> .venv\Scripts\Activate.ps1         # Windows (PowerShell)
> ```

### Using Makefile (macOS/Linux/Git Bash)

```bash
# Download artifacts and generate website
make test-website

# Download artifacts, generate website, and serve locally
make test-website-serve
```

**Note:** On Windows, use Git Bash, WSL, or install `make` via Chocolatey. Alternatively, use the Python commands below.

### Using Python directly

#### Option 1: Download artifacts and generate website

```bash
# Download latest artifacts from GitHub Actions and generate website
python3 test_website_locally.py

# Then serve the website locally
python3 test_website_locally.py --serve
```

#### Option 2: Download and serve in one command

```bash
# Download artifacts, generate website, and start local server
python3 test_website_locally.py --serve
```

**Windows Note:** Use `python` instead of `python3` if `python3` is not recognized:
```cmd
python test_website_locally.py --serve
```

The website will be available at http://localhost:8000

## Usage Examples

### Test with latest workflow run

```bash
# Download latest artifacts and generate website
python3 test_website_locally.py
```

### Test with specific workflow run

```bash
# Use a specific run ID (find on GitHub Actions page)
python3 test_website_locally.py --run-id 12345678
```

### Regenerate website without re-downloading

```bash
# Skip download if you already have the artifacts
python3 test_website_locally.py --skip-download

# Or regenerate and serve immediately
python3 test_website_locally.py --skip-download --serve
```

### Use custom port for local server

```bash
# Serve on port 3000 instead of default 8000
python3 test_website_locally.py --serve --port 3000
```

## Workflow

The `test_website_locally.py` script automates this workflow:

1. **Find latest successful workflow run** - Queries GitHub API for the most recent successful "Spider Shop Spiderlings Scrape" workflow
2. **Download artifacts** - Downloads these artifacts to `tmp/local-testing/`:
   - `spidershop-snapshot` → `spidershop_spiderlings_scrape.csv`
   - `spidershop-history` → `spidershop_spiderlings_history.csv`
   - `breeder-opportunity-table` → `breeder_opportunity_table.csv`
   - `dealer-supply-risk-table` → `dealer_supply_risk_table.csv`
   - `analysis-summary` → `analysis_summary.md`
3. **Generate website** - Runs `src/generate_website.py` to create HTML files in `tmp/local-testing/website/`
4. **Serve locally** (optional) - Starts HTTP server to preview the website

All downloaded artifacts and generated files are stored in `tmp/local-testing/` which is gitignored, keeping your project root clean.

## Manual Testing

If you prefer to do steps manually:

```bash
# 1. Download artifacts (this script handles it)
python3 test_website_locally.py

# 2. Make changes to src/generate_website.py
# ... edit files ...

# 3. Regenerate website
python3 test_website_locally.py --skip-download

# 4. Preview in browser
cd tmp/local-testing/website
python3 -m http.server 8000
# Open http://localhost:8000
```

## Troubleshooting

### "GitHub CLI (gh) is not installed"

Install and authenticate:
```bash
# macOS
brew install gh

# Windows (winget)
winget install --id GitHub.cli

# Windows (Chocolatey)
choco install gh

# Linux (Debian/Ubuntu)
sudo apt install gh

# Authenticate (all platforms)
gh auth login
```

### "make: command not found" (Windows)

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

4. **Use Python commands directly** (no `make` needed):
   ```cmd
   python test_website_locally.py --serve
   ```

### "python3: command not found" (Windows)

On Windows, use `python` instead of `python3`:
```cmd
python test_website_locally.py --serve
```

Or add a Python 3 alias:
```powershell
# PowerShell
Set-Alias python3 python
```

### "No successful runs found"

Make sure the scrape workflow has run successfully at least once. You can trigger it manually:
```bash
gh workflow run "Spider Shop Spiderlings Scrape" --repo christianacca/spidershop-historical-analysis
```

### "Artifact not found"

Some artifacts may not exist on older runs. The script will skip missing artifacts and continue.

### Port already in use

Change the port:
```bash
python3 test_website_locally.py --serve --port 3000
```

## Next Steps (Future Enhancement)

The next phase would be to run the scraper locally to generate fresh data:

```bash
# Future enhancement - not yet implemented
python3 src/scrape_spidershop_spiderlings.py --local
python3 test_website_locally.py --skip-download --serve
```

This would eliminate the need to download artifacts from GitHub Actions entirely.

## Files Created

- `test_website_locally.py` - Main testing script
- `tmp/local-testing/` - All downloaded artifacts and generated files (gitignored)
  - `*.csv` - Downloaded CSV files
  - `analysis_summary.md` - Downloaded analysis summary
  - `website/` - Generated HTML files
  - `artifacts_temp/` - Temporary download directory (auto-cleaned)

## Clean Up

To clean up downloaded files:

```bash
# Using Makefile
make clean-artifacts

# Or manually
rm -rf tmp/local-testing/
```

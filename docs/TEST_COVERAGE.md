# Test Coverage Guide

## Overview

This project uses `pytest-cov` (built on `coverage.py`) to measure and report test coverage. Coverage reports are available in multiple formats:

- **Terminal output**: Quick summary when running tests locally
- **HTML reports**: Interactive, browsable coverage visualization
- **JSON reports**: Machine-readable for CI/CD and agent consumption
- **Markdown summaries**: Human-readable summaries in GitHub Actions

## Running Tests with Coverage Locally

### Basic Coverage Report

Run tests with terminal coverage summary:

```bash
pytest tests/ --cov=src --cov-report=term-missing -v
```

This shows:
- Overall coverage percentage
- Line-by-line coverage for each module
- Which lines are missing coverage (not executed by tests)

### Generate HTML Coverage Report

For a detailed, interactive HTML report:

```bash
pytest tests/ --cov=src --cov-report=html -v
```

Then open the report in your browser:

```bash
open htmlcov/index.html
```

The HTML report provides:
- Module-by-module coverage breakdown
- Color-coded line highlighting (green = covered, red = not covered)
- Branch coverage visualization
- Easy navigation through source files

### Generate All Report Formats

To generate HTML, JSON, and terminal reports simultaneously:

```bash
pytest tests/ \
  --cov=src \
  --cov-report=html \
  --cov-report=json \
  --cov-report=term-missing \
  -v
```

This creates:
- `htmlcov/` directory with HTML report
- `coverage.json` with machine-readable data
- Terminal output with missing lines

### Coverage for Specific Modules

Test coverage for a single module:

```bash
pytest tests/test_breeder_matrix.py --cov=src.breeder_matrix --cov-report=term-missing
```

## GitHub Actions Integration

### Automated Test Workflow

The `.github/workflows/test.yml` workflow automatically:

1. **Runs on**:
   - Push to `master` or `refactor-modules` branches
   - Pull requests to `master`
   - Manual trigger via `workflow_dispatch`

2. **Generates reports**:
   - HTML coverage report (uploaded as artifact)
   - JSON coverage data (uploaded as artifact)
   - Markdown summary (uploaded as artifact)
   - Terminal output in workflow logs

3. **Uploads artifacts** (retained for 90 days):
   - `test-coverage-report` - Full HTML report
   - `coverage-json` - JSON data for programmatic access
   - `coverage-summary` - Markdown summary

4. **Adds PR comments** with coverage summary (for pull requests)

5. **Enforces threshold**: Fails if coverage drops below 80%

### Viewing Coverage in GitHub Actions

#### From Workflow Run

1. Go to **Actions** tab in GitHub
2. Click on a workflow run
3. Scroll to **Artifacts** section at the bottom
4. Download `test-coverage-report.zip`
5. Extract and open `index.html` in your browser

#### From Pull Request

Coverage summary is automatically posted as a PR comment, showing:
- Total coverage percentage
- Per-module breakdown
- Link to download full HTML report

## Agent Mode Integration

### For AI/Agent Consumption

The `coverage.json` file provides structured data that agents can parse to verify test coverage:

```python
import json

# Load coverage data
with open('coverage.json') as f:
    coverage_data = json.load(f)

# Get overall coverage
total_coverage = coverage_data['totals']['percent_covered']
print(f"Total coverage: {total_coverage:.2f}%")

# Get per-file coverage
for filepath, stats in coverage_data['files'].items():
    if 'src/' in filepath:
        module_name = filepath.split('/')[-1]
        coverage_pct = stats['summary']['percent_covered']
        missing_lines = stats['summary']['missing_lines']
        print(f"{module_name}: {coverage_pct:.2f}% ({missing_lines} lines missing)")
```

### Agents Should:

1. **Before code changes**: Run coverage to establish baseline
2. **After code changes**: Re-run coverage to verify:
   - New code has tests
   - Existing coverage didn't decrease
   - Target threshold (80%) is maintained
3. **Use JSON output**: Parse `coverage.json` for programmatic verification

Example agent workflow:

```bash
# Run tests and generate JSON
pytest tests/ --cov=src --cov-report=json -v

# Agent parses coverage.json to verify:
# - New functions have test coverage
# - Coverage meets or exceeds 80% threshold
# - No existing coverage was lost
```

## Coverage Configuration

### .coveragerc Settings

Coverage behavior is configured in [.coveragerc](.coveragerc):

- **Source**: Only `src/` directory is measured
- **Omit**: Test files and virtual environments are excluded
- **Threshold**: Minimum 80% coverage required (configurable)
- **Exclusions**: Defensive code, debug statements, and abstract methods excluded

### Adjusting Coverage Threshold

To change the minimum coverage percentage, edit `.coveragerc`:

```ini
[report]
fail_under = 80  # Change this value
```

Also update the threshold in `.github/workflows/test.yml` (line with `THRESHOLD=80`).

## Best Practices

### For Developers

1. **Run coverage locally** before pushing code
2. **Aim for 80%+ coverage** on new code
3. **Review HTML report** to find untested code paths
4. **Test edge cases** and error handling
5. **Don't game the metric** - write meaningful tests

### For QA Engineers

1. **Monitor coverage trends** across releases
2. **Download HTML reports** from GitHub Actions artifacts
3. **Review uncovered code** to identify testing gaps
4. **Focus on critical paths** - not all code needs 100% coverage
5. **Use coverage as a guide**, not a goal - quality matters more than percentage

### For CI/CD

1. Coverage reports are available as **downloadable artifacts**
2. Coverage JSON is **machine-readable** for automated analysis
3. Workflow **fails if coverage drops below threshold**
4. PR comments provide **immediate feedback** without leaving GitHub

## Troubleshooting

### Missing Coverage Data

If coverage shows 0% or missing modules:

1. Ensure you're running from project root
2. Check that `src/` directory exists in path
3. Verify tests are actually running (`pytest -v`)

### HTML Report Not Generated

```bash
# Explicitly specify HTML output
pytest tests/ --cov=src --cov-report=html

# Check that htmlcov/ directory was created
ls htmlcov/
```

### Coverage JSON Not Found

```bash
# Generate JSON explicitly
pytest tests/ --cov=src --cov-report=json

# Verify file was created
cat coverage.json | python -m json.tool
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pytest --cov=src --cov-report=term` | Quick terminal summary |
| `pytest --cov=src --cov-report=html` | Generate HTML report |
| `pytest --cov=src --cov-report=json` | Generate JSON for agents |
| `pytest --cov=src --cov-report=term-missing` | Show missing lines |
| `open htmlcov/index.html` | View HTML report (macOS) |
| `coverage report` | Show terminal summary from .coverage file |
| `coverage html` | Regenerate HTML from existing .coverage file |

## File Locations

- **Coverage config**: `.coveragerc`
- **HTML reports**: `htmlcov/` (gitignored)
- **JSON data**: `coverage.json` (gitignored)
- **Raw data**: `.coverage` (gitignored)
- **Test workflow**: `.github/workflows/test.yml`
- **Artifacts**: GitHub Actions → Workflow run → Artifacts section

## Additional Resources

- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [coverage.py documentation](https://coverage.readthedocs.io/)
- [GitHub Actions artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)

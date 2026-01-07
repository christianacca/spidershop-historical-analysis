# Test Coverage Implementation Details

> **Note:** This document describes how test coverage was set up. For practical usage, see [CONTRIBUTING.md](CONTRIBUTING.md#running-tests).

## Overview

I've set up comprehensive test coverage tooling for your project with the following components:

### 1. **pytest-cov Integration** 
   - Added `pytest-cov` to `requirements-dev.txt`
   - Configured via `.coveragerc` with 80% threshold
   - Generates HTML, JSON, and terminal reports

### 2. **GitHub Actions Workflow**
   - Created `.github/workflows/test.yml`
   - Runs on push to master/refactor-modules and PRs
   - Generates and uploads coverage reports as artifacts
   - Posts coverage summary to PR comments
   - Fails if coverage drops below 80%

### 3. **Local Development Tools**
   - `view_coverage.py` - Visual coverage summary
   - `check_coverage.py` - Module-specific coverage checker
   - HTML reports in `htmlcov/` directory

### 4. **Coverage Configuration**
   - `.coveragerc` - Coverage settings
   - `.gitignore` - Excludes coverage artifacts
   - `docs/TEST_COVERAGE.md` - Full documentation

---

## How to Use (Quick Reference)

### For You (Developer/QA)

**Run tests with coverage:**
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v
```

**View HTML report:**
```bash
open htmlcov/index.html
```

**View terminal summary:**
```bash
python view_coverage.py
```

**Check specific module:**
```bash
python check_coverage.py --module=breeder_matrix.py
```

### For GitHub Actions

Coverage reports are automatically:
- ✅ Generated on every test run
- ✅ Uploaded as artifacts (90-day retention)
- ✅ Posted as PR comments
- ✅ Available for download from Actions tab

**To download coverage from GitHub:**
1. Go to Actions tab
2. Click any workflow run
3. Scroll to Artifacts section
4. Download `test-coverage-report.zip`
5. Extract and open `index.html`

### For Agent Mode

Agents can verify coverage programmatically:

```python
import json

# Load coverage data
with open('coverage.json') as f:
    data = json.load(f)

# Check overall coverage
total = data['totals']['percent_covered']
print(f"Coverage: {total:.2f}%")

# Check specific module
for file, stats in data['files'].items():
    if 'breeder_matrix.py' in file:
        coverage = stats['summary']['percent_covered']
        print(f"breeder_matrix.py: {coverage:.2f}%")
```

Or use the helper scripts:
```bash
# Check if module meets threshold
python check_coverage.py --module=breeder_matrix.py

# View formatted summary
python view_coverage.py
```

---

## Current Coverage Status

Based on the test run:

| Module | Coverage | Status | Notes |
|--------|----------|--------|-------|
| **breeder_matrix.py** | 81.25% | ✅ | Fully tested |
| **wishlist_analysis.py** | 82.65% | ✅ | Fully tested |
| **config.py** | 100.00% | ✅ | Configuration only |
| **history.py** | 54.17% | ⚠️ | Partial coverage |
| **assertions.py** | 29.41% | ❌ | Needs tests |
| **Other modules** | 0.00% | ❌ | Not tested yet |
| **OVERALL** | **26.49%** | ❌ | Below 80% threshold |

---

## Files Created/Modified

### New Files
- ✅ `.coveragerc` - Coverage configuration
- ✅ `.github/workflows/test.yml` - GitHub Actions test workflow
- ✅ `view_coverage.py` - Coverage summary viewer
- ✅ `check_coverage.py` - Module coverage checker
- ✅ `docs/TEST_COVERAGE.md` - Full documentation
- ✅ `tests/test_breeder_matrix.py` - Comprehensive tests (19 tests)

### Modified Files
- ✅ `requirements-dev.txt` - Added pytest-cov
- ✅ `.gitignore` - Added coverage artifacts

---

## What Happens in GitHub Actions

When you push code or create a PR:

1. **Test workflow runs** (`.github/workflows/test.yml`)
2. **Installs dependencies** (including pytest-cov)
3. **Runs all tests** with coverage tracking
4. **Generates reports**:
   - HTML report for visual inspection
   - JSON report for programmatic access
   - Markdown summary for quick review
5. **Uploads artifacts** (available for 90 days):
   - `test-coverage-report` (HTML)
   - `coverage-json` (JSON data)
   - `coverage-summary` (Markdown)
6. **Posts PR comment** with coverage summary (on PRs)
7. **Checks threshold** - fails if below 80%

---

## Agent Mode Usage

When an agent is making code changes, it should:

### Before Making Changes
```bash
# Run tests and capture baseline coverage
pytest tests/ --cov=src --cov-report=json -v
python view_coverage.py > before-coverage.txt
```

### After Making Changes
```bash
# Run tests with new code
pytest tests/ --cov=src --cov-report=json -v

# Check specific module coverage
python check_coverage.py --module=new_module.py --threshold=80

# Verify overall coverage didn't drop
python view_coverage.py
```

### For Verification
The agent can parse `coverage.json` to verify:
- New functions have test coverage
- Existing coverage wasn't lost
- Threshold requirements are met

Example agent verification code:
```python
import json

def verify_coverage_for_module(module_name, min_coverage=80.0):
    """Verify a module meets minimum coverage threshold."""
    with open('coverage.json') as f:
        data = json.load(f)
    
    for filepath, stats in data['files'].items():
        if filepath.endswith(module_name):
            coverage = stats['summary']['percent_covered']
            
            if coverage >= min_coverage:
                print(f"✅ {module_name}: {coverage:.2f}% (meets {min_coverage}% threshold)")
                return True
            else:
                print(f"❌ {module_name}: {coverage:.2f}% (below {min_coverage}% threshold)")
                return False
    
    print(f"❌ {module_name} not found in coverage data")
    return False

# Usage
verify_coverage_for_module('breeder_matrix.py', 80.0)
```

---

## Tips for QA Engineers

### Visual Coverage Inspection

The HTML report (`htmlcov/index.html`) provides:
- **Red highlighting**: Lines not executed by tests
- **Green highlighting**: Lines executed by tests
- **Excluded lines**: Grayed out (e.g., debugging code)
- **Navigation**: Click module names to see source code
- **Branch coverage**: Shows which code paths were taken

### Finding Testing Gaps

1. Open HTML report: `open htmlcov/index.html`
2. Sort by coverage (click "Cover" column header)
3. Focus on modules with low coverage
4. Click module name to see specific uncovered lines
5. Red lines indicate code paths not tested

### Coverage Trends

To track coverage over time:
1. Download JSON artifacts from multiple workflow runs
2. Compare `percent_covered` values
3. Monitor for coverage regressions

### Best Practices

- ✅ Run coverage before committing
- ✅ Aim for 80%+ on new code
- ✅ Review HTML report for gaps
- ✅ Test edge cases and error paths
- ❌ Don't game the metric
- ❌ Don't aim for 100% everywhere (diminishing returns)

---

## Troubleshooting

### "coverage.json not found"
```bash
# Generate the JSON file
pytest tests/ --cov=src --cov-report=json
```

### "Coverage shows 0%"
```bash
# Ensure you're in project root
cd /path/to/spidershop-historical-analysis

# Run with verbose output
pytest tests/ --cov=src --cov-report=term -v
```

### "Can't open HTML report"
```bash
# Check if directory exists
ls htmlcov/

# Regenerate if missing
pytest tests/ --cov=src --cov-report=html
```

### "Tests pass but coverage fails"
This means coverage is below 80% threshold (currently 26.49%). This is expected since most modules don't have tests yet.

To bypass the threshold check temporarily:
```bash
# Run without checking threshold
pytest tests/ --cov=src --cov-report=term --no-cov-fail-under
```

---

## Next Steps

To improve overall coverage to 80%+, prioritize testing:

1. **parsing.py** (0% → 80%+) - Core parsing functions
2. **scraper.py** (0% → 80%+) - Web scraping logic  
3. **dealer_matrix.py** (0% → 80%+) - Dealer analysis (similar to breeder_matrix)
4. **history.py** (54% → 80%+) - Finish remaining functions
5. **assertions.py** (29% → 80%+) - Utility functions

Each module test should follow the pattern in `tests/test_breeder_matrix.py`:
- Use synthetic data
- Cover all branches
- Test edge cases
- Clear test names

---

## Documentation

- **Development guide**: [CONTRIBUTING.md](CONTRIBUTING.md#running-tests) - **Start here for running tests**
- **Full reference**: [TEST_COVERAGE.md](TEST_COVERAGE.md) - Complete documentation
- **Implementation details**: [COVERAGE_IMPLEMENTATION.md](COVERAGE_IMPLEMENTATION.md) - This document

---

## Summary

You now have a complete test coverage infrastructure that:

✅ **Works locally** - HTML and terminal reports  
✅ **Works in CI/CD** - GitHub Actions integration  
✅ **Works for agents** - JSON output for programmatic access  
✅ **Visual reports** - Interactive HTML coverage browser  
✅ **Automated checks** - Fails if coverage drops below 80%  
✅ **PR integration** - Automatic coverage comments on PRs  
✅ **Long retention** - 90-day artifact storage  
✅ **Easy to use** - Helper scripts for common tasks  

The foundation is in place. Now it's just a matter of writing tests for the remaining modules! 🚀

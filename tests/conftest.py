#!/usr/bin/env python3
"""
Shared test fixtures and utilities for all test modules.
"""
import os
import sys
from pathlib import Path
import pytest

# Add src directory to Python path to enable imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import make_row from legend_examples (production code)
from scrape.legend_examples import make_row

# Import test helpers
from helpers.test_helpers import (
    HistoryEntry,
    BreederEntry,
    DealerEntry,
    create_temp_markdown_file,
    create_temp_csv_file,
    temp_csv_file,
    write_csv_file,
    read_file_content,
    create_csv_content,
    create_breeder_csv_content,
    create_dealer_csv_content,
    create_history_csv_content,
)

__all__ = [
    'make_row',
    'HistoryEntry',
    'BreederEntry',
    'DealerEntry',
    'create_temp_markdown_file',
    'create_temp_csv_file',
    'temp_csv_file',
    'write_csv_file',
    'read_file_content',
    'create_csv_content',
    'create_breeder_csv_content',
    'create_dealer_csv_content',
    'create_history_csv_content',
]


def pytest_addoption(parser):
    """Add command-line options for test configuration."""
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run Playwright tests in headed mode (visible browser)",
    )


@pytest.fixture(autouse=True)
def isolate_test_execution(request, tmp_path, monkeypatch):
    """
    Isolate test execution to prevent file pollution in project root.
    
    This fixture:
    1. Changes working directory to a temporary directory for each test
    2. Ensures GITHUB_STEP_SUMMARY is set for production parity
    3. Maintains Python path to src directory
    
    This prevents tests from creating CSV, HTML, or other artifacts in the
    project root directory. All file operations in tests will be relative
    to the temporary directory, which is automatically cleaned up.
    
    E2E tests are excluded from isolation as they need to run from project root
    to match CI behavior and generate artifacts in expected locations.
    """
    # Skip isolation for e2e tests (they need to run from project root)
    if "e2e" in request.keywords:
        yield
        return
    
    # Save original directory
    original_dir = Path.cwd()
    
    # Change to temporary directory for test execution
    os.chdir(tmp_path)
    
    # Ensure GITHUB_STEP_SUMMARY is set (for production parity)
    if "GITHUB_STEP_SUMMARY" not in os.environ:
        summary_file = tmp_path / "github_step_summary.md"
        summary_file.touch()
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    
    # Ensure PYTHONPATH includes the original src directory
    # (since we changed CWD, relative imports might break)
    src_path = original_dir / "src"
    monkeypatch.setenv("PYTHONPATH", f"{src_path}:{os.environ.get('PYTHONPATH', '')}")
    
    # Yield control back to the test
    yield
    
    # Restore original directory after test completes
    os.chdir(original_dir)

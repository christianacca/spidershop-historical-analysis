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
    create_temp_markdown_file,
    create_temp_csv_file,
    write_csv_file,
    read_file_content,
    create_csv_content,
    create_breeder_csv_content,
    create_dealer_csv_content,
    create_history_csv_content,
)

__all__ = [
    'make_row',
    'create_temp_markdown_file',
    'create_temp_csv_file',
    'write_csv_file',
    'read_file_content',
    'create_csv_content',
    'create_breeder_csv_content',
    'create_dealer_csv_content',
    'create_history_csv_content',
]


@pytest.fixture(autouse=True)
def ensure_github_env(monkeypatch, tmp_path):
    """
    Ensure GITHUB_STEP_SUMMARY is always set during tests to match production.
    
    Production code always runs in GitHub Actions where GITHUB_STEP_SUMMARY is set.
    This fixture ensures tests run in a similar environment, preventing environment-
    dependent test behavior where tests pass locally but fail in CI (or vice versa).
    
    Sets GITHUB_STEP_SUMMARY to a temporary file that tests can write to.
    Tests that need to verify "no env var" behavior can explicitly remove it
    using monkeypatch.delenv("GITHUB_STEP_SUMMARY").
    """
    # Only set if not already set (respect existing CI environment)
    if "GITHUB_STEP_SUMMARY" not in os.environ:
        summary_file = tmp_path / "github_step_summary.md"
        summary_file.touch()
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

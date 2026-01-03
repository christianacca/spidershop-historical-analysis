#!/usr/bin/env python3
import os
from config import ANALYSIS_SUMMARY_FILE

# =====================
# ASSERTION HELPERS (ADDED)
# =====================

def assert_condition(condition: bool, message: str):
    if not condition:
        raise SystemExit(f"ASSERTION FAILED: {message}")

def get_summary_path():
    return os.environ.get("GITHUB_STEP_SUMMARY")

def get_summary_paths():
    """Returns list of paths to write summary markdown to.
    Includes both GITHUB_STEP_SUMMARY (for workflow UI) and ANALYSIS_SUMMARY_FILE (for artifact upload).
    """
    paths = []
    github_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if github_summary:
        paths.append(github_summary)
    paths.append(ANALYSIS_SUMMARY_FILE)
    return paths

def read_summary_text() -> str:
    path = get_summary_path()
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def csv_row_count(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in f) - 1  # minus header

#!/usr/bin/env python3
import os

# =====================
# ASSERTION HELPERS (ADDED)
# =====================

def assert_condition(condition: bool, message: str):
    if not condition:
        raise SystemExit(f"ASSERTION FAILED: {message}")

def get_summary_path():
    return os.environ.get("GITHUB_STEP_SUMMARY")

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

def extract_markdown_section(markdown_text: str, section_heading: str) -> str:
    """
    Extract a markdown section starting with the given heading.
    
    Args:
        markdown_text: Full markdown content
        section_heading: The heading to search for (e.g., "## 🏪 Dealer Supply Risk Matrix")
    
    Returns:
        The extracted section including the heading, or empty string if not found
    """
    lines = markdown_text.split('\n')
    table_start = None
    table_end = None
    
    for i, line in enumerate(lines):
        if line.startswith(section_heading):
            table_start = i
        # Table ends at next section heading or significant empty space after table
        if table_start is not None and table_end is None:
            if i > table_start and (line.startswith("##") or (i > table_start + 10 and not line.strip())):
                table_end = i
                break
    
    # If no end found, take until end of content
    if table_start is not None and table_end is None:
        table_end = len(lines)
    
    if table_start is None:
        return ""
    
    return '\n'.join(lines[table_start:table_end]).strip()

"""CSV file utilities for reading data files.

This module handles CSV file operations for the website generator.
"""

import csv
import os
from typing import Optional, List, Tuple


def read_csv_file(filepath: str) -> Tuple[Optional[List[str]], List[List[str]]]:
    """Read a CSV file and return headers and rows.
    
    Args:
        filepath: Path to CSV file
        
    Returns:
        Tuple of (headers, rows) where:
        - headers: List of column names (None if file doesn't exist)
        - rows: List of data rows (empty list if file doesn't exist)
    """
    if not os.path.exists(filepath):
        return None, []
    
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        rows = list(reader)
    return headers, rows

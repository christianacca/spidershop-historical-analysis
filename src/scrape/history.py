#!/usr/bin/env python3
import csv
import os
from typing import List, Dict, Any
from shared.config import CSV_HEADER
from shared.history_utils import group_by_run, k2, k3

# =====================
# HISTORY
# =====================

def load_history(path: str) -> List[Dict[str, Any]]:
    """Load historical CSV data from file.
    
    Args:
        path: Path to history CSV file
        
    Returns:
        List of row dictionaries
    """
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def append_history(path: str, rows: List[List[str]]) -> None:
    """Append rows to history CSV file, creating it with header if needed.
    
    Args:
        path: Path to history CSV file
        rows: List of data rows to append
    """
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(CSV_HEADER)
        w.writerows(rows)

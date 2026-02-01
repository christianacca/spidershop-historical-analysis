#!/usr/bin/env python3
import csv
import os
from shared.config import CSV_HEADER
from shared.history_utils import group_by_run, k2, k3

# =====================
# HISTORY
# =====================

def load_history(path: str):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def append_history(path: str, rows):
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(CSV_HEADER)
        w.writerows(rows)

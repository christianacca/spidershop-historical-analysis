"""Shared CSV writing utilities for matrix output files."""

import csv
from typing import Any, Dict, List


def write_matrix_csv(
    filepath: str,
    table: List[Dict[str, Any]],
    fallback_fieldnames: List[str],
) -> None:
    """Write matrix data to a CSV file.

    Always creates the file, using row keys when the table has data, or
    fallback_fieldnames when the table is empty (so the header row is preserved).

    Args:
        filepath: Output path for the CSV file.
        table: List of row dicts (may be empty).
        fallback_fieldnames: Column names to use when table is empty.
    """
    if table:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=table[0].keys())
            writer.writeheader()
            writer.writerows(table)
    else:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fallback_fieldnames)
            writer.writeheader()

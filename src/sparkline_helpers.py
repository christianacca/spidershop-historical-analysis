#!/usr/bin/env python3
"""
Helper functions for generating Unicode sparklines for trend visualization.

Sparklines show historical trends compactly using characters like ▁▂▃▄▅▆▇█
"""
from sparklines import sparklines


def generate_sparkline(values, max_length=8):
    """
    Generate a Unicode sparkline from a list of numeric values.
    
    Args:
        values: List of numeric values (strings or floats/ints)
        max_length: Maximum number of data points to include (default 8 for weekly data)
    
    Returns:
        String containing sparkline characters (▁▂▃▄▅▆▇█) or "-" if insufficient data
    """
    if not values:
        return "-"
    
    # Filter out None/empty values and convert to floats
    numeric_values = []
    for v in values[-max_length:]:  # Take last N values
        if v is None or v == "" or v == "0":
            numeric_values.append(None)  # Preserve gaps
        else:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                numeric_values.append(None)
    
    # Need at least 1 non-None value to generate sparkline
    non_none_values = [v for v in numeric_values if v is not None]
    if not non_none_values:
        return "-"
    
    # If only one value, show single character
    if len(non_none_values) == 1:
        return "▄"  # Mid-height bar for single value
    
    # Generate sparkline using sparklines library
    # Returns list of strings, one per line (we use single line)
    result = sparklines(numeric_values, num_lines=1)
    
    # sparklines returns a generator/list of lines
    sparkline_str = "".join(result) if result else "-"
    
    return sparkline_str if sparkline_str.strip() else "-"


def extract_historical_values(key, by_run, runs, field_name, max_runs=8):
    """
    Extract historical values for a specific (species, size) across runs.
    
    Args:
        key: Tuple of (scientific_name, size_cm)
        by_run: Dictionary mapping run_id to list of rows
        runs: Sorted list of run IDs
        field_name: Name of field to extract (e.g., "price_gbp", "wishlist_count")
        max_runs: Maximum number of runs to look back (default 8)
    
    Returns:
        List of values in chronological order (oldest to newest)
    """
    values = []
    recent_runs = runs[-max_runs:] if len(runs) > max_runs else runs
    
    for run_id in recent_runs:
        row_map = {(r.get("scientific_name"), r.get("size_cm")): r for r in by_run[run_id]}
        if key in row_map:
            values.append(row_map[key].get(field_name, ""))
        else:
            # Species not present in this run
            values.append(None)
    
    return values

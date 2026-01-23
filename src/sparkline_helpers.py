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


def extract_historical_values_with_carryforward(key, by_run, runs, field_name, max_runs=8):
    """
    Extract historical values with carry-forward for OUT-of-stock periods.
    
    When a species is OUT of stock, the last known value is carried forward.
    This reflects reality: prices and wishlist counts don't disappear when stock runs out.
    
    Args:
        key: Tuple of (scientific_name, size_cm)
        by_run: Dictionary mapping run_id to list of rows
        runs: Sorted list of run IDs
        field_name: Name of field to extract (e.g., "price_gbp", "wishlist_count")
        max_runs: Maximum number of runs to look back (default 8)
    
    Returns:
        List of values in chronological order (oldest to newest) with carry-forward
    """
    values = []
    recent_runs = runs[-max_runs:] if len(runs) > max_runs else runs
    last_known_value = None
    
    for run_id in recent_runs:
        row_map = {(r.get("scientific_name"), r.get("size_cm")): r for r in by_run[run_id]}
        if key in row_map:
            # Species present - get current value and update last_known
            current_value = row_map[key].get(field_name, "")
            values.append(current_value)
            last_known_value = current_value
        else:
            # Species OUT - carry forward last known value
            values.append(last_known_value)
    
    return values


def generate_stock_availability_sparkline(key, by_run, runs, max_runs=8):
    """
    Generate a stock availability sparkline showing IN/OUT status over time.
    
    Args:
        key: Tuple of (scientific_name, size_cm)
        by_run: Dictionary mapping run_id to list of rows
        runs: Sorted list of run IDs
        max_runs: Maximum number of runs to look back (default 8)
    
    Returns:
        String with █ for IN-stock runs, space for OUT-of-stock runs
    """
    if not runs:
        return "-"
    
    recent_runs = runs[-max_runs:] if len(runs) > max_runs else runs
    availability = []
    
    for run_id in recent_runs:
        row_map = {(r.get("scientific_name"), r.get("size_cm")): r for r in by_run[run_id]}
        if key in row_map:
            availability.append("█")  # IN stock
        else:
            availability.append(" ")  # OUT of stock
    
    result = "".join(availability)
    return result if result.strip() else "-"

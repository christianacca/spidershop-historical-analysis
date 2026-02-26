#!/usr/bin/env python3
"""
Helper functions for generating Unicode sparklines for trend visualization.

Sparklines show historical trends compactly using characters like ▁▂▃▄▅▆▇█
"""
from typing import List, Dict, Any, Optional, Union
from sparklines import sparklines


def generate_sparkline(values: List[Optional[Union[str, float, int]]], max_length: int = 8) -> str:
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
    
    # Convert values to floats, treating None/empty as gaps but "0" as valid data
    numeric_values = []
    for v in values[-max_length:]:  # Take last N values
        if v is None or v == "":
            numeric_values.append(None)  # True gaps (missing data)
        else:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                numeric_values.append(None)
    
    # Need at least 1 non-None value to generate sparkline
    non_none_values = [v for v in numeric_values if v is not None]
    if not non_none_values:
        return "-"

    # Generate sparkline using sparklines library.
    # The library correctly handles leading/trailing None gaps by emitting space
    # characters, so ' ▄' is produced for [None, 35.0] — preserving the gap that
    # represents a run where the species was present but the value was missing.
    # Do NOT special-case single values: ' ▄' is more informative than '▄' when
    # there is a preceding gap, and '▄' is still produced when no gaps exist.
    result = sparklines(numeric_values, num_lines=1)
    
    # sparklines returns a generator/list of lines
    sparkline_str = "".join(result) if result else "-"
    
    return sparkline_str if sparkline_str.strip() else "-"


def extract_historical_values(key: tuple, by_run: Dict[str, List[Dict[str, Any]]], runs: List[str], field_name: str, max_runs: int = 8) -> List[Optional[str]]:
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


def extract_historical_values_with_carryforward(key: tuple, by_run: Dict[str, List[Dict[str, Any]]], runs: List[str], field_name: str, max_runs: int = 8) -> Dict[str, Any]:
    """
    Extract historical values with carry-forward for OUT-of-stock periods.
    
    When a species is OUT of stock, the last known value is carried forward.
    This reflects reality: prices and wishlist counts don't disappear when stock runs out.
    
    Sparkline rules (per user requirements):
    - Bars only start when "records began" for that spider (skip leading None values)
    - Once the sparkline starts, there should be no gaps (carry forward when OUT)
    
    Args:
        key: Tuple of (scientific_name, size_cm)
        by_run: Dictionary mapping run_id to list of rows
        runs: Sorted list of run IDs
        field_name: Name of field to extract (e.g., "price_gbp", "wishlist_count")
        max_runs: Maximum number of runs to look back (default 8)
    
    Returns:
        Dictionary with:
            'values': List of values in chronological order (oldest to newest) with carry-forward
            'is_carried_forward': List of booleans indicating which values were carried forward
            'unicode': Unicode sparkline string for CSV display
    """
    values = []
    is_carried_forward = []
    recent_runs = runs[-max_runs:] if len(runs) > max_runs else runs
    last_known_value = None
    first_appearance = False  # Track if we've seen the species yet
    
    for run_id in recent_runs:
        row_map = {(r.get("scientific_name"), r.get("size_cm")): r for r in by_run[run_id]}
        if key in row_map:
            # Species present - get current value and update last_known
            current_value = row_map[key].get(field_name, "")
            values.append(current_value)
            is_carried_forward.append(False)
            last_known_value = current_value
            first_appearance = True
        else:
            # Species OUT
            if first_appearance:
                # We've seen the species before - carry forward last known value
                values.append(last_known_value)
                is_carried_forward.append(True)
            # else: species hasn't appeared yet - don't add anything (skip leading Nones)
    
    # Generate Unicode sparkline for CSV display
    unicode_sparkline = generate_sparkline(values, max_length=max_runs)
    
    return {
        'values': values,
        'is_carried_forward': is_carried_forward,
        'unicode': unicode_sparkline
    }


def generate_stock_availability_sparkline(key: tuple, by_run: Dict[str, List[Dict[str, Any]]], runs: List[str], max_runs: int = 8) -> str:
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

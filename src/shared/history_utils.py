#!/usr/bin/env python3
"""
Shared utility functions for working with historical data rows.

These functions provide common patterns for grouping and identifying
historical scrape data, used by both analysis and website generation.
"""
from typing import Dict, List, Any, Tuple, Optional

def group_by_run(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group historical rows by scrape_datetime (run ID).
    
    Args:
        rows: List of dictionaries with scrape_datetime keys
        
    Returns:
        Dictionary mapping scrape_datetime to list of rows from that run
    """
    by_run = {}
    for r in rows:
        by_run.setdefault(r["scrape_datetime"], []).append(r)
    return by_run

def create_species_key_with_common_name(row: Dict[str, Any]) -> Tuple[str, str, str]:
    """Create 3-tuple key: (scientific_name, common_name, size_cm).
    
    Used for grouping species that may have different common names.
    
    Args:
        row: Dictionary containing species data
        
    Returns:
        Tuple of (scientific_name, common_name, size_cm)
    """
    return (row["scientific_name"], row["common_name"], row["size_cm"])

def create_species_key(row: Dict[str, Any]) -> Tuple[str, str]:
    """Create 2-tuple key: (scientific_name, size_cm).
    
    Used for grouping species regardless of common name variations.
    
    Args:
        row: Dictionary containing species data
        
    Returns:
        Tuple of (scientific_name, size_cm)
    """
    return (row["scientific_name"], row["size_cm"])


def create_observation_coverage(
    rows: List[Dict[str, Any]],
    key: Tuple[str, str],
) -> Dict[str, Any]:
    """Return full-timeline observation metadata for a species/size key.

    Args:
        rows: Full historical row set across all runs.
        key: Species key as ``(scientific_name, size_cm)``.

    Returns:
        Dict containing:
            - first_observed_run: first run where key was observed, or None
            - latest_observed_run: latest run where key was observed, or None
            - observed_run_count: number of runs where key was observed
            - total_run_count: total number of runs in the dataset
            - current_consecutive_observation_runs: trailing observed run streak
            - ambiguous_pre_first_seen_run_count: runs before first observation
            - observed_in_current_run: whether key is present in the latest run
    """
    by_run = group_by_run(rows)
    runs = sorted(by_run)

    observed_runs = [run_timestamp for run_timestamp in runs if any(create_species_key(row) == key for row in by_run[run_timestamp])]
    first_observed_run: Optional[str] = observed_runs[0] if observed_runs else None
    latest_observed_run: Optional[str] = observed_runs[-1] if observed_runs else None
    total_run_count = len(runs)
    observed_run_count = len(observed_runs)

    current_consecutive_observation_runs = 0
    for run_timestamp in reversed(runs):
        if run_timestamp in observed_runs:
            current_consecutive_observation_runs += 1
            continue
        break

    ambiguous_pre_first_seen_run_count = 0
    if first_observed_run is not None:
        ambiguous_pre_first_seen_run_count = runs.index(first_observed_run)

    observed_in_current_run = bool(runs) and latest_observed_run == runs[-1]

    return {
        "first_observed_run": first_observed_run,
        "latest_observed_run": latest_observed_run,
        "observed_run_count": observed_run_count,
        "total_run_count": total_run_count,
        "current_consecutive_observation_runs": current_consecutive_observation_runs,
        "ambiguous_pre_first_seen_run_count": ambiguous_pre_first_seen_run_count,
        "observed_in_current_run": observed_in_current_run,
    }


def compare_prices(price_current: str, price_previous: str) -> str:
    """Compare two price strings and return a trend symbol.
    
    Args:
        price_current: Current price as string (e.g., "12.99")
        price_previous: Previous price as string (e.g., "10.99")
        
    Returns:
        Trend symbol: "↑" (rising), "↓" (falling), or "→" (stable/unchanged)
    """
    try:
        if not price_current or not price_previous:
            return "→"
        
        current = float(price_current)
        previous = float(price_previous)
        
        if current > previous:
            return "↑"
        elif current < previous:
            return "↓"
        return "→"
    except (ValueError, TypeError):
        return "→"


# Backward compatibility aliases
k3 = create_species_key_with_common_name
k2 = create_species_key

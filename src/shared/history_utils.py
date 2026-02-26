#!/usr/bin/env python3
"""
Shared utility functions for working with historical data rows.

These functions provide common patterns for grouping and identifying
historical scrape data, used by both analysis and website generation.
"""
from typing import Dict, List, Any, Tuple

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

#!/usr/bin/env python3
"""
Shared utility functions for working with historical data rows.

These functions provide common patterns for grouping and identifying
historical scrape data, used by both analysis and website generation.
"""

def group_by_run(rows):
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

def k3(r):
    """Create 3-tuple key: (scientific_name, common_name, size_cm).
    
    Used for grouping species that may have different common names.
    """
    return (r["scientific_name"], r["common_name"], r["size_cm"])

def k2(r):
    """Create 2-tuple key: (scientific_name, size_cm).
    
    Used for grouping species regardless of common name variations.
    """
    return (r["scientific_name"], r["size_cm"])

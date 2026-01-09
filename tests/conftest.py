#!/usr/bin/env python3
"""
Shared test fixtures and utilities for all test modules.
"""
import sys
from pathlib import Path

# Add src directory to Python path to enable imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def make_row(scrape_datetime, scientific_name, size_cm, price_gbp, wishlist_count="0"):
    """Helper to create a synthetic history row matching CSV schema.
    
    Args:
        scrape_datetime: ISO format datetime string (e.g., "2025-01-01")
        scientific_name: Scientific name of the species
        size_cm: Size in cm as string
        price_gbp: Price in GBP as string
        wishlist_count: Wishlist count as string (default "0")
    
    Returns:
        Dictionary matching the CSV schema for history rows
    """
    return {
        "scrape_datetime": scrape_datetime,
        "scientific_name": scientific_name,
        "common_name": "Test Spider",
        "size_cm": size_cm,
        "price_gbp": price_gbp,
        "wishlist_count": wishlist_count,
        "page_url": "https://example.com"
    }

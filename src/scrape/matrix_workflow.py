#!/usr/bin/env python3
"""Shared workflow helpers for scrape matrix builders."""

from typing import Any, Callable, Dict, List, Optional, Tuple

from scrape.wishlist_analysis import get_wishlist_count, get_wishlist_metrics
from shared.config import SIGNAL_PRIORITY
from shared.history_utils import group_by_run
from shared.sparkline_helpers import extract_historical_values_with_carryforward


def prepare_matrix_runs(
    history_rows: List[Dict[str, Any]],
) -> Optional[Tuple[Dict[str, List[Dict[str, Any]]], List[str], str, str, List[Dict[str, Any]]]]:
    """Prepare grouped run data shared by matrix builders.

    Returns None when there is insufficient run history (<2 runs).
    """
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    if len(runs) < 2:
        return None

    current_run = runs[-1]
    previous_run = runs[-2]
    current_rows = by_run[current_run]
    return by_run, runs, current_run, previous_run, current_rows


def get_wishlist_display_metrics(
    key: Tuple[str, str],
    by_run: Dict[str, List[Dict[str, Any]]],
    runs: List[str],
    current_run: str,
    wishlist_pressure_map: Dict[Tuple[str, str], str],
) -> Tuple[str, str, int, str]:
    """Return wishlist pressure, delta, count and display string for a key."""
    wishlist_pressure, wishlist_delta = get_wishlist_metrics(
        key, by_run, runs, current_run, wishlist_pressure_map
    )
    wishlist_count = get_wishlist_count(key, by_run, runs, current_run)
    wishlist_display = f"{wishlist_count} {wishlist_pressure} {wishlist_delta}"
    return wishlist_pressure, wishlist_delta, wishlist_count, wishlist_display


def generate_price_wishlist_sparklines(
    key: Tuple[str, str],
    by_run: Dict[str, List[Dict[str, Any]]],
    runs: List[str],
    max_runs: int = 8,
) -> Tuple[str, str]:
    """Generate price and wishlist sparkline unicode strings."""
    price_history = extract_historical_values_with_carryforward(
        key, by_run, runs, "price_gbp", max_runs=max_runs
    )
    wishlist_history = extract_historical_values_with_carryforward(
        key, by_run, runs, "wishlist_count", max_runs=max_runs
    )
    return price_history["unicode"], wishlist_history["unicode"]


def sort_matrix_table(
    table: List[Dict[str, Any]],
    indicator_field: str,
    tertiary_value_getter: Callable[[Dict[str, Any]], float],
) -> None:
    """Sort matrix rows by indicator, wishlist count and a tertiary metric (descending)."""

    def extract_wishlist_count(row: Dict[str, Any]) -> int:
        wishlist_value = str(row.get("Wishlist", "")).split()
        if not wishlist_value:
            return 0
        try:
            return int(wishlist_value[0])
        except (ValueError, IndexError):
            return 0

    table.sort(
        key=lambda row: (
            SIGNAL_PRIORITY.get(str(row.get(indicator_field, "")), 99),
            -extract_wishlist_count(row),
            -tertiary_value_getter(row),
        )
    )

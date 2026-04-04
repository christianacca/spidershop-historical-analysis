#!/usr/bin/env python3
"""Shared workflow helpers for scrape matrix builders."""

from typing import Any, Callable, Dict, List, Optional, Tuple

from scrape.listing_lineage import LineageResult, detect_species_lineage
from scrape.wishlist_analysis import (
    compute_wishlist_pressure,
    get_wishlist_count,
    get_wishlist_metrics,
)
from shared.config import OOS_CARRYOVER_LOOKBACK, SIGNAL_PRIORITY
from shared.history_utils import group_by_run, k2
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


def prepare_matrix_analysis(
    history_rows: List[Dict[str, Any]],
) -> Optional[
    Tuple[
        Dict[str, List[Dict[str, Any]]],
        List[str],
        str,
        str,
        List[Dict[str, Any]],
        Dict[str, int],
        Dict[Tuple[str, str], str],
    ]
]:
    """Prepare shared matrix builder context including run indices and wishlist pressure."""
    prepared = prepare_matrix_runs(history_rows)
    if prepared is None:
        return None

    by_run, runs, current_run, previous_run, current_rows = prepared
    run_index = {run_timestamp: idx for idx, run_timestamp in enumerate(runs)}
    wishlist_pressure_map = compute_wishlist_pressure(current_rows)
    return (
        by_run,
        runs,
        current_run,
        previous_run,
        current_rows,
        run_index,
        wishlist_pressure_map,
    )


def iter_lookback_rows_for_key(
    key: Tuple[str, str],
    by_run: Dict[str, List[Dict[str, Any]]],
    runs: List[str],
    current_run: str,
    run_index: Dict[str, int],
    lookback_window: int = OOS_CARRYOVER_LOOKBACK,
):
    """Yield matching historical rows newest-first within the bounded lookback window."""
    current_index = run_index[current_run]
    lookback_start = max(0, current_index - lookback_window)

    for idx in range(current_index - 1, lookback_start - 1, -1):
        run_timestamp = runs[idx]
        for row in by_run[run_timestamp]:
            if k2(row) == key:
                yield row


def collect_lookback_values_for_key(
    key: Tuple[str, str],
    by_run: Dict[str, List[Dict[str, Any]]],
    runs: List[str],
    current_run: str,
    run_index: Dict[str, int],
    value_getter: Callable[[Dict[str, Any]], Any],
    max_values: int,
    lookback_window: int = OOS_CARRYOVER_LOOKBACK,
) -> List[Any]:
    """Collect recent non-empty values for a key from the bounded lookback window."""
    values: List[Any] = []

    for row in iter_lookback_rows_for_key(
        key, by_run, runs, current_run, run_index, lookback_window=lookback_window
    ):
        value = value_getter(row)
        if value:
            values.append(value)
            if len(values) >= max_values:
                break

    return values


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


# ---------------------------------------------------------------------------
# Lineage metadata (Phase 3 / Phase 4)
# ---------------------------------------------------------------------------

#: Hidden metadata column names appended after ``Drivers`` in CSV output.
LINEAGE_METADATA_COLUMNS = [
    "Lineage Status",
    "Previous Size (cm)",
    "Current Active Size (cm)",
    "Transition Date",
    "Price Evidence State",
    "Wishlist Evidence State",
    "Transition Message",
]


def compute_lineage_metadata(
    scientific_name: str,
    history_rows: List[Dict[str, Any]],
) -> Dict[str, str]:
    """Detect listing lineage for *scientific_name* and return hidden column dict.

    This is a thin delegation wrapper around
    :func:`scrape.listing_lineage.detect_species_lineage`.  It is called
    once per unique scientific name so that both matrix modules can attach
    identical lineage metadata to all rows that share the same species.

    Args:
        scientific_name: Species to analyse.
        history_rows: Full history dataset (all species, all runs).

    Returns:
        Dict with keys matching :data:`LINEAGE_METADATA_COLUMNS`.
    """
    result: LineageResult = detect_species_lineage(history_rows, scientific_name)
    return {
        "Lineage Status": result.lineage_status,
        "Previous Size (cm)": result.previous_size,
        "Current Active Size (cm)": result.current_active_size,
        "Transition Date": result.transition_date,
        "Price Evidence State": result.price_evidence_state,
        "Wishlist Evidence State": result.wishlist_evidence_state,
        "Transition Message": result.transition_message,
    }

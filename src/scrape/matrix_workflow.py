#!/usr/bin/env python3
"""Shared workflow helpers for scrape matrix builders."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from scrape.wishlist_analysis import (
    compute_wishlist_pressure,
    get_wishlist_count,
    get_wishlist_metrics,
)
from shared.config import OOS_CARRYOVER_LOOKBACK, SIGNAL_PRIORITY
from shared.history_utils import group_by_run, k2
from shared.sparkline_helpers import extract_historical_values_with_carryforward


@dataclass(frozen=True)
class MatrixContext:
    """Shared context prepared once for matrix table builders."""

    by_run: Dict[str, List[Dict[str, Any]]]
    runs: List[str]
    current_run: str
    previous_run: str
    current_rows: List[Dict[str, Any]]
    previous_rows: List[Dict[str, Any]]
    run_index: Dict[str, int]
    wishlist_pressure_map: Dict[Tuple[str, str], str]
    current_map: Dict[Tuple[str, str], Dict[str, Any]]
    previous_map: Dict[Tuple[str, str], Dict[str, Any]]

    @classmethod
    def from_history(cls, history_rows: List[Dict[str, Any]]) -> Optional["MatrixContext"]:
        """Build shared matrix context from historical rows."""
        prepared = prepare_matrix_runs(history_rows)
        if prepared is None:
            return None

        by_run, runs, current_run, previous_run, current_rows = prepared
        previous_rows = by_run[previous_run]
        return cls(
            by_run=by_run,
            runs=runs,
            current_run=current_run,
            previous_run=previous_run,
            current_rows=current_rows,
            previous_rows=previous_rows,
            run_index={run_timestamp: idx for idx, run_timestamp in enumerate(runs)},
            wishlist_pressure_map=compute_wishlist_pressure(current_rows),
            current_map={k2(row): row for row in current_rows},
            previous_map={k2(row): row for row in previous_rows},
        )


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
    context = MatrixContext.from_history(history_rows)
    if context is None:
        return None

    return (
        context.by_run,
        context.runs,
        context.current_run,
        context.previous_run,
        context.current_rows,
        context.run_index,
        context.wishlist_pressure_map,
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

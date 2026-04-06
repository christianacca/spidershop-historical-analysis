#!/usr/bin/env python3
"""Shared workflow helpers for scrape matrix builders."""

from typing import Any, Callable, Dict, List, Optional, Tuple

from scrape.listing_lineage import LineageResult, detect_species_lineage
from scrape.wishlist_analysis import (
    get_species_wishlist_count,
)
from shared.config import OOS_CARRYOVER_LOOKBACK, SIGNAL_PRIORITY, WISHLIST_SMALL_N_FLATTEN_THRESHOLD
from shared.history_utils import group_by_run, k2
from shared.sparkline_helpers import (
    extract_historical_values_with_carryforward,
    generate_sparkline,
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
        Dict[str, "LineageResult"],
    ]
]:
    """Prepare shared matrix builder context including run indices and species-level
    lineage metadata.

    Phase 4: also returns ``species_lineage_map`` — a dict keyed by scientific name
    holding the :class:`~scrape.listing_lineage.LineageResult` for each species.
    """
    prepared = prepare_matrix_runs(history_rows)
    if prepared is None:
        return None

    by_run, runs, current_run, previous_run, current_rows = prepared
    run_index = {run_timestamp: idx for idx, run_timestamp in enumerate(runs)}

    # Compute species-level lineage map once per scientific name (Phase 4)
    # Use dict.fromkeys to preserve first-seen order (set iteration is non-deterministic)
    all_sci = dict.fromkeys(r["scientific_name"] for r in history_rows)
    species_lineage_map = {
        sci: detect_species_lineage(history_rows, sci) for sci in all_sci
    }

    return (
        by_run,
        runs,
        current_run,
        previous_run,
        current_rows,
        run_index,
        species_lineage_map,
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


def lineage_result_to_metadata_dict(result: LineageResult) -> Dict[str, str]:
    """Convert a :class:`LineageResult` to the hidden metadata column dict."""
    return {
        "Lineage Status": result.lineage_status,
        "Previous Size (cm)": result.previous_size,
        "Current Active Size (cm)": result.current_active_size,
        "Transition Date": result.transition_date,
        "Price Evidence State": result.price_evidence_state,
        "Wishlist Evidence State": result.wishlist_evidence_state,
        "Transition Message": result.transition_message,
    }


def build_lineage_clause(lineage_result: LineageResult) -> str:
    """Build the transition clause appended to Drivers text.

    Returns a human-readable clause for confirmed/ambiguous transitions, or an
    empty string for ``none`` and ``multi-variant`` states.
    """
    current_active_size = lineage_result.current_active_size or "—"
    status = lineage_result.lineage_status
    if status == "confirmed-transition":
        return (
            f"Size transition: confirmed "
            f"{lineage_result.previous_size}→{current_active_size} "
            f"on {lineage_result.transition_date}"
        )
    if status == "ambiguous-transition":
        return (
            f"Size transition: ambiguous "
            f"{lineage_result.previous_size}→{current_active_size} "
            f"on {lineage_result.transition_date}"
        )
    return ""


# ---------------------------------------------------------------------------
# Phase 4 — Species-level sparkline generation
# ---------------------------------------------------------------------------


def _generate_stitched_sparkline(
    scientific_name: str,
    prev_size: str,
    curr_size: str,
    transition_date: str,
    by_run: Dict[str, List[Dict[str, Any]]],
    runs: List[str],
    field_name: str,
    max_runs: int = 8,
) -> str:
    """Generate a sparkline by stitching the pre- and post-transition lineage.

    For runs before *transition_date* the *prev_size* key is used; for runs on or
    after *transition_date* the *curr_size* key is used.  OUT periods within the
    window carry forward the last known value (same behaviour as the per-k2 helper).

    Args:
        scientific_name: Species being analysed.
        prev_size: Size that was active before the confirmed handoff.
        curr_size: Size that became active at/after *transition_date*.
        transition_date: ``YYYY-MM-DD`` date of first observation of *curr_size*.
        by_run: Dict mapping run timestamp → list of rows.
        runs: Sorted list of all run timestamps.
        field_name: Row field to extract (``"price_gbp"`` or ``"wishlist_count"``).
        max_runs: Number of recent runs to include (default 8).

    Returns:
        Unicode sparkline string, or ``"-"`` when insufficient data.
    """
    recent_runs = runs[-max_runs:] if len(runs) > max_runs else runs
    values: List[Any] = []
    last_known = None
    started = False

    for run in recent_runs:
        run_date = run[:10]
        target_key = (scientific_name, curr_size if run_date >= transition_date else prev_size)
        matching = next(
            (r for r in by_run.get(run, []) if k2(r) == target_key),
            None,
        )
        if matching:
            val = matching.get(field_name, "")
            values.append(val)
            last_known = val
            started = True
        elif started:
            values.append(last_known)
        # Before species first appearance: skip (no leading gap bars)

    return generate_sparkline(values, max_length=max_runs)


def generate_species_price_wishlist_sparklines(
    scientific_name: str,
    lineage_result: LineageResult,
    by_run: Dict[str, List[Dict[str, Any]]],
    runs: List[str],
    max_runs: int = 8,
) -> Tuple[str, str]:
    """Return ``(price_sparkline, wishlist_sparkline)`` respecting lineage rules.

    * ``confirmed-transition``: both sparklines are stitched across the lineage.
    * ``none``: standard per-k2 sparklines for the single observed size.
    * ``ambiguous-transition`` / ``multi-variant``: both return ``"-"``.

    Args:
        scientific_name: Species being analysed.
        lineage_result: LineageResult for the species.
        by_run: Dict mapping run timestamp → list of rows.
        runs: Sorted list of all run timestamps.
        max_runs: Number of recent runs to include (default 8).

    Returns:
        ``(price_sparkline, wishlist_sparkline)`` tuple.
    """
    status = lineage_result.lineage_status
    if status == "confirmed-transition":
        price_sparkline = _generate_stitched_sparkline(
            scientific_name,
            lineage_result.previous_size,
            lineage_result.current_active_size,
            lineage_result.transition_date,
            by_run,
            runs,
            "price_gbp",
            max_runs,
        )
        wishlist_sparkline = _generate_stitched_sparkline(
            scientific_name,
            lineage_result.previous_size,
            lineage_result.current_active_size,
            lineage_result.transition_date,
            by_run,
            runs,
            "wishlist_count",
            max_runs,
        )
        return price_sparkline, wishlist_sparkline

    if status == "none":
        active_key = (scientific_name, lineage_result.current_active_size)
        return generate_price_wishlist_sparklines(active_key, by_run, runs, max_runs=max_runs)

    # ambiguous-transition or multi-variant: suppress both sparklines
    return "-", "-"


# ---------------------------------------------------------------------------
# Phase 4 — Species-level wishlist pressure map
# ---------------------------------------------------------------------------


def build_species_wishlist_pressure_map(
    species_lineage_map: Dict[str, "LineageResult"],
    by_run: Dict[str, List[Dict[str, Any]]],
    runs: List[str],
    cur_run: str,
) -> Dict[str, str]:
    """Compute species-level wishlist pressure for the current run.

    Effective count rules (per Decision 4):
    * Species IN current run with ``multi-variant`` status → max count across active variants.
    * Species IN current run (other statuses) → count for the active row.
    * Species OUT within the 5-run OOS carryover window → last known count for
      ``current_active_size`` within that window.
    * Species OUT beyond the window → 0.

    Relative ranking mirrors :func:`~scrape.wishlist_analysis.compute_wishlist_pressure`.

    Args:
        species_lineage_map: ``{scientific_name: LineageResult}`` for all species.
        by_run: Dict mapping run timestamp → list of rows.
        runs: Sorted list of all run timestamps.
        cur_run: Most recent run timestamp.

    Returns:
        ``{scientific_name: pressure_symbol}`` where pressure is one of
        ``"🔥"``, ``"⚠️"``, ``"❌"``.
    """
    counts: Dict[str, int] = {
        sci: get_species_wishlist_count(sci, lr, by_run, runs, cur_run)
        for sci, lr in species_lineage_map.items()
    }

    # Mirror ranks from compute_wishlist_pressure
    zero_keys = {sci for sci, c in counts.items() if c == 0}
    nonzero = [(sci, c) for sci, c in counts.items() if c > 0]
    result: Dict[str, str] = {sci: "❌" for sci in zero_keys}

    if not nonzero:
        return result

    nonzero.sort(key=lambda x: (-x[1], x[0]))  # descending count, then alphabetical for deterministic tie-breaking
    count_vals = [c for _, c in nonzero]
    if max(count_vals) - min(count_vals) <= WISHLIST_SMALL_N_FLATTEN_THRESHOLD:
        for sci, _ in nonzero:
            result[sci] = "⚠️"
        return result

    n = len(nonzero)
    high_cutoff = max(1, n // 4)
    low_cutoff = max(1, (3 * n) // 4)
    for i, (sci, _) in enumerate(nonzero):
        if i < high_cutoff:
            result[sci] = "🔥"
        elif i < low_cutoff:
            result[sci] = "⚠️"
        else:
            result[sci] = "❌"

    return result

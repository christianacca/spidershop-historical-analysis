#!/usr/bin/env python3
"""
Wishlist analysis and computation functions for market signal detection.

This module provides conservative, time-bounded analysis of wishlist metrics:
- Wishlist Pressure: Relative ranking within current distribution
- Wishlist Carryover: Bounded lookback for OUT-of-stock species
- Wishlist Delta: Meaningful momentum detection with conservative thresholds
"""

from shared.config import (
    WISHLIST_DELTA_INCREASE_THRESHOLD,
    WISHLIST_DELTA_DECREASE_THRESHOLD,
    OOS_CARRYOVER_LOOKBACK,
    WISHLIST_DELTA_LOOKBACK,
    WISHLIST_DELTA_PREV_LOOKBACK,
)
from shared.history_utils import k2


def _build_key_map(rows):
    """Build a dict mapping (scientific_name, size_cm) to row data.
    
    Args:
        rows: List of row dicts with scientific_name and size_cm fields.
        
    Returns:
        Dict mapping (scientific_name, size_cm) tuple to row dict.
    """
    return {k2(r): r for r in rows}


def _get_wishlist_count(row):
    """Extract wishlist count from a row, defaulting to 0 on error.
    
    Args:
        row: Row dict with optional wishlist_count field.
        
    Returns:
        Integer wishlist count (0 if missing or invalid).
    """
    try:
        return int(row.get("wishlist_count", "0") or "0")
    except (ValueError, TypeError):
        return 0


def compute_wishlist_delta(key, by_run, runs, cur_run, lookback_limit=WISHLIST_DELTA_LOOKBACK, prev_lookback_limit=WISHLIST_DELTA_PREV_LOOKBACK):
    """
    Compute Wishlist Delta (momentum signal) for a species by comparing current vs
    previous IN-stock wishlist counts using conservative thresholds.
    
    Args:
        key: (scientific_name, size_cm) tuple
        by_run: dict mapping run datetime -> list of rows
        runs: sorted list of run datetimes
        cur_run: current run datetime
        lookback_limit: max number of recent runs to look back for OUT species
        prev_lookback_limit: max runs to look back for previous comparison value
    
    Returns:
        Wishlist Delta symbol:
        - "↑" if Δ ≥ threshold (meaningful increase)
        - "→" if within threshold range (stable or noise)
        - "↓" if Δ ≤ -threshold (meaningful decrease)
    
    Rationale:
        Conservative thresholds prevent false signals from noise.
        Uses ±5 as meaningful buyer movement threshold given observed distributions.
        Weekly cadence requires higher bar for momentum detection.
        Both current and previous values are bounded in time to prevent noisy
        comparisons against months-old baselines.
    """
    # Find the index of the current run
    try:
        cur_idx = runs.index(cur_run)
    except ValueError:
        return "→"
    
    # Get current wishlist count (the "current reference run")
    # First, check if species is IN current run
    cur_rows = by_run[cur_run]
    cur_map = _build_key_map(cur_rows)
    
    current_count = None
    current_ref_idx = cur_idx  # Track which run we're using as the current reference
    
    if key in cur_map:
        # Species is IN current run
        current_count = _get_wishlist_count(cur_map[key])
    else:
        # Species is OUT - look back for last IN-stock wishlist count (carryover run)
        lookback_start = max(0, cur_idx - lookback_limit)
        for i in range(cur_idx - 1, lookback_start - 1, -1):
            rt = runs[i]
            run_rows = by_run[rt]
            run_map = _build_key_map(run_rows)
            
            if key in run_map:
                current_count = _get_wishlist_count(run_map[key])
                current_ref_idx = i  # Update reference index to the carryover run
                break
    
    # If we couldn't find a current count, return neutral
    if current_count is None:
        return "→"
    
    # Find previous comparable wishlist count (last run where species was IN)
    # BOUNDED search: only look back prev_lookback_limit runs from current reference run
    # This prevents comparing recent counts against months-old baselines, which creates
    # noisy momentum signals for OUT-of-stock species.
    previous_count = None
    prev_lookback_start = max(0, current_ref_idx - prev_lookback_limit)
    
    # Search from the run before the current reference run, bounded by prev_lookback_limit
    for i in range(current_ref_idx - 1, prev_lookback_start - 1, -1):
        rt = runs[i]
        run_rows = by_run[rt]
        run_map = _build_key_map(run_rows)
        
        if key in run_map:
            previous_count = _get_wishlist_count(run_map[key])
            break
    
    # If we couldn't find a previous count within the bounded window, return neutral
    if previous_count is None:
        return "→"
    
    # Calculate delta and apply thresholds
    delta = current_count - previous_count
    
    if delta >= WISHLIST_DELTA_INCREASE_THRESHOLD:
        return "↑"
    elif delta <= WISHLIST_DELTA_DECREASE_THRESHOLD:
        return "↓"
    else:
        return "→"


# ---------------------------------------------------------------------------
# Phase 4 — Species-level wishlist helpers
# ---------------------------------------------------------------------------

# Allow forward-reference to LineageResult without a circular import at module level
from typing import Any, Optional


def get_species_wishlist_count(
    scientific_name: str,
    lineage_result: Any,
    by_run: dict,
    runs: list,
    cur_run: str,
    lookback_limit: int = OOS_CARRYOVER_LOOKBACK,
) -> int:
    """Return the effective wishlist count for a species, respecting lineage state.

    Rules (Decision 4):
    * Species IN current run, ``multi-variant``: max count across active variants.
    * Species IN current run (other states): count for the current active row.
    * Species OUT within *lookback_limit* runs: last known count for
      ``current_active_size`` within the window.
    * Otherwise: 0.
    """
    current_active_size = lineage_result.current_active_size
    cur_rows = [r for r in by_run.get(cur_run, []) if r["scientific_name"] == scientific_name]

    if cur_rows:
        if lineage_result.lineage_status == "multi-variant":
            return max(_get_wishlist_count(r) for r in cur_rows)
        # Single active size — find the matching row
        for r in cur_rows:
            if r["size_cm"] == current_active_size:
                return _get_wishlist_count(r)
        # Fallback: use any current row for this species
        return _get_wishlist_count(cur_rows[0])

    # Species OUT — walk back for last known count for current_active_size
    if not current_active_size:
        return 0

    try:
        cur_idx = runs.index(cur_run)
    except ValueError:
        return 0

    lookback_start = max(0, cur_idx - lookback_limit)
    for i in range(cur_idx - 1, lookback_start - 1, -1):
        rt = runs[i]
        for row in by_run.get(rt, []):
            if row["scientific_name"] == scientific_name and row["size_cm"] == current_active_size:
                return _get_wishlist_count(row)
    return 0


def _stitched_count_for_run(
    scientific_name: str,
    prev_size: str,
    curr_size: str,
    transition_date: str,
    run: str,
    run_rows: list,
) -> Optional[int]:
    """Return wishlist count from the stitched lineage for *run*, or None if absent.

    Before *transition_date*: look up *prev_size*; on/after: look up *curr_size*.
    """
    run_date = run[:10]
    target_size = curr_size if run_date >= transition_date else prev_size
    for row in run_rows:
        if row["scientific_name"] == scientific_name and row["size_cm"] == target_size:
            return _get_wishlist_count(row)
    return None


def compute_species_wishlist_delta(
    scientific_name: str,
    lineage_result: Any,
    by_run: dict,
    runs: list,
    cur_run: str,
    lookback_limit: int = WISHLIST_DELTA_LOOKBACK,
    prev_lookback_limit: int = WISHLIST_DELTA_PREV_LOOKBACK,
) -> str:
    """Compute wishlist delta for a species, respecting lineage evidence rules.

    * ``ambiguous-transition`` or ``multi-variant``: always ``"→"``.
    * ``none``: delegates to :func:`compute_wishlist_delta` on the single k2 key.
    * ``confirmed-transition``: stitches pre- and post-transition observations
      to find a defensible momentum comparison.
    """
    status = lineage_result.lineage_status

    if status in ("ambiguous-transition", "multi-variant"):
        return "→"

    current_active_size = lineage_result.current_active_size

    if status == "none":
        if not current_active_size:
            return "→"
        return compute_wishlist_delta(
            (scientific_name, current_active_size),
            by_run,
            runs,
            cur_run,
            lookback_limit=lookback_limit,
            prev_lookback_limit=prev_lookback_limit,
        )

    # confirmed-transition: stitched delta logic
    prev_size = lineage_result.previous_size
    transition_date = lineage_result.transition_date

    try:
        cur_idx = runs.index(cur_run)
    except ValueError:
        return "→"

    # Step 1: Find current count reference in stitched lineage
    current_count: Optional[int] = None
    current_ref_idx = cur_idx

    val = _stitched_count_for_run(
        scientific_name, prev_size, current_active_size, transition_date,
        cur_run, by_run.get(cur_run, []),
    )
    if val is not None:
        current_count = val
    else:
        lookback_start = max(0, cur_idx - lookback_limit)
        for i in range(cur_idx - 1, lookback_start - 1, -1):
            rt = runs[i]
            val = _stitched_count_for_run(
                scientific_name, prev_size, current_active_size, transition_date,
                rt, by_run.get(rt, []),
            )
            if val is not None:
                current_count = val
                current_ref_idx = i
                break

    if current_count is None:
        return "→"

    # Step 2: Find previous count in stitched lineage (bounded)
    previous_count: Optional[int] = None
    prev_start = max(0, current_ref_idx - prev_lookback_limit)
    for i in range(current_ref_idx - 1, prev_start - 1, -1):
        rt = runs[i]
        val = _stitched_count_for_run(
            scientific_name, prev_size, current_active_size, transition_date,
            rt, by_run.get(rt, []),
        )
        if val is not None:
            previous_count = val
            break

    if previous_count is None:
        return "→"

    delta = current_count - previous_count
    if delta >= WISHLIST_DELTA_INCREASE_THRESHOLD:
        return "↑"
    elif delta <= WISHLIST_DELTA_DECREASE_THRESHOLD:
        return "↓"
    return "→"

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
    WISHLIST_OOS_CARRYOVER_LOOKBACK,
    WISHLIST_DELTA_LOOKBACK,
    WISHLIST_DELTA_PREV_LOOKBACK,
    WISHLIST_SMALL_N_FLATTEN_THRESHOLD
)


def compute_wishlist_pressure(rows):
    """
    Compute relative wishlist pressure for rows in the current run.
    
    Returns a dict mapping (scientific_name, size_cm) -> pressure symbol.
    
    Pressure symbols:
    - 🔥 = High wishlist pressure (top ~25% of non-zero wishlist counts)
    - ⚠️ = Moderate wishlist pressure (middle range)
    - ❌ = Low or no wishlist pressure (bottom tier or zero)
    
    IMPORTANT: Wishlist pressure is RELATIVE per run, not absolute.
    🔥 does NOT mean high absolute count; it reflects ranking within the current distribution.
    This prevents popularity bias and adapts to site growth or shrinkage.
    
    Uses relative ranking to avoid site-growth drift and popularity bias.
    This is run per-scrape to ensure bands adapt to current distribution.
    """
    # Extract wishlist counts, filtering to current rows only
    wishlist_data = []
    for r in rows:
        try:
            count = int(r.get("wishlist_count", "0") or "0")
            key = (r.get("scientific_name", ""), r.get("size_cm", ""))
            wishlist_data.append((key, count))
        except (ValueError, TypeError):
            key = (r.get("scientific_name", ""), r.get("size_cm", ""))
            wishlist_data.append((key, 0))
    
    if not wishlist_data:
        return {}
    
    # Separate zero and non-zero counts
    zero_keys = {k for k, c in wishlist_data if c == 0}
    nonzero = [(k, c) for k, c in wishlist_data if c > 0]
    
    result = {}
    
    # All zeros get ❌
    for k in zero_keys:
        result[k] = "❌"
    
    if not nonzero:
        return result
    
    # Sort non-zero by count descending
    nonzero.sort(key=lambda x: x[1], reverse=True)
    
    # Small-N flattening: if all wishlist counts are very close (max - min ≤ threshold),
    # then the distribution is too flat to meaningfully rank.
    # Conservative interpretation: assign ⚠️ to all non-zero to avoid artificial 🔥.
    counts = [c for _, c in nonzero]
    if counts and max(counts) - min(counts) <= WISHLIST_SMALL_N_FLATTEN_THRESHOLD:
        for k, _ in nonzero:
            result[k] = "⚠️"
        return result
    
    # Use percentile-based bands:
    # Top 25% = 🔥 (high pressure)
    # Next 50% = ⚠️ (moderate)
    # Bottom 25% = ❌ (low)
    n = len(nonzero)
    high_cutoff = max(1, n // 4)  # top 25%
    low_cutoff = max(1, (3 * n) // 4)  # bottom 25%
    
    for i, (k, _) in enumerate(nonzero):
        if i < high_cutoff:
            result[k] = "🔥"
        elif i < low_cutoff:
            result[k] = "⚠️"
        else:
            result[k] = "❌"
    
    return result


def get_oos_wishlist_carryover(key, by_run, runs, cur_run, lookback_limit=WISHLIST_OOS_CARRYOVER_LOOKBACK):
    """
    For OUT-of-stock species, carry forward wishlist pressure from the most recent run
    where it was IN stock, within a bounded lookback window.
    
    Args:
        key: (scientific_name, size_cm) tuple
        by_run: dict mapping run datetime -> list of rows
        runs: sorted list of run datetimes
        cur_run: current run datetime
        lookback_limit: max number of recent runs to look back (default 5)
    
    Returns:
        Wishlist pressure symbol (🔥/⚠️/❌) or None if not found
    
    Rationale:
        Wishlist interest often peaks just before sell-out.
        This prevents under-valuing OUT species with real latent demand.
        Keeps behavior conservative and bounded.
    """
    # Find the index of the current run
    try:
        cur_idx = runs.index(cur_run)
    except ValueError:
        return None
    
    # Look back through recent runs (excluding current)
    lookback_start = max(0, cur_idx - lookback_limit)
    for i in range(cur_idx - 1, lookback_start - 1, -1):
        rt = runs[i]
        # Check if key exists in this run
        run_rows = by_run[rt]
        run_map = {(r.get("scientific_name", ""), r.get("size_cm", "")): r for r in run_rows}
        
        if key in run_map:
            # Found the species in this run - compute its pressure
            pressure_map = compute_wishlist_pressure(run_rows)
            return pressure_map.get(key, "❌")
    
    return None


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
    cur_map = {(r.get("scientific_name", ""), r.get("size_cm", "")): r for r in cur_rows}
    
    current_count = None
    current_ref_idx = cur_idx  # Track which run we're using as the current reference
    
    if key in cur_map:
        # Species is IN current run
        try:
            current_count = int(cur_map[key].get("wishlist_count", "0") or "0")
        except (ValueError, TypeError):
            current_count = 0
    else:
        # Species is OUT - look back for last IN-stock wishlist count (carryover run)
        lookback_start = max(0, cur_idx - lookback_limit)
        for i in range(cur_idx - 1, lookback_start - 1, -1):
            rt = runs[i]
            run_rows = by_run[rt]
            run_map = {(r.get("scientific_name", ""), r.get("size_cm", "")): r for r in run_rows}
            
            if key in run_map:
                try:
                    current_count = int(run_map[key].get("wishlist_count", "0") or "0")
                    current_ref_idx = i  # Update reference index to the carryover run
                except (ValueError, TypeError):
                    current_count = 0
                    current_ref_idx = i
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
        run_map = {(r.get("scientific_name", ""), r.get("size_cm", "")): r for r in run_rows}
        
        if key in run_map:
            try:
                previous_count = int(run_map[key].get("wishlist_count", "0") or "0")
            except (ValueError, TypeError):
                previous_count = 0
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


def get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map):
    """Get wishlist pressure and delta for a species with OOS carryover logic.

    Consolidates the repeated pattern from breeder and dealer matrices:
    - If the species is IN the current run, look up its pressure directly.
    - If the species is OUT, carry forward the last known pressure (bounded lookback ≤ 5 runs).
    - Wishlist delta is always computed with its own conservative bounded lookback (≤ 3 runs).

    Args:
        key: (scientific_name, size_cm) tuple identifying the species/size.
        by_run: dict mapping run datetime -> list of row dicts.
        runs: sorted list of run datetimes.
        cur_run: datetime of the current run.
        wishlist_pressure_map: pre-computed pressure map for the current run
            (from ``compute_wishlist_pressure``).

    Returns:
        Tuple of (wishlist_pressure, wishlist_delta) where each value is
        one of the standard symbols (🔥/⚠️/❌ and ↑/→/↓ respectively).
    """
    cur_keys = {
        (r.get("scientific_name", ""), r.get("size_cm", ""))
        for r in by_run[cur_run]
    }

    if key in cur_keys:
        wishlist_pressure = wishlist_pressure_map.get(key, "❌")
    else:
        carried = get_oos_wishlist_carryover(key, by_run, runs, cur_run)
        wishlist_pressure = carried if carried else "❌"

    wishlist_delta = compute_wishlist_delta(key, by_run, runs, cur_run)

    return wishlist_pressure, wishlist_delta

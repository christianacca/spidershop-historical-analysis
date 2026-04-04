#!/usr/bin/env python3
"""
Shared utility functions for working with historical data rows.

These functions provide common patterns for grouping and identifying
historical scrape data, used by both analysis and website generation.
"""
from typing import Dict, List, Any, Tuple, Optional, Mapping

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

    observed_runs = [
        run_timestamp
        for run_timestamp in runs
        if any(create_species_key(row) == key for row in by_run[run_timestamp])
    ]
    observed_run_set = set(observed_runs)
    first_observed_run: Optional[str] = observed_runs[0] if observed_runs else None
    latest_observed_run: Optional[str] = observed_runs[-1] if observed_runs else None
    total_run_count = len(runs)
    observed_run_count = len(observed_runs)

    current_consecutive_observation_runs = 0
    for run_timestamp in reversed(runs):
        if run_timestamp in observed_run_set:
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


def is_newly_observed_coverage(observation_coverage: Mapping[str, Any]) -> bool:
    """Return whether coverage matches the shared breeder Newly Observed rule."""
    return bool(
        observation_coverage["observed_in_current_run"]
        and observation_coverage["observed_run_count"] <= 2
        and observation_coverage["current_consecutive_observation_runs"]
        == observation_coverage["observed_run_count"]
    )


def format_observation_coverage(observation_coverage: Mapping[str, Any]) -> str:
    """Return compact observation coverage text for sparse-history items."""
    return (
        f"observed {observation_coverage['observed_run_count']}"
        f"/{observation_coverage['total_run_count']} runs"
    )


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


# ---------------------------------------------------------------------------
# Species-level supply timeline (Phase 2 – Size Variant Identity)
# ---------------------------------------------------------------------------

# Thresholds shared between species-level helpers and dealer matrix
SPECIES_HIGH_RELIABILITY_THRESHOLD = 0.8
SPECIES_MEDIUM_RELIABILITY_THRESHOLD = 0.4
SPECIES_SLOW_RESTOCK_MIN_AVG_OOS = 3
SPECIES_MODERATE_RESTOCK_AVG_OOS = 2

# Breeder stock pattern thresholds (mirrors breeder_matrix.py constants)
_SPECIES_SUSTAINED_OOS_RUNS = 4
_SPECIES_EMERGING_MIN_OOS_RUNS = 2
_SPECIES_NEWLY_OBSERVED_MAX_RUNS = 2


def build_species_presence_timeline(
    history_rows: List[Dict[str, Any]],
    scientific_name: str,
) -> Dict[str, bool]:
    """Build a per-run presence timeline for *scientific_name*.

    A species is considered present in a run if any size variant for that
    scientific name appears in that run (Decision 3A).

    Args:
        history_rows: Full historical row set across all species.
        scientific_name: The species to analyse.

    Returns:
        ``{run_timestamp: True/False}`` ordered by run timestamp.
        Every run in the dataset is represented.
    """
    by_run = group_by_run(history_rows)
    ordered_runs = sorted(by_run.keys())
    timeline: Dict[str, bool] = {}
    for run in ordered_runs:
        present = any(
            r["scientific_name"] == scientific_name for r in by_run[run]
        )
        timeline[run] = present
    return timeline


def compute_species_current_oos_runs(
    timeline: Dict[str, bool],
    ordered_runs: List[str],
) -> int:
    """Count consecutive absent runs at the end of *ordered_runs*.

    Per Decision 3A: OOS runs are not additive across retired lineages.
    The counter reflects only the current trailing absence streak.

    Args:
        timeline: ``{run_timestamp: present_bool}`` from
            :func:`build_species_presence_timeline`.
        ordered_runs: Sorted list of all run timestamps.

    Returns:
        Number of consecutive absent runs ending at the current run (0 if
        the species is present in the current run).
    """
    count = 0
    for run in reversed(ordered_runs):
        if timeline.get(run, False):
            break
        count += 1
    return count


def build_species_stock_pattern(
    timeline: Dict[str, bool],
    ordered_runs: List[str],
) -> str:
    """Derive the breeder stock pattern from the species-level presence timeline.

    Pattern labels mirror the existing breeder matrix classifications:
    ``Newly Observed``, ``Sustained``, ``Emerging``, ``Cyclical``, ``Always``.

    Args:
        timeline: ``{run_timestamp: present_bool}`` from
            :func:`build_species_presence_timeline`.
        ordered_runs: Sorted list of all run timestamps.

    Returns:
        One of: ``"Newly Observed"``, ``"Sustained"``, ``"Emerging"``,
        ``"Cyclical"``, ``"Always"``.
    """
    if not ordered_runs:
        return "Always"

    oos_runs = compute_species_current_oos_runs(timeline, ordered_runs)
    current_run = ordered_runs[-1]
    in_current = timeline.get(current_run, False)

    # Newly Observed: observed ≤ 2 times total, all consecutive from first obs,
    # and present in current run.
    all_observed = [r for r in ordered_runs if timeline.get(r, False)]
    observed_run_count = len(all_observed)
    # Trailing consecutive presence
    trailing_present = 0
    for run in reversed(ordered_runs):
        if timeline.get(run, False):
            trailing_present += 1
        else:
            break
    is_newly_observed = (
        in_current
        and observed_run_count <= _SPECIES_NEWLY_OBSERVED_MAX_RUNS
        and trailing_present == observed_run_count
    )

    if is_newly_observed:
        return "Newly Observed"
    if oos_runs >= _SPECIES_SUSTAINED_OOS_RUNS:
        return "Sustained"
    if oos_runs >= _SPECIES_EMERGING_MIN_OOS_RUNS:
        return "Emerging"

    # Cyclical: currently IN, not in previous run, was seen before previous run
    if in_current and len(ordered_runs) >= 3:
        prev_run = ordered_runs[-2]
        if not timeline.get(prev_run, False):
            # Was seen before the previous run?
            seen_before = any(timeline.get(r, False) for r in ordered_runs[:-2])
            if seen_before:
                return "Cyclical"

    return "Always"


def compute_species_stock_reliability(
    timeline: Dict[str, bool],
) -> str:
    """Compute species stock reliability from the presence timeline.

    Args:
        timeline: ``{run_timestamp: present_bool}`` from
            :func:`build_species_presence_timeline`.

    Returns:
        ``"High"`` (≥ 80 % presence), ``"Medium"`` (≥ 40 %), or ``"Low"``.
    """
    if not timeline:
        return "Low"
    total = len(timeline)
    present = sum(1 for v in timeline.values() if v)
    ratio = present / total
    if ratio >= SPECIES_HIGH_RELIABILITY_THRESHOLD:
        return "High"
    if ratio >= SPECIES_MEDIUM_RELIABILITY_THRESHOLD:
        return "Medium"
    return "Low"


def compute_species_avg_oos_duration(
    timeline: Dict[str, bool],
    ordered_runs: List[str],
) -> float:
    """Compute average absence event length from the presence timeline.

    Mirrors the OOS event logic in the existing dealer matrix: absence events
    at the start of history are counted (conservative design).

    Args:
        timeline: ``{run_timestamp: present_bool}``.
        ordered_runs: Sorted run timestamps.

    Returns:
        Rounded average length of absence events (0.0 when no absence events).
    """
    oos_events: List[int] = []
    last_present: Optional[bool] = None
    for run in ordered_runs:
        present = timeline.get(run, False)
        if not present:
            if last_present is True:
                oos_events.append(1)
            elif last_present is False:
                oos_events[-1] += 1
            else:  # first run in history and already absent
                oos_events.append(1)
        last_present = present
    return round(sum(oos_events) / len(oos_events), 1) if oos_events else 0


def compute_species_restock_speed(avg_oos: float) -> str:
    """Derive restock speed label from average OOS duration.

    Args:
        avg_oos: Average OOS event length (from
            :func:`compute_species_avg_oos_duration`).

    Returns:
        ``"Slow"`` (avg ≥ 3), ``"Moderate"`` (avg == 2), or ``"Fast"``.
    """
    if avg_oos >= SPECIES_SLOW_RESTOCK_MIN_AVG_OOS:
        return "Slow"
    if avg_oos == SPECIES_MODERATE_RESTOCK_AVG_OOS:
        return "Moderate"
    return "Fast"


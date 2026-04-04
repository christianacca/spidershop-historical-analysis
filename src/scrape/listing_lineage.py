#!/usr/bin/env python3
"""Size-variant listing lineage detection.

Determines whether a species' size history represents a confirmed or ambiguous
size transition, multiple concurrent variants, or stable single-size history.
"""
from dataclasses import dataclass
from typing import Optional

from shared.history_utils import group_by_run
from shared.url_utils import normalize_product_url


@dataclass
class LineageResult:
    """Encapsulates the result of listing lineage detection for one species."""

    lineage_status: str
    """One of: 'none', 'confirmed-transition', 'ambiguous-transition', 'multi-variant'."""

    previous_size: str
    """The size that was active before the most recent transition. Blank for 'none' and 'multi-variant'."""

    current_active_size: str
    """The current or most recent active size (plain string, or 'A, B' for multi-variant)."""

    transition_date: str
    """YYYY-MM-DD date of first observation of the new size. Blank for 'none' and 'multi-variant'."""

    price_evidence_state: str
    """One of: 'standard', 'transition-affected', 'neutralized', 'multi-variant'."""

    wishlist_evidence_state: str
    """One of: 'standard', 'carried-across-transition', 'neutralized-ambiguous', 'max-active-variant'."""

    transition_message: str
    """Human-readable tooltip / banner text. Blank for 'none'."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_species_lineage(
    history_rows: list[dict],
    scientific_name: str,
) -> LineageResult:
    """Detect the listing lineage state for *scientific_name*.

    Algorithm:
    1. Build per-run size maps for the species.
    2. If the current run has ≥ 2 sizes → multi-variant.
    3. If only one size has ever been observed → none.
    4. Otherwise find the most recent transition (prev_size → current_active_size)
       and classify it as confirmed or ambiguous using the 5 Decision-2 criteria.

    Args:
        history_rows: All history rows (any species) from the full dataset.
        scientific_name: The species to analyse.

    Returns:
        A :class:`LineageResult` describing the current lineage state.
    """
    by_run = group_by_run(history_rows)
    ordered_runs = sorted(by_run.keys())

    if not ordered_runs:
        return _none_result("")

    # Build {run → {size_cm: page_url}} for this species only
    species_by_run: dict[str, dict[str, str]] = {}
    for run in ordered_runs:
        for row in by_run[run]:
            if row["scientific_name"] == scientific_name:
                species_by_run.setdefault(run, {})[row["size_cm"]] = row.get(
                    "page_url", ""
                )

    current_run = ordered_runs[-1]
    current_sizes: dict[str, str] = species_by_run.get(current_run, {})

    # ── Multi-variant: ≥ 2 sizes active in the current run ─────────────────
    if len(current_sizes) >= 2:
        return _multi_variant_result(current_sizes)

    # ── Collect all sizes ever seen ─────────────────────────────────────────
    all_sizes: set[str] = set()
    for sizes_dict in species_by_run.values():
        all_sizes.update(sizes_dict.keys())

    if len(all_sizes) <= 1:
        # Only one size ever; report whatever that is (even if currently OUT)
        the_size = (
            next(iter(current_sizes))
            if current_sizes
            else (next(iter(all_sizes)) if all_sizes else "")
        )
        return _none_result(the_size)

    # ── Find the most recent transition event ───────────────────────────────
    # Determine "current active size": 1 active now, or most recent if OUT.
    if len(current_sizes) == 1:
        current_active_size = next(iter(current_sizes))
    else:
        # OUT — find the most recent single-size run
        current_active_size = _most_recent_single_size(
            ordered_runs, species_by_run, current_run
        )
        if not current_active_size:
            return _none_result("")

    # Find first run where current_active_size appeared
    r_first_current: Optional[str] = None
    for run in ordered_runs:
        if current_active_size in species_by_run.get(run, {}):
            r_first_current = run
            break

    if r_first_current is None:
        return _none_result(current_active_size)

    r_first_idx = ordered_runs.index(r_first_current)

    # Find the most recent other size active in any run BEFORE r_first_current
    prev_size: Optional[str] = None
    prev_size_last_run: Optional[str] = None
    prev_size_url: Optional[str] = None

    for i in range(r_first_idx - 1, -1, -1):
        run = ordered_runs[i]
        sizes_in_run = species_by_run.get(run, {})
        other = {s: u for s, u in sizes_in_run.items() if s != current_active_size}
        if other:
            # Use the first other size found (most recently active)
            prev_size = next(iter(other))
            prev_size_last_run = run
            prev_size_url = other[prev_size]
            break

    if prev_size is None or prev_size_last_run is None:
        # current_active_size was the first size ever seen for this species
        return _none_result(current_active_size)

    prev_last_idx = ordered_runs.index(prev_size_last_run)
    transition_date = r_first_current[:10]  # "YYYY-MM-DD"

    # ── Check the 5 confirmed-transition conditions (Decision 2) ────────────
    # Condition 2: normalized URLs match
    norm_prev = normalize_product_url(prev_size_url) if prev_size_url else ""
    curr_url_at_first = species_by_run.get(r_first_current, {}).get(
        current_active_size, ""
    )
    norm_curr = normalize_product_url(curr_url_at_first) if curr_url_at_first else ""
    url_matches = bool(norm_prev) and bool(norm_curr) and (norm_prev == norm_curr)

    # Condition 3: new size appeared within 3 runs of old size's final observation
    gap = r_first_idx - prev_last_idx
    within_window = gap <= 3

    # Conditions 4 & 5: no same-run overlap between the two sizes during handoff
    # window = [prev_last_run … r_first_current] inclusive
    has_overlap = False
    for run in ordered_runs[prev_last_idx: r_first_idx + 1]:
        sizes_in_run = species_by_run.get(run, {})
        if prev_size in sizes_in_run and current_active_size in sizes_in_run:
            has_overlap = True
            break

    if url_matches and within_window and not has_overlap:
        return _confirmed_result(prev_size, current_active_size, transition_date)
    else:
        return _ambiguous_result(prev_size, current_active_size, transition_date)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _sort_sizes(sizes: "set[str] | list[str]") -> list[str]:
    """Sort sizes ascending numerically when possible, alphabetically otherwise."""

    def _key(s: str) -> tuple:
        try:
            return (0, float(s))
        except (ValueError, TypeError):
            return (1, s)

    return sorted(sizes, key=_key)


def _most_recent_single_size(
    ordered_runs: list[str],
    species_by_run: dict[str, dict[str, str]],
    current_run: str,
) -> str:
    """Walk backward from current_run to find the most recent run with exactly one size."""
    cur_idx = ordered_runs.index(current_run)
    for i in range(cur_idx, -1, -1):
        run = ordered_runs[i]
        sizes = species_by_run.get(run, {})
        if len(sizes) == 1:
            return next(iter(sizes))
    return ""


# ---------------------------------------------------------------------------
# Result constructors
# ---------------------------------------------------------------------------


def _none_result(current_active_size: str) -> LineageResult:
    return LineageResult(
        lineage_status="none",
        previous_size="",
        current_active_size=current_active_size,
        transition_date="",
        price_evidence_state="standard",
        wishlist_evidence_state="standard",
        transition_message="",
    )


def _multi_variant_result(current_sizes: dict[str, str]) -> LineageResult:
    sorted_sizes = _sort_sizes(current_sizes.keys())
    current_active_size = ", ".join(sorted_sizes)
    sizes_str = " cm and ".join(sorted_sizes)
    message = (
        f"This species has multiple active size variants in the current run "
        f"({sizes_str} cm). The row remains species-level. Current wishlist "
        f"context uses the highest active variant count without summing listings. "
        f"Price evidence is not shown as one clean single-line series."
    )
    return LineageResult(
        lineage_status="multi-variant",
        previous_size="",
        current_active_size=current_active_size,
        transition_date="",
        price_evidence_state="multi-variant",
        wishlist_evidence_state="max-active-variant",
        transition_message=message,
    )


def _confirmed_result(
    prev_size: str,
    current_active_size: str,
    transition_date: str,
) -> LineageResult:
    message = (
        f"Size changed from {prev_size} cm to {current_active_size} cm on "
        f"{transition_date}. Wishlist continuity is treated as continuous for "
        f"this listing. Price evidence is still useful, but recent movement may "
        f"partly reflect the size change rather than a pure same-unit price move."
    )
    return LineageResult(
        lineage_status="confirmed-transition",
        previous_size=prev_size,
        current_active_size=current_active_size,
        transition_date=transition_date,
        price_evidence_state="transition-affected",
        wishlist_evidence_state="carried-across-transition",
        transition_message=message,
    )


def _ambiguous_result(
    prev_size: str,
    current_active_size: str,
    transition_date: str,
) -> LineageResult:
    message = (
        f"Size handoff from {prev_size} cm to {current_active_size} cm could not "
        f"be confirmed as one continuing listing. Wishlist continuity is not "
        f"carried across the handoff. Price and momentum evidence are shown in a "
        f"conservative downgraded state."
    )
    return LineageResult(
        lineage_status="ambiguous-transition",
        previous_size=prev_size,
        current_active_size=current_active_size,
        transition_date=transition_date,
        price_evidence_state="neutralized",
        wishlist_evidence_state="neutralized-ambiguous",
        transition_message=message,
    )

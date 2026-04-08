"""Market Health DTO module for the History Insights page.

Builds a MarketHealthPayload-shaped dict from raw history CSV rows for a
given time window. No file I/O, no HTML templates — data in, dict out.

Public API:
    build_market_health_payload(history_rows, window_id, selected_genera,
                                is_all_selected, reference_dt) -> dict
    build_market_health_payload_all_windows(history_rows, selected_genera,
                                           is_all_selected, reference_dt) -> dict
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Optional

# ---------------------------------------------------------------------------
# Window configuration
# ---------------------------------------------------------------------------

_ALL_WINDOW_IDS = [
    "this-month",
    "last-month",
    "current-quarter",
    "last-quarter",
    "this-year",
    "last-year",
    "all-time",
]

_SPARKLINE_BASIS_NOTES = {
    "this-month": (
        "Compare within a row. Solid shows this month; dashed shows the matched"
        " point last month."
    ),
    "last-month": (
        "Compare within a row. Solid shows last month; dashed shows the prior full"
        " month."
    ),
    "current-quarter": (
        "Compare within a row. Solid shows the current quarter; dashed shows the"
        " matched point last quarter."
    ),
    "last-quarter": (
        "Compare within a row. Solid shows last quarter; dashed shows the prior"
        " full quarter."
    ),
    "this-year": (
        "Compare within a row. Solid shows this year to date; dashed shows the"
        " matched point last year."
    ),
    "last-year": (
        "Compare within a row. Solid shows last year; dashed shows the prior full"
        " year."
    ),
    "all-time": (
        "All-time view has no dashed overlay. Compare within a row; each metric"
        " keeps its own vertical scale."
    ),
}

_WINDOW_LABELS = {
    "this-month": "This month",
    "last-month": "Last month",
    "current-quarter": "Current quarter",
    "last-quarter": "Last quarter",
    "this-year": "This year",
    "last-year": "Last year",
    "all-time": "All time",
}

_WINDOW_BASIS_NOTES = {
    "this-month": "Comparison basis: month to date vs same point last month.",
    "last-month": "Comparison basis: last full month vs prior full month.",
    "current-quarter": "Comparison basis: quarter to date vs prior quarter QTD.",
    "last-quarter": "Comparison basis: last full quarter vs prior full quarter.",
    "this-year": "Comparison basis: year to date vs same point last year.",
    "last-year": "Comparison basis: last full year vs year before.",
    "all-time": (
        "Comparison basis: structural context only, with no prior-period delta."
    ),
}

# Human-readable prior period labels used in copy sentences.
_PRIOR_LABELS = {
    "this-month": "the same point last month",
    "last-month": "the prior full month",
    "current-quarter": "the same point last quarter",
    "last-quarter": "the prior full quarter",
    "this-year": "the same point last year",
    "last-year": "the prior full year",
}

# Short labels used in KPI delta badge text and events values (spec §6).
_PRIOR_DELTA_LABELS = {
    "this-month": "prior month MTD",
    "last-month": "prior full month",
    "current-quarter": "prior quarter QTD",
    "last-quarter": "prior full quarter",
    "this-year": "prior year YTD",
    "last-year": "prior full year",
}

# Events title and subtitle per window.
_EVENTS_TITLES = {
    "this-month": "Run-to-run market events this month",
    "last-month": "Run-to-run market events last month",
    "current-quarter": "Run-to-run market events this quarter",
    "last-quarter": "Run-to-run market events last quarter",
    "this-year": "Run-to-run market events this year",
    "last-year": "Run-to-run market events last year",
    "all-time": "Market events across all time",
}

_EVENTS_SUBTITLES = {
    "this-month": "This month event totals against the same point last month.",
    "last-month": "Last month event totals against the prior full month.",
    "current-quarter": "Current-quarter event totals against the same point last quarter.",
    "last-quarter": "Last-quarter event totals against the prior full quarter.",
    "this-year": "Year-to-date event totals against the same point last year.",
    "last-year": "Last-year event totals against the prior full year.",
    "all-time": "All-time event totals as structural context only.",
}


# ---------------------------------------------------------------------------
# Window date boundaries
# ---------------------------------------------------------------------------

def _quarter_start(dt: datetime) -> datetime:
    month = ((dt.month - 1) // 3) * 3 + 1
    return dt.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)


def _get_window_bounds(
    window_id: str, ref: datetime
) -> tuple[datetime, datetime, Optional[datetime], Optional[datetime], bool]:
    """Return (win_start, win_end, prior_start, prior_end, show_prior)."""
    y, m, d = ref.year, ref.month, ref.day

    if window_id == "this-month":
        win_start = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        win_end = ref
        # Same date range last month
        if m == 1:
            prior_month = 12
            prior_year = y - 1
        else:
            prior_month = m - 1
            prior_year = y
        prior_start = win_start.replace(year=prior_year, month=prior_month)
        # Clamp day to last day of prior month
        prior_day = min(d, _days_in_month(prior_month, prior_year))
        prior_end = ref.replace(
            year=prior_year, month=prior_month, day=prior_day,
            hour=23, minute=59, second=59, microsecond=999999,
        )
        return win_start, win_end, prior_start, prior_end, True

    if window_id == "last-month":
        if m == 1:
            lm, ly = 12, y - 1
        else:
            lm, ly = m - 1, y
        win_start = ref.replace(
            year=ly, month=lm, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        win_end = ref.replace(
            year=ly, month=lm, day=_days_in_month(lm, ly),
            hour=23, minute=59, second=59, microsecond=999999,
        )
        # Month before last
        if lm == 1:
            pm, py = 12, ly - 1
        else:
            pm, py = lm - 1, ly
        prior_start = ref.replace(
            year=py, month=pm, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        prior_end = ref.replace(
            year=py, month=pm, day=_days_in_month(pm, py),
            hour=23, minute=59, second=59, microsecond=999999,
        )
        return win_start, win_end, prior_start, prior_end, True

    if window_id == "current-quarter":
        qs = _quarter_start(ref)
        win_start = qs
        win_end = ref
        # Same date range last quarter
        prior_qs = _quarter_start(qs - timedelta(days=1))
        day_offset = (ref - qs).days
        prior_end_candidate = prior_qs + timedelta(days=day_offset)
        prior_start = prior_qs
        prior_end = prior_end_candidate.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        return win_start, win_end, prior_start, prior_end, True

    if window_id == "last-quarter":
        qs = _quarter_start(ref)
        prev_qs = _quarter_start(qs - timedelta(days=1))
        win_start = prev_qs
        win_end = (qs - timedelta(seconds=1)).replace(microsecond=999999)
        # Quarter before last
        prior_qs = _quarter_start(prev_qs - timedelta(days=1))
        prior_start = prior_qs
        prior_end = (prev_qs - timedelta(seconds=1)).replace(microsecond=999999)
        return win_start, win_end, prior_start, prior_end, True

    if window_id == "this-year":
        win_start = ref.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        win_end = ref
        prior_start = win_start.replace(year=y - 1)
        day_of_year = (ref - win_start).days
        prior_end = prior_start + timedelta(days=day_of_year)
        prior_end = prior_end.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        return win_start, win_end, prior_start, prior_end, True

    if window_id == "last-year":
        win_start = ref.replace(
            year=y - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        win_end = ref.replace(
            year=y - 1, month=12, day=31,
            hour=23, minute=59, second=59, microsecond=999999,
        )
        prior_start = win_start.replace(year=y - 2)
        prior_end = win_end.replace(year=y - 2)
        return win_start, win_end, prior_start, prior_end, True

    # all-time
    sentinel = datetime(1970, 1, 1)
    return sentinel, ref, None, None, False


def _days_in_month(month: int, year: int) -> int:
    if month == 12:
        return 31
    return (datetime(year, month + 1, 1) - timedelta(days=1)).day


# ---------------------------------------------------------------------------
# Row parsing helpers
# ---------------------------------------------------------------------------

def _parse_dt(s: str) -> Optional[datetime]:
    """Parse ISO datetime string; return None on failure."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _filter_rows_to_window(
    rows: list[dict], win_start: datetime, win_end: datetime
) -> list[dict]:
    result = []
    for row in rows:
        dt = _parse_dt(row.get("scrape_datetime", ""))
        if dt is not None and win_start <= dt <= win_end:
            result.append(row)
    return result


def _apply_genus_filter(
    rows: list[dict], selected_genera: list[str], is_all_selected: bool
) -> list[dict]:
    if is_all_selected or not selected_genera:
        return rows
    genera_set = set(selected_genera)
    result = []
    for row in rows:
        genus = row.get("scientific_name", "").split()[0]
        if genus in genera_set:
            result.append(row)
    return result


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def _get_sorted_runs(rows: list[dict]) -> list[str]:
    """Return sorted distinct scrape_datetime strings from rows."""
    return sorted({row["scrape_datetime"] for row in rows})


def _species_in_run(rows: list[dict], run_dt: str) -> set[str]:
    return {r["scientific_name"] for r in rows if r["scrape_datetime"] == run_dt}


def _compute_observed(rows: list[dict]) -> int:
    """Count distinct species seen in-stock at any point within the window."""
    return len({r["scientific_name"] for r in rows})


def _compute_stock_rate(rows: list[dict]) -> int:
    """
    Numerator: distinct species in-stock at the latest run.
    Denominator: distinct species seen in-stock at any point.
    Returns integer percentage (0–100).
    """
    if not rows:
        return 0
    all_species = {r["scientific_name"] for r in rows}
    latest_run = max(r["scrape_datetime"] for r in rows)
    species_at_latest = _species_in_run(rows, latest_run)
    if not all_species:
        return 0
    return round(len(species_at_latest) / len(all_species) * 100)


def _compute_median_wishlist(rows: list[dict]) -> int:
    """Median wishlist across in-stock species at the latest run.

    For species with multiple active variants, uses the max wishlist_count.
    """
    if not rows:
        return 0
    latest_run = max(r["scrape_datetime"] for r in rows)
    latest_rows = [r for r in rows if r["scrape_datetime"] == latest_run]

    # Group by species; take max wishlist per species
    by_species: dict[str, float] = {}
    for r in latest_rows:
        species = r["scientific_name"]
        try:
            wl = float(r.get("wishlist_count") or 0)
        except (ValueError, TypeError):
            wl = 0.0
        by_species[species] = max(by_species.get(species, 0.0), wl)

    values = list(by_species.values())
    if not values:
        return 0
    return round(median(values))


def _compute_median_price(rows: list[dict]) -> float:
    """Median price across in-stock species at the latest run.

    For species with multiple active variants, uses the max price.
    """
    if not rows:
        return 0.0
    latest_run = max(r["scrape_datetime"] for r in rows)
    latest_rows = [r for r in rows if r["scrape_datetime"] == latest_run]

    by_species: dict[str, float] = {}
    for r in latest_rows:
        species = r["scientific_name"]
        try:
            price = float(r.get("price_gbp") or 0)
        except (ValueError, TypeError):
            price = 0.0
        by_species[species] = max(by_species.get(species, 0.0), price)

    values = list(by_species.values())
    if not values:
        return 0.0
    return median(values)


# ---------------------------------------------------------------------------
# Sparkline series computation
# ---------------------------------------------------------------------------

def _build_sparkline_for_metric(
    rows: list[dict],
    metric: str,
    all_window_rows: list[dict],
) -> list[float]:
    """Build a 12-point sparkline series for one metric from run data."""
    runs = _get_sorted_runs(rows)
    if not runs:
        return [0.0] * 12

    def _value_at_run(run_dt: str) -> float:
        run_rows = [r for r in rows if r["scrape_datetime"] == run_dt]
        if not run_rows:
            return 0.0
        if metric == "observed":
            return float(len({r["scientific_name"] for r in run_rows}))
        if metric == "stock":
            all_species_up_to = {
                r["scientific_name"]
                for r in rows
                if r["scrape_datetime"] <= run_dt
            }
            run_species = {r["scientific_name"] for r in run_rows}
            if not all_species_up_to:
                return 0.0
            return round(len(run_species) / len(all_species_up_to) * 100)
        if metric == "wishlist":
            by_species: dict[str, float] = {}
            for r in run_rows:
                sp = r["scientific_name"]
                try:
                    wl = float(r.get("wishlist_count") or 0)
                except (ValueError, TypeError):
                    wl = 0.0
                by_species[sp] = max(by_species.get(sp, 0.0), wl)
            vals = list(by_species.values())
            return round(median(vals)) if vals else 0.0
        if metric == "price":
            by_species_p: dict[str, float] = {}
            for r in run_rows:
                sp = r["scientific_name"]
                try:
                    p = float(r.get("price_gbp") or 0)
                except (ValueError, TypeError):
                    p = 0.0
                by_species_p[sp] = max(by_species_p.get(sp, 0.0), p)
            vals_p = list(by_species_p.values())
            return round(median(vals_p)) if vals_p else 0.0
        return 0.0

    # Compute raw values at each available run
    raw_values = [_value_at_run(r) for r in runs]

    # Resample to exactly 12 points
    return _resample_to_12(raw_values)


def _resample_to_12(values: list[float]) -> list[float]:
    """Resample a list of N values to exactly 12 by even-index sampling."""
    n = len(values)
    if n == 0:
        return [0.0] * 12
    if n >= 12:
        indices = [round(i * (n - 1) / 11.0) for i in range(12)]
        return [float(values[idx]) for idx in indices]
    # n < 12: use all available, pad with last value
    padded = list(values) + [values[-1]] * (12 - n)
    return [float(v) for v in padded]


# ---------------------------------------------------------------------------
# Events computation
# ---------------------------------------------------------------------------

def _is_size_transition(
    species: str,
    runs: list[str],
    prev_run_idx: int,
    curr_run_idx: int,
    rows: list[dict],
    max_gap: int = 3,
) -> bool:
    """Detect if a drop+reappearance is a size transition (same URL, within max_gap runs)."""
    if curr_run_idx - prev_run_idx > max_gap:
        return False
    prev_rows = [
        r for r in rows
        if r["scrape_datetime"] == runs[prev_run_idx] and r["scientific_name"] == species
    ]
    curr_rows = [
        r for r in rows
        if r["scrape_datetime"] == runs[curr_run_idx] and r["scientific_name"] == species
    ]
    prev_urls = {r.get("page_url", "") for r in prev_rows}
    curr_urls = {r.get("page_url", "") for r in curr_rows}
    # Same URL + different size = size transition
    shared_urls = prev_urls & curr_urls
    if not shared_urls:
        return False
    for url in shared_urls:
        prev_sizes = {
            r.get("size_cm", "") for r in prev_rows if r.get("page_url") == url
        }
        curr_sizes = {
            r.get("size_cm", "") for r in curr_rows if r.get("page_url") == url
        }
        if prev_sizes != curr_sizes:
            return True
    return False


def _compute_events(
    rows: list[dict], window_id: str, delta_label: str
) -> dict:
    """Compute event counts across all run-pairs within the window."""
    runs = _get_sorted_runs(rows)
    is_all_time = window_id == "all-time"

    new_listings_count = 0
    dropped_listings_count = 0
    restock_count = 0
    oos_flip_count = 0

    if len(runs) < 2:
        # Can't compute transitions with fewer than 2 runs
        pass
    else:
        # All species ever seen in the window
        all_species = {r["scientific_name"] for r in rows}

        # Track which species were seen before the window (in prior rows outside the window)
        # For simplicity: species in first run are considered "pre-existing"
        first_run_species = _species_in_run(rows, runs[0])

        for i in range(1, len(runs)):
            prev_species = _species_in_run(rows, runs[i - 1])
            curr_species = _species_in_run(rows, runs[i])

            appeared = curr_species - prev_species
            disappeared = prev_species - curr_species

            for sp in appeared:
                # Check if this is a size transition
                last_seen_idx = _find_last_seen_idx(sp, runs, i - 1, rows)
                if last_seen_idx is None:
                    # Brand new species in this window
                    if i > 0:
                        new_listings_count += 1
                elif _is_size_transition(sp, runs, last_seen_idx, i, rows):
                    pass  # size transition — not counted as new listing
                else:
                    restock_count += 1

            for sp in disappeared:
                next_seen_idx = _find_next_seen_idx(sp, runs, i, rows)
                if next_seen_idx is None:
                    dropped_listings_count += 1
                    oos_flip_count += 1
                elif _is_size_transition(sp, runs, i - 1, next_seen_idx, rows):
                    pass  # size transition — not counted as drop
                else:
                    oos_flip_count += 1

    def _events_copy_new_listings(count: int) -> str:
        if is_all_time:
            return "Use this as background volume, not as a directional comparison."
        if count >= 5:
            return (
                "Introductions are materially ahead of the matched point last period,"
                " which supports the breadth expansion visible in the chart."
            )
        return (
            "Fresh introductions are only slightly ahead, so the catalog is still"
            " expanding but not surging."
        )

    def _events_copy_dropped(count: int) -> str:
        if is_all_time:
            return (
                "All-time churn is useful for scale, but weak for saying what changed"
                " recently."
            )
        return (
            "Churn also rose, but the balance still favors broader assortment rather"
            " than retreat."
        )

    def _events_copy_restocks(count: int) -> str:
        if is_all_time:
            return (
                "This shows how much movement exists in the market overall, not whether"
                " it is improving now."
            )
        if count == 0:
            return (
                "No OUT-to-IN restocks occurred this period. If the in-stock rate is"
                " also falling, supply may have stalled rather than just tightened."
            )
        return (
            "Movement is active; stock is not simply frozen, even though the in-stock"
            " rate may be weaker than last period."
        )

    def _events_copy_oos_flips(count: int) -> str:
        if is_all_time:
            return (
                "Use this as structural supply-friction context, not as a directional"
                " signal about what changed recently."
            )
        return (
            "More listings are moving from IN to OUT than at the same point last period,"
            " which helps explain why availability may be softer."
        )

    return {
        "title": _EVENTS_TITLES.get(window_id, "Market events"),
        "subtitle": _EVENTS_SUBTITLES.get(window_id, ""),
        "newListings": {
            "label": "Listings added",
            "value": f"{new_listings_count} total" if is_all_time else f"+{new_listings_count} vs {delta_label}",
            "copy": _events_copy_new_listings(new_listings_count),
        },
        "droppedListings": {
            "label": "Listings removed",
            "value": f"{dropped_listings_count} total" if is_all_time else f"{dropped_listings_count} vs {delta_label}",
            "copy": _events_copy_dropped(dropped_listings_count),
        },
        "restocks": {
            "label": "OUT \u2192 IN restocks",
            "value": f"{restock_count} total" if is_all_time else f"{restock_count} vs {delta_label}",
            "copy": _events_copy_restocks(restock_count),
        },
        "oosFlips": {
            "label": "IN \u2192 OUT stockouts",
            "value": f"{oos_flip_count} total" if is_all_time else f"+{oos_flip_count} vs {delta_label}",
            "copy": _events_copy_oos_flips(oos_flip_count),
        },
    }


def _find_last_seen_idx(
    species: str, runs: list[str], before_idx: int, rows: list[dict]
) -> Optional[int]:
    """Find most recent run index where species was seen, searching backwards from before_idx."""
    for i in range(before_idx, -1, -1):
        if species in _species_in_run(rows, runs[i]):
            return i
    return None


def _find_next_seen_idx(
    species: str, runs: list[str], after_idx: int, rows: list[dict]
) -> Optional[int]:
    """Find next run index where species appears, searching forwards from after_idx."""
    for i in range(after_idx, len(runs)):
        if species in _species_in_run(rows, runs[i]):
            return i
    return None


# ---------------------------------------------------------------------------
# Copy selection
# ---------------------------------------------------------------------------

def _observed_copy(delta: Optional[int], prior_label: str, is_all_time: bool) -> str:
    if is_all_time:
        return (
            "All-time view is best read as structural context: the catalog is broad"
            " enough to support opportunity hunting, but this lens is not about recent"
            " acceleration."
        )
    if delta is None:
        return (
            "Breadth within the selected window gives a picture of available assortment,"
            " but no prior period is available for comparison."
        )
    if delta >= 3:
        return (
            f"Breadth is ahead of {prior_label}, so the market still looks alive on"
            " assortment even while actual stock is getting tighter."
        )
    if delta >= 0:
        return (
            f"Breadth is only slightly ahead of {prior_label}, so the catalog still"
            " looks broad without signalling a step-change in assortment."
        )
    return (
        f"Fewer species are being seen in-stock than at {prior_label}, which may"
        " suggest some genera are becoming harder to source."
    )


def _stock_copy(
    delta: Optional[int], value_pct: int, prior_label: str, is_all_time: bool
) -> str:
    if is_all_time:
        return (
            "All-time availability smooths out short-term swings, so it is useful for"
            " background context rather than telling you what changed recently."
        )
    if delta is None:
        return f"Availability is at {value_pct}% for the selected window."
    if delta <= -7:
        return (
            f"{value_pct}% of listings are available now. That is {abs(delta)}"
            f" percentage points lower than {prior_label}, so availability is slipping"
            " even while the species count remains broad."
        )
    if delta <= -1:
        return (
            f"Availability is a touch weaker than {prior_label}. That reads more like"
            " a near-term tightening than a structural collapse."
        )
    if delta == 0:
        return f"The in-stock rate is holding steady vs {prior_label}."
    return (
        f"Availability is firmer than {prior_label}, which suggests supply is keeping"
        " pace with demand."
    )


def _wishlist_copy(delta: Optional[int], prior_label: str, is_all_time: bool) -> str:
    if is_all_time:
        return (
            "All-time wishlist levels show the long-run demand floor for your selected"
            " genera, not whether interest just strengthened this month or quarter."
        )
    if delta is None:
        return (
            "Wishlist interest is visible for the selected window,"
            " but no prior period is available for comparison."
        )
    if delta >= 4:
        return (
            f"Median wishlist counts are ahead of {prior_label}, reinforcing the idea"
            " that interest is improving while availability slips."
        )
    if delta >= 1:
        return (
            f"Median wishlist counts are modestly above {prior_label}, which suggests"
            " demand is holding without obviously overheating."
        )
    if delta == 0:
        return f"Median wishlist demand is stable vs {prior_label}."
    return f"Demand looks softer than {prior_label}."


def _price_copy(delta: Optional[int], prior_label: str, is_all_time: bool) -> str:
    if is_all_time:
        return (
            "All-time price mainly describes the market baseline. It is less useful than"
            " shorter windows when you are deciding whether recent conditions have"
            " shifted."
        )
    if delta is None:
        return (
            "Price data is available for the selected window,"
            " but no prior period is available for comparison."
        )
    if delta >= 2:
        return (
            f"Prices are somewhat firmer than {prior_label}, but the move is still"
            " smaller than the availability shift. Supply pressure remains the more"
            " important signal."
        )
    if delta == 1:
        return (
            f"Prices edged up a little relative to {prior_label}, which fits a market"
            " that is tightening gradually rather than repricing sharply."
        )
    if delta == 0:
        return (
            "Price is steady, so the main movement appears to be availability rather"
            " than inflation."
        )
    return (
        f"Prices have softened vs {prior_label}, which runs counter to the"
        " tighter-supply read."
    )


# ---------------------------------------------------------------------------
# Delta formatting helpers
# ---------------------------------------------------------------------------

def _format_observed_delta(delta: Optional[int], is_all_time: bool, delta_label: str) -> tuple[str, str]:
    """Return (delta_text, delta_class)."""
    if is_all_time:
        return "No prior comparison", "flat"
    if delta is None:
        return "No prior comparison", "flat"
    sign = "+" if delta >= 0 else ""
    cls = "down" if delta < 0 else ""
    return f"{sign}{delta} vs {delta_label}", cls


def _format_stock_delta(delta: Optional[int], is_all_time: bool, delta_label: str) -> tuple[str, str]:
    if is_all_time:
        return "No prior comparison", "flat"
    if delta is None:
        return "No prior comparison", "flat"
    sign = "+" if delta > 0 else ""
    cls = "down" if delta < 0 else ""
    return f"{sign}{delta} pts vs {delta_label}", cls


def _format_wishlist_delta(delta: Optional[int], is_all_time: bool, delta_label: str) -> tuple[str, str]:
    if is_all_time:
        return "No prior comparison", "flat"
    if delta is None:
        return "No prior comparison", "flat"
    sign = "+" if delta >= 0 else ""
    cls = "flat" if delta == 0 else ("down" if delta < 0 else "")
    return f"{sign}{delta} vs {delta_label}", cls


def _format_price_delta(delta: Optional[int], is_all_time: bool, delta_label: str) -> tuple[str, str]:
    if is_all_time:
        return "No prior comparison", "flat"
    if delta is None:
        return "No prior comparison", "flat"
    sign = "+" if delta > 0 else ""
    cls = "flat" if delta == 0 else ("down" if delta < 0 else "")
    return f"{sign}GBP {delta} vs {delta_label}", cls


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def build_market_health_payload(
    history_rows: list[dict],
    window_id: str,
    selected_genera: list[str],
    is_all_selected: bool = True,
    reference_dt: Optional[datetime] = None,
) -> dict:
    """Build a MarketHealthPayload-shaped dict for the given window.

    Args:
        history_rows: flat list of CSV row dicts with columns:
            scrape_datetime, scientific_name, common_name, size_cm,
            price_gbp, wishlist_count, page_url.
        window_id: one of the seven WindowId values.
        selected_genera: list of genus names to filter to when not all-selected.
        is_all_selected: True = market-wide view; False = filter to selected_genera.
        reference_dt: override current date (for testing). Defaults to datetime.now().

    Returns:
        Dict matching the MarketHealthPayload TypeScript interface.
    """
    ref = reference_dt or datetime.now()

    win_start, win_end, prior_start, prior_end, show_prior = _get_window_bounds(
        window_id, ref
    )
    is_all_time = window_id == "all-time"

    # Filter rows to window
    win_rows = _filter_rows_to_window(history_rows, win_start, win_end)
    win_rows = _apply_genus_filter(win_rows, selected_genera, is_all_selected)

    # Filter rows to prior window (if applicable)
    if show_prior and prior_start and prior_end:
        prior_rows = _filter_rows_to_window(history_rows, prior_start, prior_end)
        prior_rows = _apply_genus_filter(prior_rows, selected_genera, is_all_selected)
    else:
        prior_rows = []

    # Determine if we have enough data for meaningful comparisons
    win_runs = _get_sorted_runs(win_rows)
    has_current_data = len(win_runs) >= 1
    has_prior_data = len(_get_sorted_runs(prior_rows)) >= 1
    # showPrior is a property of the window type only (all-time = False, others = True).
    # effective_show_prior additionally requires that prior data actually exists.
    effective_show_prior = show_prior and has_prior_data

    # Edge case: no data at all — return safe empty payload
    if not has_current_data:
        return _empty_payload(window_id, is_all_time, is_all_selected, selected_genera)

    # Compute current-period metrics
    curr_observed = _compute_observed(win_rows)
    curr_stock = _compute_stock_rate(win_rows)
    curr_wishlist = _compute_median_wishlist(win_rows)
    curr_price = _compute_median_price(win_rows)

    # Compute prior metrics
    if effective_show_prior:
        prior_observed = _compute_observed(prior_rows)
        prior_stock = _compute_stock_rate(prior_rows)
        prior_wishlist = _compute_median_wishlist(prior_rows)
        prior_price = _compute_median_price(prior_rows)

        d_observed = curr_observed - prior_observed
        d_stock = curr_stock - prior_stock
        d_wishlist = curr_wishlist - prior_wishlist
        d_price = round(curr_price - prior_price)
    else:
        d_observed = d_stock = d_wishlist = d_price = None

    prior_label = _PRIOR_LABELS.get(window_id, "prior period")
    delta_label = _PRIOR_DELTA_LABELS.get(window_id, "prior period")

    # Format deltas
    obs_delta_text, obs_delta_cls = _format_observed_delta(d_observed, is_all_time, delta_label)
    stock_delta_text, stock_delta_cls = _format_stock_delta(d_stock, is_all_time, delta_label)
    wl_delta_text, wl_delta_cls = _format_wishlist_delta(d_wishlist, is_all_time, delta_label)
    price_delta_text, price_delta_cls = _format_price_delta(d_price, is_all_time, delta_label)

    # Build sparkline series
    observed_series = _build_sparkline_for_metric(win_rows, "observed", win_rows)
    stock_series = _build_sparkline_for_metric(win_rows, "stock", win_rows)
    wishlist_series = _build_sparkline_for_metric(win_rows, "wishlist", win_rows)
    price_series = _build_sparkline_for_metric(win_rows, "price", win_rows)

    if effective_show_prior:
        obs_prior = _build_sparkline_for_metric(prior_rows, "observed", prior_rows)
        stock_prior = _build_sparkline_for_metric(prior_rows, "stock", prior_rows)
        wl_prior = _build_sparkline_for_metric(prior_rows, "wishlist", prior_rows)
        price_prior = _build_sparkline_for_metric(prior_rows, "price", prior_rows)
    else:
        obs_prior = stock_prior = wl_prior = price_prior = []

    # Compute events
    events = _compute_events(win_rows, window_id, delta_label)

    # Build scope label
    scope_label = _build_scope_label(selected_genera, is_all_selected)

    return {
        "windowId": window_id,
        "windowLabel": _WINDOW_LABELS.get(window_id, window_id),
        "windowBasisNote": _WINDOW_BASIS_NOTES.get(window_id, ""),
        # showPrior: True for non-all-time windows with prior data and ≥2 current scrapes.
        "showPrior": effective_show_prior and len(win_runs) >= 2,
        "sparklineBasisNote": _SPARKLINE_BASIS_NOTES.get(window_id, ""),
        "isAllSelected": is_all_selected,
        "generaCount": 0 if is_all_selected else len(selected_genera),
        "scopeLabel": scope_label,
        "kpis": {
            "observed": {
                "id": "observed",
                "title": "Observed species",
                "value": str(curr_observed),
                "delta": obs_delta_text,
                "deltaClass": obs_delta_cls,
                "copy": _observed_copy(d_observed, prior_label, is_all_time),
            },
            "stock": {
                "id": "stock",
                "title": "In-stock rate",
                "value": f"{curr_stock}%",
                "delta": stock_delta_text,
                "deltaClass": stock_delta_cls,
                "copy": _stock_copy(d_stock, curr_stock, prior_label, is_all_time),
            },
            "wishlist": {
                "id": "wishlist",
                "title": "Median wishlist",
                "value": str(curr_wishlist),
                "delta": wl_delta_text,
                "deltaClass": wl_delta_cls,
                "copy": _wishlist_copy(d_wishlist, prior_label, is_all_time),
            },
            "price": {
                "id": "price",
                "title": "Median price",
                "value": f"GBP {round(curr_price)}",
                "delta": price_delta_text,
                "deltaClass": price_delta_cls,
                "copy": _price_copy(d_price, prior_label, is_all_time),
            },
        },
        "sparklineSeries": {
            "observed": {"current": observed_series, "prior": obs_prior},
            "stock": {"current": stock_series, "prior": stock_prior},
            "wishlist": {"current": wishlist_series, "prior": wl_prior},
            "price": {"current": price_series, "prior": price_prior},
        },
        "events": events,
    }


def _empty_payload(
    window_id: str, is_all_time: bool, is_all_selected: bool, selected_genera: list[str]
) -> dict:
    """Return a safe empty payload when no data is available for the window."""
    empty_series: list[float] = [0.0] * 12
    return {
        "windowId": window_id,
        "windowLabel": _WINDOW_LABELS.get(window_id, window_id),
        "windowBasisNote": _WINDOW_BASIS_NOTES.get(window_id, ""),
        "showPrior": False,
        "sparklineBasisNote": _SPARKLINE_BASIS_NOTES.get(window_id, ""),
        "isAllSelected": is_all_selected,
        "generaCount": 0 if is_all_selected else len(selected_genera),
        "scopeLabel": _build_scope_label(selected_genera, is_all_selected),
        "kpis": {
            "observed": _empty_kpi("observed", "Observed species"),
            "stock": _empty_kpi("stock", "In-stock rate", "0%"),
            "wishlist": _empty_kpi("wishlist", "Median wishlist"),
            "price": _empty_kpi("price", "Median price", "GBP 0"),
        },
        "sparklineSeries": {
            key: {"current": empty_series, "prior": []}
            for key in ("observed", "stock", "wishlist", "price")
        },
        "events": _compute_events([], window_id, _PRIOR_DELTA_LABELS.get(window_id, "prior period")),
    }


def _empty_kpi(kpi_id: str, title: str, value: str = "0") -> dict:
    return {
        "id": kpi_id,
        "title": title,
        "value": value,
        "delta": "No prior comparison",
        "deltaClass": "flat",
        "copy": "",
    }


def _build_scope_label(selected_genera: list[str], is_all_selected: bool) -> str:
    if is_all_selected:
        return ""
    if len(selected_genera) <= 3:
        return ", ".join(selected_genera[:-1]) + (
            f" and {selected_genera[-1]}" if len(selected_genera) > 1 else selected_genera[0]
            if selected_genera else ""
        )
    return f"your {len(selected_genera)} selected genera"


def build_market_health_payload_all_windows(
    history_rows: list[dict],
    selected_genera: list[str],
    is_all_selected: bool = True,
    reference_dt: Optional[datetime] = None,
) -> dict:
    """Build MarketHealthPayload dicts for all seven windows.

    Returns:
        Dict keyed by window_id → payload dict.
    """
    return {
        window_id: build_market_health_payload(
            history_rows,
            window_id,
            selected_genera,
            is_all_selected,
            reference_dt,
        )
        for window_id in _ALL_WINDOW_IDS
    }

"""Realistic local demo data for website generation.

This module seeds tmp/local-testing/ with a feature-complete static dataset for
local website work. The dataset is intentionally shaped to exercise the visible
UI state surface, not just to provide arbitrary CSV values.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from shared.config import (
    BREEDER_TABLE_FILE,
    CSV_HEADER,
    DEALER_TABLE_FILE,
    HISTORY_FILE,
    SNAPSHOT_FILE,
)
from shared.sparkline_helpers import (
    extract_historical_values_with_carryforward,
    generate_stock_availability_sparkline,
)
from scrape.legend import render_summary_legend


ANALYSIS_SUMMARY_FILE = "analysis_summary.md"
REQUIRED_LOCAL_FILES = (
    SNAPSHOT_FILE,
    HISTORY_FILE,
    BREEDER_TABLE_FILE,
    DEALER_TABLE_FILE,
)

DEMO_DATA_MARKER = "<!-- local-demo-data:v2 -->"
LEGACY_DEMO_MARKERS = (
    "Rich local demo data covering sustained, emerging, cyclical, always, and newly observed states.",
    "Local preview data includes volatile, moderate, and healthy dealer supply patterns.",
    "Example breeder scenario.",
    "Example dealer scenario.",
)

BREEDER_HEADERS = [
    "Species",
    "Size (cm)",
    "OOS",
    "OOS Runs",
    "Stock Pattern",
    "Price",
    "Price History",
    "Wishlist",
    "Wishlist History",
    "Signal",
    "Recommendation",
    "Drivers",
]

DEALER_HEADERS = [
    "Species",
    "Size (cm)",
    "Stock Reliability",
    "Avg OOS Duration",
    "Restock Speed",
    "Price",
    "Price History",
    "Wishlist",
    "Wishlist History",
    "Stock Availability",
    "Dealer Risk",
    "Dealer Recommendation",
    "Drivers",
]

DEMO_RUN_COUNT = 60


def _build_demo_runs() -> list[str]:
    start = datetime(2024, 10, 17, 9, 0, 0)
    return [
        (start + timedelta(weeks=offset)).strftime("%Y-%m-%d %H:%M:%S")
        for offset in range(DEMO_RUN_COUNT)
    ]


DEMO_RUNS = _build_demo_runs()


def _runs(start: int = 0, stop: int | None = None, step: int = 1) -> list[int]:
    return list(range(start, DEMO_RUN_COUNT if stop is None else stop, step))


def _without(runs: list[int], *removed: int) -> list[int]:
    removed_set = set(removed)
    return [run_id for run_id in runs if run_id not in removed_set]


def _series(count: int, baseline: float | int, tail: list[float | int] | None = None) -> list[float | int]:
    tail = tail or []
    if len(tail) > count:
        raise ValueError("Tail values cannot exceed observation count")
    return [baseline] * (count - len(tail)) + tail


def _schedule(*run_ids: int) -> list[int]:
    return list(run_ids)


def _species(
    scientific_name: str,
    common_name: str,
    size_cm: str,
    observed_runs: list[int],
    *,
    signal: str,
    stock_pattern: str,
    oos_runs: str,
    recommendation: str,
    dealer_risk: str,
    stock_reliability: str,
    avg_oos_duration: str,
    restock_speed: str,
    dealer_recommendation: str,
    drivers: str,
    price_values: list[float | int],
    wishlist_values: list[float | int],
) -> dict[str, Any]:
    if len(price_values) != len(observed_runs):
        raise ValueError(f"price_values length must match observed_runs for {scientific_name}")
    if len(wishlist_values) != len(observed_runs):
        raise ValueError(f"wishlist_values length must match observed_runs for {scientific_name}")

    return {
        "scientific_name": scientific_name,
        "common_name": common_name,
        "size_cm": size_cm,
        "observed_runs": observed_runs,
        "signal": signal,
        "stock_pattern": stock_pattern,
        "oos_runs": oos_runs,
        "recommendation": recommendation,
        "dealer_risk": dealer_risk,
        "stock_reliability": stock_reliability,
        "avg_oos_duration": avg_oos_duration,
        "restock_speed": restock_speed,
        "dealer_recommendation": dealer_recommendation,
        "drivers": drivers,
        "price_values": [float(value) for value in price_values],
        "wishlist_values": [int(value) for value in wishlist_values],
    }


DEMO_SPECIES: list[dict[str, Any]] = [
    _species(
        "Aphonopelma seemanni",
        "Costa Rican Zebra",
        "1.5",
        _runs(),
        signal="🔥",
        stock_pattern="Sustained",
        oos_runs="4",
        recommendation="Prioritise breeder holdbacks; sustained scarcity now has durable demand confirmation.",
        dealer_risk="🔥",
        stock_reliability="Low",
        avg_oos_duration="3.8",
        restock_speed="Slow",
        dealer_recommendation="Reorder early and carry buffer stock through the next demand cycle.",
        drivers="Stock: Sustained OOS; Demand: Wishlist high and still rising.",
        price_values=_series(DEMO_RUN_COUNT, 16, [17, 18, 20, 22, 25]),
        wishlist_values=_series(DEMO_RUN_COUNT, 10, [11, 12, 14, 16, 18]),
    ),
    _species(
        "Lasiodora parahybana",
        "Salmon Pink Birdeater",
        "4.0",
        _runs(0, 49, 4),
        signal="🔥",
        stock_pattern="Cyclical",
        oos_runs="9",
        recommendation="Breed to a cadence rather than continuously; recurring supply gaps are consistent.",
        dealer_risk="🔥",
        stock_reliability="Low",
        avg_oos_duration="4.5",
        restock_speed="Slow",
        dealer_recommendation="Treat as a volatile line and avoid running lean inventory.",
        drivers="Stock: Repeated long absences; supply returns are brief when they happen.",
        price_values=_series(len(_runs(0, 49, 4)), 18, [19, 20, 21, 22, 24]),
        wishlist_values=_series(len(_runs(0, 49, 4)), 9, [9, 10, 10, 10, 10]),
    ),
    _species(
        "Chromatopelma cyaneopubescens",
        "Green Bottle Blue",
        "2.0",
        _runs(),
        signal="🔥",
        stock_pattern="Sustained",
        oos_runs="5",
        recommendation="Keep breeding volume stable; demand is deep enough that stock keeps clearing.",
        dealer_risk="⚠️",
        stock_reliability="Medium",
        avg_oos_duration="2.0",
        restock_speed="Medium",
        dealer_recommendation="Monitor sell-through, but restock pressure is still manageable.",
        drivers="Demand: Consistently high wishlist pressure is supporting stable pricing.",
        price_values=_series(DEMO_RUN_COUNT, 32),
        wishlist_values=_series(DEMO_RUN_COUNT, 16),
    ),
    _species(
        "Poecilotheria regalis",
        "Indian Ornamental",
        "3.0",
        _without(_runs(), 14, 15, 33, 34, 52),
        signal="🔥",
        stock_pattern="Sustained",
        oos_runs="5",
        recommendation="Keep pairings on schedule; supply breaks remain meaningful and demand holds.",
        dealer_risk="🔥",
        stock_reliability="Low",
        avg_oos_duration="3.2",
        restock_speed="Slow",
        dealer_recommendation="Protect this line with higher reorder thresholds before gaps widen.",
        drivers="Stock: Repeated missed runs extend lead time; demand stays elevated.",
        price_values=_series(len(_without(_runs(), 14, 15, 33, 34, 52)), 40, [40, 41, 42, 43, 44]),
        wishlist_values=_series(len(_without(_runs(), 14, 15, 33, 34, 52)), 15, [15, 16, 17, 18, 19]),
    ),
    _species(
        "Tliltocatl albopilosus",
        "Curly Hair",
        "2.5",
        _without(_runs(38), 49, 51, 54),
        signal="🔥",
        stock_pattern="Emerging",
        oos_runs="3",
        recommendation="Watch for escalation; the shortage is still forming but demand support is clear.",
        dealer_risk="⚠️",
        stock_reliability="Medium",
        avg_oos_duration="1.8",
        restock_speed="Medium",
        dealer_recommendation="Secure replacements before short gaps stack into a longer shortage.",
        drivers="Stock: Emerging OOS pattern; demand trend is strengthening late in the window.",
        price_values=_series(len(_without(_runs(38), 49, 51, 54)), 18, [18, 19, 20, 21, 22]),
        wishlist_values=_series(len(_without(_runs(38), 49, 51, 54)), 9, [9, 10, 10, 12, 14]),
    ),
    _species(
        "Caribena versicolor",
        "Antilles Pinktoe",
        "2.0",
        _without(_runs(30), 46, 47, 49, 51, 53, 55, 57, 58, 59),
        signal="🔥",
        stock_pattern="Emerging",
        oos_runs="4",
        recommendation="Increase production gradually; demand stays firm even when current stock drops out.",
        dealer_risk="❌",
        stock_reliability="High",
        avg_oos_duration="0.8",
        restock_speed="Fast",
        dealer_recommendation="Supply is generally healthy; routine replenishment is still sufficient.",
        drivers="Supply: Broadly healthy overall, but late-window breaks are worth tracking.",
        price_values=_series(len(_without(_runs(30), 46, 47, 49, 51, 53, 55, 57, 58, 59)), 27, [28, 29, 30, 31, 31]),
        wishlist_values=_series(len(_without(_runs(30), 46, 47, 49, 51, 53, 55, 57, 58, 59)), 13),
    ),
    _species(
        "Monocentropus balfouri",
        "Socotra Island Blue Baboon",
        "2.5",
        _runs(),
        signal="🔥",
        stock_pattern="Sustained",
        oos_runs="4",
        recommendation="Keep consistent output; scarcity stays persistent for this premium line.",
        dealer_risk="🔥",
        stock_reliability="Low",
        avg_oos_duration="3.1",
        restock_speed="Slow",
        dealer_recommendation="Do not let this line sell through completely.",
        drivers="Stock: Sustained shortages and premium demand reinforce the hot signal.",
        price_values=_series(DEMO_RUN_COUNT, 45),
        wishlist_values=_series(DEMO_RUN_COUNT, 17),
    ),
    _species(
        "Hapalopus sp. colombia",
        "Pumpkin Patch",
        "1.0",
        _runs(),
        signal="🔥",
        stock_pattern="Emerging",
        oos_runs="2",
        recommendation="Demand is accelerating; scale breeding before the signal becomes sustained.",
        dealer_risk="⚠️",
        stock_reliability="Medium",
        avg_oos_duration="1.1",
        restock_speed="Fast",
        dealer_recommendation="Watch conversion rate and replenish quickly after each drop.",
        drivers="Demand: Sharp wishlist growth on a small-bodied species is starting to bite.",
        price_values=_series(DEMO_RUN_COUNT, 12, [12, 12, 13, 14, 15]),
        wishlist_values=_series(DEMO_RUN_COUNT, 10, [10, 11, 12, 14, 16]),
    ),
    _species(
        "Xenesthis intermedia",
        "Venezuelan Black Tiger",
        "2.0",
        _runs(18),
        signal="🔥",
        stock_pattern="Sustained",
        oos_runs="4",
        recommendation="High-value line with dependable demand; keep premium breeding slots allocated.",
        dealer_risk="🔥",
        stock_reliability="Low",
        avg_oos_duration="3.6",
        restock_speed="Slow",
        dealer_recommendation="Protect inventory with higher reorder thresholds.",
        drivers="Price: Premium tier still clears; wishlists stay elevated after entry.",
        price_values=_series(len(_runs(18)), 52, [52, 53, 54, 55, 56]),
        wishlist_values=_series(len(_runs(18)), 18),
    ),
    _species(
        "Acanthoscurria geniculata",
        "Brazilian White Knee",
        "3.0",
        _runs(),
        signal="🔥",
        stock_pattern="Sustained",
        oos_runs="3",
        recommendation="Maintain steady breeder output; demand keeps absorbing new supply.",
        dealer_risk="⚠️",
        stock_reliability="Medium",
        avg_oos_duration="1.5",
        restock_speed="Fast",
        dealer_recommendation="Keep a regular replenishment cadence and watch for shallow gaps.",
        drivers="Demand: Strong baseline with short restock windows.",
        price_values=_series(DEMO_RUN_COUNT, 22),
        wishlist_values=_series(DEMO_RUN_COUNT, 11),
    ),
    _species(
        "Bumba cabocla",
        "Brazilian Redhead",
        "1.3",
        _runs(),
        signal="🔥",
        stock_pattern="Sustained",
        oos_runs="3",
        recommendation="Demand is dependable; keep this line in the hot rotation.",
        dealer_risk="❌",
        stock_reliability="High",
        avg_oos_duration="0.6",
        restock_speed="Fast",
        dealer_recommendation="Reliable supply means standard replenishment is enough.",
        drivers="Price: Rising steadily, but supply remains fundamentally healthy.",
        price_values=_series(DEMO_RUN_COUNT, 22, [22, 23, 24, 25, 26]),
        wishlist_values=_series(DEMO_RUN_COUNT, 14),
    ),
    _species(
        "Brachypelma hamorii",
        "Mexican Red Knee",
        "2.0",
        _runs(),
        signal="⚠️",
        stock_pattern="Emerging",
        oos_runs="2",
        recommendation="Watchlist candidate; demand is stable but not urgent enough to escalate.",
        dealer_risk="⚠️",
        stock_reliability="Medium",
        avg_oos_duration="0.9",
        restock_speed="Fast",
        dealer_recommendation="Healthy enough for routine ordering, but keep an eye on emerging gaps.",
        drivers="Supply: Broadly healthy, but emerging soft spots are forming.",
        price_values=_series(DEMO_RUN_COUNT, 30),
        wishlist_values=_series(DEMO_RUN_COUNT, 10),
    ),
    _species(
        "Psalmopoeus irminia",
        "Venezuelan Suntiger",
        "1.2",
        _runs(58),
        signal="⚠️",
        stock_pattern="Newly Observed",
        oos_runs="0",
        recommendation="Monitor closely; too early for a stronger call, but the reappearance matters.",
        dealer_risk="⚠️",
        stock_reliability="Medium",
        avg_oos_duration="1.0",
        restock_speed="Fast",
        dealer_recommendation="Good candidate for monitored test inventory.",
        drivers="Coverage: Newly observed in the current window; demand is improving but history is sparse.",
        price_values=[18, 20],
        wishlist_values=[6, 8],
    ),
    _species(
        "Grammostola pulchra",
        "Brazilian Black",
        "3.5",
        _runs(),
        signal="❌",
        stock_pattern="Always",
        oos_runs="0",
        recommendation="Supply remains healthy; deprioritise breeding allocation for now.",
        dealer_risk="❌",
        stock_reliability="High",
        avg_oos_duration="0.0",
        restock_speed="Fast",
        dealer_recommendation="Reliable line; standard replenishment is sufficient.",
        drivers="Supply: Always listed with falling price and weak wishlist momentum; low urgency is well supported.",
        price_values=_series(DEMO_RUN_COUNT, 38, [38, 37, 36, 35, 34]),
        wishlist_values=_series(DEMO_RUN_COUNT, 5),
    ),
    _species(
        "Davus pentaloris",
        "Guatemalan Tiger Rump",
        "1.2",
        _schedule(5, 59),
        signal="⚠️",
        stock_pattern="Cyclical",
        oos_runs="1",
        recommendation="Keep this on the watchlist; evidence is sparse and the current run could be noise.",
        dealer_risk="⚠️",
        stock_reliability="Medium",
        avg_oos_duration="1.5",
        restock_speed="Medium",
        dealer_recommendation="Treat as a monitored line until history fills in.",
        drivers="Coverage: Sparse but not newly observed; current run needs confirmation.",
        price_values=[16, 16],
        wishlist_values=[9, 7],
    ),
    _species(
        "Theraphosa stirmi",
        "Burgundy Goliath",
        "2.2",
        _runs(55),
        signal="❌",
        stock_pattern="Cyclical",
        oos_runs="0",
        recommendation="Let supply normalise before committing more breeder capacity.",
        dealer_risk="❌",
        stock_reliability="High",
        avg_oos_duration="0.4",
        restock_speed="Fast",
        dealer_recommendation="Healthy supply and falling demand reduce urgency.",
        drivers="",
        price_values=[40, 39, 38, 37, 36],
        wishlist_values=[12, 10, 8, 6, 4],
    ),
]


def ensure_local_csv_files(directory: Path, seed_demo_data: bool = False) -> None:
    """Ensure local website CSV inputs exist.

    When ``seed_demo_data`` is true, missing inputs are created from the local
    demo dataset. Existing seeded demo data is also refreshed so local preview
    picks up the latest intended state coverage.
    """
    missing = [name for name in REQUIRED_LOCAL_FILES if not (directory / name).exists()]

    if seed_demo_data and (missing or _looks_like_seeded_demo_data(directory)):
        write_realistic_demo_data(directory)
        return

    if not missing:
        return

    missing_list = ", ".join(missing)
    raise FileNotFoundError(f"Missing required CSV files: {missing_list}")


def write_realistic_demo_data(directory: Path) -> None:
    """Write a feature-complete local dataset for website preview and development."""
    directory.mkdir(parents=True, exist_ok=True)

    history_rows = _build_history_rows()
    snapshot_rows = [row for row in history_rows if row["scrape_datetime"] == DEMO_RUNS[-1]]
    breeder_rows = _build_breeder_rows(history_rows)
    dealer_rows = _build_dealer_rows(history_rows)

    _write_csv(directory / SNAPSHOT_FILE, CSV_HEADER, snapshot_rows)
    _write_csv(directory / HISTORY_FILE, CSV_HEADER, history_rows)
    _write_csv(directory / BREEDER_TABLE_FILE, BREEDER_HEADERS, breeder_rows)
    _write_csv(directory / DEALER_TABLE_FILE, DEALER_HEADERS, dealer_rows)
    (directory / ANALYSIS_SUMMARY_FILE).write_text(
        _build_analysis_summary(breeder_rows, dealer_rows),
        encoding="utf-8",
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _looks_like_seeded_demo_data(directory: Path) -> bool:
    summary_path = directory / ANALYSIS_SUMMARY_FILE
    if not summary_path.exists():
        return False

    summary_text = summary_path.read_text(encoding="utf-8")
    if DEMO_DATA_MARKER in summary_text:
        return True
    return any(marker in summary_text for marker in LEGACY_DEMO_MARKERS)


def _build_history_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for species in DEMO_SPECIES:
        for observed_position, run_index in enumerate(species["observed_runs"]):
            price = species["price_values"][observed_position]
            wishlist = species["wishlist_values"][observed_position]
            rows.append(
                {
                    "scrape_datetime": DEMO_RUNS[run_index],
                    "scientific_name": species["scientific_name"],
                    "common_name": species["common_name"],
                    "size_cm": species["size_cm"],
                    "price_gbp": f"{price:.2f}",
                    "wishlist_count": str(wishlist),
                    "page_url": _page_url(species["scientific_name"]),
                }
            )

    rows.sort(key=lambda row: (row["scrape_datetime"], row["scientific_name"], row["size_cm"]))
    return rows


def _build_breeder_rows(history_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_run = _group_by_run(history_rows)
    runs = sorted(by_run)
    rows: list[dict[str, str]] = []

    for species in DEMO_SPECIES:
        key = (species["scientific_name"], species["size_cm"])
        latest_price = _latest_value(key, by_run, runs, "price_gbp")
        latest_wishlist = _latest_value(key, by_run, runs, "wishlist_count")
        price_history = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        wishlist_history = extract_historical_values_with_carryforward(key, by_run, runs, "wishlist_count")

        rows.append(
            {
                "Species": species["scientific_name"],
                "Size (cm)": species["size_cm"],
                "OOS": "IN" if runs[-1] in _observed_run_ids(species) else "OUT",
                "OOS Runs": species["oos_runs"],
                "Stock Pattern": species["stock_pattern"],
                "Price": f"£{latest_price} {_price_trend_arrow(price_history['values'])}",
                "Price History": price_history["unicode"],
                "Wishlist": (
                    f"{latest_wishlist} {_wishlist_pressure_icon(int(latest_wishlist))} "
                    f"{_delta_arrow(_recent_delta(wishlist_history['values']))}"
                ),
                "Wishlist History": wishlist_history["unicode"],
                "Signal": species["signal"],
                "Recommendation": species["recommendation"],
                "Drivers": species["drivers"],
            }
        )

    return rows


def _build_dealer_rows(history_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_run = _group_by_run(history_rows)
    runs = sorted(by_run)
    rows: list[dict[str, str]] = []

    for species in DEMO_SPECIES:
        key = (species["scientific_name"], species["size_cm"])
        latest_price = _latest_value(key, by_run, runs, "price_gbp")
        latest_wishlist = _latest_value(key, by_run, runs, "wishlist_count")
        price_history = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        wishlist_history = extract_historical_values_with_carryforward(key, by_run, runs, "wishlist_count")

        rows.append(
            {
                "Species": species["scientific_name"],
                "Size (cm)": species["size_cm"],
                "Stock Reliability": species["stock_reliability"],
                "Avg OOS Duration": species["avg_oos_duration"],
                "Restock Speed": species["restock_speed"],
                "Price": f"£{latest_price} {_price_trend_arrow(price_history['values'])}",
                "Price History": price_history["unicode"],
                "Wishlist": (
                    f"{latest_wishlist} {_wishlist_pressure_icon(int(latest_wishlist))} "
                    f"{_delta_arrow(_recent_delta(wishlist_history['values']))}"
                ),
                "Wishlist History": wishlist_history["unicode"],
                "Stock Availability": generate_stock_availability_sparkline(key, by_run, runs),
                "Dealer Risk": species["dealer_risk"],
                "Dealer Recommendation": species["dealer_recommendation"],
                "Drivers": species["drivers"],
            }
        )

    return rows


def _group_by_run(history_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in history_rows:
        grouped.setdefault(row["scrape_datetime"], []).append(row)
    return grouped


def _latest_value(
    key: tuple[str, str],
    by_run: dict[str, list[dict[str, str]]],
    runs: list[str],
    field_name: str,
) -> str:
    for run_id in reversed(runs):
        row_map = {(row["scientific_name"], row["size_cm"]): row for row in by_run[run_id]}
        if key in row_map:
            return row_map[key][field_name]
    raise KeyError(f"No historical rows found for {key}")


def _observed_run_ids(species: dict[str, Any]) -> set[str]:
    return {DEMO_RUNS[index] for index in species["observed_runs"]}


def _price_trend_arrow(values: list[str | None]) -> str:
    numeric_values = [float(value) for value in values if value not in (None, "")]
    if len(numeric_values) < 2:
        return "→"
    delta = numeric_values[-1] - numeric_values[0]
    if delta >= 2.0:
        return "↑"
    if delta <= -2.0:
        return "↓"
    return "→"


def _wishlist_pressure_icon(value: int) -> str:
    if value >= 15:
        return "🔥"
    if value >= 8:
        return "⚠️"
    return "❌"


def _recent_delta(values: list[str | None]) -> int:
    numeric_values = [int(value) for value in values if value not in (None, "")]
    if len(numeric_values) < 2:
        return 0
    return numeric_values[-1] - numeric_values[-2]


def _delta_arrow(delta: int) -> str:
    if delta >= 2:
        return "↑"
    if delta <= -2:
        return "↓"
    return "→"


def _page_url(scientific_name: str) -> str:
    slug = scientific_name.lower().replace(" ", "-")
    return f"https://www.thespidershop.co.uk/spiderlings/{slug}"


def _build_analysis_summary(
    breeder_rows: list[dict[str, str]],
    dealer_rows: list[dict[str, str]],
) -> str:
    breeder_counts = Counter(row["Signal"] for row in breeder_rows)
    dealer_counts = Counter(row["Dealer Risk"] for row in dealer_rows)
    legend_content = render_summary_legend()

    return (
        f"{DEMO_DATA_MARKER}\n"
        "## 🧬 Breeder Opportunity Matrix (Top 10)\n\n"
        f"**Summary:** {len(breeder_rows)} species analyzed across {DEMO_RUN_COUNT} weekly runs | "
        f"🔥 Hot: {breeder_counts['🔥']} | ⚠️ Watch: {breeder_counts['⚠️']} | ❌ Avoid: {breeder_counts['❌']}\n\n"
        "Local demo data intentionally covers sustained, emerging, cyclical, always, newly observed, stale, and low-coverage states.\n\n"
        "## 🏪 Dealer Supply Risk Matrix (Top 10)\n\n"
        f"**Summary:** {len(dealer_rows)} species analyzed across {DEMO_RUN_COUNT} weekly runs | "
        f"🔥 High Risk: {dealer_counts['🔥']} | ⚠️ Moderate Risk: {dealer_counts['⚠️']} | ❌ Low Risk: {dealer_counts['❌']}\n\n"
        "Local preview data includes tooltip, sparkline, recommendation, and stock-availability states for both analysis pages.\n\n"
        f"{legend_content}"
    )
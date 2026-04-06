#!/usr/bin/env python3
from shared.history_utils import (
    build_species_presence_timeline,
    build_species_stock_pattern,
    compare_prices,
    compute_species_current_oos_runs,
    k2,
)
from shared.config import BREEDER_TABLE_FILE, OOS_CARRYOVER_LOOKBACK, SIGNAL_PRIORITY
from shared.driver_text_helpers import build_drivers_text
from shared.price_text_helpers import format_price_cell
from shared.summary_utils import MatrixOutputConfig, write_matrix_outputs
from scrape.matrix_workflow import (
    LINEAGE_METADATA_COLUMNS,
    build_lineage_clause,
    build_species_wishlist_pressure_map,
    collect_lookback_values_for_key,
    generate_species_price_wishlist_sparklines,
    iter_lookback_rows_for_key,
    lineage_result_to_metadata_dict,
    prepare_matrix_analysis,
    prepare_matrix_runs,
)
from scrape.wishlist_analysis import compute_species_wishlist_delta, get_species_wishlist_count

# =====================
# BREEDER MATRIX (PRICE AWARE) — FIXED TO INCLUDE OUT-OF-STOCK ITEMS
# =====================

BREEDER_WARNING_PATTERN_PRIORITY = {
    "Emerging": 0,
    "Cyclical": 1,
    "Newly Observed": 2,
}

BREEDER_NEWLY_OBSERVED_MAX_RUNS = 2
BREEDER_SUSTAINED_OOS_RUNS = 4
BREEDER_EMERGING_MIN_OOS_RUNS = 2


def _extract_wishlist_count(row: dict[str, str]) -> int:
    """Extract wishlist count from the combined wishlist display cell."""
    wishlist_value = str(row.get("Wishlist", "")).split()
    if not wishlist_value:
        return 0
    try:
        return int(wishlist_value[0])
    except (ValueError, IndexError):
        return 0


def _generate_breeder_drivers_text(
    oos_status: str,
    oos_runs: int,
    pattern: str,
    price_trend: str,
    wishlist_pressure: str,
    wishlist_delta: str,
    observation_coverage_text: str = "",
    lineage_clause: str = "",
) -> str:
    """Generate structured explanation of signal drivers using semicolon separators.

    The optional *lineage_clause* is appended after the standard three-section
    text when a size transition exists.

    Returns:
        Semicolon-separated string explaining the signal drivers.
    """
    stock_details = []
    if oos_runs > 0:
        plural = "s" if oos_runs != 1 else ""
        stock_details.append(f"OOS {oos_runs} run{plural}")
    if oos_status:
        stock_details.append(f"currently {oos_status}")

    if stock_details:
        stock_section = f"Stock: {pattern} ({'; '.join(stock_details)})"
    else:
        stock_section = f"Stock: {pattern}"

    if observation_coverage_text:
        stock_section = f"{stock_section}; Coverage: {observation_coverage_text}"

    drivers = build_drivers_text(stock_section, price_trend, wishlist_pressure, wishlist_delta)

    if lineage_clause:
        drivers = f"{drivers}; {lineage_clause}"
    return drivers


def build_breeder_opportunity_table(history_rows):
    prepared = prepare_matrix_analysis(history_rows)
    if prepared is None:
        return []

    by_run, runs, cur_run, prev_run, cur_rows, run_index, species_lineage_map = prepared

    # Species-level wishlist pressure map (Phase 4)
    species_pressure_map = build_species_wishlist_pressure_map(
        species_lineage_map, by_run, runs, cur_run
    )

    # Index current run rows by k2 for price lookups
    cur_map = {k2(r): r for r in cur_rows}
    prev_rows = by_run[prev_run]
    prev_map = {k2(r): r for r in prev_rows}

    # Helper: price trend for a single (sci, size) key
    def price_trend_for_key(key):
        if key in cur_map and key in prev_map:
            return compare_prices(
                cur_map[key].get("price_gbp", ""),
                prev_map[key].get("price_gbp", ""),
            )
        prices = []
        if key in cur_map:
            v = cur_map[key].get("price_gbp", "")
            if v:
                prices.append(v)
        prices.extend(
            collect_lookback_values_for_key(
                key, by_run, runs, cur_run, run_index,
                lambda row: row.get("price_gbp", ""),
                max_values=2 - len(prices),
            )
        )
        return compare_prices(prices[0], prices[1]) if len(prices) >= 2 else "→"

    # Unique species across all history
    all_sci = sorted({r["scientific_name"] for r in history_rows})

    table = []

    for sci in all_sci:
        lineage_result = species_lineage_map[sci]
        lineage_status = lineage_result.lineage_status
        current_active_size = lineage_result.current_active_size or "—"

        # Species-level presence timeline and supply metrics
        timeline = build_species_presence_timeline(history_rows, sci)
        ordered_runs = sorted(timeline.keys())
        oos_runs = compute_species_current_oos_runs(timeline, ordered_runs)
        pattern = build_species_stock_pattern(timeline, ordered_runs)

        # OOS status
        in_current = timeline.get(cur_run, False)
        if in_current:
            if pattern == "Cyclical":
                oos_status = "IN/OUT"
            else:
                oos_status = "IN"
        else:
            oos_status = "OUT"

        # Newly Observed coverage text for drivers
        observation_coverage_text = ""
        if pattern == "Newly Observed":
            observed_count = sum(1 for v in timeline.values() if v)
            total_runs = len(timeline)
            observation_coverage_text = f"observed {observed_count}/{total_runs} runs"

        # Price — "Multiple active prices" for multi-variant
        if lineage_status == "multi-variant":
            price_cell = "Multiple active prices"
            price_trend = "→"
        else:
            active_key = (sci, current_active_size)
            # Last known price via lookback
            price_row = cur_map.get(active_key) or next(
                iter_lookback_rows_for_key(active_key, by_run, runs, cur_run, run_index),
                None,
            )
            raw_price = price_row.get("price_gbp", "") if price_row else ""
            price_trend = price_trend_for_key(active_key)
            price_cell = format_price_cell(raw_price, price_trend)

        # Sparklines
        price_sparkline, wishlist_sparkline = generate_species_price_wishlist_sparklines(
            sci, lineage_result, by_run, runs, max_runs=8
        )
        if oos_runs > OOS_CARRYOVER_LOOKBACK:
            price_sparkline = wishlist_sparkline = "-"

        # Species-level wishlist
        wishlist_pressure = species_pressure_map.get(sci, "❌")
        wishlist_delta = compute_species_wishlist_delta(sci, lineage_result, by_run, runs, cur_run)
        wishlist_count = get_species_wishlist_count(sci, lineage_result, by_run, runs, cur_run)
        wishlist_display = f"{wishlist_count} {wishlist_pressure} {wishlist_delta}"

        # Signal logic — Always is unconditionally ❌ (Decision 5: hard rule)
        if pattern == "Newly Observed":
            signal = "⚠️"
            rec = (
                "Monitor closely — newly observed, limited history "
                f"({observation_coverage_text})"
            )
        elif pattern == "Sustained" and price_trend in ("↑", "→") and wishlist_pressure == "🔥":
            signal = "🔥"
            rec = "Pair soon — sustained scarcity with strong buyer interest"
        elif pattern == "Sustained" and price_trend in ("↑", "→"):
            signal = "🔥"
            rec = "Pair soon — sustained scarcity"
        elif pattern == "Emerging" and price_trend == "↑":
            signal = "🔥"
            rec = "Consider pairing — rising demand"
        elif pattern == "Emerging" and wishlist_pressure == "🔥" and wishlist_delta == "↑":
            signal = "🔥"
            rec = "Consider pairing — emerging scarcity with surging interest"
        elif pattern == "Emerging" and wishlist_pressure == "🔥":
            if lineage_status == "ambiguous-transition":
                signal = "⚠️"
                rec = "Monitor closely — emerging scarcity; lineage continuity unconfirmed"
            else:
                signal = "⚠️"
                rec = "Monitor closely — emerging scarcity and rising interest"
        elif pattern == "Emerging":
            signal = "⚠️"
            rec = "Monitor closely — supply tightening"
        elif pattern == "Cyclical":
            signal = "⚠️"
            rec = "Breed cautiously — wave restocking"
        else:
            # Always — ❌ regardless of demand (Decision 5 hard rule)
            signal = "❌"
            rec = "Avoid for profit — oversupplied"

        # Build transition clause for Drivers
        lineage_clause = build_lineage_clause(lineage_result)

        drivers = _generate_breeder_drivers_text(
            oos_status=oos_status,
            oos_runs=oos_runs,
            pattern=pattern,
            price_trend=price_trend,
            wishlist_pressure=wishlist_pressure,
            wishlist_delta=wishlist_delta,
            observation_coverage_text=observation_coverage_text,
            lineage_clause=lineage_clause,
        )

        table.append({
            "Species": sci,
            "Size (cm)": current_active_size,
            "OOS": oos_status,
            "OOS Runs": str(oos_runs),
            "Stock Pattern": pattern,
            "Price": price_cell,
            "Price History": price_sparkline,
            "Wishlist": wishlist_display,
            "Wishlist History": wishlist_sparkline,
            "Signal": signal,
            "Recommendation": rec,
            "Drivers": drivers,
            **lineage_result_to_metadata_dict(lineage_result),
        })

    # Sort: Signal priority, breeder watch-bucket precedence, then Wishlist count and OOS runs.
    table.sort(
        key=lambda row: (
            SIGNAL_PRIORITY.get(str(row.get("Signal", "")), 99),
            BREEDER_WARNING_PATTERN_PRIORITY.get(str(row.get("Stock Pattern", "")), -1)
            if row.get("Signal") == "⚠️"
            else -1,
            -_extract_wishlist_count(row),
            -float(row["OOS Runs"]),
        )
    )
    return table

def write_breeder_outputs(table):
    output_config = MatrixOutputConfig(
        title="🧬 Breeder Opportunity Matrix",
        csv_filepath=BREEDER_TABLE_FILE,
        empty_message="No breeding opportunities detected (conservative analysis requires sufficient historical data).",
        indicator_field="Signal",
        indicator_labels={"🔥": "Hot", "⚠️": "Watch", "❌": "Avoid"},
        fallback_fieldnames=[
            "Species", "Size (cm)", "OOS", "OOS Runs", "Stock Pattern",
            "Price", "Price History", "Wishlist",
            "Wishlist History", "Signal", "Recommendation", "Drivers",
            *LINEAGE_METADATA_COLUMNS,
        ],
        table_columns=[
            "Species", "Size (cm)", "OOS", "OOS Runs", "Stock Pattern",
            "Price", "Price History", "Wishlist",
            "Wishlist History", "Signal", "Recommendation",
        ],
    )
    return write_matrix_outputs(table, output_config)

#!/usr/bin/env python3
from shared.history_utils import (
    build_species_presence_timeline,
    compare_prices,
    compute_species_avg_oos_duration,
    compute_species_restock_speed,
    compute_species_stock_reliability,
    k2,
)
from shared.config import DEALER_TABLE_FILE
from shared.sparkline_helpers import generate_species_stock_availability_sparkline
from shared.driver_text_helpers import build_drivers_text
from shared.price_text_helpers import format_price_cell
from shared.summary_utils import MatrixOutputConfig, write_matrix_outputs
from scrape.matrix_workflow import (
    LINEAGE_METADATA_COLUMNS,
    build_species_wishlist_pressure_map,
    collect_lookback_values_for_key,
    generate_species_price_wishlist_sparklines,
    lineage_result_to_metadata_dict,
    prepare_matrix_analysis,
    sort_matrix_table,
)
from scrape.wishlist_analysis import compute_species_wishlist_delta, get_species_wishlist_count

# =====================
# DEALER MATRIX (Option B: Price Pressure informational)
# =====================

DEALER_HIGH_RELIABILITY_THRESHOLD = 0.8
DEALER_MEDIUM_RELIABILITY_THRESHOLD = 0.4
DEALER_SLOW_RESTOCK_MIN_AVG_OOS = 3
DEALER_MODERATE_RESTOCK_AVG_OOS = 2


def _generate_dealer_drivers_text(
    reliability: str,
    speed: str,
    price_pressure: str,
    wishlist_pressure: str,
    wishlist_delta: str,
    lineage_clause: str = "",
) -> str:
    """Generate structured explanation of risk drivers using semicolon separators."""
    stock_section = f"Stock: Reliability {reliability} (Restock {speed})"
    drivers = build_drivers_text(stock_section, price_pressure, wishlist_pressure, wishlist_delta)
    if lineage_clause:
        drivers = f"{drivers}; {lineage_clause}"
    return drivers


def build_dealer_supply_risk_table(history_rows):
    prepared = prepare_matrix_analysis(history_rows)
    if prepared is None:
        return []

    by_run, runs, cur_run, prev_run, cur_rows, run_index, _old_pressure_map, species_lineage_map = prepared

    # Species-level wishlist pressure map (Phase 4)
    species_pressure_map = build_species_wishlist_pressure_map(
        species_lineage_map, by_run, runs, cur_run
    )

    # Price lookup helpers
    cur_map = {k2(r): r for r in cur_rows}
    prev_map = {k2(r): r for r in by_run[prev_run]}

    def last_seen_price_for_key(key):
        values = collect_lookback_values_for_key(
            key, by_run, runs, cur_run, run_index,
            lambda row: row.get("price_gbp", ""),
            max_values=1,
        )
        return values[0] if values else ""

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
        reliability = compute_species_stock_reliability(timeline)
        avg_oos = compute_species_avg_oos_duration(timeline, ordered_runs)
        speed = compute_species_restock_speed(avg_oos)

        # Price — "Multiple active prices" for multi-variant
        if lineage_status == "multi-variant":
            price_cell = "Multiple active prices"
            pp = "→"
        else:
            active_key = (sci, current_active_size)
            cur_price = cur_map.get(active_key, {}).get("price_gbp", "")
            prev_price = prev_map.get(active_key, {}).get("price_gbp", "")
            if not cur_price:
                cur_price = last_seen_price_for_key(active_key)
            if not prev_price:
                prev_prices_vals = collect_lookback_values_for_key(
                    active_key, by_run, runs, cur_run, run_index,
                    lambda row: row.get("price_gbp", ""), max_values=2,
                )
                prev_price = prev_prices_vals[1] if len(prev_prices_vals) >= 2 else (
                    prev_prices_vals[0] if prev_prices_vals else ""
                )
            pp = compare_prices(cur_price, prev_price)
            price_cell = format_price_cell(cur_price, pp)

        # Sparklines
        price_sparkline, wishlist_sparkline = generate_species_price_wishlist_sparklines(
            sci, lineage_result, by_run, runs, max_runs=8
        )

        # Stock availability sparkline (species-level)
        stock_availability_sparkline = generate_species_stock_availability_sparkline(
            sci, by_run, runs, max_runs=8
        )

        # Species-level wishlist
        wishlist_pressure = species_pressure_map.get(sci, "❌")
        wishlist_delta = compute_species_wishlist_delta(sci, lineage_result, by_run, runs, cur_run)
        wishlist_count = get_species_wishlist_count(sci, lineage_result, by_run, runs, cur_run)
        wishlist_display = f"{wishlist_count} {wishlist_pressure} {wishlist_delta}"

        # Dealer risk classification (supply-first)
        if reliability == "Low" and speed == "Slow" and wishlist_pressure == "🔥":
            risk = "🔥"
            rec = "Actively seek breeders — high demand, poor supply"
        elif reliability == "Low" and speed == "Slow":
            risk = "🔥"
            rec = "Actively seek breeders"
        elif reliability == "Low" and wishlist_pressure == "🔥":
            risk = "🔥"
            rec = "Actively seek breeders — high demand, unreliable supply"
        elif reliability == "Low" and wishlist_delta == "↑":
            risk = "🔥"
            rec = "Actively seek breeders — unreliable supply, surging interest"
        elif reliability == "Low":
            risk = "⚠️"
            rec = "Buy opportunistically — unreliable supply"
        elif reliability == "Medium" and wishlist_pressure == "🔥" and wishlist_delta == "↑":
            risk = "🔥"
            rec = "Actively seek breeders — surging demand, variable supply"
        elif reliability == "Medium" and wishlist_pressure == "🔥":
            risk = "⚠️"
            if lineage_status == "ambiguous-transition":
                rec = "Buy opportunistically — lineage continuity unconfirmed"
            else:
                rec = "Buy opportunistically — moderate demand, variable supply"
        elif reliability == "Medium":
            risk = "⚠️"
            rec = "Buy opportunistically"
        elif reliability == "High" and wishlist_pressure in ("❌", "⚠️"):
            risk = "❌"
            rec = "No urgency / oversupplied"
        elif reliability == "High" and wishlist_delta == "↓":
            risk = "❌"
            rec = "No urgency / oversupplied — interest declining"
        elif reliability == "High" and wishlist_pressure == "🔥":
            risk = "❌"
            if lineage_status == "multi-variant":
                rec = "Well-supplied, but monitor demand across active size variants"
            else:
                rec = "Well-supplied, but monitor demand"
        else:
            risk = "❌"
            rec = "No urgency / oversupplied"

        # Build transition clause for Drivers
        lineage_clause = ""
        if lineage_status == "confirmed-transition":
            lineage_clause = (
                f"Size transition: confirmed "
                f"{lineage_result.previous_size}→{current_active_size} "
                f"on {lineage_result.transition_date}"
            )
        elif lineage_status == "ambiguous-transition":
            lineage_clause = (
                f"Size transition: ambiguous "
                f"{lineage_result.previous_size}→{current_active_size} "
                f"on {lineage_result.transition_date}"
            )

        drivers = _generate_dealer_drivers_text(
            reliability=reliability,
            speed=speed,
            price_pressure=pp,
            wishlist_pressure=wishlist_pressure,
            wishlist_delta=wishlist_delta,
            lineage_clause=lineage_clause,
        )

        table.append({
            "Species": sci,
            "Size (cm)": current_active_size,
            "Stock Reliability": reliability,
            "Avg OOS Duration": avg_oos,
            "Restock Speed": speed,
            "Price": price_cell,
            "Price History": price_sparkline,
            "Wishlist": wishlist_display,
            "Wishlist History": wishlist_sparkline,
            "Stock Availability": stock_availability_sparkline,
            "Dealer Risk": risk,
            "Dealer Recommendation": rec,
            "Drivers": drivers,
            **lineage_result_to_metadata_dict(lineage_result),
        })

    # Sort: Dealer Risk (🔥 > ⚠️ > ❌), then Wishlist count (desc), then Avg OOS Duration (desc)
    sort_matrix_table(table, "Dealer Risk", lambda row: float(row["Avg OOS Duration"]))
    return table

def write_dealer_outputs(table):
    output_config = MatrixOutputConfig(
        title="🏪 Dealer Supply Risk Matrix",
        csv_filepath=DEALER_TABLE_FILE,
        empty_message="No supply risks detected (conservative analysis requires sufficient historical data).",
        indicator_field="Dealer Risk",
        indicator_labels={"🔥": "High Risk", "⚠️": "Moderate Risk", "❌": "Low Risk"},
        fallback_fieldnames=[
            "Species", "Size (cm)", "Stock Reliability", "Avg OOS Duration",
            "Restock Speed", "Price", "Price History", "Wishlist",
            "Wishlist History", "Stock Availability", "Dealer Risk",
            "Dealer Recommendation", "Drivers",
            *LINEAGE_METADATA_COLUMNS,
        ],
        table_columns=[
            "Species", "Size (cm)", "Stock Reliability", "Avg OOS Duration",
            "Restock Speed", "Price", "Price History", "Wishlist",
            "Wishlist History", "Stock Availability", "Dealer Risk",
            "Dealer Recommendation",
        ],
    )
    return write_matrix_outputs(table, output_config)

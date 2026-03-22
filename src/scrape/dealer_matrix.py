#!/usr/bin/env python3
from shared.history_utils import create_observation_coverage, k2, compare_prices
from shared.config import DEALER_TABLE_FILE
from shared.sparkline_helpers import generate_stock_availability_sparkline
from shared.driver_text_helpers import build_drivers_text
from shared.price_text_helpers import format_price_cell
from shared.summary_utils import MatrixOutputConfig, write_matrix_outputs
from scrape.matrix_workflow import (
    collect_lookback_values_for_key,
    generate_price_wishlist_sparklines,
    get_wishlist_display_metrics,
    prepare_matrix_analysis,
    prepare_matrix_runs,
    sort_matrix_table,
)

# =====================
# DEALER MATRIX (Option B: Price Pressure informational)
# =====================

DEALER_HIGH_RELIABILITY_THRESHOLD = 0.8
DEALER_MEDIUM_RELIABILITY_THRESHOLD = 0.4
DEALER_SLOW_RESTOCK_MIN_AVG_OOS = 3
DEALER_MODERATE_RESTOCK_AVG_OOS = 2

def _format_observation_coverage(observation_coverage: dict[str, int]) -> str:
    """Return compact observation coverage text for sparse-history dealer rows."""
    return (
        f"observed {observation_coverage['observed_run_count']}"
        f"/{observation_coverage['total_run_count']} runs"
    )


def _generate_dealer_drivers_text(
    reliability: str,
    speed: str,
    price_pressure: str,
    wishlist_pressure: str,
    wishlist_delta: str,
    observation_coverage_text: str = "",
) -> str:
    """Generate structured explanation of risk drivers using semicolon separators.
    
    Args:
        reliability: Stock reliability level (High/Medium/Low)
        speed: Restock speed (Fast/Moderate/Slow)
        price_pressure: Price direction (↑/→/↓)
        wishlist_pressure: Demand level (🔥/⚠️/❌)
        wishlist_delta: Momentum (↑/→/↓)
        observation_coverage_text: Optional sparse-history coverage text
        
    Returns:
        Semicolon-separated string explaining the risk drivers
        
    Example:
        "Stock: Reliability Low (Restock Slow); Demand: Wishlist 🔥 + rising; Price: Rising"
    """
    stock_section = f"Stock: Reliability {reliability} (Restock {speed})"
    if observation_coverage_text:
        stock_section = f"{stock_section}; Coverage: {observation_coverage_text}"
    return build_drivers_text(stock_section, price_pressure, wishlist_pressure, wishlist_delta)


def build_dealer_supply_risk_table(history_rows):
    prepared = prepare_matrix_analysis(history_rows)
    if prepared is None:
        return []

    by_run, runs, cur_run, prev_run, cur_rows, run_index, wishlist_pressure_map = prepared
    total_runs = len(runs)

    prev_prices = {k2(r): r.get("price_gbp", "") for r in by_run[prev_run] if r.get("price_gbp")}
    cur_prices = {k2(r): r.get("price_gbp", "") for r in by_run[cur_run] if r.get("price_gbp")}

    present_runs_map = {}
    for rt in runs:
        for r in by_run[rt]:
            present_runs_map.setdefault(k2(r), set()).add(rt)

    table = []

    def last_seen_price_for_key(key):
        values = collect_lookback_values_for_key(
            key,
            by_run,
            runs,
            cur_run,
            run_index,
            lambda row: row.get("price_gbp", ""),
            max_values=1,
        )
        return values[0] if values else ""

    for (sci, size), present_runs in present_runs_map.items():
        observation_coverage = create_observation_coverage(history_rows, (sci, size))
        limited_history = (
            observation_coverage["observed_run_count"] <= 2
            and observation_coverage["ambiguous_pre_first_seen_run_count"] > 0
        )
        observation_coverage_text = ""
        present_pct = len(present_runs) / total_runs
        reliability = (
            "High"
            if present_pct >= DEALER_HIGH_RELIABILITY_THRESHOLD
            else "Medium"
            if present_pct >= DEALER_MEDIUM_RELIABILITY_THRESHOLD
            else "Low"
        )

        # Safe OOS event counting even if the series starts with "absent"
        oos_events = []
        last_present = None
        for rt in runs:
            present = rt in present_runs
            if not present:
                if last_present is True:
                    oos_events.append(1)
                elif last_present is False:
                    oos_events[-1] += 1
                else:  # last_present is None (first run)
                    oos_events.append(1)
            last_present = present

        avg_oos = round(sum(oos_events) / len(oos_events), 1) if oos_events else 0
        speed = (
            "Slow"
            if avg_oos >= DEALER_SLOW_RESTOCK_MIN_AVG_OOS
            else "Moderate"
            if avg_oos == DEALER_MODERATE_RESTOCK_AVG_OOS
            else "Fast"
        )

        pp = compare_prices(
            cur_prices.get((sci, size), ""),
            prev_prices.get((sci, size), "")
        )
        current_or_last_price = cur_prices.get((sci, size), "") or last_seen_price_for_key((sci, size))
        price_cell = format_price_cell(current_or_last_price, pp)

        key = (sci, size)
        wishlist_pressure, wishlist_delta, wishlist_count, wishlist_display = get_wishlist_display_metrics(
            key, by_run, runs, cur_run, wishlist_pressure_map
        )

        # Dealer risk logic: Supply-first hierarchy with demand as modifier
        # Low reliability species escalate to 🔥 based on supply failure + demand signals
        # Medium reliability varies between ⚠️ and 🔥 based on demand context
        # High reliability defaults to ❌ (well-supplied) unless exceptional demand
        
        # Low reliability + slow restock (high risk regardless of demand)
        if reliability == "Low" and speed == "Slow" and wishlist_pressure == "🔥":
            risk = "🔥"
            rec = "Actively seek breeders — high demand, poor supply"
        elif reliability == "Low" and speed == "Slow":
            risk = "🔥"
            rec = "Actively seek breeders"
        # Low reliability + high wishlist (even with faster restock)
        elif reliability == "Low" and wishlist_pressure == "🔥":
            risk = "🔥"
            rec = "Actively seek breeders — high demand, unreliable supply"
        # Low reliability + rising delta (early-stage demand growth)
        elif reliability == "Low" and wishlist_delta == "↑":
            risk = "🔥"
            rec = "Actively seek breeders — unreliable supply, surging interest"
        # Medium reliability + high wishlist + rising delta
        elif reliability == "Medium" and wishlist_pressure == "🔥" and wishlist_delta == "↑":
            risk = "🔥"
            rec = "Actively seek breeders — surging demand, variable supply"
        # Medium reliability + high wishlist (without rising delta)
        elif reliability == "Medium" and wishlist_pressure == "🔥":
            risk = "⚠️"
            rec = "Buy opportunistically — moderate demand, variable supply"
        # Medium reliability with lower demand signals
        elif reliability == "Medium":
            risk = "⚠️"
            rec = "Buy opportunistically"
        # High reliability with low/moderate interest
        elif reliability == "High" and wishlist_pressure in ("❌", "⚠️"):
            risk = "❌"
            rec = "No urgency / oversupplied"
        # High reliability + falling delta
        elif reliability == "High" and wishlist_delta == "↓":
            risk = "❌"
            rec = "No urgency / oversupplied — interest declining"
        # High reliability + very high interest
        elif reliability == "High" and wishlist_pressure == "🔥":
            risk = "❌"
            rec = "Well-supplied, but monitor demand"
        # Fallback for any remaining cases
        else:
            risk = "❌"
            rec = "No urgency / oversupplied"

        if limited_history:
            observation_coverage_text = _format_observation_coverage(observation_coverage)
            rec = f"{rec} — limited history ({observation_coverage_text})"

        # Generate sparklines for historical trends (last 8 weeks)
        # Use carry-forward to show persistent values when OUT (price/wishlist don't disappear)
        price_history_sparkline, wishlist_history_sparkline = generate_price_wishlist_sparklines(
            (sci, size), by_run, runs, max_runs=8
        )
        
        stock_availability_sparkline = generate_stock_availability_sparkline((sci, size), by_run, runs, max_runs=8)
        
        # Generate structured explanation of risk drivers
        drivers = _generate_dealer_drivers_text(
            reliability=reliability,
            speed=speed,
            price_pressure=pp,
            wishlist_pressure=wishlist_pressure,
            wishlist_delta=wishlist_delta,
            observation_coverage_text=observation_coverage_text,
        )

        table.append({
            "Species": sci,
            "Size (cm)": size,
            "Stock Reliability": reliability,
            "Avg OOS Duration": avg_oos,
            "Restock Speed": speed,
            "Price": price_cell,
            "Price History": price_history_sparkline,
            "Wishlist": wishlist_display,
            "Wishlist History": wishlist_history_sparkline,
            "Stock Availability": stock_availability_sparkline,
            "Dealer Risk": risk,
            "Dealer Recommendation": rec,
            "Drivers": drivers
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
        ],
        table_columns=[
            "Species", "Size (cm)", "Stock Reliability", "Avg OOS Duration",
            "Restock Speed", "Price", "Price History", "Wishlist",
            "Wishlist History", "Stock Availability", "Dealer Risk",
            "Dealer Recommendation",
        ],
    )
    return write_matrix_outputs(table, output_config)

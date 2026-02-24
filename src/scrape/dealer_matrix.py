#!/usr/bin/env python3
from shared.history_utils import group_by_run, k2
from shared.config import DEALER_TABLE_FILE, SIGNAL_PRIORITY, TREND_PRIORITY
from scrape.wishlist_analysis import compute_wishlist_pressure, get_wishlist_metrics
from shared.sparkline_helpers import extract_historical_values_with_carryforward, generate_stock_availability_sparkline
from shared.driver_text_helpers import build_drivers_text
from shared.csv_utils import write_matrix_csv
from shared.summary_utils import MatrixSummaryConfig, write_matrix_summary

# =====================
# DEALER MATRIX (Option B: Price Pressure informational)
# =====================

def _generate_dealer_drivers_text(reliability: str, speed: str, price_pressure: str, wishlist_pressure: str, wishlist_delta: str) -> str:
    """Generate structured explanation of risk drivers using semicolon separators.
    
    Args:
        reliability: Stock reliability level (High/Medium/Low)
        speed: Restock speed (Fast/Moderate/Slow)
        price_pressure: Price direction (↑/→/↓)
        wishlist_pressure: Demand level (🔥/⚠️/❌)
        wishlist_delta: Momentum (↑/→/↓)
        
    Returns:
        Semicolon-separated string explaining the risk drivers
        
    Example:
        "Stock: Reliability Low (Restock Slow); Demand: Wishlist High + rising; Price: Rising"
    """
    stock_section = f"Stock: Reliability {reliability} (Restock {speed})"
    return build_drivers_text(stock_section, price_pressure, wishlist_pressure, wishlist_delta)


def build_dealer_supply_risk_table(history_rows):
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    total_runs = len(runs)
    if total_runs < 2:
        return []

    prev_run = runs[-2]
    cur_run = runs[-1]
    
    cur_rows = by_run[cur_run]

    # Compute wishlist pressure for current run
    wishlist_pressure_map = compute_wishlist_pressure(cur_rows)

    prev_prices = {k2(r): r.get("price_gbp", "") for r in by_run[prev_run] if r.get("price_gbp")}
    cur_prices = {k2(r): r.get("price_gbp", "") for r in by_run[cur_run] if r.get("price_gbp")}

    present_runs_map = {}
    for rt in runs:
        for r in by_run[rt]:
            present_runs_map.setdefault(k2(r), set()).add(rt)

    table = []

    for (sci, size), present_runs in present_runs_map.items():
        present_pct = len(present_runs) / total_runs
        reliability = "High" if present_pct >= 0.8 else "Medium" if present_pct >= 0.4 else "Low"

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
        speed = "Slow" if avg_oos >= 3 else "Moderate" if avg_oos == 2 else "Fast"

        pp = "→"
        if (sci, size) in prev_prices and (sci, size) in cur_prices:
            try:
                p_prev = float(prev_prices[(sci, size)])
                p_cur = float(cur_prices[(sci, size)])
                if p_cur > p_prev:
                    pp = "↑"
                elif p_cur < p_prev:
                    pp = "↓"
            except ValueError:
                pp = "→"

        key = (sci, size)
        wishlist_pressure, wishlist_delta = get_wishlist_metrics(
            key, by_run, runs, cur_run, wishlist_pressure_map
        )

        # Dealer risk logic: Supply-first hierarchy with demand as modifier
        # Low reliability species escalate to 🔥 based on supply failure + demand signals
        # Medium reliability varies between ⚠️ and 🔥 based on demand context
        # High reliability defaults to ❌ (well-supplied) unless exceptional demand
        if reliability == "Low" and speed == "Slow":
            # Low reliability + slow restock = high risk regardless of demand
            if wishlist_pressure == "🔥":
                risk = "🔥"
                rec = "Actively seek breeders — high demand, poor supply"
            else:
                risk = "🔥"
                rec = "Actively seek breeders"
        elif reliability == "Low" and wishlist_pressure == "🔥":
            # Low reliability + high wishlist even with faster restock
            risk = "🔥"
            rec = "Actively seek breeders — high demand, unreliable supply"
        elif reliability == "Low" and wishlist_delta == "↑":
            # Low reliability + rising delta (early-stage demand growth on unreliable species)
            # Rarely reached: most Low reliability cases are caught by previous branches
            # Kept for edge case where interest is accelerating but not yet at high pressure
            risk = "🔥"
            rec = "Actively seek breeders — unreliable supply, surging interest"
        elif reliability == "Medium" and wishlist_pressure == "🔥" and wishlist_delta == "↑":
            # Medium reliability + high wishlist + rising delta -> escalate to 🔥
            risk = "🔥"
            rec = "Actively seek breeders — surging demand, variable supply"
        elif reliability == "Medium" and wishlist_pressure == "🔥":
            # Medium reliability + high wishlist (without rising delta)
            risk = "⚠️"
            rec = "Buy opportunistically — moderate demand, variable supply"
        elif reliability == "Medium":
            # Medium reliability with lower demand signals
            risk = "⚠️"
            rec = "Buy opportunistically"
        elif reliability == "High" and wishlist_pressure in ("❌", "⚠️"):
            # High reliability with low/moderate interest
            risk = "❌"
            rec = "No urgency / oversupplied"
        elif reliability == "High" and wishlist_delta == "↓":
            # High reliability + falling delta (interest declining even if currently high)
            risk = "❌"
            rec = "No urgency / oversupplied — interest declining"
        elif reliability == "High" and wishlist_pressure == "🔥":
            # High reliability but very high interest - slight watch
            risk = "❌"
            rec = "Well-supplied, but monitor demand"
        else:
            # Fallback for any remaining cases
            risk = "❌"
            rec = "No urgency / oversupplied"

        # Generate sparklines for historical trends (last 8 weeks)
        # Use carry-forward to show persistent values when OUT (price/wishlist don't disappear)
        price_history = extract_historical_values_with_carryforward((sci, size), by_run, runs, "price_gbp", max_runs=8)
        price_history_sparkline = price_history['unicode']
        
        wishlist_history = extract_historical_values_with_carryforward((sci, size), by_run, runs, "wishlist_count", max_runs=8)
        wishlist_history_sparkline = wishlist_history['unicode']
        
        stock_availability_sparkline = generate_stock_availability_sparkline((sci, size), by_run, runs, max_runs=8)
        
        # Generate structured explanation of risk drivers
        drivers = _generate_dealer_drivers_text(
            reliability=reliability,
            speed=speed,
            price_pressure=pp,
            wishlist_pressure=wishlist_pressure,
            wishlist_delta=wishlist_delta
        )

        table.append({
            "Species": sci,
            "Size (cm)": size,
            "Stock Reliability": reliability,
            "Avg OOS Duration": avg_oos,
            "Restock Speed": speed,
            "Price Pressure": pp,
            "Price History": price_history_sparkline,
            "Wishlist Pressure": wishlist_pressure,
            "Wishlist Delta": wishlist_delta,
            "Wishlist History": wishlist_history_sparkline,
            "Stock Availability": stock_availability_sparkline,
            "Dealer Risk": risk,
            "Dealer Recommendation": rec,
            "Drivers": drivers
        })

    # Sort: Dealer Risk (🔥 > ⚠️ > ❌), then Wishlist Pressure (🔥 > ⚠️ > ❌), 
    # then Wishlist Delta (↑ > → > ↓), then Avg OOS Duration (desc)
    table.sort(key=lambda r: (
        SIGNAL_PRIORITY[r["Dealer Risk"]],
        SIGNAL_PRIORITY[r["Wishlist Pressure"]],
        TREND_PRIORITY[r["Wishlist Delta"]],
        -r["Avg OOS Duration"]
    ))
    return table

def write_dealer_outputs(table):
    fallback_fieldnames = [
        "Species", "Size (cm)", "Stock Reliability", "Avg OOS Duration",
        "Restock Speed", "Price Pressure", "Price History", "Wishlist Pressure",
        "Wishlist Delta", "Wishlist History", "Stock Availability", "Dealer Risk",
        "Dealer Recommendation", "Drivers",
    ]
    write_matrix_csv(DEALER_TABLE_FILE, table, fallback_fieldnames)

    config = MatrixSummaryConfig(
        title="🏪 Dealer Supply Risk Matrix",
        csv_filepath=DEALER_TABLE_FILE,
        empty_message="No supply risks detected (conservative analysis requires sufficient historical data).",
        indicator_field="Dealer Risk",
        indicator_labels={"🔥": "High Risk", "⚠️": "Moderate Risk", "❌": "Low Risk"},
        table_columns=[
            "Species", "Size (cm)", "Stock Reliability", "Avg OOS Duration",
            "Restock Speed", "Price Pressure", "Price History", "Wishlist Pressure",
            "Wishlist Delta", "Wishlist History", "Stock Availability", "Dealer Risk",
            "Dealer Recommendation",
        ],
    )
    return write_matrix_summary(table, config)

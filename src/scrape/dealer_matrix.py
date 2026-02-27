#!/usr/bin/env python3
from shared.history_utils import group_by_run, k2, compare_prices
from shared.config import DEALER_TABLE_FILE, SIGNAL_PRIORITY, TREND_PRIORITY
from scrape.wishlist_analysis import compute_wishlist_pressure, get_wishlist_metrics, get_wishlist_count
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

    # Last known price per key across all runs (for OUT species display)
    last_known_price_map: dict = {}
    for rt in runs:
        for r in by_run[rt]:
            val = r.get("price_gbp", "")
            if val:
                last_known_price_map[k2(r)] = val

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

        pp = compare_prices(
            cur_prices.get((sci, size), ""),
            prev_prices.get((sci, size), "")
        )

        key = (sci, size)
        wishlist_pressure, wishlist_delta = get_wishlist_metrics(
            key, by_run, runs, cur_run, wishlist_pressure_map
        )

        wishlist_count = get_wishlist_count(key, by_run, runs, cur_run)

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

        last_known_price = last_known_price_map.get((sci, size), "")
        combined_price = f"£{last_known_price} {pp}" if last_known_price else pp

        table.append({
            "Species": sci,
            "Size (cm)": size,
            "Stock Reliability": reliability,
            "Avg OOS Duration": avg_oos,
            "Restock Speed": speed,
            "Price": combined_price,
            "Price History": price_history_sparkline,
            "Wishlist": f"{wishlist_count} {wishlist_pressure} {wishlist_delta}",
            "Wishlist History": wishlist_history_sparkline,
            "Stock Availability": stock_availability_sparkline,
            "Dealer Risk": risk,
            "Dealer Recommendation": rec,
            "Drivers": drivers
        })

    # Sort: Dealer Risk (🔥 > ⚠️ > ❌), then Wishlist count (desc), then Price (desc), then Avg OOS Duration (desc)
    def _price_sort_key(price_str: str) -> float:
        parts = price_str.split()
        if parts and parts[0].startswith("£"):
            try:
                return float(parts[0].lstrip("£"))
            except ValueError:
                return 0.0
        return 0.0

    table.sort(key=lambda r: (
        SIGNAL_PRIORITY[r["Dealer Risk"]],
        -int(r["Wishlist"].split()[0]) if r.get("Wishlist", "").split() else 0,
        -_price_sort_key(r.get("Price", "")),
        -r["Avg OOS Duration"]
    ))
    return table

def write_dealer_outputs(table):
    fallback_fieldnames = [
        "Species", "Size (cm)", "Stock Reliability", "Avg OOS Duration",
        "Restock Speed", "Price", "Price History", "Wishlist",
        "Wishlist History", "Stock Availability", "Dealer Risk",
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
            "Restock Speed", "Price", "Price History", "Wishlist",
            "Wishlist History", "Stock Availability", "Dealer Risk",
            "Dealer Recommendation",
        ],
    )
    return write_matrix_summary(table, config)

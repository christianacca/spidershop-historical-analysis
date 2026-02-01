#!/usr/bin/env python3
import csv
from history import group_by_run, k2
from config import DEALER_TABLE_FILE
from assertions import get_summary_path
from wishlist_analysis import compute_wishlist_pressure, get_oos_wishlist_carryover, compute_wishlist_delta
from sparkline_helpers import extract_historical_values_with_carryforward, generate_stock_availability_sparkline

# =====================
# DEALER MATRIX (Option B: Price Pressure informational)
# =====================

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

    # Precompute current run keys for OOS check
    cur_keys = {k2(r) for r in cur_rows}

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

        # Get wishlist pressure with OOS carryover
        # If species is OUT now, carry forward last known pressure (bounded lookback)
        # Use lookback_limit=5 to capture historical demand within reasonable window (same as breeder matrix)
        key = (sci, size)
        if key in cur_keys:
            # Species is IN current run
            wishlist_pressure = wishlist_pressure_map.get(key, "❌")
        else:
            # Species is OUT - try to carry forward recent pressure
            carried = get_oos_wishlist_carryover(key, by_run, runs, cur_run)
            wishlist_pressure = carried if carried else "❌"

        # Compute wishlist delta (momentum signal)
        wishlist_delta = compute_wishlist_delta(key, by_run, runs, cur_run)

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
        })

    # Sort: Dealer Risk (🔥 > ⚠️ > ❌), then Wishlist Pressure (🔥 > ⚠️ > ❌), 
    # then Wishlist Delta (↑ > → > ↓), then Avg OOS Duration (desc)
    table.sort(key=lambda r: (
        {"🔥": 0, "⚠️": 1, "❌": 2}[r["Dealer Risk"]],
        {"🔥": 0, "⚠️": 1, "❌": 2}[r["Wishlist Pressure"]],
        {"↑": 0, "→": 1, "↓": 2}[r["Wishlist Delta"]],
        -r["Avg OOS Duration"]
    ))
    return table

def write_dealer_outputs(table):
    # Always create the CSV file, even if empty
    if table:
        with open(DEALER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=table[0].keys())
            w.writeheader()
            w.writerows(table)
    else:
        # Create empty CSV with header row
        fieldnames = ["Species", "Size (cm)", "Stock Reliability", "Avg OOS Duration", 
                      "Restock Speed", "Price Pressure", "Price History", "Wishlist Pressure", 
                      "Wishlist Delta", "Wishlist History", "Stock Availability", "Dealer Risk", 
                      "Dealer Recommendation"]
        with open(DEALER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()

    # Write summary to GitHub Actions step summary if available
    summary_path = get_summary_path()
    if not summary_path:
        return False

    total = len(table) if table else 0
    shown = min(10, total)

    # Calculate risk statistics
    risk_counts = {"🔥": 0, "⚠️": 0, "❌": 0}
    if table:
        for row in table:
            risk = row.get("Dealer Risk", "")
            if risk in risk_counts:
                risk_counts[risk] += 1

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n## 🏪 Dealer Supply Risk Matrix (Top 10)\n\n")
        if total == 0:
            f.write("_No supply risks detected (conservative analysis requires sufficient historical data)._\n")
        else:
            # Write summary statistics
            f.write(f"**Summary:** {total} species analyzed | 🔥 High Risk: {risk_counts['🔥']} | ⚠️ Moderate Risk: {risk_counts['⚠️']} | ❌ Low Risk: {risk_counts['❌']}\n\n")
            
            f.write("| Species | Size (cm) | Stock Reliability | Avg OOS Duration | Restock Speed | Price Pressure | Price History | Wishlist Pressure | Wishlist Delta | Wishlist History | Stock Availability | Dealer Risk | Dealer Recommendation |\n")
            f.write("|---|---:|---|---:|---|---|---|---|---|---|---|---|---|\n")
            for r in table[:shown]:
                f.write(
                    f"| {r['Species']} | {r['Size (cm)']} | {r['Stock Reliability']} | {r['Avg OOS Duration']} | "
                    f"{r['Restock Speed']} | {r['Price Pressure']} | {r['Price History']} | {r['Wishlist Pressure']} | "
                    f"{r['Wishlist Delta']} | {r['Wishlist History']} | {r['Stock Availability']} | {r['Dealer Risk']} | {r['Dealer Recommendation']} |\n"
                )
            if total > shown:
                f.write(f"\n_Showing top {shown} of {total} entries — see `{DEALER_TABLE_FILE}` for full list._\n")
    return True

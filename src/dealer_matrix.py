#!/usr/bin/env python3
import csv
from history import group_by_run, k2
from config import DEALER_TABLE_FILE
from assertions import get_summary_path
from parsing import compute_wishlist_pressure, get_oos_wishlist_carryover, compute_wishlist_delta

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

        # safe OOS event counting even if the series starts with "absent"
        oos_events = []
        last_present = None
        for rt in runs:
            present = rt in present_runs
            if not present:
                if last_present is True:
                    oos_events.append(1)
                elif last_present is False:
                    if oos_events:
                        oos_events[-1] += 1
                    else:
                        oos_events.append(1)
                else:  # last_present is None
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
        key = (sci, size)
        if key in cur_keys:
            # Species is IN current run
            wishlist_pressure = wishlist_pressure_map.get(key, "❌")
        else:
            # Species is OUT - try to carry forward recent pressure
            carried = get_oos_wishlist_carryover(key, by_run, runs, cur_run, lookback_limit=3)
            wishlist_pressure = carried if carried else "❌"

        # Compute wishlist delta (momentum signal)
        wishlist_delta = compute_wishlist_delta(key, by_run, runs, cur_run, lookback_limit=3)

        # Dealer risk logic (enhanced with wishlist pressure and delta)
        # Wishlist escalates urgency where supply is unreliable, de-escalates where interest is weak
        # Wishlist Delta acts as momentum modifier
        if reliability == "Low" and speed == "Slow":
            # Low reliability + slow restock is already high risk
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
            # NEW: Low reliability + rising delta -> reinforce 🔥
            risk = "🔥"
            rec = "Actively seek breeders — unreliable supply, surging interest"
        elif reliability == "Medium" and wishlist_pressure == "🔥" and wishlist_delta == "↑":
            # NEW: Medium reliability + high wishlist + rising delta -> escalate to 🔥
            risk = "🔥"
            rec = "Actively seek breeders — surging demand, variable supply"
        elif reliability == "Medium" and wishlist_pressure == "🔥":
            # Medium reliability + high wishlist
            risk = "⚠️"
            rec = "Buy opportunistically — moderate demand, variable supply"
        elif reliability == "Medium":
            risk = "⚠️"
            rec = "Buy opportunistically"
        elif reliability == "High" and wishlist_pressure in ("❌", "⚠️"):
            # High reliability with low/moderate interest
            risk = "❌"
            rec = "No urgency / oversupplied"
        elif reliability == "High" and wishlist_delta == "↓":
            # NEW: High reliability + falling delta -> reinforce ❌
            risk = "❌"
            rec = "No urgency / oversupplied — interest declining"
        elif reliability == "High" and wishlist_pressure == "🔥":
            # High reliability but very high interest - slight watch
            risk = "❌"
            rec = "Well-supplied, but monitor demand"
        else:
            risk = "❌"
            rec = "No urgency / oversupplied"

        table.append({
            "Species": sci,
            "Size (cm)": size,
            "Stock Reliability": reliability,
            "Avg OOS Duration": avg_oos,
            "Restock Speed": speed,
            "Price Pressure": pp,
            "Wishlist Pressure": wishlist_pressure,
            "Wishlist Δ": wishlist_delta,
            "Dealer Risk": risk,
            "Dealer Recommendation": rec,
        })

    # Sort: Dealer Risk (🔥 > ⚠️ > ❌), then Wishlist Pressure (🔥 > ⚠️ > ❌), 
    # then Wishlist Δ (↑ > → > ↓), then Avg OOS Duration (desc)
    table.sort(key=lambda r: (
        {"🔥": 0, "⚠️": 1, "❌": 2}[r["Dealer Risk"]],
        {"🔥": 0, "⚠️": 1, "❌": 2}[r["Wishlist Pressure"]],
        {"↑": 0, "→": 1, "↓": 2}[r["Wishlist Δ"]],
        -r["Avg OOS Duration"]
    ))
    return table

def write_dealer_outputs(table):
    if not table:
        return False

    with open(DEALER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=table[0].keys())
        w.writeheader()
        w.writerows(table)

    summary_path = get_summary_path()
    if not summary_path:
        return False

    total = len(table)
    shown = min(10, total)

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n## 🏪 Dealer Supply Risk Matrix\n\n")
        f.write("| Species | Size (cm) | Stock Reliability | Avg OOS Duration | Restock Speed | Price Pressure | Wishlist Pressure | Wishlist Δ | Dealer Risk | Dealer Recommendation |\n")
        f.write("|---|---:|---|---:|---|---|---|---|---|---|\n")
        for r in table[:shown]:
            f.write(
                f"| {r['Species']} | {r['Size (cm)']} | {r['Stock Reliability']} | {r['Avg OOS Duration']} | "
                f"{r['Restock Speed']} | {r['Price Pressure']} | {r['Wishlist Pressure']} | {r['Wishlist Δ']} | {r['Dealer Risk']} | {r['Dealer Recommendation']} |\n"
            )
        if total > shown:
            f.write(f"\n_Showing top {shown} of {total} entries — see `{DEALER_TABLE_FILE}` for full list._\n")

    return True

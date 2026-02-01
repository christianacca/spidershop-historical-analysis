#!/usr/bin/env python3
import csv
from shared.history_utils import group_by_run, k2
from shared.config import BREEDER_TABLE_FILE, SIGNAL_PRIORITY, TREND_PRIORITY
from shared.assertions import get_summary_path
from scrape.wishlist_analysis import compute_wishlist_pressure, get_oos_wishlist_carryover, compute_wishlist_delta
from shared.sparkline_helpers import extract_historical_values_with_carryforward

# =====================
# BREEDER MATRIX (PRICE AWARE) — FIXED TO INCLUDE OUT-OF-STOCK ITEMS
# =====================

def build_breeder_opportunity_table(history_rows):
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    if len(runs) < 2:
        return []

    cur_run = runs[-1]
    prev_run = runs[-2]

    cur_rows = by_run[cur_run]
    prev_rows = by_run[prev_run]

    # Index rows by (species,size) for quick lookup
    cur_map = {k2(r): r for r in cur_rows}
    prev_map = {k2(r): r for r in prev_rows}

    # Compute wishlist pressure for current run only
    wishlist_pressure_map = compute_wishlist_pressure(cur_rows)

    # Union of keys across ALL history so OUT items can appear in the breeder table
    all_keys = set()
    for rt in runs:
        for r in by_run[rt]:
            all_keys.add(k2(r))

    # For display of OUT items: last-seen row
    last_seen = {}
    for rt in runs:
        for r in by_run[rt]:
            last_seen[k2(r)] = r  # later runs overwrite earlier

    # Helper: last 2 price points for a key before/at current
    def price_trend_for_key(key):
        # If present now and present previous -> compare those
        if key in cur_map and key in prev_map:
            c = cur_map[key].get("price_gbp", "")
            p = prev_map[key].get("price_gbp", "")
            try:
                if c and p:
                    cf = float(c); pf = float(p)
                    if cf > pf:
                        return "↑"
                    if cf < pf:
                        return "↓"
            except ValueError:
                pass
            return "→"

        # If OUT now: compare last seen price vs price in run before last seen (if available)
        # Walk backward through runs to find last two occurrences with prices
        prices = []
        for rt in reversed(runs):
            m = {k2(r): r for r in by_run[rt]}
            if key in m:
                val = m[key].get("price_gbp", "")
                if val:
                    prices.append(val)
                if len(prices) >= 2:
                    break

        if len(prices) >= 2:
            try:
                latest = float(prices[0])
                prior = float(prices[1])
                if latest > prior:
                    return "↑"
                if latest < prior:
                    return "↓"
            except ValueError:
                return "→"
        return "→"

    table = []

    # Precompute membership sets per run for faster OOS counting
    keys_by_run = {rt: {k2(r) for r in by_run[rt]} for rt in runs}

    for key in sorted(all_keys):
        in_current = key in keys_by_run[cur_run]
        in_prev = key in keys_by_run[prev_run]

        # Use current row if present, otherwise last-seen row for display
        row = cur_map.get(key) or last_seen.get(key) or {"scientific_name": key[0], "size_cm": key[1]}

        # OOS status + consecutive OOS runs (INCLUDING the current run if OUT)
        if in_current:
            oos_status = "IN"
            oos_runs = 0

            # If it was missing last run but exists now (or flapped recently), show IN/OUT
            if not in_prev and len(runs) >= 3:
                # If seen before, it truly flapped
                seen_before = any(key in keys_by_run[rt] for rt in runs[:-1])
                if seen_before:
                    oos_status = "IN/OUT"
        else:
            oos_status = "OUT"
            # Count consecutive missing runs ending at current, including current as 1
            oos_runs = 1
            for rt in reversed(runs[:-1]):  # start from prev run backward
                if key in keys_by_run[rt]:
                    break
                oos_runs += 1

        # Pattern derived from OOS evidence
        if oos_runs >= 4:
            pattern = "Sustained"
        elif oos_runs >= 2:
            pattern = "Emerging"
        elif oos_status == "IN/OUT":
            pattern = "Cyclical"
        else:
            pattern = "Always"

        price_trend = price_trend_for_key(key)

        # Get wishlist pressure with OOS carryover
        # If species is OUT now, carry forward last known pressure (bounded lookback)
        # Use lookback_limit=5 to capture wishlist pressure for sustained OOS species (4+ runs)
        # This allows differentiation between "sustained scarcity" and "sustained scarcity + high demand"
        if in_current:
            wishlist_pressure = wishlist_pressure_map.get(key, "❌")
        else:
            # Species is OUT - try to carry forward recent pressure
            carried = get_oos_wishlist_carryover(key, by_run, runs, cur_run)
            wishlist_pressure = carried if carried else "❌"

        # Compute wishlist delta (momentum signal)
        # Keep lookback_limit=3 for delta per philosophy: "OUT carryover ≤ 3 runs" for momentum
        wishlist_delta = compute_wishlist_delta(key, by_run, runs, cur_run)

        # Recommendation logic (conservative wishlist integration with delta)
        # Base signal driven by Pattern + Price Trend (unchanged)
        # Wishlist can upgrade confidence or escalate emerging signals
        # Wishlist Delta acts as momentum modifier
        
        if pattern == "Sustained" and price_trend in ("↑", "→"):
            # Sustained scarcity is already strong - never downgrade
            # Wishlist Delta does NOT affect sustained signals (already high confidence)
            # With lookback_limit=5, we can now differentiate sustained scarcity signals:
            # - High historical demand (🔥 pressure) -> enhanced recommendation
            # - Normal or low demand -> standard sustained recommendation
            if wishlist_pressure == "🔥":
                signal = "🔥"
                rec = "Pair soon — sustained scarcity with strong buyer interest"
            else:
                signal = "🔥"
                rec = "Pair soon — sustained scarcity"
        elif pattern == "Emerging" and price_trend == "↑":
            signal = "🔥"
            rec = "Consider pairing — rising demand"
        elif pattern == "Emerging":
            # Emerging + high wishlist can escalate to warning
            # NEW: Emerging + high wishlist + rising delta -> escalate to 🔥
            # NEW: Emerging + falling delta -> do NOT escalate (remain ⚠️)
            if wishlist_pressure == "🔥" and wishlist_delta == "↑":
                signal = "🔥"
                rec = "Consider pairing — emerging scarcity with surging interest"
            elif wishlist_pressure == "🔥":
                signal = "⚠️"
                rec = "Monitor closely — emerging scarcity and rising interest"
            else:
                signal = "⚠️"
                rec = "Monitor closely — supply tightening"
        elif pattern == "Cyclical":
            signal = "⚠️"
            rec = "Breed cautiously — wave restocking"
        elif pattern == "Always" and wishlist_pressure == "🔥":
            # Always + high wishlist = early watch (NOT breeding signal yet)
            # NEW: Always + high wishlist + falling delta -> remain ❌
            if wishlist_delta == "↓":
                signal = "❌"
                rec = "Avoid for profit — interest declining"
            else:
                signal = "⚠️"
                rec = "Watch closely — high latent demand"
        else:
            signal = "❌"
            rec = "Avoid for profit — oversupplied"

        # Generate sparklines for price and wishlist trends
        # Use carry-forward to show persistent values when OUT (price/wishlist don't disappear)
        price_history = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp", max_runs=8)
        wishlist_history = extract_historical_values_with_carryforward(key, by_run, runs, "wishlist_count", max_runs=8)
        
        price_sparkline = price_history['unicode']
        wishlist_sparkline = wishlist_history['unicode']

        table.append({
            "Species": row.get("scientific_name", key[0]),
            "Size (cm)": row.get("size_cm", key[1]),
            "OOS": oos_status,
            "OOS Runs": str(oos_runs),
            "Stock Pattern": pattern,
            "Price Trend": price_trend,
            "Price History": price_sparkline,
            "Wishlist Pressure": wishlist_pressure,
            "Wishlist Delta": wishlist_delta,
            "Wishlist History": wishlist_sparkline,
            "Signal": signal,
            "Recommendation": rec,
        })

    # Sort: Signal priority (🔥 > ⚠️ > ❌), then Wishlist Pressure (🔥 > ⚠️ > ❌), 
    # then Wishlist Delta (↑ > → > ↓), then OOS Runs (desc)
    table.sort(key=lambda r: (
        SIGNAL_PRIORITY[r["Signal"]],
        SIGNAL_PRIORITY[r["Wishlist Pressure"]],
        TREND_PRIORITY[r["Wishlist Delta"]],
        -int(r["OOS Runs"])
    ))
    return table

def write_breeder_outputs(table):
    # Always create the CSV file, even if empty
    if table:
        with open(BREEDER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=table[0].keys())
            w.writeheader()
            w.writerows(table)
    else:
        # Create empty CSV with header row
        fieldnames = ["Species", "Size (cm)", "OOS", "OOS Runs", "Stock Pattern", 
                      "Price Trend", "Price History", "Wishlist Pressure", "Wishlist Delta", 
                      "Wishlist History", "Signal", "Recommendation"]
        with open(BREEDER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()

    # Write summary to GitHub Actions step summary if available
    summary_path = get_summary_path()
    if not summary_path:
        return False

    total = len(table) if table else 0
    shown = min(10, total)

    # Calculate signal statistics
    signal_counts = {"🔥": 0, "⚠️": 0, "❌": 0}
    if table:
        for row in table:
            signal = row.get("Signal", "")
            if signal in signal_counts:
                signal_counts[signal] += 1

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n## 🧬 Breeder Opportunity Matrix (Top 10)\n\n")
        if total == 0:
            f.write("_No breeding opportunities detected (conservative analysis requires sufficient historical data)._\n")
        else:
            # Write summary statistics
            f.write(f"**Summary:** {total} species analyzed | 🔥 Hot: {signal_counts['🔥']} | ⚠️ Watch: {signal_counts['⚠️']} | ❌ Avoid: {signal_counts['❌']}\n\n")
            
            f.write("| Species | Size (cm) | OOS | OOS Runs | Stock Pattern | Price Trend | Price History | Wishlist Pressure | Wishlist Delta | Wishlist History | Signal | Recommendation |\n")
            f.write("|---|---:|---|---:|---|---|---|---|---|---|---|---|\n")
            for r in table[:shown]:
                f.write(
                    f"| {r['Species']} | {r['Size (cm)']} | {r['OOS']} | {r['OOS Runs']} | "
                    f"{r['Stock Pattern']} | {r['Price Trend']} | {r['Price History']} | "
                    f"{r['Wishlist Pressure']} | {r['Wishlist Delta']} | {r['Wishlist History']} | "
                    f"{r['Signal']} | {r['Recommendation']} |\n"
                )
            if total > shown:
                f.write(f"\n_Showing top {shown} of {total} entries — see `{BREEDER_TABLE_FILE}` for full list._\n")

    return True

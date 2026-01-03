#!/usr/bin/env python3
import csv
from history import group_by_run, k2
from config import BREEDER_TABLE_FILE
from assertions import get_summary_paths

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

        # Recommendation logic (price-aware, unchanged)
        if pattern == "Sustained" and price_trend in ("↑", "→"):
            signal = "🔥"
            rec = "Pair soon — sustained scarcity"
        elif pattern == "Emerging" and price_trend == "↑":
            signal = "🔥"
            rec = "Consider pairing — rising demand"
        elif pattern == "Emerging":
            signal = "⚠️"
            rec = "Monitor closely — supply tightening"
        elif pattern == "Cyclical":
            signal = "⚠️"
            rec = "Breed cautiously — wave restocking"
        else:
            signal = "❌"
            rec = "Avoid for profit — oversupplied"

        table.append({
            "Species": row.get("scientific_name", key[0]),
            "Size (cm)": row.get("size_cm", key[1]),
            "OOS": oos_status,
            "OOS Runs": str(oos_runs),
            "Pattern": pattern,
            "Price Trend": price_trend,
            "Signal": signal,
            "Recommendation": rec,
        })

    # Sort: best signals first, then highest OOS streak
    table.sort(key=lambda r: ({"🔥": 0, "⚠️": 1, "❌": 2}[r["Signal"]], -int(r["OOS Runs"])))
    return table

def write_breeder_outputs(table):
    if not table:
        return False

    with open(BREEDER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=table[0].keys())
        w.writeheader()
        w.writerows(table)

    summary_paths = get_summary_paths()
    if not summary_paths:
        return False

    total = len(table)
    shown = min(10, total)

    for summary_path in summary_paths:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("\n## 🧬 Breeder Opportunity Matrix\n\n")
            f.write("| Species | Size (cm) | OOS | OOS Runs | Pattern | Price Trend | Signal | Recommendation |\n")
            f.write("|---|---:|---|---:|---|---|---|---|\n")
            for r in table[:shown]:
                f.write(
                    f"| {r['Species']} | {r['Size (cm)']} | {r['OOS']} | {r['OOS Runs']} | "
                    f"{r['Pattern']} | {r['Price Trend']} | {r['Signal']} | {r['Recommendation']} |\n"
                )
            if total > shown:
                f.write(f"\n_Showing top {shown} of {total} entries — see `{BREEDER_TABLE_FILE}` for full list._\n")

    return True

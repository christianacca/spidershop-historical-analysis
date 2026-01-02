# [SCRIPT START]
# NOTE: This is a direct continuation of your last corrected version.
# Only changes vs previous are:
# - Breeder Opportunity Matrix regains Price Trend column
# - Breeder recommendations again incorporate price movement

# --- snip ---
# (All imports, config, scraping, history, pricing summary remain unchanged)
# --- snip ---

# =====================
# BREEDER MATRIX (Phase 1 – PRICE AWARE, RESTORED)
# =====================

def build_breeder_opportunity_table(history_rows):
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    if len(runs) < 2:
        return []

    current = by_run[runs[-1]]
    prev = by_run[runs[-2]]

    prev_map = {k2(r): r for r in prev if r.get("price_gbp")}
    cur_map = {k2(r): r for r in current}

    table = []

    for r in current:
        k = k2(r)
        oos_runs = 0
        oos_status = "IN"

        if k not in prev_map:
            oos_status = "OUT"
            for rt in reversed(runs[:-1]):
                if any(k2(x) == k for x in by_run[rt]):
                    break
                oos_runs += 1
        elif any(k not in {k2(x) for x in by_run[rt]} for rt in runs[-3:-1]):
            oos_status = "IN/OUT"

        # Pattern
        if oos_runs >= 3:
            pattern = "Sustained"
        elif oos_runs == 2:
            pattern = "Emerging"
        elif oos_status == "IN/OUT":
            pattern = "Cyclical"
        else:
            pattern = "Always"

        # Price trend (RESTORED)
        price_trend = "→"
        if k in prev_map and r.get("price_gbp"):
            try:
                cur_p = float(r["price_gbp"])
                prev_p = float(prev_map[k]["price_gbp"])
                if cur_p > prev_p:
                    price_trend = "↑"
                elif cur_p < prev_p:
                    price_trend = "↓"
            except ValueError:
                pass

        # Recommendation logic (price-aware again)
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
            "Species": r["scientific_name"],
            "Size (cm)": r["size_cm"],
            "OOS": oos_status,
            "OOS Runs": str(oos_runs),
            "Pattern": pattern,
            "Price Trend": price_trend,
            "Signal": signal,
            "Recommendation": rec,
        })

    table.sort(key=lambda r: ({"🔥":0,"⚠️":1,"❌":2}[r["Signal"]], -int(r["OOS Runs"])))
    return table

#!/usr/bin/env python3
from shared.history_utils import group_by_run, k3
from shared.assertions import get_summary_path
from shared.parsing import format_datetime_smart

# =====================
# JOB SUMMARY — PRICING
# =====================

def calculate_pricing_summary(history_rows):
    """Calculate pricing statistics from history rows.
    
    Returns a dict with:
    - increases: count of price increases
    - decreases: count of price decreases
    - unchanged: count of unchanged prices
    - new: count of new listings
    - removed: count of removed listings
    - top_movers: list of tuples (species, size, old_price, new_price, pct_change)
    
    Returns None if insufficient data (no rows or fewer than 2 runs).
    """
    if not history_rows:
        return None

    by_run = group_by_run(history_rows)
    run_times = sorted(by_run.keys())
    if len(run_times) < 2:
        return None

    current = by_run[run_times[-1]]
    previous = by_run[run_times[-2]]

    cur_map = {k3(r): r for r in current}
    prev_map = {k3(r): r for r in previous}

    inc = dec = same = new = gone = 0
    movers = []

    for k, r in cur_map.items():
        if k not in prev_map:
            new += 1
            continue
        old_p = prev_map[k].get("price_gbp", "")
        new_p = r.get("price_gbp", "")
        if not old_p or not new_p:
            continue
        try:
            oldf = float(old_p)
            newf = float(new_p)
        except ValueError:
            continue

        if newf > oldf:
            inc += 1
        elif newf < oldf:
            dec += 1
        else:
            same += 1

        if oldf != 0:
            pct = (newf - oldf) / oldf
            movers.append((r["scientific_name"], r["size_cm"], oldf, newf, pct))

    for k in prev_map:
        if k not in cur_map:
            gone += 1

    movers.sort(key=lambda x: abs(x[4]), reverse=True)
    top5 = movers[:5]

    return {
        "increases": inc,
        "decreases": dec,
        "unchanged": same,
        "new": new,
        "removed": gone,
        "top_movers": top5
    }


def write_pricing_summary(history_rows, scrape_datetime: str):
    summary_path = get_summary_path()
    if not summary_path:
        return

    stats = calculate_pricing_summary(history_rows)
    if not stats:
        return

    # Format scrape datetime (date-only unless collision)
    formatted_datetime = format_datetime_smart([scrape_datetime])[0]
    
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("## 🕷️ Spiderlings Pricing Summary\n\n")
        f.write(f"**Scrape time (UTC):** `{formatted_datetime}`\n\n")
        f.write("### 🔄 Changes Since Last Run\n")
        f.write(f"- 🔼 Increases: **{stats['increases']}**\n")
        f.write(f"- 🔽 Decreases: **{stats['decreases']}**\n")
        f.write(f"- ➖ Unchanged: **{stats['unchanged']}**\n")
        f.write(f"- 🆕 New: **{stats['new']}**\n")
        f.write(f"- ❌ Removed: **{stats['removed']}**\n")

        f.write("\n### 🚀 Top 5 Price Movers\n")
        if not stats['top_movers']:
            f.write("_No comparable price changes detected._\n")
        else:
            f.write("| Species | Size | Old | New | Change |\n")
            f.write("|---|---|---:|---:|---:|\n")
            for s, size, o, n, p in stats['top_movers']:
                sign = "+" if p > 0 else ""
                f.write(f"| {s} | {size} | £{o:.2f} | £{n:.2f} | {sign}{p*100:.1f}% |\n")

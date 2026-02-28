#!/usr/bin/env python3
from shared.history_utils import group_by_run, k2, compare_prices
from shared.config import (
    BREEDER_TABLE_FILE,
    SIGNAL_PRIORITY,
    TREND_PRIORITY,
    OOS_CARRYOVER_LOOKBACK,
)
from scrape.wishlist_analysis import compute_wishlist_pressure, get_wishlist_metrics, get_wishlist_count
from shared.sparkline_helpers import extract_historical_values_with_carryforward
from shared.driver_text_helpers import build_drivers_text
from shared.price_text_helpers import format_price_cell
from shared.csv_utils import write_matrix_csv
from shared.summary_utils import MatrixSummaryConfig, write_matrix_summary

# =====================
# BREEDER MATRIX (PRICE AWARE) — FIXED TO INCLUDE OUT-OF-STOCK ITEMS
# =====================

def _generate_breeder_drivers_text(oos_status: str, oos_runs: int, pattern: str, price_trend: str, wishlist_pressure: str, wishlist_delta: str) -> str:
    """Generate structured explanation of signal drivers using semicolon separators.
    
    Args:
        oos_status: Current stock status (IN/OUT/IN/OUT)
        oos_runs: Number of consecutive OOS runs
        pattern: Stock pattern (Sustained/Emerging/Cyclical/Always)
        price_trend: Price direction (↑/→/↓)
        wishlist_pressure: Demand level (🔥/⚠️/❌)
        wishlist_delta: Momentum (↑/→/↓)
        
    Returns:
        Semicolon-separated string explaining the signal drivers
        
    Example:
        "Stock: Emerging (OOS 2 runs; currently OUT); Demand: Wishlist 🔥 + rising; Price: Stable"
    """
    # Stock section
    parts = []
    if oos_runs > 0:
        plural = "s" if oos_runs != 1 else ""
        parts.append(f"OOS {oos_runs} run{plural}")
    if oos_status:
        parts.append(f"currently {oos_status}")
    
    if parts:
        stock_detail = "; ".join(parts)
        stock_section = f"Stock: {pattern} ({stock_detail})"
    else:
        stock_section = f"Stock: {pattern}"
    
    return build_drivers_text(stock_section, price_trend, wishlist_pressure, wishlist_delta)


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

    # For display of OUT items: bounded last-seen row
    run_index = {rt: idx for idx, rt in enumerate(runs)}

    def get_last_seen_row_within_lookback(key):
        cur_idx = run_index[cur_run]
        lookback_start = max(0, cur_idx - OOS_CARRYOVER_LOOKBACK)
        for i in range(cur_idx - 1, lookback_start - 1, -1):
            rt = runs[i]
            for candidate in by_run[rt]:
                if k2(candidate) == key:
                    return candidate
        return None

    # Helper: last 2 price points for a key before/at current
    def price_trend_for_key(key):
        # If present now and present previous -> compare those
        if key in cur_map and key in prev_map:
            return compare_prices(
                cur_map[key].get("price_gbp", ""),
                prev_map[key].get("price_gbp", "")
            )

        # Compare the last two known prices within bounded lookback.
        # If IN now but missing previous run (flapping), include current price.
        prices = []
        if key in cur_map:
            current_value = cur_map[key].get("price_gbp", "")
            if current_value:
                prices.append(current_value)

        cur_idx = run_index[cur_run]
        lookback_start = max(0, cur_idx - OOS_CARRYOVER_LOOKBACK)
        for i in range(cur_idx - 1, lookback_start - 1, -1):
            rt = runs[i]
            m = {k2(r): r for r in by_run[rt]}
            if key in m:
                val = m[key].get("price_gbp", "")
                if val:
                    prices.append(val)
                if len(prices) >= 2:
                    break

        if len(prices) >= 2:
            return compare_prices(prices[0], prices[1])
        return "→"

    table = []

    # Precompute membership sets per run for faster OOS counting
    keys_by_run = {rt: {k2(r) for r in by_run[rt]} for rt in runs}

    for key in sorted(all_keys):
        in_current = key in keys_by_run[cur_run]
        in_prev = key in keys_by_run[prev_run]

        # Use current row if present, otherwise bounded last-seen row for display
        row = cur_map.get(key) or get_last_seen_row_within_lookback(key) or {
            "scientific_name": key[0],
            "size_cm": key[1],
        }

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
        price_cell = format_price_cell(row.get("price_gbp", ""), price_trend)

        wishlist_pressure, wishlist_delta = get_wishlist_metrics(
            key, by_run, runs, cur_run, wishlist_pressure_map
        )

        wishlist_count = get_wishlist_count(key, by_run, runs, cur_run)

        # Recommendation logic (conservative wishlist integration with delta)
        # Base signal driven by Pattern + Price Trend (unchanged)
        # Wishlist can upgrade confidence or escalate emerging signals
        # Wishlist Delta acts as momentum modifier
        
        # Sustained scarcity with strong buyer interest
        if pattern == "Sustained" and price_trend in ("↑", "→") and wishlist_pressure == "🔥":
            signal = "🔥"
            rec = "Pair soon — sustained scarcity with strong buyer interest"
        # Sustained scarcity (standard case)
        elif pattern == "Sustained" and price_trend in ("↑", "→"):
            signal = "🔥"
            rec = "Pair soon — sustained scarcity"
        # Emerging with rising price
        elif pattern == "Emerging" and price_trend == "↑":
            signal = "🔥"
            rec = "Consider pairing — rising demand"
        # Emerging + high wishlist + rising delta -> escalate to 🔥
        elif pattern == "Emerging" and wishlist_pressure == "🔥" and wishlist_delta == "↑":
            signal = "🔥"
            rec = "Consider pairing — emerging scarcity with surging interest"
        # Emerging + high wishlist (without rising delta)
        elif pattern == "Emerging" and wishlist_pressure == "🔥":
            signal = "⚠️"
            rec = "Monitor closely — emerging scarcity and rising interest"
        # Emerging (base case)
        elif pattern == "Emerging":
            signal = "⚠️"
            rec = "Monitor closely — supply tightening"
        # Cyclical restocking pattern
        elif pattern == "Cyclical":
            signal = "⚠️"
            rec = "Breed cautiously — wave restocking"
        # Always available + high wishlist + falling delta
        elif pattern == "Always" and wishlist_pressure == "🔥" and wishlist_delta == "↓":
            signal = "❌"
            rec = "Avoid for profit — interest declining"
        # Always available + high wishlist (early watch signal)
        elif pattern == "Always" and wishlist_pressure == "🔥":
            signal = "⚠️"
            rec = "Watch closely — high latent demand"
        # Default: oversupplied
        else:
            signal = "❌"
            rec = "Avoid for profit — oversupplied"

        # Generate sparklines for price and wishlist trends
        # Use carry-forward to show persistent values when OUT (price/wishlist don't disappear)
        price_history = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp", max_runs=8)
        wishlist_history = extract_historical_values_with_carryforward(key, by_run, runs, "wishlist_count", max_runs=8)
        
        price_sparkline = price_history['unicode']
        wishlist_sparkline = wishlist_history['unicode']
        
        # Generate structured explanation of signal drivers
        drivers = _generate_breeder_drivers_text(
            oos_status=oos_status,
            oos_runs=oos_runs,
            pattern=pattern,
            price_trend=price_trend,
            wishlist_pressure=wishlist_pressure,
            wishlist_delta=wishlist_delta
        )

        table.append({
            "Species": row.get("scientific_name", key[0]),
            "Size (cm)": row.get("size_cm", key[1]),
            "OOS": oos_status,
            "OOS Runs": str(oos_runs),
            "Stock Pattern": pattern,
            "Price": price_cell,
            "Price History": price_sparkline,
            "Wishlist": f"{wishlist_count} {wishlist_pressure} {wishlist_delta}",
            "Wishlist History": wishlist_sparkline,
            "Signal": signal,
            "Recommendation": rec,
            "Drivers": drivers
        })

    # Sort: Signal priority (🔥 > ⚠️ > ❌), then Wishlist count (desc), then OOS Runs (desc)
    table.sort(key=lambda r: (
        SIGNAL_PRIORITY[r["Signal"]],
        -int(r["Wishlist"].split()[0]) if r.get("Wishlist", "").split() else 0,
        -int(r["OOS Runs"])
    ))
    return table

def write_breeder_outputs(table):
    fallback_fieldnames = [
        "Species", "Size (cm)", "OOS", "OOS Runs", "Stock Pattern",
        "Price", "Price History", "Wishlist",
        "Wishlist History", "Signal", "Recommendation", "Drivers",
    ]
    write_matrix_csv(BREEDER_TABLE_FILE, table, fallback_fieldnames)

    config = MatrixSummaryConfig(
        title="🧬 Breeder Opportunity Matrix",
        csv_filepath=BREEDER_TABLE_FILE,
        empty_message="No breeding opportunities detected (conservative analysis requires sufficient historical data).",
        indicator_field="Signal",
        indicator_labels={"🔥": "Hot", "⚠️": "Watch", "❌": "Avoid"},
        table_columns=[
            "Species", "Size (cm)", "OOS", "OOS Runs", "Stock Pattern",
            "Price", "Price History", "Wishlist",
            "Wishlist History", "Signal", "Recommendation",
        ],
    )
    return write_matrix_summary(table, config)

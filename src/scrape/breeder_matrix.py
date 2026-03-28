#!/usr/bin/env python3
from shared.history_utils import (
    compare_prices,
    create_observation_coverage,
    format_observation_coverage,
    is_newly_observed_coverage,
    k2,
)
from shared.config import BREEDER_TABLE_FILE, SIGNAL_PRIORITY
from shared.driver_text_helpers import build_drivers_text
from shared.price_text_helpers import format_price_cell
from shared.summary_utils import MatrixOutputConfig, write_matrix_outputs
from scrape.matrix_workflow import (
    collect_lookback_values_for_key,
    generate_price_wishlist_sparklines,
    get_wishlist_display_metrics,
    iter_lookback_rows_for_key,
    prepare_matrix_analysis,
    prepare_matrix_runs,
)

# =====================
# BREEDER MATRIX (PRICE AWARE) — FIXED TO INCLUDE OUT-OF-STOCK ITEMS
# =====================

BREEDER_WARNING_PATTERN_PRIORITY = {
    "Emerging": 0,
    "Cyclical": 1,
    "Newly Observed": 2,
}

BREEDER_NEWLY_OBSERVED_MAX_RUNS = 2
BREEDER_SUSTAINED_OOS_RUNS = 4
BREEDER_EMERGING_MIN_OOS_RUNS = 2


def _extract_wishlist_count(row: dict[str, str]) -> int:
    """Extract wishlist count from the combined wishlist display cell."""
    wishlist_value = str(row.get("Wishlist", "")).split()
    if not wishlist_value:
        return 0
    try:
        return int(wishlist_value[0])
    except (ValueError, IndexError):
        return 0


def _generate_breeder_drivers_text(
    oos_status: str,
    oos_runs: int,
    pattern: str,
    price_trend: str,
    wishlist_pressure: str,
    wishlist_delta: str,
    observation_coverage_text: str = "",
) -> str:
    """Generate structured explanation of signal drivers using semicolon separators.
    
    Args:
        oos_status: Current stock status (IN/OUT/IN/OUT)
        oos_runs: Number of consecutive OOS runs
        pattern: Stock pattern (Sustained/Emerging/Cyclical/Always/Newly Observed)
        price_trend: Price direction (↑/→/↓)
        wishlist_pressure: Demand level (🔥/⚠️/❌)
        wishlist_delta: Momentum (↑/→/↓)
        observation_coverage_text: Optional sparse-history coverage text
        
    Returns:
        Semicolon-separated string explaining the signal drivers
        
    Example:
        "Stock: Emerging (OOS 2 runs; currently OUT); Demand: Wishlist 🔥 + rising; Price: Stable"
    """
    stock_details = []
    if oos_runs > 0:
        plural = "s" if oos_runs != 1 else ""
        stock_details.append(f"OOS {oos_runs} run{plural}")
    if oos_status:
        stock_details.append(f"currently {oos_status}")
    
    if stock_details:
        stock_section = f"Stock: {pattern} ({'; '.join(stock_details)})"
    else:
        stock_section = f"Stock: {pattern}"

    if observation_coverage_text:
        stock_section = f"{stock_section}; Coverage: {observation_coverage_text}"
    
    return build_drivers_text(stock_section, price_trend, wishlist_pressure, wishlist_delta)


def build_breeder_opportunity_table(history_rows):
    prepared = prepare_matrix_analysis(history_rows)
    if prepared is None:
        return []

    by_run, runs, cur_run, prev_run, cur_rows, run_index, wishlist_pressure_map = prepared
    prev_rows = by_run[prev_run]

    # Index rows by (species,size) for quick lookup
    cur_map = {k2(r): r for r in cur_rows}
    prev_map = {k2(r): r for r in prev_rows}

    # Union of keys across ALL history so OUT items can appear in the breeder table
    all_keys = set()
    for rt in runs:
        for r in by_run[rt]:
            all_keys.add(k2(r))

    # For display of OUT items: bounded last-seen row
    def get_last_seen_row_within_lookback(key):
        return next(iter_lookback_rows_for_key(key, by_run, runs, cur_run, run_index), None)

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

        prices.extend(
            collect_lookback_values_for_key(
                key,
                by_run,
                runs,
                cur_run,
                run_index,
                lambda row: row.get("price_gbp", ""),
                max_values=2 - len(prices),
            )
        )

        if len(prices) >= 2:
            return compare_prices(prices[0], prices[1])
        return "→"

    table = []

    # Precompute membership sets per run for faster OOS counting
    keys_by_run = {rt: {k2(r) for r in by_run[rt]} for rt in runs}

    for key in sorted(all_keys):
        in_current = key in keys_by_run[cur_run]
        in_prev = key in keys_by_run[prev_run]
        observation_coverage = create_observation_coverage(history_rows, key)
        observation_coverage_text = ""

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

        # Pattern derived from OOS evidence, with a conservative sparse-history hold state.
        is_newly_observed = is_newly_observed_coverage(observation_coverage)

        if is_newly_observed:
            pattern = "Newly Observed"
            observation_coverage_text = format_observation_coverage(observation_coverage)
        elif oos_runs >= BREEDER_SUSTAINED_OOS_RUNS:
            pattern = "Sustained"
        elif oos_runs >= BREEDER_EMERGING_MIN_OOS_RUNS:
            pattern = "Emerging"
        elif oos_status == "IN/OUT":
            pattern = "Cyclical"
        else:
            pattern = "Always"

        price_trend = price_trend_for_key(key)
        price_cell = format_price_cell(row.get("price_gbp", ""), price_trend)

        wishlist_pressure, wishlist_delta, wishlist_count, wishlist_display = get_wishlist_display_metrics(
            key, by_run, runs, cur_run, wishlist_pressure_map
        )

        # Recommendation logic (conservative wishlist integration with delta)
        # Base signal driven by Pattern + Price Trend (unchanged)
        # Wishlist can upgrade confidence or escalate emerging signals
        # Wishlist Delta acts as momentum modifier
        
        if pattern == "Newly Observed":
            signal = "⚠️"
            rec = (
                "Monitor closely — newly observed, limited history "
                f"({observation_coverage_text})"
            )
        # Sustained scarcity with strong buyer interest
        elif pattern == "Sustained" and price_trend in ("↑", "→") and wishlist_pressure == "🔥":
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
        price_sparkline, wishlist_sparkline = generate_price_wishlist_sparklines(
            key, by_run, runs, max_runs=8
        )
        
        # Generate structured explanation of signal drivers
        drivers = _generate_breeder_drivers_text(
            oos_status=oos_status,
            oos_runs=oos_runs,
            pattern=pattern,
            price_trend=price_trend,
            wishlist_pressure=wishlist_pressure,
            wishlist_delta=wishlist_delta,
            observation_coverage_text=observation_coverage_text,
        )

        table.append({
            "Species": row.get("scientific_name", key[0]),
            "Size (cm)": row.get("size_cm", key[1]),
            "OOS": oos_status,
            "OOS Runs": str(oos_runs),
            "Stock Pattern": pattern,
            "Price": price_cell,
            "Price History": price_sparkline,
            "Wishlist": wishlist_display,
            "Wishlist History": wishlist_sparkline,
            "Signal": signal,
            "Recommendation": rec,
            "Drivers": drivers
        })

    # Sort: Signal priority, breeder watch-bucket precedence, then Wishlist count and OOS runs.
    table.sort(
        key=lambda row: (
            SIGNAL_PRIORITY.get(str(row.get("Signal", "")), 99),
            BREEDER_WARNING_PATTERN_PRIORITY.get(str(row.get("Stock Pattern", "")), -1)
            if row.get("Signal") == "⚠️"
            else -1,
            -_extract_wishlist_count(row),
            -float(row["OOS Runs"]),
        )
    )
    return table

def write_breeder_outputs(table):
    output_config = MatrixOutputConfig(
        title="🧬 Breeder Opportunity Matrix",
        csv_filepath=BREEDER_TABLE_FILE,
        empty_message="No breeding opportunities detected (conservative analysis requires sufficient historical data).",
        indicator_field="Signal",
        indicator_labels={"🔥": "Hot", "⚠️": "Watch", "❌": "Avoid"},
        fallback_fieldnames=[
        "Species", "Size (cm)", "OOS", "OOS Runs", "Stock Pattern",
        "Price", "Price History", "Wishlist",
        "Wishlist History", "Signal", "Recommendation", "Drivers",
        ],
        table_columns=[
            "Species", "Size (cm)", "OOS", "OOS Runs", "Stock Pattern",
            "Price", "Price History", "Wishlist",
            "Wishlist History", "Signal", "Recommendation",
        ],
    )
    return write_matrix_outputs(table, output_config)

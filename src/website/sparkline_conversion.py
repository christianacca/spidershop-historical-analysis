"""Sparkline conversion utilities for generating interactive SVG sparklines.

This module handles conversion of Unicode sparkline characters to interactive
SVG graphics with tooltips, supporting price, wishlist, and stock availability metrics.
"""

import csv
import os
from typing import Optional, List, Tuple, Dict


# Sparkline character mapping (Unicode to relative height 0-7)
SPARKLINE_CHARS = {
    '▁': 1, '▂': 2, '▃': 3, '▄': 4,
    '▅': 5, '▆': 6, '▇': 7, '█': 8,
    ' ': None  # Gap/missing data
}


def _compute_bar_data(
    unicode_sparkline: str,
    bars: List[Optional[int]],
    metric_type: str,
    compact_values: Optional[List[str]],
    compact_is_carried_forward: Optional[List[bool]],
    color: str,
) -> List[Optional[Tuple]]:
    """Compute per-bar rendering data for a sparkline.

    Returns a list containing one entry per bar slot in ``bars``:
    - ``None`` for gap slots (space characters in stock sparklines)
    - A ``(bar_height, fill, opacity, tooltip)`` tuple for rendered bars

    This shared helper is called by both ``convert_sparkline_to_svg`` and
    ``sparkline_to_dto`` so both code paths use identical rendering semantics.
    """
    svg_height = 20
    total_slots = len(bars)

    # Precompute normalization range for price/wishlist
    if metric_type in ("price", "wishlist") and compact_values:
        valid_floats = [float(v) for v in compact_values]
        max_val = max(valid_floats) if valid_floats else 1.0
        value_range = max_val if max_val > 0 else 1.0
    else:
        value_range = None

    result: List[Optional[Tuple]] = []
    bar_index = 0  # index into compact_values / compact_is_carried_forward

    for i, height in enumerate(bars):
        if height is None:
            result.append(None)
            continue

        # Bar height
        if metric_type == "stock":
            bar_height = (height / 8.0) * svg_height
        else:
            if bar_index >= len(compact_values):
                break  # Safety guard: mismatched lengths
            val_float = float(compact_values[bar_index])
            bar_height = (0.1 + (val_float / value_range) * 0.9) * svg_height

        # Opacity gradient (older bars are more transparent)
        opacity = 0.7 + (i / total_slots) * 0.3

        # Carry-forward flag
        is_carried = (
            compact_is_carried_forward is not None
            and bar_index < len(compact_is_carried_forward)
            and compact_is_carried_forward[bar_index]
        )

        # Tooltip
        if metric_type == "price":
            val = compact_values[bar_index]
            tooltip = f"[\xa3{val}]" if is_carried else f"\xa3{val}"
        elif metric_type == "wishlist":
            val = compact_values[bar_index]
            plural = "wishlist" if val == "1" else "wishlists"
            tooltip = f"[{val} {plural}]" if is_carried else f"{val} {plural}"
        else:  # stock
            tooltip = "IN"

        result.append((bar_height, color, opacity, tooltip))
        bar_index += 1

    return result


def convert_sparkline_to_svg(unicode_sparkline: str, values: Optional[List[float]] = None, metric_type: str = "price", is_carried_forward: Optional[List[bool]] = None) -> str:
    """
    Convert a Unicode sparkline to an interactive SVG with tooltips.
    
    Args:
        unicode_sparkline: String of Unicode sparkline characters (e.g., "▁▂▃▄▅▆▇█")
        values: List of actual numeric values for price/wishlist, None for stock
        metric_type: "price", "wishlist", or "stock"
        is_carried_forward: List of booleans indicating which values are carried-forward (optional)
    
    Returns:
        String containing SVG markup, or original string if conversion not possible
        
    Raises:
        AssertionError: If values are required but missing/invalid for price/wishlist
    """
    # Don't convert if it's just a dash or empty string
    if not unicode_sparkline or unicode_sparkline == "-":
        return unicode_sparkline
    
    # Parse Unicode characters into bar heights
    bars = []
    for char in unicode_sparkline:
        if char in SPARKLINE_CHARS:
            height = SPARKLINE_CHARS[char]
            bars.append(height)
        else:
            # Unknown character, return original
            return unicode_sparkline
    
    # Need at least one non-None bar
    non_none_bars = [b for b in bars if b is not None]
    if not non_none_bars:
        return "-"
    
    # For price/wishlist: values must be provided and valid (fail fast)
    if metric_type in ["price", "wishlist"]:
        assert values is not None, f"Values required for {metric_type} sparklines"
        assert len(values) > 0, f"Values array cannot be empty for {metric_type} sparklines"
        # Validate all non-gap values are numeric (None/empty strings are gaps and are allowed)
        for v in values:
            if v is None or v == "":
                continue  # Gaps (None/empty) are treated as missing data, not errors
            assert str(v).replace('.', '').replace('-', '').isdigit(), \
                f"Invalid non-numeric value in {metric_type} sparkline: {v}"
    
    # Determine trend direction for color coding
    # For stock: always green
    if metric_type == "stock":
        color = "#22c55e"  # Green
        trend = "stock"
    # For price/wishlist: check for actual changes
    elif len(non_none_bars) >= 2 and is_carried_forward:
        # Check if ALL values after first are carried forward (no actual change)
        non_none_indices = [i for i, b in enumerate(bars) if b is not None]
        all_carried_after_first = all(
            is_carried_forward[i] 
            for i in non_none_indices[1:] 
            if i < len(is_carried_forward)
        )
        
        if all_carried_after_first:
            # No actual change - use neutral color
            color = "#3b82f6"  # Blue
            trend = "stable"
        else:
            # Has actual changes - use trend color based on first vs last
            first_val = non_none_bars[0]
            last_val = non_none_bars[-1]
            if last_val > first_val + 1:  # Rising
                color = "#22c55e"  # Green
                trend = "rising"
            elif last_val < first_val - 1:  # Falling
                color = "#ef4444"  # Red
                trend = "falling"
            else:
                color = "#3b82f6"  # Blue (stable)
                trend = "stable"
    elif len(non_none_bars) >= 2:
        # No is_carried_forward info - use simple trend detection
        first_val = non_none_bars[0]
        last_val = non_none_bars[-1]
        if last_val > first_val + 1:  # Rising
            color = "#22c55e"  # Green
            trend = "rising"
        elif last_val < first_val - 1:  # Falling
            color = "#ef4444"  # Red
            trend = "falling"
        else:
            color = "#3b82f6"  # Blue (stable)
            trend = "stable"
    else:
        # Single bar
        color = "#3b82f6"  # Blue
        trend = "stable"
    
    # Generate SVG bars
    svg_bars = []
    bar_width = 8
    bar_spacing = 10
    svg_width = len(bars) * bar_spacing
    svg_height = 20

    # Compact values for price/wishlist (strips gap entries)
    if metric_type == "stock":
        compact_values = None
        compact_is_carried_forward = None
    else:
        non_gap = [(v, cf) for v, cf in zip(values, is_carried_forward or [False] * len(values)) if v not in (None, "")]
        compact_values = [v for v, _ in non_gap]
        compact_is_carried_forward = [cf for _, cf in non_gap]

    per_bar = _compute_bar_data(
        unicode_sparkline, bars, metric_type, compact_values, compact_is_carried_forward, color
    )

    for i, item in enumerate(per_bar):
        if item is None:
            continue  # Gap slot
        bar_height, fill, opacity, tooltip = item
        x = i * bar_spacing
        y = svg_height - bar_height
        svg_bars.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" '
            f'fill="{fill}" opacity="{opacity:.2f}"><title>{tooltip}</title></rect>'
        )

    # Assemble final SVG
    if metric_type == "price":
        svg_title = "Price History"
    elif metric_type == "wishlist":
        svg_title = "Wishlist History"
    elif metric_type == "stock":
        svg_title = "Stock History"
    else:
        svg_title = f"{metric_type.capitalize()} History"
    
    svg = (
        f'<svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" '
        f'style="vertical-align: middle;">'
        f'<title>{svg_title}</title>'
        f'{"".join(svg_bars)}'
        f'</svg>'
    )
    
    return svg


def sparkline_to_dto(
    unicode_sparkline: str,
    values: Optional[List],
    metric_type: str = "price",
    is_carried_forward: Optional[List[bool]] = None,
) -> Optional[dict]:
    """Convert a Unicode sparkline to a rendering DTO dict for the Svelte SparklineBar component.

    Args:
        unicode_sparkline: String of Unicode sparkline characters (e.g., "▁▂▃▄▅▆▇█")
        values: List of actual numeric values for price/wishlist, None for stock
        metric_type: "price", "wishlist", or "stock"
        is_carried_forward: List of booleans indicating which values are carried-forward

    Returns:
        A dict with ``bars``, ``svg_width``, ``svg_height``, and ``title`` keys,
        or ``None`` for empty/dash inputs.
    """
    if not unicode_sparkline or unicode_sparkline == "-":
        return None

    # Parse Unicode characters into bar levels
    bars = []
    for char in unicode_sparkline:
        if char in SPARKLINE_CHARS:
            bars.append(SPARKLINE_CHARS[char])
        else:
            return None  # Unknown character — cannot produce DTO

    non_none_bars = [b for b in bars if b is not None]
    if not non_none_bars:
        return None

    # Determine trend color (identical logic to convert_sparkline_to_svg)
    if metric_type == "stock":
        color = "#22c55e"
    elif len(non_none_bars) >= 2 and is_carried_forward:
        non_none_indices = [i for i, b in enumerate(bars) if b is not None]
        all_carried_after_first = all(
            is_carried_forward[i]
            for i in non_none_indices[1:]
            if i < len(is_carried_forward)
        )
        if all_carried_after_first:
            color = "#3b82f6"
        else:
            first_val, last_val = non_none_bars[0], non_none_bars[-1]
            if last_val > first_val + 1:
                color = "#22c55e"
            elif last_val < first_val - 1:
                color = "#ef4444"
            else:
                color = "#3b82f6"
    elif len(non_none_bars) >= 2:
        first_val, last_val = non_none_bars[0], non_none_bars[-1]
        if last_val > first_val + 1:
            color = "#22c55e"
        elif last_val < first_val - 1:
            color = "#ef4444"
        else:
            color = "#3b82f6"
    else:
        color = "#3b82f6"

    # Compact values for price/wishlist (strips gap entries)
    if metric_type in ("price", "wishlist") and values is not None:
        non_gap = [
            (v, cf)
            for v, cf in zip(values, is_carried_forward or [False] * len(values))
            if v not in (None, "")
        ]
        compact_values = [v for v, _ in non_gap]
        compact_is_carried_forward = [cf for _, cf in non_gap]
    else:
        compact_values = None
        compact_is_carried_forward = None

    per_bar = _compute_bar_data(
        unicode_sparkline, bars, metric_type, compact_values, compact_is_carried_forward, color
    )

    dto_bars = []
    for item in per_bar:
        if item is None:
            dto_bars.append(None)
        else:
            bar_height, fill, opacity, tooltip = item
            dto_bars.append({
                "bar_height": bar_height,
                "fill": fill,
                "opacity": opacity,
                "tooltip": tooltip,
            })

    titles = {"price": "Price History", "wishlist": "Wishlist History", "stock": "Stock History"}
    title = titles.get(metric_type, f"{metric_type.capitalize()} History")

    return {
        "bars": dto_bars,
        "svg_width": len(bars) * 10,
        "svg_height": 20,
        "title": title,
    }


def load_historical_sparkline_data() -> Tuple[Dict[str, List[Dict[str, str]]], List[str]]:
    """
    Load historical data from history CSV in format ready for sparkline extraction.
    
    Returns:
        Tuple of (by_run, runs) where:
        - by_run: Dictionary mapping run_id (scrape_datetime) to list of rows
        - runs: Sorted list of run IDs (scrape_datetime values)
    """
    from shared.history_utils import group_by_run
    
    history_file = "spidershop_spiderlings_history.csv"
    if not os.path.exists(history_file):
        return {}, []
    
    try:
        history = []
        with open(history_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append(row)
        
        # Group by run and get sorted runs
        by_run = group_by_run(history)
        runs = sorted(by_run)
        
        return by_run, runs
    except Exception as e:
        print(f"Warning: Could not load historical data: {e}")
        return {}, []


def convert_sparklines_in_rows(headers: List[str], rows: List[List[str]], historical_data: Tuple[Dict[str, List[Dict[str, str]]], List[str]], csv_filename: str) -> List[List[str]]:
    """
    Convert Unicode sparklines to SVG in specific columns.
    
    Args:
        headers: List of column names
        rows: List of data rows
        historical_data: Tuple of (by_run, runs) for sparkline extraction
        csv_filename: Name of the CSV file being processed
    
    Returns:
        Modified rows with sparklines converted to SVG
    """
    from shared.sparkline_helpers import extract_historical_values_with_carryforward
    
    by_run, runs = historical_data
    
    # Identify sparkline columns
    sparkline_columns = {}
    for i, header in enumerate(headers):
        if "History" in header or "Availability" in header:
            if "Price" in header:
                sparkline_columns[i] = "price_gbp"
            elif "Wishlist" in header:
                sparkline_columns[i] = "wishlist_count"
            elif "Stock" in header or "Availability" in header:
                sparkline_columns[i] = "stock"
    
    if not sparkline_columns:
        return rows  # No sparkline columns found
    
    # Get species and size column indices
    species_idx = headers.index("Species") if "Species" in headers else None
    size_idx = headers.index("Size (cm)") if "Size (cm)" in headers else None
    
    # Convert sparklines in each row
    converted_rows = []
    for row in rows:
        new_row = list(row)  # Make a copy
        
        # Get species/size for looking up historical values
        species = row[species_idx] if species_idx is not None else None
        size = row[size_idx] if size_idx is not None else None
        key = (species, size) if species and size else None
        
        # Convert each sparkline column
        for col_idx, field_name in sparkline_columns.items():
            if col_idx < len(new_row):
                unicode_sparkline = new_row[col_idx]
                
                # Extract values with carried-forward tracking using the same logic as matrix generation
                values = None
                is_carried_forward = None
                
                # Determine metric type from field_name
                if field_name == "stock":
                    metric_type = "stock"
                elif field_name == "price_gbp":
                    metric_type = "price"
                elif field_name == "wishlist_count":
                    metric_type = "wishlist"
                else:
                    metric_type = None
                
                # Extract historical values if available
                if field_name != "stock" and key and by_run:
                    result = extract_historical_values_with_carryforward(key, by_run, runs, field_name, max_runs=8)
                    values = result['values']
                    is_carried_forward = result['is_carried_forward']
                
                # Convert to SVG only if we have valid data
                # For price/wishlist: skip conversion if no values (keep Unicode sparkline)
                # For stock: always convert (doesn't need values)
                if metric_type == "stock" or (values and len(values) > 0):
                    svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type, is_carried_forward=is_carried_forward)
                    new_row[col_idx] = svg
                # else: keep Unicode sparkline unchanged
        
        converted_rows.append(new_row)
    
    return converted_rows


def build_sparkline_dto_rows(
    headers: List[str],
    rows: List[List],
    historical_data: Tuple[Dict[str, List[Dict[str, str]]], List[str]],
    csv_filename: str,
) -> List[List]:
    """Convert Unicode sparklines to DTO dicts in sparkline columns.

    Parallel to ``convert_sparklines_in_rows`` but returns pre-computed rendering
    DTO dicts instead of SVG strings.  Non-sparkline cells are unchanged.  When
    historical data is unavailable for a species, the Unicode sparkline is kept as-is.

    Args:
        headers: List of column names
        rows: List of data rows
        historical_data: Tuple of (by_run, runs) for sparkline extraction
        csv_filename: Name of the CSV file being processed

    Returns:
        Modified rows with sparkline cells replaced by DTO dicts where possible
    """
    from shared.sparkline_helpers import extract_historical_values_with_carryforward

    by_run, runs = historical_data

    # Identify sparkline columns (same mapping as convert_sparklines_in_rows)
    sparkline_columns: Dict[int, str] = {}
    for i, header in enumerate(headers):
        if "History" in header or "Availability" in header:
            if "Price" in header:
                sparkline_columns[i] = "price_gbp"
            elif "Wishlist" in header:
                sparkline_columns[i] = "wishlist_count"
            elif "Stock" in header or "Availability" in header:
                sparkline_columns[i] = "stock"

    if not sparkline_columns:
        return rows

    species_idx = headers.index("Species") if "Species" in headers else None
    size_idx = headers.index("Size (cm)") if "Size (cm)" in headers else None

    converted_rows = []
    for row in rows:
        new_row = list(row)
        species = row[species_idx] if species_idx is not None else None
        size = row[size_idx] if size_idx is not None else None
        key = (species, size) if species and size else None

        for col_idx, field_name in sparkline_columns.items():
            if col_idx >= len(new_row):
                continue
            unicode_sparkline = new_row[col_idx]

            if field_name == "stock":
                metric_type = "stock"
            elif field_name == "price_gbp":
                metric_type = "price"
            elif field_name == "wishlist_count":
                metric_type = "wishlist"
            else:
                continue

            values = None
            is_carried_forward = None
            if field_name != "stock" and key and by_run:
                result = extract_historical_values_with_carryforward(
                    key, by_run, runs, field_name, max_runs=8
                )
                values = result["values"]
                is_carried_forward = result["is_carried_forward"]

            if metric_type == "stock" or (values and len(values) > 0):
                dto = sparkline_to_dto(unicode_sparkline, values, metric_type, is_carried_forward)
                if dto is not None:
                    new_row[col_idx] = dto
                # else: keep unicode sparkline if conversion failed

        converted_rows.append(new_row)

    return converted_rows

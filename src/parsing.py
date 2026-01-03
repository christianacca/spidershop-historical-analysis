#!/usr/bin/env python3
import re
from decimal import Decimal, InvalidOperation
from config import PARENS_RE, SIZE_RE, WISHLIST_COUNT_RE

# =====================
# PARSING HELPERS
# =====================

def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()

def first_cm_parenthetical(text: str):
    for m in PARENS_RE.finditer(text or ""):
        if "cm" in m.group(1).lower():
            return m.group(0)
    return None

def parse_size_cm(text: str) -> str:
    paren = first_cm_parenthetical(text)
    if not paren:
        return ""
    inner = paren[1:-1]
    m = SIZE_RE.match(inner)
    if not m:
        return ""
    try:
        val = m.group(2) or m.group(1)
        d = Decimal(val)
        return str(int(d)) if d == d.to_integral_value() else format(d, "f")
    except InvalidOperation:
        return ""

def remove_size_parenthetical_only(text: str) -> str:
    text = normalize_whitespace(text)
    paren = first_cm_parenthetical(text)
    if not paren:
        return text
    return normalize_whitespace(text.replace(paren, " ", 1))

def parse_price(text: str) -> str:
    if not text:
        return ""
    s = text.replace("£", "").replace("\u00a3", "").replace(",", "").strip()
    try:
        return format(Decimal(s), "f")
    except InvalidOperation:
        return ""

def parse_wishlist_count(text: str) -> str:
    if not text:
        return "0"
    text = normalize_whitespace(text)
    m = WISHLIST_COUNT_RE.search(text)
    if m:
        return m.group(1)
    return "0"

def compute_wishlist_pressure(rows):
    """
    Compute relative wishlist pressure for rows in the current run.
    
    Returns a dict mapping (scientific_name, size_cm) -> pressure symbol.
    
    Pressure symbols:
    - 🔥 = High wishlist pressure (top ~25% of non-zero wishlist counts)
    - ⚠️ = Moderate wishlist pressure (middle range)
    - ❌ = Low or no wishlist pressure (bottom tier or zero)
    
    IMPORTANT: Wishlist pressure is RELATIVE per run, not absolute.
    🔥 does NOT mean high absolute count; it reflects ranking within the current distribution.
    This prevents popularity bias and adapts to site growth or shrinkage.
    
    Uses relative ranking to avoid site-growth drift and popularity bias.
    This is run per-scrape to ensure bands adapt to current distribution.
    """
    # Extract wishlist counts, filtering to current rows only
    wishlist_data = []
    for r in rows:
        try:
            count = int(r.get("wishlist_count", "0") or "0")
            key = (r.get("scientific_name", ""), r.get("size_cm", ""))
            wishlist_data.append((key, count))
        except (ValueError, TypeError):
            key = (r.get("scientific_name", ""), r.get("size_cm", ""))
            wishlist_data.append((key, 0))
    
    if not wishlist_data:
        return {}
    
    # Separate zero and non-zero counts
    zero_keys = {k for k, c in wishlist_data if c == 0}
    nonzero = [(k, c) for k, c in wishlist_data if c > 0]
    
    result = {}
    
    # All zeros get ❌
    for k in zero_keys:
        result[k] = "❌"
    
    if not nonzero:
        return result
    
    # Sort non-zero by count descending
    nonzero.sort(key=lambda x: x[1], reverse=True)
    
    # Small-N flattening: if all wishlist counts are very close (max - min ≤ 1),
    # then the distribution is too flat to meaningfully rank.
    # Conservative interpretation: assign ⚠️ to all non-zero to avoid artificial 🔥.
    counts = [c for _, c in nonzero]
    if counts and max(counts) - min(counts) <= 1:
        for k, _ in nonzero:
            result[k] = "⚠️"
        return result
    
    # Use percentile-based bands:
    # Top 25% = 🔥 (high pressure)
    # Next 50% = ⚠️ (moderate)
    # Bottom 25% = ❌ (low)
    n = len(nonzero)
    high_cutoff = max(1, n // 4)  # top 25%
    low_cutoff = max(1, (3 * n) // 4)  # bottom 25%
    
    for i, (k, _) in enumerate(nonzero):
        if i < high_cutoff:
            result[k] = "🔥"
        elif i < low_cutoff:
            result[k] = "⚠️"
        else:
            result[k] = "❌"
    
    return result


def get_oos_wishlist_carryover(key, by_run, runs, cur_run, lookback_limit=3):
    """
    For OUT-of-stock species, carry forward wishlist pressure from the most recent run
    where it was IN stock, within a bounded lookback window.
    
    Args:
        key: (scientific_name, size_cm) tuple
        by_run: dict mapping run datetime -> list of rows
        runs: sorted list of run datetimes
        cur_run: current run datetime
        lookback_limit: max number of recent runs to look back (default 3)
    
    Returns:
        Wishlist pressure symbol (🔥/⚠️/❌) or None if not found
    
    Rationale:
        Wishlist interest often peaks just before sell-out.
        This prevents under-valuing OUT species with real latent demand.
        Keeps behavior conservative and bounded.
    """
    # Find the index of the current run
    try:
        cur_idx = runs.index(cur_run)
    except ValueError:
        return None
    
    # Look back through recent runs (excluding current)
    lookback_start = max(0, cur_idx - lookback_limit)
    for i in range(cur_idx - 1, lookback_start - 1, -1):
        rt = runs[i]
        # Check if key exists in this run
        run_rows = by_run[rt]
        run_map = {(r.get("scientific_name", ""), r.get("size_cm", "")): r for r in run_rows}
        
        if key in run_map:
            # Found the species in this run - compute its pressure
            pressure_map = compute_wishlist_pressure(run_rows)
            return pressure_map.get(key, "❌")
    
    return None


def compute_wishlist_delta(key, by_run, runs, cur_run, lookback_limit=3):
    """
    Compute Wishlist Delta (momentum signal) for a species by comparing current vs
    previous IN-stock wishlist counts using conservative thresholds.
    
    Args:
        key: (scientific_name, size_cm) tuple
        by_run: dict mapping run datetime -> list of rows
        runs: sorted list of run datetimes
        cur_run: current run datetime
        lookback_limit: max number of recent runs to look back for OUT species (default 3)
    
    Returns:
        Wishlist Delta symbol:
        - "↑" if Δ ≥ +5 (meaningful increase)
        - "→" if −4 ≤ Δ ≤ +4 (stable or noise)
        - "↓" if Δ ≤ −5 (meaningful decrease)
    
    Rationale:
        Conservative thresholds prevent false signals from noise.
        Uses ±5 as meaningful buyer movement threshold given observed distributions.
        Weekly cadence requires higher bar for momentum detection.
    """
    # Find the index of the current run
    try:
        cur_idx = runs.index(cur_run)
    except ValueError:
        return "→"
    
    # Get current wishlist count
    # First, check if species is IN current run
    cur_rows = by_run[cur_run]
    cur_map = {(r.get("scientific_name", ""), r.get("size_cm", "")): r for r in cur_rows}
    
    current_count = None
    if key in cur_map:
        # Species is IN current run
        try:
            current_count = int(cur_map[key].get("wishlist_count", "0") or "0")
        except (ValueError, TypeError):
            current_count = 0
    else:
        # Species is OUT - look back for last IN-stock wishlist count
        lookback_start = max(0, cur_idx - lookback_limit)
        for i in range(cur_idx - 1, lookback_start - 1, -1):
            rt = runs[i]
            run_rows = by_run[rt]
            run_map = {(r.get("scientific_name", ""), r.get("size_cm", "")): r for r in run_rows}
            
            if key in run_map:
                try:
                    current_count = int(run_map[key].get("wishlist_count", "0") or "0")
                except (ValueError, TypeError):
                    current_count = 0
                break
    
    # If we couldn't find a current count, return neutral
    if current_count is None:
        return "→"
    
    # Find previous comparable wishlist count (last run where species was IN)
    previous_count = None
    lookback_start = max(0, cur_idx - lookback_limit)
    
    # Start from the run before where we found current_count
    # If species is IN now, start from prev run
    # If species is OUT now and we found count in an older run, start from before that
    search_start_idx = cur_idx - 1
    if key not in cur_map:
        # Species is OUT - we found current_count in an older run
        # Need to search before that run
        for i in range(cur_idx - 1, lookback_start - 1, -1):
            rt = runs[i]
            run_rows = by_run[rt]
            run_map = {(r.get("scientific_name", ""), r.get("size_cm", "")): r for r in run_rows}
            if key in run_map:
                search_start_idx = i - 1
                break
    
    # Now find the previous IN-stock occurrence
    for i in range(search_start_idx, -1, -1):
        rt = runs[i]
        run_rows = by_run[rt]
        run_map = {(r.get("scientific_name", ""), r.get("size_cm", "")): r for r in run_rows}
        
        if key in run_map:
            try:
                previous_count = int(run_map[key].get("wishlist_count", "0") or "0")
            except (ValueError, TypeError):
                previous_count = 0
            break
    
    # If we couldn't find a previous count, return neutral
    if previous_count is None:
        return "→"
    
    # Calculate delta and apply thresholds
    delta = current_count - previous_count
    
    if delta >= 5:
        return "↑"
    elif delta <= -5:
        return "↓"
    else:
        return "→"

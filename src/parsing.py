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

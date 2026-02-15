#!/usr/bin/env python3
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List
from shared.config import PARENS_RE, SIZE_RE, WISHLIST_COUNT_RE

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


def format_datetime_smart(datetimes: List[str]) -> List[str]:
    """Format datetime strings intelligently: date-only unless collision.
    
    Returns date-only format (YYYY-MM-DD) for unique dates, but includes
    time (YYYY-MM-DD HH:MM) when multiple DIFFERENT runs occur on the same date
    to avoid ambiguous display.
    
    Args:
        datetimes: List of ISO format datetime strings (e.g., "2026-02-15T10:30+00:00")
        
    Returns:
        List of formatted strings in same order as input. Date-only when only
        one unique time exists for a date, full timestamp when multiple unique
        times exist on the same date.
        
    Example:
        >>> format_datetime_smart(["2026-02-15T10:00+00:00", "2026-02-16T10:00+00:00"])
        ["2026-02-15", "2026-02-16"]
        
        >>> format_datetime_smart(["2026-02-15T10:00+00:00", "2026-02-15T14:00+00:00"])
        ["2026-02-15 10:00", "2026-02-15 14:00"]
        
        >>> format_datetime_smart(["2026-02-15T10:00+00:00", "2026-02-15T10:00+00:00"])
        ["2026-02-15", "2026-02-15"]  # Same time repeated = no collision
    """
    if not datetimes:
        return []
    
    # Parse all datetimes and track unique times per date
    parsed = []
    date_to_times = {}  # Map date to set of unique times
    
    for dt_str in datetimes:
        try:
            # Handle both ISO format with timezone and simple date strings
            if 'T' in dt_str:
                # Full ISO format with time
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                # Simple date string (YYYY-MM-DD)
                dt = datetime.strptime(dt_str, "%Y-%m-%d")
            
            date_only = dt.strftime("%Y-%m-%d")
            time_only = dt.strftime("%H:%M")
            
            parsed.append((dt, date_only))
            
            # Track unique times for this date
            if date_only not in date_to_times:
                date_to_times[date_only] = set()
            date_to_times[date_only].add(time_only)
        except (ValueError, AttributeError):
            # Fallthrough: return original string if parsing fails
            parsed.append((None, dt_str))
    
    # Format each datetime based on whether its date has multiple unique times
    result = []
    for dt, date_str in parsed:
        if dt is None:
            # Parsing failed, return original
            result.append(date_str)
        elif len(date_to_times.get(date_str, set())) > 1:
            # Collision: multiple unique times on this date
            result.append(dt.strftime("%Y-%m-%d %H:%M"))
        else:
            # Only one unique time for this date (may appear in multiple rows)
            result.append(date_str)
    
    return result


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
    
    parsed = []
    date_to_times = {}
    
    for dt_str in datetimes:
        dt, date_str = _parse_datetime(dt_str)
        if dt:
            time_str = dt.strftime("%H:%M")
            if date_str not in date_to_times:
                date_to_times[date_str] = set()
            date_to_times[date_str].add(time_str)
        parsed.append((dt, date_str))
    
    return [_format_parsed_datetime(dt, date_str, date_to_times) for dt, date_str in parsed]


def _parse_datetime(dt_str: str):
    """Parse datetime string into datetime object and date string.
    
    Returns:
        Tuple of (datetime_object, date_string). If parsing fails, returns (None, original_string).
    """
    try:
        if 'T' in dt_str:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        elif ' ' in dt_str:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(dt_str, "%Y-%m-%d")
        return dt, dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            return dt, dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return None, dt_str


def _format_parsed_datetime(dt, date_str: str, date_to_times: dict) -> str:
    """Format parsed datetime based on collision detection.
    
    Returns:
        Formatted datetime string (date-only or with time if collision detected).
    """
    if dt is None:
        return date_str
    
    has_collision = len(date_to_times.get(date_str, set())) > 1
    return dt.strftime("%Y-%m-%d %H:%M") if has_collision else date_str


# Overrides for column names that cannot be cleanly derived from snake_case alone
# (e.g. because they contain units in parentheses or use abbreviations with
# different casing from what simple title-casing would produce).
_HEADER_DISPLAY_OVERRIDES: dict[str, str] = {
    "scrape_datetime": "Scrape Date",
    "size_cm": "Size (cm)",
    "price_gbp": "Price (GBP)",
    "page_url": "Page URL",
}


def snake_to_display_header(name: str) -> str:
    """Convert a snake_case column name to a human-readable display name.

    Falls back to title-casing each word when no explicit override exists.

    Examples::

        >>> snake_to_display_header("scientific_name")
        'Scientific Name'
        >>> snake_to_display_header("wishlist_count")
        'Wishlist Count'
        >>> snake_to_display_header("size_cm")
        'Size (cm)'
        >>> snake_to_display_header("price_gbp")
        'Price (GBP)'
        >>> snake_to_display_header("scrape_datetime")
        'Scrape Date'
    """
    if name in _HEADER_DISPLAY_OVERRIDES:
        return _HEADER_DISPLAY_OVERRIDES[name]
    return " ".join(word.capitalize() for word in name.split("_"))


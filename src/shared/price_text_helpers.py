#!/usr/bin/env python3
"""Helpers for formatting matrix price display values."""


def format_price_cell(price_value: str, trend: str) -> str:
    """Format price cell as currency + trend arrow.

    Examples:
        "25.00", "↑" -> "£25.00 ↑"
        "", "→" -> "N/A →"
    """
    try:
        if price_value is not None and str(price_value).strip() != "":
            amount = float(str(price_value).strip())
            return f"£{amount:.2f} {trend}"
    except (TypeError, ValueError):
        return f"N/A {trend}"

    return f"N/A {trend}"

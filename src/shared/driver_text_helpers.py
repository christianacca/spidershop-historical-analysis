"""Helper functions for generating driver text explanations."""

# Common emoji/symbol to text mappings used across analysis modules
WISHLIST_PRESSURE_TEXT = {
    "🔥": "High",
    "⚠️": "Moderate",
    "❌": "Low"
}

DELTA_TEXT = {
    "↑": "rising",
    "→": "stable",
    "↓": "falling"
}

PRICE_TEXT = {
    "↑": "Rising",
    "→": "Stable",
    "↓": "Falling"
}


def format_wishlist_pressure(wishlist_pressure: str) -> str:
    """Convert wishlist pressure emoji to human-readable text.
    
    Args:
        wishlist_pressure: Emoji indicator (🔥/⚠️/❌)
        
    Returns:
        Human-readable string (High/Moderate/Low) or original value if not recognized
    """
    return WISHLIST_PRESSURE_TEXT.get(wishlist_pressure, wishlist_pressure)


def format_delta(delta: str) -> str:
    """Convert delta arrow to human-readable text.
    
    Args:
        delta: Arrow indicator (↑/→/↓)
        
    Returns:
        Human-readable string (rising/stable/falling) or original value if not recognized
    """
    return DELTA_TEXT.get(delta, delta)


def format_price_trend(price_trend: str) -> str:
    """Convert price trend arrow to human-readable text.
    
    Args:
        price_trend: Arrow indicator (↑/→/↓)
        
    Returns:
        Human-readable string (Rising/Stable/Falling) or original value if not recognized
    """
    return PRICE_TEXT.get(price_trend, price_trend)


def build_demand_section(wishlist_pressure: str, wishlist_delta: str, qualifier: str = "") -> str:
    """Build standardized demand section for driver text.

    Args:
        wishlist_pressure: Demand level (🔥/⚠️/❌)
        wishlist_delta: Momentum (↑/→/↓)
        qualifier: Optional parenthetical context when the delta is forced neutral
            (e.g. ``"momentum neutralized; continuity unconfirmed"``).  When
            provided the standard ``"+ delta_text"`` suffix is replaced with
            ``"(<qualifier>)"``.

    Returns:
        Formatted demand section (e.g., "Demand: Wishlist High + rising" or
        "Demand: Wishlist High (momentum neutralized; continuity unconfirmed)")
    """
    pressure_text = format_wishlist_pressure(wishlist_pressure)
    if qualifier:
        return f"Demand: Wishlist {pressure_text} ({qualifier})"
    return f"Demand: Wishlist {pressure_text} + {format_delta(wishlist_delta)}"


def build_price_section(price_trend: str) -> str:
    """Build standardized price section for driver text.

    Args:
        price_trend: Price direction (↑/→/↓)

    Returns:
        Formatted price section (e.g., "Price: Rising")
    """
    return f"Price: {format_price_trend(price_trend)}"


def lineage_driver_overrides(lineage_status: str) -> tuple[str, str]:
    """Return ``(demand_qualifier, price_override)`` for a given lineage status.

    Centralises the mapping so neither breeder nor dealer matrix needs to
    duplicate the same ``if/elif`` block.

    Returns:
        ``demand_qualifier`` — passed to :func:`build_demand_section` to replace
        the standard ``"+ delta"`` suffix with a parenthetical explanation.

        ``price_override`` — when non-empty, replaces the standard
        ``"Price: <trend>"`` string entirely.
    """
    if lineage_status == "multi-variant":
        return "active variants overlap; delta neutralized", "Price: Multiple active sizes"
    if lineage_status == "ambiguous-transition":
        return "momentum neutralized; continuity unconfirmed", ""
    return "", ""


def build_drivers_text(
    stock_section: str,
    price_trend: str,
    wishlist_pressure: str,
    wishlist_delta: str,
    demand_qualifier: str = "",
    price_override: str = "",
) -> str:
    """Build standardized drivers text combining stock, demand, and price sections.

    Args:
        stock_section: Pre-formatted stock section text (e.g., "Stock: Emerging (OOS 2 runs)")
        price_trend: Price direction (↑/→/↓)
        wishlist_pressure: Demand level (🔥/⚠️/❌)
        wishlist_delta: Momentum (↑/→/↓)
        demand_qualifier: Optional qualifier passed through to
            :func:`build_demand_section` — replaces the standard delta suffix
            with a parenthetical explanation.
        price_override: When non-empty, replaces the standard
            ``"Price: <trend>"`` text entirely (e.g. ``"Price: Multiple active sizes"``).

    Returns:
        Semicolon-separated driver explanation
        (e.g., "Stock: Emerging (OOS 2 runs); Demand: Wishlist High + rising; Price: Stable")
    """
    demand_section = build_demand_section(wishlist_pressure, wishlist_delta, demand_qualifier)
    price_section = price_override if price_override else build_price_section(price_trend)
    return f"{stock_section}; {demand_section}; {price_section}"

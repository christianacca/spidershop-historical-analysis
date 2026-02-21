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


def format_wishlist_pressure(wishlist_pressure):
    """Convert wishlist pressure emoji to human-readable text.
    
    Args:
        wishlist_pressure: Emoji indicator (🔥/⚠️/❌)
        
    Returns:
        Human-readable string (High/Moderate/Low) or original value if not recognized
    """
    return WISHLIST_PRESSURE_TEXT.get(wishlist_pressure, wishlist_pressure)


def format_delta(delta):
    """Convert delta arrow to human-readable text.
    
    Args:
        delta: Arrow indicator (↑/→/↓)
        
    Returns:
        Human-readable string (rising/stable/falling) or original value if not recognized
    """
    return DELTA_TEXT.get(delta, delta)


def format_price_trend(price_trend):
    """Convert price trend arrow to human-readable text.
    
    Args:
        price_trend: Arrow indicator (↑/→/↓)
        
    Returns:
        Human-readable string (Rising/Stable/Falling) or original value if not recognized
    """
    return PRICE_TEXT.get(price_trend, price_trend)


def build_demand_section(wishlist_pressure: str, wishlist_delta: str) -> str:
    """Build standardized demand section for driver text.

    Args:
        wishlist_pressure: Demand level (🔥/⚠️/❌)
        wishlist_delta: Momentum (↑/→/↓)

    Returns:
        Formatted demand section (e.g., "Demand: Wishlist High + rising")
    """
    pressure_text = format_wishlist_pressure(wishlist_pressure)
    delta_text = format_delta(wishlist_delta)
    return f"Demand: Wishlist {pressure_text} + {delta_text}"


def build_price_section(price_trend: str) -> str:
    """Build standardized price section for driver text.

    Args:
        price_trend: Price direction (↑/→/↓)

    Returns:
        Formatted price section (e.g., "Price: Rising")
    """
    price_text = format_price_trend(price_trend)
    return f"Price: {price_text}"

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

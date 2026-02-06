"""Tests for driver text helper functions."""
import pytest
from shared.driver_text_helpers import (
    format_wishlist_pressure,
    format_delta,
    format_price_trend
)


class TestFormatWishlistPressure:
    """Test wishlist pressure emoji to text conversion."""
    
    @pytest.mark.parametrize("input_emoji,expected_text", [
        ("🔥", "High"),
        ("⚠️", "Moderate"),
        ("❌", "Low"),
    ])
    def test_converts_known_emojis(self, input_emoji, expected_text):
        assert format_wishlist_pressure(input_emoji) == expected_text
    
    def test_returns_original_for_unknown_values(self):
        assert format_wishlist_pressure("Unknown") == "Unknown"
        assert format_wishlist_pressure("") == ""


class TestFormatDelta:
    """Test delta arrow to text conversion."""
    
    @pytest.mark.parametrize("input_arrow,expected_text", [
        ("↑", "rising"),
        ("→", "stable"),
        ("↓", "falling"),
    ])
    def test_converts_known_arrows(self, input_arrow, expected_text):
        assert format_delta(input_arrow) == expected_text
    
    def test_returns_original_for_unknown_values(self):
        assert format_delta("Unknown") == "Unknown"
        assert format_delta("") == ""


class TestFormatPriceTrend:
    """Test price trend arrow to text conversion."""
    
    @pytest.mark.parametrize("input_arrow,expected_text", [
        ("↑", "Rising"),
        ("→", "Stable"),
        ("↓", "Falling"),
    ])
    def test_converts_known_arrows(self, input_arrow, expected_text):
        assert format_price_trend(input_arrow) == expected_text
    
    def test_returns_original_for_unknown_values(self):
        assert format_price_trend("Unknown") == "Unknown"
        assert format_price_trend("") == ""

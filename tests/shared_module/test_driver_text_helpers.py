"""Tests for driver text helper functions."""
import pytest
from shared.driver_text_helpers import (
    format_wishlist_pressure,
    format_delta,
    format_price_trend,
    build_demand_section,
    build_price_section,
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


class TestBuildDemandSection:
    """Test demand section builder."""

    @pytest.mark.parametrize("pressure,delta,expected", [
        ("🔥", "↑", "Demand: Wishlist High + rising"),
        ("⚠️", "→", "Demand: Wishlist Moderate + stable"),
        ("❌", "↓", "Demand: Wishlist Low + falling"),
    ])
    def test_formats_known_values(self, pressure, delta, expected):
        assert build_demand_section(pressure, delta) == expected

    def test_falls_back_to_raw_values_for_unknown_inputs(self):
        assert build_demand_section("X", "Y") == "Demand: Wishlist X + Y"


class TestBuildPriceSection:
    """Test price section builder."""

    @pytest.mark.parametrize("price_trend,expected", [
        ("↑", "Price: Rising"),
        ("→", "Price: Stable"),
        ("↓", "Price: Falling"),
    ])
    def test_formats_known_values(self, price_trend, expected):
        assert build_price_section(price_trend) == expected

    def test_falls_back_to_raw_value_for_unknown_input(self):
        assert build_price_section("X") == "Price: X"

"""Tests for driver text helper functions."""
import pytest
from shared.driver_text_helpers import (
    format_wishlist_pressure,
    format_delta,
    format_price_trend,
    build_demand_section,
    build_price_section,
    build_drivers_text,
    lineage_driver_overrides,
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

    def test_qualifier_replaces_delta_suffix(self):
        """When qualifier is provided, it appears in parens instead of '+ delta'."""
        result = build_demand_section("🔥", "→", qualifier="momentum neutralized; continuity unconfirmed")
        assert result == "Demand: Wishlist High (momentum neutralized; continuity unconfirmed)"

    def test_qualifier_multi_variant(self):
        result = build_demand_section("🔥", "→", qualifier="active variants overlap; delta neutralized")
        assert result == "Demand: Wishlist High (active variants overlap; delta neutralized)"

    def test_empty_qualifier_uses_standard_format(self):
        """Passing an empty qualifier string falls back to the standard format."""
        assert build_demand_section("🔥", "↑", qualifier="") == "Demand: Wishlist High + rising"


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


class TestLineageDriverOverrides:
    """Test lineage_driver_overrides — centralised derivation of demand/price qualifiers."""

    def test_multi_variant_returns_both_overrides(self):
        demand_q, price_o = lineage_driver_overrides("multi-variant")
        assert demand_q == "active variants overlap; delta neutralized"
        assert price_o == "Price: Multiple active sizes"

    def test_ambiguous_transition_returns_demand_qualifier_only(self):
        demand_q, price_o = lineage_driver_overrides("ambiguous-transition")
        assert demand_q == "momentum neutralized; continuity unconfirmed"
        assert price_o == ""

    @pytest.mark.parametrize("status", ["none", "confirmed-transition", "", "unknown"])
    def test_no_override_for_other_statuses(self, status):
        demand_q, price_o = lineage_driver_overrides(status)
        assert demand_q == ""
        assert price_o == ""


class TestBuildDriversText:
    """Test combined drivers text builder."""

    def test_combines_stock_demand_and_price_sections(self):
        result = build_drivers_text(
            stock_section="Stock: Emerging (OOS 2 runs; currently OUT)",
            price_trend="→",
            wishlist_pressure="🔥",
            wishlist_delta="↑",
        )
        assert result == "Stock: Emerging (OOS 2 runs; currently OUT); Demand: Wishlist High + rising; Price: Stable"

    def test_simple_stock_section_no_detail(self):
        result = build_drivers_text(
            stock_section="Stock: Always Available",
            price_trend="↓",
            wishlist_pressure="❌",
            wishlist_delta="→",
        )
        assert result == "Stock: Always Available; Demand: Wishlist Low + stable; Price: Falling"

    def test_dealer_style_stock_section(self):
        result = build_drivers_text(
            stock_section="Stock: Reliability Low (Restock Slow)",
            price_trend="↑",
            wishlist_pressure="⚠️",
            wishlist_delta="↑",
        )
        assert result == "Stock: Reliability Low (Restock Slow); Demand: Wishlist Moderate + rising; Price: Rising"

    def test_demand_qualifier_replaces_delta_suffix(self):
        """demand_qualifier is forwarded to build_demand_section."""
        result = build_drivers_text(
            stock_section="Stock: Emerging (OOS 2 runs; currently OUT)",
            price_trend="→",
            wishlist_pressure="🔥",
            wishlist_delta="→",
            demand_qualifier="momentum neutralized; continuity unconfirmed",
        )
        assert result == (
            "Stock: Emerging (OOS 2 runs; currently OUT); "
            "Demand: Wishlist High (momentum neutralized; continuity unconfirmed); "
            "Price: Stable"
        )

    def test_price_override_replaces_price_section(self):
        """price_override replaces the Price section entirely."""
        result = build_drivers_text(
            stock_section="Stock: Always (currently IN)",
            price_trend="→",
            wishlist_pressure="🔥",
            wishlist_delta="→",
            price_override="Price: Multiple active sizes",
        )
        assert result == (
            "Stock: Always (currently IN); "
            "Demand: Wishlist High + stable; "
            "Price: Multiple active sizes"
        )

    def test_demand_qualifier_and_price_override_together(self):
        """Both overrides active simultaneously (multi-variant case)."""
        result = build_drivers_text(
            stock_section="Stock: Always (currently IN)",
            price_trend="→",
            wishlist_pressure="🔥",
            wishlist_delta="→",
            demand_qualifier="active variants overlap; delta neutralized",
            price_override="Price: Multiple active sizes",
        )
        assert result == (
            "Stock: Always (currently IN); "
            "Demand: Wishlist High (active variants overlap; delta neutralized); "
            "Price: Multiple active sizes"
        )

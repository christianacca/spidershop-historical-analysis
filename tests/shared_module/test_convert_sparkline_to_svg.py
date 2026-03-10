"""
Comprehensive tests for sparkline DTO conversion.

Tests cover all behavioral rules from docs/SPARKLINES.md (Part 2: SVG Sparklines)
using sparkline_to_dto (the successor to the deleted convert_sparkline_to_svg):
- Rule 1: Price/Wishlist show continuous bars (no gaps)
- Rule 2: Stock availability shows gaps for OUT periods
- Tooltip formatting with square brackets for carried-forward values
- Color coding based on trend direction
- Edge cases (empty, single value, flat lines)
"""

import pytest
from website.sparkline_dto import sparkline_to_dto


def _real_bars(dto: dict) -> list:
    """Return only the non-None (non-gap) bars from a DTO."""
    return [b for b in dto["bars"] if b is not None]


class TestBasicConversion:
    """Test basic DTO generation from Unicode characters."""

    def test_converts_single_bar(self):
        dto = sparkline_to_dto("\u2584", values=["15.00"], metric_type="price")
        assert dto is not None
        assert len(_real_bars(dto)) == 1
        assert _real_bars(dto)[0]["bar_height"] == pytest.approx(20.0)
        assert _real_bars(dto)[0]["tooltip"] == "\xa315.00"

    def test_converts_rising_trend(self):
        dto = sparkline_to_dto(
            "\u2581\u2583\u2585\u2587",
            values=["10.00", "12.00", "15.00", "18.00"],
            metric_type="price",
        )
        assert dto is not None
        bars = _real_bars(dto)
        assert len(bars) == 4
        assert bars[0]["bar_height"] == pytest.approx(12.0)
        assert bars[1]["bar_height"] == pytest.approx(14.0)
        assert bars[2]["bar_height"] == pytest.approx(17.0)
        assert bars[3]["bar_height"] == pytest.approx(20.0)

    def test_converts_all_eight_character_levels(self):
        dto = sparkline_to_dto(
            "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588",
            metric_type="stock",
        )
        assert dto is not None
        bars = _real_bars(dto)
        assert len(bars) == 8
        expected = [2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0]
        for bar, exp in zip(bars, expected):
            assert bar["bar_height"] == pytest.approx(exp)


class TestContinuousBars:
    """Test Rule 1: Price/Wishlist sparklines show continuous bars (no gaps)."""

    def test_price_sparkline_continuous_with_carryforward(self):
        unicode_str = "\u2583\u2586\u2586\u2586\u2586\u2587\u2588"
        values = ["12.00", "15.00", "15.00", "15.00", "15.00", "18.00", "20.00"]
        is_carried = [False, False, True, True, True, False, False]
        dto = sparkline_to_dto(unicode_str, values=values, metric_type="price", is_carried_forward=is_carried)
        assert dto is not None
        assert len(_real_bars(dto)) == 7
        tooltips = [b["tooltip"] for b in dto["bars"] if b is not None]
        assert "\xa312.00" in tooltips
        assert "\xa315.00" in tooltips
        assert tooltips.count("[\xa315.00]") == 3
        assert "\xa318.00" in tooltips
        assert "\xa320.00" in tooltips

    def test_wishlist_sparkline_continuous_with_carryforward(self):
        dto = sparkline_to_dto(
            "\u2581\u2583\u2583\u2587",
            values=["5", "7", "7", "12"],
            metric_type="wishlist",
            is_carried_forward=[False, False, True, False],
        )
        assert dto is not None
        bars = _real_bars(dto)
        assert len(bars) == 4
        tooltips = [b["tooltip"] for b in bars]
        assert "5 wishlists" in tooltips
        assert "7 wishlists" in tooltips
        assert "[7 wishlists]" in tooltips
        assert "12 wishlists" in tooltips

    def test_flat_line_all_carried_forward(self):
        dto = sparkline_to_dto(
            "\u2584\u2584\u2584\u2584",
            values=["20.00", "20.00", "20.00", "20.00"],
            metric_type="price",
            is_carried_forward=[False, True, True, True],
        )
        assert dto is not None
        bars = _real_bars(dto)
        assert len(bars) == 4
        for b in bars:
            assert b["bar_height"] == pytest.approx(20.0)
        tooltips = [b["tooltip"] for b in bars]
        assert "\xa320.00" in tooltips
        assert tooltips.count("[\xa320.00]") == 3


class TestStockAvailabilityGaps:
    """Test Rule 2: Stock sparklines show visual gaps for OUT periods."""

    def test_stock_sparkline_has_gaps(self):
        dto = sparkline_to_dto("\u2588\u2588  \u2588\u2588 ", metric_type="stock")
        assert dto is not None
        assert len(_real_bars(dto)) == 4
        assert dto["bars"][0] is not None
        assert dto["bars"][1] is not None
        assert dto["bars"][2] is None
        assert dto["bars"][3] is None
        assert dto["bars"][4] is not None
        assert dto["bars"][5] is not None
        assert dto["bars"][6] is None
        for b in _real_bars(dto):
            assert b["tooltip"] == "IN"

    def test_stock_sparkline_single_gap(self):
        dto = sparkline_to_dto("\u2588 \u2588", metric_type="stock")
        assert dto is not None
        assert len(dto["bars"]) == 3
        assert dto["bars"][1] is None
        assert len(_real_bars(dto)) == 2
        for b in _real_bars(dto):
            assert b["tooltip"] == "IN"

    def test_stock_sparkline_all_in_stock(self):
        dto = sparkline_to_dto("\u2588\u2588\u2588\u2588", metric_type="stock")
        assert dto is not None
        assert len(_real_bars(dto)) == 4
        for b in _real_bars(dto):
            assert b["tooltip"] == "IN"


class TestColorCoding:
    """Test color coding based on trend direction."""

    def test_uptrend_gets_green(self):
        dto = sparkline_to_dto(
            "\u2581\u2583\u2585\u2587\u2588",
            values=["10", "12", "15", "18", "20"],
            metric_type="price",
        )
        assert dto is not None
        for b in _real_bars(dto):
            assert b["fill"] == "#22c55e"

    def test_downtrend_gets_red(self):
        dto = sparkline_to_dto(
            "\u2588\u2587\u2585\u2583\u2581",
            values=["20", "18", "15", "12", "10"],
            metric_type="price",
        )
        assert dto is not None
        for b in _real_bars(dto):
            assert b["fill"] == "#ef4444"

    def test_flat_line_gets_blue(self):
        dto = sparkline_to_dto(
            "\u2584\u2584\u2584\u2584",
            values=["15", "15", "15", "15"],
            metric_type="price",
        )
        assert dto is not None
        for b in _real_bars(dto):
            assert b["fill"] == "#3b82f6"

    def test_flat_carried_forward_gets_blue(self):
        dto = sparkline_to_dto(
            "\u2586\u2586\u2586\u2586",
            values=["15.00", "15.00", "15.00", "15.00"],
            metric_type="price",
            is_carried_forward=[False, True, True, True],
        )
        assert dto is not None
        for b in _real_bars(dto):
            assert b["fill"] == "#3b82f6"

    def test_downtrend_with_carryforward_gets_red(self):
        dto = sparkline_to_dto(
            "\u2588\u2587\u2585\u2585\u2583",
            values=["20.00", "18.00", "15.00", "15.00", "12.00"],
            metric_type="price",
            is_carried_forward=[False, False, False, True, False],
        )
        assert dto is not None
        for b in _real_bars(dto):
            assert b["fill"] == "#ef4444"

    def test_uptrend_with_carryforward_gets_green(self):
        dto = sparkline_to_dto(
            "\u2581\u2583\u2583\u2585\u2588",
            values=["10.00", "12.00", "12.00", "15.00", "20.00"],
            metric_type="price",
            is_carried_forward=[False, False, True, False, False],
        )
        assert dto is not None
        for b in _real_bars(dto):
            assert b["fill"] == "#22c55e"

    def test_single_bar_gets_blue(self):
        dto = sparkline_to_dto("\u2584", values=["15.00"], metric_type="price")
        assert dto is not None
        assert _real_bars(dto)[0]["fill"] == "#3b82f6"

    def test_stock_availability_always_green(self):
        dto = sparkline_to_dto("\u2588 \u2588 \u2588", metric_type="stock")
        assert dto is not None
        for b in _real_bars(dto):
            assert b["fill"] == "#22c55e"


class TestTooltipFormatting:
    """Test tooltip content and formatting."""

    def test_price_tooltips_show_currency(self):
        dto = sparkline_to_dto(
            "\u2581\u2584\u2588",
            values=["10.00", "15.00", "20.00"],
            metric_type="price",
        )
        assert dto is not None
        tooltips = [b["tooltip"] for b in _real_bars(dto)]
        assert "\xa310.00" in tooltips
        assert "\xa315.00" in tooltips
        assert "\xa320.00" in tooltips

    def test_wishlist_tooltips_show_count(self):
        dto = sparkline_to_dto(
            "\u2581\u2584\u2588",
            values=["3", "5", "8"],
            metric_type="wishlist",
        )
        assert dto is not None
        tooltips = [b["tooltip"] for b in _real_bars(dto)]
        assert "3 wishlists" in tooltips
        assert "5 wishlists" in tooltips
        assert "8 wishlists" in tooltips

    def test_wishlist_singular_for_one(self):
        dto = sparkline_to_dto("\u2581", values=["1"], metric_type="wishlist")
        assert dto is not None
        assert _real_bars(dto)[0]["tooltip"] == "1 wishlist"

    def test_stock_with_values_array_provided(self):
        dto = sparkline_to_dto(
            "\u2588\u2588\u2588",
            values=["dummy1", "dummy2", "dummy3"],
            metric_type="stock",
        )
        assert dto is not None
        for b in _real_bars(dto):
            assert b["tooltip"] == "IN"

    def test_carried_forward_uses_square_brackets_price(self):
        dto = sparkline_to_dto(
            "\u2584\u2584\u2584",
            values=["15.00", "15.00", "15.00"],
            metric_type="price",
            is_carried_forward=[False, True, True],
        )
        assert dto is not None
        tooltips = [b["tooltip"] for b in _real_bars(dto)]
        assert "\xa315.00" in tooltips
        assert tooltips.count("[\xa315.00]") == 2

    def test_carried_forward_uses_square_brackets_wishlist(self):
        dto = sparkline_to_dto(
            "\u2583\u2583",
            values=["7", "7"],
            metric_type="wishlist",
            is_carried_forward=[False, True],
        )
        assert dto is not None
        tooltips = [b["tooltip"] for b in _real_bars(dto)]
        assert "7 wishlists" in tooltips
        assert "[7 wishlists]" in tooltips


class TestEdgeCases:
    """Test edge cases and invalid inputs."""

    def test_empty_string_returns_none(self):
        assert sparkline_to_dto("") is None

    def test_dash_returns_none(self):
        assert sparkline_to_dto("-") is None

    def test_whitespace_only_returns_none(self):
        assert sparkline_to_dto("   ", metric_type="stock") is None

    def test_unknown_characters_return_none(self):
        assert sparkline_to_dto("\u2581XYZ\u2584") is None

    def test_all_gaps_returns_none(self):
        assert sparkline_to_dto("     ", metric_type="stock") is None

    def test_stock_sparkline_without_values_succeeds(self):
        dto = sparkline_to_dto("\u2588\u2588 \u2588", metric_type="stock")
        assert dto is not None
        assert len(_real_bars(dto)) == 3
        for b in _real_bars(dto):
            assert b["tooltip"] == "IN"


class TestDtoMetadata:
    """Test DTO metadata fields (svg_width, svg_height, title)."""

    def test_svg_width_is_slots_times_ten(self):
        dto = sparkline_to_dto(
            "\u2581\u2583\u2585\u2587",
            metric_type="stock",
        )
        assert dto is not None
        assert dto["svg_width"] == 40

        dto_gap = sparkline_to_dto("\u2588 \u2588", metric_type="stock")
        assert dto_gap is not None
        assert dto_gap["svg_width"] == 30

    def test_svg_height_is_always_twenty(self):
        dto = sparkline_to_dto(
            "\u2581\u2583\u2585\u2587",
            metric_type="stock",
        )
        assert dto is not None
        assert dto["svg_height"] == 20

    def test_title_reflects_metric_type(self):
        dto_price = sparkline_to_dto("\u2584\u2584", values=["15", "15"], metric_type="price")
        dto_wish = sparkline_to_dto("\u2584\u2584", values=["5", "5"], metric_type="wishlist")
        dto_stock = sparkline_to_dto("\u2584\u2584", metric_type="stock")

        assert dto_price["title"] == "Price History"
        assert dto_wish["title"] == "Wishlist History"
        assert dto_stock["title"] == "Stock History"

    def test_bars_include_gap_slots(self):
        dto = sparkline_to_dto("\u2588 \u2588", metric_type="stock")
        assert dto is not None
        assert len(dto["bars"]) == 3
        assert dto["bars"][1] is None

    def test_bars_x_offsets_via_index(self):
        dto = sparkline_to_dto("\u2588 \u2588", metric_type="stock")
        assert dto is not None
        assert dto["bars"][0] is not None
        assert dto["bars"][1] is None
        assert dto["bars"][2] is not None


class TestComprehensiveScenarios:
    """Test complete scenarios from SPARKLINES.md (Part 2: SVG Sparklines)."""

    def test_price_rising_with_out_period(self):
        dto = sparkline_to_dto(
            "\u2581\u2584\u2584\u2584\u2588",
            values=["10.00", "12.00", "12.00", "12.00", "15.00"],
            metric_type="price",
            is_carried_forward=[False, False, True, True, False],
        )
        assert dto is not None
        bars = _real_bars(dto)
        assert len(bars) == 5
        for b in bars:
            assert b["fill"] == "#22c55e"
        tooltips = [b["tooltip"] for b in bars]
        assert "\xa310.00" in tooltips
        assert "\xa312.00" in tooltips
        assert tooltips.count("[\xa312.00]") == 2
        assert "\xa315.00" in tooltips

    def test_flat_price_during_out(self):
        dto = sparkline_to_dto(
            "\u2584\u2584\u2584\u2584\u2584\u2584",
            values=["20.00", "20.00", "20.00", "20.00", "20.00", "20.00"],
            metric_type="price",
            is_carried_forward=[False, False, True, True, True, False],
        )
        assert dto is not None
        bars = _real_bars(dto)
        assert len(bars) == 6
        for b in bars:
            assert b["fill"] == "#3b82f6"
        tooltips = [b["tooltip"] for b in bars]
        assert tooltips.count("\xa320.00") == 3
        assert tooltips.count("[\xa320.00]") == 3

    def test_stock_with_gaps(self):
        dto = sparkline_to_dto("\u2588\u2588  \u2588", metric_type="stock")
        assert dto is not None
        assert len(_real_bars(dto)) == 3
        for b in _real_bars(dto):
            assert b["fill"] == "#22c55e"
            assert b["tooltip"] == "IN"

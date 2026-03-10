"""Phase A — DTO contract tests (RED phase).

Tests for sparkline_to_dto and build_sparkline_dto_rows.
These functions do not exist yet — every test fails with ImportError until Phase B.

Formula for price/wishlist bar heights (zero-based normalization):
    bar_height = (0.1 + (val / max_val) * 0.9) * 20
    where max_val = max(values), min is always 0

Formula for stock bar heights (unicode level):
    bar_height = (level / 8) * 20
    where level = SPARKLINE_CHARS[char] (1–8)

Opacity gradient:
    opacity = 0.7 + (i / len(bars)) * 0.3
    where i = 0-indexed position in full bars list (including None gap slots)
"""

import pytest
from website.sparkline_dto import sparkline_to_dto, build_sparkline_dto_rows


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_by_run():
    """Minimal historical data: Brachypelma hamorii 1.5cm over 3 runs."""
    by_run = {
        "2024-01-01 10:00:00": [
            {
                "scientific_name": "Brachypelma hamorii",
                "size_cm": "1.5",
                "price_gbp": "10.00",
                "wishlist_count": "2",
                "common_name": "Mexican Red Knee",
                "page_url": "https://example.com/brachypelma-hamorii",
            }
        ],
        "2024-01-08 10:00:00": [
            {
                "scientific_name": "Brachypelma hamorii",
                "size_cm": "1.5",
                "price_gbp": "15.00",
                "wishlist_count": "4",
                "common_name": "Mexican Red Knee",
                "page_url": "https://example.com/brachypelma-hamorii",
            }
        ],
        "2024-01-15 10:00:00": [
            {
                "scientific_name": "Brachypelma hamorii",
                "size_cm": "1.5",
                "price_gbp": "20.00",
                "wishlist_count": "7",
                "common_name": "Mexican Red Knee",
                "page_url": "https://example.com/brachypelma-hamorii",
            }
        ],
    }
    runs = sorted(by_run.keys())
    return by_run, runs


# ---------------------------------------------------------------------------
# TestBarHeightPrice
# ---------------------------------------------------------------------------

class TestBarHeightPrice:
    """Bar heights for price sparklines use zero-based proportional normalization."""

    def test_single_bar_max_value(self):
        """Single bar: value equals max, so bar height == full 20px."""
        dto = sparkline_to_dto("▄", ["15.00"], "price", [False])

        assert dto is not None
        assert dto["bars"][0]["bar_height"] == pytest.approx(20.0)

    def test_two_bars_proportional(self):
        """Two bars: 10/20 = 50% → bar_height = (0.1 + 0.5*0.9)*20 = 11.0."""
        dto = sparkline_to_dto("▁█", ["10.00", "20.00"], "price", [False, False])

        assert dto is not None
        assert dto["bars"][0]["bar_height"] == pytest.approx(11.0)
        assert dto["bars"][1]["bar_height"] == pytest.approx(20.0)

    def test_zero_based_normalization_floor(self):
        """Value of 0 hits the 10% floor: bar_height = 0.1 * 20 = 2.0px.

        The 0.1 floor ensures every bar is visible even when the value is zero.
        With zero-based normalization (min_val=0), val=0 / max_val=10 → normalized=0
        → bar_height = (0.1 + 0 * 0.9) * 20 = 2.0.
        """
        dto = sparkline_to_dto("▁█", ["0.00", "10.00"], "price", [False, False])

        assert dto is not None
        assert dto["bars"][0]["bar_height"] == pytest.approx(2.0)
        assert dto["bars"][1]["bar_height"] == pytest.approx(20.0)

    def test_flat_values_all_same_height(self):
        """Flat price line: all bars get full height (val/max = 1.0 for all)."""
        dto = sparkline_to_dto("▄▄▄", ["15.00", "15.00", "15.00"], "price", [False, False, False])

        assert dto is not None
        heights = [bar["bar_height"] for bar in dto["bars"]]
        assert all(h == pytest.approx(heights[0]) for h in heights)


# ---------------------------------------------------------------------------
# TestBarHeightStock
# ---------------------------------------------------------------------------

class TestBarHeightStock:
    """Bar heights for stock sparklines come from the Unicode character level (1–8)."""

    def test_stock_bar_heights_from_unicode_level(self):
        """▁ → level 1 → 2.5px, ▄ → level 4 → 10.0px, █ → level 8 → 20.0px."""
        dto = sparkline_to_dto("▁▄█", None, "stock", None)

        assert dto is not None
        assert dto["bars"][0]["bar_height"] == pytest.approx(2.5)   # 1/8 * 20
        assert dto["bars"][1]["bar_height"] == pytest.approx(10.0)  # 4/8 * 20
        assert dto["bars"][2]["bar_height"] == pytest.approx(20.0)  # 8/8 * 20


# ---------------------------------------------------------------------------
# TestGaps
# ---------------------------------------------------------------------------

class TestGaps:
    """Stock sparklines have None gap slots; price/wishlist never have gaps."""

    def test_stock_space_produces_none_in_bars(self):
        """Space character in stock sparkline → None at that index in bars list."""
        dto = sparkline_to_dto("█ █", None, "stock", None)

        assert dto is not None
        assert dto["bars"][0] is not None
        assert dto["bars"][1] is None     # gap slot
        assert dto["bars"][2] is not None

    def test_gap_slot_counts_toward_svg_width(self):
        """Gap slots still advance the x-position; svg_width = len(bars) * 10."""
        dto = sparkline_to_dto("█ █", None, "stock", None)

        assert dto is not None
        assert len(dto["bars"]) == 3
        assert dto["svg_width"] == 30     # 3 slots × 10px

    def test_price_sparklines_have_no_none_gaps(self):
        """Price sparklines carry forward values through OUT periods — no None gaps."""
        dto = sparkline_to_dto("▃▆▆▆▇", ["10.00", "15.00", "15.00", "15.00", "18.00"], "price",
                               [False, False, True, True, False])

        assert dto is not None
        assert all(bar is not None for bar in dto["bars"])


# ---------------------------------------------------------------------------
# TestColors
# ---------------------------------------------------------------------------

class TestColors:
    """Fill color is determined by trend direction based on Unicode bar levels."""

    def test_rising_trend_gets_green(self):
        """Unicode levels rise by > 1 (▁█: 1→8) → green #22c55e."""
        dto = sparkline_to_dto("▁█", ["10.00", "20.00"], "price", [False, False])

        assert dto is not None
        assert dto["bars"][0]["fill"] == "#22c55e"
        assert dto["bars"][1]["fill"] == "#22c55e"

    def test_falling_trend_gets_red(self):
        """Unicode levels fall by > 1 (█▁: 8→1) → red #ef4444."""
        dto = sparkline_to_dto("█▁", ["20.00", "10.00"], "price", [False, False])

        assert dto is not None
        assert dto["bars"][0]["fill"] == "#ef4444"

    def test_stable_flat_gets_blue(self):
        """Equal unicode levels (▄▄: 4→4) → blue #3b82f6."""
        dto = sparkline_to_dto("▄▄", ["15.00", "15.00"], "price", [False, False])

        assert dto is not None
        assert dto["bars"][0]["fill"] == "#3b82f6"

    def test_all_carry_forward_after_first_gets_blue(self):
        """Rising unicode levels but all bars after first are carry-forward → blue (no real change)."""
        dto = sparkline_to_dto("▁█", ["10.00", "20.00"], "price", [False, True])

        assert dto is not None
        assert dto["bars"][0]["fill"] == "#3b82f6"

    def test_stock_always_green(self):
        """Stock sparklines are always green regardless of bar heights."""
        dto = sparkline_to_dto("▁▄█", None, "stock", None)

        assert dto is not None
        for bar in dto["bars"]:
            if bar is not None:
                assert bar["fill"] == "#22c55e"


# ---------------------------------------------------------------------------
# TestTooltips
# ---------------------------------------------------------------------------

class TestTooltips:
    """Tooltip text is formatted per metric type and carry-forward status."""

    def test_price_real_bar(self):
        """Real price bar: plain £ notation without brackets."""
        dto = sparkline_to_dto("▄", ["15.00"], "price", [False])

        assert dto is not None
        assert dto["bars"][0]["tooltip"] == "£15.00"

    def test_price_carry_forward_bar(self):
        """Carry-forward price bar: wrapped in square brackets."""
        dto = sparkline_to_dto("▄▄", ["15.00", "15.00"], "price", [False, True])

        assert dto is not None
        assert dto["bars"][1]["tooltip"] == "[£15.00]"

    def test_wishlist_singular(self):
        """Wishlist count of 1 uses singular 'wishlist' (no 's')."""
        dto = sparkline_to_dto("▄", ["1"], "wishlist", [False])

        assert dto is not None
        assert dto["bars"][0]["tooltip"] == "1 wishlist"

    def test_wishlist_plural(self):
        """Wishlist count != 1 uses plural 'wishlists'."""
        dto = sparkline_to_dto("▄", ["7"], "wishlist", [False])

        assert dto is not None
        assert dto["bars"][0]["tooltip"] == "7 wishlists"

    def test_wishlist_carry_forward(self):
        """Carry-forward wishlist bar: count and label wrapped in square brackets."""
        dto = sparkline_to_dto("▄▄", ["7", "7"], "wishlist", [False, True])

        assert dto is not None
        assert dto["bars"][1]["tooltip"] == "[7 wishlists]"

    def test_stock_tooltip_is_in(self):
        """Stock bars always have tooltip 'IN' (gap slots have no tooltip)."""
        dto = sparkline_to_dto("█▄", None, "stock", None)

        assert dto is not None
        for bar in dto["bars"]:
            if bar is not None:
                assert bar["tooltip"] == "IN"


# ---------------------------------------------------------------------------
# TestOpacity
# ---------------------------------------------------------------------------

class TestOpacity:
    """Opacity gradient: 0.7 at position 0, increasing to approach 1.0 at last bar."""

    def test_opacity_increases_across_bars(self):
        """Later bars are more opaque than earlier bars."""
        dto = sparkline_to_dto("▁▄▄█", ["5.00", "10.00", "10.00", "20.00"], "price",
                               [False, False, False, False])

        assert dto is not None
        assert len(dto["bars"]) == 4
        assert dto["bars"][0]["opacity"] < dto["bars"][-1]["opacity"]

    def test_first_bar_opacity_is_0_7(self):
        """First bar opacity is always 0.7 (position 0 in gradient)."""
        dto = sparkline_to_dto("▁▄▄█", ["5.00", "10.00", "10.00", "20.00"], "price",
                               [False, False, False, False])

        assert dto is not None
        assert dto["bars"][0]["opacity"] == pytest.approx(0.7, abs=0.01)

    def test_last_bar_opacity_less_than_one(self):
        """Last bar opacity approaches 1.0 but never reaches it with this formula."""
        dto = sparkline_to_dto("▁▄▄█", ["5.00", "10.00", "10.00", "20.00"], "price",
                               [False, False, False, False])

        assert dto is not None
        assert dto["bars"][-1]["opacity"] < 1.0
        # For 4 bars: 0.7 + (3/4)*0.3 = 0.925
        assert dto["bars"][-1]["opacity"] == pytest.approx(0.925, abs=0.01)


# ---------------------------------------------------------------------------
# TestSvgMeta
# ---------------------------------------------------------------------------

class TestSvgMeta:
    """svg_width, svg_height, and title fields are correctly computed."""

    def test_svg_width_is_bar_count_times_10(self):
        """svg_width = total number of bar slots (including gaps) × 10px."""
        dto = sparkline_to_dto("▁▄█", ["10.00", "15.00", "20.00"], "price",
                               [False, False, False])

        assert dto is not None
        assert dto["svg_width"] == len(dto["bars"]) * 10

    def test_svg_width_includes_gap_slots(self):
        """svg_width counts gap slots (None entries) as full slots."""
        dto = sparkline_to_dto("█ █", None, "stock", None)

        assert dto is not None
        assert len(dto["bars"]) == 3
        assert dto["svg_width"] == 30

    def test_svg_height_is_20(self):
        """svg_height is always 20px."""
        dto = sparkline_to_dto("▄", ["15.00"], "price", [False])

        assert dto is not None
        assert dto["svg_height"] == 20

    def test_price_title(self):
        """Price metric produces 'Price History' title."""
        dto = sparkline_to_dto("▄", ["15.00"], "price", [False])

        assert dto is not None
        assert dto["title"] == "Price History"

    def test_wishlist_title(self):
        """Wishlist metric produces 'Wishlist History' title."""
        dto = sparkline_to_dto("▄", ["7"], "wishlist", [False])

        assert dto is not None
        assert dto["title"] == "Wishlist History"

    def test_stock_title(self):
        """Stock metric produces 'Stock History' title."""
        dto = sparkline_to_dto("█", None, "stock", None)

        assert dto is not None
        assert dto["title"] == "Stock History"


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Boundary conditions: empty input, dash, single bar, no values for stock."""

    def test_empty_string_returns_none(self):
        """Empty unicode sparkline → None (no DTO produced)."""
        assert sparkline_to_dto("", None, "stock", None) is None

    def test_dash_returns_none(self):
        """Dash placeholder '-' → None (no DTO produced)."""
        assert sparkline_to_dto("-", None, "stock", None) is None

    def test_single_bar_produces_valid_dto(self):
        """Single bar sparkline produces a DTO with one entry in bars."""
        dto = sparkline_to_dto("▄", ["15.00"], "price", [False])

        assert dto is not None
        assert len(dto["bars"]) == 1
        assert dto["bars"][0] is not None

    def test_stock_requires_no_values_arg(self):
        """Stock sparklines don't need values — None is acceptable."""
        dto = sparkline_to_dto("▁▄█", None, "stock", None)

        assert dto is not None
        assert len(dto["bars"]) == 3


# ---------------------------------------------------------------------------
# TestBuildSparklineDtoRows
# ---------------------------------------------------------------------------

class TestBuildSparklineDtoRows:
    """Integration: build_sparkline_dto_rows converts sparkline cells to DTO dicts."""

    def test_sparkline_cells_become_dto_dicts(self):
        """Species with historical data: sparkline cells are replaced with DTO dicts."""
        headers = ["Species", "Size (cm)", "Price History"]
        rows = [["Brachypelma hamorii", "1.5", "▁▄█"]]
        by_run, runs = _minimal_by_run()

        result = build_sparkline_dto_rows(headers, rows, (by_run, runs),
                                          "breeder_opportunity_table.csv")

        assert len(result) == 1
        price_history_cell = result[0][2]
        assert isinstance(price_history_cell, dict)
        assert "bars" in price_history_cell
        assert "svg_width" in price_history_cell
        assert "svg_height" in price_history_cell
        assert "title" in price_history_cell

    def test_non_sparkline_cells_pass_through_unchanged(self):
        """Non-sparkline columns are returned as original strings."""
        headers = ["Species", "Size (cm)", "Price History"]
        rows = [["Brachypelma hamorii", "1.5", "▁▄█"]]
        by_run, runs = _minimal_by_run()

        result = build_sparkline_dto_rows(headers, rows, (by_run, runs),
                                          "breeder_opportunity_table.csv")

        assert result[0][0] == "Brachypelma hamorii"
        assert result[0][1] == "1.5"

    def test_species_without_history_stays_unicode(self):
        """Species not found in historical data keeps original unicode sparkline string."""
        headers = ["Species", "Size (cm)", "Price History"]
        rows = [
            ["Brachypelma hamorii", "1.5", "▁▄█"],   # has history
            ["Unknown arachnid", "2.0", "▄▄▄"],        # no history
        ]
        by_run, runs = _minimal_by_run()

        result = build_sparkline_dto_rows(headers, rows, (by_run, runs),
                                          "breeder_opportunity_table.csv")

        # Species with history → DTO dict
        assert isinstance(result[0][2], dict)
        # Species without history → original unicode string
        assert result[1][2] == "▄▄▄"

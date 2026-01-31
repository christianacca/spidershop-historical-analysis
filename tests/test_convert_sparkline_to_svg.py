"""
Comprehensive tests for SVG sparkline conversion.

Tests cover all behavioral rules from docs/SPARKLINES.md (Part 2: SVG Sparklines):
- Rule 1: Price/Wishlist show continuous bars (no gaps)
- Rule 2: Stock availability shows gaps for OUT periods
- Tooltip formatting with square brackets for carried-forward values
- Color coding based on trend direction
- Edge cases (empty, single value, flat lines)
"""

import pytest
from website.sparkline_conversion import convert_sparkline_to_svg


class TestBasicConversion:
    """Test basic SVG generation from Unicode characters."""
    
    def test_converts_single_bar(self):
        """Single bar renders as SVG with proportional height."""
        svg = convert_sparkline_to_svg("▄", values=["15.00"], metric_type="price")
        
        assert '<svg' in svg
        assert '<rect' in svg
        # Single value: 15/15 = 100% → 10% + 100%*90% = 100% → 20.0px
        assert 'height="20.0"' in svg
        assert '<title>£15.00</title>' in svg
    
    def test_converts_rising_trend(self):
        """Rising trend generates multiple bars with increasing heights."""
        svg = convert_sparkline_to_svg("▁▃▅▇", values=["10.00", "12.00", "15.00", "18.00"], metric_type="price")
        
        assert '<svg' in svg
        assert svg.count('<rect') == 4
        # Heights are proportional to values (zero-based: 0-18 range)
        assert 'height="12.0"' in svg  # 10.00: 10/18 = 56% → 10% + 56%*90% = 60% → 12.0px
        assert 'height="14.0"' in svg  # 12.00: 12/18 = 67% → 10% + 67%*90% = 70% → 14.0px
        assert 'height="17.0"' in svg  # 15.00: 15/18 = 83% → 10% + 83%*90% = 85% → 17.0px
        assert 'height="20.0"' in svg  # 18.00: 18/18 = 100% → 100% → 20.0px
    
    def test_converts_all_eight_character_levels(self):
        """All 8 Unicode sparkline characters map to correct heights."""
        unicode = "▁▂▃▄▅▆▇█"
        svg = convert_sparkline_to_svg(unicode, metric_type="stock")
        
        # Heights: 1/8, 2/8, 3/8, 4/8, 5/8, 6/8, 7/8, 8/8 * 20
        assert 'height="2.5"' in svg   # ▁ (1/8) * 20 = 2.5
        assert 'height="5.0"' in svg   # ▂ (2/8) * 20 = 5.0
        assert 'height="7.5"' in svg   # ▃ (3/8) * 20 = 7.5
        assert 'height="10.0"' in svg  # ▄ (4/8) * 20 = 10.0
        assert 'height="12.5"' in svg  # ▅ (5/8) * 20 = 12.5
        assert 'height="15.0"' in svg  # ▆ (6/8) * 20 = 15.0
        assert 'height="17.5"' in svg  # ▇ (7/8) * 20 = 17.5
        assert 'height="20.0"' in svg  # █ (8/8) * 20 = 20.0


class TestContinuousBars:
    """Test Rule 1: Price/Wishlist sparklines show continuous bars (no gaps)."""
    
    def test_price_sparkline_continuous_with_carryforward(self):
        """Price sparklines show all bars continuously, even during OUT periods."""
        # Scenario: £12, £15, OUT, OUT, OUT, £18, £20
        # Unicode: ▃▆▆▆▆▇█ (carried forward creates plateau)
        unicode = "▃▆▆▆▆▇█"
        values = ["12.00", "15.00", "15.00", "15.00", "15.00", "18.00", "20.00"]
        is_carried = [False, False, True, True, True, False, False]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="price", is_carried_forward=is_carried)
        
        # Should have 7 bars (continuous, no gaps)
        assert svg.count('<rect') == 7
        
        # Check actual value tooltips
        assert '<title>£12.00</title>' in svg
        assert '<title>£15.00</title>' in svg
        
        # Check carried-forward value tooltips (square brackets)
        assert '<title>[£15.00]</title>' in svg
        assert svg.count('<title>[£15.00]</title>') == 3  # Three carried-forward instances
        
        # Final values
        assert '<title>£18.00</title>' in svg
        assert '<title>£20.00</title>' in svg
    
    def test_wishlist_sparkline_continuous_with_carryforward(self):
        """Wishlist sparklines show all bars continuously with square bracket notation."""
        unicode = "▁▃▃▇"
        values = ["5", "7", "7", "12"]
        is_carried = [False, False, True, False]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="wishlist", is_carried_forward=is_carried)
        
        # 4 continuous bars
        assert svg.count('<rect') == 4
        
        # Check tooltips
        assert '<title>5 wishlists</title>' in svg
        assert '<title>7 wishlists</title>' in svg
        assert '<title>[7 wishlists]</title>' in svg  # Carried forward
        assert '<title>12 wishlists</title>' in svg
    
    def test_flat_line_all_carried_forward(self):
        """Flat line from all carried-forward values shows continuous bars."""
        unicode = "▄▄▄▄"
        values = ["20.00", "20.00", "20.00", "20.00"]
        is_carried = [False, True, True, True]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="price", is_carried_forward=is_carried)
        
        # 4 bars, all same height (zero-based: 20/20 = 100% → full height)
        assert svg.count('<rect') == 4
        assert svg.count('height="20.0"') == 4
        
        # First is actual, rest are carried
        assert '<title>£20.00</title>' in svg
        assert svg.count('<title>[£20.00]</title>') == 3


class TestStockAvailabilityGaps:
    """Test Rule 2: Stock sparklines show visual gaps for OUT periods."""
    
    def test_stock_sparkline_has_gaps(self):
        """Stock availability sparklines have gaps (spaces) for OUT periods."""
        # Scenario: IN, IN, OUT, OUT, IN, IN, OUT
        # Unicode: "██  ██ " (spaces represent gaps)
        unicode = "██  ██ "
        
        svg = convert_sparkline_to_svg(unicode, metric_type="stock")
        
        # Should have only 4 bars (positions 0,1,4,5)
        # Positions 2,3,6 are spaces (gaps) - no bars
        assert svg.count('<rect') == 4
        
        # All tooltips should say "IN"
        assert svg.count('<title>IN</title>') == 4
    
    def test_stock_sparkline_single_gap(self):
        """Single OUT period creates one gap in stock sparkline."""
        unicode = "█ █"
        
        svg = convert_sparkline_to_svg(unicode, metric_type="stock")
        
        # 2 bars (positions 0 and 2), position 1 is gap
        assert svg.count('<rect') == 2
        assert svg.count('<title>IN</title>') == 2
    
    def test_stock_sparkline_all_in_stock(self):
        """All IN-stock periods show continuous bars (no gaps needed)."""
        unicode = "████"
        
        svg = convert_sparkline_to_svg(unicode, metric_type="stock")
        
        # 4 continuous bars
        assert svg.count('<rect') == 4
        assert svg.count('<title>IN</title>') == 4


class TestColorCoding:
    """Test color coding based on trend direction."""
    
    def test_uptrend_gets_green(self):
        """Rising trend (last > first) gets green color."""
        svg = convert_sparkline_to_svg("▁▃▅▇█", values=["10", "12", "15", "18", "20"], metric_type="price")
        
        # Green: #22c55e
        assert 'fill="#22c55e"' in svg
    
    def test_downtrend_gets_red(self):
        """Falling trend (last < first) gets red color."""
        svg = convert_sparkline_to_svg("█▇▅▃▁", values=["20", "18", "15", "12", "10"], metric_type="price")
        
        # Red: #ef4444
        assert 'fill="#ef4444"' in svg
    
    def test_flat_line_gets_blue(self):
        """Flat line (no change) gets blue color."""
        svg = convert_sparkline_to_svg("▄▄▄▄", values=["15", "15", "15", "15"], metric_type="price")
        
        # Blue: #3b82f6
        assert 'fill="#3b82f6"' in svg
    
    def test_flat_carried_forward_gets_blue(self):
        """Flat line from carry-forward gets blue (neutral), not gray."""
        unicode = "▆▆▆▆"
        values = ["15.00", "15.00", "15.00", "15.00"]
        is_carried = [False, True, True, True]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="price", is_carried_forward=is_carried)
        
        # Should be blue (neutral) since no actual change occurred
        assert 'fill="#3b82f6"' in svg
        # Should NOT be gray
        assert 'fill="#888"' not in svg
    
    def test_downtrend_with_carryforward_gets_red(self):
        """Downtrend with carried-forward values still gets red color."""
        unicode = "█▇▅▅▃"
        values = ["20.00", "18.00", "15.00", "15.00", "12.00"]
        is_carried = [False, False, False, True, False]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="price", is_carried_forward=is_carried)
        
        # Should be red (downtrend) despite carried-forward value
        assert 'fill="#ef4444"' in svg
    
    def test_uptrend_with_carryforward_gets_green(self):
        """Uptrend with carried-forward values still gets green color."""
        unicode = "▁▃▃▅█"
        values = ["10.00", "12.00", "12.00", "15.00", "20.00"]
        is_carried = [False, False, True, False, False]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="price", is_carried_forward=is_carried)
        
        # Should be green (uptrend) despite carried-forward value
        assert 'fill="#22c55e"' in svg
    
    def test_single_bar_gets_blue(self):
        """Single bar gets neutral color (blue)."""
        svg = convert_sparkline_to_svg("▄", values=["15.00"], metric_type="price")
        
        assert 'fill="#3b82f6"' in svg
    
    def test_stock_availability_always_green(self):
        """Stock availability bars are always green (for IN-stock periods)."""
        svg = convert_sparkline_to_svg("█ █ █", metric_type="stock")
        
        # Green: #22c55e
        assert 'fill="#22c55e"' in svg
        # Should NOT have red or blue
        assert 'fill="#ef4444"' not in svg
        assert 'fill="#3b82f6"' not in svg


class TestTooltipFormatting:
    """Test tooltip content and formatting."""
    
    def test_price_tooltips_show_currency(self):
        """Price tooltips show £ symbol with 2 decimals."""
        svg = convert_sparkline_to_svg("▁▄█", values=["10.00", "15.00", "20.00"], metric_type="price")
        
        assert '<title>£10.00</title>' in svg
        assert '<title>£15.00</title>' in svg
        assert '<title>£20.00</title>' in svg
    
    def test_wishlist_tooltips_show_count(self):
        """Wishlist tooltips show number with 'wishlists' label."""
        svg = convert_sparkline_to_svg("▁▄█", values=["3", "5", "8"], metric_type="wishlist")
        
        assert '<title>3 wishlists</title>' in svg
        assert '<title>5 wishlists</title>' in svg
        assert '<title>8 wishlists</title>' in svg
    
    def test_wishlist_singular_for_one(self):
        """Wishlist tooltip uses singular 'wishlist' for count of 1."""
        svg = convert_sparkline_to_svg("▁", values=["1"], metric_type="wishlist")
        
        assert '<title>1 wishlist</title>' in svg
    
    def test_stock_with_values_array_provided(self):
        """Stock sparklines with values array still show 'IN' tooltips."""
        unicode = "███"
        # Even if values provided, stock sparklines ignore them
        values = ["dummy1", "dummy2", "dummy3"]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="stock")
        
        # Should still show "IN" tooltips, not the dummy values
        assert svg.count('<title>IN</title>') == 3
    
    def test_carried_forward_uses_square_brackets_price(self):
        """Carried-forward price values use square bracket notation."""
        unicode = "▄▄▄"
        values = ["15.00", "15.00", "15.00"]
        is_carried = [False, True, True]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="price", is_carried_forward=is_carried)
        
        # First is actual, next two are carried
        assert '<title>£15.00</title>' in svg
        assert svg.count('<title>[£15.00]</title>') == 2
    
    def test_carried_forward_uses_square_brackets_wishlist(self):
        """Carried-forward wishlist values use square bracket notation."""
        unicode = "▃▃"
        values = ["7", "7"]
        is_carried = [False, True]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="wishlist", is_carried_forward=is_carried)
        
        assert '<title>7 wishlists</title>' in svg
        assert '<title>[7 wishlists]</title>' in svg



class TestEdgeCases:
    """Test edge cases and invalid inputs."""
    
    def test_empty_string_returns_unchanged(self):
        """Empty string is not converted."""
        assert convert_sparkline_to_svg("") == ""
    
    def test_dash_returns_unchanged(self):
        """Dash character is not converted."""
        assert convert_sparkline_to_svg("-") == "-"
    
    def test_whitespace_only_returns_dash(self):
        """Whitespace-only string (all gaps) returns dash since no bars can be rendered."""
        result = convert_sparkline_to_svg("   ")
        # All spaces = all gaps = no bars = returns dash
        assert result == "-"
    
    def test_unknown_characters_return_unchanged(self):
        """Unknown characters cause fallback to original string."""
        result = convert_sparkline_to_svg("▁XYZ▄")
        assert result == "▁XYZ▄"
    
    def test_all_gaps_returns_dash(self):
        """All space characters (no bars) returns dash."""
        # String with only spaces (all gaps, no bars to render)
        result = convert_sparkline_to_svg("     ", metric_type="stock")
        # Should return dash since no bars can be rendered
        assert result == "-"
    
    def test_price_sparkline_without_values_fails(self):
        """Price sparklines require values - fail fast if missing."""
        with pytest.raises(AssertionError, match="Values required for price sparklines"):
            convert_sparkline_to_svg("▁▃▅▇", values=None, metric_type="price")
    
    def test_wishlist_sparkline_without_values_fails(self):
        """Wishlist sparklines require values - fail fast if missing."""
        with pytest.raises(AssertionError, match="Values required for wishlist sparklines"):
            convert_sparkline_to_svg("▁▃▅▇", values=None, metric_type="wishlist")
    
    def test_price_sparkline_with_empty_values_fails(self):
        """Price sparklines require non-empty values array."""
        with pytest.raises(AssertionError, match="Values array cannot be empty"):
            convert_sparkline_to_svg("▁▃▅▇", values=[], metric_type="price")
    
    def test_price_sparkline_with_invalid_values_fails(self):
        """Price sparklines require numeric values - fail fast on invalid data."""
        with pytest.raises(AssertionError, match="Invalid non-numeric value"):
            convert_sparkline_to_svg("▁▃▅▇", values=["10", "abc", "15", "20"], metric_type="price")
    
    def test_stock_sparkline_without_values_succeeds(self):
        """Stock sparklines don't require values (uses Unicode heights)."""
        svg = convert_sparkline_to_svg("██ █", metric_type="stock")
        assert '<svg' in svg
        assert '<rect' in svg
        assert '<title>IN</title>' in svg


class TestSVGStructure:
    """Test SVG structural elements."""
    
    def test_svg_has_correct_dimensions(self):
        """SVG viewBox and dimensions calculated correctly."""
        # 4 bars × 10px spacing = 40px width, 20px height
        svg = convert_sparkline_to_svg("▁▃▅▇", metric_type="stock")
        
        assert 'width="40"' in svg
        assert 'height="20"' in svg
        assert 'viewBox="0 0 40 20"' in svg
    
    def test_bars_positioned_correctly(self):
        """Bars positioned at correct X coordinates with spacing."""
        svg = convert_sparkline_to_svg("▁▃▅", metric_type="stock")
        
        # Bar 0 at x=0, Bar 1 at x=10, Bar 2 at x=20
        assert 'x="0"' in svg
        assert 'x="10"' in svg
        assert 'x="20"' in svg
    
    def test_bar_width_is_eight_pixels(self):
        """All bars have width of 8 pixels."""
        svg = convert_sparkline_to_svg("▁▃▅▇", metric_type="stock")
        
        assert svg.count('width="8"') == 4
    
    def test_svg_has_overall_title(self):
        """SVG element has descriptive title based on metric type."""
        svg_price = convert_sparkline_to_svg("▄▄", values=["15", "15"], metric_type="price")
        svg_wishlist = convert_sparkline_to_svg("▄▄", values=["5", "5"], metric_type="wishlist")
        svg_stock = convert_sparkline_to_svg("▄▄", metric_type="stock")
        
        assert '<title>Price History</title>' in svg_price
        assert '<title>Wishlist History</title>' in svg_wishlist
        assert '<title>Stock History</title>' in svg_stock

class TestComprehensiveScenarios:
    """Test complete scenarios from SPARKLINES.md (Part 2: SVG Sparklines)."""
    
    def test_price_rising_with_out_period(self):
        """Scenario: Price rising with OUT period in middle."""
        # Weeks: £10, £12, OUT, OUT, £15
        # Bars: ▁▄▄▄█ (continuous)
        unicode = "▁▄▄▄█"
        values = ["10.00", "12.00", "12.00", "12.00", "15.00"]
        is_carried = [False, False, True, True, False]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="price", is_carried_forward=is_carried)
        
        # 5 continuous bars
        assert svg.count('<rect') == 5
        
        # Uptrend color (green)
        assert 'fill="#22c55e"' in svg
        
        # Tooltips
        assert '<title>£10.00</title>' in svg
        assert '<title>£12.00</title>' in svg
        assert svg.count('<title>[£12.00]</title>') == 2
        assert '<title>£15.00</title>' in svg
    
    def test_flat_price_during_out(self):
        """Scenario: Flat price during OUT period."""
        # Weeks: £20, £20, OUT, OUT, OUT, £20
        # Bars: ▄▄▄▄▄▄ (continuous, all same height)
        unicode = "▄▄▄▄▄▄"
        values = ["20.00", "20.00", "20.00", "20.00", "20.00", "20.00"]
        # First actual, second actual, then 3 carried, then final actual
        is_carried = [False, False, True, True, True, False]
        
        svg = convert_sparkline_to_svg(unicode, values=values, metric_type="price", is_carried_forward=is_carried)
        
        # 6 continuous bars
        assert svg.count('<rect') == 6
        
        # Neutral color (blue) - no real change
        assert 'fill="#3b82f6"' in svg
        
        # Tooltips: First two actual (£20 both times), middle 3 carried, last actual
        # So we expect 3 instances of '£20.00' (positions 0, 1, 5) and 3 of '[£20.00]' (positions 2,3,4)
        assert svg.count('<title>£20.00</title>') == 3
        assert svg.count('<title>[£20.00]</title>') == 3
    
    def test_stock_with_gaps(self):
        """Scenario: Stock with multiple OUT periods."""
        # Weeks: IN, IN, OUT, OUT, IN
        # Bars: ██  █ (gaps at positions 2,3)
        unicode = "██  █"
        
        svg = convert_sparkline_to_svg(unicode, metric_type="stock")
        
        # Only 3 bars (positions 0, 1, 4)
        assert svg.count('<rect') == 3
        
        # Green color (stock is always green)
        assert 'fill="#22c55e"' in svg
        
        # All tooltips say "IN"
        assert svg.count('<title>IN</title>') == 3

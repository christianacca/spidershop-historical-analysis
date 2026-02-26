#!/usr/bin/env python3
"""Tests for sparkline SVG conversion."""
import pytest
from bs4 import BeautifulSoup
from website.sparkline_conversion import convert_sparkline_to_svg, convert_sparklines_in_rows


class TestSparklineSVGConversion:
    """Test suite for converting Unicode sparklines to SVG."""

    def test_convert_price_sparkline_with_rising_trend(self):
        """Should convert rising price sparkline to SVG with green bars and tooltips."""
        from website.sparkline_conversion import convert_sparkline_to_svg
        
        unicode_sparkline = "▁▂▃▄▅▆▇█"
        values = ["8.99", "10.50", "12.99", "16.50", "18.99", "21.00", "21.00", "24.99"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="price")
        
        # Should be SVG element
        assert svg.startswith('<svg')
        assert '</svg>' in svg
        
        # Should have green color (rising trend)
        assert '#22c55e' in svg or '#4CAF50' in svg or 'green' in svg.lower()
        
        # Should have tooltips with price values
        assert '£8.99' in svg or '8.99' in svg
        assert '£24.99' in svg or '24.99' in svg
        
        # Should have 8 bars
        assert svg.count('<rect') == 8

    def test_convert_wishlist_sparkline_with_falling_trend(self):
        """Should convert falling wishlist sparkline to SVG with red bars."""
        from website.sparkline_conversion import convert_sparkline_to_svg
        
        unicode_sparkline = "█▇▆▅▄▃▂▁"
        values = ["45", "40", "35", "28", "20", "15", "12", "8"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="wishlist")
        
        # Should be SVG element
        assert svg.startswith('<svg')
        
        # Should have red color (falling trend)
        assert '#ef4444' in svg or '#f44336' in svg or 'red' in svg.lower()
        
        # Should have tooltips with wishlist counts
        assert '45' in svg
        assert '8' in svg
        assert 'wishlist' in svg.lower()

    def test_convert_stable_sparkline_uses_gray(self):
        """Should use gray color for stable/neutral trends."""
        from website.sparkline_conversion import convert_sparkline_to_svg
        
        unicode_sparkline = "▄▄▄▄▄▄▄▄"
        values = ["12.50", "12.50", "12.50", "13.00", "12.50", "12.50", "12.50", "12.50"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="price")
        
        # Should be blue (neutral) for stable trend
        assert '#3b82f6' in svg or '#888' in svg or 'blue' in svg.lower()

    def test_convert_sparkline_with_gaps_before_first_appearance(self):
        """Should render gaps as true empty space when species didn't exist yet (no bars)."""
        from website.sparkline_conversion import convert_sparkline_to_svg
        
        # Unicode sparkline: 4 spaces (didn't exist), then 3 bars (existed with carried-forward values)
        unicode_sparkline = "    ▄▄▄"
        values = ["20.00", "20.00", "20.00", "20.00", "20.00", "20.00", "20.00"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="price")
        
        # Should be SVG
        assert svg.startswith('<svg')
        assert '</svg>' in svg
        
        # Should have exactly 3 bars (not 7) - gaps should not render as bars
        assert svg.count('<rect') == 3
        
        # Should NOT have carried-forward indicators in tooltips (gaps are true absences)
        assert 'carried forward' not in svg.lower()
        
        # Bars should be positioned at x=40, 50, 60 (skipping first 4 positions)
        assert 'x="40"' in svg  # 5th position (index 4)
        assert 'x="50"' in svg  # 6th position (index 5)
        assert 'x="60"' in svg  # 7th position (index 6)
        
        # Should NOT have bars at x=0, 10, 20, 30 (the gap positions)
        assert 'x="0"' not in svg
        assert 'x="10"' not in svg
        assert 'x="20"' not in svg
        assert 'x="30"' not in svg

    def test_convert_stock_availability_sparkline(self):
        """Should convert stock availability sparkline (binary IN/OUT)."""
        from website.sparkline_conversion import convert_sparkline_to_svg
        
        unicode_sparkline = "█ █ █"
        values = None  # Stock availability doesn't need numeric values
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="stock")
        
        # Should have green bars for IN stock
        assert '#22c55e' in svg or '#4CAF50' in svg or 'green' in svg.lower()
        
        # Should have tooltips
        assert '<title>IN</title>' in svg

    def test_sparkline_with_no_values_returns_dash(self):
        """Should return plain dash for invalid sparklines."""
        from website.sparkline_conversion import convert_sparkline_to_svg
        
        result = convert_sparkline_to_svg("-", [], metric_type="price")
        
        # Should return the original dash (no conversion)
        assert result == "-"

    def test_sparkline_dimensions_are_consistent(self):
        """Should generate SVG with consistent dimensions."""
        from website.sparkline_conversion import convert_sparkline_to_svg
        
        unicode_sparkline = "▁▂▃▄▅▆▇█"
        values = ["10", "15", "20", "25", "30", "35", "40", "45"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="wishlist")
        
        # Should have standard dimensions
        assert 'width="80"' in svg
        assert 'height="20"' in svg
        assert 'viewBox="0 0 80 20"' in svg

    def test_sparkline_with_leading_gaps_aligns_tooltips_correctly(self):
        """
        Should align tooltips with correct values when sparkline has leading gaps.

        The values array is always index-aligned with the sparkline characters:
        leading gap characters (spaces) correspond to None at the same position in values.
        This means len(values) == len(sparkline) and bars without a corresponding value
        (None/"") are skipped during rendering.

        - Unicode sparkline: "  █▁▁▁▁" (7 chars: 2 leading spaces + 5 bars)
        - Historical values: 7 elements aligned by index (None for the 2 leading gaps)
        - Expected: only the 5 non-gap bars are rendered with correct tooltips
        """
        from website.sparkline_conversion import convert_sparkline_to_svg

        # Sparkline with 2 leading gaps (spaces), then 5 bars
        unicode_sparkline = "  █▁▁▁▁"
        # Values are index-aligned: None for each leading gap, actual values for bars
        values = [None, None, "91", "90", "90", "89", "89"]

        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="wishlist")

        # Should render only 5 bars (skipping the 2 leading gaps)
        rect_count = svg.count('<rect')
        assert rect_count == 5, f"Expected 5 bars but got {rect_count}"

        # Parse SVG to check tooltip values in order
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(svg, 'html.parser')
        rects = soup.find_all('rect')

        # Extract tooltip text from each rect's <title> child
        tooltips = [rect.find('title').text for rect in rects if rect.find('title')]

        # All 5 bars should have values
        assert "91 wishlists" in tooltips[0], f"First bar should show '91 wishlists', got {tooltips[0]}"
        assert "90 wishlists" in tooltips[1], f"Second bar should show '90 wishlists', got {tooltips[1]}"
        assert "90 wishlists" in tooltips[2], f"Third bar should show '90 wishlists', got {tooltips[2]}"
        assert "89 wishlists" in tooltips[3], f"Fourth bar should show '89 wishlists', got {tooltips[3]}"
        assert "89 wishlists" in tooltips[4], f"Fifth bar should show '89 wishlists', got {tooltips[4]}"

    def test_single_bar_sparkline_with_leading_gap_in_values(self):
        """
        Should render one bar correctly when values has a leading gap entry and only
        one valid value — the exact production failure case for Avicularia variegata.

        generate_sparkline returns a compact "▄" (length 1) when there is only one
        non-None/non-empty value, even if values has length > 1.  The render loop
        must therefore index into compact_values (gaps stripped) rather than the raw
        values array so that bar_index 0 maps to "35.00" and not the leading "".
        """
        from shared.sparkline_helpers import generate_sparkline
        from website.sparkline_conversion import convert_sparkline_to_svg

        # Jan run: species present but price was empty; Feb run: £35.00
        values = ["", "35.00"]
        sparkline = generate_sparkline(values)

        # generate_sparkline should produce a gap character for the empty-price
        # run, then a bar for the valid-price run: ' ▄' (length 2, aligned with values)
        assert sparkline == " ▄", f"Expected ' ▄', got {repr(sparkline)}"
        assert len(sparkline) == len(values), "Sparkline and values must be length-aligned"

        svg = convert_sparkline_to_svg(sparkline, values, metric_type="price",
                                       is_carried_forward=[False, False])

        assert svg.startswith("<svg"), "Should produce SVG, not the raw sparkline string"
        rect_count = svg.count("<rect")
        assert rect_count == 1, f"Expected 1 bar (gap skipped), got {rect_count}"
        assert "£35.00" in svg, "Bar tooltip should show £35.00"




class TestConvertSparklinesInRows:
    """Test suite for converting Unicode sparklines in CSV rows."""

    def test_converts_price_sparklines_in_csv_rows(self):
        """Should convert price history sparklines in CSV data rows."""
        from website.sparkline_conversion import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Price History"]
        rows = [
            ["Aphonopelma seemanni", "1.5", "▁▂▃▄▅▆▇█"]
        ]
        
        # Create historical data structure
        by_run = {
            "2025-01-01": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "8.99", "wishlist_count": "5"}],
            "2025-01-08": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "10.50", "wishlist_count": "5"}],
            "2025-01-15": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "12.99", "wishlist_count": "5"}],
            "2025-01-22": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "16.50", "wishlist_count": "5"}],
            "2025-01-29": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "18.99", "wishlist_count": "20"}],
            "2025-02-05": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "21.00", "wishlist_count": "22"}],
            "2025-02-12": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "21.00", "wishlist_count": "25"}],
            "2025-02-19": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "24.99", "wishlist_count": "28"}],
        }
        runs = sorted(by_run.keys())
        historical_data = (by_run, runs)
        
        result = convert_sparklines_in_rows(headers, rows, historical_data, "test.csv")
        
        # Should have SVG in the sparkline column
        assert '<svg' in result[0][2]
        assert '</svg>' in result[0][2]
        assert '8.99' in result[0][2] or '£8.99' in result[0][2]

    def test_converts_wishlist_sparklines_in_csv_rows(self):
        """Should convert wishlist history sparklines in CSV data rows."""
        from website.sparkline_conversion import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Wishlist History"]
        rows = [
            ["Test Species", "2.0", "▁▁▁▁████"]
        ]
        
        by_run = {
            "2025-01-01": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "5"}],
            "2025-01-08": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "5"}],
            "2025-01-15": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "5"}],
            "2025-01-22": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "5"}],
            "2025-01-29": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "20"}],
            "2025-02-05": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "22"}],
            "2025-02-12": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "25"}],
            "2025-02-19": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "28"}],
        }
        runs = sorted(by_run.keys())
        historical_data = (by_run, runs)
        
        result = convert_sparklines_in_rows(headers, rows, historical_data, "test.csv")
        
        assert '<svg' in result[0][2]
        assert 'wishlists' in result[0][2]

    def test_converts_stock_availability_sparklines_in_csv_rows(self):
        """Should convert stock availability sparklines without crashing (regression test for metric_type=None bug)."""
        from website.sparkline_conversion import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Stock Availability"]
        rows = [
            ["Test Species", "2.0", "█ █ █"]
        ]
        
        # Stock sparklines don't use historical data
        historical_data = ({}, [])
        
        # Should not raise AttributeError: 'NoneType' object has no attribute 'capitalize'
        result = convert_sparklines_in_rows(headers, rows, historical_data, "test.csv")
        
        assert '<svg' in result[0][2]
        assert '<title>IN</title>' in result[0][2]

    def test_handles_rows_without_sparkline_columns(self):
        """Should return unchanged rows when no sparkline columns present."""
        from website.sparkline_conversion import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Price"]
        rows = [
            ["Test Species", "2.0", "£10.00"]
        ]
        
        result = convert_sparklines_in_rows(headers, rows, ({}, []), "test.csv")
        
        # Should be unchanged
        assert result == rows

    def test_handles_empty_historical_data(self):
        """Should handle missing historical data gracefully."""
        from website.sparkline_conversion import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Price History"]
        rows = [
            ["Unknown Species", "1.0", "▁▂▃▄"]
        ]
        
        # No historical data available
        result = convert_sparklines_in_rows(headers, rows, ({}, []), "test.csv")
        
        # Should keep Unicode sparkline unchanged (no SVG conversion without values)
        assert result[0][2] == "▁▂▃▄"
        assert '<svg' not in result[0][2]



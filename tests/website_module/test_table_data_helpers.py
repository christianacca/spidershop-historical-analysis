#!/usr/bin/env python3
"""
Tests for rows_to_json table data serialisation helper.
"""

import pytest
from website import rows_to_json


class TestRowsToJsonEmptyInput:
    """Tests for empty and None inputs."""

    def test_empty_rows_returns_empty_list(self):
        """Should return [] when rows list is empty."""
        result = rows_to_json(["Species", "Price"], [])
        assert result == []

    def test_empty_headers_returns_empty_list(self):
        """Should return [] when headers list is empty."""
        result = rows_to_json([], [["Brachypelma hamorii", "£14.99"]])
        assert result == []

    def test_both_empty_returns_empty_list(self):
        """Should return [] when both headers and rows are empty."""
        result = rows_to_json([], [])
        assert result == []


class TestRowsToJsonBasicConversion:
    """Tests for basic row-to-dict conversion."""

    def test_single_row_single_column(self):
        """Should convert a single-row, single-column table to a list with one dict."""
        result = rows_to_json(["Species"], [["Brachypelma hamorii"]])
        assert result == [{"Species": "Brachypelma hamorii"}]

    def test_single_row_multiple_columns(self):
        """Should convert all columns to dict keys using header names."""
        headers = ["Species", "Size (cm)", "Signal"]
        rows = [["Brachypelma hamorii", "1.5", "🔥 Hot"]]
        result = rows_to_json(headers, rows)
        assert result == [{"Species": "Brachypelma hamorii", "Size (cm)": "1.5", "Signal": "🔥 Hot"}]

    def test_preserves_original_value_types(self):
        """Should preserve the original value type (str, int, float) in the dict."""
        headers = ["Name", "Count", "Price"]
        rows = [["Spider", 42, 14.99]]
        result = rows_to_json(headers, rows)
        assert result == [{"Name": "Spider", "Count": 42, "Price": 14.99}]

    def test_none_cell_value_is_preserved_as_empty_string_in_str_check(self):
        """None values should not raise and should be included (not skipped)."""
        headers = ["Species", "Notes"]
        rows = [["Brachypelma hamorii", None]]
        result = rows_to_json(headers, rows)
        # None is not SVG so it should be included as-is
        assert result == [{"Species": "Brachypelma hamorii", "Notes": None}]


class TestRowsToJsonMultiRow:
    """Tests for multi-row output."""

    def test_multiple_rows_all_converted(self):
        """Should convert all rows to dicts, one per input row."""
        headers = ["Species", "Signal"]
        rows = [
            ["Brachypelma hamorii", "🔥 Hot"],
            ["Aphonopelma seemanni", "⚠️ Watch"],
            ["Grammostola pulchripes", "❌ Avoid"],
        ]
        result = rows_to_json(headers, rows)
        assert len(result) == 3
        assert result[0] == {"Species": "Brachypelma hamorii", "Signal": "🔥 Hot"}
        assert result[1] == {"Species": "Aphonopelma seemanni", "Signal": "⚠️ Watch"}
        assert result[2] == {"Species": "Grammostola pulchripes", "Signal": "❌ Avoid"}

    def test_row_order_preserved(self):
        """Should preserve the order of rows in the output."""
        headers = ["Id"]
        rows = [["first"], ["second"], ["third"]]
        result = rows_to_json(headers, rows)
        assert [r["Id"] for r in result] == ["first", "second", "third"]


class TestRowsToJsonSvgExclusion:
    """Tests for SVG sparkline cell exclusion."""

    def test_svg_cell_is_excluded_from_dict(self):
        """Cell whose value starts with '<svg' should be absent from the row dict."""
        headers = ["Species", "Price History", "Signal"]
        svg = "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>"
        rows = [["Brachypelma hamorii", svg, "🔥 Hot"]]
        result = rows_to_json(headers, rows)
        assert result == [{"Species": "Brachypelma hamorii", "Signal": "🔥 Hot"}]
        assert "Price History" not in result[0]

    def test_multiple_svg_cells_all_excluded(self):
        """Multiple SVG cells in the same row should all be excluded."""
        headers = ["Species", "Price History", "Wishlist History"]
        svg = "<svg><polyline/></svg>"
        rows = [["Brachypelma hamorii", svg, svg]]
        result = rows_to_json(headers, rows)
        assert result == [{"Species": "Brachypelma hamorii"}]

    def test_unicode_sparkline_is_included(self):
        """Unicode sparkline string (not SVG) should be included as-is."""
        headers = ["Species", "Price History"]
        rows = [["Brachypelma hamorii", "▁▂▃▄▅▆▇"]]
        result = rows_to_json(headers, rows)
        assert result == [{"Species": "Brachypelma hamorii", "Price History": "▁▂▃▄▅▆▇"}]

    def test_svg_exclusion_does_not_affect_adjacent_rows(self):
        """SVG exclusion in one row should not affect other rows."""
        headers = ["Species", "Sparkline"]
        svg = "<svg/>"
        rows = [
            ["Spider A", svg],
            ["Spider B", "▁▂▃"],
        ]
        result = rows_to_json(headers, rows)
        assert result[0] == {"Species": "Spider A"}
        assert result[1] == {"Species": "Spider B", "Sparkline": "▁▂▃"}

    def test_cell_starting_with_svg_tag_excluded(self):
        """Cell starting with exact '<svg' prefix (case-sensitive) is excluded."""
        headers = ["Notes"]
        rows = [["<svg width='10'>content</svg>"]]
        result = rows_to_json(headers, rows)
        assert result == [{}]

    def test_cell_containing_svg_not_starting_with_svg_is_included(self):
        """Cell that contains 'svg' but doesn't start with '<svg' is NOT excluded."""
        headers = ["Notes"]
        rows = [["See the <svg> chart"]]
        result = rows_to_json(headers, rows)
        assert result == [{"Notes": "See the <svg> chart"}]

    def test_dto_dict_passes_through_unchanged(self):
        """A sparkline DTO dict is not stripped — it passes through rows_to_json intact."""
        dto = {
            "bars": [{"bar_height": 20.0, "fill": "#22c55e", "opacity": 0.7, "tooltip": "£15.00"}],
            "svg_width": 10,
            "svg_height": 20,
            "title": "Price History",
        }
        headers = ["Species", "Price History"]
        rows = [["Brachypelma hamorii", dto]]
        result = rows_to_json(headers, rows)
        assert result == [{"Species": "Brachypelma hamorii", "Price History": dto}]
        assert result[0]["Price History"] is dto

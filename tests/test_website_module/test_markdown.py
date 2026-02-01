#!/usr/bin/env python3
"""
Tests for markdown parsing and analysis section extraction.

Tests cover:
- Markdown to HTML conversion
- Analysis section extraction from markdown
- Data label addition for responsive tables
"""

import pytest
import os
from pathlib import Path
from bs4 import BeautifulSoup
from website import parse_markdown_to_html, extract_analysis_sections
from website.markdown_utils import add_data_labels_to_tables


class TestParseMarkdownToHtml:
    """Snapshot tests for markdown to HTML conversion.
    
    This test verifies that the markdown library continues to produce
    consistent HTML output. If the markdown library is upgraded and this
    test fails, review the changes in the diff to ensure they're acceptable,
    then regenerate the snapshot by running:
    
        pytest --snapshot-update
    """

    def test_markdown_conversion_matches_expected_output(self, snapshot):
        """Should convert full analysis_summary.md to HTML exactly as captured in snapshot."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        
        # Load the real analysis_summary.md fixture
        with open(fixtures_dir / "analysis_summary.md", "r", encoding="utf-8") as f:
            markdown_text = f.read()
        
        # Convert and compare with snapshot
        actual_html = parse_markdown_to_html(markdown_text)
        assert actual_html == snapshot


class TestExtractAnalysisSections:
    """Test suite for extracting analysis sections from markdown."""

    def test_nonexistent_file_returns_none(self):
        """Should return None for breeder and dealer if file doesn't exist."""
        result = extract_analysis_sections("/nonexistent/file.md")
        # Function returns (None, None, None, None, None, None) when file doesn't exist
        assert result == (None, None, None, None, None, None)

    def test_extract_breeder_section(self):
        """Should extract breeder summary stats (not full table)."""
        from conftest import create_temp_markdown_file
        
        filename = create_temp_markdown_file(
            """## 🧬 Breeder Opportunity Matrix (Top 10)

**Summary:** 109 species analyzed | 🔥 Hot: 36 | ⚠️ Watch: 30 | ❌ Avoid: 43

| Species | Size (cm) | Signal |
|---|---:|---|
| Test Species | 1 | 🔥 |

## 🏪 Dealer Supply Risk Matrix (Top 10)

Other content."""
        )
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert breeder is not None
            assert "**Summary:**" in breeder
            assert "109 species analyzed" in breeder
            # Table should NOT be extracted
            assert "| Species |" not in breeder
        finally:
            os.unlink(filename)

    def test_extract_dealer_section(self):
        """Should extract dealer summary stats (not full table)."""
        from conftest import create_temp_markdown_file
        
        filename = create_temp_markdown_file(
            """## 🏪 Dealer Supply Risk Matrix (Top 10)

**Summary:** 109 species analyzed | 🔥 High Risk: 35 | ⚠️ Moderate Risk: 57 | ❌ Low Risk: 17

| Species | Size (cm) | Dealer Risk |
|---|---:|---|
| Test Species | 1 | 🔥 |

<details>
<summary>Legend</summary>
</details>"""
        )
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert dealer is not None
            assert "**Summary:**" in dealer
            assert "109 species analyzed" in dealer
            # Table should NOT be extracted
            assert "| Species |" not in dealer
        finally:
            os.unlink(filename)

    def test_extract_legend_section(self):
        """Should extract legend from details block."""
        from conftest import create_temp_markdown_file
        
        filename = create_temp_markdown_file(
            """<details>
<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>
### 🧬 Breeder Opportunity Matrix — Legend
Breeder legend content here.
### 📖 Breeder Matrix — Practical Examples
Breeder example 1 here.
### 🏪 Dealer Supply Risk Matrix — Legend
Dealer legend content here.
### 📖 Dealer Matrix — Practical Examples
Dealer example 1 here.
</details>"""
        )
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert breeder_legend is not None
            assert "Breeder legend content here." in breeder_legend
            assert dealer_legend is not None
            assert "Dealer legend content here." in dealer_legend
            assert breeder_examples is not None
            assert "Breeder example 1 here." in breeder_examples
            assert dealer_examples is not None
            assert "Dealer example 1 here." in dealer_examples
        finally:
            os.unlink(filename)

    def test_missing_sections_return_none(self):
        """Should return None for missing sections."""
        from conftest import create_temp_markdown_file
        
        filename = create_temp_markdown_file(
            "# Some Title\n\nSome content without the expected sections."
        )
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert breeder is None
            assert dealer is None
            assert breeder_legend is None
            assert dealer_legend is None
            assert breeder_examples is None
            assert dealer_examples is None
        finally:
            os.unlink(filename)

    def test_partial_sections(self):
        """Should return None if Summary line not found."""
        from conftest import create_temp_markdown_file
        
        filename = create_temp_markdown_file(
            """## 🧬 Breeder Opportunity Matrix (Top 10)

Breeder content only (no Summary line)."""
        )
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            # Without Summary line, extraction returns None
            assert breeder is None
            assert dealer is None
            assert breeder_legend is None
            assert dealer_legend is None
            assert breeder_examples is None
            assert dealer_examples is None
        finally:
            os.unlink(filename)


class TestAddDataLabelsToTables:
    """Test suite for adding data-label attributes to HTML tables for responsive layout."""

    def test_adds_data_labels_to_simple_table(self):
        """Should add data-label attributes to all td elements based on headers."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Age</th>
                    <th>City</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>John</td>
                    <td>30</td>
                    <td>NYC</td>
                </tr>
                <tr>
                    <td>Jane</td>
                    <td>25</td>
                    <td>LA</td>
                </tr>
            </tbody>
        </table>
        """
        
        result = add_data_labels_to_tables(html)
        
        # Parse result to verify
        soup = BeautifulSoup(result, 'html.parser')
        rows = soup.find_all('tr')
        
        # First row (John)
        cells = rows[1].find_all('td')
        assert cells[0].get('data-label') == 'Name'
        assert cells[1].get('data-label') == 'Age'
        assert cells[2].get('data-label') == 'City'
        
        # Second row (Jane)
        cells = rows[2].find_all('td')
        assert cells[0].get('data-label') == 'Name'
        assert cells[1].get('data-label') == 'Age'
        assert cells[2].get('data-label') == 'City'

    def test_handles_multiple_tables(self):
        """Should add data-label attributes to multiple tables independently."""
        html = """
        <table>
            <thead><tr><th>Col1</th><th>Col2</th></tr></thead>
            <tbody><tr><td>A</td><td>B</td></tr></tbody>
        </table>
        <table>
            <thead><tr><th>Header1</th><th>Header2</th><th>Header3</th></tr></thead>
            <tbody><tr><td>X</td><td>Y</td><td>Z</td></tr></tbody>
        </table>
        """
        
        result = add_data_labels_to_tables(html)
        soup = BeautifulSoup(result, 'html.parser')
        tables = soup.find_all('table')
        
        # First table
        cells = tables[0].find('tbody').find_all('td')
        assert cells[0].get('data-label') == 'Col1'
        assert cells[1].get('data-label') == 'Col2'
        
        # Second table
        cells = tables[1].find('tbody').find_all('td')
        assert cells[0].get('data-label') == 'Header1'
        assert cells[1].get('data-label') == 'Header2'
        assert cells[2].get('data-label') == 'Header3'

    def test_handles_table_without_thead(self):
        """Should skip tables without thead gracefully."""
        html = """
        <table>
            <tbody>
                <tr><td>Data1</td><td>Data2</td></tr>
            </tbody>
        </table>
        """
        
        result = add_data_labels_to_tables(html)
        soup = BeautifulSoup(result, 'html.parser')
        cells = soup.find_all('td')
        
        # Should not have data-label attributes
        assert cells[0].get('data-label') is None
        assert cells[1].get('data-label') is None

    def test_handles_table_without_tbody(self):
        """Should skip tables without tbody gracefully."""
        html = """
        <table>
            <thead>
                <tr><th>Header1</th><th>Header2</th></tr>
            </thead>
        </table>
        """
        
        result = add_data_labels_to_tables(html)
        # Should not crash, returns valid HTML
        assert '<table>' in result

    def test_handles_mismatched_column_count(self):
        """Should handle rows with different number of cells than headers."""
        html = """
        <table>
            <thead>
                <tr><th>Col1</th><th>Col2</th><th>Col3</th></tr>
            </thead>
            <tbody>
                <tr><td>A</td><td>B</td></tr>
                <tr><td>X</td><td>Y</td><td>Z</td><td>Extra</td></tr>
            </tbody>
        </table>
        """
        
        result = add_data_labels_to_tables(html)
        soup = BeautifulSoup(result, 'html.parser')
        rows = soup.find('tbody').find_all('tr')
        
        # First row - only 2 cells, should get labels for first 2 headers
        cells = rows[0].find_all('td')
        assert len(cells) == 2
        assert cells[0].get('data-label') == 'Col1'
        assert cells[1].get('data-label') == 'Col2'
        
        # Second row - 4 cells, first 3 should get labels, 4th should not
        cells = rows[1].find_all('td')
        assert len(cells) == 4
        assert cells[0].get('data-label') == 'Col1'
        assert cells[1].get('data-label') == 'Col2'
        assert cells[2].get('data-label') == 'Col3'
        assert cells[3].get('data-label') is None  # No header for 4th column

    def test_preserves_existing_html_content(self):
        """Should preserve other HTML content and only modify tables."""
        html = """
        <div class="container">
            <p>Some text before table</p>
            <table>
                <thead><tr><th>Name</th></tr></thead>
                <tbody><tr><td>John</td></tr></tbody>
            </table>
            <p>Some text after table</p>
        </div>
        """
        
        result = add_data_labels_to_tables(html)
        
        # Should preserve structure
        assert '<div class="container">' in result
        assert '<p>Some text before table</p>' in result
        assert '<p>Some text after table</p>' in result
        
        # Should add data-label to table
        soup = BeautifulSoup(result, 'html.parser')
        td = soup.find('td')
        assert td.get('data-label') == 'Name'

    def test_empty_string_returns_empty_string(self):
        """Should handle empty string input."""
        result = add_data_labels_to_tables("")
        assert result == ""

    def test_no_tables_returns_unchanged(self):
        """Should return unchanged HTML when no tables present."""
        html = "<div><p>Just some text</p></div>"
        result = add_data_labels_to_tables(html)
        assert "<div><p>Just some text</p></div>" in result

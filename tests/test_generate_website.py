#!/usr/bin/env python3
"""
Comprehensive tests for generate_website.py using synthetic data.

Tests cover:
- Markdown to HTML conversion
- CSV file reading and parsing
- HTML generation (tables, pages, templates)
- Analysis section extraction
- Edge cases (missing files, empty data)
"""

#!/usr/bin/env python3
"""
Comprehensive tests for generate_website.py using synthetic data.

Tests cover:
- Markdown to HTML conversion
- CSV file reading and parsing
- HTML generation (tables, pages, templates)
- Analysis section extraction
- Edge cases (missing files, empty data)
"""

import pytest
import tempfile
import os
from pathlib import Path
from generate_website import (
    parse_markdown_to_html,
    extract_analysis_sections,
    read_csv_file,
    escape_html,
    generate_table_html,
    get_base_html_template,
    get_html_footer,
    generate_homepage,
    generate_data_page,
    main,
    OUTPUT_DIR,
)


class TestParseMarkdownToHtml:
    """Test suite for markdown to HTML conversion."""

    def test_empty_input_returns_empty_string(self):
        """Empty markdown should return empty string."""
        assert parse_markdown_to_html("") == ""
        assert parse_markdown_to_html(None) == ""

    def test_headers_h1_h2_h3(self):
        """Should convert markdown headers to HTML tags with heading downgrade."""
        markdown = """# Header 1
## Header 2
### Header 3"""
        expected_html = """<h1>Header 1</h1>
<h3>Header 2</h3>
<h4>Header 3</h4>"""
        html = parse_markdown_to_html(markdown)
        assert html == expected_html

    def test_italic_text_conversion(self):
        """Should convert *italic* to <em>italic</em>."""
        markdown = "This is *italic text* here"
        expected_html = '<p>This is <em>italic text</em> here</p>'
        html = parse_markdown_to_html(markdown)
        assert html == expected_html

    def test_table_with_alignment_separator(self):
        """Should handle table separator with alignment markers."""
        markdown = """| Left | Center | Right |
|:-----|:------:|------:|
| A    | B      | C     |"""
        
        expected_html = """<table class="data-table markdown-table">
<thead>
<tr>
<th style="text-align: left;">Left</th>
<th style="text-align: center;">Center</th>
<th style="text-align: right;">Right</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">A</td>
<td style="text-align: center;">B</td>
<td style="text-align: right;">C</td>
</tr>
</tbody>
</table>"""
        html = parse_markdown_to_html(markdown)
        assert html == expected_html

    def test_legend_column_header_with_list(self):
        """Should convert headers followed by lists properly."""
        # Proper markdown requires blank line before list
        markdown = """**OOS**

- `IN` — Species is currently listed for sale
- `OUT` — Species is not listed this run

**Pattern**

- `Always` — Normal availability
- `Emerging` — Missing for multiple runs"""
        
        expected_html = """<p><strong>OOS</strong></p>
<ul>
<li><code>IN</code> — Species is currently listed for sale</li>
<li><code>OUT</code> — Species is not listed this run</li>
</ul>
<p><strong>Pattern</strong></p>
<ul>
<li><code>Always</code> — Normal availability</li>
<li><code>Emerging</code> — Missing for multiple runs</li>
</ul>"""
        html = parse_markdown_to_html(markdown)
        assert html == expected_html

    def test_mixed_formatting(self):
        """Should handle multiple formatting types together."""
        markdown = """## Title

This is **bold** and *italic* with `code`."""
        expected_html = """<h3>Title</h3>
<p>This is <strong>bold</strong> and <em>italic</em> with <code>code</code>.</p>"""
        html = parse_markdown_to_html(markdown)
        assert html == expected_html

    def test_legend_example_structure(self):
        """Should convert complete legend example structure correctly."""
        # Note: markdown library requires blank line before lists
        markdown = """#### Example 1: Sustained Scarcity (Strong Opportunity)
**Scenario:** A species that has been unavailable for 4+ consecutive weeks

| Week | Listed? | Price | Wishlist Count |
|------|---------|-------|----------------|
| Jan 1 | ✅ Yes | £25.00 | 10 |
| Jan 8 | ❌ No | - | - |

**Analysis Result:**

- **OOS:** OUT
- **OOS Runs:** 4
- **Pattern:** Sustained
- **Signal:** 🔥

**Why:** When a species disappears for 4+ weeks in a row, this indicates persistent market scarcity.

---"""
        
        expected_html = """<h5>Example 1: Sustained Scarcity (Strong Opportunity)</h5>
<p><strong>Scenario:</strong> A species that has been unavailable for 4+ consecutive weeks</p>
<table class="data-table markdown-table">
<thead>
<tr>
<th>Week</th>
<th>Listed?</th>
<th>Price</th>
<th>Wishlist Count</th>
</tr>
</thead>
<tbody>
<tr>
<td>Jan 1</td>
<td>✅ Yes</td>
<td>£25.00</td>
<td>10</td>
</tr>
<tr>
<td>Jan 8</td>
<td>❌ No</td>
<td>-</td>
<td>-</td>
</tr>
</tbody>
</table>
<p><strong>Analysis Result:</strong></p>
<ul>
<li><strong>OOS:</strong> OUT</li>
<li><strong>OOS Runs:</strong> 4</li>
<li><strong>Pattern:</strong> Sustained</li>
<li><strong>Signal:</strong> 🔥</li>
</ul>
<p><strong>Why:</strong> When a species disappears for 4+ weeks in a row, this indicates persistent market scarcity.</p>
<hr />"""
        
        html = parse_markdown_to_html(markdown)
        assert html == expected_html

    def test_multiple_tables(self):
        """Should handle multiple tables in markdown."""
        markdown = """| Table 1 |
|---------|
| Data 1  |

Some text

| Table 2 |
|---------|
| Data 2  |"""
        
        expected_html = """<table class="data-table markdown-table">
<thead>
<tr>
<th>Table 1</th>
</tr>
</thead>
<tbody>
<tr>
<td>Data 1</td>
</tr>
</tbody>
</table>
<p>Some text</p>
<table class="data-table markdown-table">
<thead>
<tr>
<th>Table 2</th>
</tr>
</thead>
<tbody>
<tr>
<td>Data 2</td>
</tr>
</tbody>
</table>"""
        html = parse_markdown_to_html(markdown)
        assert html == expected_html


class TestExtractAnalysisSections:
    """Test suite for extracting analysis sections from markdown."""

    def test_nonexistent_file_returns_none(self):
        """Should return None for breeder and dealer if file doesn't exist."""
        result = extract_analysis_sections("/nonexistent/file.md")
        # Function returns (None, None, None, None, None, None) when file doesn't exist
        assert result == (None, None, None, None, None, None)

    def test_extract_breeder_section(self):
        """Should extract breeder opportunity matrix section."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## 🧬 Breeder Opportunity Matrix (Top 10)

Some analysis text here.

## 🏪 Dealer Supply Risk Matrix (Top 10)

Other content.""")
            filename = f.name
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert breeder is not None
            assert "## 🧬 Breeder Opportunity Matrix (Top 10)" in breeder
            assert "Some analysis text here." in breeder
        finally:
            os.unlink(filename)

    def test_extract_dealer_section(self):
        """Should extract dealer supply risk matrix section."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## 🏪 Dealer Supply Risk Matrix (Top 10)

Dealer analysis here.

<details>
<summary>Legend</summary>
</details>""")
            filename = f.name
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert dealer is not None
            assert "## 🏪 Dealer Supply Risk Matrix (Top 10)" in dealer
            assert "Dealer analysis here." in dealer
        finally:
            os.unlink(filename)

    def test_extract_legend_section(self):
        """Should extract legend from details block."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""<details>
<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>
### 🧬 Breeder Opportunity Matrix — Legend
Breeder legend content here.
### 📖 Breeder Matrix — Practical Examples
Breeder example 1 here.
### 🏪 Dealer Supply Risk Matrix — Legend
Dealer legend content here.
### 📖 Dealer Matrix — Practical Examples
Dealer example 1 here.
</details>""")
            filename = f.name
        
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Some Title\n\nSome content without the expected sections.")
            filename = f.name
        
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
        """Should extract only the sections that exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## 🧬 Breeder Opportunity Matrix (Top 10)

Breeder content only.""")
            filename = f.name
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert breeder is not None
            assert dealer is None
            assert breeder_legend is None
            assert dealer_legend is None
            assert breeder_examples is None
            assert dealer_examples is None
        finally:
            os.unlink(filename)


class TestReadCsvFile:
    """Test suite for CSV file reading."""

    def test_nonexistent_file_returns_none_and_empty_list(self):
        """Should return (None, []) for nonexistent file."""
        headers, rows = read_csv_file("/nonexistent/file.csv")
        assert headers is None
        assert rows == []

    def test_empty_csv_file(self):
        """Should handle empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers is None
            assert rows == []
        finally:
            os.unlink(filename)

    def test_csv_with_headers_only(self):
        """Should read CSV with only headers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Column1,Column2,Column3\n")
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Column1", "Column2", "Column3"]
            assert rows == []
        finally:
            os.unlink(filename)

    def test_csv_with_data(self):
        """Should read CSV with headers and data rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Name,Price,Size\n")
            f.write("Species A,25.00,1.0\n")
            f.write("Species B,30.50,2.5\n")
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Name", "Price", "Size"]
            assert len(rows) == 2
            assert rows[0] == ["Species A", "25.00", "1.0"]
            assert rows[1] == ["Species B", "30.50", "2.5"]
        finally:
            os.unlink(filename)

    def test_csv_with_special_characters(self):
        """Should handle CSV with special characters and quotes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write('Name,Description\n')
            f.write('"Species, with comma","Description with ""quotes"""\n')
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Name", "Description"]
            assert rows[0] == ["Species, with comma", 'Description with "quotes"']
        finally:
            os.unlink(filename)

    def test_csv_with_utf8_characters(self):
        """Should handle UTF-8 encoded characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Common\n")
            f.write("Brachypelma boehmei,🕷️ Mexican Fireleg\n")
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Species", "Common"]
            assert rows[0] == ["Brachypelma boehmei", "🕷️ Mexican Fireleg"]
        finally:
            os.unlink(filename)


class TestEscapeHtml:
    """Test suite for HTML escaping."""

    def test_escape_ampersand(self):
        """Should escape & to &amp;."""
        assert escape_html("Tom & Jerry") == "Tom &amp; Jerry"

    def test_escape_less_than(self):
        """Should escape < to &lt;."""
        assert escape_html("5 < 10") == "5 &lt; 10"

    def test_escape_greater_than(self):
        """Should escape > to &gt;."""
        assert escape_html("10 > 5") == "10 &gt; 5"

    def test_escape_double_quote(self):
        """Should escape \" to &quot;."""
        assert escape_html('Say "Hello"') == "Say &quot;Hello&quot;"

    def test_escape_single_quote(self):
        """Should escape ' to &#39;."""
        assert escape_html("It's working") == "It&#39;s working"

    def test_escape_multiple_characters(self):
        """Should escape multiple special characters."""
        assert escape_html('<script>alert("XSS")</script>') == "&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;"

    def test_none_returns_empty_string(self):
        """Should return empty string for None input."""
        assert escape_html(None) == ""

    def test_numeric_input_converted_to_string(self):
        """Should convert numeric input to string."""
        assert escape_html(42) == "42"
        assert escape_html(3.14) == "3.14"

    def test_already_safe_text_unchanged(self):
        """Should not modify text without special characters."""
        assert escape_html("Safe text 123") == "Safe text 123"


class TestGenerateTableHtml:
    """Test suite for HTML table generation."""

    def test_empty_headers_returns_no_data_message(self):
        """Should return no data message for empty headers."""
        html = generate_table_html([], [], "test-table")
        assert "No data available" in html

    def test_empty_rows_returns_no_data_message(self):
        """Should return no data message for empty rows."""
        html = generate_table_html(["Col1", "Col2"], [], "test-table")
        assert "No data available" in html

    def test_table_with_sortable_headers(self):
        """Should generate sortable table headers by default."""
        headers = ["Name", "Price", "Size"]
        rows = [["Species A", "25.00", "1.0"]]
        html = generate_table_html(headers, rows, "test-table", sortable=True)
        
        assert '<table id="test-table" class="data-table">' in html
        assert 'onclick="sortTable(0, \'test-table\')"' in html
        assert '<span class="sort-indicator">⇅</span>' in html

    def test_table_without_sortable_headers(self):
        """Should generate non-sortable table headers when sortable=False."""
        headers = ["Name", "Price"]
        rows = [["Species A", "25.00"]]
        html = generate_table_html(headers, rows, "test-table", sortable=False)
        
        assert '<table id="test-table" class="data-table">' in html
        assert 'onclick=' not in html
        assert 'sort-indicator' not in html

    def test_table_escapes_html_in_cells(self):
        """Should escape HTML special characters in table cells."""
        headers = ["Name", "Description"]
        rows = [["<script>", "Tom & Jerry"]]
        html = generate_table_html(headers, rows, "test-table")
        
        assert "&lt;script&gt;" in html
        assert "Tom &amp; Jerry" in html

    def test_table_with_multiple_rows(self):
        """Should generate table with multiple data rows."""
        headers = ["A", "B"]
        rows = [["1", "2"], ["3", "4"], ["5", "6"]]
        html = generate_table_html(headers, rows, "test-table")
        
        assert html.count("<tr>") == 4  # 1 header + 3 data rows
        assert "<td>1</td>" in html
        assert "<td>6</td>" in html

    def test_table_structure_complete(self):
        """Should generate complete table structure with thead and tbody."""
        headers = ["Col"]
        rows = [["Val"]]
        html = generate_table_html(headers, rows, "test-table")
        
        assert "<thead>" in html
        assert "</thead>" in html
        assert "<tbody>" in html
        assert "</tbody>" in html
        assert "</table>" in html

    def test_table_renders_page_url_as_link(self):
        """Should render page_url column as clickable link with scientific name as text."""
        headers = ["scientific_name", "common_name", "price_gbp", "page_url"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "25.00", "https://example.com/species1"],
            ["Grammostola rosea", "Chilean Rose", "15.00", "https://example.com/species2"]
        ]
        html = generate_table_html(headers, rows, "test-table")
        
        # Check that links are created with scientific names as text
        assert '<a href="https://example.com/species1" target="_blank" rel="noopener noreferrer">Brachypelma hamorii</a>' in html
        assert '<a href="https://example.com/species2" target="_blank" rel="noopener noreferrer">Grammostola rosea</a>' in html
        
        # Verify links open in new tab with security attributes
        assert 'target="_blank"' in html
        assert 'rel="noopener noreferrer"' in html

    def test_table_handles_empty_page_url(self):
        """Should handle empty page_url gracefully without creating a link."""
        headers = ["scientific_name", "common_name", "page_url"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "https://example.com/species1"],
            ["Grammostola rosea", "Chilean Rose", ""],  # Empty URL
            ["Aphonopelma seemanni", "Costa Rican Zebra", "   "]  # Whitespace only
        ]
        html = generate_table_html(headers, rows, "test-table")
        
        # First row should have link
        assert '<a href="https://example.com/species1"' in html
        assert '>Brachypelma hamorii</a>' in html
        
        # Empty URL rows should not have links - just render the cell value
        assert html.count('<a href=') == 1  # Only one link should exist

    def test_table_without_page_url_column(self):
        """Should render normally when page_url column doesn't exist."""
        headers = ["scientific_name", "common_name", "price_gbp"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "25.00"],
            ["Grammostola rosea", "Chilean Rose", "15.00"]
        ]
        html = generate_table_html(headers, rows, "test-table")
        
        # Should not create any links
        assert '<a href=' not in html
        assert 'target="_blank"' not in html
        
        # Should render data normally
        assert "Brachypelma hamorii" in html
        assert "Mexican Red Knee" in html

    def test_table_with_page_url_but_no_scientific_name(self):
        """Should render normally when scientific_name column is missing."""
        headers = ["common_name", "price_gbp", "page_url"]
        rows = [
            ["Mexican Red Knee", "25.00", "https://example.com/species1"],
            ["Chilean Rose", "15.00", "https://example.com/species2"]
        ]
        html = generate_table_html(headers, rows, "test-table")
        
        # Should not create links without scientific_name column
        assert '<a href=' not in html
        assert 'target="_blank"' not in html
        
        # Should render URLs as plain text
        assert "https://example.com/species1" in html
        assert "https://example.com/species2" in html


class TestGetBaseHtmlTemplate:
    """Test suite for base HTML template generation."""

    def test_includes_doctype_and_html_tags(self):
        """Should include DOCTYPE and html tags."""
        html = get_base_html_template("Test Page")
        assert "<!DOCTYPE html>" in html
        assert "<html lang=\"en\">" in html
        assert "</html>" not in html  # Base template doesn't close html

    def test_includes_title_in_head(self):
        """Should include title in head section."""
        html = get_base_html_template("My Page")
        assert "<title>My Page - Spider Shop Historical Analysis</title>" in html

    def test_includes_viewport_meta(self):
        """Should include viewport meta tag for responsive design."""
        html = get_base_html_template("Test")
        assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in html

    def test_includes_navigation(self):
        """Should include navigation menu."""
        html = get_base_html_template("Test", "home")
        assert "<nav>" in html
        assert '<a href="index.html"' in html
        assert '<a href="snapshot.html"' in html
        assert '<a href="history.html"' in html
        assert '<a href="breeder.html"' in html
        assert '<a href="dealer.html"' in html

    def test_active_page_home(self):
        """Should mark home page as active."""
        html = get_base_html_template("Test", "home")
        assert 'class="active"' in html
        # Count should match only home link
        assert html.count('class="active"') >= 1

    def test_active_page_snapshot(self):
        """Should mark snapshot page as active."""
        html = get_base_html_template("Test", "snapshot")
        assert 'snapshot.html" class="active"' in html or 'class="active"' in html

    def test_includes_css_styles(self):
        """Should include embedded CSS styles."""
        html = get_base_html_template("Test")
        assert "<style>" in html
        assert "</style>" in html
        assert ".data-table" in html
        assert "font-family:" in html

    def test_includes_header(self):
        """Should include page header with title."""
        html = get_base_html_template("Test")
        assert "<header>" in html
        assert "Spider Shop Historical Analysis" in html

    def test_opens_container_div(self):
        """Should open container div."""
        html = get_base_html_template("Test")
        assert '<div class="container">' in html


class TestGetHtmlFooter:
    """Test suite for HTML footer generation."""

    def test_includes_footer_tag(self):
        """Should include footer tag."""
        html = get_html_footer()
        assert "<footer>" in html
        assert "</footer>" in html

    def test_includes_source_link(self):
        """Should include link to source website."""
        html = get_html_footer()
        assert "thespidershop.co.uk" in html
        assert 'target="_blank"' in html

    def test_includes_github_link(self):
        """Should include GitHub repository link."""
        html = get_html_footer()
        assert "github.com/christianacca/spidershop-historical-analysis" in html

    def test_includes_timestamp(self):
        """Should include generated timestamp."""
        html = get_html_footer()
        assert "Generated:" in html
        assert "UTC" in html

    def test_includes_javascript_functions(self):
        """Should include JavaScript for table sorting and filtering."""
        html = get_html_footer()
        assert "function sortTable(" in html
        assert "function filterTable(" in html

    def test_closes_html_tags(self):
        """Should close body and html tags."""
        html = get_html_footer()
        assert "</body>" in html
        assert "</html>" in html

    def test_javascript_handles_numeric_sorting(self):
        """JavaScript should include numeric sort logic."""
        html = get_html_footer()
        assert "isNumeric" in html
        assert "parseFloat" in html

    def test_javascript_handles_string_sorting(self):
        """JavaScript should include string sort logic."""
        html = get_html_footer()
        assert "toLowerCase" in html
        assert "localeCompare" in html


class TestGenerateHomepage:
    """Test suite for homepage generation."""

    def test_generates_complete_html_page(self):
        """Should generate complete HTML page with header and footer."""
        html = generate_homepage()
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        assert "<header>" in html
        assert "<footer>" in html

    def test_includes_welcome_heading(self):
        """Should include welcome heading."""
        html = generate_homepage()
        assert "Welcome to Spider Shop Historical Analysis" in html

    def test_includes_last_scrape_time_when_provided(self):
        """Should display last scrape time when provided."""
        html = generate_homepage("2025-01-15 12:00:00")
        assert "Last Updated:" in html
        assert "2025-01-15 12:00:00" in html

    def test_omits_last_scrape_time_when_none(self):
        """Should omit last scrape time section when None."""
        html = generate_homepage(None)
        assert "Last Updated:" not in html

    def test_includes_card_grid_with_links(self):
        """Should include card grid with navigation links."""
        html = generate_homepage()
        assert "card-grid" in html
        assert "Latest Snapshot" in html
        assert "Historical Data" in html
        assert "Breeder Opportunities" in html
        assert "Dealer Supply Risk" in html

    def test_includes_download_links_section(self):
        """Should include download links for CSV files."""
        html = generate_homepage()
        assert "Download Raw Data" in html
        assert "spidershop_spiderlings_scrape.csv" in html
        assert "spidershop_spiderlings_history.csv" in html
        assert "breeder_opportunity_table.csv" in html
        assert "dealer_supply_risk_table.csv" in html

    def test_includes_about_section(self):
        """Should include about section describing the project."""
        html = generate_homepage()
        assert "About This Project" in html
        assert "automatically scrapes" in html.lower()

    def test_includes_data_description(self):
        """Should describe what data is collected."""
        html = generate_homepage()
        assert "Scientific name" in html
        assert "Common name" in html
        assert "Size" in html
        assert "Price" in html

    def test_active_page_is_home(self):
        """Should mark home as active page in navigation."""
        html = generate_homepage()
        # The template should have home as active
        assert 'active' in html


class TestGenerateDataPage:
    """Test suite for data page generation."""

    def test_generates_complete_html_page(self):
        """Should generate complete HTML page."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Name,Price\n")
            f.write("Species A,25.00\n")
            filename = f.name
        
        try:
            html = generate_data_page(
                "Test Page",
                "Test description",
                filename,
                "test-table",
                "snapshot"
            )
            assert "<!DOCTYPE html>" in html
            assert "</html>" in html
        finally:
            os.unlink(filename)

    def test_includes_title_and_description(self):
        """Should include page title and description."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            html = generate_data_page(
                "My Title",
                "My description text",
                filename,
                "test-table",
                "snapshot"
            )
            assert "My Title" in html
            assert "My description text" in html
        finally:
            os.unlink(filename)

    def test_includes_download_link(self):
        """Should include download link for CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = os.path.basename(f.name)
            temp_name = f.name
        
        try:
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot"
            )
            assert f'href="{filename}"' in html
            assert "Download CSV" in html
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def test_includes_search_filter_when_enabled(self):
        """Should include search filter when search_filter=True."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\nVal\n")
            filename = f.name
        
        try:
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                search_filter=True
            )
            assert "Search:" in html
            assert "filterTable" in html
        finally:
            os.unlink(filename)

    def test_omits_search_filter_when_disabled(self):
        """Should omit search filter when search_filter=False."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\nVal\n")
            filename = f.name
        
        try:
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                search_filter=False
            )
            assert "Search:" not in html or "table-controls" not in html
        finally:
            os.unlink(filename)

    def test_includes_data_table_from_csv(self):
        """Should include data table generated from CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Name,Price\n")
            f.write("Species A,25.00\n")
            f.write("Species B,30.00\n")
            filename = f.name
        
        try:
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot"
            )
            assert "<h3>Full Data Table</h3>" in html
            assert "<table" in html
            assert "Species A" in html
            assert "25.00" in html
            assert "Total rows:" in html
            assert "2" in html  # Two data rows
        finally:
            os.unlink(filename)

    def test_handles_nonexistent_csv_file(self):
        """Should show 'no data' message for nonexistent file."""
        html = generate_data_page(
            "Test",
            "Desc",
            "/nonexistent/file.csv",
            "test-table",
            "snapshot"
        )
        assert "No data available" in html
        assert "<table" not in html

    def test_includes_analysis_markdown_when_provided(self):
        """Should include analysis section when markdown provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            analysis_md = "## Analysis\n\nThis is **important** analysis."
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                analysis_markdown=analysis_md
            )
            assert 'class="analysis-section"' in html
            # h2 is downgraded to h3 for proper heading hierarchy
            assert "<h3>Analysis</h3>" in html
            assert "<strong>important</strong>" in html
        finally:
            os.unlink(filename)

    def test_omits_analysis_section_when_none(self):
        """Should omit analysis section when markdown not provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                analysis_markdown=None
            )
            assert 'class="analysis-section"' not in html
        finally:
            os.unlink(filename)

    def test_includes_legend_when_provided(self):
        """Should include legend in details block when provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            legend_md = "**Legend**: This explains the symbols."
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                legend_markdown=legend_md
            )
            assert "<details>" in html
            assert "How to read these tables" in html
            assert "<strong>Legend</strong>" in html
        finally:
            os.unlink(filename)

    def test_omits_legend_when_none(self):
        """Should omit legend when not provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                legend_markdown=None
            )
            assert "How to read these tables" not in html or "<details>" not in html
        finally:
            os.unlink(filename)


class TestIntegration:
    """Integration tests for the website generation workflow."""

    def test_full_page_generation_with_all_features(self):
        """Should generate complete page with all features enabled."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Price,Size\n")
            f.write("Aphonopelma seemanni,25.00,1.0\n")
            f.write("Grammostola pulchra,40.00,2.0\n")
            csv_file = f.name
        
        try:
            analysis_md = """## Analysis

This is the **analysis** section with *formatting*.

| Metric | Value |
|--------|-------|
| Count  | 2     |"""

            legend_md = "**Symbol**: Meaning of symbol."
            
            html = generate_data_page(
                "Test Page",
                "Description here",
                csv_file,
                "test-table",
                "snapshot",
                search_filter=True,
                analysis_markdown=analysis_md,
                legend_markdown=legend_md
            )
            
            # Verify all components present
            assert "<!DOCTYPE html>" in html
            assert "Test Page" in html
            assert "Description here" in html
            assert "Download CSV" in html
            assert "Search:" in html
            assert "Aphonopelma seemanni" in html
            assert "Grammostola pulchra" in html
            assert "analysis-section" in html
            assert "<strong>analysis</strong>" in html
            assert "<details>" in html
            assert "Symbol" in html
            assert "</html>" in html
        finally:
            os.unlink(csv_file)

    def test_handles_empty_csv_gracefully(self):
        """Should handle empty CSV file without errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            csv_file = f.name
        
        try:
            html = generate_data_page(
                "Empty Data",
                "No data test",
                csv_file,
                "test-table",
                "snapshot"
            )
            assert "No data available" in html
            assert "<!DOCTYPE html>" in html
            assert "</html>" in html
        finally:
            os.unlink(csv_file)

    def test_html_escaping_prevents_injection(self):
        """Should properly escape HTML to prevent injection attacks."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Name,Script\n")
            f.write('<script>alert("xss")</script>,<img src=x onerror=alert(1)>\n')
            csv_file = f.name
        
        try:
            html = generate_data_page(
                "<script>bad</script>",
                "<b>Description</b>",
                csv_file,
                "test-table",
                "snapshot"
            )
            # Verify escaping
            assert "&lt;script&gt;" in html
            assert "<script>alert" not in html
            assert "&lt;img src=" in html
        finally:
            os.unlink(csv_file)

    def test_main_function_generates_website(self):
        """Should execute main() function and generate website files."""
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            
            try:
                # Change to temp directory
                os.chdir(tmpdir)
                
                # Create minimal test CSV files
                with open("spidershop_spiderlings_scrape.csv", "w", encoding="utf-8") as f:
                    f.write("scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n")
                    f.write("2025-01-01,Aphonopelma seemanni,Test Spider,1.0,25.00,5,https://example.com\n")
                
                with open("spidershop_spiderlings_history.csv", "w", encoding="utf-8") as f:
                    f.write("scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n")
                    f.write("2025-01-01,Aphonopelma seemanni,Test Spider,1.0,25.00,5,https://example.com\n")
                
                with open("breeder_opportunity_table.csv", "w", encoding="utf-8") as f:
                    f.write("Species,Signal\n")
                    f.write("Aphonopelma seemanni,🔥\n")
                
                with open("dealer_supply_risk_table.csv", "w", encoding="utf-8") as f:
                    f.write("Species,Risk\n")
                    f.write("Aphonopelma seemanni,Low\n")
                
                with open("analysis_summary.md", "w", encoding="utf-8") as f:
                    f.write("## 🧬 Breeder Opportunity Matrix (Top 10)\n\nBreeder content\n\n")
                    f.write("## 🏪 Dealer Supply Risk Matrix (Top 10)\n\nDealer content\n\n")
                    f.write("<details><summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>\n")
                    f.write("### 🧬 Breeder Opportunity Matrix — Legend\nLegend content\n")
                    f.write("### 📖 Breeder Matrix — Practical Examples\nExample content\n")
                    f.write("### 🏪 Dealer Supply Risk Matrix — Legend\nLegend content\n")
                    f.write("### 📖 Dealer Matrix — Practical Examples\nExample content\n</details>")
                
                # Run main function
                main()
                
                # Verify output directory and files were created
                assert OUTPUT_DIR.exists()
                assert (OUTPUT_DIR / "index.html").exists()
                assert (OUTPUT_DIR / "snapshot.html").exists()
                assert (OUTPUT_DIR / "history.html").exists()
                assert (OUTPUT_DIR / "breeder.html").exists()
                assert (OUTPUT_DIR / "dealer.html").exists()
                
                # Verify CSV files were copied
                assert (OUTPUT_DIR / "spidershop_spiderlings_scrape.csv").exists()
                assert (OUTPUT_DIR / "spidershop_spiderlings_history.csv").exists()
                assert (OUTPUT_DIR / "breeder_opportunity_table.csv").exists()
                assert (OUTPUT_DIR / "dealer_supply_risk_table.csv").exists()
                
                # Verify HTML content
                with open(OUTPUT_DIR / "index.html", "r", encoding="utf-8") as f:
                    index_html = f.read()
                    assert "Spider Shop Historical Analysis" in index_html
                    assert "2025-01-01" in index_html  # Last scrape time
                
                with open(OUTPUT_DIR / "breeder.html", "r", encoding="utf-8") as f:
                    breeder_html = f.read()
                    assert "Breeder content" in breeder_html
                    assert "Legend content" in breeder_html
                
            finally:
                # Restore original directory
                os.chdir(original_dir)

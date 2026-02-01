#!/usr/bin/env python3
"""
Tests for HTML utility functions including escaping, table generation, and templates.
"""

import pytest
from pathlib import Path
from bs4 import BeautifulSoup
from website import (
    escape_html,
    generate_table_html,
    get_base_html_template,
    get_html_footer,
)


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
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verify table structure
        table = soup.find('table', id='test-table', class_='data-table')
        assert table is not None
        
        # Verify sortable headers have onclick
        headers_elements = table.select('thead th')
        assert len(headers_elements) == 3
        for i, th in enumerate(headers_elements):
            assert 'onclick' in th.attrs
            assert f"sortTable({i}, 'test-table')" in th['onclick']
            # Verify sort indicator present
            indicator = th.find('span', class_='sort-indicator')
            assert indicator is not None
            assert indicator.text == '⇅'

    def test_table_without_sortable_headers(self):
        """Should generate non-sortable table headers when sortable=False."""
        headers = ["Name", "Price"]
        rows = [["Species A", "25.00"]]
        html = generate_table_html(headers, rows, "test-table", sortable=False)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verify table structure
        table = soup.find('table', id='test-table', class_='data-table')
        assert table is not None
        
        # Verify headers do NOT have onclick or sort indicators
        headers_elements = table.select('thead th')
        assert len(headers_elements) == 2
        for th in headers_elements:
            assert 'onclick' not in th.attrs
            indicator = th.find('span', class_='sort-indicator')
            assert indicator is None

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
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verify table structure
        table = soup.find('table', id='test-table')
        assert table is not None
        
        # Count rows: 1 header row + 3 data rows
        all_rows = table.find_all('tr')
        assert len(all_rows) == 4
        
        # Verify data rows
        data_rows = table.select('tbody tr')
        assert len(data_rows) == 3
        
        # Verify first and last cell content
        first_cell = data_rows[0].find('td')
        assert first_cell.text == '1'
        last_cell = data_rows[-1].find_all('td')[-1]
        assert last_cell.text == '6'

    def test_table_structure_complete(self):
        """Should generate complete table structure with thead and tbody."""
        headers = ["Col"]
        rows = [["Val"]]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verify table exists
        table = soup.find('table', id='test-table')
        assert table is not None
        
        # Verify table has proper structure
        thead = table.find('thead')
        tbody = table.find('tbody')
        assert thead is not None
        assert tbody is not None
        
        # Verify header and data
        th = thead.find('th')
        assert th is not None
        assert th.text.strip().startswith('Col')
        
        td = tbody.find('td')
        assert td is not None
        assert td.text == 'Val'

    def test_table_renders_page_url_as_link(self):
        """Should render page_url column as clickable link with scientific name as text."""
        headers = ["scientific_name", "common_name", "price_gbp", "page_url"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "25.00", "https://example.com/species1"],
            ["Grammostola rosea", "Chilean Rose", "15.00", "https://example.com/species2"]
        ]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all data rows
        data_rows = soup.select('tbody tr')
        assert len(data_rows) == 2
        
        # Check first row link
        first_row_cells = data_rows[0].find_all('td')
        page_url_cell = first_row_cells[3]  # Fourth column
        link = page_url_cell.find('a')
        assert link is not None
        assert link['href'] == 'https://example.com/species1'
        assert link.text == 'Brachypelma hamorii'
        assert link['target'] == '_blank'
        assert 'noopener' in link['rel']
        assert 'noreferrer' in link['rel']
        
        # Check second row link
        second_row_cells = data_rows[1].find_all('td')
        page_url_cell = second_row_cells[3]
        link = page_url_cell.find('a')
        assert link is not None
        assert link['href'] == 'https://example.com/species2'
        assert link.text == 'Grammostola rosea'

    def test_table_handles_empty_page_url(self):
        """Should handle empty page_url gracefully without creating a link."""
        headers = ["scientific_name", "common_name", "page_url"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "https://example.com/species1"],
            ["Grammostola rosea", "Chilean Rose", ""],  # Empty URL
            ["Aphonopelma seemanni", "Costa Rican Zebra", "   "]  # Whitespace only
        ]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all data rows
        data_rows = soup.select('tbody tr')
        assert len(data_rows) == 3
        
        # First row should have link
        first_row_url_cell = data_rows[0].find_all('td')[2]
        first_link = first_row_url_cell.find('a')
        assert first_link is not None
        assert first_link['href'] == 'https://example.com/species1'
        assert first_link.text == 'Brachypelma hamorii'
        
        # Second row should NOT have link (empty URL)
        second_row_url_cell = data_rows[1].find_all('td')[2]
        second_link = second_row_url_cell.find('a')
        assert second_link is None
        
        # Third row should NOT have link (whitespace URL)
        third_row_url_cell = data_rows[2].find_all('td')[2]
        third_link = third_row_url_cell.find('a')
        assert third_link is None

    def test_table_without_page_url_column(self):
        """Should render normally when page_url column doesn't exist."""
        headers = ["scientific_name", "common_name", "price_gbp"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "25.00"],
            ["Grammostola rosea", "Chilean Rose", "15.00"]
        ]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should not create any links
        links = soup.find_all('a')
        assert len(links) == 0
        
        # Should render data normally
        assert soup.find(string='Brachypelma hamorii') is not None
        assert soup.find(string='Mexican Red Knee') is not None

    def test_table_with_page_url_but_no_scientific_name(self):
        """Should render normally when scientific_name column is missing."""
        headers = ["common_name", "price_gbp", "page_url"]
        rows = [
            ["Mexican Red Knee", "25.00", "https://example.com/species1"],
            ["Chilean Rose", "15.00", "https://example.com/species2"]
        ]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should not create links without scientific_name column
        links = soup.find_all('a')
        assert len(links) == 0
        
        # Should render URLs as plain text
        assert soup.find(string='https://example.com/species1') is not None
        assert soup.find(string='https://example.com/species2') is not None


class TestGetBaseHtmlTemplate:
    """Test suite for base HTML template generation."""

    def test_includes_doctype_and_html_tags(self):
        """Should include DOCTYPE and html tags."""
        html = get_base_html_template("Test Page")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check DOCTYPE (not parsed by BeautifulSoup, check raw string)
        assert "<!DOCTYPE html>" in html
        
        # Check html tag with lang attribute
        html_tag = soup.find('html')
        assert html_tag is not None
        assert html_tag.get('lang') == 'en'
        
        # Base template doesn't close html (partial template)
        assert "</html>" not in html

    def test_includes_title_in_head(self):
        """Should include title in head section."""
        html = get_base_html_template("My Page")
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.find('title')
        assert title is not None
        assert title.text == "My Page - Spider Shop Historical Analysis"

    def test_includes_viewport_meta(self):
        """Should include viewport meta tag for responsive design."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        assert viewport_meta is not None
        assert viewport_meta['content'] == 'width=device-width, initial-scale=1.0'

    def test_includes_navigation(self):
        """Should include navigation menu."""
        html = get_base_html_template("Test", "home")
        soup = BeautifulSoup(html, 'html.parser')
        
        nav = soup.find('nav')
        assert nav is not None
        
        # Check for all expected navigation links
        links = nav.find_all('a')
        assert len(links) == 5
        
        hrefs = [link['href'] for link in links]
        assert 'index.html' in hrefs
        assert 'snapshot.html' in hrefs
        assert 'history.html' in hrefs
        assert 'breeder.html' in hrefs
        assert 'dealer.html' in hrefs

    def test_active_page_home(self):
        """Should mark home page as active."""
        html = get_base_html_template("Test", "home")
        soup = BeautifulSoup(html, 'html.parser')
        
        active_links = soup.select('nav a.active')
        assert len(active_links) == 1
        assert active_links[0]['href'] == 'index.html'

    def test_active_page_snapshot(self):
        """Should mark snapshot page as active."""
        html = get_base_html_template("Test", "snapshot")
        soup = BeautifulSoup(html, 'html.parser')
        
        active_links = soup.select('nav a.active')
        assert len(active_links) == 1
        assert active_links[0]['href'] == 'snapshot.html'

    def test_includes_css_styles(self):
        """Should include embedded CSS styles."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        style = soup.find('style')
        assert style is not None
        css_content = style.string
        assert '.data-table' in css_content
        assert 'font-family:' in css_content

    def test_includes_header(self):
        """Should include page header with title."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        header = soup.find('header')
        assert header is not None
        assert 'Spider Shop Historical Analysis' in header.text

    def test_opens_container_div(self):
        """Should open container div."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        container = soup.find('div', class_='container')
        assert container is not None


class TestGetHtmlFooter:
    """Test suite for HTML footer generation."""

    def test_includes_footer_tag(self):
        """Should include footer tag."""
        html = get_html_footer()
        soup = BeautifulSoup(html, 'html.parser')
        
        footer = soup.find('footer')
        assert footer is not None

    def test_includes_source_link(self):
        """Should include link to source website."""
        html = get_html_footer()
        soup = BeautifulSoup(html, 'html.parser')
        
        footer = soup.find('footer')
        links = footer.find_all('a')
        
        # Find the spider shop link
        spider_shop_links = [link for link in links if 'thespidershop.co.uk' in link['href']]
        assert len(spider_shop_links) == 1
        assert spider_shop_links[0]['target'] == '_blank'

    def test_includes_github_link(self):
        """Should include GitHub repository link."""
        html = get_html_footer()
        soup = BeautifulSoup(html, 'html.parser')
        
        footer = soup.find('footer')
        links = footer.find_all('a')
        
        github_links = [link for link in links if 'github.com/christianacca/spidershop-historical-analysis' in link['href']]
        assert len(github_links) == 1

    def test_includes_timestamp(self):
        """Should include generated timestamp."""
        html = get_html_footer()
        soup = BeautifulSoup(html, 'html.parser')
        
        footer = soup.find('footer')
        footer_text = footer.text
        assert 'Generated:' in footer_text
        assert 'UTC' in footer_text

    def test_includes_javascript_functions(self):
        """Should include JavaScript reference for table sorting and filtering."""
        html = get_html_footer()
        soup = BeautifulSoup(html, 'html.parser')
        
        script = soup.find('script')
        assert script is not None
        # Should reference external JS file
        assert script.get('src') == 'table-interactions.js'

    def test_closes_html_tags(self):
        """Should close body and html tags."""
        html = get_html_footer()
        # These closing tags are at the end of the string
        assert "</body>" in html
        assert "</html>" in html

    def test_javascript_handles_numeric_sorting(self):
        """JavaScript file should exist and contain numeric sort logic."""
        # Read the external JavaScript file
        js_file = Path(__file__).parent.parent.parent / "templates" / "scripts" / "table-interactions.js"
        assert js_file.exists(), "JavaScript file should exist"
        
        js_content = js_file.read_text()
        assert 'isNumeric' in js_content
        assert 'parseFloat' in js_content

    def test_javascript_handles_string_sorting(self):
        """JavaScript file should exist and contain string sort logic."""
        # Read the external JavaScript file
        js_file = Path(__file__).parent.parent.parent / "templates" / "scripts" / "table-interactions.js"
        assert js_file.exists(), "JavaScript file should exist"
        
        js_content = js_file.read_text()
        assert 'toLowerCase' in js_content
        assert 'localeCompare' in js_content

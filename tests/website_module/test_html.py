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

    def test_table_escapes_html_in_cells(self):
        """Should escape HTML special characters in table cells."""
        headers = ["Name", "Description"]
        rows = [["<script>", "Tom & Jerry"]]
        html = generate_table_html(headers, rows, "test-table")
        
        assert "&lt;script&gt;" in html
        assert "Tom &amp; Jerry" in html

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

    def test_signal_cells_with_drivers_column_use_custom_tooltips(self):
        """Signal cells should use custom tooltip spans (not title attribute) when Drivers column present."""
        headers = ["Species", "Signal", "Drivers"]
        rows = [
            ["Test Spider", "🔥", "Stock: Sustained (OOS 5 runs; currently OUT); Demand: High; Price: Rising"],
        ]
        
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the Signal cell
        signal_cell = soup.select('tbody tr td.signal-hot')[0]
        
        # Should contain info icon with custom tooltip span
        info_icon = signal_cell.find('span', class_='info-icon')
        assert info_icon is not None, "Should have info-icon span"
        
        # Should NOT use title attribute
        assert 'title' not in info_icon.attrs, "Should not use native title attribute"
        
        # Should contain nested tooltip span with drivers text
        tooltip_span = info_icon.find('span', class_='tooltip')
        assert tooltip_span is not None, "Should have nested tooltip span"
        assert "Stock: Sustained" in tooltip_span.text
        assert "OOS 5 runs" in tooltip_span.text
        
        # Should have tabindex for keyboard accessibility
        assert info_icon.get('tabindex') == '0', "Should be keyboard accessible"
        
        # Drivers column should be completely hidden (not rendered at all)
        all_cells = soup.select('tbody tr td')
        assert len(all_cells) == 2, f"Expected 2 cells (Species, Signal), Drivers column should be hidden, got {len(all_cells)}"
        
        # Verify Drivers column header is also hidden
        headers_rendered = soup.select('thead tr th')
        assert len(headers_rendered) == 2, "Drivers column header should also be hidden"
        header_texts = [th.text.strip() for th in headers_rendered]
        assert "Species" in header_texts[0]
        assert "Signal" in header_texts[1]
        assert "Drivers" not in str(soup), "Drivers column should not appear anywhere in rendered HTML"

    def test_signal_cells_without_drivers_column_have_no_tooltips(self):
        """Signal cells should not have info icons when Drivers column is absent."""
        headers = ["Species", "Signal"]
        rows = [
            ["Test Spider", "🔥"],
        ]
        
        html = generate_table_html(headers, rows, "test-table")  # No drivers_col_idx
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the Signal cell
        signal_cell = soup.select('tbody tr td.signal-hot')[0]
        
        # Should NOT contain info icon
        info_icon = signal_cell.find('span', class_='info-icon')
        assert info_icon is None, "Should not have info icon when Drivers column missing"


class TestGetBaseHtmlTemplate:
    """Test suite for base HTML template generation - structural requirements not covered by E2E."""

    def test_includes_doctype_and_html_tags(self):
        """Should include DOCTYPE and html tags with lang attribute."""
        html = get_base_html_template("Test Page")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check DOCTYPE (not parsed by BeautifulSoup, check raw string)
        assert "<!DOCTYPE html>" in html
        
        # Check html tag with lang attribute
        html_tag = soup.find('html')
        assert html_tag is not None
        assert html_tag.get('lang') == 'en'

    def test_includes_viewport_meta(self):
        """Should include viewport meta tag for responsive design."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        assert viewport_meta is not None
        assert viewport_meta['content'] == 'width=device-width, initial-scale=1.0'

    def test_includes_navigation(self):
        """Should include navigation menu with all expected links."""
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
        
        active_links = soup.select('nav a.nav__link--active')
        assert len(active_links) == 1
        assert active_links[0]['href'] == 'index.html'

    def test_active_page_snapshot(self):
        """Should mark snapshot page as active."""
        html = get_base_html_template("Test", "snapshot")
        soup = BeautifulSoup(html, 'html.parser')
        
        active_links = soup.select('nav a.nav__link--active')
        assert len(active_links) == 1
        assert active_links[0]['href'] == 'snapshot.html'

    def test_includes_css_links(self):
        """Should include CSS stylesheet links in head."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        css_links = soup.find_all('link', rel='stylesheet')
        assert len(css_links) > 0, "No CSS links found"
        
        css_hrefs = [link.get('href', '') for link in css_links]
        assert any('common.css' in href for href in css_hrefs), "Missing common.css link"

    def test_includes_header(self):
        """Should include page header with site title."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        header = soup.find('header')
        assert header is not None
        assert 'Spider Shop Historical Analysis' in header.text

    def test_opens_container_div(self):
        """Should open container div for page content."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        container = soup.find('div', class_='container')
        assert container is not None


class TestGetHtmlFooter:
    """Test suite for HTML footer generation - structural requirements not covered by E2E."""

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

    def test_includes_javascript_reference(self):
        """Should include JavaScript file reference."""
        html = get_html_footer()
        soup = BeautifulSoup(html, 'html.parser')
        
        script = soup.find('script')
        assert script is not None
        assert script.get('src') == 'table-interactions.js'

    def test_closes_html_tags(self):
        """Should close body and html tags."""
        html = get_html_footer()
        # These closing tags are at the end of the string
        assert "</body>" in html
        assert "</html>" in html


class TestSpeciesPageLinking:
    """Test internal linking to species detail pages for breeder/dealer tables."""

    def test_breeder_table_links_to_species_pages_internally(self):
        """Breeder tables should link to internal species pages, not external Spider Shop."""
        headers = ["Species", "Size (cm)", "Signal", "page_url"]
        rows = [
            ["Brachypelma hamorii", "2.0", "🔥", "https://example.com/external"],
        ]
        
        html = generate_table_html(headers, rows, "breeder-table", link_to_species_page=True)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the Species column link
        data_rows = soup.select('tbody tr')
        first_row = data_rows[0]
        species_cell = first_row.find_all('td')[0]  # First column
        link = species_cell.find('a')
        
        # Should link to internal species page
        assert link is not None
        assert 'species/' in link['href']
        assert 'brachypelma-hamorii' in link['href']  # Slugified
        assert '?view=breeder' in link['href'] or '&view=breeder' in link['href']  # Include view parameter
        assert 'size=2.0' in link['href']  # Include size
        assert link.text == 'Brachypelma hamorii'
        
        # Should NOT be external link (no target="_blank")
        assert 'target' not in link.attrs or link.get('target') != '_blank'

    def test_dealer_table_links_to_species_pages_internally(self):
        """Dealer tables should link to internal species pages with dealer view."""
        headers = ["Species", "Size (cm)", "Dealer Risk", "page_url"]
        rows = [
            ["Tliltocatl albopilosus", "1.5", "⚠️", "https://example.com/external"],
        ]
        
        html = generate_table_html(headers, rows, "dealer-table", link_to_species_page=True, table_view="dealer")
        soup = BeautifulSoup(html, 'html.parser')
        
        data_rows = soup.select('tbody tr')
        first_row = data_rows[0]
        species_cell = first_row.find_all('td')[0]
        link = species_cell.find('a')
        
        assert link is not None
        assert 'species/' in link['href']
        assert 'tliltocatl-albopilosus' in link['href']
        assert '?view=dealer' in link['href'] or '&view=dealer' in link['href']  # Dealer view parameter
        assert 'size=1.5' in link['href']

    def test_history_table_keeps_external_links(self):
        """History tables should keep external Spider Shop links (no change)."""
        headers = ["scientific_name", "common_name", "page_url"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "https://thespidershop.co.uk/product/123"],
        ]
        
        # Default behavior (link_to_species_page=False or omitted)
        html = generate_table_html(headers, rows, "history-table")
        soup = BeautifulSoup(html, 'html.parser')
        
        data_rows = soup.select('tbody tr')
        first_row = data_rows[0]
        page_url_cell = first_row.find_all('td')[2]  # Third column
        link = page_url_cell.find('a')
        
        # Should be external link
        assert link is not None
        assert link['href'] == 'https://thespidershop.co.uk/product/123'
        assert link['target'] == '_blank'  # External link behavior

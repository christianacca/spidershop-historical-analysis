#!/usr/bin/env python3
"""
Tests for HTML utility functions including escaping, table generation, and templates.
"""

import pytest
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from website import (
    escape_html,
    generate_table_html,
    get_base_html_template,
    get_html_footer,
)


def _table_json(html: str) -> list:
    """Extract and parse the window['...Data'] JSON from a rendered page."""
    m = re.search(r"window\['[^']+Data'\]\s*=\s*(\[.*?\])\s*;", html, re.DOTALL)
    return json.loads(m.group(1)) if m else []


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
        """HTML special characters in cell data should be safely JSON-encoded in the payload."""
        headers = ["Name", "Description"]
        rows = [["<script>", "Tom & Jerry"]]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')

        # Rows are now rendered by Svelte — table has a mount div
        mount_div = soup.find('div', id='test-table-root')
        assert mount_div is not None, "Mount div should be present"

        # JSON payload encodes HTML-unsafe characters with \\uXXXX sequences
        assert '\\u003cscript\\u003e' in html, "< and > should be JSON-encoded in payload"
        assert 'Tom \\u0026 Jerry' in html, "& should be JSON-encoded in payload"

        # Raw unescaped form must not appear in the page outside the JSON block
        assert '<script>alert' not in html

    def test_table_renders_page_url_as_link(self):
        """URL and species name data should be present in JSON payload for Svelte link rendering."""
        headers = ["scientific_name", "common_name", "price_gbp", "page_url"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "25.00", "https://example.com/species1"],
            ["Grammostola rosea", "Chilean Rose", "15.00", "https://example.com/species2"]
        ]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')

        # Rows are rendered by Svelte; mount div is present
        mount_div = soup.find('div', id='test-table-root')
        assert mount_div is not None, "Mount div should be present"

        # Data is available in the JSON payload for Svelte to render links
        data = _table_json(html)
        assert len(data) == 2
        urls = {row.get('page_url') for row in data}
        assert 'https://example.com/species1' in urls
        assert 'https://example.com/species2' in urls
        names = {row.get('scientific_name') for row in data}
        assert 'Brachypelma hamorii' in names
        assert 'Grammostola rosea' in names

    def test_table_handles_empty_page_url(self):
        """All rows should be present in JSON payload regardless of whether page_url is empty."""
        headers = ["scientific_name", "common_name", "page_url"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "https://example.com/species1"],
            ["Grammostola rosea", "Chilean Rose", ""],  # Empty URL
            ["Aphonopelma seemanni", "Costa Rican Zebra", "   "]  # Whitespace only
        ]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')

        mount_div = soup.find('div', id='test-table-root')
        assert mount_div is not None, "Mount div should be present"

        data = _table_json(html)
        assert len(data) == 3, "All three rows should be in the JSON payload"
        names = {row.get('scientific_name') for row in data}
        assert 'Brachypelma hamorii' in names
        assert 'Grammostola rosea' in names
        assert 'Aphonopelma seemanni' in names

    def test_table_without_page_url_column(self):
        """Data should be present in JSON payload when page_url column is absent."""
        headers = ["scientific_name", "common_name", "price_gbp"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "25.00"],
            ["Grammostola rosea", "Chilean Rose", "15.00"]
        ]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')

        mount_div = soup.find('div', id='test-table-root')
        assert mount_div is not None, "Mount div should be present"

        # Data is in the JSON payload
        assert 'Brachypelma hamorii' in html
        assert 'Mexican Red Knee' in html

    def test_table_with_page_url_but_no_scientific_name(self):
        """URLs should be present in JSON payload when scientific_name column is missing."""
        headers = ["common_name", "price_gbp", "page_url"]
        rows = [
            ["Mexican Red Knee", "25.00", "https://example.com/species1"],
            ["Chilean Rose", "15.00", "https://example.com/species2"]
        ]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')

        mount_div = soup.find('div', id='test-table-root')
        assert mount_div is not None, "Mount div should be present"

        # All data is in the JSON payload
        assert 'https://example.com/species1' in html
        assert 'https://example.com/species2' in html
    def test_signal_cells_with_drivers_column_use_custom_tooltips(self):
        """Signal and Drivers data should both be in JSON payload for Svelte tooltip rendering."""
        headers = ["Species", "Signal", "Drivers"]
        rows = [
            ["Test Spider", "🔥", "Stock: Sustained (OOS 5 runs; currently OUT); Demand: High; Price: Rising"],
        ]
        
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')

        # Rows are rendered by Svelte; verify mount div
        mount_div = soup.find('div', id='test-table-root')
        assert mount_div is not None, "Mount div should be present"

        # In Svelte mode there is no server-rendered thead; all data comes via JSON.
        # The JSON payload has Species, Signal, and Drivers for Svelte to use
        data = _table_json(html)
        assert len(data) == 1
        row = data[0]
        assert row.get('Signal') == '🔥'
        assert 'Stock: Sustained' in row.get('Drivers', '')

    def test_signal_cells_without_drivers_column_have_no_tooltips(self):
        """Signal data should be in JSON payload when Drivers column is absent."""
        headers = ["Species", "Signal"]
        rows = [
            ["Test Spider", "🔥"],
        ]
        
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')

        mount_div = soup.find('div', id='test-table-root')
        assert mount_div is not None, "Mount div should be present"

        # JSON payload has Signal field
        data = _table_json(html)
        assert len(data) == 1
        assert data[0].get('Signal') == '🔥'


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
        """Species and size data should be in JSON payload for Svelte to build internal species links."""
        headers = ["Species", "Size (cm)", "Signal", "page_url"]
        rows = [
            ["Brachypelma hamorii", "2.0", "🔥", "https://example.com/external"],
        ]
        
        html = generate_table_html(headers, rows, "breeder-table", link_to_species_page=True)
        soup = BeautifulSoup(html, 'html.parser')

        mount_div = soup.find('div', id='breeder-table-root')
        assert mount_div is not None, "Mount div should be present for Svelte to mount"

        # JSON has Species and Size for Svelte to build internal links
        data = _table_json(html)
        assert len(data) == 1
        row = data[0]
        assert row.get('Species') == 'Brachypelma hamorii'
        assert row.get('Size (cm)') == '2.0'

    def test_dealer_table_links_to_species_pages_internally(self):
        """Species and size data should be in JSON payload for Svelte to build dealer-view species links."""
        headers = ["Species", "Size (cm)", "Dealer Risk", "page_url"]
        rows = [
            ["Tliltocatl albopilosus", "1.5", "⚠️", "https://example.com/external"],
        ]
        
        html = generate_table_html(headers, rows, "dealer-table", link_to_species_page=True, table_view="dealer")
        soup = BeautifulSoup(html, 'html.parser')

        mount_div = soup.find('div', id='dealer-table-root')
        assert mount_div is not None, "Mount div should be present"

        data = _table_json(html)
        assert len(data) == 1
        row = data[0]
        assert row.get('Species') == 'Tliltocatl albopilosus'
        assert row.get('Size (cm)') == '1.5'

    def test_history_table_keeps_external_links(self):
        """External URL and species name data should be in JSON payload for Svelte rendering."""
        headers = ["scientific_name", "common_name", "page_url"]
        rows = [
            ["Brachypelma hamorii", "Mexican Red Knee", "https://thespidershop.co.uk/product/123"],
        ]
        
        html = generate_table_html(headers, rows, "history-table")
        soup = BeautifulSoup(html, 'html.parser')

        mount_div = soup.find('div', id='history-table-root')
        assert mount_div is not None, "Mount div should be present"

        data = _table_json(html)
        assert len(data) == 1
        row = data[0]
        assert row.get('page_url') == 'https://thespidershop.co.uk/product/123'
        assert row.get('scientific_name') == 'Brachypelma hamorii'

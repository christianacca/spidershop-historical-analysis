#!/usr/bin/env python3
"""Tests for page generation functions."""
import pytest
import tempfile
import os
from pathlib import Path
from bs4 import BeautifulSoup
from website import PageConfig
from website.generate_website import generate_homepage, generate_data_page, main, OUTPUT_DIR


class TestGenerateHomepage:
    """Test suite for homepage generation."""

    def test_generates_complete_html_page(self):
        """Should generate complete HTML page with header and footer."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check DOCTYPE
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        
        # Check semantic elements
        assert soup.find('header') is not None
        assert soup.find('footer') is not None

    def test_includes_welcome_heading(self):
        """Should include welcome heading."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find h2 with welcome text
        headings = soup.find_all('h2')
        welcome_heading = [h for h in headings if 'Welcome to Spider Shop Historical Analysis' in h.text]
        assert len(welcome_heading) == 1

    def test_includes_last_scrape_time_when_provided(self):
        """Should display last scrape time when provided."""
        html = generate_homepage("2025-01-15 12:00:00")
        soup = BeautifulSoup(html, 'html.parser')
        
        info_box = soup.find('div', class_='info-box')
        assert info_box is not None
        assert 'Last Updated:' in info_box.text
        assert '2025-01-15 12:00:00' in info_box.text

    def test_omits_last_scrape_time_when_none(self):
        """Should omit last scrape time section when None."""
        html = generate_homepage(None)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should not have info-box with "Last Updated"
        info_boxes = soup.find_all('div', class_='info-box')
        for box in info_boxes:
            assert 'Last Updated:' not in box.text

    def test_includes_card_grid_with_links(self):
        """Should include card grid with navigation links."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        
        card_grid = soup.find('div', class_='card-grid')
        assert card_grid is not None
        
        # Should have 4 cards
        cards = card_grid.find_all('div', class_='card')
        assert len(cards) == 4
        
        # Check card content
        card_texts = [card.text for card in cards]
        assert any('Latest Snapshot' in text for text in card_texts)
        assert any('Historical Data' in text for text in card_texts)
        assert any('Breeder Opportunities' in text for text in card_texts)
        assert any('Dealer Supply Risk' in text for text in card_texts)

    def test_includes_download_links_section(self):
        """Should include download links for CSV files."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find download links section
        download_section = soup.find('div', class_='download-links')
        assert download_section is not None
        
        # Check for all expected CSV download links
        links = download_section.find_all('a')
        hrefs = [link['href'] for link in links]
        assert 'spidershop_spiderlings_scrape.csv' in hrefs
        assert 'spidershop_spiderlings_history.csv' in hrefs
        assert 'breeder_opportunity_table.csv' in hrefs
        assert 'dealer_supply_risk_table.csv' in hrefs

    def test_includes_about_section(self):
        """Should include about section describing the project."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find h3 with "About This Project"
        headings = soup.find_all('h3')
        about_heading = [h for h in headings if 'About This Project' in h.text]
        assert len(about_heading) == 1
        
        # Check for "automatically scrapes" text (case insensitive)
        assert 'automatically scrapes' in html.lower()

    def test_includes_data_description(self):
        """Should describe what data is collected."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the list describing captured data
        lists = soup.find_all('ul')
        data_description_found = False
        for ul in lists:
            list_text = ul.text
            if all(term in list_text for term in ['Scientific name', 'Common name', 'Size', 'Price']):
                data_description_found = True
                break
        assert data_description_found

    def test_active_page_is_home(self):
        """Should mark home as active page in navigation."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find active link in navigation
        active_links = soup.select('nav a.active')
        assert len(active_links) == 1
        assert active_links[0]['href'] == 'index.html'


class TestGenerateDataPage:
    """Test suite for data page generation."""

    def test_generates_complete_html_page(self):
        """Should generate complete HTML page."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Name,Price\n")
            f.write("Species A,25.00\n")
            filename = f.name
        
        try:
            html = generate_data_page(PageConfig(
                title="Test Page",
                description="Test description",
                csv_filename=filename,
                table_id="test-table",
                active_page="snapshot"
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check DOCTYPE
            assert "<!DOCTYPE html>" in html
            assert "</html>" in html
            
            # Check HTML structure
            assert soup.find('html') is not None
        finally:
            os.unlink(filename)

    def test_includes_title_and_description(self):
        """Should include page title and description."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            html = generate_data_page(PageConfig(
                title="My Title",
                description="My description text",
                csv_filename=filename,
                table_id="test-table",
                active_page="snapshot"
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check title in head
            title = soup.find('title')
            assert title is not None
            assert 'My Title' in title.text
            
            # Check description in content
            assert 'My description text' in html
        finally:
            os.unlink(filename)

    def test_includes_download_link(self):
        """Should include download link for CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = os.path.basename(f.name)
            temp_name = f.name
        
        try:
            html = generate_data_page(PageConfig(
                title="Test",
                description="Desc",
                csv_filename=filename,
                table_id="test-table",
                active_page="snapshot"
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find download link
            download_links = soup.find_all('a', href=filename)
            assert len(download_links) >= 1
            
            # Check for "Download CSV" text
            link_texts = [link.text for link in download_links]
            assert any('Download CSV' in text for text in link_texts)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def test_includes_search_filter_when_enabled(self):
        """Should include search filter when search_filter=True."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\nVal\n")
            filename = f.name
        
        try:
            html = generate_data_page(PageConfig(
                title="Test",
                description="Desc",
                csv_filename=filename,
                table_id="test-table",
                active_page="snapshot",
                search_filter=True
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find search input
            search_input = soup.find('input', type='text')
            assert search_input is not None
            assert 'oninput' in search_input.attrs or 'onkeyup' in search_input.attrs
            assert 'filterTable' in html
        finally:
            os.unlink(filename)

    def test_omits_search_filter_when_disabled(self):
        """Should omit search filter when search_filter=False."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\nVal\n")
            filename = f.name
        
        try:
            html = generate_data_page(PageConfig(
                title="Test",
                description="Desc",
                csv_filename=filename,
                table_id="test-table",
                active_page="snapshot",
                search_filter=False
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should not have table-controls div or search input
            table_controls = soup.find('div', class_='table-controls')
            assert table_controls is None or soup.find('input', type='text') is None
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
            html = generate_data_page(PageConfig(
                title="Test",
                description="Desc",
                csv_filename=filename,
                table_id="test-table",
                active_page="snapshot"
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find "Full Data Table" heading
            headings = soup.find_all('h3')
            assert any('Full Data Table' in h.text for h in headings)
            
            # Find the table
            table = soup.find('table', id='test-table')
            assert table is not None
            
            # Verify data content
            assert soup.find(string='Species A') is not None
            assert soup.find(string='25.00') is not None
            
            # Check for row count
            assert 'Total rows:' in html
            assert '2' in html
        finally:
            os.unlink(filename)

    def test_handles_nonexistent_csv_file(self):
        """Should show 'no data' message for nonexistent file."""
        html = generate_data_page(PageConfig(
            title="Test",
            description="Desc",
            csv_filename="/nonexistent/file.csv",
            table_id="test-table",
            active_page="snapshot"
        ))
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should have "No data available" message
        assert 'No data available' in html
        
        # Should not have a table
        table = soup.find('table', id='test-table')
        assert table is None

    def test_includes_top_10_table_when_provided(self):
        """Should render top 10 table from CSV data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Size (cm),Signal\n")
            for i in range(15):
                f.write(f"Species {i},1,🔥\n")
            filename = f.name
        
        try:
            html = generate_data_page(PageConfig(
                title="Test",
                description="Desc",
                csv_filename=filename,
                table_id="test-table",
                active_page="breeder"
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Top 10 table should be rendered from CSV (first 10 rows)
            h3_tags = soup.find_all('h3')
            top_10_heading = [h for h in h3_tags if 'Top 10' in h.text]
            assert len(top_10_heading) > 0, "Should have 'Top 10' heading"
            
            # Should have at least one table
            tables = soup.find_all('table')
            assert len(tables) > 0, "Should have table rendered from CSV"
        finally:
            os.unlink(filename)

    def test_omits_analysis_section_when_none(self):
        """Should omit analysis section when markdown not provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            html = generate_data_page(PageConfig(
                title="Test",
                description="Desc",
                csv_filename=filename,
                table_id="test-table",
                active_page="snapshot",
                analysis_markdown=None
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should not have analysis-section div
            analysis_section = soup.find('div', class_='analysis-section')
            assert analysis_section is None
        finally:
            os.unlink(filename)

    def test_includes_legend_when_provided(self):
        """Should include legend in details block when provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            legend_md = "**Legend**: This explains the symbols."
            html = generate_data_page(PageConfig(
                title="Test",
                description="Desc",
                csv_filename=filename,
                table_id="test-table",
                active_page="snapshot",
                legend_markdown=legend_md
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find details element
            details = soup.find('details')
            assert details is not None
            
            # Check summary text
            summary = details.find('summary')
            assert summary is not None
            assert 'How to read these tables' in summary.text
            
            # Check for legend content
            strong = details.find('strong', string='Legend')
            assert strong is not None
        finally:
            os.unlink(filename)

    def test_omits_legend_when_none(self):
        """Should omit legend when not provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            html = generate_data_page(PageConfig(
                title="Test",
                description="Desc",
                csv_filename=filename,
                table_id="test-table",
                active_page="snapshot",
                legend_markdown=None
            ))
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should not have details element with legend
            details_elements = soup.find_all('details')
            for details in details_elements:
                assert 'How to read these tables' not in details.text
        finally:
            os.unlink(filename)


class TestPageConfig:
    """Tests for PageConfig dataclass and its usage."""

    def test_pageconfig_with_all_required_fields(self):
        """PageConfig should accept all required fields."""
        config = PageConfig(
            title="Test Title",
            description="Test Description",
            csv_filename="test.csv",
            table_id="test-table",
            active_page="test"
        )
        
        assert config.title == "Test Title"
        assert config.description == "Test Description"
        assert config.csv_filename == "test.csv"
        assert config.table_id == "test-table"
        assert config.active_page == "test"
        assert config.search_filter is True  # Default value
        assert config.analysis_markdown is None
        assert config.legend_markdown is None
        assert config.examples_markdown is None

    def test_pageconfig_with_optional_fields(self):
        """PageConfig should accept optional fields."""
        config = PageConfig(
            title="Test",
            description="Desc",
            csv_filename="test.csv",
            table_id="id",
            active_page="page",
            search_filter=False,
            analysis_markdown="# Analysis",
            legend_markdown="## Legend",
            examples_markdown="### Examples"
        )
        
        assert config.search_filter is False
        assert config.analysis_markdown == "# Analysis"
        assert config.legend_markdown == "## Legend"
        assert config.examples_markdown == "### Examples"

    def test_generate_data_page_with_pageconfig(self, tmp_path):
        """generate_data_page should work with PageConfig parameter."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Species,Price\nTest Spider,£10.00\n")
        
        os.chdir(tmp_path)
        
        config = PageConfig(
            title="Test Page",
            description="Test description using PageConfig",
            csv_filename="test.csv",
            table_id="config-test-table",
            active_page="test"
        )
        
        html = generate_data_page(config=config)
        
        # Verify the page was generated correctly
        assert "Test Page" in html
        assert "Test description using PageConfig" in html
        assert "config-test-table" in html
        assert "Test Spider" in html

    def test_pageconfig_improves_readability(self, tmp_path):
        """PageConfig makes complex calls more readable."""
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text("Species,Signal\nTest,🔥\n")
        
        os.chdir(tmp_path)
        
        # New style: much more readable with named fields
        config = PageConfig(
            title="Breeder Opportunities",
            description="Analysis of breeding opportunities",
            csv_filename="breeder.csv",
            table_id="breeder-table",
            active_page="breeder",
            search_filter=True,
            legend_markdown="## Legend content",
            examples_markdown="### Examples content"
        )
        
        html = generate_data_page(config=config)
        
        # All parameters should be respected
        assert "Breeder Opportunities" in html
        assert "Analysis of breeding opportunities" in html
        assert "breeder-table" in html
        assert "Legend content" in html
        assert "Examples content" in html



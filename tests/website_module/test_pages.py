#!/usr/bin/env python3
"""Tests for page generation functions."""
import pytest
import tempfile
import os
from pathlib import Path
from bs4 import BeautifulSoup
from conftest import page_config, temp_csv_file
from website.generate_website import generate_homepage, generate_analysis_page, generate_snapshot_page, generate_history_page, main, OUTPUT_DIR


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
        """Should include disclaimer section with non-affiliation and as-is notice."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find h3 with "Disclaimer"
        headings = soup.find_all('h3')
        disclaimer_heading = [h for h in headings if 'Disclaimer' in h.text]
        assert len(disclaimer_heading) == 1
        
        # Check for non-affiliation text
        assert 'not affiliated' in html.lower()

    def test_includes_data_description(self):
        """Should include as-is / no-liability disclaimer text."""
        html = generate_homepage()
        
        assert 'as is' in html.lower()
        assert 'no liability' in html.lower() or 'accepts no liability' in html.lower()

    def test_active_page_is_home(self):
        """Should mark home as active page in navigation."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find active link in navigation
        active_links = soup.select('nav a.active')
        assert len(active_links) == 1
        assert active_links[0]['href'] == 'index.html'


class TestGenerateSnapshotPage:
    """Test suite for snapshot page generation."""

    _ALL_CSV_COLUMNS = [
        "scrape_datetime", "scientific_name", "common_name",
        "size_cm", "price_gbp", "wishlist_count", "page_url",
    ]
    _ALL_DISPLAY_HEADERS = [
        "Scientific Name", "Common Name",
        "Size (cm)", "Price (GBP)", "Wishlist Count", "Page URL",
    ]

    def test_generates_complete_html_page(self):
        """Should generate complete HTML page."""
        from conftest import temp_csv_file
        
        csv_content = "Name,Price\nSpecies A,25.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_title("Test Page").with_description("Test description").build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check DOCTYPE
            assert "<!DOCTYPE html>" in html
            assert "</html>" in html
            
            # Check HTML structure
            assert soup.find('html') is not None

    def test_includes_title_and_description(self):
        """Should include page title and description."""
        from conftest import temp_csv_file
        
        csv_content = "Col\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_title("My Title").with_description("My description text").build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check title in head
            title = soup.find('title')
            assert title is not None
            assert 'My Title' in title.text
            
            # Check description in content
            assert 'My description text' in html

    def test_includes_download_link(self):
        """Should include download link for CSV file."""
        from conftest import temp_csv_file
        
        csv_content = "Name,Price\nSpecies A,25.00\n"  # Include proper CSV with header and data
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_title("Test").with_description("Desc").build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find download link (now uses btn-download class)
            download_links = soup.find_all('a', class_='btn-download')
            assert len(download_links) >= 1, "Should have at least one download link with btn-download class"
            
            # Check for "Download CSV" text
            link_texts = [link.text for link in download_links]
            assert any('Download CSV' in text for text in link_texts), "Download link should contain 'Download CSV' text"

    def test_includes_search_filter_when_enabled(self):
        """Should include search filter when search_filter=True (behavior tested by E2E)."""
        from conftest import temp_csv_file
        
        csv_content = "Col\nVal\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_description("Desc").with_title("Test").with_search(True).build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find search input - should have data attributes for event listeners
            search_input = soup.find('input', type='text')
            assert search_input is not None
            assert search_input.get('data-action') == 'search', "Search input should have data-action attribute"
            assert search_input.get('data-table-id') is not None, "Search input should have data-table-id attribute"
            # Filter function should still be in external JavaScript (referenced externally)
            assert 'filterTable' not in html, "filterTable should be in external JS, not inline"

    def test_includes_advanced_filters_toggle_when_search_enabled(self):
        """Should include 'More Filters' toggle button when search_filter=True."""
        from conftest import temp_csv_file
        
        csv_content = "Col\nVal\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_description("Desc").with_title("Test").with_search(True).build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find toggle button (now uses btn-filters class)
            toggle_button = soup.find('button', class_='btn-filters')
            assert toggle_button is not None, "Toggle button should exist when search is enabled"
            
            # Verify button uses data attributes (ES modules pattern)
            assert toggle_button.has_attr('data-action'), "Toggle button should have data-action attribute"
            assert toggle_button['data-action'] == 'toggle-filters', "Should have toggle-filters action"
            assert toggle_button.has_attr('data-content-id'), "Should have data-content-id attribute"
            
            # Verify button contains arrow and text
            assert toggle_button.find('span', class_='arrow') is not None, "Should have arrow span"
            button_text = toggle_button.get_text()
            assert 'More Filters' in button_text or 'Filters' in button_text, "Should have filter button text"
            
            # Verify advanced filters container exists
            advanced_filters = soup.find('div', class_='advanced-filters-content')
            assert advanced_filters is not None, "Advanced filters container should exist"
            assert 'id' in advanced_filters.attrs, "Advanced filters should have ID for toggle reference"

    def test_omits_search_filter_when_disabled(self):
        """Should omit search filter when search_filter=False."""
        csv_content = "Col\nVal\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .with_search(False) \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should not have table-controls div or search input
            table_controls = soup.find('div', class_='table-controls')
            assert table_controls is None or soup.find('input', type='text') is None

    def test_includes_data_table_from_csv(self):
        """Should include data table generated from CSV."""
        csv_content = "Name,Price\nSpecies A,25.00\nSpecies B,30.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find "Data Table" heading
            headings = soup.find_all('h3')
            assert any('Data Table' in h.text for h in headings)
            
            # Find the table (snapshot builder uses snapshot-table as ID)
            table = soup.find('table', id='snapshot-table')
            assert table is not None
            
            # Verify data content
            assert soup.find(string='Species A') is not None
            assert soup.find(string='25.00') is not None

    def test_action_buttons_container_with_download_and_filter_buttons(self):
        """Should have action-buttons container with download and filter buttons side by side."""
        csv_content = "Name,Price\nSpecies A,25.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .with_search(True) \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find action-buttons container
            action_buttons = soup.find('div', class_='action-buttons')
            assert action_buttons is not None, "Should have action-buttons container"
            
            # Check download button
            download_link = action_buttons.find('a', class_='btn-download')
            assert download_link is not None, "Should have download button with btn-download class"
            assert 'Download CSV' in download_link.text, "Download button should have text"
            assert download_link.has_attr('download'), "Download button should have download attribute"
            assert download_link.has_attr('href'), "Download button should have href"
            
            # Check filter button
            filter_button = action_buttons.find('button', class_='btn-filters')
            assert filter_button is not None, "Should have filter button with btn-filters class"
            assert 'More Filters' in filter_button.text or 'Filters' in filter_button.text, "Filter button should have text"
            assert filter_button.has_attr('data-action'), "Filter button should have data-action attribute"
            assert filter_button['data-action'] == 'toggle-filters', "Filter button should have toggle-filters action"
            assert filter_button.has_attr('data-content-id'), "Filter button should have data-content-id attribute"
            
            # Verify both buttons are direct children of action-buttons container
            direct_children = [child for child in action_buttons.children if child.name in ['a', 'button']]
            assert len(direct_children) == 2, "Should have exactly 2 button elements as direct children"

    def test_action_buttons_omits_filter_button_when_search_disabled(self):
        """Should only show download button when search is disabled."""
        csv_content = "Name,Price\nSpecies A,25.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .with_search(False) \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Download button should exist
            download_link = soup.find('a', class_='btn-download')
            assert download_link is not None, "Should have download button"
            
            # Filter button should NOT exist
            filter_button = soup.find('button', class_='btn-filters')
            assert filter_button is None, "Should NOT have filter button when search disabled"

    def test_table_stats_strip_shows_species_count(self):
        """Should show 'Showing: x of x species' strip above table."""
        csv_content = "Name,Price\nSpecies A,25.00\nSpecies B,30.00\nSpecies C,15.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find table-stats strip
            stats_strip = soup.find('div', class_='table-stats')
            assert stats_strip is not None, "Should have table-stats strip"
            
            # Check for "Showing:" text
            assert 'Showing:' in stats_strip.text, "Stats strip should contain 'Showing:' text"
            
            # Check for visible count span
            visible_count_span = stats_strip.find('span', id='visible-count-snapshot-table')
            assert visible_count_span is not None, "Should have visible-count span with table-id in ID"
            assert visible_count_span.text == '3', "Visible count should equal total rows initially"
            
            # Check for total count
            assert 'of 3 species' in stats_strip.text, "Should show total species count"

    def test_table_stats_strip_exists_even_when_search_disabled(self):
        """Should show stats strip regardless of search filter setting."""
        csv_content = "Name,Price\nSpecies A,25.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .with_search(False) \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Stats strip should exist even without search
            stats_strip = soup.find('div', class_='table-stats')
            assert stats_strip is not None, "Should have stats strip even when search disabled"
            assert 'Showing:' in stats_strip.text, "Should show species count"

    def test_handles_nonexistent_csv_file(self):
        """Should show 'no data' message for nonexistent file."""
        config = page_config.snapshot("/nonexistent/file.csv") \
            .with_title("Test") \
            .with_description("Desc") \
            .build()
        html = generate_snapshot_page(config)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should have "No data available" message
        assert 'No data available' in html
        
        # Should not have a table
        table = soup.find('table', id='test-table')
        assert table is None

    def test_includes_top_10_filter_button_when_data_provided(self):
        """Should render top 10 filter button when there is data."""
        csv_content = "Species,Size (cm),Signal\n" + "".join(f"Species {i},1,🔥\n" for i in range(15))
        with temp_csv_file(csv_content) as filename:
            config = page_config.breeder(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .build()
            html = generate_analysis_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Top 10 filter button should exist with correct data attributes
            top10_btn = soup.find('button', attrs={
                'data-action': 'filter-signal',
                'data-signal': '🔥',
                'data-limit': '10'
            })
            assert top10_btn is not None, "Should have a 🔥 Hot (top 10) filter button"
            
            # Should have one table
            tables = soup.find_all('table')
            assert len(tables) == 1, "Should have exactly one table rendered from CSV"

    def test_omits_analysis_section_when_none(self):
        """Should omit analysis section when markdown not provided."""
        csv_content = "Col\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should not have analysis-section div
            analysis_section = soup.find('div', class_='analysis-section')
            assert analysis_section is None

    def test_includes_legend_when_provided(self):
        """Should include legend in details block when provided."""
        csv_content = "Col\n"
        legend_md = "**Legend**: This explains the symbols."
        with temp_csv_file(csv_content) as filename:
            # Use breeder config which supports legend_markdown (snapshot doesn't)
            config = page_config.breeder(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .with_legend(legend_md) \
                .build()
            html = generate_analysis_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find details element with legend (not instruction box)
            details_elements = soup.find_all('details')
            legend_details = [d for d in details_elements if 'How to read these tables' in d.text]
            assert len(legend_details) > 0, "Should have legend details element"
            
            # Check summary text
            summary = legend_details[0].find('summary')
            assert summary is not None
            assert 'How to read these tables' in summary.text
            
            # Check for legend content
            strong = legend_details[0].find('strong', string='Legend')
            assert strong is not None

            # Legend details must have id="legend-section" so the anchor link can target it
            assert legend_details[0].get('id') == 'legend-section', \
                "Legend <details> must have id='legend-section' for the anchor link to work"

    def test_omits_legend_when_none(self):
        """Should omit legend when not provided."""
        csv_content = "Col\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should not have details element with legend
            details_elements = soup.find_all('details')
            for details in details_elements:
                assert 'How to read these tables' not in details.text

    def test_includes_instruction_box_for_breeder_page(self):
        """Should include 'How to use this page' instruction box for breeder pages."""
        csv_content = "Species,Size (cm),Signal\nTest Spider,1.5,🔥\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.breeder(filename) \
                .with_title("Breeder Opportunities") \
                .with_description("Test") \
                .build()
            html = generate_analysis_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should have instruction box
            instruction_box = soup.find('details', class_='instruction-box')
            assert instruction_box is not None, "Should have instruction box details element"
            
            # Should have summary with "How to use this page"
            summary = instruction_box.find('summary')
            assert summary is not None
            assert 'How to use this page' in summary.text
            
            # Should mention 60 seconds
            assert '60 second' in summary.text.lower() or '60-second' in summary.text.lower()
            
            # Should include key breeder concepts
            text = instruction_box.text
            assert 'breeding' in text.lower()  # "breeding investment"
            assert 'opportunity' in text.lower()
            assert '🔥' in text
            assert 'ℹ️' in text or 'info icon' in text.lower()
            
            # Should explain strategic context
            assert 'signal' in text.lower()
            assert 'stock pattern' in text.lower()

            # Should have a subtle anchor linking to the legend section
            legend_link = instruction_box.find('a', attrs={'data-action': 'open-details'})
            assert legend_link is not None, "Instruction box should have a legend anchor link"
            assert legend_link.get('href') == '#legend-section'
            assert legend_link.get('data-target') == 'legend-section'

    def test_includes_instruction_box_for_dealer_page(self):
        """Should include 'How to use this page' instruction box for dealer pages."""
        csv_content = "Species,Size (cm),Risk\nTest Spider,1.5,🔥\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.dealer(filename) \
                .with_title("Dealer Supply Risk") \
                .with_description("Test") \
                .build()
            html = generate_analysis_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should have instruction box
            instruction_box = soup.find('details', class_='instruction-box')
            assert instruction_box is not None, "Should have instruction box details element"
            
            # Should have summary with "How to use this page"
            summary = instruction_box.find('summary')
            assert summary is not None
            assert 'How to use this page' in summary.text
            
            # Should include key dealer concepts  
            text = instruction_box.text
            assert 'risk' in text.lower()  # "High Risk", "Moderate Risk", etc.
            assert 'supply' in text.lower()  # "supply reliability"
            assert '🔥' in text
            assert 'ℹ️' in text or 'info icon' in text.lower()
            
            # Should explain strategic context
            assert 'restock' in text.lower()
            assert 'inventory' in text.lower()

            # Should have a subtle anchor linking to the legend section
            legend_link = instruction_box.find('a', attrs={'data-action': 'open-details'})
            assert legend_link is not None, "Instruction box should have a legend anchor link"
            assert legend_link.get('href') == '#legend-section'
            assert legend_link.get('data-target') == 'legend-section'

    def test_omits_instruction_box_for_snapshot_page(self):
        """Should NOT include instruction box for snapshot pages (simple pages)."""
        csv_content = "Col\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Snapshot") \
                .with_description("Test") \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should not have instruction box
            instruction_box = soup.find('details', class_='instruction-box')
            assert instruction_box is None, "Snapshot pages should not have instruction box"

    def test_table_headers_use_proper_english_display_names(self):
        """All raw CSV column names must be replaced with proper English in <th> elements.
        scrape_datetime is excluded from the table and shown in an info box instead."""
        row = ",".join(["2026-01-15T06:10+00:00", "Species A", "Common A",
                        "1.5", "25.00", "5", "http://example.com"])
        csv_content = ",".join(self._ALL_CSV_COLUMNS) + "\n" + row + "\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_title("T").with_description("D").build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, "html.parser")

            th_texts = [
                th.get_text(separator=" ", strip=True).replace("\u21c5", "").strip()
                for th in soup.select("table th")
            ]

            for raw in self._ALL_CSV_COLUMNS:
                assert raw not in th_texts, (
                    f"Raw CSV column name '{raw}' should not appear as a table header"
                )
            for display in self._ALL_DISPLAY_HEADERS:
                assert display in th_texts, (
                    f"Expected display header '{display}' not found in table headers: {th_texts}"
                )
            assert "Scrape Date" not in th_texts, (
                "Scrape Date should not appear as a table column (shown in stats strip instead)"
            )

            # scrape_date shown in the table-stats strip, not a separate info-box
            stats_strip = soup.find(class_="table-stats")
            assert stats_strip is not None, "Should have a table-stats strip"
            assert "Scraped" in stats_strip.get_text(), "Stats strip should show scrape date"


class TestPageConfig:
    """Tests for PageConfig dataclass and its usage."""

    def test_pageconfig_with_all_required_fields(self):
        """BreederPageConfig should accept all required fields with defaults."""
        from website.page_config import BreederPageConfig
        
        config = BreederPageConfig(
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
        """BreederPageConfig should accept optional fields."""
        from website.page_config import BreederPageConfig
        
        config = BreederPageConfig(
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

    def test_generate_snapshot_page_with_pageconfig(self, tmp_path):
        """generate_snapshot_page should work with BasePageConfig parameter."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Species,Price\nTest Spider,£10.00\n")
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Test Page",
            description="Test description using PageConfig",
            csv_filename="test.csv",
            table_id="config-test-table",
            active_page="test"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Verify the page was generated correctly
        assert "Test Page" in html
        assert "Test description using PageConfig" in html
        assert "config-test-table" in html
        assert "Test Spider" in html

    def test_pageconfig_improves_readability(self, tmp_path):
        """BreederPageConfig makes complex calls more readable."""
        from website.page_config import BreederPageConfig
        
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text("Species,Signal\nTest,🔥\n")
        
        os.chdir(tmp_path)
        
        # New style: much more readable with named fields
        config = BreederPageConfig(
            title="Breeder Opportunities",
            description="Analysis of breeding opportunities",
            csv_filename="breeder.csv",
            table_id="breeder-table",
            active_page="breeder",
            search_filter=True,
           legend_markdown="## Legend content",
            examples_markdown="### Examples content"
        )
        
        html = generate_analysis_page(config=config)
        
        # All parameters should be respected
        assert "Breeder Opportunities" in html
        assert "Analysis of breeding opportunities" in html
        assert "breeder-table" in html
        assert "Legend content" in html
        assert "Examples content" in html


class TestWishlistRangeCalculation:
    """Test suite for dynamic wishlist range calculation in snapshot page."""

    def test_wishlist_range_calculated_from_csv_data(self, tmp_path):
        """Should calculate wishlist min/max from actual CSV data."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,8.99,5,http://example.com\n"
        csv_content += "2026-01-01,Brachypelma hamorii,Mexican Red Knee,2.0,12.50,15,http://example.com\n"
        csv_content += "2026-01-01,Chromatopelma cyaneopubescens,GBB,1.0,10.00,8,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Verify wishlist slider has correct min/max from data (5, 15)
        assert 'min="5"' in html, "Expected min='5' based on CSV data"
        assert 'max="15"' in html, "Expected max='15' based on CSV data"
        assert 'value="15"' in html, "Expected slider to initialize at max value"
        
        # Verify display shows correct range
        assert "Showing: 5 - 15" in html, "Expected display to show '5 - 15'"

    def test_wishlist_slider_absent_when_column_missing(self, tmp_path):
        """Should omit wishlist slider entirely when wishlist_count column is missing."""
        from website.page_config import BasePageConfig
        from bs4 import BeautifulSoup
        
        csv_file = tmp_path / "snapshot.csv"
        # Old CSV format without wishlist_count
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,page_url\n"
        csv_content += "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,8.99,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        soup = BeautifulSoup(html, "html.parser")
        
        # Slider should be absent when column does not exist
        assert soup.find("input", id="wishlistMin") is None, "Expected no wishlist slider when column absent"
        assert soup.find("input", id="wishlistMax") is None, "Expected no wishlist slider when column absent"

    def test_wishlist_range_handles_empty_csv(self, tmp_path):
        """Should show 'no data' message when CSV has no data rows."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        # Header only, no data
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # When no data, page shows info message instead of table/filters
        assert "No data available" in html
        assert "snapshot-table" not in html

    def test_wishlist_range_handles_invalid_values(self, tmp_path):
        """Should skip invalid wishlist values and use valid ones."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,8.99,3,http://example.com\n"
        csv_content += "2026-01-01,Species B,Common B,2.0,12.50,invalid,http://example.com\n"  # Invalid
        csv_content += "2026-01-01,Species C,Common C,1.0,10.00,20,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Should use valid values only (3, 20)
        assert 'min="3"' in html
        assert 'max="20"' in html

    def test_wishlist_range_with_single_value(self, tmp_path):
        """Should handle CSV with only one row correctly."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,8.99,42,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Min and max should both be 42
        assert 'min="42"' in html
        assert 'max="42"' in html
        assert 'value="42"' in html

    def test_wishlist_range_with_zero_values(self, tmp_path):
        """Should correctly handle zero wishlist counts."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,8.99,0,http://example.com\n"
        csv_content += "2026-01-01,Species B,Common B,2.0,12.50,5,http://example.com\n"
        csv_content += "2026-01-01,Species C,Common C,1.0,10.00,0,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Should correctly identify 0 as minimum
        assert 'min="0"' in html
        assert 'max="5"' in html


class TestPriceRangeCalculation:
    """Test suite for dynamic price range calculation in snapshot page."""

    def test_price_range_calculated_from_csv_data(self, tmp_path):
        """Should calculate price min/max from actual CSV data."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,£8.99,5,http://example.com\n"
        csv_content += "2026-01-01,Brachypelma hamorii,Mexican Red Knee,2.0,£25.50,15,http://example.com\n"
        csv_content += "2026-01-01,Chromatopelma cyaneopubescens,GBB,1.0,£12.00,8,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Verify price slider has correct min/max from data (8, 26 - rounded up)
        assert 'min="8"' in html, "Expected min='8' based on CSV data"
        assert 'max="26"' in html, "Expected max='26' based on CSV data (25.50 rounded up + 1)"
        assert 'value="26"' in html, "Expected slider to initialize at max value"
        
        # Verify display shows correct range
        assert "Showing: £8 - £26" in html, "Expected display to show '£8 - £26'"

    def test_price_slider_absent_when_column_missing(self, tmp_path):
        """Should omit price slider entirely when price_gbp column is missing."""
        from website.page_config import BasePageConfig
        from bs4 import BeautifulSoup
        
        csv_file = tmp_path / "snapshot.csv"
        # CSV format without price_gbp
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,5,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        soup = BeautifulSoup(html, "html.parser")
        
        # Slider should be absent when column does not exist
        assert soup.find("input", id="priceMin") is None, "Expected no price slider when column absent"
        assert soup.find("input", id="priceMax") is None, "Expected no price slider when column absent"

    def test_price_range_handles_empty_csv(self, tmp_path):
        """Should show 'no data' message when CSV has no data rows."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        # Header only, no data
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # When no data, page shows info message instead of table/filters
        assert "No data available" in html
        assert "snapshot-table" not in html

    def test_price_range_handles_invalid_values(self, tmp_path):
        """Should skip invalid price values and use valid ones."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,£10.50,3,http://example.com\n"
        csv_content += "2026-01-01,Species B,Common B,2.0,invalid,5,http://example.com\n"  # Invalid
        csv_content += "2026-01-01,Species C,Common C,1.0,£45.99,20,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Should use valid values only (10, 46)
        assert 'min="10"' in html
        assert 'max="46"' in html

    def test_price_range_with_single_value(self, tmp_path):
        """Should handle CSV with only one row correctly."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,£15.99,42,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Min should be 15, max should be 16 (15.99 -> 15, then +1)
        assert 'min="15"' in html
        assert 'max="16"' in html
        assert 'value="16"' in html

    def test_price_range_with_decimal_prices(self, tmp_path):
        """Should correctly handle decimal prices and round appropriately."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,£7.50,0,http://example.com\n"
        csv_content += "2026-01-01,Species B,Common B,2.0,£12.99,5,http://example.com\n"
        csv_content += "2026-01-01,Species C,Common C,1.0,£22.75,0,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Min should be 7 (floor), max should be 23 (floor of 22.75 + 1)
        assert 'min="7"' in html
        assert 'max="23"' in html

    def test_price_range_handles_prices_without_pound_symbol(self, tmp_path):
        """Should handle prices that don't have £ symbol."""
        from website.page_config import BasePageConfig
        
        csv_file = tmp_path / "snapshot.csv"
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,10.00,5,http://example.com\n"
        csv_content += "2026-01-01,Species B,Common B,2.0,30.50,8,http://example.com\n"
        csv_file.write_text(csv_content)
        
        os.chdir(tmp_path)
        
        config = BasePageConfig(
            title="Snapshot",
            description="Current scrape",
            csv_filename="snapshot.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )
        
        html = generate_snapshot_page(config=config)
        
        # Should correctly parse prices without £ symbol
        assert 'min="10"' in html
        assert 'max="31"' in html


class TestGenerateHistoryPage:
    """Test suite for history page generation."""

    def test_generates_complete_html_page(self):
        """Should generate complete HTML page."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Historical Data").with_description("All history").build()
            html = generate_history_page(config)

            assert "<!DOCTYPE html>" in html
            assert "</html>" in html
            assert BeautifulSoup(html, 'html.parser').find('html') is not None

    def test_includes_action_buttons_with_download_and_filter_toggle(self):
        """Should have download link in stats bar and standalone More Filters button when scrape_datetimes present."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            # Download link should be in the stats bar
            stats_strip = soup.find('div', class_='table-stats')
            assert stats_strip is not None, "Should have table-stats strip"
            download_link = stats_strip.find('a', class_='btn-download')
            assert download_link is not None, "Download link should be inside the stats bar"
            assert download_link.has_attr('download'), "Download link should have download attribute"
            assert 'Download' in download_link.text

            # More Filters button should exist as a standalone button (not inside action-buttons)
            filter_button = soup.find('button', class_='btn-filters')
            assert filter_button is not None, "Should have More Filters toggle button"
            assert filter_button['data-action'] == 'toggle-filters'
            assert filter_button.has_attr('data-content-id')
            assert filter_button.find('span', class_='arrow') is not None

    _ALL_CSV_COLUMNS = [
        "scrape_datetime", "scientific_name", "common_name",
        "size_cm", "price_gbp", "wishlist_count", "page_url",
    ]
    _ALL_DISPLAY_HEADERS = [
        "Scrape Date", "Scientific Name", "Common Name",
        "Size (cm)", "Price (GBP)", "Wishlist Count", "Page URL",
    ]

    def test_table_headers_use_proper_english_display_names(self):
        """All raw CSV column names must be replaced with proper English in <th> elements."""
        row = ",".join(["2026-01-15T06:10+00:00", "Species A", "Common A",
                        "1.5", "25.00", "5", "http://example.com"])
        csv_content = ",".join(self._ALL_CSV_COLUMNS) + "\n" + row + "\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("T").with_description("D").build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, "html.parser")

            th_texts = [
                th.get_text(separator=" ", strip=True).replace("\u21c5", "").strip()
                for th in soup.select("table th")
            ]

            for raw in self._ALL_CSV_COLUMNS:
                assert raw not in th_texts, (
                    f"Raw CSV column name '{raw}' should not appear as a table header"
                )
            for display in self._ALL_DISPLAY_HEADERS:
                assert display in th_texts, (
                    f"Expected display header '{display}' not found in table headers: {th_texts}"
                )

    def test_includes_filter_badge_on_toggle_button(self):
        """Should include hidden filter badge span on the toggle button."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            filter_button = soup.find('button', class_='btn-filters')
            badge = filter_button.find('span', class_='filter-badge')
            assert badge is not None, "Toggle button should contain filter-badge span"
            assert 'hidden' in badge.get('class', []), "Badge should be hidden initially"
            assert badge['id'].startswith('filterBadge-'), "Badge ID should start with 'filterBadge-'"

    def test_search_filter_inside_advanced_filters_panel(self):
        """Should place search input inside the advanced-filters-content panel."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            panel = soup.find('div', class_='advanced-filters-content')
            assert panel is not None, "Should have advanced-filters-content panel"
            search_input = panel.find('input', attrs={'data-action': 'search'})
            assert search_input is not None, "Search input should be inside the filter panel"
            assert search_input.get('data-table-id') is not None

    def test_omits_filter_toggle_when_search_disabled(self):
        """Should omit More Filters button when search_filter=False."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(False).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            assert soup.find('button', class_='btn-filters') is None, "Should not have filter toggle when search disabled"
            assert soup.find('input', type='text') is None, "Should not have search input when search disabled"

    def test_table_stats_strip_shows_row_count(self):
        """Should show 'Filtered Results: Showing x of x rows' strip (with scrape_datetimes present)."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08 10:00:00,Species B,Common B,2.0,30.00,8,http://example.com\n"
        csv_content += "2026-01-15 10:00:00,Species A,Common A,1.5,26.00,6,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            stats_strip = soup.find('div', class_='table-stats')
            assert stats_strip is not None, "Should have table-stats strip"
            assert 'Filtered Results:' in stats_strip.text

            table_id = config.table_id
            visible_count_span = stats_strip.find('span', id=f'visible-count-{table_id}')
            assert visible_count_span is not None, "Should have visible-count span"
            assert visible_count_span.text == '3', "Visible count should equal total rows initially"
            assert 'of 3 rows' in stats_strip.text, "Should show total row count"

    def test_omits_total_rows_paragraph(self):
        """Should NOT have the old 'Total rows: N' paragraph."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").build()
            html = generate_history_page(config)

            assert 'Total rows:' not in html, "Old 'Total rows:' paragraph should be removed"

    def test_no_data_shows_info_box(self):
        """Should show 'no data' info box when CSV is missing."""
        config = page_config.history("/nonexistent/file.csv").with_title("Test").with_description("Desc").build()
        html = generate_history_page(config)

        assert 'No data available' in html
        assert BeautifulSoup(html, 'html.parser').find('table') is None

    def test_price_sliders_have_correct_data_attributes(self):
        """Should have data-filter='price' and data-table-id on slider inputs."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,20.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            for slider_id in ('priceMin', 'priceMax'):
                slider = soup.find('input', id=slider_id)
                assert slider is not None
                assert slider.get('data-filter') == 'price', f"{slider_id} should have data-filter='price'"
                assert slider.get('data-table-id') == config.table_id, f"{slider_id} should have data-table-id"

    def test_table_rows_have_data_price_attribute(self):
        """Should set data-price on each table row so JS can filter by price."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08 10:00:00,Species B,Common B,2.0,30.00,8,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            table = soup.find('table', id=config.table_id)
            rows = table.select('tbody tr')
            assert len(rows) == 2
            for row in rows:
                assert row.has_attr('data-price'), "Each row should have data-price attribute"
            prices = {row['data-price'] for row in rows}
            assert '25.00' in prices
            assert '30.00' in prices

    def test_price_sliders_absent_when_search_disabled(self):
        """Should not render price sliders when search_filter=False."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(False).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            assert soup.find('input', id='priceMin') is None, "priceMin should not exist when search disabled"
            assert soup.find('input', id='priceMax') is None, "priceMax should not exist when search disabled"

    def test_wishlist_sliders_have_correct_data_attributes(self):
        """Should have data-filter='wishlist' and data-table-id on wishlist slider inputs."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,20.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            for slider_id in ('wishlistMin', 'wishlistMax'):
                slider = soup.find('input', id=slider_id)
                assert slider is not None, f"Should have {slider_id} slider"
                assert slider.get('data-filter') == 'wishlist', f"{slider_id} should have data-filter='wishlist'"
                assert slider.get('data-table-id') == config.table_id, f"{slider_id} should have data-table-id"

    def test_table_rows_have_data_wishlist_attribute(self):
        """Should set data-wishlist on each table row so JS can filter by wishlist count."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08 10:00:00,Species B,Common B,2.0,30.00,10,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            table = soup.find('table', id=config.table_id)
            rows = table.select('tbody tr')
            assert len(rows) == 2
            for row in rows:
                assert row.has_attr('data-wishlist'), "Each row should have data-wishlist attribute"
            wishlist_values = {row['data-wishlist'] for row in rows}
            assert '5' in wishlist_values
            assert '10' in wishlist_values

    def test_wishlist_sliders_absent_when_search_disabled(self):
        """Should not render wishlist sliders when search_filter=False."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(False).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            assert soup.find('input', id='wishlistMin') is None, "wishlistMin should not exist when search disabled"
            assert soup.find('input', id='wishlistMax') is None, "wishlistMax should not exist when search disabled"

    def test_date_checkboxes_rendered_one_per_unique_scrape_datetime(self):
        """Should render one checkbox per unique scrape_datetime value."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species A,Common A,1.5,26.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species B,Common B,2.0,30.00,8,http://example.com\n"
        csv_content += "2026-01-15,Species A,Common A,1.5,27.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            checkboxes = soup.find_all('input', attrs={'data-date-value': True})
            assert len(checkboxes) == 3, f"Expected 3 date checkboxes (one per unique date), got {len(checkboxes)}"
            date_values = {cb['data-date-value'] for cb in checkboxes}
            assert '2026-01-01' in date_values
            assert '2026-01-08' in date_values
            assert '2026-01-15' in date_values

    def test_date_checkbox_row_counts_are_correct(self):
        """Each date checkbox label should show the correct (N rows) count."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species A,Common A,1.5,26.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species B,Common B,2.0,30.00,8,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            # Find count labels by locating each date-row label
            date_rows = soup.find_all('label', class_='date-row')
            counts_by_date = {}
            for label in date_rows:
                cb = label.find('input', attrs={'data-date-value': True})
                count_span = label.find('span', class_='date-count')
                if cb and count_span:
                    counts_by_date[cb['data-date-value']] = count_span.text.strip()

            assert counts_by_date.get('2026-01-01') == '(1 rows)', f"Expected '(1 rows)' for 2026-01-01, got '{counts_by_date.get('2026-01-01')}'"
            assert counts_by_date.get('2026-01-08') == '(2 rows)', f"Expected '(2 rows)' for 2026-01-08, got '{counts_by_date.get('2026-01-08')}'"

    def test_rows_have_data_date_attribute(self):
        """Each table row should have a data-date attribute matching its formatted scrape_datetime."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species B,Common B,2.0,30.00,8,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            table = soup.find('table', id=config.table_id)
            rows = table.select('tbody tr')
            assert len(rows) == 2
            for row in rows:
                assert row.has_attr('data-date'), "Each row should have data-date attribute"
            date_values = {row['data-date'] for row in rows}
            assert '2026-01-01' in date_values
            assert '2026-01-08' in date_values

    def test_date_checkboxes_ordered_most_recent_first(self):
        """Date checkboxes should be rendered most-recent-first."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species B,Common B,2.0,30.00,8,http://example.com\n"
        csv_content += "2026-01-15,Species A,Common A,1.5,27.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            checkboxes = soup.find_all('input', attrs={'data-date-value': True})
            date_order = [cb['data-date-value'] for cb in checkboxes]
            assert date_order[0] == '2026-01-15', f"First (most recent) date should be 2026-01-15, got '{date_order[0]}'"
            assert date_order[-1] == '2026-01-01', f"Last (oldest) date should be 2026-01-01, got '{date_order[-1]}'"

    def test_all_dates_master_checkbox_rendered(self):
        """Should render 'All Dates' master checkbox, checked by default."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            all_dates_cb = soup.find('input', id=f'allDates-{config.table_id}')
            assert all_dates_cb is not None, "Should have allDates master checkbox"
            assert all_dates_cb.has_attr('checked'), "allDates checkbox should be checked by default"

    def test_date_filter_absent_when_search_disabled(self):
        """Should not render date filter section when search_filter=False."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(False).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            assert soup.find('div', class_='date-filter-section') is None, "Date filter section should not exist when search disabled"
            assert soup.find('input', attrs={'data-date-value': True}) is None, "Date checkboxes should not exist when search disabled"

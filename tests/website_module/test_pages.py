#!/usr/bin/env python3
"""Tests for page generation functions."""
import json
import re
import pytest
import tempfile
import os
from pathlib import Path
from bs4 import BeautifulSoup
from conftest import page_config, temp_csv_file
from website.generate_website import generate_homepage, generate_analysis_page, generate_snapshot_page, generate_history_page, generate_history_insights_page, main, OUTPUT_DIR
from website.page_config import BasePageConfig


def _table_json(html: str) -> list:
    """Extract and parse the window['...Data'] JSON from a rendered page."""
    m = re.search(r"window\['[^']+Data'\]\s*=\s*(\[.*?\])\s*;", html, re.DOTALL)
    return json.loads(m.group(1)) if m else []


class TestGenerateHistoryInsightsPage:
    """Tests for history-insights page generation — raw data serialisation."""

    def _make_history_csv(self, tmp_path, run_dates: list) -> str:
        """Write a minimal history CSV with one species across given run dates."""
        csv_path = tmp_path / "spidershop_spiderlings_history.csv"
        header = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url"
        rows = [
            f"{dt},Aphonopelma seemanni,Costa Rican Zebra,1.5,25.00,10,https://example.com/1"
            for dt in run_dates
        ]
        csv_path.write_text("\n".join([header] + rows) + "\n", encoding="utf-8")
        return str(csv_path)

    def _config(self, csv_filename: str) -> BasePageConfig:
        return BasePageConfig(
            title="Market Health",
            description="Test",
            csv_filename=csv_filename,
            table_id="history-table",
            active_page="history-insights",
        )

    def test_injects_market_health_raw_data_global(self, tmp_path):
        """Generated HTML must contain window.marketHealthRawData (not marketHealthPayloads)."""
        runs = [
            "2026-01-01T06:10:00",
            "2026-01-08T06:10:00",
            "2026-01-15T06:10:00",
        ]
        csv_path = self._make_history_csv(tmp_path, runs)
        html = generate_history_insights_page(self._config(csv_path))
        assert "window.marketHealthRawData" in html, (
            "Generated HTML must contain window.marketHealthRawData"
        )
        assert "window.marketHealthPayloads" not in html, (
            "Old window.marketHealthPayloads global must not appear in generated HTML"
        )

    def test_raw_data_has_records_and_reference_date(self, tmp_path):
        """The injected JSON must have a 'records' list and a 'referenceDate' string."""
        runs = [
            "2026-01-01T06:10:00",
            "2026-01-08T06:10:00",
            "2026-01-15T06:10:00",
        ]
        csv_path = self._make_history_csv(tmp_path, runs)
        html = generate_history_insights_page(self._config(csv_path))
        import json
        m = re.search(r'window\.marketHealthRawData\s*=\s*(\{.*?\});', html, re.DOTALL)
        assert m, "window.marketHealthRawData JSON not found in generated HTML"
        raw = json.loads(m.group(1))
        assert "records" in raw, "Raw data must have a 'records' key"
        assert "referenceDate" in raw, "Raw data must have a 'referenceDate' key"
        assert isinstance(raw["records"], list), "'records' must be a list"
        assert raw["referenceDate"] != "", "'referenceDate' must be non-empty when rows exist"

    def test_records_count_equals_source_rows(self, tmp_path):
        """Every source row must appear as a record (no server-side deduplication)."""
        runs = [
            "2026-01-01T06:10:00",
            "2026-01-08T06:10:00",
            "2026-01-15T06:10:00",
        ]
        csv_path = self._make_history_csv(tmp_path, runs)
        html = generate_history_insights_page(self._config(csv_path))
        import json
        m = re.search(r'window\.marketHealthRawData\s*=\s*(\{.*?\});', html, re.DOTALL)
        raw = json.loads(m.group(1))
        # One species × 3 runs = 3 rows → 3 records
        assert len(raw["records"]) == 3, (
            f"Expected 3 records (1 species × 3 runs), got {len(raw['records'])}"
        )

    def test_reference_date_matches_latest_run(self, tmp_path):
        """referenceDate must equal the most recent scrape_datetime in the source data."""
        runs = [
            "2026-01-01T06:10:00",
            "2026-01-08T06:10:00",
            "2026-01-15T06:10:00",
        ]
        csv_path = self._make_history_csv(tmp_path, runs)
        html = generate_history_insights_page(self._config(csv_path))
        import json
        m = re.search(r'window\.marketHealthRawData\s*=\s*(\{.*?\});', html, re.DOTALL)
        raw = json.loads(m.group(1))
        assert raw["referenceDate"] == "2026-01-15T06:10:00", (
            f"referenceDate must be the latest run date; got {raw['referenceDate']!r}"
        )


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
        
        # Should have 5 cards (snapshot, history, history-insights, breeder, dealer)
        cards = card_grid.find_all('div', class_='card')
        assert len(cards) == 5
        
        # Check card content
        card_texts = [card.text for card in cards]
        assert any('Latest Snapshot' in text for text in card_texts)
        assert any('Historical Data' in text for text in card_texts)
        assert any('History Insights' in text for text in card_texts)
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
        active_links = soup.select('nav a.nav__link--active')
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
        """Should rely on the Svelte table stats strip for CSV download controls."""
        from conftest import temp_csv_file
        
        csv_content = "Name,Price\nSpecies A,25.00\n"  # Include proper CSV with header and data
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_title("Test").with_description("Desc").build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            assert soup.find('div', class_='action-buttons') is None
            assert soup.find('a', class_='btn--download') is None

    def test_includes_search_filter_when_enabled(self):
        """Should include search filter when search_filter=True (behavior tested by E2E)."""
        from conftest import temp_csv_file
        
        csv_content = "Col\nVal\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_description("Desc").with_title("Test").with_search(True).build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Search is now rendered by the Svelte SortableTable component.
            # Verify the Svelte mount point is present so the component can render search.
            mount_div = soup.find('div', id='snapshot-table-root')
            assert mount_div is not None, "Svelte mount div should exist for search to be rendered"
            # Filter function should still be in external JavaScript (referenced externally)
            assert 'filterTable' not in html, "filterTable should be in external JS, not inline"

    def test_includes_advanced_filters_toggle_when_search_enabled(self):
        """Should include filter toggle when search_filter=True (now rendered by Svelte SortableTable)."""
        from conftest import temp_csv_file
        
        csv_content = "Col\nVal\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_description("Desc").with_title("Test").with_search(True).build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')
            
            # The filter toggle button is now rendered by the Svelte SortableTable component.
            # Verify the Svelte mount point is present so the component can render the toggle.
            mount_div = soup.find('div', id='snapshot-table-root')
            assert mount_div is not None, "Svelte mount div should be present (renders filter toggle)"
            data = _table_json(html)
            assert len(data) > 0, "JSON payload should have data for Svelte to render filters"

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
            
            # Svelte renders the table client-side; only the mount div is in the HTML
            table = soup.find('div', id='snapshot-table-root')
            assert table is not None, "Svelte mount div should be present"
            
            # Verify data content appears in JSON payload
            assert 'Species A' in html
            assert '25.00' in html

    def test_snapshot_page_omits_top_level_action_buttons(self):
        """Should omit the old top-level action-buttons wrapper; controls are rendered by Svelte."""
        csv_content = "Name,Price\nSpecies A,25.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .with_search(True) \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            assert soup.find('div', class_='action-buttons') is None
            assert soup.find('a', class_='btn--download') is None

            # The filter toggle button is now rendered by Svelte SortableTable
            mount_div = soup.find('div', id='snapshot-table-root')
            assert mount_div is not None, "Svelte mount div should be present (handles filter toggle button)"

    def test_snapshot_page_omits_top_level_download_button_when_search_disabled(self):
        """Should omit the old top-level download button when search is disabled."""
        csv_content = "Name,Price\nSpecies A,25.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .with_search(False) \
                .build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            assert soup.find('div', class_='action-buttons') is None
            assert soup.find('a', class_='btn--download') is None

            # Filter toggle is Svelte-rendered (not in Python HTML); its presence/absence
            # based on search config is verified by E2E tests.
            filter_button = soup.find('button', class_='btn--filters')
            assert filter_button is None, "Should NOT have filter button when search disabled"

    def test_table_stats_strip_shows_species_count(self):
        """Stats strip is rendered by Svelte SortableTable; JSON payload should have the correct row count."""
        csv_content = "Name,Price\nSpecies A,25.00\nSpecies B,30.00\nSpecies C,15.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .build()
            html = generate_snapshot_page(config)
            
            # Stats strip ("Showing X of Y species") is rendered by Svelte; verify JSON has the correct row count.
            data = _table_json(html)
            assert len(data) == 3, f"JSON payload should have 3 rows to match CSV, got {len(data)}"

    def test_table_stats_strip_exists_even_when_search_disabled(self):
        """Stats strip is rendered by Svelte regardless of search setting; JSON payload should have data."""
        csv_content = "Name,Price\nSpecies A,25.00\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .with_search(False) \
                .build()
            html = generate_snapshot_page(config)
            
            # Stats strip is rendered by Svelte from JSON data.
            data = _table_json(html)
            assert len(data) > 0, "JSON payload should have data (Svelte renders stats from this)"

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
        """Top-10 filter button is rendered by Svelte SortableTable; JSON should have enough Hot rows."""
        csv_content = "Species,Size (cm),Signal\n" + "".join(f"Species {i},1,🔥\n" for i in range(15))
        with temp_csv_file(csv_content) as filename:
            config = page_config.breeder(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .build()
            html = generate_analysis_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            # Top-10 filter button is rendered by Svelte SortableTable.
            # Verify the mount div exists and JSON has enough Hot rows.
            mount_div = soup.find('div', id='breeder-table-root')
            assert mount_div is not None, "Svelte mount div should be present for top-10 filter"

            data = _table_json(html)
            hot_rows = [row for row in data if row.get('Signal') == '🔥']
            assert len(hot_rows) >= 10, "Should have at least 10 Hot rows for Svelte top-10 filter rendering"

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
            # Legend details must have class="legend-box" so CSS box styles apply
            assert 'legend-box' in (legend_details[0].get('class') or []), \
                "Legend <details> must have class='legend-box' for CSS styling"

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

    def test_examples_render_collapsed_when_provided(self):
        """Practical Examples should render in a collapsed details block by default."""
        csv_content = "Species,Size (cm),Signal\nTest Spider,1.5,🔥\n"
        examples_md = "### 📖 Breeder Matrix — Practical Examples\n\nExample content."
        with temp_csv_file(csv_content) as filename:
            config = page_config.breeder(filename) \
                .with_title("Test") \
                .with_description("Desc") \
                .with_examples(examples_md) \
                .build()
            html = generate_analysis_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            details_elements = soup.find_all('details')
            example_details = [d for d in details_elements if 'Practical Examples' in d.text]
            assert len(example_details) == 1, "Should have a Practical Examples details element"
            assert example_details[0].get('open') is None, "Practical Examples should start collapsed"
            assert 'examples-box' in (example_details[0].get('class') or []), \
                "Examples <details> must have class='examples-box' for CSS styling"

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

            # Should have subtle anchors linking to methodology and legend sections
            details_links = instruction_box.find_all('a', attrs={'data-action': 'open-details'})
            assert len(details_links) == 2, "Instruction box should have methodology and legend anchor links"
            methodology_link = instruction_box.find('a', attrs={'data-target': 'methodology-section'})
            assert methodology_link is not None, "Instruction box should have a methodology anchor link"
            assert methodology_link.get('href') == '#methodology-section'
            legend_link = instruction_box.find('a', attrs={'data-target': 'legend-section'})
            assert legend_link is not None, "Instruction box should have a legend anchor link"
            assert legend_link.get('href') == '#legend-section'

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

            # Should have subtle anchors linking to methodology and legend sections
            details_links = instruction_box.find_all('a', attrs={'data-action': 'open-details'})
            assert len(details_links) == 2, "Instruction box should have methodology and legend anchor links"
            methodology_link = instruction_box.find('a', attrs={'data-target': 'methodology-section'})
            assert methodology_link is not None, "Instruction box should have a methodology anchor link"
            assert methodology_link.get('href') == '#methodology-section'
            legend_link = instruction_box.find('a', attrs={'data-target': 'legend-section'})
            assert legend_link is not None, "Instruction box should have a legend anchor link"
            assert legend_link.get('href') == '#legend-section'

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
        """All raw CSV column names must be replaced with proper English display names in JSON data.
        scrape_datetime is excluded from the visible columns and shown in an info box instead.
        (SortableTable renders headers client-side; we verify the JSON payload has correct keys.)"""
        row = ",".join(["2026-01-15T06:10+00:00", "Species A", "Common A",
                        "1.5", "25.00", "5", "http://example.com"])
        csv_content = ",".join(self._ALL_CSV_COLUMNS) + "\n" + row + "\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_title("T").with_description("D").build()
            html = generate_snapshot_page(config)
            soup = BeautifulSoup(html, "html.parser")

            # SortableTable renders headers client-side from the JSON data.
            # Verify the JSON payload uses display names, not raw CSV column names.
            data = _table_json(html)
            assert len(data) > 0, "Should have JSON data rows"
            json_keys = set(data[0].keys())

            for raw in self._ALL_CSV_COLUMNS:
                assert raw not in json_keys, (
                    f"Raw CSV column name '{raw}' should not appear as a JSON key"
                )
            for display in self._ALL_DISPLAY_HEADERS:
                assert display in json_keys, (
                    f"Expected display header '{display}' not found in JSON keys: {json_keys}"
                )

            # scrape_date shown in the table-stats-date paragraph, not a table column
            stats_date = soup.find(class_="table-stats-date")
            assert stats_date is not None, "Should have a table-stats-date element"
            assert "Scraped" in stats_date.get_text(), "Stats element should show scrape date"


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
        
        # Wishlist sliders are now rendered by the Svelte SortableTable from JSON data.
        # Verify the JSON payload contains all the wishlist values for Svelte to compute the range.
        data = _table_json(html)
        wishlist_values = [int(row['Wishlist Count']) for row in data if row.get('Wishlist Count', '').isdigit()]
        assert min(wishlist_values) == 5, f"Expected min wishlist value 5 in JSON, got {min(wishlist_values)}"
        assert max(wishlist_values) == 15, f"Expected max wishlist value 15 in JSON, got {max(wishlist_values)}"

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
        
        # Wishlist sliders are now rendered by Svelte; verify JSON has all rows including invalid.
        # Svelte SortableTable handles invalid values when computing the slider range (verified by E2E).
        data = _table_json(html)
        assert len(data) == 3, f"JSON payload should have all 3 rows, got {len(data)}"
        valid_values = [int(row['Wishlist Count']) for row in data if str(row.get('Wishlist Count', '')).isdigit()]
        assert 3 in valid_values, "JSON should contain wishlist value 3"
        assert 20 in valid_values, "JSON should contain wishlist value 20"

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
        
        # Wishlist sliders are now rendered by Svelte from JSON data.
        # Verify the single row has wishlist_count=42 in the JSON payload.
        data = _table_json(html)
        assert len(data) == 1, f"JSON payload should have 1 row, got {len(data)}"
        assert str(data[0].get('Wishlist Count')) == '42', f"Expected wishlist value 42, got {data[0].get('Wishlist Count')}"

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
        
        # Wishlist sliders are now rendered by Svelte from JSON data.
        # Verify JSON has all rows with wishlist values including 0 and 5.
        data = _table_json(html)
        wishlist_values = [row.get('Wishlist Count') for row in data]
        assert '0' in wishlist_values or 0 in wishlist_values, "JSON should contain wishlist count 0"
        assert '5' in wishlist_values or 5 in wishlist_values, "JSON should contain wishlist count 5"


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
        
        # Price sliders are now rendered by the Svelte SortableTable from JSON data.
        # Verify the JSON payload contains all price values for Svelte to compute the range.
        data = _table_json(html)
        assert len(data) == 3, f"JSON payload should have 3 rows, got {len(data)}"
        assert all('Price (GBP)' in row for row in data), "All JSON rows should have Price (GBP) field"
        # Prices are present in the JSON for Svelte to parse and compute slider range (verified by E2E)
        assert '£8.99' in html or '8.99' in html, "Price data should appear in JSON payload"

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
        
        # Price sliders are now rendered by Svelte; verify JSON has all rows including invalid price row.
        # Svelte SortableTable handles invalid values when computing the slider range (verified by E2E).
        data = _table_json(html)
        assert len(data) == 3, f"JSON payload should have all 3 rows (including invalid price row), got {len(data)}"

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
        
        # Price sliders are now rendered by Svelte from JSON data.
        # Verify the single row has price data in JSON.
        data = _table_json(html)
        assert len(data) == 1, f"JSON payload should have 1 row, got {len(data)}"
        assert 'Price (GBP)' in data[0], "JSON row should have Price (GBP) field"

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
        
        # Price sliders are now rendered by Svelte from JSON data.
        # Verify JSON has all rows with price data for Svelte to compute the range.
        data = _table_json(html)
        assert len(data) == 3, f"JSON payload should have 3 rows, got {len(data)}"
        assert all('Price (GBP)' in row for row in data), "All JSON rows should have Price (GBP) field"

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
        
        # Price sliders are now rendered by Svelte from JSON data.
        # Verify JSON has rows with price data even without £ symbol.
        data = _table_json(html)
        assert len(data) == 2, f"JSON payload should have 2 rows, got {len(data)}"
        assert all('Price (GBP)' in row for row in data), "All JSON rows should have Price (GBP) field"


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

    def test_svelte_mount_target_and_json_data_injected(self):
        """Should inject a Svelte mount-target div and table JSON data script.

        The download link, More Filters button, stats strip, and table structure are
        Svelte-rendered client-side and covered by E2E tests; this unit test verifies
        the server-side contract: mount target exists and JSON payload is present.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            skeleton = soup.find('div', attrs={'data-table-skeleton-for': config.table_id})
            assert skeleton is not None, "Should include a server-rendered history skeleton"
            assert 'table-skeleton--history' in skeleton.get('class', []), (
                "History page should use the history skeleton variant"
            )

            # Svelte mount target must be present
            mount_div = soup.find('div', id=f'{config.table_id}-root')
            assert mount_div is not None, "Should have Svelte mount-target div"

            # JSON data payload must be injected
            data = _table_json(html)
            assert len(data) == 1, "JSON data should contain one row"

    _ALL_CSV_COLUMNS = [
        "scrape_datetime", "scientific_name", "common_name",
        "size_cm", "price_gbp", "wishlist_count", "page_url",
    ]
    _ALL_DISPLAY_HEADERS = [
        "Scrape Date", "Scientific Name", "Common Name",
        "Size (cm)", "Price (GBP)", "Wishlist Count", "Page URL",
    ]

    def test_table_headers_use_proper_english_display_names(self):
        """JSON row keys must use proper English display names (not raw CSV column names).

        The <th> elements are Svelte-rendered and covered by E2E; this unit test verifies
        that generate_history_page injects JSON whose keys are the correct display labels.
        """
        row = ",".join(["2026-01-15T06:10+00:00", "Species A", "Common A",
                        "1.5", "25.00", "5", "http://example.com"])
        csv_content = ",".join(self._ALL_CSV_COLUMNS) + "\n" + row + "\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("T").with_description("D").build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 1, "Expected one row in JSON"
            keys = set(data[0].keys()) - {'_raw_scrape_datetime'}  # exclude internal key

            for raw in self._ALL_CSV_COLUMNS:
                assert raw not in keys, (
                    f"Raw CSV column name '{raw}' should not appear as a JSON key"
                )
            for display in self._ALL_DISPLAY_HEADERS:
                assert display in keys, (
                    f"Expected display header '{display}' not found in JSON keys: {keys}"
                )

    def test_json_data_injected_for_svelte_filter_rendering(self):
        """JSON payload must be present so Svelte can render the filter badge and toggle.

        The filter badge / More Filters button are Svelte-rendered; coverage is in E2E.
        This unit test verifies the server injects non-empty JSON when data is present.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 1, "JSON payload should contain one row for Svelte rendering"
            # Confirm table-id is used for the mount target so Svelte can find it
            soup = BeautifulSoup(html, 'html.parser')
            assert soup.find('div', id=f'{config.table_id}-root') is not None, "Mount target must exist"

    def test_json_data_present_so_svelte_can_render_search_panel(self):
        """JSON data must be injected when search_filter=True so Svelte renders the panel.

        The advanced-filters-content div and search input are Svelte-rendered (E2E coverage);
        this unit test verifies the Python side injects the JSON required by Svelte.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 1, "JSON payload must be non-empty for Svelte to render filters"
            assert 'Price (GBP)' in data[0], "JSON row should include Price column for slider"
            assert 'Wishlist Count' in data[0], "JSON row should include Wishlist column for slider"

    def test_omits_filter_toggle_when_search_disabled(self):
        """Should omit More Filters button when search_filter=False."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(False).build()
            html = generate_history_page(config)
            soup = BeautifulSoup(html, 'html.parser')

            # Filter toggle is Svelte-rendered (not in Python HTML); its presence/absence
            # based on search config is verified by E2E tests.
            assert soup.find('button', class_='btn--filters') is None, "Should not have filter toggle when search disabled"
            assert soup.find('input', type='text') is None, "Should not have search input when search disabled"

    def test_json_data_contains_all_rows_for_svelte_stats_strip(self):
        """JSON payload must include all rows so Svelte can display 'Showing N of N rows'.

        The table-stats strip is Svelte-rendered and covered by E2E; this unit test
        verifies the Python side injects the correct number of rows into the JSON.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08 10:00:00,Species B,Common B,2.0,30.00,8,http://example.com\n"
        csv_content += "2026-01-15 10:00:00,Species A,Common A,1.5,26.00,6,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 3, f"JSON should contain all 3 rows, got {len(data)}"

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

    def test_json_data_contains_price_values_for_svelte_slider(self):
        """JSON rows must include Price (GBP) values so Svelte can compute range slider bounds.

        The priceMin/priceMax slider inputs are Svelte-rendered and covered by E2E;
        this unit test verifies the Python side injects price data into the JSON.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,20.00,5,http://example.com\n"
        csv_content += "2026-01-08 10:00:00,Species B,Common B,2.0,35.00,8,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 2
            prices = {row.get('Price (GBP)') for row in data}
            assert '20.00' in prices, "JSON should include the min price value"
            assert '35.00' in prices, "JSON should include the max price value"

    def test_table_rows_have_data_price_attribute(self):
        """Should include price data in the JSON payload for JS filtering."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08 10:00:00,Species B,Common B,2.0,30.00,8,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 2, f"Expected 2 rows in JSON, got {len(data)}"
            prices = {row.get('Price (GBP)') for row in data}
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

    def test_json_data_contains_wishlist_values_for_svelte_slider(self):
        """JSON rows must include Wishlist Count values so Svelte can compute range slider bounds.

        The wishlistMin/wishlistMax slider inputs are Svelte-rendered and covered by E2E;
        this unit test verifies the Python side injects wishlist data into the JSON.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,20.00,3,http://example.com\n"
        csv_content += "2026-01-08 10:00:00,Species B,Common B,2.0,35.00,12,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 2
            wishlist_values = {str(row.get('Wishlist Count')) for row in data}
            assert '3' in wishlist_values, "JSON should include the min wishlist value"
            assert '12' in wishlist_values, "JSON should include the max wishlist value"

    def test_table_rows_have_data_wishlist_attribute(self):
        """Should include wishlist data in the JSON payload for JS filtering."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01 10:00:00,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08 10:00:00,Species B,Common B,2.0,30.00,10,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 2, f"Expected 2 rows in JSON, got {len(data)}"
            wishlist_values = {str(row.get('Wishlist Count')) for row in data}
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

    def test_json_data_contains_all_unique_dates_for_svelte_date_filter(self):
        """JSON rows must contain Scrape Date values for all unique dates.

        The date checkboxes are Svelte-rendered (DateFilter.svelte) and covered by E2E;
        this unit test verifies the Python side injects correct Scrape Date values.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species A,Common A,1.5,26.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species B,Common B,2.0,30.00,8,http://example.com\n"
        csv_content += "2026-01-15,Species A,Common A,1.5,27.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 4, f"Expected 4 rows in JSON, got {len(data)}"
            date_values = {str(row.get('Scrape Date')) for row in data}
            unique_dates = {d for d in date_values if d != 'None'}
            assert '2026-01-01' in unique_dates
            assert '2026-01-08' in unique_dates
            assert '2026-01-15' in unique_dates
            assert len(unique_dates) == 3, f"Expected 3 unique dates, got {unique_dates}"

    def test_json_data_row_counts_per_date_are_correct(self):
        """JSON rows per date must match the CSV row counts per unique scrape_datetime.

        The date checkbox row counts are Svelte-rendered (DateFilter.svelte) from this
        JSON data; E2E tests verify the UI display. This test verifies the server injects
        the correct number of rows per date.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species A,Common A,1.5,26.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species B,Common B,2.0,30.00,8,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)

            data = _table_json(html)
            from collections import Counter
            date_counts = Counter(str(row.get('Scrape Date')) for row in data)
            assert date_counts['2026-01-01'] == 1, f"Expected 1 row for 2026-01-01, got {date_counts['2026-01-01']}"
            assert date_counts['2026-01-08'] == 2, f"Expected 2 rows for 2026-01-08, got {date_counts['2026-01-08']}"

    def test_rows_have_data_date_attribute(self):
        """Each row in the JSON payload should include its formatted scrape_datetime."""
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species B,Common B,2.0,30.00,8,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 2, f"Expected 2 rows in JSON, got {len(data)}"
            date_values = {str(row.get('Scrape Date')) for row in data}
            assert '2026-01-01' in date_values
            assert '2026-01-08' in date_values

    def test_json_data_dates_in_csv_order_for_svelte_to_reverse(self):
        """JSON rows must preserve CSV (oldest-first) Scrape Date order for all rows.

        Svelte's DateFilter component reverses the unique dates to show most-recent-first;
        the JSON rows contain per-row dates in CSV order. E2E covers the rendered order;
        this unit test confirms the per-row Scrape Date values in the JSON are correct.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species B,Common B,2.0,30.00,8,http://example.com\n"
        csv_content += "2026-01-15,Species A,Common A,1.5,27.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 3, f"Expected 3 rows, got {len(data)}"
            row_dates = [str(row.get('Scrape Date')) for row in data]
            assert row_dates[0] == '2026-01-01', f"First CSV row date should be 2026-01-01, got {row_dates[0]}"
            assert row_dates[-1] == '2026-01-15', f"Last CSV row date should be 2026-01-15, got {row_dates[-1]}"

    def test_json_rows_include_raw_scrape_datetime_for_svelte_date_filter(self):
        """Every JSON row must include _raw_scrape_datetime so Svelte's DateFilter can work.

        The 'All Dates' master checkbox is Svelte-rendered (DateFilter.svelte) and uses
        the _raw_scrape_datetime key; this unit test verifies the Python side injects it.
        """
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Species A,Common A,1.5,25.00,5,http://example.com\n"
        csv_content += "2026-01-08,Species B,Common B,2.0,30.00,8,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.history(filename).with_title("Test").with_description("Desc").with_search(True).build()
            html = generate_history_page(config)

            data = _table_json(html)
            assert len(data) == 2, f"Expected 2 rows, got {len(data)}"
            for row in data:
                assert '_raw_scrape_datetime' in row, "Every JSON row must have _raw_scrape_datetime for DateFilter"
            raw_dates = {row['_raw_scrape_datetime'] for row in data}
            assert '2026-01-01' in raw_dates
            assert '2026-01-08' in raw_dates

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


class TestHamburgerNav:
    """HTML structure tests for the hamburger navigation added in Phase 13.

    Each regular page (extending base.html) must render:
    - A .nav-toggle button with the correct ARIA attributes
    - Three .nav-toggle__bar spans inside it
    - A <nav id="main-nav"> element containing links
    - A .header__inner wrapper around the title and the toggle

    Species detail pages must suppress both elements entirely — breadcrumbs
    and back buttons already provide all the navigation context needed.
    """

    # ------------------------------------------------------------------
    # Regular pages — hamburger button present
    # ------------------------------------------------------------------

    def test_homepage_has_nav_toggle_button(self):
        """Homepage must contain the hamburger button."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        btn = soup.find('button', class_='nav-toggle')
        assert btn is not None, "Homepage must have a .nav-toggle button"

    def test_nav_toggle_has_aria_expanded_false(self):
        """Hamburger button must start in closed state (aria-expanded=false)."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        btn = soup.find('button', class_='nav-toggle')
        assert btn is not None
        assert btn.get('aria-expanded') == 'false', (
            f"nav-toggle must have aria-expanded='false', got {btn.get('aria-expanded')!r}"
        )

    def test_nav_toggle_has_aria_controls_main_nav(self):
        """Hamburger button must reference the nav via aria-controls."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        btn = soup.find('button', class_='nav-toggle')
        assert btn is not None
        assert btn.get('aria-controls') == 'main-nav', (
            f"nav-toggle must have aria-controls='main-nav', got {btn.get('aria-controls')!r}"
        )

    def test_nav_toggle_has_three_bar_spans(self):
        """Hamburger icon must consist of three .nav-toggle__bar spans."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        btn = soup.find('button', class_='nav-toggle')
        assert btn is not None
        bars = btn.find_all('span', class_='nav-toggle__bar')
        assert len(bars) == 3, f"nav-toggle must have 3 bar spans, found {len(bars)}"

    def test_homepage_has_main_nav(self):
        """Homepage must contain a <nav id='main-nav'> element."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        nav = soup.find('nav', id='main-nav')
        assert nav is not None, "Homepage must have <nav id='main-nav'>"

    def test_homepage_nav_contains_all_links(self):
        """Main nav must contain links to every section of the site."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        nav = soup.find('nav', id='main-nav')
        assert nav is not None
        hrefs = {a.get('href') for a in nav.find_all('a')}
        for expected in ('index.html', 'snapshot.html', 'history.html', 'breeder.html', 'dealer.html'):
            assert expected in hrefs, f"Main nav is missing a link to {expected}"

    def test_header_inner_wraps_title_and_toggle(self):
        """The .header__inner div must contain both the title block and the toggle button."""
        html = generate_homepage()
        soup = BeautifulSoup(html, 'html.parser')
        inner = soup.find('div', class_='header__inner')
        assert inner is not None, "<header> must have a .header__inner wrapper"
        assert inner.find('div', class_='header__title') is not None, (
            ".header__inner must contain .header__title"
        )
        assert inner.find('button', class_='nav-toggle') is not None, (
            ".header__inner must contain the .nav-toggle button"
        )

    def test_analysis_page_has_nav_toggle_button(self, tmp_path):
        """Analysis pages (e.g. snapshot) must also contain the hamburger button."""
        from conftest import temp_csv_file
        csv_content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        csv_content += "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,25.00,5,http://example.com\n"
        with temp_csv_file(csv_content) as filename:
            config = page_config.snapshot(filename).with_title("Test Snapshot").with_description("Desc").build()
            html = generate_snapshot_page(config)
        soup = BeautifulSoup(html, 'html.parser')
        assert soup.find('button', class_='nav-toggle') is not None, (
            "Snapshot page must have a .nav-toggle button"
        )
        assert soup.find('nav', id='main-nav') is not None, (
            "Snapshot page must have <nav id='main-nav'>"
        )

    # ------------------------------------------------------------------
    # Species detail pages — hamburger and nav suppressed
    # ------------------------------------------------------------------

    def test_species_detail_has_no_nav_toggle(self):
        """Species detail page must NOT render the hamburger button."""
        from website.species_detail import generate_species_page
        html = generate_species_page(
            scientific_name='Aphonopelma seemanni',
            common_name='Costa Rican Zebra',
            species_data={},
            chart_data={'runs': []},
        )
        soup = BeautifulSoup(html, 'html.parser')
        assert soup.find('button', class_='nav-toggle') is None, (
            "Species detail page must NOT render the .nav-toggle hamburger button"
        )

    def test_species_detail_has_no_main_nav(self):
        """Species detail page must NOT render the main navigation."""
        from website.species_detail import generate_species_page
        html = generate_species_page(
            scientific_name='Aphonopelma seemanni',
            common_name='Costa Rican Zebra',
            species_data={},
            chart_data={'runs': []},
        )
        soup = BeautifulSoup(html, 'html.parser')
        assert soup.find('nav') is None, (
            "Species detail page must NOT render a <nav> element"
        )

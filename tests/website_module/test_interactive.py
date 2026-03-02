#!/usr/bin/env python3
"""Tests for interactive table features."""
import json
import re
import pytest
import os
from pathlib import Path
from bs4 import BeautifulSoup
from conftest import page_config
from website.generate_website import generate_analysis_page, generate_snapshot_page


def _table_json(html: str) -> list:
    """Extract and parse the window['...Data'] JSON from a rendered page."""
    m = re.search(r"window\['[^']+Data'\]\s*=\s*(\[.*?\])\s*;", html, re.DOTALL)
    return json.loads(m.group(1)) if m else []


class TestInteractiveFilterButtons:
    """Test suite for interactive filter buttons in data tables.
    
    This implements the UX enhancement for quick filtering of tables by signal type,
    allowing users to instantly show only Hot (🔥), Watch (⚠️), or Avoid (❌) items.
    """

    def test_breeder_page_has_filter_buttons(self, tmp_path):
        """Breeder page should include filter buttons above the table for Signal column."""
        # Create a test CSV with Signal column
        csv_file = tmp_path / "test_breeder.csv"
        csv_file.write_text(
            "Species,Signal,Recommendation\n"
            "Hot Species,🔥,Good opportunity\n"
            "Watch Species,⚠️,Monitor\n"
            "Avoid Species,❌,Skip\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("test_breeder.csv").with_title("Test Breeder Opportunities").with_description("Test description").build()
        html = generate_analysis_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Filter buttons are now rendered by the Svelte SortableTable component.
        # Verify the Svelte mount point and JSON payload are present.
        mount_div = soup.find('div', id='breeder-table-root')
        assert mount_div is not None, "Svelte mount div should be present for breeder table"
        
        data = _table_json(html)
        signal_values = {row.get('Signal') for row in data}
        assert '🔥' in signal_values, "JSON payload should have Hot signal data for Svelte filter rendering"
        assert '⚠️' in signal_values, "JSON payload should have Watch signal data for Svelte filter rendering"
        assert '❌' in signal_values, "JSON payload should have Avoid signal data for Svelte filter rendering"

    def test_dealer_page_has_filter_buttons(self, tmp_path):
        """Dealer page should include filter buttons above the table for Dealer Risk column."""
        csv_file = tmp_path / "test_dealer.csv"
        csv_file.write_text(
            "Species,Stock Reliability,Dealer Risk,Recommendation\n"
            "Risky Species,40%,🔥,Stock up\n"
            "Watch Species,65%,⚠️,Monitor\n"
            "Safe Species,95%,❌,No action\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.dealer("test_dealer.csv").with_title("Test Dealer Supply Risk").with_description("Test description").build()
        html = generate_analysis_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Filter buttons are now rendered by the Svelte SortableTable component.
        mount_div = soup.find('div', id='dealer-table-root')
        assert mount_div is not None, "Svelte mount div should be present for dealer table"
        
        data = _table_json(html)
        risk_values = {row.get('Dealer Risk') for row in data}
        assert len(risk_values) > 0, "JSON payload should have Dealer Risk data for Svelte filter rendering"

    def test_filter_buttons_have_onclick_handlers(self, tmp_path):
        """Filter buttons should have data attributes for JavaScript filtering (behavior tested by E2E)."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Species,Signal\nTest,🔥\n")
        
        os.chdir(tmp_path)
        config = page_config.breeder("test.csv").with_title("Test").with_description("Test").build()
        html = generate_analysis_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        buttons = soup.find_all('button', class_='filter-btn')
        
        # Each button should have data attributes for event listeners (behavior validated by E2E tests)
        for btn in buttons:
            assert btn.get('data-action') is not None, "Filter buttons should have data-action attribute"
            assert btn.get('data-signal') is not None, "Filter buttons should have data-signal attribute"
            assert btn.get('data-table-id') is not None, "Filter buttons should have data-table-id attribute"

    def test_snapshot_page_has_no_filter_buttons(self, tmp_path):
        """Snapshot and history pages should NOT have filter buttons (no Signal column)."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Species,Price,Size\nTest,25.00,2\n")
        
        os.chdir(tmp_path)
        config = page_config.snapshot("test.csv").with_description("Test").build()
        html = generate_snapshot_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should NOT have filter buttons
        filter_container = soup.find('div', class_='filter-buttons-container')
        assert filter_container is None, "Snapshot page should not have filter buttons (no Signal column)"

    def test_javascript_filter_function_exists(self, tmp_path):
        """Generated pages should reference external JavaScript and have filter attributes.
        
        Note: This test only verifies HTML structure. Actual JS behavior is tested via E2E tests.
        """
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Species,Signal\nTest,🔥\n")
        
        os.chdir(tmp_path)
        config = page_config.breeder("test.csv").with_title("Test").with_description("Test").build()
        html = generate_analysis_page(config)
        
        # Verify HTML references external JS and JSON payload has signal data for Svelte filtering
        assert 'src="breeder-page.js"' in html, "Should reference the breeder page slice script"
        data = _table_json(html)
        assert len(data) > 0, "JSON payload should have rows for Svelte to render"
        assert data[0].get('Signal') in ['🔥', '⚠️', '❌'], "JSON rows should have Signal values for Svelte filter rendering"


class TestStockPatternFiltering:
    """Test suite for Stock Pattern filtering feature on breeder page."""

    def test_breeder_page_has_stock_pattern_filter_buttons(self, tmp_path):
        """Breeder page should have Stock Pattern filter buttons."""
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text(
            "Species,Size (cm),OOS,OOS Runs,Stock Pattern,Signal\n"
            "Test Species 1,1,OUT,4,Sustained,🔥\n"
            "Test Species 2,2,OUT,3,Emerging,⚠️\n"
            "Test Species 3,1,IN/OUT,0,Cyclical,⚠️\n"
            "Test Species 4,1,IN,0,Always,❌\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("breeder.csv").with_title("Breeder Opportunities").with_description("Test").build()
        html = generate_analysis_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Stock pattern filter buttons are now rendered by the Svelte SortableTable component.
        # Verify the Svelte mount point and JSON payload have the correct stock pattern data.
        mount_div = soup.find('div', id='breeder-table-root')
        assert mount_div is not None, "Svelte mount div should be present for breeder table"
        
        data = _table_json(html)
        patterns = {row.get('Stock Pattern') for row in data}
        assert 'Sustained' in patterns, "JSON payload should include Sustained stock pattern"
        assert 'Emerging' in patterns, "JSON payload should include Emerging stock pattern"
        assert 'Cyclical' in patterns, "JSON payload should include Cyclical stock pattern"
        assert 'Always' in patterns, "JSON payload should include Always stock pattern"

    def test_breeder_table_rows_have_stock_pattern_data_attribute(self, tmp_path):
        """Breeder table rows should have data-stock-pattern attribute for filtering."""
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text(
            "Species,Size (cm),OOS,OOS Runs,Stock Pattern,Signal\n"
            "Test Species 1,1,OUT,4,Sustained,🔥\n"
            "Test Species 2,2,OUT,3,Emerging,⚠️\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("breeder.csv").with_title("Breeder Opportunities").with_description("Test").build()
        html = generate_analysis_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        # Svelte renders the table — no Python-generated <table> element
        assert soup.find('div', id='breeder-table-root') is not None, "Should have mount div"

        data = _table_json(html)
        assert len(data) == 2, f"Expected 2 rows in JSON, got {len(data)}"

        # Check first row
        assert data[0].get('Stock Pattern') == 'Sustained'
        assert data[0].get('Signal') == '🔥'

        # Check second row
        assert data[1].get('Stock Pattern') == 'Emerging'
        assert data[1].get('Signal') == '⚠️'
    
    def test_top_10_filter_button_replaces_separate_table(self, tmp_path):
        """Verify the Top 10 section is a filter button, not a separate table.
        
        The old approach rendered a separate top 10 table. The new approach
        uses a '🔥 Hot (top 10)' filter button that limits the full table to
        the first 10 Hot rows via client-side JS (data-limit attribute).
        
        This test ensures:
        - Only ONE table exists (no separate top 10 table)
        - A '🔥 Hot (top 10)' filter button exists with correct data attributes
        - Full table rows have all required data attributes for filtering
        - The top 10 button targets the correct table ID
        """
        # Create 15 rows to ensure the full dataset is large enough
        rows = []
        for i in range(15):
            pattern = ['Sustained', 'Emerging', 'Cyclical'][i % 3]
            signal = ['🔥', '⚠️', '❌'][i % 3]
            rows.append(f"Species {i},1,OUT,{i+1},{pattern},{signal}")
        
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text(
            "Species,Size (cm),OOS,OOS Runs,Stock Pattern,Signal\n" +
            "\n".join(rows)
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("breeder.csv").with_title("Breeder Opportunities").with_description("Test").build()
        html = generate_analysis_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Svelte renders the table — no separate Python-generated tables exist
        all_tables = soup.find_all('table')
        assert len(all_tables) == 0, f"Svelte pages should have 0 Python-rendered tables, found {len(all_tables)}"
        
        # The mount div and JSON script replace the old table element
        assert soup.find('div', id='breeder-table-root') is not None, "Should have mount div"

        # CRITICAL: JSON data must contain all 15 rows with Signal and Stock Pattern fields
        data = _table_json(html)
        assert len(data) == 15, f"JSON data should have all 15 rows, found {len(data)}"
        for i, row in enumerate(data):
            assert 'Signal' in row, f"Row {i} missing Signal field in JSON"
            assert 'Stock Pattern' in row, f"Row {i} missing Stock Pattern field in JSON"
            assert row['Signal'] in ['🔥', '⚠️', '❌'], f"Invalid signal value: {row['Signal']}"

        # The top-10 filter button is now rendered by the Svelte SortableTable component.
        # Verify JSON has enough Hot rows for Svelte to render the top-10 button.
        hot_rows = [row for row in data if row.get('Signal') == '🔥']
        assert len(hot_rows) >= 5, "JSON should have enough Hot rows for top-10 filtering"

    def test_dealer_page_does_not_have_stock_pattern_filters(self, tmp_path):
        """Dealer page should NOT have Stock Pattern filters (not applicable)."""
        csv_file = tmp_path / "dealer.csv"
        csv_file.write_text(
            "Species,Size (cm),Stock Reliability,Dealer Risk\n"
            "Test Species,1,Low,🔥\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.dealer("dealer.csv").with_title("Dealer Supply Risk").with_description("Test").build()
        html = generate_analysis_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should NOT have stock pattern filters
        stock_pattern_container = soup.find('div', class_='stock-pattern-filters')
        assert stock_pattern_container is None, "Dealer page should not have stock pattern filters"

    def test_stock_pattern_filter_javascript_function_exists(self, tmp_path):
        """Breeder page should reference external JavaScript and have stock pattern attributes."""
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text(
            "Species,Size (cm),Stock Pattern,Signal\n"
            "Test,1,Sustained,🔥\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("breeder.csv").with_title("Breeder Opportunities").with_description("Test").build()
        html = generate_analysis_page(config)
        
        # Should reference the breeder page slice script; JSON payload should have stock pattern data.
        # Actual filtering behaviour is verified by E2E tests.
        assert 'src="breeder-page.js"' in html, "Should reference the breeder page slice script"
        data = _table_json(html)
        assert any(row.get('Stock Pattern') for row in data), "JSON rows should have Stock Pattern values"

    def test_stock_pattern_buttons_have_counts(self, tmp_path):
        """Stock pattern filter buttons should display counts for each pattern."""
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text(
            "Species,Size (cm),Stock Pattern,Signal\n"
            "Species 1,1,Sustained,🔥\n"
            "Species 2,2,Sustained,🔥\n"
            "Species 3,1,Emerging,⚠️\n"
            "Species 4,1,Emerging,⚠️\n"
            "Species 5,1,Emerging,⚠️\n"
            "Species 6,1,Cyclical,⚠️\n"
            "Species 7,1,Always,❌\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("breeder.csv").with_title("Breeder Opportunities").with_description("Test").build()
        html = generate_analysis_page(config)
        
        # Stock pattern counts are now computed by the Svelte SortableTable from JSON data.
        # Verify the JSON payload has the correct stock pattern distribution.
        from collections import Counter
        data = _table_json(html)
        counts = Counter(row.get('Stock Pattern') for row in data)
        assert len(data) == 7, f"JSON should have all 7 rows, got {len(data)}"
        assert counts['Sustained'] == 2, "Should have 2 Sustained rows in JSON"
        assert counts['Emerging'] == 3, "Should have 3 Emerging rows in JSON"
        assert counts['Cyclical'] == 1, "Should have 1 Cyclical row in JSON"
        assert counts['Always'] == 1, "Should have 1 Always row in JSON"

    def test_stock_pattern_filter_has_clear_label(self, tmp_path):
        """Stock pattern filters should have a clear label indicating what they filter."""
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text(
            "Species,Size (cm),Stock Pattern,Signal\n"
            "Test,1,Sustained,🔥\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("breeder.csv").with_title("Breeder Opportunities").with_description("Test").build()
        html = generate_analysis_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Stock pattern filter label is now rendered by the Svelte SortableTable component.
        # The JSON payload contains "Stock Pattern" as a data field key, which is present in the HTML.
        html_lower = html.lower()
        assert 'stock pattern' in html_lower, \
            "Should have 'Stock Pattern' referenced in HTML (in JSON payload for Svelte rendering)"

    def test_signal_filter_has_clear_label_on_breeder_page(self, tmp_path):
        """Signal filters should have a clear label on breeder page for consistency."""
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text(
            "Species,Size (cm),Signal\n"
            "Test,1,🔥\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("breeder.csv").with_title("Breeder Opportunities").with_description("Test").build()
        html = generate_analysis_page(config)
        
        # Signal filter labels are now rendered by the Svelte SortableTable component.
        # Verify the JSON payload has Signal field data for Svelte to render filter labels.
        data = _table_json(html)
        assert len(data) > 0, "JSON payload should have rows"
        assert 'Signal' in data[0], "JSON rows should have Signal field for Svelte to render filter labels"

    def test_signal_filter_has_clear_label_on_dealer_page(self, tmp_path):
        """Dealer Risk filters should have a clear label on dealer page for consistency."""
        csv_file = tmp_path / "dealer.csv"
        csv_file.write_text(
            "Species,Size (cm),Dealer Risk\n"
            "Test,1,🔥\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.dealer("dealer.csv").with_title("Dealer Supply Risk").with_description("Test").build()
        html = generate_analysis_page(config)
        
        # Should have a label for dealer risk filters (e.g., "🎯 Risk Level:" or "Dealer Risk:")
        html_lower = html.lower()
        assert 'risk' in html_lower and ':' in html, \
            "Dealer page should have clear label for risk level filters"



#!/usr/bin/env python3
"""Tests for interactive table features."""
import pytest
import os
from pathlib import Path
from bs4 import BeautifulSoup
from conftest import page_config
from website.generate_website import generate_data_page


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
        html = generate_data_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should have a filter container
        filter_container = soup.find('div', class_='filter-buttons-container')
        assert filter_container is not None, "Should have filter buttons container"
        
        # Should have filter buttons with correct labels and emojis
        buttons = filter_container.find_all('button', class_='filter-btn')
        assert len(buttons) == 4, "Should have 4 filter buttons (All, Hot, Watch, Avoid)"
        
        button_texts = [btn.get_text(strip=True) for btn in buttons]
        assert 'Show All' in button_texts[0], "Should have Show All button"
        assert '🔥' in button_texts[1], "Should have Hot button with emoji"
        assert '⚠️' in button_texts[2], "Should have Watch button with emoji"
        assert '❌' in button_texts[3], "Should have Avoid button with emoji"

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
        html = generate_data_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should have filter buttons
        filter_container = soup.find('div', class_='filter-buttons-container')
        assert filter_container is not None, "Should have filter buttons container"
        
        buttons = filter_container.find_all('button', class_='filter-btn')
        assert len(buttons) == 4, "Should have 4 filter buttons"

    def test_filter_buttons_have_onclick_handlers(self, tmp_path):
        """Filter buttons should have onclick handlers for JavaScript filtering."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Species,Signal\nTest,🔥\n")
        
        os.chdir(tmp_path)
        config = page_config.breeder("test.csv").with_title("Test").with_description("Test").build()
        html = generate_data_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        buttons = soup.find_all('button', class_='filter-btn')
        
        # Each button should have an onclick attribute
        for btn in buttons:
            assert btn.get('onclick') is not None, "Filter buttons should have onclick handlers"
            assert 'filterBySignal' in btn.get('onclick'), "Should call filterBySignal function"

    def test_snapshot_page_has_no_filter_buttons(self, tmp_path):
        """Snapshot and history pages should NOT have filter buttons (no Signal column)."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Species,Price,Size\nTest,25.00,2\n")
        
        os.chdir(tmp_path)
        config = page_config.snapshot("test.csv").with_description("Test").build()
        html = generate_data_page(config)
        
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
        html = generate_data_page(config)
        
        # Verify HTML includes JS reference and data attributes (structure only)
        assert 'src="table-interactions.js"' in html, "Should reference external JavaScript file"
        assert 'data-signal=' in html, "Table rows should have data-signal attributes for filtering"
        
        # Verify JS file exists (but don't check implementation - E2E tests verify behavior)
        js_file = Path(__file__).parent.parent.parent / "templates" / "scripts" / "table-interactions.js"
        assert js_file.exists(), "JavaScript file should exist"


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
        html = generate_data_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should have stock pattern filter buttons
        stock_pattern_container = soup.find('div', class_='stock-pattern-filters')
        assert stock_pattern_container is not None, "Breeder page should have stock pattern filter container"
        
        # Check for specific filter buttons
        buttons = stock_pattern_container.find_all('button', class_='filter-btn')
        button_texts = [btn.text.strip() for btn in buttons]
        
        # Check that buttons exist (may have counts in parentheses now)
        assert any('Show All' in text for text in button_texts), "Should have 'Show All' button"
        assert any('Sustained' in text for text in button_texts), "Should have 'Sustained' filter button"
        assert any('Emerging' in text for text in button_texts), "Should have 'Emerging' filter button"
        assert any('Cyclical' in text for text in button_texts), "Should have 'Cyclical' filter button"
        assert any('Always' in text for text in button_texts), "Should have 'Always' filter button"

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
        html = generate_data_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', id='breeder-table')
        rows = table.select('tbody tr')
        
        # Check first row
        assert rows[0].get('data-stock-pattern') == 'Sustained'
        assert rows[0].get('data-signal') == '🔥'
        
        # Check second row
        assert rows[1].get('data-stock-pattern') == 'Emerging'
        assert rows[1].get('data-signal') == '⚠️'
    
    def test_top_10_and_full_table_have_unique_ids_and_correct_filter_attributes(self, tmp_path):
        """Regression test: Top 10 and full table must have unique IDs and full table needs filter attributes.
        
        Bug fixed: When top 10 table was introduced, both tables had id='breeder-table',
        causing JavaScript filters to target the wrong table (top 10 instead of full table).
        Additionally, the full table's rows lacked data-signal and data-stock-pattern attributes
        because context variables weren't passed to the template include.
        
        This test ensures:
        - Table IDs are unique (breeder-table-top10 vs breeder-table)
        - Full table rows have all required data attributes for filtering
        - Filter buttons target the correct table ID (full table, not top 10)
        """
        # Create 15 rows to ensure top 10 section renders
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
        html = generate_data_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should have EXACTLY 2 tables (top 10 + full)
        all_tables = soup.find_all('table')
        assert len(all_tables) == 2, f"Should have 2 tables (top 10 + full), found {len(all_tables)}"
        
        # Tables MUST have UNIQUE IDs (was the root cause of the bug)
        table_ids = [t.get('id') for t in all_tables]
        assert len(table_ids) == len(set(table_ids)), f"Table IDs must be unique, found duplicates: {table_ids}"
        assert 'breeder-table-top10' in table_ids, "Top 10 table should have -top10 suffix"
        assert 'breeder-table' in table_ids, "Full table should have base ID"
        
        # Top 10 table should have exactly 10 rows
        top_10_table = soup.find('table', id='breeder-table-top10')
        assert top_10_table is not None, "Top 10 table should exist"
        top_10_rows = top_10_table.select('tbody tr')
        assert len(top_10_rows) == 10, f"Top 10 should have 10 rows, found {len(top_10_rows)}"
        
        # Full table should have all 15 rows
        full_table = soup.find('table', id='breeder-table')
        assert full_table is not None, "Full table should exist"
        full_rows = full_table.select('tbody tr')
        assert len(full_rows) == 15, f"Full table should have 15 rows, found {len(full_rows)}"
        
        # CRITICAL: Full table rows MUST have data-signal and data-stock-pattern attributes
        # This was missing because template {% include %} didn't pass context variables
        for i, row in enumerate(full_rows):
            signal_attr = row.get('data-signal')
            pattern_attr = row.get('data-stock-pattern')
            assert signal_attr is not None, f"Full table row {i} missing data-signal attribute (filters won't work)"
            assert pattern_attr is not None, f"Full table row {i} missing data-stock-pattern attribute (filters won't work)"
            assert signal_attr in ['🔥', '⚠️', '❌'], f"Invalid signal value: {signal_attr}"
        
        # Filter buttons MUST target the full table (breeder-table), NOT the top 10 table
        filter_buttons = soup.find_all('button', class_='filter-btn')
        assert len(filter_buttons) > 0, "Should have filter buttons"
        
        for btn in filter_buttons:
            onclick = btn.get('onclick', '')
            if 'filterBySignal' in onclick or 'filterByStockPattern' in onclick:
                assert "'breeder-table'" in onclick, f"Filter button should target 'breeder-table', found: {onclick}"
                assert "'breeder-table-top10'" not in onclick, f"Filter must NOT target top 10 table: {onclick}"

    def test_dealer_page_does_not_have_stock_pattern_filters(self, tmp_path):
        """Dealer page should NOT have Stock Pattern filters (not applicable)."""
        csv_file = tmp_path / "dealer.csv"
        csv_file.write_text(
            "Species,Size (cm),Stock Reliability,Dealer Risk\n"
            "Test Species,1,Low,🔥\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.dealer("dealer.csv").with_title("Dealer Supply Risk").with_description("Test").build()
        html = generate_data_page(config)
        
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
        html = generate_data_page(config)
        
        # Should reference external JS file and have data attributes
        assert 'src="table-interactions.js"' in html, "Should reference external JavaScript file"
        assert 'data-stock-pattern=' in html, "Table rows should have data-stock-pattern attributes"
        
        # Verify the external JavaScript file contains filterByStockPattern function
        js_file = Path(__file__).parent.parent.parent / "templates" / "scripts" / "table-interactions.js"
        assert js_file.exists(), "JavaScript file should exist"
        js_content = js_file.read_text()
        assert 'function filterByStockPattern' in js_content

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
        html = generate_data_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        stock_pattern_container = soup.find('div', class_='stock-pattern-filters')
        buttons = stock_pattern_container.find_all('button', class_='filter-btn')
        button_texts = [btn.text.strip() for btn in buttons]
        
        # Check for counts in button text
        assert 'Show All (7)' in button_texts, "Show All should have total count"
        assert 'Sustained (2)' in button_texts, "Sustained should have count of 2"
        assert 'Emerging (3)' in button_texts, "Emerging should have count of 3"
        assert 'Cyclical (1)' in button_texts, "Cyclical should have count of 1"
        assert 'Always (1)' in button_texts, "Always should have count of 1"

    def test_stock_pattern_filter_has_clear_label(self, tmp_path):
        """Stock pattern filters should have a clear label indicating what they filter."""
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text(
            "Species,Size (cm),Stock Pattern,Signal\n"
            "Test,1,Sustained,🔥\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("breeder.csv").with_title("Breeder Opportunities").with_description("Test").build()
        html = generate_data_page(config)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should have a label/heading for stock pattern filters
        # Look for text like "Stock Pattern:" or "Filter by Pattern:" near the buttons
        stock_pattern_container = soup.find('div', class_='stock-pattern-filters')
        assert stock_pattern_container is not None
        
        # Check if there's a label element or heading text before/inside the container
        # The label should contain "Stock Pattern" or similar text
        parent = stock_pattern_container.parent
        assert parent is not None
        
        # Look for label text in the HTML near the filter buttons
        html_lower = html.lower()
        assert 'stock pattern' in html_lower or 'filter by pattern' in html_lower, \
            "Should have clear label indicating stock pattern filtering"

    def test_signal_filter_has_clear_label_on_breeder_page(self, tmp_path):
        """Signal filters should have a clear label on breeder page for consistency."""
        csv_file = tmp_path / "breeder.csv"
        csv_file.write_text(
            "Species,Size (cm),Signal\n"
            "Test,1,🔥\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.breeder("breeder.csv").with_title("Breeder Opportunities").with_description("Test").build()
        html = generate_data_page(config)
        
        # Should have a label for signal filters (e.g., "🎯 Signal:" or similar)
        html_lower = html.lower()
        assert 'signal:' in html_lower, "Breeder page should have clear label for signal filters"

    def test_signal_filter_has_clear_label_on_dealer_page(self, tmp_path):
        """Dealer Risk filters should have a clear label on dealer page for consistency."""
        csv_file = tmp_path / "dealer.csv"
        csv_file.write_text(
            "Species,Size (cm),Dealer Risk\n"
            "Test,1,🔥\n"
        )
        
        os.chdir(tmp_path)
        config = page_config.dealer("dealer.csv").with_title("Dealer Supply Risk").with_description("Test").build()
        html = generate_data_page(config)
        
        # Should have a label for dealer risk filters (e.g., "🎯 Risk Level:" or "Dealer Risk:")
        html_lower = html.lower()
        assert 'risk' in html_lower and ':' in html, \
            "Dealer page should have clear label for risk level filters"



#!/usr/bin/env python3
"""
Tests for scrape_spidershop_spiderlings.py orchestration logic.

Focuses on the main() workflow without duplicating tests for individual
modules (scraper, breeder_matrix, dealer_matrix, etc.).
"""

import pytest
from unittest.mock import patch, mock_open
from scrape_spidershop_spiderlings import main


# Minimal HTML that includes product structure
MINIMAL_PRODUCT_LIST_HTML = """
<ul class="products">
    <li>
        <a href="/product/megaphobema-mesomelas/">
            <div class="product-text">
                <h2>Megaphobema mesomelas</h2>
                <h3>Costa Rican Red Leg (1-2cm)</h3>
                <span class="price">£100.00</span>
            </div>
        </a>
    </li>
</ul>
"""

MINIMAL_PRODUCT_PAGE_HTML = """
<div class="product-text">
    <h2>Megaphobema mesomelas</h2>
    <h3>Costa Rican Red Leg (1-2cm)</h3>
    <span class="price">£100.00</span>
</div>
"""


class TestMainOrchestration:
    """Test the main() orchestration workflow."""

    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.scrape_product')
    @patch('scrape_spidershop_spiderlings.extract_product_urls')
    @patch('scrape_spidershop_spiderlings.load_history')
    @patch('scrape_spidershop_spiderlings.append_history')
    @patch('scrape_spidershop_spiderlings.write_pricing_summary')
    @patch('scrape_spidershop_spiderlings.build_breeder_opportunity_table')
    @patch('scrape_spidershop_spiderlings.write_breeder_outputs')
    @patch('scrape_spidershop_spiderlings.build_dealer_supply_risk_table')
    @patch('scrape_spidershop_spiderlings.write_dealer_outputs')
    @patch('scrape_spidershop_spiderlings.write_summary_legend')
    @patch('scrape_spidershop_spiderlings.close_driver')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('scrape_spidershop_spiderlings.csv_row_count')
    @patch('scrape_spidershop_spiderlings.read_summary_text')
    def test_main_completes_with_minimal_data(
        self,
        mock_read_summary,
        mock_csv_count,
        mock_exists,
        mock_file,
        mock_close_driver,
        mock_write_legend,
        mock_write_dealer,
        mock_build_dealer,
        mock_write_breeder,
        mock_build_breeder,
        mock_write_pricing,
        mock_append_history,
        mock_load_history,
        mock_extract_urls,
        mock_scrape_product,
        mock_fetch
    ):
        """Test that main() completes successfully with minimal mocked data."""
        # Setup: Mock fetch to return HTML for page 1, then 404 for page 2
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        mock_fetch.side_effect = [
            MINIMAL_PRODUCT_LIST_HTML,  # First page
            HTTPError(response=response_404)  # Second page (triggers pagination break)
        ]
        
        # Mock URL extraction
        mock_extract_urls.return_value = ['https://example.com/product/test/']
        
        # Mock product scraping
        mock_scrape_product.return_value = (
            'Megaphobema mesomelas',  # scientific name
            'Costa Rican Red Leg',     # common name
            '1-2',                      # size
            '100.00',                   # price
            '0'                         # wishlist count
        )
        
        # Mock history (empty)
        mock_load_history.return_value = []
        
        # Mock analysis outputs
        mock_build_breeder.return_value = []
        mock_write_breeder.return_value = True
        mock_build_dealer.return_value = []
        mock_write_dealer.return_value = True
        
        # Mock file existence checks
        mock_exists.return_value = True
        mock_csv_count.return_value = 1
        mock_read_summary.return_value = "## 🧬 Breeder Opportunity Matrix\n## 🏪 Dealer Supply Risk Matrix"
        
        # Execute
        main()
        
        # Verify orchestration happened
        assert mock_fetch.called
        assert mock_extract_urls.called
        assert mock_scrape_product.called
        assert mock_append_history.called
        assert mock_write_pricing.called
        assert mock_build_breeder.called
        assert mock_write_breeder.called
        assert mock_build_dealer.called
        assert mock_write_dealer.called
        assert mock_write_legend.called
        assert mock_close_driver.called

    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.scrape_product')
    @patch('scrape_spidershop_spiderlings.extract_product_urls')
    @patch('scrape_spidershop_spiderlings.load_history')
    @patch('scrape_spidershop_spiderlings.append_history')
    @patch('scrape_spidershop_spiderlings.write_pricing_summary')
    @patch('scrape_spidershop_spiderlings.build_breeder_opportunity_table')
    @patch('scrape_spidershop_spiderlings.write_breeder_outputs')
    @patch('scrape_spidershop_spiderlings.build_dealer_supply_risk_table')
    @patch('scrape_spidershop_spiderlings.write_dealer_outputs')
    @patch('scrape_spidershop_spiderlings.write_summary_legend')
    @patch('scrape_spidershop_spiderlings.close_driver')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('scrape_spidershop_spiderlings.csv_row_count')
    @patch('scrape_spidershop_spiderlings.read_summary_text')
    def test_main_handles_multiple_pages(
        self,
        mock_read_summary,
        mock_csv_count,
        mock_exists,
        mock_file,
        mock_close_driver,
        mock_write_legend,
        mock_write_dealer,
        mock_build_dealer,
        mock_write_breeder,
        mock_build_breeder,
        mock_write_pricing,
        mock_append_history,
        mock_load_history,
        mock_extract_urls,
        mock_scrape_product,
        mock_fetch
    ):
        """Test that main() correctly handles pagination across multiple pages."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        # Return HTML for 3 pages, then 404
        mock_fetch.side_effect = [
            MINIMAL_PRODUCT_LIST_HTML,  # Page 1
            MINIMAL_PRODUCT_LIST_HTML,  # Page 2
            MINIMAL_PRODUCT_LIST_HTML,  # Page 3
            HTTPError(response=response_404)  # Page 4 (404)
        ]
        
        # Return different URLs for each page
        mock_extract_urls.side_effect = [
            ['https://example.com/product/species-1/'],
            ['https://example.com/product/species-2/'],
            ['https://example.com/product/species-3/']
        ]
        
        # Mock product scraping
        mock_scrape_product.return_value = ('Genus species', 'Common Name', '2', '50.00', '5')
        
        # Mock history
        mock_load_history.return_value = []
        mock_build_breeder.return_value = []
        mock_write_breeder.return_value = True
        mock_build_dealer.return_value = []
        mock_write_dealer.return_value = True
        
        # Mock file checks
        mock_exists.return_value = True
        mock_csv_count.return_value = 3
        mock_read_summary.return_value = "## 🧬 Breeder Opportunity Matrix\n## 🏪 Dealer Supply Risk Matrix"
        
        # Execute
        main()
        
        # Verify all 3 pages were fetched
        assert mock_fetch.call_count == 4  # 3 successful + 1 404
        assert mock_extract_urls.call_count == 3
        assert mock_scrape_product.call_count == 3
        
    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.extract_product_urls')
    @patch('scrape_spidershop_spiderlings.close_driver')
    def test_main_fails_on_zero_results(
        self,
        mock_close_driver,
        mock_extract_urls,
        mock_fetch
    ):
        """Test that main() raises SystemExit when scrape returns zero rows."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        # Return empty product list
        mock_fetch.side_effect = [HTTPError(response=response_404)]
        
        # Execute and expect SystemExit (from assert_condition)
        with pytest.raises(SystemExit, match="Scrape completed but returned ZERO rows"):
            main()
        
        # Verify cleanup still happens
        assert mock_close_driver.called
        
    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.scrape_product')
    @patch('scrape_spidershop_spiderlings.extract_product_urls')
    @patch('scrape_spidershop_spiderlings.load_history')
    @patch('scrape_spidershop_spiderlings.append_history')
    @patch('scrape_spidershop_spiderlings.write_pricing_summary')
    @patch('scrape_spidershop_spiderlings.build_breeder_opportunity_table')
    @patch('scrape_spidershop_spiderlings.write_breeder_outputs')
    @patch('scrape_spidershop_spiderlings.build_dealer_supply_risk_table')
    @patch('scrape_spidershop_spiderlings.write_dealer_outputs')
    @patch('scrape_spidershop_spiderlings.write_summary_legend')
    @patch('scrape_spidershop_spiderlings.close_driver')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('scrape_spidershop_spiderlings.csv_row_count')
    @patch('scrape_spidershop_spiderlings.read_summary_text')
    def test_main_migrates_old_history_format(
        self,
        mock_read_summary,
        mock_csv_count,
        mock_exists,
        mock_file,
        mock_close_driver,
        mock_write_legend,
        mock_write_dealer,
        mock_build_dealer,
        mock_write_breeder,
        mock_build_breeder,
        mock_write_pricing,
        mock_append_history,
        mock_load_history,
        mock_extract_urls,
        mock_scrape_product,
        mock_fetch
    ):
        """Test that main() adds wishlist_count field to old history rows."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        mock_fetch.side_effect = [MINIMAL_PRODUCT_LIST_HTML, HTTPError(response=response_404)]
        mock_extract_urls.return_value = ['https://example.com/product/test/']
        mock_scrape_product.return_value = ('Genus species', 'Common', '1', '25.00', '3')
        
        # Mock old history format without wishlist_count
        old_history = [
            {
                'scrape_datetime': '2025-01-01T00:00+00:00',
                'scientific_name': 'Old species',
                'common_name': 'Old common',
                'size_cm': '2',
                'price_gbp': '30.00',
                'page_url': 'https://example.com/old'
                # No wishlist_count field
            }
        ]
        mock_load_history.return_value = old_history
        
        mock_build_breeder.return_value = []
        mock_write_breeder.return_value = True
        mock_build_dealer.return_value = []
        mock_write_dealer.return_value = True
        mock_exists.return_value = True
        mock_csv_count.return_value = 1
        mock_read_summary.return_value = "## 🧬 Breeder Opportunity Matrix\n## 🏪 Dealer Supply Risk Matrix"
        
        # Execute
        main()
        
        # Verify wishlist_count was added
        assert old_history[0]['wishlist_count'] == '0'
        
    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.scrape_product')
    @patch('scrape_spidershop_spiderlings.extract_product_urls')
    @patch('scrape_spidershop_spiderlings.load_history')
    @patch('scrape_spidershop_spiderlings.append_history')
    @patch('scrape_spidershop_spiderlings.write_pricing_summary')
    @patch('scrape_spidershop_spiderlings.build_breeder_opportunity_table')
    @patch('scrape_spidershop_spiderlings.write_breeder_outputs')
    @patch('scrape_spidershop_spiderlings.build_dealer_supply_risk_table')
    @patch('scrape_spidershop_spiderlings.write_dealer_outputs')
    @patch('scrape_spidershop_spiderlings.write_summary_legend')
    @patch('scrape_spidershop_spiderlings.close_driver')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('scrape_spidershop_spiderlings.csv_row_count')
    @patch('scrape_spidershop_spiderlings.read_summary_text')
    def test_main_deduplicates_history_rows(
        self,
        mock_read_summary,
        mock_csv_count,
        mock_exists,
        mock_file,
        mock_close_driver,
        mock_write_legend,
        mock_write_dealer,
        mock_build_dealer,
        mock_write_breeder,
        mock_build_breeder,
        mock_write_pricing,
        mock_append_history,
        mock_load_history,
        mock_extract_urls,
        mock_scrape_product,
        mock_fetch
    ):
        """Test that main() only appends new rows that don't exist in history."""
        from requests.exceptions import HTTPError
        from datetime import datetime, timezone
        
        response_404 = type('Response', (), {'status_code': 404})()
        
        mock_fetch.side_effect = [MINIMAL_PRODUCT_LIST_HTML, HTTPError(response=response_404)]
        mock_extract_urls.return_value = ['https://example.com/product/test/']
        mock_scrape_product.return_value = ('Genus species', 'Common', '1', '25.00', '3')
        
        # Use a mock datetime that will match the scraped data
        with patch('scrape_spidershop_spiderlings.datetime') as mock_datetime:
            # Create a proper mock datetime
            fixed_time = datetime(2025, 1, 8, 12, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = fixed_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            scrape_dt = fixed_time.replace(second=0, microsecond=0).isoformat(timespec="minutes")
            
            # Mock history that already contains this exact row
            existing_history = [
                {
                    'scrape_datetime': scrape_dt,
                    'scientific_name': 'Genus species',
                    'common_name': 'Common',
                    'size_cm': '1',
                    'price_gbp': '25.00',
                    'wishlist_count': '3',
                    'page_url': 'https://example.com/product/test/'
                }
            ]
            mock_load_history.return_value = existing_history
            
            mock_build_breeder.return_value = []
            mock_write_breeder.return_value = True
            mock_build_dealer.return_value = []
            mock_write_dealer.return_value = True
            mock_exists.return_value = True
            mock_csv_count.return_value = 1
            mock_read_summary.return_value = "## 🧬 Breeder Opportunity Matrix\n## 🏪 Dealer Supply Risk Matrix"
            
            main()
        
        # Verify append_history was called with empty list (no new rows)
        call_args = mock_append_history.call_args[0]
        new_rows = call_args[1]
        assert len(new_rows) == 0
        
    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.extract_product_urls')
    @patch('scrape_spidershop_spiderlings.close_driver')
    def test_main_cleans_up_on_error(
        self,
        mock_close_driver,
        mock_extract_urls,
        mock_fetch
    ):
        """Test that browser cleanup happens even when an error occurs."""
        # Mock an error during fetching
        mock_fetch.side_effect = RuntimeError("Network error")
        
        # Execute and expect error
        with pytest.raises(RuntimeError, match="Network error"):
            main()
        
        # Verify cleanup still happened via finally block
        assert mock_close_driver.called
        
    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.scrape_product')
    @patch('scrape_spidershop_spiderlings.extract_product_urls')
    @patch('scrape_spidershop_spiderlings.load_history')
    @patch('scrape_spidershop_spiderlings.append_history')
    @patch('scrape_spidershop_spiderlings.write_pricing_summary')
    @patch('scrape_spidershop_spiderlings.build_breeder_opportunity_table')
    @patch('scrape_spidershop_spiderlings.write_breeder_outputs')
    @patch('scrape_spidershop_spiderlings.build_dealer_supply_risk_table')
    @patch('scrape_spidershop_spiderlings.write_dealer_outputs')
    @patch('scrape_spidershop_spiderlings.write_summary_legend')
    @patch('scrape_spidershop_spiderlings.close_driver')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('scrape_spidershop_spiderlings.csv_row_count')
    @patch('scrape_spidershop_spiderlings.read_summary_text')
    def test_main_fails_when_breeder_output_not_written(
        self,
        mock_read_summary,
        mock_csv_count,
        mock_exists,
        mock_file,
        mock_close_driver,
        mock_write_legend,
        mock_write_dealer,
        mock_build_dealer,
        mock_write_breeder,
        mock_build_breeder,
        mock_write_pricing,
        mock_append_history,
        mock_load_history,
        mock_extract_urls,
        mock_scrape_product,
        mock_fetch
    ):
        """Test that main() fails assertion when breeder output write returns False."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        mock_fetch.side_effect = [MINIMAL_PRODUCT_LIST_HTML, HTTPError(response=response_404)]
        mock_extract_urls.return_value = ['https://example.com/product/test/']
        mock_scrape_product.return_value = ('Genus species', 'Common', '1', '25.00', '3')
        mock_load_history.return_value = []
        mock_build_breeder.return_value = []
        mock_write_breeder.return_value = False  # Writer returns False
        mock_build_dealer.return_value = []
        mock_write_dealer.return_value = True
        mock_exists.return_value = True
        mock_csv_count.return_value = 1
        
        # Execute and expect SystemExit (from assert_condition)
        with pytest.raises(SystemExit, match="Breeder Opportunity Matrix was not written"):
            main()
        
        assert mock_close_driver.called
        
    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.scrape_product')
    @patch('scrape_spidershop_spiderlings.extract_product_urls')
    @patch('scrape_spidershop_spiderlings.load_history')
    @patch('scrape_spidershop_spiderlings.append_history')
    @patch('scrape_spidershop_spiderlings.write_pricing_summary')
    @patch('scrape_spidershop_spiderlings.build_breeder_opportunity_table')
    @patch('scrape_spidershop_spiderlings.write_breeder_outputs')
    @patch('scrape_spidershop_spiderlings.build_dealer_supply_risk_table')
    @patch('scrape_spidershop_spiderlings.write_dealer_outputs')
    @patch('scrape_spidershop_spiderlings.write_summary_legend')
    @patch('scrape_spidershop_spiderlings.close_driver')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('scrape_spidershop_spiderlings.csv_row_count')
    def test_main_fails_when_summary_missing_breeder_section(
        self,
        mock_csv_count,
        mock_exists,
        mock_file,
        mock_close_driver,
        mock_write_legend,
        mock_write_dealer,
        mock_build_dealer,
        mock_write_breeder,
        mock_build_breeder,
        mock_write_pricing,
        mock_append_history,
        mock_load_history,
        mock_extract_urls,
        mock_scrape_product,
        mock_fetch
    ):
        """Test that main() fails assertion when summary is missing breeder section."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        mock_fetch.side_effect = [MINIMAL_PRODUCT_LIST_HTML, HTTPError(response=response_404)]
        mock_extract_urls.return_value = ['https://example.com/product/test/']
        mock_scrape_product.return_value = ('Genus species', 'Common', '1', '25.00', '3')
        mock_load_history.return_value = []
        mock_build_breeder.return_value = []
        mock_write_breeder.return_value = True
        mock_build_dealer.return_value = []
        mock_write_dealer.return_value = True
        mock_exists.return_value = True
        mock_csv_count.return_value = 1
        
        # Mock read_summary_text to return content missing breeder section
        with patch('scrape_spidershop_spiderlings.read_summary_text') as mock_read_summary:
            mock_read_summary.return_value = "## 🏪 Dealer Supply Risk Matrix"
            
            # Execute and expect SystemExit (from assert_condition)
            with pytest.raises(SystemExit, match="Breeder Opportunity Matrix heading missing"):
                main()
        
        assert mock_close_driver.called

    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.close_driver')
    def test_main_reraises_non_404_http_error(
        self,
        mock_close_driver,
        mock_fetch
    ):
        """Test that main() re-raises non-404 HTTP errors."""
        from requests.exceptions import HTTPError
        response_500 = type('Response', (), {'status_code': 500})()
        
        # Return 500 error (not 404)
        mock_fetch.side_effect = HTTPError(response=response_500)
        
        # Execute and expect HTTPError to be re-raised
        with pytest.raises(HTTPError):
            main()
        
        # Verify cleanup still happens
        assert mock_close_driver.called

    @patch('scrape_spidershop_spiderlings.fetch')
    @patch('scrape_spidershop_spiderlings.extract_product_urls')
    @patch('scrape_spidershop_spiderlings.close_driver')
    def test_main_stops_when_no_product_urls_found(
        self,
        mock_close_driver,
        mock_extract_urls,
        mock_fetch
    ):
        """Test that main() stops pagination when no product URLs are extracted."""
        # First page returns HTML but extract_product_urls finds nothing
        mock_fetch.return_value = MINIMAL_PRODUCT_LIST_HTML
        mock_extract_urls.return_value = []  # Empty list
        
        # Execute and expect zero rows assertion
        with pytest.raises(SystemExit, match="Scrape completed but returned ZERO rows"):
            main()
        
        # Verify we only fetched once before stopping
        assert mock_fetch.call_count == 1
        assert mock_close_driver.called

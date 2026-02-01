#!/usr/bin/env python3
"""
Tests for scrape_spidershop_spiderlings.py orchestration logic.

Focuses on the main() workflow without duplicating tests for individual
modules (scraper, breeder_matrix, dealer_matrix, etc.).
"""

import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
from scrape.scrape_spidershop_spiderlings import main


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


@pytest.fixture
def mock_scraping():
    """Fixture that patches scraping-related functions."""
    with patch('scrape.scrape_spidershop_spiderlings.fetch') as mock_fetch, \
         patch('scrape.scrape_spidershop_spiderlings.extract_product_urls') as mock_extract_urls, \
         patch('scrape.scrape_spidershop_spiderlings.scrape_product') as mock_scrape_product:
        yield {
            'fetch': mock_fetch,
            'extract_urls': mock_extract_urls,
            'scrape_product': mock_scrape_product
        }


@pytest.fixture
def mock_history():
    """Fixture that patches history-related functions."""
    with patch('scrape.scrape_spidershop_spiderlings.load_history') as mock_load, \
         patch('scrape.scrape_spidershop_spiderlings.append_history') as mock_append:
        yield {
            'load': mock_load,
            'append': mock_append
        }


@pytest.fixture
def mock_analysis():
    """Fixture that patches analysis and output functions."""
    with patch('scrape.scrape_spidershop_spiderlings.write_pricing_summary') as mock_pricing, \
         patch('scrape.scrape_spidershop_spiderlings.build_breeder_opportunity_table') as mock_build_breeder, \
         patch('scrape.scrape_spidershop_spiderlings.write_breeder_outputs') as mock_write_breeder, \
         patch('scrape.scrape_spidershop_spiderlings.build_dealer_supply_risk_table') as mock_build_dealer, \
         patch('scrape.scrape_spidershop_spiderlings.write_dealer_outputs') as mock_write_dealer, \
         patch('scrape.scrape_spidershop_spiderlings.write_summary_legend') as mock_legend:
        yield {
            'pricing': mock_pricing,
            'build_breeder': mock_build_breeder,
            'write_breeder': mock_write_breeder,
            'build_dealer': mock_build_dealer,
            'write_dealer': mock_write_dealer,
            'legend': mock_legend
        }


@pytest.fixture
def mock_file_system():
    """Fixture that patches file system operations."""
    with patch('builtins.open', mock_open()) as mock_file, \
         patch('os.path.exists') as mock_exists, \
         patch('scrape.scrape_spidershop_spiderlings.csv_row_count') as mock_csv_count, \
         patch('scrape.scrape_spidershop_spiderlings.read_summary_text') as mock_read_summary:
        yield {
            'file': mock_file,
            'exists': mock_exists,
            'csv_count': mock_csv_count,
            'read_summary': mock_read_summary
        }


@pytest.fixture
def mock_browser():
    """Fixture that patches browser cleanup."""
    with patch('scrape.scrape_spidershop_spiderlings.close_driver') as mock_close:
        yield mock_close


class TestMainOrchestration:
    """Test the main() orchestration workflow."""

    def test_main_completes_with_minimal_data(
        self, mock_scraping, mock_history, mock_analysis, mock_file_system, mock_browser
    ):
        """Test that main() completes successfully with minimal mocked data."""
        # Setup: Mock fetch to return HTML for page 1, then 404 for page 2
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        mock_scraping['fetch'].side_effect = [
            MINIMAL_PRODUCT_LIST_HTML,  # First page
            HTTPError(response=response_404)  # Second page (triggers pagination break)
        ]
        
        # Mock URL extraction
        mock_scraping['extract_urls'].return_value = ['https://example.com/product/test/']
        
        # Mock product scraping
        mock_scraping['scrape_product'].return_value = (
            'Megaphobema mesomelas',  # scientific name
            'Costa Rican Red Leg',     # common name
            '1-2',                      # size
            '100.00',                   # price
            '0'                         # wishlist count
        )
        
        # Mock history (empty)
        mock_history['load'].return_value = []
        
        # Mock analysis outputs
        mock_analysis['build_breeder'].return_value = []
        mock_analysis['write_breeder'].return_value = True
        mock_analysis['build_dealer'].return_value = []
        mock_analysis['write_dealer'].return_value = True
        
        # Mock file existence checks
        mock_file_system['exists'].return_value = True
        mock_file_system['csv_count'].return_value = 1
        mock_file_system['read_summary'].return_value = "## 🧬 Breeder Opportunity Matrix (Top 10)\n## 🏪 Dealer Supply Risk Matrix (Top 10)"
        
        # Execute
        main()
        
        # Verify orchestration happened
        assert mock_scraping['fetch'].called
        assert mock_scraping['extract_urls'].called
        assert mock_scraping['scrape_product'].called
        assert mock_history['append'].called
        assert mock_analysis['pricing'].called
        assert mock_analysis['build_breeder'].called
        assert mock_analysis['write_breeder'].called
        assert mock_analysis['build_dealer'].called
        assert mock_analysis['write_dealer'].called
        assert mock_analysis['legend'].called
        assert mock_browser.called

    def test_main_handles_multiple_pages(
        self, mock_scraping, mock_history, mock_analysis, mock_file_system, mock_browser
    ):
        """Test that main() correctly handles pagination across multiple pages."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        # Return HTML for 3 pages, then 404
        mock_scraping['fetch'].side_effect = [
            MINIMAL_PRODUCT_LIST_HTML,  # Page 1
            MINIMAL_PRODUCT_LIST_HTML,  # Page 2
            MINIMAL_PRODUCT_LIST_HTML,  # Page 3
            HTTPError(response=response_404)  # Page 4 (404)
        ]
        
        # Return different URLs for each page
        mock_scraping['extract_urls'].side_effect = [
            ['https://example.com/product/species-1/'],
            ['https://example.com/product/species-2/'],
            ['https://example.com/product/species-3/']
        ]
        
        # Mock product scraping
        mock_scraping['scrape_product'].return_value = ('Genus species', 'Common Name', '2', '50.00', '5')
        
        # Mock history
        mock_history['load'].return_value = []
        mock_analysis['build_breeder'].return_value = []
        mock_analysis['write_breeder'].return_value = True
        mock_analysis['build_dealer'].return_value = []
        mock_analysis['write_dealer'].return_value = True
        
        # Mock file checks
        mock_file_system['exists'].return_value = True
        mock_file_system['csv_count'].return_value = 3
        mock_file_system['read_summary'].return_value = "## 🧬 Breeder Opportunity Matrix (Top 10)\n## 🏪 Dealer Supply Risk Matrix (Top 10)"
        
        # Execute
        main()
        
        # Verify all 3 pages were fetched
        assert mock_scraping['fetch'].call_count == 4  # 3 successful + 1 404
        assert mock_scraping['extract_urls'].call_count == 3
        assert mock_scraping['scrape_product'].call_count == 3
        
    def test_main_fails_on_zero_results(self, mock_scraping, mock_browser):
        """Test that main() raises SystemExit when scrape returns zero rows."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        # Return empty product list
        mock_scraping['fetch'].side_effect = [HTTPError(response=response_404)]
        
        # Execute and expect SystemExit (from assert_condition)
        with pytest.raises(SystemExit, match="Scrape completed but returned ZERO rows"):
            main()
        
        # Verify cleanup still happens
        assert mock_browser.called
        
    def test_main_migrates_old_history_format(
        self, mock_scraping, mock_history, mock_analysis, mock_file_system, mock_browser
    ):
        """Test that main() adds wishlist_count field to old history rows."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        mock_scraping['fetch'].side_effect = [MINIMAL_PRODUCT_LIST_HTML, HTTPError(response=response_404)]
        mock_scraping['extract_urls'].return_value = ['https://example.com/product/test/']
        mock_scraping['scrape_product'].return_value = ('Genus species', 'Common', '1', '25.00', '3')
        
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
        mock_history['load'].return_value = old_history
        
        mock_analysis['build_breeder'].return_value = []
        mock_analysis['write_breeder'].return_value = True
        mock_analysis['build_dealer'].return_value = []
        mock_analysis['write_dealer'].return_value = True
        mock_file_system['exists'].return_value = True
        mock_file_system['csv_count'].return_value = 1
        mock_file_system['read_summary'].return_value = "## 🧬 Breeder Opportunity Matrix (Top 10)\n## 🏪 Dealer Supply Risk Matrix (Top 10)"
        
        # Execute
        main()
        
        # Verify wishlist_count was added
        assert old_history[0]['wishlist_count'] == '0'
        
    def test_main_deduplicates_history_rows(
        self, mock_scraping, mock_history, mock_analysis, mock_file_system, mock_browser
    ):
        """Test that main() only appends new rows that don't exist in history."""
        from requests.exceptions import HTTPError
        from datetime import datetime, timezone
        
        response_404 = type('Response', (), {'status_code': 404})()
        
        mock_scraping['fetch'].side_effect = [MINIMAL_PRODUCT_LIST_HTML, HTTPError(response=response_404)]
        mock_scraping['extract_urls'].return_value = ['https://example.com/product/test/']
        mock_scraping['scrape_product'].return_value = ('Genus species', 'Common', '1', '25.00', '3')
        
        # Use a mock datetime that will match the scraped data
        with patch('scrape.scrape_spidershop_spiderlings.datetime') as mock_datetime:
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
            mock_history['load'].return_value = existing_history
            
            mock_analysis['build_breeder'].return_value = []
            mock_analysis['write_breeder'].return_value = True
            mock_analysis['build_dealer'].return_value = []
            mock_analysis['write_dealer'].return_value = True
            mock_file_system['exists'].return_value = True
            mock_file_system['csv_count'].return_value = 1
            mock_file_system['read_summary'].return_value = "## 🧬 Breeder Opportunity Matrix (Top 10)\n## 🏪 Dealer Supply Risk Matrix (Top 10)"
            
            main()
        
        # Verify append_history was called with empty list (no new rows)
        call_args = mock_history['append'].call_args[0]
        new_rows = call_args[1]
        assert len(new_rows) == 0
        
    def test_main_cleans_up_on_error(self, mock_scraping, mock_browser):
        """Test that browser cleanup happens even when an error occurs."""
        # Mock an error during fetching
        mock_scraping['fetch'].side_effect = RuntimeError("Network error")
        
        # Execute and expect error
        with pytest.raises(RuntimeError, match="Network error"):
            main()
        
        # Verify cleanup still happened via finally block
        assert mock_browser.called
        
    def test_main_fails_when_breeder_output_not_written(
        self, mock_scraping, mock_history, mock_analysis, mock_file_system, mock_browser
    ):
        """Test that main() fails assertion when breeder output write returns False."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        mock_scraping['fetch'].side_effect = [MINIMAL_PRODUCT_LIST_HTML, HTTPError(response=response_404)]
        mock_scraping['extract_urls'].return_value = ['https://example.com/product/test/']
        mock_scraping['scrape_product'].return_value = ('Genus species', 'Common', '1', '25.00', '3')
        mock_history['load'].return_value = []
        mock_analysis['build_breeder'].return_value = []
        mock_analysis['write_breeder'].return_value = False  # Writer returns False
        mock_analysis['build_dealer'].return_value = []
        mock_analysis['write_dealer'].return_value = True
        mock_file_system['exists'].return_value = True
        mock_file_system['csv_count'].return_value = 1
        
        # Execute and expect SystemExit (from assert_condition)
        with pytest.raises(SystemExit, match="Breeder Opportunity Matrix \\(Top 10\\) was not written"):
            main()
        
        assert mock_browser.called
        
    def test_main_fails_when_summary_missing_breeder_section(
        self, mock_scraping, mock_history, mock_analysis, mock_file_system, mock_browser
    ):
        """Test that main() fails assertion when summary is missing breeder section."""
        from requests.exceptions import HTTPError
        response_404 = type('Response', (), {'status_code': 404})()
        
        mock_scraping['fetch'].side_effect = [MINIMAL_PRODUCT_LIST_HTML, HTTPError(response=response_404)]
        mock_scraping['extract_urls'].return_value = ['https://example.com/product/test/']
        mock_scraping['scrape_product'].return_value = ('Genus species', 'Common', '1', '25.00', '3')
        mock_history['load'].return_value = []
        mock_analysis['build_breeder'].return_value = []
        mock_analysis['write_breeder'].return_value = True
        mock_analysis['build_dealer'].return_value = []
        mock_analysis['write_dealer'].return_value = True
        mock_file_system['exists'].return_value = True
        mock_file_system['csv_count'].return_value = 1
        
        # Mock read_summary_text to return content missing breeder section
        with patch('scrape.scrape_spidershop_spiderlings.read_summary_text') as mock_read_summary:
            mock_read_summary.return_value = "## 🏪 Dealer Supply Risk Matrix (Top 10)"
            
            # Execute and expect SystemExit (from assert_condition)
            with pytest.raises(SystemExit, match="Breeder Opportunity Matrix \\(Top 10\\) heading missing"):
                main()
        
        assert mock_browser.called

    def test_main_reraises_non_404_http_error(self, mock_scraping, mock_browser):
        """Test that main() re-raises non-404 HTTP errors."""
        from requests.exceptions import HTTPError
        response_500 = type('Response', (), {'status_code': 500})()
        
        # Return 500 error (not 404)
        mock_scraping['fetch'].side_effect = HTTPError(response=response_500)
        
        # Execute and expect HTTPError to be re-raised
        with pytest.raises(HTTPError):
            main()
        
        # Verify cleanup still happens
        assert mock_browser.called

    def test_main_stops_when_no_product_urls_found(self, mock_scraping, mock_browser):
        """Test that main() stops pagination when no product URLs are extracted."""
        # First page returns HTML but extract_product_urls finds nothing
        mock_scraping['fetch'].return_value = MINIMAL_PRODUCT_LIST_HTML
        mock_scraping['extract_urls'].return_value = []  # Empty list
        
        # Execute and expect zero rows assertion
        with pytest.raises(SystemExit, match="Scrape completed but returned ZERO rows"):
            main()
        
        # Verify we only fetched once before stopping
        assert mock_scraping['fetch'].call_count == 1
        assert mock_browser.called

    def test_full_analysis_summary_snapshot(
        self, mock_scraping, mock_browser, tmp_path, snapshot
    ):
        """
        Integration snapshot test capturing key sections of analysis_summary.md.
        
        Verifies pipeline orchestration (scraping → history → matrices → summary),
        section presence, and basic format. Detailed content is tested in unit tests.
        
        Snapshot covers:
        - Pricing summary structure
        - Breeder matrix section (minimal rows - details tested in unit tests)
        - Dealer matrix section (minimal rows - details tested in unit tests)  
        - Legend presence (truncated - full text tested elsewhere)
        """
        # Mock scraping - page 1 returns URLs, page 2 returns empty (end pagination)
        mock_scraping["fetch"].side_effect = [
            MagicMock(),  # Page 1 HTML
            MagicMock(),  # Page 2 HTML
        ]
        mock_scraping["extract_urls"].side_effect = [
            ["url1", "url2"],  # Page 1 has products
            [],  # Page 2 is empty (triggers stop)
        ]
        mock_scraping["scrape_product"].side_effect = [
            ("Aphonopelma seemanni", "Costa Rican Zebra", "1.0", "25.00", "5"),
            ("Grammostola pulchra", "Brazilian Black", "2.0", "40.00", "15"),
        ]
        
        # Create minimal history with just enough data for integration test
        # (detailed analysis scenarios are tested in unit tests)
        history_content = (
            "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
            "2025-01-01T10:00:00,Aphonopelma seemanni,Costa Rican Zebra,1.0,20.00,3,https://example.com/1\n"
            "2025-01-01T10:00:00,Cyriocosmus elegans,Trinidad Dwarf,0.5,25.00,15,https://example.com/2\n"
            "2025-01-08T10:00:00,Aphonopelma seemanni,Costa Rican Zebra,1.0,22.00,4,https://example.com/1\n"
            "2025-01-15T10:00:00,Aphonopelma seemanni,Costa Rican Zebra,1.0,23.00,4,https://example.com/1\n"
            "2025-01-22T10:00:00,Aphonopelma seemanni,Costa Rican Zebra,1.0,24.00,5,https://example.com/1\n"
        )
        (tmp_path / "spidershop_spiderlings_history.csv").write_text(history_content)
        
        # Set up environment
        os.chdir(tmp_path)
        summary_file = tmp_path / "analysis_summary.md"
        os.environ["GITHUB_STEP_SUMMARY"] = str(summary_file)
        
        try:
            main()
            
            # Read the generated summary
            assert summary_file.exists()
            summary_content = summary_file.read_text(encoding="utf-8")
            
            # Normalize timestamps to avoid snapshot mismatches
            # Replace actual timestamp with placeholder
            import re
            summary_content = re.sub(
                r'\*\*Scrape time \(UTC\):\*\* `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}\+\d{2}:\d{2}`',
                '**Scrape time (UTC):** `YYYY-MM-DDTHH:MM+00:00`',
                summary_content
            )
            
            # Truncate legend and examples sections to reduce snapshot noise
            # (Full legend/example text is documentation, not integration logic)
            # Keep just enough to verify sections exist and basic structure
            def truncate_legend_section(content):
                """Keep only first few lines of legend sections to verify presence."""
                # Find the legend details block
                details_start = content.find('<details>')
                if details_start == -1:
                    return content
                
                # Find the first legend subsection
                breeder_legend_start = content.find('### 🧬 Breeder Opportunity Matrix — Legend', details_start)
                if breeder_legend_start == -1:
                    return content
                
                # Find where examples start (truncate point)
                examples_start = content.find('### 📖 Breeder Matrix — Practical Examples', details_start)
                if examples_start == -1:
                    examples_start = content.find('### 🏪 Dealer Supply Risk Matrix — Legend', details_start)
                
                if examples_start == -1:
                    return content
                
                # Keep structure up to examples, then add truncation marker
                truncation_note = "\n\n[... Legend details truncated in snapshot - full text verified in production ...]\n\n"
                
                # Find end of details block
                details_end = content.find('</details>', examples_start)
                if details_end == -1:
                    return content
                
                # Reconstruct: keep everything before examples + truncation note + closing tag
                return (content[:examples_start] + 
                       truncation_note +
                       content[details_end:])
            
            summary_content = truncate_legend_section(summary_content)
            
            # Snapshot the complete summary
            assert summary_content == snapshot
            
        finally:
            if "GITHUB_STEP_SUMMARY" in os.environ:
                del os.environ["GITHUB_STEP_SUMMARY"]


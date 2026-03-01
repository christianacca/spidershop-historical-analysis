#!/usr/bin/env python3
"""Integration tests for website generation."""
import pytest
import tempfile
import os
from pathlib import Path
from bs4 import BeautifulSoup
from conftest import create_temp_csv_file, temp_csv_file, BreederEntry, create_breeder_csv_content, page_config
from website import generate_table_html, get_base_html_template, get_html_footer
from website.generate_website import generate_homepage, generate_analysis_page, generate_snapshot_page, generate_history_page, main, OUTPUT_DIR


class TestIntegration:
    """Integration tests for the website generation workflow."""

    def test_website_splits_analysis_into_separate_pages(self):
        """Should split analysis_summary.md into separate breeder and dealer pages with converted HTML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            
            try:
                os.chdir(tmpdir)
                
                # Create minimal CSV files
                with open("spidershop_spiderlings_scrape.csv", "w", encoding="utf-8") as f:
                    f.write("scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n")
                    f.write("2025-01-01,Test Species,Test,1.0,25.00,5,https://example.com\n")
                
                with open("spidershop_spiderlings_history.csv", "w", encoding="utf-8") as f:
                    f.write("scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n")
                
                with open("breeder_opportunity_table.csv", "w", encoding="utf-8") as f:
                    f.write("Species,Size (cm),Signal\n")
                    for i in range(15):
                        f.write(f"Test Species {i},1,🔥\n")
                
                with open("dealer_supply_risk_table.csv", "w", encoding="utf-8") as f:
                    f.write("Species,Size (cm),Dealer Risk\n")
                    for i in range(12):
                        f.write(f"Test Species {i},1,⚠️\n")
                
                # Create analysis_summary.md with markdown inside details blocks
                with open("analysis_summary.md", "w", encoding="utf-8") as f:
                    f.write("""## 🧬 Breeder Opportunity Matrix (Top 10)

**Summary:** 109 species analyzed | 🔥 Hot: 36 | ⚠️ Watch: 30 | ❌ Avoid: 43

Breeder content here.

## 🏪 Dealer Supply Risk Matrix (Top 10)

**Summary:** 109 species analyzed | 🔥 High Risk: 35 | ⚠️ Moderate Risk: 57 | ❌ Low Risk: 17

Dealer content here.

<details markdown="1">
<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>

### 🧬 Breeder Opportunity Matrix — Legend

**OOS**

- `IN` — Species is currently listed
- `OUT` — Species is not listed

### 📖 Breeder Matrix — Practical Examples

Example content for breeders.

### 🏪 Dealer Supply Risk Matrix — Legend

**Stock Reliability**

- `High` — Listed in most runs
- `Low` — Rarely listed

### 📖 Dealer Matrix — Practical Examples

Example content for dealers.

</details>""")
                
                # Run main function
                main()
                
                # Verify breeder.html was created
                breeder_html_path = OUTPUT_DIR / "breeder.html"
                assert breeder_html_path.exists(), "breeder.html should be created"
                
                with open(breeder_html_path, "r", encoding="utf-8") as f:
                    breeder_html = f.read()
                
                # Top 10 filter button should be rendered from CSV (not markdown)
                assert "<table" in breeder_html, "Should have table rendered from CSV"
                assert 'data-limit="10"' in breeder_html, "Should have 🔥 Hot (top 10) filter button"
                
                # Summary stats should be extracted and rendered as cards
                assert "109 species analyzed" in breeder_html or "Species Analyzed" in breeder_html
                
                # Verify legend markdown was converted to HTML (not left as markdown)
                assert "<h4>🧬 Breeder Opportunity Matrix — Legend</h4>" in breeder_html
                assert "<ul>" in breeder_html
                assert "<li><code>IN</code>" in breeder_html
                
                # Verify examples were converted
                assert "<h4>📖 Breeder Matrix — Practical Examples</h4>" in breeder_html
                assert "Example content for breeders" in breeder_html
                
                # Verify NO markdown syntax remains
                assert "### 🧬 Breeder" not in breeder_html
                assert "- `IN`" not in breeder_html
                
                # Verify dealer.html was created and contains converted HTML
                dealer_html_path = OUTPUT_DIR / "dealer.html"
                assert dealer_html_path.exists(), "dealer.html should be created"
                
                with open(dealer_html_path, "r", encoding="utf-8") as f:
                    dealer_html = f.read()
                
                # Top 10 filter button should be rendered from CSV
                assert "<table" in dealer_html
                assert 'data-limit="10"' in dealer_html, "Should have 🔥 Hot (top 10) filter button"
                
                # Verify legend/examples were converted to HTML
                assert "<h4>" in dealer_html  # Some heading converted
                assert "Example content for dealers" in dealer_html
                assert "Example content for dealers" in dealer_html
                
                # Verify NO markdown syntax remains
                assert "### 🏪 Dealer" not in dealer_html
                assert "- `High`" not in dealer_html
                
            finally:
                os.chdir(original_dir)

    def test_full_page_generation_with_all_features(self):
        """Should generate complete page with all features enabled."""
        entries = [BreederEntry(species=f"Species {i}", size_cm="1.0", signal="🔥") for i in range(15)]
        csv_content = create_breeder_csv_content(entries)
        
        with temp_csv_file(csv_content) as csv_file:
            # Summary line for stats extraction
            analysis_md = "**Summary:** 15 species analyzed | 🔥 Hot: 15 | ⚠️ Watch: 0 | ❌ Avoid: 0"
            legend_md = "**Symbol**: Meaning of symbol."
            
            config = page_config.breeder(csv_file, analysis_md).with_title("Test Page").with_description("Description here").with_legend(legend_md).with_search(True).build()
            html = generate_analysis_page(config)
            
            # Verify all components present
            assert "<!DOCTYPE html>" in html
            assert "Test Page" in html
            assert "Description here" in html
            assert "Download CSV" in html
            assert "Search:" in html
            assert "Species 0" in html or "Species 1" in html
            assert 'data-limit="10"' in html, "Should have 🔥 Hot (top 10) filter button"
            assert "<table" in html, "Should have table"
            assert 'id="legend-section"' in html, "Legend <details> should have id='legend-section'"
            assert "Symbol" in html
            assert "</html>" in html

    def test_handles_empty_csv_gracefully(self):
        """Should handle empty CSV file without errors."""
        with temp_csv_file("") as csv_file:
            config = page_config.snapshot(csv_file).build()
            html = generate_snapshot_page(config)
            assert "No data available" in html
            assert "<!DOCTYPE html>" in html
            assert "</html>" in html

    def test_html_escaping_prevents_injection(self):
        """Page title is HTML-escaped; CSV cell data is safely JSON-encoded in the payload."""
        # Deliberately malicious input to test escaping
        csv_content = 'Name,Script\n<script>alert("xss")</script>,<img src=x onerror=alert(1)>\n'
        
        with temp_csv_file(csv_content) as csv_file:
            config = page_config.custom(
                title="<script>bad</script>",
                csv_filename=csv_file,
                active_page="snapshot",
                description="<b>Description</b>"
            ).build()
            html = generate_snapshot_page(config)
            # Page title goes through Jinja2 HTML autoescape
            assert "&lt;script&gt;" in html
            # Raw script tag from CSV data must not appear outside the JSON block
            assert "<script>alert" not in html
            # CSV data is JSON-encoded with \\uXXXX escapes (not HTML entity escapes)
            assert '\\u003cimg' in html, "< in CSV data should be JSON-encoded as \\u003c"

    def test_main_function_generates_website(self):
        """Should execute main() function and generate website files."""
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            
            try:
                # Change to temp directory
                os.chdir(tmpdir)
                
                # Create minimal test CSV files
                with open("spidershop_spiderlings_scrape.csv", "w", encoding="utf-8") as f:
                    f.write("scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n")
                    f.write("2025-01-01,Aphonopelma seemanni,Test Spider,1.0,25.00,5,https://example.com\n")
                
                with open("spidershop_spiderlings_history.csv", "w", encoding="utf-8") as f:
                    f.write("scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n")
                    f.write("2025-01-01,Aphonopelma seemanni,Test Spider,1.0,25.00,5,https://example.com\n")
                
                with open("breeder_opportunity_table.csv", "w", encoding="utf-8") as f:
                    f.write("Species,Signal\n")
                    f.write("Aphonopelma seemanni,🔥\n")
                
                with open("dealer_supply_risk_table.csv", "w", encoding="utf-8") as f:
                    f.write("Species,Risk\n")
                    f.write("Aphonopelma seemanni,Low\n")
                
                with open("analysis_summary.md", "w", encoding="utf-8") as f:
                    f.write("## 🧬 Breeder Opportunity Matrix (Top 10)\n\nBreeder content\n\n")
                    f.write("## 🏪 Dealer Supply Risk Matrix (Top 10)\n\nDealer content\n\n")
                    f.write("<details><summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>\n")
                    f.write("### 🧬 Breeder Opportunity Matrix — Legend\nLegend content\n")
                    f.write("### 📖 Breeder Matrix — Practical Examples\nExample content\n")
                    f.write("### 🏪 Dealer Supply Risk Matrix — Legend\nLegend content\n")
                    f.write("### 📖 Dealer Matrix — Practical Examples\nExample content\n</details>")
                
                # Run main function
                main()
                
                # Verify output directory and files were created
                assert OUTPUT_DIR.exists()
                assert (OUTPUT_DIR / "index.html").exists()
                assert (OUTPUT_DIR / "snapshot.html").exists()
                assert (OUTPUT_DIR / "history.html").exists()
                assert (OUTPUT_DIR / "breeder.html").exists()
                assert (OUTPUT_DIR / "dealer.html").exists()
                
                # Verify species-detail.css was copied
                css_path = OUTPUT_DIR / "species-detail.css"
                assert css_path.exists(), "species-detail.css should be copied to output directory"
                
                # Verify CSS file contains expected styles
                with open(css_path, "r", encoding="utf-8") as f:
                    css_content = f.read()
                assert ".breadcrumbs" in css_content
                assert ".badge" in css_content
                assert ".segment" in css_content
                
                # Verify species pages link to CSS with correct relative path
                species_pages = list((OUTPUT_DIR / "species").glob("*.html"))
                if species_pages:  # Only check if species pages were generated
                    with open(species_pages[0], "r", encoding="utf-8") as f:
                        html_content = f.read()
                    assert '../species-detail.css' in html_content, \
                        "Species pages should link to CSS with relative path ../species-detail.css"
                
                # Verify CSV files were copied
                assert (OUTPUT_DIR / "spidershop_spiderlings_scrape.csv").exists()
                assert (OUTPUT_DIR / "spidershop_spiderlings_history.csv").exists()
                assert (OUTPUT_DIR / "breeder_opportunity_table.csv").exists()
                assert (OUTPUT_DIR / "dealer_supply_risk_table.csv").exists()
                
                # Verify HTML content
                with open(OUTPUT_DIR / "index.html", "r", encoding="utf-8") as f:
                    index_html = f.read()
                    assert "Spider Shop Historical Analysis" in index_html
                    assert "2025-01-01" in index_html  # Last scrape time
                
                with open(OUTPUT_DIR / "breeder.html", "r", encoding="utf-8") as f:
                    breeder_html = f.read()
                    assert "<table" in breeder_html, "Should have table rendered from CSV"
                    assert 'data-limit="10"' in breeder_html or "109 species" in breeder_html

                # Verify page headings include the icons matching the homepage cards
                expected_headings = {
                    "snapshot.html": "📸 Latest Snapshot",
                    "history.html": "📊 Historical Data",
                    "breeder.html": "🌱 Breeder Opportunities",
                    "dealer.html": "📦 Dealer Supply Risk",
                }
                for filename, expected_heading in expected_headings.items():
                    with open(OUTPUT_DIR / filename, "r", encoding="utf-8") as f:
                        page_html = f.read()
                    soup = BeautifulSoup(page_html, "html.parser")
                    h2 = soup.find("h2")
                    assert h2 is not None, f"{filename} should have an <h2> heading"
                    assert h2.get_text(strip=True) == expected_heading, (
                        f"{filename} <h2> should be '{expected_heading}', got '{h2.get_text(strip=True)}'"
                    )

            finally:
                # Restore original directory
                os.chdir(original_dir)


class TestHtmlSnapshots:
    """Focused HTML snapshot tests for critical components.
    
    Keep snapshots small and focused on specific components, not entire pages.
    This provides regression detection while keeping diffs manageable.
    """

    def test_table_structure_snapshot(self, snapshot):
        """Should maintain consistent table HTML structure."""
        headers = ["Species", "Signal", "OOS"]
        rows = [
            ["Aphonopelma seemanni", "🔥", "OUT"],
            ["Brachypelma hamorii", "⚠️", "IN"],
        ]
        
        html = generate_table_html(headers, rows, "breeder-table", sortable=True)
        
        # Extract just the table element (not wrapper divs or script)
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        
        assert snapshot == str(table)

    def test_navigation_structure_snapshot(self, snapshot):
        """Should maintain consistent navigation HTML structure."""
        template = get_base_html_template("Test Page", "test")
        
        # Extract just the nav element
        soup = BeautifulSoup(template, "html.parser")
        nav = soup.find("nav")
        
        assert snapshot == str(nav)

    def test_card_grid_snapshot(self, snapshot):
        """Should maintain consistent card grid structure on homepage."""
        html = generate_homepage(last_scrape_time="2025-01-15T12:00:00")
        
        # Extract just the card grid section
        soup = BeautifulSoup(html, "html.parser")
        card_section = soup.find("section", class_="card-grid")
        
        assert snapshot == str(card_section)

    def test_footer_structure_snapshot(self, snapshot):
        """Should maintain consistent footer HTML structure (excluding timestamp)."""
        footer = get_html_footer()
        
        # Extract just the footer element
        soup = BeautifulSoup(footer, "html.parser")
        footer_elem = soup.find("footer")
        
        # Remove the timestamp paragraph for snapshot (it changes every run)
        timestamp_p = footer_elem.find("p", string=lambda text: text and "Generated:" in text)
        if timestamp_p:
            timestamp_p.decompose()
        
        assert snapshot == str(footer_elem)

    def test_search_filter_snapshot(self, snapshot):
        """Should maintain consistent search filter HTML structure."""
        from website.page_config import BreederPageConfig
        
        html = generate_analysis_page(BreederPageConfig(
            title="Test Page",
            description="Test description",
            csv_filename="test.csv",
            table_id="test-table",
            active_page="breeder",
            search_filter=True
        ))
        
        # Extract just the search container
        soup = BeautifulSoup(html, "html.parser")
        search = soup.find("div", class_="search-container")
        
        assert snapshot == str(search)

    def test_download_links_snapshot(self, snapshot):
        """Should maintain consistent download links HTML structure."""
        html = generate_homepage(last_scrape_time="2025-01-15T12:00:00")
        
        # Extract just the download section
        soup = BeautifulSoup(html, "html.parser")
        download_section = soup.find("section", class_="download-section")
        
        assert snapshot == str(download_section)


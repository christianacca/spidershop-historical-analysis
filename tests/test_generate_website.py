#!/usr/bin/env python3
"""
Comprehensive tests for generate_website.py using synthetic data.

Tests cover:
- Markdown to HTML conversion
- CSV file reading and parsing
- HTML generation (tables, pages, templates)
- Analysis section extraction
- Edge cases (missing files, empty data)
"""

#!/usr/bin/env python3
"""
Comprehensive tests for generate_website.py using synthetic data.

Tests cover:
- Markdown to HTML conversion
- CSV file reading and parsing
- HTML generation (tables, pages, templates)
- Analysis section extraction
- Edge cases (missing files, empty data)
"""

import pytest
import tempfile
import os
from pathlib import Path
from bs4 import BeautifulSoup
from generate_website import (
    parse_markdown_to_html,
    extract_analysis_sections,
    read_csv_file,
    escape_html,
    generate_table_html,
    get_base_html_template,
    get_html_footer,
    generate_homepage,
    generate_data_page,
    main,
    OUTPUT_DIR,
)


class TestParseMarkdownToHtml:
    """Snapshot tests for markdown to HTML conversion.
    
    This test verifies that the markdown library continues to produce
    consistent HTML output. If the markdown library is upgraded and this
    test fails, review the changes in the diff to ensure they're acceptable,
    then regenerate the snapshot by running:
    
        pytest --snapshot-update
    """

    def test_markdown_conversion_matches_expected_output(self, snapshot):
        """Should convert full analysis_summary.md to HTML exactly as captured in snapshot."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        
        # Load the real analysis_summary.md fixture
        with open(fixtures_dir / "analysis_summary.md", "r", encoding="utf-8") as f:
            markdown_text = f.read()
        
        # Convert and compare with snapshot
        actual_html = parse_markdown_to_html(markdown_text)
        assert actual_html == snapshot


class TestExtractAnalysisSections:
    """Test suite for extracting analysis sections from markdown."""

    def test_nonexistent_file_returns_none(self):
        """Should return None for breeder and dealer if file doesn't exist."""
        result = extract_analysis_sections("/nonexistent/file.md")
        # Function returns (None, None, None, None, None, None) when file doesn't exist
        assert result == (None, None, None, None, None, None)

    def test_extract_breeder_section(self):
        """Should extract breeder opportunity matrix section."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## 🧬 Breeder Opportunity Matrix (Top 10)

Some analysis text here.

## 🏪 Dealer Supply Risk Matrix (Top 10)

Other content.""")
            filename = f.name
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert breeder is not None
            assert "## 🧬 Breeder Opportunity Matrix (Top 10)" in breeder
            assert "Some analysis text here." in breeder
        finally:
            os.unlink(filename)

    def test_extract_dealer_section(self):
        """Should extract dealer supply risk matrix section."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## 🏪 Dealer Supply Risk Matrix (Top 10)

Dealer analysis here.

<details>
<summary>Legend</summary>
</details>""")
            filename = f.name
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert dealer is not None
            assert "## 🏪 Dealer Supply Risk Matrix (Top 10)" in dealer
            assert "Dealer analysis here." in dealer
        finally:
            os.unlink(filename)

    def test_extract_legend_section(self):
        """Should extract legend from details block."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""<details>
<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>
### 🧬 Breeder Opportunity Matrix — Legend
Breeder legend content here.
### 📖 Breeder Matrix — Practical Examples
Breeder example 1 here.
### 🏪 Dealer Supply Risk Matrix — Legend
Dealer legend content here.
### 📖 Dealer Matrix — Practical Examples
Dealer example 1 here.
</details>""")
            filename = f.name
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert breeder_legend is not None
            assert "Breeder legend content here." in breeder_legend
            assert dealer_legend is not None
            assert "Dealer legend content here." in dealer_legend
            assert breeder_examples is not None
            assert "Breeder example 1 here." in breeder_examples
            assert dealer_examples is not None
            assert "Dealer example 1 here." in dealer_examples
        finally:
            os.unlink(filename)

    def test_missing_sections_return_none(self):
        """Should return None for missing sections."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Some Title\n\nSome content without the expected sections.")
            filename = f.name
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert breeder is None
            assert dealer is None
            assert breeder_legend is None
            assert dealer_legend is None
            assert breeder_examples is None
            assert dealer_examples is None
        finally:
            os.unlink(filename)

    def test_partial_sections(self):
        """Should extract only the sections that exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## 🧬 Breeder Opportunity Matrix (Top 10)

Breeder content only.""")
            filename = f.name
        
        try:
            breeder, dealer, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(filename)
            assert breeder is not None
            assert dealer is None
            assert breeder_legend is None
            assert dealer_legend is None
            assert breeder_examples is None
            assert dealer_examples is None
        finally:
            os.unlink(filename)


class TestExtractSummaryStatistics:
    """Test suite for extracting summary statistics from markdown."""

    def test_extract_breeder_summary_stats(self):
        """Should extract breeder summary statistics from markdown Summary line."""
        from generate_website import extract_summary_stats
        
        markdown = """## 🧬 Breeder Opportunity Matrix (Top 10)

**Summary:** 106 species analyzed | 🔥 Hot: 42 | ⚠️ Watch: 38 | ❌ Avoid: 26

| Species | Size (cm) | OOS |
|---|---:|---|
| Test Species | 1 | OUT |
"""
        
        stats = extract_summary_stats(markdown)
        assert stats is not None
        assert stats['total'] == 106
        assert stats['hot'] == 42
        assert stats['watch'] == 38
        assert stats['avoid'] == 26

    def test_extract_dealer_summary_stats(self):
        """Should extract dealer summary statistics from markdown Summary line."""
        from generate_website import extract_summary_stats
        
        markdown = """## 🏪 Dealer Supply Risk Matrix (Top 10)

**Summary:** 106 species analyzed | 🔥 High Risk: 42 | ⚠️ Moderate Risk: 38 | ❌ Low Risk: 26

| Species | Size (cm) | Stock Reliability |
|---|---:|---|
| Test Species | 1 | Low |
"""
        
        stats = extract_summary_stats(markdown)
        assert stats is not None
        assert stats['total'] == 106
        assert stats['hot'] == 42
        assert stats['watch'] == 38
        assert stats['avoid'] == 26

    def test_extract_summary_stats_missing_summary(self):
        """Should return None when Summary line is missing."""
        from generate_website import extract_summary_stats
        
        markdown = """## 🧬 Breeder Opportunity Matrix (Top 10)

| Species | Size (cm) | OOS |
|---|---:|---|
| Test Species | 1 | OUT |
"""
        
        stats = extract_summary_stats(markdown)
        assert stats is None

    def test_extract_summary_stats_none_input(self):
        """Should return None when markdown is None."""
        from generate_website import extract_summary_stats
        stats = extract_summary_stats(None)
        assert stats is None


class TestSummaryStatsInHtml:
    """Test suite for rendering summary stats in HTML output."""

    def test_breeder_page_includes_summary_stats_cards(self):
        """Should render summary statistics as HTML cards in breeder page and remove duplicate Summary line."""
        from generate_website import generate_data_page
        
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Signal,Recommendation\n")
            f.write("Species A,🔥,Hot opportunity\n")
            f.write("Species B,⚠️,Watch closely\n")
            f.write("Species C,❌,Avoid\n")
            csv_filename = f.name
        
        # Create markdown with Summary line
        analysis_markdown = """## 🧬 Breeder Opportunity Matrix (Top 10)

**Summary:** 3 species analyzed | 🔥 Hot: 1 | ⚠️ Watch: 1 | ❌ Avoid: 1

| Species | Signal |
|---|---|
| Species A | 🔥 |
"""
        
        try:
            html = generate_data_page(
                "Breeder Opportunities",
                "Test description",
                csv_filename,
                "test-table",
                "breeder",
                analysis_markdown=analysis_markdown
            )
            
            # Verify summary stats cards are present in HTML
            assert '<div class="summary-stats">' in html
            assert '<div class="stat-card">' in html
            
            # Verify all 4 stats are present
            assert '<div class="stat-value">3</div>' in html  # total
            assert '<div class="stat-label">Species Analyzed</div>' in html
            
            assert '<div class="stat-value">1</div>' in html  # hot count (appears 3 times for hot/watch/avoid)
            assert '<div class="stat-label">🔥 Hot</div>' in html
            assert '<div class="stat-label">⚠️ Watch</div>' in html
            assert '<div class="stat-label">❌ Avoid</div>' in html
            
            # Verify Summary line text is NOT duplicated in the analysis HTML
            assert '**Summary:**' not in html
            assert 'Summary: 3 species analyzed' not in html
            assert '<strong>Summary:</strong>' not in html
            
            # Verify the table IS still present
            assert '<table' in html
            assert 'Species A' in html
        finally:
            os.unlink(csv_filename)

    def test_dealer_page_includes_summary_stats_cards(self):
        """Should render summary statistics with dealer-specific labels."""
        from generate_website import generate_data_page
        
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Dealer Risk,Notes\n")
            f.write("Species A,🔥,High risk\n")
            f.write("Species B,⚠️,Moderate risk\n")
            f.write("Species C,❌,Low risk\n")
            csv_filename = f.name
        
        # Create markdown with Summary line (dealer format)
        analysis_markdown = """## 🏪 Dealer Supply Risk Matrix (Top 10)

**Summary:** 3 species analyzed | 🔥 High Risk: 1 | ⚠️ Moderate Risk: 1 | ❌ Low Risk: 1

| Species | Dealer Risk |
|---|---|
| Species A | 🔥 |
"""
        
        try:
            html = generate_data_page(
                "Dealer Supply Risk",
                "Test description",
                csv_filename,
                "test-table",
                "dealer",
                analysis_markdown=analysis_markdown
            )
            
            # Verify summary stats cards are present
            assert '<div class="summary-stats">' in html
            
            # Verify dealer-specific labels are used (not breeder labels)
            # Note: extract_summary_stats returns hot/watch/avoid regardless of terminology,
            # but the template should use dealer-friendly labels
            assert '<div class="stat-label">🔥 High Risk</div>' in html
            assert '<div class="stat-label">⚠️ Moderate Risk</div>' in html
            assert '<div class="stat-label">❌ Low Risk</div>' in html
        finally:
            os.unlink(csv_filename)

    def test_page_without_analysis_has_no_summary_stats(self):
        """Should not render summary stats section when no analysis markdown provided."""
        from generate_website import generate_data_page
        
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Price\n")
            f.write("Species A,25.00\n")
            csv_filename = f.name
        
        try:
            html = generate_data_page(
                "Test Page",
                "Test description",
                csv_filename,
                "test-table",
                "test",
                analysis_markdown=None
            )
            
            # Verify NO summary stats section present
            assert '<div class="summary-stats">' not in html
            assert '<div class="stat-card">' not in html
        finally:
            os.unlink(csv_filename)

    def test_page_with_analysis_but_no_summary_line_has_no_stats(self):
        """Should not render summary stats when analysis markdown lacks Summary line."""
        from generate_website import generate_data_page
        
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Signal\n")
            f.write("Species A,🔥\n")
            csv_filename = f.name
        
        # Markdown WITHOUT Summary line
        analysis_markdown = """## 🧬 Breeder Opportunity Matrix (Top 10)

| Species | Signal |
|---|---|
| Species A | 🔥 |
"""
        
        try:
            html = generate_data_page(
                "Breeder Opportunities",
                "Test description",
                csv_filename,
                "test-table",
                "breeder",
                analysis_markdown=analysis_markdown
            )
            
            # Verify NO summary stats section
            assert '<div class="summary-stats">' not in html
        finally:
            os.unlink(csv_filename)


class TestReadCsvFile:
    """Test suite for CSV file reading."""

    def test_nonexistent_file_returns_none_and_empty_list(self):
        """Should return (None, []) for nonexistent file."""
        headers, rows = read_csv_file("/nonexistent/file.csv")
        assert headers is None
        assert rows == []

    def test_empty_csv_file(self):
        """Should handle empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers is None
            assert rows == []
        finally:
            os.unlink(filename)

    def test_csv_with_headers_only(self):
        """Should read CSV with only headers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Column1,Column2,Column3\n")
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Column1", "Column2", "Column3"]
            assert rows == []
        finally:
            os.unlink(filename)

    def test_csv_with_data(self):
        """Should read CSV with headers and data rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Name,Price,Size\n")
            f.write("Species A,25.00,1.0\n")
            f.write("Species B,30.50,2.5\n")
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Name", "Price", "Size"]
            assert len(rows) == 2
            assert rows[0] == ["Species A", "25.00", "1.0"]
            assert rows[1] == ["Species B", "30.50", "2.5"]
        finally:
            os.unlink(filename)

    def test_csv_with_special_characters(self):
        """Should handle CSV with special characters and quotes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write('Name,Description\n')
            f.write('"Species, with comma","Description with ""quotes"""\n')
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Name", "Description"]
            assert rows[0] == ["Species, with comma", 'Description with "quotes"']
        finally:
            os.unlink(filename)

    def test_csv_with_utf8_characters(self):
        """Should handle UTF-8 encoded characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Common\n")
            f.write("Brachypelma boehmei,🕷️ Mexican Fireleg\n")
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Species", "Common"]
            assert rows[0] == ["Brachypelma boehmei", "🕷️ Mexican Fireleg"]
        finally:
            os.unlink(filename)


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

    def test_table_with_sortable_headers(self):
        """Should generate sortable table headers by default."""
        headers = ["Name", "Price", "Size"]
        rows = [["Species A", "25.00", "1.0"]]
        html = generate_table_html(headers, rows, "test-table", sortable=True)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verify table structure
        table = soup.find('table', id='test-table', class_='data-table')
        assert table is not None
        
        # Verify sortable headers have onclick
        headers_elements = table.select('thead th')
        assert len(headers_elements) == 3
        for i, th in enumerate(headers_elements):
            assert 'onclick' in th.attrs
            assert f"sortTable({i}, 'test-table')" in th['onclick']
            # Verify sort indicator present
            indicator = th.find('span', class_='sort-indicator')
            assert indicator is not None
            assert indicator.text == '⇅'

    def test_table_without_sortable_headers(self):
        """Should generate non-sortable table headers when sortable=False."""
        headers = ["Name", "Price"]
        rows = [["Species A", "25.00"]]
        html = generate_table_html(headers, rows, "test-table", sortable=False)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verify table structure
        table = soup.find('table', id='test-table', class_='data-table')
        assert table is not None
        
        # Verify headers do NOT have onclick or sort indicators
        headers_elements = table.select('thead th')
        assert len(headers_elements) == 2
        for th in headers_elements:
            assert 'onclick' not in th.attrs
            indicator = th.find('span', class_='sort-indicator')
            assert indicator is None

    def test_table_escapes_html_in_cells(self):
        """Should escape HTML special characters in table cells."""
        headers = ["Name", "Description"]
        rows = [["<script>", "Tom & Jerry"]]
        html = generate_table_html(headers, rows, "test-table")
        
        assert "&lt;script&gt;" in html
        assert "Tom &amp; Jerry" in html

    def test_table_with_multiple_rows(self):
        """Should generate table with multiple data rows."""
        headers = ["A", "B"]
        rows = [["1", "2"], ["3", "4"], ["5", "6"]]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verify table structure
        table = soup.find('table', id='test-table')
        assert table is not None
        
        # Count rows: 1 header row + 3 data rows
        all_rows = table.find_all('tr')
        assert len(all_rows) == 4
        
        # Verify data rows
        data_rows = table.select('tbody tr')
        assert len(data_rows) == 3
        
        # Verify first and last cell content
        first_cell = data_rows[0].find('td')
        assert first_cell.text == '1'
        last_cell = data_rows[-1].find_all('td')[-1]
        assert last_cell.text == '6'

    def test_table_structure_complete(self):
        """Should generate complete table structure with thead and tbody."""
        headers = ["Col"]
        rows = [["Val"]]
        html = generate_table_html(headers, rows, "test-table")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verify table exists
        table = soup.find('table', id='test-table')
        assert table is not None
        
        # Verify table has proper structure
        thead = table.find('thead')
        tbody = table.find('tbody')
        assert thead is not None
        assert tbody is not None
        
        # Verify header and data
        th = thead.find('th')
        assert th is not None
        assert th.text.strip().startswith('Col')
        
        td = tbody.find('td')
        assert td is not None
        assert td.text == 'Val'

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


class TestGetBaseHtmlTemplate:
    """Test suite for base HTML template generation."""

    def test_includes_doctype_and_html_tags(self):
        """Should include DOCTYPE and html tags."""
        html = get_base_html_template("Test Page")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check DOCTYPE (not parsed by BeautifulSoup, check raw string)
        assert "<!DOCTYPE html>" in html
        
        # Check html tag with lang attribute
        html_tag = soup.find('html')
        assert html_tag is not None
        assert html_tag.get('lang') == 'en'
        
        # Base template doesn't close html (partial template)
        assert "</html>" not in html

    def test_includes_title_in_head(self):
        """Should include title in head section."""
        html = get_base_html_template("My Page")
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.find('title')
        assert title is not None
        assert title.text == "My Page - Spider Shop Historical Analysis"

    def test_includes_viewport_meta(self):
        """Should include viewport meta tag for responsive design."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        assert viewport_meta is not None
        assert viewport_meta['content'] == 'width=device-width, initial-scale=1.0'

    def test_includes_navigation(self):
        """Should include navigation menu."""
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
        
        active_links = soup.select('nav a.active')
        assert len(active_links) == 1
        assert active_links[0]['href'] == 'index.html'

    def test_active_page_snapshot(self):
        """Should mark snapshot page as active."""
        html = get_base_html_template("Test", "snapshot")
        soup = BeautifulSoup(html, 'html.parser')
        
        active_links = soup.select('nav a.active')
        assert len(active_links) == 1
        assert active_links[0]['href'] == 'snapshot.html'

    def test_includes_css_styles(self):
        """Should include embedded CSS styles."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        style = soup.find('style')
        assert style is not None
        css_content = style.string
        assert '.data-table' in css_content
        assert 'font-family:' in css_content

    def test_includes_header(self):
        """Should include page header with title."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        header = soup.find('header')
        assert header is not None
        assert 'Spider Shop Historical Analysis' in header.text

    def test_opens_container_div(self):
        """Should open container div."""
        html = get_base_html_template("Test")
        soup = BeautifulSoup(html, 'html.parser')
        
        container = soup.find('div', class_='container')
        assert container is not None


class TestGetHtmlFooter:
    """Test suite for HTML footer generation."""

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

    def test_includes_javascript_functions(self):
        """Should include JavaScript for table sorting and filtering."""
        html = get_html_footer()
        soup = BeautifulSoup(html, 'html.parser')
        
        script = soup.find('script')
        assert script is not None
        js_content = script.string
        assert 'function sortTable(' in js_content
        assert 'function filterTable(' in js_content

    def test_closes_html_tags(self):
        """Should close body and html tags."""
        html = get_html_footer()
        # These closing tags are at the end of the string
        assert "</body>" in html
        assert "</html>" in html

    def test_javascript_handles_numeric_sorting(self):
        """JavaScript should include numeric sort logic."""
        html = get_html_footer()
        soup = BeautifulSoup(html, 'html.parser')
        
        script = soup.find('script')
        js_content = script.string
        assert 'isNumeric' in js_content
        assert 'parseFloat' in js_content

    def test_javascript_handles_string_sorting(self):
        """JavaScript should include string sort logic."""
        html = get_html_footer()
        soup = BeautifulSoup(html, 'html.parser')
        
        script = soup.find('script')
        js_content = script.string
        assert 'toLowerCase' in js_content
        assert 'localeCompare' in js_content


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
            html = generate_data_page(
                "Test Page",
                "Test description",
                filename,
                "test-table",
                "snapshot"
            )
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
            html = generate_data_page(
                "My Title",
                "My description text",
                filename,
                "test-table",
                "snapshot"
            )
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
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot"
            )
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
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                search_filter=True
            )
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
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                search_filter=False
            )
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
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot"
            )
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
        html = generate_data_page(
            "Test",
            "Desc",
            "/nonexistent/file.csv",
            "test-table",
            "snapshot"
        )
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should have "No data available" message
        assert 'No data available' in html
        
        # Should not have a table
        table = soup.find('table', id='test-table')
        assert table is None

    def test_includes_analysis_markdown_when_provided(self):
        """Should include analysis section when markdown provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            analysis_md = "## Analysis\n\nThis is **important** analysis."
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                analysis_markdown=analysis_md
            )
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find analysis section
            analysis_section = soup.find('div', class_='analysis-section')
            assert analysis_section is not None
            
            # h2 is downgraded to h3 for proper heading hierarchy
            h3 = analysis_section.find('h3')
            assert h3 is not None
            assert 'Analysis' in h3.text
            
            # Check for formatted content
            strong = soup.find('strong', string='important')
            assert strong is not None
        finally:
            os.unlink(filename)

    def test_omits_analysis_section_when_none(self):
        """Should omit analysis section when markdown not provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Col\n")
            filename = f.name
        
        try:
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                analysis_markdown=None
            )
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
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                legend_markdown=legend_md
            )
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
            html = generate_data_page(
                "Test",
                "Desc",
                filename,
                "test-table",
                "snapshot",
                legend_markdown=None
            )
            soup = BeautifulSoup(html, 'html.parser')
            
            # Should not have details element with legend
            details_elements = soup.find_all('details')
            for details in details_elements:
                assert 'How to read these tables' not in details.text
        finally:
            os.unlink(filename)


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
                    f.write("Species,Signal\n")
                
                with open("dealer_supply_risk_table.csv", "w", encoding="utf-8") as f:
                    f.write("Species,Risk\n")
                
                # Create analysis_summary.md with markdown inside details blocks
                with open("analysis_summary.md", "w", encoding="utf-8") as f:
                    f.write("""## 🧬 Breeder Opportunity Matrix (Top 10)

Breeder content here.

## 🏪 Dealer Supply Risk Matrix (Top 10)

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
                
                # Verify breeder.html was created and contains converted HTML
                breeder_html_path = OUTPUT_DIR / "breeder.html"
                assert breeder_html_path.exists(), "breeder.html should be created"
                
                with open(breeder_html_path, "r", encoding="utf-8") as f:
                    breeder_html = f.read()
                
                # Verify breeder content is present
                assert "Breeder content here" in breeder_html
                
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
                
                # Verify dealer content is present
                assert "Dealer content here" in dealer_html
                
                # Verify legend markdown was converted to HTML
                assert "<h4>🏪 Dealer Supply Risk Matrix — Legend</h4>" in dealer_html
                assert "<ul>" in breeder_html
                assert "<li><code>High</code>" in dealer_html
                
                # Verify examples were converted
                assert "<h4>📖 Dealer Matrix — Practical Examples</h4>" in dealer_html
                assert "Example content for dealers" in dealer_html
                
                # Verify NO markdown syntax remains
                assert "### 🏪 Dealer" not in dealer_html
                assert "- `High`" not in dealer_html
                
            finally:
                os.chdir(original_dir)

    def test_full_page_generation_with_all_features(self):
        """Should generate complete page with all features enabled."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Price,Size\n")
            f.write("Aphonopelma seemanni,25.00,1.0\n")
            f.write("Grammostola pulchra,40.00,2.0\n")
            csv_file = f.name
        
        try:
            analysis_md = """## Analysis

This is the **analysis** section with *formatting*.

| Metric | Value |
|--------|-------|
| Count  | 2     |"""

            legend_md = "**Symbol**: Meaning of symbol."
            
            html = generate_data_page(
                "Test Page",
                "Description here",
                csv_file,
                "test-table",
                "snapshot",
                search_filter=True,
                analysis_markdown=analysis_md,
                legend_markdown=legend_md
            )
            
            # Verify all components present
            assert "<!DOCTYPE html>" in html
            assert "Test Page" in html
            assert "Description here" in html
            assert "Download CSV" in html
            assert "Search:" in html
            assert "Aphonopelma seemanni" in html
            assert "Grammostola pulchra" in html
            assert "analysis-section" in html
            assert "<strong>analysis</strong>" in html
            assert "<details>" in html
            assert "Symbol" in html
            assert "</html>" in html
        finally:
            os.unlink(csv_file)

    def test_handles_empty_csv_gracefully(self):
        """Should handle empty CSV file without errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            csv_file = f.name
        
        try:
            html = generate_data_page(
                "Empty Data",
                "No data test",
                csv_file,
                "test-table",
                "snapshot"
            )
            assert "No data available" in html
            assert "<!DOCTYPE html>" in html
            assert "</html>" in html
        finally:
            os.unlink(csv_file)

    def test_html_escaping_prevents_injection(self):
        """Should properly escape HTML to prevent injection attacks."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Name,Script\n")
            f.write('<script>alert("xss")</script>,<img src=x onerror=alert(1)>\n')
            csv_file = f.name
        
        try:
            html = generate_data_page(
                "<script>bad</script>",
                "<b>Description</b>",
                csv_file,
                "test-table",
                "snapshot"
            )
            # Verify escaping
            assert "&lt;script&gt;" in html
            assert "<script>alert" not in html
            assert "&lt;img src=" in html
        finally:
            os.unlink(csv_file)

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
                    assert "Breeder content" in breeder_html
                    assert "Legend content" in breeder_html
                
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
        
        html = generate_table_html("breeder-table", headers, rows, sortable=True)
        
        # Extract just the table element (not wrapper divs)
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
        html = generate_data_page(
            title="Test Page",
            description="Test description",
            csv_filename="test.csv",
            table_id="test-table",
            active_page="test",
            search_filter=True
        )
        
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


class TestCssValidation:
    """CSS validation tests to ensure styles are well-formed and complete."""

    def test_css_is_present_in_template(self):
        """Should include CSS in base template."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        style = soup.find("style")
        
        assert style is not None
        assert len(style.string) > 100  # Should have substantial CSS

    def test_css_contains_critical_selectors(self):
        """Should include critical CSS selectors for layout."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        critical_selectors = [
            "body",
            "header",
            "nav",
            "footer",
            ".container",
            "table",
            "th",
            "td",
        ]
        
        for selector in critical_selectors:
            assert selector in css, f"Missing critical selector: {selector}"

    def test_css_contains_responsive_breakpoints(self):
        """Should include media queries for responsive design."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Check for media query presence
        assert "@media" in css
        assert "max-width" in css or "min-width" in css

    def test_css_has_proper_bracing(self):
        """Should have balanced braces in CSS."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        open_braces = css.count("{")
        close_braces = css.count("}")
        
        assert open_braces == close_braces, "Unbalanced CSS braces"
        assert open_braces > 0, "No CSS rules found"

    def test_css_contains_color_scheme(self):
        """Should define color scheme variables or consistent colors."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Should have color definitions (hex, rgb, or named)
        has_colors = (
            "#" in css or  # Hex colors
            "rgb" in css or  # RGB colors
            "color:" in css  # Color properties
        )
        
        assert has_colors, "No color definitions found in CSS"

    def test_css_includes_table_styling(self):
        """Should include comprehensive table styling."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Check for key table elements (not all need explicit selectors)
        required_table_elements = ["table", "th", "td"]
        
        for element in required_table_elements:
            assert element in css, f"Missing table element styling: {element}"

    def test_css_includes_interactive_states(self):
        """Should include hover and active states for interactive elements."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Should have pseudo-class selectors for interactivity
        assert ":hover" in css, "Missing hover states"

    def test_css_has_proper_semicolons(self):
        """Should have semicolons after CSS property values."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Count property-value pairs (rough heuristic: look for colons in rules)
        # This is a basic sanity check, not exhaustive validation
        style_blocks = css.split("}")
        
        for block in style_blocks:
            if "{" in block and ":" in block:
                # Extract the rules part (after opening brace)
                rules_part = block.split("{")[-1]
                colon_count = rules_part.count(":")
                semicolon_count = rules_part.count(";")
                
                # Allow for last property to optionally omit semicolon
                # But most should have them
                if colon_count > 0:
                    assert semicolon_count >= colon_count - 1, \
                        f"Missing semicolons in CSS block: {block[:50]}..."

    def test_css_box_model_consistency(self):
        """Should use consistent box-sizing model."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Modern best practice: use border-box for predictable sizing
        assert "box-sizing" in css
        assert "border-box" in css

    def test_css_font_specifications(self):
        """Should specify font families and sizes."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        assert "font-family" in css
        assert "font-size" in css or "rem" in css or "em" in css

    def test_css_no_obvious_typos(self):
        """Should not contain common CSS property typos."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string.lower()
        
        # Common typos to check for
        typos = [
            "colr:",  # color typo
            "widht:",  # width typo
            "heigth:",  # height typo
            "margn:",  # margin typo
            "paddin:",  # padding typo
        ]
        
        for typo in typos:
            assert typo not in css, f"Found possible typo: {typo}"

    def test_css_layout_properties_present(self):
        """Should include modern layout properties."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Should use modern layout techniques
        has_modern_layout = (
            "display: flex" in css or
            "display: grid" in css or
            "display:flex" in css or
            "display:grid" in css
        )
        
        assert has_modern_layout, "No modern layout properties found"


class TestSparklineSVGConversion:
    """Test suite for converting Unicode sparklines to SVG."""

    def test_convert_price_sparkline_with_rising_trend(self):
        """Should convert rising price sparkline to SVG with green bars and tooltips."""
        from generate_website import convert_sparkline_to_svg
        
        unicode_sparkline = "▁▂▃▄▅▆▇█"
        values = ["8.99", "10.50", "12.99", "16.50", "18.99", "21.00", "21.00", "24.99"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="price")
        
        # Should be SVG element
        assert svg.startswith('<svg')
        assert '</svg>' in svg
        
        # Should have green color (rising trend)
        assert '#22c55e' in svg or '#4CAF50' in svg or 'green' in svg.lower()
        
        # Should have tooltips with price values
        assert '£8.99' in svg or '8.99' in svg
        assert '£24.99' in svg or '24.99' in svg
        
        # Should have 8 bars
        assert svg.count('<rect') == 8

    def test_convert_wishlist_sparkline_with_falling_trend(self):
        """Should convert falling wishlist sparkline to SVG with red bars."""
        from generate_website import convert_sparkline_to_svg
        
        unicode_sparkline = "█▇▆▅▄▃▂▁"
        values = ["45", "40", "35", "28", "20", "15", "12", "8"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="wishlist")
        
        # Should be SVG element
        assert svg.startswith('<svg')
        
        # Should have red color (falling trend)
        assert '#ef4444' in svg or '#f44336' in svg or 'red' in svg.lower()
        
        # Should have tooltips with wishlist counts
        assert '45' in svg
        assert '8' in svg
        assert 'wishlist' in svg.lower()

    def test_convert_stable_sparkline_uses_gray(self):
        """Should use gray color for stable/neutral trends."""
        from generate_website import convert_sparkline_to_svg
        
        unicode_sparkline = "▄▄▄▄▄▄▄▄"
        values = ["12.50", "12.50", "12.50", "13.00", "12.50", "12.50", "12.50", "12.50"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="price")
        
        # Should be blue (neutral) for stable trend
        assert '#3b82f6' in svg or '#888' in svg or 'blue' in svg.lower()

    def test_convert_sparkline_with_gaps_before_first_appearance(self):
        """Should render gaps as true empty space when species didn't exist yet (no bars)."""
        from generate_website import convert_sparkline_to_svg
        
        # Unicode sparkline: 4 spaces (didn't exist), then 3 bars (existed with carried-forward values)
        unicode_sparkline = "    ▄▄▄"
        values = ["20.00", "20.00", "20.00", "20.00", "20.00", "20.00", "20.00"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="price")
        
        # Should be SVG
        assert svg.startswith('<svg')
        assert '</svg>' in svg
        
        # Should have exactly 3 bars (not 7) - gaps should not render as bars
        assert svg.count('<rect') == 3
        
        # Should NOT have carried-forward indicators in tooltips (gaps are true absences)
        assert 'carried forward' not in svg.lower()
        
        # Bars should be positioned at x=40, 50, 60 (skipping first 4 positions)
        assert 'x="40"' in svg  # 5th position (index 4)
        assert 'x="50"' in svg  # 6th position (index 5)
        assert 'x="60"' in svg  # 7th position (index 6)
        
        # Should NOT have bars at x=0, 10, 20, 30 (the gap positions)
        assert 'x="0"' not in svg
        assert 'x="10"' not in svg
        assert 'x="20"' not in svg
        assert 'x="30"' not in svg

    def test_convert_stock_availability_sparkline(self):
        """Should convert stock availability sparkline (binary IN/OUT)."""
        from generate_website import convert_sparkline_to_svg
        
        unicode_sparkline = "█ █ █"
        values = None  # Stock availability doesn't need numeric values
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="stock")
        
        # Should have green bars for IN stock
        assert '#22c55e' in svg or '#4CAF50' in svg or 'green' in svg.lower()
        
        # Should have tooltips
        assert '<title>IN</title>' in svg

    def test_sparkline_with_no_values_returns_dash(self):
        """Should return plain dash for invalid sparklines."""
        from generate_website import convert_sparkline_to_svg
        
        result = convert_sparkline_to_svg("-", [], metric_type="price")
        
        # Should return the original dash (no conversion)
        assert result == "-"

    def test_sparkline_dimensions_are_consistent(self):
        """Should generate SVG with consistent dimensions."""
        from generate_website import convert_sparkline_to_svg
        
        unicode_sparkline = "▁▂▃▄▅▆▇█"
        values = ["10", "15", "20", "25", "30", "35", "40", "45"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="wishlist")
        
        # Should have standard dimensions
        assert 'width="80"' in svg
        assert 'height="20"' in svg
        assert 'viewBox="0 0 80 20"' in svg

    def test_sparkline_with_leading_gaps_aligns_tooltips_correctly(self):
        """
        Should align tooltips with correct values when sparkline has leading gaps.
        
        This is a regression test for the bug where:
        - Unicode sparkline: "  █▁▁▁▁" (2 leading spaces/gaps, then 5 bars)
        - Historical values: [0, 0, 91, 90] (4 values in chronological order)
        - Expected: First bar (█) should show "0 wishlists", subsequent bars show actual values
        - Bug: Tooltips were misaligned because we indexed values[] using position in bars[]
        """
        from generate_website import convert_sparkline_to_svg
        
        # Sparkline with 2 leading gaps (spaces), then 5 bars
        unicode_sparkline = "  █▁▁▁▁"
        # Historical values: [old=0, old=0, new=91, newest=90]
        # But we only have 4 values in the history, not 7
        values = ["0", "0", "91", "90"]
        
        svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type="wishlist")
        
        # Should render only 5 bars (skipping the 2 leading gaps)
        rect_count = svg.count('<rect')
        assert rect_count == 5, f"Expected 5 bars but got {rect_count}"
        
        # Parse SVG to check tooltip values in order
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(svg, 'html.parser')
        rects = soup.find_all('rect')
        
        # Extract tooltip text from each rect's <title> child
        tooltips = [rect.find('title').text for rect in rects if rect.find('title')]
        
        # The first 4 bars should have actual wishlist values
        # Note: The values list has 4 items, sparkline has 5 bars (2 gaps + 5 bars = 7 positions)
        # So bars [2,3,4,5] should map to values [0,1,2,3]
        assert "0 wishlists" in tooltips[0], f"First bar should show '0 wishlists', got {tooltips[0]}"
        assert "0 wishlists" in tooltips[1], f"Second bar should show '0 wishlists', got {tooltips[1]}"
        assert "91 wishlists" in tooltips[2], f"Third bar should show '91 wishlists', got {tooltips[2]}"
        assert "90 wishlists" in tooltips[3], f"Fourth bar should show '90 wishlists', got {tooltips[3]}"
        # Fifth bar has no value (beyond values list), should show "Week N"
        assert "Week" in tooltips[4], f"Fifth bar should show 'Week N', got {tooltips[4]}"


class TestConvertSparklinesInRows:
    """Test suite for converting Unicode sparklines in CSV rows."""

    def test_converts_price_sparklines_in_csv_rows(self):
        """Should convert price history sparklines in CSV data rows."""
        from generate_website import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Price History"]
        rows = [
            ["Aphonopelma seemanni", "1.5", "▁▂▃▄▅▆▇█"]
        ]
        
        # Create historical data structure
        by_run = {
            "2025-01-01": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "8.99", "wishlist_count": "5"}],
            "2025-01-08": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "10.50", "wishlist_count": "5"}],
            "2025-01-15": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "12.99", "wishlist_count": "5"}],
            "2025-01-22": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "16.50", "wishlist_count": "5"}],
            "2025-01-29": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "18.99", "wishlist_count": "20"}],
            "2025-02-05": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "21.00", "wishlist_count": "22"}],
            "2025-02-12": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "21.00", "wishlist_count": "25"}],
            "2025-02-19": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "24.99", "wishlist_count": "28"}],
        }
        runs = sorted(by_run.keys())
        historical_data = (by_run, runs)
        
        result = convert_sparklines_in_rows(headers, rows, historical_data, "test.csv")
        
        # Should have SVG in the sparkline column
        assert '<svg' in result[0][2]
        assert '</svg>' in result[0][2]
        assert '8.99' in result[0][2] or '£8.99' in result[0][2]

    def test_converts_wishlist_sparklines_in_csv_rows(self):
        """Should convert wishlist history sparklines in CSV data rows."""
        from generate_website import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Wishlist History"]
        rows = [
            ["Test Species", "2.0", "▁▁▁▁████"]
        ]
        
        by_run = {
            "2025-01-01": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "5"}],
            "2025-01-08": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "5"}],
            "2025-01-15": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "5"}],
            "2025-01-22": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "5"}],
            "2025-01-29": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "20"}],
            "2025-02-05": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "22"}],
            "2025-02-12": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "25"}],
            "2025-02-19": [{"scientific_name": "Test Species", "size_cm": "2.0", "price_gbp": "10.00", "wishlist_count": "28"}],
        }
        runs = sorted(by_run.keys())
        historical_data = (by_run, runs)
        
        result = convert_sparklines_in_rows(headers, rows, historical_data, "test.csv")
        
        assert '<svg' in result[0][2]
        assert 'wishlists' in result[0][2]

    def test_converts_stock_availability_sparklines_in_csv_rows(self):
        """Should convert stock availability sparklines without crashing (regression test for metric_type=None bug)."""
        from generate_website import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Stock Availability"]
        rows = [
            ["Test Species", "2.0", "█ █ █"]
        ]
        
        # Stock sparklines don't use historical data
        historical_data = ({}, [])
        
        # Should not raise AttributeError: 'NoneType' object has no attribute 'capitalize'
        result = convert_sparklines_in_rows(headers, rows, historical_data, "test.csv")
        
        assert '<svg' in result[0][2]
        assert '<title>IN</title>' in result[0][2]

    def test_handles_rows_without_sparkline_columns(self):
        """Should return unchanged rows when no sparkline columns present."""
        from generate_website import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Price"]
        rows = [
            ["Test Species", "2.0", "£10.00"]
        ]
        
        result = convert_sparklines_in_rows(headers, rows, ({}, []), "test.csv")
        
        # Should be unchanged
        assert result == rows

    def test_handles_empty_historical_data(self):
        """Should handle missing historical data gracefully."""
        from generate_website import convert_sparklines_in_rows
        
        headers = ["Species", "Size (cm)", "Price History"]
        rows = [
            ["Unknown Species", "1.0", "▁▂▃▄"]
        ]
        
        # No historical data available
        result = convert_sparklines_in_rows(headers, rows, ({}, []), "test.csv")
        
        # Should still convert to SVG (without values)
        assert '<svg' in result[0][2]


class TestConvertSparklinesInHtml:
    """Test suite for converting Unicode sparklines in HTML tables."""

    def test_converts_sparklines_in_markdown_table(self):
        """Should convert Unicode sparklines in markdown-generated HTML tables."""
        from generate_website import convert_sparklines_in_html
        
        # Simulate markdown-generated HTML with Unicode sparklines
        html = """
        <table>
            <thead>
                <tr>
                    <th>Species</th>
                    <th>Size (cm)</th>
                    <th>Price History</th>
                    <th>Wishlist History</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Aphonopelma seemanni</td>
                    <td>1.5</td>
                    <td>▁▂▃▄▅▆▇█</td>
                    <td>▁▁▁▁████</td>
                </tr>
            </tbody>
        </table>
        """
        
        # Mock historical data in (by_run, runs) format
        # Create simple structure with one run per row
        by_run = {
            "2025-01-01": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "8.99", "wishlist_count": "5"}],
            "2025-01-08": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "10.50", "wishlist_count": "5"}],
            "2025-01-15": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "12.99", "wishlist_count": "5"}],
            "2025-01-22": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "16.50", "wishlist_count": "5"}],
            "2025-01-29": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "18.99", "wishlist_count": "20"}],
            "2025-02-05": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "21.00", "wishlist_count": "22"}],
            "2025-02-12": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "21.00", "wishlist_count": "25"}],
            "2025-02-19": [{"scientific_name": "Aphonopelma seemanni", "size_cm": "1.5", "price_gbp": "24.99", "wishlist_count": "28"}],
        }
        runs = sorted(by_run.keys())
        historical_data = (by_run, runs)
        
        result = convert_sparklines_in_html(html, historical_data)
        
        # Should contain SVG elements
        assert '<svg' in result
        assert '</svg>' in result
        
        # Should have tooltips with actual values
        assert '8.99' in result or '£8.99' in result
        assert '24.99' in result or '£24.99' in result
        
        # Should NOT contain Unicode sparklines anymore
        assert '▁▂▃▄▅▆▇█' not in result

    def test_handles_html_without_tables(self):
        """Should return unchanged HTML when no tables present."""
        from generate_website import convert_sparklines_in_html
        
        html = "<p>No tables here</p>"
        result = convert_sparklines_in_html(html, ({}, []))
        
        assert result == html

    def test_handles_tables_without_sparkline_columns(self):
        """Should not modify tables without sparkline columns."""
        from generate_website import convert_sparklines_in_html
        
        html = """
        <table>
            <thead>
                <tr><th>Name</th><th>Value</th></tr>
            </thead>
            <tbody>
                <tr><td>Test</td><td>123</td></tr>
            </tbody>
        </table>
        """
        
        result = convert_sparklines_in_html(html, ({}, []))
        
        # Should contain table but no SVG
        assert '<table>' in result
        assert '<svg' not in result

    def test_handles_empty_html(self):
        """Should handle None or empty HTML gracefully."""
        from generate_website import convert_sparklines_in_html
        
        assert convert_sparklines_in_html(None, ({}, [])) is None
        assert convert_sparklines_in_html("", ({}, [])) == ""

    def test_converts_stock_availability_sparklines(self):
        """Should convert stock availability sparklines in HTML tables."""
        from generate_website import convert_sparklines_in_html
        
        html = """
        <table>
            <thead>
                <tr>
                    <th>Species</th>
                    <th>Stock Availability</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Test Species</td>
                    <td>█ █ █</td>
                </tr>
            </tbody>
        </table>
        """
        
        result = convert_sparklines_in_html(html, ({}, []))
        
        # Should contain SVG for stock availability
        assert '<svg' in result
        assert '<title>IN</title>' in result

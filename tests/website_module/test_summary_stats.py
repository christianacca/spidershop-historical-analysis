#!/usr/bin/env python3
"""Tests for summary statistics extraction and rendering."""
import pytest
import tempfile
import os
from bs4 import BeautifulSoup
from website import PageConfig
from website.generate_website import extract_summary_stats, generate_data_page


class TestExtractSummaryStatistics:
    """Test suite for extracting summary statistics from markdown."""

    def test_extract_breeder_summary_stats(self):
        """Should extract breeder summary statistics from markdown Summary line."""
        from website.generate_website import extract_summary_stats
        
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
        from website.generate_website import extract_summary_stats
        
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
        from website.generate_website import extract_summary_stats
        
        markdown = """## 🧬 Breeder Opportunity Matrix (Top 10)

| Species | Size (cm) | OOS |
|---|---:|---|
| Test Species | 1 | OUT |
"""
        
        stats = extract_summary_stats(markdown)
        assert stats is None

    def test_extract_summary_stats_none_input(self):
        """Should return None when markdown is None."""
        from website.generate_website import extract_summary_stats
        stats = extract_summary_stats(None)
        assert stats is None


class TestSummaryStatsInHtml:
    """Test suite for rendering summary stats in HTML output."""

    def test_breeder_page_includes_summary_stats_cards(self):
        """Should render summary statistics as HTML cards in breeder page and remove duplicate Summary line."""
        from website.generate_website import generate_data_page
        from conftest import create_temp_csv_file
        
        # Create a temporary CSV file
        csv_filename = create_temp_csv_file(
            "Species,Signal,Recommendation\n"
            "Species A,🔥,Hot opportunity\n"
            "Species B,⚠️,Watch closely\n"
            "Species C,❌,Avoid\n"
        )
        
        # Create markdown with Summary line
        analysis_markdown = """## 🧬 Breeder Opportunity Matrix (Top 10)

**Summary:** 3 species analyzed | 🔥 Hot: 1 | ⚠️ Watch: 1 | ❌ Avoid: 1

| Species | Signal |
|---|---|
| Species A | 🔥 |
"""
        
        try:
            html = generate_data_page(PageConfig(
                title="Breeder Opportunities",
                description="Test description",
                csv_filename=csv_filename,
                table_id="test-table",
                active_page="breeder",
                analysis_markdown=analysis_markdown
            ))
            
            # Verify summary stats cards are present in HTML
            assert '<div class="summary-stats">' in html
            assert '<div class="stat-card">' in html
            
            # Verify all 4 stats are present
            assert '<div class="stat-value">3</div>' in html  # total
            assert '<div class="stat-label">Species Analyzed</div>' in html
            
            assert '<div class="stat-value">1</div>' in html  # hot count (appears 3 times for hot/watch/avoid)
            # Labels now wrapped in stat-label div with info icons
            assert '🔥 Hot' in html
            assert '⚠️ Watch' in html
            assert '❌ Avoid' in html
            
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
        from website.generate_website import generate_data_page
        
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
            html = generate_data_page(PageConfig(
                title="Dealer Supply Risk",
                description="Test description",
                csv_filename=csv_filename,
                table_id="test-table",
                active_page="dealer",
                analysis_markdown=analysis_markdown
            ))
            
            # Verify summary stats cards are present
            assert '<div class="summary-stats">' in html
            
            # Verify dealer-specific labels are used (not breeder labels)
            # Note: extract_summary_stats returns hot/watch/avoid regardless of terminology,
            # but the template should use dealer-friendly labels
            assert '🔥 High Risk' in html
            assert '⚠️ Moderate Risk' in html
            assert '❌ Low Risk' in html
        finally:
            os.unlink(csv_filename)

    def test_page_without_analysis_has_no_summary_stats(self):
        """Should not render summary stats section when no analysis markdown provided."""
        from website.generate_website import generate_data_page
        
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Price\n")
            f.write("Species A,25.00\n")
            csv_filename = f.name
        
        try:
            html = generate_data_page(PageConfig(
                title="Test Page",
                description="Test description",
                csv_filename=csv_filename,
                table_id="test-table",
                active_page="test",
                analysis_markdown=None
            ))
            
            # Verify NO summary stats section present
            assert '<div class="summary-stats">' not in html
            assert '<div class="stat-card">' not in html
        finally:
            os.unlink(csv_filename)

    def test_page_with_analysis_but_no_summary_line_has_no_stats(self):
        """Should not render summary stats when analysis markdown lacks Summary line."""
        from website.generate_website import generate_data_page
        
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
            html = generate_data_page(PageConfig(
                title="Breeder Opportunities",
                description="Test description",
                csv_filename=csv_filename,
                table_id="test-table",
                active_page="breeder",
                analysis_markdown=analysis_markdown
            ))
            
            # Verify NO summary stats section (because no Summary line found)
            assert '<div class="summary-stats">' not in html
        finally:
            os.unlink(csv_filename)

    def test_breeder_summary_cards_include_tooltip_explanations(self):
        """Should include info icons with tooltip explanations for breeder signals."""
        from website.generate_website import generate_data_page
        
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Signal\n")
            f.write("Species A,🔥\n")
            csv_filename = f.name
        
        analysis_markdown = """## 🧬 Breeder Opportunity Matrix (Top 10)

**Summary:** 3 species analyzed | 🔥 Hot: 1 | ⚠️ Watch: 1 | ❌ Avoid: 1
"""
        
        try:
            html = generate_data_page(PageConfig(
                title="Breeder Opportunities",
                description="Test description",
                csv_filename=csv_filename,
                table_id="test-table",
                active_page="breeder",
                analysis_markdown=analysis_markdown
            ))
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Verify info icons are present (one for each stat except total)
            info_icons = soup.find_all('span', class_='info-icon')
            assert len(info_icons) == 3  # hot, watch, avoid
            
            # Verify tooltips contain breeder-specific explanations
            tooltips = soup.find_all('span', class_='tooltip')
            assert len(tooltips) == 3
            
            # Check hot tooltip
            hot_tooltip = tooltips[0].get_text()
            assert 'breeding opportunity' in hot_tooltip.lower()
            assert 'scarcity' in hot_tooltip.lower()
            
            # Check watch tooltip
            watch_tooltip = tooltips[1].get_text()
            assert 'emerging' in watch_tooltip.lower()
            assert 'monitor' in watch_tooltip.lower() or 'watch' in watch_tooltip.lower()
            
            # Check avoid tooltip
            avoid_tooltip = tooltips[2].get_text()
            assert 'oversupplied' in avoid_tooltip.lower() or 'always available' in avoid_tooltip.lower()
        finally:
            os.unlink(csv_filename)

    def test_dealer_summary_cards_include_tooltip_explanations(self):
        """Should include info icons with dealer-specific tooltip explanations."""
        from website.generate_website import generate_data_page
        
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Dealer Risk\n")
            f.write("Species A,🔥\n")
            csv_filename = f.name
        
        analysis_markdown = """## 🏪 Dealer Supply Risk Matrix (Top 10)

**Summary:** 3 species analyzed | 🔥 High Risk: 1 | ⚠️ Moderate Risk: 1 | ❌ Low Risk: 1
"""
        
        try:
            html = generate_data_page(PageConfig(
                title="Dealer Supply Risk",
                description="Test description",
                csv_filename=csv_filename,
                table_id="test-table",
                active_page="dealer",
                analysis_markdown=analysis_markdown
            ))
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Verify tooltips contain dealer-specific explanations
            tooltips = soup.find_all('span', class_='tooltip')
            assert len(tooltips) == 3
            
            # Check high risk tooltip
            high_risk_tooltip = tooltips[0].get_text()
            assert 'supply' in high_risk_tooltip.lower()
            assert 'risk' in high_risk_tooltip.lower() or 'lost sales' in high_risk_tooltip.lower()
            
            # Check moderate risk tooltip
            moderate_risk_tooltip = tooltips[1].get_text()
            assert 'moderate' in moderate_risk_tooltip.lower()
            assert 'supply' in moderate_risk_tooltip.lower()
            
            # Check low risk tooltip
            low_risk_tooltip = tooltips[2].get_text()
            assert 'healthy' in low_risk_tooltip.lower() or 'well-supplied' in low_risk_tooltip.lower()
        finally:
            os.unlink(csv_filename)



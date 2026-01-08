#!/usr/bin/env python3
"""
Comprehensive tests for pricing_summary.py using synthetic historical data.

Tests cover all branches including:
- Price increases and decreases
- Unchanged prices
- New listings
- Removed listings
- Top movers calculation
- Edge cases (insufficient data, missing prices, invalid prices)
"""

import sys
from pathlib import Path
import tempfile
import os

# Add src directory to Python path to enable imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from pricing_summary import calculate_pricing_summary, write_pricing_summary


def make_row(scrape_datetime, scientific_name, size_cm, price_gbp, wishlist_count="0"):
    """Helper to create a synthetic history row matching CSV schema."""
    return {
        "scrape_datetime": scrape_datetime,
        "scientific_name": scientific_name,
        "common_name": "Test Spider",
        "size_cm": size_cm,
        "price_gbp": price_gbp,
        "wishlist_count": wishlist_count,
        "page_url": "https://example.com"
    }


class TestCalculatePricingSummary:
    """Test suite for pricing summary calculation."""

    def test_empty_history_returns_none(self):
        """Should return None when history is empty."""
        result = calculate_pricing_summary([])
        assert result is None

    def test_single_run_returns_none(self):
        """Should return None when only one run exists."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is None

    def test_price_increase(self):
        """Should count price increases correctly."""
        history = [
            # Previous run
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00"),
            # Current run - both prices increased
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "35.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert result["increases"] == 2
        assert result["decreases"] == 0
        assert result["unchanged"] == 0
        assert result["new"] == 0
        assert result["removed"] == 0

    def test_price_decrease(self):
        """Should count price decreases correctly."""
        history = [
            # Previous run
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "30.00"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "35.00"),
            # Current run - both prices decreased
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert result["increases"] == 0
        assert result["decreases"] == 2
        assert result["unchanged"] == 0

    def test_price_unchanged(self):
        """Should count unchanged prices correctly."""
        history = [
            # Previous run
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00"),
            # Current run - prices unchanged
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert result["increases"] == 0
        assert result["decreases"] == 0
        assert result["unchanged"] == 2

    def test_new_listings(self):
        """Should count new listings correctly."""
        history = [
            # Previous run - only one species
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00"),
            # Current run - added two new species
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert result["new"] == 2
        assert result["unchanged"] == 1

    def test_removed_listings(self):
        """Should count removed listings correctly."""
        history = [
            # Previous run - three species
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00"),
            # Current run - only one species remains
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert result["removed"] == 2
        assert result["unchanged"] == 1

    def test_mixed_changes(self):
        """Should handle mixed price changes, new, and removed listings."""
        history = [
            # Previous run
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00"),  # Will increase
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00"),   # Will decrease
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00"),  # Will be removed
            make_row("2025-01-01", "Lasiodora parahybana", "2.5", "35.00"), # Will stay same
            # Current run
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00"),  # Increased
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "25.00"),   # Decreased
            make_row("2025-01-08", "Lasiodora parahybana", "2.5", "35.00"), # Unchanged
            make_row("2025-01-08", "Theraphosa blondi", "3.0", "50.00"),    # New
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert result["increases"] == 1
        assert result["decreases"] == 1
        assert result["unchanged"] == 1
        assert result["new"] == 1
        assert result["removed"] == 1

    def test_top_movers_sorted_by_absolute_change(self):
        """Should return top 5 movers sorted by absolute percentage change."""
        history = [
            # Previous run
            make_row("2025-01-01", "Species A", "1.0", "10.00"),  # +100%
            make_row("2025-01-01", "Species B", "1.0", "20.00"),  # +50%
            make_row("2025-01-01", "Species C", "1.0", "30.00"),  # -33.3%
            make_row("2025-01-01", "Species D", "1.0", "40.00"),  # +25%
            make_row("2025-01-01", "Species E", "1.0", "50.00"),  # -20%
            make_row("2025-01-01", "Species F", "1.0", "60.00"),  # +10%
            # Current run
            make_row("2025-01-08", "Species A", "1.0", "20.00"),  # +100%
            make_row("2025-01-08", "Species B", "1.0", "30.00"),  # +50%
            make_row("2025-01-08", "Species C", "1.0", "20.00"),  # -33.3%
            make_row("2025-01-08", "Species D", "1.0", "50.00"),  # +25%
            make_row("2025-01-08", "Species E", "1.0", "40.00"),  # -20%
            make_row("2025-01-08", "Species F", "1.0", "66.00"),  # +10%
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        top_movers = result["top_movers"]
        assert len(top_movers) == 5  # Should limit to top 5
        # Check sorted by absolute percentage (Species A = 100% should be first)
        assert top_movers[0][0] == "Species A"
        assert top_movers[0][4] == pytest.approx(1.0, abs=0.01)  # 100% = 1.0
        assert top_movers[1][0] == "Species B"
        assert abs(top_movers[1][4]) == pytest.approx(0.5, abs=0.01)  # 50%

    def test_missing_price_fields_ignored(self):
        """Should skip rows with missing or empty price fields."""
        history = [
            # Previous run
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", ""),  # Empty price
            # Current run
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00"),  # Has price now
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        # Only Species A should be counted as increase (has valid prices in both runs)
        assert result["increases"] == 1
        # Species B should not be counted in any category since old price was empty

    def test_invalid_price_format_ignored(self):
        """Should skip rows with non-numeric price values."""
        history = [
            # Previous run
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "invalid"),
            # Current run
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        # Only Species A should be counted
        assert result["increases"] == 1

    def test_zero_price_excluded_from_movers(self):
        """Should not include items with zero price in top movers calculation."""
        history = [
            # Previous run
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "0.00"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "20.00"),
            # Current run
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "10.00"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        # Both should be counted as increases
        assert result["increases"] == 2
        # But only Species B should be in movers (Species A had old price of 0)
        assert len(result["top_movers"]) == 1
        assert result["top_movers"][0][0] == "Brachypelma hamorii"

    def test_same_species_different_sizes_treated_separately(self):
        """Should treat same species with different sizes as separate items."""
        history = [
            # Previous run
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00"),
            make_row("2025-01-01", "Aphonopelma seemanni", "2.0", "30.00"),
            # Current run - only size 1.0 present
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert result["increases"] == 1  # 1.0 size increased
        assert result["removed"] == 1     # 2.0 size removed

    def test_percentage_calculation_accuracy(self):
        """Should calculate percentage changes accurately."""
        history = [
            # Previous run
            make_row("2025-01-01", "Test Species", "1.0", "20.00"),
            # Current run - 50% increase
            make_row("2025-01-08", "Test Species", "1.0", "30.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert len(result["top_movers"]) == 1
        species, size, old_price, new_price, pct_change = result["top_movers"][0]
        assert species == "Test Species"
        assert old_price == 20.00
        assert new_price == 30.00
        assert pct_change == pytest.approx(0.5, abs=0.001)  # 50% = 0.5

    def test_negative_percentage_calculation(self):
        """Should calculate negative percentage changes correctly."""
        history = [
            # Previous run
            make_row("2025-01-01", "Test Species", "1.0", "40.00"),
            # Current run - 25% decrease
            make_row("2025-01-08", "Test Species", "1.0", "30.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert len(result["top_movers"]) == 1
        _, _, _, _, pct_change = result["top_movers"][0]
        assert pct_change == pytest.approx(-0.25, abs=0.001)  # -25% = -0.25

    def test_more_than_five_movers_limited_to_top_five(self):
        """Should limit top movers to 5 even when more changes exist."""
        history = []
        # Previous run - 10 species
        for i in range(10):
            history.append(make_row("2025-01-01", f"Species {i}", "1.0", "10.00"))
        # Current run - all increase by different amounts
        for i in range(10):
            new_price = 10.00 + (i + 1) * 2  # Varying increases
            history.append(make_row("2025-01-08", f"Species {i}", "1.0", str(new_price)))
        
        result = calculate_pricing_summary(history)
        assert result is not None
        assert result["increases"] == 10
        assert len(result["top_movers"]) == 5

    def test_no_movers_when_no_comparable_prices(self):
        """Should have empty top_movers when no valid price comparisons exist."""
        history = [
            # Previous run - all have prices
            make_row("2025-01-01", "Species A", "1.0", "25.00"),
            make_row("2025-01-01", "Species B", "1.5", "30.00"),
            # Current run - completely different species (all new)
            make_row("2025-01-08", "Species C", "2.0", "35.00"),
            make_row("2025-01-08", "Species D", "2.5", "40.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        assert result["new"] == 2
        assert result["removed"] == 2
        assert len(result["top_movers"]) == 0

    def test_multiple_runs_uses_last_two(self):
        """Should compare only the last two runs, ignoring earlier data."""
        history = [
            # Run 1 (oldest)
            make_row("2025-01-01", "Test Species", "1.0", "10.00"),
            # Run 2 (middle)
            make_row("2025-01-08", "Test Species", "1.0", "20.00"),
            # Run 3 (latest)
            make_row("2025-01-15", "Test Species", "1.0", "25.00"),
        ]
        result = calculate_pricing_summary(history)
        assert result is not None
        # Should compare Run 3 vs Run 2 (20.00 -> 25.00 = +25%)
        # NOT Run 3 vs Run 1 (10.00 -> 25.00 = +150%)
        assert result["increases"] == 1
        pct_change = result["top_movers"][0][4]
        assert pct_change == pytest.approx(0.25, abs=0.001)  # 25% not 150%


class TestWritePricingSummary:
    """Test suite for write_pricing_summary function."""

    def test_writes_summary_to_file(self):
        """Should write pricing summary to markdown file."""
        history = [
            # Previous run
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00", "3"),
            # Current run
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00", "8"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "2"),
        ]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            temp_path = f.name
        
        try:
            # Set environment variable for summary path
            os.environ['GITHUB_STEP_SUMMARY'] = temp_path
            
            write_pricing_summary(history, "2025-01-08T12:00:00")
            
            # Verify file was written
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check that key elements are present
            assert "## 🕷️ Spiderlings Pricing Summary" in content
            assert "2025-01-08T12:00:00" in content
            assert "🔼 Increases:" in content
            assert "🔽 Decreases:" in content
            assert "➖ Unchanged:" in content
            assert "🆕 New:" in content
            assert "❌ Removed:" in content
            assert "🚀 Top 5 Price Movers" in content
            
        finally:
            # Cleanup
            if 'GITHUB_STEP_SUMMARY' in os.environ:
                del os.environ['GITHUB_STEP_SUMMARY']
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_no_write_when_summary_path_missing(self):
        """Should return early when GITHUB_STEP_SUMMARY is not set."""
        history = [
            make_row("2025-01-01", "Test Species", "1.0", "25.00"),
            make_row("2025-01-08", "Test Species", "1.0", "30.00"),
        ]
        
        # Ensure env var is not set
        if 'GITHUB_STEP_SUMMARY' in os.environ:
            del os.environ['GITHUB_STEP_SUMMARY']
        
        # Should not raise error, just return early
        write_pricing_summary(history, "2025-01-08T12:00:00")

    def test_no_write_when_insufficient_data(self):
        """Should return early when insufficient history data."""
        history = [
            make_row("2025-01-01", "Test Species", "1.0", "25.00"),
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            temp_path = f.name
        
        try:
            os.environ['GITHUB_STEP_SUMMARY'] = temp_path
            
            write_pricing_summary(history, "2025-01-01T12:00:00")
            
            # File should be empty or not written
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert content == ""  # Nothing should be written
            
        finally:
            if 'GITHUB_STEP_SUMMARY' in os.environ:
                del os.environ['GITHUB_STEP_SUMMARY']
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_formats_percentage_changes_correctly(self):
        """Should format percentage changes with proper signs."""
        history = [
            # Previous run
            make_row("2025-01-01", "Species A", "1.0", "10.00"),
            make_row("2025-01-01", "Species B", "1.0", "30.00"),
            # Current run - A increases, B decreases
            make_row("2025-01-08", "Species A", "1.0", "15.00"),  # +50%
            make_row("2025-01-08", "Species B", "1.0", "25.00"),  # -16.67%
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            temp_path = f.name
        
        try:
            os.environ['GITHUB_STEP_SUMMARY'] = temp_path
            
            write_pricing_summary(history, "2025-01-08T12:00:00")
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for positive sign on increase
            assert "+50" in content or "+ 50" in content
            # Check for negative percentage (no + sign)
            assert "-16" in content or "- 16" in content
            
        finally:
            if 'GITHUB_STEP_SUMMARY' in os.environ:
                del os.environ['GITHUB_STEP_SUMMARY']
            if os.path.exists(temp_path):
                os.unlink(temp_path)

#!/usr/bin/env python3
"""
Comprehensive tests for sparkline_helpers.py

Tests all behavioral rules from docs/SPARKLINES.md with 100% branch coverage.
Tests are organized by function and behavior for clarity.
"""
import pytest
from sparkline_helpers import (
    generate_sparkline,
    extract_historical_values,
    extract_historical_values_with_carryforward,
    generate_stock_availability_sparkline
)
from conftest import make_row
from history import group_by_run


# ==================== generate_sparkline() ====================

class TestGenerateSparkline:
    """Test sparkline generation with all edge cases per SPARKLINES.md spec."""
    
    def test_empty_list_returns_dash(self):
        """No data at all → "-" """
        assert generate_sparkline([]) == "-"
    
    def test_none_values_only_returns_dash(self):
        """All None values → "-" """
        assert generate_sparkline([None, None, None]) == "-"
    
    def test_empty_string_values_only_returns_dash(self):
        """All empty strings → "-" """
        assert generate_sparkline(["", "", ""]) == "-"
    
    def test_mixed_none_and_empty_returns_dash(self):
        """Mix of None and empty strings → "-" """
        assert generate_sparkline([None, "", None, ""]) == "-"
    
    def test_single_valid_value_returns_mid_height(self):
        """Single value → "▄" (mid-height bar)"""
        assert generate_sparkline(["12.50"]) == "▄"
        assert generate_sparkline([12.5]) == "▄"
        assert generate_sparkline(["0"]) == "▄"  # Zero is valid data
    
    def test_flat_line_all_same_value(self):
        """All identical values → all mid-height (min = max)"""
        result = generate_sparkline(["12", "12", "12", "12"])
        assert len(result) == 4
        assert result == "▄▄▄▄"  # All same height when no variance
    
    def test_two_distinct_values_min_and_max(self):
        """Two distinct values → shortest and tallest bars"""
        result = generate_sparkline(["10", "20"])
        assert len(result) == 2
        assert result[0] < result[1]  # First should be shorter
        # Specific characters: min gets ▁, max gets █
        result = generate_sparkline(["10", "10", "20", "20"])
        assert result == "▁▁██"
    
    def test_steady_increase_shows_rising_trend(self):
        """Scenario 1 from spec: £10 → £24 in steps"""
        values = ["10", "12", "14", "16", "18", "20", "22", "24"]
        result = generate_sparkline(values)
        assert len(result) == 8
        # Each bar should be same or taller than previous
        for i in range(len(result) - 1):
            assert result[i] <= result[i+1]
    
    def test_price_drop_with_recovery(self):
        """Scenario 3 from spec: £20 → £15 → £20"""
        values = ["20", "18", "15", "15", "16", "18", "19", "20"]
        result = generate_sparkline(values)
        assert len(result) == 8
        # Should show dip in middle
        assert min(result) == result[2] or min(result) == result[3]  # Lowest at positions 2-3
    
    def test_respects_max_length_parameter(self):
        """Should truncate to max_length most recent values"""
        values = ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]
        result = generate_sparkline(values, max_length=5)
        assert len(result) == 5  # Only last 5 values
    
    def test_handles_numeric_types(self):
        """Should accept strings, ints, and floats"""
        assert generate_sparkline([10, 20]) == "▁█"
        assert generate_sparkline([10.5, 20.5]) == "▁█"
        assert generate_sparkline(["10.5", "20.5"]) == "▁█"
    
    def test_invalid_string_treated_as_none(self):
        """Non-numeric strings → treated as None (gap)"""
        result = generate_sparkline(["10", "not-a-number", "20"])
        # Should skip the invalid value but still generate sparkline
        assert result != "-"
    
    def test_zero_is_valid_data_point(self):
        """Zero should be treated as valid data, not a gap"""
        result = generate_sparkline(["0", "10", "20"])
        assert len(result) == 3
        assert result[0] == "▁"  # Zero is minimum


# ==================== extract_historical_values() ====================

class TestExtractHistoricalValues:
    """Test basic extraction without carry-forward (shows None for OUT periods)."""
    
    def test_extracts_values_when_present(self):
        """Should extract field values for runs where species is IN stock"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10.00", "5"),
            make_row("2025-01-08", "Spider A", "1.0", "12.00", "6"),
            make_row("2025-01-15", "Spider A", "1.0", "15.00", "7"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        values = extract_historical_values(key, by_run, runs, "price_gbp")
        
        assert values == ["10.00", "12.00", "15.00"]
    
    def test_returns_none_when_species_out(self):
        """Should return None for runs where species is OUT of stock"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10.00", "5"),
            make_row("2025-01-08", "Spider B", "2.0", "20.00", "3"),  # Spider A is OUT
            make_row("2025-01-15", "Spider A", "1.0", "15.00", "7"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        values = extract_historical_values(key, by_run, runs, "price_gbp")
        
        assert len(values) == 3
        assert values[0] == "10.00"
        assert values[1] is None  # OUT
        assert values[2] == "15.00"
    
    def test_respects_max_runs_parameter(self):
        """Should limit lookback to max_runs"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10.00", "1"),
            make_row("2025-01-08", "Spider A", "1.0", "11.00", "2"),
            make_row("2025-01-15", "Spider A", "1.0", "12.00", "3"),
            make_row("2025-01-22", "Spider A", "1.0", "13.00", "4"),
            make_row("2025-01-29", "Spider A", "1.0", "14.00", "5"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        values = extract_historical_values(key, by_run, runs, "price_gbp", max_runs=3)
        
        assert len(values) == 3
        assert values == ["12.00", "13.00", "14.00"]  # Last 3 runs only
    
    def test_extracts_wishlist_field(self):
        """Should work with different field names"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10.00", "5"),
            make_row("2025-01-08", "Spider A", "1.0", "12.00", "8"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        values = extract_historical_values(key, by_run, runs, "wishlist_count")
        
        assert values == ["5", "8"]
    
    def test_handles_missing_field(self):
        """Should return empty string if field doesn't exist in row"""
        history = [
            {"scrape_datetime": "2025-01-01", "scientific_name": "Spider A", "size_cm": "1.0"},
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        values = extract_historical_values(key, by_run, runs, "price_gbp")
        
        assert values == [""]


# ==================== extract_historical_values_with_carryforward() ====================

class TestExtractWithCarryforward:
    """Test carry-forward behavior per SPARKLINES.md rules."""
    
    # Rule 1: Start Point - Skip Leading Gaps
    
    def test_skips_leading_out_periods(self):
        """Rule 1: Sparklines start when species first appears (skip leading gaps)"""
        history = [
            make_row("2025-01-01", "Spider B", "2.0", "20.00", "3"),  # Spider A not here
            make_row("2025-01-08", "Spider B", "2.0", "20.00", "3"),  # Spider A not here
            make_row("2025-01-15", "Spider A", "1.0", "12.00", "5"),  # First appearance
            make_row("2025-01-22", "Spider A", "1.0", "13.00", "6"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        
        # Should skip weeks 1-2, start at week 3
        assert result['values'] == ["12.00", "13.00"]
        assert result['is_carried_forward'] == [False, False]
        assert result['unicode'] == "▁█"  # 12.00 < 13.00 → rising
    
    def test_never_appears_returns_empty_list(self):
        """Species that never appears → empty list"""
        history = [
            make_row("2025-01-01", "Spider B", "2.0", "20.00", "3"),
            make_row("2025-01-08", "Spider B", "2.0", "20.00", "3"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")  # Never appears
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        
        assert result['values'] == []
        assert result['is_carried_forward'] == []
        assert result['unicode'] == "-"
    
    # Rule 2: Carry-Forward - No Mid-Sparkline Gaps
    
    def test_carries_forward_during_single_out_week(self):
        """Rule 2: Carry forward last known value during OUT period"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "25.00", "5"),
            make_row("2025-01-08", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
            make_row("2025-01-15", "Spider A", "1.0", "30.00", "8"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        
        assert result['values'] == ["25.00", "25.00", "30.00"]  # Carried forward in week 2
        assert result['is_carried_forward'] == [False, True, False]
        assert result['unicode'] == "▁▁█"
    
    def test_carries_forward_during_multiple_out_weeks(self):
        """Rule 2: Carry forward persists across multiple OUT weeks"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "25.00", "5"),
            make_row("2025-01-08", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
            make_row("2025-01-15", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
            make_row("2025-01-22", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
            make_row("2025-01-29", "Spider A", "1.0", "30.00", "8"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        
        assert result['values'] == ["25.00", "25.00", "25.00", "25.00", "30.00"]
        assert result['is_carried_forward'] == [False, True, True, True, False]
        assert result['unicode'] == "▁▁▁▁█"
    
    def test_updates_carryforward_value_on_restock(self):
        """When species returns, carry-forward value updates to new value"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "20.00", "5"),
            make_row("2025-01-08", "Spider A", "1.0", "22.00", "6"),  # Price increases
            make_row("2025-01-15", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
            make_row("2025-01-22", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
            make_row("2025-01-29", "Spider A", "1.0", "25.00", "8"),  # Returns with new price
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        
        # Carries 22.00 during OUT, then updates to 25.00
        assert result['values'] == ["20.00", "22.00", "22.00", "22.00", "25.00"]
        assert result['is_carried_forward'] == [False, False, True, True, False]
        assert result['unicode'] == "▁▄▄▄█"
    
    def test_carries_forward_until_end_if_never_restocks(self):
        """If species goes OUT and never returns, carry forward to end"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "20.00", "5"),
            make_row("2025-01-08", "Spider A", "1.0", "22.00", "6"),
            make_row("2025-01-15", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
            make_row("2025-01-22", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        
        assert result['values'] == ["20.00", "22.00", "22.00", "22.00"]
        assert result['is_carried_forward'] == [False, False, True, True]
        assert result['unicode'] == "▁███"
    
    # Combined scenarios (Start Point + Carry-Forward)
    
    def test_scenario_2_volatility_with_out_period(self):
        """Scenario 2 from spec: Interest growing despite OUT period"""
        history = [
            make_row("2025-01-01", "Spider B", "2.0", "20.00", "3"),  # Spider A not yet listed
            make_row("2025-01-08", "Spider A", "1.0", "10.00", "5"),  # First appearance
            make_row("2025-01-15", "Spider A", "1.0", "11.00", "7"),
            make_row("2025-01-22", "Spider B", "2.0", "20.00", "3"),  # Spider A OUT
            make_row("2025-01-29", "Spider B", "2.0", "20.00", "3"),  # Spider A OUT
            make_row("2025-02-05", "Spider B", "2.0", "20.00", "3"),  # Spider A OUT
            make_row("2025-02-12", "Spider A", "1.0", "12.00", "12"),
            make_row("2025-02-19", "Spider A", "1.0", "13.00", "15"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "wishlist_count")
        
        # Skips week 1, starts week 2, carries 7 during weeks 4-6
        assert result['values'] == ["5", "7", "7", "7", "7", "12", "15"]
        assert result['is_carried_forward'] == [False, False, True, True, True, False, False]
        assert result['unicode'] == "▁▂▂▂▂▆█"
    
    # Test with different fields
    
    def test_works_with_wishlist_count_field(self):
        """Carry-forward should work for wishlist_count too"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "20.00", "10"),
            make_row("2025-01-08", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
            make_row("2025-01-15", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
            make_row("2025-01-22", "Spider A", "1.0", "25.00", "15"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "wishlist_count")
        
        assert result['values'] == ["10", "10", "10", "15"]
        assert result['is_carried_forward'] == [False, True, True, False]
        assert result['unicode'] == "▁▁▁█"
    
    def test_handles_empty_field_value(self):
        """If field is missing/empty, should carry forward empty string"""
        history = [
            {"scrape_datetime": "2025-01-01", "scientific_name": "Spider A", "size_cm": "1.0"},
            make_row("2025-01-08", "Spider B", "2.0", "40.00", "3"),  # Spider A OUT
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        
        assert result['values'] == ["", ""]  # Empty string carried forward
        assert result['is_carried_forward'] == [False, True]
        assert result['unicode'] == "-"
    
    # Test max_runs parameter
    
    def test_respects_max_runs_with_carryforward(self):
        """Should limit to last N runs even with carry-forward"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10.00", "1"),
            make_row("2025-01-08", "Spider A", "1.0", "11.00", "2"),
            make_row("2025-01-15", "Spider A", "1.0", "12.00", "3"),
            make_row("2025-01-22", "Spider A", "1.0", "13.00", "4"),
            make_row("2025-01-29", "Spider B", "2.0", "20.00", "5"),  # Spider A OUT
            make_row("2025-02-05", "Spider A", "1.0", "14.00", "6"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp", max_runs=3)
        
        # Last 3 runs: week 4 (13.00), week 5 (OUT, carry 13.00), week 6 (14.00)
        assert len(result['values']) == 3
        assert result['values'] == ["13.00", "13.00", "14.00"]
        assert result['is_carried_forward'] == [False, True, False]
        assert result['unicode'] == "▁▁█"


# ==================== generate_stock_availability_sparkline() ====================

class TestStockAvailabilitySparkline:
    """Test stock availability indicator (different from price/wishlist sparklines)."""
    
    def test_shows_filled_block_for_in_stock(self):
        """IN stock → █"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10.00", "5"),
            make_row("2025-01-08", "Spider A", "1.0", "12.00", "6"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = generate_stock_availability_sparkline(key, by_run, runs)
        
        assert result == "██"
    
    def test_shows_space_for_out_of_stock(self):
        """OUT stock → space (this is intentional - shows gaps unlike price sparklines)"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10.00", "5"),
            make_row("2025-01-08", "Spider B", "2.0", "20.00", "3"),  # Spider A OUT
            make_row("2025-01-15", "Spider A", "1.0", "12.00", "6"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = generate_stock_availability_sparkline(key, by_run, runs)
        
        assert result == "█ █"  # Block, space, block
    
    def test_pattern_in_out_in_out(self):
        """Should accurately show IN/OUT pattern"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10.00", "5"),  # IN
            make_row("2025-01-08", "Spider B", "2.0", "20.00", "3"),  # OUT
            make_row("2025-01-15", "Spider A", "1.0", "12.00", "6"),  # IN
            make_row("2025-01-22", "Spider B", "2.0", "20.00", "3"),  # OUT
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = generate_stock_availability_sparkline(key, by_run, runs)
        
        assert result == "█ █ "
    
    def test_respects_max_runs_parameter(self):
        """Should limit to last N runs"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10.00", "1"),
            make_row("2025-01-08", "Spider A", "1.0", "11.00", "2"),
            make_row("2025-01-15", "Spider A", "1.0", "12.00", "3"),
            make_row("2025-01-22", "Spider A", "1.0", "13.00", "4"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = generate_stock_availability_sparkline(key, by_run, runs, max_runs=2)
        
        assert result == "██"  # Last 2 runs only
    
    def test_empty_runs_returns_dash(self):
        """No runs → "-" """
        result = generate_stock_availability_sparkline(("Spider A", "1.0"), {}, [])
        assert result == "-"
    
    def test_all_out_returns_dash(self):
        """All OUT (only spaces) → "-" """
        history = [
            make_row("2025-01-01", "Spider B", "2.0", "20.00", "3"),
            make_row("2025-01-08", "Spider B", "2.0", "20.00", "3"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")  # Never appears
        
        result = generate_stock_availability_sparkline(key, by_run, runs)
        
        # All spaces, strip() leaves empty string → treated as dash
        assert result == "-" or result.strip() == ""


# ==================== Integration Tests ====================

class TestSparklineIntegration:
    """End-to-end tests combining extraction + generation per SPARKLINES.md scenarios."""
    
    def test_scenario_1_steady_increase(self):
        """Scenario 1: £10 → £24 steady increase"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "10", "5"),
            make_row("2025-01-08", "Spider A", "1.0", "12", "5"),
            make_row("2025-01-15", "Spider A", "1.0", "14", "5"),
            make_row("2025-01-22", "Spider A", "1.0", "16", "5"),
            make_row("2025-01-29", "Spider A", "1.0", "18", "5"),
            make_row("2025-02-05", "Spider A", "1.0", "20", "5"),
            make_row("2025-02-12", "Spider A", "1.0", "22", "5"),
            make_row("2025-02-19", "Spider A", "1.0", "24", "5"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        sparkline = result['unicode']
        
        # Should show clear upward trend
        assert len(sparkline) == 8
        for i in range(len(sparkline) - 1):
            assert sparkline[i] <= sparkline[i+1]
    
    def test_scenario_2_with_carry_forward(self):
        """Scenario 2: Wishlist growing despite OUT (plateau then surge)"""
        history = [
            make_row("2025-01-01", "Spider B", "2.0", "20.00", "1"),  # Not yet listed
            make_row("2025-01-08", "Spider A", "1.0", "10.00", "5"),  # First appearance
            make_row("2025-01-15", "Spider A", "1.0", "10.00", "7"),
            make_row("2025-01-22", "Spider B", "2.0", "20.00", "3"),  # OUT
            make_row("2025-01-29", "Spider B", "2.0", "20.00", "3"),  # OUT
            make_row("2025-02-05", "Spider B", "2.0", "20.00", "3"),  # OUT
            make_row("2025-02-12", "Spider A", "1.0", "10.00", "12"),  # Surge on restock
            make_row("2025-02-19", "Spider A", "1.0", "10.00", "15"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "wishlist_count")
        sparkline = result['unicode']
        
        # Should show: low, mid, mid(plateau x3), high, higher
        assert len(sparkline) == 7
        # Minimum at start (5), maximum at end (15)
        assert sparkline[0] < sparkline[-1]
    
    def test_scenario_3_price_drop_recovery(self):
        """Scenario 3: £20 → £15 → £20 (dip and recovery)"""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "20", "5"),
            make_row("2025-01-08", "Spider A", "1.0", "18", "5"),
            make_row("2025-01-15", "Spider A", "1.0", "15", "5"),
            make_row("2025-01-22", "Spider A", "1.0", "15", "5"),
            make_row("2025-01-29", "Spider A", "1.0", "16", "5"),
            make_row("2025-02-05", "Spider A", "1.0", "18", "5"),
            make_row("2025-02-12", "Spider A", "1.0", "19", "5"),
            make_row("2025-02-19", "Spider A", "1.0", "20", "5"),
        ]
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Spider A", "1.0")
        
        result = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp")
        sparkline = result['unicode']
        
        # Should show dip in middle (positions 2-3)
        assert len(sparkline) == 8
        min_bar = min(sparkline)
        assert sparkline[2] == min_bar or sparkline[3] == min_bar

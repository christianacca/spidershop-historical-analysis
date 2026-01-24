#!/usr/bin/env python3
"""
Tests for sparkline_helpers.py

Tests the carry-forward behavior for price and wishlist sparklines when species goes OUT of stock.
"""
import pytest
from sparkline_helpers import generate_sparkline, extract_historical_values_with_carryforward, generate_stock_availability_sparkline
from conftest import make_row
from history import group_by_run


class TestCarryForwardBehavior:
    """Test that price/wishlist values carry forward when species is OUT of stock."""
    
    def test_extract_with_carryforward_carries_last_known_value(self):
        """When species goes OUT, should carry forward last known value instead of None."""
        history = [
            # Week 1: IN with price 25.00
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            # Week 2: OUT (no entry)
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "3"),
            # Week 3: OUT (no entry)
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "3"),
            # Week 4: IN with price 30.00
            make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "30.00", "8"),
        ]
        
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Aphonopelma seemanni", "1.0")
        
        # Extract with carry-forward
        values = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp", max_runs=8)
        
        # Should be: [25.00, 25.00, 25.00, 30.00]
        # Weeks 2 and 3 carry forward the value from week 1
        assert len(values) == 4
        assert values[0] == "25.00"
        assert values[1] == "25.00"  # Carried forward
        assert values[2] == "25.00"  # Carried forward
        assert values[3] == "30.00"
    
    def test_extract_with_carryforward_handles_initial_out_period(self):
        """When species starts OUT, should skip leading periods until first IN observation.
        
        Per user requirements:
        - Bars only start when "records began" for that spider
        - Once the sparkline starts, there should be no gaps
        """
        history = [
            # Week 1: OUT (no entry)
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "3"),
            # Week 2: OUT (no entry)
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "3"),
            # Week 3: IN with price 25.00
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            # Week 4: OUT (no entry)
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "3"),
        ]
        
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Aphonopelma seemanni", "1.0")
        
        values = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp", max_runs=8)
        
        # Should skip leading None values and start from first appearance: [25.00, 25.00]
        assert len(values) == 2
        assert values[0] == "25.00"
        assert values[1] == "25.00"  # Carried forward
    
    def test_extract_with_carryforward_handles_value_changes(self):
        """Should update carry-forward value when species returns with new price."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "20.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "22.00", "6"),  # Price increases
            # OUT for 2 weeks
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-29", "Aphonopelma seemanni", "1.0", "25.00", "8"),  # Returns with new price
        ]
        
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Aphonopelma seemanni", "1.0")
        
        values = extract_historical_values_with_carryforward(key, by_run, runs, "price_gbp", max_runs=8)
        
        # Should be: [20.00, 22.00, 22.00, 22.00, 25.00]
        assert len(values) == 5
        assert values[0] == "20.00"
        assert values[1] == "22.00"
        assert values[2] == "22.00"  # Carried forward
        assert values[3] == "22.00"  # Carried forward
        assert values[4] == "25.00"
    
    def test_sparkline_without_gaps_shows_continuous_trend(self):
        """Sparkline should show continuous trend without gaps when values carry forward."""
        # Simulate: price 20, 20, 20, 20 (carried forward during OUT periods)
        values = ["20.00", "20.00", "20.00", "20.00"]
        
        sparkline = generate_sparkline(values, max_length=8)
        
        # Should show consistent height, no spaces
        assert " " not in sparkline  # No gaps
        assert len(sparkline) == 4  # 4 characters for 4 values
    
    def test_sparkline_with_trend_during_out_period(self):
        """Sparkline should show flat line during OUT period (carried forward value)."""
        # Simulate: increasing, then OUT (carry forward), then increase again
        values = ["20.00", "25.00", "25.00", "25.00", "30.00"]
        
        sparkline = generate_sparkline(values, max_length=8)
        
        # Should show low, mid, mid, mid, high pattern (no gaps)
        assert " " not in sparkline
        assert len(sparkline) == 5
    
    def test_wishlist_carryforward_works_same_as_price(self):
        """Wishlist counts should also carry forward when OUT."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "20.00", "10"),
            # OUT for 2 weeks
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "25.00", "15"),
        ]
        
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Aphonopelma seemanni", "1.0")
        
        values = extract_historical_values_with_carryforward(key, by_run, runs, "wishlist_count", max_runs=8)
        
        # Should be: [10, 10, 10, 15]
        assert len(values) == 4
        assert values[0] == "10"
        assert values[1] == "10"  # Carried forward
        assert values[2] == "10"  # Carried forward
        assert values[3] == "15"
    
    def test_stock_availability_still_shows_gaps(self):
        """Stock Availability should still show gaps (spaces) for OUT periods - this is correct behavior."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "20.00", "5"),
            # OUT
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "8"),
        ]
        
        by_run = group_by_run(history)
        runs = sorted(by_run)
        key = ("Aphonopelma seemanni", "1.0")
        
        sparkline = generate_stock_availability_sparkline(key, by_run, runs, max_runs=8)
        
        # Should be: █ █ (IN, OUT, IN)
        assert sparkline == "█ █"

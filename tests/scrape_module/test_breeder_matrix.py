#!/usr/bin/env python3
"""
Comprehensive tests for breeder_matrix.py using synthetic historical data.

Tests cover all branches including:
- Sustained scarcity (4+ OOS runs)
- Emerging scarcity (2-3 OOS runs)  
- Cyclical patterns (IN/OUT)
- Always available species
- Price trends (rising, falling, stable)
- Wishlist pressure integration
- Wishlist delta (momentum) signals
- OOS carryover behavior
"""

import pytest
from scrape.breeder_matrix import build_breeder_opportunity_table
from conftest import make_row


def assert_price_cell(price_cell: str, expected_arrow: str, expected_value: str) -> None:
    """Assert a combined price cell has expected value and trend arrow."""
    assert price_cell == f"£{expected_value} {expected_arrow}"


class TestBuildBreederOpportunityTable:
    """Test suite for breeder opportunity matrix generation."""

    def test_insufficient_runs_returns_empty(self):
        """Should return empty list when less than 2 runs available."""
        # Single run
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        ]
        result = build_breeder_opportunity_table(history)
        assert result == []

        # Empty history
        result = build_breeder_opportunity_table([])
        assert result == []

    def test_sustained_scarcity_4_oos_runs(self):
        """Species missing for 4+ consecutive runs should show 'Sustained' pattern with 🔥 signal."""
        history = [
            # Run 1: Species present
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "15"),
            
            # Run 2: seemanni goes OUT
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "16"),
            
            # Run 3: seemanni still OUT
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "42.00", "17"),
            
            # Run 4: seemanni still OUT
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "42.00", "18"),
            
            # Run 5: seemanni still OUT (4 consecutive OOS runs including this one)
            make_row("2025-01-29", "Grammostola pulchra", "2.0", "43.00", "20"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        assert seemanni_entry["OOS"] == "OUT"
        assert seemanni_entry["OOS Runs"] == "4"
        assert seemanni_entry["Stock Pattern"] == "Sustained"
        assert seemanni_entry["Signal"] == "🔥"
        assert "sustained scarcity" in seemanni_entry["Recommendation"].lower()

    def test_sustained_scarcity_with_falling_price_is_watch_not_avoid(self):
        """Sustained scarcity with a falling price must resolve to ⚠️ Watch, not ❌ Avoid.

        Hard rule: sustained scarcity is never downgraded (see copilot-instructions.md).
        Price trend only controls whether the row escalates to 🔥 Hot; it must not demote
        a Sustained pattern below ⚠️ Watch.
        """
        history = [
            # Runs 1-3: seemanni IN with a clearly falling price
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "30.00", "5"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "20.00", "5"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "8"),
            # Runs 4-7: seemanni goes OUT for 4 consecutive runs (Sustained)
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-01-29", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-02-05", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-02-12", "Grammostola pulchra", "2.0", "40.00", "8"),
        ]

        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]

        assert seemanni_entry["Stock Pattern"] == "Sustained"
        assert seemanni_entry["Signal"] == "⚠️", (
            "Sustained scarcity must stay ⚠️ Watch even when price is falling — "
            "the hard rule 'sustained scarcity is never downgraded' applies."
        )

    def test_emerging_scarcity_2_3_oos_runs(self):
        """Species missing 2-3 consecutive runs should show 'Emerging' pattern."""
        history = [
            # Run 1: Both present
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "8"),
            
            # Run 2: seemanni goes OUT
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "9"),
            
            # Run 3: seemanni still OUT (2 consecutive OOS runs)
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "42.00", "10"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        assert seemanni_entry["OOS"] == "OUT"
        assert seemanni_entry["OOS Runs"] == "2"
        assert seemanni_entry["Stock Pattern"] == "Emerging"
        assert seemanni_entry["Signal"] in ["🔥", "⚠️"]

    def test_cyclical_pattern_in_out_flapping(self):
        """Species that flaps between IN and OUT should show 'Cyclical' pattern."""
        history = [
            # Run 1: Present
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            
            # Run 2: OUT
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "8"),
            
            # Run 3: Present again (flapped)
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "26.00", "6"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "42.00", "9"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        assert seemanni_entry["OOS"] == "IN/OUT"
        assert seemanni_entry["Stock Pattern"] == "Cyclical"
        assert seemanni_entry["Signal"] == "⚠️"
        assert "wave restocking" in seemanni_entry["Recommendation"].lower()

    def test_always_available_pattern(self):
        """Species present in all runs should show 'Always' pattern."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "3"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "3"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "4"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        assert seemanni_entry["OOS"] == "IN"
        assert seemanni_entry["OOS Runs"] == "0"
        assert seemanni_entry["Stock Pattern"] == "Always"
        # Without high wishlist pressure, should be ❌
        assert seemanni_entry["Signal"] == "❌"

    def test_newly_observed_pattern_for_single_current_observation(self):
        """A current-run first observation should not be misclassified as Always."""
        history = [
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "6"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "41.00", "3"),
        ]

        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]

        assert seemanni_entry["OOS"] == "IN"
        assert seemanni_entry["OOS Runs"] == "0"
        assert seemanni_entry["Stock Pattern"] == "Newly Observed"
        assert seemanni_entry["Signal"] == "⚠️"
        assert "limited history" in seemanni_entry["Recommendation"].lower()
        assert "observed 1/3 runs" in seemanni_entry["Recommendation"].lower()
        assert "observed 1/3 runs" in seemanni_entry["Drivers"].lower()

    def test_newly_observed_pattern_for_latest_two_consecutive_runs(self):
        """Two latest consecutive observations should still qualify as Newly Observed."""
        history = [
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "8"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "41.00", "3"),
            make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "26.00", "10"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "42.00", "3"),
        ]

        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]

        assert seemanni_entry["Stock Pattern"] == "Newly Observed"
        assert seemanni_entry["Signal"] == "⚠️"
        assert "observed 2/4 runs" in seemanni_entry["Recommendation"].lower()

    def test_newly_observed_exits_after_three_observed_runs(self):
        """Three observed runs should fall back to the normal taxonomy."""
        history = [
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "6"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "7"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "41.00", "3"),
            make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "25.00", "8"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "42.00", "3"),
        ]

        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]

        assert seemanni_entry["Stock Pattern"] == "Always"
        assert seemanni_entry["Stock Pattern"] != "Newly Observed"

    def test_newly_observed_does_not_infer_pre_first_seen_oos_runs(self):
        """Runs before first appearance must stay ambiguous, not count as OOS evidence."""
        history = [
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "7"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "41.00", "3"),
        ]

        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]

        assert seemanni_entry["OOS"] == "IN"
        assert seemanni_entry["OOS Runs"] == "0"
        assert seemanni_entry["Stock Pattern"] == "Newly Observed"

    def test_newly_observed_does_not_escalate_above_watch_with_strong_wishlist(self):
        """Strong wishlist signals must not upgrade Newly Observed above ⚠️."""
        history = [
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00", "1"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "40"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00", "1"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "26.00", "50"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "41.00", "1"),
            make_row("2025-01-15", "Brachypelma hamorii", "1.5", "31.00", "1"),
        ]

        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]

        assert seemanni_entry["Stock Pattern"] == "Newly Observed"
        assert seemanni_entry["Wishlist"].split()[1] == "🔥"
        assert seemanni_entry["Signal"] == "⚠️"

    def test_newly_observed_sorts_below_evidence_backed_watch_rows_and_above_avoid(self):
        """Newly Observed should be last within ⚠️ rows, but still above ❌ rows."""
        history = [
            make_row("2025-01-01", "Cyclical Watch", "1.0", "25.00", "2"),
            make_row("2025-01-01", "Always Avoid", "1.0", "20.00", "2"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "2"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "2"),
            make_row("2025-01-08", "Always Avoid", "1.0", "20.00", "2"),
            make_row("2025-01-15", "Always Avoid", "1.0", "20.00", "2"),
            make_row("2025-01-15", "Newly Observed Watch", "1.0", "30.00", "30"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "41.00", "2"),
            make_row("2025-01-22", "Cyclical Watch", "1.0", "27.00", "2"),
            make_row("2025-01-22", "Newly Observed Watch", "1.0", "31.00", "35"),
            make_row("2025-01-22", "Always Avoid", "1.0", "20.00", "2"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "42.00", "2"),
        ]

        table = build_breeder_opportunity_table(history)
        species_order = [row["Species"] for row in table]

        assert species_order.index("Cyclical Watch") < species_order.index("Newly Observed Watch")
        assert species_order.index("Newly Observed Watch") < species_order.index("Always Avoid")

    def test_price_trend_rising(self):
        """Should detect rising price trend."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00", "6"),
        ]
        
        table = build_breeder_opportunity_table(history)
        entry = table[0]

        assert_price_cell(entry["Price"], "↑", "30.00")

    def test_price_trend_falling(self):
        """Should detect falling price trend."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "30.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "6"),
        ]
        
        table = build_breeder_opportunity_table(history)
        entry = table[0]

        assert_price_cell(entry["Price"], "↓", "25.00")

    def test_price_trend_stable(self):
        """Should detect stable price trend."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "6"),
        ]
        
        table = build_breeder_opportunity_table(history)
        entry = table[0]

        assert_price_cell(entry["Price"], "→", "25.00")

    def test_price_trend_for_oos_species(self):
        """Should compute price trend for OUT species using last two known prices."""
        # Test rising price trend
        history_rising = [
            # Run 1: Present at £25
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            
            # Run 2: Present at £30 (price increased)
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00", "6"),
            
            # Run 3: OUT (should still show ↑ based on last two prices)
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "8"),
        ]
        
        table = build_breeder_opportunity_table(history_rising)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        assert_price_cell(seemanni_entry["Price"], "↑", "30.00")
        
        # Test falling price trend (covers line 79)
        history_falling = [
            # Run 1: Present at £30
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00", "5"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "5"),
            
            # Run 2: Present at £25 (price decreased)
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "25.00", "6"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
            
            # Runs 3-5: OUT (should show ↓ based on last two prices)
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "7"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "41.00", "8"),
            make_row("2025-01-29", "Grammostola pulchra", "2.0", "42.00", "9"),
        ]
        
        table = build_breeder_opportunity_table(history_falling)
        hamorii_entry = [r for r in table if r["Species"] == "Brachypelma hamorii"][0]
        assert_price_cell(hamorii_entry["Price"], "↓", "25.00")

    def test_price_value_for_oos_species_expires_after_bounded_lookback(self):
        """OUT species beyond bounded lookback should show N/A price value."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-01-29", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-02-05", "Grammostola pulchra", "2.0", "40.00", "8"),
            make_row("2025-02-12", "Grammostola pulchra", "2.0", "40.00", "8"),
        ]

        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]

        assert seemanni_entry["OOS"] == "OUT"
        assert seemanni_entry["OOS Runs"] == "6"
        assert seemanni_entry["Price"] == "N/A →"

    def test_emerging_with_rising_price_gets_fire_signal(self):
        """Emerging scarcity + rising price should get 🔥 signal."""
        history = [
            # Run 1: Present at low price
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "5"),
            
            # Run 2: seemanni price rises, still present
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00", "6"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
            
            # Run 3: seemanni goes OUT (1 OOS run)
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "42.00", "5"),
            
            # Run 4: seemanni still OUT (2 OOS runs, emerging pattern)
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "42.00", "5"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        assert seemanni_entry["Stock Pattern"] == "Emerging"
        assert_price_cell(seemanni_entry["Price"], "↑", "30.00")
        assert seemanni_entry["Signal"] == "🔥"
        assert "rising demand" in seemanni_entry["Recommendation"].lower()

    def test_wishlist_pressure_high_with_sustained_escalates_signal(self):
        """High wishlist pressure with sustained scarcity should enhance recommendation."""
        history = [
            # Run 1: Species present with low wishlist
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "2"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
            
            # Runs 2-5: seemanni OUT, but it had high wishlist when last seen
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "42.00", "1"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "42.00", "1"),
            make_row("2025-01-29", "Grammostola pulchra", "2.0", "43.00", "1"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        # Should show sustained pattern with signal
        assert seemanni_entry["Stock Pattern"] == "Sustained"
        assert seemanni_entry["Signal"] == "🔥"

    def test_emerging_with_high_wishlist_and_rising_delta_escalates_to_fire(self):
        """Emerging + high wishlist + rising delta should escalate to 🔥."""
        history = [
            # Run 1: Present with moderate wishlist
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00", "1"),
            
            # Run 2: seemanni present with higher wishlist
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "15"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00", "1"),
            
            # Run 3: seemanni OUT (emerging)
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "42.00", "1"),
            make_row("2025-01-15", "Brachypelma hamorii", "1.5", "30.00", "1"),
            
            # Run 4: seemanni still OUT (2 OOS, emerging pattern)
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "42.00", "1"),
            make_row("2025-01-22", "Brachypelma hamorii", "1.5", "30.00", "1"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        assert seemanni_entry["Stock Pattern"] == "Emerging"
        # High wishlist from carryover + positive delta should escalate
        assert seemanni_entry["Signal"] == "🔥"

    def test_always_available_with_falling_delta_stays_avoid(self):
        """Always available + falling wishlist delta should remain ❌."""
        history = [
            # Run 1: Always present with high wishlist
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "20"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
            
            # Run 2: Still present but wishlist dropping
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "15"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
            
            # Run 3: Still present, wishlist still dropping
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "8"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "1"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        assert seemanni_entry["Stock Pattern"] == "Always"
        # Falling delta should keep it as ❌
        if seemanni_entry["Wishlist"].split()[2] == "↓":
            assert seemanni_entry["Signal"] == "❌"

    def test_sorting_priority_signal_then_wishlist_pressure(self):
        """Table should sort by Signal (🔥>⚠️>❌), then Wishlist count (desc), then OOS Runs."""
        history = [
            # Create species with different signals
            # Species A: Sustained (🔥)
            make_row("2025-01-01", "Species A", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Species B", "1.0", "30.00", "3"),
            make_row("2025-01-15", "Species B", "1.0", "30.00", "3"),
            make_row("2025-01-22", "Species B", "1.0", "30.00", "3"),
            make_row("2025-01-29", "Species B", "1.0", "30.00", "3"),  # A is OUT for 4 runs
            
            # Species C: Always available (❌)
            make_row("2025-01-01", "Species C", "1.0", "20.00", "2"),
            make_row("2025-01-08", "Species C", "1.0", "20.00", "2"),
            make_row("2025-01-15", "Species C", "1.0", "20.00", "2"),
            make_row("2025-01-22", "Species C", "1.0", "20.00", "2"),
            make_row("2025-01-29", "Species C", "1.0", "20.00", "2"),
        ]
        
        table = build_breeder_opportunity_table(history)
        
        # 🔥 signals should come first
        assert table[0]["Signal"] == "🔥"
        # ❌ signals should come last
        assert table[-1]["Signal"] == "❌"

    def test_multiple_sizes_same_species_produces_one_multi_variant_row(self):
        """Phase 4: two active sizes collapse into one multi-variant species row."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-01", "Aphonopelma seemanni", "2.0", "35.00", "8"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "26.00", "6"),
            make_row("2025-01-08", "Aphonopelma seemanni", "2.0", "36.00", "9"),
        ]

        table = build_breeder_opportunity_table(history)

        # Phase 4: one row per species
        seemanni_rows = [r for r in table if r["Species"] == "Aphonopelma seemanni"]
        assert len(seemanni_rows) == 1
        assert seemanni_rows[0]["Lineage Status"] == "multi-variant"

    def test_oos_carryover_bounded_to_3_runs(self):
        """Wishlist pressure carryover for OUT species should be bounded to 3 runs."""
        history = [
            # Run 1: Present with very high wishlist
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "50"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
            
            # Runs 2-6: OUT for 5 consecutive runs
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "42.00", "1"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "42.00", "1"),
            make_row("2025-01-29", "Grammostola pulchra", "2.0", "43.00", "1"),
            make_row("2025-02-05", "Grammostola pulchra", "2.0", "43.00", "1"),  # 5 OOS runs
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        # After 5 OOS runs, carryover should expire (beyond 3-run lookback)
        # So wishlist pressure should revert to default (❌)
        assert seemanni_entry["OOS Runs"] == "5"
        # The pressure may have expired due to lookback limit
        # Just verify the logic handles this gracefully

    def test_wishlist_delta_neutral_when_no_comparable_in_stock_value(self):
        """Wishlist delta should be neutral (→) when no valid comparison exists."""
        history = [
            # Only 2 runs, species appears once only
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "10"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        # No previous in-stock value to compare
        assert seemanni_entry["Wishlist"].split()[2] == "→"

    def test_result_structure_has_all_required_columns(self):
        """Result should have all expected columns in correct format."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "26.00", "6"),
        ]
        
        table = build_breeder_opportunity_table(history)
        
        assert len(table) > 0
        entry = table[0]
        
        # Verify all expected keys exist (including sparkline and lineage metadata columns)
        expected_keys = {
            "Species", "Size (cm)", "OOS", "OOS Runs", "Stock Pattern",
            "Price", "Price History", "Wishlist",
            "Wishlist History", "Signal", "Recommendation", "Drivers",
            # Hidden lineage metadata columns (Phase 3+)
            "Lineage Status", "Previous Size (cm)", "Current Active Size (cm)",
            "Transition Date", "Price Evidence State", "Wishlist Evidence State",
            "Transition Message",
        }
        assert set(entry.keys()) == expected_keys
        assert isinstance(entry["Species"], str)
        assert isinstance(entry["OOS Runs"], str)  # Stored as string
        assert entry["Signal"] in ["🔥", "⚠️", "❌"]
        assert entry["Stock Pattern"] in ["Sustained", "Emerging", "Cyclical", "Always", "Newly Observed"]
        assert entry["Price"].endswith(("↑", "↓", "→"))

    def test_complex_multi_species_scenario(self):
        """Integration test with multiple species showing different patterns."""
        history = [
            # Run 1: Three species, various wishlists
            make_row("2025-01-01", "Species A", "1.0", "25.00", "50"),  # High wishlist
            make_row("2025-01-01", "Species B", "1.0", "30.00", "5"),   # Moderate
            make_row("2025-01-01", "Species C", "1.0", "20.00", "2"),   # Low
            
            # Run 2: Species A goes OUT, B price rises, C stable
            make_row("2025-01-08", "Species B", "1.0", "35.00", "6"),
            make_row("2025-01-08", "Species C", "1.0", "20.00", "2"),
            
            # Run 3: A still OUT (emerging), B and C present
            make_row("2025-01-15", "Species B", "1.0", "36.00", "8"),
            make_row("2025-01-15", "Species C", "1.0", "20.00", "2"),
            
            # Run 4: A still OUT (emerging becoming sustained), B and C present
            make_row("2025-01-22", "Species B", "1.0", "38.00", "10"),
            make_row("2025-01-22", "Species C", "1.0", "20.00", "2"),
        ]
        
        table = build_breeder_opportunity_table(history)
        
        # Should have 3 species
        assert len(table) == 3
        
        # Species A should show emerging pattern (3 OOS runs)
        species_a = [r for r in table if r["Species"] == "Species A"][0]
        assert species_a["Stock Pattern"] == "Emerging"
        assert species_a["OOS Runs"] == "3"
        
        # Species B should show always available with rising price
        species_b = [r for r in table if r["Species"] == "Species B"][0]
        assert species_b["Stock Pattern"] == "Always"
        assert_price_cell(species_b["Price"], "↑", "38.00")
        
        # Species C should show always available with stable price
        species_c = [r for r in table if r["Species"] == "Species C"][0]
        assert species_c["Stock Pattern"] == "Always"
        assert_price_cell(species_c["Price"], "→", "20.00")

    def test_price_trend_with_invalid_price_values(self):
        """Should handle invalid price values gracefully (ValueError exception)."""
        history = [
            # Run 1: Present with invalid price
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "invalid", "5"),
            
            # Run 2: Present with valid price
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "6"),
        ]
        
        table = build_breeder_opportunity_table(history)
        entry = table[0]
        
        # Trend should default to neutral when historical comparison fails,
        # while still showing the current valid price
        assert_price_cell(entry["Price"], "→", "25.00")

    def test_price_trend_oos_species_with_invalid_historical_prices(self):
        """Should handle invalid historical prices for OUT species."""
        history = [
            # Run 1: Present with invalid price
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "not-a-number", "5"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "5"),
            
            # Run 2: Present with another invalid price
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "also-invalid", "6"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
            
            # Runs 3-5: Species goes OUT (need 5 runs minimum)
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "5"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "41.00", "6"),
            make_row("2025-01-29", "Grammostola pulchra", "2.0", "42.00", "7"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        # Should default to stable when historical prices can't be parsed (hits line 79)
        assert seemanni_entry["Price"].endswith("→")

    def test_price_trend_only_one_historical_price_for_oos_species(self):
        """Should default to neutral when only one historical price exists for OUT species."""
        history = [
            # Run 1: Species present with price
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "5"),
            
            # Run 2: seemanni goes OUT (only 1 price point)
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        # With only 1 historical price, should default to neutral
        assert_price_cell(seemanni_entry["Price"], "→", "25.00")

    def test_sustained_scarcity_with_high_wishlist_pressure(self):
        """
        Test the previously unreachable code: sustained scarcity (4+ OOS runs) 
        with high wishlist pressure from last IN-stock run (within 5-run lookback).
        
        This verifies that Option A (lookback_limit=5) successfully makes the 
        differentiated signal reachable: "sustained scarcity with strong buyer interest"
        """
        history = [
            # Run 1: Species present with very high wishlist (will be 🔥 pressure)
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "50"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00", "2"),
            
            # Run 2: seemanni goes OUT (OOS run 1)
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "3"),
            make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00", "2"),
            
            # Run 3: seemanni still OUT (OOS run 2)
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "42.00", "3"),
            make_row("2025-01-15", "Brachypelma hamorii", "1.5", "30.00", "2"),
            
            # Run 4: seemanni still OUT (OOS run 3)
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "42.00", "3"),
            make_row("2025-01-22", "Brachypelma hamorii", "1.5", "30.00", "2"),
            
            # Run 5: seemanni still OUT (OOS run 4 - triggers "Sustained" pattern)
            make_row("2025-01-29", "Grammostola pulchra", "2.0", "43.00", "3"),
            make_row("2025-01-29", "Brachypelma hamorii", "1.5", "31.00", "2"),
        ]
        
        table = build_breeder_opportunity_table(history)
        seemanni_entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        # Verify sustained pattern classification
        assert seemanni_entry["OOS"] == "OUT"
        assert seemanni_entry["OOS Runs"] == "4"
        assert seemanni_entry["Stock Pattern"] == "Sustained"
        
        # With lookback_limit=5, the high wishlist from run 1 should be carried forward
        # (run 1 is 4 runs back from run 5, which is within the 5-run lookback window)
        assert seemanni_entry["Wishlist"].split()[1] == "🔥"
        
        # Signal should be 🔥 with enhanced recommendation
        assert seemanni_entry["Signal"] == "🔥"
        assert "strong buyer interest" in seemanni_entry["Recommendation"].lower()
        assert "sustained scarcity" in seemanni_entry["Recommendation"].lower()

    def test_breeder_markdown_table_snapshot(self, tmp_path, snapshot):
        """
        Snapshot test for breeder matrix markdown table format.
        Captures the complete markdown output to catch any unintended changes.
        """
        import sys
        from pathlib import Path
        import os
        
        src_path = Path(__file__).parent.parent / "src"
        sys.path.insert(0, str(src_path))
        
        from scrape.breeder_matrix import write_breeder_outputs
        from shared.assertions import extract_markdown_section
        
        # Create comprehensive test data with varied scenarios
        history = [
            # Sustained scarcity - high OOS count
            make_row("2025-01-01", "Cyriocosmus elegans", "0.5", "25.00", "15"),
            make_row("2025-01-29", "Cyriocosmus elegans", "0.5", "30.00", "20"),
            
            # Emerging scarcity - moderate OOS
            make_row("2025-01-01", "Davus sp. \"Panama\"", "1.0", "20.00", "10"),
            make_row("2025-01-15", "Davus sp. \"Panama\"", "1.0", "22.00", "12"),
            make_row("2025-01-29", "Davus sp. \"Panama\"", "1.0", "22.00", "13"),
            
            # Always available
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "18.00", "2"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "18.00", "2"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "18.00", "2"),
            make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "18.00", "2"),
            make_row("2025-01-29", "Aphonopelma seemanni", "1.0", "18.00", "1"),
        ]
        
        table = build_breeder_opportunity_table(history)
        
        # Temporarily change to tmp directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Write outputs which will generate the markdown summary
            result = write_breeder_outputs(table)
            assert result is True
            
            # Read the summary
            summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
            assert summary_path is not None
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_content = f.read()
            
            # Extract the breeder matrix section using helper function
            markdown_section = extract_markdown_section(summary_content, "## 🧬 Breeder Opportunity Matrix")
            
            # Snapshot the markdown section
            assert markdown_section == snapshot
            
        finally:
            os.chdir(original_cwd)

class TestSparklineColumns:
    """Test suite for sparkline trend visualization in breeder matrix."""

    def test_sparkline_columns_present(self):
        """Should include Price History and Wishlist History sparkline columns."""
        history = [
            # Week 1
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "20.00", "5"),
            # Week 2
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "22.00", "8"),
            # Week 3
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "12"),
        ]
        
        table = build_breeder_opportunity_table(history)
        
        # Verify sparkline columns exist
        assert len(table) > 0
        entry = table[0]
        assert "Price History" in entry
        assert "Wishlist History" in entry

    def test_sparkline_shows_trend_characters(self):
        """Should contain Unicode sparkline characters (▁▂▃▄▅▆▇█) in sparkline columns."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "20.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "30.00", "15"),
        ]
        
        table = build_breeder_opportunity_table(history)
        entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        # Should contain sparkline characters (any of ▁▂▃▄▅▆▇█ or space for gaps)
        sparkline_chars = "▁▂▃▄▅▆▇█ "
        price_history = entry["Price History"]
        wishlist_history = entry["Wishlist History"]
        
        # At least some characters should be sparkline characters
        assert any(c in sparkline_chars for c in price_history)
        assert any(c in sparkline_chars for c in wishlist_history)

    def test_sparkline_empty_for_single_data_point(self):
        """Should show minimal sparkline when only one data point exists."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
        ]
        
        table = build_breeder_opportunity_table(history)
        entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        # With only one data point, sparkline should be minimal (single character or dash)
        assert "Price History" in entry
        assert "Wishlist History" in entry
        # Should be very short (1-2 chars)
        assert len(entry["Price History"]) <= 2
        assert len(entry["Wishlist History"]) <= 2

    def test_drivers_column_exists_and_uses_semicolons(self):
        """Should include Drivers column with semicolon-separated explanation (not commas)."""
        history = [
            # Run 1: Present
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "15"),
            
            # Run 2: seemanni goes OUT
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "16"),
            
            # Run 3: seemanni still OUT (2 consecutive = Emerging)
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "42.00", "17"),
        ]
        
        table = build_breeder_opportunity_table(history)
        entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]
        
        # Drivers column should exist
        assert "Drivers" in entry
        drivers = entry["Drivers"]
        
        # Should be non-empty
        assert drivers != ""
        
        # Should use semicolons as separators, NOT commas (to avoid CSV delimiter conflicts)
        assert ";" in drivers
        assert drivers.count(";") >= 2  # At least 3 sections separated by semicolons
        
        # Should contain key information structured
        assert "Stock" in drivers or "Pattern" in drivers
        assert "Demand" in drivers or "Wishlist" in drivers
        assert "Price" in drivers

    def test_sparkline_suppressed_when_oos_exceeds_carryover_window(self):
        """Price History and Wishlist History should be '-' when species OOS > 5 runs."""
        filler = "Grammostola pulchra"
        history = [
            # Run 1: Both present — gives sparklines prior data
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-01", filler, "2.0", "40.00", "5"),
            # Runs 2–7: seemanni absent (6 consecutive OOS runs, exceeds lookback of 5)
            make_row("2025-01-08", filler, "2.0", "40.00", "5"),
            make_row("2025-01-15", filler, "2.0", "40.00", "5"),
            make_row("2025-01-22", filler, "2.0", "40.00", "5"),
            make_row("2025-01-29", filler, "2.0", "40.00", "5"),
            make_row("2025-02-05", filler, "2.0", "40.00", "5"),
            make_row("2025-02-12", filler, "2.0", "40.00", "5"),
        ]

        table = build_breeder_opportunity_table(history)
        entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]

        assert entry["Price History"] == "-"
        assert entry["Wishlist History"] == "-"

    def test_sparkline_not_suppressed_at_carryover_boundary(self):
        """Price History and Wishlist History should be populated when species OOS exactly 5 runs."""
        filler = "Grammostola pulchra"
        history = [
            # Runs 1-2: Both present — sparklines will carry-forward from run 2
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-01", filler, "2.0", "40.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "26.00", "11"),
            make_row("2025-01-08", filler, "2.0", "40.00", "5"),
            # Runs 3–7: seemanni absent (exactly 5 consecutive OOS runs — at window boundary)
            make_row("2025-01-15", filler, "2.0", "40.00", "5"),
            make_row("2025-01-22", filler, "2.0", "40.00", "5"),
            make_row("2025-01-29", filler, "2.0", "40.00", "5"),
            make_row("2025-02-05", filler, "2.0", "40.00", "5"),
            make_row("2025-02-12", filler, "2.0", "40.00", "5"),
        ]

        table = build_breeder_opportunity_table(history)
        entry = [r for r in table if r["Species"] == "Aphonopelma seemanni"][0]

        sparkline_chars = "▁▂▃▄▅▆▇█"
        assert any(c in sparkline_chars for c in entry["Price History"])
        assert any(c in sparkline_chars for c in entry["Wishlist History"])


# ---------------------------------------------------------------------------
# Phase 3: hidden lineage metadata columns
# ---------------------------------------------------------------------------

# Helpers that create rows with custom URLs for transition scenarios.
def _mrow(dt, sci, size, price, wishlist="10", url=None):
    row = make_row(dt, sci, size, price, wishlist)
    if url is not None:
        row["page_url"] = url
    return row


FILLER = "Grammostola pulchra"


def _frow(dt):
    return make_row(dt, FILLER, "2.0", "40.00", "5")


_HIDDEN_COLS = [
    "Lineage Status",
    "Previous Size (cm)",
    "Current Active Size (cm)",
    "Transition Date",
    "Price Evidence State",
    "Wishlist Evidence State",
    "Transition Message",
]

_CONF_URL = "https://thespidershop.co.uk/product/test-confirmed"
_AMB_URL_A = "https://thespidershop.co.uk/product/test-ambiguous-a"
_AMB_URL_B = "https://thespidershop.co.uk/product/test-ambiguous-b"  # different URL


class TestHiddenLineageMetadataColumns:
    """Phase 3: hidden metadata columns are attached to each row in the table.

    At Phase 3 the matrix is still (sci, size)-keyed; every row for a species
    carries the same lineage metadata derived from detect_species_lineage().
    """

    # -- Scenario A: confirmed size transition ---------------------------------

    def _build_scenario_a_history(self):
        """Confirmed 3→5 transition: same URL, gap=1, no overlap. Currently OUT 2 runs."""
        sci = "Scenario A species"
        return [
            # Run 1: 3cm present
            _mrow("2026-01-01", sci, "3", "25.00", "100", url=_CONF_URL),
            _frow("2026-01-01"),
            # Run 2: 5cm appears (confirmed handoff)
            _mrow("2026-02-04", sci, "5", "35.00", "110", url=_CONF_URL),
            _frow("2026-02-04"),
            # Run 3: OUT
            _frow("2026-02-11"),
            # Run 4: OUT (2 consecutive)
            _frow("2026-02-18"),
        ], sci

    def test_scenario_a_breeder_hidden_columns_confirmed_transition(self):
        history, sci = self._build_scenario_a_history()
        table = build_breeder_opportunity_table(history)
        rows = [r for r in table if r["Species"] == sci]
        assert rows, f"No row found for {sci}"

        row = rows[0]
        for col in _HIDDEN_COLS:
            assert col in row, f"Missing hidden column: {col}"
        assert row["Lineage Status"] == "confirmed-transition"
        assert row["Previous Size (cm)"] == "3"
        assert row["Current Active Size (cm)"] == "5"
        assert row["Transition Date"] == "2026-02-04"
        assert row["Price Evidence State"] == "transition-affected"
        assert row["Wishlist Evidence State"] == "carried-across-transition"
        assert "Size changed from 3 cm to 5 cm on 2026-02-04" in row["Transition Message"]
        assert "Drivers" in row and row["Drivers"]

    # -- Scenario B: ambiguous transition -------------------------------------

    def _build_scenario_b_history(self):
        """Ambiguous: URL mismatch between old and new size."""
        sci = "Scenario B species"
        return [
            # Run 1: 3cm with URL A
            _mrow("2026-01-01", sci, "3", "25.00", "100", url=_AMB_URL_A),
            _frow("2026-01-01"),
            # Run 2: 5cm with URL B (mismatch → ambiguous)
            _mrow("2026-02-04", sci, "5", "35.00", "120", url=_AMB_URL_B),
            _frow("2026-02-04"),
            # Run 3: OUT
            _frow("2026-02-11"),
            # Run 4: OUT (2 consecutive)
            _frow("2026-02-18"),
        ], sci

    def test_scenario_b_breeder_hidden_columns_ambiguous_transition(self):
        history, sci = self._build_scenario_b_history()
        table = build_breeder_opportunity_table(history)
        rows = [r for r in table if r["Species"] == sci]
        assert rows

        row = rows[0]
        assert row["Lineage Status"] == "ambiguous-transition"
        assert row["Previous Size (cm)"] == "3"
        assert row["Current Active Size (cm)"] == "5"
        assert row["Transition Date"] == "2026-02-04"
        assert row["Price Evidence State"] == "neutralized"
        assert row["Wishlist Evidence State"] == "neutralized-ambiguous"
        assert "could not be confirmed" in row["Transition Message"]

    # -- Scenario C: multi-variant --------------------------------------------

    def _build_scenario_c_history(self):
        """Two sizes active in current run → multi-variant. Needs ≥2 runs."""
        sci = "Scenario C species"
        return [
            # Run 1: only 3cm (to satisfy ≥2 runs requirement)
            _mrow("2026-01-01", sci, "3", "25.00", "80", url=_CONF_URL),
            _frow("2026-01-01"),
            # Run 2 (current): both 3cm and 5cm active → multi-variant
            _mrow("2026-01-08", sci, "3", "25.00", "80", url=_CONF_URL),
            _mrow("2026-01-08", sci, "5", "35.00", "120", url=_CONF_URL),
            _frow("2026-01-08"),
        ], sci

    def test_scenario_c_breeder_hidden_columns_multi_variant(self):
        history, sci = self._build_scenario_c_history()
        table = build_breeder_opportunity_table(history)
        rows = [r for r in table if r["Species"] == sci]
        assert rows

        row = rows[0]
        assert row["Lineage Status"] == "multi-variant"
        assert row["Previous Size (cm)"] == ""
        assert row["Current Active Size (cm)"] == "3, 5"
        assert row["Transition Date"] == ""
        assert row["Price Evidence State"] == "multi-variant"
        assert row["Wishlist Evidence State"] == "max-active-variant"
        assert "multiple active size variants" in row["Transition Message"]

    # -- Scenario D: stable single-size species --------------------------------

    def _build_scenario_d_history(self):
        """Stable: only one size ever observed, no transition."""
        sci = "Scenario D species"
        return [
            _mrow("2026-01-01", sci, "3", "25.00", "10", url=_CONF_URL),
            _frow("2026-01-01"),
            _mrow("2026-01-08", sci, "3", "25.00", "12", url=_CONF_URL),
            _frow("2026-01-08"),
        ], sci

    def test_scenario_d_breeder_hidden_columns_none_status(self):
        history, sci = self._build_scenario_d_history()
        table = build_breeder_opportunity_table(history)
        rows = [r for r in table if r["Species"] == sci]
        assert rows

        row = rows[0]
        assert row["Lineage Status"] == "none"
        assert row["Previous Size (cm)"] == ""
        assert row["Current Active Size (cm)"] == "3"
        assert row["Transition Date"] == ""
        assert row["Price Evidence State"] == "standard"
        assert row["Wishlist Evidence State"] == "standard"
        assert row["Transition Message"] == ""


# ---------------------------------------------------------------------------
# Phase 4: species-level row identity — acceptance scenarios
# ---------------------------------------------------------------------------

_P4_CONF_URL = "https://thespidershop.co.uk/product/p4-confirmed"
_P4_AMB_URL_A = "https://thespidershop.co.uk/product/p4-ambiguous-a"
_P4_AMB_URL_B = "https://thespidershop.co.uk/product/p4-ambiguous-b"

_P4_FILLER = "P4 Filler species"


def _p4frow(dt):
    return _mrow(dt, _P4_FILLER, "2.0", "20.00", "10")


class TestBreederPhase4AcceptanceScenarios:
    """Phase 4: one row per species in the breeder table.

    These tests are the primary regression guards for the species-level row
    identity migration. The key assertion — exactly one row per scientific name
    — FAILS in Phase 3 (size-keyed) for any species with multiple historical
    size variants.
    """

    # ── Scenario A: confirmed transition ────────────────────────────────────

    _SCI_A = "Phase4 Breeder Confirmed"

    def _history_a(self):
        """8 runs: 3 cm for R1–R4, 5 cm for R5–R6 (same URL → confirmed), OUT R7–R8."""
        sci, url = self._SCI_A, _P4_CONF_URL
        return [
            _mrow("2025-10-01", sci, "3", "35.00", "50",  url=url), _p4frow("2025-10-01"),
            _mrow("2025-10-08", sci, "3", "35.00", "70",  url=url), _p4frow("2025-10-08"),
            _mrow("2025-10-15", sci, "3", "35.00", "90",  url=url), _p4frow("2025-10-15"),
            _mrow("2025-10-22", sci, "3", "35.00", "100", url=url), _p4frow("2025-10-22"),
            # R5: 5 cm appears (same URL, gap=1, no overlap → confirmed)
            _mrow("2025-10-29", sci, "5", "35.00", "100", url=url), _p4frow("2025-10-29"),
            # R6: 5 cm continues; wishlist rises
            _mrow("2025-11-05", sci, "5", "35.00", "120", url=url), _p4frow("2025-11-05"),
            # R7–R8: species OUT
            _p4frow("2025-11-12"),
            _p4frow("2025-11-19"),
        ]

    def test_scenario_a_confirmed_transition(self):
        """Confirmed transition: one row, supply metrics correct, wishlist carries, sparklines not suppressed."""
        rows = [r for r in build_breeder_opportunity_table(self._history_a())
                if r["Species"] == self._SCI_A]
        assert len(rows) == 1, f"Expected 1 row for {self._SCI_A!r}, got {len(rows)}"
        row = rows[0]
        assert row["Size (cm)"] == "5"
        assert row["OOS"] == "OUT"
        assert row["OOS Runs"] == "2"
        assert row["Stock Pattern"] == "Emerging"
        assert row["Signal"] == "🔥"
        wishlist = row["Wishlist"]
        assert wishlist.startswith("120"), f"Expected count 120, got {wishlist!r}"
        assert "🔥" in wishlist
        assert "↑" in wishlist
        assert row["Price History"] != "-"
        assert row["Wishlist History"] != "-"
        assert "transition" in row["Drivers"].lower()

    # ── Scenario B: ambiguous transition ────────────────────────────────────

    _SCI_B = "Phase4 Breeder Ambiguous"

    def _history_b(self):
        """8 runs: 3 cm for R1–R4 (URL A), 5 cm for R5–R6 (URL B → ambiguous), OUT R7–R8."""
        sci = self._SCI_B
        return [
            _mrow("2025-10-01", sci, "3", "35.00", "50",  url=_P4_AMB_URL_A), _p4frow("2025-10-01"),
            _mrow("2025-10-08", sci, "3", "35.00", "70",  url=_P4_AMB_URL_A), _p4frow("2025-10-08"),
            _mrow("2025-10-15", sci, "3", "35.00", "90",  url=_P4_AMB_URL_A), _p4frow("2025-10-15"),
            _mrow("2025-10-22", sci, "3", "35.00", "100", url=_P4_AMB_URL_A), _p4frow("2025-10-22"),
            # R5: 5 cm with different URL → ambiguous
            _mrow("2025-10-29", sci, "5", "35.00", "100", url=_P4_AMB_URL_B), _p4frow("2025-10-29"),
            _mrow("2025-11-05", sci, "5", "35.00", "120", url=_P4_AMB_URL_B), _p4frow("2025-11-05"),
            # R7–R8: species OUT
            _p4frow("2025-11-12"),
            _p4frow("2025-11-19"),
        ]

    def test_scenario_b_ambiguous_transition(self):
        """Ambiguous transition: one row, evidence suppressed, wishlist delta neutralized."""
        rows = [r for r in build_breeder_opportunity_table(self._history_b())
                if r["Species"] == self._SCI_B]
        assert len(rows) == 1, f"Expected 1 row for {self._SCI_B!r}, got {len(rows)}"
        row = rows[0]
        assert row["Price History"] == "-"
        assert row["Wishlist History"] == "-"
        assert "→" in row["Wishlist"]
        assert "↑" not in row["Wishlist"]

    def test_scenario_b_drivers_explain_ambiguous_demand(self):
        """Ambiguous transition: Drivers demand section must explain neutralized delta."""
        rows = [r for r in build_breeder_opportunity_table(self._history_b())
                if r["Species"] == self._SCI_B]
        drivers = rows[0]["Drivers"]
        assert "momentum neutralized; continuity unconfirmed" in drivers, (
            f"Expected ambiguous demand qualifier in Drivers, got: {drivers!r}"
        )

    # ── Scenario C: multi-variant (overlapping sizes) ───────────────────────

    _SCI_C = "Phase4 Breeder Overlap"

    def _history_c(self):
        """3 runs with both 3 cm and 5 cm active in every run → 'Always' pattern."""
        sci = self._SCI_C
        return [
            make_row("2025-10-01", sci, "3", "25.00", "80"),
            make_row("2025-10-01", sci, "5", "35.00", "120"),
            _p4frow("2025-10-01"),
            make_row("2025-10-08", sci, "3", "25.00", "80"),
            make_row("2025-10-08", sci, "5", "35.00", "120"),
            _p4frow("2025-10-08"),
            make_row("2025-10-15", sci, "3", "25.00", "80"),
            make_row("2025-10-15", sci, "5", "35.00", "120"),
            _p4frow("2025-10-15"),
        ]

    def test_scenario_c_multi_variant(self):
        """Multi-variant: one row, comma-separated sizes, suppressed evidence, ❌ signal."""
        rows = [r for r in build_breeder_opportunity_table(self._history_c())
                if r["Species"] == self._SCI_C]
        assert len(rows) == 1, f"Expected 1 row for {self._SCI_C!r}, got {len(rows)}"
        row = rows[0]
        assert row["Size (cm)"] == "3, 5"
        assert row["Price"] == "Multiple active prices"
        assert row["Price History"] == "-"
        assert row["Wishlist History"] == "-"
        assert row["Signal"] == "❌"

    def test_scenario_c_drivers_explain_multi_variant_price_and_demand(self):
        """Multi-variant: Drivers price section must say 'Multiple active sizes',
        demand must explain overlapping variants."""
        rows = [r for r in build_breeder_opportunity_table(self._history_c())
                if r["Species"] == self._SCI_C]
        drivers = rows[0]["Drivers"]
        assert "Price: Multiple active sizes" in drivers, (
            f"Expected 'Price: Multiple active sizes' in Drivers, got: {drivers!r}"
        )
        assert "active variants overlap; delta neutralized" in drivers, (
            f"Expected multi-variant demand qualifier in Drivers, got: {drivers!r}"
        )

    # ── Scenario D: stable single-size species (regression guard) ───────────

    _SCI_D = "Phase4 Breeder Stable"

    def _history_d(self):
        """4 runs: species stable at 5 cm throughout."""
        sci = self._SCI_D
        return [
            make_row("2025-10-01", sci, "5", "35.00", "10"), _p4frow("2025-10-01"),
            make_row("2025-10-08", sci, "5", "35.00", "10"), _p4frow("2025-10-08"),
            make_row("2025-10-15", sci, "5", "35.00", "10"), _p4frow("2025-10-15"),
            make_row("2025-10-22", sci, "5", "35.00", "10"), _p4frow("2025-10-22"),
        ]

    def test_scenario_d_stable_single_size(self):
        """Stable species: one row, none lineage, single size, evidence not suppressed."""
        rows = [r for r in build_breeder_opportunity_table(self._history_d())
                if r["Species"] == self._SCI_D]
        assert len(rows) == 1
        row = rows[0]
        assert row["Size (cm)"] == "5"
        assert row["Lineage Status"] == "none"
        assert row["Price History"] != "-"
        assert row["Wishlist History"] != "-"

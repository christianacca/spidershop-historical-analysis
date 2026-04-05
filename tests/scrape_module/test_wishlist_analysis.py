#!/usr/bin/env python3
"""
Unit tests for compute_wishlist_delta().

compute_wishlist_delta is the k2-level building block still called by
compute_species_wishlist_delta (for species with lineage_status == 'none').
These tests verify its edge cases directly so that the species-level wrapper
does not need to re-test each low-level boundary.

Covers:
- Species IN the current run — rising, stable, and falling delta
- Species OUT of the current run — carryover run used as current reference
- No prior comparable observation within the bounded window → neutral
"""

from shared.history_utils import group_by_run
from scrape.wishlist_analysis import compute_wishlist_delta, compute_species_wishlist_delta, get_species_wishlist_count
from scrape.listing_lineage import LineageResult
from conftest import make_row


def _setup(history_rows):
    """Return (by_run, runs, cur_run) from raw rows."""
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    cur_run = runs[-1]
    return by_run, runs, cur_run


class TestComputeWishlistDelta:
    """Tests for compute_wishlist_delta() — the k2-level momentum helper."""

    # -----------------------------------------------------------------
    # IN-stock species
    # -----------------------------------------------------------------

    def test_in_stock_rising_wishlist_returns_up_delta(self):
        """Wishlist count rising by ≥5 across runs → ↑ delta."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "20"),
        ]
        by_run, runs, cur_run = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        assert compute_wishlist_delta(key, by_run, runs, cur_run) == "↑"

    def test_in_stock_stable_wishlist_returns_neutral_delta(self):
        """Wishlist count change within ±4 → → delta."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "12"),
        ]
        by_run, runs, cur_run = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        assert compute_wishlist_delta(key, by_run, runs, cur_run) == "→"

    def test_in_stock_falling_wishlist_returns_down_delta(self):
        """Wishlist count falling by ≥5 → ↓ delta."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "20"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "10"),
        ]
        by_run, runs, cur_run = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        assert compute_wishlist_delta(key, by_run, runs, cur_run) == "↓"

    def test_in_stock_no_prior_observation_returns_neutral(self):
        """Only one run with the species — no previous value to compare → → delta."""
        history = [
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "20"),
        ]
        by_run, runs, cur_run = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        assert compute_wishlist_delta(key, by_run, runs, cur_run) == "→"

    # -----------------------------------------------------------------
    # OUT-of-stock species — carryover run as current reference
    # -----------------------------------------------------------------

    def test_out_of_stock_uses_carryover_run_as_current_reference(self):
        """Species OOS in current run; last IN-stock count used as current reference.

        Run 1: count=10, Run 2: count=20, Run 3 (current): species absent.
        Delta should compare run 2 (20) vs run 1 (10) → ↑.
        """
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "20"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "5"),
        ]
        by_run, runs, cur_run = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        assert compute_wishlist_delta(key, by_run, runs, cur_run) == "↑"

    def test_out_of_stock_first_time_no_prior_comparison_returns_neutral(self):
        """Species OOS for the first time — only one historical observation → → delta."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
        ]
        by_run, runs, cur_run = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        assert compute_wishlist_delta(key, by_run, runs, cur_run) == "→"

    def test_never_observed_returns_neutral(self):
        """Species never in any run — no reference at all → → delta."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "10"),
        ]
        by_run, runs, cur_run = _setup(history)
        key = ("Unknown spider", "1.0")

        assert compute_wishlist_delta(key, by_run, runs, cur_run) == "→"


def _none_lineage(current_active_size: str) -> LineageResult:
    return LineageResult("none", "", current_active_size, "", "standard", "standard", "")


def _confirmed_lineage(prev_size: str, curr_size: str, transition_date: str) -> LineageResult:
    return LineageResult(
        "confirmed-transition", prev_size, curr_size, transition_date,
        "transition-affected", "carried-across-transition", "",
    )


# ---------------------------------------------------------------------------
# get_species_wishlist_count — OOS edge cases
# ---------------------------------------------------------------------------

class TestGetSpeciesWishlistCount:
    """OOS branches not reached by the k2-level tests above."""

    _SCI = "Aphonopelma seemanni"
    _FILLER = "Grammostola pulchra"

    def test_oos_empty_current_active_size_returns_zero(self):
        """Species OOS + current_active_size is blank → 0 immediately (no walkback)."""
        history = [
            make_row("2025-01-01", self._SCI, "1.0", "25.00", "15"),
            make_row("2025-01-08", self._FILLER, "2.0", "40.00", "5"),  # sci absent
        ]
        by_run, runs, cur_run = _setup(history)
        assert get_species_wishlist_count(self._SCI, _none_lineage(""), by_run, runs, cur_run) == 0

    def test_oos_beyond_lookback_window_returns_zero(self):
        """Species OOS for more runs than the carryover window → 0 (no prior found)."""
        history = (
            [make_row(f"2025-01-{i+1:02d}", self._SCI, "1.0", "25.00", "15") for i in range(2)]
            + [make_row(f"2025-02-{i+1:02d}", self._FILLER, "2.0", "40.00", "5") for i in range(6)]
        )
        by_run, runs, cur_run = _setup(history)
        assert get_species_wishlist_count(self._SCI, _none_lineage("1.0"), by_run, runs, cur_run) == 0


# ---------------------------------------------------------------------------
# compute_species_wishlist_delta — confirmed-transition paths
# ---------------------------------------------------------------------------

class TestComputeSpeciesWishlistDelta:
    """Branches specific to confirmed-transition stitched comparison."""

    _SCI = "Test spider"
    _FILLER = "Grammostola pulchra"

    def test_confirmed_transition_oos_declining_delta(self):
        """Species OOS in current run; stitched walkback finds count 10 (dropped from 30) → ↓."""
        history = [
            make_row("2025-01-01", self._SCI, "3", "25.00", "30"),   # R1: prev_size "3"
            make_row("2025-01-08", self._SCI, "5", "25.00", "10"),   # R2: curr_size "5"
            make_row("2025-01-15", self._FILLER, "2.0", "40.00", "5"),  # R3 cur: sci absent
        ]
        by_run, runs, cur_run = _setup(history)
        lr = _confirmed_lineage("3", "5", "2025-01-08")
        assert compute_species_wishlist_delta(self._SCI, lr, by_run, runs, cur_run) == "↓"

    def test_confirmed_transition_no_prior_reference_returns_neutral(self):
        """Confirmed-transition with only one run: current_count found but no previous → →."""
        history = [
            make_row("2025-01-08", self._SCI, "5", "25.00", "20"),
            make_row("2025-01-08", self._FILLER, "2.0", "40.00", "5"),
        ]
        by_run, runs, cur_run = _setup(history)
        lr = _confirmed_lineage("3", "5", "2025-01-08")
        assert compute_species_wishlist_delta(self._SCI, lr, by_run, runs, cur_run) == "→"

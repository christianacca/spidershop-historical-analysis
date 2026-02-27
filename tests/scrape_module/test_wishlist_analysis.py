#!/usr/bin/env python3
"""
Unit tests for wishlist_analysis.get_wishlist_metrics().

Covers:
- Species IN the current run (pressure from map, delta from history)
- Species OUT of the current run with recent carryover available
- Species OUT with no carryover within the bounded window (→ ❌)
- Wishlist delta: rising, stable, falling
"""

import pytest
from shared.history_utils import group_by_run
from scrape.wishlist_analysis import compute_wishlist_pressure, get_wishlist_metrics, get_wishlist_count
from conftest import make_row


def _setup(history_rows):
    """Return (key_fn, by_run, runs, cur_run, wishlist_pressure_map) from raw rows."""
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    cur_run = runs[-1]
    wishlist_pressure_map = compute_wishlist_pressure(by_run[cur_run])
    return by_run, runs, cur_run, wishlist_pressure_map


class TestGetWishlistMetrics:
    """Tests for the get_wishlist_metrics() shared utility."""

    # -----------------------------------------------------------------
    # IN-stock species
    # -----------------------------------------------------------------

    def test_in_stock_returns_pressure_from_map(self):
        """Species present in current run — pressure comes directly from wishlist_pressure_map."""
        # Two runs; species present in both with very different wishlist counts so
        # ranking produces a deterministic 🔥 result for the high-count species.
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "1"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
            make_row("2025-01-01", "Lasiodora parahybana", "1.5", "20.00", "50"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "2"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "2"),
            make_row("2025-01-08", "Lasiodora parahybana", "1.5", "20.00", "50"),
        ]

        by_run, runs, cur_run, wishlist_pressure_map = _setup(history)
        key = ("Lasiodora parahybana", "1.5")

        wishlist_pressure, _ = get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map)

        assert wishlist_pressure == "🔥"

    def test_in_stock_zero_wishlist_returns_no_pressure(self):
        """Species in current run with wishlist 0 → ❌ pressure."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "0"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "0"),
        ]

        by_run, runs, cur_run, wishlist_pressure_map = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        wishlist_pressure, _ = get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map)

        assert wishlist_pressure == "❌"

    def test_in_stock_rising_wishlist_returns_up_delta(self):
        """Wishlist count rising by ≥5 across runs → ↑ delta."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "20"),
        ]

        by_run, runs, cur_run, wishlist_pressure_map = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        _, wishlist_delta = get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map)

        assert wishlist_delta == "↑"

    def test_in_stock_stable_wishlist_returns_neutral_delta(self):
        """Wishlist count change within ±4 → → delta."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "12"),
        ]

        by_run, runs, cur_run, wishlist_pressure_map = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        _, wishlist_delta = get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map)

        assert wishlist_delta == "→"


class TestGetWishlistCount:
    """Tests for get_wishlist_count() — bounded by OOS_CARRYOVER_LOOKBACK (5 runs)."""

    def _setup(self, history_rows):
        by_run = group_by_run(history_rows)
        runs = sorted(by_run)
        cur_run = runs[-1]
        return by_run, runs, cur_run

    def test_in_current_run_returns_current_count(self):
        """Species IN the current run → returns its actual wishlist count."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "20"),
        ]
        by_run, runs, cur_run = self._setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        assert get_wishlist_count(key, by_run, runs, cur_run) == 20

    def test_out_within_carryover_window_returns_last_known_count(self):
        """Species OOS for 3 runs (within 5) → returns count from last IN-stock run."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "45"),
        ]
        filler = "Grammostola pulchra"
        for week in range(1, 4):
            dt = f"2025-01-{(1 + week * 7):02d}"
            history.append(make_row(dt, filler, "2.0", "40.00", "5"))

        by_run, runs, cur_run = self._setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        assert get_wishlist_count(key, by_run, runs, cur_run) == 45

    def test_out_beyond_carryover_window_returns_zero(self):
        """Species OOS for 6 runs → beyond the 5-run window → returns 0.

        The count window matches the pressure-tier carryover window so that the
        raw count used for ranking expires at the same time as the pressure tier.
        Once the pressure tier is ❌ the count should also be 0.
        """
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "67"),
        ]
        filler = "Grammostola pulchra"
        for week in range(1, 7):  # 6 filler runs → 6 OOS runs
            dt = f"2025-01-{(1 + week * 7):02d}"
            history.append(make_row(dt, filler, "2.0", "40.00", "5"))

        by_run, runs, cur_run = self._setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        # 6 OOS runs is beyond the 5-run window → expired, return 0
        assert get_wishlist_count(key, by_run, runs, cur_run) == 0

    def test_never_observed_returns_zero(self):
        """Species never present in any run → returns 0."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "10"),
        ]
        by_run, runs, cur_run = self._setup(history)
        key = ("Unknown spider", "1.0")

        assert get_wishlist_count(key, by_run, runs, cur_run) == 0
    def test_in_stock_falling_wishlist_returns_down_delta(self):
        """Wishlist count falling by ≥5 → ↓ delta."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "20"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "10"),
        ]

        by_run, runs, cur_run, wishlist_pressure_map = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        _, wishlist_delta = get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map)

        assert wishlist_delta == "↓"

    # -----------------------------------------------------------------
    # OUT-of-stock species — carryover
    # -----------------------------------------------------------------

    def test_out_of_stock_carries_forward_recent_pressure(self):
        """Species OUT in current run but IN recent run → pressure carried forward."""
        # Run 1: species present with high wishlist; Run 2: species OUT.
        # Carryover should return the pressure from run 1.
        history = [
            # Filler species so run 1 has enough variety for a meaningful distribution
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "1"),
            make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "2"),
            make_row("2025-01-01", "Lasiodora parahybana", "1.5", "20.00", "50"),
            # Run 2: Lasiodora goes OUT; other species remain
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "1"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "2"),
        ]

        by_run, runs, cur_run, wishlist_pressure_map = _setup(history)
        key = ("Lasiodora parahybana", "1.5")

        wishlist_pressure, _ = get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map)

        assert wishlist_pressure == "🔥"

    def test_out_of_stock_no_recent_history_returns_no_pressure(self):
        """Species never present in history → ❌ pressure (no carryover possible)."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        ]

        by_run, runs, cur_run, wishlist_pressure_map = _setup(history)
        key = ("Unknown spider", "1.0")  # not in any run

        wishlist_pressure, _ = get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map)

        assert wishlist_pressure == "❌"

    def test_out_of_stock_beyond_carryover_limit_returns_no_pressure(self):
        """Species last seen more than 5 runs ago → carryover expires → ❌ pressure."""
        # 7 runs; species present only in run 1, absent for 6 consecutive runs.
        history = [make_row("2025-01-01", "Lasiodora parahybana", "1.5", "20.00", "50")]
        filler = "Aphonopelma seemanni"
        for week in range(1, 7):
            dt = f"2025-01-{(1 + week * 7):02d}"
            history.append(make_row(dt, filler, "1.0", "25.00", "5"))

        by_run, runs, cur_run, wishlist_pressure_map = _setup(history)
        key = ("Lasiodora parahybana", "1.5")

        wishlist_pressure, _ = get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map)

        assert wishlist_pressure == "❌"

    def test_out_of_stock_returns_neutral_delta_when_no_prior_comparison(self):
        """Species OUT for the first time (no previous comparable run) → → delta."""
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
            # Run 2: species disappears — only one historical observation available
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
        ]

        by_run, runs, cur_run, wishlist_pressure_map = _setup(history)
        key = ("Aphonopelma seemanni", "1.0")

        _, wishlist_delta = get_wishlist_metrics(key, by_run, runs, cur_run, wishlist_pressure_map)

        assert wishlist_delta == "→"

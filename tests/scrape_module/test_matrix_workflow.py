#!/usr/bin/env python3
"""Tests for shared matrix workflow helpers used by breeder/dealer builders."""

from scrape.matrix_workflow import (
    build_species_wishlist_pressure_map,
    collect_lookback_values_for_key,
    generate_price_wishlist_sparklines,
    iter_lookback_rows_for_key,
    prepare_matrix_analysis,
    prepare_matrix_runs,
    sort_matrix_table,
)
from shared.history_utils import k2
from conftest import make_row


class TestPrepareMatrixRuns:
    """Run preparation helper behavior."""

    def test_returns_none_for_insufficient_runs(self):
        history = [make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5")]
        assert prepare_matrix_runs(history) is None

    def test_returns_grouped_context_for_two_or_more_runs(self):
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "26.00", "6"),
        ]
        result = prepare_matrix_runs(history)
        assert result is not None
        by_run, runs, current_run, previous_run, current_rows = result
        assert runs == ["2025-01-01", "2025-01-08"]
        assert previous_run == "2025-01-01"
        assert current_run == "2025-01-08"
        assert current_rows == by_run[current_run]


class TestPrepareMatrixAnalysis:
    """Extended builder context preparation shared by matrix tables."""

    def test_returns_none_for_insufficient_runs(self):
        history = [make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5")]

        assert prepare_matrix_analysis(history) is None

    def test_returns_run_index_and_wishlist_pressure(self):
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "26.00", "11"),
            make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
        ]

        prepared = prepare_matrix_analysis(history)

        assert prepared is not None
        by_run, runs, current_run, previous_run, current_rows, run_index, _ = prepared
        assert runs == ["2025-01-01", "2025-01-08"]
        assert current_run == "2025-01-08"
        assert previous_run == "2025-01-01"
        assert current_rows == by_run[current_run]
        assert run_index == {"2025-01-01": 0, "2025-01-08": 1}


class TestLookbackHelpers:
    """Bounded historical lookup helpers shared across matrix builders."""

    def test_iter_lookback_rows_returns_matching_rows_newest_first_within_window(self):
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "20.00", "1"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "21.00", "2"),
            make_row("2025-01-15", "Grammostola pulchra", "2.0", "30.00", "3"),
            make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "24.00", "4"),
            make_row("2025-01-29", "Grammostola pulchra", "2.0", "31.00", "4"),
        ]
        prepared = prepare_matrix_analysis(history)
        assert prepared is not None
        by_run, runs, current_run, _, _, run_index, _ = prepared

        rows = list(
            iter_lookback_rows_for_key(
                ("Aphonopelma seemanni", "1.0"), by_run, runs, current_run, run_index
            )
        )

        assert [row["scrape_datetime"] for row in rows] == ["2025-01-22", "2025-01-08", "2025-01-01"]

    def test_collect_lookback_values_filters_empty_values_and_respects_limit(self):
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "20.00", "1"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "", "2"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "24.00", "3"),
            make_row("2025-01-22", "Grammostola pulchra", "2.0", "30.00", "3"),
        ]
        prepared = prepare_matrix_analysis(history)
        assert prepared is not None
        by_run, runs, current_run, _, _, run_index, _ = prepared

        values = collect_lookback_values_for_key(
            ("Aphonopelma seemanni", "1.0"),
            by_run,
            runs,
            current_run,
            run_index,
            lambda row: row.get("price_gbp", ""),
            max_values=2,
        )

        assert values == ["24.00", "20.00"]


class TestSparklineHelpers:
    """Sparkline helper output behavior."""

    def test_generates_price_and_wishlist_sparklines(self):
        history = [
            make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "20.00", "5"),
            make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "8"),
            make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "30.00", "12"),
        ]
        prepared = prepare_matrix_runs(history)
        assert prepared is not None
        by_run, runs, *_ = prepared

        price_sparkline, wishlist_sparkline = generate_price_wishlist_sparklines(
            ("Aphonopelma seemanni", "1.0"), by_run, runs, max_runs=8
        )

        assert isinstance(price_sparkline, str)
        assert isinstance(wishlist_sparkline, str)
        assert len(price_sparkline) > 0
        assert len(wishlist_sparkline) > 0


class TestSortMatrixTable:
    """Shared sort ordering behavior."""

    def test_sorts_by_signal_then_wishlist_then_tertiary_desc(self):
        table = [
            {"Signal": "⚠️", "Wishlist": "20 🔥 ↑", "OOS Runs": "2"},
            {"Signal": "🔥", "Wishlist": "1 ⚠️ →", "OOS Runs": "1"},
            {"Signal": "🔥", "Wishlist": "8 🔥 →", "OOS Runs": "4"},
        ]

        sort_matrix_table(table, "Signal", lambda row: float(row["OOS Runs"]))

        assert table[0]["Signal"] == "🔥"
        assert table[0]["Wishlist"].startswith("8")
        assert table[1]["Signal"] == "🔥"
        assert table[2]["Signal"] == "⚠️"


# ---------------------------------------------------------------------------
# build_species_wishlist_pressure_map — small-N flatten branch
# ---------------------------------------------------------------------------

class TestBuildSpeciesWishlistPressureMap:
    """Small-N flatten: all nonzero counts within WISHLIST_SMALL_N_FLATTEN_THRESHOLD → ⚠️."""

    def test_small_n_flatten_assigns_moderate_to_all_nonzero(self):
        """Counts 10 and 11 differ by 1 (≤ threshold of 1) → both species get ⚠️."""
        history = [
            make_row("2025-01-01", "Spider A", "1.0", "25.00", "10"),
            make_row("2025-01-01", "Spider B", "1.0", "25.00", "11"),
            make_row("2025-01-08", "Spider A", "1.0", "25.00", "10"),
            make_row("2025-01-08", "Spider B", "1.0", "25.00", "11"),
        ]
        prepared = prepare_matrix_analysis(history)
        assert prepared is not None
        by_run, runs, cur_run, _, _, _, species_lineage_map = prepared
        result = build_species_wishlist_pressure_map(species_lineage_map, by_run, runs, cur_run)
        assert result["Spider A"] == "⚠️"
        assert result["Spider B"] == "⚠️"

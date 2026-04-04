#!/usr/bin/env python3
"""Tests for shared historical observation metadata helpers."""

from conftest import HistoryEntry

from shared.history_utils import (
    build_species_presence_timeline,
    build_species_stock_pattern,
    compute_species_avg_oos_duration,
    compute_species_current_oos_runs,
    compute_species_restock_speed,
    compute_species_stock_reliability,
    create_observation_coverage,
    format_observation_coverage,
    group_by_run,
    is_newly_observed_coverage,
    k2,
)


def _coverage(entries):
    return create_observation_coverage(
        [entry.__dict__.copy() for entry in entries],
        ("Aphonopelma seemanni", "1.5"),
    )


class TestCreateObservationCoverage:
    """Observation coverage reflects the full dataset timeline."""

    def test_reports_full_dataset_denominator_for_late_first_observation(self):
        coverage = _coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-15 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-22 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
            ]
        )

        assert coverage["first_observed_run"] == "2024-01-15 10:00:00"
        assert coverage["latest_observed_run"] == "2024-01-22 10:00:00"
        assert coverage["observed_run_count"] == 2
        assert coverage["total_run_count"] == 4
        assert coverage["ambiguous_pre_first_seen_run_count"] == 2

    def test_does_not_treat_runs_before_first_observation_as_observed(self):
        coverage = _coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-15 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
            ]
        )

        assert coverage["observed_run_count"] == 1
        assert coverage["ambiguous_pre_first_seen_run_count"] == 2
        assert coverage["observed_in_current_run"] is True

    def test_counts_one_current_consecutive_observation_run(self):
        coverage = _coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-15 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
            ]
        )

        assert coverage["current_consecutive_observation_runs"] == 1

    def test_counts_two_current_consecutive_observation_runs(self):
        coverage = _coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-15 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
            ]
        )

        assert coverage["current_consecutive_observation_runs"] == 2

    def test_counts_three_current_consecutive_observation_runs(self):
        coverage = _coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-15 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
            ]
        )

        assert coverage["current_consecutive_observation_runs"] == 3
        assert coverage["ambiguous_pre_first_seen_run_count"] == 0

    def test_latest_observed_can_differ_from_first_when_species_disappears(self):
        coverage = create_observation_coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ).__dict__.copy(),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ).__dict__.copy(),
                HistoryEntry(
                    scrape_datetime="2024-01-15 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ).__dict__.copy(),
                HistoryEntry(
                    scrape_datetime="2024-01-22 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ).__dict__.copy(),
            ],
            ("Aphonopelma seemanni", "1.5"),
        )

        assert coverage["first_observed_run"] == "2024-01-01 10:00:00"
        assert coverage["latest_observed_run"] == "2024-01-15 10:00:00"
        assert coverage["observed_run_count"] == 2
        assert coverage["observed_in_current_run"] is False

    def test_accepts_row_dicts_via_create_species_key_alias(self):
        row = HistoryEntry(scientific_name="Aphonopelma seemanni", size_cm="1.5").__dict__.copy()

        assert k2(row) == ("Aphonopelma seemanni", "1.5")


class TestIsNewlyObservedCoverage:
    """Newly observed classification should come from one shared predicate."""

    def test_returns_true_for_current_run_first_observation(self):
        coverage = _coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
            ]
        )

        assert is_newly_observed_coverage(coverage) is True

    def test_returns_true_for_latest_two_consecutive_observations(self):
        coverage = _coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-15 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
            ]
        )

        assert is_newly_observed_coverage(coverage) is True

    def test_returns_false_for_non_consecutive_sparse_observations(self):
        coverage = _coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-15 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
            ]
        )

        assert is_newly_observed_coverage(coverage) is False

    def test_returns_false_after_three_observed_runs(self):
        coverage = _coverage(
            [
                HistoryEntry(
                    scrape_datetime="2024-01-01 10:00:00",
                    scientific_name="Other species",
                    size_cm="1.0",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-08 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-15 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
                HistoryEntry(
                    scrape_datetime="2024-01-22 10:00:00",
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                ),
            ]
        )

        assert is_newly_observed_coverage(coverage) is False


class TestFormatObservationCoverage:
    """Coverage formatting is shared across matrix modules."""

    def test_formats_observed_and_total_run_counts(self):
        assert format_observation_coverage(
            {
                "observed_run_count": 2,
                "total_run_count": 5,
            }
        ) == "observed 2/5 runs"


# ---------------------------------------------------------------------------
# Helper to build synthetic history rows for species-level timeline tests
# ---------------------------------------------------------------------------

SCI = "Aphonopelma seemanni"
OTHER = "Grammostola pulchra"


def _h(*run_specs):
    """Build history rows from (datetime, present_bool) specs.

    A filler row for OTHER species anchors each run.
    """
    rows = []
    for dt, present in run_specs:
        rows.append({
            "scrape_datetime": dt,
            "scientific_name": OTHER,
            "common_name": "Other",
            "size_cm": "2.0",
            "price_gbp": "40.00",
            "wishlist_count": "10",
            "page_url": "https://example.com/other",
        })
        if present:
            rows.append({
                "scrape_datetime": dt,
                "scientific_name": SCI,
                "common_name": "Costa Rican Zebra",
                "size_cm": "1.5",
                "price_gbp": "25.00",
                "wishlist_count": "5",
                "page_url": "https://example.com/seemanni",
            })
    return rows


# ---------------------------------------------------------------------------
# Phase 2 tests: build_species_presence_timeline
# ---------------------------------------------------------------------------

class TestBuildSpeciesPresenceTimeline:
    """build_species_presence_timeline returns one bool per run."""

    def test_present_run_is_true(self):
        history = _h(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", True),
        )
        by_run = group_by_run(history)
        ordered_runs = sorted(by_run.keys())
        timeline = build_species_presence_timeline(history, SCI)

        assert timeline["2026-01-01 10:00:00"] is True
        assert timeline["2026-01-08 10:00:00"] is True

    def test_absent_run_is_false(self):
        history = _h(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
        )
        timeline = build_species_presence_timeline(history, SCI)

        assert timeline["2026-01-08 10:00:00"] is False

    def test_multi_variant_run_is_true(self):
        """A run with two sizes for the species is still True."""
        rows = [
            {
                "scrape_datetime": "2026-01-01 10:00:00",
                "scientific_name": SCI,
                "size_cm": "3",
                "price_gbp": "25.00",
                "wishlist_count": "5",
                "page_url": "https://example.com/a",
            },
            {
                "scrape_datetime": "2026-01-01 10:00:00",
                "scientific_name": SCI,
                "size_cm": "5",
                "price_gbp": "35.00",
                "wishlist_count": "10",
                "page_url": "https://example.com/a",
            },
        ]
        timeline = build_species_presence_timeline(rows, SCI)
        assert timeline["2026-01-01 10:00:00"] is True

    def test_transition_run_old_gone_new_appears_is_true(self):
        """If old size leaves and new size appears in SAME run, species is present."""
        rows = [
            {
                "scrape_datetime": "2026-01-01 10:00:00",
                "scientific_name": SCI,
                "size_cm": "3",
                "price_gbp": "25.00",
                "wishlist_count": "5",
                "page_url": "https://example.com/a",
            },
            # Run 2: 3cm gone, 5cm appears (species is still present)
            {
                "scrape_datetime": "2026-01-08 10:00:00",
                "scientific_name": SCI,
                "size_cm": "5",
                "price_gbp": "35.00",
                "wishlist_count": "10",
                "page_url": "https://example.com/a",
            },
        ]
        timeline = build_species_presence_timeline(rows, SCI)
        assert timeline["2026-01-08 10:00:00"] is True

    def test_all_runs_included_even_when_absent(self):
        """All run keys appear in the timeline, including absent runs."""
        history = _h(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
            ("2026-01-15 10:00:00", True),
        )
        timeline = build_species_presence_timeline(history, SCI)

        assert set(timeline.keys()) == {
            "2026-01-01 10:00:00",
            "2026-01-08 10:00:00",
            "2026-01-15 10:00:00",
        }


# ---------------------------------------------------------------------------
# Phase 2 tests: compute_species_current_oos_runs
# ---------------------------------------------------------------------------

class TestComputeSpeciesCurrentOosRuns:
    """OOS runs is the trailing streak of absent runs — not additive."""

    def _timeline_and_runs(self, *run_specs):
        history = _h(*run_specs)
        by_run = group_by_run(history)
        ordered_runs = sorted(by_run.keys())
        timeline = build_species_presence_timeline(history, SCI)
        return timeline, ordered_runs

    def test_zero_when_present_in_current_run(self):
        timeline, runs = self._timeline_and_runs(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", True),
        )
        assert compute_species_current_oos_runs(timeline, runs) == 0

    def test_one_absent_run(self):
        timeline, runs = self._timeline_and_runs(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
        )
        assert compute_species_current_oos_runs(timeline, runs) == 1

    def test_two_consecutive_absent_runs(self):
        timeline, runs = self._timeline_and_runs(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
            ("2026-01-15 10:00:00", False),
        )
        assert compute_species_current_oos_runs(timeline, runs) == 2

    def test_oos_counter_resets_on_re_presence(self):
        """Decision 3A: counter resets on re-presence — not additive across lineages."""
        # size 3 had 1 OOS run, species came back (size 5), then 2 current OOS runs
        timeline, runs = self._timeline_and_runs(
            ("2026-01-01 10:00:00", True),   # size 3 present
            ("2026-01-08 10:00:00", False),  # species absent (OOS run 1 for retired size)
            ("2026-01-15 10:00:00", True),   # size 5 appears — reset!
            ("2026-01-22 10:00:00", False),  # absent (current OOS run 1)
            ("2026-01-29 10:00:00", False),  # absent (current OOS run 2)
        )
        assert compute_species_current_oos_runs(timeline, runs) == 2

    def test_oos_from_beginning_of_history(self):
        """Species never present in recent runs."""
        timeline, runs = self._timeline_and_runs(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
            ("2026-01-15 10:00:00", False),
            ("2026-01-22 10:00:00", False),
            ("2026-01-29 10:00:00", False),
        )
        assert compute_species_current_oos_runs(timeline, runs) == 4


# ---------------------------------------------------------------------------
# Phase 2 tests: build_species_stock_pattern
# ---------------------------------------------------------------------------

class TestBuildSpeciesStockPattern:
    """Stock pattern is derived from species-level presence timeline."""

    def _pattern(self, *run_specs):
        history = _h(*run_specs)
        by_run = group_by_run(history)
        ordered_runs = sorted(by_run.keys())
        timeline = build_species_presence_timeline(history, SCI)
        return build_species_stock_pattern(timeline, ordered_runs)

    def test_sustained_at_four_oos_runs(self):
        pattern = self._pattern(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
            ("2026-01-15 10:00:00", False),
            ("2026-01-22 10:00:00", False),
            ("2026-01-29 10:00:00", False),
        )
        assert pattern == "Sustained"

    def test_emerging_at_two_oos_runs(self):
        pattern = self._pattern(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
            ("2026-01-15 10:00:00", False),
        )
        assert pattern == "Emerging"

    def test_emerging_at_three_oos_runs(self):
        pattern = self._pattern(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
            ("2026-01-15 10:00:00", False),
            ("2026-01-22 10:00:00", False),
        )
        assert pattern == "Emerging"

    def test_cyclical_when_present_now_absent_last_run_seen_before(self):
        """Currently IN, not in previous run, but was present before that."""
        pattern = self._pattern(
            ("2026-01-01 10:00:00", True),  # was present before
            ("2026-01-08 10:00:00", False), # absent last run
            ("2026-01-15 10:00:00", True),  # present now (flapped back)
        )
        assert pattern == "Cyclical"

    def test_always_when_consistently_present(self):
        pattern = self._pattern(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", True),
            ("2026-01-15 10:00:00", True),
        )
        assert pattern == "Always"

    def test_newly_observed_first_time_in_current_run(self):
        """Species first appears in current run only — Newly Observed."""
        pattern = self._pattern(
            ("2026-01-01 10:00:00", False),  # filler run, species absent
            ("2026-01-08 10:00:00", True),   # first observation
        )
        assert pattern == "Newly Observed"

    def test_newly_observed_first_two_consecutive_runs(self):
        """Newly observed for 2 consecutive runs from first appearance."""
        pattern = self._pattern(
            ("2026-01-01 10:00:00", False),
            ("2026-01-08 10:00:00", True),
            ("2026-01-15 10:00:00", True),
        )
        assert pattern == "Newly Observed"

    def test_not_newly_observed_after_three_observed_runs(self):
        pattern = self._pattern(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", True),
            ("2026-01-15 10:00:00", True),
        )
        assert pattern != "Newly Observed"


# ---------------------------------------------------------------------------
# Phase 2 tests: compute_species_stock_reliability
# ---------------------------------------------------------------------------

class TestComputeSpeciesStockReliability:
    """Reliability = presence ratio mapped to High/Medium/Low."""

    def _reliability(self, *run_specs):
        history = _h(*run_specs)
        timeline = build_species_presence_timeline(history, SCI)
        return compute_species_stock_reliability(timeline)

    def test_high_when_all_present(self):
        assert self._reliability(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", True),
            ("2026-01-15 10:00:00", True),
            ("2026-01-22 10:00:00", True),
            ("2026-01-29 10:00:00", True),
        ) == "High"

    def test_high_at_80_percent_presence(self):
        # 8 present out of 10 runs = 80%
        specs = [("2026-01-0{} 10:00:00".format(i + 1), True) for i in range(8)] + [
            ("2026-02-01 10:00:00", False),
            ("2026-02-08 10:00:00", False),
        ]
        assert self._reliability(*specs) == "High"

    def test_medium_at_50_percent_presence(self):
        """5 present / 10 runs = 50% → Medium."""
        specs = []
        for i in range(10):
            present = i % 2 == 0  # every other run
            specs.append((f"2026-01-{i+1:02d} 10:00:00", present))
        assert self._reliability(*specs) == "Medium"

    def test_low_below_40_percent(self):
        """2 present out of 10 runs = 20% → Low."""
        specs = [(f"2026-01-{i+1:02d} 10:00:00", i < 2) for i in range(10)]
        assert self._reliability(*specs) == "Low"


# ---------------------------------------------------------------------------
# Phase 2 tests: compute_species_avg_oos_duration
# ---------------------------------------------------------------------------

class TestComputeSpeciesAvgOosDuration:
    """Avg OOS duration is the average length of absence events."""

    def _avg_oos(self, *run_specs):
        history = _h(*run_specs)
        by_run = group_by_run(history)
        ordered_runs = sorted(by_run.keys())
        timeline = build_species_presence_timeline(history, SCI)
        return compute_species_avg_oos_duration(timeline, ordered_runs)

    def test_zero_when_always_present(self):
        assert self._avg_oos(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", True),
        ) == 0

    def test_single_one_run_absence(self):
        assert self._avg_oos(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
            ("2026-01-15 10:00:00", True),
        ) == 1.0

    def test_single_two_run_absence(self):
        assert self._avg_oos(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),
            ("2026-01-15 10:00:00", False),
            ("2026-01-22 10:00:00", True),
        ) == 2.0

    def test_average_of_two_absence_events(self):
        """Two OOS events: 1 run and 3 runs → avg 2.0."""
        assert self._avg_oos(
            ("2026-01-01 10:00:00", True),
            ("2026-01-08 10:00:00", False),   # event 1: 1 run
            ("2026-01-15 10:00:00", True),
            ("2026-01-22 10:00:00", False),   # event 2: 3 runs
            ("2026-01-29 10:00:00", False),
            ("2026-02-05 10:00:00", False),
            ("2026-02-12 10:00:00", True),
        ) == 2.0

    def test_absence_at_start_of_history(self):
        """Absence at history start counts as an event per existing dealer logic."""
        avg = self._avg_oos(
            ("2026-01-01 10:00:00", False),  # series starts absent
            ("2026-01-08 10:00:00", True),
        )
        assert avg == 1.0


# ---------------------------------------------------------------------------
# Phase 2 tests: compute_species_restock_speed
# ---------------------------------------------------------------------------

class TestComputeSpeciesRestockSpeed:
    """Restock speed is derived from avg OOS duration."""

    def test_fast_for_zero(self):
        assert compute_species_restock_speed(0) == "Fast"

    def test_fast_for_one(self):
        assert compute_species_restock_speed(1.0) == "Fast"

    def test_moderate_for_two(self):
        assert compute_species_restock_speed(2.0) == "Moderate"

    def test_slow_for_three(self):
        assert compute_species_restock_speed(3.0) == "Slow"

    def test_slow_for_greater_than_three(self):
        assert compute_species_restock_speed(4.5) == "Slow"
#!/usr/bin/env python3
"""Tests for shared historical observation metadata helpers."""

from conftest import HistoryEntry

from shared.history_utils import create_observation_coverage, k2


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
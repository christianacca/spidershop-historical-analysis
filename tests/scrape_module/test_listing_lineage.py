#!/usr/bin/env python3
"""Tests for listing lineage detection (Phase 1 - Size Variant Identity)."""

import pytest
from scrape.listing_lineage import LineageResult, detect_species_lineage


# ---------------------------------------------------------------------------
# Helper row builders for lineage tests
# ---------------------------------------------------------------------------

PRODUCT_URL_A = "https://thespidershop.co.uk/product/test-species"
PRODUCT_URL_B = "https://thespidershop.co.uk/product/different-product"


def _row(scrape_datetime, scientific_name, size_cm, url=PRODUCT_URL_A):
    """Create a minimal history row for lineage testing."""
    return {
        "scrape_datetime": scrape_datetime,
        "scientific_name": scientific_name,
        "common_name": "Test Species",
        "size_cm": size_cm,
        "price_gbp": "25.00",
        "wishlist_count": "10",
        "page_url": url,
    }


def _other_row(scrape_datetime):
    """Create a filler row (different species) to anchor a run."""
    return _row(scrape_datetime, "Grammostola pulchra", "2.0",
                url="https://thespidershop.co.uk/product/grammostola-pulchra")


SCI = "Example species"


# ---------------------------------------------------------------------------
# Helper to build a history that also includes filler rows per run
# ---------------------------------------------------------------------------

def _build_history(*run_specs):
    """Build history rows from run specs.

    Each spec is a tuple: (datetime_str, list_of_sizes_or_empty)
    Sizes is a list of (size_cm, url) pairs. Empty list = species absent.
    A filler row is always added per run so the run exists in by_run.
    """
    rows = []
    for dt, size_specs in run_specs:
        rows.append(_other_row(dt))
        for size_cm, url in size_specs:
            rows.append(_row(dt, SCI, size_cm, url))
    return rows


# ---------------------------------------------------------------------------
# Scenario: none – only one size ever observed
# ---------------------------------------------------------------------------

class TestNoneLineage:
    """Species with a single historically observed size yields 'none' status."""

    def test_single_size_in_current_run(self):
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-15 10:00:00", [("3", PRODUCT_URL_A)]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "none"
        assert result.previous_size == ""
        assert result.current_active_size == "3"
        assert result.transition_date == ""
        assert result.price_evidence_state == "standard"
        assert result.wishlist_evidence_state == "standard"
        assert result.transition_message == ""

    def test_single_size_currently_out(self):
        """Single size, species is OUT in current run — still 'none'."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-15 10:00:00", []),  # OUT
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "none"
        assert result.previous_size == ""
        assert result.current_active_size == "3"
        assert result.price_evidence_state == "standard"
        assert result.wishlist_evidence_state == "standard"


# ---------------------------------------------------------------------------
# Scenario: confirmed-transition (all 5 conditions met)
# ---------------------------------------------------------------------------

class TestConfirmedTransition:
    """All 5 conditions satisfied → confirmed-transition."""

    def test_basic_confirmed_transition_3_to_5(self):
        """Old 3cm → new 5cm, same URL, within 1 run, no overlap."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("3", PRODUCT_URL_A)]),
            # Handoff: 3cm gone, 5cm appears
            ("2026-02-04 10:00:00", [("5", PRODUCT_URL_A)]),
            ("2026-02-11 10:00:00", [("5", PRODUCT_URL_A)]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "confirmed-transition"
        assert result.previous_size == "3"
        assert result.current_active_size == "5"
        assert result.transition_date == "2026-02-04"
        assert result.price_evidence_state == "transition-affected"
        assert result.wishlist_evidence_state == "carried-across-transition"

    def test_confirmed_transition_message_format(self):
        """Transition message matches spec wording exactly."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-02-04 10:00:00", [("5", PRODUCT_URL_A)]),
        )
        result = detect_species_lineage(history, SCI)

        expected_msg = (
            "Size changed from 3 cm to 5 cm on 2026-02-04. "
            "Wishlist continuity is treated as continuous for this listing. "
            "Price evidence is still useful, but recent movement may partly "
            "reflect the size change rather than a pure same-unit price move."
        )
        assert result.transition_message == expected_msg

    def test_confirmed_transition_within_12_run_window(self):
        """New size appears exactly 3 runs after old size's final run — well within the 12-run window."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),   # idx 0
            ("2026-01-08 10:00:00", []),                        # idx 1 (gap 1)
            ("2026-01-15 10:00:00", []),                        # idx 2 (gap 2)
            ("2026-01-22 10:00:00", [("5", PRODUCT_URL_A)]),   # idx 3 (gap = 3-0 = 3, within 12-run window)
        )
        result = detect_species_lineage(history, SCI)
        assert result.lineage_status == "confirmed-transition"

    def test_confirmed_transition_url_normalized_for_comparison(self):
        """URLs that differ only by case/www/trailing-slash still match."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", "HTTPS://WWW.thespidershop.co.uk/product/foo/")]),
            ("2026-01-08 10:00:00", [("5", "https://thespidershop.co.uk/product/foo")]),
        )
        result = detect_species_lineage(history, SCI)
        assert result.lineage_status == "confirmed-transition"


# ---------------------------------------------------------------------------
# Scenario: ambiguous-transition conditions
# ---------------------------------------------------------------------------

class TestAmbiguousTransition:
    """Any failing condition degrades the transition to ambiguous."""

    def _ambiguous_message(self, prev, current, date):
        return (
            f"Size handoff from {prev} cm to {current} cm could not be confirmed "
            "as one continuing listing. Wishlist continuity is not carried across "
            "the handoff. Price and momentum evidence are shown in a conservative "
            "downgraded state."
        )

    def test_ambiguous_from_url_mismatch(self):
        """Different normalized URLs → ambiguous."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("5", PRODUCT_URL_B)]),  # different URL
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "ambiguous-transition"
        assert result.previous_size == "3"
        assert result.current_active_size == "5"
        assert result.price_evidence_state == "neutralized"
        assert result.wishlist_evidence_state == "neutralized-ambiguous"
        assert result.transition_message == self._ambiguous_message("3", "5", "2026-01-08")

    def test_ambiguous_from_gap_greater_than_12(self):
        """Gap > 12 runs → ambiguous."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),    # idx 0
            ("2026-01-08 10:00:00", []),                         # idx 1
            ("2026-01-15 10:00:00", []),                         # idx 2
            ("2026-01-22 10:00:00", []),                         # idx 3
            ("2026-01-29 10:00:00", []),                         # idx 4
            ("2026-02-05 10:00:00", []),                         # idx 5
            ("2026-02-12 10:00:00", []),                         # idx 6
            ("2026-02-19 10:00:00", []),                         # idx 7
            ("2026-02-26 10:00:00", []),                         # idx 8
            ("2026-03-05 10:00:00", []),                         # idx 9
            ("2026-03-12 10:00:00", []),                         # idx 10
            ("2026-03-19 10:00:00", []),                         # idx 11
            ("2026-03-26 10:00:00", []),                         # idx 12
            ("2026-04-02 10:00:00", [("5", PRODUCT_URL_A)]),    # idx 13 — gap=13 > 12
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "ambiguous-transition"

    def test_ambiguous_from_same_run_overlap(self):
        """Both sizes present in same run during handoff → ambiguous."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            # Both present at same time — overlap!
            ("2026-01-08 10:00:00", [("3", PRODUCT_URL_A), ("5", PRODUCT_URL_A)]),
            ("2026-01-15 10:00:00", [("5", PRODUCT_URL_A)]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "ambiguous-transition"

    def test_ambiguous_from_missing_url_on_old_size(self):
        """Blank URL on old size → cannot satisfy URL gate → ambiguous."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", "")]),          # blank URL
            ("2026-01-08 10:00:00", [("5", PRODUCT_URL_A)]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "ambiguous-transition"

    def test_ambiguous_from_blank_url_on_new_size(self):
        """Blank URL on new size → ambiguous."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("5", "")]),           # blank URL
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "ambiguous-transition"

    def test_ambiguous_transition_date_recorded(self):
        """Transition date is the date of the first new size run even for ambiguous."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-02-04 10:00:00", [("5", PRODUCT_URL_B)]),  # URL mismatch
        )
        result = detect_species_lineage(history, SCI)

        assert result.transition_date == "2026-02-04"

    def test_ambiguous_previous_size_and_current_size_populated(self):
        """Previous size and current active size populated for ambiguous."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("5", PRODUCT_URL_B)]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.previous_size == "3"
        assert result.current_active_size == "5"


# ---------------------------------------------------------------------------
# Scenario: multi-variant (two+ sizes active in current run)
# ---------------------------------------------------------------------------

class TestMultiVariant:
    """Two or more sizes in the current run → multi-variant state."""

    def test_two_sizes_in_current_run(self):
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [
                ("3", PRODUCT_URL_A),
                ("5", PRODUCT_URL_A),
            ]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "multi-variant"
        assert result.previous_size == ""
        assert result.current_active_size == "3, 5"
        assert result.transition_date == ""
        assert result.price_evidence_state == "multi-variant"
        assert result.wishlist_evidence_state == "max-active-variant"

    def test_current_active_size_comma_separated_ascending(self):
        """Sizes in comma-separated ascending string for multi-variant."""
        history = _build_history(
            ("2026-01-01 10:00:00", [
                ("5", PRODUCT_URL_A),
                ("3", PRODUCT_URL_A),
            ]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.current_active_size == "3, 5"

    def test_multi_variant_message_format(self):
        """Multi-variant transition message matches spec wording."""
        history = _build_history(
            ("2026-01-01 10:00:00", [
                ("3", PRODUCT_URL_A),
                ("5", PRODUCT_URL_A),
            ]),
        )
        result = detect_species_lineage(history, SCI)

        expected_msg = (
            "This species has multiple active size variants in the current run "
            "(3 cm and 5 cm). The row remains species-level. Current wishlist "
            "context uses the highest active variant count without summing listings. "
            "Price evidence is not shown as one clean single-line series."
        )
        assert result.transition_message == expected_msg

    def test_multi_variant_overrides_prior_confirmed_transition(self):
        """Even if there was a confirmed transition in history, multi-variant wins."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("5", PRODUCT_URL_A)]),  # confirmed 3→5
            # Current run has both 5cm and 7cm → multi-variant
            ("2026-01-15 10:00:00", [
                ("5", PRODUCT_URL_A),
                ("7", PRODUCT_URL_A),
            ]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "multi-variant"
        assert result.current_active_size == "5, 7"

    def test_multi_variant_overrides_ambiguous_transition(self):
        """Multi-variant in current run still takes precedence over ambiguous."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("5", PRODUCT_URL_B)]),  # ambiguous (URL mismatch)
            ("2026-01-15 10:00:00", [
                ("5", PRODUCT_URL_B),
                ("7", PRODUCT_URL_A),
            ]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "multi-variant"


# ---------------------------------------------------------------------------
# Precedence rule: multi-variant > ambiguous > confirmed > none
# ---------------------------------------------------------------------------

class TestPrecedence:
    """Explicit precedence checks covering all pairs."""

    def test_ambiguous_beats_confirmed_when_url_mismatch(self):
        """Ambiguous result is returned when confirmed criteria fail."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("5", PRODUCT_URL_B)]),  # URL mismatch
        )
        result = detect_species_lineage(history, SCI)
        assert result.lineage_status == "ambiguous-transition"

    def test_multi_variant_beats_all_others(self):
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("5", PRODUCT_URL_B)]),  # would be ambiguous
            ("2026-01-15 10:00:00", [
                ("5", PRODUCT_URL_B),
                ("3", PRODUCT_URL_A),  # both sizes back — multi-variant
            ]),
        )
        result = detect_species_lineage(history, SCI)
        assert result.lineage_status == "multi-variant"


# ---------------------------------------------------------------------------
# Sequential transitions (3→5→7): only most recent event reported
# ---------------------------------------------------------------------------

class TestSequentialTransitions:
    """Sequential confirmed transitions report only the most recent event."""

    def test_sequential_transitions_report_most_recent_only(self):
        """3→5→7: Previous Size=5, Current Active Size=7."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("5", PRODUCT_URL_A)]),  # 3→5 confirmed
            ("2026-01-15 10:00:00", [("7", PRODUCT_URL_A)]),  # 5→7 confirmed
        )
        result = detect_species_lineage(history, SCI)

        assert result.lineage_status == "confirmed-transition"
        assert result.previous_size == "5"
        assert result.current_active_size == "7"
        assert result.transition_date == "2026-01-15"

    def test_sequential_transitions_transition_date_is_most_recent(self):
        """Transition date is the date of the most recent handoff, not the first."""
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-02-04 10:00:00", [("5", PRODUCT_URL_A)]),
            ("2026-03-01 10:00:00", [("7", PRODUCT_URL_A)]),
        )
        result = detect_species_lineage(history, SCI)

        assert result.transition_date == "2026-03-01"
        assert result.previous_size == "5"


# ---------------------------------------------------------------------------
# Metadata field contracts
# ---------------------------------------------------------------------------

class TestMetadataFieldsForNone:
    """For 'none' state, previous_size and transition_date are blank."""

    def test_previous_size_is_blank_for_none(self):
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
        )
        result = detect_species_lineage(history, SCI)
        assert result.lineage_status == "none"
        assert result.previous_size == ""
        assert result.transition_date == ""

    def test_current_active_size_is_current_size_for_none(self):
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A)]),
            ("2026-01-08 10:00:00", [("3", PRODUCT_URL_A)]),
        )
        result = detect_species_lineage(history, SCI)
        assert result.current_active_size == "3"


class TestMetadataFieldsForMultiVariant:
    """For 'multi-variant' state, previous_size and transition_date are blank."""

    def test_previous_size_is_blank_for_multi_variant(self):
        history = _build_history(
            ("2026-01-01 10:00:00", [("3", PRODUCT_URL_A), ("5", PRODUCT_URL_A)]),
        )
        result = detect_species_lineage(history, SCI)
        assert result.lineage_status == "multi-variant"
        assert result.previous_size == ""
        assert result.transition_date == ""

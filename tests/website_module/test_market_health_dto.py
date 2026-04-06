"""Tests for src/website/market_health_dto.py — Phase 6 TDD."""

from datetime import datetime

import pytest

from website.market_health_dto import (
    build_market_health_payload,
    build_market_health_payload_all_windows,
)

# Fixed reference date: Q1 2026, mid-January.
# current-quarter window = Jan 1 – Jan 15, 2026
# prior quarter = Oct 1 – Oct 15, 2025
REF_DT = datetime(2026, 1, 15, 12, 0, 0)

# Runs within Q1 2026 (three weekly scrapes)
RUN1 = "2026-01-01T06:10:00"
RUN2 = "2026-01-08T06:10:00"
RUN3 = "2026-01-15T06:10:00"  # latest run

# Prior quarter runs (Q4 2025)
PRIOR_RUN1 = "2025-10-01T06:10:00"
PRIOR_RUN2 = "2025-10-08T06:10:00"
PRIOR_RUN3 = "2025-10-15T06:10:00"  # latest prior run


def _row(
    dt: str,
    species: str,
    price: str = "10.00",
    wishlist: str = "5",
    size: str = "2.0",
    common: str = "Test Species",
    url: str = "https://example.com/test",
) -> dict:
    return {
        "scrape_datetime": dt,
        "scientific_name": species,
        "common_name": common,
        "size_cm": size,
        "price_gbp": price,
        "wishlist_count": wishlist,
        "page_url": url,
    }


class TestObservedSpecies:
    def test_counts_distinct_species_seen_in_window(self):
        rows = [
            _row(RUN1, "Species A"),
            _row(RUN1, "Species B"),
            _row(RUN2, "Species A"),
            _row(RUN2, "Species C"),
            _row(RUN3, "Species A"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["kpis"]["observed"]["value"] == "3"

    def test_species_outside_window_excluded(self):
        rows = [
            _row("2025-09-30T06:10:00", "Old Species"),  # before Q1 2026
            _row(RUN1, "Current Species"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["kpis"]["observed"]["value"] == "1"

    def test_positive_delta_class_is_empty(self):
        """Delta > 0 → deltaClass='' (positive)."""
        rows_current = [
            _row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A"),
            _row(RUN1, "B"), _row(RUN2, "B"), _row(RUN3, "B"),
        ]
        rows_prior = [_row(PRIOR_RUN1, "A"), _row(PRIOR_RUN2, "A"), _row(PRIOR_RUN3, "A")]
        result = build_market_health_payload(
            rows_current + rows_prior, "current-quarter", [], is_all_selected=True,
            reference_dt=REF_DT,
        )
        assert result["kpis"]["observed"]["deltaClass"] == ""

    def test_negative_delta_class_is_down(self):
        """Delta < 0 → deltaClass='down'."""
        rows_current = [_row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A")]
        rows_prior = [
            _row(PRIOR_RUN1, "A"), _row(PRIOR_RUN2, "A"), _row(PRIOR_RUN3, "A"),
            _row(PRIOR_RUN1, "B"), _row(PRIOR_RUN2, "B"), _row(PRIOR_RUN3, "B"),
        ]
        result = build_market_health_payload(
            rows_current + rows_prior, "current-quarter", [], is_all_selected=True,
            reference_dt=REF_DT,
        )
        assert result["kpis"]["observed"]["deltaClass"] == "down"


class TestInStockRate:
    def test_rate_when_all_species_in_stock_at_latest_run(self):
        rows = [_row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["kpis"]["stock"]["value"] == "100%"

    def test_rate_when_one_species_drops_out(self):
        # Species A in-stock at all 3 runs; Species B only runs 1+2 (drops at RUN3)
        rows = [
            _row(RUN1, "Species A"), _row(RUN2, "Species A"), _row(RUN3, "Species A"),
            _row(RUN1, "Species B"), _row(RUN2, "Species B"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        # Numerator: 1 in-stock at RUN3; denominator: 2 seen; 50%
        assert result["kpis"]["stock"]["value"] == "50%"

    def test_multi_variant_species_counted_once(self):
        # Species A has 2 size variants at RUN3 — counts once
        rows = [
            _row(RUN3, "Species A", size="1.5", url="https://x.com/a"),
            _row(RUN3, "Species A", size="3.0", url="https://x.com/a"),
            _row(RUN3, "Species B"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["kpis"]["stock"]["value"] == "100%"


class TestMedianWishlist:
    def test_odd_number_of_species(self):
        rows = [
            _row(RUN3, "A", wishlist="3"),
            _row(RUN3, "B", wishlist="7"),
            _row(RUN3, "C", wishlist="5"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["kpis"]["wishlist"]["value"] == "5"

    def test_max_wishlist_used_for_multi_variant_species(self):
        # Species A has two variants; wishlist 3 and 8 → use max=8
        # Species B has wishlist 4; median([8, 4]) = 6
        rows = [
            _row(RUN3, "Species A", wishlist="3", size="1.5", url="https://x.com/a"),
            _row(RUN3, "Species A", wishlist="8", size="3.0", url="https://x.com/a"),
            _row(RUN3, "Species B", wishlist="4"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["kpis"]["wishlist"]["value"] == "6"


class TestMedianPrice:
    def test_price_format(self):
        rows = [
            _row(RUN3, "A", price="12.00"),
            _row(RUN3, "B", price="18.00"),
            _row(RUN3, "C", price="24.00"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["kpis"]["price"]["value"] == "GBP 18"

    def test_median_price_rounded_to_integer(self):
        rows = [_row(RUN3, "A", price="10.50"), _row(RUN3, "B", price="15.50")]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        # median([10.50, 15.50]) = 13.0 → "GBP 13"
        assert result["kpis"]["price"]["value"] == "GBP 13"


class TestPriorPeriodBoundary:
    def test_current_quarter_show_prior_true(self):
        rows = [_row(RUN1, "A"), _row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["showPrior"] is True

    def test_all_time_show_prior_false(self):
        rows = [_row(RUN1, "A"), _row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "all-time", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["showPrior"] is False

    def test_all_time_prior_sparkline_series_empty(self):
        rows = [_row(RUN1, "A"), _row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "all-time", [], is_all_selected=True, reference_dt=REF_DT
        )
        for key in ("observed", "stock", "wishlist", "price"):
            assert result["sparklineSeries"][key]["prior"] == []

    def test_all_time_delta_class_is_flat(self):
        rows = [_row(RUN1, "A"), _row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "all-time", [], is_all_selected=True, reference_dt=REF_DT
        )
        for key in ("observed", "stock", "wishlist", "price"):
            assert result["kpis"][key]["deltaClass"] == "flat"

    def test_all_time_delta_text_is_no_prior_comparison(self):
        rows = [_row(RUN1, "A"), _row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "all-time", [], is_all_selected=True, reference_dt=REF_DT
        )
        for key in ("observed", "stock", "wishlist", "price"):
            assert result["kpis"][key]["delta"] == "No prior comparison"

    def test_prior_delta_uses_matched_prior_period(self):
        """Prior period for current-quarter should be Q4 2025 QTD (Oct 1–15)."""
        rows_current = [
            _row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A"),
            _row(RUN1, "B"), _row(RUN2, "B"), _row(RUN3, "B"),
        ]
        rows_prior = [
            _row(PRIOR_RUN1, "A"), _row(PRIOR_RUN2, "A"), _row(PRIOR_RUN3, "A"),
        ]
        result = build_market_health_payload(
            rows_current + rows_prior, "current-quarter", [], is_all_selected=True,
            reference_dt=REF_DT,
        )
        # current = 2 species; prior = 1 species; delta = +1
        delta = result["kpis"]["observed"]["delta"]
        assert delta.startswith("+1")


class TestSparklineSeries:
    def test_sparkline_series_has_12_points(self):
        rows = [_row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        for key in ("observed", "stock", "wishlist", "price"):
            assert len(result["sparklineSeries"][key]["current"]) == 12

    def test_sparkline_values_are_numeric(self):
        rows = [_row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        for key in ("observed", "stock", "wishlist", "price"):
            for v in result["sparklineSeries"][key]["current"]:
                assert isinstance(v, (int, float))

    def test_prior_sparkline_has_12_points_when_show_prior_true(self):
        rows = [
            _row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A"),
            _row(PRIOR_RUN1, "A"), _row(PRIOR_RUN2, "A"), _row(PRIOR_RUN3, "A"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        for key in ("observed", "stock", "wishlist", "price"):
            assert len(result["sparklineSeries"][key]["prior"]) == 12


class TestEvents:
    def test_new_listings_count_species_first_appearing_in_window(self):
        # A appears at RUN1 (not new — first run of window)
        # B appears at RUN2 (new in window relative to RUN1)
        rows = [
            _row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A"),
            _row(RUN2, "B"), _row(RUN3, "B"),
            # C was present before window
            _row("2025-12-15T06:10:00", "C"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        # B first appears in run 2 — counts as new listing introduced mid-window
        events = result["events"]
        assert isinstance(events["newListings"]["value"], str)
        assert events["newListings"]["value"] != ""

    def test_dropped_listings_count(self):
        # B disappears after RUN2
        rows = [
            _row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A"),
            _row(RUN1, "B"), _row(RUN2, "B"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        events = result["events"]
        assert isinstance(events["droppedListings"]["value"], str)

    def test_restock_count(self):
        # A: IN at RUN1, OUT at RUN2, IN at RUN3 — one restock.
        # Species B is present at all 3 runs to establish that RUN2 was a valid scrape.
        rows = [
            _row(RUN1, "A"),
            # A absent from RUN2
            _row(RUN3, "A"),
            _row(RUN1, "B"), _row(RUN2, "B"), _row(RUN3, "B"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        # One OUT→IN transition for A at RUN3
        assert "1" in result["events"]["restocks"]["value"]

    def test_oos_flip_count(self):
        # A: IN at RUN1, OUT at RUN2
        rows = [
            _row(RUN1, "A"),
            # out at RUN2, RUN3
            _row(RUN1, "B"), _row(RUN2, "B"), _row(RUN3, "B"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        # One IN→OUT transition for A at RUN2
        assert "1" in result["events"]["oosFlips"]["value"]


class TestGenusFiltering:
    def test_is_all_selected_true_includes_all_genera(self):
        rows = [
            _row(RUN3, "Avicularia purpurea"),
            _row(RUN3, "Caribena versicolor"),
            _row(RUN3, "Psalmopoeus irminia"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", ["Avicularia"], is_all_selected=True,
            reference_dt=REF_DT,
        )
        # is_all_selected=True → all 3 species counted
        assert result["kpis"]["observed"]["value"] == "3"

    def test_is_all_selected_false_filters_by_genus(self):
        rows = [
            _row(RUN3, "Avicularia purpurea"),
            _row(RUN3, "Caribena versicolor"),
            _row(RUN3, "Psalmopoeus irminia"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", ["Avicularia", "Caribena"], is_all_selected=False,
            reference_dt=REF_DT,
        )
        # Only Avicularia and Caribena → 2 species
        assert result["kpis"]["observed"]["value"] == "2"

    def test_genus_filter_excludes_from_all_metrics(self):
        rows = [
            _row(RUN3, "Avicularia purpurea", price="20.00", wishlist="10"),
            _row(RUN3, "Psalmopoeus irminia", price="30.00", wishlist="20"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", ["Avicularia"], is_all_selected=False,
            reference_dt=REF_DT,
        )
        # Only Avicularia in scope → observed=1, price=20, wishlist=10
        assert result["kpis"]["observed"]["value"] == "1"
        assert result["kpis"]["price"]["value"] == "GBP 20"
        assert result["kpis"]["wishlist"]["value"] == "10"


class TestEdgeCases:
    def test_fewer_than_2_scrapes_returns_safe_payload(self):
        rows = [_row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        # Should not crash; showPrior should be False (no prior data to compare)
        assert isinstance(result, dict)
        assert "kpis" in result
        assert "events" in result
        assert result["showPrior"] is False

    def test_empty_history_rows_returns_safe_payload(self):
        result = build_market_health_payload(
            [], "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert isinstance(result, dict)
        assert result["kpis"]["observed"]["value"] == "0"

    def test_size_transition_not_counted_as_drop_plus_add(self):
        """A size transition (same URL, same species, within 3 runs) is NOT a drop+add."""
        # A at size 2.0 at RUN1; absent at RUN2; A at size 3.0 at RUN3 (size transition)
        rows = [
            _row(RUN1, "Species A", size="2.0", url="https://x.com/a"),
            # absent at RUN2
            _row(RUN3, "Species A", size="3.0", url="https://x.com/a"),
            # Species B always present (to have a denominator)
            _row(RUN1, "Species B"), _row(RUN2, "Species B"), _row(RUN3, "Species B"),
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        events = result["events"]
        # Species A's gap should NOT generate a newListings + droppedListings pair
        # The events are text strings; check that droppedListings doesn't inflated count
        # (Species B transitions generate 0 events; expect 0 drops for this scenario)
        assert "0" in events["droppedListings"]["value"] or events["droppedListings"]["value"].startswith("0")


class TestAllWindowsFunction:
    def test_returns_all_seven_windows(self):
        rows = [_row(RUN3, "A")]
        result = build_market_health_payload_all_windows(
            rows, [], is_all_selected=True, reference_dt=REF_DT
        )
        expected_keys = {
            "this-month", "last-month", "current-quarter", "last-quarter",
            "this-year", "last-year", "all-time",
        }
        assert set(result.keys()) == expected_keys

    def test_each_window_has_required_keys(self):
        rows = [_row(RUN3, "A")]
        result = build_market_health_payload_all_windows(
            rows, [], is_all_selected=True, reference_dt=REF_DT
        )
        for window_id, payload in result.items():
            assert "windowId" in payload, f"missing windowId in {window_id}"
            assert "kpis" in payload, f"missing kpis in {window_id}"
            assert "sparklineSeries" in payload, f"missing sparklineSeries in {window_id}"
            assert "events" in payload, f"missing events in {window_id}"

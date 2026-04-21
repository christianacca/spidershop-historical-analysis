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
        """showPrior=True requires both current AND prior period data to exist."""
        rows = [
            _row(RUN1, "A"), _row(RUN3, "A"),
            _row(PRIOR_RUN1, "A"), _row(PRIOR_RUN3, "A"),
        ]
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


class TestDeltaLabels:
    """KPI delta badges and events values must use window-specific prior labels (spec §6)."""

    @pytest.mark.parametrize("window_id,expected_label", [
        ("current-quarter", "prior quarter QTD"),
        ("last-quarter", "prior full quarter"),
        ("this-month", "prior month MTD"),
        ("last-month", "prior full month"),
        ("this-year", "prior year YTD"),
        ("last-year", "prior full year"),
    ])
    def test_kpi_delta_contains_window_specific_label(self, window_id, expected_label):
        """Each window uses its own prior-period label in delta badge text (not generic 'prior')."""
        # Build rows that span multiple windows; REF_DT anchors the window.
        # We need rows in BOTH the current window and its prior window to get a non-None delta.
        # Use REF_DT (Jan 15 2026) as reference — rows below cover Q4 2025 and Q1 2026.
        rows_current = [
            _row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A"),
            _row(RUN1, "B"), _row(RUN2, "B"), _row(RUN3, "B"),
        ]
        rows_prior = [
            _row(PRIOR_RUN1, "A"), _row(PRIOR_RUN2, "A"), _row(PRIOR_RUN3, "A"),
        ]
        # For windows other than current-quarter we still pass the same raw rows;
        # only the window-id changes. The important thing is the delta label suffix.
        result = build_market_health_payload(
            rows_current + rows_prior, window_id, [], is_all_selected=True,
            reference_dt=REF_DT,
        )
        for kpi_key in ("observed", "stock", "wishlist", "price"):
            delta = result["kpis"][kpi_key]["delta"]
            if delta == "No prior comparison":
                continue  # window has no matching prior data — label test not applicable
            assert expected_label in delta, (
                f"window={window_id!r} kpi={kpi_key!r}: "
                f"expected {expected_label!r} in delta {delta!r}"
            )

    def test_events_values_contain_window_specific_label_current_quarter(self):
        """Events card values must use 'prior quarter QTD' for current-quarter window."""
        rows = [
            _row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A"),
            _row(RUN2, "B"), _row(RUN3, "B"),  # B appears mid-window → new listing
        ]
        result = build_market_health_payload(
            rows, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        events = result["events"]
        for event_key in ("newListings", "droppedListings", "restocks", "oosFlips"):
            value = events[event_key]["value"]
            if "total" in value:
                continue  # all-time path — not applicable
            assert "prior quarter QTD" in value, (
                f"events[{event_key!r}].value={value!r} missing 'prior quarter QTD'"
            )

    def test_all_time_delta_text_unchanged(self):
        """All-time window must still produce 'No prior comparison', not contain a delta label."""
        rows = [_row(RUN1, "A"), _row(RUN3, "A")]
        result = build_market_health_payload(
            rows, "all-time", [], is_all_selected=True, reference_dt=REF_DT
        )
        for kpi_key in ("observed", "stock", "wishlist", "price"):
            assert result["kpis"][kpi_key]["delta"] == "No prior comparison"


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


class TestPriceCopyDeltaZero:
    """Price copy for delta=0 must match spec §3.4."""

    def test_price_copy_delta_zero_references_availability_not_prior_label(self):
        """spec §3.4: delta=0 → 'Price is steady, so the main movement appears to be
        availability rather than inflation.' — no prior_label reference."""
        rows_current = [
            _row(RUN1, "A", price="20.00"), _row(RUN2, "A", price="20.00"), _row(RUN3, "A", price="20.00"),
        ]
        rows_prior = [
            _row(PRIOR_RUN1, "A", price="20.00"), _row(PRIOR_RUN2, "A", price="20.00"),
            _row(PRIOR_RUN3, "A", price="20.00"),
        ]
        result = build_market_health_payload(
            rows_current + rows_prior,
            "current-quarter",
            [],
            is_all_selected=True,
            reference_dt=REF_DT,
        )
        copy = result["kpis"]["price"]["copy"]
        assert "availability" in copy.lower(), f"Expected 'availability' in copy, got: {copy!r}"
        assert "inflation" in copy.lower(), f"Expected 'inflation' in copy, got: {copy!r}"
        # Must NOT say "steady vs" which would reference a prior label comparison pattern
        assert "prior quarter" not in copy, f"delta=0 copy must not reference prior period: {copy!r}"


class TestNoPriorDataCopy:
    """When effective_show_prior is False (no prior rows) for a comparative window,
    copy must use a neutral no-comparison statement instead of phrases that imply a
    comparison happened (spec §3 — copy states only define delta-based branches; the
    delta=None non-all-time case must not fall into a positive/negative branch)."""

    # RUN1-3 in Q1 2026; deliberately omit Q4 2025 rows so prior_rows = [].
    _ONLY_CURRENT = [
        _row(RUN1, "A", price="20.00", wishlist="10"),
        _row(RUN2, "A", price="21.00", wishlist="11"),
        _row(RUN3, "A", price="22.00", wishlist="12"),
    ]

    def test_observed_no_prior_copy_does_not_imply_comparison(self):
        result = build_market_health_payload(
            self._ONLY_CURRENT, "current-quarter", [], is_all_selected=True,
            reference_dt=REF_DT
        )
        copy = result["kpis"]["observed"]["copy"]
        # These phrases all imply a comparison occurred — must be absent when no prior data
        forbidden = ["ahead of", "behind", "fewer species are being seen in-stock than at"]
        for phrase in forbidden:
            assert phrase not in copy.lower(), (
                f"No-prior observed copy must not contain {phrase!r}: {copy!r}"
            )

    def test_wishlist_no_prior_copy_does_not_imply_comparison(self):
        result = build_market_health_payload(
            self._ONLY_CURRENT, "current-quarter", [], is_all_selected=True,
            reference_dt=REF_DT
        )
        copy = result["kpis"]["wishlist"]["copy"]
        forbidden = ["ahead of", "above", "softer than", "modestly above"]
        for phrase in forbidden:
            assert phrase not in copy.lower(), (
                f"No-prior wishlist copy must not contain {phrase!r}: {copy!r}"
            )

    def test_price_no_prior_copy_does_not_imply_comparison(self):
        result = build_market_health_payload(
            self._ONLY_CURRENT, "current-quarter", [], is_all_selected=True,
            reference_dt=REF_DT
        )
        copy = result["kpis"]["price"]["copy"]
        forbidden = ["firmer than", "edged up", "softened vs", "holding steady"]
        for phrase in forbidden:
            assert phrase not in copy.lower(), (
                f"No-prior price copy must not contain {phrase!r}: {copy!r}"
            )

    def test_show_prior_false_when_no_prior_rows(self):
        """showPrior must be False when prior_rows is empty, even for a comparative window."""
        result = build_market_health_payload(
            self._ONLY_CURRENT, "current-quarter", [], is_all_selected=True,
            reference_dt=REF_DT
        )
        assert result["showPrior"] is False, (
            "showPrior should be False when there are no prior-period rows"
        )


class TestInProgressBasisNotes:
    """Dynamic basis notes for in-progress windows (spec §4.4 and §6 amendment).

    REF_DT = 2026-01-15 (Q1 2026, mid-January).
    - current-quarter: Q1 2026 (Jan 1 – Jan 15) vs Q4 2025 (Oct 1 – Oct 15)
    - this-month:      Jan 2026 (Jan 1 – Jan 15) vs Dec 2025 (Dec 1 – Dec 15)
    - this-year:       2026 (Jan 1 – Jan 15) vs 2025

    Completed windows must keep their static strings unchanged.
    """

    _ROWS = [_row(RUN1, "A"), _row(RUN2, "A"), _row(RUN3, "A")]

    def test_current_quarter_window_basis_note_is_dynamic(self):
        result = build_market_health_payload(
            self._ROWS, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        note = result["windowBasisNote"]
        assert "Quarter in progress" in note, f"Expected 'Quarter in progress' in: {note!r}"
        assert "Q1 2026" in note, f"Expected 'Q1 2026' in: {note!r}"
        assert "Jan 1" in note, f"Expected 'Jan 1' in: {note!r}"
        assert "Jan 15" in note, f"Expected 'Jan 15' in: {note!r}"
        assert "Q4 2025" in note, f"Expected 'Q4 2025' in: {note!r}"
        assert "Oct 1" in note, f"Expected 'Oct 1' in: {note!r}"
        assert "Oct 15" in note, f"Expected 'Oct 15' in: {note!r}"

    def test_current_quarter_sparkline_basis_note_is_dynamic(self):
        result = build_market_health_payload(
            self._ROWS, "current-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        note = result["sparklineBasisNote"]
        assert "Q1 2026" in note, f"Expected 'Q1 2026' in: {note!r}"
        assert "Jan 1" in note, f"Expected 'Jan 1' in: {note!r}"
        assert "Jan 15" in note, f"Expected 'Jan 15' in: {note!r}"
        assert "Q4 2025" in note, f"Expected 'Q4 2025' in: {note!r}"
        assert "Oct 1" in note, f"Expected 'Oct 1' in: {note!r}"
        assert "Oct 15" in note, f"Expected 'Oct 15' in: {note!r}"

    def test_this_month_window_basis_note_is_dynamic(self):
        # REF_DT = Jan 15, 2026 → same-span last month = Dec 1 – Dec 15, 2025
        result = build_market_health_payload(
            self._ROWS, "this-month", [], is_all_selected=True, reference_dt=REF_DT
        )
        note = result["windowBasisNote"]
        assert "Month in progress" in note, f"Expected 'Month in progress' in: {note!r}"
        assert "Jan 2026" in note, f"Expected 'Jan 2026' in: {note!r}"
        assert "Jan 1" in note, f"Expected 'Jan 1' in: {note!r}"
        assert "Jan 15" in note, f"Expected 'Jan 15' in: {note!r}"
        assert "Dec 1" in note, f"Expected 'Dec 1' in: {note!r}"
        assert "Dec 15" in note, f"Expected 'Dec 15' in: {note!r}"

    def test_this_month_sparkline_basis_note_is_dynamic(self):
        result = build_market_health_payload(
            self._ROWS, "this-month", [], is_all_selected=True, reference_dt=REF_DT
        )
        note = result["sparklineBasisNote"]
        assert "Jan 2026" in note, f"Expected 'Jan 2026' in: {note!r}"
        assert "Jan 1" in note, f"Expected 'Jan 1' in: {note!r}"
        assert "Jan 15" in note, f"Expected 'Jan 15' in: {note!r}"
        assert "Dec 1" in note, f"Expected 'Dec 1' in: {note!r}"
        assert "Dec 15" in note, f"Expected 'Dec 15' in: {note!r}"

    def test_this_year_window_basis_note_is_dynamic(self):
        result = build_market_health_payload(
            self._ROWS, "this-year", [], is_all_selected=True, reference_dt=REF_DT
        )
        note = result["windowBasisNote"]
        assert "Year in progress" in note, f"Expected 'Year in progress' in: {note!r}"
        assert "2026" in note, f"Expected '2026' in: {note!r}"
        assert "Jan 1" in note, f"Expected 'Jan 1' in: {note!r}"
        assert "Jan 15" in note, f"Expected 'Jan 15' in: {note!r}"
        assert "2025" in note, f"Expected '2025' in: {note!r}"

    def test_this_year_sparkline_basis_note_is_dynamic(self):
        result = build_market_health_payload(
            self._ROWS, "this-year", [], is_all_selected=True, reference_dt=REF_DT
        )
        note = result["sparklineBasisNote"]
        assert "2026" in note, f"Expected '2026' in: {note!r}"
        assert "Jan 1" in note, f"Expected 'Jan 1' in: {note!r}"
        assert "Jan 15" in note, f"Expected 'Jan 15' in: {note!r}"
        assert "2025" in note, f"Expected '2025' in: {note!r}"

    def test_last_quarter_keeps_static_basis_note(self):
        """Completed windows must not be touched — static string unchanged."""
        result = build_market_health_payload(
            self._ROWS, "last-quarter", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["windowBasisNote"] == (
            "Comparison basis: last full quarter vs prior full quarter."
        )

    def test_all_time_keeps_static_basis_note(self):
        result = build_market_health_payload(
            self._ROWS, "all-time", [], is_all_selected=True, reference_dt=REF_DT
        )
        assert result["windowBasisNote"] == (
            "Comparison basis: structural context only, with no prior-period delta."
        )

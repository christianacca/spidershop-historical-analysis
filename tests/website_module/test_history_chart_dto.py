"""Tests for build_history_chart_dto.

Phase 7 — RED phase: all tests fail with ImportError until the implementation
in src/website/history_chart_dto.py is written.
"""

import pytest
from website.history_chart_dto import build_history_chart_dto


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_row(
    scrape_datetime: str,
    scientific_name: str,
    common_name: str = "Common Name",
    price_gbp: str = "14.99",
    wishlist_count: str = "3",
) -> dict:
    return {
        "scrape_datetime": scrape_datetime,
        "scientific_name": scientific_name,
        "common_name": common_name,
        "size_cm": "1.5",
        "price_gbp": price_gbp,
        "wishlist_count": wishlist_count,
        "page_url": "https://example.com/species",
    }


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------

class TestEmptyInput:
    def test_empty_input_returns_empty_species_list_and_scrape_dates(self):
        result = build_history_chart_dto([])

        assert result["species"] == []
        assert result["scrape_dates"] == []


# ---------------------------------------------------------------------------
# Single species grouping
# ---------------------------------------------------------------------------

class TestSingleSpecies:
    def test_single_species_with_multiple_rows_groups_all_runs_under_one_entry(self):
        rows = [
            _make_row("2026-01-01T06:10:00", "Brachypelma hamorii", price_gbp="10.00"),
            _make_row("2026-01-08T06:10:00", "Brachypelma hamorii", price_gbp="12.00"),
            _make_row("2026-01-15T06:10:00", "Brachypelma hamorii", price_gbp="15.00"),
        ]

        result = build_history_chart_dto(rows)

        assert len(result["species"]) == 1
        assert result["species"][0]["scientific_name"] == "Brachypelma hamorii"
        assert len(result["species"][0]["runs"]) == 3


# ---------------------------------------------------------------------------
# in_stock detection
# ---------------------------------------------------------------------------

class TestInStockDetection:
    def test_row_with_non_empty_price_is_in_stock_true(self):
        rows = [_make_row("2026-01-01T06:10:00", "Brachypelma hamorii", price_gbp="14.99")]

        result = build_history_chart_dto(rows)

        assert result["species"][0]["runs"][0]["in_stock"] is True

    def test_row_with_empty_price_is_in_stock_false(self):
        rows = [_make_row("2026-01-01T06:10:00", "Brachypelma hamorii", price_gbp="")]

        result = build_history_chart_dto(rows)

        assert result["species"][0]["runs"][0]["in_stock"] is False

    def test_row_with_none_price_is_in_stock_false(self):
        row = _make_row("2026-01-01T06:10:00", "Brachypelma hamorii")
        row["price_gbp"] = None

        result = build_history_chart_dto([row])

        assert result["species"][0]["runs"][0]["in_stock"] is False


# ---------------------------------------------------------------------------
# Numeric field coercion
# ---------------------------------------------------------------------------

class TestNumericCoercion:
    def test_price_gbp_is_coerced_to_float(self):
        rows = [_make_row("2026-01-01T06:10:00", "Brachypelma hamorii", price_gbp="14.99")]

        result = build_history_chart_dto(rows)

        assert result["species"][0]["runs"][0]["price_gbp"] == pytest.approx(14.99)

    def test_wishlist_count_is_coerced_to_int(self):
        rows = [_make_row("2026-01-01T06:10:00", "Brachypelma hamorii", wishlist_count="7")]

        result = build_history_chart_dto(rows)

        assert result["species"][0]["runs"][0]["wishlist_count"] == 7

    def test_empty_price_produces_none_not_zero(self):
        rows = [_make_row("2026-01-01T06:10:00", "Brachypelma hamorii", price_gbp="")]

        result = build_history_chart_dto(rows)

        assert result["species"][0]["runs"][0]["price_gbp"] is None

    def test_empty_wishlist_produces_none_not_zero(self):
        rows = [_make_row("2026-01-01T06:10:00", "Brachypelma hamorii", wishlist_count="")]

        result = build_history_chart_dto(rows)

        assert result["species"][0]["runs"][0]["wishlist_count"] is None


# ---------------------------------------------------------------------------
# scrape_dates — sorted and deduplicated
# ---------------------------------------------------------------------------

class TestScrapeDates:
    def test_scrape_dates_are_sorted_chronologically_and_deduplicated(self):
        rows = [
            _make_row("2026-01-15T06:10:00", "Brachypelma hamorii"),
            _make_row("2026-01-01T06:10:00", "Brachypelma hamorii"),
            _make_row("2026-01-08T06:10:00", "Brachypelma hamorii"),
            # duplicate date for second species
            _make_row("2026-01-01T06:10:00", "Acanthoscurria geniculata", common_name="Brazilian Giant Whiteknee"),
        ]

        result = build_history_chart_dto(rows)

        assert result["scrape_dates"] == [
            "2026-01-01T06:10:00",
            "2026-01-08T06:10:00",
            "2026-01-15T06:10:00",
        ]


# ---------------------------------------------------------------------------
# Multiple species
# ---------------------------------------------------------------------------

class TestMultipleSpecies:
    def test_multiple_species_produce_one_entry_each_in_species_list(self):
        rows = [
            _make_row("2026-01-01T06:10:00", "Brachypelma hamorii", common_name="Mexican Red Knee"),
            _make_row("2026-01-01T06:10:00", "Acanthoscurria geniculata", common_name="Brazilian Giant Whiteknee"),
            _make_row("2026-01-01T06:10:00", "Chromatopelma cyaneopubescens", common_name="Green Bottle Blue"),
        ]

        result = build_history_chart_dto(rows)

        assert len(result["species"]) == 3
        names = {s["scientific_name"] for s in result["species"]}
        assert names == {
            "Brachypelma hamorii",
            "Acanthoscurria geniculata",
            "Chromatopelma cyaneopubescens",
        }

    def test_common_name_is_preserved_per_species(self):
        rows = [
            _make_row("2026-01-01T06:10:00", "Brachypelma hamorii", common_name="Mexican Red Knee"),
        ]

        result = build_history_chart_dto(rows)

        assert result["species"][0]["common_name"] == "Mexican Red Knee"

    def test_run_date_matches_scrape_datetime(self):
        rows = [_make_row("2026-01-08T06:10:00", "Brachypelma hamorii")]

        result = build_history_chart_dto(rows)

        assert result["species"][0]["runs"][0]["date"] == "2026-01-08T06:10:00"


# ---------------------------------------------------------------------------
# Runs ordering
# ---------------------------------------------------------------------------

class TestRunsOrdering:
    def test_runs_are_sorted_chronologically_regardless_of_input_order(self):
        """Runs in the output must be sorted by date even when input rows are unordered."""
        rows = [
            _make_row("2026-01-15T06:10:00", "Brachypelma hamorii", price_gbp="15.00"),
            _make_row("2026-01-01T06:10:00", "Brachypelma hamorii", price_gbp="10.00"),
            _make_row("2026-01-08T06:10:00", "Brachypelma hamorii", price_gbp="12.00"),
        ]

        result = build_history_chart_dto(rows)

        run_dates = [r["date"] for r in result["species"][0]["runs"]]
        assert run_dates == [
            "2026-01-01T06:10:00",
            "2026-01-08T06:10:00",
            "2026-01-15T06:10:00",
        ]

    def test_each_species_runs_sorted_independently(self):
        """Each species' runs are sorted independently of other species."""
        rows = [
            _make_row("2026-01-15T06:10:00", "Brachypelma hamorii"),
            _make_row("2026-01-08T06:10:00", "Acanthoscurria geniculata"),
            _make_row("2026-01-01T06:10:00", "Brachypelma hamorii"),
            _make_row("2026-01-01T06:10:00", "Acanthoscurria geniculata"),
        ]

        result = build_history_chart_dto(rows)

        species_by_name = {s["scientific_name"]: s for s in result["species"]}
        hamorii_dates = [r["date"] for r in species_by_name["Brachypelma hamorii"]["runs"]]
        geniculata_dates = [r["date"] for r in species_by_name["Acanthoscurria geniculata"]["runs"]]
        assert hamorii_dates == ["2026-01-01T06:10:00", "2026-01-15T06:10:00"]
        assert geniculata_dates == ["2026-01-01T06:10:00", "2026-01-08T06:10:00"]

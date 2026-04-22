#!/usr/bin/env python3
"""Tests for market_health_raw_dto.py — the raw data serialiser used by the
client-side market-health engine."""
import pytest
from website.market_health_raw_dto import build_raw_market_health_data


def _make_row(
    scrape_datetime="2026-04-14T06:10:00",
    scientific_name="Avicularia avicularia",
    size_cm="2.0",
    page_url="https://example.com/1",
    wishlist_count="12",
    price_gbp="24.99",
) -> dict:
    """Return a minimal history CSV row dict."""
    return {
        "scrape_datetime": scrape_datetime,
        "scientific_name": scientific_name,
        "size_cm": size_cm,
        "page_url": page_url,
        "wishlist_count": wishlist_count,
        "price_gbp": price_gbp,
    }


class TestBuildRawMarketHealthData:
    """Unit tests for build_raw_market_health_data."""

    # ── output structure ────────────────────────────────────────────────────

    def test_output_has_records_and_reference_date_keys(self):
        rows = [_make_row()]
        result = build_raw_market_health_data(rows)
        assert "records" in result
        assert "referenceDate" in result

    def test_records_is_a_list(self):
        result = build_raw_market_health_data([_make_row()])
        assert isinstance(result["records"], list)

    def test_reference_date_is_a_string(self):
        result = build_raw_market_health_data([_make_row()])
        assert isinstance(result["referenceDate"], str)

    # ── referenceDate ───────────────────────────────────────────────────────

    def test_reference_date_equals_max_scrape_datetime(self):
        rows = [
            _make_row(scrape_datetime="2026-04-07T06:10:00"),
            _make_row(scrape_datetime="2026-04-14T06:10:00"),
            _make_row(scrape_datetime="2026-03-31T06:10:00"),
        ]
        result = build_raw_market_health_data(rows)
        assert result["referenceDate"] == "2026-04-14T06:10:00"

    def test_reference_date_empty_when_no_rows(self):
        result = build_raw_market_health_data([])
        assert result["referenceDate"] == ""

    # ── empty input ─────────────────────────────────────────────────────────

    def test_empty_history_rows_returns_empty_records(self):
        result = build_raw_market_health_data([])
        assert result["records"] == []

    # ── numeric field types ─────────────────────────────────────────────────

    def test_wishlist_count_is_int_not_string(self):
        result = build_raw_market_health_data([_make_row(wishlist_count="12")])
        assert isinstance(result["records"][0]["wishlistCount"], int)
        assert result["records"][0]["wishlistCount"] == 12

    def test_price_gbp_is_float_not_string(self):
        result = build_raw_market_health_data([_make_row(price_gbp="24.99")])
        assert isinstance(result["records"][0]["priceGbp"], float)
        assert abs(result["records"][0]["priceGbp"] - 24.99) < 1e-6

    # ── missing / invalid field handling ────────────────────────────────────

    def test_missing_wishlist_count_defaults_to_zero(self):
        row = _make_row()
        del row["wishlist_count"]
        result = build_raw_market_health_data([row])
        assert result["records"][0]["wishlistCount"] == 0

    def test_invalid_wishlist_count_defaults_to_zero(self):
        result = build_raw_market_health_data([_make_row(wishlist_count="not-a-number")])
        assert result["records"][0]["wishlistCount"] == 0

    def test_none_wishlist_count_defaults_to_zero(self):
        result = build_raw_market_health_data([_make_row(wishlist_count=None)])
        assert result["records"][0]["wishlistCount"] == 0

    def test_missing_price_gbp_defaults_to_zero(self):
        row = _make_row()
        del row["price_gbp"]
        result = build_raw_market_health_data([row])
        assert result["records"][0]["priceGbp"] == 0.0

    def test_invalid_price_gbp_defaults_to_zero(self):
        result = build_raw_market_health_data([_make_row(price_gbp="n/a")])
        assert result["records"][0]["priceGbp"] == 0.0

    # ── field mapping ───────────────────────────────────────────────────────

    def test_size_variant_matches_size_cm_from_input(self):
        result = build_raw_market_health_data([_make_row(size_cm="3.5")])
        assert result["records"][0]["sizeVariant"] == "3.5"

    def test_page_url_matches_page_url_from_input(self):
        result = build_raw_market_health_data([_make_row(page_url="https://example.com/spider")])
        assert result["records"][0]["pageUrl"] == "https://example.com/spider"

    def test_scientific_name_preserved(self):
        result = build_raw_market_health_data([_make_row(scientific_name="Brachypelma hamorii")])
        assert result["records"][0]["scientificName"] == "Brachypelma hamorii"

    def test_scrape_datetime_preserved(self):
        result = build_raw_market_health_data([_make_row(scrape_datetime="2026-01-01T06:10:00")])
        assert result["records"][0]["scrapeDatetime"] == "2026-01-01T06:10:00"

    # ── variant-level preservation ──────────────────────────────────────────

    def test_multi_variant_species_produces_one_record_per_variant(self):
        """Same scientific_name with different size_cm → two separate records."""
        rows = [
            _make_row(size_cm="2.0", price_gbp="24.99"),
            _make_row(size_cm="3.5", price_gbp="34.99"),
        ]
        result = build_raw_market_health_data(rows)
        assert len(result["records"]) == 2
        size_variants = {r["sizeVariant"] for r in result["records"]}
        assert size_variants == {"2.0", "3.5"}

    def test_all_rows_serialised_one_to_one(self):
        """Record count must equal source row count (no deduplication at this layer)."""
        rows = [
            _make_row(scrape_datetime="2026-04-01T06:10:00", scientific_name="Species A"),
            _make_row(scrape_datetime="2026-04-01T06:10:00", scientific_name="Species B"),
            _make_row(scrape_datetime="2026-04-08T06:10:00", scientific_name="Species A"),
        ]
        result = build_raw_market_health_data(rows)
        assert len(result["records"]) == 3

    # ── skip rows guard ─────────────────────────────────────────────────────

    def test_rows_with_both_name_and_datetime_empty_are_skipped(self):
        """Rows where both scientificName and scrapeDatetime are empty are skipped."""
        rows = [
            {"scientific_name": "", "scrape_datetime": "", "size_cm": "", "page_url": "",
             "wishlist_count": "0", "price_gbp": "0"},
            _make_row(),  # valid row
        ]
        result = build_raw_market_health_data(rows)
        assert len(result["records"]) == 1

    def test_row_with_name_but_no_datetime_is_kept(self):
        """A row with a scientific name but empty datetime is retained."""
        row = _make_row(scrape_datetime="")
        result = build_raw_market_health_data([row])
        assert len(result["records"]) == 1

    def test_row_with_datetime_but_no_name_is_kept(self):
        """A row with a datetime but empty scientific name is retained."""
        row = _make_row(scientific_name="")
        result = build_raw_market_health_data([row])
        assert len(result["records"]) == 1

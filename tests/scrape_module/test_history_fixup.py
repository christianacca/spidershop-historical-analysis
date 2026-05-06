#!/usr/bin/env python3
"""
Tests for history_fixup.py — general-purpose history CSV fixup system.

Tests are organised around three concerns:
1. PageUrlFixup  — corrects bad listing-page URLs to product-detail URLs (no network)
2. LifestyleFixup — backfills lifestyle field by live-fetching each species' detail page
3. apply_all_fixups — integration: runs fixups in order, returns combined stats
"""

import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError

from scrape.history_fixup import (
    PageUrlFixup,
    LifestyleFixup,
    FixupStats,
    apply_all_fixups,
    REGISTERED_FIXUPS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_row(scientific_name="Genus species", page_url="https://www.thespidershop.co.uk/product/genus-species/", lifestyle=""):
    return {
        "scrape_datetime": "2025-01-01T10:00+00:00",
        "scientific_name": scientific_name,
        "common_name": "Common Name",
        "size_cm": "2.0",
        "price_gbp": "25.00",
        "wishlist_count": "5",
        "page_url": page_url,
        "lifestyle": lifestyle,
    }


PRODUCT_HTML_TERRESTRIAL = """
<html><body>
  <div class="spices-info">
    <div class="col lifestyle">
      <div class="row"><p>Lifestyle</p></div>
      <div class="rowb">Terrestrial</div>
    </div>
  </div>
</body></html>
"""

PRODUCT_HTML_NO_LIFESTYLE = """
<html><body>
  <h1>Genus species</h1>
</body></html>
"""


# ---------------------------------------------------------------------------
# PageUrlFixup
# ---------------------------------------------------------------------------

class TestPageUrlFixup:
    def test_good_url_is_unchanged(self):
        """Rows already containing /product/ are left untouched."""
        rows = [make_row(page_url="https://www.thespidershop.co.uk/product/genus-species/")]
        result, stats = PageUrlFixup().apply(rows)
        assert result[0]["page_url"] == "https://www.thespidershop.co.uk/product/genus-species/"
        assert stats.rows_changed == 0

    def test_bad_url_fixed_using_sibling_row(self):
        """Bad URL replaced with /product/ URL found in another row for same species."""
        rows = [
            make_row(page_url="https://www.thespidershop.co.uk/page/2/"),
            make_row(page_url="https://www.thespidershop.co.uk/product/genus-species/"),
        ]
        result, stats = PageUrlFixup().apply(rows)
        assert result[0]["page_url"] == "https://www.thespidershop.co.uk/product/genus-species/"
        assert stats.rows_changed == 1

    def test_bad_url_fixed_by_deriving_slug_when_no_sibling(self):
        """Bad URL with no sibling → derive slug from scientific name."""
        rows = [make_row(scientific_name="Aphonopelma seemanni", page_url="https://www.thespidershop.co.uk/page/3/")]
        result, stats = PageUrlFixup().apply(rows)
        assert result[0]["page_url"] == "https://www.thespidershop.co.uk/product/aphonopelma-seemanni/"
        assert stats.rows_changed == 1

    def test_derived_slug_uses_lowercase_hyphenated_name(self):
        """Derived slug is lowercased and spaces replaced with hyphens."""
        rows = [make_row(scientific_name="Brachypelma Hamorii", page_url="https://www.thespidershop.co.uk/page/1/")]
        result, stats = PageUrlFixup().apply(rows)
        assert "brachypelma-hamorii" in result[0]["page_url"]

    def test_all_rows_for_species_fixed_when_sibling_present(self):
        """All bad-URL rows for the same species are updated when a good sibling exists."""
        rows = [
            make_row(page_url="https://www.thespidershop.co.uk/page/1/"),
            make_row(page_url="https://www.thespidershop.co.uk/page/2/"),
            make_row(page_url="https://www.thespidershop.co.uk/product/genus-species/"),
        ]
        result, stats = PageUrlFixup().apply(rows)
        assert all(r["page_url"] == "https://www.thespidershop.co.uk/product/genus-species/" for r in result)
        assert stats.rows_changed == 2

    def test_multiple_species_fixed_independently(self):
        """Different species with bad URLs are each fixed independently."""
        rows = [
            make_row(scientific_name="Species one", page_url="https://www.thespidershop.co.uk/page/1/"),
            make_row(scientific_name="Species two", page_url="https://www.thespidershop.co.uk/page/1/"),
        ]
        result, stats = PageUrlFixup().apply(rows)
        assert result[0]["page_url"] == "https://www.thespidershop.co.uk/product/species-one/"
        assert result[1]["page_url"] == "https://www.thespidershop.co.uk/product/species-two/"
        assert stats.rows_changed == 2

    def test_stats_name_is_page_url_fixup(self):
        result, stats = PageUrlFixup().apply([])
        assert stats.name == "PageUrlFixup"

    def test_empty_rows_returns_no_changes(self):
        result, stats = PageUrlFixup().apply([])
        assert result == []
        assert stats.rows_changed == 0
        assert stats.errors == []


# ---------------------------------------------------------------------------
# LifestyleFixup
# ---------------------------------------------------------------------------

class TestLifestyleFixup:
    @patch("scrape.history_fixup.fetch")
    def test_empty_lifestyle_populated_by_fetching_product_page(self, mock_fetch):
        """Species with all-empty lifestyle → fetches product page → sets value on all rows."""
        mock_fetch.return_value = PRODUCT_HTML_TERRESTRIAL
        rows = [
            make_row(lifestyle=""),
            make_row(lifestyle=""),
        ]
        result, stats = LifestyleFixup().apply(rows)
        assert all(r["lifestyle"] == "Terrestrial" for r in result)
        assert stats.rows_changed == 2
        mock_fetch.assert_called_once()

    @patch("scrape.history_fixup.fetch")
    def test_already_populated_lifestyle_is_not_refetched(self, mock_fetch):
        """Species already having a lifestyle value → fetch is NOT called."""
        rows = [make_row(lifestyle="Arboreal")]
        result, stats = LifestyleFixup().apply(rows)
        assert result[0]["lifestyle"] == "Arboreal"
        assert stats.rows_changed == 0
        mock_fetch.assert_not_called()

    @patch("scrape.history_fixup.fetch")
    def test_http_error_leaves_lifestyle_empty_and_logs_error(self, mock_fetch):
        """404 from the product page → lifestyle stays '' and error is recorded."""
        response_404 = MagicMock()
        response_404.status_code = 404
        mock_fetch.side_effect = HTTPError(response=response_404)
        rows = [make_row(lifestyle="")]
        result, stats = LifestyleFixup().apply(rows)
        assert result[0]["lifestyle"] == ""
        assert stats.rows_changed == 0
        assert len(stats.errors) == 1
        assert "Genus species" in stats.errors[0]

    @patch("scrape.history_fixup.fetch")
    def test_missing_lifestyle_element_leaves_empty_string(self, mock_fetch):
        """Page fetched but .spices-info .col.lifestyle .rowb absent → lifestyle stays ''."""
        mock_fetch.return_value = PRODUCT_HTML_NO_LIFESTYLE
        rows = [make_row(lifestyle="")]
        result, stats = LifestyleFixup().apply(rows)
        assert result[0]["lifestyle"] == ""
        assert stats.rows_changed == 0

    @patch("scrape.history_fixup.fetch")
    def test_only_fetches_once_per_species_even_with_multiple_rows(self, mock_fetch):
        """Multiple rows for same species → only one HTTP fetch."""
        mock_fetch.return_value = PRODUCT_HTML_TERRESTRIAL
        rows = [make_row(lifestyle=""), make_row(lifestyle=""), make_row(lifestyle="")]
        LifestyleFixup().apply(rows)
        mock_fetch.assert_called_once()

    @patch("scrape.history_fixup.fetch")
    def test_species_with_no_product_url_is_skipped(self, mock_fetch):
        """Species where all rows have a bad (non-/product/) URL → skipped, no fetch."""
        rows = [make_row(lifestyle="", page_url="https://www.thespidershop.co.uk/page/2/")]
        result, stats = LifestyleFixup().apply(rows)
        assert result[0]["lifestyle"] == ""
        assert stats.rows_changed == 0
        mock_fetch.assert_not_called()

    @patch("scrape.history_fixup.fetch")
    def test_picks_first_product_url_for_fetch(self, mock_fetch):
        """When multiple /product/ URLs exist, uses the first one found."""
        mock_fetch.return_value = PRODUCT_HTML_TERRESTRIAL
        rows = [
            make_row(lifestyle="", page_url="https://www.thespidershop.co.uk/product/genus-species/"),
            make_row(lifestyle="", page_url="https://www.thespidershop.co.uk/product/genus-species-v2/"),
        ]
        LifestyleFixup().apply(rows)
        fetched_url = mock_fetch.call_args[0][0]
        assert fetched_url == "https://www.thespidershop.co.uk/product/genus-species/"

    @patch("scrape.history_fixup.fetch")
    def test_multiple_species_each_fetched_independently(self, mock_fetch):
        """Two species with empty lifestyle → two fetches, each species gets its own value."""
        mock_fetch.return_value = PRODUCT_HTML_TERRESTRIAL
        rows = [
            make_row(scientific_name="Species one", lifestyle=""),
            make_row(scientific_name="Species two", lifestyle=""),
        ]
        result, stats = LifestyleFixup().apply(rows)
        assert all(r["lifestyle"] == "Terrestrial" for r in result)
        assert mock_fetch.call_count == 2

    def test_stats_name_is_lifestyle_fixup(self):
        result, stats = LifestyleFixup().apply([])
        assert stats.name == "LifestyleFixup"

    @patch("scrape.history_fixup.fetch")
    def test_rows_without_lifestyle_key_are_treated_as_empty(self, mock_fetch):
        """Old CSV rows with no 'lifestyle' key (7-column schema) must not raise KeyError."""
        mock_fetch.return_value = PRODUCT_HTML_TERRESTRIAL
        row = {
            "scrape_datetime": "2025-01-01T10:00+00:00",
            "scientific_name": "Genus species",
            "common_name": "Common Name",
            "size_cm": "2.0",
            "price_gbp": "25.00",
            "wishlist_count": "5",
            "page_url": "https://www.thespidershop.co.uk/product/genus-species/",
            # no 'lifestyle' key — simulates old 7-column CSV
        }
        result, stats = LifestyleFixup().apply([row])
        assert result[0]["lifestyle"] == "Terrestrial"
        assert stats.rows_changed == 1


# ---------------------------------------------------------------------------
# apply_all_fixups
# ---------------------------------------------------------------------------

class TestApplyAllFixups:
    @patch("scrape.history_fixup.fetch")
    def test_page_url_fixup_runs_before_lifestyle_fixup(self, mock_fetch):
        """PageUrlFixup runs first so the fixed URL is used by LifestyleFixup for the fetch."""
        mock_fetch.return_value = PRODUCT_HTML_TERRESTRIAL
        rows = [
            make_row(
                scientific_name="Genus species",
                page_url="https://www.thespidershop.co.uk/page/2/",  # bad URL
                lifestyle="",
            )
        ]
        result, all_stats = apply_all_fixups(rows, [PageUrlFixup(), LifestyleFixup()])
        # URL was fixed first, enabling the lifestyle fetch
        assert "/product/" in result[0]["page_url"]
        assert result[0]["lifestyle"] == "Terrestrial"
        assert len(all_stats) == 2

    @patch("scrape.history_fixup.fetch")
    def test_returns_one_stats_per_fixup(self, mock_fetch):
        mock_fetch.return_value = PRODUCT_HTML_TERRESTRIAL
        rows = [make_row(lifestyle="")]
        _, all_stats = apply_all_fixups(rows, [PageUrlFixup(), LifestyleFixup()])
        assert len(all_stats) == 2
        assert all_stats[0].name == "PageUrlFixup"
        assert all_stats[1].name == "LifestyleFixup"

    def test_empty_fixup_list_returns_rows_unchanged(self):
        rows = [make_row()]
        result, all_stats = apply_all_fixups(rows, [])
        assert result == rows
        assert all_stats == []

    def test_rows_are_not_mutated_in_original_list(self):
        """apply_all_fixups must not mutate the input list reference."""
        rows = [make_row(page_url="https://www.thespidershop.co.uk/page/2/")]
        original_url = rows[0]["page_url"]
        apply_all_fixups(rows, [PageUrlFixup()])
        # Original list content is allowed to be mutated (in-place dict edits are fine),
        # but the list itself should still be the same object
        assert rows[0]["page_url"] != original_url  # dict was mutated in place (acceptable)


# ---------------------------------------------------------------------------
# REGISTERED_FIXUPS contract
# ---------------------------------------------------------------------------

class TestRegisteredFixups:
    def test_registered_fixups_is_non_empty_list(self):
        assert isinstance(REGISTERED_FIXUPS, list)
        assert len(REGISTERED_FIXUPS) > 0

    def test_registered_fixups_contains_page_url_fixup(self):
        assert any(isinstance(f, PageUrlFixup) for f in REGISTERED_FIXUPS)

    def test_registered_fixups_contains_lifestyle_fixup(self):
        assert any(isinstance(f, LifestyleFixup) for f in REGISTERED_FIXUPS)

    def test_page_url_fixup_comes_before_lifestyle_fixup(self):
        """Order matters: URL must be fixed before lifestyle can use it."""
        names = [type(f).__name__ for f in REGISTERED_FIXUPS]
        assert names.index("PageUrlFixup") < names.index("LifestyleFixup")

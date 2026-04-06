#!/usr/bin/env python3
"""Tests for URL normalization utilities (Phase 1 - Size Variant Identity)."""

import pytest
from shared.url_utils import normalize_product_url


class TestNormalizeProductUrl:
    """Tests for normalize_product_url matching spec rules exactly."""

    # Spec examples
    def test_spec_example_1_strips_scheme_host_query_fragment(self):
        """HTTPS://www.thespidershop.co.uk/product/foo/?bar=1#frag → https://thespidershop.co.uk/product/foo"""
        result = normalize_product_url(
            "HTTPS://www.thespidershop.co.uk/product/foo/?bar=1#frag"
        )
        assert result == "https://thespidershop.co.uk/product/foo"

    def test_spec_example_2_strips_trailing_slash(self):
        """https://thespidershop.co.uk/product/foo/ → https://thespidershop.co.uk/product/foo"""
        result = normalize_product_url("https://thespidershop.co.uk/product/foo/")
        assert result == "https://thespidershop.co.uk/product/foo"

    # Lowercase scheme and host
    def test_lowercases_scheme(self):
        result = normalize_product_url("HTTP://example.com/path")
        assert result.startswith("http://")

    def test_lowercases_host(self):
        result = normalize_product_url("https://EXAMPLE.COM/path")
        assert "example.com" in result

    # www. stripping
    def test_strips_www_prefix(self):
        result = normalize_product_url("https://www.example.com/product/foo")
        assert result == "https://example.com/product/foo"

    def test_does_not_strip_non_www_subdomain(self):
        result = normalize_product_url("https://shop.example.com/product/foo")
        assert result == "https://shop.example.com/product/foo"

    # Query string and fragment discarding
    def test_discards_query_string(self):
        result = normalize_product_url("https://example.com/product?id=123&size=3")
        assert "?" not in result
        assert "id=123" not in result

    def test_discards_fragment(self):
        result = normalize_product_url("https://example.com/product/foo#description")
        assert "#" not in result

    # Trailing slash stripping (exactly one)
    def test_strips_exactly_one_trailing_slash(self):
        result = normalize_product_url("https://example.com/product/foo/")
        assert result == "https://example.com/product/foo"

    def test_does_not_strip_if_no_trailing_slash(self):
        result = normalize_product_url("https://example.com/product/foo")
        assert result == "https://example.com/product/foo"

    # Whitespace trimming
    def test_trims_leading_whitespace(self):
        result = normalize_product_url("  https://example.com/product/foo")
        assert result == "https://example.com/product/foo"

    def test_trims_trailing_whitespace(self):
        result = normalize_product_url("https://example.com/product/foo  ")
        assert result == "https://example.com/product/foo"

    # Duplicate slash collapsing in path
    def test_collapses_duplicate_slashes_in_path(self):
        result = normalize_product_url("https://example.com/product//foo")
        assert result == "https://example.com/product/foo"

    def test_collapses_multiple_duplicate_slashes(self):
        result = normalize_product_url("https://example.com//product///foo")
        assert result == "https://example.com/product/foo"

    # Edge cases
    def test_empty_string_returns_empty(self):
        result = normalize_product_url("")
        assert result == ""

    def test_blank_whitespace_only_returns_empty(self):
        result = normalize_product_url("   ")
        assert result == ""

    def test_missing_scheme_returns_original_stripped(self):
        """URL without a scheme cannot be parsed; return the stripped input."""
        url = "thespidershop.co.uk/product/foo"
        result = normalize_product_url(url)
        # Should return the stripped input unchanged (no scheme to normalize)
        assert result == url

    def test_no_path_preserves_host(self):
        result = normalize_product_url("https://example.com")
        assert result == "https://example.com"

    # Same-URL equality after normalization (key for transition detection)
    def test_same_url_different_case_scheme_equals(self):
        url1 = "HTTPS://www.thespidershop.co.uk/product/chilobrachys/"
        url2 = "https://thespidershop.co.uk/product/chilobrachys"
        assert normalize_product_url(url1) == normalize_product_url(url2)

    def test_same_url_with_and_without_query_equals(self):
        url1 = "https://example.com/product/foo?ref=tracker"
        url2 = "https://example.com/product/foo"
        assert normalize_product_url(url1) == normalize_product_url(url2)

    def test_different_paths_not_equal(self):
        url1 = "https://example.com/product/foo"
        url2 = "https://example.com/product/bar"
        assert normalize_product_url(url1) != normalize_product_url(url2)

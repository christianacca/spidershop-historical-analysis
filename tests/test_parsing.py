#!/usr/bin/env python3
"""
Comprehensive tests for parsing.py module.

Tests cover all parsing functions including:
- Whitespace normalization
- Size extraction from parentheticals
- Price parsing with various formats
- Wishlist count extraction
- Edge cases and error handling
"""

import sys
from pathlib import Path

# Add src directory to Python path to enable imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from parsing import (
    normalize_whitespace,
    first_cm_parenthetical,
    parse_size_cm,
    remove_size_parenthetical_only,
    parse_price,
    parse_wishlist_count,
)


class TestNormalizeWhitespace:
    """Test suite for normalize_whitespace function."""

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert normalize_whitespace("") == ""

    def test_none_input(self):
        """None input should return empty string."""
        assert normalize_whitespace(None) == ""

    def test_single_space(self):
        """Single space should be stripped."""
        assert normalize_whitespace(" ") == ""

    def test_multiple_spaces(self):
        """Multiple spaces should collapse to single space."""
        assert normalize_whitespace("hello    world") == "hello world"

    def test_leading_trailing_spaces(self):
        """Leading and trailing spaces should be removed."""
        assert normalize_whitespace("  hello world  ") == "hello world"

    def test_tabs_and_newlines(self):
        """Tabs and newlines should collapse to single space."""
        assert normalize_whitespace("hello\t\nworld") == "hello world"

    def test_non_breaking_space(self):
        """Non-breaking space (U+00A0) should be converted to regular space."""
        assert normalize_whitespace("hello\u00a0world") == "hello world"

    def test_mixed_whitespace(self):
        """Mixed whitespace types should be normalized."""
        assert normalize_whitespace("  hello \t\n  world  \u00a0  test  ") == "hello world test"

    def test_normal_text(self):
        """Normal text with regular spaces should remain unchanged."""
        assert normalize_whitespace("Aphonopelma seemanni") == "Aphonopelma seemanni"


class TestFirstCmParenthetical:
    """Test suite for first_cm_parenthetical function."""

    def test_no_parentheses(self):
        """Text without parentheses should return None."""
        assert first_cm_parenthetical("Aphonopelma seemanni") is None

    def test_no_cm_in_parentheses(self):
        """Parentheses without 'cm' should return None."""
        assert first_cm_parenthetical("Spider (adult)") is None

    def test_simple_cm_size(self):
        """Simple cm size in parentheses should be found."""
        assert first_cm_parenthetical("Spider (3cm)") == "(3cm)"

    def test_cm_with_spaces(self):
        """cm with spaces should be found."""
        assert first_cm_parenthetical("Spider (3 cm)") == "(3 cm)"

    def test_cm_case_insensitive(self):
        """Should find CM, Cm, cM variations."""
        assert first_cm_parenthetical("Spider (3CM)") == "(3CM)"
        assert first_cm_parenthetical("Spider (3Cm)") == "(3Cm)"

    def test_range_size(self):
        """Range size with cm should be found."""
        assert first_cm_parenthetical("Spider (2-3cm)") == "(2-3cm)"

    def test_first_cm_parenthetical_multiple(self):
        """Should return first cm parenthetical when multiple exist."""
        assert first_cm_parenthetical("Spider (2cm) (adult) (3cm)") == "(2cm)"

    def test_non_cm_then_cm(self):
        """Should skip non-cm parentheses and find first cm one."""
        assert first_cm_parenthetical("Spider (adult) (2cm)") == "(2cm)"

    def test_none_input(self):
        """None input should return None."""
        assert first_cm_parenthetical(None) is None

    def test_empty_string(self):
        """Empty string should return None."""
        assert first_cm_parenthetical("") is None


class TestParseSizeCm:
    """Test suite for parse_size_cm function."""

    def test_no_parenthetical(self):
        """Text without size parenthetical should return empty string."""
        assert parse_size_cm("Aphonopelma seemanni") == ""

    def test_integer_size(self):
        """Integer size should be extracted as integer string."""
        assert parse_size_cm("Spider (3cm)") == "3"

    def test_decimal_size(self):
        """Decimal size should be preserved."""
        assert parse_size_cm("Spider (2.5cm)") == "2.5"

    def test_range_size(self):
        """Range size should return upper bound."""
        assert parse_size_cm("Spider (2-3cm)") == "3"

    def test_range_with_decimal(self):
        """Range with decimal should return upper bound."""
        assert parse_size_cm("Spider (1.5-2.5cm)") == "2.5"

    def test_spaces_in_parentheses(self):
        """Spaces around size should be handled."""
        assert parse_size_cm("Spider ( 3 cm )") == "3"

    def test_en_dash_range(self):
        """En dash (U+2013) in range should work."""
        assert parse_size_cm("Spider (2–3cm)") == "3"

    def test_case_insensitive_cm(self):
        """CM in uppercase should work."""
        assert parse_size_cm("Spider (3CM)") == "3"

    def test_decimal_as_integer(self):
        """Decimal that equals integer should be formatted as integer."""
        assert parse_size_cm("Spider (3.0cm)") == "3"

    def test_invalid_format(self):
        """Invalid size format should return empty string."""
        assert parse_size_cm("Spider (big cm)") == ""

    def test_no_cm_unit(self):
        """Number without cm unit should return empty string."""
        assert parse_size_cm("Spider (3)") == ""

    def test_non_cm_parenthetical(self):
        """Non-cm parenthetical should return empty string."""
        assert parse_size_cm("Spider (adult)") == ""

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert parse_size_cm("") == ""


class TestRemoveSizeParentheticalOnly:
    """Test suite for remove_size_parenthetical_only function."""

    def test_no_parenthetical(self):
        """Text without parenthetical should remain unchanged."""
        text = "Aphonopelma seemanni"
        assert remove_size_parenthetical_only(text) == text

    def test_removes_cm_parenthetical(self):
        """Should remove cm parenthetical."""
        assert remove_size_parenthetical_only("Spider (3cm)") == "Spider"

    def test_preserves_non_cm_parenthetical(self):
        """Should preserve non-cm parenthetical."""
        assert remove_size_parenthetical_only("Spider (adult)") == "Spider (adult)"

    def test_removes_only_first_cm(self):
        """Should remove only first cm parenthetical."""
        result = remove_size_parenthetical_only("Spider (3cm) (adult)")
        assert result == "Spider (adult)"

    def test_normalizes_whitespace(self):
        """Should normalize whitespace after removal."""
        assert remove_size_parenthetical_only("Spider  (3cm)  ") == "Spider"

    def test_handles_multiple_spaces(self):
        """Should handle multiple spaces correctly."""
        assert remove_size_parenthetical_only("Spider   (3cm)   Extra") == "Spider Extra"

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert remove_size_parenthetical_only("") == ""


class TestParsePrice:
    """Test suite for parse_price function."""

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert parse_price("") == ""

    def test_none_input(self):
        """None input should return empty string."""
        assert parse_price(None) == ""

    def test_simple_price(self):
        """Simple price should be parsed."""
        assert parse_price("25.00") == "25.00"

    def test_price_with_pound_sign(self):
        """Price with £ symbol should be parsed."""
        assert parse_price("£25.00") == "25.00"

    def test_price_with_unicode_pound(self):
        """Price with unicode pound symbol should be parsed."""
        assert parse_price("\u00a325.00") == "25.00"

    def test_price_with_comma(self):
        """Price with comma should be parsed."""
        assert parse_price("1,250.00") == "1250.00"

    def test_integer_price(self):
        """Integer price should be formatted with decimal."""
        assert parse_price("25") == "25"

    def test_price_with_spaces(self):
        """Price with spaces should be stripped and parsed."""
        assert parse_price(" 25.00 ") == "25.00"

    def test_price_with_all_formatting(self):
        """Price with all formatting should be cleaned and parsed."""
        assert parse_price(" £1,250.50 ") == "1250.50"

    def test_invalid_price(self):
        """Invalid price string should return empty string."""
        assert parse_price("not a price") == ""

    def test_multiple_decimals(self):
        """Price with multiple decimal points should return empty string."""
        assert parse_price("25.00.50") == ""

    def test_zero_price(self):
        """Zero price should be formatted correctly."""
        assert parse_price("0.00") == "0.00"

    def test_negative_price(self):
        """Negative price should be parsed (though unusual)."""
        assert parse_price("-25.00") == "-25.00"


class TestParseWishlistCount:
    """Test suite for parse_wishlist_count function."""

    def test_empty_string(self):
        """Empty string should return '0'."""
        assert parse_wishlist_count("") == "0"

    def test_none_input(self):
        """None input should return '0'."""
        assert parse_wishlist_count(None) == "0"

    def test_single_user_has(self):
        """Single user format should be parsed."""
        assert parse_wishlist_count("1 user has this item in their wishlist") == "1"

    def test_multiple_users_have(self):
        """Multiple users format should be parsed."""
        assert parse_wishlist_count("5 users have this item in their wishlists") == "5"

    def test_with_extra_whitespace(self):
        """Extra whitespace should be handled."""
        assert parse_wishlist_count("  5  users  have  this  item  in  their  wishlists  ") == "5"

    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert parse_wishlist_count("5 USERS HAVE THIS ITEM IN THEIR WISHLISTS") == "5"

    def test_mixed_case(self):
        """Mixed case should work."""
        assert parse_wishlist_count("5 Users Have This Item In Their Wishlist") == "5"

    def test_single_user_singular_wishlist(self):
        """Singular wishlist should work."""
        assert parse_wishlist_count("1 user has this item in their wishlist") == "1"

    def test_large_number(self):
        """Large number should be parsed."""
        assert parse_wishlist_count("150 users have this item in their wishlists") == "150"

    def test_zero_users(self):
        """Zero users should be parsed."""
        assert parse_wishlist_count("0 users have this item in their wishlists") == "0"

    def test_no_match_returns_zero(self):
        """Text without wishlist pattern should return '0'."""
        assert parse_wishlist_count("Some random text") == "0"

    def test_number_without_pattern(self):
        """Number without proper pattern should return '0'."""
        assert parse_wishlist_count("5 people like this") == "0"

    def test_with_line_breaks(self):
        """Text with line breaks should be normalized and matched."""
        assert parse_wishlist_count("5\nusers\nhave\nthis\nitem\nin\ntheir\nwishlists") == "5"

    def test_embedded_in_larger_text(self):
        """Pattern embedded in larger text should be found."""
        assert parse_wishlist_count("Product details: 5 users have this item in their wishlists. Price: £25") == "5"

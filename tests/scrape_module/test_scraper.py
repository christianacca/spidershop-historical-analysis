#!/usr/bin/env python3
"""
Comprehensive tests for scraper.py module.

Tests cover:
- Product URL extraction from category pages
- Duplicate URL filtering
- URL resolution and normalization
- Product detail scraping (mocked to avoid actual web requests)
- Edge cases and error handling
"""

import pytest
from unittest.mock import patch, MagicMock
from scrape.scraper import extract_product_urls, scrape_product


class TestExtractProductUrls:
    """Test suite for extract_product_urls function."""

    def test_empty_html(self):
        """Empty HTML should return empty list."""
        html = ""
        result = extract_product_urls(html, "https://example.com")
        assert result == []

    def test_no_product_links(self):
        """HTML without /product/ links should return empty list."""
        html = """
        <html>
            <body>
                <a href="/category/tarantulas">Tarantulas</a>
                <a href="/about">About</a>
                <a href="https://example.com/contact">Contact</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert result == []

    def test_single_product_link(self):
        """Should extract single product link."""
        html = """
        <html>
            <body>
                <a href="/product/aphonopelma-seemanni">Product</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 1
        assert result[0] == "https://example.com/product/aphonopelma-seemanni"

    def test_multiple_product_links(self):
        """Should extract multiple product links."""
        html = """
        <html>
            <body>
                <a href="/product/aphonopelma-seemanni">Product 1</a>
                <a href="/product/brachypelma-hamorii">Product 2</a>
                <a href="/product/grammostola-pulchra">Product 3</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 3
        assert "https://example.com/product/aphonopelma-seemanni" in result
        assert "https://example.com/product/brachypelma-hamorii" in result
        assert "https://example.com/product/grammostola-pulchra" in result

    def test_duplicate_links_filtered(self):
        """Should filter out duplicate product links."""
        html = """
        <html>
            <body>
                <a href="/product/aphonopelma-seemanni">Product 1</a>
                <a href="/product/aphonopelma-seemanni">Product 1 Again</a>
                <a href="/product/brachypelma-hamorii">Product 2</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 2
        assert result.count("https://example.com/product/aphonopelma-seemanni") == 1

    def test_relative_urls_converted_to_absolute(self):
        """Should convert relative URLs to absolute."""
        html = """
        <html>
            <body>
                <a href="/product/test">Relative</a>
                <a href="/product/test2">Another Relative</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com/category/")
        assert len(result) == 2
        assert all(url.startswith("https://example.com") for url in result)

    def test_absolute_product_urls(self):
        """Should handle absolute product URLs."""
        html = """
        <html>
            <body>
                <a href="https://example.com/product/test">Absolute</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 1
        assert result[0] == "https://example.com/product/test"

    def test_mixed_product_and_non_product_links(self):
        """Should only extract product links from mixed content."""
        html = """
        <html>
            <body>
                <nav>
                    <a href="/home">Home</a>
                    <a href="/category/spiders">Spiders</a>
                </nav>
                <div class="products">
                    <a href="/product/spider1">Spider 1</a>
                    <a href="/product/spider2">Spider 2</a>
                </div>
                <footer>
                    <a href="/terms">Terms</a>
                </footer>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 2
        assert all("/product/" in url for url in result)

    def test_links_without_href_attribute(self):
        """Should handle <a> tags without href attribute."""
        html = """
        <html>
            <body>
                <a>No Href</a>
                <a href="/product/test">With Href</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 1

    def test_empty_href_attribute(self):
        """Should handle empty href attributes."""
        html = """
        <html>
            <body>
                <a href="">Empty</a>
                <a href="/product/test">Valid</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 1

    def test_whitespace_in_href(self):
        """Should handle whitespace in href attributes."""
        html = """
        <html>
            <body>
                <a href="  /product/test  ">Whitespace</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 1
        assert result[0] == "https://example.com/product/test"

    def test_product_not_in_path_not_extracted(self):
        """Should only extract URLs with /product/ in the path."""
        html = """
        <html>
            <body>
                <a href="/category/products">Category</a>
                <a href="/products">Products</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 0

    def test_product_in_fragment_extracted(self):
        """Should extract URLs with /product/ in path even with fragments."""
        html = """
        <html>
            <body>
                <a href="/product/test#reviews">With Fragment</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 1
        assert "/product/test" in result[0]

    def test_maintains_insertion_order(self):
        """Should maintain the order of first occurrence for URLs."""
        html = """
        <html>
            <body>
                <a href="/product/spider1">First</a>
                <a href="/product/spider2">Second</a>
                <a href="/product/spider1">First Again</a>
                <a href="/product/spider3">Third</a>
            </body>
        </html>
        """
        result = extract_product_urls(html, "https://example.com")
        assert len(result) == 3
        assert result[0].endswith("/product/spider1")
        assert result[1].endswith("/product/spider2")
        assert result[2].endswith("/product/spider3")


class TestScrapeProduct:
    """Test suite for scrape_product function."""

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_complete_product(self, mock_fetch):
        """Should scrape all product details correctly."""
        mock_html = """
        <html>
            <body>
                <h1>Aphonopelma seemanni</h1>
                <h2>Costa Rican Zebra (2cm)</h2>
                <span class="woocommerce-Price-amount">£25.00</span>
                <span class="yith-wcwl-add-to-wishlist__counter">5 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        scientific_name, common_name, size_cm, price_gbp, wishlist_count = scrape_product("https://example.com/product/test")

        assert scientific_name == "Aphonopelma seemanni"
        assert common_name == "Costa Rican Zebra"
        assert size_cm == "2"
        assert price_gbp == "25.00"
        assert wishlist_count == "5"
        mock_fetch.assert_called_once_with("https://example.com/product/test", wait_for_selector=".yith-wcwl-add-to-wishlist__counter", timeout=10)

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_with_decimal_size(self, mock_fetch):
        """Should handle decimal sizes correctly."""
        mock_html = """
        <html>
            <body>
                <h1>Brachypelma hamorii</h1>
                <h2>Mexican Red Knee (2.5cm)</h2>
                <span class="woocommerce-Price-amount">£30.00</span>
                <span class="yith-wcwl-add-to-wishlist__counter">3 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        _, _, size_cm, _, _ = scrape_product("https://example.com/product/test")

        assert size_cm == "2.5"

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_with_size_range(self, mock_fetch):
        """Should extract upper bound from size range."""
        mock_html = """
        <html>
            <body>
                <h1>Grammostola pulchra</h1>
                <h2>Brazilian Black (2-3cm)</h2>
                <span class="woocommerce-Price-amount">£40.00</span>
                <span class="yith-wcwl-add-to-wishlist__counter">10 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        _, _, size_cm, _, _ = scrape_product("https://example.com/product/test")

        assert size_cm == "3"

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_missing_h1(self, mock_fetch):
        """Should handle missing h1 element."""
        mock_html = """
        <html>
            <body>
                <h2>Common Name (2cm)</h2>
                <span class="woocommerce-Price-amount">£25.00</span>
                <span class="yith-wcwl-add-to-wishlist__counter">5 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        scientific_name, common_name, _, _, _ = scrape_product("https://example.com/product/test")

        assert scientific_name == ""
        assert common_name == "Common Name"

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_missing_h2(self, mock_fetch):
        """Should handle missing h2 element."""
        mock_html = """
        <html>
            <body>
                <h1>Aphonopelma seemanni</h1>
                <span class="woocommerce-Price-amount">£25.00</span>
                <span class="yith-wcwl-add-to-wishlist__counter">5 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        scientific_name, common_name, size_cm, _, _ = scrape_product("https://example.com/product/test")

        assert scientific_name == "Aphonopelma seemanni"
        assert common_name == ""
        assert size_cm == ""

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_missing_price(self, mock_fetch):
        """Should handle missing price element."""
        mock_html = """
        <html>
            <body>
                <h1>Aphonopelma seemanni</h1>
                <h2>Costa Rican Zebra (2cm)</h2>
                <span class="yith-wcwl-add-to-wishlist__counter">5 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        _, _, _, price_gbp, _ = scrape_product("https://example.com/product/test")

        assert price_gbp == ""

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_missing_wishlist(self, mock_fetch):
        """Should handle missing wishlist element."""
        mock_html = """
        <html>
            <body>
                <h1>Aphonopelma seemanni</h1>
                <h2>Costa Rican Zebra (2cm)</h2>
                <span class="woocommerce-Price-amount">£25.00</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        _, _, _, _, wishlist_count = scrape_product("https://example.com/product/test")

        assert wishlist_count == "0"

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_with_extra_whitespace(self, mock_fetch):
        """Should normalize whitespace in extracted text."""
        mock_html = """
        <html>
            <body>
                <h1>  Aphonopelma   seemanni  </h1>
                <h2>  Costa Rican Zebra   (2cm)  </h2>
                <span class="woocommerce-Price-amount">  £25.00  </span>
                <span class="yith-wcwl-add-to-wishlist__counter">  5 users have this item in their wishlists  </span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        scientific_name, common_name, size_cm, price_gbp, wishlist_count = scrape_product("https://example.com/product/test")

        assert scientific_name == "Aphonopelma seemanni"
        assert common_name == "Costa Rican Zebra"
        assert price_gbp == "25.00"
        assert wishlist_count == "5"

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_with_unicode_characters(self, mock_fetch):
        """Should handle unicode characters in product details."""
        mock_html = """
        <html>
            <body>
                <h1>Brachypelma boehmei</h1>
                <h2>Mexican Fireleg (3cm)</h2>
                <span class="woocommerce-Price-amount">£35.00</span>
                <span class="yith-wcwl-add-to-wishlist__counter">8 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        scientific_name, _, _, price_gbp, _ = scrape_product("https://example.com/product/test")

        assert scientific_name == "Brachypelma boehmei"
        assert price_gbp == "35.00"

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_zero_wishlist_count(self, mock_fetch):
        """Should handle zero wishlist count."""
        mock_html = """
        <html>
            <body>
                <h1>Aphonopelma seemanni</h1>
                <h2>Costa Rican Zebra (2cm)</h2>
                <span class="woocommerce-Price-amount">£25.00</span>
                <span class="yith-wcwl-add-to-wishlist__counter">0 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        _, _, _, _, wishlist_count = scrape_product("https://example.com/product/test")

        assert wishlist_count == "0"

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_single_user_wishlist(self, mock_fetch):
        """Should handle singular wishlist text."""
        mock_html = """
        <html>
            <body>
                <h1>Aphonopelma seemanni</h1>
                <h2>Costa Rican Zebra (2cm)</h2>
                <span class="woocommerce-Price-amount">£25.00</span>
                <span class="yith-wcwl-add-to-wishlist__counter">1 user has this item in their wishlist</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        _, _, _, _, wishlist_count = scrape_product("https://example.com/product/test")

        assert wishlist_count == "1"

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_no_size_in_common_name(self, mock_fetch):
        """Should handle common name without size parenthetical."""
        mock_html = """
        <html>
            <body>
                <h1>Aphonopelma seemanni</h1>
                <h2>Costa Rican Zebra</h2>
                <span class="woocommerce-Price-amount">£25.00</span>
                <span class="yith-wcwl-add-to-wishlist__counter">5 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        _, common_name, size_cm, _, _ = scrape_product("https://example.com/product/test")

        assert common_name == "Costa Rican Zebra"
        assert size_cm == ""

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_calls_browser_with_correct_parameters(self, mock_fetch):
        """Should call fetch_with_browser with correct selector and timeout."""
        mock_html = "<html><body><h1>Test</h1></body></html>"
        mock_fetch.return_value = mock_html

        scrape_product("https://example.com/product/test-product")

        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[0][0] == "https://example.com/product/test-product"
        assert call_args[1]["wait_for_selector"] == ".yith-wcwl-add-to-wishlist__counter"
        assert call_args[1]["timeout"] == 10

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_with_price_formatting(self, mock_fetch):
        """Should handle various price formats."""
        mock_html = """
        <html>
            <body>
                <h1>Aphonopelma seemanni</h1>
                <h2>Costa Rican Zebra (2cm)</h2>
                <span class="woocommerce-Price-amount">£1,250.50</span>
                <span class="yith-wcwl-add-to-wishlist__counter">5 users have this item in their wishlists</span>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        _, _, _, price_gbp, _ = scrape_product("https://example.com/product/test")

        assert price_gbp == "1250.50"

    @patch('scrape.scraper.fetch_with_browser')
    def test_scrape_product_with_actual_html_structure(self, mock_fetch):
        """Should scrape product using actual Spider Shop HTML structure."""
        mock_html = """
        <html>
            <body>
                <div class="product-details w-br-holder livestock">
                    <div class="head-holder">
                        <h1>Abdomegaphobema mesomelas</h1>
                        <h2>Costa Rican Red Leg (1-2cm)</h2>
                    </div>
                    <div class="product-info">
                        <p class="price">
                            <span class="woocommerce-Price-amount amount">
                                <bdi>
                                    <span class="woocommerce-Price-currencySymbol">£</span>100.00
                                </bdi>
                            </span>
                        </p>
                        <div class="yith-add-to-wishlist-button-block">
                            <span class="yith-wcwl-add-to-wishlist__counter">38 users have this item in their wishlists</span>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_html

        scientific_name, common_name, size_cm, price_gbp, wishlist_count = scrape_product("https://example.com/product/test")

        assert scientific_name == "Abdomegaphobema mesomelas"
        assert common_name == "Costa Rican Red Leg"
        assert size_cm == "2"  # Upper bound of range
        assert price_gbp == "100.00"
        assert wishlist_count == "38"

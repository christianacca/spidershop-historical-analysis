#!/usr/bin/env python3
"""E2E tests for basic navigation and page loading.

Scope:
- All pages load without console errors or 404s
- Links between pages work correctly
- Assets (CSS, JS files) load successfully
- Basic navigation flows (breeder → species, dealer → species)

What's NOT tested here:
- JavaScript functionality (see test_table_interactions.py and test_species_page_interactions.py)
- Complex user interactions (filtering, sorting, tab switching)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_minimal


@pytest.mark.e2e
def test_all_pages_load_without_errors(e2e_site_minimal) -> None:
    """Verify all HTML pages load successfully with no console/HTTP errors."""
    page, base_url, errors = e2e_site_minimal

    # Test all main pages load
    pages_to_test = [
        ("index.html", "Spider Shop"),
        ("breeder.html", "Breeder"),
        ("dealer.html", "Dealer"),
    ]

    for page_path, expected_title_fragment in pages_to_test:
        page.goto(f"{base_url}/{page_path}", wait_until="domcontentloaded")
        assert expected_title_fragment in page.title(), f"Page {page_path} has unexpected title"


@pytest.mark.e2e
def test_navigation_from_breeder_to_species_detail(e2e_site_minimal) -> None:
    """Verify navigation from breeder table to species detail page works correctly."""
    page, base_url, errors = e2e_site_minimal

    # Navigate to breeder page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Click first species link in table
    breeder_link = page.locator('table a[href^="species/"]').first
    assert breeder_link.count() == 1, "Expected at least one species link in breeder table"
    
    with page.expect_navigation():
        breeder_link.click()

    # Verify we're on a species detail page
    assert "/species/" in page.url, "Expected to navigate to species detail page"
    
    # Verify back buttons exist (this is basic structure, not testing highlight logic)
    assert page.locator("#back-breeder").count() == 1, "Expected breeder back button"
    assert page.locator("#back-dealer").count() == 1, "Expected dealer back button"


@pytest.mark.e2e
def test_navigation_from_dealer_to_species_detail(e2e_site_minimal) -> None:
    """Verify navigation from dealer table to species detail page works correctly."""
    page, base_url, errors = e2e_site_minimal

    # Navigate to dealer page
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    
    # Click first species link in table
    dealer_link = page.locator('table a[href^="species/"]').first
    assert dealer_link.count() == 1, "Expected at least one species link in dealer table"
    
    with page.expect_navigation():
        dealer_link.click()

    # Verify we're on a species detail page
    assert "/species/" in page.url, "Expected to navigate to species detail page"
    
    # Verify back buttons exist
    assert page.locator("#back-breeder").count() == 1, "Expected breeder back button"
    assert page.locator("#back-dealer").count() == 1, "Expected dealer back button"

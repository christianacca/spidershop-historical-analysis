#!/usr/bin/env python3
"""E2E tests for scroll position restoration on back navigation.

Scope:
- Scroll position is saved when leaving a listing page (breeder/dealer) towards a species page
- Scroll position is restored when going back from a species page to the listing page
- Works on mobile portrait viewport (the most painful user-experience case)

What's NOT tested here:
- Scroll restoration for non-VT browsers (handled by browser's built-in scroll restoration)
- Scroll restoration between non-species pages
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_multi_species


def _set_mobile_portrait(page) -> None:
    """Set viewport to a standard mobile portrait size."""
    page.set_viewport_size({"width": 375, "height": 812})


def _wait_for_table_ready(page) -> None:
    """Wait for the Svelte table to be fully mounted and visible."""
    page.wait_for_selector('[data-table-ready="true"]', state='attached', timeout=5000)
    page.wait_for_timeout(100)  # Allow render to settle


@pytest.mark.e2e
def test_scroll_position_restored_when_going_back_to_breeder_page(e2e_site_multi_species) -> None:
    """Scroll position should be restored when navigating back from species to breeder page.

    On mobile portrait the table renders as full-width cards (not a table).
    Without scroll restoration, the user loses their position in the list every
    time they tap a species link and hit Back — the page returns to the top.
    """
    page, base_url, _ = e2e_site_multi_species

    _set_mobile_portrait(page)

    # Navigate to breeder page and wait for table
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    _wait_for_table_ready(page)

    # Scroll down to a position that should be within the skeleton height (modest amount)
    page.evaluate("window.scrollTo(0, 250)")
    page.wait_for_timeout(150)

    scroll_before = page.evaluate("window.scrollY")
    assert scroll_before >= 200, (
        f"Expected page to scroll to at least 200px (got {scroll_before}). "
        "Page may not be tall enough — check fixture data."
    )

    # Navigate to a species page via the table link
    species_link = page.locator('table a[href^="species/"], a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()

    assert "/species/" in page.url, "Expected to navigate to a species detail page"

    # Navigate back using the "Back to Breeder Table" button
    back_btn = page.locator("#back-breeder")
    assert back_btn.count() == 1, "Expected #back-breeder button on species page"

    with page.expect_navigation():
        back_btn.click()

    # Wait for the view transition animation (0.3 s) and table mount (≤ 520 ms)
    page.wait_for_timeout(700)

    scroll_after = page.evaluate("window.scrollY")
    assert scroll_after >= 150, (
        f"Expected scroll position to be restored to ~{scroll_before}px after back navigation, "
        f"but got {scroll_after}px. The page is scrolled to the top instead of the previous position."
    )


@pytest.mark.e2e
def test_scroll_position_restored_when_going_back_to_dealer_page(e2e_site_multi_species) -> None:
    """Scroll position should be restored when navigating back from species to dealer page."""
    page, base_url, _ = e2e_site_multi_species

    _set_mobile_portrait(page)

    # Navigate to dealer page and wait for table
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    _wait_for_table_ready(page)

    # Scroll down to a modest position
    page.evaluate("window.scrollTo(0, 250)")
    page.wait_for_timeout(150)

    scroll_before = page.evaluate("window.scrollY")
    assert scroll_before >= 200, (
        f"Expected page to scroll to at least 200px (got {scroll_before}). "
        "Page may not be tall enough — check fixture data."
    )

    # Navigate to a species page via the table link
    species_link = page.locator('table a[href^="species/"], a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()

    assert "/species/" in page.url, "Expected to navigate to a species detail page"

    # Navigate back using the "Back to Dealer Table" button
    back_btn = page.locator("#back-dealer")
    assert back_btn.count() == 1, "Expected #back-dealer button on species page"

    with page.expect_navigation():
        back_btn.click()

    # Wait for the view transition animation and table mount
    page.wait_for_timeout(700)

    scroll_after = page.evaluate("window.scrollY")
    assert scroll_after >= 150, (
        f"Expected scroll position to be restored to ~{scroll_before}px after back navigation, "
        f"but got {scroll_after}px. The page is scrolled to the top instead of the previous position."
    )


@pytest.mark.e2e
def test_no_scroll_restoration_on_direct_page_load(e2e_site_multi_species) -> None:
    """Scroll position should NOT be restored on direct navigation (not back from species)."""
    page, base_url, _ = e2e_site_multi_species

    _set_mobile_portrait(page)

    # First visit to breeder page (direct), scroll, then navigate to dealer (non-species)
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    _wait_for_table_ready(page)

    page.evaluate("window.scrollTo(0, 300)")
    page.wait_for_timeout(150)

    # Navigate to dealer page (not a species page — no backward VT applies)
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    _wait_for_table_ready(page)

    scroll_on_dealer = page.evaluate("window.scrollY")
    # Dealer page should start at the top (no scroll restoration for non-species back nav)
    assert scroll_on_dealer < 100, (
        f"Dealer page should start near top on direct load, got scrollY={scroll_on_dealer}"
    )

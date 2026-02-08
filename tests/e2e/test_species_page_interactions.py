#!/usr/bin/env python3
"""E2E tests for species detail page interactions.

Scope:
- Tab switching between Breeder and Dealer views
- URL parameter initialization (?view=breeder or ?view=dealer)
- URL updates via window.history.pushState() when switching tabs
- Back button highlighting logic (sync with active tab)
- ARIA attribute updates during tab switches

What's NOT tested here:
- Basic page loads and navigation (see test_navigation_and_page_loads.py)
- Table interactions (see test_table_interactions.py)
- Chart rendering (future: low priority)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_minimal


@pytest.mark.e2e
def test_tab_switching_between_breeder_and_dealer_views(e2e_site_minimal) -> None:
    """Verify clicking tabs switches between breeder and dealer panels correctly."""
    page, base_url, errors = e2e_site_minimal

    # Navigate from breeder page to species detail
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Initially breeder view should be active (default)
    breeder_tab = page.locator("#tab-breeder")
    dealer_tab = page.locator("#tab-dealer")
    breeder_panel = page.locator("#panel-breeder")
    dealer_panel = page.locator("#panel-dealer")
    
    # Verify initial state (breeder active)
    assert breeder_tab.get_attribute("aria-selected") == "true", "Breeder tab should be active initially"
    assert dealer_tab.get_attribute("aria-selected") == "false", "Dealer tab should not be active initially"
    assert breeder_panel.is_visible(), "Breeder panel should be visible"
    assert not dealer_panel.is_visible(), "Dealer panel should be hidden"
    
    # Click dealer tab
    dealer_tab.click()
    page.wait_for_timeout(100)
    
    # Verify dealer view is now active
    assert dealer_tab.get_attribute("aria-selected") == "true", "Dealer tab should be active after click"
    assert breeder_tab.get_attribute("aria-selected") == "false", "Breeder tab should not be active after click"
    assert dealer_panel.is_visible(), "Dealer panel should be visible after click"
    assert not breeder_panel.is_visible(), "Breeder panel should be hidden after click"
    
    # Click breeder tab to switch back
    breeder_tab.click()
    page.wait_for_timeout(100)
    
    # Verify back to breeder view
    assert breeder_tab.get_attribute("aria-selected") == "true", "Breeder tab should be active again"
    assert dealer_tab.get_attribute("aria-selected") == "false", "Dealer tab should not be active again"
    assert breeder_panel.is_visible(), "Breeder panel should be visible again"
    assert not dealer_panel.is_visible(), "Dealer panel should be hidden again"


@pytest.mark.e2e
def test_url_parameter_initializes_correct_tab_on_load(e2e_site_minimal) -> None:
    """Verify ?view=dealer URL parameter activates dealer tab on page load."""
    page, base_url, errors = e2e_site_minimal

    # Navigate from dealer page to species detail (URL will have ?view=dealer)
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Wait for page to load and JS to initialize
    page.wait_for_timeout(200)
    
    # Verify dealer tab is active (because we came from dealer page)
    dealer_tab = page.locator("#tab-dealer")
    breeder_tab = page.locator("#tab-breeder")
    dealer_panel = page.locator("#panel-dealer")
    breeder_panel = page.locator("#panel-breeder")
    
    assert "?view=dealer" in page.url, "URL should contain ?view=dealer parameter"
    assert dealer_tab.get_attribute("aria-selected") == "true", "Dealer tab should be active on load"
    assert breeder_tab.get_attribute("aria-selected") == "false", "Breeder tab should not be active on load"
    assert dealer_panel.is_visible(), "Dealer panel should be visible on load"
    assert not breeder_panel.is_visible(), "Breeder panel should be hidden on load"


@pytest.mark.e2e
def test_url_updates_on_tab_switch_via_pushstate(e2e_site_minimal) -> None:
    """Verify URL changes when switching tabs (without page reload)."""
    page, base_url, errors = e2e_site_minimal

    # Navigate from breeder page to species detail
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Initial URL should have ?view=breeder
    assert "?view=breeder" in page.url, "URL should start with ?view=breeder"
    
    # Click dealer tab
    dealer_tab = page.locator("#tab-dealer")
    dealer_tab.click()
    page.wait_for_timeout(200)
    
    # URL should now have ?view=dealer (without full page reload)
    assert "?view=dealer" in page.url, "URL should update to ?view=dealer after clicking dealer tab"
    
    # Click breeder tab
    breeder_tab = page.locator("#tab-breeder")
    breeder_tab.click()
    page.wait_for_timeout(200)
    
    # URL should be back to ?view=breeder
    assert "?view=breeder" in page.url, "URL should update to ?view=breeder after clicking breeder tab"


@pytest.mark.e2e
def test_back_button_highlighting_syncs_with_active_tab(e2e_site_minimal) -> None:
    """Verify back button highlighting updates when switching between tabs."""
    page, base_url, errors = e2e_site_minimal

    # Navigate from breeder page to species detail
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Wait for JS to initialize highlighting
    page.wait_for_function(
        "document.getElementById('back-breeder')?.classList.contains('origin-btn') === true"
    )
    
    back_breeder = page.locator("#back-breeder")
    back_dealer = page.locator("#back-dealer")
    
    # Initially: breeder button should be highlighted (origin-btn class)
    assert "origin-btn" in back_breeder.get_attribute("class"), "Breeder back button should be highlighted initially"
    assert "origin-btn" not in back_dealer.get_attribute("class"), "Dealer back button should not be highlighted initially"
    
    # Switch to dealer tab
    dealer_tab = page.locator("#tab-dealer")
    dealer_tab.click()
    page.wait_for_timeout(200)
    
    # Now dealer button should be highlighted
    page.wait_for_function(
        "document.getElementById('back-dealer')?.classList.contains('origin-btn') === true"
    )
    
    assert "origin-btn" in back_dealer.get_attribute("class"), "Dealer back button should be highlighted after switching to dealer tab"
    assert "origin-btn" not in back_breeder.get_attribute("class"), "Breeder back button should not be highlighted after switching to dealer tab"
    
    # Switch back to breeder tab
    breeder_tab = page.locator("#tab-breeder")
    breeder_tab.click()
    page.wait_for_timeout(200)
    
    # Breeder button should be highlighted again
    page.wait_for_function(
        "document.getElementById('back-breeder')?.classList.contains('origin-btn') === true"
    )
    
    assert "origin-btn" in back_breeder.get_attribute("class"), "Breeder back button should be highlighted again after switching back"
    assert "origin-btn" not in back_dealer.get_attribute("class"), "Dealer back button should not be highlighted again after switching back"

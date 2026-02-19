#!/usr/bin/env python3
"""E2E tests for history page filter UI.

Scope (Step 1 — layout alignment):
- action-buttons bar renders with download link and More Filters toggle
- More Filters toggle shows/hides the advanced-filters panel
- Search input inside the panel filters rows
- Filter badge appears when search is active, hidden when cleared
- table-stats visible count updates as search filters rows

What's NOT tested here:
- Price/wishlist sliders (added in later steps)
- Date filter checkboxes (added in later steps)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_multi_species


@pytest.mark.e2e
def test_more_filters_toggle_shows_and_hides_panel(e2e_site_multi_species) -> None:
    """More Filters button should toggle the advanced-filters panel open and closed."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")

    panel = page.locator("#advanced-filters-history-table")

    # Panel is hidden initially
    assert not panel.is_visible(), "Filter panel should be hidden before toggle"

    # Click toggle — panel opens
    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)
    assert panel.is_visible(), "Filter panel should be visible after first click"

    # Click toggle again — panel closes
    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)
    assert not panel.is_visible(), "Filter panel should be hidden after second click"


@pytest.mark.e2e
def test_search_input_filters_history_rows(e2e_site_multi_species) -> None:
    """Typing in the search box should hide rows that don't match."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")

    total_rows = page.locator("#history-table tbody tr").count()
    assert total_rows > 1, "Expected more than one row to make search filtering meaningful"

    # Open the filter panel
    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)

    # Type a species name that matches only one row
    search_input = page.locator("input[data-action='search'][data-table-id='history-table']")
    search_input.fill("Aphonopelma")
    page.wait_for_timeout(200)

    visible_rows = page.locator("#history-table tbody tr:visible").count()
    hidden_rows = page.locator("#history-table tbody tr.hidden").count()

    assert visible_rows >= 1, "At least one row should remain visible after search"
    assert hidden_rows > 0, "Some rows should be hidden after search"
    assert visible_rows + hidden_rows == total_rows


@pytest.mark.e2e
def test_filter_badge_hidden_initially(e2e_site_multi_species) -> None:
    """Filter badge on the More Filters button should be hidden when no filters are active."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")

    badge = page.locator("#filterBadge-history-table")
    assert not badge.is_visible(), "Filter badge should be hidden when no filters are active"


@pytest.mark.e2e
def test_filter_badge_shows_when_search_active(e2e_site_multi_species) -> None:
    """Filter badge should appear and show '1' when search filter is active."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")

    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)

    page.locator("input[data-action='search'][data-table-id='history-table']").fill("Aphonopelma")
    page.wait_for_timeout(200)

    badge = page.locator("#filterBadge-history-table")
    assert badge.is_visible(), "Filter badge should be visible when search is active"
    assert badge.text_content() == "1", "Filter badge should show '1' for one active filter"


@pytest.mark.e2e
def test_filter_badge_hidden_after_search_cleared(e2e_site_multi_species) -> None:
    """Filter badge should disappear when search input is cleared."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")

    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)

    search_input = page.locator("input[data-action='search'][data-table-id='history-table']")
    search_input.fill("Aphonopelma")
    page.wait_for_timeout(200)

    # Now clear the search
    search_input.fill("")
    page.wait_for_timeout(200)

    badge = page.locator("#filterBadge-history-table")
    assert not badge.is_visible(), "Filter badge should be hidden after search is cleared"


@pytest.mark.e2e
def test_visible_count_updates_with_search(e2e_site_multi_species) -> None:
    """The table-stats 'Showing: X of Y' count should update as search filters rows."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")

    total_rows = page.locator("#history-table tbody tr").count()

    # Initial count should equal total rows
    visible_count_initial = page.locator("#visible-count-history-table").text_content()
    assert visible_count_initial == str(total_rows), (
        f"Initial visible count should be {total_rows}, got '{visible_count_initial}'"
    )

    # Open filters and search
    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)
    page.locator("input[data-action='search'][data-table-id='history-table']").fill("Aphonopelma")
    page.wait_for_timeout(200)

    visible_count_after = int(page.locator("#visible-count-history-table").text_content())
    assert visible_count_after < total_rows, "Visible count should decrease after search filters rows"
    assert visible_count_after >= 1, "Visible count should be at least 1 when a matching row exists"


# ---------------------------------------------------------------------------
# Step 2: Price range slider
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_price_sliders_exist_and_initialise_correctly(e2e_site_multi_species) -> None:
    """Price sliders should render with min/max derived from CSV data after opening filters."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")
    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)

    price_min_slider = page.locator("#priceMin")
    price_max_slider = page.locator("#priceMax")
    assert price_min_slider.is_visible(), "priceMin slider should be visible after opening filters"
    assert price_max_slider.is_visible(), "priceMax slider should be visible after opening filters"

    data_min = price_min_slider.get_attribute("min")
    data_max = price_max_slider.get_attribute("max")
    assert data_min is not None and data_min.replace(".", "", 1).lstrip("-").isdigit()
    assert data_max is not None and data_max.replace(".", "", 1).lstrip("-").isdigit()

    # Sliders start at their respective extremes
    assert price_min_slider.get_attribute("value") == data_min
    assert price_max_slider.get_attribute("value") == data_max

    # Display text reflects initial range
    display = page.locator("#priceDisplay")
    assert display.is_visible()
    display_text = display.text_content()
    assert f"£{data_min}" in display_text and f"£{data_max}" in display_text


@pytest.mark.e2e
def test_price_max_slider_hides_rows_above_threshold(e2e_site_multi_species) -> None:
    """Moving price max slider down should hide rows with data-price above the threshold."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")
    total_rows = page.locator("#history-table tbody tr").count()
    assert total_rows > 1

    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)

    # Set max to a value below the most expensive row (£35 in test data; set to £28)
    page.locator("#priceMax").fill("28")
    page.wait_for_timeout(200)

    visible = page.locator("#history-table tbody tr:visible").count()
    hidden = page.locator("#history-table tbody tr.hidden").count()
    assert visible > 0, "Some rows should remain visible"
    assert hidden > 0, "Some rows should be hidden above the threshold"
    assert visible + hidden == total_rows

    # Every visible row should have data-price <= 28
    for row in page.locator("#history-table tbody tr:visible").all():
        price = float(row.get_attribute("data-price"))
        assert price <= 28, f"Visible row has price {price} > 28"


@pytest.mark.e2e
def test_price_filter_badge_shows_one(e2e_site_multi_species) -> None:
    """Filter badge should show '1' when price range is narrowed."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")
    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)

    page.locator("#priceMax").fill("28")
    page.wait_for_timeout(200)

    badge = page.locator("#filterBadge-history-table")
    assert badge.is_visible(), "Badge should be visible when price filter is active"
    assert badge.text_content() == "1", f"Badge should show '1', got '{badge.text_content()}'"


@pytest.mark.e2e
def test_price_filter_reset_shows_all_rows(e2e_site_multi_species) -> None:
    """Resetting price max slider to data max should make all rows visible again."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")
    total_rows = page.locator("#history-table tbody tr").count()

    page.locator(".btn-filters").click()
    page.wait_for_timeout(200)

    price_max_slider = page.locator("#priceMax")
    data_max = price_max_slider.get_attribute("max")

    # Narrow then reset
    price_max_slider.fill("20")
    page.wait_for_timeout(200)
    price_max_slider.fill(data_max)
    page.wait_for_timeout(200)

    visible = page.locator("#history-table tbody tr:visible").count()
    assert visible == total_rows, f"All {total_rows} rows should be visible after reset, got {visible}"

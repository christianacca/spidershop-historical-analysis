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

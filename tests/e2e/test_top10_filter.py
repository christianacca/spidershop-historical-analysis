#!/usr/bin/env python3
"""E2E tests for the 🔥 Hot (top 10) filter button.

Scope:
- Clicking '🔥 Hot (top 10)' limits visible rows to 10 when >10 Hot rows exist
- Only Hot rows are shown after clicking the button
- Regular '🔥 Hot' (no limit) shows all Hot rows
- 'Show All' resets after applying the top-10 filter
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_large_table


@pytest.mark.e2e
def test_hot_top_10_button_limits_visible_rows_to_10(e2e_site_large_table) -> None:
    """Clicking '🔥 Hot (top 10)' should show at most 10 rows when >10 Hot rows exist."""
    page, base_url, errors = e2e_site_large_table

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    # All 20 rows visible initially
    all_rows = page.locator('#breeder-table tbody tr').count()
    assert all_rows == 20, f"Expected 20 rows in test data, got {all_rows}"

    # Click the '🔥 Hot (top 10)' button (identified by data-limit attribute)
    top10_button = page.locator('button[data-action="filter-signal"][data-limit="10"]')
    top10_button.click()
    page.wait_for_timeout(100)

    # Exactly 10 rows should be visible (not all 15 Hot rows)
    visible_rows = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_rows == 10, f"Expected exactly 10 visible rows after Hot (top 10) filter, got {visible_rows}"

    # The button should be active
    assert "active" in top10_button.get_attribute("class"), "Expected active class on Hot (top 10) button"


@pytest.mark.e2e
def test_hot_top_10_button_shows_only_hot_rows(e2e_site_large_table) -> None:
    """Clicking '🔥 Hot (top 10)' should only show rows with data-signal='🔥'."""
    page, base_url, errors = e2e_site_large_table

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    top10_button = page.locator('button[data-action="filter-signal"][data-limit="10"]')
    top10_button.click()
    page.wait_for_timeout(100)

    # All visible rows should be Hot — no Watch or Avoid rows visible
    non_hot_visible = page.locator('#breeder-table tbody tr:visible').filter(
        has_not=page.locator('text="🔥"')
    ).count()
    assert non_hot_visible == 0, f"Expected no non-Hot rows visible, got {non_hot_visible}"


@pytest.mark.e2e
def test_hot_full_button_shows_all_hot_rows(e2e_site_large_table) -> None:
    """Clicking '🔥 Hot' (no limit) should show all 15 Hot rows, not just 10."""
    page, base_url, errors = e2e_site_large_table

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    # Click the regular '🔥 Hot' button (no data-limit attribute)
    hot_button = page.locator(
        'button[data-action="filter-signal"][data-signal="🔥"]:not([data-limit])'
    )
    hot_button.click()
    page.wait_for_timeout(100)

    visible_rows = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_rows == 15, f"Expected all 15 Hot rows visible (no limit), got {visible_rows}"


@pytest.mark.e2e
def test_show_all_resets_after_hot_top_10_filter(e2e_site_large_table) -> None:
    """Clicking 'Show All' after '🔥 Hot (top 10)' should restore all 20 rows."""
    page, base_url, errors = e2e_site_large_table

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    # Apply the top 10 filter first
    top10_button = page.locator('button[data-action="filter-signal"][data-limit="10"]')
    top10_button.click()
    page.wait_for_timeout(100)

    # Then reset with Show All
    show_all = page.locator('button[data-action="filter-signal"][data-signal="all"]')
    show_all.click()
    page.wait_for_timeout(100)

    visible_rows = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_rows == 20, f"Expected all 20 rows after Show All, got {visible_rows}"

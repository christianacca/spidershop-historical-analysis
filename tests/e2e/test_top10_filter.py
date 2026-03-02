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
    assert "is-active" in top10_button.get_attribute("class"), "Expected is-active class on Hot (top 10) button"


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


@pytest.mark.e2e
@pytest.mark.parametrize(
    "header_key,first_visible_after_sort",
    [
        ("Species", "Watch Species 03"),  # desc alpha sort: Watch > Hot > Avoid
        ("Price", "Hot Species 01"),
    ],
)
def test_hot_top_10_shows_same_entries_regardless_of_sort_order(
    e2e_site_large_table, header_key: str, first_visible_after_sort: str
) -> None:
    """'Hot (top 10)' should always show the same 10 species in original CSV order,
    regardless of any active sort.

    Regression test: when sorted first, Hot (top 10) must still select the first 10
    HOT entries from original CSV order, not the first 10 visible rows in sorted DOM order.
    """
    page, base_url, errors = e2e_site_large_table

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    # Two clicks on the header to reach descending order (first click = asc, second = desc)
    # Use :text-is() for exact match to avoid matching "Price History" when header_key="Price"
    sortable_header = page.locator(f'#breeder-table thead th:text-is("{header_key}")')
    sortable_header.click()
    page.wait_for_timeout(100)
    sortable_header.click()
    page.wait_for_timeout(100)

    visible_rows_after_sort = page.locator('#breeder-table tbody tr:visible')
    assert visible_rows_after_sort.first.locator('td').first.text_content() == first_visible_after_sort

    top10_button = page.locator('button[data-action="filter-signal"][data-limit="10"]')
    top10_button.click()
    page.wait_for_timeout(100)

    visible_rows = page.locator('#breeder-table tbody tr:visible')
    assert visible_rows.count() == 10

    # The first 10 from original CSV order must be present
    assert visible_rows.filter(has_text="Hot Species 01").count() == 1, (
        "'Hot Species 01' must be visible — it is in the original top 10"
    )
    # The last 5 Hot rows must NOT be visible
    assert visible_rows.filter(has_text="Hot Species 15").count() == 0, (
        "'Hot Species 15' must not be visible — it is outside the original top 10 in CSV order"
    )

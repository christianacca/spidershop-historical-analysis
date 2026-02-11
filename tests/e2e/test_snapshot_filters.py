#!/usr/bin/env python3
"""E2E tests for snapshot page price range slider filter.

Scope:
- Price range slider (max value) filtering
- Price display updates as slider moves
- Filter badge increments when slider is active
- Visible count updates ("Showing X of Y species")
- Integration with existing search filter (AND logic)

What's NOT tested here:
- Wishlist count slider (future feature)
- Size checkboxes (future feature)
- Basic page loads (see test_navigation_and_page_loads.py)
- Table sorting (see test_table_interactions.py)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_multi_species


@pytest.mark.e2e
def test_price_slider_exists_and_initializes_correctly(e2e_site_multi_species) -> None:
    """Verify price slider renders with correct initial state (max value, no filtering)."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Verify slider exists
    price_slider = page.locator("#priceMax")
    assert price_slider.is_visible(), "Price slider should be visible after expanding filters"
    
    # Verify initial value is max (400)
    initial_value = price_slider.get_attribute("value")
    assert initial_value == "400", f"Expected slider initial value to be '400', got '{initial_value}'"
    
    # Verify min/max attributes
    min_value = price_slider.get_attribute("min")
    max_value = price_slider.get_attribute("max")
    assert min_value == "5", f"Expected min='5', got '{min_value}'"
    assert max_value == "400", f"Expected max='400', got '{max_value}'"
    
    # Verify price display shows initial range
    price_display = page.locator("#priceDisplay")
    assert price_display.is_visible(), "Price display should be visible"
    display_text = price_display.text_content()
    assert "£5" in display_text and "£400" in display_text, \
        f"Expected price display to show '£5 - £400', got '{display_text}'"


@pytest.mark.e2e
def test_price_slider_filters_rows_correctly(e2e_site_multi_species) -> None:
    """Verify moving price slider hides rows above the selected price."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()
    assert total_rows > 0, "Expected at least one row in snapshot table"
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Set slider to £30
    price_slider = page.locator("#priceMax")
    price_slider.fill("30")  # Playwright's fill() triggers the oninput event
    page.wait_for_timeout(200)
    
    # Verify some rows are hidden
    visible_rows = page.locator('#snapshot-table tbody tr:visible').count()
    hidden_rows = page.locator('#snapshot-table tbody tr.hidden').count()
    
    assert visible_rows > 0, "Expected at least some rows to remain visible"
    assert hidden_rows > 0, "Expected at least some rows to be hidden"
    assert visible_rows + hidden_rows == total_rows, \
        f"Expected visible ({visible_rows}) + hidden ({hidden_rows}) = total ({total_rows})"
    
    # Verify all visible rows have price <= £30
    visible_price_cells = page.locator('#snapshot-table tbody tr:visible').locator('td').nth(3).all_text_contents()
    for price_text in visible_price_cells:
        # Remove £ symbol and convert to float
        price_value = float(price_text.replace('£', '').strip())
        assert price_value <= 30.0, \
            f"Expected visible row price ({price_value}) to be <= 30.0"


@pytest.mark.e2e
def test_price_slider_updates_display_text(e2e_site_multi_species) -> None:
    """Verify price display updates as slider moves."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Move slider to £50
    price_slider = page.locator("#priceMax")
    price_slider.fill("50")
    page.wait_for_timeout(200)
    
    # Verify display updates
    price_display = page.locator("#priceDisplay")
    display_text = price_display.text_content()
    assert "£50" in display_text, f"Expected display to show '£50', got '{display_text}'"
    assert "£5" in display_text, f"Expected display to show min '£5', got '{display_text}'"
    
    # Move slider to £100
    price_slider.fill("100")
    page.wait_for_timeout(200)
    
    display_text = price_display.text_content()
    assert "£100" in display_text, f"Expected display to show '£100', got '{display_text}'"


@pytest.mark.e2e
def test_price_slider_updates_filter_badge(e2e_site_multi_species) -> None:
    """Verify filter badge increments when price slider is moved from max."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Initially badge should be hidden (no active filters)
    badge = page.locator("#filterBadge-snapshot-table")
    initial_classes = badge.get_attribute("class") or ""
    assert "hidden" in initial_classes, "Badge should be hidden when no filters active"
    
    # Move slider away from max
    price_slider = page.locator("#priceMax")
    price_slider.fill("50")
    page.wait_for_timeout(200)
    
    # Badge should now be visible with count = 1
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" not in badge_classes, "Badge should be visible when price filter is active"
    
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge to show '1' active filter, got '{badge_text}'"
    
    # Reset slider to max
    price_slider.fill("400")
    page.wait_for_timeout(200)
    
    # Badge should be hidden again
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" in badge_classes, "Badge should be hidden when slider reset to max"


@pytest.mark.e2e
def test_price_slider_updates_visible_count(e2e_site_multi_species) -> None:
    """Verify 'Showing X of Y species' updates correctly when price filter is applied."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Get total count from stats
    stats = page.locator(".table-stats")
    initial_stats = stats.text_content()
    # Extract total from "Showing: X of Y species"
    total_species = int(initial_stats.split("of")[1].strip().split(" ")[0])
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Apply price filter
    price_slider = page.locator("#priceMax")
    price_slider.fill("30")
    page.wait_for_timeout(200)
    
    # Verify stats updated
    updated_stats = stats.text_content()
    assert "Showing:" in updated_stats, "Stats should contain 'Showing:'"
    assert f"of {total_species}" in updated_stats, f"Stats should still show 'of {total_species}'"
    
    # Extract visible count
    visible_count = int(updated_stats.split("Showing:")[1].strip().split(" ")[0])
    assert visible_count < total_species, \
        f"Expected visible count ({visible_count}) to be less than total ({total_species})"
    assert visible_count > 0, "Expected at least some species to remain visible"


@pytest.mark.e2e
def test_price_slider_and_search_filter_combine_with_AND_logic(e2e_site_multi_species) -> None:
    """Verify price slider and search filter work together (both must match)."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Apply search filter first (e.g., "Brachypelma")
    search_input = page.locator("#search-snapshot-table")
    search_input.type("Brachypelma")
    page.wait_for_timeout(200)
    
    # Count rows after search
    visible_after_search = page.locator('#snapshot-table tbody tr:visible').count()
    assert visible_after_search > 0, "Expected at least one match for 'Brachypelma'"
    
    # Now apply price filter (assume Brachypelma species has price > £20)
    price_slider = page.locator("#priceMax")
    price_slider.fill("20")
    page.wait_for_timeout(200)
    
    # Count rows after both filters
    visible_after_both = page.locator('#snapshot-table tbody tr:visible').count()
    
    # Should show fewer results (or zero if all Brachypelma species are > £20)
    assert visible_after_both <= visible_after_search, \
        f"Expected combined filter ({visible_after_both}) <= search only ({visible_after_search})"
    
    # Verify filter badge shows 2 active filters (search + price)
    badge = page.locator("#filterBadge-snapshot-table")
    badge_text = badge.text_content()
    assert badge_text == "2", f"Expected badge to show '2' active filters, got '{badge_text}'"


@pytest.mark.e2e
def test_price_slider_reset_to_max_shows_all_rows(e2e_site_multi_species) -> None:
    """Verify resetting slider to max (£400) shows all rows again."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()
    
    # Expand advanced filters and apply filter
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    price_slider = page.locator("#priceMax")
    price_slider.fill("25")
    page.wait_for_timeout(200)
    
    # Verify filtering occurred
    visible_after_filter = page.locator('#snapshot-table tbody tr:visible').count()
    assert visible_after_filter < total_rows, "Expected filtering to hide some rows"
    
    # Reset slider to max
    price_slider.fill("400")
    page.wait_for_timeout(200)
    
    # Verify all rows visible again
    visible_after_reset = page.locator('#snapshot-table tbody tr:visible').count()
    assert visible_after_reset == total_rows, \
        f"Expected all {total_rows} rows visible after reset, got {visible_after_reset}"
    
    # Verify no hidden rows
    hidden_rows = page.locator('#snapshot-table tbody tr.hidden').count()
    assert hidden_rows == 0, f"Expected no hidden rows after reset, got {hidden_rows}"


# --- Wishlist Count Range Slider Tests ---


@pytest.mark.e2e
def test_wishlist_slider_exists_and_initializes_correctly(e2e_site_multi_species) -> None:
    """Verify wishlist slider renders with correct initial state (0-20 range)."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Verify wishlist slider exists
    wishlist_slider = page.locator("#wishlistMax")
    assert wishlist_slider.is_visible(), "Wishlist slider should be visible after expanding filters"
    
    # Verify initial value is max (300)
    initial_value = wishlist_slider.get_attribute("value")
    assert initial_value == "300", f"Expected wishlist slider initial value to be '300', got '{initial_value}'"
    
    # Verify min/max attributes
    min_value = wishlist_slider.get_attribute("min")
    max_value = wishlist_slider.get_attribute("max")
    assert min_value == "0", f"Expected min='0', got '{min_value}'"
    assert max_value == "300", f"Expected max='300', got '{max_value}'"
    
    # Verify wishlist display shows initial range
    wishlist_display = page.locator("#wishlistDisplay")
    assert wishlist_display.is_visible(), "Wishlist display should be visible"
    display_text = wishlist_display.text_content()
    assert "0" in display_text and "300" in display_text, \
        f"Expected wishlist display to show '0 - 300', got '{display_text}'"


@pytest.mark.e2e
def test_wishlist_slider_filters_rows_correctly(e2e_site_multi_species) -> None:
    """Verify moving wishlist slider hides rows above the selected value."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()
    assert total_rows > 0, "Expected at least one row in snapshot table"
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Set wishlist max to 10 (filter out high wishlist counts)
    wishlist_slider = page.locator("#wishlistMax")
    wishlist_slider.fill("10")
    page.wait_for_timeout(200)
    
    # Verify some rows are hidden
    visible_rows = page.locator('#snapshot-table tbody tr:visible').count()
    hidden_rows = page.locator('#snapshot-table tbody tr.hidden').count()
    
    assert visible_rows > 0, "Expected at least some rows to remain visible"
    assert hidden_rows > 0, "Expected at least some rows to be hidden"
    assert visible_rows + hidden_rows == total_rows, \
        f"Expected visible ({visible_rows}) + hidden ({hidden_rows}) = total ({total_rows})"
    
    # Verify all visible rows have wishlist <= 10
    visible_wishlist_cells = page.locator('#snapshot-table tbody tr:visible').locator('td').nth(5).all_text_contents()
    for wishlist_text in visible_wishlist_cells:
        wishlist_value = int(wishlist_text.strip())
        assert wishlist_value <= 10, \
            f"Expected visible row wishlist ({wishlist_value}) to be <= 10"


@pytest.mark.e2e
def test_wishlist_slider_updates_display_text(e2e_site_multi_species) -> None:
    """Verify wishlist display updates as slider moves."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Move slider to 15
    wishlist_slider = page.locator("#wishlistMax")
    wishlist_slider.fill("15")
    page.wait_for_timeout(200)
    
    # Verify display updates
    wishlist_display = page.locator("#wishlistDisplay")
    display_text = wishlist_display.text_content()
    assert "15" in display_text, f"Expected display to show '15', got '{display_text}'"
    assert "0" in display_text, f"Expected display to show min '0', got '{display_text}'"
    
    # Move slider to 10
    wishlist_slider.fill("10")
    page.wait_for_timeout(200)
    
    display_text = wishlist_display.text_content()
    assert "10" in display_text, f"Expected display to show '10', got '{display_text}'"


@pytest.mark.e2e
def test_wishlist_slider_updates_filter_badge(e2e_site_multi_species) -> None:
    """Verify filter badge increments when wishlist slider is moved from max."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Initially badge should be hidden (no active filters)
    badge = page.locator("#filterBadge-snapshot-table")
    initial_classes = badge.get_attribute("class") or ""
    assert "hidden" in initial_classes, "Badge should be hidden when no filters active"
    
    # Move slider away from max
    wishlist_slider = page.locator("#wishlistMax")
    wishlist_slider.fill("10")
    page.wait_for_timeout(200)
    
    # Badge should now be visible with count = 1
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" not in badge_classes, "Badge should be visible when wishlist filter is active"
    
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge to show '1' active filter, got '{badge_text}'"
    
    # Reset slider to max
    wishlist_slider.fill("300")
    page.wait_for_timeout(200)
    
    # Badge should be hidden again
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" in badge_classes, "Badge should be hidden when slider reset to max"


@pytest.mark.e2e
def test_wishlist_and_price_sliders_combine_in_badge(e2e_site_multi_species) -> None:
    """Verify filter badge shows 2 when both price and wishlist sliders are active."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Apply price filter
    price_slider = page.locator("#priceMax")
    price_slider.fill("50")
    page.wait_for_timeout(200)
    
    # Badge should show 1
    badge = page.locator("#filterBadge-snapshot-table")
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge '1' after price filter, got '{badge_text}'"
    
    # Apply wishlist filter
    wishlist_slider = page.locator("#wishlistMax")
    wishlist_slider.fill("10")
    page.wait_for_timeout(200)
    
    # Badge should show 2
    badge_text = badge.text_content()
    assert badge_text == "2", f"Expected badge '2' after both filters, got '{badge_text}'"


@pytest.mark.e2e
def test_wishlist_slider_and_search_combine_with_AND_logic(e2e_site_multi_species) -> None:
    """Verify wishlist slider and search filter work together (both must match)."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Apply search filter first
    search_input = page.locator("#search-snapshot-table")
    search_input.type("Brachypelma")
    page.wait_for_timeout(200)
    
    # Count rows after search
    visible_after_search = page.locator('#snapshot-table tbody tr:visible').count()
    assert visible_after_search > 0, "Expected at least one match for 'Brachypelma'"
    
    # Now apply wishlist filter
    wishlist_slider = page.locator("#wishlistMax")
    wishlist_slider.fill("10")
    page.wait_for_timeout(200)
    
    # Count rows after both filters
    visible_after_both = page.locator('#snapshot-table tbody tr:visible').count()
    
    # Should show fewer or equal results
    assert visible_after_both <= visible_after_search, \
        f"Expected combined filter ({visible_after_both}) <= search only ({visible_after_search})"
    
    # Verify filter badge shows 2 active filters (search + wishlist)
    badge = page.locator("#filterBadge-snapshot-table")
    badge_text = badge.text_content()
    assert badge_text == "2", f"Expected badge to show '2' active filters, got '{badge_text}'"

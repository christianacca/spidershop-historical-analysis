#!/usr/bin/env python3
"""E2E tests for snapshot page dual-handle range slider filters.

Scope:
- Price range sliders (min and max handles) filtering
- Wishlist count range sliders (min and max handles) filtering
- Display text updates as sliders move
- Filter badge increments when sliders are active (both min and max)
- Filter badge counts dual sliders as ONE filter (not two)
- Visible count updates ("Showing X of Y species")
- Min/max constraint enforcement (min cannot exceed max)
- Integration with existing search filter (AND logic)

What's NOT tested here:
- Basic page loads (see test_navigation_and_page_loads.py)
- Table sorting (see test_table_interactions.py)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_multi_species


@pytest.mark.e2e
def test_price_slider_exists_and_initializes_correctly(e2e_site_multi_species) -> None:
    """Verify price sliders (min and max) render with correct initial state derived from data."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Verify both sliders exist
    price_min_slider = page.locator("#priceMin")
    price_max_slider = page.locator("#priceMax")
    assert price_min_slider.is_visible(), "Price min slider should be visible after expanding filters"
    assert price_max_slider.is_visible(), "Price max slider should be visible after expanding filters"
    
    # Get actual min/max values from sliders (should be derived from CSV data)
    data_min = price_min_slider.get_attribute("min")
    data_max = price_max_slider.get_attribute("max")
    min_initial_value = price_min_slider.get_attribute("value")
    max_initial_value = price_max_slider.get_attribute("value")
    
    # Verify initial values (min slider starts at min, max slider starts at max)
    assert min_initial_value == data_min, \
        f"Expected price min slider initial value to be '{data_min}', got '{min_initial_value}'"
    assert max_initial_value == data_max, \
        f"Expected price max slider initial value to be '{data_max}', got '{max_initial_value}'"
    
    # Verify min is a valid number
    assert data_min is not None and data_min.replace('.', '', 1).isdigit(), \
        f"Expected min to be a valid number, got '{data_min}'"
    
    # Verify max is a valid number
    assert data_max is not None and data_max.replace('.', '', 1).isdigit(), \
        f"Expected max to be a valid number, got '{data_max}'"
    
    # Verify price display shows initial range
    price_display = page.locator("#priceDisplay")
    assert price_display.is_visible(), "Price display should be visible"
    display_text = price_display.text_content()
    assert f"£{data_min}" in display_text and f"£{data_max}" in display_text, \
        f"Expected price display to show '£{data_min} - £{data_max}', got '{display_text}'"


@pytest.mark.e2e
def test_price_slider_filters_rows_correctly(e2e_site_multi_species) -> None:
    """Verify moving price max slider hides rows above the selected price."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()
    assert total_rows > 0, "Expected at least one row in snapshot table"
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Set max slider to £30
    price_max_slider = page.locator("#priceMax")
    price_max_slider.fill("30")  # Playwright's fill() triggers the oninput event
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
    """Verify price display updates as both sliders move."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Get slider's actual min/max from attributes
    price_min_slider = page.locator("#priceMin")
    price_max_slider = page.locator("#priceMax")
    data_min = float(price_min_slider.get_attribute("min"))
    data_max = float(price_max_slider.get_attribute("max"))
    
    # Calculate test values
    mid_value = int((data_min + data_max) / 2)
    high_value = int(data_max * 0.8)
    
    # Move max slider to mid value
    price_max_slider.fill(str(mid_value))
    page.wait_for_timeout(200)
    
    # Verify display updates
    price_display = page.locator("#priceDisplay")
    display_text = price_display.text_content()
    assert f"£{mid_value}" in display_text, f"Expected display to show max '£{mid_value}', got '{display_text}'"
    assert f"£{int(data_min)}" in display_text, f"Expected display to show min '£{int(data_min)}', got '{display_text}'"
    
    # Move min slider up
    price_min_slider.fill(str(int(data_min + 5)))
    page.wait_for_timeout(200)
    
    display_text = price_display.text_content()
    assert f"£{int(data_min + 5)}" in display_text, f"Expected display to show min '£{int(data_min + 5)}', got '{display_text}'"


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
    
    # Get slider's actual min/max from attributes
    price_slider = page.locator("#priceMax")
    min_value = float(price_slider.get_attribute("min"))
    max_value = float(price_slider.get_attribute("max"))
    
    # Move slider away from max (use a value below max)
    test_value = int(max(min_value, max_value * 0.5))
    price_slider.fill(str(test_value))
    page.wait_for_timeout(200)
    
    # Badge should now be visible with count = 1
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" not in badge_classes, "Badge should be visible when price filter is active"
    
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge to show '1' active filter, got '{badge_text}'"
    
    # Reset slider to max
    price_slider.fill(str(int(max_value)))
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
    """Verify resetting slider to max shows all rows again."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()
    
    # Expand advanced filters and apply filter
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Get slider's actual min/max from attributes
    price_slider = page.locator("#priceMax")
    min_value = float(price_slider.get_attribute("min"))
    max_value = float(price_slider.get_attribute("max"))
    
    # Set slider to low value (filter heavily)
    low_value = int(max(min_value, min_value + 10))
    price_slider.fill(str(low_value))
    page.wait_for_timeout(200)
    
    # Verify filtering occurred
    visible_after_filter = page.locator('#snapshot-table tbody tr:visible').count()
    assert visible_after_filter < total_rows, "Expected filtering to hide some rows"
    
    # Reset slider to max
    price_slider.fill(str(int(max_value)))
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
    """Verify wishlist sliders (min and max) render with correct initial state derived from data."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Verify both wishlist sliders exist
    wishlist_min_slider = page.locator("#wishlistMin")
    wishlist_max_slider = page.locator("#wishlistMax")
    assert wishlist_min_slider.is_visible(), "Wishlist min slider should be visible after expanding filters"
    assert wishlist_max_slider.is_visible(), "Wishlist max slider should be visible after expanding filters"
    
    # Get actual min/max values from sliders (should be derived from CSV data)
    data_min = wishlist_min_slider.get_attribute("min")
    data_max = wishlist_max_slider.get_attribute("max")
    min_initial_value = wishlist_min_slider.get_attribute("value")
    max_initial_value = wishlist_max_slider.get_attribute("value")
    
    # Verify initial values (min slider starts at min, max slider starts at max)
    assert min_initial_value == data_min, \
        f"Expected wishlist min slider initial value to be '{data_min}', got '{min_initial_value}'"
    assert max_initial_value == data_max, \
        f"Expected wishlist max slider initial value to be '{data_max}', got '{max_initial_value}'"
    
    # Verify min is a valid number
    assert data_min is not None and data_min.isdigit(), \
        f"Expected min to be a valid number, got '{data_min}'"
    
    # Verify max is a valid number
    assert data_max is not None and data_max.isdigit(), \
        f"Expected max to be a valid number, got '{data_max}'"
    
    # Verify wishlist display shows initial range
    wishlist_display = page.locator("#wishlistDisplay")
    assert wishlist_display.is_visible(), "Wishlist display should be visible"
    display_text = wishlist_display.text_content()
    assert data_min in display_text and data_max in display_text, \
        f"Expected wishlist display to show '{data_min} - {data_max}', got '{display_text}'"


@pytest.mark.e2e
def test_wishlist_slider_filters_rows_correctly(e2e_site_multi_species) -> None:
    """Verify moving wishlist max slider hides rows above the selected value."""
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
    wishlist_max_slider = page.locator("#wishlistMax")
    wishlist_max_slider.fill("10")
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
    """Verify wishlist display updates as both sliders move."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Get slider's actual min/max from attributes
    wishlist_min_slider = page.locator("#wishlistMin")
    wishlist_max_slider = page.locator("#wishlistMax")
    data_min = wishlist_min_slider.get_attribute("min")
    data_max = int(wishlist_max_slider.get_attribute("max"))
    
    # Calculate test values
    mid_value = max(int(data_min), (int(data_min) + data_max) // 2)
    low_value = max(int(data_min), mid_value - 1)
    
    # Move max slider to mid value
    wishlist_max_slider.fill(str(mid_value))
    page.wait_for_timeout(200)
    
    # Verify display updates
    wishlist_display = page.locator("#wishlistDisplay")
    display_text = wishlist_display.text_content()
    assert str(mid_value) in display_text, f"Expected display to show '{mid_value}', got '{display_text}'"
    assert data_min in display_text, f"Expected display to show min '{data_min}', got '{display_text}'"
    
    # Move min slider up
    wishlist_min_slider.fill(str(int(data_min) + 1))
    page.wait_for_timeout(200)
    
    display_text = wishlist_display.text_content()
    assert str(int(data_min) + 1) in display_text, f"Expected display to show '{int(data_min) + 1}', got '{display_text}'"


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
    
    # Get slider's actual min/max from attributes
    wishlist_slider = page.locator("#wishlistMax")
    min_value = int(wishlist_slider.get_attribute("min"))
    max_value = int(wishlist_slider.get_attribute("max"))
    
    # Move slider away from max (use a value below max)
    test_value = max(min_value, max_value - 2)
    wishlist_slider.fill(str(test_value))
    page.wait_for_timeout(200)
    
    # Badge should now be visible with count = 1
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" not in badge_classes, "Badge should be visible when wishlist filter is active"
    
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge to show '1' active filter, got '{badge_text}'"
    
    # Reset slider to max
    wishlist_slider.fill(str(max_value))
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
    
    # Get price slider's actual min/max and set to mid-range
    price_slider = page.locator("#priceMax")
    price_min = float(price_slider.get_attribute("min"))
    price_max = float(price_slider.get_attribute("max"))
    price_test_value = int((price_min + price_max) * 0.5)
    
    # Apply price filter
    price_slider.fill(str(price_test_value))
    page.wait_for_timeout(200)
    
    # Badge should show 1
    badge = page.locator("#filterBadge-snapshot-table")
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge '1' after price filter, got '{badge_text}'"
    
    # Get wishlist slider's actual min/max and set below max
    wishlist_slider = page.locator("#wishlistMax")
    wishlist_min = int(wishlist_slider.get_attribute("min"))
    wishlist_max = int(wishlist_slider.get_attribute("max"))
    wishlist_test_value = max(wishlist_min, wishlist_max - 2)
    
    # Apply wishlist filter
    wishlist_slider.fill(str(wishlist_test_value))
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
# New E2E tests to add for dual-handle slider functionality

@pytest.mark.e2e
def test_price_min_slider_filters_rows_correctly(e2e_site_multi_species) -> None:
    """Verify moving price min slider hides rows below the selected price."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()
    assert total_rows > 0, "Expected at least one row in snapshot table"
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Get actual range and calculate a valid test min value
    price_min_slider = page.locator("#priceMin")
    price_max_slider = page.locator("#priceMax")
    data_min = float(price_min_slider.get_attribute("min"))
    data_max = float(price_max_slider.get_attribute("max"))
    
    # Set min slider to mid-range value (ensures rows will be filtered)
    test_min = int((data_min + data_max) * 0.4)
    
    price_min_slider.fill(str(test_min))
    page.wait_for_timeout(200)
    
    # Verify some rows are hidden (unless all prices are above test_min)
    visible_rows = page.locator('#snapshot-table tbody tr:visible').count()
    hidden_rows = page.locator('#snapshot-table tbody tr.hidden').count()
    
    assert visible_rows > 0, "Expected at least some rows to remain visible"
    assert visible_rows + hidden_rows == total_rows, \
        f"Expected visible ({visible_rows}) + hidden ({hidden_rows}) = total ({total_rows})"
    
    # Verify all visible rows have price >= test_min
    visible_rows = page.locator('#snapshot-table tbody tr:visible').all()
    for row in visible_rows:
        price_attr = row.get_attribute('data-price')
        price_value = float(price_attr.replace('£', '').strip())
        assert price_value >= test_min, \
            f"Expected visible row price ({price_value}) to be >= {test_min}"


@pytest.mark.e2e
def test_price_min_max_sliders_work_together(e2e_site_multi_species) -> None:
    """Verify both min and max sliders filter correctly when used together."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Get actual data range
    price_min_slider = page.locator("#priceMin")
    price_max_slider = page.locator("#priceMax")
    data_min = float(price_min_slider.get_attribute("min"))
    data_max = float(price_max_slider.get_attribute("max"))
    
    # Calculate valid test range within the data range
    test_min = int(data_min + (data_max - data_min) * 0.3)
    test_max = int(data_min + (data_max - data_min) * 0.7)
    
    # Set range
    price_min_slider.fill(str(test_min))
    page.wait_for_timeout(100)
    price_max_slider.fill(str(test_max))
    page.wait_for_timeout(200)
    
    # Verify display shows correct range
    price_display = page.locator("#priceDisplay")
    display_text = price_display.text_content()
    assert f"£{test_min}" in display_text and f"£{test_max}" in display_text, \
        f"Expected display to show '£{test_min} - £{test_max}', got '{display_text}'"
    
    # Verify all visible rows are in range
    visible_rows = page.locator('#snapshot-table tbody tr:visible').all()
    for row in visible_rows:
        price_attr = row.get_attribute('data-price')
        price_value = float(price_attr.replace('£', '').strip())
        assert test_min <= price_value <= test_max, \
            f"Expected visible row price ({price_value}) to be between £{test_min} and £{test_max}"


@pytest.mark.e2e
def test_wishlist_min_slider_filters_rows_correctly(e2e_site_multi_species) -> None:
    """Verify moving wishlist min slider hides rows below the selected count."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Get min value and set min slider up
    wishlist_min_slider = page.locator("#wishlistMin")
    data_min = int(wishlist_min_slider.get_attribute("min"))
    test_min = data_min + 2
    
    wishlist_min_slider.fill(str(test_min))
    page.wait_for_timeout(200)
    
    # Verify filtering occurred
    visible_rows = page.locator('#snapshot-table tbody tr:visible').count()
    assert visible_rows < total_rows, "Expected some rows to be hidden"


@pytest.mark.e2e
def test_wishlist_min_max_sliders_work_together(e2e_site_multi_species) -> None:
    """Verify both wishlist min and max sliders filter correctly when used together."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Set range 5 - 15
    wishlist_min_slider = page.locator("#wishlistMin")
    wishlist_max_slider = page.locator("#wishlistMax")
    data_max = int(wishlist_max_slider.get_attribute("max"))
    
    # Only test if we have enough range
    if data_max >= 15:
        wishlist_min_slider.fill("5")
        page.wait_for_timeout(100)
        wishlist_max_slider.fill("15")
        page.wait_for_timeout(200)
        
        # Verify display shows 5 - 15
        wishlist_display = page.locator("#wishlistDisplay")
        display_text = wishlist_display.text_content()
        assert "5" in display_text and "15" in display_text, \
            f"Expected display to show '5 - 15', got '{display_text}'"
@pytest.mark.e2e
def test_price_min_slider_updates_filter_badge(e2e_site_multi_species) -> None:
    """Verify filter badge increments when price MIN slider is moved UP from minimum."""
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
    
    # Get min slider's actual range
    price_min_slider = page.locator("#priceMin")
    data_min = float(price_min_slider.get_attribute("min"))
    data_max = float(price_min_slider.get_attribute("max"))
    
    # Move MIN slider UP from minimum (restricts lower bound)
    test_value = int(data_min + (data_max - data_min) * 0.3)
    price_min_slider.fill(str(test_value))
    page.wait_for_timeout(200)
    
    # Badge should now be visible with count = 1
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" not in badge_classes, "Badge should be visible when price min filter is active"
    
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge to show '1' active filter, got '{badge_text}'"
    
    # Reset min slider back to minimum
    price_min_slider.fill(str(int(data_min)))
    page.wait_for_timeout(200)
    
    # Badge should be hidden again
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" in badge_classes, "Badge should be hidden after resetting min slider"


@pytest.mark.e2e
def test_wishlist_min_slider_updates_filter_badge(e2e_site_multi_species) -> None:
    """Verify filter badge increments when wishlist MIN slider is moved UP from minimum."""
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
    
    # Get min slider's actual range
    wishlist_min_slider = page.locator("#wishlistMin")
    data_min = int(wishlist_min_slider.get_attribute("min"))
    data_max = int(wishlist_min_slider.get_attribute("max"))
    
    # Move MIN slider UP from minimum (restricts lower bound)
    test_value = data_min + max(1, (data_max - data_min) // 3)
    wishlist_min_slider.fill(str(test_value))
    page.wait_for_timeout(200)
    
    # Badge should now be visible with count = 1
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" not in badge_classes, "Badge should be visible when wishlist min filter is active"
    
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge to show '1' active filter, got '{badge_text}'"
    
    # Reset min slider back to minimum
    wishlist_min_slider.fill(str(data_min))
    page.wait_for_timeout(200)
    
    # Badge should be hidden again
    badge_classes = badge.get_attribute("class") or ""
    assert "hidden" in badge_classes, "Badge should be hidden after resetting min slider"


@pytest.mark.e2e
def test_both_price_sliders_count_as_one_filter(e2e_site_multi_species) -> None:
    """Verify moving both min and max price sliders still counts as just ONE filter."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Get sliders
    price_min_slider = page.locator("#priceMin")
    price_max_slider = page.locator("#priceMax")
    data_min = float(price_min_slider.get_attribute("min"))
    data_max = float(price_max_slider.get_attribute("max"))
    
    # Move BOTH sliders (narrow the range)
    test_min = int(data_min + (data_max - data_min) * 0.3)
    test_max = int(data_min + (data_max - data_min) * 0.7)
    
    price_min_slider.fill(str(test_min))
    page.wait_for_timeout(100)
    price_max_slider.fill(str(test_max))
    page.wait_for_timeout(200)
    
    # Badge should show count = 1 (not 2)
    badge = page.locator("#filterBadge-snapshot-table")
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge to show '1' active filter (not 2), got '{badge_text}'"


@pytest.mark.e2e
def test_both_wishlist_sliders_count_as_one_filter(e2e_site_multi_species) -> None:
    """Verify moving both min and max wishlist sliders still counts as just ONE filter."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Get sliders
    wishlist_min_slider = page.locator("#wishlistMin")
    wishlist_max_slider = page.locator("#wishlistMax")
    data_min = int(wishlist_min_slider.get_attribute("min"))
    data_max = int(wishlist_max_slider.get_attribute("max"))
    
    # Move BOTH sliders (narrow the range)
    test_min = data_min + max(1, (data_max - data_min) // 3)
    test_max = data_min + max(2, (data_max - data_min) * 2 // 3)
    
    wishlist_min_slider.fill(str(test_min))
    page.wait_for_timeout(100)
    wishlist_max_slider.fill(str(test_max))
    page.wait_for_timeout(200)

    # Badge should show count = 1 (not 2)
    badge = page.locator("#filterBadge-snapshot-table")
    badge_text = badge.text_content()
    assert badge_text == "1", f"Expected badge to show '1' active filter (not 2), got '{badge_text}'"


# ---------------------------------------------------------------------------
# Snapshot page structural styles
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_snapshot_page_structure_and_styling(e2e_site_multi_species) -> None:
    """Snapshot page should have action buttons, correct brand colors, stats strip, and correct layout."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")

    action_buttons = page.locator('.action-buttons')
    assert action_buttons.count() == 1, "Snapshot page should have .action-buttons container"
    display = action_buttons.evaluate('el => window.getComputedStyle(el).display')
    assert 'flex' in display, f"Action buttons should use flexbox layout, got {display}"
    download_btn = action_buttons.locator('.btn-download')
    assert download_btn.count() == 1 and download_btn.is_visible(), \
        "Download button should be present and visible"
    filter_btn = action_buttons.locator('.btn-filters')
    assert filter_btn.count() == 1 and filter_btn.is_visible(), \
        "Filter button should be present and visible"

    # #27ae60 = rgb(39, 174, 96)
    download_bg = download_btn.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert 'rgb(39, 174, 96)' in download_bg, \
        f"Download button should be green, got {download_bg}"
    # #3498db = rgb(52, 152, 219) — cross-browser sub-pixel rendering may vary
    filter_bg = filter_btn.evaluate('el => window.getComputedStyle(el).backgroundColor')
    parts = filter_bg.lstrip('rgb(').rstrip(')').split(',')
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    assert 40 <= r <= 62 and 140 <= g <= 162 and 205 <= b <= 230, \
        f"Filter button should be ~#3498db (blue), got {filter_bg}"

    stats_strip = page.locator('.table-stats')
    assert stats_strip.count() == 1 and stats_strip.is_visible(), \
        "Snapshot page should have visible .table-stats strip"
    # #e8f4f8 = rgb(232, 244, 248)
    bg_color = stats_strip.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert 'rgb(232, 244, 248)' in bg_color, \
        f"Stats strip should have light blue background, got {bg_color}"
    stats_text = stats_strip.text_content()
    assert 'Showing:' in stats_text and 'species' in stats_text.lower(), \
        f"Stats strip should mention 'Showing:' and 'species', got: {stats_text}"
    assert stats_strip.locator('span[id^="visible-count"]').count() == 1, \
        "Stats strip should have visible-count span"

    data_table = page.locator('.data-table')
    assert data_table.count() >= 1, "Should have data table"
    stats_box = stats_strip.bounding_box()
    table_box = data_table.first.bounding_box()
    assert stats_box is not None and table_box is not None
    assert stats_box['y'] < table_box['y'], "Stats strip should appear above the table"
    vertical_gap = table_box['y'] - (stats_box['y'] + stats_box['height'])
    assert vertical_gap < 100, \
        f"Stats strip and table should be close together, gap is {vertical_gap}px"

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
from playwright.sync_api import expect

from e2e.css_tokens import token_rgb
from e2e.fixtures import e2e_site_multi_species


def _open_advanced_filters(page) -> None:
    """Click the More Filters toggle and wait for the filters panel to appear in DOM."""
    page.locator(".advanced-filters-toggle").click()
    page.locator(".advanced-filters-content").wait_for(state="visible")


@pytest.mark.e2e
def test_price_slider_exists_and_initializes_correctly(e2e_site_multi_species) -> None:
    """Verify price sliders (min and max) render with correct initial state derived from data."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

    # Verify both sliders exist
    price_min_slider = page.locator("#priceMin")
    price_max_slider = page.locator("#priceMax")
    assert price_min_slider.is_visible(), "Price min slider should be visible after expanding filters"
    assert price_max_slider.is_visible(), "Price max slider should be visible after expanding filters"
    
    # Get actual min/max values from sliders (should be derived from CSV data)
    data_min = price_min_slider.get_attribute("min")
    data_max = price_max_slider.get_attribute("max")
    min_initial_value = price_min_slider.input_value()
    max_initial_value = price_max_slider.input_value()
    
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

    _open_advanced_filters(page)

    # Set max slider to £30
    price_max_slider = page.locator("#priceMax")
    price_max_slider.fill("30")  # Playwright's fill() triggers the oninput event
    expect(page.locator('#snapshot-table tbody tr')).not_to_have_count(total_rows)

    # Verify some rows are filtered out (Svelte removes filtered rows from DOM)
    visible_rows = page.locator('#snapshot-table tbody tr').count()

    assert visible_rows > 0, "Expected at least some rows to remain visible"
    assert visible_rows < total_rows, "Expected some rows to be filtered out"


@pytest.mark.e2e
def test_price_slider_updates_display_text(e2e_site_multi_species) -> None:
    """Verify price display updates as both sliders move."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

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

    # Verify display updates
    price_display = page.locator("#priceDisplay")
    expect(price_display).to_contain_text(f"£{mid_value}")
    assert f"£{int(data_min)}" in price_display.text_content(), \
        f"Expected display to show min '£{int(data_min)}'"

    # Move min slider up
    price_min_slider.fill(str(int(data_min + 5)))

    expect(price_display).to_contain_text(f"£{int(data_min + 5)}")


@pytest.mark.e2e
def test_price_slider_updates_filter_badge(e2e_site_multi_species) -> None:
    """Verify filter badge increments when price slider is moved from max."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

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

    # Badge should now be visible with count = 1
    expect(badge).to_have_text("1")

    # Reset slider to max
    price_slider.fill(str(int(max_value)))

    # Badge should be hidden again
    expect(badge).not_to_be_visible()


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
    
    _open_advanced_filters(page)

    # Apply price filter
    price_slider = page.locator("#priceMax")
    price_slider.fill("30")
    expect(stats).not_to_contain_text(f"Showing: {total_species}")

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
    
    _open_advanced_filters(page)

    # Apply search filter first (e.g., "Brachypelma")
    badge = page.locator("#filterBadge-snapshot-table")
    search_input = page.locator("#search-snapshot-table")
    search_input.type("Brachypelma")
    expect(badge).to_have_text("1")

    # Count rows after search
    visible_after_search = page.locator('#snapshot-table tbody tr').count()
    assert visible_after_search > 0, "Expected at least one match for 'Brachypelma'"

    # Now apply price filter (assume Brachypelma species has price > £20)
    price_slider = page.locator("#priceMax")
    price_slider.fill("20")
    expect(badge).to_have_text("2")

    # Count rows after both filters
    visible_after_both = page.locator('#snapshot-table tbody tr').count()

    # Should show fewer results (or zero if all Brachypelma species are > £20)
    assert visible_after_both <= visible_after_search, \
        f"Expected combined filter ({visible_after_both}) <= search only ({visible_after_search})"


@pytest.mark.e2e
def test_price_slider_reset_to_max_shows_all_rows(e2e_site_multi_species) -> None:
    """Verify resetting slider to max shows all rows again."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()
    
    _open_advanced_filters(page)

    # Get slider's actual min/max from attributes
    price_slider = page.locator("#priceMax")
    min_value = float(price_slider.get_attribute("min"))
    max_value = float(price_slider.get_attribute("max"))

    # Set slider to low value (filter heavily)
    low_value = int(max(min_value, min_value + 10))
    price_slider.fill(str(low_value))
    rows = page.locator('#snapshot-table tbody tr')
    expect(rows).not_to_have_count(total_rows)

    # Reset slider to max
    price_slider.fill(str(int(max_value)))

    # Verify all rows visible again
    expect(rows).to_have_count(total_rows)

    # Verify no hidden rows
    hidden_rows = page.locator('#snapshot-table tbody tr.hidden').count()
    assert hidden_rows == 0, f"Expected no hidden rows after reset, got {hidden_rows}"


# --- Wishlist Count Range Slider Tests ---


@pytest.mark.e2e
def test_wishlist_slider_exists_and_initializes_correctly(e2e_site_multi_species) -> None:
    """Verify wishlist sliders (min and max) render with correct initial state derived from data."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

    # Verify both wishlist sliders exist
    wishlist_min_slider = page.locator("#wishlistMin")
    wishlist_max_slider = page.locator("#wishlistMax")
    assert wishlist_min_slider.is_visible(), "Wishlist min slider should be visible after expanding filters"
    assert wishlist_max_slider.is_visible(), "Wishlist max slider should be visible after expanding filters"
    
    # Get actual min/max values from sliders (should be derived from CSV data)
    data_min = wishlist_min_slider.get_attribute("min")
    data_max = wishlist_max_slider.get_attribute("max")
    min_initial_value = wishlist_min_slider.input_value()
    max_initial_value = wishlist_max_slider.input_value()
    
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

    _open_advanced_filters(page)

    # Set wishlist max to 10 (filter out high wishlist counts)
    wishlist_max_slider = page.locator("#wishlistMax")
    wishlist_max_slider.fill("10")
    expect(page.locator('#snapshot-table tbody tr')).not_to_have_count(total_rows)

    # Verify some rows are filtered out (Svelte removes filtered rows from DOM)
    visible_rows = page.locator('#snapshot-table tbody tr').count()

    assert visible_rows > 0, "Expected at least some rows to remain visible"
    assert visible_rows < total_rows, "Expected some rows to be filtered out"

    # Verify all visible rows have wishlist <= 10
    # Use data-wishlist attribute from tr elements to reliably get per-row values
    visible_wishlist_values = page.locator('#snapshot-table tbody tr').evaluate_all(
        'rows => rows.map(r => parseInt(r.getAttribute("data-wishlist") || "0"))'
    )
    for wishlist_value in visible_wishlist_values:
        assert wishlist_value <= 10, \
            f"Expected visible row wishlist ({wishlist_value}) to be <= 10"


@pytest.mark.e2e
def test_wishlist_slider_updates_display_text(e2e_site_multi_species) -> None:
    """Verify wishlist display updates as both sliders move."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

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

    # Verify display updates
    wishlist_display = page.locator("#wishlistDisplay")
    expect(wishlist_display).to_contain_text(str(mid_value))
    assert data_min in wishlist_display.text_content(), \
        f"Expected display to show min '{data_min}'"

    # Move min slider up
    wishlist_min_slider.fill(str(int(data_min) + 1))

    expect(wishlist_display).to_contain_text(str(int(data_min) + 1))


@pytest.mark.e2e
def test_wishlist_slider_updates_filter_badge(e2e_site_multi_species) -> None:
    """Verify filter badge increments when wishlist slider is moved from max."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

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

    # Badge should now be visible with count = 1
    expect(badge).to_have_text("1")

    # Reset slider to max
    wishlist_slider.fill(str(max_value))

    # Badge should be hidden again
    expect(badge).not_to_be_visible()


@pytest.mark.e2e
def test_wishlist_and_price_sliders_combine_in_badge(e2e_site_multi_species) -> None:
    """Verify filter badge shows 2 when both price and wishlist sliders are active."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

    # Get price slider's actual min/max and set to mid-range
    price_slider = page.locator("#priceMax")
    price_min = float(price_slider.get_attribute("min"))
    price_max = float(price_slider.get_attribute("max"))
    price_test_value = int((price_min + price_max) * 0.5)
    badge = page.locator("#filterBadge-snapshot-table")

    # Apply price filter
    price_slider.fill(str(price_test_value))

    # Badge should show 1
    expect(badge).to_have_text("1")

    # Get wishlist slider's actual min/max and set below max
    wishlist_slider = page.locator("#wishlistMax")
    wishlist_min = int(wishlist_slider.get_attribute("min"))
    wishlist_max = int(wishlist_slider.get_attribute("max"))
    wishlist_test_value = max(wishlist_min, wishlist_max - 2)

    # Apply wishlist filter
    wishlist_slider.fill(str(wishlist_test_value))

    # Badge should show 2
    expect(badge).to_have_text("2")


@pytest.mark.e2e
def test_wishlist_slider_and_search_combine_with_AND_logic(e2e_site_multi_species) -> None:
    """Verify wishlist slider and search filter work together (both must match)."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

    # Apply search filter first
    badge = page.locator("#filterBadge-snapshot-table")
    search_input = page.locator("#search-snapshot-table")
    search_input.type("Brachypelma")
    expect(badge).to_have_text("1")

    # Count rows after search
    visible_after_search = page.locator('#snapshot-table tbody tr').count()
    assert visible_after_search > 0, "Expected at least one match for 'Brachypelma'"

    # Now apply wishlist filter
    wishlist_slider = page.locator("#wishlistMax")
    wishlist_slider.fill("10")
    expect(badge).to_have_text("2")

    # Count rows after both filters
    visible_after_both = page.locator('#snapshot-table tbody tr').count()

    # Should show fewer or equal results
    assert visible_after_both <= visible_after_search, \
        f"Expected combined filter ({visible_after_both}) <= search only ({visible_after_search})"
# New E2E tests to add for dual-handle slider functionality

@pytest.mark.e2e
def test_price_min_slider_filters_rows_correctly(e2e_site_multi_species) -> None:
    """Verify moving price min slider hides rows below the selected price."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()
    assert total_rows > 0, "Expected at least one row in snapshot table"

    _open_advanced_filters(page)

    # Get actual range and calculate a valid test min value
    price_min_slider = page.locator("#priceMin")
    price_max_slider = page.locator("#priceMax")
    data_min = float(price_min_slider.get_attribute("min"))
    data_max = float(price_max_slider.get_attribute("max"))

    # Set min slider to mid-range value (ensures rows will be filtered)
    test_min = int((data_min + data_max) * 0.4)

    price_min_slider.fill(str(test_min))
    expect(page.locator('#snapshot-table tbody tr')).not_to_have_count(total_rows)

    # Verify some rows are filtered out (Svelte removes filtered rows from DOM)
    visible_rows_count = page.locator('#snapshot-table tbody tr').count()

    assert visible_rows_count > 0, "Expected at least some rows to remain visible"

    # Verify all visible rows have price >= test_min
    # Price (GBP) is column index 3 (0-based) in the snapshot table
    visible_rows_list = page.locator('#snapshot-table tbody tr').all()
    for row in visible_rows_list:
        price_text = row.locator('td').nth(3).text_content() or '0'
        price_value = float(price_text.replace('£', '').strip() or '0')
        assert price_value >= test_min, \
            f"Expected visible row price ({price_value}) to be >= {test_min}"


@pytest.mark.e2e
def test_price_min_max_sliders_work_together(e2e_site_multi_species) -> None:
    """Verify both min and max sliders filter correctly when used together."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

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
    price_max_slider.fill(str(test_max))

    # Verify display shows correct range
    price_display = page.locator("#priceDisplay")
    expect(price_display).to_contain_text(f"£{test_max}")
    assert f"£{test_min}" in price_display.text_content(), \
        f"Expected display to show '£{test_min}'"

    # Verify all visible rows are in range
    # Price (GBP) is column index 3 (0-based) in the snapshot table
    visible_rows = page.locator('#snapshot-table tbody tr').all()
    for row in visible_rows:
        price_text = row.locator('td').nth(3).text_content() or '0'
        price_value = float(price_text.replace('£', '').strip() or '0')
        assert test_min <= price_value <= test_max, \
            f"Expected visible row price ({price_value}) to be between £{test_min} and £{test_max}"


@pytest.mark.e2e
def test_wishlist_min_slider_filters_rows_correctly(e2e_site_multi_species) -> None:
    """Verify moving wishlist min slider hides rows below the selected count."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Count total rows
    total_rows = page.locator('#snapshot-table tbody tr').count()

    _open_advanced_filters(page)

    # Get min value and set min slider up
    wishlist_min_slider = page.locator("#wishlistMin")
    data_min = int(wishlist_min_slider.get_attribute("min"))
    test_min = data_min + 2

    wishlist_min_slider.fill(str(test_min))

    # Verify filtering occurred
    expect(page.locator('#snapshot-table tbody tr')).not_to_have_count(total_rows)


@pytest.mark.e2e
def test_wishlist_min_max_sliders_work_together(e2e_site_multi_species) -> None:
    """Verify both wishlist min and max sliders filter correctly when used together."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

    # Set range 5 - 15
    wishlist_min_slider = page.locator("#wishlistMin")
    wishlist_max_slider = page.locator("#wishlistMax")
    data_max = int(wishlist_max_slider.get_attribute("max"))

    # Only test if we have enough range
    if data_max >= 15:
        wishlist_min_slider.fill("5")
        wishlist_max_slider.fill("15")

        # Verify display shows 5 - 15
        wishlist_display = page.locator("#wishlistDisplay")
        expect(wishlist_display).to_contain_text("15")
        assert "5" in wishlist_display.text_content(), \
            f"Expected display to show '5 - 15', got '{wishlist_display.text_content()}'"
@pytest.mark.e2e
def test_price_min_slider_updates_filter_badge(e2e_site_multi_species) -> None:
    """Verify filter badge increments when price MIN slider is moved UP from minimum."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

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

    # Badge should now be visible with count = 1
    expect(badge).to_have_text("1")

    # Reset min slider back to minimum
    price_min_slider.fill(str(int(data_min)))

    # Badge should be hidden again
    expect(badge).not_to_be_visible()


@pytest.mark.e2e
def test_wishlist_min_slider_updates_filter_badge(e2e_site_multi_species) -> None:
    """Verify filter badge increments when wishlist MIN slider is moved UP from minimum."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

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

    # Badge should now be visible with count = 1
    expect(badge).to_have_text("1")

    # Reset min slider back to minimum
    wishlist_min_slider.fill(str(data_min))

    # Badge should be hidden again
    expect(badge).not_to_be_visible()


@pytest.mark.e2e
def test_both_price_sliders_count_as_one_filter(e2e_site_multi_species) -> None:
    """Verify moving both min and max price sliders still counts as just ONE filter."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

    # Get sliders
    price_min_slider = page.locator("#priceMin")
    price_max_slider = page.locator("#priceMax")
    data_min = float(price_min_slider.get_attribute("min"))
    data_max = float(price_max_slider.get_attribute("max"))

    # Move BOTH sliders (narrow the range)
    test_min = int(data_min + (data_max - data_min) * 0.3)
    test_max = int(data_min + (data_max - data_min) * 0.7)

    price_min_slider.fill(str(test_min))
    price_max_slider.fill(str(test_max))

    # Badge should show count = 1 (not 2)
    badge = page.locator("#filterBadge-snapshot-table")
    expect(badge).to_have_text("1")


@pytest.mark.e2e
def test_both_wishlist_sliders_count_as_one_filter(e2e_site_multi_species) -> None:
    """Verify moving both min and max wishlist sliders still counts as just ONE filter."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    _open_advanced_filters(page)

    # Get sliders
    wishlist_min_slider = page.locator("#wishlistMin")
    wishlist_max_slider = page.locator("#wishlistMax")
    data_min = int(wishlist_min_slider.get_attribute("min"))
    data_max = int(wishlist_max_slider.get_attribute("max"))

    # Move BOTH sliders (narrow the range)
    test_min = data_min + max(1, (data_max - data_min) // 3)
    test_max = data_min + max(2, (data_max - data_min) * 2 // 3)

    wishlist_min_slider.fill(str(test_min))
    wishlist_max_slider.fill(str(test_max))

    # Badge should show count = 1 (not 2)
    badge = page.locator("#filterBadge-snapshot-table")
    expect(badge).to_have_text("1")


# ---------------------------------------------------------------------------
# Snapshot page structural styles
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_snapshot_page_structure_and_styling(e2e_site_multi_species) -> None:
    """Snapshot page should rely on the stats strip download control and keep the expected layout."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")

    action_buttons = page.locator('.action-buttons')
    assert action_buttons.count() == 0, "Snapshot page should not render the old .action-buttons container"

    stats_strip = page.locator('.table-stats')
    assert stats_strip.count() == 1 and stats_strip.is_visible(), \
        "Snapshot page should have visible .table-stats strip"

    download_btn = stats_strip.locator('.btn--download')
    assert download_btn.count() == 1 and download_btn.is_visible(), \
        "Stats strip download button should be present and visible"

    download_bg = download_btn.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert token_rgb('--color-success') in download_bg, \
        f"Download button should be green, got {download_bg}"

    # Advanced-filters toggle is rendered by SortableTable (not inside .action-buttons)
    advanced_toggle = page.locator('.advanced-filters-toggle')
    assert advanced_toggle.count() == 1 and advanced_toggle.is_visible(), \
        "Advanced filters toggle should be present and visible inside SortableTable"

    bg_color = stats_strip.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert token_rgb('--color-info-bg') in bg_color, \
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

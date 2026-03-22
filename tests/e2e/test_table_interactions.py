#!/usr/bin/env python3
"""E2E tests for table interactions (sorting, filtering, search).

Scope:
- Table sorting by clicking column headers (numeric and string columns)
- Signal/risk filtering (🔥/⚠️/❌ buttons)
- Stock pattern filtering (Sustained/Emerging/Cyclical/Always) on breeder page
- Text search filtering
- Combined filter interactions (signal + stock pattern, signal + search, etc.)
- Advanced filters toggle expand/collapse
- "Show All" button to clear filters

What's NOT tested here:
- Basic page loads and navigation (see test_navigation_and_page_loads.py)
- Species detail page interactions (see test_species_page_interactions.py)
"""

from __future__ import annotations

import re
import pytest
from playwright.sync_api import expect

from e2e.css_tokens import token_rgb
from e2e.fixtures import e2e_site_multi_species


@pytest.mark.e2e
@pytest.mark.parametrize(
    "column_index,parse_cell",
    [
        (3, lambda cell: int(cell.strip())),
        (5, lambda cell: float(cell.strip().split()[0].replace("£", ""))),
    ],
)
def test_table_sorting_numeric_columns(e2e_site_multi_species, column_index, parse_cell) -> None:
    """Verify clicking numeric headers (including Price) sorts ascending/descending."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    column_header = page.locator('#breeder-table thead th').nth(column_index)

    # First click: sort ascending
    column_header.click()
    expect(column_header).to_have_attribute('data-sort-direction', 'asc')

    column_cells = page.locator('#breeder-table tbody tr td').nth(column_index).all_text_contents()
    column_values = [parse_cell(cell) for cell in column_cells if cell.strip()]

    # Verify ascending order
    assert column_values == sorted(column_values), f"Expected ascending order, got {column_values}"

    # Second click: sort descending
    column_header.click()
    expect(column_header).to_have_attribute('data-sort-direction', 'desc')

    column_cells = page.locator('#breeder-table tbody tr td').nth(column_index).all_text_contents()
    column_values = [parse_cell(cell) for cell in column_cells if cell.strip()]

    # Verify descending order
    assert column_values == sorted(column_values, reverse=True), f"Expected descending order, got {column_values}"


@pytest.mark.e2e
def test_table_sorting_string_columns(e2e_site_multi_species) -> None:
    """Verify clicking string column headers sorts alphabetically."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Click "Species" column header (index 0)
    species_header = page.locator('#breeder-table thead th').nth(0)
    species_header.click()
    expect(species_header).to_have_attribute('data-sort-direction', 'asc')

    # Get species names from sorted rows
    species_cells = page.locator('#breeder-table tbody tr td').nth(0).all_text_contents()
    species_names = [cell.strip() for cell in species_cells]
    
    # Verify alphabetical order (ascending by default)
    assert species_names == sorted(species_names), f"Expected alphabetical order, got {species_names}"
    
    # Second click: descending
    species_header.click()
    expect(species_header).to_have_attribute('data-sort-direction', 'desc')

    species_cells = page.locator('#breeder-table tbody tr td').nth(0).all_text_contents()
    species_names = [cell.strip() for cell in species_cells]
    
    # Verify reverse alphabetical order
    assert species_names == sorted(species_names, reverse=True), f"Expected reverse order, got {species_names}"


@pytest.mark.e2e
def test_breeder_price_column_exists_with_currency_and_arrow_values(e2e_site_multi_species) -> None:
    """Breeder table should expose the Price column with currency+arrow values."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    headers = [h.strip() for h in page.locator("#breeder-table thead th").all_text_contents()]
    price_idx = next((index for index, header in enumerate(headers) if header.startswith("Price")), None)
    assert price_idx is not None, f"Expected Price header, got: {headers}"
    price_cells = page.locator(f"#breeder-table tbody tr td:nth-child({price_idx + 1})").all_text_contents()
    price_values = [cell.strip() for cell in price_cells if cell.strip()]

    assert price_values, "Expected non-empty Price values in breeder table"
    assert all(value.startswith("£") and value.endswith(("↑", "→", "↓")) for value in price_values), (
        f"Expected currency+arrow values, got: {price_values}"
    )


@pytest.mark.e2e
def test_dealer_price_column_exists_with_currency_and_arrow_values(e2e_site_multi_species) -> None:
    """Dealer table should expose the Price column with currency+arrow values."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")

    headers = [h.strip() for h in page.locator("#dealer-table thead th").all_text_contents()]
    price_idx = next((index for index, header in enumerate(headers) if header.startswith("Price")), None)
    assert price_idx is not None, f"Expected Price header, got: {headers}"
    price_cells = page.locator(f"#dealer-table tbody tr td:nth-child({price_idx + 1})").all_text_contents()
    price_values = [cell.strip() for cell in price_cells if cell.strip()]

    assert price_values, "Expected non-empty Price values in dealer table"
    assert all(value.startswith("£") and value.endswith(("↑", "→", "↓")) for value in price_values), (
        f"Expected currency+arrow values, got: {price_values}"
    )


@pytest.mark.e2e
def test_signal_filtering_on_breeder_table(e2e_site_multi_species) -> None:
    """Verify signal filter buttons (🔥/⚠️/❌) work correctly on breeder page."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # All rows visible initially
    all_rows = page.locator('#breeder-table tbody tr').count()
    assert all_rows == 6, "Expected 6 breeder species in test data"
    
    # Click "🔥 Hot" filter button (use specific selector to avoid matching Hot (top 10))
    hot_button = page.locator('button[data-action="filter-signal"][data-signal="🔥"]:not([data-limit])')
    hot_button.click()
    expect(page.locator('#breeder-table tbody tr')).to_have_count(2)
    
    # Verify button has active class
    assert "is-active" in hot_button.get_attribute("class"), "Expected is-active class on clicked button"
    
    # Click "Show All" to reset (use specific selector for signal filter)
    show_all = page.locator('button[data-action="filter-signal"][data-signal="all"]')
    show_all.click()
    expect(page.locator('#breeder-table tbody tr')).to_have_count(6)


@pytest.mark.e2e
def test_stock_pattern_filtering_on_breeder_table(e2e_site_multi_species) -> None:
    """Verify stock pattern filter buttons work correctly on breeder page."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Expand advanced filters if the panel is not yet in the DOM
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        # The panel is rendered with {#if showAdvanced} — if not yet in DOM, expand it.
        advanced_content = page.locator(".advanced-filters-content")
        if advanced_content.count() == 0:
            advanced_toggle.click()
            advanced_content.wait_for(state="visible")
    
    # Click "Emerging" pattern filter
    emerging_button = page.locator('button[data-action="filter-stock-pattern"][data-stock-pattern="Emerging"]')
    emerging_button.click()
    expect(page.locator('#breeder-table tbody tr')).to_have_count(2)

    # Verify button has active class
    assert "is-active" in emerging_button.get_attribute("class"), "Expected is-active class"


@pytest.mark.e2e
def test_signal_filter_rebases_remaining_breeder_filters(e2e_site_multi_species) -> None:
    """Selecting a breeder signal should update stock counts and slider ranges."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    hot_button = page.locator('button[data-action="filter-signal"][data-signal="🔥"]:not([data-limit])')
    hot_button.click()
    expect(page.locator('#breeder-table tbody tr')).to_have_count(2)

    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_content = page.locator(".advanced-filters-content")
        if advanced_content.count() == 0:
            advanced_toggle.click()
            advanced_content.wait_for(state="visible")

    expect(page.locator('button[data-action="filter-stock-pattern"][data-stock-pattern="all"]')).to_have_text(
        'Show All (2)'
    )
    expect(page.locator('button[data-action="filter-stock-pattern"][data-stock-pattern="Sustained"]')).to_have_text(
        'Sustained (1)'
    )
    expect(page.locator('button[data-action="filter-stock-pattern"][data-stock-pattern="Cyclical"]')).to_have_text(
        'Cyclical (1)'
    )
    expect(page.locator('button[data-action="filter-stock-pattern"][data-stock-pattern="Emerging"]')).to_have_text(
        'Emerging (0)'
    )

    price_min = page.locator('#priceMin')
    price_max = page.locator('#priceMax')
    wishlist_min = page.locator('#wishlistMin')
    wishlist_max = page.locator('#wishlistMax')

    expect(page.locator('#priceDisplay')).to_have_text('£20 – £25')
    expect(page.locator('#wishlistDisplay')).to_have_text('3 – 5')

    assert price_min.evaluate("el => ({ min: el.min, max: el.max, value: el.value })") == {
        'min': '20',
        'max': '25',
        'value': '20',
    }
    assert price_max.evaluate("el => ({ min: el.min, max: el.max, value: el.value })") == {
        'min': '20',
        'max': '25',
        'value': '25',
    }
    assert wishlist_min.evaluate("el => ({ min: el.min, max: el.max, value: el.value })") == {
        'min': '3',
        'max': '5',
        'value': '3',
    }
    assert wishlist_max.evaluate("el => ({ min: el.min, max: el.max, value: el.value })") == {
        'min': '3',
        'max': '5',
        'value': '5',
    }


@pytest.mark.e2e
def test_newly_observed_filtering_on_breeder_table(e2e_site_multi_species) -> None:
    """Verify the Newly Observed stock pattern is exposed and filters breeder rows."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_content = page.locator(".advanced-filters-content")
        if advanced_content.count() == 0:
            advanced_toggle.click()
            advanced_content.wait_for(state="visible")

    newly_observed_button = page.locator(
        'button[data-action="filter-stock-pattern"][data-stock-pattern="Newly Observed"]'
    )
    newly_observed_button.click()

    visible_rows = page.locator('#breeder-table tbody tr')
    expect(visible_rows).to_have_count(1)
    expect(visible_rows.first).to_contain_text('Psalmopoeus irminia')


@pytest.mark.e2e
def test_search_filter_on_breeder_and_dealer_tables(e2e_site_multi_species) -> None:
    """Test that the text search filter works on both breeder and dealer tables."""
    page, base_url, errors = e2e_site_multi_species

    # TEST: Breeder page search filter
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Expand advanced filters (panel uses {#if showAdvanced} — wait for element in DOM)
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_toggle.click()
        page.locator(".advanced-filters-content").wait_for(timeout=2000)
    
    # All rows should be visible initially
    assert page.locator("#breeder-table tbody tr").count() == 6, "Expected 6 visible breeder rows initially"
    
    # Type "Brachypelma" in search box
    search_input = page.locator("#search-breeder-table")
    assert search_input.count() == 1, "Search input should exist"
    search_input.type("Brachypelma")
    visible_rows = page.locator("#breeder-table tbody tr")
    expect(visible_rows).to_have_count(1)

    # Verify the correct species is visible
    visible_text = visible_rows.first.text_content()
    assert "Brachypelma hamorii" in visible_text, "Wrong species visible after filter"
    
    # Clear search - all rows should be visible again
    search_input.fill("")
    search_input.dispatch_event("keyup")
    expect(page.locator("#breeder-table tbody tr")).to_have_count(6)
    
    # TEST: Dealer page search filter
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    
    # Expand advanced filters (panel uses {#if showAdvanced} — wait for element in DOM)
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_toggle.click()
        page.locator(".advanced-filters-content").wait_for(timeout=2000)
    
    # All rows visible initially
    assert page.locator("#dealer-table tbody tr").count() == 5, "Expected 5 visible rows initially on dealer page"
    
    # Search for "hamorii"
    search_input = page.locator("#search-dealer-table")
    assert search_input.count() == 1, "Search input should exist on dealer page"
    search_input.type("hamorii")
    visible_rows = page.locator("#dealer-table tbody tr")
    expect(visible_rows).to_have_count(1)

    visible_text = visible_rows.first.text_content()
    assert "hamorii" in visible_text, "Wrong species visible after filter on dealer page"
    
    # Test case-insensitive search
    search_input.fill("")
    search_input.dispatch_event("keyup")
    search_input.type("PULCHRA")  # UPPERCASE
    expect(page.locator("#dealer-table tbody tr")).to_have_count(1)
    
    visible_text = visible_rows.first.text_content()
    assert "pulchra" in visible_text.lower(), "Case-insensitive search failed"


@pytest.mark.e2e
def test_combined_signal_and_stock_pattern_filters(e2e_site_multi_species) -> None:
    """Verify applying multiple filter types (signal then stock pattern) uses AND logic.
    
    NOTE: SortableTable applies AND logic: both signal and stock pattern filters are
    combined. This test verifies: ⚠️ signal (3 rows) AND Emerging pattern (2 rows)
    = 2 rows (Brachypelma ⚠️ Emerging + Pterinochilus ⚠️ Emerging).
    """
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_toggle.click()
        page.locator(".advanced-filters-content").wait_for(state="visible")

    # Apply signal filter: ⚠️ Watch (use specific selector to avoid matching top10)
    watch_button = page.locator('button[data-action="filter-signal"][data-signal="⚠️"]:not([data-limit])')
    watch_button.click()
    expect(page.locator('#breeder-table tbody tr')).to_have_count(3)

    # Now apply stock pattern filter: Emerging (both ⚠️ species are Emerging)
    # SortableTable applies AND logic: shows rows matching BOTH filters
    emerging_button = page.locator("button[data-action='filter-stock-pattern'][data-stock-pattern='Emerging']")
    emerging_button.click()
    expect(page.locator('#breeder-table tbody tr')).to_have_count(2)

    # Click signal filter's "Show All" to clear the signal filter
    show_all = page.locator('button[data-action="filter-signal"][data-signal="all"]:not([data-limit])')
    show_all.click()
    # Also clear the stock pattern filter (filters are independent — each must be reset separately)
    show_all_stock = page.locator("button[data-action='filter-stock-pattern'][data-stock-pattern='all']")
    show_all_stock.click()
    expect(page.locator('#breeder-table tbody tr')).to_have_count(6)


@pytest.mark.e2e
def test_combined_signal_and_newly_observed_filters(e2e_site_multi_species) -> None:
    """Verify ⚠️ signal and Newly Observed stock pattern combine with AND logic."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_toggle.click()
        page.locator(".advanced-filters-content").wait_for(state="visible")

    watch_button = page.locator('button[data-action="filter-signal"][data-signal="⚠️"]:not([data-limit])')
    watch_button.click()
    expect(page.locator('#breeder-table tbody tr')).to_have_count(3)

    newly_observed_button = page.locator(
        'button[data-action="filter-stock-pattern"][data-stock-pattern="Newly Observed"]'
    )
    newly_observed_button.click()

    visible_rows = page.locator('#breeder-table tbody tr')
    expect(visible_rows).to_have_count(1)
    expect(visible_rows.first).to_contain_text('Psalmopoeus irminia')


@pytest.mark.e2e
def test_search_filter_combined_with_signal_filter(e2e_site_multi_species) -> None:
    """Verify search text filter works together with signal filter."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_toggle.click()
        page.locator(".advanced-filters-content").wait_for(state="visible")

    # Apply ⚠️ Watch signal filter first (3 species)
    watch_button = page.locator('button:has-text("⚠️")')
    watch_button.click()
    expect(page.locator('#breeder-table tbody tr')).to_have_count(3)

    # Now type search: "Brachypelma" (only matches one of the ⚠️ species)
    search_input = page.locator("#search-breeder-table")
    search_input.type("Brachypelma")
    expect(page.locator('#breeder-table tbody tr')).to_have_count(1)

    visible_text = page.locator('#breeder-table tbody tr').first.text_content()
    assert "Brachypelma" in visible_text, "Expected Brachypelma in filtered results"


@pytest.mark.e2e
def test_advanced_filters_toggle_expand_collapse(e2e_site_multi_species) -> None:
    """Verify clicking 'Advanced Filters' toggle expands/collapses the advanced filters panel.
    
    Navigates to snapshot page (which has price/wishlist sliders requiring the toggle).
    SortableTable uses conditional rendering ({#if showAdvanced}) — expanded state is
    indicated by DOM presence of .advanced-filters-content, not a CSS .show class.
    """
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    toggle_button = page.locator(".advanced-filters-toggle")
    assert toggle_button.count() > 0, "snapshot.html should have an advanced-filters-toggle button"
    content_div = page.locator(".advanced-filters-content")
    
    # Click to toggle (initially collapsed - content not in DOM)
    toggle_button.click()
    content_div.wait_for(state="visible")

    # Click again to toggle back
    toggle_button.click()
    content_div.wait_for(state="detached")

@pytest.mark.e2e
def test_snapshot_page_advanced_filters_toggle(e2e_site_multi_species) -> None:
    """Verify 'Advanced Filters' toggle works on snapshot page."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Verify toggle button exists (snapshot page has price/wishlist sliders)
    toggle_button = page.locator(".advanced-filters-toggle")
    assert toggle_button.is_visible(), "Toggle button should be visible on snapshot page"
    
    # Verify filter content container is initially not in DOM (collapsed by default)
    content_div = page.locator(".advanced-filters-content")
    assert content_div.count() == 0, "Advanced filters content should not be in DOM when collapsed"
    
    # Click to expand
    toggle_button.click()
    content_div.wait_for(state="visible")

    # Verify button has 'is-expanded' class when open
    toggle_classes = toggle_button.get_attribute("class").split()
    assert "is-expanded" in toggle_classes, "Toggle button should have 'is-expanded' class when expanded"
    
    # Verify search input is now accessible
    search_input = page.locator("input[type='text']")
    assert search_input.is_visible(), "Search input should be visible when filters expanded"
    
    # Click again to collapse
    toggle_button.click()
    content_div.wait_for(state="detached")

    toggle_classes = toggle_button.get_attribute("class").split()
    assert "is-expanded" not in toggle_classes, "Toggle button should not have 'is-expanded' class when collapsed"


@pytest.mark.e2e
def test_snapshot_filter_badge_updates_with_search(e2e_site_multi_species) -> None:
    """Snapshot page should show filter count badge when search is active."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Badge should be hidden by default
    badge = page.locator(".toggle-btn__badge")
    assert badge.count() == 1, "Badge element should exist on snapshot page"
    assert not badge.is_visible(), "Badge should be hidden when no filters active"
    
    # Expand filters (snapshot page uses .advanced-filters-toggle)
    toggle_button = page.locator(".advanced-filters-toggle")
    toggle_button.click()
    page.locator(".advanced-filters-content").wait_for(state="visible")

    # Type in search box
    search_input = page.locator("#search-snapshot-table")
    search_input.type("hamorii")
    expect(badge).to_have_text("1")

    # Clear search
    search_input.fill("")
    search_input.dispatch_event("keyup")
    expect(badge).not_to_be_visible()


@pytest.mark.e2e
def test_snapshot_stats_strip_updates_count_when_filtered(e2e_site_multi_species) -> None:
    """Snapshot page stats strip should update visible count when filters are applied."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Get initial count from stats strip
    stats_strip = page.locator(".table-stats")
    assert stats_strip.count() == 1, "Should have stats strip"
    
    visible_count_span = page.locator("#visible-count-snapshot-table")
    assert visible_count_span.count() == 1, "Should have visible count span"
    
    initial_text = stats_strip.text_content()
    assert "Showing:" in initial_text, "Should show 'Showing:' text"
    
    # Get total count (should match initial visible count)
    # Pattern: "Showing: X of Y species"
    match = re.search(r'Showing:\s*(\d+)\s*of\s*(\d+)\s*species', initial_text)
    assert match, f"Should match pattern, got: {initial_text}"
    initial_visible = int(match.group(1))
    total_count = int(match.group(2))
    assert initial_visible == total_count, "Initially all rows should be visible"
    assert total_count > 1, "Should have multiple species for meaningful test"
    
    # Expand advanced filters
    toggle_button = page.locator(".advanced-filters-toggle")
    toggle_button.click()
    page.locator(".advanced-filters-content").wait_for(state="visible")

    # Apply search filter that will reduce visible rows
    search_input = page.locator("#search-snapshot-table")
    search_input.type("hamorii")  # Should match only specific species
    expect(stats_strip).not_to_contain_text(f"Showing: {total_count} of {total_count}")
    
    # Check that visible count has decreased
    filtered_text = stats_strip.text_content()
    filtered_match = re.search(r'Showing:\s*(\d+)\s*of\s*(\d+)\s*species', filtered_text)
    assert filtered_match, f"Should still match pattern after filtering, got: {filtered_text}"
    filtered_visible = int(filtered_match.group(1))
    filtered_total = int(filtered_match.group(2))
    
    assert filtered_visible < total_count, f"Visible count should decrease after filtering, got {filtered_visible} vs {total_count}"
    assert filtered_total == total_count, "Total count should remain unchanged"
    assert filtered_visible >= 1, "Should have at least one matching species"
    
    # Clear the filter
    search_input.fill("")
    search_input.dispatch_event("keyup")
    expect(stats_strip).to_contain_text(f"Showing: {total_count} of")

    # Verify count returns to original
    final_text = stats_strip.text_content()
    final_match = re.search(r'Showing:\s*(\d+)\s*of\s*(\d+)\s*species', final_text)
    assert final_match, f"Should match pattern after clearing, got: {final_text}"
    final_visible = int(final_match.group(1))


# ---------------------------------------------------------------------------
# Analysis page structure and styling (breeder / dealer)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_analysis_pages_have_analysis_ui(e2e_site_multi_species) -> None:
    """Breeder/dealer pages should have summary stat cards, signal filter buttons, and instruction box."""
    page, base_url, errors = e2e_site_multi_species

    for page_name in ['breeder.html', 'dealer.html']:
        page.goto(f"{base_url}/{page_name}", wait_until="domcontentloaded")

        summary_stats = page.locator('.summary-stats')
        assert summary_stats.count() == 1, f"{page_name} should have .summary-stats container"
        assert page.locator('.stat-card').count() >= 3, f"{page_name} should have at least 3 stat cards"
        assert page.locator('.stat-card.stat-card--hot').count() >= 1, f"{page_name} should have .stat-card--hot card"
        assert page.locator('.stat-card.stat-card--watch').count() >= 1, f"{page_name} should have .stat-card--watch card"
        assert page.locator('.stat-card.stat-card--avoid').count() >= 1, f"{page_name} should have .stat-card--avoid card"

        assert page.locator('.filter-controls').count() >= 1, \
            f"{page_name} should have filter button containers"
        assert page.locator('.filter-btn[data-action="filter-signal"]').count() >= 3, \
            f"{page_name} should have at least 3 signal filter buttons"

        instruction_box = page.locator('.instruction-box')
        assert instruction_box.count() == 1, f"{page_name} should have .instruction-box"
        tag_name = instruction_box.evaluate('el => el.tagName.toLowerCase()')
        assert tag_name == 'details', \
            f"{page_name} instruction box should be <details>, got <{tag_name}>"
        assert instruction_box.locator('summary').count() == 1, \
            f"{page_name} instruction box should have <summary>"


@pytest.mark.e2e
def test_non_analysis_pages_lack_analysis_ui(e2e_site_multi_species) -> None:
    """Snapshot/history pages should NOT have summary stats, signal filter buttons, or instruction box."""
    page, base_url, errors = e2e_site_multi_species

    for page_name in ['snapshot.html', 'history.html']:
        page.goto(f"{base_url}/{page_name}", wait_until="domcontentloaded")

        assert page.locator('.summary-stats').count() == 0, \
            f"{page_name} should NOT have .summary-stats"
        assert page.locator('.stat-card').count() == 0, \
            f"{page_name} should NOT have stat cards"
        assert page.locator('.filter-btn[data-action="filter-signal"]').count() == 0, \
            f"{page_name} should NOT have signal filter buttons"
        assert page.locator('.instruction-box').count() == 0, \
            f"{page_name} should NOT have .instruction-box"


@pytest.mark.e2e
def test_instruction_box_legend_link_opens_legend_section(e2e_site_multi_species) -> None:
    """Clicking the 'See full column legend' link should open the legend <details> section."""
    page, base_url, errors = e2e_site_multi_species

    for page_name in ['breeder.html', 'dealer.html']:
        page.goto(f"{base_url}/{page_name}", wait_until="domcontentloaded")

        legend_section = page.locator('#legend-section')
        if legend_section.count() == 0:
            pytest.skip(f"No legend section rendered on {page_name} with current test data")

        # Legend should start closed
        is_open_before = legend_section.evaluate('el => el.open')
        assert not is_open_before, f"{page_name}: #legend-section should be closed on page load"

        # The legend link lives inside instruction-box which is a collapsed <details>.
        # Open the instruction box first so the link becomes visible.
        instruction_box = page.locator('.instruction-box')
        instruction_box.locator('summary').click()

        # Click the anchor inside instruction-box
        legend_link = page.locator('.instruction-box a[data-action="open-details"]')
        assert legend_link.count() == 1, \
            f"{page_name}: instruction box should contain exactly one legend anchor"

        legend_link.click()

        # Legend should now be open (JS handler sets open=true)
        is_open_after = legend_section.evaluate('el => el.open')
        assert is_open_after, \
            f"{page_name}: #legend-section should be open after clicking the legend link"


@pytest.mark.e2e
def test_filter_buttons_layout(e2e_site_multi_species) -> None:
    """Filter button containers should use flexbox; individual buttons use inline-flex."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    container_display = page.locator('.filter-controls').first.evaluate(
        'el => window.getComputedStyle(el).display'
    )
    assert container_display == 'flex', \
        f".filter-controls should use flex, got {container_display}"

    button_display = page.locator('.filter-btn').first.evaluate(
        'el => window.getComputedStyle(el).display'
    )
    assert 'flex' in button_display or 'inline' in button_display, \
        f"Filter button should have flex or inline display, got {button_display}"


@pytest.mark.e2e
def test_stat_cards_have_correct_border_colors(e2e_site_multi_species) -> None:
    """Stat cards should have color-coded left borders (red=hot, orange=watch, gray=avoid)."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    hot_card = page.locator('.stat-card.stat-card--hot').first
    if hot_card.count() > 0:
        border_color = hot_card.evaluate('el => window.getComputedStyle(el).borderLeftColor')
        # --color-danger: #e74c3c
        assert token_rgb('--color-danger') in border_color, \
            f"Hot card should have red border, got {border_color}"

    watch_card = page.locator('.stat-card.stat-card--watch').first
    if watch_card.count() > 0:
        border_color = watch_card.evaluate('el => window.getComputedStyle(el).borderLeftColor')
        # --color-signal-watch: #f59e0b
        assert token_rgb('--color-signal-watch') in border_color, \
            f"Watch card should have amber border, got {border_color}"

    avoid_card = page.locator('.stat-card.stat-card--avoid').first
    if avoid_card.count() > 0:
        border_color = avoid_card.evaluate('el => window.getComputedStyle(el).borderLeftColor')
        # --color-signal-avoid: #94a3b8
        assert token_rgb('--color-signal-avoid') in border_color, \
            f"Avoid card should have slate border, got {border_color}"


@pytest.mark.e2e
def test_active_filter_button_has_correct_styling(e2e_site_multi_species) -> None:
    """Active filter buttons should have blue background and white text."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    hot_button = page.locator('.filter-btn').first
    hot_button.click()
    assert hot_button.evaluate('el => el.classList.contains("is-active")'), \
        "Clicked filter button should have 'is-active' class"

    bg_color = hot_button.evaluate('el => window.getComputedStyle(el).backgroundColor')
    # FilterButton.svelte .filter-btn.is-active uses --color-accent
    assert token_rgb('--color-accent') in bg_color, \
        f"Active button should have blue (--color-accent) background, got {bg_color}"

    text_color = hot_button.evaluate('el => window.getComputedStyle(el).color')
    assert 'rgb(255, 255, 255)' in text_color or 'white' in text_color.lower(), \
        f"Active button should have white text, got {text_color}"


@pytest.mark.e2e
def test_table_scroll_containers_have_overflow_auto(e2e_site_multi_species) -> None:
    """Tables should be wrapped in .table-scroll containers with overflow-x: auto."""
    page, base_url, errors = e2e_site_multi_species

    for page_name in ['breeder.html', 'dealer.html', 'history.html']:
        page.goto(f"{base_url}/{page_name}", wait_until="domcontentloaded")

        containers = page.locator('.table-scroll')
        assert containers.count() >= 1, \
            f"{page_name} should have at least one .table-scroll container"

        overflow_x = containers.first.evaluate(
            'el => window.getComputedStyle(el).overflowX'
        )
        assert overflow_x == 'auto', \
            f"{page_name} .table-scroll should have overflow-x: auto, got {overflow_x}"


@pytest.mark.e2e
def test_analysis_row_count_paragraph_styling(e2e_site_multi_species) -> None:
    """Row-count strip on analysis pages should use the .table-stats component."""
    page, base_url, errors = e2e_site_multi_species

    for page_name in ['breeder.html', 'dealer.html']:
        page.goto(f"{base_url}/{page_name}", wait_until="domcontentloaded")

        stats = page.locator('.table-stats')
        assert stats.count() >= 1, \
            f"{page_name} should have at least one .table-stats element"

        display = stats.first.evaluate(
            'el => window.getComputedStyle(el).display'
        )
        assert display == 'flex', \
            f"{page_name} .table-stats should have display: flex, got {display}"

        color = stats.first.evaluate(
            'el => window.getComputedStyle(el).color'
        )
        # --color-text: #333
        assert token_rgb('--color-text') in color, \
            f"{page_name} .table-stats should use --color-text (#333), got {color}"


@pytest.mark.e2e
def test_analysis_examples_content_padding(e2e_site_multi_species) -> None:
    """Examples content inside <details> should use .examples-content class with padding.

    Skipped when the examples section is absent from the test dataset.
    """
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    examples_content = page.locator('.examples-content')
    if examples_content.count() == 0:
        pytest.skip("Examples section not rendered with current test data")

    padding = examples_content.first.evaluate(
        'el => window.getComputedStyle(el).padding'
    )
    assert padding == '15px', f".examples-content should have padding: 15px, got {padding}"


@pytest.mark.e2e
def test_signal_filter_row_layout(e2e_site_multi_species) -> None:
    """Signal filter row should be a flex container so label and buttons share a line."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    filter_row = page.locator('.filter-section')
    assert filter_row.count() >= 1, "Breeder page should have .filter-section element"

    styles = filter_row.first.evaluate(
        'el => { const s = window.getComputedStyle(el); '
        'return { display: s.display, alignItems: s.alignItems, marginBottom: s.marginBottom }; }'
    )
    assert styles['display'] == 'flex', \
        f".filter-section should have display: flex, got {styles['display']}"
    assert styles['alignItems'] == 'center', \
        f".filter-section should have align-items: center, got {styles['alignItems']}"
    assert styles['marginBottom'] == '15px', \
        f".filter-section should have margin-bottom: 15px, got {styles['marginBottom']}"


@pytest.mark.e2e
def test_filter_label_styling(e2e_site_multi_species) -> None:
    """Signal filter label (.filter-label) should have correct color and right spacing."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    filter_label = page.locator('.filter-label')
    assert filter_label.count() >= 1, "Breeder page should have .filter-label element"

    # --color-primary-light: #34495e
    color = filter_label.first.evaluate('el => window.getComputedStyle(el).color')
    assert token_rgb('--color-primary-light') in color, \
        f".filter-label should be rgb(52, 73, 94), got {color}"

    margin_right = filter_label.first.evaluate('el => window.getComputedStyle(el).marginRight')
    assert margin_right == '10px', \
        f".filter-label should have margin-right: 10px, got {margin_right}"


@pytest.mark.e2e
def test_search_input_styling(e2e_site_multi_species) -> None:
    """Search inputs should use .search-input class with full-width and consistent style."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    # Wait for Svelte to mount the table before interacting with filters
    page.locator("#breeder-table tbody tr").first.wait_for(timeout=5000)

    # Search is inside the More Filters panel — expand it first
    advanced_toggle = page.locator(".advanced-filters-toggle")
    assert advanced_toggle.count() > 0, "Expected .advanced-filters-toggle button to be present"
    advanced_toggle.first.click()
    page.locator(".advanced-filters-content").wait_for(timeout=2000)

    search_input = page.locator('.search-input')
    assert search_input.count() >= 1, "Breeder page should have .search-input element"

    # The search input is in a column-direction flex container (label stacked above input),
    # so the full row width is available — verify the input fills it.
    row_width = search_input.first.evaluate(
        'el => el.parentElement.getBoundingClientRect().width'
    )
    input_width = search_input.first.evaluate(
        'el => el.getBoundingClientRect().width'
    )
    assert abs(row_width - input_width) < 5, \
        f".search-input should fill its container width (row={row_width:.1f}, input={input_width:.1f})"

    border_radius = search_input.first.evaluate(
        'el => window.getComputedStyle(el).borderRadius'
    )
    assert border_radius == '4px', \
        f".search-input should have border-radius: 4px, got {border_radius}"

    font_size = search_input.first.evaluate(
        'el => parseFloat(window.getComputedStyle(el).fontSize)'
    )
    assert 14 <= font_size <= 16, \
        f".search-input should have font-size ~0.95rem (~15px), got {font_size}px"
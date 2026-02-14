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

import pytest

from e2e.fixtures import e2e_site_multi_species


@pytest.mark.e2e
def test_table_sorting_numeric_columns(e2e_site_multi_species) -> None:
    """Verify clicking numeric column headers sorts the table correctly (ascending/descending)."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Find the "OOS Runs" column header (index 3 based on breeder table structure)
    # Species | Size | Signal | OOS Runs | ...
    oos_header = page.locator('#breeder-table thead th').nth(3)
    
    # First click: sort descending (default direction flips from undefined to desc)
    oos_header.click()
    page.wait_for_timeout(100)  # Small delay for sorting to complete
    
    # Verify sort direction attribute
    sort_direction = oos_header.get_attribute('data-sort-direction')
    assert sort_direction == 'desc', "Expected descending sort after first click"
    
    # Get all OOS values from visible rows
    oos_cells = page.locator('#breeder-table tbody tr:visible td').nth(3).all_text_contents()
    oos_values = [int(cell.strip()) for cell in oos_cells if cell.strip().isdigit()]
    
    # Verify descending order
    assert oos_values == sorted(oos_values, reverse=True), f"Expected descending order, got {oos_values}"
    
    # Second click: sort ascending
    oos_header.click()
    page.wait_for_timeout(100)
    
    sort_direction = oos_header.get_attribute('data-sort-direction')
    assert sort_direction == 'asc', "Expected ascending sort after second click"
    
    oos_cells = page.locator('#breeder-table tbody tr:visible td').nth(3).all_text_contents()
    oos_values = [int(cell.strip()) for cell in oos_cells if cell.strip().isdigit()]
    
    # Verify ascending order
    assert oos_values == sorted(oos_values), f"Expected ascending order, got {oos_values}"


@pytest.mark.e2e
def test_table_sorting_string_columns(e2e_site_multi_species) -> None:
    """Verify clicking string column headers sorts alphabetically."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Click "Species" column header (index 0)
    species_header = page.locator('#breeder-table thead th').nth(0)
    species_header.click()
    page.wait_for_timeout(100)
    
    # Get species names from visible rows
    species_cells = page.locator('#breeder-table tbody tr:visible td').nth(0).all_text_contents()
    species_names = [cell.strip() for cell in species_cells]
    
    # Verify alphabetical order (ascending by default)
    assert species_names == sorted(species_names), f"Expected alphabetical order, got {species_names}"
    
    # Second click: descending
    species_header.click()
    page.wait_for_timeout(100)
    
    species_cells = page.locator('#breeder-table tbody tr:visible td').nth(0).all_text_contents()
    species_names = [cell.strip() for cell in species_cells]
    
    # Verify reverse alphabetical order
    assert species_names == sorted(species_names, reverse=True), f"Expected reverse order, got {species_names}"


@pytest.mark.e2e
def test_signal_filtering_on_breeder_table(e2e_site_multi_species) -> None:
    """Verify signal filter buttons (🔥/⚠️/❌) work correctly on breeder page."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # All rows visible initially
    all_rows = page.locator('#breeder-table tbody tr').count()
    assert all_rows == 5, "Expected 5 species in test data"
    
    # Click "🔥 Hot" filter button
    hot_button = page.locator('button:has-text("🔥")')
    hot_button.click()
    page.wait_for_timeout(100)
    
    # Only rows with data-signal="🔥" should be visible
    visible_rows = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_rows == 2, "Expected 2 species with 🔥 signal"
    
    # Verify button has active class
    assert "active" in hot_button.get_attribute("class"), "Expected active class on clicked button"
    
    # Click "Show All" to reset (use specific selector for signal filter)
    show_all = page.locator('button[onclick*="filterBySignal"][onclick*="all"]')
    show_all.click()
    page.wait_for_timeout(100)
    
    visible_rows = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_rows == 5, "Expected all rows visible after Show All"


@pytest.mark.e2e
def test_stock_pattern_filtering_on_breeder_table(e2e_site_multi_species) -> None:
    """Verify stock pattern filter buttons work correctly on breeder page."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Expand advanced filters if collapsed
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        # Check if already expanded
        advanced_content = page.locator(".advanced-filters-content")
        if not advanced_content.get_attribute("class").split().__contains__("show"):
            advanced_toggle.click()
            page.wait_for_timeout(200)
    
    # Click "Emerging" pattern filter
    emerging_button = page.locator('button[onclick*="filterByStockPattern(\'Emerging\'"]')
    emerging_button.click()
    page.wait_for_timeout(100)
    
    # Only rows with data-stock-pattern="Emerging" should be visible
    visible_rows = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_rows == 2, "Expected 2 species with Emerging pattern"
    
    # Verify button has active class
    assert "active" in emerging_button.get_attribute("class"), "Expected active class"


@pytest.mark.e2e
def test_search_filter_on_breeder_and_dealer_tables(e2e_site_multi_species) -> None:
    """Test that the text search filter works on both breeder and dealer tables."""
    page, base_url, errors = e2e_site_multi_species

    # TEST: Breeder page search filter
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_toggle.click()
        page.wait_for_selector(".advanced-filters-content.show", timeout=2000)
    
    # All rows should be visible initially
    visible_rows = page.locator("#breeder-table tbody tr:visible")
    assert visible_rows.count() == 5, "Expected 5 visible rows initially"
    
    # Type "Brachypelma" in search box
    search_input = page.locator("#search-breeder-table")
    assert search_input.count() == 1, "Search input should exist"
    search_input.type("Brachypelma")
    
    # Only 1 row should be visible (Brachypelma hamorii)
    page.wait_for_timeout(200)
    visible_rows = page.locator("#breeder-table tbody tr:visible")
    assert visible_rows.count() == 1, "Expected 1 visible row after filtering 'Brachypelma'"
    
    # Verify the correct species is visible
    visible_text = visible_rows.first.text_content()
    assert "Brachypelma hamorii" in visible_text, "Wrong species visible after filter"
    
    # Clear search - all rows should be visible again
    search_input.fill("")
    search_input.dispatch_event("keyup")
    page.wait_for_timeout(200)
    visible_rows = page.locator("#breeder-table tbody tr:visible")
    assert visible_rows.count() == 5, "Expected 5 visible rows after clearing filter"
    
    # TEST: Dealer page search filter
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_toggle.click()
        page.wait_for_selector(".advanced-filters-content.show", timeout=2000)
    
    # All rows visible initially
    visible_rows = page.locator("#dealer-table tbody tr:visible")
    assert visible_rows.count() == 5, "Expected 5 visible rows initially on dealer page"
    
    # Search for "hamorii"
    search_input = page.locator("#search-dealer-table")
    assert search_input.count() == 1, "Search input should exist on dealer page"
    search_input.type("hamorii")
    
    # Only 1 row should be visible
    page.wait_for_timeout(200)
    visible_rows = page.locator("#dealer-table tbody tr:visible")
    assert visible_rows.count() == 1, "Expected 1 visible row after filtering 'hamorii'"
    
    visible_text = visible_rows.first.text_content()
    assert "hamorii" in visible_text, "Wrong species visible after filter on dealer page"
    
    # Test case-insensitive search
    search_input.fill("")
    search_input.dispatch_event("keyup")
    page.wait_for_timeout(100)
    search_input.type("PULCHRA")  # UPPERCASE
    page.wait_for_timeout(200)
    visible_rows = page.locator("#dealer-table tbody tr:visible")
    assert visible_rows.count() == 1, "Expected 1 visible row for case-insensitive search"
    
    visible_text = visible_rows.first.text_content()
    assert "pulchra" in visible_text.lower(), "Case-insensitive search failed"


@pytest.mark.e2e
def test_combined_signal_and_stock_pattern_filters(e2e_site_multi_species) -> None:
    """Verify applying multiple filter types (signal then stock pattern).
    
    NOTE: Current implementation replaces filters rather than combining them (no AND logic yet).
    This test verifies the actual behavior: stock pattern filter replaces signal filter.
    """
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_toggle.click()
        page.wait_for_timeout(200)
    
    # Apply signal filter: 🔥 Hot
    hot_button = page.locator('button:has-text("🔥")')
    hot_button.click()
    page.wait_for_timeout(100)
    
    # Should show 2 rows with 🔥 signal
    visible_after_signal = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_after_signal == 2, "Expected 2 rows after signal filter"
    
    # Now apply stock pattern filter: Emerging
    # NOTE: Current implementation replaces the signal filter (doesn't combine via AND)
    emerging_button = page.locator("button[onclick*=\"filterByStockPattern('Emerging'\"]")
    emerging_button.click()
    page.wait_for_timeout(100)
    
    # Should show 2 rows (Emerging pattern species: Brachypelma, Pterinochilus)
    # Signal filter is replaced, not combined (filters don't AND together currently)
    visible_after_both = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_after_both == 2, "Expected 2 rows with Emerging pattern (signal filter replaced)"
    
    # Click signal filter's "Show All" to clear filters
    show_all = page.locator('button[onclick*="filterBySignal"][onclick*="all"]')
    show_all.click()
    page.wait_for_timeout(100)
    
    # All rows should be visible
    visible_after_clear = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_after_clear == 5, "Expected all 5 rows after Show All"


@pytest.mark.e2e
def test_search_filter_combined_with_signal_filter(e2e_site_multi_species) -> None:
    """Verify search text filter works together with signal filter."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Expand advanced filters
    advanced_toggle = page.locator(".advanced-filters-toggle")
    if advanced_toggle.count() > 0:
        advanced_toggle.click()
        page.wait_for_timeout(200)
    
    # Apply ⚠️ Watch signal filter first (2 species)
    watch_button = page.locator('button:has-text("⚠️")')
    watch_button.click()
    page.wait_for_timeout(100)
    
    visible_after_signal = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_after_signal == 2, "Expected 2 rows with ⚠️ signal"
    
    # Now type search: "Brachypelma" (only matches one of the ⚠️ species)
    search_input = page.locator("#search-breeder-table")
    search_input.type("Brachypelma")
    page.wait_for_timeout(200)
    
    # Should show only 1 row (Brachypelma hamorii with ⚠️)
    visible_after_both = page.locator('#breeder-table tbody tr:visible').count()
    assert visible_after_both == 1, "Expected 1 row matching both ⚠️ and 'Brachypelma'"
    
    visible_text = page.locator('#breeder-table tbody tr:visible').first.text_content()
    assert "Brachypelma" in visible_text, "Expected Brachypelma in filtered results"


@pytest.mark.e2e
def test_advanced_filters_toggle_expand_collapse(e2e_site_multi_species) -> None:
    """Verify clicking 'More Filters' toggle expands/collapses advanced filters section."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    toggle_button = page.locator(".advanced-filters-toggle")
    content_div = page.locator(".advanced-filters-content")
    
    # Initially expanded or collapsed (depends on implementation)
    initial_classes = content_div.get_attribute("class").split()
    initially_expanded = "show" in initial_classes
    
    # Click to toggle
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Verify class changed
    after_click_classes = content_div.get_attribute("class").split()
    has_show_after_click = "show" in after_click_classes
    
    assert has_show_after_click != initially_expanded, "Expected toggle to change expanded state"
    
    # Click again to toggle back
    toggle_button.click()
    page.wait_for_timeout(200)
    
    final_classes = content_div.get_attribute("class").split()
    has_show_finally = "show" in final_classes
    
    assert has_show_finally == initially_expanded, "Expected toggle to return to initial state"

@pytest.mark.e2e
def test_snapshot_page_advanced_filters_toggle(e2e_site_multi_species) -> None:
    """Verify 'More Filters' toggle works on snapshot page."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Verify toggle button exists (snapshot page uses .btn-filters)
    toggle_button = page.locator(".btn-filters")
    assert toggle_button.is_visible(), "Toggle button should be visible on snapshot page"
    
    # Verify filter content container exists
    content_div = page.locator(".advanced-filters-content")
    assert content_div.count() > 0, "Advanced filters content container should exist"
    
    # Initially should be collapsed (no 'show' class)
    initial_classes = content_div.get_attribute("class").split()
    initially_expanded = "show" in initial_classes
    
    # Click to expand
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Verify expanded
    after_click_classes = content_div.get_attribute("class").split()
    has_show_after_click = "show" in after_click_classes
    assert has_show_after_click != initially_expanded, "Expected toggle to change expanded state"
    
    # Verify arrow rotation (button should have 'expanded' class)
    toggle_classes = toggle_button.get_attribute("class").split()
    button_expanded = "expanded" in toggle_classes
    assert button_expanded == has_show_after_click, "Toggle button should have 'expanded' class when content is shown"
    
    # Verify search input is now accessible
    search_input = page.locator("input[type='text']")
    assert search_input.is_visible(), "Search input should be visible when filters expanded"
    
    # Click again to collapse
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Verify collapsed
    final_classes = content_div.get_attribute("class").split()
    has_show_finally = "show" in final_classes
    assert has_show_finally == initially_expanded, "Expected toggle to return to initial state"


@pytest.mark.e2e
def test_snapshot_filter_badge_updates_with_search(e2e_site_multi_species) -> None:
    """Snapshot page should show filter count badge when search is active."""
    page, base_url, errors = e2e_site_multi_species

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Badge should be hidden by default
    badge = page.locator(".filter-badge")
    assert badge.count() == 1, "Badge element should exist on snapshot page"
    assert not badge.is_visible(), "Badge should be hidden when no filters active"
    
    # Expand filters (snapshot page uses .btn-filters)
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Type in search box
    search_input = page.locator("#search-snapshot-table")
    search_input.type("hamorii")
    page.wait_for_timeout(200)
    
    # Badge should appear with count "1"
    assert badge.is_visible(), "Badge should be visible when search active"
    assert badge.text_content() == "1", "Badge should show '1' for one active filter"
    
    # Clear search
    search_input.fill("")
    search_input.dispatch_event("keyup")
    page.wait_for_timeout(200)
    
    # Badge should hide again
    assert not badge.is_visible(), "Badge should hide when filters cleared"


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
    import re
    match = re.search(r'Showing:\s*(\d+)\s*of\s*(\d+)\s*species', initial_text)
    assert match, f"Should match pattern, got: {initial_text}"
    initial_visible = int(match.group(1))
    total_count = int(match.group(2))
    assert initial_visible == total_count, "Initially all rows should be visible"
    assert total_count > 1, "Should have multiple species for meaningful test"
    
    # Expand advanced filters
    toggle_button = page.locator(".btn-filters")
    toggle_button.click()
    page.wait_for_timeout(200)
    
    # Apply search filter that will reduce visible rows
    search_input = page.locator("#search-snapshot-table")
    search_input.type("hamorii")  # Should match only specific species
    page.wait_for_timeout(300)  # Give time for filtering to complete
    
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
    page.wait_for_timeout(300)
    
    # Verify count returns to original
    final_text = stats_strip.text_content()
    final_match = re.search(r'Showing:\s*(\d+)\s*of\s*(\d+)\s*species', final_text)
    assert final_match, f"Should match pattern after clearing, got: {final_text}"
    final_visible = int(final_match.group(1))
    
    assert final_visible == total_count, f"Count should return to original after clearing filter, got {final_visible} vs {total_count}"
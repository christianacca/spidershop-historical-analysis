#!/usr/bin/env python3
"""E2E tests for CSS styling and visual regression prevention.

Scope:
- Verify analysis-specific styles (summary stats, filter buttons, instruction box) exist ONLY on breeder/dealer pages
- Verify snapshot/history pages do NOT have analysis-specific styles
- Verify common styles (tables, header, footer) present on all pages
- Verify interactive states (active filter buttons, computed styles)

Purpose: Safety net for CSS refactoring (splitting base.html <style> into separate files)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_minimal


@pytest.mark.e2e
def test_analysis_pages_have_summary_stats_cards(e2e_site_minimal) -> None:
    """Breeder/dealer pages should have summary stat cards with correct styling."""
    page, base_url, errors = e2e_site_minimal

    # Test breeder page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Summary stats container should exist
    summary_stats = page.locator('.summary-stats')
    assert summary_stats.count() == 1, "Breeder page should have .summary-stats container"
    
    # Stat cards should exist with correct classes
    stat_cards = page.locator('.stat-card')
    assert stat_cards.count() >= 3, "Should have at least 3 stat cards (hot, watch, avoid)"
    
    # Check for specific stat card types
    assert page.locator('.stat-card.stat-hot').count() >= 1, "Should have .stat-hot card"
    assert page.locator('.stat-card.stat-watch').count() >= 1, "Should have .stat-watch card"
    assert page.locator('.stat-card.stat-avoid').count() >= 1, "Should have .stat-avoid card"
    
    # Test dealer page
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    
    summary_stats = page.locator('.summary-stats')
    assert summary_stats.count() == 1, "Dealer page should have .summary-stats container"
    
    stat_cards = page.locator('.stat-card')
    assert stat_cards.count() >= 3, "Dealer should have at least 3 stat cards"


@pytest.mark.e2e
def test_snapshot_history_pages_have_no_summary_stats(e2e_site_minimal) -> None:
    """Snapshot/history pages should NOT have summary stat cards (analysis-only feature)."""
    page, base_url, errors = e2e_site_minimal

    # Test snapshot page
    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    summary_stats = page.locator('.summary-stats')
    assert summary_stats.count() == 0, "Snapshot page should NOT have .summary-stats container"
    
    stat_cards = page.locator('.stat-card')
    assert stat_cards.count() == 0, "Snapshot page should NOT have stat cards"
    
    # Test history page
    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")
    
    summary_stats = page.locator('.summary-stats')
    assert summary_stats.count() == 0, "History page should NOT have .summary-stats container"
    
    stat_cards = page.locator('.stat-card')
    assert stat_cards.count() == 0, "History page should NOT have stat cards"


@pytest.mark.e2e
def test_filter_buttons_exist_on_analysis_pages(e2e_site_minimal) -> None:
    """Breeder/dealer pages should have signal filter buttons with correct structure."""
    page, base_url, errors = e2e_site_minimal

    # Test breeder page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Breeder has two filter button containers (signal + stock pattern)
    filter_containers = page.locator('.filter-buttons-container')
    assert filter_containers.count() >= 1, "Breeder page should have filter button containers"
    
    # Check for signal filter buttons specifically (have data-action="filter-signal")
    signal_buttons = page.locator('.filter-btn[data-action="filter-signal"]')
    assert signal_buttons.count() >= 3, "Should have at least 3 signal filter buttons (hot, watch, avoid)"
    
    # Test dealer page
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    
    # Dealer has one filter button container (signal only, no stock pattern)
    filter_containers = page.locator('.filter-buttons-container')
    assert filter_containers.count() >= 1, "Dealer page should have filter button container"
    
    signal_buttons = page.locator('.filter-btn[data-action="filter-signal"]')
    assert signal_buttons.count() >= 3, "Dealer should have at least 3 signal filter buttons"


@pytest.mark.e2e
def test_filter_buttons_have_flexbox_layout(e2e_site_minimal) -> None:
    """Filter button container should use flexbox layout."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Get computed style of first filter buttons container (signal filters)
    container_display = page.locator('.filter-buttons-container').first.evaluate(
        'el => window.getComputedStyle(el).display'
    )
    # Can be 'flex' or 'inline-block' depending on the container
    assert container_display in ['flex', 'inline-block'], \
        f"Filter container should have flex or inline-block display, got {container_display}"
    
    # Check filter button has appropriate display
    button_display = page.locator('.filter-btn').first.evaluate(
        'el => window.getComputedStyle(el).display'
    )
    assert 'flex' in button_display or 'inline' in button_display, \
        f"Filter button should have flex or inline display, got {button_display}"


@pytest.mark.e2e
def test_snapshot_history_pages_have_no_signal_filter_buttons(e2e_site_minimal) -> None:
    """Snapshot/history pages should NOT have signal filter buttons (analysis-only feature)."""
    page, base_url, errors = e2e_site_minimal

    # Test snapshot page
    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Should not have the signal filter buttons container
    filter_container = page.locator('.filter-buttons-container')
    signal_buttons_count = filter_container.count()
    
    # If container exists, check it doesn't have signal filter buttons (might have other controls)
    if signal_buttons_count > 0:
        # Check specifically for signal/risk filter buttons (have data-signal or similar)
        signal_filters = page.locator('.filter-btn[onclick*="filterBySignal"]')
        assert signal_filters.count() == 0, "Snapshot page should NOT have signal filter buttons"
    
    # Test history page
    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")
    
    signal_filters = page.locator('.filter-btn[onclick*="filterBySignal"]')
    assert signal_filters.count() == 0, "History page should NOT have signal filter buttons"


@pytest.mark.e2e
def test_instruction_box_exists_on_analysis_pages(e2e_site_minimal) -> None:
    """Breeder/dealer pages should have instruction box (details element)."""
    page, base_url, errors = e2e_site_minimal

    # Test breeder page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    instruction_box = page.locator('.instruction-box')
    assert instruction_box.count() == 1, "Breeder page should have .instruction-box"
    
    # Should be a details element
    tag_name = instruction_box.evaluate('el => el.tagName.toLowerCase()')
    assert tag_name == 'details', f"Instruction box should be <details> element, got <{tag_name}>"
    
    # Should have summary element
    summary = instruction_box.locator('summary')
    assert summary.count() == 1, "Instruction box should have <summary>"
    
    # Test dealer page
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    
    instruction_box = page.locator('.instruction-box')
    assert instruction_box.count() == 1, "Dealer page should have .instruction-box"
    
    tag_name = instruction_box.evaluate('el => el.tagName.toLowerCase()')
    assert tag_name == 'details', f"Dealer instruction box should be <details>, got <{tag_name}>"


@pytest.mark.e2e
def test_instruction_box_not_on_snapshot_history(e2e_site_minimal) -> None:
    """Snapshot/history pages should NOT have instruction box (simple data pages)."""
    page, base_url, errors = e2e_site_minimal

    # Test snapshot page
    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    instruction_box = page.locator('.instruction-box')
    assert instruction_box.count() == 0, "Snapshot page should NOT have .instruction-box"
    
    # Test history page
    page.goto(f"{base_url}/history.html", wait_until="domcontentloaded")
    
    instruction_box = page.locator('.instruction-box')
    assert instruction_box.count() == 0, "History page should NOT have .instruction-box"


@pytest.mark.e2e
def test_data_tables_styled_consistently_all_pages(e2e_site_minimal) -> None:
    """All pages with tables should have consistent table styling from common CSS."""
    page, base_url, errors = e2e_site_minimal

    pages_with_tables = [
        ('breeder.html', '#breeder-table'),
        ('dealer.html', '#dealer-table'),
        ('snapshot.html', '#snapshot-table'),
        ('history.html', '#history-table'),
    ]
    
    for page_name, table_id in pages_with_tables:
        page.goto(f"{base_url}/{page_name}", wait_until="domcontentloaded")
        
        table = page.locator(table_id)
        assert table.count() == 1, f"{page_name} should have table with id {table_id}"
        
        # Check table has data-table class
        has_class = table.evaluate('el => el.classList.contains("data-table")')
        assert has_class, f"Table on {page_name} should have .data-table class"
        
        # Check border-collapse (common table style)
        border_collapse = table.evaluate('el => window.getComputedStyle(el).borderCollapse')
        assert border_collapse == 'collapse', f"{page_name} table should have border-collapse:collapse"
        
        # Check table header has background color (should not be transparent)
        th_bg = page.locator(f'{table_id} thead th').first.evaluate(
            'el => window.getComputedStyle(el).backgroundColor'
        )
        assert th_bg != 'rgba(0, 0, 0, 0)' and th_bg != 'transparent', \
            f"{page_name} table headers should have background color"


@pytest.mark.e2e
def test_stat_cards_have_correct_border_colors(e2e_site_minimal) -> None:
    """Stat cards should have color-coded left borders (red=hot, orange=watch, gray=avoid)."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Check hot card has red-ish border
    hot_card = page.locator('.stat-card.stat-hot').first
    if hot_card.count() > 0:
        border_color = hot_card.evaluate('el => window.getComputedStyle(el).borderLeftColor')
        # Should be red-ish: #e74c3c = rgb(231, 76, 60)
        assert 'rgb(231, 76, 60)' in border_color or '#e74c3c' in border_color.lower(), \
            f"Hot card should have red border, got {border_color}"
    
    # Check watch card has orange border
    watch_card = page.locator('.stat-card.stat-watch').first
    if watch_card.count() > 0:
        border_color = watch_card.evaluate('el => window.getComputedStyle(el).borderLeftColor')
        # Should be orange: #f39c12 = rgb(243, 156, 18)
        assert 'rgb(243, 156, 18)' in border_color or '#f39c12' in border_color.lower(), \
            f"Watch card should have orange border, got {border_color}"
    
    # Check avoid card has gray border
    avoid_card = page.locator('.stat-card.stat-avoid').first
    if avoid_card.count() > 0:
        border_color = avoid_card.evaluate('el => window.getComputedStyle(el).borderLeftColor')
        # Should be gray: #95a5a6 = rgb(149, 165, 166)
        assert 'rgb(149, 165, 166)' in border_color or '#95a5a6' in border_color.lower(), \
            f"Avoid card should have gray border, got {border_color}"


@pytest.mark.e2e
def test_active_filter_button_has_correct_styling(e2e_site_minimal) -> None:
    """Active filter buttons should have blue background and white text."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Click a filter button to make it active
    hot_button = page.locator('.filter-btn').first
    hot_button.click()
    page.wait_for_timeout(100)  # Wait for class change
    
    # Check if button has 'active' class
    has_active_class = hot_button.evaluate('el => el.classList.contains("active")')
    assert has_active_class, "Clicked filter button should have 'active' class"
    
    # Check background color is blue (#3498db = rgb(52, 152, 219))
    bg_color = hot_button.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert 'rgb(52, 152, 219)' in bg_color or '#3498db' in bg_color.lower(), \
        f"Active button should have blue background, got {bg_color}"
    
    # Check text color is white
    text_color = hot_button.evaluate('el => window.getComputedStyle(el).color')
    # White can be rgb(255, 255, 255) or just 'white'
    assert 'rgb(255, 255, 255)' in text_color or 'white' in text_color.lower(), \
        f"Active button should have white text, got {text_color}"


@pytest.mark.e2e
def test_header_footer_styled_consistently_all_pages(e2e_site_minimal) -> None:
    """Header and footer should have consistent styling on all pages (from common CSS)."""
    page, base_url, errors = e2e_site_minimal

    pages = ['index.html', 'breeder.html', 'dealer.html', 'snapshot.html', 'history.html']
    
    for page_name in pages:
        page.goto(f"{base_url}/{page_name}", wait_until="domcontentloaded")
        
        # Check header styling
        header = page.locator('header')
        assert header.count() == 1, f"{page_name} should have header element"
        
        header_bg = header.evaluate('el => window.getComputedStyle(el).backgroundColor')
        # Should be dark: #2c3e50 = rgb(44, 62, 80)
        assert 'rgb(44, 62, 80)' in header_bg or '#2c3e50' in header_bg.lower(), \
            f"{page_name} header should have dark background, got {header_bg}"
        
        header_color = header.evaluate('el => window.getComputedStyle(el).color')
        # Should be white
        assert 'rgb(255, 255, 255)' in header_color or 'white' in header_color.lower(), \
            f"{page_name} header should have white text, got {header_color}"
        
        # Check footer exists
        footer = page.locator('footer')
        assert footer.count() == 1, f"{page_name} should have footer element"


@pytest.mark.e2e
def test_snapshot_page_has_action_buttons_container(e2e_site_minimal) -> None:
    """Snapshot page should have action-buttons container with side-by-side layout."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Find action-buttons container
    action_buttons = page.locator('.action-buttons')
    assert action_buttons.count() == 1, "Snapshot page should have .action-buttons container"
    
    # Check it uses flexbox
    display = action_buttons.evaluate('el => window.getComputedStyle(el).display')
    assert 'flex' in display, f"Action buttons should use flexbox layout, got {display}"
    
    # Check download button exists
    download_btn = action_buttons.locator('.btn-download')
    assert download_btn.count() == 1, "Should have download button inside action-buttons"
    assert download_btn.is_visible(), "Download button should be visible"
    
    # Check filter button exists
    filter_btn = action_buttons.locator('.btn-filters')
    assert filter_btn.count() == 1, "Should have filter button inside action-buttons"
    assert filter_btn.is_visible(), "Filter button should be visible"


@pytest.mark.e2e
def test_snapshot_page_buttons_have_correct_colors(e2e_site_minimal) -> None:
    """Snapshot page buttons should have correct brand colors (green download, blue filter)."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Check download button is green
    download_btn = page.locator('.btn-download')
    download_bg = download_btn.evaluate('el => window.getComputedStyle(el).backgroundColor')
    # #27ae60 = rgb(39, 174, 96)
    assert 'rgb(39, 174, 96)' in download_bg, f"Download button should be green, got {download_bg}"
    
    # Check filter button is blue
    filter_btn = page.locator('.btn-filters')
    filter_bg = filter_btn.evaluate('el => window.getComputedStyle(el).backgroundColor')
    # #3498db = rgb(52, 152, 219)
    assert 'rgb(52, 152, 219)' in filter_bg, f"Filter button should be blue, got {filter_bg}"


@pytest.mark.e2e
def test_snapshot_page_has_table_stats_strip(e2e_site_minimal) -> None:
    """Snapshot page should have table-stats strip showing species count."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Find table-stats strip
    stats_strip = page.locator('.table-stats')
    assert stats_strip.count() == 1, "Snapshot page should have .table-stats strip"
    assert stats_strip.is_visible(), "Stats strip should be visible"
    
    # Check it has light blue background
    bg_color = stats_strip.evaluate('el => window.getComputedStyle(el).backgroundColor')
    # #e8f4f8 = rgb(232, 244, 248)
    assert 'rgb(232, 244, 248)' in bg_color, f"Stats strip should have light blue background, got {bg_color}"
    
    # Check for "Showing:" text
    stats_text = stats_strip.text_content()
    assert 'Showing:' in stats_text, f"Stats strip should contain 'Showing:', got: {stats_text}"
    assert 'species' in stats_text.lower(), f"Stats strip should mention 'species', got: {stats_text}"
    
    # Check for visible-count span
    visible_count_span = stats_strip.locator('span[id^="visible-count"]')
    assert visible_count_span.count() == 1, "Stats strip should have visible-count span"


@pytest.mark.e2e
def test_snapshot_page_stats_strip_positioned_above_table(e2e_site_minimal) -> None:
    """Stats strip should appear directly above the data table."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/snapshot.html", wait_until="domcontentloaded")
    
    # Get positions
    stats_strip = page.locator('.table-stats')
    data_table = page.locator('.data-table')
    
    assert stats_strip.count() == 1, "Should have stats strip"
    assert data_table.count() >= 1, "Should have data table"
    
    # Get bounding boxes
    stats_box = stats_strip.bounding_box()
    table_box = data_table.first.bounding_box()
    
    assert stats_box is not None, "Stats strip should have dimensions"
    assert table_box is not None, "Table should have dimensions"
    
    # Stats strip should be above the table (lower y value)
    assert stats_box['y'] < table_box['y'], "Stats strip should appear above the table"
    
    # They should be relatively close (within 100px)
    vertical_gap = table_box['y'] - (stats_box['y'] + stats_box['height'])
    assert vertical_gap < 100, f"Stats strip and table should be close together, gap is {vertical_gap}px"

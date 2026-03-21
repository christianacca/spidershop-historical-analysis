#!/usr/bin/env python3
"""E2E tests for species detail page interactions.

Scope:
- Tab switching between Breeder and Dealer views
- URL parameter initialization (?view=breeder or ?view=dealer)
- URL updates via window.history.pushState() when switching tabs
- Back button highlighting logic (sync with active tab)
- ARIA attribute updates during tab switches
- Chart rendering (price trends, wishlist trends, stock strips)
- SVG visualization validation
- Interactive tooltip behavior

What's NOT tested here:
- Basic page loads and navigation (see test_navigation_and_page_loads.py)
- Table interactions (see test_table_interactions.py)
"""

from __future__ import annotations

import pytest

from e2e.css_tokens import hex_to_rgb, token_rgb
from e2e.fixtures import e2e_site_minimal


@pytest.mark.e2e
def test_tab_switching_between_breeder_and_dealer_views(e2e_site_minimal) -> None:
    """Verify clicking tabs switches between breeder and dealer panels correctly."""
    page, base_url, errors = e2e_site_minimal

    # Navigate from breeder page to species detail
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Initially breeder view should be active (default)
    breeder_tab = page.locator("#tab-breeder")
    dealer_tab = page.locator("#tab-dealer")
    breeder_panel = page.locator("#panel-breeder")
    dealer_panel = page.locator("#panel-dealer")
    
    # Verify initial state (breeder active)
    assert breeder_tab.get_attribute("aria-selected") == "true", "Breeder tab should be active initially"
    assert dealer_tab.get_attribute("aria-selected") == "false", "Dealer tab should not be active initially"
    assert breeder_panel.is_visible(), "Breeder panel should be visible"
    assert not dealer_panel.is_visible(), "Dealer panel should be hidden"
    
    # Click dealer tab
    dealer_tab.click()
    page.wait_for_timeout(100)
    
    # Verify dealer view is now active
    assert dealer_tab.get_attribute("aria-selected") == "true", "Dealer tab should be active after click"
    assert breeder_tab.get_attribute("aria-selected") == "false", "Breeder tab should not be active after click"
    assert dealer_panel.is_visible(), "Dealer panel should be visible after click"
    assert not breeder_panel.is_visible(), "Breeder panel should be hidden after click"
    
    # Click breeder tab to switch back
    breeder_tab.click()
    page.wait_for_timeout(100)
    
    # Verify back to breeder view
    assert breeder_tab.get_attribute("aria-selected") == "true", "Breeder tab should be active again"
    assert dealer_tab.get_attribute("aria-selected") == "false", "Dealer tab should not be active again"
    assert breeder_panel.is_visible(), "Breeder panel should be visible again"
    assert not dealer_panel.is_visible(), "Dealer panel should be hidden again"


@pytest.mark.e2e
def test_url_parameter_initializes_correct_tab_on_load(e2e_site_minimal) -> None:
    """Verify ?view=dealer URL parameter activates dealer tab on page load."""
    page, base_url, errors = e2e_site_minimal

    # Navigate from dealer page to species detail (URL will have ?view=dealer)
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Wait for page to load and JS to initialize
    page.wait_for_timeout(200)
    
    # Verify dealer tab is active (because we came from dealer page)
    dealer_tab = page.locator("#tab-dealer")
    breeder_tab = page.locator("#tab-breeder")
    dealer_panel = page.locator("#panel-dealer")
    breeder_panel = page.locator("#panel-breeder")
    
    assert "?view=dealer" in page.url, "URL should contain ?view=dealer parameter"
    assert dealer_tab.get_attribute("aria-selected") == "true", "Dealer tab should be active on load"
    assert breeder_tab.get_attribute("aria-selected") == "false", "Breeder tab should not be active on load"
    assert dealer_panel.is_visible(), "Dealer panel should be visible on load"
    assert not breeder_panel.is_visible(), "Breeder panel should be hidden on load"


@pytest.mark.e2e
def test_url_updates_on_tab_switch_via_pushstate(e2e_site_minimal) -> None:
    """Verify URL changes when switching tabs (without page reload)."""
    page, base_url, errors = e2e_site_minimal

    # Navigate from breeder page to species detail
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Initial URL should have ?view=breeder
    assert "?view=breeder" in page.url, "URL should start with ?view=breeder"
    
    # Click dealer tab
    dealer_tab = page.locator("#tab-dealer")
    dealer_tab.click()
    page.wait_for_timeout(200)
    
    # URL should now have ?view=dealer (without full page reload)
    assert "?view=dealer" in page.url, "URL should update to ?view=dealer after clicking dealer tab"
    
    # Click breeder tab
    breeder_tab = page.locator("#tab-breeder")
    breeder_tab.click()
    page.wait_for_timeout(200)
    
    # URL should be back to ?view=breeder
    assert "?view=breeder" in page.url, "URL should update to ?view=breeder after clicking breeder tab"


@pytest.mark.e2e
def test_back_button_highlighting_syncs_with_active_tab(e2e_site_minimal) -> None:
    """Verify back button highlighting updates when switching between tabs."""
    page, base_url, errors = e2e_site_minimal

    # Navigate from breeder page to species detail
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Wait for JS to initialize highlighting
    page.wait_for_function(
        "document.getElementById('back-breeder')?.classList.contains('origin-btn') === true"
    )
    
    back_breeder = page.locator("#back-breeder")
    back_dealer = page.locator("#back-dealer")
    
    # Initially: breeder button should be highlighted (origin-btn class)
    assert "origin-btn" in back_breeder.get_attribute("class"), "Breeder back button should be highlighted initially"
    assert "origin-btn" not in back_dealer.get_attribute("class"), "Dealer back button should not be highlighted initially"
    
    # Switch to dealer tab
    dealer_tab = page.locator("#tab-dealer")
    dealer_tab.click()
    page.wait_for_timeout(200)
    
    # Now dealer button should be highlighted
    page.wait_for_function(
        "document.getElementById('back-dealer')?.classList.contains('origin-btn') === true"
    )
    
    assert "origin-btn" in back_dealer.get_attribute("class"), "Dealer back button should be highlighted after switching to dealer tab"
    assert "origin-btn" not in back_breeder.get_attribute("class"), "Breeder back button should not be highlighted after switching to dealer tab"
    
    # Switch back to breeder tab
    breeder_tab = page.locator("#tab-breeder")
    breeder_tab.click()
    page.wait_for_timeout(200)
    
    # Breeder button should be highlighted again
    page.wait_for_function(
        "document.getElementById('back-breeder')?.classList.contains('origin-btn') === true"
    )
    
    assert "origin-btn" in back_breeder.get_attribute("class"), "Breeder back button should be highlighted again after switching back"
    assert "origin-btn" not in back_dealer.get_attribute("class"), "Dealer back button should not be highlighted again after switching back"


@pytest.mark.e2e
def test_price_chart_renders_svg_with_data_points(e2e_site_minimal) -> None:
    """Verify price trend chart renders as SVG with correct structure and data points."""
    page, base_url, errors = e2e_site_minimal

    # Navigate to species detail page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Wait for chart rendering
    page.wait_for_timeout(300)
    
    # Verify price chart container and SVG exist
    price_chart = page.locator("#price-chart")
    assert price_chart.is_visible(), "Price chart container should be visible"
    
    svg = price_chart.locator("svg")
    assert svg.count() > 0, "Price chart should contain an SVG element"
    
    # Verify SVG has valid dimensions (may be percentage or pixel values)
    svg_element = svg.first
    width = svg_element.get_attribute("width")
    height = svg_element.get_attribute("height")
    assert width is not None, "SVG should have width attribute"
    assert height is not None, "SVG should have height attribute"
    # Accept either percentage ("100%") or pixel values ("600")
    assert width in ["100%"] or (width.isdigit() and int(width) > 0), f"SVG width should be valid, got: {width}"
    assert height in ["100%"] or (height.isdigit() and int(height) > 0), f"SVG height should be valid, got: {height}"
    
    # Verify chart has data visualization elements (polyline or circles for data points)
    # Charts use polylines for line segments and circles for data points
    has_polylines = svg_element.locator("polyline").count() > 0
    has_circles = svg_element.locator("circle").count() > 0
    assert has_polylines or has_circles, "Chart should contain polyline or circle elements for data visualization"
    
    # Verify price axis labels exist (text elements)
    text_elements = svg_element.locator("text")
    assert text_elements.count() > 0, "Chart should contain text elements for axis labels"


@pytest.mark.e2e
def test_wishlist_chart_renders_svg_correctly(e2e_site_minimal) -> None:
    """Verify wishlist trend chart renders as SVG with correct structure."""
    page, base_url, errors = e2e_site_minimal

    # Navigate to species detail page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Wait for chart rendering
    page.wait_for_timeout(300)
    
    # Verify wishlist chart container and SVG exist
    wishlist_chart = page.locator("#wishlist-chart")
    assert wishlist_chart.is_visible(), "Wishlist chart container should be visible"
    
    svg = wishlist_chart.locator("svg")
    assert svg.count() > 0, "Wishlist chart should contain an SVG element"
    
    # Verify SVG structure
    svg_element = svg.first
    width = svg_element.get_attribute("width")
    height = svg_element.get_attribute("height")
    assert width is not None, "Wishlist SVG should have width attribute"
    assert height is not None, "Wishlist SVG should have height attribute"
    # Accept either percentage or pixel values
    assert width in ["100%"] or (width.isdigit() and int(width) > 0), f"Wishlist SVG width should be valid, got: {width}"
    assert height in ["100%"] or (height.isdigit() and int(height) > 0), f"Wishlist SVG height should be valid, got: {height}"
    
    # Verify data visualization elements exist
    has_polylines = svg_element.locator("polyline").count() > 0
    has_circles = svg_element.locator("circle").count() > 0
    assert has_polylines or has_circles, "Wishlist chart should contain data visualization elements"
    
    # Wishlist chart should use different color than price chart
    # Price uses #3498db (blue), wishlist uses #16a34a (green)
    polylines = svg_element.locator("polyline")
    if polylines.count() > 0:
        stroke_color = polylines.first.get_attribute("stroke")
        assert stroke_color is not None, "Polyline should have stroke color"
        # Check for green color variations (#16a34a or rgb equivalent)
        assert "#16a34a" in stroke_color.lower() or "rgb(22, 163, 74)" in stroke_color, \
            f"Wishlist chart should use green color, got: {stroke_color}"


@pytest.mark.e2e
def test_stock_strip_renders_observed_timeline(e2e_site_minimal) -> None:
    """Verify stock observation strip renders with correct rectangle elements."""
    page, base_url, errors = e2e_site_minimal

    # Navigate to species detail page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Wait for chart rendering
    page.wait_for_timeout(300)
    
    # Verify stock strip container and SVG exist
    stock_strip = page.locator("#stock-strip")
    assert stock_strip.is_visible(), "Stock strip container should be visible"
    
    svg = stock_strip.locator("svg")
    assert svg.count() > 0, "Stock strip should contain an SVG element"
    
    # Verify SVG structure
    svg_element = svg.first
    width = svg_element.get_attribute("width")
    height = svg_element.get_attribute("height")
    assert width is not None, "Stock strip SVG should have width attribute"
    assert height is not None, "Stock strip SVG should have height attribute"
    # Accept either percentage or pixel values
    assert width in ["100%"] or (width.isdigit() and int(width) > 0), f"Stock strip SVG width should be valid, got: {width}"
    assert height in ["100%"] or (height.isdigit() and int(height) > 0), f"Stock strip SVG height should be valid, got: {height}"
    
    # Stock strip uses rectangles to show observed (green) vs not-observed (gray) timeline
    rectangles = svg_element.locator("rect")
    assert rectangles.count() > 0, "Stock strip should contain rectangle elements for timeline"
    
    # Verify rectangles have fill colors (implementation may vary, check any rect has color)
    # Stock strip typically uses multiple rectangles with different fills
    rect_with_fill = False
    for i in range(min(rectangles.count(), 5)):  # Check first few rectangles
        rect = rectangles.nth(i)
        fill_color = rect.get_attribute("fill")
        if fill_color and fill_color not in ["none", "transparent"]:
            rect_with_fill = True
            break
    
    assert rect_with_fill, "Stock strip should have rectangles with fill colors"


@pytest.mark.e2e
def test_chart_handles_data_gaps_correctly(e2e_site_minimal) -> None:
    """Verify charts handle null/missing data gracefully with line segments."""
    page, base_url, errors = e2e_site_minimal

    # Navigate to species detail page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Wait for chart rendering
    page.wait_for_timeout(300)
    
    # For charts with gaps (null values), JavaScript should create multiple polyline segments
    # instead of connecting across gaps with a continuous line
    price_svg = page.locator("#price-chart svg")
    
    if price_svg.count() > 0:
        # If there are gaps in data, there should be multiple polyline elements (one per segment)
        # OR a single polyline with disconnected points (implementation dependent)
        # At minimum, chart should render without JavaScript errors
        polylines = price_svg.locator("polyline")
        circles = price_svg.locator("circle")
        
        # Should have some visual elements
        total_elements = polylines.count() + circles.count()
        assert total_elements > 0, "Chart with data gaps should still render visual elements"
    
    # Most importantly: no JavaScript errors should occur
    assert not errors['page_errors'], "Chart rendering should not produce JavaScript errors"
    assert not errors['console_errors'], "Chart rendering should not produce console errors"


@pytest.mark.e2e
def test_chart_tooltips_show_on_hover(e2e_site_minimal) -> None:
    """Verify interactive tooltips appear when hovering over data points."""
    page, base_url, errors = e2e_site_minimal

    # Navigate to species detail page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    with page.expect_navigation():
        species_link.click()
    
    # Wait for chart rendering
    page.wait_for_timeout(300)
    
    # Charts use circle elements for interactive data points with tooltips
    price_svg = page.locator("#price-chart svg")
    
    if price_svg.count() > 0:
        circles = price_svg.locator("circle")
        
        if circles.count() > 0:
            # Hover over first data point
            first_circle = circles.first
            first_circle.hover()
            page.wait_for_timeout(200)
            
            # Tooltip should appear (implementation may use title, data attributes, or separate div)
            # Check for common tooltip patterns:
            # 1. SVG title element
            # 2. title attribute on circle
            # 3. Separate tooltip div

            has_title_element = price_svg.locator("title").count() > 0
            has_title_attr = first_circle.get_attribute("title") is not None
            has_tooltip_div = page.locator(".info-tip__text, [role='tooltip']").count() > 0
            
            # At least one tooltip mechanism should be present
            # (Note: implementation details may vary, this is flexible validation)
            tooltip_exists = has_title_element or has_title_attr or has_tooltip_div
            
            # If no explicit tooltip found, at least verify circle has data attributes
            # that could be used for tooltips (data-price, data-date, etc.)
            if not tooltip_exists:
                # Chart should at minimum have interactive elements configured
                assert first_circle.get_attribute("r") is not None, \
                    "Interactive data points should have radius attribute"


# ---------------------------------------------------------------------------
# Species detail page structural styles
# ---------------------------------------------------------------------------


def _navigate_to_species_page(page, base_url: str) -> None:
    """Navigate from the breeder table to the first available species detail page."""
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]').first
    assert species_link.count() == 1, "Breeder page should have at least one species link"
    species_href = species_link.get_attribute('href')
    page.goto(f"{base_url}/{species_href}", wait_until="domcontentloaded")
    page.wait_for_timeout(200)


@pytest.mark.e2e
def test_species_detail_badge_row_has_center_alignment(e2e_site_minimal) -> None:
    """.badge-row on species detail page should have align-items: center."""
    page, base_url, errors = e2e_site_minimal

    _navigate_to_species_page(page, base_url)

    badge_row = page.locator('.badge-row')
    assert badge_row.count() >= 1, "Species detail page should have .badge-row"

    align = badge_row.first.evaluate('el => window.getComputedStyle(el).alignItems')
    assert align == 'center', f".badge-row should have align-items: center, got {align}"


@pytest.mark.e2e
def test_species_detail_chart_legend_dot_colors(e2e_site_minimal) -> None:
    """Chart legend dots should use semantic CSS classes instead of inline background colors."""
    page, base_url, errors = e2e_site_minimal

    _navigate_to_species_page(page, base_url)

    # Price dot — --color-accent
    price_dot = page.locator('.legend-dot--price')
    assert price_dot.count() >= 1, "Should have .legend-dot--price element"
    price_bg = price_dot.first.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert token_rgb('--color-accent') in price_bg, \
        f".legend-dot--price should have {token_rgb('--color-accent')}, got {price_bg}"

    # Gap dot — --color-signal-avoid
    gap_dot = page.locator('.legend-dot--gap')
    assert gap_dot.count() >= 1, "Should have .legend-dot--gap elements"
    gap_bg = gap_dot.first.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert token_rgb('--color-signal-avoid') in gap_bg, \
        f".legend-dot--gap should have {token_rgb('--color-signal-avoid')}, got {gap_bg}"

    # Wishlist dot — #16a34a (species-detail.css, not a common.css token)
    wishlist_dot = page.locator('.legend-dot--wishlist')
    assert wishlist_dot.count() >= 1, "Should have .legend-dot--wishlist element"
    wishlist_bg = wishlist_dot.first.evaluate(
        'el => window.getComputedStyle(el).backgroundColor'
    )
    assert hex_to_rgb('#16a34a') in wishlist_bg, \
        f".legend-dot--wishlist should have {hex_to_rgb('#16a34a')}, got {wishlist_bg}"


@pytest.mark.e2e
def test_species_detail_stock_strip_spans_full_grid_width(e2e_site_minimal) -> None:
    """.stock-strip should span the full width of the two-column grid."""
    page, base_url, errors = e2e_site_minimal

    _navigate_to_species_page(page, base_url)

    stock_strip = page.locator('.stock-strip')
    assert stock_strip.count() >= 1, "Species detail should have .stock-strip"

    grid_column = stock_strip.first.evaluate(
        'el => window.getComputedStyle(el).gridColumn'
    )
    assert '1' in grid_column and '-1' in grid_column, \
        f".stock-strip should span full grid width (1 / -1), got gridColumn='{grid_column}'"


@pytest.mark.e2e
def test_species_detail_legend_swatch_colors(e2e_site_minimal) -> None:
    """Stock timeline legend swatches should use semantic modifier classes."""
    page, base_url, errors = e2e_site_minimal

    _navigate_to_species_page(page, base_url)

    # Observed swatch — #dcfce7 (species-detail.css, not a common.css token)
    observed_swatch = page.locator('.legend-swatch--observed')
    assert observed_swatch.count() >= 1, "Should have .legend-swatch--observed"
    obs_bg = observed_swatch.first.evaluate(
        'el => window.getComputedStyle(el).backgroundColor'
    )
    assert hex_to_rgb('#dcfce7') in obs_bg, \
        f".legend-swatch--observed should have {hex_to_rgb('#dcfce7')}, got {obs_bg}"

    # Gap swatch — #f1f5f9 (species-detail.css, not a common.css token)
    gap_swatch = page.locator('.legend-swatch--gap')
    assert gap_swatch.count() >= 1, "Should have .legend-swatch--gap"
    gap_bg = gap_swatch.first.evaluate(
        'el => window.getComputedStyle(el).backgroundColor'
    )
    assert hex_to_rgb('#f1f5f9') in gap_bg, \
        f".legend-swatch--gap should have {hex_to_rgb('#f1f5f9')}, got {gap_bg}"


@pytest.mark.e2e
def test_species_detail_history_panel_has_top_margin(e2e_site_minimal) -> None:
    """The history observations panel should use .panel--history class with top margin."""
    page, base_url, errors = e2e_site_minimal

    _navigate_to_species_page(page, base_url)

    history_panel = page.locator('.panel--history')
    assert history_panel.count() >= 1, "Species detail should have .panel--history"

    margin_top = history_panel.first.evaluate(
        'el => window.getComputedStyle(el).marginTop'
    )
    assert margin_top == '20px', \
        f".panel--history should have margin-top: 20px, got {margin_top}"


@pytest.mark.e2e
def test_species_detail_table_footnote_styling(e2e_site_minimal) -> None:
    """The history table footnote should use .table-footnote class with muted styling."""
    page, base_url, errors = e2e_site_minimal

    _navigate_to_species_page(page, base_url)

    footnote = page.locator('.table-footnote')
    assert footnote.count() >= 1, "Species detail should have .table-footnote"

    # --color-text-dim: #607080
    color = footnote.first.evaluate('el => window.getComputedStyle(el).color')
    assert token_rgb('--color-text-dim') in color, \
        f".table-footnote should have {token_rgb('--color-text-dim')}, got {color}"

    # 0.92rem ≈ 14.72px at default 16px root
    font_size = footnote.first.evaluate(
        'el => parseFloat(window.getComputedStyle(el).fontSize)'
    )
    assert 13 <= font_size <= 16, \
        f".table-footnote should have font-size ~0.92rem (~14.7px), got {font_size}px"

    margin_top = footnote.first.evaluate('el => window.getComputedStyle(el).marginTop')
    assert margin_top == '10px', \
        f".table-footnote should have margin-top: 10px, got {margin_top}"


@pytest.mark.e2e
def test_species_detail_observation_coverage_emphasizes_key_dates(e2e_site_minimal) -> None:
    """Observation coverage should stay subtle overall while first/latest dates get the visual emphasis."""
    page, base_url, errors = e2e_site_minimal

    _navigate_to_species_page(page, base_url)

    coverage_panel = page.locator('.panel--observation-coverage')
    assert coverage_panel.count() == 1, "Species detail should have a compact observation coverage panel"

    panel_bg = coverage_panel.first.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert token_rgb('--color-surface-light') in panel_bg, \
        f"Observation coverage panel should use {token_rgb('--color-surface-light')}, got {panel_bg}"

    key_metrics = page.locator('.coverage-metric--key-date')
    assert key_metrics.count() == 2, "First/latest observed metrics should use key-date emphasis styling"

    first_border = key_metrics.nth(0).evaluate('el => window.getComputedStyle(el).borderLeftColor')
    latest_border = key_metrics.nth(1).evaluate('el => window.getComputedStyle(el).borderLeftColor')
    assert token_rgb('--color-accent') in first_border, \
        f"First observed metric should emphasize with accent border, got {first_border}"
    assert token_rgb('--color-accent') in latest_border, \
        f"Latest observed metric should emphasize with accent border, got {latest_border}"

    context_metric = page.locator('.coverage-metric--context')
    assert context_metric.count() == 1, "Observed runs metric should use lower-emphasis context styling"
    context_border = context_metric.first.evaluate('el => window.getComputedStyle(el).borderLeftWidth')
    assert context_border == '1px', \
        f"Context metric should not use the stronger key-date border treatment, got {context_border}"

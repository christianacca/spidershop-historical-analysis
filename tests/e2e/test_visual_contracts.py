#!/usr/bin/env python3
"""Visual regression guard tests — G9.

These tests are intentionally minimal.  Each one asserts a single visual
contract that CSS depends on.  They exist to prevent a future migration step
from silently dropping a feature that the stylesheet expects.

Guarded contracts (one per fix):
- G1: Wishlist column non-empty (correct JSON key 'Wishlist' used)
- G2: Signal <td> cells carry .signal-hot / .signal-watch / .signal-avoid
- G3: Sparkline SVG bars present with explicit hex fill, not "currentColor"
- G3b: Sparkline SVG bar <rect> elements have per-bar tooltip <title> children
- G4: Info icon (ℹ️) present inside signal cells that have Drivers data
- G5: Column headers show ⇅ / ↑ / ↓ sort-indicator glyphs
- G6: Signal filter buttons include a parenthesised row count
- G7: Stat card .info-tip__text tooltip is visibility:hidden / position:absolute at rest
- H2: Price Trend column renders a non-empty value (key 'Price' in JSON)
"""

from __future__ import annotations

import re

import pytest

from e2e.fixtures import e2e_site_multi_species  # noqa: F401 – fixture registration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _go_breeder(page, base_url: str) -> None:
    """Navigate to breeder.html and wait for the table body to be ready."""
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.locator("#breeder-table tbody tr").first.wait_for(timeout=5000)


# ---------------------------------------------------------------------------
# G1 — Wishlist column non-empty
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_wishlist_column_not_empty(e2e_site_multi_species) -> None:
    """Wishlist column uses the correct JSON key ('Wishlist') so cells render non-empty values."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    headers = page.locator("#breeder-table thead th").all_text_contents()
    wishlist_idx = next(
        (i for i, h in enumerate(headers) if "Wishlist" in h),
        None,
    )
    assert wishlist_idx is not None, "No 'Wishlist' column found in breeder table headers"

    first_row_cells = page.locator("#breeder-table tbody tr").first.locator("td").all_text_contents()
    cell_text = first_row_cells[wishlist_idx].strip() if wishlist_idx < len(first_row_cells) else ""
    assert cell_text not in ("", "—"), (
        f"Wishlist cell is empty or placeholder; got: {cell_text!r}"
    )


# ---------------------------------------------------------------------------
# H2 — Price Trend column non-empty
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_price_trend_column_not_empty(e2e_site_multi_species) -> None:
    """Price Trend column renders a non-empty value (JSON key 'Price')."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    headers = page.locator("#breeder-table thead th").all_text_contents()
    # Strip sort-indicator glyphs (⇅/↑/↓) from header text before matching
    price_idx = next(
        (i for i, h in enumerate(headers) if h.replace("⇅", "").replace("↑", "").replace("↓", "").strip() == "Price Trend"),
        None,
    )
    assert price_idx is not None, "No 'Price Trend' column found in breeder table headers"

    first_row_cells = page.locator("#breeder-table tbody tr").first.locator("td").all_text_contents()
    cell_text = first_row_cells[price_idx].strip() if price_idx < len(first_row_cells) else ""
    assert cell_text not in ("", "—"), (
        f"Price Trend cell is empty or placeholder; got: {cell_text!r}"
    )


# ---------------------------------------------------------------------------
# G2 — Signal <td> CSS classes
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_signal_cells_have_css_class(e2e_site_multi_species) -> None:
    """Signal <td> cells carry .signal-hot, .signal-watch, or .signal-avoid so CSS can style them."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    signal_classes = {"signal-hot", "signal-watch", "signal-avoid"}
    rows = page.locator("#breeder-table tbody tr").all()
    assert rows, "No breeder table rows found"

    found_any = False
    for row in rows:
        cells = row.locator("td").all()
        for cell in cells:
            classes = (cell.get_attribute("class") or "").split()
            if signal_classes.intersection(classes):
                found_any = True
                break
        if found_any:
            break

    assert found_any, (
        "No <td> with .signal-hot / .signal-watch / .signal-avoid found in breeder table. "
        "CSS signal colouring will be broken."
    )


# ---------------------------------------------------------------------------
# G3 — Sparkline SVG uses explicit hex fill, not "currentColor"
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_sparkline_fill_is_not_currentColor(e2e_site_multi_species) -> None:
    """Sparkline SVG bars are present with explicit hex colours, not 'currentColor'.

    This contract is mechanism-agnostic: asserts that <rect> elements inside sparkline
    SVGs carry a hex fill, regardless of whether they were produced by unicodeToSvg or
    the DTO-based SparklineBar component.
    """
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    # SparklineBar renders <svg class="sparkline" ...> — the class is on the svg itself
    rects = page.locator("svg.sparkline rect")
    count = rects.count()
    assert count > 0, "No sparkline <rect> elements found inside svg.sparkline elements in breeder table"

    fills = set()
    for i in range(min(count, 20)):
        fill = rects.nth(i).get_attribute("fill") or ""
        if fill:
            fills.add(fill)

    assert "currentColor" not in fills, (
        "At least one sparkline element uses 'currentColor'; expected explicit hex colour."
    )
    assert any(f.startswith("#") for f in fills), (
        f"Expected at least one sparkline element with a hex fill, found: {fills}"
    )


# ---------------------------------------------------------------------------
# G3b — Sparkline bar <rect> elements have per-bar tooltip <title> children
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_sparkline_bar_has_tooltip(e2e_site_multi_species) -> None:
    """Each sparkline bar <rect> has a child <title> with a non-empty tooltip string.

    This guards the DTO pipeline: Python must emit tooltip strings and SparklineBar
    must render them as <title> children inside each <rect>.
    Price-history sparklines are checked because they always carry £ amounts.
    """
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    # Find a <rect> inside a svg.sparkline element on the breeder page
    first_rect = page.locator("svg.sparkline rect").first
    assert first_rect.count() > 0 or page.locator("svg.sparkline rect").count() > 0, (
        "No <rect> found inside svg.sparkline on breeder page"
    )

    # The rect must have a child <title> containing tooltip text
    title_child = first_rect.locator("title")
    assert title_child.count() > 0, (
        "No <title> child found inside sparkline <rect>; per-bar tooltips are missing"
    )
    tooltip_text = title_child.first.text_content() or ""
    assert tooltip_text.strip(), "Sparkline <rect> <title> child is empty"

    # Price-history sparklines must contain £ amounts
    rects_with_title = page.locator("svg.sparkline rect")
    found_price_tooltip = False
    for i in range(min(rects_with_title.count(), 30)):
        rect_title = rects_with_title.nth(i).locator("title")
        if rect_title.count() > 0:
            text = rect_title.first.text_content() or ""
            if "£" in text:
                found_price_tooltip = True
                break
    assert found_price_tooltip, (
        "No sparkline bar tooltip found containing '£'; "
        "price-history tooltips are missing from the breeder page"
    )


# ---------------------------------------------------------------------------
# G4 — Info icon inside signal cells
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_info_icon_present_for_signal_cells(e2e_site_multi_species) -> None:
    """Signal cells with Drivers data contain a .info-icon element."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    info_icons = page.locator("#breeder-table .info-tip")
    assert info_icons.count() > 0, (
        "No .info-tip found in the breeder table. "
        "Info-tip / Drivers tooltip feature is broken."
    )


# ---------------------------------------------------------------------------
# G5 — Sort indicator glyphs in column headers
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_sort_indicator_glyph_in_headers(e2e_site_multi_species) -> None:
    """All sortable column headers show ⇅ (or ↑/↓ after a click) indicator glyph."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    headers = page.locator("#breeder-table thead th").all_text_contents()
    assert headers, "No <th> elements found in breeder table"

    glyphs = {"⇅", "↑", "↓"}
    headers_with_glyph = [h for h in headers if any(g in h for g in glyphs)]
    assert len(headers_with_glyph) > 0, (
        f"No sort-indicator glyph (⇅/↑/↓) found in any header. Headers: {headers}"
    )


# ---------------------------------------------------------------------------
# G6 — Signal filter buttons include a parenthesised row count
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_filter_button_shows_row_count(e2e_site_multi_species) -> None:
    """Signal filter buttons (Show All, 🔥 Hot, …) include a parenthesised row count."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    # Signal filter buttons are rendered *outside* the <table> element by Svelte —
    # use the data-action attribute to select them reliably.
    filter_buttons = page.locator('.filter-btn[data-action="filter-signal"]').all()
    assert filter_buttons, "No .filter-btn[data-action='filter-signal'] elements found on breeder page"

    _row_count_re = re.compile(r"\(\d+\)")
    buttons_with_count = [
        btn.text_content() for btn in filter_buttons
        if _row_count_re.search(btn.text_content() or "")
    ]
    assert buttons_with_count, (
        "No signal filter button includes a parenthesised row count. "
        f"Button texts: {[b.text_content() for b in filter_buttons]}"
    )


# ---------------------------------------------------------------------------
# H3 — Stock Pattern and Search are inside the "More Filters" panel
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_stock_pattern_not_visible_initially(e2e_site_multi_species) -> None:
    """Stock Pattern filter buttons are hidden until "More Filters" is expanded."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    stock_btns = page.locator('button[data-action="filter-stock-pattern"]')
    assert stock_btns.count() == 0, (
        "Stock Pattern filter buttons should not be in the DOM before expanding More Filters"
    )


@pytest.mark.e2e
def test_search_not_visible_initially(e2e_site_multi_species) -> None:
    """Search input is hidden until 'More Filters' is expanded."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    search = page.locator(f"#search-breeder-table")
    assert search.count() == 0, (
        "Search input should not be in the DOM before expanding More Filters"
    )


@pytest.mark.e2e
def test_stock_pattern_visible_after_more_filters(e2e_site_multi_species) -> None:
    """Stock Pattern filter buttons appear after expanding 'More Filters'."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    page.locator(".advanced-filters-toggle").click()
    page.locator(".advanced-filters-content").wait_for(timeout=3000)

    stock_btns = page.locator('button[data-action="filter-stock-pattern"]')
    assert stock_btns.count() > 0, "Stock Pattern filter buttons should be visible after expanding More Filters"


@pytest.mark.e2e
def test_search_visible_after_more_filters(e2e_site_multi_species) -> None:
    """Search input appears after expanding 'More Filters'."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    page.locator(".advanced-filters-toggle").click()
    page.locator(".advanced-filters-content").wait_for(timeout=3000)

    search = page.locator("#search-breeder-table")
    assert search.count() > 0, "Search input should be visible after expanding More Filters"


@pytest.mark.e2e
def test_more_filters_button_in_signal_row(e2e_site_multi_species) -> None:
    """'More Filters' toggle button is located inside the signal filter row."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    # The toggle button must be a descendant of the signal .filter-section
    toggle_in_signal_row = page.locator(".filter-section .advanced-filters-toggle")
    assert toggle_in_signal_row.count() > 0, (
        "'.advanced-filters-toggle' should be inside '.filter-section' on breeder page"
    )


# ---------------------------------------------------------------------------
# H6 — Emoji prefix labels on filter rows
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_signal_filter_row_has_emoji_label(e2e_site_multi_species) -> None:
    """Signal filter row displays '🎯 Signal:' prefix label."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    signal_row = page.locator(".filter-section").first
    row_text = signal_row.text_content() or ""
    assert "🎯" in row_text, f"Expected '🎯' emoji in signal filter row, got: {row_text[:80]!r}"


@pytest.mark.e2e
def test_advanced_panel_has_stock_pattern_and_search_emoji_labels(e2e_site_multi_species) -> None:
    """After expanding More Filters, '📊 Stock Pattern:' and '🔍 Search:' labels are visible."""
    page, base_url, _errors = e2e_site_multi_species
    _go_breeder(page, base_url)

    page.locator(".advanced-filters-toggle").click()
    panel = page.locator(".advanced-filters-content")
    panel.wait_for(timeout=3000)

    panel_text = panel.text_content() or ""
    assert "📊" in panel_text, f"Expected '📊' emoji in advanced filters panel, got: {panel_text[:120]!r}"
    assert "🔍" in panel_text, f"Expected '🔍' emoji in advanced filters panel, got: {panel_text[:120]!r}"


# ---------------------------------------------------------------------------
# G7 — Stat card info-tip tooltip is hidden at rest
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.parametrize("page_path", ["breeder.html", "dealer.html"])
def test_stat_card_info_tip_hidden_at_rest(page_path, e2e_site_multi_species) -> None:
    """Stat card .info-tip__text tooltip has visibility:hidden and position:absolute at rest.

    Guards against a regression where the tooltip text rendered visibly inline because the
    CSS rule (defined in common.css) was not scoped broadly enough to reach Python-template HTML.
    """
    page, base_url, _errors = e2e_site_multi_species
    page.goto(f"{base_url}/{page_path}", wait_until="domcontentloaded")

    tooltip = page.locator(".stat-card .info-tip__text").first
    assert tooltip.count() > 0 or page.locator(".stat-card .info-tip__text").count() > 0, (
        f"No .stat-card .info-tip__text found on {page_path}"
    )

    visibility = tooltip.evaluate("el => window.getComputedStyle(el).visibility")
    position = tooltip.evaluate("el => window.getComputedStyle(el).position")

    assert visibility == "hidden", (
        f".stat-card .info-tip__text on {page_path} has visibility={visibility!r}, expected 'hidden'. "
        "Tooltip text is visible inline — CSS rule may not be applying to Python-template HTML."
    )
    assert position == "absolute", (
        f".stat-card .info-tip__text on {page_path} has position={position!r}, expected 'absolute'."
    )


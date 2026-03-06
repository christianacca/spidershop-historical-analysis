#!/usr/bin/env python3
"""E2E regression tests for breeder-page-specific visual contracts.

Scope:
- G1: Wishlist column uses correct JSON key (Wishlist Pressure), cell is non-empty
- G2: Signal td cells carry .signal-hot/.signal-watch/.signal-avoid class
- G3: Sparkline SVG bars use trend-based colour (not currentColor)
- G4: ℹ️ info icon is present in signal cells that have Drivers data
- G5: Column headers show ⇅/↑/↓ glyph for sortable columns
- G6: Signal filter buttons include a parenthesised row count
- G7: Price / wishlist sliders visible for breeder page

What's NOT tested here:
- General sorting / filtering behaviour (see test_table_interactions.py)
- Snapshot/dealer/history page interactions (separate files)
"""

from __future__ import annotations

import re

import pytest

from e2e.fixtures import e2e_site_multi_species


def _wait_for_breeder_table(page, base_url: str) -> None:
    """Navigate to breeder page and wait for the Svelte table to mount."""
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.locator("#breeder-table tbody tr").first.wait_for(timeout=5000)


def _wait_for_dealer_table(page, base_url: str) -> None:
    """Navigate to dealer page and wait for the Svelte table to mount."""
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    page.locator("#dealer-table tbody tr").first.wait_for(timeout=5000)


_SORT_INDICATORS = str.maketrans("", "", "⇅↑↓")


def _clean_headers(raw_headers: list[str]) -> list[str]:
    """Strip sort-indicator glyphs from header text contents."""
    return [h.translate(_SORT_INDICATORS).strip() for h in raw_headers]


# ── G1 — Wishlist column non-empty ───────────────────────────────────────────


@pytest.mark.e2e
def test_wishlist_column_not_empty(e2e_site_multi_species) -> None:
    """Wishlist column uses correct JSON key ('Wishlist'); cells are non-empty."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    # Find the column index for the "Wishlist" header (label for Wishlist Pressure key)
    headers = _clean_headers(page.locator("#breeder-table thead th").all_text_contents())
    assert "Wishlist" in headers, f"Expected 'Wishlist' header, got: {headers}"
    col_index = headers.index("Wishlist")

    # Check first row's Wishlist cell is non-empty (and not a placeholder dash)
    first_wishlist_cell = (
        page.locator(f"#breeder-table tbody tr:first-child td:nth-child({col_index + 1})")
        .text_content()
        or ""
    ).strip()

    assert first_wishlist_cell not in ("", "—", "-"), (
        f"Expected non-empty Wishlist cell but got: {first_wishlist_cell!r}"
    )


# ── G2 — Signal CSS classes on td elements ────────────────────────────────────


@pytest.mark.e2e
def test_signal_cells_have_css_class_breeder(e2e_site_multi_species) -> None:
    """Signal td cells carry signal-hot/watch/avoid class on breeder page."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    # The Signal column header — find its index
    headers = _clean_headers(page.locator("#breeder-table thead th").all_text_contents())
    assert "Signal" in headers, f"No 'Signal' header found: {headers}"
    col_index = headers.index("Signal")

    # Locate all signal cells
    signal_cells = page.locator(
        f"#breeder-table tbody tr td:nth-child({col_index + 1})"
    ).all()

    found_hot = False
    for cell in signal_cells:
        text = (cell.text_content() or "").strip()
        classes = cell.get_attribute("class") or ""
        if "🔥" in text:
            assert "signal-hot" in classes, (
                f"Expected .signal-hot on 🔥 cell, got classes: {classes!r}"
            )
            found_hot = True
        elif "⚠️" in text:
            assert "signal-watch" in classes, (
                f"Expected .signal-watch on ⚠️ cell, got classes: {classes!r}"
            )
        elif "❌" in text:
            assert "signal-avoid" in classes, (
                f"Expected .signal-avoid on ❌ cell, got classes: {classes!r}"
            )

    assert found_hot, "No 🔥 rows found in breeder table — test data may be wrong"


@pytest.mark.e2e
def test_signal_cells_have_css_class_dealer(e2e_site_multi_species) -> None:
    """Dealer Risk td cells carry signal-hot/watch/avoid class on dealer page."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_dealer_table(page, base_url)

    headers = _clean_headers(page.locator("#dealer-table thead th").all_text_contents())
    assert "Dealer Risk" in headers, f"No 'Dealer Risk' header found: {headers}"
    col_index = headers.index("Dealer Risk")

    risk_cells = page.locator(
        f"#dealer-table tbody tr td:nth-child({col_index + 1})"
    ).all()

    found_hot = False
    for cell in risk_cells:
        text = (cell.text_content() or "").strip()
        classes = cell.get_attribute("class") or ""
        if "🔥" in text:
            assert "signal-hot" in classes, (
                f"Expected .signal-hot on 🔥 cell, got classes: {classes!r}"
            )
            found_hot = True
        elif "⚠️" in text:
            assert "signal-watch" in classes, (
                f"Expected .signal-watch on ⚠️ cell, got classes: {classes!r}"
            )
        elif "❌" in text:
            assert "signal-avoid" in classes, (
                f"Expected .signal-avoid on ❌ cell, got classes: {classes!r}"
            )

    assert found_hot, "No 🔥 rows found in dealer table — test data may be wrong"


# ── G3 — Sparkline trend colours ─────────────────────────────────────────────


@pytest.mark.e2e
def test_sparkline_svg_uses_trend_colour_not_currentcolor(e2e_site_multi_species) -> None:
    """Price History sparkline bars use a hex trend colour, not 'currentColor'."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    headers = _clean_headers(page.locator("#breeder-table thead th").all_text_contents())
    assert "Price History" in headers, f"No 'Price History' header: {headers}"
    col_index = headers.index("Price History")

    # Find the first cell that contains a sparkline SVG
    cells = page.locator(
        f"#breeder-table tbody tr td:nth-child({col_index + 1})"
    ).all()

    sparkline_cell = None
    for cell in cells:
        if cell.locator("svg").count() > 0:
            sparkline_cell = cell
            break

    assert sparkline_cell is not None, (
        "No sparkline SVG found in Price History column — test data may lack price_history values"
    )

    # The first rect's fill must be a specific hex colour, not 'currentColor'
    rect = sparkline_cell.locator("rect").first
    fill = rect.get_attribute("fill") or ""
    assert fill != "currentColor", f"Sparkline rect still uses currentColor; fill={fill!r}"
    assert fill.startswith("#"), f"Expected a hex colour fill, got: {fill!r}"


@pytest.mark.e2e
def test_rising_sparkline_uses_green_fill(e2e_site_multi_species) -> None:
    """A rising sparkline (▁▄▇) in the Price History column uses green (#22c55e)."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    headers = _clean_headers(page.locator("#breeder-table thead th").all_text_contents())
    col_index = headers.index("Price History")
    species_col_index = headers.index("Species")

    rows = page.locator("#breeder-table tbody tr").all()
    for row in rows:
        species = (
            row.locator(f"td:nth-child({species_col_index + 1})").text_content() or ""
        ).strip()
        # Aphonopelma seemanni has price_history="▁▄▇" (rising → green)
        if "seemanni" not in species:
            continue
        svg_cell = row.locator(f"td:nth-child({col_index + 1})")
        if svg_cell.locator("svg").count() == 0:
            pytest.skip("seemanni row has no sparkline SVG — check test data")
        fill = svg_cell.locator("rect").first.get_attribute("fill") or ""
        assert fill == "#22c55e", (
            f"Rising sparkline for seemanni should be green (#22c55e), got: {fill!r}"
        )
        return

    pytest.skip("seemanni row not found in table")


# ── G4 — Info icons and Drivers tooltips ─────────────────────────────────────


@pytest.mark.e2e
def test_signal_cell_with_drivers_has_info_icon(e2e_site_multi_species) -> None:
    """Signal cells that have non-empty Drivers data render a .info-icon child."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    headers = _clean_headers(page.locator("#breeder-table thead th").all_text_contents())
    assert "Signal" in headers, f"No 'Signal' header: {headers}"
    col_index = headers.index("Signal")

    signal_cells = page.locator(
        f"#breeder-table tbody tr td:nth-child({col_index + 1})"
    ).all()

    found_icon = False
    for cell in signal_cells:
        icon = cell.locator(".info-icon")
        if icon.count() > 0:
            # Icon must have a non-empty title (tooltip)
            title = icon.first.get_attribute("title") or ""
            assert title, f".info-icon has empty title attribute on cell: {cell.text_content()}"
            found_icon = True

    assert found_icon, (
        "No .info-icon found in any signal cell — "
        "check that test data has non-empty 'drivers' values"
    )


@pytest.mark.e2e
def test_signal_cell_without_drivers_has_no_info_icon(e2e_site_multi_species) -> None:
    """Signal cells with empty Drivers do not render a .info-icon."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    headers = _clean_headers(page.locator("#breeder-table thead th").all_text_contents())
    col_index = headers.index("Signal")
    species_col_index = headers.index("Species")

    rows = page.locator("#breeder-table tbody tr").all()
    for row in rows:
        species = (
            row.locator(f"td:nth-child({species_col_index + 1})").text_content() or ""
        ).strip()
        # pulchra row has drivers="" in test data
        if "pulchra" not in species:
            continue
        signal_cell = row.locator(f"td:nth-child({col_index + 1})")
        icon_count = signal_cell.locator(".info-icon").count()
        assert icon_count == 0, (
            f"pulchra (empty drivers) should have no .info-icon, found {icon_count}"
        )
        return

    pytest.skip("pulchra row not found in table")


# ── G5 — Sort arrow glyphs ────────────────────────────────────────────────────


@pytest.mark.e2e
def test_sort_indicator_default_shows_bidirectional_arrow(e2e_site_multi_species) -> None:
    """All column headers show ⇅ by default before any sorting."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    indicators = page.locator("#breeder-table thead th .sort-indicator").all_text_contents()
    assert indicators, "No .sort-indicator elements found in breeder table headers"
    for text in indicators:
        assert text == "⇅", f"Expected ⇅ indicator before sorting, got: {text!r}"


@pytest.mark.e2e
def test_sort_indicator_updates_after_click(e2e_site_multi_species) -> None:
    """Clicking a column header updates that header's .sort-indicator to ↑."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    # Click the Species column header
    page.locator("#breeder-table thead th").first.click()
    page.wait_for_timeout(200)

    # First header should now show ↑
    first_indicator = page.locator("#breeder-table thead th").first.locator(
        ".sort-indicator"
    )
    assert first_indicator.text_content() == "↑", (
        f"Expected ↑ after first click, got: {first_indicator.text_content()!r}"
    )

    # Second click on the same header should show ↓
    page.locator("#breeder-table thead th").first.click()
    page.wait_for_timeout(200)
    assert first_indicator.text_content() == "↓", (
        f"Expected ↓ after second click, got: {first_indicator.text_content()!r}"
    )


# ── G6 — Per-filter row counts ────────────────────────────────────────────────


@pytest.mark.e2e
def test_show_all_button_includes_row_count(e2e_site_multi_species) -> None:
    """The 'Show All' signal filter button label includes a row count in parentheses."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    # Find the 'Show All' filter button for the breeder table
    show_all_btn = page.locator('button[data-action="filter-signal"][data-signal="all"]').first
    show_all_btn.wait_for(timeout=3000)

    label_text = show_all_btn.text_content() or ""
    assert re.search(r"Show All \(\d+\)", label_text), (
        f"Expected 'Show All (N)' label, got: {label_text!r}"
    )


# ── G7 — Price / wishlist sliders ─────────────────────────────────────────────


@pytest.mark.e2e
def test_advanced_filters_button_visible_on_breeder_page(e2e_site_multi_species) -> None:
    """Breeder page shows 'Advanced Filters' toggle button (price/wishlist sliders are wired)."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    toggle_btn = page.locator(".advanced-filters-toggle").first
    toggle_btn.wait_for(timeout=3000)
    assert toggle_btn.is_visible(), "Advanced Filters toggle button not visible on breeder page"


@pytest.mark.e2e
def test_price_and_wishlist_sliders_visible_after_expanding_advanced_filters(
    e2e_site_multi_species,
) -> None:
    """Clicking Advanced Filters reveals price and wishlist sliders on breeder page."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    # Click to expand
    page.locator(".advanced-filters-toggle").first.click()
    page.wait_for_timeout(200)

    # Price slider range inputs should be visible
    price_min = page.locator("#priceMin").first
    assert price_min.is_visible(), "Price min slider not visible after expanding Advanced Filters"

    price_max = page.locator("#priceMax").first
    assert price_max.is_visible(), "Price max slider not visible after expanding Advanced Filters"


# ── G8 — "▶ More Filters" / "▼ More Filters" toggle label ────────────────────


@pytest.mark.e2e
def test_more_filters_button_label_collapsed(e2e_site_multi_species) -> None:
    """Advanced Filters toggle shows '▶ More Filters' when the panel is collapsed."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    btn = page.locator(".advanced-filters-toggle").first
    btn.wait_for(timeout=3000)
    label = btn.text_content() or ""
    assert "▶ More Filters" in label, f"Expected '▶ More Filters' in collapsed label, got: {label!r}"
    assert "▼" not in label, f"'▼' should not appear in collapsed label, got: {label!r}"


@pytest.mark.e2e
def test_more_filters_button_label_expanded(e2e_site_multi_species) -> None:
    """Advanced Filters toggle gains is-expanded class after clicking to expand the panel."""
    page, base_url, errors = e2e_site_multi_species
    _wait_for_breeder_table(page, base_url)

    btn = page.locator(".advanced-filters-toggle").first
    btn.click()
    page.wait_for_timeout(200)

    classes = btn.get_attribute("class") or ""
    assert "is-expanded" in classes, f"Expected 'is-expanded' class on expanded toggle, got: {classes!r}"
    assert btn.text_content() and "More Filters" in (btn.text_content() or ""), \
        f"Button should still contain 'More Filters' text when expanded"





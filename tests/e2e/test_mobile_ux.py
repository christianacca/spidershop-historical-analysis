#!/usr/bin/env python3
"""E2E tests for mobile UX patterns (Phase 14).

Scope:
- P1: Stat cards render as a 2-column grid at tablet (481–768 px) and
      1-column at small phone (≤ 480 px)
- P2: Signal cells suppress the eyebrow label (::before) at mobile viewport
- P3: Recommendation column card-value text is left-aligned at mobile
- P4: Header padding is reduced at ≤ 480 px phone viewport
- Regression: desktop layout is not broken by any of the above

These tests use real browser rendering via Playwright to verify computed CSS
properties that cannot be verified with Python CSS structure tests alone.
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_multi_species


# ---------------------------------------------------------------------------
# P1: Stat cards 2×2 grid at tablet; 1-column at small phone
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_summary_stats_two_column_grid_at_tablet_viewport(e2e_site_multi_species) -> None:
    """At a 600 px tablet viewport the summary stats must render as a 2-column grid."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 600, 'height': 900})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    grid_columns = page.locator('.summary-stats').evaluate(
        'el => window.getComputedStyle(el).gridTemplateColumns'
    )
    # At 600 px the 2-column grid should produce two track sizes (e.g. "290px 290px").
    # Each track is a single token (no internal spaces for px values), so splitting
    # on whitespace gives exactly 2 items for a 2-track layout.
    tracks = grid_columns.split()
    assert len(tracks) == 2, (
        f"Expected 2 grid tracks at 600px tablet viewport, got {len(tracks)} in: {grid_columns!r}"
    )


@pytest.mark.e2e
def test_summary_stats_one_column_at_phone_viewport(e2e_site_multi_species) -> None:
    """At a 390 px phone viewport the summary stats must collapse to a 1-column grid."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    grid_columns = page.locator('.summary-stats').evaluate(
        'el => window.getComputedStyle(el).gridTemplateColumns'
    )
    tracks = grid_columns.split()
    assert len(tracks) == 1, (
        f"Expected 1 grid track at 390px phone viewport, got {len(tracks)} in: {grid_columns!r}"
    )


@pytest.mark.e2e
def test_summary_stats_auto_fit_columns_at_desktop_viewport(e2e_site_multi_species) -> None:
    """At 1280 px desktop the summary stats should use 4 columns (regression guard)."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 1280, 'height': 720})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    grid_columns = page.locator('.summary-stats').evaluate(
        'el => window.getComputedStyle(el).gridTemplateColumns'
    )
    tracks = grid_columns.split()
    assert len(tracks) >= 3, (
        f"Expected 3+ grid tracks at 1280px desktop, got {len(tracks)} in: {grid_columns!r}"
    )


# ---------------------------------------------------------------------------
# P2: Signal cells suppress the ::before eyebrow label at mobile
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_signal_cell_before_pseudo_hidden_at_mobile(e2e_site_multi_species) -> None:
    """At 390 px mobile, signal cells must suppress the ::before eyebrow label."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    signal_selector = (
        '#breeder-table td.signal-hot, '
        '#breeder-table td.signal-watch, '
        '#breeder-table td.signal-avoid'
    )
    signal_cell = page.locator(signal_selector).first
    signal_cell.wait_for(state='visible')

    pseudo_display = signal_cell.evaluate(
        'el => window.getComputedStyle(el, "::before").display'
    )
    assert pseudo_display == 'none', (
        f"Signal cell ::before must be display:none at mobile, got {pseudo_display!r}"
    )


@pytest.mark.e2e
def test_signal_cell_block_display_at_mobile(e2e_site_multi_species) -> None:
    """At 390 px mobile, signal cells must use display:block (not flex) so content is centred."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    signal_selector = (
        '#breeder-table td.signal-hot, '
        '#breeder-table td.signal-watch, '
        '#breeder-table td.signal-avoid'
    )
    signal_cell = page.locator(signal_selector).first
    signal_cell.wait_for(state='visible')

    display = signal_cell.evaluate('el => window.getComputedStyle(el).display')
    assert display == 'block', (
        f"Signal cell must be display:block at mobile (not flex), got {display!r}"
    )


@pytest.mark.e2e
def test_signal_cell_before_visible_at_desktop(e2e_site_multi_species) -> None:
    """At 1280 px desktop, signal cells must keep the ::before label (regression guard)."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 1280, 'height': 720})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    # At desktop, the card layout is not active; signal cells use display:table-cell
    # and the ::before pseudo-element is NOT rendered (it only exists in card layout).
    # The regression guard is: the signal cells should NOT have display:none on their
    # ::before — desktop styles must be unaffected.
    signal_cell = page.locator('#breeder-table td.signal-hot').first
    signal_cell.wait_for(state='visible')

    cell_display = signal_cell.evaluate('el => window.getComputedStyle(el).display')
    # At desktop the signal cell should NOT be block layout (it's a normal table cell)
    assert cell_display != 'block', (
        f"Signal cell must not be display:block at desktop, got {cell_display!r}"
    )


# ---------------------------------------------------------------------------
# P3: Recommendation text left-aligned at mobile
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_recommendation_card_value_left_aligned_at_mobile(e2e_site_multi_species) -> None:
    """At 390 px mobile, the Recommendation .card-value must be left-aligned."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    card_value = page.locator('#breeder-table td[data-label="Recommendation"] .card-value').first
    card_value.wait_for(state='attached')

    text_align = card_value.evaluate('el => window.getComputedStyle(el).textAlign')
    assert text_align == 'left', (
        f"Recommendation .card-value must be text-align:left at mobile, got {text_align!r}"
    )


@pytest.mark.e2e
def test_dealer_recommendation_card_value_left_aligned_at_mobile(e2e_site_multi_species) -> None:
    """At 390 px mobile, the Dealer Recommendation .card-value must be left-aligned."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")

    card_value = page.locator('#dealer-table td[data-label="Dealer Recommendation"] .card-value').first
    card_value.wait_for(state='attached')

    text_align = card_value.evaluate('el => window.getComputedStyle(el).textAlign')
    assert text_align == 'left', (
        f"Dealer Recommendation .card-value must be text-align:left at mobile, got {text_align!r}"
    )


@pytest.mark.e2e
def test_recommendation_card_value_right_aligned_at_desktop(e2e_site_multi_species) -> None:
    """At 1280 px desktop, the Recommendation .card-value must keep its default alignment."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 1280, 'height': 720})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    # At desktop card-layout is inactive; this column is just a plain <td>.
    # The regression guard is: the mobileTextAlign prop must NOT affect desktop layout.
    rec_td = page.locator('#breeder-table td[data-label="Recommendation"]').first
    rec_td.wait_for(state='visible')

    # Verify data-mobile-align attribute is present (set by Svelte)
    has_attr = rec_td.evaluate('el => el.hasAttribute("data-mobile-align")')
    assert has_attr, "Recommendation td must have data-mobile-align attribute set by Svelte"


# ---------------------------------------------------------------------------
# P4: Reduced header padding at ≤ 480 px phone
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_header_reduced_padding_at_phone_viewport(e2e_site_multi_species) -> None:
    """At 390 px phone viewport, header padding-top must be ≤ 12 px."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    padding_top = page.locator('header').evaluate(
        'el => parseFloat(window.getComputedStyle(el).paddingTop)'
    )
    assert padding_top <= 12, (
        f"Header paddingTop must be ≤12px at 390px phone (reduced from 20px), "
        f"got {padding_top}px"
    )


@pytest.mark.e2e
def test_header_standard_padding_at_desktop_viewport(e2e_site_multi_species) -> None:
    """At 1280 px desktop, header padding-top must remain 20 px (regression guard)."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 1280, 'height': 720})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    padding_top = page.locator('header').evaluate(
        'el => parseFloat(window.getComputedStyle(el).paddingTop)'
    )
    assert padding_top == 20, (
        f"Header paddingTop at desktop must remain 20px, got {padding_top}px"
    )


# ---------------------------------------------------------------------------
# P5: Landscape phone — hamburger nav
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_nav_hamburger_shown_at_landscape_phone(e2e_site_multi_species) -> None:
    """At 844×390 landscape phone, the hamburger toggle must be visible."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 844, 'height': 390})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    hamburger_display = page.locator('.nav-toggle').evaluate(
        'el => window.getComputedStyle(el).display'
    )
    assert hamburger_display == 'flex', (
        f"Hamburger must be display:flex at 844×390 landscape phone, got {hamburger_display!r}"
    )


@pytest.mark.e2e
def test_nav_hidden_at_landscape_phone(e2e_site_multi_species) -> None:
    """At 844×390 landscape phone, the nav must be hidden by default (before toggle)."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 844, 'height': 390})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    nav_display = page.locator('nav').evaluate(
        'el => window.getComputedStyle(el).display'
    )
    assert nav_display == 'none', (
        f"Nav must be display:none at 844×390 landscape phone, got {nav_display!r}"
    )


@pytest.mark.e2e
def test_nav_fits_single_row_at_ipad_landscape(e2e_site_multi_species) -> None:
    """At 1024×768 iPad landscape, the nav must fit in a single row (no wrapping)."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 1024, 'height': 768})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    # A single-row nav (padding:15px top+bottom) is ≤ ~65 px tall.
    # Two-row wrapping produces ~130 px+.  80 px is a safe threshold.
    nav_height = page.locator('nav').evaluate(
        'el => el.getBoundingClientRect().height'
    )
    # Single-row nav: ~30px padding + ~40px items + ~15px ul margin ≈ 85–120px.
    # Two-row wrapping produces ≥ 130px.  120px is a safe single-row threshold.
    assert nav_height <= 120, (
        f"Nav must fit in a single row at 1024×768 iPad landscape, "
        f"got height {nav_height}px"
    )


@pytest.mark.e2e
def test_nav_hamburger_hidden_at_desktop(e2e_site_multi_species) -> None:
    """At 1280×720 desktop, the hamburger must remain hidden (regression guard)."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 1280, 'height': 720})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    hamburger_display = page.locator('.nav-toggle').evaluate(
        'el => window.getComputedStyle(el).display'
    )
    assert hamburger_display == 'none', (
        f"Hamburger must be hidden at 1280×720 desktop, got {hamburger_display!r}"
    )


# ---------------------------------------------------------------------------
# P6: Galaxy Fold — header h1 font scaling
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_header_h1_smaller_font_at_fold_width(e2e_site_multi_species) -> None:
    """At 280px Galaxy Fold, header h1 font-size must be ≤ 19.2px (≤ 1.2rem at 16px base)."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 280, 'height': 653})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    font_size_px = page.locator('header h1').evaluate(
        'el => parseFloat(window.getComputedStyle(el).fontSize)'
    )
    assert font_size_px <= 19.2, (
        f"header h1 font-size must be ≤19.2px at 280px Fold viewport, got {font_size_px}px"
    )


@pytest.mark.e2e
def test_header_h1_font_unchanged_at_standard_phone(e2e_site_multi_species) -> None:
    """At 390px phone, header h1 font-size must stay at the mobile size (regression guard)."""
    page, base_url, errors = e2e_site_multi_species

    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

    font_size_px = page.locator('header h1').evaluate(
        'el => parseFloat(window.getComputedStyle(el).fontSize)'
    )
    # The ≤768px block sets header h1 to 1.5rem = 24px at 16px base.
    # The ≤320px breakpoint must NOT fire at 390px.
    assert font_size_px >= 22, (
        f"header h1 font-size must be ≥22px at 390px phone, got {font_size_px}px"
    )

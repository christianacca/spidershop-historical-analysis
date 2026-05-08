#!/usr/bin/env python3
"""E2E tests for the History Insights global filter panel (WP-Arch).

Scope:
- T1: Genus selection triggers MarketHealthSection heading update
- T2: Time window change updates the basis note and aria-pressed state
- T3: All-mode → narrow (select genera) → clear all restores all-mode scope label
- T4: Lifestyle preset (terrestrial) selects matching genera and shows chips

Data notes (multi-species fixture):
  Available genera: Aphonopelma, Brachypelma, Grammostola, Lasiodora, Psalmopoeus, Pterinochilus (6 total)
  Terrestrial preset matches: Aphonopelma, Brachypelma, Grammostola (3 of 6)

What's NOT tested here:
- KPI value accuracy (depends on fixture data — brittle)
- Visual styling of filter panel (covered by FiltersPanel.visual.test.ts)
- Complete GenusSelector state machine (covered by Vitest component tests)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_multi_species


def _navigate_to_insights(page, base_url: str) -> None:
    """Navigate to history-insights.html and wait for JS mount."""
    page.goto(f"{base_url}/history-insights.html", wait_until="networkidle")


def _expand_selector(page) -> None:
    """Click 'Show genus selector' to open the expandable suggestion area."""
    page.get_by_role("button", name="Show genus selector").click()


# ── T1 — Genus selection updates MarketHealthSection heading ─────────────────


@pytest.mark.e2e
def test_genus_selection_updates_market_health_heading(e2e_site_multi_species) -> None:
    """Selecting a genus updates the MarketHealthSection heading to genus-specific phrasing."""
    page, base_url, errors = e2e_site_multi_species

    _navigate_to_insights(page, base_url)

    # Initial heading is the all-mode question
    initial_heading_text = page.locator("#market-health-heading").text_content() or ""
    assert "wider tarantula market" in initial_heading_text, (
        f"Expected all-mode heading; got: {initial_heading_text!r}"
    )

    # Expand the genus selector
    _expand_selector(page)

    # Click the suggestion row for 'Aphonopelma'
    page.locator("button.suggestion-row").filter(has_text="Aphonopelma").first.click()

    # A chip for 'Aphonopelma' appears in the chips row
    chips_text = page.locator(".chips").text_content() or ""
    assert "Aphonopelma" in chips_text, (
        f"Expected 'Aphonopelma' chip after genus selection; chips text: {chips_text!r}"
    )

    # MarketHealthSection heading changes to genus-specific phrasing
    updated_heading = page.locator("#market-health-heading").text_content() or ""
    assert "Aphonopelma" in updated_heading, (
        f"Expected heading to mention 'Aphonopelma'; got: {updated_heading!r}"
    )


# ── T2 — Window change updates basis note ────────────────────────────────────


@pytest.mark.e2e
def test_window_change_updates_basis_note(e2e_site_multi_species) -> None:
    """Clicking 'All time' updates the basis note and sets aria-pressed='true'."""
    page, base_url, errors = e2e_site_multi_species

    _navigate_to_insights(page, base_url)

    # Click the 'All time' window pill button
    all_time_btn = page.get_by_role("button", name="All time")
    all_time_btn.click()

    # The two p.micro-note elements on this page are:
    #   [0] "Search or use shortcut groups..." (FiltersPanel genus group)
    #   [1] basis note from TimeWindowSelector
    basis_note_text = page.locator("p.micro-note").nth(1).text_content() or ""
    assert "structural context only" in basis_note_text, (
        f"Expected basis note to contain 'structural context only'; got: {basis_note_text!r}"
    )

    # 'All time' button has aria-pressed="true"
    aria_pressed = all_time_btn.get_attribute("aria-pressed")
    assert aria_pressed == "true", (
        f"Expected aria-pressed='true' on 'All time' button; got: {aria_pressed!r}"
    )


# ── T3 — All-mode → narrow → clear all ───────────────────────────────────────


@pytest.mark.e2e
def test_clear_all_reverts_to_all_mode(e2e_site_multi_species) -> None:
    """Selecting 4 genera then clicking Clear all restores the all-genera scope label."""
    page, base_url, errors = e2e_site_multi_species

    _navigate_to_insights(page, base_url)

    # Expand selector and select 4 genera.
    # With ≥4 genera, buildScopeLabel returns "your N selected genera".
    _expand_selector(page)
    for genus in ["Aphonopelma", "Brachypelma", "Grammostola", "Lasiodora"]:
        page.locator("button.suggestion-row").filter(has_text=genus).first.click()

    # Global scope label (inside .scope-inline) shows "your 4 selected genera"
    scope_text = page.locator(".scope-inline .scope-label").text_content() or ""
    assert "your 4 selected genera" in scope_text, (
        f"Expected 'your 4 selected genera' in scope label; got: {scope_text!r}"
    )

    # Click 'Clear all' (selector is still expanded; button is in the expanded-preview section)
    page.get_by_role("button", name="Clear all").click()

    # Global scope label reverts to all-genera format
    scope_text_after = page.locator(".scope-inline .scope-label").text_content() or ""
    assert "all genera" in scope_text_after, (
        f"Expected 'all genera' in scope label after Clear all; got: {scope_text_after!r}"
    )

    # .chips div is removed from DOM in all-mode (rendered only when !isAllSelected)
    assert page.locator(".chips").count() == 0, (
        "Expected no .chips element after Clear all (removed from DOM in all-mode)"
    )


# ── T4 — Lifestyle preset (terrestrial) ──────────────────────────────────────


@pytest.mark.e2e
def test_terrestrial_preset_selects_matching_genera(e2e_site_multi_species) -> None:
    """Clicking the Terrestrial preset selects genera matching the preset that are available.

    The multi-species fixture has 6 genera: Aphonopelma, Brachypelma, Grammostola,
    Lasiodora, Psalmopoeus, Pterinochilus.  The terrestrial preset list includes
    Aphonopelma, Brachypelma, and Grammostola — so 3 of 6 genera are selected.
    """
    page, base_url, errors = e2e_site_multi_species

    _navigate_to_insights(page, base_url)

    # Expand the selector (Terrestrial button lives in the expanded-preview section)
    _expand_selector(page)

    # Click the 'Terrestrial' quick-pick button
    page.get_by_role("button", name="Terrestrial").click()

    # Selector count label (inside .selector-shell) shows "3 of 5 genera selected"
    count_label_text = page.locator(".selector-shell .scope-label").text_content() or ""
    assert "3 of 6 genera selected" in count_label_text, (
        f"Expected '3 of 6 genera selected' in count label; got: {count_label_text!r}"
    )

    # Aphonopelma chip is present (it is always in the terrestrial preset)
    chips_text = page.locator(".chips").text_content() or ""
    assert "Aphonopelma" in chips_text, (
        f"Expected 'Aphonopelma' chip after Terrestrial preset; chips text: {chips_text!r}"
    )

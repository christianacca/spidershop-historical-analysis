#!/usr/bin/env python3
"""E2E tests for size-transition (lineage) affordances — plan Step 12.

Validates:
- Warning icons on Price / Price History cells for transition-affected species
- Tooltip text matches the Transition Message
- Transition banner on species detail page for confirmed-transition species
- No banner for a stable species
- Exactly one row per species (primary one-row-per-species regression guard)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_lineage

_TRANSITION_SPECIES = 'Chilobrachys sp. "South Thai"'
_STABLE_SPECIES = "Aphonopelma seemanni"
_TRANSITION_SPECIES_PAGE = "species/chilobrachys-sp.-south-thai.html"
_STABLE_SPECIES_PAGE = "species/aphonopelma-seemanni.html"
_TRANSITION_MESSAGE = (
    "Size changed from 3 cm to 5.0 cm on 2025-12-10. "
    "Price history may not be fully like-for-like across this transition."
)


def _get_price_cell(page, table_id: str, species_name: str):
    """Return the Price <td> for a given species row in the named table.

    Finds the column index of the Price header, then returns the <td> at that
    position in the row containing ``species_name``.
    """
    page.wait_for_selector(f"#{table_id} thead th", timeout=5000)
    headers = [
        h.strip()
        for h in page.locator(f"#{table_id} thead th").all_text_contents()
    ]
    price_idx = next(
        (i for i, h in enumerate(headers) if "Price" in h and "History" not in h),
        None,
    )
    assert price_idx is not None, f"Could not find Price column in {table_id}. Headers: {headers}"

    row = page.locator(f"#{table_id} tbody tr", has=page.locator("td", has_text=species_name))
    assert row.count() == 1, f"Expected exactly one row for '{species_name}' in {table_id}"

    return row.locator(f"td:nth-child({price_idx + 1})")


def _get_price_history_cell(page, table_id: str, species_name: str):
    """Return the Price History <td> for a given species row."""
    page.wait_for_selector(f"#{table_id} thead th", timeout=5000)
    headers = [
        h.strip()
        for h in page.locator(f"#{table_id} thead th").all_text_contents()
    ]
    ph_idx = next((i for i, h in enumerate(headers) if "Price History" in h), None)
    assert ph_idx is not None, f"Could not find Price History column in {table_id}. Headers: {headers}"

    row = page.locator(f"#{table_id} tbody tr", has=page.locator("td", has_text=species_name))
    assert row.count() == 1, f"Expected exactly one row for '{species_name}' in {table_id}"

    return row.locator(f"td:nth-child({ph_idx + 1})")


@pytest.mark.e2e
def test_one_row_per_species_in_breeder_table(e2e_site_lineage) -> None:
    """Breeder table must have exactly one row per species — no duplicate rows."""
    page, base_url, _errors = e2e_site_lineage

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.wait_for_selector("#breeder-table tbody tr", timeout=5000)
    rows = page.locator("#breeder-table tbody tr")
    assert rows.count() == 2, (
        f"Expected exactly 2 rows (one per species), got {rows.count()}"
    )

    all_species_texts = page.locator("#breeder-table tbody tr td:nth-child(1)").all_text_contents()
    unique_species = {t.strip() for t in all_species_texts}
    assert len(unique_species) == rows.count(), (
        f"Duplicate species rows found: {sorted(all_species_texts)}"
    )


@pytest.mark.e2e
def test_one_row_per_species_in_dealer_table(e2e_site_lineage) -> None:
    """Dealer table must have exactly one row per species — no duplicate rows."""
    page, base_url, _errors = e2e_site_lineage

    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    page.wait_for_selector("#dealer-table tbody tr", timeout=5000)
    rows = page.locator("#dealer-table tbody tr")
    assert rows.count() == 2, (
        f"Expected exactly 2 rows (one per species), got {rows.count()}"
    )


@pytest.mark.e2e
def test_price_cell_shows_warning_icon_for_transition_species(e2e_site_lineage) -> None:
    """Price cell must show a ℹ️ info-tip for a confirmed-transition species."""
    page, base_url, _errors = e2e_site_lineage

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.wait_for_selector("#breeder-table tbody tr", timeout=5000)

    price_td = _get_price_cell(page, "breeder-table", _TRANSITION_SPECIES)
    warning_icon = price_td.locator(".warning-tip")
    assert warning_icon.count() == 1, (
        f"Expected a .warning-tip in the Price cell for '{_TRANSITION_SPECIES}', found none"
    )


@pytest.mark.e2e
def test_price_history_cell_shows_warning_icon_for_transition_species(e2e_site_lineage) -> None:
    """Price History cell must also show a ℹ️ info-tip for a confirmed-transition species."""
    page, base_url, _errors = e2e_site_lineage

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.wait_for_selector("#breeder-table tbody tr", timeout=5000)

    ph_td = _get_price_history_cell(page, "breeder-table", _TRANSITION_SPECIES)
    warning_icon = ph_td.locator(".warning-tip")
    assert warning_icon.count() == 1, (
        f"Expected a .warning-tip in the Price History cell for '{_TRANSITION_SPECIES}', found none"
    )


@pytest.mark.e2e
def test_warning_icon_tooltip_text_matches_transition_message(e2e_site_lineage) -> None:
    """The tooltip text inside the warning icon must equal the Transition Message value."""
    page, base_url, _errors = e2e_site_lineage

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.wait_for_selector("#breeder-table tbody tr", timeout=5000)

    price_td = _get_price_cell(page, "breeder-table", _TRANSITION_SPECIES)
    tooltip_text = price_td.locator(".warning-tip__text").text_content().strip()
    assert tooltip_text == _TRANSITION_MESSAGE, (
        f"Tooltip text mismatch.\n  Expected: {_TRANSITION_MESSAGE!r}\n  Got:      {tooltip_text!r}"
    )


@pytest.mark.e2e
def test_no_warning_icon_for_stable_species(e2e_site_lineage) -> None:
    """Price and Price History cells for a standard species must have no warning icon."""
    page, base_url, _errors = e2e_site_lineage

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.wait_for_selector("#breeder-table tbody tr", timeout=5000)

    price_td = _get_price_cell(page, "breeder-table", _STABLE_SPECIES)
    assert price_td.locator(".warning-tip").count() == 0, (
        f"Stable species '{_STABLE_SPECIES}' Price cell should not show a warning icon"
    )

    ph_td = _get_price_history_cell(page, "breeder-table", _STABLE_SPECIES)
    assert ph_td.locator(".warning-tip").count() == 0, (
        f"Stable species '{_STABLE_SPECIES}' Price History cell should not show a warning icon"
    )


@pytest.mark.e2e
def test_transition_banner_shown_on_species_detail_for_confirmed_transition(e2e_site_lineage) -> None:
    """Species detail page for a confirmed-transition species must show the transition banner."""
    page, base_url, _errors = e2e_site_lineage

    page.goto(
        f"{base_url}/{_TRANSITION_SPECIES_PAGE}",
        wait_until="domcontentloaded",
    )

    banner = page.locator(".transition-banner")
    assert banner.count() == 1, (
        f"Expected exactly one .transition-banner for '{_TRANSITION_SPECIES}', found {banner.count()}"
    )

    banner_text = banner.locator(".transition-banner__text").text_content().strip()
    assert banner_text == _TRANSITION_MESSAGE, (
        f"Banner text mismatch.\n  Expected: {_TRANSITION_MESSAGE!r}\n  Got:      {banner_text!r}"
    )


@pytest.mark.e2e
def test_no_transition_banner_on_species_detail_for_stable_species(e2e_site_lineage) -> None:
    """Species detail page for a standard species must not show any transition banner."""
    page, base_url, _errors = e2e_site_lineage

    page.goto(
        f"{base_url}/{_STABLE_SPECIES_PAGE}",
        wait_until="domcontentloaded",
    )

    banner = page.locator(".transition-banner")
    assert banner.count() == 0, (
        f"Stable species '{_STABLE_SPECIES}' should have no .transition-banner, found {banner.count()}"
    )

#!/usr/bin/env python3
"""E2E checks for semantic observation significance states on species detail pages."""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_multi_species


def _navigate_to_species_page(page, base_url: str, species_name: str) -> None:
    """Navigate from the breeder table to a specific species detail page."""
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    species_link = page.locator('table a[href^="species/"]', has_text=species_name)
    assert species_link.count() == 1, f"Breeder page should link to {species_name}"
    species_href = species_link.get_attribute('href')
    page.goto(f"{base_url}/{species_href}", wait_until="domcontentloaded")
    page.wait_for_timeout(200)


@pytest.mark.e2e
def test_species_detail_observation_coverage_surfaces_significance_states(e2e_site_multi_species) -> None:
    """Newly observed species should surface semantic states without reverting to loud warning-card styling."""
    page, base_url, errors = e2e_site_multi_species

    _navigate_to_species_page(page, base_url, "Psalmopoeus irminia")

    new_metric = page.locator('.coverage-metric--new')
    assert new_metric.count() == 1, "Newly observed species should flag the first-observed metric as new"

    low_metric = page.locator('.coverage-metric--low')
    assert low_metric.count() == 1, "Sparse history should flag the coverage metric as low"

    stale_metric = page.locator('.coverage-metric--stale')
    assert stale_metric.count() == 0, "Current-run newly observed species should not be marked stale"

    metric_flags = page.locator('.coverage-metric__flag')
    assert metric_flags.count() == 2, "New and low-coverage observation states should render compact flags"

    first_flag_text = new_metric.first.locator('.coverage-metric__flag').inner_text().strip()
    coverage_flag_text = low_metric.first.locator('.coverage-metric__flag').inner_text().strip()
    assert first_flag_text.lower() == 'new', \
        f"Expected first-observed flag to be 'New', got {first_flag_text}"
    assert coverage_flag_text.lower() == 'low coverage', \
        f"Expected coverage flag to be 'Low coverage', got {coverage_flag_text}"

    new_border = new_metric.first.evaluate('el => window.getComputedStyle(el).borderLeftWidth')
    low_border = low_metric.first.evaluate('el => window.getComputedStyle(el).borderLeftWidth')
    assert new_border == '1px', f"New state should stay subtle rather than using a strong left border, got {new_border}"
    assert low_border == '1px', f"Low-coverage state should stay subtle rather than using a strong left border, got {low_border}"

    flag_transform = new_metric.first.locator('.coverage-metric__flag').evaluate(
        'el => window.getComputedStyle(el).textTransform'
    )
    assert flag_transform == 'none', f"Observation flags should use sentence case styling, got text-transform {flag_transform}"
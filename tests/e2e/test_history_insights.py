#!/usr/bin/env python3
"""E2E tests for the History Insights page.

Scope:
- Page loads successfully with correct title
- Market Health section renders (`.market-health-section` present)
- All 4 KPI cards are visible with non-empty metric values
- Events mini-grid is present (4 event tiles)
- `window.marketHealthRawData` is injected (not `marketHealthPayloads`)
- At least 4 SVG sparklines are rendered inside the section

What's NOT tested here:
- Exact KPI values (depend on fixture CSV data — brittle)
- Time window switching UI (not yet implemented in WP1)
- Run-selection interaction (covered by Vitest component tests)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_minimal


@pytest.mark.e2e
def test_page_loads(e2e_site_minimal) -> None:
    """history-insights.html loads without errors and has the expected title."""
    page, base_url, errors = e2e_site_minimal

    response = page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")
    assert response is not None and response.status == 200, (
        f"Expected HTTP 200 for history-insights.html, got {response.status if response else 'no response'}"
    )
    assert "History Insights" in page.title(), (
        f"Page title should contain 'History Insights'; got {page.title()!r}"
    )


@pytest.mark.e2e
def test_market_health_section_renders(e2e_site_minimal) -> None:
    """The .market-health-section container exists and all 4 KPI cards are present."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="networkidle")

    section = page.locator(".market-health-section")
    assert section.count() == 1, (
        "Expected exactly one .market-health-section element after JS mount"
    )

    kpi_cards = page.locator(".kpi-card")
    assert kpi_cards.count() == 4, (
        f"Expected 4 .kpi-card elements; got {kpi_cards.count()}"
    )


@pytest.mark.e2e
def test_kpi_values_are_non_empty(e2e_site_minimal) -> None:
    """Each KPI card's .metric-value must have non-empty text content.

    Confirms the engine computed a value — not a blank placeholder — for each KPI.
    """
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="networkidle")

    metric_values = page.locator(".metric-value").all_text_contents()
    assert len(metric_values) == 4, (
        f"Expected 4 .metric-value elements; got {len(metric_values)}"
    )
    for i, val in enumerate(metric_values):
        assert val.strip() != "", (
            f".metric-value[{i}] is empty — engine may have failed to compute a value"
        )


@pytest.mark.e2e
def test_events_grid_renders(e2e_site_minimal) -> None:
    """The events mini-grid is present with 4 event tiles visible."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="networkidle")

    event_tiles = page.locator(".event-tile")
    assert event_tiles.count() == 4, (
        f"Expected 4 .event-tile elements; got {event_tiles.count()}"
    )


@pytest.mark.e2e
def test_no_window_market_health_payloads(e2e_site_minimal) -> None:
    """The old window.marketHealthPayloads global must be absent.

    The new architecture uses window.marketHealthRawData instead — this test
    confirms the cutover is complete and the stale global was removed.
    """
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")

    old_global_type = page.evaluate("typeof window.marketHealthPayloads")
    assert old_global_type == "undefined", (
        f"window.marketHealthPayloads should be undefined after Phase 12 cutover; "
        f"got typeof = {old_global_type!r}"
    )

    new_global_type = page.evaluate("typeof window.marketHealthRawData")
    assert new_global_type == "object", (
        f"window.marketHealthRawData should be an object; got typeof = {new_global_type!r}"
    )


@pytest.mark.e2e
def test_sparklines_rendered(e2e_site_minimal) -> None:
    """At least 4 SVG sparklines are rendered inside the Market Health section."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="networkidle")

    svg_count = page.evaluate(
        "document.querySelectorAll('.market-health-section svg').length"
    )
    assert svg_count >= 4, (
        f"Expected at least 4 SVG elements inside .market-health-section; got {svg_count}"
    )

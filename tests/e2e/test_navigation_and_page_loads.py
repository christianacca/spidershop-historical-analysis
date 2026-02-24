#!/usr/bin/env python3
"""E2E tests for basic navigation and page loading.

Scope:
- All pages load without console errors or 404s
- Links between pages work correctly
- Assets (CSS, JS files) load successfully
- Basic navigation flows (breeder → species, dealer → species)

What's NOT tested here:
- JavaScript functionality (see test_table_interactions.py and test_species_page_interactions.py)
- Complex user interactions (filtering, sorting, tab switching)
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_minimal


@pytest.mark.e2e
def test_all_pages_load_without_errors(e2e_site_minimal) -> None:
    """Verify all HTML pages load, have correct titles, and have consistently styled header/footer."""
    page, base_url, errors = e2e_site_minimal

    pages_to_test = [
        ("index.html", "Spider Shop"),
        ("breeder.html", "Breeder Opportunities"),
        ("dealer.html", "Dealer Supply Risk"),
        ("snapshot.html", "Latest Snapshot"),
        ("history.html", "Historical Data"),
    ]

    for page_path, expected_title_fragment in pages_to_test:
        page.goto(f"{base_url}/{page_path}", wait_until="domcontentloaded")
        assert expected_title_fragment in page.title(), f"Page {page_path} has unexpected title"

        header = page.locator('header')
        assert header.count() == 1, f"{page_path} should have header element"
        # #2c3e50 = rgb(44, 62, 80)
        header_bg = header.evaluate('el => window.getComputedStyle(el).backgroundColor')
        assert 'rgb(44, 62, 80)' in header_bg, \
            f"{page_path} header should have dark background, got {header_bg}"
        header_color = header.evaluate('el => window.getComputedStyle(el).color')
        assert 'rgb(255, 255, 255)' in header_color or 'white' in header_color.lower(), \
            f"{page_path} header should have white text, got {header_color}"

        footer = page.locator('footer')
        assert footer.count() == 1, f"{page_path} should have footer element"


@pytest.mark.e2e
def test_navigation_from_breeder_to_species_detail(e2e_site_minimal) -> None:
    """Verify navigation from breeder table to species detail page works correctly."""
    page, base_url, errors = e2e_site_minimal

    # Navigate to breeder page
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    
    # Click first species link in table
    breeder_link = page.locator('table a[href^="species/"]').first
    assert breeder_link.count() == 1, "Expected at least one species link in breeder table"
    
    with page.expect_navigation():
        breeder_link.click()

    # Verify we're on a species detail page
    assert "/species/" in page.url, "Expected to navigate to species detail page"
    
    # Verify back buttons exist (this is basic structure, not testing highlight logic)
    assert page.locator("#back-breeder").count() == 1, "Expected breeder back button"
    assert page.locator("#back-dealer").count() == 1, "Expected dealer back button"


@pytest.mark.e2e
def test_navigation_from_dealer_to_species_detail(e2e_site_minimal) -> None:
    """Verify navigation from dealer table to species detail page works correctly."""
    page, base_url, errors = e2e_site_minimal

    # Navigate to dealer page
    page.goto(f"{base_url}/dealer.html", wait_until="domcontentloaded")
    
    # Click first species link in table
    dealer_link = page.locator('table a[href^="species/"]').first
    assert dealer_link.count() == 1, "Expected at least one species link in dealer table"
    
    with page.expect_navigation():
        dealer_link.click()

    # Verify we're on a species detail page
    assert "/species/" in page.url, "Expected to navigate to species detail page"
    
    # Verify back buttons exist
    assert page.locator("#back-breeder").count() == 1, "Expected breeder back button"
    assert page.locator("#back-dealer").count() == 1, "Expected dealer back button"


# ---------------------------------------------------------------------------
# Cross-page structural styles
# ---------------------------------------------------------------------------


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

        has_class = table.evaluate('el => el.classList.contains("data-table")')
        assert has_class, f"Table on {page_name} should have .data-table class"

        border_collapse = table.evaluate('el => window.getComputedStyle(el).borderCollapse')
        assert border_collapse == 'collapse', f"{page_name} table should have border-collapse:collapse"

        th_bg = page.locator(f'{table_id} thead th').first.evaluate(
            'el => window.getComputedStyle(el).backgroundColor'
        )
        assert th_bg != 'rgba(0, 0, 0, 0)' and th_bg != 'transparent', \
            f"{page_name} table headers should have background color"


# ---------------------------------------------------------------------------
# Homepage-specific styles
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_homepage_styling(e2e_site_minimal) -> None:
    """Homepage card grid, link/border colors, info-box, and disclaimer section should be correctly styled."""
    page, base_url, errors = e2e_site_minimal

    page.goto(f"{base_url}/index.html", wait_until="domcontentloaded")

    card_grid = page.locator('.card-grid')
    assert card_grid.count() == 1, "Homepage should have .card-grid container"
    display = card_grid.evaluate('el => window.getComputedStyle(el).display')
    assert display == 'grid', f"Card grid should use CSS grid, got display={display}"
    cards = page.locator('.card')
    assert cards.count() >= 4, f"Homepage should have at least 4 .card items, found {cards.count()}"
    border_radius = cards.first.evaluate('el => window.getComputedStyle(el).borderRadius')
    assert border_radius != '0px', f"Cards should have border-radius, got {border_radius}"

    # #3498db = rgb(52, 152, 219)
    card_link = page.locator('.card a').first
    link_color = card_link.evaluate('el => window.getComputedStyle(el).color')
    assert 'rgb(52, 152, 219)' in link_color, \
        f"Card links should be blue rgb(52,152,219), got {link_color}"
    # #e1e8ed = rgb(225, 232, 237)
    first_card = page.locator('.card').first
    border_color = first_card.evaluate('el => window.getComputedStyle(el).borderColor')
    assert 'rgb(225, 232, 237)' in border_color, \
        f"Card border should be rgb(225,232,237), got {border_color}"

    info_box = page.locator('.info-box')
    assert info_box.count() >= 1, "Homepage should have at least one .info-box"
    # #e8f4f8 = rgb(232, 244, 248)
    bg = info_box.first.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert 'rgb(232, 244, 248)' in bg, f"Info-box background should be light blue, got {bg}"
    # #3498db = rgb(52, 152, 219)
    border_left = info_box.first.evaluate('el => window.getComputedStyle(el).borderLeftColor')
    assert 'rgb(52, 152, 219)' in border_left, \
        f"Info-box left-border should be blue, got {border_left}"

    disclaimer = page.locator('.disclaimer')
    assert disclaimer.count() >= 1, "Homepage should have .disclaimer element"
    disclaimer_text = disclaimer.first.text_content()
    assert 'not affiliated' in disclaimer_text.lower(), \
        f".disclaimer should contain affiliation notice, got: {disclaimer_text[:80]}"

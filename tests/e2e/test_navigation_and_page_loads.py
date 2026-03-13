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

from e2e.css_tokens import token_rgb
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
        header_bg = header.evaluate('el => window.getComputedStyle(el).backgroundColor')
        assert token_rgb('--color-primary') in header_bg, \
            f"{page_path} header should have dark background (--color-primary), got {header_bg}"
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


@pytest.mark.e2e
def test_breeder_skeleton_present_before_js_and_removed_after_mount(e2e_site_minimal) -> None:
    """Breeder page should ship a server-rendered skeleton and remove it after mount."""
    page, base_url, errors = e2e_site_minimal

    page.route('**/breeder-page.js', lambda route: route.abort())
    try:
        page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

        skeleton = page.locator('[data-table-skeleton-for="breeder-table"]')
        assert skeleton.count() == 1, "Expected breeder skeleton in server-rendered HTML"
        assert page.locator('#breeder-table').count() == 0, "Table should not mount while page script is blocked"
    finally:
        page.unroute('**/breeder-page.js')

    page.goto(f"{base_url}/breeder.html", wait_until="networkidle")
    page.wait_for_function(
        """() => !document.querySelector('[data-table-skeleton-for="breeder-table"]')""",
        timeout=2000,
    )
    assert page.locator('[data-table-skeleton-for="breeder-table"]').count() == 0, (
        "Skeleton should be removed after the breeder table mounts"
    )
    assert page.locator('#breeder-table').count() == 1, "Mounted breeder table should be present"


@pytest.mark.e2e
def test_breeder_skeleton_has_visual_loading_contract_before_js(e2e_site_minimal) -> None:
    """Blocked-JS first paint should still show a table-shaped animated skeleton."""
    page, base_url, errors = e2e_site_minimal

    page.route('**/breeder-page.js', lambda route: route.abort())
    try:
        page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")

        skeleton = page.locator('[data-table-skeleton-for="breeder-table"]')
        assert skeleton.count() == 1, "Expected breeder skeleton in server-rendered HTML"

        contract = skeleton.evaluate(
            """(el) => {
                const firstHeader = el.querySelector('.table-skeleton__cell--header');
                const firstBody = el.querySelector('.table-skeleton__cell:not(.table-skeleton__cell--header)');
                const style = window.getComputedStyle(el);
                const bodyStyle = firstBody ? window.getComputedStyle(firstBody) : null;
                return {
                    minHeight: style.minHeight,
                    headerCount: el.querySelectorAll('.table-skeleton__cell--header').length,
                    rowCount: el.querySelectorAll('.table-skeleton__row').length,
                    animationName: bodyStyle?.animationName ?? null,
                    animationDuration: bodyStyle?.animationDuration ?? null,
                    backgroundImage: bodyStyle?.backgroundImage ?? null,
                    borderRadius: style.borderRadius,
                };
            }"""
        )

        assert contract['headerCount'] >= 6, f"Expected table-like header cells, got {contract['headerCount']}"
        assert contract['rowCount'] >= 8, f"Expected several placeholder rows, got {contract['rowCount']}"
        assert contract['animationName'] == 'table-skeleton-shimmer', (
            f"Expected shimmer animation, got {contract['animationName']}"
        )
        assert contract['animationDuration'] == '1.8s', (
            f"Expected 1.8s skeleton shimmer, got {contract['animationDuration']}"
        )
        assert contract['backgroundImage'] and contract['backgroundImage'] != 'none', (
            "Expected gradient background on skeleton cells"
        )
        assert contract['minHeight'] != '0px', "Expected reserved skeleton height before mount"
        assert contract['borderRadius'] != '0px', "Expected softened skeleton card edges"
    finally:
        page.unroute('**/breeder-page.js')


@pytest.mark.e2e
def test_breeder_skeleton_fades_before_it_is_removed(e2e_site_minimal) -> None:
    """The handoff should fade the skeleton out before the DOM node is removed."""
    page, base_url, errors = e2e_site_minimal

    page.add_init_script(
        """
        (() => {
          const nativeSetTimeout = window.setTimeout.bind(window);
                    const now = 40;
                    window.performance.now = () => now;
                    const queued = [];
                    window.__runNextSkeletonTimeout = (delay) => {
                        const index = queued.findIndex((entry) => entry.delay === delay);
                        if (index === -1) {
                            return false;
                        }

                        const [entry] = queued.splice(index, 1);
                        entry.callback();
                        return true;
                    };
          window.setTimeout = (callback, delay, ...args) => {
                                                if (delay === 480 || delay === 260) {
                            queued.push({ delay, callback: () => callback(...args) });
              return queued.length;
            }
            return nativeSetTimeout(callback, delay, ...args);
          };
        })();
        """
    )

    page.goto(f"{base_url}/breeder.html", wait_until="networkidle")

    skeleton = page.locator('[data-table-skeleton-for="breeder-table"]')
    assert skeleton.count() == 1, "Skeleton should still exist while delayed removal is intercepted"

    initial = page.locator('[data-table-shell="breeder-table"]').evaluate(
        """(el) => {
            const root = el.querySelector('#breeder-table-root');
            return {
                shellReady: el.getAttribute('data-table-ready'),
                rootOpacity: root ? window.getComputedStyle(root).opacity : null,
            };
        }"""
    )

    assert initial['shellReady'] == 'false', "Shell should stay in pre-ready state during minimum dwell"
    assert initial['rootOpacity'] == '0', "Mounted table should stay hidden until the cross-fade begins"

    assert page.evaluate('window.__runNextSkeletonTimeout(480)') is True, (
        "Expected queued dwell timer before the cross-fade begins"
    )
    page.evaluate(
        """() => new Promise((resolve) => {
            requestAnimationFrame(() => {
                requestAnimationFrame(resolve);
            });
        })"""
    )

    handoff = skeleton.evaluate(
        """(el) => {
            const style = window.getComputedStyle(el);
            const shell = document.querySelector('[data-table-shell="breeder-table"]');
            const root = document.querySelector('#breeder-table-root');
            return {
                shellReady: shell?.getAttribute('data-table-ready') ?? null,
                opacity: style.opacity,
                transitionProperty: style.transitionProperty,
                transitionDuration: style.transitionDuration,
                rootOpacity: root ? window.getComputedStyle(root).opacity : null,
                rootTransitionProperty: root ? window.getComputedStyle(root).transitionProperty : null,
                rootTransitionDuration: root ? window.getComputedStyle(root).transitionDuration : null,
            };
        }"""
    )

    assert handoff['shellReady'] == 'true', "Shell should be marked ready before the skeleton is removed"
    assert 'opacity' in handoff['transitionProperty'], (
        f"Expected opacity transition during handoff, got {handoff['transitionProperty']}"
    )
    assert handoff['transitionDuration'] == '0.26s', (
        f"Expected 0.26s fade duration, got {handoff['transitionDuration']}"
    )
    assert 'opacity' in handoff['rootTransitionProperty'], (
        f"Expected table root opacity transition during handoff, got {handoff['rootTransitionProperty']}"
    )
    assert handoff['rootTransitionDuration'] == '0.26s', (
        f"Expected table root fade-in duration, got {handoff['rootTransitionDuration']}"
    )
    assert 0 <= float(handoff['opacity']) <= 1, (
        f"Expected skeleton opacity to be in transition, got {handoff['opacity']}"
    )

    assert page.evaluate('window.__runNextSkeletonTimeout(260)') is True, (
        "Expected queued removal timer after the cross-fade begins"
    )
    assert page.locator('[data-table-skeleton-for="breeder-table"]').count() == 0, (
        "Skeleton should be removed after the fade-out completes"
    )


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

    card_link = page.locator('.card a').first
    link_color = card_link.evaluate('el => window.getComputedStyle(el).color')
    assert token_rgb('--color-accent') in link_color, \
        f"Card links should be --color-accent, got {link_color}"
    first_card = page.locator('.card').first
    border_color = first_card.evaluate('el => window.getComputedStyle(el).borderColor')
    assert token_rgb('--color-border-alt') in border_color, \
        f"Card border should be --color-border-alt, got {border_color}"

    info_box = page.locator('.info-box')
    assert info_box.count() >= 1, "Homepage should have at least one .info-box"
    bg = info_box.first.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert token_rgb('--color-info-bg') in bg, \
        f"Info-box background should be --color-info-bg, got {bg}"
    border_left = info_box.first.evaluate('el => window.getComputedStyle(el).borderLeftColor')
    assert token_rgb('--color-accent') in border_left, \
        f"Info-box left-border should be --color-accent, got {border_left}"

    disclaimer = page.locator('.disclaimer')
    assert disclaimer.count() >= 1, "Homepage should have .disclaimer element"
    disclaimer_text = disclaimer.first.text_content()
    assert 'not affiliated' in disclaimer_text.lower(), \
        f".disclaimer should contain affiliation notice, got: {disclaimer_text[:80]}"

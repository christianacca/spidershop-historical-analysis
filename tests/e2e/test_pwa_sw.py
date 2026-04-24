#!/usr/bin/env python3
"""E2E tests for the PWA service worker (WP-SW).

Scope:
- SW registration on all pages (via base.html) produces no errors
- SW activates and becomes the controller after initial page loads
- Precache manifest covers at least one hashed JS bundle
- HTML navigation routes land in the `html-pages` SWR cache
- `#sw-update-toast-root` mount point present on every page
- Update toast is hidden on fresh load (no waiting SW)
- Pages load and function correctly when SW is blocked (progressive enhancement)

Test isolation:
- SW tests live in their own module so they never contaminate other modules.
- All tests (except the SW-blocked test) share one browser context (module-scoped
  fixture). SW state accumulates across tests within this module; this is intentional
  — each test builds on the SW state established by the previous ones.
- The SW-blocked test creates its own browser context to isolate the `service_workers='block'`
  configuration.

What's NOT tested here:
- Update toast live two-version flow (requires serving two sequential builds; deferred
  to manual QA — see Phase 4 feed-forward log).
- Offline behaviour (requires Network panel manipulation; covered in manual QA).
"""

from __future__ import annotations

import pytest

from e2e.fixtures import e2e_site_minimal


@pytest.mark.e2e
def test_sw_toast_root_present_on_all_pages(e2e_site_minimal) -> None:
    """#sw-update-toast-root mount point exists on all main pages (base.html change)."""
    page, base_url, _ = e2e_site_minimal

    pages = ["index.html", "breeder.html", "history-insights.html"]
    for path in pages:
        page.goto(f"{base_url}/{path}", wait_until="domcontentloaded")
        mount_div = page.query_selector("#sw-update-toast-root")
        assert mount_div is not None, (
            f"#sw-update-toast-root not found on {path} — base.html change may not have propagated"
        )


@pytest.mark.e2e
def test_sw_registers_without_console_errors(e2e_site_minimal) -> None:
    """SW registration produces no 'SW registration failed' console warnings."""
    page, base_url, _ = e2e_site_minimal

    sw_warns: list[str] = []

    def on_console(msg):
        if msg.type in ("warning", "error"):
            sw_warns.append(msg.text)

    page.on("console", on_console)
    try:
        page.goto(f"{base_url}/history-insights.html", wait_until="load")
        # Wait for SW to finish registering — navigator.serviceWorker.ready resolves
        # only when an active SW exists. The SW registration script runs on 'load',
        # so waiting until load + SW ready confirms registration was attempted.
        page.evaluate("navigator.serviceWorker.ready")
    finally:
        page.remove_listener("console", on_console)

    failed = [w for w in sw_warns if "SW registration failed" in w]
    assert not failed, f"SW registration emitted failure messages: {failed}"


@pytest.mark.e2e
def test_sw_activates_after_two_navigations(e2e_site_minimal) -> None:
    """SW controller is non-null after two navigations (SW installed and active)."""
    page, base_url, _ = e2e_site_minimal

    # Navigate to a page within scope; preceding tests have already triggered SW
    # installation. This navigation is intercepted by the now-active SW.
    page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")

    # navigator.serviceWorker.ready resolves only when an active SW exists.
    # Using this instead of wait_for_timeout() for reliability.
    page.evaluate("navigator.serviceWorker.ready")

    controller_present = page.evaluate("navigator.serviceWorker.controller !== null")
    assert controller_present, (
        "Expected navigator.serviceWorker.controller to be non-null after two navigations "
        "(SW should be active and controlling page)"
    )


@pytest.mark.e2e
def test_precache_contains_hashed_js_bundle(e2e_site_minimal) -> None:
    """Workbox precache contains at least one hashed JS bundle entry."""
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")
    page.evaluate("navigator.serviceWorker.ready")

    precache_entry_count = page.evaluate("""
        async () => {
            const keys = await caches.keys();
            const precache = keys.find(k => k.startsWith('workbox-precache-v2-'));
            if (!precache) return 0;
            const cache = await caches.open(precache);
            const reqs = await cache.keys();
            // URLs may include ?__WB_REVISION__=... query params for unversioned files,
            // so use includes() not endsWith().
            return reqs.filter(r => r.url.includes('.js')).length;
        }
    """)
    assert precache_entry_count > 0, (
        f"Expected at least one hashed JS entry in workbox-precache-v2-* cache, got {precache_entry_count}"
    )


@pytest.mark.e2e
def test_html_page_cached_in_html_pages(e2e_site_minimal) -> None:
    """A navigated HTML page is present in the `html-pages` SWR cache."""
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")
    page.evaluate("navigator.serviceWorker.ready")

    cached = page.evaluate("""
        async () => {
            const cache = await caches.open('html-pages');
            const keys = await cache.keys();
            return keys.some(r => r.url.includes('history-insights.html'));
        }
    """)
    assert cached is True, (
        "Expected history-insights.html to be cached in the 'html-pages' SWR cache"
    )


@pytest.mark.e2e
def test_update_toast_hidden_on_fresh_load(e2e_site_minimal) -> None:
    """The SW update toast is not visible on a fresh load (no waiting SW)."""
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/index.html", wait_until="domcontentloaded")

    toast = page.query_selector(".sw-update-toast")
    assert toast is None, (
        "Expected .sw-update-toast to be absent from DOM on fresh load (no update pending)"
    )


@pytest.mark.e2e
def test_page_loads_with_sw_blocked(e2e_site_minimal) -> None:
    """Pages load and function correctly when SW is blocked (progressive enhancement)."""
    page, base_url, _ = e2e_site_minimal

    # Create a new browser context with service workers blocked.
    # We reuse the existing browser instance from the fixture (via page.context.browser)
    # to avoid starting a new sync_playwright() session inside the fixture's asyncio loop.
    ctx = page.context.browser.new_context(service_workers="block")
    try:
        blocked_page = ctx.new_page()
        blocked_page.set_default_timeout(5_000)
        blocked_page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")

        # Page should still render core content without SW
        title = blocked_page.title()
        assert title != "", "Expected page to have a title even with SW blocked"

        # SW guard in sw-toast-entry.ts must prevent mounting
        toast = blocked_page.query_selector(".sw-update-toast")
        assert toast is None, "Expected .sw-update-toast to be absent when SW is blocked"

        # SW must not be controlling the page
        controller = blocked_page.evaluate("navigator.serviceWorker.controller")
        assert controller is None, "Expected no SW controller when service workers are blocked"
    finally:
        ctx.close()

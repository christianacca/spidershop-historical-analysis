#!/usr/bin/env python3
"""E2E tests for View Transitions and Speculation Rules.

Scope:
- Inline classic script registers the pagereveal handler on every page (fires
  before DOMContentLoaded; a module script would miss the event)
- view-transitions-entry.js module is still loaded (exports pure functions for
  unit testing; the runtime behaviour is handled by the inline script)
- <script type="speculationrules"> block is present on all pages
- Speculation rules JSON is valid and matches expected prefetch config
- common.css contains the @view-transition { navigation: auto } opt-in rule
- No console errors introduced by the new entry point
"""

from __future__ import annotations

import json

import pytest

from e2e.fixtures import e2e_site_minimal


LISTING_PAGES = ["breeder.html", "dealer.html", "snapshot.html", "history.html"]
ALL_MAIN_PAGES = ["index.html"] + LISTING_PAGES


@pytest.mark.e2e
def test_view_transitions_script_present_on_all_pages(e2e_site_minimal) -> None:
    """view-transitions-entry.js is referenced on every page served by base.html."""
    page, base_url, _ = e2e_site_minimal

    for path in ALL_MAIN_PAGES:
        page.goto(f"{base_url}/{path}", wait_until="domcontentloaded")
        scripts = page.locator('script[src*="view-transitions-entry"]')
        assert scripts.count() >= 1, (
            f"view-transitions-entry.js not loaded on {path}"
        )
        src = scripts.first.get_attribute("src") or ""
        assert src.endswith("view-transitions-entry.js"), (
            f"Expected src ending in view-transitions-entry.js, got {src!r} on {path}"
        )


@pytest.mark.e2e
def test_speculation_rules_block_present_on_all_pages(e2e_site_minimal) -> None:
    """<script type='speculationrules'> is present on every page."""
    page, base_url, _ = e2e_site_minimal

    for path in ALL_MAIN_PAGES:
        page.goto(f"{base_url}/{path}", wait_until="domcontentloaded")
        rules = page.locator('script[type="speculationrules"]')
        assert rules.count() >= 1, (
            f"<script type='speculationrules'> not found on {path}"
        )


@pytest.mark.e2e
def test_speculation_rules_json_prefetches_species_links(e2e_site_minimal) -> None:
    """Speculation rules JSON targets species pages with moderate eagerness."""
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    raw = page.locator('script[type="speculationrules"]').first.inner_text()
    rules = json.loads(raw)

    assert "prefetch" in rules, "Expected 'prefetch' key in speculation rules"
    assert len(rules["prefetch"]) >= 1

    rule = rules["prefetch"][0]
    assert rule.get("source") == "document", (
        f"Expected source='document', got {rule.get('source')!r}"
    )
    assert rule.get("eagerness") == "moderate", (
        f"Expected eagerness='moderate', got {rule.get('eagerness')!r}"
    )
    where = rule.get("where", {})
    assert "species" in where.get("href_matches", ""), (
        f"Expected href_matches to target species pages, got: {where}"
    )


@pytest.mark.e2e
def test_view_transition_css_opt_in_present(e2e_site_minimal) -> None:
    """common.css contains the @view-transition { navigation: auto } opt-in rule."""
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    css_text = page.evaluate("() => fetch('./common.css').then(r => r.text())")

    assert "@view-transition" in css_text, (
        "common.css must contain @view-transition rule"
    )
    assert "navigation: auto" in css_text, (
        "common.css @view-transition rule must set navigation: auto"
    )


@pytest.mark.e2e
def test_no_console_errors_from_view_transitions_entry(e2e_site_minimal) -> None:
    """view-transitions-entry.js introduces no console errors on load."""
    page, base_url, errors = e2e_site_minimal

    errors["console_errors"].clear()
    page.goto(f"{base_url}/breeder.html", wait_until="networkidle")

    vt_errors = [e for e in errors["console_errors"] if "view-transition" in e.lower()]
    assert not vt_errors, f"Console errors related to view-transitions: {vt_errors}"


@pytest.mark.e2e
def test_view_transitions_script_present_on_species_pages(e2e_site_minimal) -> None:
    """view-transitions-entry.js and speculationrules are present on species detail pages.

    Species detail pages extend base.html so should inherit both script blocks.
    """
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/species/aphonopelma-seemanni.html", wait_until="domcontentloaded")

    scripts = page.locator('script[src*="view-transitions-entry"]')
    assert scripts.count() >= 1, "view-transitions-entry.js not loaded on species detail page"

    rules = page.locator('script[type="speculationrules"]')
    assert rules.count() >= 1, "<script type='speculationrules'> not found on species detail page"


@pytest.mark.e2e
def test_view_transition_css_reduced_motion_override(e2e_site_minimal) -> None:
    """common.css disables view transitions when prefers-reduced-motion is active.

    Accessibility requirement: users who prefer reduced motion must not see
    the slide animation triggered by VT.
    """
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    css_text = page.evaluate("() => fetch('./common.css').then(r => r.text())")

    assert "prefers-reduced-motion" in css_text, (
        "common.css must contain a prefers-reduced-motion media query for VT"
    )
    assert "navigation: none" in css_text, (
        "common.css must set navigation: none inside prefers-reduced-motion to disable VT"
    )


@pytest.mark.e2e
def test_view_transition_css_slide_keyframes_present(e2e_site_minimal) -> None:
    """common.css defines all four directional slide keyframes for VT animations."""
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    css_text = page.evaluate("() => fetch('./common.css').then(r => r.text())")

    for name in (
        "vt-slide-in-right",
        "vt-slide-out-right",
    ):
        assert f"@keyframes {name}" in css_text, (
            f"Missing @keyframes {name} in common.css"
        )


@pytest.mark.e2e
def test_view_transition_animation_duration(e2e_site_minimal) -> None:
    """VT slide animations use 0.3s duration — long enough to register direction.

    0.25s is too fast: the directional cue is lost as a blur.  0.3s gives the
    eye time to track the slide without feeling sluggish.
    """
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    css_text = page.evaluate("() => fetch('./common.css').then(r => r.text())")

    # All four animation declarations must use 0.3s, not 0.25s.
    assert "0.3s" in css_text, (
        "VT animations must use 0.3s duration (0.25s is too fast to register direction)"
    )
    assert "0.25s" not in css_text, (
        "Old 0.25s duration must be removed — update all four VT animation declarations"
    )


@pytest.mark.e2e
def test_view_transition_keyframe_translation_is_full_slide(e2e_site_minimal) -> None:
    """VT slide keyframes translate by 100% — full off-screen slide.

    The detail page enters from translateX(100%) and exits to translateX(100%).
    The listing page does not translate (animation: none keeps it stationary).
    This is the cover/uncover pattern: detail slides over a static listing.
    """
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    css_text = page.evaluate("() => fetch('./common.css').then(r => r.text())")

    assert "translateX(100%)" in css_text, (
        "VT keyframes must use translateX(100%) for a full off-screen slide"
    )
    # Left-direction keyframes are not used in cover/uncover pattern
    assert "translateX(-100%)" not in css_text, (
        "translateX(-100%) keyframes should not exist — cover/uncover only slides right"
    )
    # Partial translations should be gone
    assert "translateX(15%)" not in css_text, (
        "Old partial translateX(15%) must be removed"
    )
    assert "translateX(-15%)" not in css_text, (
        "Old partial translateX(-15%) must be removed"
    )


@pytest.mark.e2e
def test_view_transition_inline_handler_present(e2e_site_minimal) -> None:
    """An inline (non-module) <script> registers the pagereveal listener on every page.

    view-transitions-entry.js is a <script type="module"> which is deferred
    until after DOMContentLoaded.  But the pagereveal event fires BEFORE
    DOMContentLoaded.  The direction-detection logic (forward/backward type
    assignment) must therefore live in an inline classic script so it runs
    synchronously during HTML parsing — before pagereveal fires.
    """
    page, base_url, _ = e2e_site_minimal

    for path in ALL_MAIN_PAGES + ["species/aphonopelma-seemanni.html"]:
        page.goto(f"{base_url}/{path}", wait_until="domcontentloaded")

        # Find all inline (no src) non-module scripts
        inline_scripts = page.locator("script:not([type='module']):not([src]):not([type='speculationrules'])")
        contents = [
            inline_scripts.nth(i).inner_text()
            for i in range(inline_scripts.count())
        ]
        combined = "\n".join(contents)

        assert "pagereveal" in combined, (
            f"No inline non-module script containing 'pagereveal' found on {path}. "
            "The pagereveal handler must be in a classic script so it fires before DOMContentLoaded."
        )
        assert "vt.types.add" in combined or "types.add" in combined, (
            f"Inline pagereveal handler on {path} must call vt.types.add() to set direction type."
        )


@pytest.mark.e2e
def test_view_transition_animations_use_correct_easing(e2e_site_minimal) -> None:
    """VT cover animation uses ease-out for entry and ease-in for exit.

    Cover/uncover pattern: detail slides in with ease-out (fast start, soft
    landing) and exits with ease-in (gentle start, accelerating off-screen).
    The listing page has animation:none and does not need an easing value.
    """
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    css_text = page.evaluate("() => fetch('./common.css').then(r => r.text())")

    # Extract only the VT animation rules to avoid false positives from
    # other animations in the sheet (e.g. skeleton shimmer uses ease-in-out).
    import re
    vt_rules = "\n".join(
        m.group(0)
        for m in re.finditer(
            r"html:active-view-transition-type[^}]+\{[^}]+\}", css_text
        )
    )

    assert "ease-out" in vt_rules, (
        "Forward VT animation (detail entering) must use ease-out"
    )
    assert "ease-in" in vt_rules, (
        "Backward VT animation (detail exiting) must use ease-in"
    )
    assert "ease-in-out" not in vt_rules, (
        "VT cover/uncover rules must not use ease-in-out — asymmetric easing required"
    )


@pytest.mark.e2e
def test_no_horizontal_overflow_on_mobile_portrait(e2e_site_minimal) -> None:
    """Listing pages must not overflow horizontally at 390px mobile portrait.

    Root cause: .info-tip__text and .warning-tip__text use position:absolute
    and can extend beyond the layout viewport.  When scrollWidth > clientWidth
    on the SOURCE page, the browser's visual viewport widens to accommodate the
    overflow.  This causes a viewport size mismatch between the source and
    destination pages at transition time, breaking the cross-document VT slide
    animation on mobile portrait.

    Fix: .info-tip__text and .warning-tip__text use position:fixed at
    max-width: 768px in common.css.  Fixed elements are removed from document
    flow and do not contribute to scrollWidth.
    """
    page, base_url, _ = e2e_site_minimal

    # Create a new context at 390px mobile portrait using the same browser
    browser = page.context.browser
    mobile_ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
    )
    mobile_page = mobile_ctx.new_page()

    try:
        for path in LISTING_PAGES:
            mobile_page.goto(f"{base_url}/{path}", wait_until="load")
            # Wait for Svelte table to mount so tooltip elements are in the DOM
            mobile_page.wait_for_timeout(500)

            overflow = mobile_page.evaluate(
                """() => ({
                    scrollWidth: document.documentElement.scrollWidth,
                    clientWidth: document.documentElement.clientWidth,
                    innerWidth: window.innerWidth,
                })"""
            )
            assert overflow["scrollWidth"] <= overflow["clientWidth"], (
                f"{path} at 390px mobile portrait: "
                f"scrollWidth ({overflow['scrollWidth']}) > clientWidth ({overflow['clientWidth']}). "
                "Horizontal overflow breaks the view-transition slide on mobile. "
                "Hidden tooltip elements (position:absolute) are extending beyond the viewport. "
                "Fix: use position:fixed on .info-tip__text and .warning-tip__text at max-width: 768px in common.css."
            )
    finally:
        mobile_ctx.close()

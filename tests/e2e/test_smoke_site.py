#!/usr/bin/env python3
"""Playwright smoke tests for the generated static site.

These tests are intentionally small and coarse:
- ensure key pages load in a real browser
- ensure local CSS/JS assets do not 404
- ensure key navigation flows work (dealer/breeder -> species detail)

They are opt-in to avoid slowing down `make test`:
- run via `make test-e2e`
"""

from __future__ import annotations

import functools
import http.server
import os
import socketserver
import threading
from pathlib import Path

import pytest


def _write_minimal_inputs(cwd: Path) -> None:
    from conftest import HistoryEntry, BreederEntry, DealerEntry
    from conftest import create_history_csv_content, create_breeder_csv_content, create_dealer_csv_content
    
    # Snapshot CSV
    (cwd / "spidershop_spiderlings_scrape.csv").write_text(
        create_history_csv_content([
            HistoryEntry(
                scrape_datetime="2026-01-01",
                scientific_name="Aphonopelma seemanni",
                common_name="Costa Rican Zebra",
                price_gbp="25.00",
                wishlist_count="5"
            )
        ]),
        encoding="utf-8",
    )

    # History CSV
    (cwd / "spidershop_spiderlings_history.csv").write_text(
        create_history_csv_content([
            HistoryEntry(
                scrape_datetime="2025-12-25",
                scientific_name="Aphonopelma seemanni",
                common_name="Costa Rican Zebra",
                price_gbp="24.00",
                wishlist_count="4"
            ),
            HistoryEntry(
                scrape_datetime="2026-01-01",
                scientific_name="Aphonopelma seemanni",
                common_name="Costa Rican Zebra",
                price_gbp="25.00",
                wishlist_count="5"
            )
        ]),
        encoding="utf-8",
    )

    # Include Size (cm) so species pages can be generated.
    (cwd / "breeder_opportunity_table.csv").write_text(
        create_breeder_csv_content([
            BreederEntry(
                species="Aphonopelma seemanni",
                signal="🔥",
                oos_runs="4"
            )
        ]),
        encoding="utf-8",
    )
    (cwd / "dealer_supply_risk_table.csv").write_text(
        create_dealer_csv_content([
            DealerEntry(
                species="Aphonopelma seemanni",
                risk="⚠️",
                stock_reliability="Low",
                restock_speed="Slow"
            )
        ]),
        encoding="utf-8",
    )

    (cwd / "analysis_summary.md").write_text(
        "## 🧬 Breeder Opportunity Matrix (Top 10)\n\n"
        "**Summary:** 1 species analyzed | 🔥 Hot: 1 | ⚠️ Watch: 0 | ❌ Avoid: 0\n\n"
        "## 🏪 Dealer Supply Risk Matrix (Top 10)\n\n"
        "**Summary:** 1 species analyzed | 🔥 High Risk: 0 | ⚠️ Moderate Risk: 1 | ❌ Low Risk: 0\n",
        encoding="utf-8",
    )


def _write_multi_species_inputs(cwd: Path) -> None:
    """Write test data with multiple species for testing search filter."""
    from conftest import HistoryEntry, BreederEntry, DealerEntry
    from conftest import create_history_csv_content, create_breeder_csv_content, create_dealer_csv_content
    
    # Multiple species for filter testing
    history_entries = [
        HistoryEntry(
            scrape_datetime="2026-01-01",
            scientific_name="Aphonopelma seemanni",
            common_name="Costa Rican Zebra",
            price_gbp="25.00",
            wishlist_count="5"
        ),
        HistoryEntry(
            scrape_datetime="2026-01-01",
            scientific_name="Brachypelma hamorii",
            common_name="Mexican Red Knee",
            price_gbp="30.00",
            wishlist_count="8"
        ),
        HistoryEntry(
            scrape_datetime="2026-01-01",
            scientific_name="Grammostola pulchra",
            common_name="Brazilian Black",
            price_gbp="35.00",
            wishlist_count="12"
        ),
    ]
    
    (cwd / "spidershop_spiderlings_scrape.csv").write_text(
        create_history_csv_content(history_entries),
        encoding="utf-8",
    )
    (cwd / "spidershop_spiderlings_history.csv").write_text(
        create_history_csv_content(history_entries),
        encoding="utf-8",
    )
    
    (cwd / "breeder_opportunity_table.csv").write_text(
        create_breeder_csv_content([
            BreederEntry(
                species="Aphonopelma seemanni",
                signal="🔥",
                oos_runs="4"
            ),
            BreederEntry(
                species="Brachypelma hamorii",
                signal="⚠️",
                oos_runs="2"
            ),
            BreederEntry(
                species="Grammostola pulchra",
                signal="❌",
                oos_runs="0"
            ),
        ]),
        encoding="utf-8",
    )
    
    (cwd / "dealer_supply_risk_table.csv").write_text(
        create_dealer_csv_content([
            DealerEntry(
                species="Aphonopelma seemanni",
                risk="🔥",
                stock_reliability="Low",
                restock_speed="Slow"
            ),
            DealerEntry(
                species="Brachypelma hamorii",
                risk="⚠️",
                stock_reliability="Medium",
                restock_speed="Medium"
            ),
            DealerEntry(
                species="Grammostola pulchra",
                risk="❌",
                stock_reliability="High",
                restock_speed="Fast"
            ),
        ]),
        encoding="utf-8",
    )
    
    (cwd / "analysis_summary.md").write_text(
        "## 🧬 Breeder Opportunity Matrix (Top 10)\n\n"
        "**Summary:** 3 species analyzed | 🔥 Hot: 1 | ⚠️ Watch: 1 | ❌ Avoid: 1\n\n"
        "## 🏪 Dealer Supply Risk Matrix (Top 10)\n\n"
        "**Summary:** 3 species analyzed | 🔥 High Risk: 1 | ⚠️ Moderate Risk: 1 | ❌ Low Risk: 1\n",
        encoding="utf-8",
    )


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Keep test output clean.
        return


@pytest.mark.e2e
def test_site_smoke_breeder_and_dealer_detail_flows(request) -> None:
    if os.environ.get("RUN_E2E") != "1":
        pytest.skip("Playwright smoke tests are opt-in; run via `make test-e2e`.")

    playwright_sync = pytest.importorskip("playwright.sync_api")
    sync_playwright = playwright_sync.sync_playwright

    from website.generate_website import OUTPUT_DIR, main

    cwd = Path.cwd()
    _write_minimal_inputs(cwd)
    main()

    output_dir = (cwd / OUTPUT_DIR).resolve(strict=False)
    assert output_dir.exists(), "Expected website output directory to exist"

    handler = functools.partial(_SilentHandler, directory=str(output_dir))

    # Bind an ephemeral port.
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        base_url = f"http://127.0.0.1:{port}"

        # Support headed mode for debugging (PWHEADED=1 or --headed flag)
        headed = os.environ.get("PWHEADED") == "1" or request.config.getoption("--headed", default=False)
        slow_mo = int(os.environ.get("PWSLOW", "0"))  # milliseconds
        
        # Video recording for CI debugging (optional)
        video_dir = cwd / "tmp" / "e2e-videos" if os.environ.get("PWVIDEO") == "1" else None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not headed, slow_mo=slow_mo)
            context_options = {}
            if video_dir:
                video_dir.mkdir(parents=True, exist_ok=True)
                context_options["record_video_dir"] = str(video_dir)
            context = browser.new_context(**context_options)
            
            # Enable trace recording for debugging failures
            trace_path = cwd / "tmp" / "e2e-trace.zip"
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = context.new_page()

            console_errors: list[str] = []
            page_errors: list[str] = []
            bad_responses: list[str] = []

            def on_console(msg):
                # Only capture actual console.error() calls from JavaScript
                # Ignore browser resource loading messages
                if msg.type == "error" and not msg.text.startswith("Failed to load resource"):
                    console_errors.append(msg.text)

            def on_response(resp):
                url = resp.url
                if not url.startswith(base_url):
                    return
                if url.endswith("/favicon.ico"):
                    return
                if resp.status >= 400:
                    bad_responses.append(f"{resp.status} {url}")

            page.on("console", on_console)
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.on("response", on_response)

            # Basic load
            page.goto(f"{base_url}/index.html", wait_until="networkidle")
            assert "Spider Shop" in page.title()

            # Breeder -> species detail -> correct origin button highlighted
            page.goto(f"{base_url}/breeder.html", wait_until="networkidle")
            breeder_link = page.locator('table a[href^="species/"]').first
            assert breeder_link.count() == 1
            with page.expect_navigation():
                breeder_link.click()

            assert page.locator("#back-breeder").count() == 1
            assert page.locator("#back-dealer").count() == 1

            page.wait_for_function(
                "document.getElementById('back-breeder')?.classList.contains('origin-btn') === true"
            )
            assert page.eval_on_selector(
                "#back-breeder", "el => el.classList.contains('origin-btn')"
            )
            assert not page.eval_on_selector(
                "#back-dealer", "el => el.classList.contains('origin-btn')"
            )

            # Dealer -> species detail (via ?view=dealer) -> correct origin button highlighted
            page.goto(f"{base_url}/dealer.html", wait_until="networkidle")
            dealer_link = page.locator('table a[href^="species/"]').first
            assert dealer_link.count() == 1
            with page.expect_navigation():
                dealer_link.click()

            page.wait_for_function(
                "document.getElementById('back-dealer')?.classList.contains('origin-btn') === true"
            )
            assert page.eval_on_selector(
                "#back-dealer", "el => el.classList.contains('origin-btn')"
            )
            assert not page.eval_on_selector(
                "#back-breeder", "el => el.classList.contains('origin-btn')"
            )

            # Stop trace before closing context
            context.tracing.stop(path=str(trace_path))
            context.close()
            browser.close()

        httpd.shutdown()
        thread.join(timeout=2)

    # Keep trace on failure for debugging
    has_errors = page_errors or console_errors or bad_responses
    if has_errors:
        print(f"\n🔍 Trace saved to: {trace_path}")
        print(f"   View with: playwright show-trace {trace_path}")
    else:
        # Clean up trace on success
        trace_path.unlink(missing_ok=True)

    assert not page_errors, "Page errors:\n" + "\n".join(page_errors)
    assert not console_errors, "Console errors:\n" + "\n".join(console_errors)
    assert not bad_responses, "Bad local responses:\n" + "\n".join(bad_responses)


@pytest.mark.e2e
def test_search_filter_on_breeder_and_dealer_tables(request) -> None:
    """Test that the advanced search filter works on both breeder and dealer tables."""
    if os.environ.get("RUN_E2E") != "1":
        pytest.skip("Playwright smoke tests are opt-in; run via `make test-e2e`.")

    playwright_sync = pytest.importorskip("playwright.sync_api")
    sync_playwright = playwright_sync.sync_playwright

    from website.generate_website import OUTPUT_DIR, main

    cwd = Path.cwd()
    _write_multi_species_inputs(cwd)
    main()

    output_dir = (cwd / OUTPUT_DIR).resolve(strict=False)
    assert output_dir.exists(), "Expected website output directory to exist"

    handler = functools.partial(_SilentHandler, directory=str(output_dir))

    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        base_url = f"http://127.0.0.1:{port}"

        headed = os.environ.get("PWHEADED") == "1" or request.config.getoption("--headed", default=False)
        slow_mo = int(os.environ.get("PWSLOW", "0"))
        video_dir = cwd / "tmp" / "e2e-videos" if os.environ.get("PWVIDEO") == "1" else None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not headed, slow_mo=slow_mo)
            context_options = {}
            if video_dir:
                video_dir.mkdir(parents=True, exist_ok=True)
                context_options["record_video_dir"] = str(video_dir)
            context = browser.new_context(**context_options)
            
            trace_path = cwd / "tmp" / "e2e-trace-search.zip"
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = context.new_page()

            console_errors: list[str] = []
            page_errors: list[str] = []
            bad_responses: list[str] = []

            def on_console(msg):
                if msg.type == "error" and not msg.text.startswith("Failed to load resource"):
                    console_errors.append(msg.text)

            def on_response(resp):
                url = resp.url
                if not url.startswith(base_url):
                    return
                if url.endswith("/favicon.ico"):
                    return
                if resp.status >= 400:
                    bad_responses.append(f"{resp.status} {url}")

            page.on("console", on_console)
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.on("response", on_response)

            # TEST: Breeder page search filter
            page.goto(f"{base_url}/breeder.html", wait_until="networkidle")
            
            # Expand advanced filters
            advanced_toggle = page.locator(".advanced-filters-toggle")
            if advanced_toggle.count() > 0:
                advanced_toggle.click()
                page.wait_for_selector(".advanced-filters-content.show", timeout=2000)
            
            # All rows should be visible initially (3 species)
            visible_rows = page.locator("#breeder-table tbody tr:visible")
            assert visible_rows.count() == 3, "Expected 3 visible rows initially"
            
            # Type "Brachypelma" in search box
            search_input = page.locator("#search-breeder-table")
            assert search_input.count() == 1, "Search input should exist"
            search_input.type("Brachypelma")  # Use type() to trigger keyup events
            
            # Only 1 row should be visible (Brachypelma hamorii)
            page.wait_for_timeout(200)  # Small delay for filter to apply
            visible_rows = page.locator("#breeder-table tbody tr:visible")
            assert visible_rows.count() == 1, "Expected 1 visible row after filtering 'Brachypelma'"
            
            # Verify the correct species is visible
            visible_text = visible_rows.first.text_content()
            assert "Brachypelma hamorii" in visible_text, "Wrong species visible after filter"
            
            # Clear search - all rows should be visible again
            search_input.fill("")
            search_input.dispatch_event("keyup")  # Manually trigger keyup event
            page.wait_for_timeout(200)
            visible_rows = page.locator("#breeder-table tbody tr:visible")
            assert visible_rows.count() == 3, "Expected 3 visible rows after clearing filter"
            
            # TEST: Dealer page search filter
            page.goto(f"{base_url}/dealer.html", wait_until="networkidle")
            
            # Expand advanced filters
            advanced_toggle = page.locator(".advanced-filters-toggle")
            if advanced_toggle.count() > 0:
                advanced_toggle.click()
                page.wait_for_selector(".advanced-filters-content.show", timeout=2000)
            
            # All rows visible initially
            visible_rows = page.locator("#dealer-table tbody tr:visible")
            assert visible_rows.count() == 3, "Expected 3 visible rows initially on dealer page"
            
            # Search for "hamorii" (should match "Brachypelma hamorii")
            search_input = page.locator("#search-dealer-table")
            assert search_input.count() == 1, "Search input should exist on dealer page"
            search_input.type("hamorii")  # Use type() to trigger keyup events
            
            # Only 1 row should be visible
            page.wait_for_timeout(200)
            visible_rows = page.locator("#dealer-table tbody tr:visible")
            assert visible_rows.count() == 1, "Expected 1 visible row after filtering 'hamorii'"
            
            visible_text = visible_rows.first.text_content()
            assert "hamorii" in visible_text, "Wrong species visible after filter on dealer page"
            
            # Test case-insensitive search
            search_input.fill("")  # Clear first
            search_input.dispatch_event("keyup")
            page.wait_for_timeout(100)
            search_input.type("PULCHRA")  # UPPERCASE
            page.wait_for_timeout(200)
            visible_rows = page.locator("#dealer-table tbody tr:visible")
            assert visible_rows.count() == 1, "Expected 1 visible row for case-insensitive search"
            
            visible_text = visible_rows.first.text_content()
            assert "pulchra" in visible_text.lower(), "Case-insensitive search failed"

            context.tracing.stop(path=str(trace_path))
            context.close()
            browser.close()

        httpd.shutdown()
        thread.join(timeout=2)

    has_errors = page_errors or console_errors or bad_responses
    if has_errors:
        print(f"\n🔍 Trace saved to: {trace_path}")
        print(f"   View with: playwright show-trace {trace_path}")
    else:
        trace_path.unlink(missing_ok=True)

    assert not page_errors, "Page errors:\n" + "\n".join(page_errors)
    assert not console_errors, "Console errors:\n" + "\n".join(console_errors)
    assert not bad_responses, "Bad local responses:\n" + "\n".join(bad_responses)


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
    (cwd / "spidershop_spiderlings_scrape.csv").write_text(
        "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,2.0,25.00,5,https://example.com/a\n",
        encoding="utf-8",
    )

    (cwd / "spidershop_spiderlings_history.csv").write_text(
        "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        "2025-12-25,Aphonopelma seemanni,Costa Rican Zebra,2.0,24.00,4,https://example.com/a\n"
        "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,2.0,25.00,5,https://example.com/a\n",
        encoding="utf-8",
    )

    # Include Size (cm) so species pages can be generated.
    (cwd / "breeder_opportunity_table.csv").write_text(
        "Species,Size (cm),Signal,OOS Runs\n"
        "Aphonopelma seemanni,2.0,🔥,4\n",
        encoding="utf-8",
    )
    (cwd / "dealer_supply_risk_table.csv").write_text(
        "Species,Size (cm),Dealer Risk,Stock Reliability,Restock Speed\n"
        "Aphonopelma seemanni,2.0,⚠️,Low,Slow\n",
        encoding="utf-8",
    )

    (cwd / "analysis_summary.md").write_text(
        "## 🧬 Breeder Opportunity Matrix (Top 10)\n\n"
        "**Summary:** 1 species analyzed | 🔥 Hot: 1 | ⚠️ Watch: 0 | ❌ Avoid: 0\n\n"
        "## 🏪 Dealer Supply Risk Matrix (Top 10)\n\n"
        "**Summary:** 1 species analyzed | 🔥 High Risk: 0 | ⚠️ Moderate Risk: 1 | ❌ Low Risk: 0\n",
        encoding="utf-8",
    )


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Keep test output clean.
        return


@pytest.mark.e2e
def test_site_smoke_breeder_and_dealer_detail_flows() -> None:
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

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            console_errors: list[str] = []
            page_errors: list[str] = []
            bad_responses: list[str] = []

            def on_console(msg):
                if msg.type == "error":
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

            context.close()
            browser.close()

        httpd.shutdown()
        thread.join(timeout=2)

    assert not page_errors, "Page errors:\n" + "\n".join(page_errors)
    assert not console_errors, "Console errors:\n" + "\n".join(console_errors)
    assert not bad_responses, "Bad local responses:\n" + "\n".join(bad_responses)

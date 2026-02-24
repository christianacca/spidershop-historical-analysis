#!/usr/bin/env python3
"""Shared utilities for E2E tests using Playwright.

This module provides:
- Test data fixtures for different scenarios (minimal, multi-species, large tables)
- Browser setup with error capturing and trace recording
- HTTP server context manager for serving static sites
- Common assertions for browser errors

Design principles:
- Isolated: Each test gets fresh data and server instance
- Deterministic: Fixed test data, no randomness
- Fast: Minimal data sets, ephemeral ports
- High signal: Capture only meaningful errors (console.error, 4xx/5xx responses)
"""

from __future__ import annotations

import functools
import http.server
import os
import socketserver
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that doesn't log requests (keeps test output clean)."""
    
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


@contextmanager
def test_server(output_dir: Path):
    """Context manager that starts an HTTP server for the generated website.
    
    Args:
        output_dir: Path to the website directory to serve
        
    Yields:
        base_url: The URL to access the server (e.g., "http://127.0.0.1:54321")
    """
    handler = functools.partial(_SilentHandler, directory=str(output_dir))
    
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()
            thread.join(timeout=2)


def create_browser_with_error_capture(
    playwright,
    headed: bool = False,
    slow_mo: int = 0,
    video_dir: Path | None = None,
    trace_path: Path | None = None,
) -> tuple[Browser, BrowserContext, Page, dict]:
    """Create a Playwright browser with error capturing enabled.
    
    Args:
        playwright: Playwright instance from sync_playwright()
        headed: If True, show browser window (for debugging)
        slow_mo: Delay in ms between actions (for debugging)
        video_dir: If set, record video to this directory
        trace_path: If set, record trace to this file
        
    Returns:
        Tuple of (browser, context, page, error_storage)
        
        error_storage dict contains:
        - 'console_errors': List of console.error() messages
        - 'page_errors': List of JavaScript exceptions
        - 'bad_responses': List of HTTP errors (4xx/5xx from local server)
    """
    browser = playwright.chromium.launch(headless=not headed, slow_mo=slow_mo)

    # This is a static site served from localhost with no real async backend.
    # Playwright's default timeout is 30s, which slows down failures when selectors
    # are missing. Keep E2E feedback tight by using a shorter default.
    default_timeout_ms = 5_000
    
    context_options = {}
    if video_dir:
        video_dir.mkdir(parents=True, exist_ok=True)
        context_options["record_video_dir"] = str(video_dir)
    
    context = browser.new_context(**context_options)

    context.set_default_timeout(default_timeout_ms)
    context.set_default_navigation_timeout(default_timeout_ms)
    
    if trace_path:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
    
    page = context.new_page()

    page.set_default_timeout(default_timeout_ms)
    page.set_default_navigation_timeout(default_timeout_ms)
    
    # Error storage
    errors = {
        'console_errors': [],
        'page_errors': [],
        'bad_responses': []
    }
    
    def on_console(msg):
        # Only capture actual console.error() calls from JavaScript
        # Ignore browser resource loading messages
        if msg.type == "error" and not msg.text.startswith("Failed to load resource"):
            errors['console_errors'].append(msg.text)
    
    def on_pageerror(err):
        errors['page_errors'].append(str(err))
    
    def on_response(resp):
        # Only check responses from the test server (ignore external URLs)
        # Note: base_url is not available here, so we filter by status code only
        # and let the caller filter by URL if needed
        if resp.url.endswith("/favicon.ico"):
            return
        if resp.status >= 400:
            errors['bad_responses'].append(f"{resp.status} {resp.url}")
    
    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    page.on("response", on_response)
    
    return browser, context, page, errors


def assert_no_browser_errors(errors: dict, trace_path: Path | None = None):
    """Assert that no browser errors occurred during test execution.
    
    Args:
        errors: Error storage dict from create_browser_with_error_capture()
        trace_path: If set and errors exist, print trace location for debugging
    """
    has_errors = errors['page_errors'] or errors['console_errors'] or errors['bad_responses']
    
    if has_errors and trace_path:
        print(f"\n🔍 Trace saved to: {trace_path}")
        print(f"   View with: playwright show-trace {trace_path}")
    elif not has_errors and trace_path:
        # Clean up trace on success
        trace_path.unlink(missing_ok=True)
    
    assert not errors['page_errors'], "Page errors:\n" + "\n".join(errors['page_errors'])
    assert not errors['console_errors'], "Console errors:\n" + "\n".join(errors['console_errors'])
    assert not errors['bad_responses'], "Bad local responses:\n" + "\n".join(errors['bad_responses'])


def write_minimal_test_data(cwd: Path) -> None:
    """Write minimal test data (1 species) for basic navigation/smoke tests.
    
    This is the smallest data set that allows all pages to generate successfully.
    Includes 6 weeks of historical data for chart rendering validation.
    """
    from helpers.test_helpers import (
        HistoryEntry, BreederEntry, DealerEntry,
        create_history_csv_content, create_breeder_csv_content, create_dealer_csv_content
    )
    
    # Generate 6 weeks of history for realistic chart rendering
    # Include price variations, wishlist changes, and stock gaps (OUT runs)
    history_entries = [
        # Week 1: In stock
        HistoryEntry(
            scrape_datetime="2025-12-18",
            scientific_name="Aphonopelma seemanni",
            common_name="Costa Rican Zebra",
            price_gbp="23.00",
            wishlist_count="3"
        ),
        # Week 2: In stock, price increase
        HistoryEntry(
            scrape_datetime="2025-12-25",
            scientific_name="Aphonopelma seemanni",
            common_name="Costa Rican Zebra",
            price_gbp="24.00",
            wishlist_count="4"
        ),
        # Week 3: OUT (gap in data - no entry)
        # Week 4: OUT (gap in data - no entry)
        # Week 5: Back in stock, higher price and wishlist
        HistoryEntry(
            scrape_datetime="2026-01-08",
            scientific_name="Aphonopelma seemanni",
            common_name="Costa Rican Zebra",
            price_gbp="26.00",
            wishlist_count="7"
        ),
        # Week 6: Current run - in stock
        HistoryEntry(
            scrape_datetime="2026-01-15",
            scientific_name="Aphonopelma seemanni",
            common_name="Costa Rican Zebra",
            price_gbp="25.00",
            wishlist_count="5"
        ),
    ]
    
    # Current snapshot is the latest entry
    (cwd / "spidershop_spiderlings_scrape.csv").write_text(
        create_history_csv_content([history_entries[-1]]),
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


def write_multi_species_test_data(cwd: Path) -> None:
    """Write test data with 5 species for filtering, sorting, and search tests.
    
    This data set includes:
    - Mix of signals (🔥, ⚠️, ❌) and risks
    - Mix of stock patterns (Sustained, Emerging, Cyclical, Always)
    - Variety of numeric values (OOS runs, prices, wishlist counts) for sorting
    - Different name patterns for search testing
    """
    from helpers.test_helpers import (
        HistoryEntry, BreederEntry, DealerEntry,
        create_history_csv_content, create_breeder_csv_content, create_dealer_csv_content
    )
    
    history_entries = [
        HistoryEntry(
            scrape_datetime="2026-01-01",
            scientific_name="Aphonopelma seemanni",
            common_name="Costa Rican Zebra",
            size_cm="1.5",
            price_gbp="25.00",
            wishlist_count="5"
        ),
        HistoryEntry(
            scrape_datetime="2026-01-01",
            scientific_name="Brachypelma hamorii",
            common_name="Mexican Red Knee",
            size_cm="2.0",
            price_gbp="30.00",
            wishlist_count="8"
        ),
        HistoryEntry(
            scrape_datetime="2026-01-01",
            scientific_name="Grammostola pulchra",
            common_name="Brazilian Black",
            size_cm="3.5",
            price_gbp="35.00",
            wishlist_count="12"
        ),
        HistoryEntry(
            scrape_datetime="2026-01-01",
            scientific_name="Lasiodora parahybana",
            common_name="Salmon Pink Birdeater",
            size_cm="4.0",
            price_gbp="20.00",
            wishlist_count="3"
        ),
        HistoryEntry(
            scrape_datetime="2026-01-01",
            scientific_name="Pterinochilus murinus",
            common_name="Orange Baboon Tarantula",
            size_cm="1.0",
            price_gbp="15.00",
            wishlist_count="10"
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
                size_cm="1.5",
                signal="🔥",
                oos_runs="4",
                stock_pattern="Sustained"
            ),
            BreederEntry(
                species="Brachypelma hamorii",
                size_cm="2.0",
                signal="⚠️",
                oos_runs="2",
                stock_pattern="Emerging"
            ),
            BreederEntry(
                species="Grammostola pulchra",
                size_cm="3.5",
                signal="❌",
                oos_runs="0",
                stock_pattern="Always"
            ),
            BreederEntry(
                species="Lasiodora parahybana",
                size_cm="4.0",
                signal="🔥",
                oos_runs="6",
                stock_pattern="Cyclical"
            ),
            BreederEntry(
                species="Pterinochilus murinus",
                size_cm="1.0",
                signal="⚠️",
                oos_runs="3",
                stock_pattern="Emerging"
            ),
        ]),
        encoding="utf-8",
    )
    
    (cwd / "dealer_supply_risk_table.csv").write_text(
        create_dealer_csv_content([
            DealerEntry(
                species="Aphonopelma seemanni",
                size_cm="1.5",
                risk="🔥",
                stock_reliability="Low",
                restock_speed="Slow"
            ),
            DealerEntry(
                species="Brachypelma hamorii",
                size_cm="2.0",
                risk="⚠️",
                stock_reliability="Medium",
                restock_speed="Medium"
            ),
            DealerEntry(
                species="Grammostola pulchra",
                size_cm="3.5",
                risk="❌",
                stock_reliability="High",
                restock_speed="Fast"
            ),
            DealerEntry(
                species="Lasiodora parahybana",
                size_cm="4.0",
                risk="🔥",
                stock_reliability="Low",
                restock_speed="Slow"
            ),
            DealerEntry(
                species="Pterinochilus murinus",
                size_cm="1.0",
                risk="⚠️",
                stock_reliability="Medium",
                restock_speed="Fast"
            ),
        ]),
        encoding="utf-8",
    )
    
    (cwd / "analysis_summary.md").write_text(
        "## 🧬 Breeder Opportunity Matrix (Top 10)\n\n"
        "**Summary:** 5 species analyzed | 🔥 Hot: 2 | ⚠️ Watch: 2 | ❌ Avoid: 1\n\n"
        "## 🏪 Dealer Supply Risk Matrix (Top 10)\n\n"
        "**Summary:** 5 species analyzed | 🔥 High Risk: 2 | ⚠️ Moderate Risk: 2 | ❌ Low Risk: 1\n\n"
        "<details markdown=\"1\">\n"
        "<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>\n\n"
        "### 🧬 Breeder Opportunity Matrix — Legend\n\n"
        "**Signal**\n\n"
        "- `🔥` — Strong breeding opportunity signal\n"
        "- `⚠️` — Emerging opportunity\n"
        "- `❌` — Oversupplied\n\n"
        "### 📖 Breeder Matrix — Practical Examples\n\n"
        "Example breeder scenario.\n\n"
        "### 🏪 Dealer Supply Risk Matrix — Legend\n\n"
        "**Risk**\n\n"
        "- `🔥` — High supply risk\n"
        "- `⚠️` — Moderate risk\n"
        "- `❌` — Reliable supply\n\n"
        "### 📖 Dealer Matrix — Practical Examples\n\n"
        "Example dealer scenario.\n\n"
        "</details>\n",
        encoding="utf-8",
    )


def write_history_multi_date_test_data(cwd: "Path") -> None:
    """Write test data with 3 species across 3 weekly dates for date filter tests.

    Creates 9 history rows (3 species x 3 dates):
    - Dates: 2026-01-01, 2026-01-08, 2026-01-15 (oldest first in CSV order,
      most-recent-first after generate_history_page processes them)
    - Species: Aphonopelma seemanni, Brachypelma hamorii, Grammostola pulchra
    """
    from helpers.test_helpers import (
        HistoryEntry,
        BreederEntry,
        DealerEntry,
        create_history_csv_content,
        create_breeder_csv_content,
        create_dealer_csv_content,
    )

    species_data = [
        ("Aphonopelma seemanni", "Costa Rican Zebra", "1.5", "25.00", "5"),
        ("Brachypelma hamorii", "Mexican Red Knee", "2.0", "30.00", "10"),
        ("Grammostola pulchra", "Brazilian Black", "3.5", "50.00", "3"),
    ]
    dates = ["2026-01-01T06:10:00", "2026-01-08T06:10:00", "2026-01-15T06:10:00"]

    history_entries = [
        HistoryEntry(
            scrape_datetime=date,
            scientific_name=sci,
            common_name=common,
            size_cm=size,
            price_gbp=price,
            wishlist_count=wishlist,
        )
        for date in dates
        for sci, common, size, price, wishlist in species_data
    ]

    (cwd / "spidershop_spiderlings_scrape.csv").write_text(
        create_history_csv_content(history_entries), encoding="utf-8"
    )
    (cwd / "spidershop_spiderlings_history.csv").write_text(
        create_history_csv_content(history_entries), encoding="utf-8"
    )

    (cwd / "breeder_opportunity_table.csv").write_text(
        create_breeder_csv_content(
            [
                BreederEntry(
                    species="Aphonopelma seemanni",
                    size_cm="1.5",
                    signal="🔥",
                    oos_runs="4",
                    stock_pattern="Sustained",
                ),
                BreederEntry(
                    species="Brachypelma hamorii",
                    size_cm="2.0",
                    signal="⚠️",
                    oos_runs="2",
                    stock_pattern="Emerging",
                ),
                BreederEntry(
                    species="Grammostola pulchra",
                    size_cm="3.5",
                    signal="❌",
                    oos_runs="0",
                    stock_pattern="Always",
                ),
            ]
        ),
        encoding="utf-8",
    )

    (cwd / "dealer_supply_risk_table.csv").write_text(
        create_dealer_csv_content(
            [
                DealerEntry(
                    species="Aphonopelma seemanni",
                    size_cm="1.5",
                    risk="🔥",
                    stock_reliability="Low",
                    restock_speed="Slow",
                ),
                DealerEntry(
                    species="Brachypelma hamorii",
                    size_cm="2.0",
                    risk="⚠️",
                    stock_reliability="Medium",
                    restock_speed="Medium",
                ),
                DealerEntry(
                    species="Grammostola pulchra",
                    size_cm="3.5",
                    risk="❌",
                    stock_reliability="High",
                    restock_speed="Fast",
                ),
            ]
        ),
        encoding="utf-8",
    )

    (cwd / "analysis_summary.md").write_text(
        "## 🧬 Breeder Opportunity Matrix (Top 10)\n\n"
        "**Summary:** 3 species analyzed | 🔥 Hot: 1 | ⚠️ Watch: 1 | ❌ Avoid: 1\n\n"
        "## 🏪 Dealer Supply Risk Matrix (Top 10)\n\n"
        "**Summary:** 3 species analyzed | 🔥 High Risk: 1 | ⚠️ Moderate Risk: 1 | ❌ Low Risk: 1\n",
        encoding="utf-8",
    )

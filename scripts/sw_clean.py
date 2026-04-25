#!/usr/bin/env python3
"""
Clear the service worker registration and all SW-managed caches for the site.

Navigates to the target origin using a headless Chromium browser, runs the
unregister + cache-clear script, and exits. The browser window is not shown.

Usage:
    python scripts/sw_clean.py --local          # http://127.0.0.1:8000
    python scripts/sw_clean.py --deployed       # https://christianacca.github.io/spidershop-historical-analysis/
    python scripts/sw_clean.py --url <URL>      # any URL
"""

import argparse
import sys

DEPLOYED_URL = "https://christianacca.github.io/spidershop-historical-analysis/"
LOCAL_URL = "http://127.0.0.1:8000/"

# JS that unregisters all SWs scoped to this origin and deletes all caches.
_CLEAN_SCRIPT = """
async () => {
    const results = { unregistered: 0, cachesDeleted: 0 };

    // Unregister every SW registration on this origin.
    if ('serviceWorker' in navigator) {
        const regs = await navigator.serviceWorker.getRegistrations();
        for (const reg of regs) {
            await reg.unregister();
            results.unregistered += 1;
        }
    }

    // Delete every cache entry on this origin.
    if ('caches' in window) {
        const names = await caches.keys();
        for (const name of names) {
            await caches.delete(name);
            results.cachesDeleted += 1;
        }
    }

    return results;
}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Clear SW registration and caches for the site.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--local", action="store_true", help=f"Target local dev server ({LOCAL_URL})")
    group.add_argument("--deployed", action="store_true", help=f"Target deployed GitHub Pages site ({DEPLOYED_URL})")
    group.add_argument("--url", metavar="URL", help="Target an arbitrary URL")
    args = parser.parse_args()

    if args.local:
        url = LOCAL_URL
        label = "local dev server"
    elif args.deployed:
        url = DEPLOYED_URL
        label = "deployed GitHub Pages site"
    else:
        url = args.url
        label = url

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright is not installed. Run: pip install -r requirements-dev.txt", file=sys.stderr)
        sys.exit(1)

    print(f"🧹 Clearing SW and caches for {label} ...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            except Exception as e:
                print(f"❌ Could not navigate to {url}: {e}", file=sys.stderr)
                if args.local:
                    print("   Is the local server running? Start it with: make serve-only", file=sys.stderr)
                sys.exit(1)

            result = page.evaluate(_CLEAN_SCRIPT)
            sw_count = result.get("unregistered", 0)
            cache_count = result.get("cachesDeleted", 0)
        finally:
            browser.close()

    print(f"✅ Done — {sw_count} SW registration(s) unregistered, {cache_count} cache(s) deleted.")
    print("   Reload the page in your browser to start fresh.")


if __name__ == "__main__":
    main()

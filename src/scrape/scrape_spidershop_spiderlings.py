#!/usr/bin/env python3
import csv
import os
from datetime import datetime, timezone
from urllib.parse import urljoin

from requests.exceptions import HTTPError

from shared.config import BASE_URL, SNAPSHOT_FILE, HISTORY_FILE, CSV_HEADER, BREEDER_TABLE_FILE, DEALER_TABLE_FILE
from scrape.http_client import fetch
from scrape.scraper import extract_product_urls, scrape_product
from scrape.browser_client import close_driver
from scrape.history import load_history, append_history
from scrape.pricing_summary import write_pricing_summary
from scrape.breeder_matrix import build_breeder_opportunity_table, write_breeder_outputs
from scrape.dealer_matrix import build_dealer_supply_risk_table, write_dealer_outputs
from scrape.legend import write_summary_legend
from shared.assertions import assert_condition, csv_row_count, read_summary_text

# =====================
# MAIN
# =====================

def main():
    scrape_dt = datetime.now(timezone.utc).replace(second=0, microsecond=0).isoformat(timespec="minutes")

    all_rows = []
    page = 1

    try:
        while True:
            category_url = BASE_URL if page == 1 else urljoin(BASE_URL, f"page/{page}/")
            try:
                category_html = fetch(category_url)
            except HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    break
                raise

            product_urls = extract_product_urls(category_html, category_url)
            if not product_urls:
                break

            for pu in product_urls:
                sci, com, size, price, wishlist, lifestyle = scrape_product(pu)
                all_rows.append([scrape_dt, sci, com, size, price, wishlist, pu, lifestyle])

            page += 1

        assert_condition(len(all_rows) > 0, "Scrape completed but returned ZERO rows")

        with open(SNAPSHOT_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(CSV_HEADER)
            w.writerows(all_rows)

        history_rows = load_history(HISTORY_FILE)
        
        # Add missing fields to old history rows for backward compatibility
        needs_rewrite = any(
            "wishlist_count" not in row or "lifestyle" not in row
            for row in history_rows
        )
        
        for row in history_rows:
            row.setdefault("wishlist_count", "0")
            row.setdefault("lifestyle", "")
        
        # If any fields were added to old rows, rewrite the history file with updated schema
        if needs_rewrite and history_rows:
            with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=CSV_HEADER)
                w.writeheader()
                w.writerows(history_rows)
        
        existing = {tuple(r[h] for h in CSV_HEADER) for r in history_rows}

        new_rows = [r for r in all_rows if tuple(r) not in existing]
        append_history(HISTORY_FILE, new_rows)
        history_rows.extend(dict(zip(CSV_HEADER, r)) for r in new_rows)

        # Clear analysis_summary.md before writing new analysis
        summary_path = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_path and os.path.exists(summary_path):
            open(summary_path, "w").close()

        write_pricing_summary(history_rows, scrape_dt)

        breeder_table = build_breeder_opportunity_table(history_rows)
        breeder_written = write_breeder_outputs(breeder_table)

        dealer_table = build_dealer_supply_risk_table(history_rows)
        dealer_written = write_dealer_outputs(dealer_table)

        write_summary_legend()

        # =====================
        # ASSERTIONS (BASELINE-PRESERVING)
        # =====================

        assert_condition(os.path.exists(SNAPSHOT_FILE), f"Missing snapshot CSV: {SNAPSHOT_FILE}")
        assert_condition(csv_row_count(SNAPSHOT_FILE) > 0, "Snapshot CSV has 0 data rows")

        assert_condition(os.path.exists(HISTORY_FILE), f"Missing history CSV: {HISTORY_FILE}")
        assert_condition(csv_row_count(HISTORY_FILE) > 0, "History CSV has 0 data rows")

        assert_condition(os.path.exists(BREEDER_TABLE_FILE), f"Missing breeder table CSV: {BREEDER_TABLE_FILE}")
        # Note: Empty tables are valid when no opportunities are detected (conservative analysis)

        assert_condition(os.path.exists(DEALER_TABLE_FILE), f"Missing dealer table CSV: {DEALER_TABLE_FILE}")
        # Note: Empty tables are valid when no supply risks are detected (conservative analysis)

        assert_condition(breeder_written, "Breeder Opportunity Matrix (Top 10) was not written (writer returned False)")
        assert_condition(dealer_written, "Dealer Supply Risk Matrix (Top 10) was not written (writer returned False)")

        summary_text = read_summary_text()
        assert_condition("## 🧬 Breeder Opportunity Matrix (Top 10)" in summary_text,
                         "Breeder Opportunity Matrix (Top 10) heading missing from Job Summary")
        assert_condition("## 🏪 Dealer Supply Risk Matrix (Top 10)" in summary_text,
                         "Dealer Supply Risk Matrix (Top 10) heading missing from Job Summary")

        print(f"Snapshot rows: {len(all_rows)}")
        print(f"New historical rows appended: {len(new_rows)}")
    
    finally:
        # Clean up browser resources
        close_driver()

if __name__ == "__main__":
    main()

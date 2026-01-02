#!/usr/bin/env python3
import csv
import os
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

# =====================
# CONFIG
# =====================

BASE_URL = "https://thespidershop.co.uk/product-category/tarantulas-for-sale-in-the-uk/spiderlings/"

SNAPSHOT_FILE = "spidershop_spiderlings_scrape.csv"
HISTORY_FILE = "spidershop_spiderlings_history.csv"

BREEDER_TABLE_FILE = "breeder_opportunity_table.csv"
DEALER_TABLE_FILE = "dealer_supply_risk_table.csv"

CSV_HEADER = [
    "scrape_datetime",
    "scientific_name",
    "common_name",
    "size_cm",
    "price_gbp",
    "page_url",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/7.1)",
    "Accept-Language": "en-GB,en;q=0.9",
}

PARENS_RE = re.compile(r"\(([^)]*)\)")
SIZE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(?:[-–]\s*(\d+(?:\.\d+)?))?\s*cm\s*$",
    re.IGNORECASE,
)

# =====================
# ASSERTION HELPERS
# =====================

def assert_condition(condition: bool, message: str):
    if not condition:
        raise SystemExit(f"ASSERTION FAILED: {message}")

def read_summary_text():
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_summary_path():
    return os.environ.get("GITHUB_STEP_SUMMARY")

# =====================
# UTILITIES
# =====================

def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

# =====================
# PARSING HELPERS
# =====================

def first_cm_parenthetical(text: str):
    for m in PARENS_RE.finditer(text or ""):
        if "cm" in m.group(1).lower():
            return m.group(0)
    return None

def parse_size_cm(text: str) -> str:
    paren = first_cm_parenthetical(text)
    if not paren:
        return ""
    inner = paren[1:-1]
    m = SIZE_RE.match(inner)
    if not m:
        return ""
    try:
        val = m.group(2) or m.group(1)
        d = Decimal(val)
        return str(int(d)) if d == d.to_integral_value() else format(d, "f")
    except InvalidOperation:
        return ""

def remove_size_parenthetical_only(text: str) -> str:
    text = normalize_whitespace(text)
    paren = first_cm_parenthetical(text)
    if not paren:
        return text
    return normalize_whitespace(text.replace(paren, " ", 1))

def parse_price(text: str) -> str:
    if not text:
        return ""
    s = text.replace("£", "").replace("\u00a3", "").replace(",", "").strip()
    try:
        return format(Decimal(s), "f")
    except InvalidOperation:
        return ""

# =====================
# SCRAPING
# =====================

def extract_product_urls(category_html: str, category_url: str):
    soup = BeautifulSoup(category_html, "html.parser")
    urls, seen = [], set()

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if "/product/" not in href:
            continue
        full = urljoin(category_url, href)
        if full not in seen:
            seen.add(full)
            urls.append(full)

    return urls

def scrape_product(product_url: str):
    soup = BeautifulSoup(fetch(product_url), "html.parser")

    h1 = soup.find("h1")
    scientific_name = normalize_whitespace(h1.get_text()) if h1 else ""

    h2 = soup.find("h2")
    common_line = normalize_whitespace(h2.get_text()) if h2 else ""

    price_el = soup.select_one(".woocommerce-Price-amount")

    return (
        scientific_name,
        remove_size_parenthetical_only(common_line),
        parse_size_cm(common_line),
        parse_price(normalize_whitespace(price_el.get_text()) if price_el else ""),
    )

# =====================
# HISTORY
# =====================

def load_history(path: str):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def append_history(path: str, rows):
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(CSV_HEADER)
        w.writerows(rows)

# =====================
# HELPERS
# =====================

def group_by_run(rows):
    by_run = {}
    for r in rows:
        by_run.setdefault(r["scrape_datetime"], []).append(r)
    return by_run

def k2(r):
    return (r["scientific_name"], r["size_cm"])

# =====================
# PRICING SUMMARY
# =====================

def write_pricing_summary(history_rows, scrape_dt):
    summary = get_summary_path()
    if not summary:
        return

    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    if len(runs) < 2:
        return

    cur = by_run[runs[-1]]
    prev = by_run[runs[-2]]

    cur_map = {k2(r): r for r in cur if r["price_gbp"]}
    prev_map = {k2(r): r for r in prev if r["price_gbp"]}

    inc = dec = same = new = gone = 0
    movers = []

    for k, r in cur_map.items():
        if k not in prev_map:
            new += 1
            continue
        cp, pp = float(r["price_gbp"]), float(prev_map[k]["price_gbp"])
        if cp > pp:
            inc += 1
        elif cp < pp:
            dec += 1
        else:
            same += 1
        if pp:
            movers.append((r["scientific_name"], r["size_cm"], pp, cp, (cp - pp) / pp))

    gone = len([k for k in prev_map if k not in cur_map])
    movers.sort(key=lambda x: abs(x[4]), reverse=True)
    top5 = movers[:5]

    with open(summary, "a", encoding="utf-8") as f:
        f.write("## 🕷️ Spiderlings Pricing Summary\n\n")
        f.write(f"**Scrape time (UTC):** `{scrape_dt}`\n\n")
        f.write(f"- 🔼 Increases: **{inc}**\n")
        f.write(f"- 🔽 Decreases: **{dec}**\n")
        f.write(f"- ➖ Unchanged: **{same}**\n")
        f.write(f"- 🆕 New: **{new}**\n")
        f.write(f"- ❌ Removed: **{gone}**\n\n")
        f.write("### 🚀 Top 5 Price Movers\n")
        if top5:
            f.write("| Species | Size | Old | New | Change |\n|---|---|---:|---:|---:|\n")
            for s, size, o, n, p in top5:
                sign = "+" if p > 0 else ""
                f.write(f"| {s} | {size} | £{o:.2f} | £{n:.2f} | {sign}{p*100:.1f}% |\n")
        else:
            f.write("_No comparable price changes detected._\n")

# =====================
# BREEDER MATRIX
# =====================

def build_breeder_opportunity_table(history_rows):
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    if len(runs) < 2:
        return []

    cur = by_run[runs[-1]]
    prev = by_run[runs[-2]]
    prev_price = {k2(r): r["price_gbp"] for r in prev if r["price_gbp"]}

    table = []

    for r in cur:
        key = k2(r)
        oos_runs = 0
        if key not in {k2(x) for x in prev}:
            for rt in reversed(runs[:-1]):
                if any(k2(x) == key for x in by_run[rt]):
                    break
                oos_runs += 1

        pattern = "Sustained" if oos_runs >= 3 else "Emerging" if oos_runs == 2 else "Always"

        price_trend = "→"
        if key in prev_price and r["price_gbp"]:
            cp, pp = float(r["price_gbp"]), float(prev_price[key])
            if cp > pp:
                price_trend = "↑"
            elif cp < pp:
                price_trend = "↓"

        if pattern == "Sustained" and price_trend != "↓":
            signal, rec = "🔥", "Pair soon — sustained scarcity"
        elif pattern == "Emerging" and price_trend == "↑":
            signal, rec = "🔥", "Consider pairing — rising demand"
        elif pattern == "Emerging":
            signal, rec = "⚠️", "Monitor closely — supply tightening"
        else:
            signal, rec = "❌", "Avoid for profit — oversupplied"

        table.append({
            "Species": r["scientific_name"],
            "Size (cm)": r["size_cm"],
            "Pattern": pattern,
            "Price Trend": price_trend,
            "Signal": signal,
            "Recommendation": rec,
        })

    return table

def write_breeder_outputs(table):
    if not table:
        return False

    with open(BREEDER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=table[0].keys())
        w.writeheader()
        w.writerows(table)

    summary = get_summary_path()
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n## 🧬 Breeder Opportunity Matrix\n\n")
            f.write("| Species | Size | Pattern | Price Trend | Signal | Recommendation |\n")
            f.write("|---|---|---|---|---|---|\n")
            for r in table[:10]:
                f.write(
                    f"| {r['Species']} | {r['Size (cm)']} | {r['Pattern']} | "
                    f"{r['Price Trend']} | {r['Signal']} | {r['Recommendation']} |\n"
                )
            if len(table) > 10:
                f.write(f"\n_Showing top 10 of {len(table)} entries — see `{BREEDER_TABLE_FILE}` for full list._\n")
    return True

# =====================
# DEALER MATRIX
# =====================

def build_dealer_supply_risk_table(history_rows):
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    if len(runs) < 2:
        return []

    prev = by_run[runs[-2]]
    cur = by_run[runs[-1]]

    prev_prices = {k2(r): r["price_gbp"] for r in prev if r["price_gbp"]}
    cur_prices = {k2(r): r["price_gbp"] for r in cur if r["price_gbp"]}

    presence = {}
    for rt in runs:
        for r in by_run[rt]:
            presence.setdefault(k2(r), set()).add(rt)

    table = []

    for (sci, size), pres in presence.items():
        reliability = "High" if len(pres) / len(runs) >= 0.8 else "Medium"
        price_pressure = "→"
        if (sci, size) in prev_prices and (sci, size) in cur_prices:
            cp, pp = float(cur_prices[(sci, size)]), float(prev_prices[(sci, size)])
            if cp > pp:
                price_pressure = "↑"
            elif cp < pp:
                price_pressure = "↓"

        risk = "❌" if reliability == "High" else "⚠️"
        rec = "No urgency / oversupplied" if risk == "❌" else "Buy opportunistically"

        table.append({
            "Species": sci,
            "Size (cm)": size,
            "Stock Reliability": reliability,
            "Price Pressure": price_pressure,
            "Dealer Risk": risk,
            "Dealer Recommendation": rec,
        })

    return table

def write_dealer_outputs(table):
    if not table:
        return False

    with open(DEALER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=table[0].keys())
        w.writeheader()
        w.writerows(table)

    summary = get_summary_path()
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n## 🏪 Dealer Supply Risk Matrix\n\n")
            f.write("| Species | Size | Reliability | Price Pressure | Risk | Recommendation |\n")
            f.write("|---|---|---|---|---|---|\n")
            for r in table[:10]:
                f.write(
                    f"| {r['Species']} | {r['Size (cm)']} | {r['Stock Reliability']} | "
                    f"{r['Price Pressure']} | {r['Dealer Risk']} | {r['Dealer Recommendation']} |\n"
                )
            if len(table) > 10:
                f.write(f"\n_Showing top 10 of {len(table)} entries — see `{DEALER_TABLE_FILE}` for full list._\n")
    return True

# =====================
# MAIN
# =====================

def main():
    scrape_dt = datetime.now(timezone.utc).replace(second=0, microsecond=0).isoformat(timespec="minutes")

    all_rows = []
    page = 1

    while True:
        url = BASE_URL if page == 1 else urljoin(BASE_URL, f"page/{page}/")
        try:
            html = fetch(url)
        except HTTPError as e:
            if e.response.status_code == 404:
                break
            raise

        for pu in extract_product_urls(html, url):
            sci, com, size, price = scrape_product(pu)
            all_rows.append([scrape_dt, sci, com, size, price, url])

        page += 1

    assert_condition(len(all_rows) > 0, "Scrape completed but returned ZERO rows")

    with open(SNAPSHOT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        w.writerows(all_rows)

    history = load_history(HISTORY_FILE)
    existing = {tuple(r[h] for h in CSV_HEADER) for r in history}
    new_rows = [r for r in all_rows if tuple(r) not in existing]

    append_history(HISTORY_FILE, new_rows)
    history.extend(dict(zip(CSV_HEADER, r)) for r in new_rows)

    write_pricing_summary(history, scrape_dt)

    breeder_table = build_breeder_opportunity_table(history)
    breeder_written = write_breeder_outputs(breeder_table)

    dealer_table = build_dealer_supply_risk_table(history)
    dealer_written = write_dealer_outputs(dealer_table)

    summary_text = read_summary_text()

    # =====================
    # FINAL ASSERTIONS
    # =====================

    assert_condition(breeder_written, "Breeder Opportunity Matrix not written")
    assert_condition(dealer_written, "Dealer Supply Risk Matrix not written")

    assert_condition(
        "## 🧬 Breeder Opportunity Matrix" in summary_text,
        "Breeder Opportunity Matrix missing from Job Summary",
    )

    assert_condition(
        "## 🏪 Dealer Supply Risk Matrix" in summary_text,
        "Dealer Supply Risk Matrix missing from Job Summary",
    )

    print(f"Snapshot rows: {len(all_rows)}")
    print(f"New history rows: {len(new_rows)}")

if __name__ == "__main__":
    main()

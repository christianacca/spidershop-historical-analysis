#!/usr/bin/env python3
import csv
import os
import re
from datetime import datetime, timezone, timedelta
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
HISTORY_FILE  = "spidershop_spiderlings_history.csv"

CSV_HEADER = [
    "scrape_datetime",
    "scientific_name",
    "common_name",
    "size_cm",
    "price_gbp",
    "page_url",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/4.1)",
    "Accept-Language": "en-GB,en;q=0.9",
}

PARENS_RE = re.compile(r"\(([^)]*)\)")
SIZE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(?:[-–]\s*(\d+(?:\.\d+)?))?\s*cm\s*$",
    re.IGNORECASE,
)

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

def median(values):
    if not values:
        return None
    values = sorted(values)
    n = len(values)
    mid = n // 2
    if n % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2

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
    html = fetch(product_url)
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    scientific_name = normalize_whitespace(h1.get_text()) if h1 else ""

    h2 = soup.find("h2")
    common_line = normalize_whitespace(h2.get_text()) if h2 else ""

    common_name = remove_size_parenthetical_only(common_line)
    size_cm = parse_size_cm(common_line)

    price_el = soup.select_one(".price .woocommerce-Price-amount, .woocommerce-Price-amount")
    price_gbp = parse_price(normalize_whitespace(price_el.get_text()) if price_el else "")

    return scientific_name, common_name, size_cm, price_gbp

# =====================
# HISTORY HANDLING
# =====================

def load_existing_history(path: str):
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {tuple(row[h] for h in CSV_HEADER) for row in csv.DictReader(f)}

def append_history(path: str, rows):
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(CSV_HEADER)
        w.writerows(rows)

# =====================
# JOB SUMMARY
# =====================

def write_job_summary(history_file: str, scrape_datetime: str):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path or not os.path.exists(history_file):
        return

    now = datetime.fromisoformat(scrape_datetime)
    window_start = now - timedelta(days=90)

    with open(history_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_run = {}
    for r in rows:
        by_run.setdefault(r["scrape_datetime"], []).append(r)

    run_times = sorted(by_run.keys())
    current = by_run[run_times[-1]]
    previous = by_run[run_times[-2]] if len(run_times) > 1 else []

    def key(r):
        return (r["scientific_name"], r["common_name"], r["size_cm"])

    cur_map = {key(r): r for r in current}
    prev_map = {key(r): r for r in previous}

    prices = [float(r["price_gbp"]) for r in current if r["price_gbp"]]
    inc = dec = same = new = gone = 0

    for k, r in cur_map.items():
        if k not in prev_map:
            new += 1
        elif r["price_gbp"] != prev_map[k]["price_gbp"]:
            if float(r["price_gbp"]) > float(prev_map[k]["price_gbp"]):
                inc += 1
            else:
                dec += 1
        else:
            same += 1

    for k in prev_map:
        if k not in cur_map:
            gone += 1

    # Rolling 3-month median
    rolling_prices = [
        float(r["price_gbp"])
        for r in rows
        if r["price_gbp"]
        and window_start <= datetime.fromisoformat(r["scrape_datetime"]) <= now
    ]

    rolling_median = median(rolling_prices)

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("## 🕷️ Spiderlings Pricing Summary\n\n")
        f.write(f"**Scrape time (UTC):** `{scrape_datetime}`\n\n")

        f.write("### 📊 Current Snapshot\n")
        f.write(f"- Listings: **{len(current)}**\n")
        if prices:
            f.write(f"- Median price (this run): **£{median(prices):.2f}**\n")

        f.write("\n### 🔄 Changes Since Last Run\n")
        f.write(f"- 🔼 Price increases: **{inc}**\n")
        f.write(f"- 🔽 Price decreases: **{dec}**\n")
        f.write(f"- ➖ Unchanged: **{same}**\n")
        f.write(f"- 🆕 New listings: **{new}**\n")
        f.write(f"- ❌ Removed listings: **{gone}**\n")

        f.write("\n### 📈 Rolling 3-Month Median Price\n")
        if rolling_median is None:
            f.write("_Insufficient historical data (need up to 90 days)._")
        else:
            f.write(
                f"- Window: `{window_start.date()} → {now.date()}`\n"
                f"- Price points: **{len(rolling_prices)}**\n"
                f"- Median price: **£{rolling_median:.2f}**\n"
            )

# =====================
# MAIN
# =====================

def main():
    scrape_datetime = (
        datetime.now(timezone.utc)
        .replace(second=0, microsecond=0)
        .isoformat(timespec="minutes")
    )

    all_rows = []
    page = 1

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
            sci, com, size, price = scrape_product(pu)
            all_rows.append([
                scrape_datetime, sci, com, size, price, category_url
            ])

        page += 1

    if not all_rows:
        raise SystemExit("ERROR: Scrape completed but returned ZERO rows")

    with open(SNAPSHOT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        w.writerows(all_rows)

    existing = load_existing_history(HISTORY_FILE)
    new_rows = [r for r in all_rows if tuple(r) not in existing]
    append_history(HISTORY_FILE, new_rows)

    write_job_summary(HISTORY_FILE, scrape_datetime)

    print(f"Snapshot rows: {len(all_rows)}")
    print(f"New historical rows appended: {len(new_rows)}")

if __name__ == "__main__":
    main()

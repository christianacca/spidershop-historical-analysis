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
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/7.2)",
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

def get_summary_path():
    return os.environ.get("GITHUB_STEP_SUMMARY")

def read_summary_text() -> str:
    path = get_summary_path()
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def csv_row_count(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in f) - 1

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

    common_name = remove_size_parenthetical_only(common_line)
    size_cm = parse_size_cm(common_line)

    price_el = soup.select_one(".woocommerce-Price-amount")
    price_gbp = parse_price(normalize_whitespace(price_el.get_text()) if price_el else "")

    return scientific_name, common_name, size_cm, price_gbp

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

def k3(r):
    return (r["scientific_name"], r["common_name"], r["size_cm"])

def k2(r):
    return (r["scientific_name"], r["size_cm"])

# =====================
# LEGENDS (NEW)
# =====================

def write_breeder_legend(f):
    f.write("""
<details>
<summary><strong>ℹ️ Breeder Opportunity Matrix — Legend</strong></summary>

**OOS**
- `IN` — Currently listed
- `OUT` — Not listed this run
- `IN/OUT` — Recently restocked after absence

**OOS Runs**
- Consecutive weekly scrapes absent (including current run if OUT)

**Pattern**
- `Always` — Normal noise (0–1 OOS runs)
- `Emerging` — Repeated scarcity (2–3 OOS runs)
- `Sustained` — Persistent shortage (4+ OOS runs)
- `Cyclical` — Regular disappear/reappear behaviour

**Price Trend**
- `↑` Increasing
- `↓` Decreasing
- `→` Flat / insufficient data

**Signal**
- 🔥 Strong breeding opportunity
- ⚠️ Monitor
- ❌ Oversupplied

**Recommendation**
- Breeder-focused action guidance

</details>
""")

def write_dealer_legend(f):
    f.write("""
<details>
<summary><strong>ℹ️ Dealer Supply Risk Matrix — Legend</strong></summary>

**Stock Reliability**
- `High` — Usually available
- `Medium` — Intermittent
- `Low` — Rarely stocked

**Avg OOS Duration**
- Average consecutive weeks out of stock

**Restock Speed**
- `Fast` — ~1 week
- `Moderate` — ~2 weeks
- `Slow` — 3+ weeks

**Price Pressure**
- `↑` Rising
- `↓` Falling
- `→` Stable

**Dealer Risk**
- 🔥 High missed-sales risk
- ⚠️ Moderate
- ❌ Low

**Dealer Recommendation**
- Dealer-focused action guidance

</details>
""")

# =====================
# BREEDER MATRIX
# =====================
# (UNCHANGED LOGIC – omitted here for brevity in explanation,
# but INCLUDED in your pasted script exactly as provided)
# =====================

# 👉 Everything from:
# build_breeder_opportunity_table
# write_breeder_outputs
# build_dealer_supply_risk_table
# write_dealer_outputs
# main()
# remains IDENTICAL to your baseline,
# EXCEPT for the two calls below 👇

# In write_breeder_outputs(), after the table footer:
#     write_breeder_legend(f)

# In write_dealer_outputs(), after the table footer:
#     write_dealer_legend(f)

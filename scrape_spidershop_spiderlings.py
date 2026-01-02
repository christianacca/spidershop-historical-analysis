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
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/8.0)",
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

def read_summary_text():
    path = get_summary_path()
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def csv_row_count(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, newline="", encoding="utf-8") as f:
        return max(0, sum(1 for _ in f) - 1)

# =====================
# UTILITIES
# =====================

def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

# =====================
# PARSING
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
    return normalize_whitespace(text.replace(paren, "", 1)) if paren else text

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

def extract_product_urls(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    seen, urls = set(), []
    for a in soup.select("a[href*='/product/']"):
        href = a.get("href", "").strip()
        full = urljoin(base_url, href)
        if full not in seen:
            seen.add(full)
            urls.append(full)
    return urls

def scrape_product(url: str):
    soup = BeautifulSoup(fetch(url), "html.parser")
    h1 = soup.find("h1")
    h2 = soup.find("h2")
    price_el = soup.select_one(".woocommerce-Price-amount")

    common_line = normalize_whitespace(h2.get_text()) if h2 else ""

    return (
        normalize_whitespace(h1.get_text()) if h1 else "",
        remove_size_parenthetical_only(common_line),
        parse_size_cm(common_line),
        parse_price(normalize_whitespace(price_el.get_text()) if price_el else ""),
    )

# =====================
# HISTORY
# =====================

def load_history(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def append_history(path, rows):
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
    out = {}
    for r in rows:
        out.setdefault(r["scrape_datetime"], []).append(r)
    return out

def key(r):
    return (r["scientific_name"], r["size_cm"])

# =====================
# BREEDER MATRIX (FIXED)
# =====================

def build_breeder_opportunity_table(history_rows):
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    if len(runs) < 2:
        return []

    latest = by_run[runs[-1]]
    latest_keys = {key(r) for r in latest}

    # Build historical universe
    species_rows = {}
    for rt in runs:
        for r in by_run[rt]:
            species_rows.setdefault(key(r), []).append((rt, r))

    table = []

    for (sci, size), timeline in species_rows.items():
        timeline.sort(key=lambda x: x[0])

        in_latest = (sci, size) in latest_keys
        oos_runs = 0
        for rt in reversed(runs):
            if any(rt == t[0] for t in timeline):
                break
            oos_runs += 1

        if in_latest:
            oos_status = "IN"
        else:
            oos_status = "OUT"

        if oos_runs >= 3:
            pattern = "Sustained"
        elif oos_runs >= 1:
            pattern = "Emerging"
        else:
            pattern = "Always"

        # Price trend: last two known prices
        price_trend = "→"
        prices = [r["price_gbp"] for _, r in timeline if r.get("price_gbp")]
        if len(prices) >= 2:
            try:
                p_prev = float(prices[-2])
                p_cur = float(prices[-1])
                if p_cur > p_prev:
                    price_trend = "↑"
                elif p_cur < p_prev:
                    price_trend = "↓"
            except ValueError:
                pass

        if pattern == "Sustained":
            signal, rec = "🔥", "Pair soon — sustained scarcity"
        elif pattern == "Emerging":
            signal, rec = "⚠️", "Consider pairing — early scarcity signal"
        else:
            signal, rec = "❌", "Avoid for profit — oversupplied"

        table.append({
            "Species": sci,
            "Size (cm)": size,
            "OOS": oos_status,
            "OOS Runs": str(oos_runs),
            "Pattern": pattern,
            "Price Trend": price_trend,
            "Signal": signal,
            "Recommendation": rec,
        })

    table.sort(key=lambda r: ({"🔥": 0, "⚠️": 1, "❌": 2}[r["Signal"]], -int(r["OOS Runs"])))
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
            f.write("| Species | Size (cm) | OOS | OOS Runs | Pattern | Price Trend | Signal | Recommendation |\n")
            f.write("|---|---:|---|---:|---|---|---|---|\n")
            for r in table[:10]:
                f.write(
                    f"| {r['Species']} | {r['Size (cm)']} | {r['OOS']} | {r['OOS Runs']} | "
                    f"{r['Pattern']} | {r['Price Trend']} | {r['Signal']} | {r['Recommendation']} |\n"
                )
            if len(table) > 10:
                f.write(f"\n_Showing top 10 of {len(table)} entries — see `{BREEDER_TABLE_FILE}` for full list._\n")
    return True

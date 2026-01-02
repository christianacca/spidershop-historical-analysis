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
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/6.1)",
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

def scrape_product(url: str):
    soup = BeautifulSoup(fetch(url), "html.parser")

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
# ANALYSIS HELPERS
# =====================

def group_by_run(rows):
    by_run = {}
    for r in rows:
        by_run.setdefault(r["scrape_datetime"], []).append(r)
    return by_run

def key(r):
    return (r["scientific_name"], r["size_cm"])

# =====================
# BREEDER MATRIX (Phase 1)
# =====================

def build_breeder_opportunity_table(rows):
    by_run = group_by_run(rows)
    runs = sorted(by_run)
    if len(runs) < 2:
        return []

    current, prev = by_run[runs[-1]], by_run[runs[-2]]
    prev_keys = {key(r) for r in prev}

    table = []

    for r in current:
        k = key(r)
        oos_runs = 0
        oos = "IN"

        if k not in prev_keys:
            oos = "OUT"
            for rt in reversed(runs[:-1]):
                if any(key(x) == k for x in by_run[rt]):
                    break
                oos_runs += 1
        elif any(k not in {key(x) for x in by_run[rt]} for rt in runs[-3:-1]):
            oos = "IN/OUT"

        if oos_runs >= 3:
            pattern = "Sustained"
            signal = "🔥"
            rec = "Pair soon — sustained scarcity"
        elif oos_runs == 2:
            pattern = "Emerging"
            signal = "🔥"
            rec = "Consider pairing — monitor supply"
        elif oos == "IN/OUT":
            pattern = "Cyclical"
            signal = "⚠️"
            rec = "Breed cautiously — wave restocking"
        else:
            pattern = "Always"
            signal = "❌"
            rec = "Avoid for profit — oversupplied"

        table.append({
            "Species": r["scientific_name"],
            "Size (cm)": r["size_cm"],
            "OOS": oos,
            "OOS Runs": str(oos_runs),
            "Pattern": pattern,
            "Signal": signal,
            "Recommendation": rec,
        })

    table.sort(key=lambda r: ({"🔥":0,"⚠️":1,"❌":2}[r["Signal"]], -int(r["OOS Runs"])))
    return table

# =====================
# DEALER MATRIX (Phase 2)
# =====================

def build_dealer_supply_risk_table(rows):
    by_run = group_by_run(rows)
    runs = sorted(by_run)
    total_runs = len(runs)

    history = {}
    for rt in runs:
        for r in by_run[rt]:
            history.setdefault(key(r), []).append(rt)

    table = []

    for (sci, size), seen_runs in history.items():
        present_pct = len(seen_runs) / total_runs
        reliability = (
            "High" if present_pct >= 0.8 else
            "Medium" if present_pct >= 0.4 else
            "Low"
        )

        oos_events = []
        last_present = None
        for rt in runs:
            present = rt in seen_runs
            if last_present is True and not present:
                oos_events.append(1)
            elif last_present is False and not present:
                oos_events[-1] += 1
            last_present = present

        avg_oos = round(sum(oos_events) / len(oos_events), 1) if oos_events else 0
        speed = "Slow" if avg_oos >= 3 else "Moderate" if avg_oos == 2 else "Fast"

        if reliability == "Low" and speed == "Slow":
            risk = "🔥"
            rec = "Actively seek breeders"
        elif reliability == "Medium":
            risk = "⚠️"
            rec = "Buy opportunistically"
        else:
            risk = "❌"
            rec = "No urgency / oversupplied"

        table.append({
            "Species": sci,
            "Size (cm)": size,
            "Stock Reliability": reliability,
            "Avg OOS Duration": avg_oos,
            "Restock Speed": speed,
            "Dealer Risk": risk,
            "Dealer Recommendation": rec,
        })

    table.sort(key=lambda r: {"🔥":0,"⚠️":1,"❌":2}[r["Dealer Risk"]])
    return table

# =====================
# OUTPUT
# =====================

def write_table_csv(path, table):
    if not table:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=table[0].keys())
        w.writeheader()
        w.writerows(table)

def write_summary_table(title, table, columns):
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary or not table:
        return

    shown = min(10, len(table))
    with open(summary, "a", encoding="utf-8") as f:
        f.write(f"\n## {title}\n\n")
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "|".join(["---"]*len(columns)) + "|\n")
        for r in table[:shown]:
            f.write("| " + " | ".join(str(r[c]) for c in columns) + " |\n")
        if len(table) > shown:
            f.write(
                f"\n_Showing top {shown} of {len(table)} entries — "
                f"see CSV artifact for full list._\n"
            )

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
            if e.response is not None and e.response.status_code == 404:
                break
            raise

        urls = extract_product_urls(html, url)
        if not urls:
            break

        for pu in urls:
            sci, com, size, price = scrape_product(pu)
            all_rows.append([scrape_dt, sci, com, size, price, url])

        page += 1

    if not all_rows:
        raise SystemExit("ERROR: Scrape returned ZERO rows")

    with open(SNAPSHOT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        w.writerows(all_rows)

    history_rows = load_history(HISTORY_FILE)
    existing = {tuple(r[h] for h in CSV_HEADER) for r in history_rows}

    new_rows = [r for r in all_rows if tuple(r) not in existing]
    append_history(HISTORY_FILE, new_rows)

    history_rows.extend(dict(zip(CSV_HEADER, r)) for r in new_rows)

    breeder = build_breeder_opportunity_table(history_rows)
    dealer = build_dealer_supply_risk_table(history_rows)

    write_table_csv(BREEDER_TABLE_FILE, breeder)
    write_table_csv(DEALER_TABLE_FILE, dealer)

    write_summary_table(
        "🧬 Breeder Opportunity Matrix",
        breeder,
        ["Species","Size (cm)","OOS","OOS Runs","Pattern","Signal","Recommendation"]
    )

    write_summary_table(
        "🏪 Dealer Supply Risk Matrix",
        dealer,
        ["Species","Size (cm)","Stock Reliability","Avg OOS Duration","Restock Speed","Dealer Risk","Dealer Recommendation"]
    )

    print(f"Snapshot rows: {len(all_rows)}")
    print(f"History rows added: {len(new_rows)}")

if __name__ == "__main__":
    main()

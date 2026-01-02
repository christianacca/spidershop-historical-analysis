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
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/6.3)",
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
    # IMPORTANT: keep both "£" and "\u00a3" handling
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
        href = a.get("href", "").strip()  # IMPORTANT: keep .strip()
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
# JOB SUMMARY — PRICING
# =====================

def write_pricing_summary(history_rows, scrape_datetime: str):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path or not history_rows:
        return

    by_run = {}
    for r in history_rows:
        by_run.setdefault(r["scrape_datetime"], []).append(r)

    run_times = sorted(by_run.keys())
    if not run_times:
        return

    current = by_run[run_times[-1]]
    previous = by_run[run_times[-2]] if len(run_times) > 1 else []

    def k3(r):
        return (r["scientific_name"], r["common_name"], r["size_cm"])

    cur_map = {k3(r): r for r in current}
    prev_map = {k3(r): r for r in previous}

    prices = [float(r["price_gbp"]) for r in current if r.get("price_gbp")]

    inc = dec = same = new = gone = 0
    movers = []

    for k, r in cur_map.items():
        if k not in prev_map:
            new += 1
            continue
        old_p = prev_map[k].get("price_gbp", "")
        new_p = r.get("price_gbp", "")
        if not old_p or not new_p:
            continue
        try:
            oldf = float(old_p)
            newf = float(new_p)
        except ValueError:
            continue

        if newf > oldf:
            inc += 1
        elif newf < oldf:
            dec += 1
        else:
            same += 1

        if oldf != 0:
            pct = (newf - oldf) / oldf
            movers.append((r["scientific_name"], r["size_cm"], oldf, newf, pct))

    for k in prev_map:
        if k not in cur_map:
            gone += 1

    movers.sort(key=lambda x: abs(x[4]), reverse=True)
    top5 = movers[:5]

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("## 🕷️ Spiderlings Pricing Summary\n\n")
        f.write(f"**Scrape time (UTC):** `{scrape_datetime}`\n\n")
        f.write(f"- Listings: **{len(current)}**\n")
        if prices:
            f.write(f"- Price range: **£{min(prices):.2f} – £{max(prices):.2f}**\n")

        f.write("\n### 🔄 Changes Since Last Run\n")
        f.write(f"- 🔼 Increases: **{inc}**\n")
        f.write(f"- 🔽 Decreases: **{dec}**\n")
        f.write(f"- ➖ Unchanged: **{same}**\n")
        f.write(f"- 🆕 New: **{new}**\n")
        f.write(f"- ❌ Removed: **{gone}**\n")

        f.write("\n### 🚀 Top 5 Price Movers\n")
        if not top5:
            f.write("_No comparable price changes detected._\n")
        else:
            f.write("| Species | Size | Old | New | Change |\n")
            f.write("|--------|------|-----|-----|--------|\n")
            for s, size, o, n, p in top5:
                sign = "+" if p > 0 else ""
                f.write(f"| {s} | {size} | £{o:.2f} | £{n:.2f} | {sign}{p*100:.1f}% |\n")

# =====================
# ANALYSIS HELPERS
# =====================

def group_by_run(rows):
    by_run = {}
    for r in rows:
        by_run.setdefault(r["scrape_datetime"], []).append(r)
    return by_run

def k2(r):
    return (r["scientific_name"], r["size_cm"])

# =====================
# BREEDER MATRIX (Phase 1)
# =====================

def build_breeder_opportunity_table(history_rows):
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    if len(runs) < 2:
        return []

    current = by_run[runs[-1]]
    prev = by_run[runs[-2]]
    prev_keys = {k2(r) for r in prev}

    table = []

    for r in current:
        k = k2(r)
        oos_runs = 0
        oos_status = "IN"

        if k not in prev_keys:
            oos_status = "OUT"
            for rt in reversed(runs[:-1]):
                if any(k2(x) == k for x in by_run[rt]):
                    break
                oos_runs += 1
        elif any(k not in {k2(x) for x in by_run[rt]} for rt in runs[-3:-1]):
            oos_status = "IN/OUT"

        if oos_runs >= 3:
            pattern = "Sustained"
            signal = "🔥"
            rec = "Pair soon — sustained scarcity"
        elif oos_runs == 2:
            pattern = "Emerging"
            signal = "🔥"
            rec = "Consider pairing — monitor supply"
        elif oos_status == "IN/OUT":
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
            "OOS": oos_status,
            "OOS Runs": str(oos_runs),
            "Pattern": pattern,
            "Signal": signal,
            "Recommendation": rec,
        })

    table.sort(key=lambda r: ({"🔥": 0, "⚠️": 1, "❌": 2}[r["Signal"]], -int(r["OOS Runs"])))
    return table

def write_breeder_opportunity_outputs(table):
    if not table:
        return

    total_rows = len(table)
    shown = min(10, total_rows)

    # CSV (full)
    with open(BREEDER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=table[0].keys())
        w.writeheader()
        w.writerows(table)

    # Job Summary (top 10 + footer)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n## 🧬 Breeder Opportunity Matrix\n\n")
        f.write("| Species | Size (cm) | OOS | OOS Runs | Pattern | Signal | Recommendation |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in table[:shown]:
            f.write(
                f"| {r['Species']} | {r['Size (cm)']} | {r['OOS']} | {r['OOS Runs']} | "
                f"{r['Pattern']} | {r['Signal']} | {r['Recommendation']} |\n"
            )
        if total_rows > shown:
            f.write(
                f"\n_Showing top {shown} of {total_rows} entries — "
                f"see `{BREEDER_TABLE_FILE}` for full list._\n"
            )

# =====================
# DEALER MATRIX (Phase 2 + Option B: Price Pressure)
# =====================

def build_dealer_supply_risk_table(history_rows):
    by_run = group_by_run(history_rows)
    runs = sorted(by_run)
    total_runs = len(runs)
    if total_runs < 2:
        return []

    # Presence map by (species,size)
    present_runs_map = {}
    for rt in runs:
        for r in by_run[rt]:
            present_runs_map.setdefault(k2(r), set()).add(rt)

    # Price pressure based on last two runs only (informational)
    prev_run = runs[-2]
    cur_run = runs[-1]
    prev_prices = {k2(r): r.get("price_gbp", "") for r in by_run[prev_run] if r.get("price_gbp")}
    cur_prices = {k2(r): r.get("price_gbp", "") for r in by_run[cur_run] if r.get("price_gbp")}

    table = []

    for (sci, size), present_runs in present_runs_map.items():
        present_pct = len(present_runs) / total_runs
        reliability = "High" if present_pct >= 0.8 else "Medium" if present_pct >= 0.4 else "Low"

        # Average OOS duration across OOS events
        oos_events = []
        last_present = None
        for rt in runs:
            present = rt in present_runs
            if last_present is True and not present:
                oos_events.append(1)
            elif last_present is False and not present:
                oos_events[-1] += 1
            last_present = present

        avg_oos = round(sum(oos_events) / len(oos_events), 1) if oos_events else 0
        speed = "Slow" if avg_oos >= 3 else "Moderate" if avg_oos == 2 else "Fast"

        # Price Pressure (Option B) — informational only
        pp = "→"
        if (sci, size) in prev_prices and (sci, size) in cur_prices:
            try:
                p_prev = float(prev_prices[(sci, size)])
                p_cur = float(cur_prices[(sci, size)])
                if p_cur > p_prev:
                    pp = "↑"
                elif p_cur < p_prev:
                    pp = "↓"
            except ValueError:
                pp = "→"

        # Dealer Risk (unchanged by price)
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
            "Price Pressure": pp,
            "Dealer Risk": risk,
            "Dealer Recommendation": rec,
        })

    table.sort(key=lambda r: {"🔥": 0, "⚠️": 1, "❌": 2}[r["Dealer Risk"]])
    return table

def write_dealer_supply_outputs(table):
    if not table:
        return

    total_rows = len(table)
    shown = min(10, total_rows)

    # CSV (full)
    with open(DEALER_TABLE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=table[0].keys())
        w.writeheader()
        w.writerows(table)

    # Job Summary (top 10 + footer)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n## 🏪 Dealer Supply Risk Matrix\n\n")
        f.write("| Species | Size (cm) | Stock Reliability | Avg OOS Duration | Restock Speed | Price Pressure | Dealer Risk | Dealer Recommendation |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in table[:shown]:
            f.write(
                f"| {r['Species']} | {r['Size (cm)']} | {r['Stock Reliability']} | {r['Avg OOS Duration']} | "
                f"{r['Restock Speed']} | {r['Price Pressure']} | {r['Dealer Risk']} | {r['Dealer Recommendation']} |\n"
            )
        if total_rows > shown:
            f.write(
                f"\n_Showing top {shown} of {total_rows} entries — "
                f"see `{DEALER_TABLE_FILE}` for full list._\n"
            )

# =====================
# MAIN
# =====================

def main():
    scrape_dt = datetime.now(timezone.utc).replace(second=0, microsecond=0).isoformat(timespec="minutes")

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
            all_rows.append([scrape_dt, sci, com, size, price, category_url])

        page += 1

    if not all_rows:
        raise SystemExit("ERROR: Scrape completed but returned ZERO rows")

    # Snapshot CSV
    with open(SNAPSHOT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        w.writerows(all_rows)

    # Load history (from downloaded artifact if present)
    history_rows = load_history(HISTORY_FILE)
    existing = {tuple(r[h] for h in CSV_HEADER) for r in history_rows}

    new_rows = [r for r in all_rows if tuple(r) not in existing]
    append_history(HISTORY_FILE, new_rows)

    # Extend in-memory rows for analysis
    history_rows.extend(dict(zip(CSV_HEADER, r)) for r in new_rows)

    # Job Summary: Pricing snapshot
    write_pricing_summary(history_rows, scrape_dt)

    # Phase 1: Breeder outputs
    breeder_table = build_breeder_opportunity_table(history_rows)
    write_breeder_opportunity_outputs(breeder_table)

    # Phase 2: Dealer outputs (Option B: includes Price Pressure column)
    dealer_table = build_dealer_supply_risk_table(history_rows)
    write_dealer_supply_outputs(dealer_table)

    print(f"Snapshot rows: {len(all_rows)}")
    print(f"New historical rows appended: {len(new_rows)}")

if __name__ == "__main__":
    main()

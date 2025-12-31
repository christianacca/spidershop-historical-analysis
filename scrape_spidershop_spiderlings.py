#!/usr/bin/env python3
import csv
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

BASE_URL = "https://thespidershop.co.uk/product-category/tarantulas-for-sale-in-the-uk/spiderlings/"
OUTFILE = "spidershop_spiderlings_scrape.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/2.2)",
    "Accept-Language": "en-GB,en;q=0.9",
}

PARENS_RE = re.compile(r"\(([^)]*)\)")
SIZE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(?:[-–]\s*(\d+(?:\.\d+)?))?\s*cm\s*$",
    re.IGNORECASE,
)

# ---------- Normalization ----------

def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    # Replace non-breaking & other odd unicode spaces with normal space
    text = text.replace("\u00a0", " ")
    # Collapse all whitespace runs
    return re.sub(r"\s+", " ", text).strip()

# ---------- HTTP ----------

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

# ---------- Parsing helpers ----------

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
        val = m.group(2) or m.group(1)  # upper bound
        d = Decimal(val)
        return str(int(d)) if d == d.to_integral_value() else format(d, "f")
    except InvalidOperation:
        return ""

def remove_size_parenthetical_only(text: str) -> str:
    text = normalize_whitespace(text)
    paren = first_cm_parenthetical(text)
    if not paren:
        return text
    cleaned = text.replace(paren, " ", 1)
    return normalize_whitespace(cleaned)

def parse_price(text: str) -> str:
    if not text:
        return ""
    s = (
        text.replace("£", "")
            .replace("\u00a3", "")
            .replace(",", "")
            .strip()
    )
    try:
        return format(Decimal(s), "f")
    except InvalidOperation:
        return ""

# ---------- Scraping ----------

def extract_product_urls(category_html: str, category_url: str):
    soup = BeautifulSoup(category_html, "html.parser")
    urls = []
    seen = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if "/product/" not in href:
            continue
        full = urljoin(category_url, href)
        if full in seen:
            continue
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
    price_gbp = parse_price(
        normalize_whitespace(price_el.get_text()) if price_el else ""
    )

    return scientific_name, common_name, size_cm, price_gbp

# ---------- Main ----------

def main():
    all_rows = []
    page = 1

    while True:
        category_url = BASE_URL if page == 1 else urljoin(BASE_URL, f"page/{page}/")
        try:
            category_html = fetch(category_url)
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                break  # normal end of pagination
            raise

        product_urls = extract_product_urls(category_html, category_url)
        if not product_urls:
            break

        for pu in product_urls:
            scientific_name, common_name, size_cm, price_gbp = scrape_product(pu)
            all_rows.append([
                scientific_name,
                common_name,
                size_cm,
                price_gbp,
                category_url
            ])

        page += 1

    with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "scientific_name",
            "common_name",
            "size_cm",
            "price_gbp",
            "page_url"
        ])
        w.writerows(all_rows)

    row_count = len(all_rows)
    print(f"Wrote {row_count} rows → {OUTFILE}")

    if row_count == 0:
        raise SystemExit("ERROR: Scrape completed but returned ZERO rows")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import csv
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://thespidershop.co.uk/product-category/tarantulas-for-sale-in-the-uk/spiderlings/"
OUTFILE = "spidershop_spiderlings_scrape.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/2.0)",
    "Accept-Language": "en-GB,en;q=0.9",
}

PARENS_RE = re.compile(r"\(([^)]*)\)")
SIZE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(?:[-–]\s*(\d+(?:\.\d+)?))?\s*cm\s*$",
    re.IGNORECASE,
)

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def first_cm_parenthetical(text: str):
    for m in PARENS_RE.finditer(text or ""):
        inner = m.group(1)
        if "cm" in inner.lower():
            return m.group(0)  # includes parentheses
    return None

def parse_size_cm_from_text(text: str) -> str:
    """
    - Find FIRST (...) containing 'cm'
    - Parse numeric; for ranges select upper bound
    - On failure return ""
    """
    paren = first_cm_parenthetical(text)
    if not paren:
        return ""
    inner = paren[1:-1]
    sm = SIZE_RE.match(inner)
    if not sm:
        return ""
    try:
        upper = sm.group(2) or sm.group(1)
        d = Decimal(upper)
        return str(int(d)) if d == d.to_integral_value() else format(d, "f")
    except InvalidOperation:
        return ""

def remove_size_parenthetical_only(text: str) -> str:
    """
    Remove ONLY the first parenthetical group that contains 'cm' (plus surrounding whitespace).
    """
    paren = first_cm_parenthetical(text)
    if not paren:
        return (text or "").strip()
    cleaned = (text or "").replace(paren, " ", 1)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def parse_price_gbp(text: str) -> str:
    if not text:
        return ""
    s = text.strip().replace("£", "").replace("\u00a3", "").replace(",", "").strip()
    try:
        return format(Decimal(s), "f")
    except InvalidOperation:
        return ""

def extract_product_urls(category_html: str, category_url: str):
    """
    Collect product links from the category page. We only take hrefs containing '/product/'.
    Deterministic, no inference.
    """
    soup = BeautifulSoup(category_html, "html.parser")
    urls = []
    seen = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        if "/product/" not in href:
            continue
        full = urljoin(category_url, href)
        if full in seen:
            continue
        seen.add(full)
        urls.append(full)

    return urls

def scrape_product(product_url: str):
    """
    Extract fields explicitly from the product page HTML:
    - scientific_name: <h1> (product title)
    - common_name: <h2> (the line that usually contains common name + size)
    - size_cm: parsed from that <h2> line using your rules
    - price_gbp: from price amount text
    """
    html = fetch(product_url)
    soup = BeautifulSoup(html, "html.parser")

    # scientific_name from H1
    h1 = soup.find("h1")
    scientific_name = h1.get_text(strip=True) if h1 else ""

    # common name line is typically an H2 on product page (as seen on site)
    # We take the first <h2> after h1, but we don't assume structure beyond tag presence.
    h2s = soup.find_all("h2")
    common_line = h2s[0].get_text(strip=True) if h2s else ""

    common_name = remove_size_parenthetical_only(common_line) if common_line else ""
    size_cm = parse_size_cm_from_text(common_line) if common_line else ""

    # price: prefer WooCommerce price amount element if present
    price_text = ""
    price_el = soup.select_one(".price .woocommerce-Price-amount, .woocommerce-Price-amount")
    if price_el:
        price_text = price_el.get_text(strip=True)

    price_gbp = parse_price_gbp(price_text)

    return scientific_name, common_name, size_cm, price_gbp

def main():
    all_rows = []
    page = 1

    while True:
        category_url = BASE_URL if page == 1 else urljoin(BASE_URL, f"page/{page}/")
        category_html = fetch(category_url)

        product_urls = extract_product_urls(category_html, category_url)
        if not product_urls:
            break

        for pu in product_urls:
            scientific_name, common_name, size_cm, price_gbp = scrape_product(pu)
            all_rows.append([scientific_name, common_name, size_cm, price_gbp, category_url])

        page += 1

    with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scientific_name", "common_name", "size_cm", "price_gbp", "page_url"])
        w.writerows(all_rows)

    row_count = len(all_rows)
    print(f"Wrote {row_count} rows → {OUTFILE}")

    if row_count == 0:
        raise SystemExit("ERROR: Scrape completed but returned ZERO rows")

if __name__ == "__main__":
    main()

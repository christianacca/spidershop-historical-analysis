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
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/1.2)",
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

def extract_size_cm(title_text: str) -> str:
    for m in PARENS_RE.finditer(title_text):
        inner = m.group(1)
        if "cm" not in inner.lower():
            continue
        sm = SIZE_RE.match(inner)
        if not sm:
            return ""
        try:
            upper = sm.group(2) or sm.group(1)
            d = Decimal(upper)
            return str(int(d)) if d == d.to_integral_value() else format(d, "f")
        except InvalidOperation:
            return ""
    return ""

def extract_common_name(title_text: str) -> str:
    for m in PARENS_RE.finditer(title_text):
        if "cm" in m.group(1).lower():
            title_text = title_text.replace(m.group(0), "", 1)
            break
    return re.sub(r"\s+", " ", title_text).strip()

def extract_price(bdi) -> str:
    if not bdi:
        return ""
    text = bdi.get_text(strip=True).replace("£", "").replace(",", "")
    try:
        return format(Decimal(text), "f")
    except InvalidOperation:
        return ""

def scrape_page(html: str, page_url: str):
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    products = soup.select("li.product")

    for p in products:
        title = p.select_one("h2.woocommerce-loop-product__title")
        price = p.select_one("bdi")

        if not title:
            continue

        title_text = title.get_text(strip=True)

        scientific_name = title_text
        common_name = extract_common_name(title_text)
        size_cm = extract_size_cm(title_text)
        price_gbp = extract_price(price)

        rows.append([
            scientific_name,
            common_name,
            size_cm,
            price_gbp,
            page_url
        ])

    return rows

def main():
    all_rows = []
    page = 1

    while True:
        url = BASE_URL if page == 1 else urljoin(BASE_URL, f"page/{page}/")
        html = fetch(url)

        rows = scrape_page(html, url)
        if not rows:
            break

        all_rows.extend(rows)
        page += 1

    with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scientific_name",
            "common_name",
            "size_cm",
            "price_gbp",
            "page_url",
        ])
        writer.writerows(all_rows)

    row_count = len(all_rows)
    print(f"Wrote {row_count} rows → {OUTFILE}")

    if row_count == 0:
        raise SystemExit("ERROR: Scrape completed but returned ZERO rows")

if __name__ == "__main__":
    main()

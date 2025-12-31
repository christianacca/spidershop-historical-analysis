#!/usr/bin/env python3
import csv
import re
import sys
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://thespidershop.co.uk/product-category/tarantulas-for-sale-in-the-uk/spiderlings/"
OUTFILE = "spidershop_spiderlings_scrape.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; spidershop-scraper/1.0; +https://example.com)",
    "Accept-Language": "en-GB,en;q=0.9",
}

# --- Regex helpers (deterministic) ---

PARENS_RE = re.compile(r"\(([^)]*)\)")
CM_IN_PARENS_RE = re.compile(r"\(([^)]*cm[^)]*)\)", re.IGNORECASE)

# Accept: 2cm, 0.5cm, 1-2cm, 0.5-1cm, 2 - 3 cm, hyphen variants "-" or "–"
SIZE_RE = re.compile(
    r"^\s*(?P<a>\d+(?:\.\d+)?)\s*(?:(?:-|–)\s*(?P<b>\d+(?:\.\d+)?))?\s*cm\s*$",
    re.IGNORECASE,
)

def first_cm_parenthetical(h3_text: str):
    """Return the full '(...)' text for the FIRST parenthetical group containing 'cm' (case-insensitive)."""
    matches = list(PARENS_RE.finditer(h3_text))
    for m in matches:
        inner = m.group(1)
        if re.search(r"cm", inner, flags=re.IGNORECASE):
            return "(" + inner + ")"
    return None

def parse_size_cm_from_h3(h3_text: str) -> str:
    """
    Implements your exact size rules:
    - Find FIRST parentheses group containing 'cm'
    - Parse formats; for ranges, select upper bound
    - On failure, return empty string
    """
    paren = first_cm_parenthetical(h3_text)
    if not paren:
        return ""

    inner = paren[1:-1]  # remove surrounding parentheses
    m = SIZE_RE.match(inner)
    if not m:
        return ""

    try:
        a = Decimal(m.group("a"))
        b_str = m.group("b")
        if b_str is not None:
            b = Decimal(b_str)
            val = b  # upper bound
        else:
            val = a
        # Preserve as plain string (no inference/rounding)
        # Normalize Decimal like "2.0" -> "2" only if exact integer
        if val == val.to_integral_value():
            return str(int(val))
        return format(val.normalize(), "f").rstrip("0").rstrip(".") if "." in str(val) else str(val)
    except (InvalidOperation, ValueError):
        return ""

def common_name_from_h3(h3_text: str) -> str:
    """
    - Remove ONLY the FIRST parenthetical group that contains 'cm' (plus surrounding whitespace).
    - Do NOT remove other parentheses not containing 'cm'.
    """
    paren = first_cm_parenthetical(h3_text)
    if not paren:
        return h3_text.strip()

    # Remove that specific substring, plus surrounding whitespace
    # We do a targeted replace once.
    cleaned = h3_text.replace(paren, " ", 1)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def parse_price_gbp_from_bdi(bdi_text: str) -> str:
    """
    - Extract numeric value from <bdi> text.
    - Remove currency symbols and formatting.
    - Example: "£15.00" -> "15.00"
    - If parse fails, return empty string.
    """
    if not bdi_text:
        return ""
    # Strip currency symbols and whitespace, keep digits, dot, comma
    s = bdi_text.strip()
    s = s.replace("£", "").replace("\u00a3", "")
    s = s.replace(",", "")
    s = s.strip()
    # Validate numeric
    try:
        d = Decimal(s)
        # Keep 2dp if provided; otherwise keep exact decimal
        return format(d, "f")
    except (InvalidOperation, ValueError):
        return ""

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def extract_listings(html: str, page_url: str):
    soup = BeautifulSoup(html, "html.parser")

    # WooCommerce typical: <li class="product"> ... with h2/h3 in some theme variants.
    # We will extract any element that contains an <h2> and <h3> and a <bdi> within a product card.
    products = soup.select("li.product, .product, .woocommerce-LoopProduct-link")

    rows = []
    seen = set()

    for p in products:
        h2 = p.find("h2")
        h3 = p.find("h3")
        bdi = p.find("bdi")

        scientific_name = h2.get_text(strip=True) if h2 else ""
        h3_text = h3.get_text(strip=True) if h3 else ""
        common_name = common_name_from_h3(h3_text) if h3_text else ""
        size_cm = parse_size_cm_from_h3(h3_text) if h3_text else ""
        price_gbp = parse_price_gbp_from_bdi(bdi.get_text(strip=True) if bdi else "")

        # One row per listing ONLY if we have at least a scientific name OR h3 text OR price;
        # but we won't invent anything. We also de-duplicate identical rows per page.
        if not (scientific_name or h3_text or (bdi and bdi.get_text(strip=True))):
            continue

        row = (scientific_name, common_name, size_cm, price_gbp, page_url)
        if row in seen:
            continue
        seen.add(row)
        rows.append(row)

    return rows

def page_has_listings(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    # Heuristic: if there is at least one <h2> inside a product element
    for p in soup.select("li.product, .product"):
        if p.find("h2"):
            return True
    return False

def main():
    all_rows = []
    page_num = 1

    while True:
        page_url = BASE_URL if page_num == 1 else urljoin(BASE_URL, f"page/{page_num}/")
        try:
            html = fetch(page_url)
        except requests.HTTPError as e:
            # Stop on first missing page / 404 etc (no inference)
            break
        except Exception as e:
            print(f"ERROR fetching {page_url}: {e}", file=sys.stderr)
            break

        if not page_has_listings(html):
            break

        rows = extract_listings(html, page_url)
        if not rows:
            break

        all_rows.extend(rows)
        page_num += 1

    with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scientific_name", "common_name", "size_cm", "price_gbp", "page_url"])
        for r in all_rows:
            w.writerow(r)

    print(OUTFILE)

if __name__ == "__main__":
    main()

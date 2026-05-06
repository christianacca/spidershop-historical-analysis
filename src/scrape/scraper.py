#!/usr/bin/env python3
from typing import List, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scrape.http_client import fetch
from scrape.browser_client import fetch_with_browser
from shared.parsing import normalize_whitespace, remove_size_parenthetical_only, parse_size_cm, parse_price, parse_wishlist_count

# =====================
# SCRAPING
# =====================

def extract_product_urls(category_html: str, category_url: str) -> List[str]:
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

def scrape_product(product_url: str) -> Tuple[str, str, str, str, str, str]:
    # Use browser automation to handle JavaScript-rendered wishlist counter
    # Wait for the wishlist element to load (with timeout fallback)
    html = fetch_with_browser(product_url, wait_for_selector=".yith-wcwl-add-to-wishlist__counter", timeout=10)
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    scientific_name = ""
    if h1:
        scientific_name = normalize_whitespace(h1.get_text())

    h2 = soup.find("h2")
    common_line = ""
    if h2:
        common_line = normalize_whitespace(h2.get_text())

    common_name = remove_size_parenthetical_only(common_line)
    size_cm = parse_size_cm(common_line)

    price_el = soup.select_one(".woocommerce-Price-amount")
    price_text = ""
    if price_el:
        price_text = normalize_whitespace(price_el.get_text())
    price_gbp = parse_price(price_text)

    wishlist_el = soup.select_one(".yith-wcwl-add-to-wishlist__counter")
    wishlist_text = ""
    if wishlist_el:
        wishlist_text = normalize_whitespace(wishlist_el.get_text())
    wishlist_count = parse_wishlist_count(wishlist_text)

    lifestyle_el = soup.select_one(".spices-info .col.lifestyle .rowb")
    lifestyle = ""
    if lifestyle_el:
        lifestyle = normalize_whitespace(lifestyle_el.get_text())

    return scientific_name, common_name, size_cm, price_gbp, wishlist_count, lifestyle

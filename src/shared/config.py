#!/usr/bin/env python3
import re

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
    "wishlist_count",
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
WISHLIST_COUNT_RE = re.compile(r"(\d+)\s+users?\s+(?:has|have)\s+this\s+item\s+in\s+their\s+wishlists?", re.IGNORECASE)

# Wishlist analysis thresholds
WISHLIST_DELTA_INCREASE_THRESHOLD = 5
WISHLIST_DELTA_DECREASE_THRESHOLD = -5
OOS_CARRYOVER_LOOKBACK = 5
WISHLIST_DELTA_LOOKBACK = 3
WISHLIST_DELTA_PREV_LOOKBACK = 12
WISHLIST_SMALL_N_FLATTEN_THRESHOLD = 1

# Signal priority for sorting (lower number = higher priority)
SIGNAL_PRIORITY = {"🔥": 0, "⚠️": 1, "❌": 2}
TREND_PRIORITY = {"↑": 0, "→": 1, "↓": 2}

# Polite scraping — rate-limit handling
REQUEST_DELAY_SECONDS = 2.0   # fixed pause before every HTTP request
REQUEST_MAX_RETRIES = 3       # max retries on 429 before giving up

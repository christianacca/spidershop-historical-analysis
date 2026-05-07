#!/usr/bin/env python3
"""
General-purpose history CSV fixup system.

A fixup is a standalone transformation that corrects a known data quality issue
in the accumulated history CSV.  Each fixup:
  - receives the full list of history rows (dicts)
  - returns a (possibly modified) list of rows plus a FixupStats summary
  - must not raise — errors are captured in FixupStats.errors

REGISTERED_FIXUPS is the single authoritative list of fixups to run, in order.
PageUrlFixup must precede LifestyleFixup so that corrected URLs are available
when LifestyleFixup fetches product pages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol, List, Tuple, Dict, Any

from bs4 import BeautifulSoup
from requests.exceptions import HTTPError

from scrape.http_client import fetch


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class FixupStats:
    name: str
    rows_changed: int = 0
    errors: List[str] = field(default_factory=list)


class Fixup(Protocol):
    def apply(self, rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], FixupStats]:
        ...


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BAD_URL_RE = re.compile(r"/page/\d+/")


def _is_bad_url(url: str) -> bool:
    """True when the URL is a paged listing URL rather than a product detail URL."""
    return "/product/" not in url


def _derive_product_url(scientific_name: str) -> str:
    slug = scientific_name.lower().replace(" ", "-")
    return f"https://www.thespidershop.co.uk/product/{slug}/"


def _parse_lifestyle(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    el = soup.select_one(".spices-info .col.lifestyle .rowb")
    if el is None:
        return ""
    return el.get_text(strip=True)


# ---------------------------------------------------------------------------
# PageUrlFixup
# ---------------------------------------------------------------------------

class PageUrlFixup:
    """
    Corrects rows where page_url is a paged listing URL (e.g. /page/2/) rather
    than a product detail URL (e.g. /product/aphonopelma-seemanni/).

    Fix priority per species:
      1. Use the first /product/ URL found in another row for the same species.
      2. Derive the URL from the scientific name slug (no network call).
    """

    def apply(self, rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], FixupStats]:
        stats = FixupStats(name="PageUrlFixup")

        # Build a map: scientific_name → first /product/ URL seen across all rows
        good_urls: Dict[str, str] = {}
        for row in rows:
            name = row["scientific_name"]
            if name not in good_urls and not _is_bad_url(row["page_url"]):
                good_urls[name] = row["page_url"]

        for row in rows:
            if not _is_bad_url(row["page_url"]):
                continue
            name = row["scientific_name"]
            fixed = good_urls.get(name) or _derive_product_url(name)
            row["page_url"] = fixed
            stats.rows_changed += 1

        return rows, stats


# ---------------------------------------------------------------------------
# LifestyleFixup
# ---------------------------------------------------------------------------

class LifestyleFixup:
    """
    Backfills the lifestyle field for species where every row has lifestyle == "".

    For each such species:
      - Finds the first /product/ URL in the rows for that species.
      - Fetches the product page via http_client.fetch() (server-rendered HTML,
        no Chrome required).
      - Parses .spices-info .col.lifestyle .rowb.
      - Sets the value on all rows for the species.

    Errors (HTTPError, element not found) are captured in FixupStats.errors;
    the lifestyle field is left as "" in those cases.
    """

    def apply(self, rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], FixupStats]:
        stats = FixupStats(name="LifestyleFixup")

        # Group rows by scientific_name
        species_rows: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            species_rows.setdefault(row["scientific_name"], []).append(row)

        for name, species in species_rows.items():
            # Skip species that already have a lifestyle value in any row
            if any(r.get("lifestyle", "") for r in species):
                continue

            # Find the first /product/ URL to fetch from
            product_url = next(
                (r["page_url"] for r in species if not _is_bad_url(r["page_url"])),
                None,
            )
            if product_url is None:
                continue  # no usable URL — skip silently

            try:
                html = fetch(product_url)
                lifestyle = _parse_lifestyle(html)
                if lifestyle:
                    for row in species:
                        row["lifestyle"] = lifestyle
                        stats.rows_changed += 1
            except HTTPError as exc:
                stats.errors.append(
                    f"{name}: HTTP error fetching {product_url} — {exc}"
                )

        return rows, stats


# ---------------------------------------------------------------------------
# apply_all_fixups
# ---------------------------------------------------------------------------

def apply_all_fixups(
    rows: List[Dict[str, Any]],
    fixups: List[Fixup],
) -> Tuple[List[Dict[str, Any]], List[FixupStats]]:
    """Run fixups sequentially; each receives the output of the previous one."""
    all_stats: List[FixupStats] = []
    for fixup in fixups:
        rows, stats = fixup.apply(rows)
        all_stats.append(stats)
    return rows, all_stats


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

REGISTERED_FIXUPS: List[Fixup] = [
    PageUrlFixup(),
    LifestyleFixup(),
]

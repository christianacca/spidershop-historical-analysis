"""History chart data DTO for the history chart/KPI page.

Provides a pure function that transforms flat history CSV rows into a
structured payload suitable for client-side time-series charting.  No file
I/O, no HTML, no templates — data in, dict out.
"""

from typing import Optional


def _coerce_price(raw: Optional[str]) -> Optional[float]:
    """Return ``float`` for non-empty strings, ``None`` otherwise."""
    if not raw:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


def _coerce_wishlist(raw: Optional[str]) -> Optional[int]:
    """Return ``int`` for non-empty strings, ``None`` otherwise."""
    if not raw:
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def build_history_chart_dto(history_rows: list[dict]) -> dict:
    """Convert flat history CSV rows into a structured chart/KPI payload.

    Args:
        history_rows: List of dicts keyed by CSV column name (``scrape_datetime``,
            ``scientific_name``, ``common_name``, ``price_gbp``, ``wishlist_count``,
            ``size_cm``, ``page_url``).  The list may contain rows for multiple
            species and multiple scrape dates.

    Returns:
        A dict with two keys:

        - ``species`` — a list of per-species dicts, each containing
          ``scientific_name``, ``common_name``, and ``runs`` (list of
          :class:`HistoryChartRun`-shaped dicts sorted chronologically by
          ``date``).
        - ``scrape_dates`` — a chronologically sorted, deduplicated list of all
          scrape datetime strings across every species.

    Example::

        rows = [
            {"scrape_datetime": "2026-01-01T06:10:00", "scientific_name": "Brachypelma hamorii",
             "common_name": "Mexican Red Knee", "price_gbp": "14.99", "wishlist_count": "3",
             "size_cm": "1.5", "page_url": "https://example.com"},
        ]
        result = build_history_chart_dto(rows)
        # {
        #   "species": [
        #       {"scientific_name": "Brachypelma hamorii", "common_name": "Mexican Red Knee",
        #        "runs": [{"date": "2026-01-01T06:10:00", "price_gbp": 14.99,
        #                  "wishlist_count": 3, "in_stock": True}]}
        #   ],
        #   "scrape_dates": ["2026-01-01T06:10:00"]
        # }
    """
    if not history_rows:
        return {"species": [], "scrape_dates": []}

    # Preserve insertion order for species (dict preserves insertion order in Python 3.7+)
    species_map: dict[str, dict] = {}
    all_dates: set[str] = set()

    for row in history_rows:
        scientific_name: str = row.get("scientific_name", "")
        common_name: str = row.get("common_name", "")
        scrape_datetime: str = row.get("scrape_datetime", "")
        raw_price: Optional[str] = row.get("price_gbp")
        raw_wishlist: Optional[str] = row.get("wishlist_count")

        price_gbp = _coerce_price(raw_price)
        wishlist_count = _coerce_wishlist(raw_wishlist)
        in_stock = bool(raw_price)

        run = {
            "date": scrape_datetime,
            "price_gbp": price_gbp,
            "wishlist_count": wishlist_count,
            "in_stock": in_stock,
        }

        if scientific_name not in species_map:
            species_map[scientific_name] = {
                "scientific_name": scientific_name,
                "common_name": common_name,
                "runs": [],
            }

        species_map[scientific_name]["runs"].append(run)
        all_dates.add(scrape_datetime)

    for entry in species_map.values():
        entry["runs"].sort(key=lambda r: r["date"])

    return {
        "species": list(species_map.values()),
        "scrape_dates": sorted(all_dates),
    }

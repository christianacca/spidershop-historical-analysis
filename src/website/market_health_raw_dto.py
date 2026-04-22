"""Raw Market Health DTO — serialises history CSV rows into the minimal payload
consumed by the client-side market-health-engine.ts.

No KPI computation, no window logic, no copy strings. Data in, records out.

Public API:
    build_raw_market_health_data(history_rows: list[dict]) -> dict
"""


def build_raw_market_health_data(history_rows: list[dict]) -> dict:
    """Serialise history CSV rows into the raw payload for the client-side engine.

    Each source row (one per species × size-variant × scrape run) is preserved
    as a variant-level record.  The client-side engine deduplicates to
    species-level and applies window logic internally.

    Args:
        history_rows: List of dicts, one per CSV row.  Expected keys:
            ``scrape_datetime``, ``scientific_name``, ``size_cm``,
            ``page_url``, ``wishlist_count``, ``price_gbp``.

    Returns:
        A dict with two keys:
        - ``records``: list of variant-level dicts matching the TypeScript
          ``RawRunRecord`` interface.
        - ``referenceDate``: ISO string of the most recent ``scrape_datetime``
          in the source data, or an empty string when ``history_rows`` is empty.
    """
    records = []
    for row in history_rows:
        scientific_name = row.get("scientific_name", "")
        scrape_datetime = row.get("scrape_datetime", "")

        # Skip rows that are entirely empty on the identity fields
        if not scientific_name and not scrape_datetime:
            continue

        try:
            wishlist_count = int(row.get("wishlist_count", 0) or 0)
        except (ValueError, TypeError):
            wishlist_count = 0

        try:
            price_gbp = float(row.get("price_gbp", 0.0) or 0.0)
        except (ValueError, TypeError):
            price_gbp = 0.0

        records.append({
            "scrapeDatetime": scrape_datetime,
            "scientificName": scientific_name,
            "sizeVariant": row.get("size_cm", ""),
            "pageUrl": row.get("page_url", ""),
            "wishlistCount": wishlist_count,
            "priceGbp": price_gbp,
        })

    reference_date = ""
    if history_rows:
        datetimes = [
            r.get("scrape_datetime", "")
            for r in history_rows
            if r.get("scrape_datetime", "")
        ]
        if datetimes:
            reference_date = max(datetimes)

    return {
        "records": records,
        "referenceDate": reference_date,
    }

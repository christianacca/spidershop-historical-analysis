#!/usr/bin/env python3
import logging
import time
import requests
from shared.config import HEADERS, REQUEST_DELAY_SECONDS, REQUEST_MAX_RETRIES

logger = logging.getLogger(__name__)

# =====================
# HTTP CLIENT
# =====================

def fetch(url: str) -> str:
    time.sleep(REQUEST_DELAY_SECONDS)

    for attempt in range(REQUEST_MAX_RETRIES + 1):
        r = requests.get(url, headers=HEADERS, timeout=30)

        if r.status_code != 429 or attempt == REQUEST_MAX_RETRIES:
            r.raise_for_status()
            return r.text

        retry_after = r.headers.get("Retry-After")
        try:
            wait = float(retry_after) + 1.0 if retry_after is not None else 2 ** (attempt + 1)
        except ValueError:
            wait = 2 ** (attempt + 1)

        logger.warning(
            "Rate limited (429) fetching %s — attempt %d/%d, waiting %.1fs%s",
            url,
            attempt + 1,
            REQUEST_MAX_RETRIES,
            wait,
            f" (Retry-After: {retry_after})" if retry_after else "",
        )
        print(
            f"⚠️  Rate limited (429): {url} — attempt {attempt + 1}/{REQUEST_MAX_RETRIES},"
            f" waiting {wait:.1f}s{f' (Retry-After: {retry_after})' if retry_after else ''}",
            flush=True,
        )
        time.sleep(wait)

    raise RuntimeError("fetch: unreachable")  # pragma: no cover

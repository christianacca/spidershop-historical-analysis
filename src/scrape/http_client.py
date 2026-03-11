#!/usr/bin/env python3
import time
import requests
from shared.config import HEADERS, REQUEST_DELAY_SECONDS, REQUEST_MAX_RETRIES

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

        time.sleep(wait)

    raise RuntimeError("fetch: unreachable")  # pragma: no cover

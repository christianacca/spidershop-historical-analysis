#!/usr/bin/env python3
import requests
from shared.config import HEADERS

# =====================
# HTTP CLIENT
# =====================

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

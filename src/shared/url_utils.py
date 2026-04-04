#!/usr/bin/env python3
"""URL normalization utilities for size-variant identity detection."""

import re
from urllib.parse import urlparse, urlunparse

_DUPLICATE_SLASH_RE = re.compile(r"//+")


def normalize_product_url(url: str) -> str:
    """Normalize a product URL for identity comparison.

    Applies the following transformations (per spec):
    1. Trim leading and trailing whitespace.
    2. Discard any query string.
    3. Discard any fragment.
    4. Lowercase the scheme and host.
    5. Strip a leading ``www.`` from the host.
    6. Collapse duplicate ``/`` characters in the path.
    7. Strip exactly one trailing slash from the path.
    8. Preserve the remaining path string as-is.

    Returns the empty string for blank or unparseable inputs.

    Examples::

        >>> normalize_product_url("HTTPS://www.thespidershop.co.uk/product/foo/?bar=1#frag")
        'https://thespidershop.co.uk/product/foo'
        >>> normalize_product_url("https://thespidershop.co.uk/product/foo/")
        'https://thespidershop.co.uk/product/foo'
    """
    url = url.strip()
    if not url:
        return ""

    parsed = urlparse(url)

    # If there is no scheme, urlparse puts everything in path/netloc
    # and cannot meaningfully normalize; return the stripped input as-is.
    if not parsed.scheme:
        return url

    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()

    # Strip exactly one leading "www." from host (handles "www.example.com" → "example.com")
    if host.startswith("www."):
        host = host[4:]

    # Collapse duplicate slashes in path
    path = _DUPLICATE_SLASH_RE.sub("/", parsed.path)

    # Strip exactly one trailing slash from path
    if path.endswith("/") and len(path) > 1:
        path = path[:-1]

    # Reconstruct without query or fragment
    return urlunparse((scheme, host, path, "", "", ""))

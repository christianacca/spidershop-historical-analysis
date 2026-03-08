"""CSS design-token helper for E2E tests.

Parses ``--custom-property: value;`` declarations from ``templates/common.css``
and provides hex-to-rgb conversion so E2E style assertions can reference tokens
by name instead of hardcoded hex or rgb values.

Usage::

    from e2e.css_tokens import token_rgb, hex_to_rgb

    # Assert against a token value
    assert token_rgb('--color-accent') in computed_bg  # 'rgb(52, 152, 219)'

    # Assert against a value that lives in a component stylesheet (not common.css)
    assert hex_to_rgb('#16a34a') in computed_bg  # 'rgb(22, 163, 74)'
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

# Resolved relative to this file so the path is correct regardless of cwd.
_COMMON_CSS = Path(__file__).parents[2] / "templates" / "common.css"


@lru_cache(maxsize=1)
def _parse_tokens() -> dict[str, str]:
    """Parse all ``--name: value;`` declarations from the :root block of common.css."""
    text = _COMMON_CSS.read_text(encoding="utf-8")
    root_match = re.search(r":root\s*\{([^}]+)\}", text, re.DOTALL)
    if not root_match:
        return {}
    block = root_match.group(1)
    result: dict[str, str] = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+)", block):
        name = m.group(1)
        # Strip inline /* comments */ and surrounding whitespace
        value = re.sub(r"/\*.*?\*/", "", m.group(2)).strip()
        result[name] = value
    return result


def hex_to_rgb(hex_color: str) -> str:
    """Convert a hex colour to the ``rgb(r, g, b)`` string returned by ``getComputedStyle``.

    Accepts both 6-digit (``#rrggbb``) and 3-digit shorthand (``#rgb``) forms.
    Case-insensitive.

    Examples::

        hex_to_rgb('#3498db')  # 'rgb(52, 152, 219)'
        hex_to_rgb('#fff')     # 'rgb(255, 255, 255)'
    """
    h = hex_color.lstrip("#").lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgb({r}, {g}, {b})"


def token_rgb(name: str) -> str:
    """Return the ``rgb(r, g, b)`` string for a CSS custom property from ``common.css``.

    Args:
        name: CSS custom property name including the leading ``--``,
              e.g. ``'--color-accent'``.

    Returns:
        A string such as ``'rgb(52, 152, 219)'``.

    Raises:
        KeyError: if *name* is not found in the ``common.css`` ``:root`` block.
        ValueError: if the token's value is not a hex colour.

    Example::

        bg = element.evaluate('el => window.getComputedStyle(el).backgroundColor')
        assert token_rgb('--color-accent') in bg
    """
    tokens = _parse_tokens()
    if name not in tokens:
        raise KeyError(f"Token {name!r} not found in common.css :root block")
    value = tokens[name]
    if not value.startswith("#"):
        raise ValueError(
            f"Token {name!r} value {value!r} is not a hex color; "
            "only hex tokens can be converted to rgb() format"
        )
    return hex_to_rgb(value)

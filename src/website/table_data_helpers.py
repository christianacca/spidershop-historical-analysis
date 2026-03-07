"""Table data serialisation helpers for Svelte component mounting.

Provides utilities to convert server-side table data into JSON payloads that
Svelte components read from ``window.<tableId>Data`` at runtime.
"""

from typing import Any, List


def rows_to_json(headers: List[str], rows: List[List[Any]]) -> List[dict]:
    """Convert raw table rows to a JSON-serialisable list of dicts keyed by column name.

    Args:
        headers: Column header strings (display names, not raw CSV names).
        rows: Raw row data as ``List[List[Any]]`` — pre-enumeration and ideally
              pre-sparkline-conversion.  If a cell value is a string that starts
              with ``'<svg'`` it is **omitted** from the resulting dict (SVG markup
              is too large for inline JSON; the Svelte component regenerates SVG
              on the client from the original Unicode sparkline string).

    Returns:
        ``List[dict]`` — one dict per row, keyed by the corresponding header name.
        Rows with SVG cells have those keys absent; all other cells are included
        with their original value (str, int, float, or None converted to ``""``).

    Example::

        headers = ["Species", "Price", "Signal"]
        rows = [["Brachypelma hamorii", "£14.99", "🔥 Hot"]]
        result = rows_to_json(headers, rows)
        # [{"Species": "Brachypelma hamorii", "Price": "£14.99", "Signal": "🔥 Hot"}]
    """
    if not headers or not rows:
        return []

    result: List[dict] = []
    for row in rows:
        row_dict: dict = {}
        for i, value in enumerate(row):
            if i >= len(headers):
                break
            row_dict[headers[i]] = value
        result.append(row_dict)
    return result

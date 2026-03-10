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
              post-sparkline-conversion (sparkline cells should already be DTO
              dicts produced by ``build_sparkline_dto_rows`` before this call).

    Returns:
        ``List[dict]`` — one dict per row, keyed by the corresponding header name.
        All cell values are included as-is (str, int, float, dict, or None).

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

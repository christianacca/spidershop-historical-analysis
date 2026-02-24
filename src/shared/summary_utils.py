"""Shared GitHub Actions step-summary utilities for matrix output."""

from dataclasses import dataclass
from typing import Any, Dict, List

from shared.assertions import get_summary_path

# Columns whose values should be right-aligned in the markdown table.
_RIGHT_ALIGN_COLUMNS = {"OOS Runs", "Avg OOS Duration"}


def _column_separator(column_name: str) -> str:
    return "---:" if column_name.endswith("(cm)") or column_name in _RIGHT_ALIGN_COLUMNS else "---"


@dataclass
class MatrixSummaryConfig:
    """Configuration for generating a matrix summary section in GitHub Actions step summary.

    Attributes:
        title: Section heading (without the "Top N" suffix), e.g. "🧬 Breeder Opportunity Matrix".
        csv_filepath: Path to the CSV file, used in the "see full list" footer note.
        empty_message: Message shown when the table has no rows.
        indicator_field: Row key used to count signal/risk totals, e.g. "Signal".
        indicator_labels: Mapping of emoji indicator → human-readable label,
            e.g. {"🔥": "Hot", "⚠️": "Watch", "❌": "Avoid"}.
        table_columns: Ordered list of column names to include in the markdown table
            (the "Drivers" column is intentionally omitted from the summary display).
    """

    title: str
    csv_filepath: str
    empty_message: str
    indicator_field: str
    indicator_labels: Dict[str, str]
    table_columns: List[str]


def write_matrix_summary(
    table: List[Dict[str, Any]],
    config: MatrixSummaryConfig,
    max_shown: int = 10,
) -> bool:
    """Write a matrix summary section to the GitHub Actions step summary file.

    Produces a heading, optional statistics line, and a markdown table limited to
    *max_shown* rows.  Does nothing (returns False) when the step-summary path is
    not available (i.e. not running inside GitHub Actions).

    Args:
        table: Sorted list of row dicts produced by the matrix builder.
        config: Display configuration for this matrix type.
        max_shown: Maximum number of rows to include in the summary table.

    Returns:
        True if the summary was written, False if no summary path was available.
    """
    summary_path = get_summary_path()
    if not summary_path:
        return False

    total = len(table) if table else 0
    shown = min(max_shown, total)

    indicator_counts: Dict[str, int] = {emoji: 0 for emoji in config.indicator_labels}
    for row in table:
        indicator = row.get(config.indicator_field, "")
        if indicator in indicator_counts:
            indicator_counts[indicator] += 1

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(f"\n## {config.title} (Top {max_shown})\n\n")
        if total == 0:
            f.write(f"_{config.empty_message}_\n")
            return True

        stats_parts = [f"{total} species analyzed"]
        for emoji, label in config.indicator_labels.items():
            stats_parts.append(f"{emoji} {label}: {indicator_counts[emoji]}")
        f.write(f"**Summary:** {' | '.join(stats_parts)}\n\n")

        # Header row
        header = " | ".join(config.table_columns)
        f.write(f"| {header} |\n")

        # Separator row
        separators = [_column_separator(col) for col in config.table_columns]
        separator = "|" + "|".join(separators) + "|"
        f.write(f"{separator}\n")

        # Data rows
        for row in table[:shown]:
            values = " | ".join(str(row.get(col, "")) for col in config.table_columns)
            f.write(f"| {values} |\n")

        if total > shown:
            f.write(
                f"\n_Showing top {shown} of {total} entries"
                f" — see `{config.csv_filepath}` for full list._\n"
            )

    return True

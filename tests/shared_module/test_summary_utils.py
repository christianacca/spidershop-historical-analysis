"""Tests for shared GitHub Actions summary writing utilities."""
import os
import pytest

from shared.summary_utils import (
    MatrixOutputConfig,
    MatrixSummaryConfig,
    write_matrix_outputs,
    write_matrix_summary,
)


def _make_config(**overrides) -> MatrixSummaryConfig:
    """Return a minimal MatrixSummaryConfig, optionally overriding fields."""
    defaults = dict(
        title="🧪 Test Matrix",
        csv_filepath="test_matrix.csv",
        empty_message="Nothing detected.",
        indicator_field="Signal",
        indicator_labels={"🔥": "Hot", "⚠️": "Watch", "❌": "Avoid"},
        table_columns=["Species", "Size (cm)", "OOS Runs", "Signal"],
    )
    defaults.update(overrides)
    return MatrixSummaryConfig(**defaults)


def _read_summary() -> str:
    path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if not path:
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestWriteMatrixSummaryReturnValue:
    """Return value reflects whether the summary was written."""

    def test_returns_false_when_no_summary_path(self, monkeypatch):
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        assert write_matrix_summary([], _make_config()) is False

    def test_returns_true_when_summary_path_is_set(self):
        assert write_matrix_summary([], _make_config()) is True


class TestWriteMatrixSummaryEmptyTable:
    """Correct output when table is empty."""

    def test_writes_section_heading(self):
        write_matrix_summary([], _make_config())
        assert "## 🧪 Test Matrix (Top 10)" in _read_summary()

    def test_writes_empty_message(self):
        write_matrix_summary([], _make_config(empty_message="All clear."))
        assert "_All clear._" in _read_summary()

    def test_does_not_write_summary_stats_line(self):
        write_matrix_summary([], _make_config())
        assert "**Summary:**" not in _read_summary()


class TestWriteMatrixSummaryWithData:
    """Correct output when table contains rows."""

    def _table(self):
        return [
            {"Species": "Spider A", "Size (cm)": "1.0", "OOS Runs": "3", "Signal": "🔥"},
            {"Species": "Spider B", "Size (cm)": "2.0", "OOS Runs": "0", "Signal": "❌"},
        ]

    def test_writes_summary_stats_line(self):
        write_matrix_summary(self._table(), _make_config())
        content = _read_summary()
        assert "**Summary:** 2 species analyzed" in content
        assert "🔥 Hot: 1" in content
        assert "⚠️ Watch: 0" in content
        assert "❌ Avoid: 1" in content

    def test_writes_column_headers(self):
        write_matrix_summary(self._table(), _make_config())
        content = _read_summary()
        assert "| Species | Size (cm) | OOS Runs | Signal |" in content

    def test_separator_right_aligns_cm_and_oos_runs_columns(self):
        write_matrix_summary(self._table(), _make_config())
        lines = _read_summary().splitlines()
        separator = next(l for l in lines if "---" in l)
        # "Size (cm)" → ---:, "OOS Runs" → ---:, others → ---
        assert separator == "|---|---:|---:|---|"

    def test_writes_data_rows_in_table_column_order(self):
        write_matrix_summary(self._table(), _make_config())
        content = _read_summary()
        assert "| Spider A | 1.0 | 3 | 🔥 |" in content
        assert "| Spider B | 2.0 | 0 | ❌ |" in content

    def test_does_not_write_footer_when_all_rows_shown(self):
        write_matrix_summary(self._table(), _make_config())
        assert "for full list" not in _read_summary()


class TestWriteMatrixSummaryPagination:
    """Footer note appears only when rows are truncated."""

    def test_writes_footer_when_rows_exceed_max_shown(self):
        table = [
            {"Species": f"Spider {i}", "Size (cm)": "1.0", "OOS Runs": "0", "Signal": "❌"}
            for i in range(15)
        ]
        write_matrix_summary(table, _make_config(), max_shown=5)
        content = _read_summary()
        assert "Showing top 5 of 15" in content
        assert "test_matrix.csv" in content

    def test_max_shown_controls_heading_suffix(self):
        write_matrix_summary([], _make_config(), max_shown=5)
        assert "## 🧪 Test Matrix (Top 5)" in _read_summary()


class TestWriteMatrixSummaryColumnSeparators:
    """Column separator alignment rules."""

    @pytest.mark.parametrize("col,expected_sep", [
        ("Species", "---"),
        ("Size (cm)", "---:"),
        ("OOS Runs", "---:"),
        ("Avg OOS Duration", "---:"),
        ("Signal", "---"),
        ("Stock Pattern", "---"),
    ])
    def test_column_separator_alignment(self, col, expected_sep):
        from shared.summary_utils import _column_separator
        assert _column_separator(col) == expected_sep


class TestWriteMatrixOutputs:
    """Tests for shared CSV + summary output writing."""

    def test_uses_default_table_columns_without_drivers(self):
        table = [{
            "Species": "Spider A",
            "Size (cm)": "1.0",
            "Signal": "🔥",
            "Drivers": "Stock: Sustained",
        }]
        config = MatrixOutputConfig(
            title="🧪 Test Matrix",
            csv_filepath="matrix.csv",
            empty_message="No rows.",
            indicator_field="Signal",
            indicator_labels={"🔥": "Hot", "⚠️": "Watch", "❌": "Avoid"},
            fallback_fieldnames=["Species", "Size (cm)", "Signal", "Drivers"],
        )

        result = write_matrix_outputs(table, config)
        assert result is True

        content = _read_summary()
        assert "| Species | Size (cm) | Signal |" in content
        assert "Drivers" not in content

    def test_respects_explicit_table_columns(self):
        table = [{
            "Species": "Spider A",
            "Signal": "🔥",
            "Wishlist": "10 🔥 ↑",
            "Drivers": "Stock: Emerging",
        }]
        config = MatrixOutputConfig(
            title="🧪 Test Matrix",
            csv_filepath="matrix.csv",
            empty_message="No rows.",
            indicator_field="Signal",
            indicator_labels={"🔥": "Hot", "⚠️": "Watch", "❌": "Avoid"},
            fallback_fieldnames=["Species", "Signal", "Wishlist", "Drivers"],
            table_columns=["Species", "Wishlist", "Signal"],
        )

        result = write_matrix_outputs(table, config)
        assert result is True

        content = _read_summary()
        assert "| Species | Wishlist | Signal |" in content

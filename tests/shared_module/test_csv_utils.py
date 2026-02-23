"""Tests for shared CSV writing utilities."""
import csv
import os
import pytest

from shared.csv_utils import write_matrix_csv


class TestWriteMatrixCsv:
    """Test write_matrix_csv() with populated and empty tables."""

    def test_writes_header_and_rows_when_table_has_data(self, tmp_path):
        table = [
            {"Species": "Aphonopelma seemanni", "Size (cm)": "1.0", "Signal": "🔥"},
            {"Species": "Grammostola pulchra", "Size (cm)": "2.0", "Signal": "❌"},
        ]
        output = tmp_path / "output.csv"
        write_matrix_csv(str(output), table, fallback_fieldnames=["Species"])

        with open(output, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["Species"] == "Aphonopelma seemanni"
        assert rows[1]["Signal"] == "❌"

    def test_uses_table_keys_as_fieldnames_when_table_has_data(self, tmp_path):
        table = [{"A": "1", "B": "2"}]
        output = tmp_path / "output.csv"
        write_matrix_csv(str(output), table, fallback_fieldnames=["X", "Y"])

        with open(output, encoding="utf-8") as f:
            header_line = f.readline()

        assert "A" in header_line
        assert "B" in header_line
        assert "X" not in header_line

    def test_creates_header_only_csv_when_table_is_empty(self, tmp_path):
        fallback = ["Species", "Size (cm)", "Signal"]
        output = tmp_path / "output.csv"
        write_matrix_csv(str(output), [], fallback_fieldnames=fallback)

        with open(output, encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 1
        assert "Species" in lines[0]
        assert "Signal" in lines[0]

    def test_creates_file_even_when_table_is_empty(self, tmp_path):
        output = tmp_path / "output.csv"
        assert not output.exists()
        write_matrix_csv(str(output), [], fallback_fieldnames=["Col"])
        assert output.exists()

    def test_overwrites_existing_file(self, tmp_path):
        output = tmp_path / "output.csv"
        output.write_text("old content\n", encoding="utf-8")

        write_matrix_csv(str(output), [{"Col": "new"}], fallback_fieldnames=["Col"])

        content = output.read_text(encoding="utf-8")
        assert "old content" not in content
        assert "new" in content

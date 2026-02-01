#!/usr/bin/env python3
"""
Tests for CSV file reading and parsing.
"""

import pytest
import tempfile
import os
from website import read_csv_file


class TestReadCsvFile:
    """Test suite for CSV file reading."""

    def test_nonexistent_file_returns_none_and_empty_list(self):
        """Should return (None, []) for nonexistent file."""
        headers, rows = read_csv_file("/nonexistent/file.csv")
        assert headers is None
        assert rows == []

    def test_empty_csv_file(self):
        """Should handle empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers is None
            assert rows == []
        finally:
            os.unlink(filename)

    def test_csv_with_headers_only(self):
        """Should read CSV with only headers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Column1,Column2,Column3\n")
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Column1", "Column2", "Column3"]
            assert rows == []
        finally:
            os.unlink(filename)

    def test_csv_with_data(self):
        """Should read CSV with headers and data rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Name,Price,Size\n")
            f.write("Species A,25.00,1.0\n")
            f.write("Species B,30.50,2.5\n")
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Name", "Price", "Size"]
            assert len(rows) == 2
            assert rows[0] == ["Species A", "25.00", "1.0"]
            assert rows[1] == ["Species B", "30.50", "2.5"]
        finally:
            os.unlink(filename)

    def test_csv_with_special_characters(self):
        """Should handle CSV with special characters and quotes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write('Name,Description\n')
            f.write('"Species, with comma","Description with ""quotes"""\n')
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Name", "Description"]
            assert rows[0] == ["Species, with comma", 'Description with "quotes"']
        finally:
            os.unlink(filename)

    def test_csv_with_utf8_characters(self):
        """Should handle UTF-8 encoded characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Species,Common\n")
            f.write("Brachypelma boehmei,🕷️ Mexican Fireleg\n")
            filename = f.name
        
        try:
            headers, rows = read_csv_file(filename)
            assert headers == ["Species", "Common"]
            assert rows[0] == ["Brachypelma boehmei", "🕷️ Mexican Fireleg"]
        finally:
            os.unlink(filename)

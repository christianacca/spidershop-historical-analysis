#!/usr/bin/env python3
"""
Tests for test_helpers module to ensure all helper functions work correctly.
"""

import pytest
import os
from pathlib import Path
from test_helpers import (
    create_temp_markdown_file,
    create_temp_csv_file,
    write_csv_file,
    read_file_content,
    create_csv_content,
    create_breeder_csv_content,
    create_dealer_csv_content,
    create_history_csv_content,
)


class TestCreateTempMarkdownFile:
    """Tests for create_temp_markdown_file helper."""

    def test_creates_file_with_content(self):
        """Should create a markdown file with specified content."""
        content = "# Test Heading\n\nTest content"
        filepath = create_temp_markdown_file(content)
        
        try:
            assert os.path.exists(filepath)
            assert filepath.endswith('.md')
            
            with open(filepath, 'r', encoding='utf-8') as f:
                actual = f.read()
            
            assert actual == content
        finally:
            os.unlink(filepath)

    def test_handles_unicode_content(self):
        """Should correctly handle Unicode characters."""
        content = "🔥 Hot: 36 | ⚠️ Watch: 30 | ❌ Avoid: 43"
        filepath = create_temp_markdown_file(content)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                actual = f.read()
            
            assert actual == content
        finally:
            os.unlink(filepath)


class TestCreateTempCsvFile:
    """Tests for create_temp_csv_file helper."""

    def test_creates_csv_with_content(self):
        """Should create a CSV file with specified content."""
        content = "Name,Age\nAlice,30\nBob,25\n"
        filepath = create_temp_csv_file(content)
        
        try:
            assert os.path.exists(filepath)
            assert filepath.endswith('.csv')
            
            with open(filepath, 'r', encoding='utf-8') as f:
                actual = f.read()
            
            assert actual == content
        finally:
            os.unlink(filepath)


class TestWriteCsvFile:
    """Tests for write_csv_file helper."""

    def test_writes_csv_data(self, tmp_path):
        """Should write headers and rows to CSV file."""
        csv_path = tmp_path / "test.csv"
        headers = ["Name", "Age", "City"]
        rows = [
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"]
        ]
        
        write_csv_file(csv_path, headers, rows)
        
        content = csv_path.read_text(encoding="utf-8")
        expected = "Name,Age,City\nAlice,30,NYC\nBob,25,LA\n"
        assert content == expected

    def test_handles_empty_rows(self, tmp_path):
        """Should handle empty rows list."""
        csv_path = tmp_path / "empty.csv"
        headers = ["Column1", "Column2"]
        rows = []
        
        write_csv_file(csv_path, headers, rows)
        
        content = csv_path.read_text(encoding="utf-8")
        assert content == "Column1,Column2\n"


class TestReadFileContent:
    """Tests for read_file_content helper."""

    def test_reads_file_content(self, tmp_path):
        """Should read file content with UTF-8 encoding."""
        test_file = tmp_path / "test.txt"
        test_content = "Test content with 🔥 emoji"
        test_file.write_text(test_content, encoding="utf-8")
        
        actual = read_file_content(test_file)
        assert actual == test_content


class TestCreateCsvContent:
    """Tests for create_csv_content helper."""

    def test_creates_csv_string(self):
        """Should generate CSV string from headers and rows."""
        headers = ["A", "B"]
        rows = [["1", "2"], ["3", "4"]]
        
        result = create_csv_content(headers, rows)
        
        assert result == "A,B\n1,2\n3,4\n"

    def test_handles_single_row(self):
        """Should handle single row."""
        headers = ["Name"]
        rows = [["Alice"]]
        
        result = create_csv_content(headers, rows)
        
        assert result == "Name\nAlice\n"


class TestCreateBreederCsvContent:
    """Tests for create_breeder_csv_content helper."""

    def test_creates_default_breeder_csv(self):
        """Should create breeder CSV with default values."""
        result = create_breeder_csv_content()
        
        assert "Species,Size (cm),Signal" in result
        assert "Test Species,1.0,🔥" in result

    def test_creates_custom_breeder_csv(self):
        """Should create breeder CSV with custom values."""
        result = create_breeder_csv_content(
            species="Custom Species",
            size="2.5",
            signal="⚠️"
        )
        
        assert "Custom Species,2.5,⚠️" in result

    def test_adds_extra_columns(self):
        """Should add extra columns when specified."""
        result = create_breeder_csv_content(
            extra_columns={"Price": "30.00", "Wishlist": "5"}
        )
        
        assert "Price,Wishlist" in result
        assert "30.00,5" in result


class TestCreateDealerCsvContent:
    """Tests for create_dealer_csv_content helper."""

    def test_creates_default_dealer_csv(self):
        """Should create dealer CSV with default values."""
        result = create_dealer_csv_content()
        
        assert "Species,Size (cm),Dealer Risk" in result
        assert "Test Species,1.0,🔥" in result

    def test_creates_custom_dealer_csv(self):
        """Should create dealer CSV with custom values."""
        result = create_dealer_csv_content(
            species="Custom Species",
            size="3.0",
            risk="❌"
        )
        
        assert "Custom Species,3.0,❌" in result

    def test_adds_extra_columns(self):
        """Should add extra columns when specified."""
        result = create_dealer_csv_content(
            extra_columns={"Reliability": "85%", "Avg OOS": "2"}
        )
        
        assert "Reliability,Avg OOS" in result
        assert "85%,2" in result


class TestCreateHistoryCsvContent:
    """Tests for create_history_csv_content helper."""

    def test_creates_default_history_csv(self):
        """Should create history CSV with default entry."""
        result = create_history_csv_content()
        
        # Check headers
        assert "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url" in result
        # Check default values
        assert "Test species" in result
        assert "25.00" in result

    def test_creates_custom_history_csv(self):
        """Should create history CSV with custom entries."""
        entries = [
            {
                "scrape_datetime": "2024-01-01 10:00:00",
                "scientific_name": "Species A",
                "common_name": "Common A",
                "size_cm": "1.5",
                "price_gbp": "20.00",
                "wishlist_count": "3",
                "page_url": "http://example.com/a"
            },
            {
                "scrape_datetime": "2024-01-02 10:00:00",
                "scientific_name": "Species B",
                "common_name": "Common B",
                "size_cm": "2.0",
                "price_gbp": "30.00",
                "wishlist_count": "5",
                "page_url": "http://example.com/b"
            }
        ]
        
        result = create_history_csv_content(entries)
        
        assert "Species A" in result
        assert "Species B" in result
        assert "20.00" in result
        assert "30.00" in result
        # Should have 2 data rows + 1 header
        assert result.count('\n') == 3

    def test_handles_missing_fields(self):
        """Should handle missing fields with empty strings."""
        entries = [
            {
                "scrape_datetime": "2024-01-01 10:00:00",
                "scientific_name": "Partial Species",
                # Missing other fields
            }
        ]
        
        result = create_history_csv_content(entries)
        
        assert "Partial Species" in result
        # Check that commas are present for empty fields
        assert result.count(',') >= 6  # At least 6 commas (7 columns)

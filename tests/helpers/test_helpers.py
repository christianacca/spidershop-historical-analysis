"""Common test helper utilities for creating test fixtures and data.

This module provides reusable helper functions to reduce boilerplate in tests.
"""

import tempfile
import os
from contextlib import contextmanager
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class HistoryEntry:
    """Entry for historical scrape CSV data.
    
    Fields are ordered to match CSV column order.
    page_url is auto-generated from scientific_name if not provided.
    """
    scrape_datetime: str = "2024-01-01 10:00:00"
    scientific_name: str = "Test species"
    common_name: str = "Test Common Name"
    size_cm: str = "1.0"
    price_gbp: str = "25.00"
    wishlist_count: str = "0"
    page_url: str = ""  # Auto-generated if empty
    
    def __post_init__(self):
        """Auto-generate page_url from scientific_name if not provided."""
        if not self.page_url:
            url_slug = self.scientific_name.lower().replace(" ", "-")
            self.page_url = f"https://www.thespidershop.co.uk/spiderlings/{url_slug}"


@dataclass
class BreederEntry:
    """Entry for breeder opportunity CSV data.
    
    Fields are ordered to match CSV column order.
    """
    species: str = "Test Species"
    size_cm: str = "1.0"
    oos: str = ""
    oos_runs: str = ""
    stock_pattern: str = ""
    price_trend: str = ""
    price_history: str = ""
    wishlist_pressure: str = ""
    wishlist_delta: str = ""
    wishlist_history: str = ""
    signal: str = "🔥"
    recommendation: str = ""


@dataclass
class DealerEntry:
    """Entry for dealer supply risk CSV data.
    
    Fields are ordered to match CSV column order.
    """
    species: str = "Test Species"
    size_cm: str = "1.0"
    stock_reliability: str = ""
    avg_oos_duration: str = ""
    restock_speed: str = ""
    price_pressure: str = ""
    price_history: str = ""
    wishlist_pressure: str = ""
    wishlist_delta: str = ""
    wishlist_history: str = ""
    stock_availability: str = ""
    risk: str = "🔥"
    dealer_recommendation: str = ""


def create_temp_markdown_file(content: str) -> str:
    """Create a temporary markdown file with given content.
    
    Args:
        content: Markdown content to write
        
    Returns:
        Path to the temporary file (caller must clean up)
        
    Example:
        >>> filepath = create_temp_markdown_file("## Test\\nContent")
        >>> try:
        ...     with open(filepath) as f:
        ...         print(f.read())
        ... finally:
        ...     os.unlink(filepath)
    """
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.md', 
        delete=False, 
        encoding='utf-8'
    ) as f:
        f.write(content)
        return f.name


def create_temp_csv_file(content: str) -> str:
    """Create a temporary CSV file with given content.
    
    Args:
        content: CSV content to write (including header)
        
    Returns:
        Path to the temporary file (caller must clean up)
        
    Example:
        >>> filepath = create_temp_csv_file("Name,Age\\nAlice,30\\n")
        >>> try:
        ...     with open(filepath) as f:
        ...         print(f.read())
        ... finally:
        ...     os.unlink(filepath)
    """
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.csv', 
        delete=False, 
        encoding='utf-8'
    ) as f:
        f.write(content)
        return f.name


@contextmanager
def temp_csv_file(content: str):
    """Context manager for temporary CSV file with automatic cleanup.
    
    Args:
        content: CSV content to write (including header)
        
    Yields:
        Path to the temporary CSV file
        
    Example:
        >>> from conftest import temp_csv_file
        >>> with temp_csv_file("Name,Age\\nAlice,30\\n") as csv_path:
        ...     # Use csv_path
        ...     with open(csv_path) as f:
        ...         print(f.read())
        # File automatically deleted after with block
    """
    filepath = create_temp_csv_file(content)
    try:
        yield filepath
    finally:
        try:
            os.unlink(filepath)
        except FileNotFoundError:
            pass  # File already deleted


def write_csv_file(path: Path, headers: List[str], rows: List[List[str]]) -> None:
    """Write CSV data to a file path.
    
    Args:
        path: Path object or string path to write to
        headers: List of column headers
        rows: List of data rows (each row is a list of strings)
        
    Example:
        >>> from pathlib import Path
        >>> path = Path("test.csv")
        >>> write_csv_file(path, ["Name", "Age"], [["Alice", "30"], ["Bob", "25"]])
        >>> path.unlink()  # cleanup
    """
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(row))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_file_content(path: Path) -> str:
    """Read file content with UTF-8 encoding.
    
    Args:
        path: Path to file to read
        
    Returns:
        File content as string
        
    Example:
        >>> from pathlib import Path
        >>> path = Path("test.txt")
        >>> path.write_text("test content")
        >>> read_file_content(path)
        'test content'
        >>> path.unlink()  # cleanup
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _field_name_to_csv_header(field_name: str, dataclass_type=None) -> str:
    """Convert a dataclass field name to CSV column header.
    
    Args:
        field_name: Snake_case field name
        dataclass_type: The dataclass type (for context-specific formatting)
        
    Returns:
        CSV column header with proper formatting
        
    Examples:
        >>> _field_name_to_csv_header("species")
        'Species'
        >>> _field_name_to_csv_header("size_cm", BreederEntry)
        'Size (cm)'
        >>> _field_name_to_csv_header("size_cm", HistoryEntry)
        'size_cm'
        >>> _field_name_to_csv_header("oos_runs")
        'OOS Runs'
        >>> _field_name_to_csv_header("risk")
        'Dealer Risk'
    """
    # HistoryEntry fields - keep lowercase with underscores
    if dataclass_type and dataclass_type.__name__ == 'HistoryEntry':
        return field_name
    
    # Special cases for breeder/dealer fields
    special_cases = {
        "size_cm": "Size (cm)",
        "risk": "Dealer Risk",
        "avg_oos_duration": "Avg OOS Duration",
    }
    
    if field_name in special_cases:
        return special_cases[field_name]
    
    # Convert snake_case to Title Case
    # Handle acronyms like OOS
    words = field_name.split("_")
    formatted_words = []
    for word in words:
        if word.upper() in ["OOS"]:
            formatted_words.append(word.upper())
        else:
            formatted_words.append(word.capitalize())
    
    return " ".join(formatted_words)


def create_csv_content(headers: List[str], rows: List[List[str]]) -> str:
    """Generate CSV content string from headers and rows.
    
    Args:
        headers: List of column headers
        rows: List of data rows (each row is a list of strings)
        
    Returns:
        Formatted CSV string with newline-terminated rows
        
    Example:
        >>> create_csv_content(["A", "B"], [["1", "2"], ["3", "4"]])
        'A,B\\n1,2\\n3,4\\n'
    """
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(row))
    return "\n".join(lines) + "\n"


def create_dataclass_csv_content(entries: List, default_factory=None) -> str:
    """Generate CSV content from a list of dataclass instances.
    
    Headers are automatically derived from dataclass field names.
    
    Args:
        entries: List of dataclass instances. If None/empty, creates a single default instance.
        default_factory: Callable that creates a default instance (e.g., BreederEntry).
                        If None, uses the first entry's type.
        
    Returns:
        CSV content string with columns derived from dataclass fields
        
    Example:
        >>> entries = [BreederEntry(species="Test Spider", signal="🔥", oos_runs="4")]
        >>> content = create_dataclass_csv_content(entries)
        >>> "OOS Runs" in content
        True
    """
    if not entries:
        if default_factory is None:
            raise ValueError("Must provide either entries or default_factory")
        entries = [default_factory()]
    
    # Get dataclass type from first entry
    entry_type = type(entries[0])
    field_names = [f.name for f in fields(entry_type)]
    headers = [_field_name_to_csv_header(name, entry_type) for name in field_names]
    
    rows = []
    for entry in entries:
        row = [getattr(entry, field_name) for field_name in field_names]
        rows.append(row)
    
    return create_csv_content(headers, rows)


# Convenience wrappers for backward compatibility and clearer test code
def create_breeder_csv_content(entries: Optional[List[BreederEntry]] = None) -> str:
    """Generate breeder opportunity CSV content.
    
    Example:
        >>> entries = [BreederEntry(species="Test Spider", signal="🔥", oos_runs="4")]
        >>> content = create_breeder_csv_content(entries)
        >>> "OOS Runs" in content
        True
    """
    return create_dataclass_csv_content(entries or [], BreederEntry)


def create_dealer_csv_content(entries: Optional[List[DealerEntry]] = None) -> str:
    """Generate dealer supply risk CSV content.
    
    Example:
        >>> entries = [DealerEntry(species="Test Spider", risk="⚠️", stock_reliability="Low")]
        >>> content = create_dealer_csv_content(entries)
        >>> "Stock Reliability" in content
        True
    """
    return create_dataclass_csv_content(entries or [], DealerEntry)


def create_history_csv_content(entries: Optional[List[HistoryEntry]] = None) -> str:
    """Generate historical scrape CSV content.
    
    Auto-generates page_url from scientific_name if not provided.
    
    Example:
        >>> entries = [HistoryEntry(scientific_name="Test species", wishlist_count="5")]
        >>> content = create_history_csv_content(entries)
        >>> "Test species" in content
        True
    """
    return create_dataclass_csv_content(entries or [], HistoryEntry)

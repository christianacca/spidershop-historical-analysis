"""Common test helper utilities for creating test fixtures and data.

This module provides reusable helper functions to reduce boilerplate in tests.
"""

import tempfile
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class HistoryEntry:
    """Entry for historical scrape CSV data."""
    scientific_name: str = "Test species"
    scrape_datetime: str = "2024-01-01 10:00:00"
    common_name: str = "Test Common Name"
    size_cm: str = "1.0"
    price_gbp: str = "25.00"
    wishlist_count: str = "0"
    page_url: str = ""  # Auto-generated if empty


@dataclass
class BreederEntry:
    """Entry for breeder opportunity CSV data."""
    species: str = "Test Species"
    size_cm: str = "1.0"
    signal: str = "🔥"
    extra_columns: Dict[str, str] = field(default_factory=dict)


@dataclass
class DealerEntry:
    """Entry for dealer supply risk CSV data."""
    species: str = "Test Species"
    size_cm: str = "1.0"
    risk: str = "🔥"
    extra_columns: Dict[str, str] = field(default_factory=dict)


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


def create_breeder_csv_content(
    entries: Optional[List[BreederEntry]] = None
) -> str:
    """Generate standard breeder opportunity CSV content for testing.
    
    Args:
        entries: List of BreederEntry objects. If None, creates a single default entry.
        
    Returns:
        CSV content string with standard breeder columns
        
    Example:
        >>> from test_helpers import BreederEntry
        >>> entries = [BreederEntry(species="Test Spider", signal="🔥", extra_columns={"Price": "30.00"})]
        >>> content = create_breeder_csv_content(entries)
        >>> "Price" in content
        True
    """
    if entries is None:
        entries = [BreederEntry()]
    
    # Collect all unique column names across all entries
    all_extra_cols = set()
    for entry in entries:
        all_extra_cols.update(entry.extra_columns.keys())
    
    headers = ["Species", "Size (cm)", "Signal"] + sorted(all_extra_cols)
    
    rows = []
    for entry in entries:
        row = [entry.species, entry.size_cm, entry.signal]
        for col in sorted(all_extra_cols):
            row.append(entry.extra_columns.get(col, ""))
        rows.append(row)
    
    return create_csv_content(headers, rows)


def create_dealer_csv_content(
    entries: Optional[List[DealerEntry]] = None
) -> str:
    """Generate standard dealer supply risk CSV content for testing.
    
    Args:
        entries: List of DealerEntry objects. If None, creates a single default entry.
        
    Returns:
        CSV content string with standard dealer columns
        
    Example:
        >>> from test_helpers import DealerEntry
        >>> entries = [DealerEntry(species="Test Spider", risk="⚠️", extra_columns={"Reliability": "85%"})]
        >>> content = create_dealer_csv_content(entries)
        >>> "Reliability" in content
        True
    """
    if entries is None:
        entries = [DealerEntry()]
    
    # Collect all unique column names across all entries
    all_extra_cols = set()
    for entry in entries:
        all_extra_cols.update(entry.extra_columns.keys())
    
    headers = ["Species", "Size (cm)", "Dealer Risk"] + sorted(all_extra_cols)
    
    rows = []
    for entry in entries:
        row = [entry.species, entry.size_cm, entry.risk]
        for col in sorted(all_extra_cols):
            row.append(entry.extra_columns.get(col, ""))
        rows.append(row)
    
    return create_csv_content(headers, rows)


def create_history_csv_content(entries: Optional[List[HistoryEntry]] = None) -> str:
    """Generate historical scrape data CSV content.
    
    Args:
        entries: List of HistoryEntry objects. If None, creates a single default entry.
                 page_url is auto-generated from scientific_name if not provided (empty string).
        
    Returns:
        CSV content with standard history columns
        
    Example:
        >>> from test_helpers import HistoryEntry
        >>> entries = [HistoryEntry(scientific_name="Test species", wishlist_count="5")]
        >>> content = create_history_csv_content(entries)
        >>> "Test species" in content
        True
    """
    if entries is None:
        entries = [HistoryEntry()]
    
    headers = [
        "scrape_datetime",
        "scientific_name",
        "common_name",
        "size_cm",
        "price_gbp",
        "wishlist_count",
        "page_url"
    ]
    
    rows = []
    for entry in entries:
        # Generate page_url if not provided
        page_url = entry.page_url
        if not page_url:
            url_slug = entry.scientific_name.lower().replace(" ", "-")
            page_url = f"https://www.thespidershop.co.uk/spiderlings/{url_slug}"
        
        row = [
            entry.scrape_datetime,
            entry.scientific_name,
            entry.common_name,
            entry.size_cm,
            entry.price_gbp,
            entry.wishlist_count,
            page_url
        ]
        rows.append(row)
    
    return create_csv_content(headers, rows)

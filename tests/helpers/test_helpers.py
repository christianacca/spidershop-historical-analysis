"""Common test helper utilities for creating test fixtures and data.

This module provides reusable helper functions to reduce boilerplate in tests.
"""

import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional


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
    species: str = "Test Species",
    size: str = "1.0",
    signal: str = "🔥",
    extra_columns: Optional[Dict[str, str]] = None
) -> str:
    """Generate standard breeder opportunity CSV content for testing.
    
    Args:
        species: Species name
        size: Size in cm
        signal: Signal emoji (🔥/⚠️/❌)
        extra_columns: Additional columns to include (e.g., {"Price": "25.00"})
        
    Returns:
        CSV content string with standard breeder columns
        
    Example:
        >>> content = create_breeder_csv_content(extra_columns={"Price": "30.00"})
        >>> "Price" in content
        True
    """
    headers = ["Species", "Size (cm)", "Signal"]
    row = [species, size, signal]
    
    if extra_columns:
        headers.extend(extra_columns.keys())
        row.extend(extra_columns.values())
    
    return create_csv_content(headers, [row])


def create_dealer_csv_content(
    species: str = "Test Species",
    size: str = "1.0",
    risk: str = "🔥",
    extra_columns: Optional[Dict[str, str]] = None
) -> str:
    """Generate standard dealer supply risk CSV content for testing.
    
    Args:
        species: Species name
        size: Size in cm
        risk: Risk emoji (🔥/⚠️/❌)
        extra_columns: Additional columns to include
        
    Returns:
        CSV content string with standard dealer columns
        
    Example:
        >>> content = create_dealer_csv_content(extra_columns={"Reliability": "85%"})
        >>> "Reliability" in content
        True
    """
    headers = ["Species", "Size (cm)", "Dealer Risk"]
    row = [species, size, risk]
    
    if extra_columns:
        headers.extend(extra_columns.keys())
        row.extend(extra_columns.values())
    
    return create_csv_content(headers, [row])


def create_history_csv_content(entries: Optional[List[Dict[str, str]]] = None) -> str:
    """Generate historical scrape data CSV content.
    
    Args:
        entries: List of dictionaries with scrape data fields
                 If None, creates a single default entry
        
    Returns:
        CSV content with standard history columns
        
    Example:
        >>> entries = [
        ...     {
        ...         "scrape_datetime": "2024-01-01 10:00:00",
        ...         "scientific_name": "Test species",
        ...         "size_cm": "1.0",
        ...         "price_gbp": "25.00",
        ...         "wishlist_count": "5"
        ...     }
        ... ]
        >>> content = create_history_csv_content(entries)
        >>> "Test species" in content
        True
    """
    headers = [
        "scrape_datetime",
        "scientific_name",
        "common_name",
        "size_cm",
        "price_gbp",
        "wishlist_count",
        "page_url"
    ]
    
    if entries is None:
        # Default entry
        entries = [{
            "scrape_datetime": "2024-01-01 10:00:00",
            "scientific_name": "Test species",
            "common_name": "Test common",
            "size_cm": "1.0",
            "price_gbp": "25.00",
            "wishlist_count": "0",
            "page_url": "http://example.com"
        }]
    
    rows = []
    for entry in entries:
        row = [entry.get(h, "") for h in headers]
        rows.append(row)
    
    return create_csv_content(headers, rows)

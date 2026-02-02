"""Configuration dataclass for website page generation."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PageConfig:
    """Configuration for generating a data page.
    
    This encapsulates all the parameters needed to generate a complete HTML page
    with data tables, analysis sections, and interactive features.
    
    Attributes:
        title: Page title displayed in header
        description: Brief description shown below title
        csv_filename: Path to CSV file containing table data
        table_id: HTML element ID for the main data table
        active_page: Navigation identifier (e.g., 'breeder', 'dealer', 'snapshot')
        search_filter: Whether to include text search functionality
        analysis_markdown: Optional markdown content for analysis summary
        legend_markdown: Optional markdown content for legend/help section
        examples_markdown: Optional markdown content for practical examples
    """
    title: str
    description: str
    csv_filename: str
    table_id: str
    active_page: str
    search_filter: bool = True
    analysis_markdown: Optional[str] = None
    legend_markdown: Optional[str] = None
    examples_markdown: Optional[str] = None
    link_to_species_page: bool = False  # Whether to link Species column to internal pages
    table_view: str = "breeder"  # View parameter for species page links ("breeder" or "dealer")

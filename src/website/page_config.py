"""Configuration dataclasses for website page generation."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BasePageConfig:
    """Base configuration for all page types.
    
    Contains fields common to all page configurations.
    """
    title: str
    description: str
    csv_filename: str
    table_id: str
    active_page: str


@dataclass
class BreederPageConfig(BasePageConfig):
    """Configuration for breeder opportunity pages.
    
    Includes analysis, legend, examples, search, and species linking.
    """
    search_filter: bool = True
    analysis_markdown: Optional[str] = None
    legend_markdown: Optional[str] = None
    examples_markdown: Optional[str] = None
    link_to_species_page: bool = True
    table_view: str = "breeder"


@dataclass
class DealerPageConfig(BasePageConfig):
    """Configuration for dealer supply risk pages.
    
    Includes analysis, legend, examples, search, and species linking.
    """
    search_filter: bool = True
    analysis_markdown: Optional[str] = None
    legend_markdown: Optional[str] = None
    examples_markdown: Optional[str] = None
    link_to_species_page: bool = True
    table_view: str = "dealer"


@dataclass
class SnapshotPageConfig(BasePageConfig):
    """Configuration for snapshot pages.
    
    Simpler pages with just search and species linking (no analysis/legend).
    """
    search_filter: bool = True
    link_to_species_page: bool = True
    table_view: str = "breeder"


@dataclass
class HistoryPageConfig(BasePageConfig):
    """Configuration for historical data pages.
    
    Simplest pages with just search (no species linking).
    """
    search_filter: bool = True

"""Configuration dataclasses for website page generation."""

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class PageNavItem:
    """Navigation item with icon and metadata for a single site page."""

    icon: str
    label: str
    url: str
    active_page: str
    card_description: Optional[str] = None
    card_link_text: Optional[str] = None

    @property
    def title(self) -> str:
        """Page heading combining icon and label (e.g. '📸 Latest Snapshot')."""
        return f"{self.icon} {self.label}"


NAV_ITEMS: List[PageNavItem] = [
    PageNavItem(
        icon="🏠",
        label="Home",
        url="index.html",
        active_page="home",
    ),
    PageNavItem(
        icon="📸",
        label="Latest Snapshot",
        url="snapshot.html",
        active_page="snapshot",
        card_description="View the most recent scrape of all available spiderling listings, including scientific names, common names, sizes, and prices.",
        card_link_text="View Snapshot",
    ),
    PageNavItem(
        icon="📊",
        label="Historical Data",
        url="history.html",
        active_page="history",
        card_description="Explore accumulated pricing data across all scrapes to track trends and price changes over time.",
        card_link_text="View History",
    ),
    PageNavItem(
        icon="🌱",
        label="Breeder Opportunities",
        url="breeder.html",
        active_page="breeder",
        card_description="Analysis showing breeding opportunities based on market trends and pricing patterns.",
        card_link_text="View Analysis",
    ),
    PageNavItem(
        icon="📦",
        label="Dealer Supply Risk",
        url="dealer.html",
        active_page="dealer",
        card_description="Analysis highlighting inventory availability patterns and supply risk indicators.",
        card_link_text="View Analysis",
    ),
]


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
    methodology: Optional[dict[str, Any]] = None
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
    methodology: Optional[dict[str, Any]] = None
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

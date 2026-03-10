"""Website generation package for GitHub Pages deployment."""

from website.page_config import (
    BasePageConfig,
    BreederPageConfig,
    DealerPageConfig,
    SnapshotPageConfig,
    HistoryPageConfig,
)
from website.sparkline_dto import (
    load_historical_sparkline_data,
    SPARKLINE_CHARS,
)
from website.markdown_utils import (
    parse_markdown_to_html,
    add_data_labels_to_tables,
    extract_summary_stats,
    extract_analysis_sections,
)
from website.csv_utils import read_csv_file
from website.table_data_helpers import rows_to_json

__all__ = [
    # Configuration
    'PageConfig',
    # Sparkline utilities
    'load_historical_sparkline_data',
    'SPARKLINE_CHARS',
    # Markdown utilities
    'parse_markdown_to_html',
    'add_data_labels_to_tables',
    'extract_summary_stats',
    'extract_analysis_sections',
    # CSV utilities
    'read_csv_file',
    # Table data helpers
    'rows_to_json',
]

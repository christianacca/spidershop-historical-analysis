"""Website generation package for GitHub Pages deployment."""

from website.page_config import (
    BasePageConfig,
    BreederPageConfig,
    DealerPageConfig,
    SnapshotPageConfig,
    HistoryPageConfig,
)
from website.sparkline_conversion import (
    convert_sparkline_to_svg,
    load_historical_sparkline_data,
    convert_sparklines_in_rows,
    SPARKLINE_CHARS,
)
from website.markdown_utils import (
    parse_markdown_to_html,
    add_data_labels_to_tables,
    extract_summary_stats,
    extract_analysis_sections,
)
from website.html_utils import (
    escape_html,
    generate_table_html,
    get_base_html_template,
    get_html_footer,
)
from website.csv_utils import read_csv_file

__all__ = [
    # Configuration
    'PageConfig',
    # Sparkline conversion
    'convert_sparkline_to_svg',
    'load_historical_sparkline_data',
    'convert_sparklines_in_rows',
    'SPARKLINE_CHARS',
    # Markdown utilities
    'parse_markdown_to_html',
    'add_data_labels_to_tables',
    'extract_summary_stats',
    'extract_analysis_sections',
    # HTML utilities
    'escape_html',
    'generate_table_html',
    'get_base_html_template',
    'get_html_footer',
    # CSV utilities
    'read_csv_file',
]

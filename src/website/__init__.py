"""Website generation package for GitHub Pages deployment."""

from website.page_config import PageConfig
from website.sparkline_conversion import (
    convert_sparkline_to_svg,
    load_historical_sparkline_data,
    convert_sparklines_in_rows,
    SPARKLINE_CHARS,
)

__all__ = [
    'PageConfig',
    'convert_sparkline_to_svg',
    'load_historical_sparkline_data',
    'convert_sparklines_in_rows',
    'SPARKLINE_CHARS',
]

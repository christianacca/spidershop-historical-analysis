"""HTML generation utilities for website components.

This module handles HTML table generation, templates, and page fragments.
"""

import re
from datetime import datetime, timezone
from typing import Optional, List, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


# Setup Jinja2 environment
template_dir = Path(__file__).parent.parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)


def escape_html(text: Any) -> str:
    """Escape HTML special characters.
    
    Note: With Jinja2 auto-escaping enabled, this function is primarily
    used for backward compatibility with tests. Jinja2 handles escaping
    automatically in templates.
    
    Args:
        text: Text to escape (can be None)
        
    Returns:
        HTML-escaped string, or empty string if text is None
    """
    if text is None:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def generate_table_html(
    headers: Optional[List[str]], 
    rows: List[List[str]], 
    table_id: str, 
    sortable: bool = True,
    link_to_species_page: bool = False,
    table_view: str = "breeder"
) -> str:
    """Generate HTML table from headers and rows using Jinja2 template.
    
    Args:
        headers: List of column headers
        rows: List of data rows
        table_id: HTML id attribute for the table
        sortable: Whether to enable sorting functionality
        link_to_species_page: If True, link Species column to internal species detail pages
                             instead of external page_url links (for breeder/dealer tables)
        table_view: View parameter for species page links ("breeder" or "dealer")
        
    Returns:
        HTML string containing the rendered table
    """
    if not headers or not rows:
        return "<p>No data available.</p>"
    
    # Find column indices for special rendering
    page_url_idx = None
    scientific_name_idx = None
    species_idx = None  # For breeder/dealer tables
    size_idx = None  # For breeder/dealer tables
    signal_col_idx = None
    stock_pattern_col_idx = None
    
    # Drivers column exists in breeder/dealer tables but not history/snapshot
    drivers_col_idx = headers.index('Drivers') if headers and 'Drivers' in headers else None
    
    try:
        page_url_idx = headers.index('page_url')
        scientific_name_idx = headers.index('scientific_name')
    except ValueError:
        pass  # Columns not found, render normally
    
    # For breeder/dealer tables with internal species linking
    if link_to_species_page:
        try:
            species_idx = headers.index('Species')
            size_idx = headers.index('Size (cm)')
        except ValueError:
            pass  # Not a breeder/dealer table
    
    # Find Signal or Dealer Risk column for color-coding
    try:
        signal_col_idx = headers.index('Signal')
    except ValueError:
        try:
            signal_col_idx = headers.index('Dealer Risk')
        except ValueError:
            pass  # No signal column found
    
    # Find Stock Pattern column for breeder filtering
    try:
        stock_pattern_col_idx = headers.index('Stock Pattern')
    except ValueError:
        pass  # No stock pattern column (not breeder table)
    
    # Enumerate headers and rows for template
    headers_enum = list(enumerate(headers))
    rows_enum = [list(enumerate(row)) for row in rows]
    
    template = jinja_env.get_template('table.html')
    return template.render(
        table_id=table_id,
        headers=headers_enum,
        rows=rows_enum,
        sortable=sortable,
        page_url_idx=page_url_idx,
        scientific_name_idx=scientific_name_idx,
        species_idx=species_idx,
        size_idx=size_idx,
        link_to_species_page=link_to_species_page,
        table_view=table_view,
        signal_col_idx=signal_col_idx,
        stock_pattern_col_idx=stock_pattern_col_idx,
        drivers_col_idx=drivers_col_idx
    )


def get_base_html_template(title: str, active_page: str = "") -> str:
    """Return the base HTML template with navigation.
    
    Note: This function is kept for backward compatibility with tests.
    The actual rendering now uses Jinja2 templates via render_page().
    This returns a partial HTML fragment for testing purposes.
    
    Args:
        title: Page title
        active_page: Active navigation page identifier
        
    Returns:
        Partial HTML string (header + nav + opening container)
    """
    template = jinja_env.get_template('base.html')
    html = template.render(
        title=title,
        active_page=active_page,
        path_prefix="",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )
    # Return everything up to (and including) the third <div class="container">
    # which is the main content container after header and nav
    container_pattern = r'<div class="container">'
    matches = list(re.finditer(container_pattern, html))
    if len(matches) >= 3:
        # Get position after the third container div
        pos = matches[2].end()
        return html[:pos] + '\n'
    return html


def get_html_footer() -> str:
    """Return the HTML footer with closing tags.
    
    Note: This function is kept for backward compatibility with tests.
    The actual rendering now uses Jinja2 templates via render_page().
    This returns a partial HTML fragment for testing purposes.
    
    Returns:
        Partial HTML string (closing divs + footer + scripts + closing tags)
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    # Return the closing structure that tests expect
    return f"""    </div>
    
    <footer>
        <p>Data scraped from <a href="https://thespidershop.co.uk/" target="_blank">The Spider Shop UK</a></p>
        <p><a href="https://github.com/christianacca/spidershop-historical-analysis" target="_blank">View on GitHub</a></p>
        <p>Generated: {timestamp}</p>
    </footer>
    
    <script src="table-interactions.js"></script>
</body>
</html>"""

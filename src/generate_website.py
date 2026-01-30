#!/usr/bin/env python3
"""
Generate a static HTML website from scraped CSV data for GitHub Pages deployment.

IMPORTANT - Output Location:
    The OUTPUT_DIR is relative to the CURRENT WORKING DIRECTORY when this script runs:
    
    - GitHub workflow: Runs from project root → creates website/ at root
    - Coding agent: Runs from project root → creates website/ at root
    - Make command: Changes to tmp/local-testing/ first → creates website/ there
    
    This means the generated website/ folder location varies depending on execution context.
"""

import csv
import os
import re
import markdown
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Output directory for the generated website
# NOTE: This is RELATIVE to the current working directory when the script runs!
# See docstring above for how this behaves in different execution contexts.
OUTPUT_DIR = Path("website")

# Setup Jinja2 environment
template_dir = Path(__file__).parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)

# Sparkline character mapping (Unicode to relative height 0-7)
SPARKLINE_CHARS = {
    '▁': 1, '▂': 2, '▃': 3, '▄': 4,
    '▅': 5, '▆': 6, '▇': 7, '█': 8,
    ' ': None  # Gap/missing data
}


def convert_sparkline_to_svg(unicode_sparkline, values=None, metric_type="price", is_carried_forward=None):
    """
    Convert a Unicode sparkline to an interactive SVG with tooltips.
    
    Args:
        unicode_sparkline: String of Unicode sparkline characters (e.g., "▁▂▃▄▅▆▇█")
        values: List of actual numeric values (for tooltips), or None for stock availability
        metric_type: "price", "wishlist", or "stock" (affects formatting and colors)
        is_carried_forward: List of booleans indicating which values are carried-forward (optional)
    
    Returns:
        String containing SVG markup, or original string if conversion not possible
    """
    # Don't convert if it's just a dash or empty string
    if not unicode_sparkline or unicode_sparkline == "-":
        return unicode_sparkline
    
    # Handle whitespace-only strings - treat as "no data" after parsing
    # (but don't exit early - need to check if it's all spaces which means all gaps)
    
    # Parse Unicode characters into bar heights
    bars = []
    for char in unicode_sparkline:
        if char in SPARKLINE_CHARS:
            height = SPARKLINE_CHARS[char]
            bars.append(height)
        else:
            # Unknown character, return original
            return unicode_sparkline
    
    # Need at least one non-None bar
    non_none_bars = [b for b in bars if b is not None]
    if not non_none_bars:
        return "-"
    
    # Determine trend direction for color coding
    # For carried-forward values: check if ALL non-None bars after first are carried forward
    # If so, treat as neutral (no actual change occurred)
    if len(non_none_bars) >= 2 and is_carried_forward:
        # Check if we have actual change by examining is_carried_forward flags
        non_none_indices = [i for i, b in enumerate(bars) if b is not None]
        first_idx = non_none_indices[0]
        last_idx = non_none_indices[-1]
        
        # Check if all values after first are carried forward
        all_carried_after_first = all(
            is_carried_forward[i] 
            for i in non_none_indices[1:] 
            if i < len(is_carried_forward)
        )
        
        if all_carried_after_first:
            # No actual change - use neutral color
            color = "#3b82f6"  # Blue
            trend = "stable"
        else:
            # Has actual changes - use trend color
            first_val = non_none_bars[0]
            last_val = non_none_bars[-1]
            if last_val > first_val + 1:  # Rising (allow for minor fluctuation)
                color = "#22c55e"  # Green
                trend = "rising"
            elif last_val < first_val - 1:  # Falling
                color = "#ef4444"  # Red
                trend = "falling"
            else:
                color = "#3b82f6"  # Blue (stable)
                trend = "stable"
    elif len(non_none_bars) >= 2:
        # No is_carried_forward info - use simple trend detection
        first_val = non_none_bars[0]
        last_val = non_none_bars[-1]
        if last_val > first_val + 1:  # Rising (allow for minor fluctuation)
            color = "#22c55e"  # Green
            trend = "rising"
        elif last_val < first_val - 1:  # Falling
            color = "#ef4444"  # Red
            trend = "falling"
        else:
            color = "#3b82f6"  # Blue (stable)
            trend = "stable"
    else:
        color = "#3b82f6"  # Blue
        trend = "stable"
    
    # For stock availability, always use green for IN bars
    if metric_type == "stock":
        color = "#22c55e"  # Green
        trend = "stock"
    
    # Generate SVG bars
    svg_bars = []
    bar_width = 8
    bar_spacing = 10
    svg_width = len(bars) * bar_spacing
    svg_height = 20
    max_bar_height = svg_height
    
    # Determine if we should use actual values for proportional heights
    # Use actual values when available and metric is price or wishlist
    # Allow partial values - as long as we have SOME values for price/wishlist
    use_proportional_values = (values is not None and 
                               len(values) > 0 and 
                               metric_type in ["price", "wishlist"])
    
    # Calculate min/max for proportional scaling if using actual values
    if use_proportional_values:
        # Only use numeric values that exist
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                pass
        
        if len(numeric_values) >= 2:
            # Use zero-based normalization for better proportional representation
            # This ensures that similar values (e.g., 120 vs 126) look similar
            min_val = 0  # Always use zero as baseline
            max_val = max(numeric_values)
            value_range = max_val if max_val > 0 else 1.0
        else:
            # Not enough values for proportional scaling
            use_proportional_values = False
    
    # Track how many non-None bars we've processed for proper values indexing
    bar_index = 0
    
    for i, height in enumerate(bars):
        x = i * bar_spacing
        
        if height is None:
            # Gap - represents OUT-of-stock or periods before species first appeared
            # Don't render anything (true gap)
            continue
        else:
            # Calculate bar height
            if use_proportional_values and bar_index < len(values):
                try:
                    # Use actual numeric value for proportional height
                    val_float = float(values[bar_index])
                    # Normalize to 0-1 range, then scale to max height
                    # Add small minimum (10%) to ensure all bars are visible
                    normalized = (val_float - min_val) / value_range
                    bar_height = (0.1 + normalized * 0.9) * max_bar_height
                except (ValueError, TypeError):
                    # Value doesn't exist or isn't numeric - fall back to Unicode height
                    bar_height = (height / 8.0) * max_bar_height
            else:
                # Use Unicode character height (for stock or when no values)
                bar_height = (height / 8.0) * max_bar_height
            
            y = svg_height - bar_height
            
            # Check if this bar is carried-forward
            is_carried = is_carried_forward and bar_index < len(is_carried_forward) and is_carried_forward[bar_index]
            
            # Generate tooltip
            # Use bar_index (count of non-None bars) to index into values list
            if values and bar_index < len(values):
                val = values[bar_index]
                if metric_type == "price":
                    # Format price with square brackets if carried forward
                    if is_carried:
                        tooltip = f"[£{val}]"
                    else:
                        tooltip = f"£{val}"
                elif metric_type == "wishlist":
                    # Format wishlist count with singular/plural and square brackets
                    plural = "wishlist" if val == "1" else "wishlists"
                    if is_carried:
                        tooltip = f"[{val} {plural}]"
                    else:
                        tooltip = f"{val} {plural}"
                else:  # stock
                    tooltip = "IN"
            else:
                if metric_type == "stock":
                    tooltip = "IN"
                else:
                    tooltip = f"Week {bar_index + 1}"
            
            # Adjust opacity based on position (gradient effect)
            opacity = 0.7 + (i / len(bars)) * 0.3
            
            svg_bars.append(
                f'<rect x="{x}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" '
                f'fill="{color}" opacity="{opacity:.2f}"><title>{tooltip}</title></rect>'
            )
            
            # Increment bar_index only for rendered bars
            bar_index += 1
    
    # Assemble final SVG
    if metric_type == "price":
        svg_title = "Price History"
    elif metric_type == "wishlist":
        svg_title = "Wishlist History"
    elif metric_type == "stock":
        svg_title = "Stock History"
    else:
        svg_title = f"{metric_type.capitalize()} History"
    
    svg = (
        f'<svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" '
        f'style="vertical-align: middle;">'
        f'<title>{svg_title}</title>'
        f'{"".join(svg_bars)}'
        f'</svg>'
    )
    
    return svg


def parse_markdown_to_html(markdown_text):
    """Convert markdown to HTML using the markdown library.
    
    Uses the 'tables', 'fenced_code', and 'md_in_html' extensions.
    Downgrades heading levels (h2→h3, h3→h4) to maintain proper hierarchy.
    """
    if not markdown_text:
        return ""
    
    # Configure markdown with extensions
    # md_in_html allows markdown parsing inside HTML blocks like <details>
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'md_in_html'])
    
    # Convert markdown to HTML
    html = md.convert(markdown_text)
    
    # Add our custom class to tables for styling consistency
    html = html.replace('<table>', '<table class="data-table markdown-table">')
    
    # Downgrade heading levels to maintain semantic hierarchy
    # h2 → h3, h3 → h4, h4 → h5, h5 → h6
    # Process in reverse order to avoid double-replacements
    html = html.replace('<h5>', '<h6>').replace('</h5>', '</h6>')
    html = html.replace('<h4>', '<h5>').replace('</h4>', '</h5>')
    html = html.replace('<h3>', '<h4>').replace('</h3>', '</h4>')
    html = html.replace('<h2>', '<h3>').replace('</h2>', '</h3>')
    
    return html


def extract_summary_stats(markdown):
    """
    Extract summary statistics from markdown content.
    
    Looks for line like: **Summary:** 106 species analyzed | 🔥 Hot: 42 | ⚠️ Watch: 38 | ❌ Avoid: 26
    or: **Summary:** 106 species analyzed | 🔥 High Risk: 42 | ⚠️ Moderate Risk: 38 | ❌ Low Risk: 26
    
    Returns dict with keys: total, hot, watch, avoid, or None if not found.
    """
    if not markdown:
        return None
    
    # Match either "Hot/Watch/Avoid" or "High Risk/Moderate Risk/Low Risk" format
    pattern = r'\*\*Summary:\*\*\s*(\d+)\s*species analyzed\s*\|.*?🔥\s*(?:Hot|High Risk):\s*(\d+)\s*\|.*?⚠️\s*(?:Watch|Moderate Risk):\s*(\d+)\s*\|.*?❌\s*(?:Avoid|Low Risk):\s*(\d+)'
    match = re.search(pattern, markdown)
    
    if match:
        return {
            'total': int(match.group(1)),
            'hot': int(match.group(2)),
            'watch': int(match.group(3)),
            'avoid': int(match.group(4))
        }
    
    return None


def extract_analysis_sections(markdown_file):
    """Extract breeder and dealer analysis sections from markdown file."""
    if not os.path.exists(markdown_file):
        return None, None, None, None, None, None
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract breeder section
    breeder_match = re.search(
        r'## 🧬 Breeder Opportunity Matrix \(Top 10\)\n\n(.*?)(?=\n## |\n<details>|$)',
        content,
        re.DOTALL
    )
    breeder_md = breeder_match.group(0) if breeder_match else None
    
    # Extract dealer section
    dealer_match = re.search(
        r'## 🏪 Dealer Supply Risk Matrix \(Top 10\)\n\n(.*?)(?=\n<details>|$)',
        content,
        re.DOTALL
    )
    dealer_md = dealer_match.group(0) if dealer_match else None
    
    # Extract full legend content
    legend_match = re.search(
        r'<details(?:\s+markdown="1")?>\s*<summary><strong>ℹ️ How to read these tables \(Legend\)</strong></summary>(.*?)</details>',
        content,
        re.DOTALL
    )
    legend_full = legend_match.group(1) if legend_match else None
    
    # Extract breeder legend and examples
    breeder_legend = None
    breeder_examples = None
    dealer_legend = None
    dealer_examples = None
    
    if legend_full:
        # Split at breeder examples heading
        breeder_examples_split = re.split(r'### 📖 Breeder Matrix — Practical Examples', legend_full)
        breeder_legend = breeder_examples_split[0].strip()
        remaining = breeder_examples_split[1]
        
        # Split remaining at dealer legend heading
        dealer_split = re.split(r'### 🏪 Dealer Supply Risk Matrix — Legend', remaining)
        breeder_examples = '### 📖 Breeder Matrix — Practical Examples' + dealer_split[0]
        remaining_dealer = dealer_split[1]
        
        # Split dealer remaining at dealer examples heading
        dealer_examples_split = re.split(r'### 📖 Dealer Matrix — Practical Examples', remaining_dealer)
        dealer_legend = '### 🏪 Dealer Supply Risk Matrix — Legend' + dealer_examples_split[0].strip()
        dealer_examples = '### 📖 Dealer Matrix — Practical Examples' + dealer_examples_split[1]
    
    return breeder_md, dealer_md, breeder_legend, dealer_legend, breeder_examples, dealer_examples


def read_csv_file(filepath):
    """Read a CSV file and return headers and rows."""
    if not os.path.exists(filepath):
        return None, []
    
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        rows = list(reader)
    return headers, rows


def escape_html(text):
    """Escape HTML special characters.
    
    Note: With Jinja2 auto-escaping enabled, this function is primarily
    used for backward compatibility with tests. Jinja2 handles escaping
    automatically in templates.
    """
    if text is None:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def generate_table_html(headers, rows, table_id, sortable=True):
    """Generate HTML table from headers and rows using Jinja2 template."""
    if not headers or not rows:
        return "<p>No data available.</p>"
    
    # Find column indices for special rendering
    page_url_idx = None
    scientific_name_idx = None
    signal_col_idx = None
    try:
        page_url_idx = headers.index('page_url')
        scientific_name_idx = headers.index('scientific_name')
    except ValueError:
        pass  # Columns not found, render normally
    
    # Find Signal or Dealer Risk column for color-coding
    try:
        signal_col_idx = headers.index('Signal')
    except ValueError:
        try:
            signal_col_idx = headers.index('Dealer Risk')
        except ValueError:
            pass  # No signal column found
    
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
        signal_col_idx=signal_col_idx
    )


def get_base_html_template(title, active_page=""):
    """Return the base HTML template with navigation.
    
    Note: This function is kept for backward compatibility with tests.
    The actual rendering now uses Jinja2 templates via render_page().
    This returns a partial HTML fragment for testing purposes.
    """
    template = jinja_env.get_template('base.html')
    html = template.render(
        title=title,
        active_page=active_page,
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


def get_html_footer():
    """Return the HTML footer with closing tags.
    
    Note: This function is kept for backward compatibility with tests.
    The actual rendering now uses Jinja2 templates via render_page().
    This returns a partial HTML fragment for testing purposes.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    # Return the closing structure that tests expect
    return f"""    </div>
    
    <footer>
        <p>Data scraped from <a href="https://thespidershop.co.uk/" target="_blank">The Spider Shop UK</a></p>
        <p><a href="https://github.com/christianacca/spidershop-historical-analysis" target="_blank">View on GitHub</a></p>
        <p>Generated: {timestamp}</p>
    </footer>
    
    <script>
        function sortTable(columnIndex, tableId) {{
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Determine if column is numeric
            let isNumeric = true;
            for (let i = 0; i < Math.min(5, rows.length); i++) {{
                const cellText = rows[i].cells[columnIndex].textContent.trim();
                if (cellText && isNaN(parseFloat(cellText.replace(/[^0-9.-]/g, '')))) {{
                    isNumeric = false;
                    break;
                }}
            }}
            
            // Get current sort direction
            const header = table.querySelectorAll('th')[columnIndex];
            const currentDirection = header.getAttribute('data-sort-direction') || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            
            // Clear all sort indicators
            table.querySelectorAll('th').forEach(th => {{
                th.removeAttribute('data-sort-direction');
            }});
            
            // Set new sort direction
            header.setAttribute('data-sort-direction', newDirection);
            
            // Sort rows
            rows.sort((a, b) => {{
                let aVal = a.cells[columnIndex].textContent.trim();
                let bVal = b.cells[columnIndex].textContent.trim();
                
                if (isNumeric) {{
                    aVal = parseFloat(aVal.replace(/[^0-9.-]/g, '')) || 0;
                    bVal = parseFloat(bVal.replace(/[^0-9.-]/g, '')) || 0;
                    return newDirection === 'asc' ? aVal - bVal : bVal - aVal;
                }} else {{
                    aVal = aVal.toLowerCase();
                    bVal = bVal.toLowerCase();
                    if (newDirection === 'asc') {{
                        return aVal.localeCompare(bVal);
                    }} else {{
                        return bVal.localeCompare(aVal);
                    }}
                }}
            }});
            
            // Reappend sorted rows
            rows.forEach(row => tbody.appendChild(row));
        }}
        
        function filterTable(searchInput, tableId) {{
            const filter = searchInput.value.toLowerCase();
            const table = document.getElementById(tableId);
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>"""


def generate_homepage(last_scrape_time=None):
    """Generate the homepage with overview and links using Jinja2 template."""
    template = jinja_env.get_template('homepage.html')
    return template.render(
        active_page='home',
        last_scrape_time=last_scrape_time,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )


def load_historical_sparkline_data():
    """
    Load historical data from history CSV in format ready for sparkline extraction.
    
    Returns:
        Tuple of (by_run, runs) where:
        - by_run: Dictionary mapping run_id (scrape_datetime) to list of rows
        - runs: Sorted list of run IDs (scrape_datetime values)
    """
    from history import group_by_run
    
    history_file = "spidershop_spiderlings_history.csv"
    if not os.path.exists(history_file):
        return {}, []
    
    try:
        history = []
        with open(history_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append(row)
        
        # Group by run and get sorted runs
        by_run = group_by_run(history)
        runs = sorted(by_run)
        
        return by_run, runs
    except Exception as e:
        print(f"Warning: Could not load historical data: {e}")
        return {}, []


def convert_sparklines_in_rows(headers, rows, historical_data, csv_filename):
    """
    Convert Unicode sparklines to SVG in specific columns.
    
    Args:
        headers: List of column names
        rows: List of data rows
        historical_data: Tuple of (by_run, runs) for sparkline extraction
        csv_filename: Name of the CSV file being processed
    
    Returns:
        Modified rows with sparklines converted to SVG
    """
    from sparkline_helpers import extract_historical_values_with_carryforward
    
    by_run, runs = historical_data
    
    # Identify sparkline columns
    sparkline_columns = {}
    for i, header in enumerate(headers):
        if "History" in header or "Availability" in header:
            if "Price" in header:
                sparkline_columns[i] = "price_gbp"
            elif "Wishlist" in header:
                sparkline_columns[i] = "wishlist_count"
            elif "Stock" in header or "Availability" in header:
                sparkline_columns[i] = "stock"
    
    if not sparkline_columns:
        return rows  # No sparkline columns found
    
    # Get species and size column indices
    species_idx = headers.index("Species") if "Species" in headers else None
    size_idx = headers.index("Size (cm)") if "Size (cm)" in headers else None
    
    # Convert sparklines in each row
    converted_rows = []
    for row in rows:
        new_row = list(row)  # Make a copy
        
        # Get species/size for looking up historical values
        species = row[species_idx] if species_idx is not None else None
        size = row[size_idx] if size_idx is not None else None
        key = (species, size) if species and size else None
        
        # Convert each sparkline column
        for col_idx, field_name in sparkline_columns.items():
            if col_idx < len(new_row):
                unicode_sparkline = new_row[col_idx]
                
                # Extract values with carried-forward tracking using the same logic as matrix generation
                values = None
                is_carried_forward = None
                
                # Determine metric type from field_name
                if field_name == "stock":
                    metric_type = "stock"
                elif field_name == "price_gbp":
                    metric_type = "price"
                elif field_name == "wishlist_count":
                    metric_type = "wishlist"
                else:
                    metric_type = None
                
                # Extract historical values if available
                if field_name != "stock" and key and by_run:
                    result = extract_historical_values_with_carryforward(key, by_run, runs, field_name, max_runs=8)
                    values = result['values']
                    is_carried_forward = result['is_carried_forward']
                
                # Convert to SVG
                svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type, is_carried_forward=is_carried_forward)
                new_row[col_idx] = svg
        
        converted_rows.append(new_row)
    
    return converted_rows


def convert_sparklines_in_html(html, historical_data):
    """
    Convert Unicode sparklines to SVG in HTML tables (post-processing).
    
    This handles sparklines in markdown-generated HTML tables (e.g., Top 10 analysis tables).
    
    Args:
        html: HTML string containing tables with Unicode sparklines
        historical_data: Tuple of (by_run, runs) for sparkline extraction
    
    Returns:
        HTML string with sparklines converted to SVG
    """
    if not html:
        return html
    
    from bs4 import BeautifulSoup
    from sparkline_helpers import extract_historical_values_with_carryforward
    
    by_run, runs = historical_data
    
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    
    for table in tables:
        # Find header row to identify column positions
        thead = table.find('thead')
        if not thead:
            continue
        
        header_row = thead.find('tr')
        if not header_row:
            continue
        
        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
        
        # Identify sparkline columns and their field names
        sparkline_columns = {}
        for i, header in enumerate(headers):
            if "Price History" in header:
                sparkline_columns[i] = ("price_gbp", "price")
            elif "Wishlist History" in header:
                sparkline_columns[i] = ("wishlist_count", "wishlist")
            elif "Stock Availability" in header or "Stock" in header:
                sparkline_columns[i] = (None, "stock")
        
        if not sparkline_columns:
            continue
        
        # Find species and size columns
        species_idx = None
        size_idx = None
        try:
            species_idx = headers.index("Species")
        except ValueError:
            pass
        try:
            size_idx = headers.index("Size (cm)")
        except ValueError:
            pass
        
        # Process each data row
        tbody = table.find('tbody')
        if not tbody:
            continue
        
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            
            # Get species/size for looking up historical values
            species = cells[species_idx].get_text(strip=True) if species_idx is not None and species_idx < len(cells) else None
            size = cells[size_idx].get_text(strip=True) if size_idx is not None and size_idx < len(cells) else None
            key = (species, size) if species and size else None
            
            # Convert sparklines in this row
            for col_idx, (field_name, metric_type) in sparkline_columns.items():
                if col_idx >= len(cells):
                    continue
                
                cell = cells[col_idx]
                unicode_sparkline = cell.get_text(strip=True)
                
                # Extract values with carried-forward tracking
                values = None
                is_carried_forward = None
                
                if key and by_run and field_name is not None:
                    result = extract_historical_values_with_carryforward(key, by_run, runs, field_name, max_runs=8)
                    values = result['values']
                    is_carried_forward = result['is_carried_forward']
                
                # Convert to SVG
                svg = convert_sparkline_to_svg(unicode_sparkline, values, metric_type, is_carried_forward=is_carried_forward)
                
                # Replace cell content with SVG (mark as safe HTML)
                cell.clear()
                cell.append(BeautifulSoup(svg, 'html.parser'))
    
    return str(soup)


def apply_signal_styling_to_html(html):
    """
    Apply color-coded CSS classes to Signal/Dealer Risk cells in HTML tables.
    
    This post-processes markdown-generated HTML tables (e.g., Top 10 analysis tables)
    to add the same styling used in the full data tables.
    
    Args:
        html: HTML string containing tables with Signal or Dealer Risk columns
    
    Returns:
        HTML string with signal cells styled
    """
    if not html:
        return html
    
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    
    for table in tables:
        # Find header row to identify Signal/Dealer Risk column
        thead = table.find('thead')
        if not thead:
            continue
        
        header_row = thead.find('tr')
        if not header_row:
            continue
        
        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
        
        # Find Signal or Dealer Risk column index
        signal_col_idx = None
        try:
            signal_col_idx = headers.index("Signal")
        except ValueError:
            try:
                signal_col_idx = headers.index("Dealer Risk")
            except ValueError:
                continue  # No signal column in this table
        
        # Process each data row
        tbody = table.find('tbody')
        if not tbody:
            continue
        
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            
            if signal_col_idx >= len(cells):
                continue
            
            signal_cell = cells[signal_col_idx]
            signal_text = signal_cell.get_text(strip=True)
            
            # Add appropriate CSS class based on signal emoji
            if '🔥' in signal_text:
                signal_cell['class'] = signal_cell.get('class', []) + ['signal-hot']
            elif '⚠️' in signal_text:
                signal_cell['class'] = signal_cell.get('class', []) + ['signal-watch']
            elif '❌' in signal_text:
                signal_cell['class'] = signal_cell.get('class', []) + ['signal-avoid']
    
    return str(soup)


def generate_data_page(title, description, csv_filename, table_id, active_page, search_filter=True, analysis_markdown=None, legend_markdown=None, examples_markdown=None):
    """Generate a data page with table from CSV and optional analysis using Jinja2 template."""
    headers, rows = read_csv_file(csv_filename)
    
    # Load historical data if available to enrich sparklines with values
    historical_data = load_historical_sparkline_data()
    
    # Convert Unicode sparklines to SVG in sparkline columns
    if headers and rows:
        rows = convert_sparklines_in_rows(headers, rows, historical_data, csv_filename)
    
    # Extract summary stats from analysis markdown BEFORE converting to HTML
    summary_stats = extract_summary_stats(analysis_markdown) if analysis_markdown else None
    
    # Remove the Summary line from markdown to avoid duplication (stats are rendered as cards)
    if analysis_markdown and summary_stats:
        analysis_markdown = re.sub(
            r'\*\*Summary:\*\*\s*\d+\s*species analyzed\s*\|[^\n]+\n\n',
            '',
            analysis_markdown
        )
    
    # Convert markdown to HTML if provided
    analysis_html = parse_markdown_to_html(analysis_markdown) if analysis_markdown else None
    
    # Convert sparklines in analysis HTML (Top 10 tables from markdown)
    if analysis_html:
        analysis_html = convert_sparklines_in_html(analysis_html, historical_data)
        # Apply signal cell styling to Top 10 tables
        analysis_html = apply_signal_styling_to_html(analysis_html)
    
    # Determine labels and tooltips based on page type (breeder vs dealer)
    stats_labels = None
    tooltips = None
    if summary_stats:
        if active_page == "dealer":
            stats_labels = {
                'hot': '🔥 High Risk',
                'watch': '⚠️ Moderate Risk',
                'avoid': '❌ Low Risk'
            }
            tooltips = {
                'hot': 'High risk of lost sales due to supply constraints. Low stock reliability (<40% of runs) or slow restock speed, often with rising demand.',
                'watch': 'Moderate supply concerns. Medium reliability (40-79% of runs) or intermittent restock patterns. Monitor carefully for escalating demand.',
                'avoid': 'Healthy supply with high reliability (≥80% of runs). No urgency — these species consistently restock and are well-supplied.'
            }
        else:  # breeder or other pages
            stats_labels = {
                'hot': '🔥 Hot',
                'watch': '⚠️ Watch',
                'avoid': '❌ Avoid'
            }
            tooltips = {
                'hot': 'Strong breeding opportunity. Sustained or emerging scarcity patterns (4+ weeks out of stock) with rising prices or high demand signals.',
                'watch': 'Emerging opportunity forming. Species showing early scarcity (2-3 weeks) or cyclical patterns. Monitor for escalating signals.',
                'avoid': 'Oversupplied or always available. No meaningful scarcity pattern detected, regardless of demand spikes.'
            }
    
    examples_html = parse_markdown_to_html(examples_markdown) if examples_markdown else None
    
    # Wrap legend markdown in details tag and convert
    legend_html = None
    if legend_markdown:
        legend_with_wrapper = f'<details markdown="1">\n<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>\n\n{legend_markdown}\n\n</details>'
        legend_html = parse_markdown_to_html(legend_with_wrapper)
    
    # Find column indices for special rendering
    page_url_idx = None
    scientific_name_idx = None
    signal_col_idx = None
    if headers:
        try:
            page_url_idx = headers.index('page_url')
            scientific_name_idx = headers.index('scientific_name')
        except ValueError:
            pass
        
        # Find Signal or Dealer Risk column for color-coding
        try:
            signal_col_idx = headers.index('Signal')
        except ValueError:
            try:
                signal_col_idx = headers.index('Dealer Risk')
            except ValueError:
                pass  # No signal column found
    
    # Enumerate headers and rows for template
    headers_enum = list(enumerate(headers)) if headers else []
    rows_enum = [list(enumerate(row)) for row in rows] if rows else []
    
    template = jinja_env.get_template('data_page.html')
    return template.render(
        page_title=title,
        description=description,
        csv_filename=csv_filename,
        table_id=table_id,
        active_page=active_page,
        search_filter=search_filter,
        analysis_html=analysis_html,
        summary_stats=summary_stats,
        stats_labels=stats_labels,
        tooltips=tooltips,
        legend_html=legend_html,
        examples_html=examples_html,
        headers=headers_enum,
        rows=rows_enum,
        sortable=True,
        page_url_idx=page_url_idx,
        scientific_name_idx=scientific_name_idx,
        signal_col_idx=signal_col_idx,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )


def main():
    """Main function to generate the static website."""
    print("Generating static website...")
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Get last scrape time from snapshot if available
    last_scrape_time = None
    snapshot_headers, snapshot_rows = read_csv_file("spidershop_spiderlings_scrape.csv")
    if snapshot_rows and snapshot_headers:
        # First column should be scrape_datetime
        last_scrape_time = snapshot_rows[0][0] if snapshot_rows[0] else None
    
    # Extract analysis sections from markdown summary
    breeder_analysis = None
    dealer_analysis = None
    breeder_legend = None
    dealer_legend = None
    breeder_examples = None
    dealer_examples = None
    
    if os.path.exists("analysis_summary.md"):
        print("  Extracting analysis from summary...")
        breeder_analysis, dealer_analysis, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections("analysis_summary.md")
    
    # Generate homepage
    print("  Generating index.html...")
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(generate_homepage(last_scrape_time))
    
    # Generate snapshot page
    print("  Generating snapshot.html...")
    with open(OUTPUT_DIR / "snapshot.html", "w", encoding="utf-8") as f:
        f.write(generate_data_page(
            "Latest Snapshot",
            "Current scrape results showing all available tarantula spiderlings.",
            "spidershop_spiderlings_scrape.csv",
            "snapshot-table",
            "snapshot"
        ))
    
    # Generate history page
    print("  Generating history.html...")
    with open(OUTPUT_DIR / "history.html", "w", encoding="utf-8") as f:
        f.write(generate_data_page(
            "Historical Data",
            "Accumulated historical pricing data across all scrape runs.",
            "spidershop_spiderlings_history.csv",
            "history-table",
            "history"
        ))
    
    # Generate breeder opportunity page
    print("  Generating breeder.html...")
    with open(OUTPUT_DIR / "breeder.html", "w", encoding="utf-8") as f:
        f.write(generate_data_page(
            "Breeder Opportunities",
            "Analysis showing breeding opportunities based on market trends and pricing patterns.",
            "breeder_opportunity_table.csv",
            "breeder-table",
            "breeder",
            analysis_markdown=breeder_analysis,
            legend_markdown=breeder_legend,
            examples_markdown=breeder_examples
        ))
    
    # Generate dealer supply risk page
    print("  Generating dealer.html...")
    with open(OUTPUT_DIR / "dealer.html", "w", encoding="utf-8") as f:
        f.write(generate_data_page(
            "Dealer Supply Risk",
            "Analysis highlighting inventory availability patterns and supply risk indicators.",
            "dealer_supply_risk_table.csv",
            "dealer-table",
            "dealer",
            analysis_markdown=dealer_analysis,
            legend_markdown=dealer_legend,
            examples_markdown=dealer_examples
        ))
    
    # Copy CSV files to output directory
    print("  Copying CSV files...")
    csv_files = [
        "spidershop_spiderlings_scrape.csv",
        "spidershop_spiderlings_history.csv",
        "breeder_opportunity_table.csv",
        "dealer_supply_risk_table.csv"
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            with open(csv_file, "r", encoding="utf-8") as src:
                content = src.read()
            with open(OUTPUT_DIR / csv_file, "w", encoding="utf-8") as dst:
                dst.write(content)
            print(f"    Copied {csv_file}")
    
    print(f"\n✅ Website generated successfully in '{OUTPUT_DIR}' directory")
    print(f"   Total HTML pages: 5")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate a static HTML website from scraped CSV data for GitHub Pages deployment.

IMPORTANT - Output Location:
    The OUTPUT_DIR is relative to the CURRENT WORKING DIRECTORY when this script runs:
    
    - GitHub workflow: Runs from project root → creates website/ at root
    - Coding agent: Runs from project root → creates website/ at root
    - Make command: Changes to tmp/local-testing/ first → creates website/ there
    
    This means the generated website/ folder location varies depending on execution context.

Usage Example:
    
    from website import PageConfig
    from website.generate_website import generate_data_page
    
    config = PageConfig(
        title="Breeder Opportunities",
        description="Analysis of breeding opportunities",
        csv_filename="breeder_opportunity_table.csv",
        table_id="breeder-table",
        active_page="breeder",
        analysis_markdown=breeder_analysis,
        legend_markdown=breeder_legend,
        examples_markdown=breeder_examples
    )
    html = generate_data_page(config)
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports of sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
import os
import re
import markdown
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Handle both direct script execution and module import
try:
    from website.page_config import PageConfig
    from website.sparkline_conversion import (
        convert_sparkline_to_svg,
        load_historical_sparkline_data,
        convert_sparklines_in_rows,
    )
except ModuleNotFoundError:
    from page_config import PageConfig
    from sparkline_conversion import (
        convert_sparkline_to_svg,
        load_historical_sparkline_data,
        convert_sparklines_in_rows,
    )

# Output directory for the generated website
# NOTE: This is RELATIVE to the current working directory when the script runs!
# See docstring above for how this behaves in different execution contexts.
OUTPUT_DIR = Path("website")

# Setup Jinja2 environment
template_dir = Path(__file__).parent.parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)


def parse_markdown_to_html(markdown_text: Optional[str]) -> str:
    """Convert markdown to HTML using the markdown library.
    
    Uses the 'tables', 'fenced_code', and 'md_in_html' extensions.
    Downgrades heading levels (h2→h3, h3→h4) to maintain proper hierarchy.
    Adds data-label attributes to table cells for responsive card layout.
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
    
    # Add data-label attributes to table cells for mobile responsive layout
    html = add_data_labels_to_tables(html)
    
    # Downgrade heading levels to maintain semantic hierarchy
    # h2 → h3, h3 → h4, h4 → h5, h5 → h6
    # Process in reverse order to avoid double-replacements
    html = html.replace('<h5>', '<h6>').replace('</h5>', '</h6>')
    html = html.replace('<h4>', '<h5>').replace('</h4>', '</h5>')
    html = html.replace('<h3>', '<h4>').replace('</h3>', '</h4>')
    html = html.replace('<h2>', '<h3>').replace('</h2>', '</h3>')
    
    return html


def add_data_labels_to_tables(html: str) -> str:
    """Add data-label attributes to table cells for mobile responsive layout.
    
    Parses HTML tables and adds data-label attributes to each <td> element
    based on the corresponding <th> header text. This enables CSS-based
    responsive card layouts where labels appear on mobile devices.
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    
    for table in tables:
        # Extract headers
        thead = table.find('thead')
        if not thead:
            continue
        
        header_row = thead.find('tr')
        if not header_row:
            continue
        
        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
        
        # Add data-label to each cell in tbody
        tbody = table.find('tbody')
        if not tbody:
            continue
        
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            for i, cell in enumerate(cells):
                if i < len(headers):
                    cell['data-label'] = headers[i]
    
    return str(soup)


def extract_summary_stats(markdown: Optional[str]) -> Optional[Dict[str, int]]:
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
    """
    Extract analysis text (summary stats only) from markdown file.
    
    Tables are no longer extracted - they will be rendered directly from CSV files.
    This function only extracts the Summary line for statistics.
    """
    if not os.path.exists(markdown_file):
        return None, None, None, None, None, None
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract breeder summary line only (no table)
    breeder_summary_match = re.search(
        r'\*\*Summary:\*\*\s*\d+\s*species analyzed\s*\|[^\n]+',
        content
    )
    breeder_md = breeder_summary_match.group(0) if breeder_summary_match else None
    
    # Extract dealer summary line only (no table)
    dealer_summary_match = re.search(
        r'## 🏪 Dealer Supply Risk Matrix \(Top 10\)\n\n\*\*Summary:\*\*\s*\d+\s*species analyzed\s*\|[^\n]+',
        content
    )
    dealer_md = dealer_summary_match.group(0) if dealer_summary_match else None
    
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
        breeder_examples_parts = re.split(r'### 📖 Breeder Matrix — Practical Examples', legend_full)
        if len(breeder_examples_parts) >= 2:
            breeder_legend = breeder_examples_parts[0].strip()
            remaining = breeder_examples_parts[1]
            
            # Split remaining at dealer legend heading
            dealer_split = re.split(r'### 🏪 Dealer Supply Risk Matrix — Legend', remaining)
            if len(dealer_split) >= 2:
                breeder_examples = '### 📖 Breeder Matrix — Practical Examples' + dealer_split[0]
                remaining_dealer = dealer_split[1]
                
                # Split dealer remaining at dealer examples heading
                dealer_examples_split = re.split(r'### 📖 Dealer Matrix — Practical Examples', remaining_dealer)
                if len(dealer_examples_split) >= 2:
                    dealer_legend = '### 🏪 Dealer Supply Risk Matrix — Legend' + dealer_examples_split[0].strip()
                    dealer_examples = '### 📖 Dealer Matrix — Practical Examples' + dealer_examples_split[1]
    
    return breeder_md, dealer_md, breeder_legend, dealer_legend, breeder_examples, dealer_examples


def read_csv_file(filepath: str) -> Tuple[Optional[List[str]], List[List[str]]]:
    """Read a CSV file and return headers and rows."""
    if not os.path.exists(filepath):
        return None, []
    
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        rows = list(reader)
    return headers, rows


def escape_html(text: Any) -> str:
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


def generate_table_html(headers: Optional[List[str]], rows: List[List[str]], table_id: str, sortable: bool = True) -> str:
    """Generate HTML table from headers and rows using Jinja2 template."""
    if not headers or not rows:
        return "<p>No data available.</p>"
    
    # Find column indices for special rendering
    page_url_idx = None
    scientific_name_idx = None
    signal_col_idx = None
    stock_pattern_col_idx = None
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
        signal_col_idx=signal_col_idx,
        stock_pattern_col_idx=stock_pattern_col_idx
    )


def get_base_html_template(title: str, active_page: str = "") -> str:
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


def get_html_footer() -> str:
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
    
    <script src="table-interactions.js"></script>
</body>
</html>"""


def generate_homepage(last_scrape_time: Optional[str] = None) -> str:
    """Generate the homepage with overview and links using Jinja2 template."""
    template = jinja_env.get_template('homepage.html')
    return template.render(
        active_page='home',
        last_scrape_time=last_scrape_time,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )


def generate_data_page(config: PageConfig) -> str:
    """Generate a data page with table from CSV and optional analysis using Jinja2 template.
    
    Args:
        config: PageConfig object containing all page generation parameters
    
    Returns:
        str: Complete HTML page content
        
    Example:
        config = PageConfig(
            title="Breeder Opportunities",
            description="Market analysis",
            csv_filename="breeder_table.csv",
            table_id="breeder-table",
            active_page="breeder"
        )
        html = generate_data_page(config)
    """
    headers, rows = read_csv_file(config.csv_filename)
    
    # Load historical data if available to enrich sparklines with values
    historical_data = load_historical_sparkline_data()
    
    # Convert Unicode sparklines to SVG in sparkline columns
    if headers and rows:
        rows = convert_sparklines_in_rows(headers, rows, historical_data, config.csv_filename)
    
    # Extract summary stats from analysis markdown
    summary_stats = extract_summary_stats(config.analysis_markdown) if config.analysis_markdown else None
    
    # Generate top 10 table from CSV (first 10 rows, already sorted by analysis modules)
    top_10_headers = None
    top_10_rows = None
    if headers and rows and len(rows) > 0:
        top_10_headers = headers
        top_10_rows = rows[:10]  # CSV is already sorted by breeder_matrix/dealer_matrix
    
    # No markdown to HTML conversion for analysis - no tables to render
    analysis_html = None
    
    # Determine labels and tooltips based on page type (breeder vs dealer)
    stats_labels = None
    tooltips = None
    if summary_stats:
        if config.active_page == "dealer":
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
    
    examples_html = parse_markdown_to_html(config.examples_markdown) if config.examples_markdown else None
    
    # Wrap legend markdown in details tag and convert
    legend_html = None
    if config.legend_markdown:
        legend_with_wrapper = f'<details markdown="1">\n<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>\n\n{config.legend_markdown}\n\n</details>'
        legend_html = parse_markdown_to_html(legend_with_wrapper)
    
    # Find column indices for special rendering
    page_url_idx = None
    scientific_name_idx = None
    signal_col_idx = None
    stock_pattern_col_idx = None
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
        
        # Find Stock Pattern column for breeder filtering
        try:
            stock_pattern_col_idx = headers.index('Stock Pattern')
        except ValueError:
            pass  # No stock pattern column (not breeder table)
    
    # Calculate stock pattern counts for filter buttons
    stock_pattern_counts = None
    if stock_pattern_col_idx is not None and rows:
        from collections import Counter
        patterns = [row[stock_pattern_col_idx] for row in rows if stock_pattern_col_idx < len(row)]
        pattern_counter = Counter(patterns)
        stock_pattern_counts = {
            'total': len(patterns),
            'sustained': pattern_counter.get('Sustained', 0),
            'emerging': pattern_counter.get('Emerging', 0),
            'cyclical': pattern_counter.get('Cyclical', 0),
            'always': pattern_counter.get('Always', 0)
        }
    
    # Enumerate headers and rows for template
    headers_enum = list(enumerate(headers)) if headers else []
    rows_enum = [list(enumerate(row)) for row in rows] if rows else []
    
    # Enumerate top 10 headers and rows for separate rendering
    top_10_headers_enum = list(enumerate(top_10_headers)) if top_10_headers else []
    top_10_rows_enum = [list(enumerate(row)) for row in top_10_rows] if top_10_rows else []
    
    template = jinja_env.get_template('data_page.html')
    return template.render(
        page_title=config.title,
        description=config.description,
        csv_filename=config.csv_filename,
        table_id=config.table_id,
        active_page=config.active_page,
        search_filter=config.search_filter,
        analysis_html=analysis_html,
        summary_stats=summary_stats,
        stats_labels=stats_labels,
        tooltips=tooltips,
        legend_html=legend_html,
        examples_html=examples_html,
        top_10_headers=top_10_headers_enum,
        top_10_rows=top_10_rows_enum,
        headers=headers_enum,
        rows=rows_enum,
        sortable=True,
        page_url_idx=page_url_idx,
        scientific_name_idx=scientific_name_idx,
        signal_col_idx=signal_col_idx,
        stock_pattern_col_idx=stock_pattern_col_idx,
        stock_pattern_counts=stock_pattern_counts,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )


def main() -> None:
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
        f.write(generate_data_page(config=PageConfig(
            title="Latest Snapshot",
            description="Current scrape results showing all available tarantula spiderlings.",
            csv_filename="spidershop_spiderlings_scrape.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )))
    
    # Generate history page
    print("  Generating history.html...")
    with open(OUTPUT_DIR / "history.html", "w", encoding="utf-8") as f:
        f.write(generate_data_page(config=PageConfig(
            title="Historical Data",
            description="Accumulated historical pricing data across all scrape runs.",
            csv_filename="spidershop_spiderlings_history.csv",
            table_id="history-table",
            active_page="history"
        )))
    
    # Generate breeder opportunity page
    print("  Generating breeder.html...")
    with open(OUTPUT_DIR / "breeder.html", "w", encoding="utf-8") as f:
        f.write(generate_data_page(config=PageConfig(
            title="Breeder Opportunities",
            description="Analysis showing breeding opportunities based on market trends and pricing patterns.",
            csv_filename="breeder_opportunity_table.csv",
            table_id="breeder-table",
            active_page="breeder",
            analysis_markdown=breeder_analysis,
            legend_markdown=breeder_legend,
            examples_markdown=breeder_examples
        )))
    
    # Generate dealer supply risk page
    print("  Generating dealer.html...")
    with open(OUTPUT_DIR / "dealer.html", "w", encoding="utf-8") as f:
        f.write(generate_data_page(config=PageConfig(
            title="Dealer Supply Risk",
            description="Analysis highlighting inventory availability patterns and supply risk indicators.",
            csv_filename="dealer_supply_risk_table.csv",
            table_id="dealer-table",
            active_page="dealer",
            analysis_markdown=dealer_analysis,
            legend_markdown=dealer_legend,
            examples_markdown=dealer_examples
        )))
    
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
    
    # Copy JavaScript file to output directory
    print("  Copying JavaScript files...")
    js_source = Path(__file__).parent.parent.parent / "templates" / "scripts" / "table-interactions.js"
    if js_source.exists():
        with open(js_source, "r", encoding="utf-8") as src:
            content = src.read()
        with open(OUTPUT_DIR / "table-interactions.js", "w", encoding="utf-8") as dst:
            dst.write(content)
        print(f"    Copied table-interactions.js")
    
    print(f"\n✅ Website generated successfully in '{OUTPUT_DIR}' directory")
    print(f"   Total HTML pages: 5")


if __name__ == "__main__":
    main()

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

import os
import shutil
from datetime import datetime, timezone
from typing import Optional

# Handle both direct script execution and module import
try:
    from website.page_config import PageConfig
    from website.sparkline_conversion import (
        load_historical_sparkline_data,
        convert_sparklines_in_rows,
    )
    from website.markdown_utils import (
        parse_markdown_to_html,
        extract_summary_stats,
        extract_analysis_sections,
    )
    from website.html_utils import (
        generate_table_html,
        jinja_env,
    )
    from website.csv_utils import read_csv_file
except ModuleNotFoundError:
    from page_config import PageConfig
    from sparkline_conversion import (
        load_historical_sparkline_data,
        convert_sparklines_in_rows,
    )
    from markdown_utils import (
        parse_markdown_to_html,
        extract_summary_stats,
        extract_analysis_sections,
    )
    from html_utils import (
        generate_table_html,
        jinja_env,
    )
    from csv_utils import read_csv_file

# Output directory for the generated website
# NOTE: This is RELATIVE to the current working directory when the script runs!
# See docstring above for how this behaves in different execution contexts.
OUTPUT_DIR = Path("website")


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

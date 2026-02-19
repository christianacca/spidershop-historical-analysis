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
    from website.generate_website import generate_analysis_page
    
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
    html = generate_analysis_page(config)
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports of sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import shutil
from datetime import datetime, timezone
from typing import Optional, Callable, Tuple, List, Any

# Handle both direct script execution and module import
try:
    from website.page_config import BasePageConfig
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
    from website.species_detail import (
        get_species_list,
        slugify_species,
        get_species_data,
        build_chart_data,
        get_default_size,
        get_page_url,
        generate_species_page,
    )
    from shared.parsing import format_datetime_smart
except ModuleNotFoundError:
    from page_config import BasePageConfig
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


def _calculate_column_range(
    rows: List[List[Any]], 
    col_idx: Optional[int], 
    default_min: int, 
    default_max: int,
    parser: Callable[[Any], float]
) -> Tuple[int, int, bool]:
    """
    Calculate min/max range for a column in CSV data.
    
    Args:
        rows: CSV rows (list of lists)
        col_idx: Column index to extract values from
        default_min: Default minimum if no valid values found
        default_max: Default maximum if no valid values found
        parser: Function to parse cell value to float (handles type conversions)
        
    Returns:
        Tuple of (min_value, max_value, found_values) where:
        - min_value: Minimum value as integer (or default)
        - max_value: Maximum value as integer (or default)
        - found_values: Boolean indicating if any valid values were found
    """
    if not rows or col_idx is None:
        return default_min, default_max, False
    
    values = []
    for row in rows:
        if col_idx < len(row):
            try:
                values.append(parser(row[col_idx]))
            except (ValueError, TypeError):
                pass
    
    if not values:
        return default_min, default_max, False
    
    return int(min(values)), int(max(values)), True


def _parse_price_value(value: Any) -> float:
    """Parse a price value, removing the £ symbol if present."""
    price_str = str(value).replace('£', '').strip()
    return float(price_str)


def generate_homepage(last_scrape_time: Optional[str] = None) -> str:
    """Generate the homepage with overview and links using Jinja2 template."""
    template = jinja_env.get_template('homepage.html')
    return template.render(
        active_page='home',
        last_scrape_time=last_scrape_time,
        path_prefix="",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )


def generate_snapshot_page(config: BasePageConfig) -> str:
    """Generate a snapshot page for current scrape data (raw data display)."""
    # Read CSV file
    headers, rows = read_csv_file(config.csv_filename)
    
    # Format scrape_datetime column (date-only unless collision)
    if headers and rows and 'scrape_datetime' in headers:
        datetime_idx = headers.index('scrape_datetime')
        datetimes = [row[datetime_idx] for row in rows]
        formatted_dates = format_datetime_smart(datetimes)
        for i, row in enumerate(rows):
            row[datetime_idx] = formatted_dates[i]
    
    #Load sparkline data from history CSV for conversion
    sparkline_data = load_historical_sparkline_data()
    
    # Convert Unicode sparklines to SVG in rows
    if headers and rows:
        rows = convert_sparklines_in_rows(headers, rows, sparkline_data, config.csv_filename)
    
    # Find column indices for special rendering
    page_url_idx = None
    scientific_name_idx = None
    price_idx = None
    wishlist_idx = None
    if headers:
        try:
            page_url_idx = headers.index('page_url')
            scientific_name_idx = headers.index('scientific_name')
            price_idx = headers.index('price_gbp')
            wishlist_idx = headers.index('wishlist_count')
        except ValueError:
            pass
    
    # Calculate wishlist range from data
    wishlist_min, wishlist_max, _ = _calculate_column_range(
        rows=rows,
        col_idx=wishlist_idx,
        default_min=0,
        default_max=300,
        parser=lambda x: int(x)
    )
    
    # Calculate price range from data
    price_min, price_max, found_prices = _calculate_column_range(
        rows=rows,
        col_idx=price_idx,
        default_min=5,
        default_max=400,
        parser=_parse_price_value
    )
    # Round up max price for better UX (only when actual prices found)
    if found_prices:
        price_max = price_max + 1
    
    # Enumerate headers and rows for template
    headers_enum = list(enumerate(headers)) if headers else []
    rows_enum = [list(enumerate(row)) for row in rows] if rows else []
    
    template = jinja_env.get_template('snapshot_page.html')
    return template.render(
        page_title=config.title,
        description=config.description,
        csv_filename=config.csv_filename,
        table_id=config.table_id,
        active_page=config.active_page,
        path_prefix="",
        search_filter=getattr(config, 'search_filter', True),
        headers=headers_enum,
        rows=rows_enum,
        page_url_idx=page_url_idx,
        price_idx=price_idx,
        price_min=price_min,
        price_max=price_max,
        wishlist_idx=wishlist_idx,
        wishlist_min=wishlist_min,
        wishlist_max=wishlist_max,
        scientific_name_idx=scientific_name_idx,
        signal_col_idx=None,  # Snapshot has no signal column
        stock_pattern_col_idx=None,  # Snapshot has no stock pattern column
        drivers_col_idx=None,  # Snapshot has no drivers column
        sortable=True,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )


def generate_history_page(config: BasePageConfig) -> str:
    """Generate a history page for historical scrape data (raw data display)."""
    # Read CSV file
    headers, rows = read_csv_file(config.csv_filename)
    
    # Format scrape_datetime column (date-only unless collision)
    if headers and rows and 'scrape_datetime' in headers:
        datetime_idx = headers.index('scrape_datetime')
        datetimes = [row[datetime_idx] for row in rows]
        formatted_dates = format_datetime_smart(datetimes)
        for i, row in enumerate(rows):
            row[datetime_idx] = formatted_dates[i]
    
    # Load sparkline data from history CSV for conversion
    sparkline_data = load_historical_sparkline_data()
    
    # Convert Unicode sparklines to SVG in rows
    if headers and rows:
        rows = convert_sparklines_in_rows(headers, rows, sparkline_data, config.csv_filename)
    
    # Find column indices for special rendering
    page_url_idx = None
    scientific_name_idx = None
    price_idx = None
    if headers:
        try:
            page_url_idx = headers.index('page_url')
            scientific_name_idx = headers.index('scientific_name')
        except ValueError:
            pass
        try:
            price_idx = headers.index('price_gbp')
        except ValueError:
            pass

    # Calculate price range from data
    price_min, price_max, found_prices = _calculate_column_range(
        rows=rows,
        col_idx=price_idx,
        default_min=5,
        default_max=400,
        parser=_parse_price_value
    )
    # Round up max price for better UX (only when actual prices found)
    if found_prices:
        price_max = price_max + 1

    # Enumerate headers and rows for template
    headers_enum = list(enumerate(headers)) if headers else []
    rows_enum = [list(enumerate(row)) for row in rows] if rows else []

    template = jinja_env.get_template('history_page.html')
    return template.render(
        page_title=config.title,
        description=config.description,
        csv_filename=config.csv_filename,
        table_id=config.table_id,
        active_page=config.active_page,
        path_prefix="",
        search_filter=getattr(config, 'search_filter', True),
        headers=headers_enum,
        rows=rows_enum,
        page_url_idx=page_url_idx,
        price_idx=price_idx,
        price_min=price_min,
        price_max=price_max,
        scientific_name_idx=scientific_name_idx,
        signal_col_idx=None,  # History has no signal column
        stock_pattern_col_idx=None,  # History has no stock pattern column
        drivers_col_idx=None,  # History has no drivers column
        sortable=True,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )


def generate_analysis_page(config: BasePageConfig) -> str:
    """Generate an analysis page (breeder/dealer) with table from CSV and analysis using Jinja2 template.
    
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
        html = generate_analysis_page(config)
    """
    # Validate that this function is only used for analysis pages
    assert config.active_page in ("breeder", "dealer"), \
        f"generate_analysis_page only serves breeder/dealer pages, got: {config.active_page}"
    headers, rows = read_csv_file(config.csv_filename)
    
    # Load historical data if available to enrich sparklines with values
    historical_data = load_historical_sparkline_data()
    
    # Convert Unicode sparklines to SVG in sparkline columns
    if headers and rows:
        rows = convert_sparklines_in_rows(headers, rows, historical_data, config.csv_filename)
    
    # Extract summary stats from analysis markdown (if config has this attribute)
    analysis_markdown = getattr(config, 'analysis_markdown', None)
    summary_stats = extract_summary_stats(analysis_markdown) if analysis_markdown else None
    
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
    
    # Get optional markdown fields (may not exist on all config types)
    examples_markdown = getattr(config, 'examples_markdown', None)
    examples_html = parse_markdown_to_html(examples_markdown) if examples_markdown else None
    
    # Wrap legend markdown in details tag and convert
    legend_html = None
    legend_markdown = getattr(config, 'legend_markdown', None)
    if legend_markdown:
        legend_with_wrapper = f'<details markdown="1">\n<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>\n\n{legend_markdown}\n\n</details>'
        legend_html = parse_markdown_to_html(legend_with_wrapper)
    
    # Find column indices for special rendering
    page_url_idx = None
    scientific_name_idx = None
    species_idx = None
    size_idx = None
    signal_col_idx = None
    stock_pattern_col_idx = None
    if headers:
        try:
            page_url_idx = headers.index('page_url')
            scientific_name_idx = headers.index('scientific_name')
        except ValueError:
            pass
        
        # For breeder/dealer tables with species page linking
        link_to_species_page = getattr(config, 'link_to_species_page', False)
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
    
    # Find drivers column index for tooltip rendering
    # Drivers column exists in breeder/dealer tables but not history/snapshot
    drivers_col_idx = headers.index('Drivers') if headers and 'Drivers' in headers else None
    
    template = jinja_env.get_template('analysis_page.html')
    return template.render(
        page_title=config.title,
        description=config.description,
        csv_filename=config.csv_filename,
        table_id=config.table_id,
        active_page=config.active_page,
        path_prefix="",
        search_filter=getattr(config, 'search_filter', True),
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
        drivers_col_idx=drivers_col_idx,
        sortable=True,
        page_url_idx=page_url_idx,
        scientific_name_idx=scientific_name_idx,
        species_idx=species_idx,
        size_idx=size_idx,
        link_to_species_page=getattr(config, 'link_to_species_page', False),
        table_view=getattr(config, 'table_view', 'breeder'),
        signal_col_idx=signal_col_idx,
        stock_pattern_col_idx=stock_pattern_col_idx,
        stock_pattern_counts=stock_pattern_counts,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )


def _build_common_name_map(history_csv: str) -> dict:
    """
    Build a mapping of scientific names to common names from history CSV.
    
    Args:
        history_csv: Path to history CSV file
        
    Returns:
        Dict mapping scientific names to common names
    """
    history_headers, history_rows = read_csv_file(history_csv)
    common_name_map = {}
    
    if history_headers and history_rows:
        sci_idx = history_headers.index("scientific_name")
        common_idx = history_headers.index("common_name")
        for row in history_rows:
            if sci_idx < len(row) and common_idx < len(row):
                common_name_map[row[sci_idx]] = row[common_idx]
    
    return common_name_map


def generate_species_pages() -> int:
    """Generate individual species detail pages.
    
    Returns:
        Number of species pages generated
    """
    # Use already-imported functions from top of module
    # (Imports at top work because this function is called after module initialization)
    
    # Create species subdirectory
    species_dir = OUTPUT_DIR / "species"
    species_dir.mkdir(exist_ok=True)
    
    # Get unique species list from breeder and dealer CSVs
    breeder_csv = "breeder_opportunity_table.csv"
    dealer_csv = "dealer_supply_risk_table.csv"
    history_csv = "spidershop_spiderlings_history.csv"
    
    # Check if CSVs exist
    if not os.path.exists(breeder_csv) and not os.path.exists(dealer_csv):
        print("  ⚠️ No breeder or dealer CSVs found, skipping species pages")
        return 0
    
    if not os.path.exists(history_csv):
        print("  ⚠️ No history CSV found, skipping species pages")
        return 0
    
    # Get species list
    species_list = get_species_list(
        breeder_csv_path=breeder_csv if os.path.exists(breeder_csv) else None,
        dealer_csv_path=dealer_csv if os.path.exists(dealer_csv) else None
    )
    
    if not species_list:
        print("  ⚠️ No species found in current tables")
        return 0
    
    print(f"  Generating {len(species_list)} species pages...")
    
    # Build common name mapping from history
    common_name_map = _build_common_name_map(history_csv)
    
    # Generate each species page
    for scientific_name, size in species_list:
        slug = slugify_species(scientific_name)
        common_name = common_name_map.get(scientific_name, "")
        
        # Get species data from all CSVs
        species_data = get_species_data(
            scientific_name, size,
            breeder_csv, dealer_csv, history_csv
        )
        
        # Build chart data (last 26 runs)
        chart_data = build_chart_data(scientific_name, size, history_csv)
        
        # Get page URL from most recent observation
        page_url = get_page_url(scientific_name, size, history_csv)
        
        # Determine default view based on which table has data
        default_view = "breeder" if species_data["breeder"] else "dealer"
        
        # Generate page HTML
        html = generate_species_page(
            scientific_name=scientific_name,
            common_name=common_name,
            size=size,
            species_data=species_data,
            chart_data=chart_data,
            page_url=page_url,
            default_view=default_view
        )
        
        # Write to file
        output_path = species_dir / f"{slug}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    
    print(f"    Generated {len(species_list)} species pages in species/ directory")
    return len(species_list)


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
        from website.page_config import SnapshotPageConfig
        f.write(generate_snapshot_page(config=SnapshotPageConfig(
            title="Latest Snapshot",
            description="Current scrape results showing all available tarantula spiderlings.",
            csv_filename="spidershop_spiderlings_scrape.csv",
            table_id="snapshot-table",
            active_page="snapshot"
        )))
    
    # Generate history page
    print("  Generating history.html...")
    with open(OUTPUT_DIR / "history.html", "w", encoding="utf-8") as f:
        from website.page_config import HistoryPageConfig
        f.write(generate_history_page(config=HistoryPageConfig(
            title="Historical Data",
            description="Accumulated historical pricing data across all scrape runs.",
            csv_filename="spidershop_spiderlings_history.csv",
            table_id="history-table",
            active_page="history"
        )))
    
    # Generate breeder opportunity page
    print("  Generating breeder.html...")
    with open(OUTPUT_DIR / "breeder.html", "w", encoding="utf-8") as f:
        from website.page_config import BreederPageConfig
        f.write(generate_analysis_page(config=BreederPageConfig(
            title="Breeder Opportunities",
            description="Analysis showing breeding opportunities based on market trends and pricing patterns.",
            csv_filename="breeder_opportunity_table.csv",
            table_id="breeder-table",
            active_page="breeder",
            analysis_markdown=breeder_analysis,
            legend_markdown=breeder_legend,
            examples_markdown=breeder_examples,
            link_to_species_page=True,
            table_view="breeder"
        )))
    
    # Generate dealer supply risk page
    print("  Generating dealer.html...")
    with open(OUTPUT_DIR / "dealer.html", "w", encoding="utf-8") as f:
        from website.page_config import DealerPageConfig
        f.write(generate_analysis_page(config=DealerPageConfig(
            title="Dealer Supply Risk",
            description="Analysis highlighting inventory availability patterns and supply risk indicators.",
            csv_filename="dealer_supply_risk_table.csv",
            table_id="dealer-table",
            active_page="dealer",
            analysis_markdown=dealer_analysis,
            legend_markdown=dealer_legend,
            examples_markdown=dealer_examples,
            link_to_species_page=True,
            table_view="dealer"
        )))
    
    # Generate species detail pages
    print("  Generating species detail pages...")
    species_count = generate_species_pages()
    
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
    
    # Copy JavaScript files to output directory
    print("  Copying JavaScript files...")
    scripts_dir = Path(__file__).parent.parent.parent / "templates" / "scripts"
    js_files = ["constants.js", "utils.js", "table-interactions.js", "species-detail.js", "table-setup.js"]
    
    for js_file in js_files:
        js_source = scripts_dir / js_file
        if js_source.exists():
            with open(js_source, "r", encoding="utf-8") as src:
                content = src.read()
            with open(OUTPUT_DIR / js_file, "w", encoding="utf-8") as dst:
                dst.write(content)
            print(f"    Copied {js_file}")
    
    # Copy CSS files for species detail pages
    print("  Copying CSS files...")
    css_files = ["common.css", "analysis.css", "species-detail.css"]
    templates_dir = Path(__file__).parent.parent.parent / "templates"
    
    for css_file in css_files:
        css_source = templates_dir / css_file
        if css_source.exists():
            with open(css_source, "r", encoding="utf-8") as src:
                content = src.read()
            with open(OUTPUT_DIR / css_file, "w", encoding="utf-8") as dst:
                dst.write(content)
            print(f"    Copied {css_file}")
    
    print(f"\n✅ Website generated successfully in '{OUTPUT_DIR}' directory")
    print(f"   Total HTML pages: {5 + species_count} (5 main pages + {species_count} species pages)")


if __name__ == "__main__":
    main()

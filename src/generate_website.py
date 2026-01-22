#!/usr/bin/env python3
"""
Generate a static HTML website from scraped CSV data for GitHub Pages deployment.
"""

import csv
import os
import re
import markdown
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Output directory for the generated website
OUTPUT_DIR = Path("website")

# Setup Jinja2 environment
template_dir = Path(__file__).parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)


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
    try:
        page_url_idx = headers.index('page_url')
        scientific_name_idx = headers.index('scientific_name')
    except ValueError:
        pass  # Columns not found, render normally
    
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
        scientific_name_idx=scientific_name_idx
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


def generate_data_page(title, description, csv_filename, table_id, active_page, search_filter=True, analysis_markdown=None, legend_markdown=None, examples_markdown=None):
    """Generate a data page with table from CSV and optional analysis using Jinja2 template."""
    headers, rows = read_csv_file(csv_filename)
    
    # Convert markdown to HTML if provided
    analysis_html = parse_markdown_to_html(analysis_markdown) if analysis_markdown else None
    examples_html = parse_markdown_to_html(examples_markdown) if examples_markdown else None
    
    # Wrap legend markdown in details tag and convert
    legend_html = None
    if legend_markdown:
        legend_with_wrapper = f'<details markdown="1">\n<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>\n\n{legend_markdown}\n\n</details>'
        legend_html = parse_markdown_to_html(legend_with_wrapper)
    
    # Find column indices for special rendering
    page_url_idx = None
    scientific_name_idx = None
    if headers:
        try:
            page_url_idx = headers.index('page_url')
            scientific_name_idx = headers.index('scientific_name')
        except ValueError:
            pass
    
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
        legend_html=legend_html,
        examples_html=examples_html,
        headers=headers_enum,
        rows=rows_enum,
        sortable=True,
        page_url_idx=page_url_idx,
        scientific_name_idx=scientific_name_idx,
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

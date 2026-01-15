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

# Output directory for the generated website
OUTPUT_DIR = Path("website")


def parse_markdown_to_html(markdown_text):
    """Convert markdown to HTML using the markdown library.
    
    Uses the 'tables' and 'fenced_code' extensions for enhanced support.
    """
    if not markdown_text:
        return ""
    
    # Configure markdown with extensions
    md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    
    # Convert markdown to HTML
    html = md.convert(markdown_text)
    
    # Add our custom class to tables for styling consistency
    html = html.replace('<table>', '<table class="data-table markdown-table">')
    
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
        r'<details>.*?<summary><strong>ℹ️ How to read these tables \(Legend\)</strong></summary>(.*?)</details>',
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
    """Escape HTML special characters."""
    if text is None:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def generate_table_html(headers, rows, table_id, sortable=True):
    """Generate HTML table from headers and rows."""
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
    
    html = f'<table id="{table_id}" class="data-table">\n'
    html += "  <thead>\n    <tr>\n"
    
    for i, header in enumerate(headers):
        if sortable:
            html += f'      <th onclick="sortTable({i}, \'{table_id}\')">{escape_html(header)} <span class="sort-indicator">⇅</span></th>\n'
        else:
            html += f'      <th>{escape_html(header)}</th>\n'
    
    html += "    </tr>\n  </thead>\n"
    html += "  <tbody>\n"
    
    for row in rows:
        html += "    <tr>\n"
        for i, cell in enumerate(row):
            # Special rendering for page_url column
            if i == page_url_idx and page_url_idx is not None and scientific_name_idx is not None:
                url = cell.strip() if cell else ""
                scientific_name = row[scientific_name_idx] if scientific_name_idx < len(row) else ""
                
                if url:
                    html += f'      <td><a href="{escape_html(url)}" target="_blank" rel="noopener noreferrer">{escape_html(scientific_name)}</a></td>\n'
                else:
                    html += f"      <td>{escape_html(cell)}</td>\n"
            else:
                html += f"      <td>{escape_html(cell)}</td>\n"
        html += "    </tr>\n"
    
    html += "  </tbody>\n</table>\n"
    return html


def get_base_html_template(title, active_page=""):
    """Return the base HTML template with navigation."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(title)} - Spider Shop Historical Analysis</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: #2c3e50;
            color: white;
            padding: 20px 0;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        header .container {{
            padding: 0 20px;
        }}
        
        header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        nav {{
            background: white;
            padding: 15px 0;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        
        nav ul {{
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 0 20px;
        }}
        
        nav a {{
            color: #2c3e50;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
            transition: background 0.3s;
            display: block;
        }}
        
        nav a:hover {{
            background: #ecf0f1;
        }}
        
        nav a.active {{
            background: #3498db;
            color: white;
        }}
        
        .content {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }}
        
        h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        
        h3 {{
            color: #34495e;
            margin: 20px 0 15px 0;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            font-size: 0.95rem;
        }}
        
        .data-table th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .data-table th:hover {{
            background: #2c3e50;
        }}
        
        .sort-indicator {{
            font-size: 0.8em;
            margin-left: 5px;
            opacity: 0.6;
        }}
        
        .data-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .data-table tbody tr:hover {{
            background: #f8f9fa;
        }}
        
        .data-table tbody tr:nth-child(even) {{
            background: #fafafa;
        }}
        
        .data-table tbody tr:nth-child(even):hover {{
            background: #f0f0f0;
        }}
        
        .info-box {{
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .download-links {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .download-links a {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 10px 20px;
            margin: 5px 10px 5px 0;
            border-radius: 5px;
            text-decoration: none;
            transition: background 0.3s;
        }}
        
        .download-links a:hover {{
            background: #2980b9;
        }}
        
        .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .card {{
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            padding: 20px;
            transition: box-shadow 0.3s;
        }}
        
        .card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .card h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        
        .card p {{
            color: #666;
            margin: 10px 0;
        }}
        
        .card a {{
            color: #3498db;
            text-decoration: none;
            font-weight: 600;
        }}
        
        .card a:hover {{
            text-decoration: underline;
        }}
        
        footer {{
            text-align: center;
            padding: 30px 20px;
            color: #7f8c8d;
            margin-top: 50px;
        }}
        
        footer a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        footer a:hover {{
            text-decoration: underline;
        }}
        
        .table-controls {{
            margin: 20px 0;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .table-controls input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 0.95rem;
            flex: 1;
            min-width: 200px;
        }}
        
        .table-controls label {{
            font-weight: 600;
            color: #555;
        }}
        
        .analysis-section {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            margin: 30px 0;
            border-left: 4px solid #3498db;
        }}
        
        .analysis-section h2 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        
        .analysis-section h3 {{
            color: #34495e;
            margin-top: 25px;
        }}
        
        .analysis-section p {{
            margin: 10px 0;
            line-height: 1.8;
        }}
        
        .analysis-section ul {{
            margin: 10px 0 10px 20px;
        }}
        
        .analysis-section li {{
            margin: 5px 0;
        }}
        
        .analysis-section code {{
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        .analysis-section hr {{
            margin: 30px 0;
            border: none;
            border-top: 2px solid #dee2e6;
        }}
        
        .markdown-table {{
            margin: 20px 0 !important;
            font-size: 0.9rem !important;
        }}
        
        details {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #e1e8ed;
        }}
        
        details summary {{
            cursor: pointer;
            font-weight: 600;
            color: #2c3e50;
            padding: 10px;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        
        details summary:hover {{
            background: #f8f9fa;
        }}
        
        details[open] summary {{
            margin-bottom: 15px;
            border-bottom: 1px solid #e1e8ed;
        }}
        
        @media (max-width: 768px) {{
            .data-table {{
                font-size: 0.85rem;
            }}
            
            .data-table th,
            .data-table td {{
                padding: 8px;
            }}
            
            header h1 {{
                font-size: 1.5rem;
            }}
            
            nav ul {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>🕷️ Spider Shop Historical Analysis</h1>
            <p>Tarantula Spiderling Pricing & Market Data</p>
        </div>
    </header>
    
    <nav>
        <div class="container">
            <ul>
                <li><a href="index.html" class="{'active' if active_page == 'home' else ''}">Home</a></li>
                <li><a href="snapshot.html" class="{'active' if active_page == 'snapshot' else ''}">Latest Snapshot</a></li>
                <li><a href="history.html" class="{'active' if active_page == 'history' else ''}">Historical Data</a></li>
                <li><a href="breeder.html" class="{'active' if active_page == 'breeder' else ''}">Breeder Opportunities</a></li>
                <li><a href="dealer.html" class="{'active' if active_page == 'dealer' else ''}">Dealer Supply Risk</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container">
"""


def get_html_footer():
    """Return the HTML footer with closing tags."""
    return """    </div>
    
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
</html>""".format(timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))


def generate_homepage(last_scrape_time=None):
    """Generate the homepage with overview and links."""
    html = get_base_html_template("Home", "home")
    
    html += '        <div class="content">\n'
    html += '            <h2>Welcome to Spider Shop Historical Analysis</h2>\n'
    
    if last_scrape_time:
        html += f'            <div class="info-box">\n'
        html += f'                <strong>Last Updated:</strong> {escape_html(last_scrape_time)}\n'
        html += '            </div>\n'
    
    html += """            <p>This website provides historical pricing data and market analysis for tarantula spiderlings from The Spider Shop UK. The data is automatically scraped and updated weekly.</p>
            
            <h3>Available Data</h3>
            
            <div class="card-grid">
                <div class="card">
                    <h3>📸 Latest Snapshot</h3>
                    <p>View the most recent scrape of all available spiderling listings, including scientific names, common names, sizes, and prices.</p>
                    <a href="snapshot.html">View Snapshot →</a>
                </div>
                
                <div class="card">
                    <h3>📊 Historical Data</h3>
                    <p>Explore accumulated pricing data across all scrapes to track trends and price changes over time.</p>
                    <a href="history.html">View History →</a>
                </div>
                
                <div class="card">
                    <h3>🌱 Breeder Opportunities</h3>
                    <p>Analysis showing breeding opportunities based on market trends and pricing patterns.</p>
                    <a href="breeder.html">View Analysis →</a>
                </div>
                
                <div class="card">
                    <h3>📦 Dealer Supply Risk</h3>
                    <p>Analysis highlighting inventory availability patterns and supply risk indicators.</p>
                    <a href="dealer.html">View Analysis →</a>
                </div>
            </div>
            
            <h3>Download Raw Data</h3>
            <div class="download-links">
                <a href="spidershop_spiderlings_scrape.csv" download>⬇️ Download Snapshot CSV</a>
                <a href="spidershop_spiderlings_history.csv" download>⬇️ Download History CSV</a>
                <a href="breeder_opportunity_table.csv" download>⬇️ Download Breeder Table CSV</a>
                <a href="dealer_supply_risk_table.csv" download>⬇️ Download Dealer Table CSV</a>
            </div>
            
            <h3>About This Project</h3>
            <p>This project automatically scrapes tarantula spiderling listings from The Spider Shop UK website on a weekly schedule. The data captures:</p>
            <ul style="margin: 15px 0 15px 30px;">
                <li><strong>Scientific name</strong> (Genus + species)</li>
                <li><strong>Common name</strong> (descriptive name)</li>
                <li><strong>Size</strong> (in centimeters)</li>
                <li><strong>Price</strong> (in GBP)</li>
            </ul>
            <p>The collected data is used to track pricing history over time for market analysis and generate opportunity matrices for breeders and dealers.</p>
        </div>
"""
    
    html += get_html_footer()
    return html


def generate_data_page(title, description, csv_filename, table_id, active_page, search_filter=True, analysis_markdown=None, legend_markdown=None, examples_markdown=None):
    """Generate a data page with table from CSV and optional analysis."""
    html = get_base_html_template(title, active_page)
    
    html += '        <div class="content">\n'
    html += f'            <h2>{escape_html(title)}</h2>\n'
    html += f'            <p>{escape_html(description)}</p>\n'
    
    html += f'            <div class="download-links">\n'
    html += f'                <a href="{csv_filename}" download>⬇️ Download CSV</a>\n'
    html += '            </div>\n'
    
    # Add analysis section if provided
    if analysis_markdown:
        html += '            <div class="analysis-section">\n'
        html += parse_markdown_to_html(analysis_markdown)
        html += '            </div>\n'
    
    headers, rows = read_csv_file(csv_filename)
    
    if headers and rows:
        # Add full table header
        html += '            <h3>Full Data Table</h3>\n'
        
        if search_filter:
            html += f'            <div class="table-controls">\n'
            html += f'                <label for="search-{table_id}">Search:</label>\n'
            html += f'                <input type="text" id="search-{table_id}" placeholder="Type to filter..." onkeyup="filterTable(this, \'{table_id}\')">\n'
            html += '            </div>\n'
        
        html += f'            <div style="overflow-x: auto;">\n'
        html += f'                {generate_table_html(headers, rows, table_id)}\n'
        html += '            </div>\n'
        html += f'            <p style="margin-top: 15px; color: #666;"><strong>Total rows:</strong> {len(rows)}</p>\n'
    else:
        html += '            <div class="info-box">\n'
        html += '                <p>No data available yet. Please check back after the next scrape run.</p>\n'
        html += '            </div>\n'
    
    # Add legend if provided
    if legend_markdown:
        html += '            <details>\n'
        html += '                <summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>\n'
        html += '                <div style="padding: 15px;">\n'
        html += parse_markdown_to_html(legend_markdown)
        html += '                </div>\n'
        html += '            </details>\n'
    
    # Add examples section if provided (separate from legend)
    if examples_markdown:
        html += '            <details open>\n'
        html += '                <summary><strong>📖 Practical Examples</strong></summary>\n'
        html += '                <div style="padding: 15px;">\n'
        html += parse_markdown_to_html(examples_markdown)
        html += '                </div>\n'
        html += '            </details>\n'
    
    html += '        </div>\n'
    html += get_html_footer()
    return html


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

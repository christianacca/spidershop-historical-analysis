"""Markdown processing utilities for website generation.

This module handles markdown-to-HTML conversion and content extraction.
"""

import os
import re
import markdown
from typing import Optional, Dict, Tuple


def parse_markdown_to_html(markdown_text: Optional[str]) -> str:
    """Convert markdown to HTML using the markdown library.
    
    Uses the 'tables', 'fenced_code', and 'md_in_html' extensions.
    Downgrades heading levels (h2→h3, h3→h4) to maintain proper hierarchy.
    Adds data-label attributes to table cells for responsive card layout.
    
    Args:
        markdown_text: Markdown content to convert
        
    Returns:
        HTML string, or empty string if input is None/empty
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
    
    Args:
        html: HTML string containing tables
        
    Returns:
        Modified HTML with data-label attributes added
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
    
    Args:
        markdown: Markdown content to parse
        
    Returns:
        Dict with keys: total, hot, watch, avoid, or None if not found
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


def extract_analysis_sections(markdown_file: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extract analysis text (summary stats only) from markdown file.
    
    Tables are no longer extracted - they will be rendered directly from CSV files.
    This function only extracts the Summary line for statistics.
    
    Args:
        markdown_file: Path to markdown file
        
    Returns:
        Tuple of (breeder_md, dealer_md, breeder_legend, dealer_legend, 
                  breeder_examples, dealer_examples)
        All values can be None if sections are not found
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
                    dealer_legend = (
                        '### 🏪 Dealer Supply Risk Matrix — Legend\n\n'
                        + dealer_examples_split[0].strip()
                    )
                    dealer_examples = '### 📖 Dealer Matrix — Practical Examples' + dealer_examples_split[1]
    
    return breeder_md, dealer_md, breeder_legend, dealer_legend, breeder_examples, dealer_examples

#!/usr/bin/env python3
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from assertions import get_summary_path
from legend_examples import generate_breeder_examples, generate_dealer_examples

# =====================
# LEGEND
# =====================

def write_summary_legend():
    summary_path = get_summary_path()
    if not summary_path:
        return

    # Set up Jinja2 environment
    templates_dir = Path(__file__).parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("legend.md")
    
    # Render legend with dynamically generated examples
    legend_content = template.render(
        breeder_examples=generate_breeder_examples(),
        dealer_examples=generate_dealer_examples()
    )
    
    # Append to summary file
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(legend_content)

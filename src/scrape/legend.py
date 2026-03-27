#!/usr/bin/env python3
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from shared.assertions import get_summary_path
from scrape.legend_examples import generate_breeder_examples, generate_dealer_examples

# =====================
# LEGEND
# =====================

def render_summary_legend() -> str:
    templates_dir = Path(__file__).parent.parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("legend.md")

    return template.render(
        breeder_examples=generate_breeder_examples(),
        dealer_examples=generate_dealer_examples(),
    )

def write_summary_legend():
    summary_path = get_summary_path()
    if not summary_path:
        return

    legend_content = render_summary_legend()
    
    # Append to summary file
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(legend_content)

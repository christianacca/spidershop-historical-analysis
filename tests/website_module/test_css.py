#!/usr/bin/env python3
"""Tests for CSS validation."""
import pytest
from pathlib import Path
from bs4 import BeautifulSoup
from website import get_base_html_template


def get_css_content(css_filename: str) -> str:
    """Read CSS content from templates directory."""
    css_path = Path(__file__).parent.parent.parent / "templates" / css_filename
    with open(css_path, "r", encoding="utf-8") as f:
        return f.read()


class TestCssValidation:
    """CSS validation tests to ensure styles are well-formed and complete."""

    def test_css_contains_critical_selectors(self):
        """Should include critical CSS selectors for layout in common.css."""
        css = get_css_content("common.css")
        
        critical_selectors = [
            "body",
            "header",
            "nav",
            "footer",
            ".container",
            "table",
            "th",
            "td",
        ]
        
        for selector in critical_selectors:
            assert selector in css, f"Missing critical selector in common.css: {selector}"

    def test_css_contains_responsive_breakpoints(self):
        """Should include media queries for responsive design in common.css."""
        css = get_css_content("common.css")
        
        # Check for media query presence
        assert "@media" in css
        assert "max-width" in css or "min-width" in css

    def test_css_has_proper_bracing(self):
        """Should have balanced braces in CSS files."""
        for css_file in ["common.css", "analysis.css"]:
            css = get_css_content(css_file)
            
            open_braces = css.count("{")
            close_braces = css.count("}")
            
            assert open_braces == close_braces, f"Unbalanced CSS braces in {css_file}"
            assert open_braces > 0, f"No CSS rules found in {css_file}"

    def test_css_includes_table_styling(self):
        """Should include comprehensive table styling in common.css."""
        css = get_css_content("common.css")
        
        # Check for key table elements
        required_table_elements = ["table", "th", "td"]
        
        for element in required_table_elements:
            assert element in css, f"Missing table element styling in common.css: {element}"

    def test_css_has_proper_semicolons(self):
        """Should have semicolons after CSS property values."""
        for css_file in ["common.css", "analysis.css"]:
            css = get_css_content(css_file)
            
            # Count property-value pairs (rough heuristic: look for colons in rules)
            style_blocks = css.split("}")
            
            for block in style_blocks:
                if "{" in block and ":" in block:
                    # Extract the rules part (after opening brace)
                    rules_part = block.split("{")[-1]
                    colon_count = rules_part.count(":")
                    semicolon_count = rules_part.count(";")
                    
                    # Allow for last property to optionally omit semicolon
                    if colon_count > 0:
                        assert semicolon_count >= colon_count - 1, \
                            f"Missing semicolons in {css_file} block: {block[:50]}..."

    def test_css_box_model_consistency(self):
        """Should use consistent box-sizing model in common.css."""
        css = get_css_content("common.css")
        
        # Modern best practice: use border-box for predictable sizing
        assert "box-sizing" in css
        assert "border-box" in css

    def test_css_font_specifications(self):
        """Should specify font families and sizes in common.css."""
        css = get_css_content("common.css")
        
        assert "font-family" in css
        assert "font-size" in css or "rem" in css or "em" in css

    def test_css_no_obvious_typos(self):
        """Should not contain common CSS property typos."""
        for css_file in ["common.css", "analysis.css"]:
            css = get_css_content(css_file).lower()
            
            # Common typos to check for
            typos = [
                "colr:",  # color typo
                "widht:",  # width typo
                "heigth:",  # height typo
                "margn:",  # margin typo
                "paddin:",  # padding typo
            ]
            
            for typo in typos:
                assert typo not in css, f"Found possible typo in {css_file}: {typo}"

    def test_css_layout_properties_present(self):
        """Should include modern layout properties in common.css."""
        css = get_css_content("common.css")
        
        # Should use modern layout techniques
        has_modern_layout = (
            "display: flex" in css or
            "display: grid" in css or
            "display:flex" in css or
            "display:grid" in css
        )
        
        assert has_modern_layout, "No modern layout properties found in common.css"

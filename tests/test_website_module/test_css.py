#!/usr/bin/env python3
"""Tests for CSS validation."""
import pytest
from bs4 import BeautifulSoup
from website import get_base_html_template


class TestCssValidation:
    """CSS validation tests to ensure styles are well-formed and complete."""

    def test_css_is_present_in_template(self):
        """Should include CSS in base template."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        style = soup.find("style")
        
        assert style is not None
        assert len(style.string) > 100  # Should have substantial CSS

    def test_css_contains_critical_selectors(self):
        """Should include critical CSS selectors for layout."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
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
            assert selector in css, f"Missing critical selector: {selector}"

    def test_css_contains_responsive_breakpoints(self):
        """Should include media queries for responsive design."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Check for media query presence
        assert "@media" in css
        assert "max-width" in css or "min-width" in css

    def test_css_has_proper_bracing(self):
        """Should have balanced braces in CSS."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        open_braces = css.count("{")
        close_braces = css.count("}")
        
        assert open_braces == close_braces, "Unbalanced CSS braces"
        assert open_braces > 0, "No CSS rules found"

    def test_css_contains_color_scheme(self):
        """Should define color scheme variables or consistent colors."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Should have color definitions (hex, rgb, or named)
        has_colors = (
            "#" in css or  # Hex colors
            "rgb" in css or  # RGB colors
            "color:" in css  # Color properties
        )
        
        assert has_colors, "No color definitions found in CSS"

    def test_css_includes_table_styling(self):
        """Should include comprehensive table styling."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Check for key table elements (not all need explicit selectors)
        required_table_elements = ["table", "th", "td"]
        
        for element in required_table_elements:
            assert element in css, f"Missing table element styling: {element}"

    def test_css_includes_interactive_states(self):
        """Should include hover and active states for interactive elements."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Should have pseudo-class selectors for interactivity
        assert ":hover" in css, "Missing hover states"

    def test_css_has_proper_semicolons(self):
        """Should have semicolons after CSS property values."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Count property-value pairs (rough heuristic: look for colons in rules)
        # This is a basic sanity check, not exhaustive validation
        style_blocks = css.split("}")
        
        for block in style_blocks:
            if "{" in block and ":" in block:
                # Extract the rules part (after opening brace)
                rules_part = block.split("{")[-1]
                colon_count = rules_part.count(":")
                semicolon_count = rules_part.count(";")
                
                # Allow for last property to optionally omit semicolon
                # But most should have them
                if colon_count > 0:
                    assert semicolon_count >= colon_count - 1, \
                        f"Missing semicolons in CSS block: {block[:50]}..."

    def test_css_box_model_consistency(self):
        """Should use consistent box-sizing model."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Modern best practice: use border-box for predictable sizing
        assert "box-sizing" in css
        assert "border-box" in css

    def test_css_font_specifications(self):
        """Should specify font families and sizes."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        assert "font-family" in css
        assert "font-size" in css or "rem" in css or "em" in css

    def test_css_no_obvious_typos(self):
        """Should not contain common CSS property typos."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string.lower()
        
        # Common typos to check for
        typos = [
            "colr:",  # color typo
            "widht:",  # width typo
            "heigth:",  # height typo
            "margn:",  # margin typo
            "paddin:",  # padding typo
        ]
        
        for typo in typos:
            assert typo not in css, f"Found possible typo: {typo}"

    def test_css_layout_properties_present(self):
        """Should include modern layout properties."""
        html = get_base_html_template("Test", "test")
        soup = BeautifulSoup(html, "html.parser")
        css = soup.find("style").string
        
        # Should use modern layout techniques
        has_modern_layout = (
            "display: flex" in css or
            "display: grid" in css or
            "display:flex" in css or
            "display:grid" in css
        )
        
        assert has_modern_layout, "No modern layout properties found"



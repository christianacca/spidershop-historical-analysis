#!/usr/bin/env python3
"""Tests for CSS validation."""
import pytest
from pathlib import Path
from bs4 import BeautifulSoup


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


class TestHamburgerNavCss:
    """CSS structure tests for the hamburger navigation (Phase 13).

    These tests verify that common.css contains the correct selectors and rules
    to implement the hamburger toggle pattern.  They do NOT test computed styles
    (those are E2E / visual-contract tests) — they only confirm the rules are
    present and that the CSS is structurally consistent.
    """

    def test_nav_toggle_selector_present(self):
        """common.css must define a .nav-toggle rule (desktop: hidden)."""
        css = get_css_content("common.css")
        assert ".nav-toggle" in css, ".nav-toggle selector must exist in common.css"

    def test_nav_toggle_bar_selector_present(self):
        """common.css must define .nav-toggle__bar for the three icon bars."""
        css = get_css_content("common.css")
        assert ".nav-toggle__bar" in css, ".nav-toggle__bar selector must exist in common.css"

    def test_nav_toggle_hidden_by_default(self):
        """The desktop rule must set display:none on .nav-toggle so it only
        appears on mobile via the media query override."""
        css = get_css_content("common.css")
        # The desktop block appears before any @media query.
        # Find the .nav-toggle rule and assert display:none is inside it.
        desktop_block_end = css.find("@media")
        desktop_css = css[:desktop_block_end] if desktop_block_end != -1 else css
        toggle_start = desktop_css.find(".nav-toggle")
        assert toggle_start != -1, ".nav-toggle must be defined outside media queries"
        block_start = desktop_css.find("{", toggle_start)
        block_end = desktop_css.find("}", block_start)
        rule_block = desktop_css[block_start:block_end]
        assert "display: none" in rule_block or "display:none" in rule_block, (
            ".nav-toggle must have display:none in the desktop (non-media-query) block"
        )

    def test_nav_toggle_visible_in_mobile_media_query(self):
        """Inside the ≤768 px media query, .nav-toggle must be display:flex."""
        css = get_css_content("common.css")
        assert ".nav-toggle" in css
        # Confirm display:flex appears after a max-width:768px media query.
        mobile_query_idx = css.find("max-width: 768px")
        assert mobile_query_idx != -1, "≤768px breakpoint must exist in common.css"
        mobile_css = css[mobile_query_idx:]
        toggle_idx = mobile_css.find(".nav-toggle")
        assert toggle_idx != -1, ".nav-toggle must be re-declared inside the mobile breakpoint"
        block_start = mobile_css.find("{", toggle_idx)
        block_end = mobile_css.find("}", block_start)
        rule_block = mobile_css[block_start:block_end]
        assert "display: flex" in rule_block or "display:flex" in rule_block, (
            ".nav-toggle must have display:flex inside the ≤768px media query"
        )

    def test_nav_hidden_by_default_in_mobile_media_query(self):
        """Inside the ≤768 px media query, bare nav must be display:none."""
        css = get_css_content("common.css")
        mobile_query_idx = css.find("max-width: 768px")
        assert mobile_query_idx != -1
        mobile_css = css[mobile_query_idx:]
        # Find a standalone 'nav {' rule (not nav.nav--open or nav ul etc.)
        import re
        match = re.search(r'\bnav\s*\{([^}]*?)\}', mobile_css)
        assert match is not None, "A bare 'nav { }' rule must exist in the ≤768px block"
        rule_body = match.group(1)
        assert "display: none" in rule_body or "display:none" in rule_body, (
            "nav must be display:none by default inside the ≤768px media query"
        )

    def test_nav_open_state_in_mobile_media_query(self):
        """Inside the ≤768 px media query, nav.nav--open must be display:block."""
        css = get_css_content("common.css")
        mobile_query_idx = css.find("max-width: 768px")
        assert mobile_query_idx != -1
        mobile_css = css[mobile_query_idx:]
        assert "nav.nav--open" in mobile_css, (
            "nav.nav--open must be declared inside the ≤768px media query"
        )
        import re
        match = re.search(r'nav\.nav--open\s*\{([^}]*?)\}', mobile_css)
        assert match is not None
        rule_body = match.group(1)
        assert "display: block" in rule_body or "display:block" in rule_body, (
            "nav.nav--open must have display:block inside the ≤768px media query"
        )

    def test_nav_open_ul_stacks_vertically(self):
        """nav.nav--open ul must set flex-direction:column so links stack in one column."""
        css = get_css_content("common.css")
        mobile_query_idx = css.find("max-width: 768px")
        assert mobile_query_idx != -1
        mobile_css = css[mobile_query_idx:]
        assert "nav.nav--open ul" in mobile_css, (
            "nav.nav--open ul must be declared inside the ≤768px media query"
        )
        import re
        match = re.search(r'nav\.nav--open ul\s*\{([^}]*?)\}', mobile_css)
        assert match is not None
        rule_body = match.group(1)
        assert "flex-direction: column" in rule_body or "flex-direction:column" in rule_body, (
            "nav.nav--open ul must have flex-direction:column inside the ≤768px media query"
        )

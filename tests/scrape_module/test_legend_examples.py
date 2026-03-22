#!/usr/bin/env python3
"""
Tests for legend_examples.py - validates dynamically generated examples.

This module validates that:
1. The examples are generated from actual matrix computation logic
2. The generated results match the example descriptions
3. The examples include proper structure (scenario, data, analysis, why)
4. The synthetic data produces expected outcomes
"""
import pytest
from scrape.breeder_matrix import build_breeder_opportunity_table
from scrape.dealer_matrix import build_dealer_supply_risk_table
from scrape.legend_examples import (
    generate_breeder_examples,
    generate_dealer_examples,
    generate_breeder_example_1,
    generate_breeder_example_2,
    generate_breeder_example_3,
    generate_breeder_example_4,
    generate_breeder_example_5,
    generate_breeder_example_6,
    generate_breeder_example_8,
    generate_dealer_example_1,
    generate_dealer_example_2,
    generate_dealer_example_3,
    generate_dealer_example_4,
    generate_dealer_example_5,
    generate_dealer_example_6,
    generate_dealer_example_7,
)


class TestGeneratedBreederExamples:
    """Test dynamically generated breeder examples."""
    
    def test_breeder_examples_section_header(self):
        """Generated examples should have section header."""
        examples = generate_breeder_examples()
        assert "### 📖 Breeder Matrix — Practical Examples" in examples
    
    def test_breeder_example_1_sustained_scarcity(self):
        """Example 1 should demonstrate sustained scarcity (4+ OOS runs)."""
        example = generate_breeder_example_1()
        assert "#### Example 1: Sustained Scarcity (Strong Opportunity)" in example
        assert "**OOS:** OUT" in example
        assert "**OOS Runs:** 4" in example
        assert "**Stock Pattern:** Sustained" in example
        assert "**Signal:** 🔥" in example
    
    def test_breeder_example_2_emerging_with_price_rise(self):
        """Example 2 should demonstrate emerging scarcity with rising price."""
        example = generate_breeder_example_2()
        assert "#### Example 2: Emerging Scarcity with Rising Price" in example
        assert "**Stock Pattern:** Emerging" in example
        assert "**Price:** £30.00 ↑" in example
        assert "**Signal:** 🔥" in example
    
    def test_breeder_example_3_cyclical_pattern(self):
        """Example 3 should demonstrate cyclical availability pattern."""
        example = generate_breeder_example_3()
        assert "#### Example 3: Cyclical Pattern (Batch Supply)" in example
        assert "**OOS:** IN/OUT" in example
        assert "**Stock Pattern:** Cyclical" in example
        assert "**Signal:** ⚠️" in example
    
    def test_breeder_example_4_always_available(self):
        """Example 4 should demonstrate oversupplied market."""
        example = generate_breeder_example_4()
        assert "#### Example 4: Always Available (Oversupplied)" in example
        assert "**OOS:** IN" in example
        assert "**Stock Pattern:** Always" in example
        assert "**Signal:** ❌" in example
    
    def test_breeder_example_5_emerging_with_high_demand(self):
        """Example 5 should demonstrate emerging scarcity with wishlist surge."""
        example = generate_breeder_example_5()
        assert "#### Example 5: Emerging Opportunity with High Demand" in example
        assert "**Stock Pattern:** Emerging" in example
        assert "**Wishlist:**" in example
        assert "**Signal:** 🔥" in example
    
    def test_breeder_example_6_always_available_falling_interest(self):
        """Example 6 should demonstrate oversupplied market with declining interest."""
        example = generate_breeder_example_6()
        assert "#### Example 6: Always Available with Falling Interest" in example
        assert "**Stock Pattern:** Always" in example
        assert "**Wishlist:**" in example
        assert "**Signal:** ❌" in example

    def test_breeder_example_8_newly_observed(self):
        """Example 8 should demonstrate the limited-history hold state."""
        example = generate_breeder_example_8()
        assert "#### Example 8: Newly Observed (Limited History Hold State)" in example
        assert "**OOS:** IN" in example
        assert "**OOS Runs:** 0" in example
        assert "**Stock Pattern:** Newly Observed" in example
        assert "**Signal:** ⚠️" in example
        assert "limited history" in example.lower()


class TestGeneratedDealerExamples:
    """Test dynamically generated dealer examples."""
    
    def test_dealer_examples_section_header(self):
        """Generated examples should have section header."""
        examples = generate_dealer_examples()
        assert "### 📖 Dealer Matrix — Practical Examples" in examples
    
    def test_dealer_example_1_high_reliability(self):
        """Example 1 should demonstrate high reliability scenario."""
        example = generate_dealer_example_1()
        assert "#### Example 1: High Reliability (No Urgency)" in example
        # Reliability should be High (example aims for 9/10 = 90%)
        assert "**Dealer Risk:**" in example
    
    def test_dealer_example_2_medium_reliability(self):
        """Example 2 should demonstrate medium reliability scenario."""
        example = generate_dealer_example_2()
        assert "#### Example 2: Medium Reliability (Watch and Wait)" in example
        # Example aims for 50% availability
        assert "**Stock Reliability:**" in example
        assert "**Dealer Risk:**" in example
    
    def test_dealer_example_3_low_reliability_slow_restock(self):
        """Example 3 should demonstrate low reliability scenario."""
        example = generate_dealer_example_3()
        assert "#### Example 3: Low Reliability + Slow Restock (High Risk)" in example
        # Example aims for 3/10 = 30% availability
        assert "**Stock Reliability:**" in example
        assert "**Restock Speed:**" in example
        assert "**Dealer Risk:**" in example
    
    def test_dealer_example_4_low_reliability_high_demand(self):
        """Example 4 should demonstrate low reliability with high demand."""
        example = generate_dealer_example_4()
        assert "#### Example 4: Low Reliability + High Demand (Critical Risk)" in example
        # Example aims for 1/6 weeks with high wishlist
        assert "**Stock Reliability:**" in example
        assert "**Wishlist:**" in example
        assert "**Dealer Risk:**" in example
    
    def test_dealer_example_5_medium_reliability_surging_demand(self):
        """Example 5 should demonstrate medium reliability with surging demand."""
        example = generate_dealer_example_5()
        assert "#### Example 5: Medium Reliability + Surging Demand (Escalated Risk)" in example
        assert "**Stock Reliability:**" in example
        assert "**Wishlist:**" in example
        assert "**Dealer Risk:** 🔥" in example
    
    def test_dealer_example_6_high_reliability_falling_demand(self):
        """Example 6 should demonstrate high reliability with falling demand."""
        example = generate_dealer_example_6()
        assert "#### Example 6: High Reliability + Falling Demand (No Action Needed)" in example
        assert "**Stock Reliability:**" in example
        assert "**Wishlist:**" in example
        assert "**Dealer Risk:** ❌" in example
    
    def test_dealer_example_7_low_reliability_surging_interest(self):
        """Example 7 should demonstrate low reliability with surging interest."""
        example = generate_dealer_example_7()
        assert "#### Example 7: Low Reliability + Surging Interest (Early Warning)" in example
        assert "**Stock Reliability:**" in example
        assert "**Wishlist:**" in example
        assert "**Dealer Risk:**" in example


class TestExampleStructure:
    """Test that generated examples have proper structure."""
    
    def test_all_breeder_examples_have_scenarios(self):
        """All breeder examples should have scenario descriptions."""
        examples = generate_breeder_examples()
        example_count = examples.count("#### Example")
        scenario_count = examples.count("**Scenario:**")
        assert scenario_count == 8, f"Expected 8 scenarios, found {scenario_count}"
    
    def test_all_dealer_examples_have_scenarios(self):
        """All dealer examples should have scenario descriptions."""
        examples = generate_dealer_examples()
        example_count = examples.count("#### Example")
        scenario_count = examples.count("**Scenario:**")
        assert scenario_count == 7, f"Expected 7 scenarios, found {scenario_count}"
    
    def test_all_examples_have_analysis_results(self):
        """All examples should include Analysis Result sections."""
        breeder_examples = generate_breeder_examples()
        dealer_examples = generate_dealer_examples()
        
        breeder_count = breeder_examples.count("**Analysis Result:**")
        dealer_count = dealer_examples.count("**Analysis Result:**")
        
        # Breeder example 7 uses different headers: "**Breeder Analysis:**" and "**Dealer Analysis:**"
        breeder_analysis_count = breeder_examples.count("**Breeder Analysis:**")
        dealer_analysis_in_breeder_count = breeder_examples.count("**Dealer Analysis:**")
        
        # 7 standard examples + 1 special example with 2 analysis sections
        assert breeder_count == 7, f"Expected 7 standard analysis sections, found {breeder_count}"
        assert breeder_analysis_count == 1, f"Expected 1 Breeder Analysis section, found {breeder_analysis_count}"
        assert dealer_analysis_in_breeder_count == 1, f"Expected 1 Dealer Analysis section in breeder examples, found {dealer_analysis_in_breeder_count}"
        assert dealer_count == 7, f"Expected 7 dealer analysis sections, found {dealer_count}"
    
    def test_all_examples_have_why_explanations(self):
        """All examples should include Why explanations."""
        breeder_examples = generate_breeder_examples()
        dealer_examples = generate_dealer_examples()
        
        breeder_count = breeder_examples.count("**Why:**")
        dealer_count = dealer_examples.count("**Why:**")
        
        # Breeder example 7 has a different structure (Why the Different Metrics?)
        assert breeder_count == 7, f"Expected 7 breeder why sections, found {breeder_count}"
        assert dealer_count == 7, f"Expected 7 dealer why sections, found {dealer_count}"
    
    def test_examples_include_markdown_tables(self):
        """Examples should include markdown tables with data."""
        breeder_examples = generate_breeder_examples()
        
        # Check for table headers (now using Date column instead of Week)
        assert "| Date | Listed? | Price | Wishlist Count |" in breeder_examples
        assert "|------|---------|-------|----------------|" in breeder_examples
    
    def test_generated_content_is_string(self):
        """Generated examples should return strings."""
        breeder = generate_breeder_examples()
        dealer = generate_dealer_examples()
        
        assert isinstance(breeder, str)
        assert isinstance(dealer, str)
        assert len(breeder) > 0
        assert len(dealer) > 0


class TestSparklineLegendDocumentation:
    """Test that sparkline columns are properly documented in the legend."""

    def test_breeder_legend_documents_newly_observed_and_ambiguity(self):
        """Legend should explain Newly Observed and ambiguous pre-first-seen absence."""
        from scrape.legend import write_summary_legend
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            summary_file = os.path.join(tmpdir, "summary.md")
            os.environ["GITHUB_STEP_SUMMARY"] = summary_file

            write_summary_legend()

            with open(summary_file, "r", encoding="utf-8") as f:
                legend_content = f.read()

            breeder_start = legend_content.find("### 🧬 Breeder Opportunity Matrix")
            dealer_start = legend_content.find("### 🏪 Dealer Supply Risk Matrix")
            breeder_section = legend_content[breeder_start:dealer_start]

            assert "`Newly Observed`" in breeder_section
            assert "pre-first-seen absence is ambiguous" in breeder_section.lower()
            assert "limited history" in breeder_section.lower()
    
    def test_breeder_legend_documents_price_history(self):
        """Breeder legend should document Price History sparkline column."""
        from scrape.legend import write_summary_legend
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_file = os.path.join(tmpdir, "summary.md")
            os.environ["GITHUB_STEP_SUMMARY"] = summary_file
            
            write_summary_legend()
            
            with open(summary_file, "r", encoding="utf-8") as f:
                legend_content = f.read()
            
            # Check that Price History section exists
            assert "**Price History**" in legend_content
            
            # Check key documentation elements
            assert "Unicode sparkline" in legend_content or "sparkline" in legend_content
            assert "8 weeks" in legend_content or "last 8 weeks" in legend_content
            assert "▁▂▃▄▅▆▇█" in legend_content
            
            # Should be in breeder section (before dealer section)
            breeder_start = legend_content.find("### 🧬 Breeder Opportunity Matrix")
            dealer_start = legend_content.find("### 🏪 Dealer Supply Risk Matrix")
            price_history_pos = legend_content.find("**Price History**")
            
            assert breeder_start < price_history_pos < dealer_start
    
    def test_breeder_legend_documents_wishlist_history(self):
        """Breeder legend should document Wishlist History sparkline column."""
        from scrape.legend import write_summary_legend
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_file = os.path.join(tmpdir, "summary.md")
            os.environ["GITHUB_STEP_SUMMARY"] = summary_file
            
            write_summary_legend()
            
            with open(summary_file, "r", encoding="utf-8") as f:
                legend_content = f.read()
            
            # Check that Wishlist History section exists in breeder section
            breeder_start = legend_content.find("### 🧬 Breeder Opportunity Matrix")
            dealer_start = legend_content.find("### 🏪 Dealer Supply Risk Matrix")
            
            breeder_section = legend_content[breeder_start:dealer_start]
            
            assert "**Wishlist History**" in breeder_section
            assert "sparkline" in breeder_section[breeder_section.find("**Wishlist History**"):]
            assert "8 weeks" in breeder_section or "last 8 weeks" in breeder_section
    
    def test_dealer_legend_documents_price_history(self):
        """Dealer legend should document Price History sparkline column."""
        from scrape.legend import write_summary_legend
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_file = os.path.join(tmpdir, "summary.md")
            os.environ["GITHUB_STEP_SUMMARY"] = summary_file
            
            write_summary_legend()
            
            with open(summary_file, "r", encoding="utf-8") as f:
                legend_content = f.read()
            
            # Check that Price History section exists in dealer section
            dealer_start = legend_content.find("### 🏪 Dealer Supply Risk Matrix")
            
            dealer_section = legend_content[dealer_start:]
            
            assert "**Price History**" in dealer_section
            assert "Unicode sparkline" in dealer_section or "sparkline" in dealer_section
            assert "▁▂▃▄▅▆▇█" in dealer_section
    
    def test_dealer_legend_documents_wishlist_history(self):
        """Dealer legend should document Wishlist History sparkline column."""
        from scrape.legend import write_summary_legend
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_file = os.path.join(tmpdir, "summary.md")
            os.environ["GITHUB_STEP_SUMMARY"] = summary_file
            
            write_summary_legend()
            
            with open(summary_file, "r", encoding="utf-8") as f:
                legend_content = f.read()
            
            # Check that Wishlist History section exists in dealer section
            dealer_start = legend_content.find("### 🏪 Dealer Supply Risk Matrix")
            
            dealer_section = legend_content[dealer_start:]
            
            assert "**Wishlist History**" in dealer_section
            assert "sparkline" in dealer_section[dealer_section.find("**Wishlist History**"):]
    
    def test_dealer_legend_documents_stock_availability(self):
        """Dealer legend should document Stock Availability sparkline column (unique to dealer matrix)."""
        from scrape.legend import write_summary_legend
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_file = os.path.join(tmpdir, "summary.md")
            os.environ["GITHUB_STEP_SUMMARY"] = summary_file
            
            write_summary_legend()
            
            with open(summary_file, "r", encoding="utf-8") as f:
                legend_content = f.read()
            
            # Check that Stock Availability section exists in dealer section
            dealer_start = legend_content.find("### 🏪 Dealer Supply Risk Matrix")
            
            dealer_section = legend_content[dealer_start:]
            
            assert "**Stock Availability**" in dealer_section
            
            # Check key documentation elements
            assert "█" in dealer_section  # IN-stock character
            assert "Binary sparkline" in dealer_section or "sparkline" in dealer_section
            assert "8 weeks" in dealer_section or "last 8 weeks" in dealer_section
            assert "IN" in dealer_section and "OUT" in dealer_section
    
    def test_breeder_legend_does_not_have_stock_availability(self):
        """Breeder legend should NOT have Stock Availability (it's dealer-only)."""
        from scrape.legend import write_summary_legend
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_file = os.path.join(tmpdir, "summary.md")
            os.environ["GITHUB_STEP_SUMMARY"] = summary_file
            
            write_summary_legend()
            
            with open(summary_file, "r", encoding="utf-8") as f:
                legend_content = f.read()
            
            # Extract breeder section only
            breeder_start = legend_content.find("### 🧬 Breeder Opportunity Matrix")
            dealer_start = legend_content.find("### 🏪 Dealer Supply Risk Matrix")
            
            breeder_section = legend_content[breeder_start:dealer_start]
            
            # Stock Availability should NOT be in breeder section
            assert "**Stock Availability**" not in breeder_section
    
    def test_sparkline_documentation_includes_examples(self):
        """Sparkline documentation should include example patterns."""
        from scrape.legend import write_summary_legend
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_file = os.path.join(tmpdir, "summary.md")
            os.environ["GITHUB_STEP_SUMMARY"] = summary_file
            
            write_summary_legend()
            
            with open(summary_file, "r", encoding="utf-8") as f:
                legend_content = f.read()
            
            # Price History should have example
            assert "Example:" in legend_content or "example" in legend_content.lower()
            
            # Stock Availability should have examples for different patterns
            dealer_start = legend_content.find("### 🏪 Dealer Supply Risk Matrix")
            dealer_section = legend_content[dealer_start:]
            
            stock_avail_start = dealer_section.find("**Stock Availability**")
            if stock_avail_start != -1:
                stock_avail_section = dealer_section[stock_avail_start:stock_avail_start+1000]
                assert "Example" in stock_avail_section or "example" in stock_avail_section.lower()

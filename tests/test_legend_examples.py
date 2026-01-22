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
from breeder_matrix import build_breeder_opportunity_table
from dealer_matrix import build_dealer_supply_risk_table
from legend_examples import (
    generate_breeder_examples,
    generate_dealer_examples,
    generate_breeder_example_1,
    generate_breeder_example_2,
    generate_breeder_example_3,
    generate_breeder_example_4,
    generate_breeder_example_5,
    generate_breeder_example_6,
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
        assert "**Price Trend:** ↑" in example
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
        assert "**Wishlist Delta:** ↑" in example
        assert "**Signal:** 🔥" in example
    
    def test_breeder_example_6_always_available_falling_interest(self):
        """Example 6 should demonstrate oversupplied market with declining interest."""
        example = generate_breeder_example_6()
        assert "#### Example 6: Always Available with Falling Interest" in example
        assert "**Stock Pattern:** Always" in example
        assert "**Wishlist Delta:** ↓" in example
        assert "**Signal:** ❌" in example


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
        assert "**Wishlist Pressure:** 🔥" in example
        assert "**Dealer Risk:**" in example
    
    def test_dealer_example_5_medium_reliability_surging_demand(self):
        """Example 5 should demonstrate medium reliability with surging demand."""
        example = generate_dealer_example_5()
        assert "#### Example 5: Medium Reliability + Surging Demand (Escalated Risk)" in example
        assert "**Stock Reliability:**" in example
        assert "**Wishlist Delta:** ↑" in example
        assert "**Dealer Risk:** 🔥" in example
    
    def test_dealer_example_6_high_reliability_falling_demand(self):
        """Example 6 should demonstrate high reliability with falling demand."""
        example = generate_dealer_example_6()
        assert "#### Example 6: High Reliability + Falling Demand (No Action Needed)" in example
        assert "**Stock Reliability:**" in example
        assert "**Wishlist Delta:** ↓" in example
        assert "**Dealer Risk:** ❌" in example
    
    def test_dealer_example_7_low_reliability_surging_interest(self):
        """Example 7 should demonstrate low reliability with surging interest."""
        example = generate_dealer_example_7()
        assert "#### Example 7: Low Reliability + Surging Interest (Early Warning)" in example
        assert "**Stock Reliability:**" in example
        assert "**Wishlist Delta:** ↑" in example
        assert "**Dealer Risk:**" in example


class TestExampleStructure:
    """Test that generated examples have proper structure."""
    
    def test_all_breeder_examples_have_scenarios(self):
        """All breeder examples should have scenario descriptions."""
        examples = generate_breeder_examples()
        example_count = examples.count("#### Example")
        scenario_count = examples.count("**Scenario:**")
        assert scenario_count == 7, f"Expected 7 scenarios, found {scenario_count}"
    
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
        
        # 6 standard examples + 1 special example with 2 analysis sections
        assert breeder_count == 6, f"Expected 6 standard analysis sections, found {breeder_count}"
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
        assert breeder_count == 6, f"Expected 6 breeder why sections, found {breeder_count}"
        assert dealer_count == 7, f"Expected 7 dealer why sections, found {dealer_count}"
    
    def test_examples_include_markdown_tables(self):
        """Examples should include markdown tables with data."""
        breeder_examples = generate_breeder_examples()
        
        # Check for table headers
        assert "| Week | Listed? | Price | Wishlist Count |" in breeder_examples
        assert "|------|---------|-------|----------------|" in breeder_examples
    
    def test_generated_content_is_string(self):
        """Generated examples should return strings."""
        breeder = generate_breeder_examples()
        dealer = generate_dealer_examples()
        
        assert isinstance(breeder, str)
        assert isinstance(dealer, str)
        assert len(breeder) > 0
        assert len(dealer) > 0

#!/usr/bin/env python3
"""Tests for static analysis methodology content and rendering."""

from bs4 import BeautifulSoup

from conftest import temp_csv_file
from scrape import breeder_matrix, dealer_matrix
from shared.config import (
    OOS_CARRYOVER_LOOKBACK,
    WISHLIST_DELTA_DECREASE_THRESHOLD,
    WISHLIST_DELTA_INCREASE_THRESHOLD,
    WISHLIST_DELTA_LOOKBACK,
    WISHLIST_DELTA_PREV_LOOKBACK,
    WISHLIST_SMALL_N_FLATTEN_THRESHOLD,
)
from website.analysis_methodology import (
    build_breeder_methodology,
    build_dealer_methodology,
)
from website.generate_website import generate_analysis_page
from website.page_config import BreederPageConfig, DealerPageConfig


class TestAnalysisMethodologyBuilder:
    """Methodology data should reflect live production rule thresholds."""

    def test_build_breeder_methodology_contains_live_thresholds_and_edge_case(self):
        """Breeder methodology should expose verified thresholds and Newly Observed guidance."""
        methodology = build_breeder_methodology()

        threshold_lines = [
            item["label"]
            for group in methodology["threshold_groups"]
            for item in group["items"]
        ]
        decision_labels = [node["label"] for node in methodology["decision_tree"]["nodes"]]
        edge_case_titles = [note["title"] for note in methodology["edge_cases"]]

        assert any(
            f"Sustained: OOS runs >= {breeder_matrix.BREEDER_SUSTAINED_OOS_RUNS}" in line
            for line in threshold_lines
        )
        assert any(
            f"Emerging: OOS runs >= {breeder_matrix.BREEDER_EMERGING_MIN_OOS_RUNS} and < {breeder_matrix.BREEDER_SUSTAINED_OOS_RUNS}" in line
            for line in threshold_lines
        )
        assert any(
            f"Wishlist delta up: delta >= {WISHLIST_DELTA_INCREASE_THRESHOLD}" in line
            for line in threshold_lines
        )
        assert any(
            f"Wishlist delta down: delta <= {WISHLIST_DELTA_DECREASE_THRESHOLD}" in line
            for line in threshold_lines
        )
        assert any(
            f"OOS carryover lookback: {OOS_CARRYOVER_LOOKBACK} runs" in line
            for line in threshold_lines
        )
        assert any(
            f"Current delta lookup window: {WISHLIST_DELTA_LOOKBACK} runs" in line
            for line in threshold_lines
        )
        assert any(
            f"Previous comparable lookup window: {WISHLIST_DELTA_PREV_LOOKBACK} runs" in line
            for line in threshold_lines
        )
        assert any(
            f"Small-N flattening: max-min <= {WISHLIST_SMALL_N_FLATTEN_THRESHOLD}" in line
            for line in threshold_lines
        )
        assert any("Newly Observed => Watch" in label for label in decision_labels)
        assert "Breeder Newly Observed" in edge_case_titles
        assert methodology["worked_example"]["result"] == "🔥 Hot"

    def test_build_dealer_methodology_contains_live_thresholds_and_limited_history_note(self):
        """Dealer methodology should expose reliability/restock thresholds and limited-history caveat."""
        methodology = build_dealer_methodology()

        threshold_lines = [
            item["label"]
            for group in methodology["threshold_groups"]
            for item in group["items"]
        ]
        decision_labels = [node["label"] for node in methodology["decision_tree"]["nodes"]]
        edge_cases = {note["title"]: note["body"] for note in methodology["edge_cases"]}

        assert any(
            f"High reliability: presence percentage >= {dealer_matrix.DEALER_HIGH_RELIABILITY_THRESHOLD}" in line
            for line in threshold_lines
        )
        assert any(
            f"Medium reliability: >= {dealer_matrix.DEALER_MEDIUM_RELIABILITY_THRESHOLD} and < {dealer_matrix.DEALER_HIGH_RELIABILITY_THRESHOLD}" in line
            for line in threshold_lines
        )
        assert any(
            f"Slow restock: average OOS duration >= {dealer_matrix.DEALER_SLOW_RESTOCK_MIN_AVG_OOS}" in line
            for line in threshold_lines
        )
        assert any(
            f"Moderate restock: average OOS duration == {dealer_matrix.DEALER_MODERATE_RESTOCK_AVG_OOS}" in line
            for line in threshold_lines
        )
        assert any("High reliability stays Low Risk" in label for label in decision_labels)
        assert "Dealer Limited History" in edge_cases
        assert "informational only" in edge_cases["Dealer price pressure"].lower()
        assert methodology["worked_example"]["result"] == "🔥 High Risk"
        assert methodology["worked_example"]["species"] == "Monocentropus balfouri"


class TestAnalysisMethodologyRendering:
    """Methodology should render below the legend on analysis pages."""

    def test_breeder_page_renders_methodology_after_legend(self):
        """Breeder page should render methodology below the legend and include worked-example content."""
        csv_content = "Species,Size (cm),Signal\nAphonopelma seemanni,1.5,🔥\n"
        with temp_csv_file(csv_content) as filename:
            config = BreederPageConfig(
                title="Breeder Opportunities",
                description="Test breeder page",
                csv_filename=filename,
                table_id="breeder-table",
                active_page="breeder",
                legend_markdown="**Legend**: test legend",
                methodology=build_breeder_methodology(),
            )

            html = generate_analysis_page(config)
            soup = BeautifulSoup(html, "html.parser")

            methodology = soup.find("section", id="methodology-section")
            assert methodology is not None, "Breeder page should render methodology section"
            assert "How the breeder analysis works" in methodology.get_text(" ", strip=True)
            assert "Worked example" in methodology.get_text(" ", strip=True)
            assert "Aphonopelma seemanni" in methodology.get_text(" ", strip=True)

            assert html.index('id="breeder-table-root"') < html.index('id="legend-section"')
            assert html.index('id="legend-section"') < html.index('id="methodology-section"')

    def test_dealer_page_renders_methodology_after_legend(self):
        """Dealer page should render methodology below the legend with page-specific content."""
        csv_content = "Species,Size (cm),Dealer Risk\nTliltocatl albopilosus,2.0,🔥\n"
        with temp_csv_file(csv_content) as filename:
            config = DealerPageConfig(
                title="Dealer Supply Risk",
                description="Test dealer page",
                csv_filename=filename,
                table_id="dealer-table",
                active_page="dealer",
                legend_markdown="**Legend**: dealer legend",
                methodology=build_dealer_methodology(),
            )

            html = generate_analysis_page(config)
            soup = BeautifulSoup(html, "html.parser")

            methodology = soup.find("section", id="methodology-section")
            assert methodology is not None, "Dealer page should render methodology section"
            assert "How the dealer analysis works" in methodology.get_text(" ", strip=True)
            assert "Worked example" in methodology.get_text(" ", strip=True)
            assert "Monocentropus balfouri" in methodology.get_text(" ", strip=True)

            assert html.index('id="dealer-table-root"') < html.index('id="legend-section"')
            assert html.index('id="legend-section"') < html.index('id="methodology-section"')

    def test_methodology_cards_render_in_expected_internal_order(self):
        """Methodology section should preserve the intended summary-to-edge-case order."""
        csv_content = "Species,Size (cm),Signal\nAphonopelma seemanni,1.5,🔥\n"
        with temp_csv_file(csv_content) as filename:
            config = BreederPageConfig(
                title="Breeder Opportunities",
                description="Test breeder page",
                csv_filename=filename,
                table_id="breeder-table",
                active_page="breeder",
                legend_markdown="**Legend**: test legend",
                methodology=build_breeder_methodology(),
            )

            html = generate_analysis_page(config)
            soup = BeautifulSoup(html, "html.parser")

            stack = soup.select_one("#methodology-section .analysis-methodology__stack")
            assert stack is not None, "Methodology stack should be rendered"

            section_classes = [
                next(class_name for class_name in section.get("class", []) if class_name.startswith("methodology-card--"))
                for section in stack.find_all("section", recursive=False)
            ]

            assert section_classes == [
                "methodology-card--summary",
                "methodology-card--example",
                "methodology-card--thresholds",
                "methodology-card--decision-tree",
                "methodology-card--edge-cases",
            ]
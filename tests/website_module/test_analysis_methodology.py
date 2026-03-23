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
        thresholds_tab = next(tab for tab in methodology["tabs"] if tab["id"] == "thresholds")
        tree_tab = next(tab for tab in methodology["tabs"] if tab["id"] == "tree")
        example_tab = next(tab for tab in methodology["tabs"] if tab["id"] == "example")

        threshold_lines = [
            item["label"]
            for card in thresholds_tab["cards"]
            for item in card["items"]
        ]
        decision_labels = [branch["label"] for branch in tree_tab["tree"]["branches"]]
        threshold_titles = [card["title"] for card in thresholds_tab["cards"]]

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
        assert "Time Windows" in threshold_titles
        assert any("If Sustained" in label for label in decision_labels)
        assert any("If Emerging" in label for label in decision_labels)
        assert example_tab["example"]["result"] == "🔥 Hot"

        escalation_rules = next(
            card for card in thresholds_tab["cards"] if card["title"] == "Escalation Rules"
        )
        sustained_hot_rule = next(
            item
            for item in escalation_rules["items"]
            if item["label"] == "Sustained + price up or flat => Hot"
        )
        assert "wishlist" not in sustained_hot_rule["detail"].lower()

        sustained_branch = next(
            branch for branch in tree_tab["tree"]["branches"] if branch["label"] == "If Sustained"
        )
        assert "falling price" in sustained_branch["copy"].lower()

        price_step = next(
            step for step in example_tab["example"]["steps"] if step["title"] == "Price trend"
        )
        assert "£8.99" in price_step["detail"]
        assert "£15.00" in price_step["detail"]
        assert "£25.00" in price_step["detail"]
        assert "£17" not in price_step["detail"]

    def test_build_dealer_methodology_contains_live_thresholds_and_limited_history_note(self):
        """Dealer methodology should expose reliability/restock thresholds and limited-history caveat."""
        methodology = build_dealer_methodology()
        thresholds_tab = next(tab for tab in methodology["tabs"] if tab["id"] == "thresholds")
        tree_tab = next(tab for tab in methodology["tabs"] if tab["id"] == "tree")
        example_tab = next(tab for tab in methodology["tabs"] if tab["id"] == "example")

        threshold_lines = [
            item["label"]
            for card in thresholds_tab["cards"]
            for item in card["items"]
        ]
        decision_labels = [branch["label"] for branch in tree_tab["tree"]["branches"]]

        assert any(str(dealer_matrix.DEALER_HIGH_RELIABILITY_THRESHOLD) in line for line in threshold_lines)
        assert any(
            str(dealer_matrix.DEALER_MEDIUM_RELIABILITY_THRESHOLD) in line for line in threshold_lines
        )
        assert any(
            f"Slow restock: average OOS duration >= {dealer_matrix.DEALER_SLOW_RESTOCK_MIN_AVG_OOS}" in line
            for line in threshold_lines
        )
        assert any(
            f"Moderate restock: average OOS duration == {dealer_matrix.DEALER_MODERATE_RESTOCK_AVG_OOS}" in line
            for line in threshold_lines
        )
        assert any("If High" in label for label in decision_labels)
        assert any("Dealer Limited History" in line for line in threshold_lines)
        assert any("Dealer price pressure" in line for line in threshold_lines)
        assert example_tab["example"]["result"] == "🔥 High Risk"
        assert example_tab["example"]["species"] == "Aphonopelma seemanni"

        dealer_price_step = next(
            step for step in example_tab["example"]["steps"] if step["title"] == "Restock speed"
        )
        assert "3.1" not in dealer_price_step["detail"]
        assert "seeded" not in dealer_price_step["detail"].lower()

        dealer_output_step = next(
            step for step in example_tab["example"]["steps"] if step["title"] == "Output row"
        )
        assert "seeded" not in dealer_output_step["detail"].lower()

        breeder_methodology = build_breeder_methodology()
        breeder_example_tab = next(tab for tab in breeder_methodology["tabs"] if tab["id"] == "example")
        breeder_price_step = next(
            step for step in breeder_example_tab["example"]["steps"] if step["title"] == "Price trend"
        )
        assert "seeded" not in breeder_price_step["detail"].lower()


class TestAnalysisMethodologyRendering:
    """Methodology should render as a primary explanatory panel on analysis pages."""

    def test_methodology_renders_as_closed_details_panel_by_default(self):
        """Methodology should be expandable and collapsed by default."""
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

            methodology = soup.find("details", id="methodology-section")
            assert methodology is not None, "Methodology should render as a details element"
            assert methodology.get("open") is None, "Methodology should be collapsed by default"

            summary = methodology.find("summary")
            assert summary is not None, "Methodology should expose a summary trigger"
            assert "How the breeder analysis works" in summary.get_text(" ", strip=True)
            assert "Threshold inventory, compact decision logic" not in summary.get_text(" ", strip=True)
            title = summary.find("strong")
            assert title is not None, "Methodology summary should use the shared strong-label pattern"

            content = methodology.find(class_="analysis-methodology__content")
            assert content is not None, "Methodology should render expandable body content"
            assert "Threshold inventory, compact decision logic" in content.get_text(" ", strip=True)

    def test_breeder_page_renders_methodology_above_legend_and_table(self):
        """Breeder page should render methodology before the legend and the full table."""
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

            methodology = soup.find("details", id="methodology-section")
            assert methodology is not None, "Breeder page should render methodology section"
            assert "How the breeder analysis works" in methodology.get_text(" ", strip=True)
            assert "Threshold Inventory" in methodology.get_text(" ", strip=True)
            assert "Decision Tree" in methodology.get_text(" ", strip=True)
            assert "Worked Example" in methodology.get_text(" ", strip=True)
            assert "Aphonopelma seemanni" in methodology.get_text(" ", strip=True)

            assert html.index('id="methodology-section"') < html.index('id="legend-section"')
            assert html.index('id="legend-section"') < html.index('id="breeder-table-root"')

    def test_dealer_page_renders_methodology_above_legend_and_table(self):
        """Dealer page should render methodology before the legend and the full table."""
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

            methodology = soup.find("details", id="methodology-section")
            assert methodology is not None, "Dealer page should render methodology section"
            assert "How the dealer analysis works" in methodology.get_text(" ", strip=True)
            assert "Threshold Inventory" in methodology.get_text(" ", strip=True)
            assert "Decision Tree" in methodology.get_text(" ", strip=True)
            assert "Worked Example" in methodology.get_text(" ", strip=True)
            assert "Aphonopelma seemanni" in methodology.get_text(" ", strip=True)

            assert html.index('id="methodology-section"') < html.index('id="legend-section"')
            assert html.index('id="legend-section"') < html.index('id="dealer-table-root"')

    def test_methodology_renders_tab_shell_with_one_active_panel(self):
        """Methodology should render tab buttons and a default active panel shell."""
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

            tab_buttons = soup.select("#methodology-section [data-methodology-tab]")
            tab_panels = soup.select("#methodology-section [data-methodology-panel]")

            assert [button.get_text(" ", strip=True) for button in tab_buttons] == [
                "Threshold Inventory",
                "Decision Tree",
                "Worked Example",
            ]
            assert len(tab_panels) == 3
            assert sum("is-active" in panel.get("class", []) for panel in tab_panels) == 1
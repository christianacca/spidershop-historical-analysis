#!/usr/bin/env python3
"""Tests for realistic local demo data used by website generation."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from website.local_demo_data import ensure_local_csv_files, write_realistic_demo_data
from website.markdown_utils import extract_analysis_sections
from website.species_detail import get_observation_metadata


def _read_rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_write_realistic_demo_data_writes_feature_complete_dataset(tmp_path: Path) -> None:
    """Demo data should exercise analysis, history, species, and top-10 states."""
    write_realistic_demo_data(tmp_path)

    required_files = [
        tmp_path / "spidershop_spiderlings_scrape.csv",
        tmp_path / "spidershop_spiderlings_history.csv",
        tmp_path / "breeder_opportunity_table.csv",
        tmp_path / "dealer_supply_risk_table.csv",
        tmp_path / "analysis_summary.md",
    ]

    for path in required_files:
        assert path.exists(), f"Expected {path.name} to be written"

    breeder_rows = _read_rows(tmp_path / "breeder_opportunity_table.csv")
    dealer_rows = _read_rows(tmp_path / "dealer_supply_risk_table.csv")
    history_rows = _read_rows(tmp_path / "spidershop_spiderlings_history.csv")

    assert len(breeder_rows) >= 15, "Expected enough breeder rows to exercise top-10 filtering"
    assert sum(row["Signal"] == "🔥" for row in breeder_rows) >= 11
    assert {row["Signal"] for row in breeder_rows} >= {"🔥", "⚠️", "❌"}
    assert {row["Stock Pattern"] for row in breeder_rows} >= {
        "Sustained",
        "Emerging",
        "Cyclical",
        "Always",
        "Newly Observed",
    }

    assert len(dealer_rows) >= 10
    assert {row["Dealer Risk"] for row in dealer_rows} >= {"🔥", "⚠️", "❌"}

    assert len({row["scrape_datetime"] for row in history_rows}) >= 5
    assert len({row["scientific_name"] for row in history_rows}) >= 10

    summary_text = (tmp_path / "analysis_summary.md").read_text(encoding="utf-8")
    assert "Breeder Opportunity Matrix" in summary_text
    assert "Dealer Supply Risk Matrix" in summary_text


def test_write_realistic_demo_data_covers_comprehensive_ui_states(tmp_path: Path) -> None:
    """Demo data should intentionally cover the visible website state surface."""
    write_realistic_demo_data(tmp_path)

    breeder_rows = _read_rows(tmp_path / "breeder_opportunity_table.csv")
    dealer_rows = _read_rows(tmp_path / "dealer_supply_risk_table.csv")
    history_rows = _read_rows(tmp_path / "spidershop_spiderlings_history.csv")
    history_csv = tmp_path / "spidershop_spiderlings_history.csv"

    assert len({row["scrape_datetime"] for row in history_rows}) >= 60

    assert all(row["Recommendation"].strip() for row in breeder_rows)
    assert all(row["Dealer Recommendation"].strip() for row in dealer_rows)

    assert all(row["Price History"].strip() for row in breeder_rows)
    assert all(row["Wishlist History"].strip() for row in breeder_rows)
    assert all(row["Price History"].strip() for row in dealer_rows)
    assert all(row["Wishlist History"].strip() for row in dealer_rows)
    assert all(row["Stock Availability"].strip() for row in dealer_rows)

    assert any(row["Drivers"].strip() for row in breeder_rows)
    assert any(not row["Drivers"].strip() for row in breeder_rows)
    assert any(row["Drivers"].strip() for row in dealer_rows)
    assert any(not row["Drivers"].strip() for row in dealer_rows)

    assert {row["OOS"] for row in breeder_rows} >= {"IN", "OUT"}

    breeder_price_arrows = {row["Price"].split()[-1] for row in breeder_rows}
    dealer_price_arrows = {row["Price"].split()[-1] for row in dealer_rows}
    assert breeder_price_arrows | dealer_price_arrows >= {"↑", "→", "↓"}

    breeder_wishlist_tokens = [row["Wishlist"].split() for row in breeder_rows]
    dealer_wishlist_tokens = [row["Wishlist"].split() for row in dealer_rows]
    pressure_icons = {tokens[1] for tokens in breeder_wishlist_tokens + dealer_wishlist_tokens}
    delta_arrows = {tokens[2] for tokens in breeder_wishlist_tokens + dealer_wishlist_tokens}
    assert pressure_icons >= {"🔥", "⚠️", "❌"}
    assert delta_arrows >= {"↑", "→", "↓"}

    observation_metadata = []
    for row in breeder_rows:
        metadata = get_observation_metadata(row["Species"], row["Size (cm)"], str(history_csv))
        assert metadata is not None, f"Expected history for {row['Species']}"
        observation_metadata.append(metadata)

    assert any(
        metadata["first_observed_status"] == "new"
        and metadata["coverage_status"] == "low"
        and metadata["latest_observed_status"] == "current"
        for metadata in observation_metadata
    )
    assert any(metadata["latest_observed_status"] == "stale" for metadata in observation_metadata)
    assert any(
        metadata["coverage_status"] == "low"
        and metadata["first_observed_status"] == "current"
        for metadata in observation_metadata
    )
    assert any(
        metadata["first_observed_status"] == "current"
        and metadata["latest_observed_status"] == "current"
        and metadata["coverage_status"] == "current"
        for metadata in observation_metadata
    )


def test_write_realistic_demo_data_includes_full_production_legend_and_examples(tmp_path: Path) -> None:
    """Demo analysis summary should reuse the full legend content and worked examples used in production."""
    write_realistic_demo_data(tmp_path)

    _, _, breeder_legend, dealer_legend, breeder_examples, dealer_examples = extract_analysis_sections(
        str(tmp_path / "analysis_summary.md")
    )

    assert breeder_legend is not None
    assert "**OOS** (Current Availability)" in breeder_legend
    assert "**Recommendation** (Final Assessment)" in breeder_legend

    assert dealer_legend is not None
    assert "**Stock Reliability** (Historical Supply Pattern)" in dealer_legend
    assert "**Dealer Recommendation** (Final Assessment)" in dealer_legend

    assert breeder_examples is not None
    assert "Sustained Scarcity" in breeder_examples
    assert "Emerging Scarcity with Rising Price" in breeder_examples

    assert dealer_examples is not None
    assert "High Reliability (No Urgency)" in dealer_examples
    assert "Low Reliability + High Demand (Critical Risk)" in dealer_examples
    assert "Low Reliability + Stable Demand (Supply Warning)" in dealer_examples


def test_ensure_local_csv_files_seeds_demo_data_when_requested(tmp_path: Path) -> None:
    """Missing local CSVs should be created when demo seeding is enabled."""
    ensure_local_csv_files(tmp_path, seed_demo_data=True)

    assert (tmp_path / "spidershop_spiderlings_scrape.csv").exists()
    assert (tmp_path / "spidershop_spiderlings_history.csv").exists()
    assert (tmp_path / "breeder_opportunity_table.csv").exists()
    assert (tmp_path / "dealer_supply_risk_table.csv").exists()


def test_ensure_local_csv_files_raises_when_missing_and_demo_seed_disabled(tmp_path: Path) -> None:
    """Existing strict behavior should remain available when demo seeding is disabled."""
    with pytest.raises(FileNotFoundError, match="Missing required CSV files"):
        ensure_local_csv_files(tmp_path, seed_demo_data=False)


def test_ensure_local_csv_files_refreshes_legacy_seeded_demo_data(tmp_path: Path) -> None:
    """Seed mode should refresh older seeded demo data instead of leaving stale local fixtures in place."""
    (tmp_path / "spidershop_spiderlings_scrape.csv").write_text(
        "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        "2025-01-01 09:00:00,Legacy Spider,Legacy,1.0,10.00,1,https://example.com/legacy\n",
        encoding="utf-8",
    )
    (tmp_path / "spidershop_spiderlings_history.csv").write_text(
        "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        "2025-01-01 09:00:00,Legacy Spider,Legacy,1.0,10.00,1,https://example.com/legacy\n",
        encoding="utf-8",
    )
    (tmp_path / "breeder_opportunity_table.csv").write_text(
        "Species,Size (cm),OOS,OOS Runs,Stock Pattern,Price,Price History,Wishlist,Wishlist History,Signal,Recommendation,Drivers\n"
        "Legacy Spider,1.0,IN,0,Always,£10.00 →,▁,1 ❌ →,▁,❌,Legacy recommendation,\n",
        encoding="utf-8",
    )
    (tmp_path / "dealer_supply_risk_table.csv").write_text(
        "Species,Size (cm),Stock Reliability,Avg OOS Duration,Restock Speed,Price,Price History,Wishlist,Wishlist History,Stock Availability,Dealer Risk,Dealer Recommendation,Drivers\n"
        "Legacy Spider,1.0,High,0.0,Fast,£10.00 →,▁,1 ❌ →,▁,██,❌,Legacy dealer recommendation,\n",
        encoding="utf-8",
    )
    (tmp_path / "analysis_summary.md").write_text(
        "## 🧬 Breeder Opportunity Matrix (Top 10)\n\n"
        "Rich local demo data covering sustained, emerging, cyclical, always, and newly observed states.\n",
        encoding="utf-8",
    )

    ensure_local_csv_files(tmp_path, seed_demo_data=True)

    history_rows = _read_rows(tmp_path / "spidershop_spiderlings_history.csv")
    assert len({row["scrape_datetime"] for row in history_rows}) >= 60
    assert any(row["scientific_name"] != "Legacy Spider" for row in history_rows)


def test_ensure_local_csv_files_refreshes_placeholder_stub_summary(tmp_path: Path) -> None:
    """Seed mode should replace old placeholder local summaries with the real demo dataset."""
    (tmp_path / "spidershop_spiderlings_scrape.csv").write_text(
        "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        "2025-01-01 09:00:00,Stub Spider,Stub,1.0,10.00,1,https://example.com/stub\n",
        encoding="utf-8",
    )
    (tmp_path / "spidershop_spiderlings_history.csv").write_text(
        "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        "2025-01-01 09:00:00,Stub Spider,Stub,1.0,10.00,1,https://example.com/stub\n",
        encoding="utf-8",
    )
    (tmp_path / "breeder_opportunity_table.csv").write_text(
        "Species,Size (cm),OOS,OOS Runs,Stock Pattern,Price,Price History,Wishlist,Wishlist History,Signal,Recommendation,Drivers\n"
        "Stub Spider,1.0,IN,0,Always,£10.00 →,▁,1 ❌ →,▁,❌,Stub recommendation,\n",
        encoding="utf-8",
    )
    (tmp_path / "dealer_supply_risk_table.csv").write_text(
        "Species,Size (cm),Stock Reliability,Avg OOS Duration,Restock Speed,Price,Price History,Wishlist,Wishlist History,Stock Availability,Dealer Risk,Dealer Recommendation,Drivers\n"
        "Stub Spider,1.0,High,0.0,Fast,£10.00 →,▁,1 ❌ →,▁,██,❌,Stub dealer recommendation,\n",
        encoding="utf-8",
    )
    (tmp_path / "analysis_summary.md").write_text(
        "## 🧬 Breeder Opportunity Matrix (Top 10)\n\n"
        "**Summary:** 5 species analyzed | 🔥 Hot: 2 | ⚠️ Watch: 2 | ❌ Avoid: 1\n\n"
        "## 🏪 Dealer Supply Risk Matrix (Top 10)\n\n"
        "**Summary:** 5 species analyzed | 🔥 High Risk: 2 | ⚠️ Moderate Risk: 2 | ❌ Low Risk: 1\n\n"
        "<details markdown=\"1\">\n"
        "<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>\n\n"
        "### 🧬 Breeder Opportunity Matrix — Legend\n\n"
        "**Signal**\n\n"
        "- `🔥` — Strong breeding opportunity signal\n\n"
        "### 📖 Breeder Matrix — Practical Examples\n\n"
        "Example breeder scenario.\n\n"
        "### 🏪 Dealer Supply Risk Matrix — Legend\n\n"
        "**Risk**\n\n"
        "- `🔥` — High supply risk\n\n"
        "### 📖 Dealer Matrix — Practical Examples\n\n"
        "Example dealer scenario.\n\n"
        "</details>\n",
        encoding="utf-8",
    )

    ensure_local_csv_files(tmp_path, seed_demo_data=True)

    summary_text = (tmp_path / "analysis_summary.md").read_text(encoding="utf-8")
    assert "Example dealer scenario." not in summary_text
    assert "High Reliability (No Urgency)" in summary_text

    history_rows = _read_rows(tmp_path / "spidershop_spiderlings_history.csv")
    assert len({row["scrape_datetime"] for row in history_rows}) >= 60
    assert any(row["scientific_name"] != "Stub Spider" for row in history_rows)


def test_generated_demo_site_renders_signal_tooltip_for_pulchra(tmp_path: Path) -> None:
    """Seeded generated breeder HTML should keep pulchra's tooltip-driving payload intact."""
    from website.generate_website import main as generate_website_main

    write_realistic_demo_data(tmp_path)

    original_dir = Path.cwd()
    try:
        os.chdir(tmp_path)
        generate_website_main()
    finally:
        os.chdir(original_dir)

    breeder_html = (tmp_path / "website" / "breeder.html").read_text(encoding="utf-8")
    match = re.search(
        r"window\['breeder-tableData'\]\s*=\s*(\[.*?\]);</script>",
        breeder_html,
        re.DOTALL,
    )
    assert match is not None, "Expected breeder.html to include the embedded Svelte table payload"

    table_rows = json.loads(match.group(1))
    pulchra_row = next(
        (row for row in table_rows if row.get("Species") == "Grammostola pulchra"),
        None,
    )
    assert pulchra_row is not None, "Expected Grammostola pulchra in the generated breeder table payload"

    assert pulchra_row.get("Drivers"), "Expected pulchra payload row to include Drivers text for the client-side signal tooltip"
    assert "falling price" in pulchra_row["Drivers"].lower()


def test_generated_demo_site_renders_practical_examples_on_analysis_pages(tmp_path: Path) -> None:
    """Seeded local website output should include practical examples on both analysis pages."""
    from website.generate_website import main as generate_website_main

    write_realistic_demo_data(tmp_path)

    original_dir = Path.cwd()
    try:
        os.chdir(tmp_path)
        generate_website_main()
    finally:
        os.chdir(original_dir)

    breeder_html = (tmp_path / "website" / "breeder.html").read_text(encoding="utf-8")
    dealer_html = (tmp_path / "website" / "dealer.html").read_text(encoding="utf-8")

    assert "Practical Examples" in breeder_html
    assert "Sustained Scarcity" in breeder_html

    assert "Practical Examples" in dealer_html
    assert "High Reliability (No Urgency)" in dealer_html
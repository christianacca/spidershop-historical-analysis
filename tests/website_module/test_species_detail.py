"""
Tests for species detail page generation.

Following TDD approach: tests written first to define expected behavior.
"""

import os
import pytest
from pathlib import Path
from conftest import (
    HistoryEntry,
    BreederEntry,
    DealerEntry,
    create_temp_csv_file,
    temp_csv_file,
    create_breeder_csv_content,
    create_dealer_csv_content,
    create_history_csv_content
)


class TestGetSpeciesList:
    """Test extraction of unique species names from breeder/dealer CSVs."""

    def test_extracts_species_from_breeder_csv_only(self):
        """Should extract species list when only breeder CSV is provided."""
        from website.species_detail import get_species_list

        breeder_csv = create_temp_csv_file(
            "Species,Size (cm),Signal\n"
            "Aphonopelma seemanni,1.5,\U0001f525\n"
            "Brachypelma hamorii,2.0,\u26a0\ufe0f\n"
        )
        
        try:
            species_list = get_species_list(breeder_csv_path=breeder_csv)
            
            assert len(species_list) == 2
            assert "Aphonopelma seemanni" in species_list
            assert "Brachypelma hamorii" in species_list
        finally:
            Path(breeder_csv).unlink()

    def test_extracts_species_from_dealer_csv_only(self):
        """Should extract species list when only dealer CSV is provided."""
        from website.species_detail import get_species_list

        dealer_csv = create_temp_csv_file(
            "Species,Size (cm),Dealer Risk\n"
            "Tliltocatl albopilosus,1.0,\U0001f525\n"
        )
        
        try:
            species_list = get_species_list(dealer_csv_path=dealer_csv)
            
            assert len(species_list) == 1
            assert "Tliltocatl albopilosus" in species_list
        finally:
            Path(dealer_csv).unlink()

    def test_merges_species_from_both_csvs_without_duplicates(self):
        """Should merge species from both CSVs and remove duplicates."""
        from website.species_detail import get_species_list

        breeder_csv = create_temp_csv_file(
            "Species,Size (cm),Signal\n"
            "Aphonopelma seemanni,1.5,\U0001f525\n"
            "Brachypelma hamorii,2.0,\u26a0\ufe0f\n"
        )
        dealer_csv = create_temp_csv_file(
            "Species,Size (cm),Dealer Risk\n"
            "Aphonopelma seemanni,1.5,\U0001f525\n"  # Duplicate
            "Tliltocatl albopilosus,1.0,\u26a0\ufe0f\n"
        )
        
        try:
            species_list = get_species_list(breeder_csv_path=breeder_csv, dealer_csv_path=dealer_csv)
            
            assert len(species_list) == 3  # No duplicate
            assert "Aphonopelma seemanni" in species_list
            assert "Brachypelma hamorii" in species_list
            assert "Tliltocatl albopilosus" in species_list
        finally:
            Path(breeder_csv).unlink()
            Path(dealer_csv).unlink()
    
    def test_returns_empty_when_missing_species_column(self):
        """Should return empty list when CSV doesn't have Species column."""
        from website.species_detail import get_species_list
        
        # CSVs without Species column
        breeder_content = "Signal\n\U0001f525\n"
        dealer_content = "Dealer Risk\n\u26a0\ufe0f\n"
        
        with temp_csv_file(breeder_content) as breeder_path:
            with temp_csv_file(dealer_content) as dealer_path:
                assert get_species_list(breeder_csv_path=breeder_path) == []
                assert get_species_list(dealer_csv_path=dealer_path) == []


class TestSlugifySpecies:
    """Test scientific name to URL slug conversion."""

    def test_converts_to_lowercase_with_hyphens(self):
        """Should convert spaces to hyphens and lowercase the name."""
        from website.species_detail import slugify_species

        assert slugify_species("Aphonopelma seemanni") == "aphonopelma-seemanni"
        assert slugify_species("Brachypelma hamorii") == "brachypelma-hamorii"

    def test_handles_multiple_spaces(self):
        """Should handle multiple consecutive spaces."""
        from website.species_detail import slugify_species

        assert slugify_species("Grammostola  pulchra") == "grammostola-pulchra"

    def test_handles_already_lowercase(self):
        """Should work with already lowercase names."""
        from website.species_detail import slugify_species

        assert slugify_species("poecilotheria metallica") == "poecilotheria-metallica"

    def test_strips_single_quotes(self):
        """Single quotes in sp. names must be removed."""
        from website.species_detail import slugify_species

        assert slugify_species("Antikuna sp. 'Herradura'") == "antikuna-sp.-herradura"

    def test_strips_double_quotes(self):
        """Double quotes in variety names must be removed."""
        from website.species_detail import slugify_species

        assert slugify_species('Chilobrachys sp. "South Thai"') == "chilobrachys-sp.-south-thai"

    def test_strips_forward_slash(self):
        """Forward slash must be removed — it would be treated as a path separator."""
        from website.species_detail import slugify_species

        assert slugify_species('Cyriopagopoeus sp. "Big/Black"') == "cyriopagopoeus-sp.-bigblack"


class TestGetSpeciesData:
    """Test data extraction for a specific species from all CSVs."""

    def test_extracts_breeder_metrics_for_species_and_size(self):
        """Should extract breeder-specific metrics matching species and size."""
        from website.species_detail import get_species_data

        breeder_csv = create_temp_csv_file(
            "Species,Size (cm),OOS Runs,Stock Pattern,Signal,Recommendation\n"
            "Aphonopelma seemanni,1.5,8,Sustained,🔥,Strong opportunity\n"
            "Brachypelma hamorii,2.0,3,Cyclical,⚠️,Monitor\n"
        )
        dealer_csv = create_temp_csv_file("Species,Size (cm),Dealer Risk\nOther,1.0,❌\n")
        history_csv = create_temp_csv_file("scrape_datetime,scientific_name,size_cm\n")
        
        try:
            data = get_species_data(
                "Aphonopelma seemanni",
                breeder_csv, dealer_csv, history_csv
            )
            
            assert data["breeder"]["signal"] == "🔥"
            assert data["breeder"]["oos_runs"] == "8"
            assert data["breeder"]["stock_pattern"] == "Sustained"
        finally:
            Path(breeder_csv).unlink()
            Path(dealer_csv).unlink()
            Path(history_csv).unlink()

    def test_extracts_dealer_metrics_for_species_and_size(self):
        """Should extract dealer-specific metrics matching species and size."""
        from website.species_detail import get_species_data

        breeder_csv = create_temp_csv_file("Species,Size (cm),Signal\nOther,1.0,❌\n")
        dealer_csv = create_temp_csv_file(
            "Species,Size (cm),Stock Reliability,Restock Speed,Dealer Risk\n"
            "Aphonopelma seemanni,1.5,45%,Slow,🔥\n"
        )
        history_csv = create_temp_csv_file("scrape_datetime,scientific_name,size_cm\n")
        
        try:
            data = get_species_data(
                "Aphonopelma seemanni",
                breeder_csv, dealer_csv, history_csv
            )
            
            assert data["dealer"]["risk"] == "🔥"
            assert data["dealer"]["stock_reliability"] == "45%"
            assert data["dealer"]["restock_speed"] == "Slow"
        finally:
            Path(breeder_csv).unlink()
            Path(dealer_csv).unlink()
            Path(history_csv).unlink()

    def test_returns_none_for_missing_breeder_metrics(self):
        """Should return None for breeder metrics when species not in breeder CSV."""
        from website.species_detail import get_species_data

        breeder_csv = create_temp_csv_file("Species,Size (cm),Signal\nOther,1.0,❌\n")
        dealer_csv = create_temp_csv_file(
            "Species,Size (cm),Dealer Risk\nAphonopelma seemanni,1.5,🔥\n"
        )
        history_csv = create_temp_csv_file("scrape_datetime,scientific_name,size_cm\n")
        
        try:
            data = get_species_data(
                "Aphonopelma seemanni",
                breeder_csv, dealer_csv, history_csv
            )
            
            assert data["breeder"] is None
            assert data["dealer"]["risk"] == "🔥"
        finally:
            Path(breeder_csv).unlink()
            Path(dealer_csv).unlink()
            Path(history_csv).unlink()


class TestBuildChartData:
    """Test chart data extraction from history CSV with 26-run window."""

    def test_extracts_observations_within_26_run_window(self):
        """Should extract observed data points within the last 26 runs."""
        from website.species_detail import build_chart_data

        # Create history with 30 runs total
        # Our target species is observed in 15 of them (every other run)
        # Need to have SOME species in every run so we get 30 distinct run dates
        history_entries = []
        for i in range(30):
            run_date = f"2025-01-{str(i+1).zfill(2)} 06:00:00"
            if i % 2 == 0:  # Our target species observed every other run
                history_entries.append(HistoryEntry(
                    scrape_datetime=run_date,
                    scientific_name="Aphonopelma seemanni",
                    size_cm="1.5",
                    price_gbp=f"{10.0 + i}",
                    wishlist_count=str(i * 2),
                ))
            else:  # Other species observed on alternate runs (to create complete run timeline)
                history_entries.append(HistoryEntry(
                    scrape_datetime=run_date,
                    scientific_name="Other Species",
                    size_cm="2.0",
                    price_gbp="20.0",
                    wishlist_count="10",
                ))
        
        history_csv = create_temp_csv_file(create_history_csv_content(history_entries))
        
        try:
            chart_data = build_chart_data("Aphonopelma seemanni", history_csv)
            
            # Should have 26 runs (last 26 of 30 total)
            assert len(chart_data["runs"]) == 26
            
            # First run should be run 5 (index 4), not run 1
            assert chart_data["runs"][0]["date"].startswith("2025-01-05")
            
            # Last run should be run 30
            assert chart_data["runs"][25]["date"].startswith("2025-01-30")
            assert chart_data["runs"][25]["date"].startswith("2025-01-30")
        finally:
            Path(history_csv).unlink()

    def test_marks_gaps_for_missing_observations(self):
        """Should mark runs as gaps when species was not observed."""
        from website.species_detail import build_chart_data

        history_entries = [
            HistoryEntry(
                scrape_datetime="2025-01-01 06:00:00",
                scientific_name="Aphonopelma seemanni",
                size_cm="1.5",
                price_gbp="10.0",
                wishlist_count="5"
            ),
            # Run 2: species OUT, but OTHER species present (to create the run)
            HistoryEntry(
                scrape_datetime="2025-01-02 06:00:00",
                scientific_name="Other Species",
                size_cm="2.0",
                price_gbp="20.0",
                wishlist_count="10"
            ),
            HistoryEntry(
                scrape_datetime="2025-01-03 06:00:00",
                scientific_name="Aphonopelma seemanni",
                size_cm="1.5",
                price_gbp="12.0",
                wishlist_count="8"
            ),
        ]
        
        history_csv = create_temp_csv_file(create_history_csv_content(history_entries))
        
        try:
            chart_data = build_chart_data("Aphonopelma seemanni", history_csv)
            
            # Run 1: observed
            assert chart_data["runs"][0]["observed"] is True
            assert chart_data["runs"][0]["price"] == "10.0"
            assert chart_data["runs"][0]["size"] == "1.5"
            
            # Run 2: gap (species OUT but run exists)
            assert chart_data["runs"][1]["observed"] is False
            assert chart_data["runs"][1]["price"] is None
            assert chart_data["runs"][1]["wishlist"] is None
            assert chart_data["runs"][1]["size"] is None
            
            # Run 3: observed
            assert chart_data["runs"][2]["observed"] is True
            assert chart_data["runs"][2]["price"] == "12.0"
            assert chart_data["runs"][2]["size"] == "1.5"
        finally:
            Path(history_csv).unlink()

    def test_handles_species_with_no_observations(self):
        """Should return empty chart data when species has no observations."""
        from website.species_detail import build_chart_data

        history_csv = create_temp_csv_file(
            "scrape_datetime,scientific_name,size_cm,price_gbp,wishlist_count\n"
            "2025-01-01 06:00:00,Other Species,1.0,10.0,5\n"
        )
        
        try:
            chart_data = build_chart_data("Aphonopelma seemanni", history_csv)
            
            assert chart_data["runs"] == []
        finally:
            Path(history_csv).unlink()
    
    def test_handles_empty_history_csv(self):
        """Should return empty runs when history CSV has no rows."""
        from website.species_detail import build_chart_data
        
        # Create CSV with headers only, no data
        content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        history_csv = create_temp_csv_file(content)
        
        try:
            chart_data = build_chart_data("Aphonopelma seemanni", history_csv)
            
            assert chart_data["runs"] == []
        finally:
            Path(history_csv).unlink()

    def test_handles_empty_size_cm_without_raising(self):
        """Should not raise ValueError when size_cm is an empty string in history CSV."""
        from website.species_detail import build_chart_data

        # Reproduces the production failure: size_cm field is blank in the CSV
        content = (
            "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
            "2025-01-01 06:00:00,Aphonopelma seemanni,Costa Rican Zebra,,10.00,5,http://example.com\n"
        )
        history_csv = create_temp_csv_file(content)

        try:
            # Must not raise ValueError: could not convert string to float: ''
            chart_data = build_chart_data("Aphonopelma seemanni", history_csv)

            assert len(chart_data["runs"]) == 1
            run = chart_data["runs"][0]
            assert run["observed"] is True
            # Empty size_cm values should be excluded from the size string
            assert run["size"] == ""
        finally:
            Path(history_csv).unlink()


class TestGetDefaultSize:
    """Test default size selection from most recent observation."""

    def test_returns_most_recently_observed_size(self):
        """Should return the size from the most recent observation."""
        from website.species_detail import get_default_size

        history_entries = [
            HistoryEntry(
                scrape_datetime="2025-01-01 06:00:00",
                scientific_name="Aphonopelma seemanni",
                size_cm="1.0",
                price_gbp="10.0",
                wishlist_count="5"
            ),
            HistoryEntry(
                scrape_datetime="2025-01-15 06:00:00",
                scientific_name="Aphonopelma seemanni",
                size_cm="1.5",
                price_gbp="12.0",
                wishlist_count="8"
            ),
            HistoryEntry(
                scrape_datetime="2025-01-20 06:00:00",
                scientific_name="Aphonopelma seemanni",
                size_cm="2.0",
                price_gbp="15.0",
                wishlist_count="10"
            ),
        ]
        
        history_csv = create_temp_csv_file(create_history_csv_content(history_entries))
        
        try:
            default_size = get_default_size("Aphonopelma seemanni", history_csv)
            
            assert default_size == "2.0"
        finally:
            Path(history_csv).unlink()

    def test_returns_none_when_species_has_no_observations(self):
        """Should return None when species has never been observed."""
        from website.species_detail import get_default_size

        history_csv = create_temp_csv_file(
            "scrape_datetime,scientific_name,size_cm,price_gbp,wishlist_count\n"
            "2025-01-01 06:00:00,Other Species,1.0,10.0,5\n"
        )
        
        try:
            default_size = get_default_size("Aphonopelma seemanni", history_csv)
            
            assert default_size is None
        finally:
            Path(history_csv).unlink()
    
    def test_returns_none_when_history_empty(self):
        """Should return None when history has no rows."""
        from website.species_detail import get_default_size
        
        content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        
        with temp_csv_file(content) as csv_path:
            result = get_default_size("Aphonopelma seemanni", csv_path)
            assert result is None


class TestGetObservationMetadata:
    """Test extraction of full-history observation metadata for species pages."""

    def test_uses_full_dataset_run_count_and_reports_first_and_latest_observed(self):
        """Observation metadata should use the full run timeline, not only observed rows."""
        from website.species_detail import get_observation_metadata

        history_entries = [
            HistoryEntry(
                scrape_datetime="2025-01-01 06:00:00",
                scientific_name="Other Species",
                size_cm="2.0",
            ),
            HistoryEntry(
                scrape_datetime="2025-01-08 06:00:00",
                scientific_name="Other Species",
                size_cm="2.0",
            ),
            HistoryEntry(
                scrape_datetime="2025-01-15 06:00:00",
                scientific_name="Aphonopelma seemanni",
                size_cm="1.5",
            ),
            HistoryEntry(
                scrape_datetime="2025-01-22 06:00:00",
                scientific_name="Other Species",
                size_cm="2.0",
            ),
            HistoryEntry(
                scrape_datetime="2025-01-29 06:00:00",
                scientific_name="Aphonopelma seemanni",
                size_cm="1.5",
            ),
        ]

        history_csv = create_temp_csv_file(create_history_csv_content(history_entries))

        try:
            metadata = get_observation_metadata("Aphonopelma seemanni", history_csv)

            assert metadata["first_observed"] == "2025-01-15"
            assert metadata["latest_observed"] == "2025-01-29"
            assert metadata["observed_run_count"] == 2
            assert metadata["total_run_count"] == 5
            assert metadata["observed_runs_display"] == "2/5 runs"
            assert metadata["has_ambiguous_pre_first_seen_runs"] is False
        finally:
            Path(history_csv).unlink()

    def test_flags_new_first_observed_and_low_coverage(self):
        """Latest-2-run species should be flagged as newly added with low coverage."""
        from website.species_detail import get_observation_metadata

        history_entries = [
            HistoryEntry(scrape_datetime="2025-01-01 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-01-08 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-01-15 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-01-22 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-01-29 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-02-05 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-02-12 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-02-19 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-02-26 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-03-05 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-03-12 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-03-19 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-03-26 06:00:00", scientific_name="Psalmopoeus irminia", size_cm="1.2"),
            HistoryEntry(scrape_datetime="2025-04-02 06:00:00", scientific_name="Psalmopoeus irminia", size_cm="1.2"),
        ]

        history_csv = create_temp_csv_file(create_history_csv_content(history_entries))

        try:
            metadata = get_observation_metadata("Psalmopoeus irminia", history_csv)

            assert metadata["first_observed_status"] == "new"
            assert metadata["first_observed_flag"] == "New"
            assert metadata["latest_observed_status"] == "current"
            assert metadata["latest_observed_flag"] is None
            assert metadata["coverage_status"] == "low"
            assert metadata["coverage_flag"] == "Low coverage"
        finally:
            Path(history_csv).unlink()

    def test_flags_stale_latest_observed(self):
        """Species not seen for 4+ runs should be flagged as stale evidence."""
        from website.species_detail import get_observation_metadata

        history_entries = [
            HistoryEntry(scrape_datetime="2025-01-01 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-01-08 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-01-15 06:00:00", scientific_name="Aphonopelma seemanni", size_cm="1.5"),
            HistoryEntry(scrape_datetime="2025-01-22 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-01-29 06:00:00", scientific_name="Aphonopelma seemanni", size_cm="1.5"),
            HistoryEntry(scrape_datetime="2025-02-05 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-02-12 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-02-19 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-02-26 06:00:00", scientific_name="Other Species", size_cm="2.0"),
        ]

        history_csv = create_temp_csv_file(create_history_csv_content(history_entries))

        try:
            metadata = get_observation_metadata("Aphonopelma seemanni", history_csv)

            assert metadata["latest_observed_status"] == "stale"
            assert metadata["latest_observed_flag"] == "Stale"
        finally:
            Path(history_csv).unlink()

    def test_does_not_flag_non_consecutive_sparse_history_as_new(self):
        """Sparse history alone should not imply the breeder Newly Observed state."""
        from website.species_detail import get_observation_metadata

        history_entries = [
            HistoryEntry(scrape_datetime="2025-01-01 06:00:00", scientific_name="Aphonopelma seemanni", size_cm="1.5"),
            HistoryEntry(scrape_datetime="2025-01-08 06:00:00", scientific_name="Other Species", size_cm="2.0"),
            HistoryEntry(scrape_datetime="2025-01-15 06:00:00", scientific_name="Aphonopelma seemanni", size_cm="1.5"),
        ]

        history_csv = create_temp_csv_file(create_history_csv_content(history_entries))

        try:
            metadata = get_observation_metadata("Aphonopelma seemanni", history_csv)

            assert metadata["first_observed_status"] == "current"
            assert metadata["first_observed_flag"] is None
            assert metadata["coverage_status"] == "low"
        finally:
            Path(history_csv).unlink()


class TestGenerateSpeciesPage:
    """Test species page HTML generation."""

    def test_renders_observation_metadata_and_newly_observed_callout(self):
        """Species page should render limited-history metadata and ambiguity wording."""
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": {
                "signal": "⚠️",
                "stock_pattern": "Newly Observed",
                "oos_runs": "0",
                "wishlist": "18 🔥 ↑",
                "drivers": "Stock: Newly Observed (currently IN); Coverage: observed 2/5 runs; Demand: Wishlist High + rising; Price: Rising",
            },
            "dealer": {
                "risk": "⚠️",
                "stock_reliability": "Medium",
                "restock_speed": "Moderate",
                "wishlist": "18 🔥 ↑",
                "drivers": "Stock: Reliability Medium (Restock Moderate); Coverage: observed 2/5 runs; Demand: Wishlist High + rising; Price: Rising",
            },
        }
        chart_data = {"runs": []}
        observation_metadata = {
            "first_observed": "2025-01-15",
            "latest_observed": "2025-01-29",
            "observed_run_count": 2,
            "total_run_count": 5,
            "observed_runs_display": "2/5 runs",
            "has_ambiguous_pre_first_seen_runs": True,
            "first_observed_status": "new",
            "first_observed_flag": "New",
            "latest_observed_status": "stale",
            "latest_observed_flag": "Stale",
            "coverage_status": "low",
            "coverage_flag": "Low coverage",
        }

        html = generate_species_page(
            "Aphonopelma seemanni",
            "Common Name",
            species_data,
            chart_data,
            observation_metadata=observation_metadata,
            default_view="breeder",
        )

        assert "First observed in dataset" in html
        assert "2025-01-15" in html
        assert "Latest observed" in html
        assert "2025-01-29" in html
        assert "Observed in 2/5 runs" in html
        assert "Pre-first-seen absence is ambiguous" in html
        assert "Newly observed in the dataset" in html
        assert "limited history means supply is not yet proven stable or scarce" in html

        evidence_pos = html.index("<div class=\"section-title\">Evidence")
        coverage_pos = html.index("Observation Coverage")
        tabs_pos = html.index("Breeder view")

        assert coverage_pos > evidence_pos
        assert coverage_pos > tabs_pos
        assert "coverage-metric--key-date" not in html
        assert "coverage-metric--context" in html
        assert "coverage-metric--new" in html
        assert "coverage-metric--stale" in html
        assert "coverage-metric--low" in html
        assert "New" in html
        assert "Stale" in html
        assert "Low coverage" in html

    def test_generates_html_with_breeder_and_dealer_sections(self):
        """Should generate HTML with both perspective sections and required CSS.
        
        Regression: Previously only included species-detail.css, missing analysis.css
        which contains critical stat card styles (.summary-stats, .stat-card, etc.).
        """
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": {
                "signal": "🔥",
                "oos_runs": "8",
                "stock_pattern": "Sustained",
                "wishlist": "24 🔥 ↑",
                "drivers": "",
            },
            "dealer": {
                "risk": "⚠️",
                "stock_reliability": "45%",
                "restock_speed": "Slow",
                "wishlist": "24 ⚠️ →",
                "drivers": "",
            },
        }
        chart_data = {"runs": []}
        
        html = generate_species_page(
            "Aphonopelma seemanni",
            "Common Name",
            species_data,
            chart_data
        )
        
        # Check basic structure
        assert "<h2>Aphonopelma seemanni</h2>" in html
        assert "Common Name" in html
        assert 'id="panel-breeder"' in html
        assert 'id="panel-dealer"' in html
        
        # Check breeder section includes signal
        assert "🔥" in html
        
        # Check dealer section includes risk
        assert "⚠️" in html
        
        # CSS regression checks: both stylesheets must be included
        assert 'href="../analysis.css"' in html, "Missing analysis.css (contains stat card styles)"
        assert 'href="../species-detail.css"' in html, "Missing species-detail.css"
        
        # Verify CSS cascade order
        analysis_idx = html.find('href="../analysis.css"')
        species_idx = html.find('href="../species-detail.css"')
        assert analysis_idx < species_idx, "analysis.css must come before species-detail.css"
        
        # Verify critical classes from analysis.css are present
        assert 'class="summary-stats"' in html, ".summary-stats missing (from analysis.css)"
        assert 'class="stat-card' in html, ".stat-card missing (from analysis.css)"
        assert 'class="stat-value"' in html, ".stat-value missing (from analysis.css)"

        # Regression: wishlist is a composite 'count pressure delta' string that the
        # template must split and render per part. If the template references the wrong
        # key the cards silently show '—'.
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        stat_values = [el.get_text(strip=True) for el in soup.select(".stat-value")]
        assert "🔥" in stat_values, "Breeder Wishlist Pressure card must render '🔥', not '—'"
        assert "↑" in stat_values, "Breeder Wishlist Delta card must render '↑', not '—'"
        assert "⚠️" in stat_values, "Dealer Demand Context card must render '⚠️', not '—'"
        assert "→" in stat_values, "Dealer Wishlist Delta card must render '→', not '—'"
        assert "—" not in stat_values, (
            "No stat card should show '—' when wishlist data is provided; "
            f"got stat values: {stat_values}"
        )

    def test_includes_breadcrumb_navigation(self):
        """Should include breadcrumb with perspective origin."""
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": {"signal": "🔥"},
            "dealer": None,
        }
        chart_data = {"runs": []}
        
        html = generate_species_page(
            "Aphonopelma seemanni",
            "Common Name",
            species_data,
            chart_data,
            default_view="breeder"
        )
        
        assert 'class="breadcrumbs"' in html
        
    def test_includes_tab_segmented_control(self):
        """Should include tabs for switching between breeder/dealer views."""
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": {"signal": "🔥"},
            "dealer": {"risk": "⚠️"},
        }
        chart_data = {"runs": []}
        
        html = generate_species_page(
            "Aphonopelma seemanni",
            "Common Name",
            species_data,
            chart_data
        )
        
        assert 'class="segment"' in html
        assert 'data-view="breeder"' in html
        assert 'data-view="dealer"' in html

    def test_toggles_origin_button_highlight_based_on_selected_view(self):
        """Should include back buttons for breeder and dealer navigation.

        Note: This test only verifies HTML structure. Actual button highlighting
        behavior (based on ?view= parameter) is tested via E2E tests.
        
        This is a subtle regression surface: species pages are static HTML, but
        the initial view can be set via `?view=dealer` links from the dealer table.
        The page must update the highlighted origin button accordingly.
        """
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": {"signal": "🔥"},
            "dealer": {"risk": "⚠️"},
        }
        chart_data = {"runs": []}

        html = generate_species_page(
            "Aphonopelma seemanni",
            "Common Name",
            species_data,
            chart_data,
        )

        # Verify back buttons exist (structure only, E2E tests verify highlighting logic)
        assert 'id="back-breeder"' in html
        assert 'id="back-dealer"' in html


class TestGetPageUrl:
    """Tests for get_page_url function."""
    
    def test_returns_most_recent_page_url_for_species_and_size(self):
        """Should return page_url from most recent observation."""
        from website.species_detail import get_page_url
        
        # Create test CSV with multiple observations
        content = create_history_csv_content([
            HistoryEntry(
                scrape_datetime="2025-01-01 10:00:00",
                scientific_name="Test Spider",
                common_name="Common",
                size_cm="1.5",
                price_gbp="25.00",
                wishlist_count="10",
                page_url="https://example.com/old"
            ),
            HistoryEntry(
                scrape_datetime="2025-01-15 10:00:00",
                scientific_name="Test Spider",
                common_name="Common",
                size_cm="1.5",
                price_gbp="26.00",
                wishlist_count="12",
                page_url="https://example.com/recent"
            ),
            HistoryEntry(
                scrape_datetime="2025-01-08 10:00:00",
                scientific_name="Test Spider",
                common_name="Common",
                size_cm="1.5",
                price_gbp="25.50",
                wishlist_count="11",
                page_url="https://example.com/middle"
            ),
        ])
        
        with temp_csv_file(content) as csv_path:
            result = get_page_url("Test Spider", csv_path)
            assert result == "https://example.com/recent"
    
    def test_returns_none_when_species_not_found(self):
        """Should return None when species not in history."""
        from website.species_detail import get_page_url
        
        content = create_history_csv_content([
            HistoryEntry(
                scrape_datetime="2025-01-01 10:00:00",
                scientific_name="Other Spider",
                common_name="Common",
                size_cm="1.5",
                price_gbp="25.00",
                wishlist_count="10",
                page_url="https://example.com/other"
            ),
        ])
        
        with temp_csv_file(content) as csv_path:
            result = get_page_url("Test Spider", csv_path)
            assert result is None
    
    def test_returns_url_regardless_of_size_variant(self):
        """Phase 5: should return URL for species even when multiple sizes exist."""
        from website.species_detail import get_page_url
        
        content = create_history_csv_content([
            HistoryEntry(
                scrape_datetime="2025-01-01 10:00:00",
                scientific_name="Test Spider",
                common_name="Common",
                size_cm="1.0",
                price_gbp="25.00",
                wishlist_count="10",
                page_url="https://example.com/small"
            ),
        ])
        
        with temp_csv_file(content) as csv_path:
            result = get_page_url("Test Spider", csv_path)
            assert result == "https://example.com/small"
    
    def test_returns_none_when_history_empty(self):
        """Should return None when history CSV is empty."""
        from website.species_detail import get_page_url
        
        content = "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        
        with temp_csv_file(content) as csv_path:
            result = get_page_url("Test Spider", csv_path)
            assert result is None


class TestSignalTooltipDrivers:
    """Test signal driver tooltips in Opportunity Signal cards."""

    def test_breeder_signal_card_includes_drivers_tooltip(self):
        """Should include info icon with drivers tooltip in breeder Opportunity Signal card."""
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": {
                "signal": "🔥",
                "oos_runs": "4",
                "oos": "OUT",
                "stock_pattern": "Sustained",
                "price_trend": "↑",
                "wishlist_pressure": "🔥",
                "wishlist_delta": "↑",
                "drivers": "Stock: Sustained (OOS 4 runs; currently OUT); Demand: Wishlist High + rising; Price: Rising"
            },
            "dealer": None,
        }
        chart_data = {"runs": []}
        
        html = generate_species_page(
            "Test Spider",
            "Common Name",
            species_data,
            chart_data,
            default_view="breeder"
        )
        
        # Check that the Opportunity Signal card label has the info icon structure
        assert '<div class="stat-label">Opportunity Signal' in html
        
        # Check for info icon with tooltip structure matching table implementation
        assert '<span class="info-tip" tabindex="0">ℹ️' in html
        assert '<span class="info-tip__text">' in html
        
        # Check that the drivers text is in the tooltip
        assert "Stock: Sustained (OOS 4 runs; currently OUT)" in html
        assert "Demand: Wishlist High + rising" in html
        assert "Price: Rising" in html

    def test_dealer_signal_card_includes_drivers_tooltip(self):
        """Should include info icon with drivers tooltip in dealer Supply Risk card."""
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": None,
            "dealer": {
                "risk": "🔥",
                "stock_reliability": "Low",
                "restock_speed": "Slow",
                "price_pressure": "↑",
                "wishlist_pressure": "🔥",
                "wishlist_delta": "↑",
                "drivers": "Stock: Reliability Low (Restock Slow); Demand: Wishlist High + rising; Price: Rising"
            },
        }
        chart_data = {"runs": []}
        
        html = generate_species_page(
            "Test Spider",
            "Common Name",
            species_data,
            chart_data,
            default_view="dealer"
        )
        
        # Check that the Supply Risk card label has the info icon structure
        assert '<div class="stat-label">Supply Risk' in html
        
        # Check for info icon with tooltip structure
        assert '<span class="info-tip" tabindex="0">ℹ️' in html
        assert '<span class="info-tip__text">' in html
        
        # Check that the drivers text is in the tooltip
        assert "Stock: Reliability Low (Restock Slow)" in html
        assert "Demand: Wishlist High + rising" in html
        assert "Price: Rising" in html

    def test_tooltip_always_present_when_species_data_exists(self):
        """Should always include tooltip when species data is present (drivers always populated in CSV)."""
        from website.species_detail import generate_species_page

        # Test breeder perspective
        species_data = {
            "breeder": {
                "signal": "🔥",
                "oos_runs": "4",
                "drivers": "Stock: Sustained (OOS 4 runs; currently OUT); Demand: Wishlist High + rising; Price: Rising"
            },
            "dealer": None,
        }
        chart_data = {"runs": []}
        
        html = generate_species_page(
            "Test Spider",
            "Common Name",
            species_data,
            chart_data,
            default_view="breeder"
        )
        
        # Check that the card exists with tooltip
        assert '<div class="stat-label">Opportunity Signal<span class="info-tip"' in html
        assert 'Stock: Sustained (OOS 4 runs; currently OUT)' in html
        
        # Test dealer perspective
        species_data = {
            "breeder": None,
            "dealer": {
                "risk": "⚠️",
                "drivers": "Stock: Reliability Medium (Restock Slow); Demand: Wishlist Moderate + stable; Price: Stable"
            },
        }
        
        html = generate_species_page(
            "Test Spider",
            "Common Name",
            species_data,
            chart_data,
            default_view="dealer"
        )
        
        # Check that the card exists with tooltip
        assert '<div class="stat-label">Supply Risk<span class="info-tip"' in html
        assert 'Stock: Reliability Medium (Restock Slow)' in html


# ============================================================================
# Phase 5 — species-level function signatures (RED tests written first — TDD)
# ============================================================================


class TestGetSpeciesListPhase5:
    """Phase 5: get_species_list() returns list[str] — unique species names only."""

    def test_returns_list_of_strings_not_tuples(self):
        """Phase 5: returned items must be str, not (species, size) tuples."""
        from website.species_detail import get_species_list

        breeder_csv = create_temp_csv_file(
            "Species,Size (cm),Signal\n"
            "Aphonopelma seemanni,1.5,🔥\n"
        )
        try:
            species_list = get_species_list(breeder_csv_path=breeder_csv)
            assert len(species_list) == 1
            assert isinstance(species_list[0], str)
            assert species_list[0] == "Aphonopelma seemanni"
        finally:
            Path(breeder_csv).unlink()

    def test_deduplicates_multi_variant_species(self):
        """Phase 5: species with two active sizes must appear once in the list."""
        from website.species_detail import get_species_list

        breeder_csv = create_temp_csv_file(
            "Species,Size (cm),Signal\n"
            "Aphonopelma seemanni,1.0,🔥\n"
            "Aphonopelma seemanni,2.0,🔥\n"
            "Brachypelma hamorii,2.0,⚠️\n"
        )
        try:
            species_list = get_species_list(breeder_csv_path=breeder_csv)
            assert len(species_list) == 2
            assert "Aphonopelma seemanni" in species_list
            assert "Brachypelma hamorii" in species_list
        finally:
            Path(breeder_csv).unlink()

    def test_merges_species_from_both_csvs(self):
        """Phase 5: union of breeder + dealer species, no duplicates."""
        from website.species_detail import get_species_list

        breeder_csv = create_temp_csv_file(
            "Species,Size (cm),Signal\n"
            "Aphonopelma seemanni,1.5,🔥\n"
            "Brachypelma hamorii,2.0,⚠️\n"
        )
        dealer_csv = create_temp_csv_file(
            "Species,Size (cm),Dealer Risk\n"
            "Aphonopelma seemanni,1.5,🔥\n"
            "Tliltocatl albopilosus,1.0,⚠️\n"
        )
        try:
            species_list = get_species_list(
                breeder_csv_path=breeder_csv, dealer_csv_path=dealer_csv
            )
            assert len(species_list) == 3
            assert "Aphonopelma seemanni" in species_list
            assert "Brachypelma hamorii" in species_list
            assert "Tliltocatl albopilosus" in species_list
        finally:
            Path(breeder_csv).unlink()
            Path(dealer_csv).unlink()

    def test_returns_sorted_list(self):
        """Phase 5: list must be sorted alphabetically."""
        from website.species_detail import get_species_list

        breeder_csv = create_temp_csv_file(
            "Species,Size (cm),Signal\n"
            "Tliltocatl albopilosus,1.0,⚠️\n"
            "Aphonopelma seemanni,1.5,🔥\n"
        )
        try:
            species_list = get_species_list(breeder_csv_path=breeder_csv)
            assert species_list == sorted(species_list)
        finally:
            Path(breeder_csv).unlink()


class TestGetSpeciesDataPhase5:
    """Phase 5: get_species_data() has no 'size' parameter."""

    def test_accepts_no_size_argument(self):
        """Phase 5: calling without size must not raise TypeError."""
        from website.species_detail import get_species_data

        breeder_csv = create_temp_csv_file(
            "Species,Size (cm),Signal,Recommendation,OOS,OOS Runs,Stock Pattern,"
            "Price,Price History,Wishlist,Wishlist History\n"
            "Aphonopelma seemanni,1.5,🔥,Pair soon,OUT,3,Sustained,"
            "£25.00 →,▄▄▃▂▁,-,-\n"
        )
        dealer_csv = create_temp_csv_file(
            "Species,Size (cm),Dealer Risk,Stock Reliability,Restock Speed,"
            "Avg OOS Duration,Price,Price History,Wishlist,Wishlist History,"
            "Stock Availability,Dealer Recommendation\n"
            "Aphonopelma seemanni,1.5,🔥,Low,Slow,3.0,£25.00 →,▄▄▃▂▁,-,-,  ▁▁▁,Seek breeders\n"
        )
        history_csv = create_temp_csv_file(
            "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,"
            "wishlist_count,page_url\n"
            "2025-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,25.00,5,"
            "http://example.com\n"
        )
        try:
            # Must not raise TypeError — no size argument
            result = get_species_data(
                "Aphonopelma seemanni",
                breeder_csv, dealer_csv, history_csv
            )
            assert "breeder" in result
            assert "dealer" in result
        finally:
            Path(breeder_csv).unlink()
            Path(dealer_csv).unlink()
            Path(history_csv).unlink()


class TestBuildChartDataPhase5:
    """Phase 5: build_chart_data() has no 'size' parameter — species-level timeline."""

    def test_accepts_no_size_argument(self):
        """Phase 5: calling without size must not raise TypeError."""
        from website.species_detail import build_chart_data

        history_csv = create_temp_csv_file(
            "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,"
            "wishlist_count,page_url\n"
            "2025-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,25.00,5,"
            "http://example.com\n"
        )
        try:
            # Must not raise TypeError
            result = build_chart_data("Aphonopelma seemanni", history_csv)
            assert "runs" in result
        finally:
            Path(history_csv).unlink()

    def test_includes_multi_variant_observations(self):
        """Phase 5: chart includes observations for ALL sizes of the species."""
        from website.species_detail import build_chart_data

        history_csv = create_temp_csv_file(
            "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,"
            "wishlist_count,page_url\n"
            "2025-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.0,20.00,3,http://a.com\n"
            "2025-01-01,Aphonopelma seemanni,Costa Rican Zebra,2.0,30.00,8,http://b.com\n"
            "2025-01-08,Aphonopelma seemanni,Costa Rican Zebra,2.0,31.00,9,http://b.com\n"
        )
        try:
            result = build_chart_data("Aphonopelma seemanni", history_csv)
            # Both runs should be included (species present in both)
            assert len(result["runs"]) == 2
            assert all(r["observed"] for r in result["runs"])
        finally:
            Path(history_csv).unlink()


class TestGetObservationMetadataPhase5:
    """Phase 5: get_observation_metadata() has no 'size' parameter."""

    def test_accepts_no_size_argument(self):
        """Phase 5: calling without size must not raise TypeError."""
        from website.species_detail import get_observation_metadata

        history_csv = create_temp_csv_file(
            "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,"
            "wishlist_count,page_url\n"
            "2025-01-01,Aphonopelma seemanni,Costa Rican Zebra,1.5,25.00,5,"
            "http://example.com\n"
            "2025-01-08,Aphonopelma seemanni,Costa Rican Zebra,1.5,26.00,6,"
            "http://example.com\n"
        )
        try:
            result = get_observation_metadata("Aphonopelma seemanni", history_csv)
            assert result is not None
            assert "observed_run_count" in result
        finally:
            Path(history_csv).unlink()

    def test_observation_count_includes_all_sizes(self):
        """Phase 5: observation count reflects species-level presence (all sizes)."""
        from website.species_detail import get_observation_metadata

        # 4 total runs; species present in 3 (once with size 1.0, twice with 2.0)
        history_csv = create_temp_csv_file(
            "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,"
            "wishlist_count,page_url\n"
            "2025-01-01,Filler spider,Common,1.0,10.00,1,http://f.com\n"
            "2025-01-01,Aphonopelma seemanni,CRZ,1.0,20.00,3,http://a.com\n"
            "2025-01-08,Filler spider,Common,1.0,10.00,1,http://f.com\n"
            "2025-01-08,Aphonopelma seemanni,CRZ,2.0,30.00,8,http://b.com\n"
            "2025-01-15,Filler spider,Common,1.0,10.00,1,http://f.com\n"
            "2025-01-15,Aphonopelma seemanni,CRZ,2.0,31.00,9,http://b.com\n"
            "2025-01-22,Filler spider,Common,1.0,10.00,1,http://f.com\n"
        )
        try:
            result = get_observation_metadata("Aphonopelma seemanni", history_csv)
            assert result is not None
            # Species was present in 3 of 4 runs
            assert result["observed_run_count"] == 3
            assert result["total_run_count"] == 4
        finally:
            Path(history_csv).unlink()


# ============================================================================
# Phase 5 — template changes: size badge removal + transition banner
# ============================================================================


class TestPhase5TemplateSizeBadgeRemoval:
    """Phase 5: 'Showing size:' badge must be absent — size is no longer shown."""

    def test_does_not_render_size_badge(self):
        """Template must not include the 'Showing size: Xcm' badge after Phase 5."""
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": {
                "signal": "🔥",
                "oos_runs": "4",
                "stock_pattern": "Sustained",
                "wishlist": "12 🔥 ↑",
                "drivers": "",
                "lineage_status": "none",
            },
            "dealer": None,
        }
        chart_data = {"runs": []}

        html = generate_species_page(
            "Aphonopelma seemanni",
            "Common Name",
            species_data,
            chart_data,
        )

        assert "Showing size:" not in html

    def test_chart_table_includes_size_column(self):
        """Chart data table must include a 'Size (cm)' column."""
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": {
                "signal": "🔥",
                "oos_runs": "2",
                "stock_pattern": "Sustained",
                "wishlist": "5 🔥 →",
                "drivers": "",
            },
            "dealer": None,
        }
        chart_data = {
            "runs": [
                {"date": "2025-01-01", "observed": True, "price": "25.00", "wishlist": "5", "size": "1.5"},
                {"date": "2025-01-08", "observed": False, "price": None, "wishlist": None, "size": None},
            ]
        }

        html = generate_species_page(
            "Aphonopelma seemanni",
            "Common Name",
            species_data,
            chart_data,
        )

        assert "<th>Size (cm)</th>" in html


class TestPhase5TransitionBanner:
    """Phase 5: transition banner shown for confirmed/ambiguous transitions, hidden for none/multi-variant."""

    def _species_data_with_lineage(self, lineage_status: str, transition_message: str = "") -> dict:
        return {
            "breeder": {
                "signal": "⚠️",
                "oos_runs": "2",
                "stock_pattern": "Emerging",
                "wishlist": "8 ⚠️ →",
                "drivers": "",
                "lineage_status": lineage_status,
                "transition_message": transition_message,
                "previous_size_cm": "3",
                "current_active_size_cm": "5",
                "transition_date": "2026-02-04",
            },
            "dealer": None,
        }

    def test_renders_transition_banner_for_confirmed_transition(self):
        """Banner must appear when lineage_status is 'confirmed-transition'."""
        from website.species_detail import generate_species_page

        species_data = self._species_data_with_lineage(
            "confirmed-transition",
            "Size changed from 3 cm to 5 cm on 2026-02-04. Price evidence is affected.",
        )
        chart_data = {"runs": []}

        html = generate_species_page(
            "Test Spider",
            "Common Name",
            species_data,
            chart_data,
        )

        assert 'class="transition-banner' in html
        assert "Size changed from 3 cm to 5 cm on 2026-02-04" in html

    def test_renders_transition_banner_for_ambiguous_transition(self):
        """Banner must appear when lineage_status is 'ambiguous-transition'."""
        from website.species_detail import generate_species_page

        species_data = self._species_data_with_lineage(
            "ambiguous-transition",
            "Size change from 3 cm detected but continuity is uncertain.",
        )
        chart_data = {"runs": []}

        html = generate_species_page(
            "Test Spider",
            "Common Name",
            species_data,
            chart_data,
        )

        assert 'class="transition-banner' in html
        assert "Size change from 3 cm detected" in html

    def test_does_not_render_transition_banner_for_none_status(self):
        """Banner must NOT appear when lineage_status is 'none'."""
        from website.species_detail import generate_species_page

        species_data = self._species_data_with_lineage("none")
        chart_data = {"runs": []}

        html = generate_species_page(
            "Test Spider",
            "Common Name",
            species_data,
            chart_data,
        )

        assert 'class="transition-banner' not in html

    def test_does_not_render_transition_banner_for_multi_variant(self):
        """Banner must NOT appear when lineage_status is 'multi-variant'."""
        from website.species_detail import generate_species_page

        species_data = self._species_data_with_lineage("multi-variant")
        chart_data = {"runs": []}

        html = generate_species_page(
            "Test Spider",
            "Common Name",
            species_data,
            chart_data,
        )

        assert 'class="transition-banner' not in html

    def test_does_not_render_transition_banner_when_lineage_status_absent(self):
        """Banner must NOT appear when species_data has no lineage_status field."""
        from website.species_detail import generate_species_page

        species_data = {
            "breeder": {
                "signal": "🔥",
                "oos_runs": "4",
                "stock_pattern": "Sustained",
                "wishlist": "12 🔥 ↑",
                "drivers": "",
                # No lineage_status key
            },
            "dealer": None,
        }
        chart_data = {"runs": []}

        html = generate_species_page(
            "Test Spider",
            "Common Name",
            species_data,
            chart_data,
        )

        assert 'class="transition-banner' not in html

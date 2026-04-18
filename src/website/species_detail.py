"""
Species detail page generation module.

Generates individual species pages with breeder/dealer perspectives,
historical charts, and evidence sections following observations-only philosophy.
"""

import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Set
from collections import defaultdict
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from website.csv_utils import read_csv_file
from shared.history_utils import build_species_presence_timeline
from shared.parsing import format_datetime_smart


# Initialize Jinja2 environment
template_dir = Path(__file__).parent.parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))


def slugify_species(scientific_name: str) -> str:
    """
    Convert scientific name to URL-safe slug.
    
    Args:
        scientific_name: Species name (e.g., "Aphonopelma seemanni")
        
    Returns:
        URL slug (e.g., "aphonopelma-seemanni")
    """
    slug = scientific_name.lower()
    slug = re.sub(r"[^a-z0-9\s.]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def _extract_species_from_csv(csv_path: str, species_set: Set[str]) -> bool:
    """
    Helper to extract species names from a single matrix CSV.

    Args:
        csv_path: Path to CSV file
        species_set: Set to add scientific name strings to

    Returns:
        True if extraction succeeded, False if Species column is absent
    """
    headers, rows = read_csv_file(csv_path)
    if "Species" not in headers:
        return False
    species_idx = headers.index("Species")

    for row in rows:
        species_set.add(row[species_idx])

    return True


def get_species_list(
    breeder_csv_path: Optional[str] = None,
    dealer_csv_path: Optional[str] = None
) -> list[str]:
    """
    Extract unique species names from breeder and/or dealer CSVs.

    Phase 5: returns ``list[str]`` (scientific names only).  One row per species
    in the Phase 4 matrices means no deduplication by size is necessary.

    Args:
        breeder_csv_path: Path to breeder opportunity table CSV
        dealer_csv_path: Path to dealer supply risk table CSV

    Returns:
        Sorted list of unique scientific name strings
    """
    species_set: Set[str] = set()

    if breeder_csv_path:
        if not _extract_species_from_csv(breeder_csv_path, species_set):
            return []

    if dealer_csv_path:
        if not _extract_species_from_csv(dealer_csv_path, species_set):
            return []

    return sorted(species_set)


def _normalize_header(header: str, key_map: Optional[Dict[str, str]] = None) -> str:
    """
    Normalize CSV header to Python dict key.
    
    Args:
        header: CSV header string
        key_map: Optional mapping of specific headers to keys
        
    Returns:
        Normalized key string
    """
    if key_map and header in key_map:
        return key_map[header]
    return header.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("%", "")


def _extract_csv_row_data(
    csv_path: str,
    scientific_name: str,
    key_map: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, str]]:
    """
    Extract data for a specific species from a matrix CSV file.

    Phase 5: match by scientific name only — Phase 4 matrices have one row per
    species, so the ``size`` parameter is no longer required.

    Args:
        csv_path: Path to CSV file
        scientific_name: Scientific name to filter by
        key_map: Optional mapping of specific headers to normalized keys

    Returns:
        Dict of extracted data, or None if not found
    """
    headers, rows = read_csv_file(csv_path)
    if "Species" not in headers:
        return None
    species_idx = headers.index("Species")

    for row in rows:
        if row[species_idx] == scientific_name:
            result = {}
            for i, header in enumerate(headers):
                key = _normalize_header(header, key_map)
                result[key] = row[i]
            return result

    return None


def get_species_data(
    scientific_name: str,
    breeder_csv_path: str,
    dealer_csv_path: str,
    history_csv_path: str
) -> Dict[str, Optional[Dict[str, str]]]:
    """
    Extract all data for a specific species from CSV files.

    Phase 5: ``size`` parameter removed — Phase 4 matrices have one row per
    species, so matching by scientific name alone is sufficient.

    Args:
        scientific_name: Scientific name to filter by
        breeder_csv_path: Path to breeder opportunity table CSV
        dealer_csv_path: Path to dealer supply risk table CSV
        history_csv_path: Path to historical observations CSV

    Returns:
        Dict with 'breeder', 'dealer', and 'history' keys containing extracted data
    """
    dealer_key_map = {
        "Dealer Risk": "risk",
        "Stock Reliability": "stock_reliability",
        "Restock Speed": "restock_speed"
    }

    return {
        "breeder": _extract_csv_row_data(breeder_csv_path, scientific_name),
        "dealer": _extract_csv_row_data(dealer_csv_path, scientific_name, dealer_key_map),
        "history": []
    }


def build_chart_data(
    scientific_name: str,
    history_csv_path: str,
    window_size: int = 26
) -> Dict[str, List[Dict[str, any]]]:
    """
    Extract chart data from history CSV with observations-only approach.

    Phase 5: ``size`` parameter removed — species-level chart uses any observation
    for the species in a given run to mark it as present.

    Args:
        scientific_name: Scientific name to filter by
        history_csv_path: Path to historical observations CSV
        window_size: Number of most recent runs to include (default 26)

    Returns:
        Dict with 'runs' list containing dicts with:
            - date: scrape datetime string
            - observed: bool (True if species observed in this run)
            - price: price string or None if not observed
            - wishlist: wishlist count string or None if not observed
    """
    headers, rows = read_csv_file(history_csv_path)

    if not rows:
        return {"runs": []}

    species_idx = headers.index("scientific_name")
    datetime_idx = headers.index("scrape_datetime")
    price_idx = headers.index("price_gbp")
    wishlist_idx = headers.index("wishlist_count")
    size_idx = headers.index("size_cm")

    all_run_dates = sorted(set(row[datetime_idx] for row in rows))
    recent_run_dates = all_run_dates[-window_size:] if len(all_run_dates) > window_size else all_run_dates

    # Species-level: any row for this species in a run marks it as observed
    # When multiple rows exist for one run (multi-variant), price/wishlist come from
    # the first encountered; all distinct sizes are collected and joined.
    observations: Dict[str, Dict] = {}
    for row in rows:
        if row[species_idx] == scientific_name:
            run_date = row[datetime_idx]
            if run_date not in observations:
                observations[run_date] = {
                    "price": row[price_idx],
                    "wishlist": row[wishlist_idx],
                    "sizes": []
                }
            size_value = row[size_idx].strip()
            if size_value and size_value not in observations[run_date]["sizes"]:
                observations[run_date]["sizes"].append(size_value)
    
    # If species has NEVER been observed, return empty chart data
    if not observations:
        return {"runs": []}
    
    # Format dates smartly (date-only unless collision)
    formatted_dates = format_datetime_smart(recent_run_dates)
    date_to_formatted = dict(zip(recent_run_dates, formatted_dates))
    
    # Build chart data: iterate through ALL recent runs, mark gaps where species wasn't observed
    chart_data = {"runs": []}
    for run_date in recent_run_dates:
        if run_date in observations:
            # Species was observed in this run
            sizes = sorted(observations[run_date]["sizes"], key=float)
            chart_data["runs"].append({
                "date": date_to_formatted[run_date],
                "observed": True,
                "price": observations[run_date]["price"],
                "wishlist": observations[run_date]["wishlist"],
                "size": ", ".join(f"{float(s):g}" for s in sizes)
            })
        else:
            # Gap: species was NOT observed in this run (out of stock)
            chart_data["runs"].append({
                "date": date_to_formatted[run_date],
                "observed": False,
                "price": None,
                "wishlist": None,
                "size": None
            })
    
    return chart_data


def get_default_size(
    scientific_name: str,
    history_csv_path: str
) -> Optional[str]:
    """
    Get the most recently observed size for a species.
    
    Args:
        scientific_name: Scientific name to filter by
        history_csv_path: Path to historical observations CSV
        
    Returns:
        Size (cm) string from most recent observation, or None if never observed
    """
    headers, rows = read_csv_file(history_csv_path)
    
    if not rows:
        return None
    
    species_idx = headers.index("scientific_name")
    size_idx = headers.index("size_cm")
    datetime_idx = headers.index("scrape_datetime")
    
    # Filter observations for this species
    species_observations = [
        (row[datetime_idx], row[size_idx])
        for row in rows
        if row[species_idx] == scientific_name
    ]
    
    if not species_observations:
        return None
    
    # Sort by datetime and return size from most recent
    species_observations.sort(key=lambda x: x[0], reverse=True)
    return species_observations[0][1]


def get_page_url(
    scientific_name: str,
    history_csv_path: str
) -> Optional[str]:
    """
    Get the most recent page_url for a species.

    Phase 5: ``size`` parameter removed — returns the URL from the most recent
    observation for the species regardless of size.

    Args:
        scientific_name: Scientific name to filter by
        history_csv_path: Path to historical observations CSV

    Returns:
        Page URL from most recent observation, or None if never observed
    """
    headers, rows = read_csv_file(history_csv_path)

    if not rows:
        return None

    species_idx = headers.index("scientific_name")
    datetime_idx = headers.index("scrape_datetime")
    page_url_idx = headers.index("page_url")

    matching_observations = [
        (row[datetime_idx], row[page_url_idx])
        for row in rows
        if row[species_idx] == scientific_name
    ]

    if not matching_observations:
        return None

    matching_observations.sort(key=lambda x: x[0], reverse=True)
    return matching_observations[0][1]


def get_observation_metadata(
    scientific_name: str,
    history_csv_path: str,
) -> Optional[Dict[str, object]]:
    """Return full-history observation metadata for a species detail page.

    Phase 5: ``size`` parameter removed — uses species-level presence timeline
    via :func:`shared.history_utils.build_species_presence_timeline`.
    """
    headers, rows = read_csv_file(history_csv_path)

    if not rows:
        return None

    datetime_idx = headers.index("scrape_datetime")
    all_run_dates = sorted(set(row[datetime_idx] for row in rows))
    formatted_dates = format_datetime_smart(all_run_dates)
    date_to_formatted = dict(zip(all_run_dates, formatted_dates))
    history_rows = [dict(zip(headers, row)) for row in rows]

    # Species-level presence across all runs
    timeline = build_species_presence_timeline(history_rows, scientific_name)
    total_run_count = len(timeline)
    observed_run_count = sum(1 for v in timeline.values() if v)

    if observed_run_count == 0:
        return None

    observed_runs = [r for r in all_run_dates if timeline.get(r, False)]
    first_observed_run = observed_runs[0]
    latest_observed_run = observed_runs[-1]

    latest_run_index = all_run_dates.index(latest_observed_run)
    runs_since_latest_observed = total_run_count - 1 - latest_run_index

    # Newly observed: ≤ 2 presence runs and all at the trailing end
    trailing_present = 0
    for r in reversed(all_run_dates):
        if timeline.get(r, False):
            trailing_present += 1
        else:
            break
    is_newly_observed = observed_run_count <= 2 and trailing_present == observed_run_count

    first_observed_status = "new" if is_newly_observed else "current"
    latest_observed_status = "stale" if runs_since_latest_observed >= 4 else "current"
    coverage_status = "low" if observed_run_count <= 2 else "current"

    return {
        "first_observed": date_to_formatted.get(first_observed_run, first_observed_run),
        "latest_observed": date_to_formatted.get(latest_observed_run, latest_observed_run),
        "observed_run_count": observed_run_count,
        "total_run_count": total_run_count,
        "observed_runs_display": f"{observed_run_count}/{total_run_count} runs",
        "has_ambiguous_pre_first_seen_runs": False,  # species-level: no pre-first-seen ambiguity
        "first_observed_status": first_observed_status,
        "first_observed_flag": "New" if first_observed_status == "new" else None,
        "latest_observed_status": latest_observed_status,
        "latest_observed_flag": "Stale" if latest_observed_status == "stale" else None,
        "coverage_status": coverage_status,
        "coverage_flag": "Low coverage" if coverage_status == "low" else None,
    }


def generate_species_page(
    scientific_name: str,
    common_name: str,
    species_data: dict,
    chart_data: dict,
    observation_metadata: Optional[Dict[str, object]] = None,
    page_url: Optional[str] = None,
    default_view: str = "breeder"
) -> str:
    """
    Generate HTML for a species detail page.

    Phase 5: ``size`` parameter removed \u2014 species pages are now species-level.

    Args:
        scientific_name: Species scientific name
        common_name: Species common name
        species_data: Dict with 'breeder' and 'dealer' metrics
        chart_data: Dict with 'runs' list of observations
        observation_metadata: Optional coverage metadata dict
        page_url: Optional URL of the most recent listing
        default_view: Default perspective ('breeder' or 'dealer')

    Returns:
        Generated HTML string
    """
    template = jinja_env.get_template("species_detail.html")

    html = template.render(
        scientific_name=scientific_name,
        common_name=common_name,
        species_data=species_data,
        chart_data=chart_data,
        observation_metadata=observation_metadata,
        page_url=page_url,
        default_view=default_view,
        path_prefix="../",
    )

    return html

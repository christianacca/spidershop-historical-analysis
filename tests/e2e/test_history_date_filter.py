"""E2E tests for the date filter on the history page.

These tests verify that:
- Date checkboxes render correctly for 3 distinct scrape dates
- Deselecting a date hides the corresponding rows
- Quick-select "Last N Runs" buttons narrow the visible rows
- "Show All" restores all rows
- The summary strip updates to reflect the selection
- Date filter combines correctly with other filters (AND logic)
- Download Filtered CSV exports only visible rows with correct schema
"""
import csv
import io
from pathlib import Path

import pytest
from playwright.sync_api import expect

from e2e.css_tokens import token_rgb, hex_to_rgb
from e2e.fixtures import e2e_site_history_multi_date  # noqa: F401

# ---------------------------------------------------------------------------
# Page constants
# ---------------------------------------------------------------------------

HISTORY_PATH = "/history.html"
TABLE_ID = "history-table"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _visible_row_count(page) -> int:
    return page.locator(f"#{TABLE_ID} tbody tr:visible").count()


def _date_checkboxes(page):
    return page.locator(f"input[data-date-value][data-table-id='{TABLE_ID}']")


def _checkbox_for_date(page, date_value: str):
    return page.locator(f"input[data-date-value='{date_value}'][data-table-id='{TABLE_ID}']")


def _all_dates_checkbox(page):
    return page.locator(f"#allDates-{TABLE_ID}")


def _summary_strip(page):
    return page.locator(f"#summary-info-{TABLE_ID}")


def _toggle_date_picker_button(page):
    return page.locator(f"button[data-action='toggle-date-picker'][data-table-id='{TABLE_ID}']")


def _select_last_n_button(page, n: int):
    return page.locator(f"button[data-action='select-last-n'][data-n='{n}'][data-table-id='{TABLE_ID}']")


def _show_all_button(page):
    return page.locator(f"button[data-action='show-all-dates'][data-table-id='{TABLE_ID}']")


def _open_date_picker(page) -> None:
    """Click the toggle button to reveal the individual-date picker panel."""
    _toggle_date_picker_button(page).click()
    page.locator(".date-grid").wait_for(state="visible")


def _open_more_filters(page) -> None:
    """Click the More Filters toggle to reveal the search/price/wishlist panel."""
    btn = page.locator(".advanced-filters-toggle:not(.date-expand-btn)")
    btn.click()
    page.locator(".advanced-filters-content").wait_for(state="visible")




def _navigate_to_history(page, base_url: str) -> None:
    page.goto(f"{base_url}{HISTORY_PATH}")
    page.wait_for_load_state("networkidle")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDateFilterRendering:
    @pytest.mark.e2e
    def test_date_checkboxes_render_three_for_three_dates(
        self, e2e_site_history_multi_date
    ):
        """Three unique dates -> three date checkboxes, all checked, 9 rows visible."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)
        _open_date_picker(page)

        checkboxes = _date_checkboxes(page)
        assert checkboxes.count() == 3, f"Expected 3 date checkboxes, got {checkboxes.count()}"

        for i in range(3):
            assert checkboxes.nth(i).is_checked(), f"Checkbox {i} should be checked by default"

        assert _visible_row_count(page) == 9, (
            f"Expected 9 visible rows, got {_visible_row_count(page)}"
        )

    @pytest.mark.e2e
    def test_summary_info_box_visible_above_filter_section(
        self, e2e_site_history_multi_date
    ):
        """Summary info box should be visible above the date filter section."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)

        summary_box = _summary_strip(page)
        assert summary_box.is_visible(), "Summary info box should be visible"
        text = summary_box.inner_text()
        assert "Viewing" in text, f"Summary box should contain 'Viewing', got: '{text}'"
        assert "scrape runs" in text, f"Summary box should contain 'scrape runs', got: '{text}'"

    @pytest.mark.e2e
    def test_filter_section_has_label(self, e2e_site_history_multi_date):
        """Date filter section should have the '📅 Filter by Scrape Date:' label."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)

        label = page.locator(".date-filter-label")
        assert label.is_visible(), "Date filter label should be visible"
        assert "Filter by Scrape Date" in label.inner_text()

    @pytest.mark.e2e
    def test_expand_button_has_amber_style(self, e2e_site_history_multi_date):
        """The date picker expand button should use the date-expand-btn CSS class."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)

        expand_btn = _toggle_date_picker_button(page)
        assert expand_btn.is_visible(), "Expand button should be visible"
        classes = expand_btn.get_attribute("class") or ""
        assert "date-expand-btn" in classes, (
            f"Expand button should have 'date-expand-btn' class, got: '{classes}'"
        )

    @pytest.mark.e2e
    def test_download_csv_in_stats_bar(self, e2e_site_history_multi_date):
        """Download Filtered CSV button should be inside the table-stats bar."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)

        download_btn = page.locator(".table-stats a[download]")
        assert download_btn.is_visible(), "Download CSV button should be visible in the stats bar"
        assert "Download" in download_btn.inner_text()


class TestDateFilterDeselect:
    @pytest.mark.e2e
    def test_deselecting_one_date_hides_those_rows(
        self, e2e_site_history_multi_date
    ):
        """Unchecking 2026-01-15 should hide 3 rows (one per species)."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)
        _open_date_picker(page)

        _checkbox_for_date(page, "2026-01-15").uncheck()
        expect(page.locator(f"#{TABLE_ID} tbody tr")).to_have_count(6)


class TestDateFilterQuickSelect:
    @pytest.mark.e2e
    def test_select_last_2_runs_shows_correct_rows(
        self, e2e_site_history_multi_date
    ):
        """Clicking Last 2 Runs should show only the 2 most-recent dates (6 rows)."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)
        _open_date_picker(page)

        _select_last_n_button(page, 2).click()
        expect(page.locator(f"#{TABLE_ID} tbody tr")).to_have_count(6)
        assert not _checkbox_for_date(page, "2026-01-01").is_checked(), (
            "Oldest date checkbox (2026-01-01) should be unchecked after Last 2 Runs"
        )

    @pytest.mark.e2e
    def test_show_all_dates_restores_all_rows(
        self, e2e_site_history_multi_date
    ):
        """After narrowing with Last 2 Runs, Show All should restore all 9 rows."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)
        _open_date_picker(page)

        _select_last_n_button(page, 2).click()
        expect(page.locator(f"#{TABLE_ID} tbody tr")).to_have_count(6)

        _show_all_button(page).click()
        expect(page.locator(f"#{TABLE_ID} tbody tr")).to_have_count(9)
        assert _all_dates_checkbox(page).is_checked(), (
            "allDates checkbox should be checked after Show All"
        )


class TestDateFilterSummaryStrip:
    @pytest.mark.e2e
    def test_date_summary_strip_updates_on_deselect(
        self, e2e_site_history_multi_date
    ):
        """Deselecting one date should update the summary strip from 3 of 3 to 2 of 3."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)

        initial_text = _summary_strip(page).inner_text()
        assert "3" in initial_text, (
            f"Initial summary should mention 3 dates, got: '{initial_text}'"
        )

        _open_date_picker(page)
        _checkbox_for_date(page, "2026-01-08").uncheck()
        expect(_summary_strip(page)).to_contain_text("2")


class TestDateFilterCombined:
    @pytest.mark.e2e
    def test_date_and_search_combined_filter(
        self, e2e_site_history_multi_date
    ):
        """Date filter + text search should combine (AND logic).

        With only 2026-01-15 (3 rows) and searching seemanni -> 1 row visible.
        """
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)
        _open_date_picker(page)

        _select_last_n_button(page, 1).click()
        expect(page.locator(f"#{TABLE_ID} tbody tr")).to_have_count(3)
        # Open More Filters panel to access the search input
        _open_more_filters(page)
        search_input = page.locator(
            f"input[data-table-id='{TABLE_ID}'][data-action='search']"
        )
        search_input.fill("seemanni")
        expect(page.locator(f"#{TABLE_ID} tbody tr")).to_have_count(1)


class TestDownloadFilteredCsv:
    EXPECTED_HEADERS = [
        "scrape_datetime", "scientific_name", "common_name",
        "size_cm", "price_gbp", "wishlist_count", "page_url",
    ]
    # ISO datetime written into test fixture for most recent run
    MOST_RECENT_ISO_DATETIME = "2026-01-15T06:10:00"

    @pytest.mark.e2e
    def test_download_exports_only_visible_rows(self, e2e_site_history_multi_date):
        """After 'Last Run' filter (3 rows visible), download should contain only 3 data rows.

        With 9 total rows across 3 runs, the full static CSV has 9 rows. Filtering
        to the last run should produce a download with exactly 3 rows.
        """
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)
        _open_date_picker(page)

        _select_last_n_button(page, 1).click()
        expect(page.locator(f"#{TABLE_ID} tbody tr")).to_have_count(3)

        download_btn = page.locator(
            f"a[data-action='download-filtered-csv'][data-table-id='{TABLE_ID}']"
        )
        with page.expect_download() as download_info:
            download_btn.click()
        content = Path(download_info.value.path()).read_text(encoding="utf-8")

        rows = list(csv.reader(io.StringIO(content)))
        data_rows = rows[1:]

        assert len(data_rows) == 3, (
            f"Expected 3 data rows (last run only), got {len(data_rows)}"
        )

    @pytest.mark.e2e
    def test_download_headers_match_raw_csv_schema(self, e2e_site_history_multi_date):
        """Downloaded CSV headers must exactly match the raw CSV column names."""
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)

        download_btn = page.locator(
            f"a[data-action='download-filtered-csv'][data-table-id='{TABLE_ID}']"
        )
        with page.expect_download() as download_info:
            download_btn.click()
        content = Path(download_info.value.path()).read_text(encoding="utf-8")

        rows = list(csv.reader(io.StringIO(content)))
        assert rows, "Downloaded CSV must not be empty"
        assert rows[0] == self.EXPECTED_HEADERS, (
            f"Header mismatch.\n  Expected: {self.EXPECTED_HEADERS}\n  Got:      {rows[0]}"
        )

    @pytest.mark.e2e
    def test_download_preserves_raw_iso_datetime(self, e2e_site_history_multi_date):
        """scrape_datetime in the download must be the raw ISO value from the source CSV.

        The table displays a formatted date (e.g. '2026-01-15') but the downloaded
        CSV should restore the original ISO timestamp (e.g. '2026-01-15T06:10:00').
        """
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)
        _open_date_picker(page)

        _select_last_n_button(page, 1).click()
        expect(page.locator(f"#{TABLE_ID} tbody tr")).to_have_count(3)

        download_btn = page.locator(
            f"a[data-action='download-filtered-csv'][data-table-id='{TABLE_ID}']"
        )
        with page.expect_download() as download_info:
            download_btn.click()
        content = Path(download_info.value.path()).read_text(encoding="utf-8")

        rows = list(csv.reader(io.StringIO(content)))
        headers = rows[0]
        data_rows = rows[1:]

        datetime_idx = headers.index("scrape_datetime")
        for row in data_rows:
            assert row[datetime_idx] == self.MOST_RECENT_ISO_DATETIME, (
                f"Expected raw ISO datetime '{self.MOST_RECENT_ISO_DATETIME}', "
                f"got '{row[datetime_idx]}'"
            )

    @pytest.mark.e2e
    def test_download_page_url_contains_real_url_not_species_name(self, e2e_site_history_multi_date):
        """page_url column must contain the actual URL, not the link label (species name).

        The table renders page_url as '<a href="URL">species name</a>', so a naive
        td.textContent extraction would yield the species name instead of the URL.
        """
        page, base_url, _errors = e2e_site_history_multi_date
        _navigate_to_history(page, base_url)

        download_btn = page.locator(
            f"a[data-action='download-filtered-csv'][data-table-id='{TABLE_ID}']"
        )
        with page.expect_download() as download_info:
            download_btn.click()
        content = Path(download_info.value.path()).read_text(encoding="utf-8")

        rows = list(csv.reader(io.StringIO(content)))
        headers = rows[0]
        data_rows = rows[1:]

        url_idx = headers.index("page_url")
        for row in data_rows:
            url_value = row[url_idx]
            assert url_value.startswith("https://"), (
                f"Expected page_url to be a URL starting with 'https://', got '{url_value}'"
            )


# ---------------------------------------------------------------------------
# Date filter section structural styles
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_history_date_filter_section_styling(e2e_site_history_multi_date) -> None:
    """Date filter section should have amber border; expand button should have amber background."""
    page, base_url, errors = e2e_site_history_multi_date

    page.goto(f"{base_url}{HISTORY_PATH}", wait_until="domcontentloaded")

    date_section = page.locator('.date-filter-section')
    assert date_section.count() >= 1, "History page should have .date-filter-section"

    border_color = date_section.first.evaluate('el => window.getComputedStyle(el).borderColor')
    assert token_rgb('--color-date-filter') in border_color, \
        f"Date filter section border should be amber, got {border_color}"

    bg = date_section.first.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert bg != 'rgba(0, 0, 0, 0)', \
        f"Date filter section should have a background color, got {bg}"

    expand_btn = page.locator('.date-expand-btn')
    assert expand_btn.count() >= 1, "History page should have .date-expand-btn"
    btn_bg = expand_btn.first.evaluate('el => window.getComputedStyle(el).backgroundColor')
    assert token_rgb('--color-date-filter') in btn_bg, \
        f"Expand button should have amber background, got {btn_bg}"


@pytest.mark.e2e
def test_history_date_grid_styling(e2e_site_history_multi_date) -> None:
    """Date grid should use CSS grid; date rows should have white backgrounds."""
    page, base_url, errors = e2e_site_history_multi_date

    page.goto(f"{base_url}{HISTORY_PATH}", wait_until="domcontentloaded")

    expand_btn = page.locator('.date-expand-btn')
    assert expand_btn.count() >= 1, "History page should have .date-expand-btn"
    expand_btn.first.click()
    page.locator('.date-grid').wait_for(state="visible")

    date_grid = page.locator('.date-grid')
    assert date_grid.count() >= 1, "History page should have .date-grid"

    display = date_grid.first.evaluate('el => window.getComputedStyle(el).display')
    assert display == 'grid', f"Date grid should use CSS grid, got display={display}"

    date_rows = page.locator('.date-row')
    assert date_rows.count() >= 1, "History page should have .date-row items"
    row_bg = date_rows.first.evaluate('el => window.getComputedStyle(el).backgroundColor')
    # Date rows use --color-surface (#fffaf2 warm white) — not a dark or transparent colour
    assert hex_to_rgb('#fffaf2') in row_bg, \
        f"Date rows should have surface-colour background (--color-surface), got {row_bg}"

#!/usr/bin/env python3
"""Generic "output contract" tests for the generated static website.

These tests intentionally avoid per-page assertions.
Instead, they validate the generated output as a whole:
- every local asset/link referenced from HTML resolves to a real file
- links do not escape the output directory

This catches regressions like incorrect relative paths for CSS/JS.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from website.generate_website import OUTPUT_DIR, main


@dataclass(frozen=True)
class _HtmlReference:
    tag: str
    attribute: str
    raw_value: str


def _iter_references(soup: BeautifulSoup) -> Iterable[_HtmlReference]:
    # Assets
    for link in soup.find_all("link"):
        if not link.get("href"):
            continue
        # Only validate stylesheets (other rel types can be e.g. preconnect)
        rel = link.get("rel") or []
        rel_values = {r.lower() for r in rel} if isinstance(rel, list) else {str(rel).lower()}
        if "stylesheet" in rel_values:
            yield _HtmlReference(tag="link", attribute="href", raw_value=str(link["href"]))

    for script in soup.find_all("script"):
        if script.get("src"):
            yield _HtmlReference(tag="script", attribute="src", raw_value=str(script["src"]))

    for img in soup.find_all("img"):
        if img.get("src"):
            yield _HtmlReference(tag="img", attribute="src", raw_value=str(img["src"]))

    # Local navigation / downloads
    for anchor in soup.find_all("a"):
        if anchor.get("href"):
            yield _HtmlReference(tag="a", attribute="href", raw_value=str(anchor["href"]))


def _strip_fragment_and_query(url: str) -> str:
    # Avoid parsing URLs with urlparse if empty/whitespace.
    value = url.strip()
    if not value:
        return ""
    # Keep it simple: split on first ? or #, whichever comes first.
    for sep in ("#", "?"):
        if sep in value:
            value = value.split(sep, 1)[0]
    return value.strip()


def _resolve_local_reference(
    *,
    output_dir: Path,
    html_path: Path,
    reference: _HtmlReference,
) -> Optional[Path]:
    raw = reference.raw_value.strip()
    if not raw:
        return None

    # Skip anchors-only links.
    if raw.startswith("#"):
        return None

    # Skip data URIs.
    if raw.startswith("data:"):
        return None

    parsed = urlparse(raw)
    if parsed.scheme or parsed.netloc:
        # External link (https://...), mailto:, etc.
        return None

    local_path = _strip_fragment_and_query(raw)
    if not local_path:
        return None

    # Only validate file-ish links for anchors; leave other hrefs alone.
    if reference.tag == "a":
        suffixes = (".html", ".csv", ".css", ".js", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico")
        if not local_path.lower().endswith(suffixes):
            return None

    resolved = (html_path.parent / local_path).resolve(strict=False)

    output_root = output_dir.resolve(strict=False)
    if resolved != output_root and output_root not in resolved.parents:
        return resolved

    return resolved


def _write_minimal_inputs(cwd: Path) -> None:
    # Minimal snapshot/history required by website.generate_website.main()
    (cwd / "spidershop_spiderlings_scrape.csv").write_text(
        "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,2.0,25.00,5,https://example.com/a\n",
        encoding="utf-8",
    )

    (cwd / "spidershop_spiderlings_history.csv").write_text(
        "scrape_datetime,scientific_name,common_name,size_cm,price_gbp,wishlist_count,page_url\n"
        "2025-12-25,Aphonopelma seemanni,Costa Rican Zebra,2.0,24.00,4,https://example.com/a\n"
        "2026-01-01,Aphonopelma seemanni,Costa Rican Zebra,2.0,25.00,5,https://example.com/a\n",
        encoding="utf-8",
    )

    # Include Size (cm) so species pages are generated.
    (cwd / "breeder_opportunity_table.csv").write_text(
        "Species,Size (cm),Signal,OOS Runs\n"
        "Aphonopelma seemanni,2.0,🔥,4\n",
        encoding="utf-8",
    )
    (cwd / "dealer_supply_risk_table.csv").write_text(
        "Species,Size (cm),Dealer Risk,Stock Reliability,Restock Speed\n"
        "Aphonopelma seemanni,2.0,⚠️,Low,Slow\n",
        encoding="utf-8",
    )

    # Optional, but keeps behaviour closer to real runs.
    (cwd / "analysis_summary.md").write_text(
        "## 🧬 Breeder Opportunity Matrix (Top 10)\n\n"
        "**Summary:** 1 species analyzed | 🔥 Hot: 1 | ⚠️ Watch: 0 | ❌ Avoid: 0\n\n"
        "## 🏪 Dealer Supply Risk Matrix (Top 10)\n\n"
        "**Summary:** 1 species analyzed | 🔥 High Risk: 0 | ⚠️ Moderate Risk: 1 | ❌ Low Risk: 0\n",
        encoding="utf-8",
    )


def test_generated_website_has_no_broken_local_references() -> None:
    """All local href/src references in generated HTML should resolve to real files."""
    cwd = Path.cwd()
    _write_minimal_inputs(cwd)

    main()

    output_dir = (cwd / OUTPUT_DIR).resolve(strict=False)
    assert output_dir.exists(), "Expected website output directory to exist"

    html_files = sorted(output_dir.rglob("*.html"))
    assert html_files, "Expected at least one generated HTML file"

    broken: list[str] = []

    for html_path in html_files:
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

        relative_html_path = html_path.relative_to(output_dir)
        is_nested_page = len(relative_html_path.parts) > 1

        for reference in _iter_references(soup):
            raw = reference.raw_value.strip()
            # Root-absolute paths (e.g. "/species-detail.css") are fragile on
            # GitHub Pages (repo subpath) and break on nested pages.
            if raw.startswith("/") and not raw.startswith("//"):
                hint = (
                    "Use a relative path (e.g. '../...') or a template prefix like '{{ path_prefix }}...'."
                    if is_nested_page
                    else "Use a relative path (e.g. '...') or a template prefix like '{{ path_prefix }}...'."
                )
                broken.append(
                    f"{html_path.relative_to(output_dir)}: {reference.tag}[{reference.attribute}]={reference.raw_value!r} "
                    "uses a root-absolute path. " + hint
                )
                continue

            resolved = _resolve_local_reference(
                output_dir=output_dir,
                html_path=html_path,
                reference=reference,
            )
            if resolved is None:
                continue

            # If resolved escapes output_dir, treat as broken.
            output_root = output_dir.resolve(strict=False)
            if resolved != output_root and output_root not in resolved.parents:
                broken.append(
                    f"{html_path.relative_to(output_dir)}: {reference.tag}[{reference.attribute}]={reference.raw_value!r} "
                    f"resolves outside output dir -> {resolved}"
                )
                continue

            if not resolved.exists():
                broken.append(
                    f"{html_path.relative_to(output_dir)}: {reference.tag}[{reference.attribute}]={reference.raw_value!r} "
                    f"missing -> {resolved.relative_to(output_dir)}"
                )

    assert not broken, "Broken local references found:\n" + "\n".join(broken[:50])

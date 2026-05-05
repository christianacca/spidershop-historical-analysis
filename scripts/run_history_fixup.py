#!/usr/bin/env python3
"""
Run the general-purpose history fixup pipeline against a history CSV file.

Usage
-----
    PYTHONPATH=src python scripts/run_history_fixup.py \
        --input  spidershop_spiderlings_history.csv \
        --output spidershop_spiderlings_history.csv \
        [--dry-run]

Options
-------
--input   Path to the history CSV to read (required).
--output  Path to write the fixed CSV (required; may be the same as --input).
--dry-run Print a fixup report without writing the output file.

Exit codes
----------
0  All fixups applied (or --dry-run completed) with no errors.
1  One or more fixups reported errors (lifestyle fetch failures, etc.).
   The output file is still written unless --dry-run was given.
"""

import argparse
import csv
import sys
from pathlib import Path

# Allow `python scripts/run_history_fixup.py` with PYTHONPATH=src
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared.config import CSV_HEADER
from scrape.history_fixup import apply_all_fixups, REGISTERED_FIXUPS


def _load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _print_report(all_stats) -> int:
    """Print per-fixup report. Returns 1 if any errors, else 0."""
    has_errors = False
    print("\n=== History Fixup Report ===")
    for stats in all_stats:
        print(f"\n[{stats.name}]")
        print(f"  Rows changed : {stats.rows_changed}")
        if stats.errors:
            has_errors = True
            print(f"  Errors ({len(stats.errors)}):")
            for err in stats.errors:
                print(f"    - {err}")
        else:
            print("  Errors       : none")
    print()
    return 1 if has_errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix up the history CSV in-place.")
    parser.add_argument("--input", required=True, help="Path to source history CSV")
    parser.add_argument("--output", required=True, help="Path to write fixed history CSV")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing output")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 1

    print(f"Loading  : {input_path}")
    rows = _load_csv(input_path)
    print(f"Rows     : {len(rows)}")

    print("Running fixups …")
    rows, all_stats = apply_all_fixups(rows, REGISTERED_FIXUPS)

    exit_code = _print_report(all_stats)

    if args.dry_run:
        print("Dry-run — output file NOT written.")
    else:
        _write_csv(output_path, rows)
        print(f"Written  : {output_path}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
View test coverage summary from coverage.json.

This script parses the coverage JSON file and displays a formatted summary.
Useful for agents to programmatically check coverage status.

Usage:
    python view_coverage.py
    python view_coverage.py --format=json
    python view_coverage.py --format=table
    python view_coverage.py --threshold=80
"""

import sys
import json
from pathlib import Path


def load_coverage_data():
    """Load coverage data from coverage.json."""
    coverage_file = Path("tmp/coverage/coverage.json")
    if not coverage_file.exists():
        print("❌ tmp/coverage/coverage.json not found. Run tests with coverage first:")
        print("   pytest tests/ --cov=src --cov-report=json")
        sys.exit(1)
    
    with open(coverage_file) as f:
        return json.load(f)


def format_table(data, threshold=80.0):
    """Format coverage data as a table."""
    total_coverage = data['totals']['percent_covered']
    
    print("\n" + "="*80)
    print("TEST COVERAGE SUMMARY")
    print("="*80)
    print(f"\n{'Total Coverage:':<20} {total_coverage:>6.2f}%", end="")
    
    if total_coverage >= threshold:
        print(" ✅ (meets threshold)")
    else:
        print(f" ❌ (below {threshold}% threshold)")
    
    print(f"\n{'Threshold:':<20} {threshold:>6.2f}%")
    
    print("\n" + "-"*80)
    print(f"{'Module':<35} {'Stmts':>7} {'Miss':>7} {'Cover':>8} {'Status':>10}")
    print("-"*80)
    
    files_sorted = sorted(data['files'].items())
    
    for filepath, stats in files_sorted:
        if 'src/' not in filepath:
            continue
        
        module_name = filepath.split('/')[-1]
        stmts = stats['summary']['num_statements']
        missing = stats['summary']['missing_lines']
        coverage = stats['summary']['percent_covered']
        
        status = "✅" if coverage >= threshold else "⚠️" if coverage >= 50 else "❌"
        
        print(f"{module_name:<35} {stmts:>7} {missing:>7} {coverage:>7.2f}% {status:>10}")
    
    print("-"*80)
    
    # Summary stats
    totals = data['totals']
    print(f"\n{'Total Statements:':<25} {totals['num_statements']}")
    print(f"{'Covered Statements:':<25} {totals['covered_lines']}")
    print(f"{'Missing Statements:':<25} {totals['missing_lines']}")
    print(f"{'Excluded Lines:':<25} {totals['excluded_lines']}")
    print()


def format_json_output(data):
    """Format coverage data as JSON."""
    output = {
        'total_coverage': data['totals']['percent_covered'],
        'modules': {}
    }
    
    for filepath, stats in sorted(data['files'].items()):
        if 'src/' not in filepath:
            continue
        
        module_name = filepath.split('/')[-1]
        output['modules'][module_name] = {
            'statements': stats['summary']['num_statements'],
            'missing': stats['summary']['missing_lines'],
            'coverage': stats['summary']['percent_covered']
        }
    
    print(json.dumps(output, indent=2))


def check_coverage(data, threshold):
    """Check if coverage meets threshold and return exit code."""
    total_coverage = data['totals']['percent_covered']
    
    if total_coverage >= threshold:
        return 0  # Success
    else:
        return 1  # Failure


def main():
    """Main entry point."""
    # Parse arguments
    format_type = "table"
    threshold = 80.0
    
    for arg in sys.argv[1:]:
        if arg.startswith("--format="):
            format_type = arg.split("=")[1]
        elif arg.startswith("--threshold="):
            threshold = float(arg.split("=")[1])
        elif arg in ["-h", "--help"]:
            print(__doc__)
            sys.exit(0)
    
    # Load and display coverage
    data = load_coverage_data()
    
    if format_type == "json":
        format_json_output(data)
    else:
        format_table(data, threshold)
    
    # Exit with appropriate code
    sys.exit(check_coverage(data, threshold))


if __name__ == "__main__":
    main()

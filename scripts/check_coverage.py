#!/usr/bin/env python3
"""
Check if test coverage meets requirements for specific modules.

This script is designed for agent mode to verify that code changes
include appropriate test coverage.

Usage:
    # Check overall coverage
    python check_coverage.py
    
    # Check specific module
    python check_coverage.py --module=breeder_matrix.py --threshold=80
    
    # Check multiple modules
    python check_coverage.py --modules=breeder_matrix.py,dealer_matrix.py
    
    # Verbose output
    python check_coverage.py --verbose
"""

import sys
import json
from pathlib import Path


def load_coverage():
    """Load coverage.json file."""
    coverage_file = Path("coverage.json")
    
    if not coverage_file.exists():
        print("❌ coverage.json not found")
        print("Run: pytest tests/ --cov=src --cov-report=json")
        return None
    
    with open(coverage_file) as f:
        return json.load(f)


def check_module_coverage(data, module_name, threshold=80.0, verbose=False):
    """Check coverage for a specific module."""
    # Find module in coverage data
    module_path = None
    for filepath in data['files'].keys():
        if filepath.endswith(module_name):
            module_path = filepath
            break
    
    if not module_path:
        print(f"❌ Module '{module_name}' not found in coverage data")
        return False
    
    stats = data['files'][module_path]['summary']
    coverage = stats['percent_covered']
    missing = stats['missing_lines']
    statements = stats['num_statements']
    
    meets_threshold = coverage >= threshold
    status = "✅" if meets_threshold else "❌"
    
    if verbose or not meets_threshold:
        print(f"{status} {module_name}: {coverage:.2f}% coverage")
        print(f"   Statements: {statements}")
        print(f"   Missing: {missing}")
        print(f"   Threshold: {threshold}%")
        
        if not meets_threshold:
            print(f"   ⚠️  Coverage is {threshold - coverage:.2f}% below threshold")
    elif meets_threshold:
        print(f"{status} {module_name}: {coverage:.2f}%")
    
    return meets_threshold


def check_overall_coverage(data, threshold=80.0, verbose=False):
    """Check overall project coverage."""
    total_coverage = data['totals']['percent_covered']
    meets_threshold = total_coverage >= threshold
    status = "✅" if meets_threshold else "❌"
    
    print(f"{status} Overall Coverage: {total_coverage:.2f}%")
    
    if verbose or not meets_threshold:
        totals = data['totals']
        print(f"   Total Statements: {totals['num_statements']}")
        print(f"   Covered: {totals['covered_lines']}")
        print(f"   Missing: {totals['missing_lines']}")
        print(f"   Threshold: {threshold}%")
        
        if not meets_threshold:
            print(f"   ⚠️  Coverage is {threshold - total_coverage:.2f}% below threshold")
    
    return meets_threshold


def main():
    """Main entry point."""
    # Parse arguments
    modules = []
    threshold = 80.0
    verbose = False
    check_overall = True
    
    for arg in sys.argv[1:]:
        if arg.startswith("--module="):
            modules.append(arg.split("=")[1])
            check_overall = False
        elif arg.startswith("--modules="):
            modules.extend(arg.split("=")[1].split(","))
            check_overall = False
        elif arg.startswith("--threshold="):
            threshold = float(arg.split("=")[1])
        elif arg in ["--verbose", "-v"]:
            verbose = True
        elif arg in ["-h", "--help"]:
            print(__doc__)
            sys.exit(0)
    
    # Load coverage data
    data = load_coverage()
    if not data:
        sys.exit(1)
    
    # Check coverage
    all_pass = True
    
    if check_overall:
        # Check overall coverage
        all_pass = check_overall_coverage(data, threshold, verbose)
    else:
        # Check specific modules
        for module in modules:
            module = module.strip()
            passed = check_module_coverage(data, module, threshold, verbose)
            all_pass = all_pass and passed
    
    # Exit with appropriate code
    if all_pass:
        print("\n✅ All coverage checks passed")
        sys.exit(0)
    else:
        print("\n❌ Coverage checks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

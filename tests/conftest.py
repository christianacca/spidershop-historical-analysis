#!/usr/bin/env python3
"""
Shared test fixtures and utilities for all test modules.
"""
import sys
from pathlib import Path

# Add src directory to Python path to enable imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import make_row from legend_examples (production code)
from legend_examples import make_row

__all__ = ['make_row']

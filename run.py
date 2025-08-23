#!/usr/bin/env python3
"""
Test runner for AI Personal Coach
Usage: python run_tests.py --help
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cli import main

if __name__ == "__main__":
    main()

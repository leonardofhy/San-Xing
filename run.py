#!/usr/bin/env python3
"""
Test runner for 三省 (SanXing)
Usage: python run_tests.py --help
"""

import sys
from pathlib import Path

from src.cli import main

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    main()

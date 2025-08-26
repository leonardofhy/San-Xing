#!/usr/bin/env python3
"""
Launch the San-Xing interactive dashboard from the main project directory.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the Streamlit dashboard."""
    dashboard_path = Path(__file__).parent / "visualization" / "dashboard.py"
    
    if not dashboard_path.exists():
        print("❌ Error: Dashboard not found!")
        print("Make sure visualization/dashboard.py exists.")
        sys.exit(1)
    
    # Check if data exists
    data_paths = [
        Path(__file__).parent / "visualization" / "raw_data.json",
        Path(__file__).parent / "data" / "viz.csv"
    ]
    
    has_data = any(p.exists() for p in data_paths)
    if not has_data:
        print("Warning: No visualization data found.")
        print("Generate data first:")
        print("   - For JSON: cd visualization && python download_data.py")
        print("   - For CSV: uv run python -m src.cli --process-data --days 30")
        print()
    
    print("Starting San-Xing Interactive Dashboard...")
    print("Dashboard URL: http://localhost:8501")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Run streamlit from main directory
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
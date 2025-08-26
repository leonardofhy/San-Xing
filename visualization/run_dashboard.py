#!/usr/bin/env python3
"""
Convenience script to run the San-Xing dashboard.
Note: Run this from the main San-Xing directory, not the visualization subdirectory.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the Streamlit dashboard with proper configuration."""
    dashboard_path = Path(__file__).parent / "dashboard.py"
    
    if not dashboard_path.exists():
        print("Error: dashboard.py not found!")
        sys.exit(1)
    
    # Check if data exists
    data_path = Path(__file__).parent / "raw_data.json"
    if not data_path.exists():
        print("Warning: raw_data.json not found.")
        print("Generate sample data: python visualization/generate_sample_data.py")
        print("Dashboard will still run but may show limited data.")
        print()
    
    print("Starting San-Xing Dashboard...")
    print("Dashboard will be available at: http://localhost:8501")
    print("Tip: Run from main directory for best results")
    print("Use Ctrl+C to stop the server")
    print()
    
    try:
        # Run streamlit with the dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(dashboard_path),
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ])
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    except Exception as e:
        print(f"Error running dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
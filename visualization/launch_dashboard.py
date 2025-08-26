#!/usr/bin/env python3
"""
Simple launcher for San-Xing Dashboard
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the bulletproof dashboard"""
    
    dashboard_path = Path(__file__).parent / "dashboard.py"
    parent_dir = Path(__file__).parent.parent
    
    print("🚀 Launching San-Xing Dashboard...")
    print(f"📊 Dashboard: {dashboard_path.name}")
    print("🌐 Browser will open automatically")
    print("\nPress Ctrl+C to stop the dashboard")
    print("=" * 50)
    
    try:
        # Run from parent directory with uv
        cmd = ["uv", "run", "streamlit", "run", str(dashboard_path.relative_to(parent_dir))]
        subprocess.run(cmd, cwd=parent_dir)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
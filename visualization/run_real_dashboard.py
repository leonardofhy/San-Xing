#!/usr/bin/env python3
"""
Launch script for San-Xing Real Data Dashboard
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the real data dashboard"""
    
    # Get the parent directory (main San-Xing project)
    parent_dir = Path(__file__).parent.parent
    dashboard_path = Path(__file__).parent / "real_data_dashboard.py"
    
    print("🚀 Launching San-Xing Real Data Dashboard...")
    print(f"📊 Dashboard: {dashboard_path}")
    print(f"🔧 Working directory: {parent_dir}")
    print("🌐 Browser will open automatically")
    print("\n" + "="*50)
    
    try:
        # Change to parent directory and run with uv
        cmd = [
            "uv", "run", "streamlit", "run", 
            str(dashboard_path.relative_to(parent_dir)),
            "--server.headless", "false"
        ]
        
        subprocess.run(cmd, cwd=parent_dir)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
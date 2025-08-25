#!/usr/bin/env python3
"""Run all visualization analyses in sequence.

Robust to being invoked from:
 - visualization/ directory (scripts are alongside)
 - project root (scripts under visualization/)
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


BASE_DIR = Path(__file__).resolve().parent


def run_script(script_path: Path) -> bool:
    """Run a Python script and return success status."""
    rel = script_path.relative_to(BASE_DIR)
    print(f"\n{'='*50}")
    print(f"Running {rel}...")
    print("=" * 50)
    try:
        subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            cwd=str(BASE_DIR),  # ensure working directory for local file IO (raw_data.json etc.)
        )
        print(f"✓ {rel} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {rel} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"✗ {rel} not found")
        return False


def main():
    print("San-Xing Data Visualization Suite")
    print("Running all analyses...")

    script_names: List[str] = [
        "download_data.py",
        "sleep_analysis.py",
        "health_dashboard.py",
        "activity_analysis.py",
    ]

    results: List[Tuple[str, bool]] = []

    for name in script_names:
        path = BASE_DIR / name
        if path.exists():
            success = run_script(path)
            results.append((name, success))
        else:
            print(f"✗ {name} not found at {path}, skipping...")
            results.append((name, False))

    print(f"\n{'='*50}")
    print("Analysis Summary:")
    print("=" * 50)
    successful = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"{'✓' if ok else '✗'} {name}")

    print(f"\nCompleted: {successful}/{len(results)} analyses successful")
    if successful == len(results):
        print(
            "\n🎉 All analyses completed successfully! Generated PNG files are in visualization/."
        )
    else:
        print(
            "\n⚠️  Some analyses failed or were missing. Ensure you're synced & raw_data.json exists."
        )
        print(
            "   Hint: run 'uv run python visualization/download_data.py' first if raw_data.json is missing."
        )


if __name__ == "__main__":  # pragma: no cover
    main()

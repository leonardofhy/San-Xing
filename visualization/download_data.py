#!/usr/bin/env python3
"""Download raw data from HuggingFace dataset."""

import json
import os
from pathlib import Path

import requests

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def _load_token_from_config() -> str | None:
    """Attempt to read HF token from project's root config.local.toml.

    Looks for keys: hf_token, HF_TOKEN (case-insensitive) under top-level.
    Returns token string or None if unavailable / parse failure.
    """
    root_cfg = Path(__file__).resolve().parent.parent / "config.local.toml"
    if not root_cfg.exists() or tomllib is None:
        return None
    try:
        data = tomllib.loads(root_cfg.read_text(encoding="utf-8"))  # type: ignore[arg-type]
    except (OSError, ValueError, TypeError):  # pragma: no cover - non critical
        return None
    # Accept common key variants
    for k in ["hf_token", "HF_TOKEN", "huggingface_token", "HFToken"]:
        if k in data and isinstance(data[k], str) and data[k].strip():
            return data[k].strip()
    return None


def download_data(repo_id: str, output_file: str = "raw_data.json", hf_token: str = None):
    """Download raw data from HuggingFace dataset repository.

    Args:
        repo_id: HuggingFace dataset repository ID (e.g., "username/dataset-name")
        output_file: Local filename to save the data
        hf_token: HuggingFace authentication token for private repos
    """
    url = f"https://huggingface.co/datasets/{repo_id}/resolve/main/raw_data.json"

    print(f"Downloading data from: {url}")

    headers = {}
    if not hf_token:
        # Prefer explicit argument > env > config file
        hf_token = os.getenv("HF_TOKEN") or _load_token_from_config()
        if hf_token:
            print("Resolved HF token from env/config")
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        print("Using HuggingFace authentication token (masked)")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse JSON to validate format
        data = response.json()
        print(f"Downloaded {len(data)} records")

        # Save to local file
        output_path = Path(output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Data saved to: {output_path.absolute()}")
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error downloading data: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None


if __name__ == "__main__":
    # Simple CLI usage (can be extended if needed)
    repo_env = os.getenv("HF_REPO", "leonardo298/san-xing-diary")
    token_arg = os.getenv("HF_TOKEN")  # explicit env wins
    download_data(repo_env, hf_token=token_arg)

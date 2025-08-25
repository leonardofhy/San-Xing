"""Configuration module for 三省 (SanXing)"""

from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional

try:  # Python 3.11+
    import tomllib  # type: ignore
except ImportError:  # pragma: no cover
    tomllib = None  # type: ignore


_SHEET_URL_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")


def _extract_sheet_id(value: str) -> str:
    if not value:
        return ""
    m = _SHEET_URL_RE.search(value)
    return m.group(1) if m else value.strip()


@dataclass
class Config:
    """Central configuration for the insight engine"""

    # Google Sheets
    SPREADSHEET_ID: str = os.getenv("SHEET_ID", "")
    CREDENTIALS_PATH: Path = Path(os.getenv("CREDENTIALS_PATH", "")).expanduser()
    TAB_NAME: str = "MetaLog"
    TIMESTAMP_COLUMN: str = "Timestamp"
    DIARY_COLUMN: str = "今天想記點什麼？"

    # Processing
    MIN_DIARY_LENGTH: int = 3
    EARLY_MORNING_HOUR: int = 3  # < 3:00 AM = previous day
    DEFAULT_DAYS_WINDOW: int = 30
    MAX_CHAR_BUDGET: int = 8000

    # Timestamps
    TIMESTAMP_PATTERNS: tuple[str, ...] = (
        "%Y-%m-%dT%H:%M:%S",  # ISO 8601
        "%d/%m/%Y %H:%M:%S",  # Sheet format
    )

    # LLM
    LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "https://api.deepseek.com/chat/completions")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = "deepseek-reasoner"
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 2
    LLM_STREAM: bool = False  # when True, stream tokens to stdout

    # HuggingFace integration
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")

    # Output
    OUTPUT_DIR: Path = Path("./data")
    RAW_DIR: Path = field(init=False)
    INSIGHTS_DIR: Path = field(init=False)
    SNAPSHOT_DEDUP: bool = True  # avoid writing duplicate raw sheet snapshots (content-hash)

    # Versioning
    VERSION: Dict[str, str] = field(
        default_factory=lambda: {
            "schema": "s1",
            "prompt": "p1",
            "model": "deepseek-reasoner@2025-08",
            "contract": "c1",
        }
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"  # or "text"

    # Runtime (non-persistent) flags
    DRY_RUN: bool = False  # skip LLM call / network
    OFFLINE_SNAPSHOT: Optional[Path] = None  # reuse a raw snapshot instead of hitting Sheets

    def __post_init__(self):
        self.SPREADSHEET_ID = _extract_sheet_id(self.SPREADSHEET_ID)
        self.OUTPUT_DIR = self.OUTPUT_DIR.expanduser()
        self.RAW_DIR = self.OUTPUT_DIR / "raw"
        self.INSIGHTS_DIR = self.OUTPUT_DIR / "insights"
        self.RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        if self.CREDENTIALS_PATH and not self.CREDENTIALS_PATH.exists():
            # Allow deferred validation elsewhere
            pass

    def validate(self) -> None:
        """
        Validate the configuration.
        """
        errors = []
        if not self.SPREADSHEET_ID:
            errors.append("SHEET_ID missing (provide --sheet-id / --sheet-url / env SHEET_ID).")
        if self.CREDENTIALS_PATH and not self.CREDENTIALS_PATH.exists():
            errors.append(f"Credentials file not found: {self.CREDENTIALS_PATH}")
        if self.MIN_DIARY_LENGTH < 1:
            errors.append("MIN_DIARY_LENGTH must be >=1")
        if errors:
            raise ValueError("Config validation errors:\n- " + "\n- ".join(errors))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary.

        Returns:
            Dict[str, Any]: The config as a dictionary.
        """
        d = asdict(self)
        # Remove large / derived paths if needed
        return d

    @classmethod
    def from_file(cls, path: str | Path, overrides: Optional[Dict[str, Any]] = None) -> "Config":
        """Load configuration from a file.

        Args:
            path (str | Path): Path to the configuration file.
            overrides (Optional[Dict[str, Any]], optional): Overrides for the configuration. Defaults to None.

        Raises:
            FileNotFoundError: _description_
            RuntimeError: _description_
            ValueError: _description_

        Returns:
            Config: _description_
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {p}")
        suffix = p.suffix.lower()
        if suffix in {".toml", ".tml"}:
            if tomllib is None:
                raise RuntimeError("tomllib not available (Python <3.11).")
            # parse TOML content
            data = tomllib.loads(p.read_text(encoding="utf-8"))
        elif suffix == ".json":
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            raise ValueError("Unsupported config format (use .toml or .json)")

        flat = _flatten_keys(data)
        if overrides:
            flat.update({k: v for k, v in overrides.items() if v is not None})
        # Environment precedence already applied in defaults; CLI overrides passed in overrides
        cfg = cls(**_coerce_types(flat))
        return cfg


def _flatten_keys(d: Dict[str, Any], parent: str = "", sep: str = ".") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        key = f"{parent}{sep}{k}" if parent else k
        if isinstance(v, dict):
            out.update(_flatten_keys(v, key, sep))
        else:
            out[key] = v
    # Accept both nested and top-level keys; for this simple config we just return original if flat suffices
    # Filter only recognized top-level fields
    filtered: Dict[str, Any] = {}
    for k, v in out.items():
        top = k.split(sep)[-1]
        filtered[top] = v
    return filtered


def _coerce_types(data: Dict[str, Any]) -> Dict[str, Any]:
    # Simple coercions if config file uses strings
    int_fields = {
        "MIN_DIARY_LENGTH",
        "EARLY_MORNING_HOUR",
        "DEFAULT_DAYS_WINDOW",
        "MAX_CHAR_BUDGET",
        "LLM_TIMEOUT",
        "LLM_MAX_RETRIES",
    }
    bool_fields = {"DRY_RUN"}
    bool_fields.update({"LLM_STREAM"})
    bool_fields.update({"SNAPSHOT_DEDUP"})
    path_fields = {"CREDENTIALS_PATH", "OUTPUT_DIR", "OFFLINE_SNAPSHOT"}
    for f in int_fields:
        if f in data and isinstance(data[f], str) and data[f].isdigit():
            data[f] = int(data[f])
    for f in bool_fields:
        if f in data and isinstance(data[f], str):
            data[f] = data[f].lower() in {"1", "true", "yes", "on"}
    for f in path_fields:
        if f in data and data[f]:
            data[f] = Path(str(data[f])).expanduser()
    if "SHEET_ID" in data:
        data["SHEET_ID"] = _extract_sheet_id(str(data["SHEET_ID"]))
    return data

"""Configuration module for AI Personal Coach"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Central configuration for the insight engine"""
    
    # Google Sheets
    SHEET_ID: str = os.getenv("SHEET_ID", "")
    CREDENTIALS_PATH: Path = Path(os.getenv("CREDENTIALS_PATH", ""))
    TAB_NAME: str = "MetaLog"
    TIMESTAMP_COLUMN: str = "Timestamp"
    DIARY_COLUMN: str = "今天想記點什麼？"
    
    # Processing
    MIN_DIARY_LENGTH: int = 3
    EARLY_MORNING_HOUR: int = 3  # < 3:00 AM = previous day
    DEFAULT_DAYS_WINDOW: int = 30
    MAX_CHAR_BUDGET: int = 8000
    
    # Timestamps
    TIMESTAMP_PATTERNS = [
        "%Y-%m-%dT%H:%M:%S",  # ISO 8601
        "%d/%m/%Y %H:%M:%S",  # Sheet format
    ]
    
    # LLM
    LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "https://api.deepseek.com/chat/completions")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = "deepseek-reasoner"
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 2
    
    # Output
    OUTPUT_DIR: Path = Path("./data")
    RAW_DIR: Path = OUTPUT_DIR / "raw"
    INSIGHTS_DIR: Path = OUTPUT_DIR / "insights"
    
    # Versioning
    VERSION = {
        "schema": "s1",
        "prompt": "p1",
        "model": "deepseek-reasoner@2025-08",
        "contract": "c1"
    }
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"  # or "text"
    
    def __post_init__(self):
        """Create output directories if they don't exist"""
        self.RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

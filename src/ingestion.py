"""Data ingestion from Google Sheets"""

import gspread
import hashlib
import json
from google.oauth2.service_account import Credentials
from typing import List, Dict, Tuple
from pathlib import Path
from datetime import datetime
from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class SheetIngester:
    """Handles Google Sheet data fetching"""

    def __init__(self, config: Config):
        self.config = config
        self.client = None

    def connect(self) -> None:
        """Establish connection to Google Sheets"""
        if not self.config.CREDENTIALS_PATH.exists():
            raise FileNotFoundError(f"Credentials not found: {self.config.CREDENTIALS_PATH}")

        # Use modern Sheets + Drive scopes (feeds scope deprecated). Include read-only Sheets scope.
        scope = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]

        creds = Credentials.from_service_account_file(
            str(self.config.CREDENTIALS_PATH), scopes=scope
        )
        self.client = gspread.authorize(creds)
        logger.info("Connected to Google Sheets API")

    def fetch_rows(self) -> Tuple[List[Dict], str]:
        """
        Fetch all rows from MetaLog sheet
        Returns: (rows, header_hash)
        """
        if not self.client:
            self.connect()

        try:
            sheet = self.client.open_by_key(self.config.SPREADSHEET_ID)
            worksheet = sheet.worksheet(self.config.TAB_NAME)

            # Get all records as list of dicts, with duplicate header fallback
            try:
                records = worksheet.get_all_records()
            except gspread.exceptions.GSpreadException as e:
                if "duplicates" in str(e).lower():
                    logger.warning("Duplicate header detected; applying auto-unique fallback")
                    values = worksheet.get_all_values()
                    if not values:
                        return [], ""
                    header_row = self._make_headers_unique(values[0])
                    data_rows = values[1:]
                    records = [
                        {
                            header_row[i]: row[i] if i < len(row) else ""
                            for i in range(len(header_row))
                        }
                        for row in data_rows
                        if any(cell.strip() for cell in row)
                    ]
                else:
                    raise

            # Compute header hash for change detection
            headers = worksheet.row_values(1)
            header_hash = hashlib.sha256(json.dumps(headers).encode()).hexdigest()[:8]

            logger.info("Fetched %d rows, header_hash=%s", len(records), header_hash)

            # Save raw snapshot
            self._save_snapshot(records)

            return records, header_hash

        except gspread.exceptions.WorksheetNotFound:
            try:
                titles = [ws.title for ws in sheet.worksheets()] if "sheet" in locals() else []
            except (gspread.exceptions.GSpreadException, AttributeError) as e:
                # Narrowed exception handling: handle gspread errors and unexpected attribute issues,
                # fallback to empty titles and log debug info for investigation.
                logger.debug("Failed to list worksheets: %s", e)
                titles = []
            logger.error(
                "Worksheet '%s' not found. Available worksheets=%s", self.config.TAB_NAME, titles
            )
            raise
        except gspread.exceptions.APIError as e:  # type: ignore[attr-defined]
            # Attempt to extract JSON error payload
            detail = None
            try:
                if hasattr(e, "response") and hasattr(e.response, "json"):
                    detail = e.response.json()
                elif hasattr(e, "response") and hasattr(e.response, "text"):
                    detail = e.response.text
            except (ValueError, AttributeError, TypeError):
                # JSON decoding, attribute access, or unexpected type errors may occur here;
                # ignore these specific errors but let other exceptions propagate.
                pass
            logger.error(
                "Failed to fetch data (APIError) spreadsheet_id=%s tab=%s error=%s detail=%s",
                self.config.SPREADSHEET_ID,
                self.config.TAB_NAME,
                e,
                (
                    detail
                    if isinstance(detail, str)
                    else json.dumps(detail, ensure_ascii=False) if detail else None
                ),
            )
            raise
        except Exception as e:
            logger.error(
                "Failed to fetch data: %s (type=%s) spreadsheet_id=%s tab=%s",
                e,
                type(e).__name__,
                self.config.SPREADSHEET_ID,
                self.config.TAB_NAME,
            )
            raise

    def _save_snapshot(self, records: List[Dict]) -> None:
        """Save raw data snapshot for debugging/replay"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.config.RAW_DIR / f"snapshot_{timestamp}.json"

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": timestamp,
                    "sheet_id": self.config.SPREADSHEET_ID,
                    "tab_name": self.config.TAB_NAME,
                    "row_count": len(records),
                    "records": records,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info("Saved raw snapshot: %s", snapshot_path)

    def validate_headers(self, records: List[Dict]) -> bool:
        """Check if required columns exist"""
        if not records:
            return False

        required = {self.config.TIMESTAMP_COLUMN, self.config.DIARY_COLUMN}
        headers = set(records[0].keys())

        missing = required - headers
        if missing:
            logger.error("Missing required columns: %s", missing)
            return False

        return True

    @staticmethod
    def _make_headers_unique(headers: List[str]) -> List[str]:
        """Ensure headers are unique, appending suffixes for duplicates or blanks"""
        seen = {}
        result = []
        for h in headers:
            base = h.strip() or "Column"
            name = base
            idx = 1
            while name in seen:
                idx += 1
                name = f"{base}_{idx}"
            seen[name] = True
            result.append(name)
        return result


def load_cached_snapshot(path: Path) -> List[Dict]:
    """Load previously saved snapshot for offline development"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("records", [])

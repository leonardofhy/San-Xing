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
            
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        creds = Credentials.from_service_account_file(
            str(self.config.CREDENTIALS_PATH), 
            scopes=scope
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
            sheet = self.client.open_by_key(self.config.SHEET_ID)
            worksheet = sheet.worksheet(self.config.TAB_NAME)
            
            # Get all records as list of dicts
            records = worksheet.get_all_records()
            
            # Compute header hash for change detection
            headers = worksheet.row_values(1)
            header_hash = hashlib.sha256(json.dumps(headers).encode()).hexdigest()[:8]
            
            logger.info(f"Fetched {len(records)} rows, header_hash={header_hash}")
            
            # Save raw snapshot
            self._save_snapshot(records)
            
            return records, header_hash
            
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Worksheet '{self.config.TAB_NAME}' not found")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            raise
    
    def _save_snapshot(self, records: List[Dict]) -> None:
        """Save raw data snapshot for debugging/replay"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.config.RAW_DIR / f"snapshot_{timestamp}.json"
        
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "sheet_id": self.config.SHEET_ID,
                "tab_name": self.config.TAB_NAME,
                "row_count": len(records),
                "records": records
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved raw snapshot: {snapshot_path}")
    
    def validate_headers(self, records: List[Dict]) -> bool:
        """Check if required columns exist"""
        if not records:
            return False
            
        required = {self.config.TIMESTAMP_COLUMN, self.config.DIARY_COLUMN}
        headers = set(records[0].keys())
        
        missing = required - headers
        if missing:
            logger.error(f"Missing required columns: {missing}")
            return False
            
        return True


def load_cached_snapshot(path: Path) -> List[Dict]:
    """Load previously saved snapshot for offline development"""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("records", [])

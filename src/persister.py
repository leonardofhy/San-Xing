"""Output persistence module"""

import json
import csv
from pathlib import Path
from typing import List
from .models import InsightPack, DiaryEntry
from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class OutputPersister:
    """Handles JSON and CSV output writing"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def persist(self, pack: InsightPack, run_id: str) -> Path:
        """
        Write insight pack to JSON and optional CSV summary
        Returns path to main JSON file
        """
        # Write main JSON
        json_path = self.config.INSIGHTS_DIR / f"run-{run_id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(pack.to_json())
        
        logger.info("Wrote insight pack: %s", json_path)
        
        # Write theme summary CSV
        if pack.themes:
            self._write_theme_csv(pack)
        
        return json_path
    
    def _write_theme_csv(self, pack: InsightPack) -> None:
        """Write themes to CSV for quick review"""
        csv_path = self.config.INSIGHTS_DIR / "themes-latest.csv"
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Theme", "Support", "Run ID", "Generated At"])
            
            for theme in pack.themes:
                writer.writerow([
                    theme.label,
                    theme.support,
                    pack.meta["run_id"],
                    pack.meta["generatedAt"]
                ])
        
        logger.info("Wrote theme summary: %s", csv_path)
    
    def save_entries_snapshot(self, entries: List[DiaryEntry], run_id: str) -> None:
        """Save normalized entries for debugging"""
        snapshot = {
            "run_id": run_id,
            "entry_count": len(entries),
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "logical_date": str(e.logical_date),
                    "raw_timestamp": e.raw_timestamp,
                    "length": e.entry_length,
                    "is_early_morning": e.is_early_morning
                }
                for e in entries
            ]
        }
        
        path = self.config.RAW_DIR / f"entries-{run_id}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        
        logger.info("Saved entries snapshot: %s", path)

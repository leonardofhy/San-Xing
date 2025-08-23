"""Data models for diary entries and insights"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any
import hashlib
import json


@dataclass
class DiaryEntry:
    """Normalized diary entry"""
    raw_timestamp: str
    timestamp: datetime
    ts_epoch: int
    logical_date: date
    diary_text: str
    entry_length: int
    entry_id: str
    is_early_morning: bool = False
    
    @classmethod
    def from_raw(cls, raw_timestamp: str, diary_text: str, parsed_dt: datetime) -> "DiaryEntry":
        """Create entry with computed fields"""
        # Early morning adjustment
        is_early_morning = parsed_dt.hour < 3
        logical_date = (parsed_dt.date() if not is_early_morning 
                       else (parsed_dt - timedelta(days=1)).date())
        
        # Generate stable ID
        id_source = f"{raw_timestamp}{diary_text[:64]}"
        entry_id = hashlib.sha1(id_source.encode()).hexdigest()
        
        return cls(
            raw_timestamp=raw_timestamp,
            timestamp=parsed_dt,
            ts_epoch=int(parsed_dt.timestamp() * 1000),
            logical_date=logical_date,
            diary_text=diary_text.strip(),
            entry_length=len(diary_text.strip()),
            entry_id=entry_id,
            is_early_morning=is_early_morning
        )


@dataclass
class DailySummary:
    """Single day summary"""
    date: str
    summary: str


@dataclass
class Theme:
    """Extracted theme with support count"""
    label: str
    support: int


@dataclass
class InsightPack:
    """Complete analysis output"""
    meta: Dict[str, Any]
    dailySummaries: List[DailySummary] = field(default_factory=list)
    themes: List[Theme] = field(default_factory=list)
    reflectiveQuestion: str = "請回顧今天的一件小事，它代表了你想成為的人嗎?"
    anomalies: List[str] = field(default_factory=list)
    hiddenSignals: List[str] = field(default_factory=list)
    emotionalIndicators: List[Dict] = field(default_factory=list)
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "meta": self.meta,
            "dailySummaries": [{"date": ds.date, "summary": ds.summary} 
                              for ds in self.dailySummaries],
            "themes": [{"label": t.label, "support": t.support} 
                      for t in self.themes],
            "reflectiveQuestion": self.reflectiveQuestion,
            "anomalies": self.anomalies,
            "hiddenSignals": self.hiddenSignals,
            "emotionalIndicators": self.emotionalIndicators
        }
    
    @classmethod
    def create_fallback(cls, run_id: str, version: Dict, entries_count: int = 0) -> "InsightPack":
        """Create minimal fallback pack when LLM fails"""
        return cls(
            meta={
                "run_id": run_id,
                "version": version,
                "entriesAnalyzed": entries_count,
                "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "mode": "fallback"
            }
        )

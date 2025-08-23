"""LLM analysis module"""

import json
import time
from typing import List, Dict
import requests
from .models import DiaryEntry, InsightPack, DailySummary, Theme
from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class LLMAnalyzer:
    """Handles LLM prompt building and API calls"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def analyze(self, entries: List[DiaryEntry], run_id: str) -> InsightPack:
        """
        Build prompt, call LLM, parse response
        Returns InsightPack (fallback if LLM fails)
        """
        if not entries:
            return self._create_empty_pack(run_id)
        
        prompt = self._build_prompt(entries)
        
        for attempt in range(self.config.LLM_MAX_RETRIES):
            try:
                response = self._call_llm(prompt)
                pack = self._parse_response(response, run_id, len(entries))
                logger.info("Analysis successful on attempt %d", attempt + 1)
                return pack
            except Exception as e:
                logger.warning("LLM attempt %d failed: %s", attempt + 1, str(e))
                if attempt < self.config.LLM_MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        # All attempts failed - return fallback
        logger.error("All LLM attempts failed, using fallback")
        return InsightPack.create_fallback(run_id, self.config.VERSION, len(entries))
    
    def _build_prompt(self, entries: List[DiaryEntry]) -> str:
        """Build prompt from template p1"""
        entries_text = "\n\n".join([
            f"[{entry.logical_date}]\n{entry.diary_text}"
            for entry in entries
        ])
        
        return f"""You are an AI personal coach analyzing diary entries.
Return ONLY valid JSON with these keys:
- dailySummaries: array of {{date, summary}}
- themes: array of {{label, support}} (max 5, labels ≤12 chars)
- reflectiveQuestion: single open-ended question
- anomalies: array of strings (optional)
- hiddenSignals: array of strings (optional)

Diary Entries:
{entries_text}

Analyze for patterns, emotional indicators, and growth opportunities.
Output JSON only, no other text."""
    
    def _call_llm(self, prompt: str) -> Dict:
        """Call LLM API"""
        headers = {
            "Authorization": f"Bearer {self.config.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are an AI personal coach. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }
        
        response = requests.post(
            self.config.LLM_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=self.config.LLM_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    
    def _parse_response(self, data: Dict, run_id: str, entries_count: int) -> InsightPack:
        """Parse LLM response into InsightPack"""
        from datetime import datetime, timezone
        
        # Build meta
        meta = {
            "run_id": run_id,
            "version": self.config.VERSION,
            "entriesAnalyzed": entries_count,
            "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        
        # Parse components
        daily_summaries = [
            DailySummary(date=ds["date"], summary=ds["summary"])
            for ds in data.get("dailySummaries", [])
        ]
        
        themes = [
            Theme(label=t["label"], support=t.get("support", 1))
            for t in data.get("themes", [])[:5]  # Max 5
        ]
        
        return InsightPack(
            meta=meta,
            dailySummaries=daily_summaries,
            themes=themes,
            reflectiveQuestion=data.get("reflectiveQuestion", "請回顧今天的一件小事，它代表了你想成為的人嗎?"),
            anomalies=data.get("anomalies", []),
            hiddenSignals=data.get("hiddenSignals", []),
            emotionalIndicators=data.get("emotionalIndicators", [])
        )
    
    def _create_empty_pack(self, run_id: str) -> InsightPack:
        """Create empty pack when no entries"""
        return InsightPack.create_fallback(run_id, self.config.VERSION, 0)

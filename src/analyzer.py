"""LLM analysis module"""

import json
import sys
import time
from typing import List, Dict
from datetime import datetime, timezone
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
            except (
                requests.exceptions.RequestException,
                json.JSONDecodeError,
                KeyError,
                ValueError,
            ) as e:
                logger.warning("LLM attempt %d failed: %s", attempt + 1, str(e))
                if attempt < self.config.LLM_MAX_RETRIES - 1:
                    time.sleep(2**attempt)  # Exponential backoff

        # All attempts failed - return fallback
        logger.error("All LLM attempts failed, using fallback")
        return InsightPack.create_fallback(run_id, self.config.VERSION, len(entries))

    def _build_prompt(self, entries: List[DiaryEntry]) -> str:
        """Build prompt (Traditional Chinese instructions)"""
        entries_text = "\n\n".join(
            [f"[{entry.logical_date}]\n{entry.diary_text}" for entry in entries]
        )

        return f"""你是一位精準、沉著且具同理心的個人成長教練，正在分析多日的日誌內容。
請「只輸出」一個有效 JSON，不要加入解釋、前後綴或 Markdown。使用下列固定英文字鍵 (維持英文，不可翻譯)：
- dailySummaries: 陣列，元素格式 {{date, summary}}，summary 為該日期的精煉重點 (不超過 60 中文字)。
- themes: 陣列，元素格式 {{label, support}}，最多 5 個；label 需 ≤12 個全形字，代表跨日出現的核心主題；support 為整數 (出現/支持度)。
- reflectiveQuestion: 一個引導式、開放式反思問題（避免是/否回答，聚焦模式 / 習慣 / 意義）。
- anomalies: （可選）字串陣列，指出不尋常或與過往模式偏離的觀察。
- hiddenSignals: （可選）字串陣列，指出尚未被使用者明確寫出的潛在趨勢或情緒信號。
- emotionalIndicators: （可選）字串陣列，聚焦情緒調節、壓力、動機等微妙指標。

分析重點指引：
1. 抽取可行洞察：聚焦行為模式、能量變化、情緒調節、價值一致性。
2. 避免空泛語句（如：保持加油、繼續努力）；輸出具體、觀察式描述。
3. 不捏造未出現的事件；允許指出資料不足處。
4. 若日誌含凌晨（<03:00）內容，仍視為其邏輯日期 (已預先處理)。
5. reflectiveQuestion 要能引導下一步探索，而非重述既有狀態。

使用者日誌內容 (原文可能混合語言)：
{entries_text}

請執行：
- 先整體掃描 → 建立主題與信號 → 逐日濃縮 → 生成反思問題。
僅輸出最終 JSON，無任何多餘文字。"""

    def _call_llm(self, prompt: str) -> Dict:
        """Call LLM API. Supports optional streaming if config.LLM_STREAM is True.

        Streaming strategy:
        - If LLM_STREAM enabled, send request with stream=True (OpenAI-compatible) and incrementally write tokens.
        - Accumulate content; once finished, parse as JSON.
        - If provider does not support streaming (error or unexpected), fallback to non-streaming.
        """
        headers = {
            "Authorization": f"Bearer {self.config.LLM_API_KEY}",
            "Content-Type": "application/json",
        }

        base_payload = {
            "model": self.config.LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位精準且具結構化思維的個人成長教練。所有回覆必須是有效 JSON（UTF-8），不得含有額外文字。",
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
        }

        if getattr(self.config, "LLM_STREAM", False):
            try:
                stream_payload = dict(base_payload)
                stream_payload["stream"] = True
                logger.info("Starting streaming LLM call (model=%s)", self.config.LLM_MODEL)
                with requests.post(
                    self.config.LLM_ENDPOINT,
                    headers=headers,
                    json=stream_payload,
                    timeout=self.config.LLM_TIMEOUT,
                    stream=True,
                ) as r:
                    r.raise_for_status()
                    collected = []
                    for line in r.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        if line.startswith("data:"):
                            chunk = line[len("data:") :].strip()
                            if chunk == "[DONE]":
                                break
                            try:
                                j = json.loads(chunk)
                                # OpenAI-style delta path
                                delta = j.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta:
                                    token = delta["content"]
                                    collected.append(token)
                                    sys.stdout.write(token)
                                    sys.stdout.flush()
                            except json.JSONDecodeError:
                                # Some providers might emit plain text lines; still show them
                                collected.append(chunk)
                                sys.stdout.write(chunk)
                                sys.stdout.flush()
                    print()  # newline after stream
                full_content = "".join(collected).strip()
                # Attempt to locate JSON substring (in case provider prepended commentary despite instructions)
                json_start = full_content.find("{")
                json_end = full_content.rfind("}")
                if json_start == -1 or json_end == -1:
                    raise ValueError("No JSON object detected in streamed content")
                parsed = json.loads(full_content[json_start : json_end + 1])
                return parsed
            except (requests.RequestException, json.JSONDecodeError, ValueError) as e:  # fallback
                logger.warning("Streaming failed (%s); falling back to non-streaming mode", e)

        # Non-streaming path
        response = requests.post(
            self.config.LLM_ENDPOINT,
            headers=headers,
            json=base_payload,
            timeout=self.config.LLM_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)

    def _parse_response(self, data: Dict, run_id: str, entries_count: int) -> InsightPack:
        """Parse LLM response into InsightPack"""

        # Build meta
        meta = {
            "run_id": run_id,
            "version": self.config.VERSION,
            "entriesAnalyzed": entries_count,
            "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        # Parse components
        daily_summaries = [
            DailySummary(date=ds["date"], summary=ds["summary"])
            for ds in data.get("dailySummaries", [])
        ]

        themes = [
            Theme(label=t.get("label"), support=int(t.get("support", 0)))
            for t in data.get("themes", [])
        ]

        # Build InsightPack
        return InsightPack(
            meta=meta,
            dailySummaries=daily_summaries,
            themes=themes,
            reflectiveQuestion=data.get(
                "reflectiveQuestion", "請回顧今天的一件小事，它代表了你想成為的人嗎?"
            ),
            anomalies=data.get("anomalies", []),
            hiddenSignals=data.get("hiddenSignals", []),
            emotionalIndicators=data.get("emotionalIndicators", []),
        )

    def _create_empty_pack(self, run_id: str) -> InsightPack:
        """Create empty pack when no entries"""
        return InsightPack.create_fallback(run_id, self.config.VERSION, 0)

    def _create_empty_pack(self, run_id: str) -> InsightPack:
        """Create empty pack when no entries"""
        return InsightPack.create_fallback(run_id, self.config.VERSION, 0)

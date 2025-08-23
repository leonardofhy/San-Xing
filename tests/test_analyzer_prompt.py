from src.analyzer import LLMAnalyzer
from src.config import Config
from src.models import DiaryEntry
from datetime import datetime


def make_entry(ts: str, text: str):
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    return DiaryEntry.from_raw(ts, text, dt)


def test_build_prompt_structure():
    config = Config()
    analyzer = LLMAnalyzer(config)
    entries = [
        make_entry("2025-08-21T10:00:00", "學習進步"),
        make_entry("2025-08-22T11:30:00", "保持專注"),
    ]
    prompt = analyzer._build_prompt(entries)  # accessing internal for test  # noqa: SLF001
    assert "學習進步" in prompt
    assert "保持專注" in prompt
    assert "dailySummaries" in prompt

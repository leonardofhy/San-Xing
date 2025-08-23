from src.config import Config
from src.window import WindowBuilder
from src.models import DiaryEntry
from datetime import datetime

def build_entry(ts: str, text: str):
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    return DiaryEntry.from_raw(ts, text, dt)

def test_window_budget():
    config = Config()
    wb = WindowBuilder(config)
    entries = [build_entry(f"2025-08-2{i}T12:00:00", "內容" * 10) for i in range(1,6)]
    selected, chars = wb.build_window(entries, char_budget=400)
    assert len(selected) <= len(entries)
    assert chars <= 400

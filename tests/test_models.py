from src.models import DiaryEntry, InsightPack
from datetime import datetime


def test_diary_entry_id_and_early_morning():
    dt = datetime.strptime("2025-08-23T01:10:00", "%Y-%m-%dT%H:%M:%S")
    e = DiaryEntry.from_raw("2025-08-23T01:10:00", "測試內容", dt)
    assert e.is_early_morning is True
    assert len(e.entry_id) == 40  # sha1 hex length


def test_fallback_pack():
    pack = InsightPack.create_fallback("run123", {"schema":"s1","prompt":"p1","model":"m","contract":"c1"})
    assert pack.meta["mode"] == "fallback"
    assert pack.meta["entriesAnalyzed"] == 0

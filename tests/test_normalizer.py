from src.config import Config
from src.normalizer import EntryNormalizer


def test_normalizer_basic():
    config = Config()
    normalizer = EntryNormalizer(config)
    records = [
        {config.TIMESTAMP_COLUMN: "2025-08-23T10:15:00", config.DIARY_COLUMN: "學習專注與計畫"},
        {config.TIMESTAMP_COLUMN: "2025-08-23T00:45:00", config.DIARY_COLUMN: "凌晨反思"},
        {config.TIMESTAMP_COLUMN: "bad-ts", config.DIARY_COLUMN: "無效"},  # malformed timestamp should be skipped
        {config.TIMESTAMP_COLUMN: "2025-08-22T22:00:00", config.DIARY_COLUMN: "放鬆休"},  # ensure length >= 3
    ]
    entries = normalizer.normalize(records)
    assert len(entries) == 3
    # Ensure ordering ascending
    assert entries[0].raw_timestamp == "2025-08-22T22:00:00"
    # Early morning adjustment
    early_entry = [e for e in entries if e.raw_timestamp == "2025-08-23T00:45:00"][0]
    assert early_entry.is_early_morning is True

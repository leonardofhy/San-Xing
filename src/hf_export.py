"""HuggingFace dataset export utilities.

Creates a local dataset (save_to_disk) from normalized DiaryEntry objects.
Deduplicates by entry_id to ensure idempotent exports across runs.
"""

from pathlib import Path
from typing import List, Dict
import shutil

try:
    from datasets import Dataset, Features, Value
except ImportError as _ie:  # pragma: no cover
    Dataset = None  # type: ignore
    Features = None  # type: ignore
    Value = None  # type: ignore

from .models import DiaryEntry
from .logger import get_logger

logger = get_logger(__name__)


def export_hf_dataset(entries: List[DiaryEntry], out_dir: Path) -> Path:
    """Export entries to a HuggingFace dataset directory.

    Args:
        entries: normalized DiaryEntry list
        out_dir: target path (will be created / overwritten)
    Returns:
        Path to saved dataset
    """
    if Dataset is None:  # pragma: no cover
        raise RuntimeError(
            "'datasets' package not available. Install optional dependency: pip install datasets"
        )

    if not entries:
        logger.warning("No entries to export; skipping HuggingFace dataset creation")
        return out_dir

    # Dedup by entry_id (keep earliest occurrence)
    dedup: Dict[str, DiaryEntry] = {}
    for e in entries:
        if e.entry_id not in dedup:
            dedup[e.entry_id] = e

    records = [
        {
            "entry_id": e.entry_id,
            "raw_timestamp": e.raw_timestamp,
            "logical_date": str(e.logical_date),
            "timestamp_epoch_ms": e.ts_epoch,
            "diary_text": e.diary_text,
            "entry_length": e.entry_length,
            "is_early_morning": e.is_early_morning,
        }
        for e in dedup.values()
    ]

    features = Features(
        {
            "entry_id": Value("string"),
            "raw_timestamp": Value("string"),
            "logical_date": Value("string"),
            "timestamp_epoch_ms": Value("int64"),
            "diary_text": Value("string"),
            "entry_length": Value("int32"),
            "is_early_morning": Value("bool"),
        }
    )

    ds = Dataset.from_list(records, features=features)
    if out_dir.exists():
        # Remove existing directory to keep atomic state (user intentionally requested path)
        shutil.rmtree(out_dir)
        shutil.rmtree(out_dir)
    ds.save_to_disk(str(out_dir))
    logger.info(
        "Exported HuggingFace dataset: %s (entries=%d, deduped=%d)",
        out_dir,
        len(entries),
        len(records),
    )
    return out_dir

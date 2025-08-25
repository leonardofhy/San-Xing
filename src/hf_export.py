"""HuggingFace dataset export utilities.

Creates a local dataset (save_to_disk) or uploads to HuggingFace Hub from normalized DiaryEntry objects.
Deduplicates by entry_id to ensure idempotent exports across runs.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import shutil

try:
    from datasets import Dataset, Features, Value
    from huggingface_hub import HfApi
except ImportError as _ie:  # pragma: no cover
    Dataset = None  # type: ignore
    Features = None  # type: ignore
    Value = None  # type: ignore
    HfApi = None  # type: ignore

from .models import DiaryEntry
from .logger import get_logger

logger = get_logger(__name__)


def export_hf_dataset(entries: List[DiaryEntry], out_dir: Path) -> Path:
    """Export entries to a HuggingFace dataset directory (local save_to_disk).

    Args:
        entries: normalized DiaryEntry list
        out_dir: target path (will be created / overwritten)
    Returns:
        Path to saved dataset
    """
    dataset = _prepare_dataset(entries)
    
    if out_dir.exists():
        # Remove existing directory to keep atomic state (user intentionally requested path)
        shutil.rmtree(out_dir)
    dataset.save_to_disk(str(out_dir))
    
    logger.info(
        "Exported HuggingFace dataset: %s (entries=%d, deduped=%d)",
        out_dir,
        len(entries),
        len(dataset),
    )
    return out_dir


def upload_to_hf_hub(
    entries: List[DiaryEntry], 
    repo_id: str, 
    hf_token: Optional[str] = None,
    private: bool = True,
    commit_message: Optional[str] = None
) -> str:
    """Upload entries to HuggingFace Hub as a dataset.

    Args:
        entries: normalized DiaryEntry list
        repo_id: HuggingFace repo ID (e.g., "username/dataset-name")
        hf_token: HuggingFace token (or from HF_TOKEN env var)
        private: Whether to create a private repository
        commit_message: Custom commit message
    Returns:
        Repository URL
    """
    if Dataset is None or HfApi is None:  # pragma: no cover
        raise RuntimeError(
            "'datasets' and 'huggingface_hub' packages not available. "
            "Install with: pip install datasets huggingface_hub"
        )

    dataset = _prepare_dataset(entries)
    
    # Use provided token or environment variable
    token = hf_token or os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HuggingFace token required. Set HF_TOKEN env var or pass hf_token parameter")

    # Generate commit message if not provided
    if not commit_message:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Update San-Xing diary dataset - {len(dataset)} entries ({timestamp})"

    try:
        # Push dataset to hub
        dataset.push_to_hub(
            repo_id=repo_id,
            token=token,
            private=private,
            commit_message=commit_message
        )
        
        repo_url = f"https://huggingface.co/datasets/{repo_id}"
        logger.info(
            "Uploaded to HuggingFace Hub: %s (entries=%d, deduped=%d)",
            repo_url,
            len(entries),
            len(dataset),
        )
        return repo_url
        
    except Exception as e:
        logger.error("Failed to upload to HuggingFace Hub: %s", str(e))
        raise


def _prepare_dataset(entries: List[DiaryEntry]) -> Dataset:
    """Prepare dataset from diary entries with deduplication.
    
    Args:
        entries: List of DiaryEntry objects
    Returns:
        HuggingFace Dataset object
    """
    if Dataset is None:  # pragma: no cover
        raise RuntimeError(
            "'datasets' package not available. Install optional dependency: pip install datasets"
        )

    if not entries:
        logger.warning("No entries to export; creating empty dataset")
        return Dataset.from_list([])

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

    return Dataset.from_list(records, features=features)

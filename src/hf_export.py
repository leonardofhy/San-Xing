"""HuggingFace dataset export utilities.

Creates a local dataset (save_to_disk) or uploads to HuggingFace Hub from normalized DiaryEntry objects.
Deduplicates by entry_id to ensure idempotent exports across runs.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any
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


def export_hf_dataset(entries: List[DiaryEntry], out_dir: Path, format: str = "parquet") -> Path:
    """Export entries to a HuggingFace dataset directory (local save_to_disk).

    Args:
        entries: normalized DiaryEntry list
        out_dir: target path (will be created / overwritten)
        format: export format ("parquet" or "json")
    Returns:
        Path to saved dataset
    """
    dataset = _prepare_dataset(entries)
    
    if out_dir.exists():
        # Remove existing directory to keep atomic state (user intentionally requested path)
        shutil.rmtree(out_dir)
    
    if format.lower() == "json":
        # Export as JSON file
        out_dir.mkdir(parents=True, exist_ok=True)
        json_file = out_dir / "data.json"
        dataset.to_json(str(json_file))
        logger.info(
            "Exported HuggingFace dataset as JSON: %s (entries=%d, deduped=%d)",
            json_file,
            len(entries),
            len(dataset),
        )
    else:
        # Default: save as dataset directory (Parquet format)
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
        # Create JSON content directly from the dataset
        import json
        import tempfile
        
        # Convert dataset to list of dictionaries  
        data_list = []
        for item in dataset:
            data_list.append(dict(item))
        
        # Create repository if it doesn't exist
        api = HfApi()
        api.create_repo(
            repo_id=repo_id,
            token=token,
            private=private,
            repo_type="dataset",
            exist_ok=True
        )
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(data_list, tmp_file, indent=2, ensure_ascii=False)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload the JSON file directly
            api.upload_file(
                path_or_fileobj=tmp_file_path,
                path_in_repo="data.json",
                repo_id=repo_id,
                token=token,
                repo_type="dataset",
                commit_message=commit_message
            )
        finally:
            # Clean up temporary file
            Path(tmp_file_path).unlink(missing_ok=True)
        
        repo_url = f"https://huggingface.co/datasets/{repo_id}"
        logger.info(
            "Uploaded to HuggingFace Hub as JSON: %s (entries=%d, deduped=%d)",
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


def upload_raw_data_to_hf_hub(
    raw_records: List[Dict[str, Any]], 
    repo_id: str, 
    hf_token: Optional[str] = None,
    private: bool = True,
    commit_message: Optional[str] = None
) -> str:
    """Upload raw records (full Google Sheets data) to HuggingFace Hub as JSON.

    Args:
        raw_records: List of raw record dictionaries from Google Sheets
        repo_id: HuggingFace repo ID (e.g., "username/dataset-name")
        hf_token: HuggingFace token (or from HF_TOKEN env var)
        private: Whether to create a private repository
        commit_message: Custom commit message
    Returns:
        Repository URL
    """
    if HfApi is None:  # pragma: no cover
        raise RuntimeError(
            "'huggingface_hub' package not available. "
            "Install with: pip install huggingface_hub"
        )

    if not raw_records:
        logger.warning("No records to upload")
        return f"https://huggingface.co/datasets/{repo_id}"

    # Use provided token or environment variable
    token = hf_token or os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HuggingFace token required. Set HF_TOKEN env var or pass hf_token parameter")

    # Generate commit message if not provided
    if not commit_message:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Update San-Xing raw dataset - {len(raw_records)} entries ({timestamp})"

    try:
        # Create repository if it doesn't exist
        api = HfApi()
        api.create_repo(
            repo_id=repo_id,
            token=token,
            private=private,
            repo_type="dataset",
            exist_ok=True
        )

        # Create temporary JSON file with raw records
        import json
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(raw_records, tmp_file, indent=2, ensure_ascii=False)
            tmp_file_path = tmp_file.name

        try:
            # Upload the raw JSON file directly
            api.upload_file(
                path_or_fileobj=tmp_file_path,
                path_in_repo="raw_data.json",
                repo_id=repo_id,
                token=token,
                repo_type="dataset",
                commit_message=commit_message
            )
        finally:
            # Clean up temporary file
            Path(tmp_file_path).unlink(missing_ok=True)

        repo_url = f"https://huggingface.co/datasets/{repo_id}"
        logger.info(
            "Uploaded raw data to HuggingFace Hub as JSON: %s (records=%d)",
            repo_url,
            len(raw_records),
        )
        return repo_url

    except Exception as e:
        logger.error("Failed to upload raw data to HuggingFace Hub: %s", str(e))
        raise

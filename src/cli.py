"""CLI entry point for the insight engine.

Enhancements:
- Optional --config TOML/JSON file (fields:
    sheet_id, sheet_url, creds, tab, days, all,
    output_dir, char_budget, api_key)
- Optional --sheet-url (extracts sheet ID from a full
    Google Sheets URL)
- Precedence: CLI > env vars > config file >
    defaults.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

try:  # Python 3.11+
    import tomllib  # type: ignore
except (ModuleNotFoundError, ImportError):  # Fallback to tomli if installed
    try:
        import tomli as tomllib  # type: ignore
    except (ModuleNotFoundError, ImportError):
        tomllib = None  # Fallback: only JSON supported

from .analyzer import LLMAnalyzer
from .config import Config
from .data_processor import DataProcessor
from .email_service import EmailService
from .ingestion import SheetIngester
from .logger import get_logger
from .normalizer import EntryNormalizer
from .persister import OutputPersister
from .window import WindowBuilder

logger = get_logger(__name__)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="三省 (SanXing) - Diary Insight Engine")

    # Required args
    parser.add_argument(
        "--spreadsheet-id",
        "--spreadsheet_id",
        dest="spreadsheet_id",
        required=False,
        help="Google Spreadsheet ID (long ID in URL; or use --sheet-url / config file)",
    )
    parser.add_argument(
        "--sheet-url", required=False, help="Full Google Sheet URL (extract ID automatically)"
    )
    parser.add_argument(
        "--creds", required=False, type=Path, help="Service account JSON path (or via --config)"
    )
    parser.add_argument("--config", type=Path, help="Path to config file (TOML or JSON)")

    # Optional args
    parser.add_argument("--tab", default="MetaLog", help="Sheet tab name")
    parser.add_argument("--days", type=int, help="Analyze last N days")
    parser.add_argument("--all", action="store_true", help="Force full history")
    parser.add_argument("--output-dir", type=Path, default=Path("./data"), help="Output directory")
    parser.add_argument("--char-budget", type=int, default=8000, help="Max chars for LLM window")
    parser.add_argument("--api-key", help="LLM API key (or set LLM_API_KEY env)")
    parser.add_argument(
        "--stream", action="store_true", help="Stream LLM tokens to stdout (if provider supports)"
    )
    parser.add_argument(
        "--no-snapshot-dedup",
        action="store_true",
        help="Disable content-hash deduplication for raw sheet snapshots (always write new file)",
    )
    parser.add_argument(
        "--export-hf",
        dest="export_hf",
        nargs="?",
        const="data/hf-dataset",
        metavar="[PATH]",
        help=(
            "Export normalized entries as a HuggingFace dataset (save_to_disk). "
            "Optional PATH (default: data/hf-dataset)."
        ),
    )
    parser.add_argument(
        "--upload-hf",
        dest="upload_hf",
        metavar="REPO_ID",
        help=(
            "Upload entries to HuggingFace Hub. Format: 'username/dataset-name'. "
            "Requires hf_token in config or HF_TOKEN environment variable."
        ),
    )
    parser.add_argument(
        "--upload-raw",
        action="store_true",
        help="Upload full raw dataset instead of filtered entries (use with --upload-hf)",
    )
    parser.add_argument(
        "--hf-public",
        action="store_true",
        help="Make repository public when uploading to HF Hub (default: private)",
    )
    parser.add_argument(
        "--hf-format",
        dest="hf_format",
        choices=["parquet", "json"],
        default="json",
        help="Format for HuggingFace dataset export (default: json)",
    )
    parser.add_argument(
        "--process-data",
        dest="process_data",
        nargs="?",
        const="data/processed",
        metavar="[PATH]",
        help=(
            "Process raw data for visualization and export to CSV/JSON. "
            "Optional PATH prefix (default: data/processed)."
        ),
    )
    parser.add_argument(
        "--email-result",
        action="store_true",
        help="Send analysis results via email (requires email configuration)",
    )
    parser.add_argument("--email-recipient", help="Email recipient address (overrides config file)")

    args = parser.parse_args()

    # Load config file if provided
    file_cfg: Dict[str, Any] = {}
    if getattr(args, "config", None):
        if not args.config.exists():
            logger.error("Config file not found: %s", args.config)
            sys.exit(1)
        try:
            if args.config.suffix.lower() in (".toml", ".tml"):
                if not tomllib:
                    logger.error("tomllib / tomli not available; install tomli or use JSON config")
                    sys.exit(1)
                with args.config.open("rb") as f:
                    file_cfg = tomllib.load(f)
            elif args.config.suffix.lower() == ".json":
                with args.config.open("r", encoding="utf-8") as f:
                    file_cfg = json.load(f)
            else:
                logger.error("Unsupported config file extension: %s", args.config.suffix)
                sys.exit(1)
            logger.info("Loaded config file: %s", args.config)
        except (json.JSONDecodeError, OSError, AttributeError) as e:  # pragma: no cover
            logger.error("Failed to parse config file: %s", e)
            sys.exit(1)

    def cfg_get(*keys, default=None):
        """Return first non-empty value among provided keys (config file or env)."""
        for k in keys:
            if k in file_cfg and file_cfg[k] not in (None, ""):
                return file_cfg[k]
            # support ENV var variants (UPPERCASE)
            env_key = k.upper()
            if env_key in os.environ and os.environ[env_key].strip():
                return os.environ[env_key].strip()
        return default

    # Derive spreadsheet id from precedence (CLI > URL > config)
    spreadsheet_id = (
        args.spreadsheet_id
        or args.sheet_url
        or cfg_get(
            "spreadsheet_id",
            "spreadsheetId",
            "spreadsheetID",
        )
    )
    # If user provided a numeric-only id, it's likely a gid (worksheet/tab), not the spreadsheet id.
    if spreadsheet_id and spreadsheet_id.isdigit():
        logger.error(
            "Provided ID '%s' looks like a gid (tab id). Use the spreadsheetId from the sheet URL.",
            spreadsheet_id,
        )
        sys.exit(10)
    if spreadsheet_id and "http" in spreadsheet_id:
        # Extract from URL
        m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", spreadsheet_id)
        if m:
            spreadsheet_id = m.group(1)
        else:
            logger.error("Unable to extract sheet ID from URL: %s", spreadsheet_id)
            sys.exit(1)

    creds_path = args.creds or cfg_get("creds", "credentials", "credentials_path")
    tab_name = (args.tab if args.tab != parser.get_default("tab") else None) or cfg_get(
        "tab", "tab_name", default=parser.get_default("tab")
    )
    if isinstance(tab_name, str):
        tab_name = tab_name.strip()
    char_budget = (
        args.char_budget
        if args.char_budget != parser.get_default("char_budget")
        else cfg_get("char_budget", "max_chars", default=parser.get_default("char_budget"))
    )
    output_dir = (
        args.output_dir
        if args.output_dir != parser.get_default("output_dir")
        else cfg_get("output_dir", "data_dir", default=str(parser.get_default("output_dir")))
    )
    api_key = args.api_key or cfg_get("api_key", "llm_api_key")
    # LLM related (currently no CLI flags; sourced from config/env)
    llm_model = cfg_get("llm_model", "model")
    llm_timeout = cfg_get("llm_timeout", "timeout")
    llm_max_retries = cfg_get("llm_max_retries", "retries")
    llm_stream = args.stream or bool(cfg_get("llm_stream", default=False))
    # HuggingFace token (from config file or environment)
    hf_token = cfg_get("hf_token")
    snapshot_dedup_cfg = cfg_get("snapshot_dedup", "SNAPSHOT_DEDUP", default=True)

    # Email configuration
    email_enabled = args.email_result or bool(cfg_get("email_enabled", default=False))
    email_recipient = args.email_recipient or cfg_get("email_recipient")

    # Days/all precedence
    days = args.days if args.days else cfg_get("days")
    force_all = args.all or bool(cfg_get("all", default=False))

    if not spreadsheet_id:
        logger.error("Missing spreadsheet ID (use --spreadsheet-id, --sheet-url, or config)")
        sys.exit(10)
    if not creds_path:
        logger.error("Missing credentials path (provide --creds or config file entry 'creds')")
        sys.exit(10)

    creds_path = Path(creds_path)

    # Configure
    config = Config()
    # Set spreadsheet id on config (attribute name SPREADSHEET_ID)
    config.SPREADSHEET_ID = spreadsheet_id
    config.CREDENTIALS_PATH = creds_path
    config.TAB_NAME = tab_name
    config.OUTPUT_DIR = Path(output_dir)
    config.RAW_DIR = config.OUTPUT_DIR / "raw"
    config.INSIGHTS_DIR = config.OUTPUT_DIR / "insights"
    config.MAX_CHAR_BUDGET = int(char_budget)
    if api_key:
        config.LLM_API_KEY = api_key
    if llm_model:
        config.LLM_MODEL = str(llm_model)
    if llm_timeout:
        try:
            config.LLM_TIMEOUT = int(llm_timeout)
        except ValueError:
            logger.warning(
                "Invalid llm_timeout value '%s' (expected int), keeping default %s",
                llm_timeout,
                config.LLM_TIMEOUT,
            )
    if llm_max_retries:
        try:
            config.LLM_MAX_RETRIES = int(llm_max_retries)
        except ValueError:
            logger.warning(
                "Invalid llm_max_retries value '%s' (expected int), keeping default %s",
                llm_max_retries,
                config.LLM_MAX_RETRIES,
            )
    config.LLM_STREAM = bool(llm_stream)
    if hf_token:
        config.HF_TOKEN = hf_token
    # Snapshot dedup (CLI override wins)
    try:
        config.SNAPSHOT_DEDUP = str(snapshot_dedup_cfg).lower() not in {"0", "false", "no", "off"}
    except (AttributeError, ValueError, TypeError):  # pragma: no cover
        pass
    if getattr(args, "no_snapshot_dedup", False):
        config.SNAPSHOT_DEDUP = False

    # Email configuration
    config.EMAIL_ENABLED = email_enabled
    if email_recipient:
        config.EMAIL_RECIPIENT = email_recipient

    # Load all email settings from config file
    email_smtp_server = cfg_get("email_smtp_server")
    email_smtp_port = cfg_get("email_smtp_port")
    email_sender = cfg_get("email_sender")
    email_password = cfg_get("email_password")
    email_sender_name = cfg_get("email_sender_name")
    email_max_retries = cfg_get("email_max_retries")

    if email_smtp_server:
        config.EMAIL_SMTP_SERVER = email_smtp_server
    if email_smtp_port:
        config.EMAIL_SMTP_PORT = int(email_smtp_port)
    if email_sender:
        config.EMAIL_SENDER = email_sender
    if email_password:
        config.EMAIL_PASSWORD = email_password
    if not email_recipient:  # Only set if not overridden by CLI
        recipient_from_config = cfg_get("email_recipient")
        if recipient_from_config:
            config.EMAIL_RECIPIENT = recipient_from_config
    if email_sender_name:
        config.EMAIL_SENDER_NAME = email_sender_name
    if email_max_retries:
        config.EMAIL_MAX_RETRIES = int(email_max_retries)

    # Recreate dirs if custom output-dir changed
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    config.INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    # Validate early to surface misconfiguration
    try:
        config.validate()
    except (ValueError, TypeError, RuntimeError) as ve:
        logger.error("Configuration invalid: %s", ve)
        sys.exit(12)

    # Generate run ID
    now = datetime.now(timezone.utc)
    run_id = (
        now.strftime("%Y%m%dT%H%M%SZ")
        + hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:12]
        + hashlib.sha256(str(now.timestamp()).encode()).hexdigest()[:4]
    )

    logger.info(
        "Starting run %s (spreadsheet_id=%s tab=%s)",
        run_id,
        spreadsheet_id,
        tab_name,
        extra={"run_id": run_id},
    )

    try:
        # Step 1: Ingest
        ingester = SheetIngester(config)
        records, _ = ingester.fetch_rows()

        if not ingester.validate_headers(records):
            logger.error("Header validation failed")
            sys.exit(10)

        # Step 2: Normalize
        normalizer = EntryNormalizer(config)
        entries = normalizer.normalize(records)

        if not entries:
            logger.warning("No valid entries found")
            sys.exit(20)

        # Step 3: Filter by date range
        if days and not force_all:
            cutoff_date = datetime.now().date() - timedelta(days=int(days))
            entries = [e for e in entries if e.logical_date >= cutoff_date]
            logger.info("Filtered to %d entries from last %s days", len(entries), days)

        # Optional: process data for visualization
        if args.process_data:
            try:
                processor = DataProcessor(config)
                processor.load_from_records(records)
                df = processor.process_all()

                if not df.empty:
                    base_path = Path(args.process_data)
                    csv_path = Path(f"{base_path}.csv")
                    json_path = Path(f"{base_path}-analysis.json")

                    processor.export_csv(csv_path)
                    processor.export_analysis_ready(json_path)

                    stats = processor.get_summary_stats()
                    logger.info(
                        "Data processing completed. Summary: %d entries, mood avg: %.1f",
                        stats.get("total_entries", 0),
                        stats.get("mood_stats", {}).get("mean", 0) or 0,
                    )
                else:
                    logger.warning("No data to process for visualization")
            except ImportError as ie:  # pragma: no cover
                logger.error("pandas not available for data processing (%s)", ie)
            except (RuntimeError, ValueError, OSError, KeyError) as e:
                logger.error("Data processing failed: %s", str(e))

        # Optional: export HuggingFace dataset (dedup by entry_id)
        if args.export_hf:
            try:
                from .hf_export import export_hf_dataset
            except ImportError as ie:  # pragma: no cover
                logger.error("datasets library not installed; add 'datasets' dependency (%s)", ie)
                sys.exit(1)
            export_hf_dataset(entries, Path(args.export_hf), format=args.hf_format)

        # Optional: upload to HuggingFace Hub
        if args.upload_hf:
            try:
                if args.upload_raw:
                    from .hf_export import upload_raw_data_to_hf_hub

                    # Upload full raw dataset (unfiltered)
                    repo_url = upload_raw_data_to_hf_hub(
                        records,  # Use all raw records
                        args.upload_hf,
                        hf_token=config.HF_TOKEN,
                        private=not args.hf_public,
                    )
                    logger.info("Successfully uploaded raw data to: %s", repo_url)
                else:
                    from .hf_export import upload_to_hf_hub

                    # Upload processed entries (filtered by days)
                    repo_url = upload_to_hf_hub(
                        entries,
                        args.upload_hf,
                        hf_token=config.HF_TOKEN,
                        private=not args.hf_public,
                    )
                    logger.info("Successfully uploaded to: %s", repo_url)
            except ImportError as ie:  # pragma: no cover
                logger.error("datasets/huggingface_hub libraries not installed (%s)", ie)
                sys.exit(1)
            except Exception as e:
                logger.error("HuggingFace upload failed: %s", str(e))
                sys.exit(1)

        # Detect anomalies
        anomalies = normalizer.detect_anomalies(entries)

        # Step 4: Window selection
        window_builder = WindowBuilder(config)
        windowed_entries, _char_count = window_builder.build_window(entries, config.MAX_CHAR_BUDGET)

        # Step 5: Analyze
        analyzer = LLMAnalyzer(config)
        insight_pack = analyzer.analyze(windowed_entries, run_id)

        # Add detected anomalies
        if anomalies:
            insight_pack.anomalies.extend(anomalies)

        # Step 6: Persist
        persister = OutputPersister(config)
        persister.save_entries_snapshot(entries, run_id)
        output_path = persister.persist(insight_pack, run_id)

        # Step 7: Email results (optional)
        logger.debug(
            "Email configuration - EMAIL_ENABLED: %s, email_enabled flag: %s",
            getattr(config, "EMAIL_ENABLED", "NOT_SET"),
            email_enabled,
        )

        if config.EMAIL_ENABLED:
            try:
                logger.info("Attempting to send email notification")
                email_service = EmailService(config)
                email_success = email_service.send_analysis_result(insight_pack, run_id)
                if email_success:
                    logger.info("Analysis results emailed successfully")
                else:
                    logger.warning("Email sending failed, but continuing")
            except Exception as e:
                logger.error("Email service error: %s", str(e))
                # Don't fail the entire process due to email issues
        else:
            logger.info(
                "Email disabled - EMAIL_ENABLED: %s", getattr(config, "EMAIL_ENABLED", "NOT_SET")
            )

        # Determine exit code
        if insight_pack.meta.get("mode") == "fallback":
            logger.warning("Run %s completed with fallback mode", run_id)
            sys.exit(30)
        else:
            logger.info(
                "Run %s completed successfully. Output: %s",
                run_id,
                output_path,
                extra={"run_id": run_id},
            )
            sys.exit(0)

    except (ValueError, OSError, RuntimeError) as e:
        logger.error("Run failed: %s", e, extra={"run_id": run_id})
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Run interrupted by user", extra={"run_id": run_id})
        sys.exit(130)


if __name__ == "__main__":
    main()

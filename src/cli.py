"""CLI entry point for the insight engine

Enhancements:
 - Optional --config TOML/JSON file (fields: sheet_id, sheet_url, creds, tab, days, all, output_dir, char_budget, api_key)
 - Optional --sheet-url (extracts sheet ID from full Google Sheets URL)
 - Precedence: CLI > env vars > config file > defaults.
"""

from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import argparse, sys, json, re, hashlib, os

try:  # Python 3.11+
    import tomllib  # type: ignore
except (ModuleNotFoundError, ImportError):  # Fallback to tomli if installed
    try:
        import tomli as tomllib  # type: ignore
    except (ModuleNotFoundError, ImportError):
        tomllib = None  # Fallback: only JSON supported
from .ingestion import SheetIngester
from .normalizer import EntryNormalizer
from .window import WindowBuilder
from .analyzer import LLMAnalyzer
from .persister import OutputPersister
from .logger import get_logger
from .config import Config

logger = get_logger(__name__)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="AI Personal Coach - Diary Insight Engine")

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
            "Provided ID '%s' looks like a gid (tab id). Supply the full spreadsheetId from the sheet URL (the long mixed-case string).",
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

    # Days/all precedence
    days = args.days if args.days else cfg_get("days")
    force_all = args.all or bool(cfg_get("all", default=False))

    if not spreadsheet_id:
        logger.error(
            "Missing spreadsheet ID (use --spreadsheet-id / --sheet-url or add spreadsheet_id|sheet_id in config)"
        )
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
    # Recreate dirs if custom output-dir changed
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    config.INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    # Validate early to surface misconfiguration
    try:
        config.validate()
    except Exception as ve:
        logger.error("Configuration invalid: %s", ve)
        sys.exit(12)

    # Generate run ID
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "_"
        + hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:4]
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
            cutoff_date = datetime.now().date() - timedelta(days=int(days) - 1)
            entries = [e for e in entries if e.logical_date >= cutoff_date]
            logger.info("Filtered to %d entries from last %s days", len(entries), days)

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

    except Exception as e:  # pragma: no cover
        logger.error("Run failed: %s", str(e), extra={"run_id": run_id})
        sys.exit(1)


if __name__ == "__main__":
    main()

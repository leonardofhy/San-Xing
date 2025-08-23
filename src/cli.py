"""CLI entry point for the insight engine"""

import argparse
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from .config import Config
from .ingestion import SheetIngester
from .normalizer import EntryNormalizer
from .window import WindowBuilder
from .analyzer import LLMAnalyzer
from .persister import OutputPersister
from .logger import get_logger

logger = get_logger(__name__)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="AI Personal Coach - Diary Insight Engine")
    
    # Required args
    parser.add_argument("--sheet-id", required=True, help="Google Sheet ID")
    parser.add_argument("--creds", required=True, type=Path, help="Service account JSON path")
    
    # Optional args
    parser.add_argument("--tab", default="MetaLog", help="Sheet tab name")
    parser.add_argument("--days", type=int, help="Analyze last N days")
    parser.add_argument("--all", action="store_true", help="Force full history")
    parser.add_argument("--output-dir", type=Path, default=Path("./data"), help="Output directory")
    parser.add_argument("--char-budget", type=int, default=8000, help="Max chars for LLM window")
    parser.add_argument("--api-key", help="LLM API key (or set LLM_API_KEY env)")
    
    args = parser.parse_args()
    
    # Configure
    config = Config()
    config.SHEET_ID = args.sheet_id
    config.CREDENTIALS_PATH = args.creds
    config.TAB_NAME = args.tab
    config.OUTPUT_DIR = args.output_dir
    config.MAX_CHAR_BUDGET = args.char_budget
    if args.api_key:
        config.LLM_API_KEY = args.api_key
    
    # Generate run ID
    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + "_" + \
             hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:4]
    
    logger.info("Starting run %s", run_id, extra={"run_id": run_id})
    
    try:
        # Step 1: Ingest
        ingester = SheetIngester(config)
        records, header_hash = ingester.fetch_rows()
        
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
        if args.days and not args.all:
            cutoff_date = datetime.now().date() - timedelta(days=args.days - 1)
            entries = [e for e in entries if e.logical_date >= cutoff_date]
            logger.info("Filtered to %d entries from last %d days", len(entries), args.days)
        
        # Detect anomalies
        anomalies = normalizer.detect_anomalies(entries)
        
        # Step 4: Window selection
        window_builder = WindowBuilder(config)
        windowed_entries, char_count = window_builder.build_window(entries, config.MAX_CHAR_BUDGET)
        
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
            logger.info("Run %s completed successfully. Output: %s", run_id, output_path)
            sys.exit(0)
        
    except Exception as e:
        logger.error("Run failed: %s", str(e), extra={"run_id": run_id})
        sys.exit(1)


if __name__ == "__main__":
    main()

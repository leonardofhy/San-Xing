# 三省 (SanXing) - Implementation

Phase 0 implementation of the diary insight engine following the SRS specifications.

## Quick Start

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set up Google Sheets API:**

   - Create a service account in Google Cloud Console
   - Download credentials JSON file
   - Share your Google Sheet with the service account email

3. **Run analysis:**

```bash
python run.py \
  --sheet-id "1CRY53JyLUXdRNDtHRCJwbPMZBo7Azhpowl15-3UigWg" \
  --creds "/path/to/service-account.json" \
  --api-key "your-llm-api-key" \
  --days 30
```

## Project Structure

```
src/
├── __init__.py          # Package info
├── config.py            # Configuration
├── models.py            # Data models (DiaryEntry, InsightPack)
├── logger.py            # Structured logging
├── ingestion.py         # Google Sheets API
├── normalizer.py        # Entry parsing & anomaly detection
├── window.py            # Character budget windowing
├── analyzer.py          # LLM integration
├── persister.py         # JSON/CSV output
└── cli.py               # CLI entry point
```

## Core Flow

```
fetch_rows() → normalize() → window() → analyze() → persist()
```

## Exit Codes

- `0`: Success
- `10`: Missing required columns
- `20`: No valid entries found
- `30`: LLM failure (fallback mode)
- `1`: Unexpected error

## Output

- `data/insights/run-{run_id}.json` - Main insight pack
- `data/insights/themes-latest.csv` - Theme summary
- `data/raw/entries-{run_id}.json` - Normalized entries snapshot

## Environment Variables

```bash
export LLM_API_KEY="sk-..."
export SHEET_ID="1ABC..."
export CREDENTIALS_PATH="/path/to/creds.json"
```

## Development

Run with local snapshot (offline):

```python
from src.ingestion import load_cached_snapshot
records = load_cached_snapshot(Path("data/raw/snapshot_20250823.json"))
```

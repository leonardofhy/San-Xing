# Diary Analysis Workflow

This document describes the complete workflow for analyzing diary entries in the 三省 (SanXing) system.

## Overview

The diary analysis workflow transforms raw Google Sheets diary data into structured insights through a 6-step pipeline:

1. **Data Ingestion** - Fetch from Google Sheets
2. **Entry Normalization** - Parse and validate entries
3. **Date Range Filtering** - Apply time windows
4. **Content Windowing** - Manage LLM token limits
5. **LLM Analysis** - Generate insights
6. **Output Persistence** - Save results

## Detailed Workflow

### Step 1: Data Ingestion (`SheetIngester`)

**Purpose**: Securely fetch diary data from Google Sheets with OAuth2 authentication.

**Process**:
- Connect to Google Sheets API using service account credentials
- Fetch all records from the specified tab (default: "MetaLog")  
- Handle duplicate headers with auto-unique fallback
- Compute header hash for change detection
- Save raw snapshot with content-based deduplication

**Key Features**:
- **Snapshot Deduplication**: Avoid writing duplicate snapshots using SHA256 content hashing
- **Error Handling**: Robust handling of API errors, worksheet not found, etc.
- **Header Validation**: Ensures required columns exist (`Timestamp`, `今天想記點什麼？`)

**Output**: List of raw records + header hash

### Step 2: Entry Normalization (`EntryNormalizer`)

**Purpose**: Convert raw sheet data into structured `DiaryEntry` objects with validation.

**Process**:
- Parse timestamps using multiple format patterns:
  - ISO 8601: `%Y-%m-%dT%H:%M:%S`
  - Sheet format: `%d/%m/%Y %H:%M:%S`
- Apply early morning logic (entries before 3 AM belong to previous day)
- Filter entries below minimum length threshold (default: 3 chars)
- Generate stable entry IDs using SHA1 hash
- Sort entries chronologically

**Key Logic**:
```python
# Early morning adjustment
is_early_morning = parsed_dt.hour < 3
logical_date = (parsed_dt.date() if not is_early_morning 
               else (parsed_dt - timedelta(days=1)).date())

# Stable ID generation
id_source = f"{raw_timestamp}{diary_text[:64]}"
entry_id = hashlib.sha1(id_source.encode()).hexdigest()
```

**Anomaly Detection**:
- **Gap Detection**: Identifies gaps > 3 days between entries
- **Length Spike Detection**: Flags entries significantly longer than recent average (>2σ)

**Output**: List of validated `DiaryEntry` objects + anomalies

### Step 3: Date Range Filtering

**Purpose**: Apply time window constraints for focused analysis.

**Options**:
- `--days N`: Analyze last N days only
- `--all`: Force full history analysis
- Default: Process all normalized entries

**Process**:
```python
if days and not force_all:
    cutoff_date = datetime.now().date() - timedelta(days=int(days) - 1)
    entries = [e for e in entries if e.logical_date >= cutoff_date]
```

### Step 4: Content Windowing (`WindowBuilder`)

**Purpose**: Select entries that fit within LLM token/character budget.

**Strategy**:
- Start from newest entries, work backwards
- Add 50 characters overhead per entry for formatting
- Stop when budget would be exceeded
- Return entries in chronological order

**Configuration**:
- Default budget: 8000 characters
- Configurable via `--char-budget` or config file

**Logic**:
```python
for entry in reversed(entries):
    entry_chars = len(entry.diary_text) + 50  # formatting overhead
    if total_chars + entry_chars > char_budget:
        break
    selected.append(entry)
```

### Step 5: LLM Analysis (`LLMAnalyzer`)

**Purpose**: Generate structured insights using LLM analysis.

**Model Configuration**:
- Default: DeepSeek Reasoner (`deepseek-reasoner`)
- Endpoint: `https://api.deepseek.com/chat/completions`
- Temperature: 0.7
- JSON response format enforced

**Prompt Strategy**:
- **Language**: Traditional Chinese instructions
- **Format**: Strict JSON schema with English keys
- **Analysis Focus**: Behavioral patterns, energy changes, emotional regulation, value alignment
- **Constraints**: Avoid generic advice, focus on observational insights

**Key Output Fields**:
- `dailySummaries`: Date-specific summaries (≤60 Chinese chars each)
- `themes`: Cross-day themes with support counts (≤5 themes, ≤12 chars each)
- `reflectiveQuestion`: Open-ended reflection prompt
- `anomalies`: Unusual patterns or deviations
- `hiddenSignals`: Subtle emotional/behavioral indicators
- `emotionalIndicators`: Mood regulation insights

**Error Handling**:
- Retry logic with exponential backoff (default: 2 retries)
- Fallback to minimal insight pack if all attempts fail
- Stream support for real-time token display

**Streaming Support**:
```python
if config.LLM_STREAM:
    # Stream tokens to stdout in real-time
    # Accumulate full response for JSON parsing
```

### Step 6: Output Persistence (`OutputPersister`)

**Purpose**: Save analysis results in multiple formats for consumption.

**Outputs**:
1. **Main Insights**: `run-{run_id}.json` - Complete analysis pack
2. **Theme Summary**: `themes-latest.csv` - Quick reference CSV
3. **Entry Snapshot**: `entries-{run_id}.json` - Normalized entries metadata

**File Structure**:
```
data/
├── raw/
│   ├── snapshot_{hash}.json      # Raw sheet data
│   ├── snapshot_latest.json      # Latest pointer
│   └── entries-{run_id}.json     # Normalized entry metadata
└── insights/
    ├── run-{run_id}.json         # Full analysis results
    └── themes-latest.csv         # Theme summary
```

## Analysis Output Schema

### InsightPack Structure
```json
{
  "meta": {
    "run_id": "20240105T143022Z...",
    "version": {
      "schema": "s1",
      "prompt": "p1", 
      "model": "deepseek-reasoner@2025-08",
      "contract": "c1"
    },
    "entriesAnalyzed": 42,
    "generatedAt": "2024-01-05T14:30:22Z"
  },
  "dailySummaries": [
    {"date": "2024-01-05", "summary": "工作壓力大但保持學習動機"}
  ],
  "themes": [
    {"label": "學習成長", "support": 8},
    {"label": "工作壓力", "support": 5}
  ],
  "reflectiveQuestion": "請回顧今天的一件小事，它代表了你想成為的人嗎?",
  "anomalies": ["3-day gap before 2024-01-03"],
  "hiddenSignals": ["疲憊感增加的模式"],
  "emotionalIndicators": ["壓力管理策略的變化"]
}
```

## Configuration Management

### Command Line Interface
```bash
# Basic usage
python -m src.cli --spreadsheet-id {ID} --creds {PATH}

# Advanced options
python -m src.cli \
    --config config.toml \
    --days 30 \
    --char-budget 10000 \
    --stream \
    --process-data data/processed \
    --export-hf data/hf-dataset
```

### Config File Support
- **TOML**: Primary format (`.toml`, `.tml`)
- **JSON**: Alternative format (`.json`)
- **Precedence**: CLI args > env vars > config file > defaults

## Integration Features

### HuggingFace Export
- Export processed entries as HF datasets
- Support for JSON/Parquet formats
- Upload to HF Hub with privacy controls
- Raw data vs processed entry options

### Data Processing
- Generate CSV/JSON for visualization
- Statistical summaries and metrics
- Pandas-based data manipulation

### Visualization Pipeline
- Export analysis-ready data
- Integration with dashboard components
- KPI calculation and trend analysis

## Error Handling & Resilience

### Network Issues
- Exponential backoff for API calls
- Graceful degradation to fallback mode
- Comprehensive error logging with context

### Data Quality
- Header validation and duplicate handling
- Timestamp parsing with multiple formats
- Entry length and content validation

### LLM Failures
- Multi-attempt retry strategy
- Fallback insight generation
- Stream recovery for partial responses

## Performance Considerations

### Memory Management
- Streaming data processing where possible
- Efficient content windowing
- Minimal data retention during processing

### Network Optimization
- Content-based snapshot deduplication
- Efficient Sheet API usage
- Optional offline mode for development

### Token Management
- Character budget enforcement
- Smart entry selection (newest first)
- Overhead calculation for formatting

## Development & Debugging

### Snapshot System
- Raw data preservation for replay
- Content hashing for change detection
- Debugging metadata retention

### Logging Strategy
- Structured JSON logging
- Configurable log levels
- Run ID tracking for correlation

### Testing Support
- Mock data generation
- API response simulation  
- Component isolation testing
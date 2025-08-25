# 三省 (SanXing)

> 曾子曰：「吾日三省吾身——為人謀而不忠乎？與朋友交而不信乎？傳不習乎？」
>
> — 《論語·學而》

> "Zengzi said: 'I examine myself three times daily: Have I been unfaithful in planning for others? Have I been untrustworthy in my dealings with friends? Have I failed to review what was taught to me?'"
>
> — _The Analects of Confucius_, Book 1: _Xue Er_ (Learning and Practice)

Automated meta‑awareness & reflective coaching pipeline combining:

1. Google Apps Script (GAS) event‑driven daily & weekly reporting (scores + LLM feedback + email delivery)
2. A Python "diary insight engine" for deeper multi‑day log analysis, anomaly detection, windowing & structured JSON insight packs

The goal: create a closed feedback loop that transforms raw personal logs (behaviors, sleep, reflections) into structured metrics, trends and actionable reflective prompts.

---

## Feature Overview

GAS Layer (Sheets Automation):

- Event‑driven daily report pipeline (REPORT_GENERATION_STARTED → ... → REPORT_GENERATION_COMPLETED)
- Weekly aggregation pipeline (parallel WEEKLY\_\* event chain)
- Behavior & Sleep scoring with version tracking (columns: behaviorScoreVersion, sleepScoreVersion, analysisVersion)
- Early‑morning rollover logic (<03:00 counts toward previous logical day)
- Automatic sheet header sync & optional batch backfill
- HTML email delivery (daily + weekly) with configurable subjects

Python Insight Engine:

- Google Sheet ingestion (service account)
- Entry normalization & anomaly detection
- **Data processing for visualization** (mood trends, sleep patterns, activity analysis)
- Character‑budget window selection for LLM context packing
- Structured Traditional Chinese LLM prompt → JSON insight pack (dailySummaries, themes, reflectiveQuestion, anomalies, hiddenSignals, emotionalIndicators)
- **HuggingFace dataset export** (local save_to_disk + Hub upload)
- Fallback mode if LLM errors (graceful exit codes)
- Versioned output artifacts (snapshots + insight JSON + visualization CSV)

Shared Concepts:

- Strict version surfacing (scoring / prompt / model) for reproducibility
- Separation of collection (Sheets) vs. analytical windows (Python) vs. coaching narrative (LLM prompts)

---

## Repository Structure (High Level)

```text
gas/                  Google Apps Script services (event bus + orchestrator + scoring + prompts)
src/                  Python insight engine (ingestion → normalize → window → analyze → persist)
data/                 Runtime outputs (raw entry snapshots, insight JSON, theme CSV)
docs/                 Architecture, design, SRS and migration notes
config.example.toml   Sample config for Python engine (copy to config.local.toml)
run.py                Convenience entry (wraps src.cli)
```

Key GAS Services:

- `ReportOrchestrator.js`: Coordinates daily & weekly chains (event registration + context passing)
- `EventBus.js`: Lightweight pub/sub with history
- `SheetAdapter.js`: Cached sheet IO + schema alignment
- `SchemaService.js`: Versioned header schema & upgrades
- `ScoreCalculatorFactory.js`: Pluggable behavior / sleep scoring versions
- `PromptBuilderService.js`: Centralized daily & weekly prompt templates
- `ApiService.js`: LLM provider abstraction (DeepSeek currently)
- `DevTools.js`: Diagnostics & backtesting helpers

Python Core Flow:

```text
fetch_rows() → normalize() → detect_anomalies() → [process_data] → build_window() → analyze() → persist()
```

Optional data processing step extracts structured metrics (mood, sleep, activities) for visualization before LLM analysis.

---

## Architecture Highlights (GAS)

Daily Event Chain Phases:

1. REPORT_GENERATION_STARTED → read source row (MetaLog)
2. DATA_READ_COMPLETED → compute behavior & sleep scores
3. SCORES_CALCULATED → build prompt
4. PROMPT_READY → LLM call
5. ANALYSIS_COMPLETED → persist structured report row
6. REPORT_SAVED → optional email
7. REPORT_GENERATION_COMPLETED (or REPORT_GENERATION_FAILED with phase + error)

Weekly Chain:

WEEKLY_REPORT_GENERATION_STARTED → WEEKLY_DATA_COLLECTED → WEEKLY_SCORES_AGGREGATED → WEEKLY_PROMPT_READY → WEEKLY_ANALYSIS_RECEIVED → email → WEEKLY_REPORT_GENERATION_COMPLETED

Extensibility: add listeners after an existing completion event, emit a new \*\_COMPLETED event (do not mutate core orchestration unnecessarily).

Batch Backfill: `generateBatchReports()` respects `CONFIG.BATCH_PROCESS` flags (date range, skip existing).

Early Morning Rule: Timestamps with hour < 3 map to previous logical date—consistently applied in daily + weekly paths.

---

## Python Insight Engine

Purpose: Deeper multi‑day synthesis beyond per‑day scoring; produces a portable JSON insight artifact.

Components:

- `ingestion.py`: Google Sheets fetch + header validation
- `normalizer.py`: Timestamp parsing, early‑morning adjustment, filtering, anomaly detection
- `data_processor.py`: Extracts structured metrics for visualization (mood, sleep, activities)
- `window.py`: Character‑budget constrained selection for prompt context
- `analyzer.py`: Prompt construction (Traditional Chinese), LLM retries, structured JSON parsing, fallback
- `persister.py`: Stores snapshots & insight pack; updates `themes-latest.csv`
- `hf_export.py`: HuggingFace dataset export (local save + Hub upload)
- `cli.py`: Rich CLI (precedence: CLI > env > config file defaults)

Exit Codes (subset): 0 success | 10 config/validation | 20 no entries | 30 LLM fallback | 1 unexpected

---

## Setup – Google Apps Script Layer

1. Create (or open) a Apps Script project bound to your Google Sheet (default source tab name: `MetaLog`).
2. Copy each file in `gas/` (or use `clasp` for push/pull automation).
3. In Script Properties set:
   - `DEEPSEEK_API_KEY`
   - `RECIPIENT_EMAIL`
4. Review & adjust `gas/Config.js` (email subjects, models, batch range, feature flags).
5. Ensure output sheets (`DailyReport`, `WeeklyReport`, `BehaviorScores`) exist or let auto‑create run (CONFIG.OUTPUT.AUTO_CREATE_SHEETS = true).
6. Add a time‑driven trigger for `runDailyReportGeneration` (and optionally weekly function if exposed).
7. (Optional) Run DevTools helpers (e.g., `DevTools.viewEventHistory()`) from the Apps Script console for validation.

Scoring Versions: When changing scoring or analysis logic, bump `CONFIG.VERSIONS.*`; sheet rows store versions for audit.

---

## Setup – Python Insight Engine

Prerequisites: Python 3.11+, service account shared with the Google Sheet, DeepSeek API key.

1. Copy `config.example.toml` → `config.local.toml` and fill values.

2. **Edit config file for HuggingFace integration (optional):**
   Add `hf_token = "hf_your_token_here"` to your `config.local.toml` file for HF Hub uploads.

3. Install deps (using uv or pip):

```bash
uv sync  # if using uv
# Or
pip install .
```

3. Run an insight generation (last 30 days):

```bash
uv run python -m src.cli --config config.local.toml --days 30
```

4. Outputs land in `data/`:
   - `data/raw/entries-<run_id>.json`
   - `data/insights/run-<run_id>.json`
   - `data/insights/themes-latest.csv`
   - `data/processed*.csv` (if using `--process-data`)
   - `data/hf-dataset/` (if using `--export-hf`)

Environment Overrides (examples):

```bash
export LLM_API_KEY="sk-..."
export SHEET_ID="<spreadsheet-id>"
export CREDENTIALS_PATH="./secrets/service_account.json"
```

Run Offline (reuse snapshot): set `OFFLINE_SNAPSHOT` in config or env + `DRY_RUN=true` to skip network calls.

---

## CLI Usage & Reference

The Python engine exposes a flexible CLI (`python -m src.cli`) with clear precedence:

Precedence: explicit CLI flag > environment variable > config file (`config.local.toml`) > internal default.

### Core Flags

```text
--spreadsheet-id / --spreadsheet_id   Google Spreadsheet ID (the long ID after /d/ in the URL)
--sheet-url                           Full Google Sheets URL (ID auto‑extracted; overrides config)
--creds PATH                          Service account JSON path
--config PATH                         Config file (TOML or JSON)
--tab NAME                            Sheet tab name (default MetaLog)
--days N                              Analyze last N days (mutually exclusive with --all)
--all                                 Force full history (ignores --days)
--output-dir PATH                     Base output directory (default ./data)
--char-budget N                       Max characters allowed in LLM context window (default 8000)
--api-key KEY                         LLM API key (alt to env LLM_API_KEY)
--stream                              Stream LLM tokens to stdout (if provider supports)
--no-snapshot-dedup                   Disable raw snapshot content-hash dedup (always create new file)
--export-hf [PATH]                    Export entries as HuggingFace dataset (default: data/hf-dataset)
--upload-hf REPO_ID                   Upload entries to HuggingFace Hub (e.g., "username/dataset")
--hf-public                           Make HuggingFace repository public (default: private)
--process-data [PATH]                 Process data for visualization (default: data/processed)
```

### Environment Variable Aliases

You may set these to avoid repeating flags (case sensitive):

```text
SHEET_ID / SPREADSHEET_ID / SPREADSHEETID          → spreadsheet ID
LLM_API_KEY / API_KEY                              → LLM key (if not using --api-key)
CREDENTIALS_PATH / CREDS / CREDENTIALS             → service account JSON path
TAB / TAB_NAME                                     → tab name
OUTPUT_DIR / DATA_DIR                              → output directory
CHAR_BUDGET / MAX_CHARS                            → character budget
LLM_MODEL / MODEL                                  → model name
LLM_TIMEOUT / TIMEOUT                              → request timeout (int seconds)
LLM_MAX_RETRIES / RETRIES                          → retry attempts (int)
LLM_STREAM                                         → truthy enables streaming
SNAPSHOT_DEDUP                                     → set false to disable snapshot deduplication
OFFLINE_SNAPSHOT                                   → path to reuse a previous snapshot (offline mode)
DRY_RUN                                            → if truthy, skip external LLM calls when offline
```

### Config File (TOML) Sample

`config.example.toml` (copy to `config.local.toml`):

```toml
spreadsheet_id = "<sheet-id>"
creds = "./secrets/service_account.json"
tab = "MetaLog"
days = 30
char_budget = 8000
llm_model = "deepseek-chat"
llm_timeout = 60
llm_max_retries = 2
output_dir = "./data"
```

Any of these can be overridden by flags or env vars—only specify what differs from defaults.

### Return / Exit Codes

| Code | Meaning                                                                                |
| ---- | -------------------------------------------------------------------------------------- |
| 0    | Success (normal insight pack)                                                          |
| 10   | Missing / invalid required inputs (spreadsheet ID, creds) or header validation failure |
| 12   | Config validation failure (`Config.validate`)                                          |
| 20   | No valid entries after normalization / filtering                                       |
| 30   | Completed in fallback (LLM error but produced degraded artifact)                       |
| 1    | Runtime error (ingestion, IO, parsing, LLM, etc.)                                      |
| 130  | User interrupted (Ctrl+C)                                                              |

Use shell conditionals to branch on fallback vs hard failure:

```bash
uv run python -m src.cli --config config.local.toml --days 7 || ec=$?
if [ "${ec}" = "30" ]; then
   echo "Fallback mode: investigate logs but artifact exists." >&2
elif [ "${ec}" != "0" ]; then
   echo "Run failed (exit ${ec})." >&2
   exit $ec
fi
```

### Typical Workflows

1. Last 7 days, explicit sheet URL & creds:

   ```bash
   uv run python -m src.cli \
     --sheet-url "https://docs.google.com/spreadsheets/d/<ID>/edit#gid=0" \
     --creds secrets/service_account.json \
     --days 7
   ```

2. Full history (ignore `days` in config):

   ```bash
   uv run python -m src.cli --config config.local.toml --all
   ```

3. Override character budget & stream tokens:

   ```bash
   uv run python -m src.cli --config config.local.toml --days 14 --char-budget 10000 --stream
   ```

4. Minimal (all via environment):

   ```bash
   export SPREADSHEET_ID="<ID>"
   export CREDENTIALS_PATH="./secrets/service_account.json"
   export LLM_API_KEY="sk-..."
   uv run python -m src.cli --days 7
   ```

5. Offline re‑analysis using an existing snapshot:

   ```bash
   export OFFLINE_SNAPSHOT="data/raw/snapshot_20250824_225142.json"
   export DRY_RUN=true
   uv run python -m src.cli --config config.local.toml --days 7
   ```

6. Export HuggingFace dataset with default path:

   ```bash
   uv run python -m src.cli --config config.local.toml --days 7 --export-hf
   ```

7. Export HuggingFace dataset to custom path:

   ```bash
   uv run python -m src.cli --config config.local.toml --days 7 --export-hf ./data/my-hf-ds
   ```

8. **Upload to HuggingFace Hub (private by default):**

   ```bash
   uv run python -m src.cli --config config.local.toml --days 30 --upload-hf "yourusername/san-xing-diary"
   ```

9. **Process data for visualization:**

   ```bash
   uv run python -m src.cli --config config.local.toml --days 30 --process-data data/my-analysis
   ```

10. **Combined workflow (data processing + HF upload + LLM analysis):**

    ```bash
    uv run python -m src.cli --config config.local.toml --days 30 \
      --process-data data/viz \
      --upload-hf "yourusername/diary" \
      --stream
    ```

### Sample Log Output (Annotated)

Below is a real run (wrapping long lines). Key phases: ingestion → normalization → window → analyze → persist.

```text
{"ts":"2025-08-24T14:51:39.838238Z","level":"info","phase":"cli","msg":"Loaded config file: config.local.toml"}
{"ts":"2025-08-24T14:51:39.838557Z","level":"info","phase":"cli","msg":"Starting run 20250824T145139Zce6de6a6b7e68d02 (spreadsheet_id=... tab=MetaLog)","run_id":"20250824T145139Zce6de6a6b7e68d02"}
{"ts":"2025-08-24T14:51:39.839142Z","level":"info","phase":"ingestion","msg":"Connected to Google Sheets API"}
{"ts":"2025-08-24T14:51:41.209804Z","level":"warning","phase":"ingestion","msg":"Duplicate header detected; applying auto-unique fallback"}
{"ts":"2025-08-24T14:51:42.074141Z","level":"info","phase":"ingestion","msg":"Fetched 125 rows, header_hash=9e46287c"}
{"ts":"2025-08-24T14:51:42.084777Z","level":"info","phase":"normalizer","msg":"Normalized 115 entries, skipped 10"}
{"ts":"2025-08-24T14:51:42.084874Z","level":"info","phase":"cli","msg":"Filtered to 6 entries from last 7 days"}
{"ts":"2025-08-24T14:51:42.084927Z","level":"info","phase":"window","msg":"Window: 6 entries, 7558 chars (budget: 8000)"}
{"ts":"2025-08-24T14:51:42.085036Z","level":"info","phase":"analyzer","msg":"Starting streaming LLM call (model=deepseek-chat)"}
... (insight JSON printed / or saved) ...
{"ts":"2025-08-24T14:52:15.445200Z","level":"info","phase":"cli","msg":"Run 20250824T145139Zce6de6a6b7e68d02 completed successfully. Output: data/insights/run-20250824T145139Zce6de6a6b7e68d02.json","run_id":"20250824T145139Zce6de6a6b7e68d02"}
```

Phases map to modules: ingestion (`SheetIngester`), normalizer (`EntryNormalizer`), window (`WindowBuilder`), analyzer (`LLMAnalyzer`), persister (`OutputPersister`). All log lines are structured JSON (safe for machine parsing). Warnings (e.g., duplicate headers) indicate recoverable issues.

### Output Artifacts

```text
data/raw/entries-<run_id>.json      # Full normalized entries used for analysis
data/insights/run-<run_id>.json     # Insight pack JSON (themes, summaries, question, anomalies)
data/insights/themes-latest.csv     # Rolling theme counts (overwritten each run)
data/raw/snapshot_*.json            # Raw pre-normalization snapshot (if enabled)
data/processed*.csv                 # Structured data for visualization (if --process-data used)
data/processed*-analysis.json       # Analysis-ready data with summary statistics
data/hf-dataset/                    # Local HuggingFace dataset (if --export-hf used)
```

Insight JSON includes: `dailySummaries`, `themes`, `reflectiveQuestion`, `anomalies`, `hiddenSignals`, `emotionalIndicators`, plus `meta` with version / run provenance.

### Troubleshooting Quick Tips

| Symptom                  | Likely Cause                    | Action                                         |
| ------------------------ | ------------------------------- | ---------------------------------------------- |
| Exit 10 (missing ID)     | Wrong flag / env not set        | Provide `--sheet-url` or `--spreadsheet-id`    |
| Exit 10 (header fail)    | Sheet structure changed         | Align headers in GAS layer / SchemaService     |
| Exit 20                  | Filter removed all entries      | Increase `--days` or remove filters            |
| Exit 30                  | LLM transient failure           | Artifact usable; inspect logs & consider retry |
| Slow analysis            | Large char budget               | Reduce `--char-budget` or shorten window       |
| Duplicate header warning | Sheet has repeated column names | Rename in sheet; system auto-uniques for run   |

---

---

## Versioning & Reproducibility

GAS: `CONFIG.VERSIONS.{BEHAVIOR_SCORE,SLEEP_SCORE,ANALYSIS}` + per‑row columns preserve provenance.
Python: `InsightPack.meta.version` stores `schema`, `prompt`, `model`, `contract` plus `run_id` & `generatedAt`.
Always bump versions when changing scoring formulas, prompt contract, or model class.

---

## Data & Schema Notes

Never hardcode header strings elsewhere; use `SchemaService`. To add a column: register via `SchemaService.addField(...)`, set new version, update `CONFIG.SCHEMA_VERSIONS`, let `SheetAdapter` sync.

---

## Language

Prompts & outputs (coaching narration) are currently in Traditional Chinese. Internationalization is planned (central prompt templates already isolated in `PromptBuilderService` & `analyzer.py`).

---

## Privacy & Risk Disclaimer

1. Personal data (behaviors, mood, sleep patterns, free‑form notes, etc.) is transmitted to a third‑party LLM provider (currently DeepSeek) to generate analysis.
2. **HuggingFace uploads:** Datasets are private by default when uploaded to HF Hub. Use `--hf-public` flag only if you want to make your personal diary data public.
3. Review provider policies before enabling automated calls. You are solely responsible for compliance & data governance.
4. Do not include highly sensitive information in your source sheet unless you accept associated risks. Consider redacting or hashing sensitive fields.
5. Keep credentials (service account JSON, API keys, HF tokens) out of version control (`secrets/` and `config.local.toml` are git‑ignored).

---

## Testing

Python tests (pytest) cover prompt structure, model behaviors, normalization logic, window sizing, and basic DeepSeek API reachability (requires `DEEPSEEK_API_KEY`). Run:

```bash
uv run pytest -q
```

---

## Roadmap (Excerpt)

Planned: multi‑language prompt packs, richer weekly metrics (trends beyond linear deltas), standardized Google Form template, advanced scoring versions & backtesting dashboards, pluggable provider abstraction for Python engine.

---

## Contributions

Small, focused PRs welcome: prefer adding new event listeners over modifying orchestrator core. Include rationale + version bumps where logic changes output semantics.

---

## License

MIT License – see [LICENSE](./LICENSE).

---

## Quick Reference Cheat Sheet

GAS Daily Chain: REPORT_GENERATION_STARTED → DATA_READ_COMPLETED → SCORES_CALCULATED → PROMPT_READY → ANALYSIS_COMPLETED → REPORT_SAVED → REPORT_GENERATION_COMPLETED

Python Run: ingestion → normalization → [data processing] → window → analyze (LLM) → persist (insight JSON + CSV + snapshot)

Early Morning Rule: hour < 3 ⇒ logical date = previous day (consistent across layers).

Edit Prompts: GAS (`PromptBuilderService`), Python (`analyzer._build_prompt`).

Score Logic: Register new version in `ScoreCalculatorFactory`, then set active version & bump `CONFIG.VERSIONS`.

Batch Backfill: toggle & configure in `CONFIG.BATCH_PROCESS`.

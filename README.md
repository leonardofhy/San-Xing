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
- Character‑budget window selection for LLM context packing
- Structured Traditional Chinese LLM prompt → JSON insight pack (dailySummaries, themes, reflectiveQuestion, anomalies, hiddenSignals, emotionalIndicators)
- Fallback mode if LLM errors (graceful exit codes)
- Versioned output artifacts (snapshots + insight JSON)

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
fetch_rows() → normalize() → detect_anomalies() → build_window() → analyze() → persist()
```

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
- `window.py`: Character‑budget constrained selection for prompt context
- `analyzer.py`: Prompt construction (Traditional Chinese), LLM retries, structured JSON parsing, fallback
- `persister.py`: Stores snapshots & insight pack; updates `themes-latest.csv`
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

1. Install deps (using uv or pip):

```bash
uv sync  # if using uv
# Or
pip install .
```

1. Run an insight generation (last 30 days):

```bash
uv run python -m src.cli --config config.local.toml --days 30
```

1. Outputs land in `data/`:
   - `data/raw/entries-<run_id>.json`
   - `data/insights/run-<run_id>.json`
   - `data/insights/themes-latest.csv`

Environment Overrides (examples):

```bash
export LLM_API_KEY="sk-..."
export SHEET_ID="<spreadsheet-id>"
export CREDENTIALS_PATH="./secrets/service_account.json"
```

Run Offline (reuse snapshot): set `OFFLINE_SNAPSHOT` in config or env + `DRY_RUN=true` to skip network calls.

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
2. Review provider policies before enabling automated calls. You are solely responsible for compliance & data governance.
3. Do not include highly sensitive information in your source sheet unless you accept associated risks. Consider redacting or hashing sensitive fields.
4. Keep credentials (service account JSON, API keys) out of version control (`secrets/` is git‑ignored).

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

Python Run: ingestion → normalization → window → analyze (LLM) → persist (insight JSON + CSV + snapshot)

Early Morning Rule: hour < 3 ⇒ logical date = previous day (consistent across layers).

Edit Prompts: GAS (`PromptBuilderService`), Python (`analyzer._build_prompt`).

Score Logic: Register new version in `ScoreCalculatorFactory`, then set active version & bump `CONFIG.VERSIONS`.

Batch Backfill: toggle & configure in `CONFIG.BATCH_PROCESS`.

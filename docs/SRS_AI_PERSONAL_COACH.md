# Software Requirements Specification (SRS)
AI Personal Coach – Diary Insight Engine (Phase 0)

Status: Draft (implementation-focused)
Version: 0.2.0
Owner: TBD
Last Updated: 2025-08-23
Repo (rename target): `ai-personal-coach`

---
## 1. Introduction
### 1.1 Purpose
Deliver a minimal, deterministic pipeline that reads diary text from a Google Sheet and produces a structured JSON “insight pack” with summaries, simple themes, a reflective question, and metadata – resilient even if the LLM fails.

### 1.2 Scope
MUST (Phase 0):

1. Read columns `Timestamp`, `今天想記點什麼？` from sheet tab `MetaLog`.
2. Parse & normalize timestamps; apply early‑morning date adjustment (<03:00 -> logical_date = previous day).
3. Filter + order entries chronologically.
4. Build one prompt window (recent N entries or full history) within size limits.
5. Single LLM call → parse JSON → validate → persist output.
6. On LLM failure: emit fallback JSON skeleton (no crash, exit code signals degraded mode).
7. Persist deterministic run metadata (hash, versions, counts).

LATER (not in Phase 0): weekly aggregation, multi-user, SQLite store, tone shift detection, vector embeddings, knowledge graph, adaptive coaching plans.

### 1.3 Stakeholders

| Role | Objective | Primary Concerns |
|------|----------|------------------|
| End User | Introspective insight | Privacy, clarity |
| Maintainer | Stable ops | Simplicity, debuggability |
| Researcher | Prompt/model iteration | Version traceability |
| Integrator | Consume JSON | Contract stability |

### 1.4 Definitions

| Term | Definition |
|------|-----------|
| MetaLog | Source Google Sheet tab (inputs) |
| Diary Field | Column `今天想記點什麼？` |
| Insight Pack | Output JSON contract (see §9) |
| Entry | Parsed row with valid timestamp & non-empty diary text |
| Logical Date | Adjusted date (early‑morning rule) |

### 1.5 References

- Original architecture docs in `/docs/` (legacy behavior/sleep concepts — not core for Phase 0).
- Google Sheets API & gspread library docs.

### 1.6 Document Overview

Focuses on the core ingestion→analysis→output loop; omits speculative features.

---
 
## 2. Overall Description

### 2.1 Core Loop (Authoritative)

```text
fetch_rows() -> normalize() -> window() -> analyze() -> persist()
```

No branching. One LLM call. Fallback JSON if failure.

### 2.2 Components (Phase 0 Only)

| Component | Responsibility | Out-of-Scope Items Explicitly Dropped |
|-----------|----------------|---------------------------------------|
| Ingestion | Sheet read, header validation | Caching layers beyond simple file snapshot |
| Normalizer | Timestamp parse, early-morning adjust, filtering | Linguistic segmentation, language detection |
| Window Builder | Select subset respecting size limit | Multi-window batching |
| Analyzer | Build prompt, call LLM, validate JSON | Multi-model ensemble, embeddings |
| Persister | Write JSON + log, optional CSV summary | DB / SQLite |
| Version Registry | Single struct tracking versions | Distributed feature flags |

### 2.3 Functional Summary

| Step | Deterministic Rules |
|------|--------------------|
| Parse | Timestamp patterns: (1) ISO 8601; (2) `dd/MM/yyyy HH:mm:ss`; else reject row |
| Early Morning | if hour < 3 → logical_date = date - 1 (same TZ) |
| Filter | Keep if diary_text trimmed length ≥ 3 |
| Ordering | Sort by parsed timestamp ascending (stable) |
| Window | If `--days N` → entries with logical_date >= today-N+1; else full history; THEN truncate to char budget (default 8000 chars) from newest backwards, re-sort ascending |
| Prompt | Template p1; deterministic insertion order of entries |
| LLM | One call; timeout X sec (config). Retry once on network or ≥500 HTTP. |
| Validation | Strict JSON parse; required keys present or fallback |
| Persist | Write `insights/run-<run_id>.json` + summary CSV |

### 2.4 User Classes

| User | Need |
|------|------|
| Individual | Simple insights |
| Maintainer | Fast failure diagnosis |
| Researcher | Prompt iteration reproducibility |

### 2.5 Operating Environment

Python 3.11+, local CLI execution. Google Sheets via `gspread` + service account. One external LLM HTTPS call.

### 2.6 Constraints

| Constraint | Mitigation |
|-----------|-----------|
| Sheets quota | Single bulk read |
| LLM quota/cost | One call / run |
| Privacy | Optional redaction pre-pass |
| Mixed language | Treat as opaque text (Phase 0) |

### 2.7 Assumptions

| ID | Assumption | Risk |
|----|-----------|------|
| A1 | Headers unchanged | Abort run |
| A2 | Valid service account | Abort run |
| A3 | Parseable timestamps | Skipped rows reduce coverage |
| A4 | LLM reachable | Fallback mode |
| A5 | ≥5 distinct days | Sparse themes |

---
 
## 3. System Features (Phase 0)

### 3.1 Data Ingestion

| Item | Description |
|------|-------------|
| Trigger | Manual CLI or scheduled cron/job |
| Inputs | Sheet ID, tab name (`MetaLog`), credentials path |
| Process | Authorize, fetch all rows, select required columns, drop empties |
| Outputs | Raw entries list (JSON in memory), optional cached snapshot file |
| Errors | Network, credential, 404 tab not found |
| Version Hooks | Ingestion schema version (fields set) |

### 3.2 Chronological Ordering & Normalization

| Item | Description |
|------|-------------|
| Inputs | Raw entry rows |
| Rules | Parse timestamp (dd/MM/yyyy HH:mm:ss pattern variants), unify to ISO 8601; retain original string |
| Early Morning Policy | If hour < 3, keep raw timestamp but mark `logical_date = date - 1` (flag) |
| Outputs | Normalized entries array |
| Edge Cases | Duplicate timestamps, malformed timestamps, timezone drift |

### 3.3 Diary Text Preprocessing

| Aspect | Details |
|--------|---------|
| Steps | Trim, normalize whitespace, unify punctuation spacing, optionally segment long text |
| Language Handling | Assume Traditional Chinese primary; leave as-is (no destructive stemming) |
| Filtering | Discard entries under configurable min character threshold (e.g. <3 chars) |

### 3.4 Insight Generation (LLM Core)

| Component | Description |
|-----------|------------|
| Prompt Template | Includes rolling window of recent entries (configurable N days or tokens) + analysis directives |
| LLM Tasks | Theme extraction, hidden signals, emotional tone classification (qualitative), growth signals, reflective question |
| Output Contract | JSON with keys: `dailySummaries[]`, `themes[]`, `hiddenSignals[]`, `emotionalIndicators[]`, `anomalies[]`, `reflectiveQuestion`, `meta` |
| Validation | JSON parse; fallback minimal structure on parse failure |
| Retry | Up to 2 (exponential backoff) for transient errors |

### 3.5 Lightweight Anomalies (Limited)

| Anomaly | Rule |
|---------|------|
| Gap | gap_days > configured threshold (default 3) |
| Length Spike | length > mean(last 30) + 2 * stdev(last 30) |

### 3.6 Output Persistence

| Output | Format | Notes |
|--------|--------|-------|
| Insight Pack | JSON file (timestamped) | Core deliverable |
| Summary Table | CSV (themes + frequencies) | For quick review |
| SQLite (optional) | Tables: entries, runs, themes | Future extensibility |

### 3.7 CLI (Single Command)

`analyze` does everything (ingest if cache stale, then process). Flags: `--sheet-id`, `--creds`, `--tab MetaLog`, `--days N` OR `--all`, `--output-dir`, `--char-budget`, `--redact-config`.

### 3.8 Version & Traceability

Single struct persisted verbatim:

```json
{
  "version": {
    "schema": "s1",
    "prompt": "p1",
    "model": "deepseek-reasoner@2025-08",
    "contract": "c1"
  }
}
```

Increment field only when a breaking or semantic change occurs.

---
 
## 4. External Interface Requirements

### 4.1 Google Sheet Interface

| Sheet | Required Columns | Optional Future |
|-------|------------------|-----------------|
| MetaLog | Timestamp, 今天想記點什麼？ | mood, energy, behaviors |

Column Stability Strategy: store header hash & warn if changed.

### 4.2 LLM API Interface

| Field | Purpose | Example |
|-------|---------|---------|
| endpoint | Chat/completions JSON | <https://api.deepseek.com/chat/completions> |
| auth | Bearer token | env / config |
| messages | System + user prompt | array |
| response_format | Force JSON object | {"type":"json_object"} |

### 4.3 Local Storage Interface

| Artifact | Path Pattern | Rotation |
|----------|--------------|----------|
| Raw Snapshot | data/raw/YYYYMMDD.json | Keep last 30 |
| Insight Pack | data/insights/run-`<timestamp>`.json | Keep all (review later) |
| Theme CSV | data/insights/themes-latest.csv | Overwrite |

---
 
## 5. Nonfunctional Requirements

| Category | Requirement | Target |
|----------|------------|--------|
| Performance | 365 entries end-to-end w/o LLM < 2s | Local laptop |
| LLM Calls | Exactly 1 / run (Phase 0) | Enforced |
| Reliability | Fallback JSON on any LLM failure | 100% |
| Maintainability | Max module size | ≤300 LOC |
| Logging | Structured lines | phases + errors |
| Privacy | Redaction optional & logged | deterministic |

---
 
## 6. Data Requirements

### 6.1 Core Fields

| Field | Type | Notes |
|-------|------|-------|
| raw_timestamp | string | Original sheet cell |
| timestamp | datetime | Parsed UTC / local aware |
| ts_epoch | int | Milliseconds epoch |
| logical_date | date | After early-morning adjustment |
| diary_text | string | Raw diary content |
| entry_length | int | len(diary_text) |
| entry_id | string | sha1(raw_timestamp + diary_text[:64]) |

### 6.2 Insight Fields (Required vs Optional)

| Field | Req | Description |
|-------|-----|-------------|
| meta | Yes | version, run_id, entriesAnalyzed, generatedAt |
| dailySummaries | Yes | [{date, summary}] (may be empty array) |
| themes | Yes | Simple list: [{label, support}] |
| reflectiveQuestion | Yes | Non-empty string (fallback default question) |
| anomalies | No | Gap & length spike notes |
| hiddenSignals | No | Future (omit Phase 0 if absent) |
| emotionalIndicators | No | Future placeholder |

### 6.3 Data Quality Rules

1. Reject row if timestamp parse fails → log `warn`.
2. Trim diary text; if length < 3 → skip.
3. Distinct logical_date count < 2 → still produce output (themes may be empty).
4. Early-morning adjustment logged with flag.

---
 
## 7. Versioning & Migration

Single version block (§3.8). Migration script (later) re-runs analyzer with new prompt/model to regenerate insight packs; not in Phase 0 scope.

---
 
## 8. Error Handling & Logging

| Failure | Handling | Exit Code |
|---------|----------|-----------|
| Missing column | Abort before analysis | 10 |
| No valid entries | Emit empty insight pack | 20 |
| LLM failure (network/parse) | Fallback pack (note in meta) | 30 |
| Success | Normal pack | 0 |

Fallback JSON (minimum):

```json
{
  "meta": { "run_id": "...", "version": {"schema":"s1","prompt":"p1","model":"deepseek-reasoner@2025-08","contract":"c1"}, "entriesAnalyzed": 0, "generatedAt": "ISO", "mode": "fallback" },
  "dailySummaries": [],
  "themes": [],
  "reflectiveQuestion": "請回顧今天的一件小事，它代表了你想成為的人嗎?"
}
```

Log line format (JSON): `{ "ts": ISO, "phase": "ingest|analyze|persist", "level": "info|warn|error", "run_id": "...", "msg": "...", "meta": {...} }`.

---
 
## 9. Security & Privacy

| Concern | Mitigation |
|---------|-----------|
| PII exposure to LLM | Configurable redaction pass (regex list); produce redaction log |
| Credential leakage | Service account path not committed; documented .gitignore |
| Accidental wider sharing | Local file output only (Phase 0) |

---
 
## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Header rename | Abort run | Strict header check + clear error |
| LLM unavailability | Missing insights | Fallback JSON |
| Redaction misconfig | Leak sensitive text | Dry-run mode + redaction log diff |
| Token overrun | Cost spike | Char budget pre-truncation |

---
 
## 11. Future Enhancements (Short List)

1. Weekly/monthly aggregation.
2. Local model (Ollama) fallback.
3. Extended anomalies (tone shift) once tone inference reliable.

---
 
## 12. Appendices

### 12.1 Prompt Skeleton (p1)

```text
System: You are an AI personal coach. Return ONLY valid JSON with keys: dailySummaries, themes, reflectiveQuestion, meta (and optionally anomalies).
User Content:
<ENTRIES>
Formatting Rules:
1. JSON only.
2. themes max 5 items; labels ≤ 12 chars.
3. reflectiveQuestion: open-ended single question.
```

### 12.2 Output Example

```json
{
  "meta": {"run_id":"20250823T010203Z_ab12","version":{"schema":"s1","prompt":"p1","model":"deepseek-reasoner@2025-08","contract":"c1"},"entriesAnalyzed":42,"generatedAt":"2025-08-23T01:02:03Z"},
  "dailySummaries": [{"date":"2025-08-20","summary":"聚焦學習但晚間分心。"}],
  "themes": [{"label":"專注","support":4},{"label":"拖延","support":3}],
  "reflectiveQuestion": "哪個夜間分心觸發最值得本週優先處理?",
  "anomalies": ["3-day gap before 2025-08-18"]
}
```

### 12.3 CLI Flags (Phase 0)

| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| --sheet-id | Yes | Google Sheet ID | - |
| --creds | Yes | Service account JSON path | - |
| --tab | No | Sheet tab name | MetaLog |
| --days | No | Analyze last N days | (full) |
| --all | No | Force full history | false |
| --output-dir | No | Output base dir | ./data |
| --char-budget | No | Max chars for window | 8000 |
| --redact-config | No | JSON file with regex rules | (none) |

---
 
## 13. Change Log

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 0.1.0 | 2025-08-23 | TBD | Initial SRS draft |
| 0.2.0 | 2025-08-23 | TBD | Lean refactor; core loop, consolidated versioning, fallback JSON, exit codes |

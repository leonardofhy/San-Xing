# SRS Addendum: Sleep-Centric Metrics (Phase m1)

Status: Draft (pre-implementation)
Addendum Version: m1.1
Related Base SRS: `SRS_SanXing.md` (Phase 0, v0.2.0)
Last Updated: 2025-08-24
Owner: TBD

## 1. Purpose

Introduce deterministic, non-LLM sleep metrics (and scaffold for later weight metrics) to enrich insight context while remaining backward-compatible with the Phase 0 contract. Emphasis order: Sleep >>> Weight > Others. No change to existing required InsightPack fields.

## 2. Scope (m1)

IN:

1. Parse per-day sleep inputs: bedtime (`昨晚實際入睡時間`), wake time (`今天實際起床時間`).
2. Compute sleep_duration_minutes, sleep_duration_hours, sleep_midpoint_minutes, and normalized fields.
3. Persist daily sleep metrics as CSV + JSON artifacts.
4. Generate optional summary `meta.sleepSummary` (latest duration, 7d average if available, midpoint drift).
5. Provide plotting scaffold (sleep schedule & duration trend) — optional CLI flag.

DEFERRED (future m2+):

- Weight parsing & trend (deltas, EMA).
- Correlation matrix (sleep ↔ mood / weight / diary length).
- Consequence / influence visualization network.
- Multi-user segmentation.

NON-GOALS (m1):

- Altering LLM prompt or adding sleep-derived directives.
- Introducing DB or complex caching.
- Statistical sleep quality inference (we only handle duration & timing).

## 3. Data Inputs

Sheet tab: `MetaLog` (unchanged).

Required existing columns remain: `Timestamp`, `今天想記點什麼？`.

Optional columns consumed if present:

- `昨晚實際入睡時間` (string, formats: HHMM, HMM, HH:MM, H:MM).
- `今天實際起床時間` (string, same formats as above).
- (For later) `體重紀錄` (float), `今日整體心情感受` (int).

## 4. Parsing & Rules

### 4.1 Time Parsing

Accepted formats examples → minutes after midnight:

- "0245" → 2\*60+45 = 165
- "945" → 9\*60+45 = 585
- "2:45" → 165
- "23:07" → 1387

Invalid / empty → None (row still usable for diary but excluded from sleep metrics).

### 4.2 Duration Logic

**Key Interpretation**:

- `昨晚實際入睡時間` ("last night's actual sleep time") refers to when the person went to sleep the night before the diary entry's date
- `今天實際起床時間` ("today's actual wake time") refers to when they woke up on the diary entry's date

For each logical_date (post early-morning adjustment already handled in normalizer):

**Sleep Period Assignment**:

- The sleep period (bedtime → wake time) is associated with the wake date (logical_date)
- Example: Entry on Aug 23 with bedtime "0245" and wake "0945" means they slept from 2:45 AM to 9:45 AM on Aug 23

**Duration Calculation**:

- If bed_minutes <= wake_minutes → duration = wake - bed (typical case, e.g., 0245 to 0945)
- If bed_minutes > wake_minutes → duration = (1440 - bed_minutes) + wake_minutes (rare edge case: bedtime like "2330" with wake "0730", crossing midnight)

**Sleep midpoint** (minutes): (bed_minutes + duration/2) % 1440.

**Store hours** with two decimal precision: duration_hours = round(duration/60, 2).

### 4.3 Edge Cases

- Only one of bed or wake present → skip duration & midpoint for that date.
- Unrealistic duration (< 60 or > 900 minutes) → log warning but still store with `anomaly_flag: "unusual_duration"`.
- Multiple entries same logical_date: choose the earliest timestamp entry (by Timestamp field); log warning if multiple entries exist.
- Negative or zero duration → skip with warning.

## 5. Output Artifacts

Paths (relative to `data/metrics/`):

- `sleep-run-<run_id>.json`:

  ```json
  {
    "run_id": "...",
    "metrics_version": "m1",
    "generated_at": "ISO8601",
    "rows": [
      {
        "date": "YYYY-MM-DD",
        "bed_minutes": 165,
        "wake_minutes": 585,
        "duration_minutes": 420,
        "duration_hours": 7.0,
        "midpoint_minutes": 375,
        "anomaly_flag": null
      }
    ]
  }
  ```
  
- `sleep-latest.csv`: Overwritten each run; columns: date, bed_minutes, wake_minutes, duration_minutes, duration_hours, midpoint_minutes, anomaly_flag.
- (Optional when plotting) `plots/sleep_schedule.png`, `plots/sleep_duration.png`.

Retention: keep all per-run JSON; single rolling CSV + plots.

## 6. InsightPack Integration

Optional field appended (not required by existing consumers):

```json
meta.sleepSummary = {
  "latestDate": "YYYY-MM-DD",
  "latestDurationH": 7.25,
  "avg7dDurationH": 7.10,        // present only if >=3 days of valid data in last 7 days
  "midpointTrendMin": +15,        // difference (minutes) between latest midpoint and mean midpoint of prior 3 valid days (if >=3 prior)
  "validDays": 9,
  "metricsVersion": "m1"
}
```

Absence indicates metrics feature disabled or no valid sleep data.

## 7. Versioning

Add key: `VERSION.metrics = "m1"` in config version block.

Rules to bump (m2, m3...):

- Changing duration formula semantics.
- Adding new persisted columns.
- Introducing correlations into InsightPack.

Prompt version unaffected in m1.

## 8. CLI Extensions

New flags (backward-compatible):

- `--with-metrics` (default false) → compute & persist metrics.
- `--with-plots` (implies `--with-metrics`) → also render plots (requires matplotlib; if missing, log warn & skip).

Failure to parse times never aborts run; metrics simply partial.

## 9. Logging & Errors

Structured log phase: `metrics`.

Events:

- info: metrics_computed (counts)
- warn: conflicting_sleep_entries (date, entries_count)
- warn: invalid_sleep_duration (date, duration, reason)
- warn: anomaly_detected (date, type, value)
- error: unexpected exception (still non-fatal)

No new exit codes (metrics never changes run exit status).

## 10. Performance & Complexity

Target: O(N) over entries; memory negligible (<= a few KB per day). Plotting may add ~100ms overhead for <1 year of data.

## 11. Security & Privacy

No additional external calls; metrics derived locally. Plots contain only derived times/dates (no diary text).

## 12. Testing Requirements

Unit tests for:

- Time parsing edge cases (various formats, invalid inputs)
- Duration calculation (same-day, crossing midnight)
- Midpoint calculation
- Edge cases (missing data, anomalies)
- CSV/JSON output format validation

Integration tests for:

- End-to-end metrics generation with sample data
- Plot generation (if matplotlib available)
- InsightPack integration

## 13. Future (m2 Preview)

- Weight integration: weight_kg, delta_prev, ema7.
- Correlations: Pearson sleep_duration vs mood, vs weight (if >=5 overlapping days).
- Consequence plot (thresholded correlation graph).
- Sleep quality estimation from duration + consistency.

## 14. Acceptance Criteria (m1)

- Running analyze with `--with-metrics` generates `sleep-run-<id>.json` & `sleep-latest.csv` with >=1 row if valid bed/wake data exists.
- Added `VERSION.metrics` appears in persisted run InsightPack meta (even if no sleepSummary due to no data).
- If at least 3 valid days in last 7, avg7dDurationH present; else omitted.
- No modification to existing required InsightPack keys.
- Tests pass for all time parsing and duration calculation scenarios.

## 15. Example Data Flow

Input (from snapshot):

```json
{
  "Timestamp": "23/08/2025 00:38:46",
  "昨晚實際入睡時間": "0245",
  "今天實際起床時間": "0945",
  ...
}
```

Processed (logical_date after early-morning adjustment if needed):

- Date: 2025-08-22 (due to 00:38 timestamp → logical_date = prev day)
- Bed: 165 minutes (2:45 AM)
- Wake: 585 minutes (9:45 AM)
- Duration: 420 minutes (7.0 hours)
- Midpoint: 375 minutes (6:15 AM)

## 16. Change Log

| Addendum Version | Date       | Summary                                         |
| ---------------- | ---------- | ----------------------------------------------- |
| m1 (draft)       | 2025-08-24 | Initial sleep metrics specification             |
| m1.1             | 2025-08-24 | Clarified bedtime interpretation and edge cases |

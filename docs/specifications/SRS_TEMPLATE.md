# Software Requirements Specification (SRS)

Meta-Awareness System (Google Apps Script Event-Driven Reporting)

Status: Draft / Template  
Version: 0.1.0 (semantic version of this SRS)  
Owner: TBD  
Last Updated: YYYY-MM-DD

---

## 1. Introduction

### 1.1 Purpose
 
_Describe why this system exists and what this SRS covers._

### 1.2 Scope
 
_Define the product boundary: inputs (Google Sheet MetaLog), outputs (Daily/Weekly reports, emails), exclusions._

### 1.3 Stakeholders

| Role | Interest / Objective | Primary Concerns |
|------|----------------------|------------------|
| End User | | |
| System Maintainer | | |
| LLM Provider (3rd-party) | | |
| Future Integrators | | |

### 1.4 Definitions / Acronyms

| Term | Definition |
|------|------------|
| MetaLog | Daily input sheet (raw entries) |
| DailyReport | Daily output sheet (persisted analysis) |
| WeeklyReport | Weekly output sheet (aggregate analysis) |
| EventBus | Central publish/subscribe event system |
| LLM | Large Language Model |

### 1.5 References

- `docs/architecture-v2-quick-reference.md`
- `docs/daily-report-architecture-v2.md`
- `docs/architecture-v2-issue-resolution.md`
- _Add any external specs / API docs_

### 1.6 Document Overview
 
_Brief outline of the sections that follow._

---
 
## 2. Overall Description

### 2.1 Product Perspective
 
_Context diagram or bullet points: Google Apps Script, Sheets, Email, LLM API._

### 2.2 Product Functions (High-Level)

- Ingest structured & free-form daily entries from `MetaLog`.
- Compute behavior & sleep scores (versioned calculators).
- Build prompt(s) using template versions (daily/weekly).
- Call external LLM provider (DeepSeek by default).
- Persist structured analysis to output sheets.
- Send HTML summary emails.

### 2.3 User Classes & Characteristics

| User Class | Description | Access Needs |
|------------|-------------|-------------|
| Individual User | | |
| Admin / Maintainer | | |
| Developer | | |

### 2.4 Operating Environment

- Platform: Google Apps Script (V8 runtime)
- Data Store: Google Sheets (same spreadsheet)
- External APIs: DeepSeek REST (JSON), future local LLM
- Time Zone: CONFIG.TIME_ZONE (default Asia/Taipei)

### 2.5 Design & Implementation Constraints

- GAS execution quotas and time limits
- External API rate limits
- No persistent DB beyond Sheets
- Privacy concerns (personal data leaves Google when calling LLM)

### 2.6 Assumptions & Dependencies

| ID | Assumption | Impact if False |
|----|------------|-----------------|
| A1 | Sheet headers stay versioned via SchemaService | Parsing breaks / reports fail |
| A2 | API key valid and within quota | LLM analysis unavailable |
| A3 | Email sending quota sufficient | Daily notifications fail |

---
 
## 3. System Features

> Use one subsection per feature. Copy the template below.

### 3.X Feature Name

#### 3.X.1 Description
 
_What the feature does & why._

#### 3.X.2 Trigger / Entry Points
 
_Which `Main.js` function or EventBus event starts it._

#### 3.X.3 Primary Flow (Events)
 
1. Event 1
2. Event 2
3. ...

#### 3.X.4 Inputs

| Source | Data | Format |
|--------|------|--------|

#### 3.X.5 Processing Rules

- Rule 1
- Rule 2

#### 3.X.6 Outputs

| Destination | Data | Persisted? |
|-------------|------|-----------|

#### 3.X.7 Error Handling

| Failure Point | Event Emitted | Recovery Strategy |
|---------------|---------------|-------------------|

#### 3.X.8 Version / Traceability
 
_Which CONFIG versions or schema versions this feature touches._

---
 
## 4. External Interface Requirements

### 4.1 Sheet Interfaces

| Sheet | Purpose | Key Fields | Schema Version |
|-------|---------|-----------|----------------|
| MetaLog | Source input | timestamp, behaviors, mood | v1 |
| DailyReport | Daily analyzed output | date, analysis, scores | v1 |
| WeeklyReport | Weekly aggregate output | weekStart, weekEnd, analysis | v1 |
| BehaviorScores | Behavior mapping | behavior, score, category | v1 |

### 4.2 API Interface (LLM Provider)

| Field | Description | Example |
|-------|-------------|---------|
| url | Endpoint | <https://api.deepseek.com/chat/completions> |
| model | Model name | deepseek-reasoner |
| payload.messages | System + user prompt | Array |
| response_format | JSON enforced | {"type": "json_object"} |

### 4.3 Email Interface

| Email Type | Subject Template | Trigger | Content Source |
|------------|------------------|---------|----------------|
| Daily | CONFIG.DAILY_EMAIL_SUBJECT | REPORT_GENERATION_COMPLETED | DailyReport row |
| Weekly | CONFIG.WEEKLY_EMAIL_SUBJECT | WEEKLY_REPORT_GENERATION_COMPLETED | WeeklyReport data |

### 4.4 Event Interface (Canonical Event Names)

| Category | Event | Purpose |
|----------|-------|---------|
| Daily | REPORT_GENERATION_STARTED | Kick off chain |
| Daily | DATA_READ_COMPLETED | Source data ready |
| Daily | SCORES_CALCULATED | Scoring done |
| Daily | PROMPT_READY | Prompt built |
| Daily | ANALYSIS_COMPLETED | LLM result returned |
| Daily | REPORT_SAVED | Persisted to sheet |
| Daily | REPORT_GENERATION_COMPLETED | Workflow end |
| Weekly | WEEKLY_REPORT_GENERATION_STARTED | Weekly chain start |
| Weekly | WEEKLY_DATA_COLLECTED | Source week assembled |
| Weekly | WEEKLY_SCORES_AGGREGATED | Aggregation done |
| Weekly | WEEKLY_PROMPT_READY | Weekly prompt built |
| Weekly | WEEKLY_ANALYSIS_RECEIVED | LLM weekly result |
| Weekly | WEEKLY_REPORT_GENERATION_COMPLETED | Weekly workflow end |
| Error | REPORT_GENERATION_FAILED | Fatal daily failure |
| Error | WEEKLY_REPORT_GENERATION_FAILED | Fatal weekly failure |
| Error | ERROR_OCCURRED | Listener runtime error |
| Schema | SCHEMA_MISMATCH_DETECTED | Header diff detected |
| Schema | SCHEMA_UPDATED | Schema version advanced |
| API | API_CALL_FAILED | Non-success attempt |
| API | API_CALL_SUCCESS | Successful attempt |

---
 
## 5. Nonfunctional Requirements

### 5.1 Performance

| Metric | Target | Notes |
|--------|--------|-------|
| Daily run time | < GAS limit (e.g. <60s) | Depends on LLM latency |
| Weekly run time | < GAS limit | |

### 5.2 Reliability & Availability

- Retry policy: 3 attempts with backoff (ApiService)
- Batch operations sequential to reduce failures

### 5.3 Security / Privacy

| Concern | Mitigation |
|---------|-----------|
| Personal data sent to LLM | User warning + option for local provider |
| API Key exposure | Stored in Script Properties |

### 5.4 Maintainability

- Single-responsibility service objects
- Version fields persisted for reproducibility

### 5.5 Scalability

- Event-driven allows adding new listeners w/o modifying core chain

### 5.6 Localization / Internationalization

- Prompts currently Traditional Chinese; templates versioned for future locales

### 5.7 Compliance
 
Compliance notes (e.g., GDPR) – _add if any._

---
 
## 6. Data Requirements

### 6.1 Logical Data Model (Sheets as Tables)

| Entity (Sheet) | Field | Type | Notes |
|----------------|-------|------|------|
| MetaLog | timestamp | Date | Raw entry time |
| MetaLog | behaviors | String | Comma-separated |
| ... | | | |

### 6.2 Data Retention
 
_Policy for how long to keep historical rows._

### 6.3 Data Quality Rules

- Missing required sleep fields -> mark in analysis but proceed.
- Early morning timestamps <03:00 assigned to previous day.

---
 
## 7. Versioning & Migration

### 7.1 Schema Versioning Strategy
 
_Describe how `SchemaService` versions and updates headers._

### 7.2 Scoring Versioning
 
_Describe use of `ScoreCalculatorFactory` and persisted version columns._

### 7.3 Prompt Template Versioning
 
_Describe `PromptBuilderService` strategy._

### 7.4 Migration Procedures

| Change Type | Steps | Verification |
|------------|-------|--------------|
| Add field | 1) addField 2) setVersion 3) update CONFIG | Run detectSchemaChanges() |

---
 
## 8. Error Handling & Logging

### 8.1 Event-Based Error Propagation
 
_Explain FAILED events vs non-critical email failures._

### 8.2 Audit Trail

- `EventBus.eventHistory` (limit retrieval)

### 8.3 Monitoring Hooks

| Tool | Purpose |
|------|---------|
| testMicroservicesArchitecture | Health check |
| viewEventHistory | Recent events |
| detectSchemaChanges | Schema drift |

---
 
## 9. Risks & Mitigations

| ID | Risk | Impact | Probability | Mitigation |
|----|------|--------|-------------|------------|
| R1 | API downtime | No analysis | | Retry / local provider |
| R2 | Schema drift | Data mapping fails | | detectSchemaChanges() |
| R3 | GAS quota exceeded | Workflow aborts | | Optimize prompts / batch |

---
 
## 10. Open Issues

| ID | Description | Owner | Target Version |
|----|-------------|-------|----------------|
| O1 | Local LLM full integration | | |
| O2 | Automated schema migrations | | |

---
 
## 11. Future Enhancements (Non-Scope)

- Multi-user tenancy
- Real-time dashboard
- Trend analytics & anomaly detection

---
 
## 12. Appendices

### Appendix A – Prompt JSON Contracts
 
_Reference stable JSON structures expected from LLM responses._

### Appendix B – Sample Event Timeline
 
_Example chronological event log for a successful daily run._

### Appendix C – Environment Configuration

| Property | Source | Example |
|----------|--------|---------|
| DEEPSEEK_API_KEY | Script Properties | sk-*** |
| RECIPIENT_EMAIL | Script Properties | <you@example.com> |

---
 
## 13. Change Log

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 0.1.0 | YYYY-MM-DD | Name | Initial template |

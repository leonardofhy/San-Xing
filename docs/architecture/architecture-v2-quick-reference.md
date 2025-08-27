# Architecture v2 Quick Reference

## Service Map

```
┌─────────────────────────────────────────────────────────────┐
│                         Main.js                              │
│              (Public API & Entry Points)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  ReportOrchestrator.js                       │
│              (Workflow Coordination)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     EventBus.js                              │
│              (Event-Driven Messaging)                        │
└──┬──────────┬──────────┬──────────┬──────────┬─────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│Sheet │  │Score │  │Prompt│  │ API  │  │Email │
│Adapter│  │Calc  │  │Builder│ │Service│ │Service│
└──────┘  └──────┘  └──────┘  └──────┘  └──────┘
   │          │
   ▼          ▼
┌──────┐  ┌──────┐
│Schema│  │Config│
│Service│ │ .js  │
└──────┘  └──────┘
```

## Key Functions

### Entry Points (Main.js)
```javascript
runDailyReportGeneration()      // Generate today's report
runBatchReportGeneration()      // Generate multiple reports
testMicroservicesArchitecture() // Test system health
detectSchemaChanges()           // Check for header mismatches
recalculateHistoricalScores()   // Update scores without LLM
viewEventHistory()              // Debug event flow
systemCleanup()                 // Optimize performance
```

### Core Services

**EventBus**
```javascript
EventBus.emit('EVENT_NAME', data)    // Trigger event
EventBus.on('EVENT_NAME', callback)  // Listen to event
EventBus.getEventHistory()           // View recent events
```

**SchemaService**
```javascript
SchemaService.getSchema('SheetName')              // Get schema
SchemaService.mapRowToObject(sheet, headers, row) // Map data
SchemaService.detectSchemaChanges(sheet, headers) // Check changes
SchemaService.addField(sheet, field, header, ver) // Add field
```

**SheetAdapter**
```javascript
SheetAdapter.readData('SheetName', options)       // Read data
SheetAdapter.writeData('SheetName', data, opts)   // Write data
SheetAdapter.findRowByDate('Sheet', date)         // Find by date
```

**ScoreCalculatorFactory**
```javascript
ScoreCalculatorFactory.calculate('type', data)    // Calculate score
ScoreCalculatorFactory.setActiveVersion('type', 'v2') // Change version
ScoreCalculatorFactory.recalculateHistorical()    // Bulk recalc
```

## Event Flow

### Daily Report Generation
1. `REPORT_GENERATION_STARTED` → Read source data
2. `DATA_READ_COMPLETED` → Calculate scores
3. `SCORES_CALCULATED` → Build prompt
4. `PROMPT_READY` → Call LLM API
5. `ANALYSIS_COMPLETED` → Save to sheet
6. `REPORT_SAVED` → Send email
7. `REPORT_GENERATION_COMPLETED` → Done

### Error Events
- `ERROR_OCCURRED` → General errors
- `REPORT_GENERATION_FAILED` → Critical failures
- `SCHEMA_MISMATCH_DETECTED` → Header changes
- `API_CALL_FAILED` → API issues
- `EMAIL_SEND_FAILED` → Email problems

## Configuration

### Sheet Names (SchemaService.js)
- `MetaLog` → Source data
- `DailyReport` → Output reports
- `BehaviorScores` → Score mappings

### API Providers (ApiService.js)
- `deepseek` → DeepSeek API (default)
- `local` → Local LLM (future)

### Calculator Versions (ScoreCalculatorFactory.js)
- `behavior: v1` → Current behavior scoring
- `sleep: v1` → Current sleep scoring

## Common Tasks

### Add a New Field
```javascript
// 1. Update schema
SchemaService.addField('MetaLog', 'newField', 'New Field Header', 'v2');

// 2. Set active version
SchemaService.setVersion('MetaLog', 'v2');
```

### Change Scoring Algorithm
```javascript
// 1. Register new calculator
ScoreCalculatorFactory.registerCalculator('behavior', 'v2', {
  calculate(data) { /* new logic */ },
  getMetadata() { return { version: 'v2' }; }
});

// 2. Activate it
ScoreCalculatorFactory.setActiveVersion('behavior', 'v2');
```

### Switch LLM Provider
```javascript
// Use local LLM instead of DeepSeek
ApiService.setProvider('local');
```

### Debug Issues
```javascript
// Check system health
testMicroservicesArchitecture();

// View recent events
viewEventHistory(30);

// Check for schema problems
detectSchemaChanges();
```

## File Structure
```
/
├── Main.js                 # Entry points
├── ReportOrchestrator.js   # Workflow coordination
├── EventBus.js            # Event system
├── SchemaService.js       # Schema management
├── SheetAdapter.js        # Sheet operations
├── ScoreCalculatorFactory.js # Score calculations
├── PromptBuilderService.js # Prompt generation
├── ApiService.js          # LLM integration
├── EmailService.js        # Email sending
├── Config.js              # Configuration
├── BehaviorScoreService.js # Legacy (used by factory)
├── SleepQualityService.js  # Legacy (used by factory)
└── DailyReport.js         # Legacy (keep for rollback)
```

## Best Practices

1. **Never modify EventBus listeners directly** - Use on/off methods
2. **Always use SchemaService** for header mapping - Don't hardcode
3. **Test schema changes** before deployment - Use detectSchemaChanges()
4. **Monitor event history** after changes - Use viewEventHistory()
5. **Keep calculator versions** backward compatible
6. **Use batch operations** for multiple sheet writes
7. **Cache data appropriately** - SheetAdapter handles this
8. **Handle errors gracefully** - Listen to error events

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Sheet not found" | Check schema sheet names |
| "Schema mismatch" | Run `detectSchemaChanges()` |
| API timeout | Check API key and provider |
| Email not sent | Verify `CONFIG.ENABLE_DAILY_EMAIL` |
| Missing scores | Check calculator registration |
| Slow performance | Run `systemCleanup()` | 
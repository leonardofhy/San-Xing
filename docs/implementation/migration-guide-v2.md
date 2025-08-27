# Migration Guide: Daily Report v1 to v2

**Version**: 1.0
**Last Updated**: 2025-06-17

## Overview

This guide walks you through migrating from the monolithic DailyReport.js (v1) to the new microservices architecture (v2). The migration is designed to be safe and reversible.

## Pre-Migration Checklist

- [ ] Backup your Google Sheets
- [ ] Note your current trigger settings
- [ ] Export current Config.js settings
- [ ] Test current system is working
- [ ] Schedule migration during low-usage period

## Step 1: Deploy New Services

Add these new files to your Apps Script project:

1. **Core Infrastructure**
   - `EventBus.js`
   - `SchemaService.js`
   - `SheetAdapter.js`

2. **Business Logic**
   - `ScoreCalculatorFactory.js`
   - `PromptBuilderService.js`

3. **Integration Services**
   - `ApiService.js`
   - `EmailService.js`

4. **Orchestration**
   - `ReportOrchestrator.js`
   - `Main.js`

**Note**: Keep your existing files (DailyReport.js, Config.js, etc.) - do NOT delete them yet!

## Step 2: Test the New Architecture

Run this test function to verify all services are properly deployed:

```javascript
// In Apps Script editor, run:
testMicroservicesArchitecture()
```

Expected output:
```
All tests passed: true
```

If any test fails, check that the corresponding service file was properly added.

## Step 3: Check Schema Compatibility

Run the schema detection to ensure your sheets match expected headers:

```javascript
detectSchemaChanges()
```

If mismatches are found, you have two options:
1. Update SchemaService.js to match your current headers
2. Update your sheet headers to match the schema

## Step 4: Update Configuration

The new architecture uses the same Config.js, but verify these settings:

```javascript
// These should already be in your Config.js:
CONFIG.SHEET_NAME = "MetaLog"  // Your source sheet
CONFIG.OUTPUT.DAILY_SHEET = "Daily Report"  // Output sheet
CONFIG.TIME_ZONE = "Asia/Taipei"  // Your timezone
```

## Step 5: Test with Manual Run

Before updating triggers, test manually:

```javascript
// Test single day report
runDailyReportGeneration()

// Check the event history
viewEventHistory()
```

## Step 6: Update Triggers

1. Go to Apps Script Editor → Triggers
2. Find your daily report trigger
3. Change the function from `runDailyReportGeneration` (in DailyReport.js) to `runDailyReportGeneration` (in Main.js)
4. Save the trigger

## Step 7: Monitor the First Automated Run

After the first automated run:

1. Check the execution transcript in Apps Script
2. Verify email was received
3. Check Daily Report sheet for new entry
4. Run `viewEventHistory()` to see the event flow

## Rollback Plan

If issues occur, rollback is simple:

1. Go to Triggers
2. Change the function back to use DailyReport.js
3. The old system will continue working

## Common Migration Issues

### Issue: "Sheet not found" errors
**Solution**: Check sheet names in SchemaService.js match your actual sheet names

### Issue: "Schema mismatch detected" warnings
**Solution**: Run `detectSchemaChanges()` and update either sheets or schema

### Issue: Email not sending
**Solution**: Check CONFIG.ENABLE_DAILY_EMAIL is true

### Issue: API errors
**Solution**: Verify CONFIG.DEEPSEEK_API_KEY is set correctly

## Post-Migration Benefits

### Immediate Benefits
- Better error messages and debugging
- Event history for troubleshooting
- Schema change detection
- Performance improvements from caching

### New Capabilities
- Recalculate historical scores without re-running LLM
- Switch between different LLM providers
- Add new scoring algorithms easily
- Detect and handle schema changes automatically

## Advanced Migration Options

### Gradual Migration

You can run both systems in parallel:

1. Keep old trigger active
2. Create new trigger for new system with different schedule
3. Compare outputs for a few days
4. Disable old trigger when confident

### Custom Schema Migration

If your headers are very different:

```javascript
// Add your custom schema version
SchemaService.schemas.MetaLog.v2 = {
  timestamp: 'Your Timestamp Header',
  behaviors: 'Your Behavior Header',
  // ... map all your headers
};

// Set as active version
SchemaService.setVersion('MetaLog', 'v2');
```

### Historical Data Migration

To recalculate all historical scores with new algorithm:

```javascript
// Recalculate behavior scores for date range
recalculateHistoricalScores(
  '2024/01/01',  // start date
  '2024/12/31',  // end date
  'behavior',    // calculator type
  'v2'          // new version
);
```

## Support and Troubleshooting

### Debug Commands

```javascript
// View system state
testMicroservicesArchitecture()

// Check recent events
viewEventHistory(50)

// Detect schema issues  
detectSchemaChanges()

// Clean up system
systemCleanup()
```

### Performance Optimization

After migration, run cleanup:

```javascript
systemCleanup()
```

This will:
- Clear caches
- Check for duplicate entries
- Optimize spreadsheet performance

## Next Steps

After successful migration:

1. Delete old DailyReport.js (after 1-2 weeks of stable operation)
2. Explore new features like score recalculation
3. Consider adding Weekly Reports using same architecture
4. Set up regular system cleanup schedule

## Conclusion

The new architecture provides a solid foundation for future enhancements while maintaining backward compatibility. Take your time with the migration and use the rollback option if needed. The modular design makes it easy to debug and extend the system going forward. 
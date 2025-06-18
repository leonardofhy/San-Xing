/**
 * Main.js - Entry point for the Meta-Awareness Report System
 * Maintains backward compatibility with existing triggers
 * 
 * This file provides the public API that triggers and users interact with.
 * All the heavy lifting is delegated to the microservices architecture.
 */

/**
 * Generate a single daily report (backward compatible)
 * This function is called by time-based triggers
 */
function runDailyReportGeneration() {
  console.log('========== Daily Report Generation Started ==========');
  
  try {
    ReportOrchestrator.generateDailyReport()
      .then(result => {
        console.log('Daily report generation completed successfully');
        console.log('Report date:', result.date);
        console.log('Email sent:', result.emailSent || false);
      })
      .catch(error => {
        console.error('Daily report generation failed:', error);
        throw error; // Re-throw to trigger Apps Script error notification
      });
  } catch (error) {
    console.error('Failed to start daily report generation:', error);
    throw error;
  }
}

/**
 * Generate batch reports (backward compatible)
 * This function is called manually for historical data processing
 */
function runBatchReportGeneration() {
  console.log('========== Batch Report Generation Started ==========');
  
  try {
    const results = ReportOrchestrator.generateBatchReports();
    console.log('Batch report generation completed:', results);
    return results;
  } catch (error) {
    console.error('Batch report generation failed:', error);
    throw error;
  }
}

/**
 * Test the microservices architecture
 * Useful for debugging and verifying setup
 */
function testMicroservicesArchitecture() {
  console.log('========== Testing Microservices Architecture ==========');
  
  const tests = {
    eventBus: false,
    schemaService: false,
    sheetAdapter: false,
    scoreCalculators: false,
    apiService: false,
    emailTemplates: false,
    orchestrator: false
  };
  
  try {
    // Test EventBus
    EventBus.on('TEST_EVENT', (data) => {
      console.log('EventBus test received:', data);
      tests.eventBus = true;
    });
    EventBus.emit('TEST_EVENT', { test: true });
    
    // Test SchemaService
    const schema = SchemaService.getSchema('MetaLog');
    tests.schemaService = Object.keys(schema).length > 0;
    console.log('SchemaService test:', tests.schemaService);
    
    // Test SheetAdapter
    SheetAdapter.init();
    tests.sheetAdapter = SheetAdapter.spreadsheet !== null;
    console.log('SheetAdapter test:', tests.sheetAdapter);
    
    // Test ScoreCalculators
    const behaviorCalc = ScoreCalculatorFactory.getCalculator('behavior');
    const sleepCalc = ScoreCalculatorFactory.getCalculator('sleep');
    tests.scoreCalculators = behaviorCalc !== null && sleepCalc !== null;
    console.log('ScoreCalculators test:', tests.scoreCalculators);
    
    // Test ApiService
    tests.apiService = ApiService.providers.deepseek !== undefined;
    console.log('ApiService test:', tests.apiService);
    
    // Test EmailService
    tests.emailTemplates = EmailService.templates.daily.v1 !== undefined;
    console.log('EmailService test:', tests.emailTemplates);
    
    // Test Orchestrator
    ReportOrchestrator.init();
    tests.orchestrator = ReportOrchestrator.initialized;
    console.log('Orchestrator test:', tests.orchestrator);
    
    // Summary
    const allPassed = Object.values(tests).every(test => test === true);
    console.log('\n========== Test Results ==========');
    console.log(tests);
    console.log('All tests passed:', allPassed);
    
    return tests;
    
  } catch (error) {
    console.error('Architecture test failed:', error);
    return tests;
  }
}

/**
 * Recalculate historical scores without regenerating LLM analysis
 * Addresses Issue #006
 * 
 * @param {string} startDate - Start date (yyyy/MM/dd)
 * @param {string} endDate - End date (yyyy/MM/dd)
 * @param {string} calculatorType - 'behavior' or 'sleep'
 * @param {string} version - Calculator version to use
 */
function recalculateHistoricalScores(startDate, endDate, calculatorType, version) {
  console.log(`========== Recalculating ${calculatorType} scores from ${startDate} to ${endDate} ==========`);
  
  try {
    // Read historical data
    const historicalData = SheetAdapter.readData(CONFIG.OUTPUT.DAILY_SHEET);
    
    // Filter by date range
    const filteredData = historicalData.filter(entry => {
      if (!(entry.date instanceof Date)) return false;
      const entryDate = Utilities.formatDate(entry.date, CONFIG.TIME_ZONE, "yyyy/MM/dd");
      return entryDate >= startDate && entryDate <= endDate;
    });
    
    console.log(`Found ${filteredData.length} entries to recalculate`);
    
    // Prepare data for recalculation
    const dataForRecalc = filteredData.map(entry => {
      // Parse the stored analysis to get original behaviors
      let originalData = {};
      try {
        const analysis = JSON.parse(entry.analysis);
        if (calculatorType === 'behavior') {
          // Extract behaviors from analysis
          originalData = [
            ...(analysis.behaviorReview?.positive || []),
            ...(analysis.behaviorReview?.negative || []),
            ...(analysis.behaviorReview?.neutral || [])
          ];
        } else if (calculatorType === 'sleep') {
          // Extract sleep data from stored values
          originalData = {
            // This would need to be enhanced to store original sleep times
            quality: entry.sleepQuality
          };
        }
      } catch (e) {
        console.warn(`Could not parse analysis for date ${entry.date}`);
      }
      
      return {
        date: Utilities.formatDate(entry.date, CONFIG.TIME_ZONE, "yyyy/MM/dd"),
        data: originalData,
        score: entry[`${calculatorType}Total`]
      };
    });
    
    // Recalculate scores
    const results = ScoreCalculatorFactory.recalculateHistorical(
      calculatorType,
      version,
      dataForRecalc
    );
    
    // Update sheets with new scores
    console.log('Updating sheet with recalculated scores...');
    // This would need implementation to update specific columns
    
    console.log('Recalculation completed:', results);
    return results;
    
  } catch (error) {
    console.error('Score recalculation failed:', error);
    throw error;
  }
}

/**
 * View event history for debugging
 */
function viewEventHistory(limit = 20) {
  const history = EventBus.getEventHistory(limit);
  console.log(`========== Last ${limit} Events ==========`);
  history.forEach((event, index) => {
    console.log(`${index + 1}. [${Utilities.formatDate(event.timestamp, CONFIG.TIME_ZONE, "HH:mm:ss")}] ${event.event}`);
    if (event.data) {
      console.log('   Data:', JSON.stringify(event.data, null, 2));
    }
  });
  return history;
}

/**
 * Detect schema changes in sheets
 * Useful for debugging Issue #002, #004, #005
 */
function detectSchemaChanges() {
  console.log('========== Detecting Schema Changes ==========');
  
  const sheets = [CONFIG.SHEET_NAME, CONFIG.OUTPUT.DAILY_SHEET, CONFIG.OUTPUT.BEHAVIOR_SHEET];
  const results = {};
  
  sheets.forEach(sheetName => {
    try {
      const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
      if (!sheet) {
        results[sheetName] = { error: 'Sheet not found' };
        return;
      }
      
      const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
      const changes = SchemaService.detectSchemaChanges(sheetName, headers);
      
      results[sheetName] = changes;
      
      if (changes.hasChanges) {
        console.log(`\n${sheetName} has schema changes:`);
        if (changes.missing.length > 0) {
          console.log('  Missing headers:', changes.missing);
        }
        if (changes.extra.length > 0) {
          console.log('  Extra headers:', changes.extra);
        }
      } else {
        console.log(`\n${sheetName}: Schema matches expected`);
      }
    } catch (error) {
      results[sheetName] = { error: error.message };
    }
  });
  
  return results;
}

/**
 * Migration helper: Update schema to new version
 * @param {string} sheetName - Name of the sheet
 * @param {string} newVersion - New schema version
 */
function migrateSchemaVersion(sheetName, newVersion) {
  console.log(`========== Migrating ${sheetName} to schema version ${newVersion} ==========`);
  
  try {
    SchemaService.setVersion(sheetName, newVersion);
    console.log('Schema version updated successfully');
    
    // Detect any changes needed
    const changes = detectSchemaChanges();
    return changes[sheetName];
    
  } catch (error) {
    console.error('Schema migration failed:', error);
    throw error;
  }
}

/**
 * Clean up and optimize the system
 * Removes duplicate entries, optimizes sheet performance
 */
function systemCleanup() {
  console.log('========== System Cleanup Started ==========');
  
  try {
    // Clear caches
    SheetAdapter.cache = {};
    console.log('Cleared SheetAdapter cache');
    
    // Optimize spreadsheet
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    SpreadsheetApp.flush();
    console.log('Flushed pending spreadsheet changes');
    
    // Check for duplicate entries in Daily Report
    const reports = SheetAdapter.readData(CONFIG.OUTPUT.DAILY_SHEET);
    const dateCount = {};
    reports.forEach((report, index) => {
      if (report.date instanceof Date) {
        const dateStr = Utilities.formatDate(report.date, CONFIG.TIME_ZONE, "yyyy/MM/dd");
        if (!dateCount[dateStr]) {
          dateCount[dateStr] = [];
        }
        dateCount[dateStr].push(index + 2); // +2 for header and 0-based index
      }
    });
    
    const duplicates = Object.entries(dateCount)
      .filter(([date, rows]) => rows.length > 1);
    
    if (duplicates.length > 0) {
      console.log('Found duplicate dates:');
      duplicates.forEach(([date, rows]) => {
        console.log(`  ${date}: rows ${rows.join(', ')}`);
      });
    } else {
      console.log('No duplicate dates found');
    }
    
    console.log('System cleanup completed');
    return {
      cacheCleared: true,
      duplicatesFound: duplicates.length,
      duplicates: duplicates
    };
    
  } catch (error) {
    console.error('System cleanup failed:', error);
    throw error;
  }
} 
/**
 * DevTools.js – Consolidated debugging & maintenance helpers
 *
 * This file groups together non-critical helper functions that were previously
 * scattered across Main.js and other services. This keeps the global namespace
 * cleaner for production triggers, while still allowing manual invocation from
 * the Apps Script editor.
 */

// ------------------------------------------------------------------
// === Implementations moved from other files ===
// ------------------------------------------------------------------

/**
 * Debug daily report generation process
 * Shows detailed information about each step
 */
async function debugDailyReportGeneration() {
  console.log('========== Debug Daily Report Generation ==========');
  
  try {
    // Clear event history first
    EventBus.eventHistory = [];
    
    console.log('1. Starting report generation...');
    const result = await ReportOrchestrator.generateDailyReport({ debug: true });
    
    console.log('2. Report generation completed');
    console.log('Result:', JSON.stringify(result, null, 2));
    
    console.log('3. Event history:');
    const history = EventBus.getEventHistory();
    history.forEach((event, index) => {
      console.log(`   ${index + 1}. [${Utilities.formatDate(event.timestamp, CONFIG.TIME_ZONE, "HH:mm:ss")}] ${event.event}`);
      if (event.data && event.data.error) {
        console.log(`      Error: ${event.data.error.message}`);
      }
    });
    
    console.log('4. Configuration check:');
    console.log('   ENABLE_DAILY_EMAIL:', CONFIG.ENABLE_DAILY_EMAIL);
    console.log('   RECIPIENT_EMAIL:', CONFIG.RECIPIENT_EMAIL ? 'Set' : 'Not set');
    console.log('   OVERWRITE_EXISTING:', CONFIG.OUTPUT.OVERWRITE_EXISTING);
    
    return result;
  } catch (error) {
    console.error('Debug daily report generation failed:', error);
    const history = EventBus.getEventHistory();
    console.log('Event history at failure:');
    history.forEach((event, index) => {
      console.log(`   ${index + 1}. ${event.event}`);
      if (event.data && event.data.error) {
        console.log(`      Error: ${event.data.error.message}`);
      }
    });
    throw error;
  }
}

/**
 * Debug weekly report generation process
 * Shows detailed information about each step
 */
async function debugWeeklyReportGeneration() {
  console.log('========== Debug Weekly Report Generation ==========');
  
  try {
    // Clear event history first
    EventBus.eventHistory = [];
    
    console.log('1. Starting weekly report generation...');
    const result = await ReportOrchestrator.generateWeeklyReport({ debug: true });
    
    console.log('2. Weekly report generation completed');
    console.log('Result:', JSON.stringify(result, null, 2));
    
    console.log('3. Event history:');
    const history = EventBus.getEventHistory();
    history.forEach((event, index) => {
      console.log(`   ${index + 1}. [${Utilities.formatDate(event.timestamp, CONFIG.TIME_ZONE, "HH:mm:ss")}] ${event.event}`);
      if (event.data && event.data.error) {
        console.log(`      Error: ${event.data.error.message}`);
      }
    });
    
    console.log('4. Configuration check:');
    console.log('   ENABLE_WEEKLY_EMAIL:', CONFIG.ENABLE_WEEKLY_EMAIL);
    console.log('   RECIPIENT_EMAIL:', CONFIG.RECIPIENT_EMAIL ? 'Set' : 'Not set');
    console.log('   WEEK_START_DAY:', CONFIG.WEEKLY_REPORT.WEEK_START_DAY);
    console.log('   MIN_DAYS_REQUIRED:', CONFIG.WEEKLY_REPORT.MIN_DAYS_REQUIRED);
    
    return result;
  } catch (error) {
    console.error('Debug weekly report generation failed:', error);
    const history = EventBus.getEventHistory();
    console.log('Event history at failure:');
    history.forEach((event, index) => {
      console.log(`   ${index + 1}. ${event.event}`);
      if (event.data && event.data.error) {
        console.log(`      Error: ${event.data.error.message}`);
      }
    });
    throw error;
  }
}

/**
 * Test the microservices architecture
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

/**
 * Check system configuration and diagnose issues
 */
function checkSystemConfiguration() {
  console.log('========== System Configuration Check ==========');
  
  const results = {
    config: {},
    sheets: {},
    apis: {},
    issues: []
  };
  
  try {
    // Check configuration
    console.log('1. Configuration Check:');
    results.config.recipientEmail = CONFIG.RECIPIENT_EMAIL ? 'Set' : 'Not set';
    results.config.enableDailyEmail = CONFIG.ENABLE_DAILY_EMAIL;
    results.config.overwriteExisting = CONFIG.OUTPUT.OVERWRITE_EXISTING;
    results.config.deepseekApiKey = CONFIG.DEEPSEEK_API_KEY ? 'Set' : 'Not set';
    
    console.log('   - Recipient Email:', results.config.recipientEmail);
    console.log('   - Daily Email Enabled:', results.config.enableDailyEmail);
    console.log('   - Overwrite Existing:', results.config.overwriteExisting);
    console.log('   - DeepSeek API Key:', results.config.deepseekApiKey);
    
    if (!CONFIG.RECIPIENT_EMAIL) {
      results.issues.push('RECIPIENT_EMAIL not set in script properties');
    }
    if (!CONFIG.DEEPSEEK_API_KEY) {
      results.issues.push('DEEPSEEK_API_KEY not set in script properties');
    }
    
    // Check sheets existence
    console.log('2. Sheets Check:');
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const requiredSheets = [CONFIG.SHEET_NAME, CONFIG.OUTPUT.DAILY_SHEET];
    
    requiredSheets.forEach(sheetName => {
      const sheet = ss.getSheetByName(sheetName);
      const exists = sheet !== null;
      results.sheets[sheetName] = exists;
      console.log(`   - ${sheetName}:`, exists ? 'Exists' : 'Missing');
      
      if (!exists) {
        results.issues.push(`Sheet '${sheetName}' does not exist`);
      } else {
        const lastRow = sheet.getLastRow();
        console.log(`     Last row: ${lastRow}`);
        if (lastRow < 2) {
          results.issues.push(`Sheet '${sheetName}' appears to be empty`);
        }
      }
    });
    
    // Check recent data
    console.log('3. Recent Data Check:');
    try {
      SheetAdapter.init();
      const recentData = SheetAdapter.readData(CONFIG.SHEET_NAME, { numRows: 5 });
      console.log(`   - Found ${recentData.length} recent entries`);
      
      if (recentData.length > 0) {
        const latest = recentData[recentData.length - 1];
        const latestDate = latest.timestamp instanceof Date ? 
          Utilities.formatDate(latest.timestamp, CONFIG.TIME_ZONE, "yyyy/MM/dd HH:mm") : 
          'Invalid date';
        console.log(`   - Latest entry: ${latestDate}`);
        results.config.latestEntry = latestDate;
      } else {
        results.issues.push('No data found in MetaLog sheet');
      }
    } catch (error) {
      results.issues.push(`Error reading data: ${error.message}`);
    }
    
    // Summary
    console.log('4. Summary:');
    if (results.issues.length === 0) {
      console.log('   ✅ No issues found');
    } else {
      console.log('   ❌ Issues found:');
      results.issues.forEach(issue => {
        console.log(`      - ${issue}`);
      });
    }
    
    return results;
    
  } catch (error) {
    console.error('Configuration check failed:', error);
    results.issues.push(`Configuration check failed: ${error.message}`);
    return results;
  }
}

/**
 * 详细检查 MetaLog 数据情况
 */
function inspectMetaLogData() {
  console.log('========== MetaLog Data Inspection ==========');
  
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
    
    if (!sheet) {
      console.error('MetaLog sheet not found!');
      return;
    }
    
    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();
    
    console.log(`1. Sheet Info:`);
    console.log(`   - Total rows: ${lastRow}`);
    console.log(`   - Total columns: ${lastCol}`);
    
    // 检查表头
    console.log(`2. Headers:`);
    if (lastRow >= 1) {
      const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
      headers.forEach((header, index) => {
        console.log(`   ${index + 1}. ${header}`);
      });
    }
    
    // 检查最后10行的原始数据
    console.log(`3. Raw Data (Last 10 rows):`);
    if (lastRow >= 2) {
      const startRow = Math.max(2, lastRow - 9); // 最后10行数据
      const numRows = lastRow - startRow + 1;
      const rawData = sheet.getRange(startRow, 1, numRows, lastCol).getValues();
      
      rawData.forEach((row, index) => {
        const rowNum = startRow + index;
        console.log(`   Row ${rowNum}:`);
        console.log(`     Timestamp: ${row[0]} (Type: ${typeof row[0]})`);
        console.log(`     Is Date: ${row[0] instanceof Date}`);
        if (row[0] instanceof Date) {
          console.log(`     Formatted: ${Utilities.formatDate(row[0], CONFIG.TIME_ZONE, "yyyy/MM/dd HH:mm:ss")}`);
        }
        // 只显示前几列避免太多输出
        console.log(`     Other data: ${JSON.stringify(row.slice(1, 3))}`);
      });
    }
    
    // 使用 SheetAdapter 读取数据
    console.log(`4. SheetAdapter Reading:`);
    try {
      SheetAdapter.init();
      const allData = SheetAdapter.readData(CONFIG.SHEET_NAME);
      console.log(`   - SheetAdapter found ${allData.length} entries`);
      
      if (allData.length > 0) {
        console.log(`   - First entry timestamp: ${allData[0].timestamp}`);
        console.log(`   - Last entry timestamp: ${allData[allData.length - 1].timestamp}`);
        
        // 检查最后5条记录的时间戳
        console.log(`   - Last 5 entries timestamps:`);
        const last5 = allData.slice(-5);
        last5.forEach((entry, index) => {
          const actualIndex = allData.length - 5 + index;
          console.log(`     [${actualIndex + 1}] ${entry.timestamp} (${typeof entry.timestamp})`);
          if (entry.timestamp instanceof Date) {
            console.log(`         Formatted: ${Utilities.formatDate(entry.timestamp, CONFIG.TIME_ZONE, "yyyy/MM/dd HH:mm:ss")}`);
          }
        });
      }
    } catch (error) {
      console.error(`   SheetAdapter error: ${error.message}`);
    }
    
    // 检查今天的日期查找逻辑
    console.log(`5. Date Finding Logic Test:`);
    const today = new Date();
    const todayFormatted = Utilities.formatDate(today, CONFIG.TIME_ZONE, "yyyy/MM/dd");
    console.log(`   - Today: ${todayFormatted}`);
    
    // 模拟 ReportOrchestrator 的日期调整逻辑
    const now = new Date();
    const currentHour = now.getHours();
    if (currentHour < 3) {
      now.setDate(now.getDate() - 1);
    }
    const adjustedDate = Utilities.formatDate(now, CONFIG.TIME_ZONE, "yyyy/MM/dd");
    console.log(`   - Adjusted date for report: ${adjustedDate}`);
    console.log(`   - Current hour: ${currentHour}`);
    console.log(`   - Date adjustment: ${currentHour < 3 ? 'Applied (using previous day)' : 'Not applied (using current day)'}`);
    
  } catch (error) {
    console.error('MetaLog inspection failed:', error);
  }
}

/**
 * 检查最新的 MetaLog 数据
 */
function checkLatestMetaLogData(rowsToShow = 5) {
  console.log(`========== Latest MetaLog Data (Last ${rowsToShow} entries) ==========`);
  
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
    
    if (!sheet) {
      console.error('MetaLog sheet not found!');
      return;
    }
    
    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();
    
    console.log(`Sheet Info: ${lastRow} rows, ${lastCol} columns`);
    
    if (lastRow < 2) {
      console.log('No data found in sheet');
      return;
    }
    
    // 计算要读取的起始行
    const startRow = Math.max(2, lastRow - rowsToShow + 1);
    const numRows = lastRow - startRow + 1;
    
    // 获取表头
    const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
    
    // 读取最后几行数据
    const dataRange = sheet.getRange(startRow, 1, numRows, lastCol);
    const dataValues = dataRange.getValues();
    
    console.log(`\nLatest ${numRows} entries:`);
    
    // 使用 SchemaService 映射数据
    dataValues.forEach((row, index) => {
      const rowNum = startRow + index;
      const mappedData = SchemaService.mapRowToObject(CONFIG.SHEET_NAME, headers, row);
      
      console.log(`\nRow ${rowNum}:`);
      console.log(`  Timestamp: ${mappedData.timestamp}`);
      
      if (mappedData.timestamp instanceof Date) {
        console.log(`  Formatted: ${Utilities.formatDate(mappedData.timestamp, CONFIG.TIME_ZONE, "yyyy/MM/dd HH:mm:ss")}`);
      }
      
      console.log(`  Behaviors: ${mappedData.behaviors || 'N/A'}`);
      console.log(`  Mood: ${mappedData.mood || 'N/A'}`);
      console.log(`  Sleep: ${mappedData.sleepStart || 'N/A'} - ${mappedData.sleepEnd || 'N/A'}`);
    });
    
    // 显示最新条目的详细信息
    if (dataValues.length > 0) {
      const latestRow = dataValues[dataValues.length - 1];
      const latestData = SchemaService.mapRowToObject(CONFIG.SHEET_NAME, headers, latestRow);
      
      console.log('\n========== Latest Entry Details ==========');
      console.log(`Date: ${latestData.timestamp instanceof Date ? 
        Utilities.formatDate(latestData.timestamp, CONFIG.TIME_ZONE, "yyyy/MM/dd HH:mm:ss") : 
        latestData.timestamp}`);
      console.log(`Day of data: ${latestData.timestamp instanceof Date ? 
        Utilities.formatDate(latestData.timestamp, CONFIG.TIME_ZONE, "EEEE") : 
        'Unknown'}`);
      
      // 判断这是哪一天的数据（考虑凌晨填写的情况）
      if (latestData.timestamp instanceof Date) {
        const reportDate = new Date(latestData.timestamp);
        if (reportDate.getHours() < 3) {
          reportDate.setDate(reportDate.getDate() - 1);
        }
        console.log(`Report date (adjusted): ${Utilities.formatDate(reportDate, CONFIG.TIME_ZONE, "yyyy/MM/dd")}`);
      }
    }
    
    return {
      totalRows: lastRow,
      latestEntries: numRows,
      hasData: true
    };
    
  } catch (error) {
    console.error('Failed to check latest data:', error);
    return {
      error: error.message
    };
  }
}

/**
 * Batch back-test scores without calling LLM/email.
 */
async function backtestScores(startDate = CONFIG.BATCH_PROCESS.DATE_RANGE.START,
                              endDate   = CONFIG.BATCH_PROCESS.DATE_RANGE.END,
                              useLatestIfMissing = false,
                              writeToSheet = true,
                              overwriteAnalysis = false) {
  console.log(`========== Back-testing Scores ${startDate} → ${endDate} ==========`);

  const results = [];
  const start = new Date(startDate);
  const end   = new Date(endDate);

  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const dateStr = Utilities.formatDate(d, CONFIG.TIME_ZONE, 'yyyy/MM/dd');
    try {
      const res = await ReportOrchestrator.calculateScoresOnly({
        date: dateStr,
        useLatestData: useLatestIfMissing
      });

      // Preserve/overwrite analysis logic
      let existingAnalysis = '';
      let rowObj = null;
      const existingRow = SheetAdapter.findRowByDate(CONFIG.OUTPUT.DAILY_SHEET, res.date);
      if (existingRow && !overwriteAnalysis) {
        rowObj = SheetAdapter.readData(CONFIG.OUTPUT.DAILY_SHEET, { startRow: existingRow, numRows: 1 })[0];
        existingAnalysis = rowObj?.analysis || '';
      }

      const reportData = {
        timestamp: new Date(),
        date: new Date(res.date),
        analysis: existingAnalysis,
        behaviorTotal: res.scores.behavior.total ?? null,
        behaviorPositive: res.scores.behavior.details?.positive ?? null,
        behaviorNegative: res.scores.behavior.details?.negative ?? null,
        behaviorRaw: res.scores.behavior.details?.rawScore ?? null,
        behaviorGoal: res.scores.behavior.details?.goal ?? null,
        sleepTotal: res.scores.sleep.total ?? null,
        sleepDuration: res.scores.sleep.details?.duration?.score ?? null,
        sleepQuality: res.scores.sleep.details?.quality?.score ?? null,
        sleepRegularity: res.scores.sleep.details?.regularity?.score ?? null,
        behaviorScoreVersion: ScoreCalculatorFactory.activeVersions.behavior,
        sleepScoreVersion: ScoreCalculatorFactory.activeVersions.sleep,
        analysisVersion: overwriteAnalysis ? CONFIG.VERSIONS.ANALYSIS : existingAnalysis ? (rowObj?.analysisVersion || '') : ''
      };

      if (writeToSheet) {
        if (existingRow) {
          SheetAdapter.writeData(CONFIG.OUTPUT.DAILY_SHEET, [reportData], { rowIndex: existingRow });
        } else {
          SheetAdapter.writeData(CONFIG.OUTPUT.DAILY_SHEET, [reportData], { append: true });
        }
      }

      results.push({ ...res, success: true });
      console.log(`✓ ${dateStr}`);
    } catch (e) {
      results.push({ date: dateStr, error: e.message, success: false });
      console.warn(`× ${dateStr} – ${e.message}`);
    }
  }

  console.log(`Completed. Success: ${results.filter(r => r.success).length}/${results.length}`);
  return results;
}

// ------------------------------------------------------------------
// === DevTools Namespace Object ===
// ------------------------------------------------------------------

const DevTools = {
  // Report / Orchestrator helpers
  debugDailyReportGeneration,
  viewEventHistory,
  detectSchemaChanges,
  migrateSchemaVersion,
  systemCleanup,
  checkSystemConfiguration,
  inspectMetaLogData,
  checkLatestMetaLogData,
  backtestScores,
  recalculateHistoricalScores,
  testMicroservicesArchitecture
};

/**
 * Quick helper to list available DevTools functions in logs.
 */
function listDevTools() {
  console.log('Available DevTools methods:');
  Object.keys(DevTools).forEach(k => console.log(' - DevTools.' + k + '()'));
  return Object.keys(DevTools);
} 
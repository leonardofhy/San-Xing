/**
 * Main.js - Entry point for the Meta-Awareness Report System
 * This file provides the core, production-ready public API that triggers
 * and users interact with. All debugging and maintenance helpers have been
 * moved to DevTools.js.
 */

/**
 * Main trigger function for daily report generation.
 * Reads configuration from CONFIG object to determine behavior.
 */
function runDailyReportGeneration() {
  // This wrapper function is designed to be the single entry point for automated triggers.
  // It reads settings from the CONFIG object to decide which report to generate.
  
  const mode = CONFIG.DAILY_REPORT_DATE?.MODE || 'latest'; // Default to 'latest'
  let options = {};

  if (mode === 'specific') {
    // Use a specific date from config
    options.date = CONFIG.DAILY_REPORT_DATE.SPECIFIC_DATE;
    console.log(`[Main] Triggered in 'specific' mode for date: ${options.date}`);
  } else {
    // Default to using the latest available data
    options.useLatestData = true;
     console.log(`[Main] Triggered in 'latest' mode.`);
  }

  // The 'forceEmail' option is intentionally not set here.
  // Email sending logic is controlled by CONFIG.ENABLE_DAILY_EMAIL within the orchestrator.
  // For manual overrides, call runDailyReport({ forceEmail: true }) directly.

  return runDailyReport(options);
}

/**
 * Universal daily report runner. This is the core logic function.
 * @param {Object} options - Generation options.
 * @param {string} [options.date] - Target date in 'yyyy/MM/dd' format.
 * @param {boolean} [options.useLatestData=false] - If true, ignores date and uses the most recent entry.
 * @param {boolean} [options.forceEmail=false] - If true, sends an email regardless of update status or global config.
 */
async function runDailyReport(options = {}) {
  console.log('========== Daily Report Runner ==========');
  try {
    // Direct attempt with provided options.
    return await ReportOrchestrator.generateDailyReport(options);
  } catch (error) {
    // If a specific date was requested but no data was found, automatically fall back to the latest data.
    if (options.date && !options.useLatestData && error.message && error.message.includes('No data found')) {
      console.warn(`No data found for date: ${options.date}. Falling back to latest available entry.`);
      
      // We create a new options object for the fallback to avoid polluting the original call.
      const fallbackOptions = { ...options, useLatestData: true };
      delete fallbackOptions.date; // Remove specific date for fallback

      try {
        return await ReportOrchestrator.generateDailyReport(fallbackOptions);
      } catch (fallbackError) {
        console.error(`Fallback attempt also failed: ${fallbackError.message}`);
        throw fallbackError; // Throw the fallback error as it's more relevant now.
      }
    }
    
    // For any other errors, or if fallback fails, re-throw the original error.
    throw error;
  }
}

/**
 * Generate batch reports for a specified date range.
 * This function is typically called manually for historical data processing.
 * All configuration is read from CONFIG.BATCH_PROCESS.
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
 * Main trigger function for weekly report generation.
 * Generates a report for the current week (Sunday to Saturday).
 */
function runWeeklyReportGeneration() {
  console.log('[Main] Weekly report generation triggered');
  
  const options = {
    reportType: 'weekly',
    weekOffset: 0 // 0 = current week, -1 = last week, etc.
  };
  
  return runWeeklyReport(options);
}

/**
 * Universal weekly report runner.
 * @param {Object} options - Generation options
 * @param {number} [options.weekOffset=0] - Week offset (0=current, -1=previous)
 * @param {string} [options.startDate] - Custom week start date (yyyy/MM/dd)
 * @param {boolean} [options.forceEmail=false] - Force email sending
 */
async function runWeeklyReport(options = {}) {
  console.log('========== Weekly Report Runner ==========');
  try {
    return await ReportOrchestrator.generateWeeklyReport(options);
  } catch (error) {
    console.error('Weekly report generation failed:', error);
    throw error;
  }
}
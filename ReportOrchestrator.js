/**
 * ReportOrchestrator - Main coordinator for report generation
 * Uses event-driven architecture to orchestrate all services
 */
const ReportOrchestrator = {
  initialized: false,
  
  /**
   * Initialize the orchestrator and register all event handlers
   */
  init() {
    if (this.initialized) return;
    
    // Initialize core services
    SheetAdapter.init();
    
    // Register event handlers
    this._registerEventHandlers();
    
    this.initialized = true;
    console.log('[ReportOrchestrator] Initialized');
  },
  
  /**
   * Generate a daily report
   * @param {Object} options - Generation options
   * @returns {Promise} Report generation result
   */
  generateDailyReport(options = {}) {
    this.init();
    
    const context = {
      startTime: new Date(),
      options: options,
      date: options.date || this._getCurrentDate(),
      results: {}
    };
    
    console.log(`[ReportOrchestrator] Starting daily report generation for ${context.date}`);
    
    // Return a promise that resolves when the report is complete
    return new Promise((resolve, reject) => {
      const completeHandler = (context) => {
        EventBus.off('REPORT_GENERATION_COMPLETED', completeHandler);
        EventBus.off('REPORT_GENERATION_FAILED', failHandler);
        
        // Return structured result
        const result = {
          date: context.date,
          emailSent: context.emailSent || false,
          emailSkipped: context.emailSkipped || false,
          wasUpdated: context.wasUpdated || false,
          scores: context.scores,
          executionTime: new Date() - context.startTime,
          ...(context.emailError && { emailError: context.emailError.message })
        };
        
        console.log('[ReportOrchestrator] Report generation completed:', result);
        resolve(result);
      };
      
      const failHandler = (errorData) => {
        EventBus.off('REPORT_GENERATION_COMPLETED', completeHandler);
        EventBus.off('REPORT_GENERATION_FAILED', failHandler);
        
        const error = errorData.error || new Error('Unknown error');
        error.phase = errorData.phase;
        error.context = errorData.context;
        
        console.error('[ReportOrchestrator] Report generation failed:', error);
        reject(error);
      };
      
      EventBus.on('REPORT_GENERATION_COMPLETED', completeHandler);
      EventBus.on('REPORT_GENERATION_FAILED', failHandler);

      // Start the event chain *after* listeners are in place
      EventBus.emit('REPORT_GENERATION_STARTED', context);
    });
  },
  
  /**
   * Generate batch reports
   * @param {Object} options - Batch options
   * @returns {Object} Batch results
   */
  generateBatchReports(options = {}) {
    this.init();
    
    if (!CONFIG.BATCH_PROCESS.ENABLED) {
      console.log('[ReportOrchestrator] Batch processing is disabled');
      return { total: 0, success: 0, failed: 0, errors: [] };
    }
    
    const dates = this._getBatchDates();
    const results = {
      total: dates.length,
      success: 0,
      failed: 0,
      errors: []
    };
    
    console.log(`[ReportOrchestrator] Starting batch processing for ${dates.length} dates`);
    
    // Process dates sequentially to avoid overwhelming the system
    const processNext = async (index) => {
      if (index >= dates.length) {
        EventBus.emit('BATCH_PROCESSING_COMPLETED', results);
        return results;
      }
      
      const date = dates[index];
      console.log(`[ReportOrchestrator] Processing ${index + 1}/${dates.length}: ${date}`);
      
      try {
        await this.generateDailyReport({ date: date });
        results.success++;
      } catch (error) {
        results.failed++;
        results.errors.push(`${date}: ${error.message}`);
      }
      
      // Process next date
      return processNext(index + 1);
    };
    
    return processNext(0);
  },
  
  /**
   * Register all event handlers
   * @private
   */
  _registerEventHandlers() {
    // Data reading phase
    EventBus.on('REPORT_GENERATION_STARTED', (context) => {
      try {
        const data = SheetAdapter.readData('MetaLog');
        let targetData = null;
        
        // Check if we should use latest data or find by date
        if (context.options.useLatestData) {
          targetData = this._getLatestData(data);
          if (targetData) {
            // Update context date to match the actual data date
            let actualDate = new Date(targetData.timestamp);
            if (targetData.timestamp.getHours() < 3) {
              actualDate.setDate(actualDate.getDate() - 1);
            }
            context.date = Utilities.formatDate(actualDate, CONFIG.TIME_ZONE, "yyyy/MM/dd");
            console.log(`[ReportOrchestrator] Using latest data, adjusted date to: ${context.date}`);
          }
        } else {
          targetData = this._findTargetData(data, context.date);
        }
        
        if (!targetData) {
          throw new Error(`No data found for date: ${context.date}`);
        }
        
        context.sourceData = targetData;
        EventBus.emit('DATA_READ_COMPLETED', context);
      } catch (error) {
        EventBus.emit('REPORT_GENERATION_FAILED', { 
          context: context, 
          error: error,
          phase: 'data_reading'
        });
      }
    });
    
    // Score calculation phase
    EventBus.on('DATA_READ_COMPLETED', (context) => {
      try {
        // Extract behaviors array
        const behaviors = context.sourceData.behaviors 
          ? context.sourceData.behaviors.split(',').map(b => b.trim()).filter(b => b)
          : [];
        
        // Calculate scores using factory
        const behaviorScore = ScoreCalculatorFactory.calculate('behavior', behaviors);
        const sleepScore = ScoreCalculatorFactory.calculate('sleep', {
          start: context.sourceData.sleepStart,
          end: context.sourceData.sleepEnd,
          quality: context.sourceData.sleepQuality
        });
        
        context.scores = {
          behavior: behaviorScore,
          sleep: sleepScore
        };
        
        EventBus.emit('SCORES_CALCULATED', context);
      } catch (error) {
        EventBus.emit('REPORT_GENERATION_FAILED', { 
          context: context, 
          error: error,
          phase: 'score_calculation'
        });
      }
    });
    
    // Prompt building phase
    EventBus.on('SCORES_CALCULATED', (context) => {
      try {
        const prompt = PromptBuilderService.buildDailyPrompt(
          context.sourceData,
          context.scores
        );
        
        context.prompt = prompt;
        EventBus.emit('PROMPT_READY', context);
      } catch (error) {
        EventBus.emit('REPORT_GENERATION_FAILED', { 
          context: context, 
          error: error,
          phase: 'prompt_building'
        });
      }
    });
    
    // API call phase
    EventBus.on('PROMPT_READY', (context) => {
      ApiService.callLLM(context.prompt)
        .then(analysis => {
          context.analysis = analysis;
          EventBus.emit('ANALYSIS_COMPLETED', context);
        })
        .catch(error => {
          EventBus.emit('REPORT_GENERATION_FAILED', { 
            context: context, 
            error: error,
            phase: 'api_call'
          });
        });
    });
    
    // Save to sheet phase
    EventBus.on('ANALYSIS_COMPLETED', (context) => {
      try {
        const reportData = {
          timestamp: new Date(),
          date: new Date(context.date),
          analysis: JSON.stringify(context.analysis, null, 2),
          behaviorTotal: context.scores.behavior.total || 0,
          behaviorPositive: context.scores.behavior.details?.positive || 0,
          behaviorNegative: context.scores.behavior.details?.negative || 0,
          behaviorRaw: context.scores.behavior.details?.rawScore || 0,
          behaviorGoal: context.scores.behavior.details?.goal || 0,
          sleepTotal: context.scores.sleep.total || 0,
          sleepDuration: context.scores.sleep.details?.duration?.score || 0,
          sleepQuality: context.scores.sleep.details?.quality?.score || 0,
          sleepRegularity: context.scores.sleep.details?.regularity?.score || 0,
          behaviorScoreVersion: ScoreCalculatorFactory.activeVersions.behavior,
          sleepScoreVersion: ScoreCalculatorFactory.activeVersions.sleep,
          analysisVersion: CONFIG.ANALYSIS_VERSION
        };
        
        // Check if we should overwrite existing
        const existingRow = SheetAdapter.findRowByDate(CONFIG.OUTPUT.DAILY_SHEET, context.date);
        
        if (existingRow && CONFIG.OUTPUT.OVERWRITE_EXISTING) {
          SheetAdapter.writeData(CONFIG.OUTPUT.DAILY_SHEET, [reportData], { 
            rowIndex: existingRow 
          });
          context.wasUpdated = true;
        } else if (!existingRow) {
          SheetAdapter.writeData(CONFIG.OUTPUT.DAILY_SHEET, [reportData], { 
            append: true 
          });
          context.wasUpdated = true;
        } else {
          context.wasUpdated = false;
        }
        
        context.reportData = reportData;
        EventBus.emit('REPORT_SAVED', context);
      } catch (error) {
        EventBus.emit('REPORT_GENERATION_FAILED', { 
          context: context, 
          error: error,
          phase: 'save_to_sheet'
        });
      }
    });
    
    // Email sending phase
    EventBus.on('REPORT_SAVED', (context) => {
      // Check if email should be sent
      const shouldSendEmail = CONFIG.ENABLE_DAILY_EMAIL && 
        (context.wasUpdated || context.options.forceEmail);
      
      if (!shouldSendEmail) {
        console.log('[ReportOrchestrator] Skipping email - not enabled or not updated');
        context.emailSent = false;
        context.emailSkipped = true;
        EventBus.emit('REPORT_GENERATION_COMPLETED', context);
        return;
      }
      
      console.log('[ReportOrchestrator] Sending email - wasUpdated:', context.wasUpdated, 'forceEmail:', context.options.forceEmail);
      
      EmailService.sendDailyReport({
        date: context.date,
        analysis: context.analysis,
        scores: context.scores,
        mood: context.sourceData.mood
      })
        .then(() => {
          context.emailSent = true;
          EventBus.emit('REPORT_GENERATION_COMPLETED', context);
        })
        .catch(error => {
          // Email failure is not critical
          console.error('[ReportOrchestrator] Email sending failed:', error);
          context.emailSent = false;
          context.emailError = error;
          EventBus.emit('REPORT_GENERATION_COMPLETED', context);
        });
    });
    
    // Error handling
    EventBus.on('ERROR_OCCURRED', (error) => {
      console.error('[ReportOrchestrator] Error occurred:', error);
    });
    
    // Schema mismatch handling
    EventBus.on('SCHEMA_MISMATCH_DETECTED', (data) => {
      console.warn('[ReportOrchestrator] Schema mismatch detected:', data);
      // Could trigger auto-migration or notification here
    });
  },
  
  /**
   * Get current date adjusted for report generation
   * @private
   */
  _getCurrentDate() {
    const now = new Date();
    // Adjust for early morning entries (0:00-3:00 counts as previous day)
    if (now.getHours() < 3) {
      now.setDate(now.getDate() - 1);
    }
    return Utilities.formatDate(now, CONFIG.TIME_ZONE, "yyyy/MM/dd");
  },
  
  /**
   * Find target data for specific date
   * @private
   */
  _findTargetData(data, targetDate) {
    // Look for data from newest to oldest
    for (let i = data.length - 1; i >= 0; i--) {
      const entry = data[i];
      if (entry.timestamp instanceof Date) {
        let entryDate = new Date(entry.timestamp);
        
        // Apply date adjustment for early morning entries (0:00-3:00 counts as previous day)
        if (entry.timestamp.getHours() < 3) {
          entryDate.setDate(entryDate.getDate() - 1);
        }
        
        const formattedDate = Utilities.formatDate(entryDate, CONFIG.TIME_ZONE, "yyyy/MM/dd");
        if (formattedDate === targetDate) {
          return entry;
        }
      }
    }
    return null;
  },
  
  /**
   * Get the latest data entry (most recent)
   * @private
   */
  _getLatestData(data) {
    if (data.length === 0) return null;
    
    // Return the last entry (most recent)
    const latestEntry = data[data.length - 1];
    
    if (latestEntry.timestamp instanceof Date) {
      console.log(`[ReportOrchestrator] Using latest entry from: ${Utilities.formatDate(latestEntry.timestamp, CONFIG.TIME_ZONE, "yyyy/MM/dd HH:mm")}`);
      return latestEntry;
    }
    
    return null;
  },
  
  /**
   * Get dates for batch processing
   * @private
   */
  _getBatchDates() {
    const { START, END } = CONFIG.BATCH_PROCESS.DATE_RANGE;
    const dates = [];
    
    const currentDate = new Date(START);
    const endDate = new Date(END);
    
    while (currentDate <= endDate) {
      dates.push(Utilities.formatDate(currentDate, CONFIG.TIME_ZONE, "yyyy/MM/dd"));
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    if (CONFIG.BATCH_PROCESS.SKIP_EXISTING) {
      const existingDates = this._getExistingReportDates();
      return dates.filter(date => !existingDates.has(date));
    }
    
    return dates;
  },
  
  /**
   * Get existing report dates
   * @private
   */
  _getExistingReportDates() {
    const existingDates = new Set();
    
    try {
      const reports = SheetAdapter.readData(CONFIG.OUTPUT.DAILY_SHEET);
      reports.forEach(report => {
        if (report.date instanceof Date) {
          const dateStr = Utilities.formatDate(report.date, CONFIG.TIME_ZONE, "yyyy/MM/dd");
          existingDates.add(dateStr);
        }
      });
    } catch (error) {
      console.warn('[ReportOrchestrator] Could not read existing reports:', error);
    }
    
    return existingDates;
  },
  
  /**
   * Calculate scores only (no LLM, no email, no sheet write)
   * @param {Object} options { date: 'yyyy/MM/dd', useLatestData: boolean }
   * @returns {Promise<Object>} { date, scores }
   */
  async calculateScoresOnly(options = {}) {
    this.init();

    const targetDate = options.date || this._getCurrentDate();
    const data = SheetAdapter.readData(CONFIG.SHEET_NAME);

    // Find target data (reuse existing helper)
    let targetData = null;
    if (options.useLatestData) {
      targetData = this._getLatestData(data);
    } else {
      targetData = this._findTargetData(data, targetDate);
    }
    if (!targetData) {
      throw new Error(`No data found for date: ${targetDate}`);
    }

    // Calculate scores
    // Behaviors array
    const behaviors = targetData.behaviors
      ? targetData.behaviors.split(',').map(b => b.trim()).filter(Boolean)
      : [];

    const behaviorScore = ScoreCalculatorFactory.calculate('behavior', behaviors);
    const sleepScore = ScoreCalculatorFactory.calculate('sleep', {
      start: targetData.sleepStart,
      end: targetData.sleepEnd,
      quality: targetData.sleepQuality
    });

    return {
      date: targetDate,
      scores: {
        behavior: behaviorScore,
        sleep: sleepScore
      }
    };
  },

  /**
   * Generate a weekly report
   * @param {Object} options - Generation options
   * @returns {Promise} Report generation result
   */
  generateWeeklyReport(options = {}) {
    this.init();
    
    const context = {
      startTime: new Date(),
      options: Object.assign({ reportType: 'weekly', weekOffset: 0 }, options),
      reportType: 'weekly',
      results: {}
    };
    
    // Calculate week range
    const now = new Date();
    const weekOffset = context.options.weekOffset || 0;
    
    // Fix: Correct week calculation
    // For weekOffset = -1 (previous week), we want to go back 7 days from start of current week
    // For weekOffset = 0 (current week), we want start of current week
    const daysToSubtract = now.getDay() + (weekOffset * -7);
    const startOfWeek = new Date(now.getTime() - daysToSubtract * 24 * 60 * 60 * 1000);
    const endOfWeek = new Date(startOfWeek.getTime() + 6 * 24 * 60 * 60 * 1000);
    
    context.weekRange = {
      start: Utilities.formatDate(startOfWeek, CONFIG.TIME_ZONE, "yyyy/MM/dd"),
      end: Utilities.formatDate(endOfWeek, CONFIG.TIME_ZONE, "yyyy/MM/dd")
    };
    
    console.log(`[ReportOrchestrator] Starting weekly report generation for ${context.weekRange.start} - ${context.weekRange.end}`);
    
    // Register weekly event handlers if not already done
    this._registerWeeklyEventHandlers();
    
    // Return a promise that resolves when the report is complete
    return new Promise((resolve, reject) => {
      const completeHandler = (result) => {
        EventBus.off('WEEKLY_REPORT_GENERATION_COMPLETED', completeHandler);
        EventBus.off('WEEKLY_REPORT_GENERATION_FAILED', failHandler);
        resolve(result);
      };
      
      const failHandler = (error) => {
        EventBus.off('WEEKLY_REPORT_GENERATION_COMPLETED', completeHandler);
        EventBus.off('WEEKLY_REPORT_GENERATION_FAILED', failHandler);
        console.error('[ReportOrchestrator] Weekly report generation failed:', error);
        reject(error);
      };
      
      EventBus.on('WEEKLY_REPORT_GENERATION_COMPLETED', completeHandler);
      EventBus.on('WEEKLY_REPORT_GENERATION_FAILED', failHandler);
      
      // Start the weekly report generation
      EventBus.emit('WEEKLY_REPORT_GENERATION_STARTED', context);
    });
  },

  /**
   * Register weekly event handlers - only registers once
   * @private
   */
  _registerWeeklyEventHandlers() {
    if (this._weeklyHandlersRegistered) return;
    
    // Data collection phase
    EventBus.on('WEEKLY_REPORT_GENERATION_STARTED', (context) => {
      try {
        console.log('[ReportOrchestrator] Starting weekly data collection...');
        const weeklyData = this._collectWeeklyData(context.weekRange);
        context.weeklyData = weeklyData;
        EventBus.emit('WEEKLY_DATA_COLLECTED', context);
      } catch (error) {
        console.error('[ReportOrchestrator] Weekly data collection failed:', error);
        EventBus.emit('WEEKLY_REPORT_GENERATION_FAILED', {
          context: context,
          error: error,
          phase: 'data_collection'
        });
      }
    });

    // Score aggregation phase
    EventBus.on('WEEKLY_DATA_COLLECTED', (context) => {
      try {
        console.log(`[ReportOrchestrator] Collected ${context.weeklyData.dailyData.length} days of data for week ${context.weekRange.start} - ${context.weekRange.end}`);
        const aggregatedScores = this._aggregateWeeklyScores(context.weeklyData);
        context.aggregatedScores = aggregatedScores;
        EventBus.emit('WEEKLY_SCORES_AGGREGATED', context);
      } catch (error) {
        console.error('[ReportOrchestrator] Score aggregation failed:', error);
        EventBus.emit('WEEKLY_REPORT_GENERATION_FAILED', {
          context: context,
          error: error,
          phase: 'score_aggregation'
        });
      }
    });

    // Prompt building phase
    EventBus.on('WEEKLY_SCORES_AGGREGATED', (context) => {
      try {
        console.log('[ReportOrchestrator] Building weekly prompt...');
        const prompt = PromptBuilderService.buildWeeklyPrompt(context);
        context.results.prompt = prompt;
        EventBus.emit('WEEKLY_PROMPT_READY', context);
      } catch (error) {
        console.error('[ReportOrchestrator] Prompt building failed:', error);
        EventBus.emit('WEEKLY_REPORT_GENERATION_FAILED', {
          context: context,
          error: error,
          phase: 'weekly_prompt_building'
        });
      }
    });

    // API call phase with better error handling
    EventBus.on('WEEKLY_PROMPT_READY', async (context) => {
      try {
        console.log('[ReportOrchestrator] Sending weekly prompt to API...');
        console.log('[ReportOrchestrator] Prompt length:', context.results.prompt.length);
        
        const response = await ApiService.callLLM(context.results.prompt, { 
          systemMessage: PromptBuilderService.getSystemMessage('weekly') 
        });
        context.results.analysis = response;
        EventBus.emit('WEEKLY_ANALYSIS_RECEIVED', context);
      } catch (error) {
        console.error('[ReportOrchestrator] API call failed:', error);
        console.error('[ReportOrchestrator] Error details:', {
          name: error.name,
          message: error.message
        });
        EventBus.emit('WEEKLY_REPORT_GENERATION_FAILED', {
          context: context,
          error: error,
          phase: 'api_call'
        });
      }
    });

    // Email sending phase
    EventBus.on('WEEKLY_ANALYSIS_RECEIVED', (context) => {
      try {
        console.log('[ReportOrchestrator] Sending weekly email...');
        
        // Prepare report data for email service
        const reportData = {
          weekStart: context.weekRange.start,
          weekEnd: context.weekRange.end,
          analysis: context.results.analysis,
          aggregatedScores: context.aggregatedScores,
          daysWithData: context.weeklyData.dailyData.length,
          totalDays: 7,
          weeklyData: context.weeklyData
        };
        
        const emailSent = EmailService.sendWeeklyReport(reportData);
        context.results.emailSent = emailSent;
        
        console.log('[ReportOrchestrator] Weekly report generation completed successfully');
        EventBus.emit('WEEKLY_REPORT_GENERATION_COMPLETED', {
          weekRange: context.weekRange,
          emailSent: emailSent,
          analysis: context.results.analysis
        });
      } catch (error) {
        console.error('[ReportOrchestrator] Email sending failed:', error);
        EventBus.emit('WEEKLY_REPORT_GENERATION_FAILED', {
          context: context,
          error: error,
          phase: 'email_sending'
        });
      }
    });
    
    this._weeklyHandlersRegistered = true;
  },

  /**
   * Collect weekly data from the sheet
   * @private
   */
  _collectWeeklyData(weekRange) {
    // Use the same data reading approach as daily reports
    const data = SheetAdapter.readData('MetaLog');
    const dailyData = [];
    
    // Check if data exists and is an array
    if (!data || !Array.isArray(data)) {
      console.log('[ReportOrchestrator] No data found in MetaLog sheet');
      return {
        weekStart: weekRange.start,
        weekEnd: weekRange.end,
        dailyData: []
      };
    }
    
    console.log(`[ReportOrchestrator] Found ${data.length} total entries in MetaLog`);
    
    // Filter data to the week range - use same logic as daily reports
    const startDate = new Date(weekRange.start);
    const endDate = new Date(weekRange.end);
    endDate.setHours(23, 59, 59, 999); // Include the entire end date
    
    data.forEach(entry => {
      if (!entry || !entry.timestamp) return;
      
      // Use the same timestamp logic as daily reports
      if (!(entry.timestamp instanceof Date)) {
        console.log('[ReportOrchestrator] Skipping entry with invalid timestamp:', entry);
        return;
      }
      
      let entryDate = new Date(entry.timestamp);
      
      // Apply same date adjustment as daily reports (early morning entries count as previous day)
      if (entry.timestamp.getHours() < 3) {
        entryDate.setDate(entryDate.getDate() - 1);
      }
      
      // Check if entry falls within the week range
      if (entryDate < startDate || entryDate > endDate) {
        return;
      }
      
      // Calculate scores for this day using the same logic as daily reports
      const behaviors = entry.behaviors 
        ? entry.behaviors.split(',').map(b => b.trim()).filter(Boolean)
        : [];
      
      const behaviorScore = ScoreCalculatorFactory.calculate('behavior', behaviors);
      const sleepScore = ScoreCalculatorFactory.calculate('sleep', {
        start: entry.sleepStart,
        end: entry.sleepEnd,
        quality: entry.sleepQuality
      });
      
      // Get notes field
      const notes = entry.note || '';
      
      const adjustedDateStr = Utilities.formatDate(entryDate, CONFIG.TIME_ZONE, "yyyy/MM/dd");
      
      dailyData.push({
        date: adjustedDateStr,
        adjustedDate: adjustedDateStr,
        timestamp: entry.timestamp,
        behaviorTotal: behaviorScore.total,
        behaviorRaw: behaviorScore.details?.rawScore || 0,
        sleepTotal: sleepScore.total,
        notes: notes
      });
    });
    
    console.log(`[ReportOrchestrator] Filtered to ${dailyData.length} entries for week ${weekRange.start} - ${weekRange.end}`);
    
    return {
      weekStart: weekRange.start,
      weekEnd: weekRange.end,
      dailyData: dailyData
    };
  },

  /**
   * Aggregate weekly scores
   * @private
   */
  _aggregateWeeklyScores(weeklyData) {
    const { dailyData } = weeklyData;
    
    if (dailyData.length === 0) {
      return {
        avgBehaviorTotal: 0,
        avgBehaviorRaw: 0,
        avgSleepTotal: 0,
        behaviorTrend: '無數據',
        sleepTrend: '無數據',
        totalDays: 7
      };
    }
    
    const behaviorTotals = dailyData.map(day => day.behaviorTotal || 0);
    const behaviorRaws = dailyData.map(day => day.behaviorRaw || 0);
    const sleepTotals = dailyData.map(day => day.sleepTotal || 0);
    
    const avgBehaviorTotal = behaviorTotals.reduce((a, b) => a + b, 0) / behaviorTotals.length;
    const avgBehaviorRaw = behaviorRaws.reduce((a, b) => a + b, 0) / behaviorRaws.length;
    const avgSleepTotal = sleepTotals.reduce((a, b) => a + b, 0) / sleepTotals.length;
    
    // Simple trend analysis
    const behaviorTrend = this._calculateTrend(behaviorTotals);
    const sleepTrend = this._calculateTrend(sleepTotals);
    
    return {
      avgBehaviorTotal,
      avgBehaviorRaw,
      avgSleepTotal,
      behaviorTrend,
      sleepTrend,
      totalDays: 7
    };
  },

  /**
   * Calculate trend for a series of values
   * @private
   */
  _calculateTrend(values) {
    if (values.length < 2) return '無法判斷';
    
    const first = values[0];
    const last = values[values.length - 1];
    const diff = last - first;
    
    if (diff > 5) return '改善中';
    if (diff < -5) return '需關注';
    return '穩定';
  }
}; 
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
    
    // Start the event chain
    EventBus.emit('REPORT_GENERATION_STARTED', context);
    
    // Return a promise that resolves when the report is complete
    return new Promise((resolve, reject) => {
      const completeHandler = (result) => {
        EventBus.off('REPORT_GENERATION_COMPLETED', completeHandler);
        EventBus.off('REPORT_GENERATION_FAILED', failHandler);
        resolve(result);
      };
      
      const failHandler = (error) => {
        EventBus.off('REPORT_GENERATION_COMPLETED', completeHandler);
        EventBus.off('REPORT_GENERATION_FAILED', failHandler);
        reject(error);
      };
      
      EventBus.on('REPORT_GENERATION_COMPLETED', completeHandler);
      EventBus.on('REPORT_GENERATION_FAILED', failHandler);
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
        const targetData = this._findTargetData(data, context.date);
        
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
          sleepRegularity: context.scores.sleep.details?.regularity?.score || 0
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
      if (!CONFIG.ENABLE_DAILY_EMAIL || !context.wasUpdated) {
        EventBus.emit('REPORT_GENERATION_COMPLETED', context);
        return;
      }
      
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
    // Adjust for early morning entries
    if (now.getHours() < 2) {
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
        
        // Apply date adjustment for early morning entries
        if (entry.timestamp.getHours() < 2) {
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
  }
}; 
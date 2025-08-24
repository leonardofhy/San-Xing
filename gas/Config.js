// Universal Configuration for Meta-Awareness System
// Version 2.0: Simplified for new architecture

const CONFIG = {
  // --- Core Settings ---
  SHEET_NAME: "MetaLog",  // Source data sheet
  RECIPIENT_EMAIL: PropertiesService.getScriptProperties().getProperty('RECIPIENT_EMAIL'),
  TIME_ZONE: "Asia/Taipei",

  // --- Sheet Names ---
  OUTPUT: {
    DAILY_SHEET: "DailyReport",      // Daily report output
    WEEKLY_SHEET: "WeeklyReport",  // Weekly report output
    BEHAVIOR_SHEET: "BehaviorScores", // Behavior scores (no space for consistency)
    
    // Behavior Settings
    OVERWRITE_EXISTING: true,         // Whether to overwrite existing reports
    AUTO_CREATE_SHEETS: true,         // Auto-create sheets if not exist
    AUTO_SYNC_HEADERS: true          // Auto-sync headers
  },

  // --- API Settings ---
  DEEPSEEK_API_KEY: PropertiesService.getScriptProperties().getProperty('DEEPSEEK_API_KEY'),
  DAILY_MODEL: "deepseek-reasoner",
  WEEKLY_MODEL: "deepseek-reasoner",
  BEHAVIOR_SCORE_MODEL: "deepseek-chat",

  // --- Versioning ---
  VERSIONS: {
    BEHAVIOR_SCORE: "1.0.0",   // MAJOR.MINOR.PATCH, update when behavior scoring logic changes
    SLEEP_SCORE:    "1.0.0",   // update when sleep scoring logic changes
    ANALYSIS:       "1.0.0"    // update when prompt / model changes affect analysis output
  },

  // (Legacy alias) Kept for backward-compatibility with existing code. Prefer CONFIG.VERSIONS.ANALYSIS.
  ANALYSIS_VERSION: "1.0.0",  

  // --- Email Settings ---
  ENABLE_DAILY_EMAIL: true,
  DAILY_EMAIL_SUBJECT: "{date} 每日摘要｜心情: {mood}｜行為: {behaviorScore}｜睡眠: {sleepScore}",

  // --- Report Generation Settings ---
  DAILY_REPORT_DATE: {
    MODE: "latest",              // "latest" or "specific"
    SPECIFIC_DATE: "2024-05-30"  // Used when MODE is "specific"
  },

  // --- Batch Processing ---
  BATCH_PROCESS: {
    ENABLED: true,
    DATE_RANGE: {
      START: "2025-04-21",
      END: "2025-06-21"
    },
    SKIP_EXISTING: true,
    DELAY_BETWEEN_CALLS: 1000  // Delay between API calls (ms)
  },

  // --- Weekly Report Settings ---
  ENABLE_WEEKLY_EMAIL: true,
  WEEKLY_EMAIL_SUBJECT: "週報告 | {dateRange}",

  // Add weekly report configuration:
  WEEKLY_REPORT: {
    WEEK_START_DAY: 0, // 0=Sunday, 1=Monday
    INCLUDE_DAILY_BREAKDOWN: true,
    MIN_DAYS_REQUIRED: 5, // Minimum days of data to generate report
  },

  // --- Schema Versions ---
  SCHEMA_VERSIONS: {
    MetaLog: "v1",
    DailyReport: "v1", 
    BehaviorScores: "v1"
  }
};

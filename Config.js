// Universal Configuration for Meta-Awareness System
// Version 1.1: Added Email Subject Templates

const CONFIG = {
  // --- Data & User Settings ---
  SHEET_NAME: "MetaLog",
  RECIPIENT_EMAIL: PropertiesService.getScriptProperties().getProperty('RECIPIENT_EMAIL'),
  TIME_ZONE: "Asia/Taipei",

  // --- Output Settings ---
  OUTPUT: {
    // Sheet Names
    DAILY_SHEET: "Daily Report",    // Daily report output sheet name
    WEEKLY_SHEET: "WeeklyReport",  // Weekly report output sheet name
    BEHAVIOR_SHEET: "Behavior Scores",  // Behavior classification sheet name
    
    // Data Management
    OVERWRITE_EXISTING: true,      // Whether to overwrite existing data
    TIMESTAMP_COLUMN: "Last Updated",  // Timestamp column name
    DATE_COLUMN: "Date",           // Date column name
    TIMESTAMP_COLUMN_INDEX: 1      // Timestamp column position (0-based)
  },

  // --- API Keys & Models ---
  DEEPSEEK_API_KEY: PropertiesService.getScriptProperties().getProperty('DEEPSEEK_API_KEY'),
  DAILY_MODEL: "deepseek-reasoner",
  WEEKLY_MODEL: "deepseek-reasoner",
  BEHAVIOR_SCORE_MODEL: "deepseek-chat",

  // --- [New] Email Subject Templates ---
  // You can freely modify here, {date} and {mood} will be automatically replaced
  DAILY_EMAIL_SUBJECT: "Daily Growth Dashboard | {date} | Behavior Efficiency {behaviorScore}/100 | Sleep Health {sleepScore}/100",
  
  // {dateRange} will be automatically replaced
  WEEKLY_EMAIL_SUBJECT: "Weekly Growth Trend Analysis | {dateRange}",

  // --- [New] Email Control Settings ---
  ENABLE_DAILY_EMAIL: true,  // Control whether to send daily report emails

  // --- [New] Date Control Settings ---
  DAILY_REPORT_DATE: {
    MODE: "latest",  // Options: "latest" or "specific"
    SPECIFIC_DATE: "2024-05-30"  // Used when MODE is "specific", format: YYYY-MM-DD
  },

  // --- [New] Batch Processing Settings ---
  BATCH_PROCESS: {
    ENABLED: true,  // Whether to enable batch processing
    DATE_RANGE: {
      START: "2025-06-08",  // Start date, format: YYYY-MM-DD
      END: "2025-06-13"     // End date, format: YYYY-MM-DD
    },
    SKIP_EXISTING: true,    // Whether to skip existing reports
    BATCH_SIZE: 7,          // Number of days to process per batch
    DELAY_BETWEEN_BATCHES: 1000  // Delay between batches (milliseconds)
  }
};

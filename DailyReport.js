/**
 * Meta-Awareness Daily Report Automation Script
 * Version: 7.3.0
 * Last Updated: 2025-06-16
 * This version completes the architectural refactoring by using dedicated service objects
 * for all calculations (BehaviorScoreService, SleepQualityService).
 */

// =================================
// Main Service
// =================================

const DailyReportService = {
  
  /**
   * Generates a single daily summary report.
   * @param {Object} [options={}] - Optional parameters. Example: { date: '2025-06-10' }.
   * @returns {Object|null} The generated report object, or null on failure.
   */
  generateReport: function(options = {}) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sourceSheet = ss.getSheetByName(CONFIG.SHEET_NAME);
    if (!this._validateSheet(sourceSheet, `Source Sheet (${CONFIG.SHEET_NAME})`)) return null;

    const targetRowData = this._getSourceData(sourceSheet, options);
    if (!targetRowData) return null;
    
    const entry = this._extractDataFromRow(targetRowData.rowData, targetRowData.headers);
    
    // Call dedicated Service objects
    const behaviorBehaviors = entry.behavior ? entry.behavior.split(',').map(b => b.trim()).filter(b => b) : [];
    const behaviorScore = BehaviorScoreService.getUpToDateDailyScore(behaviorBehaviors);

    const sleepScore = SleepQualityService.calculateSleepHealthIndex({
      start: entry.sleepStart,
      end: entry.sleepEnd,
      quality: entry.sleepQuality
    });
    
    console.log('[Report] Processing log data:', JSON.stringify(entry, null, 2));
    console.log('[Report] Behavior score:', JSON.stringify(behaviorScore, null, 2));
    console.log('[Report] Sleep score:', JSON.stringify(sleepScore, null, 2));

    const prompt = this._buildDailyPrompt(entry, behaviorScore, sleepScore);
    const analysisJson = this._callApi(prompt);

    if (!analysisJson) {
      console.error(`[Report] LLM API call or JSON parsing failed after multiple attempts.`);
      return null;
    }

    const reportData = { 
      date: entry.date, 
      analysis: analysisJson, 
      behaviorScore, 
      sleepScore,
      mood: entry.mood 
    };

    const wasSheetUpdated = this._saveReportToSheet(ss, reportData);
    this._sendReportEmail(reportData, wasSheetUpdated);

    return reportData;
  },
  
  /**
   * Generates reports for a specified range of dates.
   * @returns {Object|null} A summary of the batch process results.
   */
  generateBatchReports: function() {
    if (!CONFIG.BATCH_PROCESS.ENABLED) {
      console.log('[Report] Batch processing is disabled. Please set BATCH_PROCESS.ENABLED = true in Config.js');
      return null;
    }

    const { START, END } = CONFIG.BATCH_PROCESS.DATE_RANGE;
    if (!START || !END || new Date(START) > new Date(END)) {
      console.error('[Report] Invalid batch processing date range. Please check Config.js.');
      return null;
    }

    const datesToProcess = this._getDatesForBatchProcessing(START, END);
    if (datesToProcess.length === 0) {
      console.log('[Report] No new data to process in the specified date range.');
      return { total: 0, success: 0, failed: 0, skipped: datesToProcess.skipped, errors: [] };
    }
    
    console.log(`[Report] Starting batch processing for ${datesToProcess.length} days...`);
    const results = { total: datesToProcess.length, success: 0, failed: 0, skipped: datesToProcess.skipped, errors: [] };

    for (const date of datesToProcess) {
      try {
        console.log(`--- Processing date: ${date} ---`);
        const result = this.generateReport({ date: date });
        
        if (result) {
          results.success++;
        } else {
          results.failed++;
          results.errors.push(`${date}: Processing failed`);
        }
        
      } catch (error) {
        results.failed++;
        results.errors.push(`${date}: ${error.message}`);
        console.error(`[Report] Critical error while processing ${date}: ${error.stack}`);
      }
    }
    
    console.log('\n[Report] Batch processing completed', JSON.stringify(results, null, 2));
    return results;
  },

  // =================================
  // Internal Helper Functions
  // =================================

  _getSourceData: function(sheet, options = {}) {
    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    let targetRowIndex;

    const mode = options.date ? "specific" : CONFIG.DAILY_REPORT_DATE.MODE;
    const specificDate = options.date 
      ? options.date.replace(/-/g, '/') 
      : CONFIG.DAILY_REPORT_DATE.SPECIFIC_DATE.replace(/-/g, '/');

    if (mode === "specific") {
      console.log(`[Report] Using specified date: ${specificDate}`);
      targetRowIndex = this._findRowByDate(sheet, specificDate, 1, this._sourceDateAdjuster);
      if (!targetRowIndex) {
        console.error(`[Report] Execution aborted: No data found for specified date ${specificDate}.`);
        return null;
      }
    } else {
      console.log('[Report] Using latest data');
      targetRowIndex = sheet.getLastRow();
    }
    
    const rowData = sheet.getRange(targetRowIndex, 1, 1, headers.length).getValues()[0];
    return { rowData, headers };
  },

  _extractDataFromRow: function(rowData, headers) {
    const dataMap = headers.reduce((map, header, index) => {
      map[header.trim()] = rowData[index];
      return map;
    }, {});
    
    const timestamp = new Date(dataMap['Timestamp']);
    const actualDate = this._sourceDateAdjuster(timestamp);
    
    return {
      date: Utilities.formatDate(actualDate, CONFIG.TIME_ZONE, "yyyy/MM/dd"),
      behavior: dataMap['今天完成了哪些？'],
      sleepStart: dataMap['昨晚實際入睡時間'],
      sleepEnd: dataMap['今天實際起床時間'],
      sleepPlanned: dataMap['今晚預計幾點入睡？'],
      sleepQuality: dataMap['昨晚睡眠品質如何？'],
      mood: dataMap['今日整體心情感受'] || 'N/A',
      energy: dataMap['今日整體精力水平如何？'],
      note: dataMap['今天想記點什麼？'],
      weight: (dataMap['體重紀錄'] !== null && dataMap['體重紀錄'] !== '') ? parseFloat(dataMap['體重紀錄']) : null,
      screenTime: dataMap['今日手機螢幕使用時間'] || null,
      topApps: dataMap['今日使用最多的 App'] || null
    };
  },
  
  _sourceDateAdjuster: function(timestamp) {
      let actualDate = new Date(timestamp);
      if (timestamp.getHours() < 2) {
        actualDate.setDate(actualDate.getDate() - 1);
      }
      return actualDate;
  },

  _findRowByDate: function(sheet, targetDate, dateColumnIndex, dateAdjustmentFn = null) {
    const lastRow = sheet.getLastRow();
    if (lastRow < 2) return null;
    
    const dateValues = sheet.getRange(2, dateColumnIndex, lastRow - 1, 1).getValues();
    
    for (let i = dateValues.length - 1; i >= 0; i--) { 
      const cellValue = dateValues[i][0];
      if (cellValue instanceof Date) {
        let dateToCompare = dateAdjustmentFn ? dateAdjustmentFn(cellValue) : cellValue;
        const rowDate = Utilities.formatDate(dateToCompare, CONFIG.TIME_ZONE, "yyyy/MM/dd");
        if (rowDate === targetDate) {
          return i + 2;
        }
      }
    }
    return null;
  },
  
  _getDatesForBatchProcessing: function(startStr, endStr) {
      const dates = [];
      const existingReports = new Set();
      let skippedCount = 0;

      if (CONFIG.BATCH_PROCESS.SKIP_EXISTING) {
          const ss = SpreadsheetApp.getActiveSpreadsheet();
          const outputSheet = ss.getSheetByName(CONFIG.OUTPUT.DAILY_SHEET);
          if (outputSheet && outputSheet.getLastRow() > 1) {
              const reportDates = outputSheet.getRange(2, 2, outputSheet.getLastRow() - 1, 1).getValues();
              reportDates.forEach(row => {
                  if (row[0] instanceof Date) {
                      existingReports.add(Utilities.formatDate(row[0], CONFIG.TIME_ZONE, "yyyy/MM/dd"));
                  }
              });
          }
      }

      const currentDate = new Date(startStr);
      const endDate = new Date(endStr);
      while (currentDate <= endDate) {
          const dateStr = Utilities.formatDate(currentDate, CONFIG.TIME_ZONE, "yyyy/MM/dd");
          if (!existingReports.has(dateStr)) {
              dates.push(dateStr);
          } else {
              skippedCount++;
          }
          currentDate.setDate(currentDate.getDate() + 1);
      }
      dates.skipped = skippedCount;
      return dates;
  },

  _saveReportToSheet: function(ss, data) {
    const outputSheet = ss.getSheetByName(CONFIG.OUTPUT.DAILY_SHEET) || ss.insertSheet(CONFIG.OUTPUT.DAILY_SHEET);
    const { date, analysis, behaviorScore, sleepScore } = data;
    const analysisText = analysis ? JSON.stringify(analysis, null, 2) : '';

    const expectedHeaders = [
      CONFIG.OUTPUT.TIMESTAMP_COLUMN, CONFIG.OUTPUT.DATE_COLUMN, 'AI Analysis',
      'Behavior Total', 'Behavior Positive', 'Behavior Negative', 'Behavior Raw', 'Behavior Goal',
      'Sleep Total', 'Sleep Duration', 'Sleep Quality', 'Sleep Regularity'
    ];
    
    const rowData = [
      new Date(), date, analysisText,
      behaviorScore.total || 0, behaviorScore.details?.positive || 0, behaviorScore.details?.negative || 0, 
      behaviorScore.details?.rawScore || 0, behaviorScore.details?.goal || 0,
      sleepScore.total || 0, sleepScore.details?.duration?.score || 0, sleepScore.details?.quality?.score || 0, sleepScore.details?.regularity?.score || 0
    ];

    this._ensureHeaders(outputSheet, expectedHeaders);
    
    const existingRow = this._findRowByDate(outputSheet, date, 2);
    
    if (existingRow && CONFIG.OUTPUT.OVERWRITE_EXISTING) {
      outputSheet.getRange(existingRow, 1, 1, rowData.length).setValues([rowData]);
      console.log(`[Report] Updated data for date ${date} (row: ${existingRow})`);
      return true;
    } else if (!existingRow) {
      outputSheet.appendRow(rowData);
      console.log(`[Report] Added new data for date ${date}`);
      return true;
    } else {
      console.log(`[Report] Skipped data for date ${date} (exists and overwrite not allowed)`);
      return false;
    }
  },

  _sendReportEmail: function(reportData, wasSheetUpdated) {
    if (!CONFIG.ENABLE_DAILY_EMAIL) {
      console.log(`[Report] Email sending is disabled (ENABLE_DAILY_EMAIL = false)`);
      return;
    }
    if (!wasSheetUpdated) {
      console.log(`[Report] Skipping email (data not updated)`);
      return;
    }
    
    const { date, analysis, behaviorScore, sleepScore, mood } = reportData;
    
    const subject = CONFIG.DAILY_EMAIL_SUBJECT
      .replace('{date}', date)
      .replace('{mood}', mood)
      .replace('{behaviorScore}', behaviorScore.total)
      .replace('{sleepScore}', sleepScore.total);

    const htmlReport = this._renderHtmlReport(date, analysis, behaviorScore, sleepScore);
    
    console.log(`[Report] Preparing to send email, subject: ${subject}`);
    const emailSent = this._sendEmailWithGmailLabel(CONFIG.RECIPIENT_EMAIL, subject, htmlReport);
    
    console.log(emailSent ? `[Report] Summary report sent successfully.` : `[Report] Email sending failed.`);
  },

  /**
   * [微優化] Builds the prompt for the LLM.
   * Repetitive logic for sleep duration text has been cleaned up.
   */
  _buildDailyPrompt: function(entry, behaviorScore, sleepScore) {
    const sleepDurationText = sleepScore.details.duration.hours !== undefined 
      ? `${sleepScore.details.duration.hours.toFixed(1)} 小時` 
      : "N/A";

    const sourceDataPrompt = `### 原始數據
- **日期**：${entry.date}
- **睡眠**：${entry.sleepStart || "未填"} 入睡，${entry.sleepEnd || "未填"} 起床。(計算出的睡眠時長約為 ${sleepDurationText})
- **主觀感受 (1-5分)**：睡眠品質 ${entry.sleepQuality || "未填"} 分，今日精力 ${entry.energy || "未填"} 分，今日心情 ${entry.mood || "未填"} 分。
${entry.weight ? `- **體重**：${entry.weight} kg` : ''}
- **行為紀錄 (原始清單)**：${entry.behavior || "無"}
- **自由敘述**：${entry.note || "無"}

### 系統評分
- **行為效率分數**：${behaviorScore.total}/100 (原始分: ${behaviorScore.details.rawScore})
  - 正向行為：${Object.entries(behaviorScore.details.behaviorScores || {}).filter(([_, score]) => score > 0).map(([behavior, score]) => `${behavior}(${score}分)`).join('、') || '無'}
  - 負向行為：${Object.entries(behaviorScore.details.behaviorScores || {}).filter(([_, score]) => score < 0).map(([behavior, score]) => `${behavior}(${score}分)`).join('、') || '無'}
- **睡眠健康指數**：${sleepScore.total}/100
  - 睡眠時長：${sleepScore.details.duration.evaluation} (${sleepScore.details.duration.score}分)
  - 睡眠品質：${sleepScore.details.quality.evaluation} (${sleepScore.details.quality.score}分)
  - 睡眠規律：${sleepScore.details.regularity.evaluation} (${sleepScore.details.regularity.score}分)`;

    const instructionPrompt = `### 分析指令
你是我的個人成長教練。請用溫暖、有洞察力且具啟發性的語氣，分析以上的日誌數據，並嚴格依照以下 JSON 結構回傳你的分析，不要包含任何 JSON 區塊外的文字或註解。

{
  "behaviorReview": {
    "title": "1. 行為盤點",
    "positive": ["將「行為紀錄 (原始清單)」中的正向行為智慧地分類並列在此處"],
    "negative": ["將「行為紀錄 (原始清單)」中的負向行為智慧地分類並列在此處"],
    "neutral": ["將「行為紀錄 (原始清單)」中的中性行為智慧地分類並列在此處"]
  },
  "sleepAnalysis": {
    "title": "2. 睡眠分析與洞察",
    "insight": "比較客觀睡眠時長 (${sleepDurationText}) 與主觀品質的關係，並提出洞察。",
    "recommendations": ["根據數據提供 1-2 個具體的睡眠改善建議"]
  },
  "statusSummary": {
    "title": "3. 今日狀態短評",
    "comment": "綜合心情、精力、行為，對今日的整體狀態給出一個總結性短評。",
    "highlights": ["點出 1-2 個本日的亮點行為"]
  },
  "coachFeedback": {
    "title": "4. AI 教練回饋與提問",
    "affirmation": "針對本日行為，給予 1 個正向肯定。",
    "suggestion": "針對本日行為，給予 1 個具體改善建議。",
    "opportunity": "從「自由敘述」中挖掘 1 個能將日常小事轉化為長期資產的「隱藏機會點」，此建議需與自由敘述高度相關。",
    "question": "最後，根據今天的整體紀錄，提出一個最值得我深入思考的開放式問題。"
  }
}`;
    
    return `你是我的個人成長教練，請用溫暖、有洞察力且具啟發性的語氣，分析以下日誌。\n\n${sourceDataPrompt}\n\n---\n\n${instructionPrompt}`;
  },
  
  _callApi: function(prompt) {
    const maxAttempts = 3;
    const delayBetweenAttempts = 2000;
    const url = "https://api.deepseek.com/chat/completions";

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const payload = { 
            model: CONFIG.DAILY_MODEL,
            messages: [
              { role: "system", content: "You are a helpful assistant who provides insightful analysis in Traditional Chinese. You must respond strictly in the JSON format requested by the user." },
              { role: "user", content: prompt }
            ], 
            response_format: { type: "json_object" },
            stream: false, 
            temperature: 0.7 
        };
        const options = { 
            method: "post", 
            contentType: "application/json", 
            headers: { Authorization: "Bearer " + CONFIG.DEEPSEEK_API_KEY }, 
            payload: JSON.stringify(payload), 
            muteHttpExceptions: true 
        };
        
        console.log(`[Report] API call attempt ${attempt}/${maxAttempts}...`);
        const response = UrlFetchApp.fetch(url, options);
        const responseCode = response.getResponseCode();
        const responseText = response.getContentText();

        if (responseCode === 200) {
          const parsedContent = JSON.parse(responseText.trim());
          const llmJsonString = parsedContent.choices[0].message.content;

          if (!llmJsonString) {
            throw new Error("API response content is empty.");
          }

          const finalJson = JSON.parse(llmJsonString);
          console.log('[Report] Successfully parsed API response JSON object.');
          return finalJson;

        } else {
          console.warn(`[Report] API request failed with status code ${responseCode}. Response: ${responseText}`);
          if (attempt < maxAttempts && responseCode >= 500) {
             Utilities.sleep(delayBetweenAttempts);
             continue;
          } else {
            return null;
          }
        }
      } catch (e) {
        console.warn(`[Report] API response parsing failed on attempt ${attempt}: ${e.message}`);
        if (attempt < maxAttempts) {
          Utilities.sleep(delayBetweenAttempts);
        }
      }
    }
    
    console.error(`[Report] Failed to successfully call API and parse JSON after ${maxAttempts} attempts.`);
    return null;
  },

  _renderHtmlReport: function(date, analysisJson, behaviorScore, sleepScore) {
      if (!analysisJson) {
        return `<h1>報告生成失敗</h1><p>無法從 AI 服務獲取有效的分析結果。</p>`;
      }
      
      const escapeHtml = (text) => {
        if (typeof text !== 'string') return '';
        return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
      };

      const createList = (items) => {
        if (!items || !Array.isArray(items) || items.length === 0) return '<li>無</li>';
        return items.map(item => `<li>${escapeHtml(item).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</li>`).join('');
      };
      
      const br = analysisJson.behaviorReview || {};
      const sa = analysisJson.sleepAnalysis || {};
      const ss = analysisJson.statusSummary || {};
      const cf = analysisJson.coachFeedback || {};

      const llmHtml = `
        <h2>${escapeHtml(br.title || '1. 行為盤點')}</h2>
        <ul>
          <li><strong>正向行為</strong>：${(br.positive && br.positive.length > 0) ? escapeHtml(br.positive.join('、')) : '無'}</li>
          <li><strong>負向行為</strong>：${(br.negative && br.negative.length > 0) ? escapeHtml(br.negative.join('、')) : '無'}</li>
          <li><strong>中性行為</strong>：${(br.neutral && br.neutral.length > 0) ? escapeHtml(br.neutral.join('、')) : '無'}</li>
        </ul>
        
        <h2>${escapeHtml(sa.title || '2. 睡眠分析與洞察')}</h2>
        <ul>
          ${sa.insight ? `<li>${escapeHtml(sa.insight)}</li>` : ''}
          ${createList(sa.recommendations)}
        </ul>
        
        <h2>${escapeHtml(ss.title || '3. 今日狀態短評')}</h2>
        <ul>
          ${ss.comment ? `<li>${escapeHtml(ss.comment)}</li>` : ''}
          ${ss.highlights && ss.highlights.length > 0 ? `<li><strong>亮點</strong>：${escapeHtml(ss.highlights.join('、'))}</li>` : ''}
        </ul>

        <div class="feedback-section">
          <h2>${escapeHtml(cf.title || '4. AI 教練回饋與提問')}</h2>
          <ul>
            ${cf.affirmation ? `<li><strong>肯定</strong>：${escapeHtml(cf.affirmation)}</li>` : ''}
            ${cf.suggestion ? `<li><strong>建議</strong>：${escapeHtml(cf.suggestion)}</li>` : ''}
            ${cf.opportunity ? `<li><strong>機會點</strong>：${escapeHtml(cf.opportunity)}</li>` : ''}
            ${cf.question ? `<li><strong>問題</strong>：${escapeHtml(cf.question)}</li>` : ''}
          </ul>
        </div>
      `;

      return `<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;line-height:1.7;color:#34495e;max-width:680px;margin:20px auto;padding:0;background-color:#f4f7f6}.container{background-color:#fff;padding:20px 30px 30px;border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,.06)}h1{color:#2c3e50;font-size:24px;border-bottom:2px solid #e0e0e0;padding-bottom:12px;margin:0 0 20px}h2{color:#2980b9;font-size:18px;margin-top:30px;margin-bottom:15px;border-left:4px solid #3498db;padding-left:12px;font-weight:600}ul{list-style-type:none;padding-left:5px;margin:0}li{margin-bottom:10px;padding-left:20px;position:relative}li::before{content:'•';color:#3498db;font-size:20px;position:absolute;left:0;top:-3px}strong{color:#c0392b;font-weight:600}.feedback-section{margin-top:30px;background-color:#e8f4fd;padding:20px;border-radius:8px;border:1px solid #d0e0f0}.feedback-section h2{margin-top:0;color:#2c3e50;border-color:#2980b9}.feedback-section li::before{color:#2980b9}.score-section{margin-top:20px;background-color:#f8f9fa;padding:15px;border-radius:8px;border:1px solid #e9ecef}.score-section h3{color:#2c3e50;margin-top:0;font-size:16px}.score-value{font-size:24px;color:#2980b9;font-weight:700;margin:10px 0}.score-details{font-size:14px;color:#7f8c8d}</style></head>
<body>
<div class="container"><h1>每日摘要報告 - ${date}</h1>
<div class="score-section"><h3>今日評分</h3>
<div class="score-value">行為效率分數：${behaviorScore.total}/100</div>
<div class="score-details">(原始分: ${behaviorScore.details.rawScore}, 正向: ${behaviorScore.details.positive}, 負向: ${behaviorScore.details.negative})</div>
<div class="score-value">睡眠健康指數：${sleepScore.total}/100</div>
<div class="score-details">(時長: ${sleepScore.details.duration.score}, 品質: ${sleepScore.details.quality.score}, 規律: ${sleepScore.details.regularity.score})</div>
</div>
${llmHtml}
</div></body></html>`;
  },
  
  _sendEmailWithGmailLabel: function(recipient, subject, htmlBody) {
    const maxAttempts = 4;
    const delayBetweenAttempts = 3000;

    try {
        GmailApp.sendEmail(recipient, subject, "", { htmlBody: htmlBody });
        console.log('[Report] Email sent, now attempting to find and apply label...');

        const sanitizedSubject = subject.replace(/[|]/g, ' ').replace(/\s+/g, ' ').trim();
        const searchQuery = `subject:("${sanitizedSubject}") to:(${recipient}) from:me newer_than:2m`;
        let threads = [];
        
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            console.log(`[Report] Label attempt ${attempt}/${maxAttempts}: Searching for email...`);
            
            if (attempt > 1) {
              Utilities.sleep(delayBetweenAttempts);
            } else {
              Utilities.sleep(2000);
            }

            threads = GmailApp.search(searchQuery, 0, 1);

            if (threads.length > 0) {
                console.log(`[Report] Email found successfully!`);
                const labelName = "Meta-Awareness/Daily";
                let label = GmailApp.getUserLabelByName(labelName) || GmailApp.createLabel(labelName);
                threads[0].addLabel(label);
                console.log(`[Report] Successfully applied label '${labelName}' to email`);
                return true;
            }
            
            if (attempt < maxAttempts) {
                console.log(`[Report] Email not found on attempt ${attempt}, retrying in ${delayBetweenAttempts / 1000} seconds...`);
            }
        }

        console.error(`[Report] Failed to find recently sent email to apply label after ${maxAttempts} attempts. Search query: ${searchQuery}`);
        return false;

    } catch (error) {
        console.error(`[Report] Error occurred while sending email or applying label: ${error.stack}`);
        return false;
    }
  },

  _validateSheet: function(sheet, sheetIdentifier) {
    if (!sheet) {
      console.error(`[Report] Execution aborted: ${sheetIdentifier} not found!`);
      return false;
    }
    if (sheet.getLastRow() < 2) {
      console.log(`[Report] Execution aborted: ${sheetIdentifier} is empty.`);
      return false;
    }
    return true;
  },

  _ensureHeaders: function(sheet, expectedHeaders) {
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(expectedHeaders);
      console.log(`[Report] Added header row to '${sheet.getName()}'`);
    } else {
      const currentHeaders = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
      if (JSON.stringify(currentHeaders) !== JSON.stringify(expectedHeaders)) {
        sheet.getRange(1, 1, 1, expectedHeaders.length).setValues([expectedHeaders]);
        console.log(`[Report] Updated header row in '${sheet.getName()}'`);
      }
    }
  }
};


// =================================
// Runnable Triggers
// =================================
// These simple functions serve as entry points for running from the Apps Script editor or triggers.

function runDailyReportGeneration() {
  DailyReportService.generateReport();
}

function runBatchReportGeneration() {
  DailyReportService.generateBatchReports();
}
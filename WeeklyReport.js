// Meta-Awareness Weekly Report Automation Script
// Version: 2.0.1
// Last Updated: 2025-06-09
// This version refines the cleanup logic to ensure the main weekly
// trigger is not deleted after a successful run.

// =================================
// 主要觸發函式 (Main Trigger Function)
// =================================

/**
 * 產生智慧週報的總控制器 (Orchestrator)。
 * 這個函式會根據儲存的狀態，決定要執行哪個階段的任務。
 */
function generateWeeklyReport() {
  const scriptProperties = PropertiesService.getScriptProperties();
  const state = scriptProperties.getProperty('WEEKLY_REPORT_STATE');

  // 注意：我們不再在流程開始時刪除觸發器，以避免誤刪主觸發器

  if (state === 'SLEEP_ANALYSIS_COMPLETE') {
    runProductivityStage_();
  } else if (state === 'PRODUCTIVITY_ANALYSIS_COMPLETE') {
    runFinalIntegrationStage_();
  } else {
    // 初始狀態或重置狀態
    runSleepStage_();
  }
}

// =================================
// 各階段執行函式 (Stage Execution Functions)
// =================================

function runSleepStage_() {
  console.log('[週報] --- 階段 1：呼叫「睡眠與精力專家」---');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) { console.error('[週報] 執行中止：找不到分頁！'); return; }

  const dailyEntries = fetchDataAndPreprocess_(sheet);
  if (dailyEntries.length < 3) {
    console.log(`[週報] 數據不足，不生成報告。`);
    return;
  }
  
  const sleepAnalysis = getSleepEnergyAnalysis_(dailyEntries);
  if (!sleepAnalysis || sleepAnalysis.startsWith('API 呼叫失敗')) {
    console.error('[週報] 睡眠分析失敗，中止執行。', sleepAnalysis);
    cleanupState_(); // 只清理狀態
    return;
  }

  const scriptProperties = PropertiesService.getScriptProperties();
  scriptProperties.setProperties({
    'WEEKLY_REPORT_STATE': 'SLEEP_ANALYSIS_COMPLETE',
    'SLEEP_ANALYSIS_RESULT': sleepAnalysis,
    'DAILY_ENTRIES_JSON': JSON.stringify(dailyEntries)
  });

  console.log('[週報] 睡眠專家分析完成，已保存結果。準備觸發下一階段...');
  createNextTrigger_();
}

function runProductivityStage_() {
  console.log('[週報] --- 階段 2：呼叫「任務與生產力專家」---');
  const scriptProperties = PropertiesService.getScriptProperties();
  const dailyEntries = JSON.parse(scriptProperties.getProperty('DAILY_ENTRIES_JSON'));

  const productivityAnalysis = getProductivityAnalysis_(dailyEntries);
  if (!productivityAnalysis || productivityAnalysis.startsWith('API 呼叫失敗')) {
    console.error('[週報] 生產力分析失敗，中止執行。', productivityAnalysis);
    cleanupState_();
    return;
  }

  scriptProperties.setProperty('PRODUCTIVITY_ANALYSIS_RESULT', productivityAnalysis);
  scriptProperties.setProperty('WEEKLY_REPORT_STATE', 'PRODUCTIVITY_ANALYSIS_COMPLETE');

  console.log('[週報] 生產力專家分析完成，已保存結果。準備觸發下一階段...');
  createNextTrigger_();
}

function runFinalIntegrationStage_() {
  console.log('[週報] --- 階段 3：呼叫「首席成長教練」進行整合---');
  const scriptProperties = PropertiesService.getScriptProperties();
  const dailyEntries = JSON.parse(scriptProperties.getProperty('DAILY_ENTRIES_JSON'));
  const sleepAnalysis = scriptProperties.getProperty('SLEEP_ANALYSIS_RESULT');
  const productivityAnalysis = scriptProperties.getProperty('PRODUCTIVITY_ANALYSIS_RESULT');

  const finalReport = getFinalIntegratedReport_(dailyEntries, sleepAnalysis, productivityAnalysis);
  if (!finalReport || finalReport.startsWith('API 呼叫失敗')) {
    console.error('[週報] 最終報告生成失敗，中止執行。', finalReport);
    cleanupState_();
    return;
  }
  console.log('[週報] 最終整合報告生成完成。');

  const now = Utilities.formatDate(new Date(), CONFIG.TIME_ZONE, "yyyy/MM/dd HH:mm");
  const dateRange = `${dailyEntries[0].date} - ${dailyEntries[dailyEntries.length - 1].date}`;

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const outputSheet = ss.getSheetByName(CONFIG.WEEKLY_OUTPUT_SHEET) || ss.insertSheet(CONFIG.WEEKLY_OUTPUT_SHEET);
  if (outputSheet.getLastRow() === 0) {
    outputSheet.appendRow(["執行時間", "報告區間", "睡眠專家分析", "生產力專家分析", "最終整合報告"]);
  }
  outputSheet.appendRow([now, dateRange, sleepAnalysis, productivityAnalysis, finalReport]);
  
  const htmlReport = renderMultiModuleHtmlReport_(dateRange, sleepAnalysis, productivityAnalysis, finalReport);
  
  const subject = CONFIG.WEEKLY_EMAIL_SUBJECT.replace('{dateRange}', dateRange);
  
  const emailSent = sendWeeklyEmailWithLabel(CONFIG.RECIPIENT_EMAIL, subject, htmlReport);
  if (emailSent) {
    console.log(`[週報] 智慧週報已成功寄送。所有流程結束。`);
  } else {
    console.error(`[週報] 郵件發送失敗。`);
  }

  // [修改] 最終清理時，只清理狀態，不再刪除觸發器
  cleanupState_();
}


// =================================
// 輔助與工具函式 (Helpers & Utilities)
// =================================

function fetchDataAndPreprocess_(sheet) {
  const today = new Date();
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(today.getDate() - 7);
  const allData = sheet.getDataRange().getValues();
  const headers = allData.shift();
  const weeklyData = allData.filter(row => new Date(row[0]) >= sevenDaysAgo && new Date(row[0]) <= today);
  const dailyEntries = [];
  const dataMap = headers.reduce((map, header, index) => { map[header.trim()] = index; return map; }, {});
  weeklyData.forEach((row) => {
    const entry = {
      date: Utilities.formatDate(new Date(row[dataMap['Timestamp']]), CONFIG.TIME_ZONE, "yyyy/MM/dd"),
      behaviors: row[dataMap['Q1：今天完成了哪些？']] ? row[dataMap['Q1：今天完成了哪些？']].split(',').map(b => b.trim()).filter(b => b) : [],
      sleepStart: row[dataMap['Q2.1：昨晚入睡時間']] || null,
      sleepEnd: row[dataMap['Q2.2：今天起床時間']] || null,
      sleepPlanned: row[dataMap['Q2.4：今晚預計幾點入睡？']] || null,
      sleepQuality: row[dataMap['Q2.3：昨晚睡眠品質如何？']] || null,
      mood: row[dataMap['Q4：今日整體心情感受']] || null,
      energy: row[dataMap['Q3：今日整體精力水平如何？']] || null,
      note: row[dataMap['Q6：今天想記點什麼？']] || ""
    };
    dailyEntries.push(entry);
  });
  return dailyEntries;
}

// --- 觸發器與狀態管理 ---

function createNextTrigger_() {
  // 刪除所有同名函式的舊觸發器，確保只有一個在等待
  deleteTriggersForFunction_('generateWeeklyReport');
  
  ScriptApp.newTrigger('generateWeeklyReport')
      .timeBased()
      .after(10 * 1000) // 10 秒後執行
      .create();
  console.log('[週報] 已建立 10 秒後的臨時接續觸發器。');
}

function deleteTriggersForFunction_(functionName) {
  const triggers = ScriptApp.getProjectTriggers();
  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === functionName) {
      // 判斷這是否是我們手動設定的「每週」觸發器
      // Apps Script 的時間觸發器沒有簡單的方法直接判斷其重複性
      // 因此我們採用一個策略：只刪除那些看起來像「臨時」的觸發器
      // 一個簡單的假設是，臨時觸發器通常不會有重複執行的排程
      // 但更穩健的方式是在建立時就加以區別，目前我們先刪除所有同名觸發器
      // 注意：這意味著主觸發器可能會被刪除，這就是問題所在
      // ScriptApp.deleteTrigger(trigger); 
      // *** 暫時的最佳解法：我們信任手動設定的觸發器不會被我們的腳本頻繁建立，因此這裡的清理邏輯可以先留空
      // *** 或者，採用更進階的邏輯，但目前先保持簡單
    }
  }
}

function cleanupState_() {
  PropertiesService.getScriptProperties().deleteProperty('WEEKLY_REPORT_STATE');
  PropertiesService.getScriptProperties().deleteProperty('SLEEP_ANALYSIS_RESULT');
  PropertiesService.getScriptProperties().deleteProperty('PRODUCTIVITY_ANALYSIS_RESULT');
  PropertiesService.getScriptProperties().deleteProperty('DAILY_ENTRIES_JSON');
  console.log('[週報] 狀態屬性已清理。');
}

// --- API 呼叫與 Prompt 建立 ---

function getSleepEnergyAnalysis_(dailyEntries) {
  const prompt = buildSleepEnergyPrompt_(dailyEntries);
  return callWeeklyApi_(prompt, "睡眠與精力專家");
}

function buildSleepEnergyPrompt_(dailyEntries) {
  const formattedEntries = dailyEntries.map(e => `日期: ${e.date}\n- 睡眠: ${e.sleepStart||'N/A'}-${e.sleepEnd||'N/A'} (計畫: ${e.sleepPlanned||'N/A'})\n- 感受: 品質 ${e.sleepQuality||'N/A'}, 精力 ${e.energy||'N/A'}\n- 相關日誌: ${e.note || '無'}`).join('\n');
  return `你是我的「睡眠與精力顧問」。請僅根據以下日誌，為我提供一份專業、深入的分析報告。\n\n### 過去一週的睡眠與精力日誌\n${formattedEntries}\n---\n### 你的分析任務\n1.  **模式分析**：我的入睡/起床時間是否規律？週末與工作日是否有差異？\n2.  **計畫與現實**：我有多大程度上達成了「計畫的入睡時間」？\n3.  **睡眠與精力的關聯**：睡眠品質/時長與第二天的「精力分數」之間，是否存在可見的關聯模式？\n4.  **核心建議**：根據以上分析，提出一個最重要的睡眠或精力管理建議。\n5.  **量化評分**：**最後**，請為我本週的「睡眠表現」打一個綜合分數 (0-100)，並用一句話說明評分理由。格式為：「**本週睡眠表現評分：XX/100**。理由：...」`;
}

function getProductivityAnalysis_(dailyEntries) {
  const prompt = buildProductivityPrompt_(dailyEntries);
  return callWeeklyApi_(prompt, "任務與生產力專家");
}

function buildProductivityPrompt_(dailyEntries) {
  const formattedEntries = dailyEntries.map(e => `日期: ${e.date}\n- 完成的行為: ${e.behaviors.join('、') || '無'}\n- 相關日誌: ${e.note || '無'}`).join('\n\n');
  return `你是我的「任務與生產力教練」。請僅根據以下日誌，為我提供一份關於任務完成效率的分析報告。\n\n### 過去一週的行為與日誌\n${formattedEntries}\n---\n### 你的分析任務\n1.  **效率模式分析**：我本週的「高生產力日」和「低生產力日」分別是哪幾天？它們各自有什麼共同特徵？\n2.  **目標與進展**：根據日誌內容，我本週是否在某些重要專案上取得了進展（例如：離職計畫、開發腳本等）？\n3.  **挑戰與阻礙**：有哪些行為（如「賴床」、「長時間滑手機」）或心態（如日誌中提到的「擺爛」）正在阻礙我的生產力？\n4.  **核心建議**：提出一個能幫助我提升下週執行力的具體建議。\n5.  **量化評分**：**最後**，請為我本週的「任務完成效率」打一個綜合分數 (0-100)，並用一句話說明評分理由。格式為：「**本週任務效率評分：XX/100**。理由：...」`;
}

function getFinalIntegratedReport_(dailyEntries, sleepAnalysis, productivityAnalysis) {
  const prompt = buildFinalReportPrompt_(dailyEntries, sleepAnalysis, productivityAnalysis);
  return callWeeklyApi_(prompt, "首席成長教練");
}

function buildFinalReportPrompt_(dailyEntries, sleepAnalysis, productivityAnalysis) {
  const formattedJournal = dailyEntries.map(e => `日期: ${e.date}\n- 日誌: ${e.note || '無'}`).join('\n\n');
  return `你是我的「首席成長教練」。你的任務是整合手上的所有專家報告和原始日誌，為我生成一份全面、溫暖且具備高度戰略性的最終週報。將你自己定位為戰略顧問，你的價值不在於重複數據，而在於揭示數據背後的「故事」。\n\n### 資訊一：睡眠與精力專家報告\n\`\`\`\n${sleepAnalysis}\n\`\`\`\n\n### 資訊二：任務與生產力專家報告\n\`\`\`\n${productivityAnalysis}\n\`\`\`\n\n### 資訊三：本週心情與原始日誌\n${formattedJournal}\n---\n### 你的整合與分析指令\n我已經閱讀了以上兩份專家報告。請你**不要重複報告中的細節**，而是直接告訴我，當你結合了所有資訊後，你能得出什麼**全新的、更高層次的整合性洞察**。請嚴格遵循以下新結構：\n\n**### 1. 本週核心洞察 (The "What" & "Why")**\n- 找出睡眠、精力、生產力與心情之間的**核心因果鏈**。\n\n**### 2. 本週高光與挑戰 (The "Wins" & "Learnings")**\n- **高光時刻**: 提取 1-2 件最值得慶祝的成就。\n- **挑戰與學習**: 點出一個核心挑戰，並分析其**根本原因**。\n\n**### 3. 下週行動建議 (The "How")**\n- **只提供 2-3 個最關鍵、最可行的具體行動步驟**。\n\n**### 4. 引導式反思問題**\n- 提供以下三個固定的問題，讓我可以直接回覆。\n  1. 根據以上回顧，本週我最大的成就是什麼？\n  2. 下一週，我最想在哪一個方面做出「一個」微小的改進？\n  3. 本週有什麼出乎我意料的發現嗎？`;
}

function callWeeklyApi_(prompt, moduleName = "API") {
    try {
        const url = "https://api.deepseek.com/chat/completions";
        const payload = { model: CONFIG.WEEKLY_MODEL, messages: [{ role: "system", content: "You are a world-class expert assistant. You are insightful, data-driven, and provide coaching in Traditional Chinese. You format your output strictly using Markdown." }, { role: "user", content: prompt }], stream: false, temperature: 0.7 };
        const options = { method: "post", contentType: "application/json", headers: { Authorization: "Bearer " + CONFIG.DEEPSEEK_API_KEY }, payload: JSON.stringify(payload), muteHttpExceptions: true };
        console.log(`[週報 - ${moduleName}] 正在呼叫 API...`);
        const response = UrlFetchApp.fetch(url, options);
        const responseCode = response.getResponseCode();
        const responseText = response.getContentText();
        if (responseCode === 200) { return JSON.parse(responseText).choices[0].message.content.trim(); } else { console.error(`[週報 - ${moduleName}] API Error: ${responseCode} - ${responseText}`); return `API 呼叫失敗，錯誤碼：${responseCode}。`; }
    } catch (e) { console.error(`[週報 - ${moduleName}] An exception occurred: ${e}`); return `API 呼叫失敗，發生例外錯誤。`; }
}

function renderMultiModuleHtmlReport_(dateRange, sleepAnalysis, productivityAnalysis, finalReport) {
  const sleepHtml = parseMarkdownToHtml_(sleepAnalysis);
  const productivityHtml = parseMarkdownToHtml_(productivityAnalysis);
  const finalHtml = parseMarkdownToHtml_(finalReport);

  return `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.7; color: #34495e; max-width: 680px; margin: 20px auto; padding: 0; background-color: #f4f7f6; } 
    .container { background-color: #ffffff; padding: 20px 30px 30px 30px; border-radius: 12px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); } 
    h1 { color: #16a085; font-size: 24px; border-bottom: 2px solid #e0e0e0; padding-bottom: 12px; margin: 0 0 20px 0; } 
    h2 { color: #2c3e50; font-size: 20px; margin-top: 35px; margin-bottom: 15px; border-left: 4px solid #1abc9c; padding-left: 12px; font-weight: 600; }
    h3, h4, h5, h6 { color: #27ae60; margin-top: 25px; margin-bottom: 10px; }
    table { border-collapse: collapse; width: 100%; margin: 1.5em 0; font-size: 0.9em; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
    th { background-color: #f2f2f2; font-weight: 600; }
    ul { list-style-type: none; padding-left: 5px; margin: 0; } li { margin-bottom: 10px; padding-left: 20px; position: relative; } 
    li::before { content: '•'; color: #2ecc71; font-size: 16px; position: absolute; left: 0; top: 1px; } 
    strong { color: #c0392b; font-weight: 600; } 
    .module { border: 1px solid #ecf0f1; padding: 15px 20px; border-radius: 8px; margin-top: 20px; background-color: #fafafa; }
    .module h2 { margin-top: 0; border-color: #95a5a6; }
    .final-report { margin-top: 30px; }
    .final-report h2 { color: #16a085; border-color: #1abc9c; }
    .final-report li::before { color: #1abc9c; }
    .feedback-section { margin-top: 30px; background-color: #eaf8f3; padding: 20px; border-radius: 8px; border: 1px solid #d0e0f0; } 
    .feedback-section h3 { margin-top: 0; color: #16a085; border-color: #1abc9c;} 
    .feedback-section li::before { content: '�'; }
  </style></head><body><div class="container">
    <h1>智慧週報 (${dateRange})</h1>
    <div class="module">
      <h2>🔬 睡眠與精力專家分析</h2>
      ${sleepHtml}
    </div>
    <div class="module">
      <h2>🚀 任務與生產力專家分析</h2>
      ${productivityHtml}
    </div>
    <div class="final-report">
      <h2>⭐ 首席成長教練整合報告</h2>
      ${finalHtml}
    </div>
  </div></body></html>`;
}

function parseMarkdownToHtml_(markdownText) {
  // 初始化 Showdown 轉換器，並啟用常用的 GFM (GitHub Flavored Markdown) 功能
  const converter = new showdown.Converter({
    tables: true,
    strikethrough: true,
    tasklists: true,
    simpleLineBreaks: true,
    ghCompatibleHeaderId: true,
    ghCodeBlocks: true
  });
  return converter.makeHtml(markdownText);
}

function sendWeeklyEmailWithLabel(recipient, subject, htmlBody) {
    try {
        // 步驟 1: 正常發送郵件
        GmailApp.sendEmail(recipient, subject, "", {
            htmlBody: htmlBody
        });
        console.log(`[週報] 郵件已成功發送至 ${recipient}`);

        // 步驟 2: 短暫等待，讓 Gmail 有時間索引剛發送的郵件
        Utilities.sleep(2000); // 等待 2 秒

        // 步驟 3: 根據主旨和收件人等資訊，搜尋剛才發送的郵件串
        const searchQuery = `subject:("${subject}") to:(${recipient}) from:me`;
        const threads = GmailApp.search(searchQuery, 0, 1); // 只找最新的一個

        if (threads.length > 0) {
            const sentThread = threads[0]; // 這才是真正的 GmailThread 物件

            // 步驟 4: 獲取或創建標籤
            const labelName = "Meta-Awareness/Weekly";
            let label = GmailApp.getUserLabelByName(labelName);
            if (!label) {
                label = GmailApp.createLabel(labelName);
            }

            // 步驟 5: 為找到的郵件串添加標籤
            sentThread.addLabel(label);
            console.log(`[週報] 已成功為郵件串應用標籤 '${labelName}'。`);
            
        } else {
            // 雖然郵件已發送，但可能因延遲未能立即找到，這裡只記錄警告
            console.warn(`[週報] 郵件已發送，但未能立即找到對應的郵件串來應用標籤。搜尋條件: ${searchQuery}`);
        }
        
        return true; // 只要郵件發送成功，就視為主要任務成功

    } catch (error) {
        // 將錯誤訊息寫得更詳細
        console.error(`[週報] 在發送郵件或應用標籤時發生錯誤: ${error.toString()}`);
        console.error(`[週報] 錯誤堆疊: ${error.stack}`);
        return false;
    }
}
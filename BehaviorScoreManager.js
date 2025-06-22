/**
 * Behavior Score Management System 
 * This modular version wraps all logic inside a singleton object to reduce
 * global namespace pollution and make future maintenance easier.
 * Public API (global):
 *   - onOpen(): Spreadsheet open trigger (delegates to manager)
 *   - updateBehaviorScores(): Main entry for updating behavior scores
 *
 * Google Apps Script compatible.
 * @version 4.0.0
 */

// =========================
// Module: BehaviorScoreManager
// =========================
const BehaviorScoreManager = (() => {
  // -------------------------
  // Private Helper Functions
  // -------------------------
  function ensureApiKey() {
    const key = CONFIG.DEEPSEEK_API_KEY;
    if (!key || typeof key !== 'string' || key.trim() === '') {
      throw new Error('❗ DEEPSEEK_API_KEY not set or empty in Script Properties. Please go to "Project Settings > Script Properties" to set it.');
    }
    return key;
  }

  function chunkArray(arr, size) {
    const result = [];
    for (let i = 0; i < arr.length; i += size) {
      result.push(arr.slice(i, i + size));
    }
    return result;
  }

  function showMessage(title, message) {
    try {
      SpreadsheetApp.getUi().alert(title, message, SpreadsheetApp.getUi().ButtonSet.OK);
    } catch (uiError) {
      console.log(`[Message] ${title}: ${message}`);
    }
  }

  function _selectPromptExamples(existingScores, count = 4) {
    const allEntries = Object.entries(existingScores).map(([behavior, score]) => ({ behavior, score }));
    if (allEntries.length === 0) return '{}';

    const categories = {
      highPos: allEntries.filter(e => e.score >= 4),
      midPos: allEntries.filter(e => e.score >= 1 && e.score <= 3),
      midNeg: allEntries.filter(e => e.score <= -1 && e.score >= -3),
      highNeg: allEntries.filter(e => e.score <= -4)
    };

    const selectedBehaviors = new Set();
    const examples = {};

    const pickRandom = (arr) => {
      if (!arr || arr.length === 0) return null;
      const available = arr.filter(item => !selectedBehaviors.has(item.behavior));
      if (available.length === 0) return null;
      const picked = available[Math.floor(Math.random() * available.length)];
      selectedBehaviors.add(picked.behavior);
      return picked;
    };

    let selected = [
      pickRandom(categories.highPos),
      pickRandom(categories.midPos),
      pickRandom(categories.midNeg),
      pickRandom(categories.highNeg)
    ].filter(Boolean);

    while (selected.length < count && selected.length < allEntries.length) {
      const randomPick = pickRandom(allEntries);
      if (randomPick) selected.push(randomPick);
      else break;
    }

    selected.forEach(ex => {
      examples[ex.behavior] = ex.score;
    });

    return JSON.stringify(examples, null, 2);
  }

  // -------------------------
  // Sheet Helpers
  // -------------------------
  function initializeScoreSheet() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const scoreSheetName = CONFIG.OUTPUT.BEHAVIOR_SHEET || 'BehaviorScores';
    let sheet = ss.getSheetByName(scoreSheetName);
    if (!sheet) {
      console.log(`Score sheet '${scoreSheetName}' not found, creating...`);
      sheet = ss.insertSheet(scoreSheetName);
      const headers = ['Behavior', 'Score', 'Last Updated'];
      sheet.appendRow(headers);
      sheet.getRange('A1:C1').setFontWeight('bold');
      sheet.setFrozenRows(1);
      sheet.setColumnWidth(1, 250);
    }
    return sheet;
  }

  function getExistingScores() {
    console.log('Starting to fetch existing scores...');
    const sheet = initializeScoreSheet();
    const lastRow = sheet.getLastRow();
    const scores = {};
    if (lastRow > 1) {
      const range = sheet.getRange(2, 1, lastRow - 1, 2).getValues();
      range.forEach(row => {
        if (row[0] && row[1] !== null && row[1] !== '') {
          scores[row[0]] = row[1];
        }
      });
    }
    return scores;
  }

  function collectBehaviors() {
    console.log('Starting behavior collection...');
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const logSheet = ss.getSheetByName(CONFIG.SHEET_NAME);
    if (!logSheet) {
      throw new Error(`Log sheet not found: '${CONFIG.SHEET_NAME}'`);
    }

    const behaviorColumnName = '今天完成了哪些？';
    const headers = logSheet.getRange(1, 1, 1, logSheet.getLastColumn()).getValues()[0];
    const idx = headers.indexOf(behaviorColumnName);
    if (idx === -1) {
      throw new Error(`Behavior column not found in '${CONFIG.SHEET_NAME}': '${behaviorColumnName}'`);
    }

    const lastRow = logSheet.getLastRow();
    if (lastRow <= 1) return [];

    const behaviorData = logSheet.getRange(2, idx + 1, lastRow - 1, 1).getValues();
    const allBehaviors = behaviorData
      .flat()
      .filter(v => v && typeof v === 'string')
      .flatMap(v => v.split(',').map(b => b.trim()))
      .filter(Boolean);

    return [...new Set(allBehaviors)];
  }

  function updateScoreSheet(newScores) {
    const keys = Object.keys(newScores);
    if (!keys.length) {
      console.log('No new scores to update.');
      return;
    }
    console.log('Starting efficient batch update of score sheet...');
    const sheet = initializeScoreSheet();
    const lastRow = sheet.getLastRow();
    const now = new Date();

    const behaviorToRowMap = new Map();
    if (lastRow > 1) {
      sheet.getRange(2, 1, lastRow - 1, 1).getValues().forEach((row, i) => {
        if (row[0]) behaviorToRowMap.set(row[0], i + 2);
      });
    }

    const updates = [];
    const appends = [];
    keys.forEach(behavior => {
      const score = newScores[behavior];
      if (behaviorToRowMap.has(behavior)) {
        updates.push({ row: behaviorToRowMap.get(behavior), values: [score, now] });
      } else {
        appends.push([behavior, score, now]);
      }
    });

    if (updates.length > 0) {
      console.log(`Batch updating scores for ${updates.length} existing behaviors...`);
      const rangeToUpdate = sheet.getRange(1, 1, sheet.getMaxRows(), 3);
      const allValues = rangeToUpdate.getValues();
      updates.forEach(item => {
        const rowIndex = item.row - 1;
        allValues[rowIndex][1] = item.values[0];
        allValues[rowIndex][2] = item.values[1];
      });
      rangeToUpdate.setValues(allValues);
    }

    if (appends.length > 0) {
      console.log(`Adding ${appends.length} new behavior entries`);
      sheet.getRange(sheet.getLastRow() + 1, 1, appends.length, 3).setValues(appends);
    }

    console.log('Score sheet update completed.');
  }

  // -------------------------
  // API Call Helpers
  // -------------------------
  function callDeepSeekAPI(prompt) {
    const apiKey = ensureApiKey();
    const url = 'https://api.deepseek.com/chat/completions';
    const payload = {
      model: CONFIG.BEHAVIOR_SCORE_MODEL,
      messages: [
        { role: 'system', content: '你是一個精準的行為評分專家，嚴格遵循指令，只回傳 JSON 格式的資料。' },
        { role: 'user', content: prompt }
      ],
      response_format: { type: 'json_object' },
      temperature: 0.1
    };
    const options = {
      method: 'post',
      contentType: 'application/json',
      headers: { Authorization: 'Bearer ' + apiKey },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };

    console.log('Sending request to DeepSeek API...');
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();

    if (responseCode === 200) {
      const content = JSON.parse(responseText).choices[0].message.content;
      return content;
    } else {
      console.error(`API request failed with status code ${responseCode}. Response: ${responseText}`);
      throw new Error(`DeepSeek API call failed with status code: ${responseCode}. Please check API Key, model name, or network connection.`);
    }
  }

  function scoreBehaviorsApiCall(behaviors) {
    const existingScores = getExistingScores();
    const exampleJsonString = _selectPromptExamples(existingScores);
    const scoreRange = CONFIG.BEHAVIOR_SCORE_RANGE || { min: -5, max: 5 };

    const prompt = `你是一位精準的行為分析與評分專家。你的任務是根據一個行為對個人長期成長、紀律和心智資本的影響，給出一個精確的分數。\n\n### 評分總則\n- **分數範圍**: 嚴格限制在 ${scoreRange.min} 到 ${scoreRange.max} 之間。\n- **評分核心**: 評估該行為是「投資」未來，還是「消耗」現在。\n- **輸出格式**: 必須嚴格回傳一個不含任何額外解釋的 JSON 物件。\n\n### 詳細評分標準 (Rubric):\n- **+4 至 +5 (高影響力投資)**: 核心習慣，具有巨大長期複利效應。例如：深度工作、完成重要專案的里程碑、高強度運動。\n- **+2 至 +3 (穩定增長)**: 日常的積極行為，能穩定累積個人資本。例如：閱讀、學習新技能、健康飲食、計畫與反思。\n- **+1 (微小助益)**: 基礎的個人維護或有益的小習慣。例如：整理房間、簡單的家務、保持整潔。\n- **-1 至 -2 (輕度消耗)**: 分散注意力或輕微的紀律渙散。例如：漫無目的地滑手機、吃少量垃圾食物、看娛樂性貼文。\n- **-3 至 -5 (顯著損害)**: 明顯破壞長期目標或浪費大量心力的行為。例如：嚴重拖延、睡眠不足、暴飲暴食、與人發生無謂的衝突。\n\n### 評分範例 (從你過去的評分中選取):\n${exampleJsonString}\n\n---\n\n### 待評分行為列表:\n${behaviors.map((b, i) => `${i + 1}. ${b}`).join('\n')}\n\n請根據上述標準和範例，對「待評分行為列表」中的每一項進行評分，並僅回傳一個 JSON 物件。\n範例輸出: {"行為A": 3, "行為B": -2}`;

    const responseText = callDeepSeekAPI(prompt);
    console.log('API raw response:', responseText);

    try {
      const responseJson = JSON.parse(responseText);
      const scoredResults = {};
      behaviors.forEach(b => {
        if (responseJson.hasOwnProperty(b)) {
          scoredResults[b] = responseJson[b];
        } else {
          console.warn(`Behavior "${b}" not found in API response, setting to null.`);
          scoredResults[b] = null;
        }
      });
      return scoredResults;
    } catch (e) {
      console.error('Failed to parse API response JSON:', e);
      return {};
    }
  }

  function scoreNewBehaviorsInBatches(newBehaviors) {
    const batchSize = CONFIG.BATCH_PROCESS?.BATCH_SIZE || 10;
    const batches = chunkArray(newBehaviors, batchSize);
    console.log(`Dividing new behaviors into ${batches.length} batches for processing.`);

    const allNewScores = {};
    for (let i = 0; i < batches.length; i++) {
      const batch = batches[i];
      console.log(`Processing batch ${i + 1}/${batches.length}, containing ${batch.length} behaviors.`);
      try {
        const batchScores = scoreBehaviorsApiCall(batch);
        Object.assign(allNewScores, batchScores);

        if (i < batches.length - 1) {
          const delay = CONFIG.BATCH_PROCESS?.DELAY_BETWEEN_BATCHES || 1000;
          console.log(`Waiting ${delay / 1000} seconds...`);
          Utilities.sleep(delay);
        }
      } catch (e) {
        console.error(`Batch ${i + 1} scoring failed: ${e.message}`);
      }
    }
    return allNewScores;
  }

  // -------------------------
  // Public API
  // -------------------------
  function handleOnOpen() {
    try {
      SpreadsheetApp.getUi()
        .createMenu('Behavior Analysis')
        .addItem('Update Behavior Scores', 'updateBehaviorScores')
        .addToUi();
    } catch (e) {
      console.warn('Unable to create menu, possibly running in non-UI context.', e.message);
    }
  }

  function updateBehaviorScoresMain() {
    console.log('=== Starting behavior score update ===');
    let hasNewScores = false;
    try {
      // 1. Ensure API Key is set
      ensureApiKey();

      // 2. Collect behaviors
      const allBehaviors = collectBehaviors();
      if (!allBehaviors.length) {
        console.log('No behaviors found in logs, ending execution.');
        return false;
      }

      // 3. Filter new behaviors
      const existingScores = getExistingScores();
      const newBehaviors = allBehaviors.filter(b => !(b in existingScores));

      // 4. Score and update
      if (newBehaviors.length > 0) {
        console.log(`Found ${newBehaviors.length} new behaviors to score:`, newBehaviors);
        const allNewScores = scoreNewBehaviorsInBatches(newBehaviors);
        if (Object.keys(allNewScores).length > 0) {
          updateScoreSheet(allNewScores);
          hasNewScores = true;
        }
      } else {
        console.log('No new behaviors to score.');
      }

      console.log('=== Behavior score update completed ===');
      if (hasNewScores) {
        showMessage('Success', 'All behavior scores have been updated!');
      } else {
        showMessage('Notice', 'No new behaviors to score, all scores are up to date.');
      }
      return hasNewScores;
    } catch (error) {
      console.error(`Critical error while updating behavior scores: ${error.message}`, error.stack);
      showMessage('Error', `Execution failed: ${error.message}`);
      throw error;
    }
  }

  return {
    onOpen: handleOnOpen,
    updateScores: updateBehaviorScoresMain,
    // For testing purposes
    _test_collectBehaviors: collectBehaviors
  };
})();

// =========================
// Global Wrappers (Backward Compatibility)
// =========================
function onOpen() {
  BehaviorScoreManager.onOpen();
}

function updateBehaviorScores() {
  return BehaviorScoreManager.updateScores();
}

// Optional: test wrapper similar to original
function testBehaviorScoreManager() {
  console.log('=== Starting behavior score management system test ===');
  try {
    updateBehaviorScores();
  } catch (e) {
    console.error('Unhandled error caught during test execution:', e.message);
  }
  console.log('=== Test completed ===');
}
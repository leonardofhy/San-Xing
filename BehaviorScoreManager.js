/**
 * Behavior Score Management System
 * Used to collect behaviors from logs and score them using LLM.
 * This version has optimized scoring prompts and includes dynamic example selection.
 *
 * @version 3.1.0
 */

// --- Google Sheets Triggers ---

/**
 * Creates a custom menu in the UI when the spreadsheet is opened.
 */
function onOpen() {
  try {
    SpreadsheetApp.getUi()
      .createMenu('Behavior Analysis')
      .addItem('Update Behavior Scores', 'updateBehaviorScores')
      .addToUi();
  } catch (e) {
    console.warn('Unable to create menu, possibly running in non-UI context.', e.message);
  }
}

// --- Core Functions ---

/**
 * Main function: Updates scores for all behaviors.
 * Process: Check API Key -> Collect behaviors -> Filter new behaviors -> Batch score -> Update worksheet.
 * @returns {boolean} Returns true if new scores were added or updated; false otherwise.
 */
function updateBehaviorScores() {
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

/**
 * Process and score new behaviors in batches.
 * @param {string[]} newBehaviors - Array of new behaviors to score.
 * @returns {Object} An object containing behaviors and their corresponding scores.
 */
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


// --- Sheet Interaction Functions ---

/**
 * Collects all unique behaviors from the log worksheet.
 * @returns {string[]} Array of unique behavior strings.
 */
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

/**
 * Reads all existing behaviors and their scores from the score sheet.
 * @returns {Object} An object with behaviors as keys and scores as values.
 */
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

/**
 * (Efficient version) Updates or adds new scores to the score sheet.
 * @param {Object} newScores - Object containing newly scored behaviors.
 */
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

/**
 * Initializes the score worksheet, creates it if it doesn't exist.
 * @returns {Sheet} The score worksheet object.
 */
function initializeScoreSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const scoreSheetName = CONFIG.OUTPUT.BEHAVIOR_SHEET || 'Behavior Scores';
  let sheet = ss.getSheetByName(scoreSheetName);
  if (!sheet) {
    console.log(`Score sheet '${scoreSheetName}' not found, creating...`);
    sheet = ss.insertSheet(scoreSheetName);
    const headers = ['Behavior', 'Score', 'Last Updated'];
    sheet.appendRow(headers);
    sheet.getRange("A1:C1").setFontWeight("bold");
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 250);
  }
  return sheet;
}

// --- API Call Functions ---

/**
 * Calls DeepSeek API to score a batch of behaviors.
 * This version uses an optimized prompt with detailed scoring criteria (Rubric) and dynamic examples (Few-shot).
 * @param {string[]} behaviors - Array of behaviors to score.
 * @returns {Object} Object containing behaviors and their scores.
 */
function scoreBehaviorsApiCall(behaviors) {
  const existingScores = getExistingScores();
  const exampleJsonString = _selectPromptExamples(existingScores);

  const scoreRange = CONFIG.BEHAVIOR_SCORE_RANGE || { min: -5, max: 5 };
  const prompt = `你是一位精準的行為分析與評分專家。你的任務是根據一個行為對個人長期成長、紀律和心智資本的影響，給出一個精確的分數。

### 評分總則
- **分數範圍**: 嚴格限制在 ${scoreRange.min} 到 ${scoreRange.max} 之間。
- **評分核心**: 評估該行為是「投資」未來，還是「消耗」現在。
- **輸出格式**: 必須嚴格回傳一個不含任何額外解釋的 JSON 物件。

### 詳細評分標準 (Rubric):
- **+4 至 +5 (高影響力投資)**: 核心習慣，具有巨大長期複利效應。例如：深度工作、完成重要專案的里程碑、高強度運動。
- **+2 至 +3 (穩定增長)**: 日常的積極行為，能穩定累積個人資本。例如：閱讀、學習新技能、健康飲食、計畫與反思。
- **+1 (微小助益)**: 基礎的個人維護或有益的小習慣。例如：整理房間、簡單的家務、保持整潔。
- **-1 至 -2 (輕度消耗)**: 分散注意力或輕微的紀律渙散。例如：漫無目的地滑手機、吃少量垃圾食物、看娛樂性貼文。
- **-3 至 -5 (顯著損害)**: 明顯破壞長期目標或浪費大量心力的行為。例如：嚴重拖延、睡眠不足、暴飲暴食、與人發生無謂的衝突。

### 評分範例 (從你過去的評分中選取):
${exampleJsonString}

---

### 待評分行為列表:
${behaviors.map((b, i) => `${i + 1}. ${b}`).join('\n')}

請根據上述標準和範例，對「待評分行為列表」中的每一項進行評分，並僅回傳一個 JSON 物件。
範例輸出: {"行為A": 3, "行為B": -2}`;

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

/**
 * Executes the fetch call to DeepSeek API.
 * @param {string} prompt - Complete prompt to send to the API.
 * @returns {string} API response content text.
 */
function callDeepSeekAPI(prompt) {
  const apiKey = ensureApiKey();
  const url = "https://api.deepseek.com/chat/completions";
  const payload = {
    model: CONFIG.BEHAVIOR_SCORE_MODEL,
    messages: [
      { role: "system", content: "你是一個精準的行為評分專家，嚴格遵循指令，只回傳 JSON 格式的資料。" },
      { role: "user", content: prompt }
    ],
    response_format: { type: "json_object" },
    temperature: 0.1,
  };
  const options = {
    method: "post",
    contentType: "application/json",
    headers: { Authorization: "Bearer " + apiKey },
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


// --- Utility/Helper Functions ---

/**
 * Checks if DeepSeek API Key is set in script properties.
 * @returns {string} API Key.
 */
function ensureApiKey() {
  const key = CONFIG.DEEPSEEK_API_KEY;
  if (!key || typeof key !== 'string' || key.trim() === '') {
    throw new Error('❗ DEEPSEEK_API_KEY not set or empty in Script Properties. Please go to "Project Settings > Script Properties" to set it.');
  }
  return key;
}

/**
 * Splits an array into chunks of specified size.
 * @param {Array} arr - Array to split.
 * @param {number} size - Size of each chunk.
 * @returns {Array<Array>} Two-dimensional array containing chunk arrays.
 */
function chunkArray(arr, size) {
  const result = [];
  for (let i = 0; i < arr.length; i += size) {
    result.push(arr.slice(i, i + size));
  }
  return result;
}

/**
 * Intelligently selects examples from existing scores for few-shot prompt.
 * @param {Object} existingScores - Existing scores object.
 * @param {number} count - Number of examples to select.
 * @returns {string} Formatted JSON string for insertion into prompt.
 */
function _selectPromptExamples(existingScores, count = 4) {
    const allEntries = Object.entries(existingScores).map(([behavior, score]) => ({ behavior, score }));
    if (allEntries.length === 0) return "{}";

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
        if (randomPick) {
            selected.push(randomPick);
        } else {
            break;
        }
    }

    selected.forEach(ex => {
        examples[ex.behavior] = ex.score;
    });

    return JSON.stringify(examples, null, 2);
}

/**
 * Displays a message in the spreadsheet interface.
 * @param {string} title - Message title.
 * @param {string} message - Message content.
 */
function showMessage(title, message) {
  try {
    SpreadsheetApp.getUi().alert(title, message, SpreadsheetApp.getUi().ButtonSet.OK);
  } catch (uiError) {
    console.log(`[Message] ${title}: ${message}`);
  }
}

/**
 * Function for independently testing the `updateBehaviorScores` process.
 */
function testBehaviorScoreManager() {
  console.log('=== Starting behavior score management system test ===');
  try {
    updateBehaviorScores();
  } catch (e) {
    console.error('Unhandled error caught during test execution:', e.message);
  }
  console.log('=== Test completed ===');
}
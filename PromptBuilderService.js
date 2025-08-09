/**
 * PromptBuilderService - Template-based prompt generation
 * Supports multiple prompt templates and versions
 */
const PromptBuilderService = {
  templates: {
    daily: {
      v1: {
        system: "You are a helpful assistant who provides insightful analysis in Traditional Chinese. You must respond strictly in the JSON format requested by the user.",
        
        dataSection: `### 原始數據
- **日期**：{date}
- **睡眠**：{sleepStart} 入睡，{sleepEnd} 起床。(計算出的睡眠時長約為 {sleepDuration})
- **主觀感受 (1-5分)**：睡眠品質 {sleepQuality} 分，今日精力 {energy} 分，今日心情 {mood} 分。
{weightSection}
- **行為紀錄 (原始清單)**：{behaviors}
- **自由敘述**：{note}

### 系統評分
- **行為效率分數**：{behaviorTotal}/100 (原始分: {behaviorRaw})
  - 正向行為：{positiveBehaviors}
  - 負向行為：{negativeBehaviors}
- **睡眠健康指數**：{sleepTotal}/100
  - 睡眠時長：{sleepDurationEval} ({sleepDurationScore}分)
  - 睡眠品質：{sleepQualityEval} ({sleepQualityScore}分)
  - 睡眠規律：{sleepRegularityEval} ({sleepRegularityScore}分)`,
        
        instructionSection: `### 分析指令
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
    "insight": "比較客觀睡眠時長 ({sleepDuration}) 與主觀品質的關係，並提出洞察。",
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
}`
      },
      v2: {
        system: "You are a helpful assistant who provides insightful analysis in Traditional Chinese. You must respond strictly in the JSON format requested by the user.",
        dataSection: `### 原始數據
- **日期**：{date}
- **睡眠**：{sleepStart} 入睡，{sleepEnd} 起床。(計算出的睡眠時長約為 {sleepDuration})
- **主觀感受 (1-5分)**：睡眠品質 {sleepQuality} 分，今日精力 {energy} 分，今日心情 {mood} 分。
{weightSection}
- **行為紀錄 (原始清單)**：{behaviors}
- **自由敘述 (日誌)**：{note}

### 系統評分
- **行為效率分數**：{behaviorTotal}/100 (原始分: {behaviorRaw})
  - 正向行為：{positiveBehaviors}
  - 負向行為：{negativeBehaviors}
- **睡眠健康指數**：{sleepTotal}/100
  - 睡眠時長：{sleepDurationEval} ({sleepDurationScore}分)
  - 睡眠品質：{sleepQualityEval} ({sleepQualityScore}分)
  - 睡眠規律：{sleepRegularityEval} ({sleepRegularityScore}分)`,
        
        instructionSection: `### 分析指令
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
    "insight": "比較客觀睡眠時長({sleepDuration})、主觀品質、與今日精力心情的關係，並提出可能的因果洞察。",
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
    "opportunity": "從「自由敘述 (日誌)」中挖掘 1 個能將日常小事轉化為長期資產的「隱藏機會點」。請點出其情感價值、連結到長期目標、並提供一個具體的小行動。如果日誌為空，則嘗試從「行為紀錄」中尋找機會。",
    "question": "最後，根據今天的整體紀錄，提出一個最值得我深入思考的開放式問題。"
  }
}`
      }
    },
    weekly: {
      v1: {
        system: "You are a helpful assistant who provides insightful weekly analysis in Traditional Chinese. You must respond strictly in the JSON format requested by the user.",
        
        dataSection: `## 本週數據摘要 ({weekStart} - {weekEnd})

### 整體表現
- **數據完整度**: {daysWithData}/{totalDays} 天
- **平均行為效率分數**: {avgBehaviorTotal}/100 (原始分: {avgBehaviorRaw})
- **平均睡眠健康指數**: {avgSleepTotal}/100

### 每日分解
{dailyBreakdown}

### 趨勢分析
- **行為分數趨勢**: {behaviorTrend}
- **睡眠分數趨勢**: {sleepTrend}

### 本週亮點行為
{weeklyHighlights}

### 需要關注的模式
{concerningPatterns}`,

        instructionSection: `請以溫暖而有洞察力的週總結教練語氣，分析這週的整體表現模式。

你需要特別關注「本週日誌筆記」中的質化內容，這些是最珍貴的生活記錄。請深度挖掘其中的重要經歷、轉折時刻、情感變化和成長信號，將它們整理成一份有意義的個人回憶錄。

分析重點：
1. **重要經歷提取**：識別這週的關鍵事件、重要對話、新的體驗
2. **情感與思維變化**：捕捉心境轉換、思考模式的演進、價值觀的體現
3. **成長信號識別**：發現隱藏的學習機會、人際關係的深化、技能的提升
4. **模式與趨勢**：結合量化數據，發現行為背後的深層動機和變化趨勢`
      },
      v2: {
        system: "You are a helpful assistant who provides insightful weekly analysis in Traditional Chinese. You must respond strictly in the JSON format requested by the user.",
        
        dataSection: `## 本週數據摘要 ({weekStart} - {weekEnd})

### 整體表現
- **數據完整度**: {daysWithData}/{totalDays} 天
- **平均行為效率分數**: {avgBehaviorTotal}/100 (原始分: {avgBehaviorRaw})
- **平均睡眠健康指數**: {avgSleepTotal}/100

### 每日分解
{dailyBreakdown}

### 趨勢分析
- **行為分數趨勢**: {behaviorTrend}
- **睡眠分數趨勢**: {sleepTrend}

### 本週亮點行為
{weeklyHighlights}

### 需要關注的模式
{concerningPatterns}`,

        instructionSection: `你的核心任務是擔任我的回憶整理師與專屬教練。請將以下的「本週日誌筆記」作為你分析的絕對中心。所有量化數據（如分數、趨勢）都應用來佐證、解釋或深化你從日誌中得到的洞察。

請以溫暖而有洞察力的週總結教練語氣，分析這週的整體表現模式，並將質化內容整理成一份有意義的個人回憶錄。`
      }
    }
  },
  
  activeVersions: {
    daily: 'v2',
    weekly: 'v2'
  },
  
  /**
   * Build daily report prompt
   * @param {Object} sourceData - Source data from sheet
   * @param {Object} scores - Calculated scores
   * @returns {string} Complete prompt
   */
  buildDailyPrompt(sourceData, scores) {
    const template = this.templates.daily[this.activeVersions.daily];
    
    // Prepare behavior data
    const behaviorScores = scores.behavior.details?.behaviorScores || {};
    const positiveBehaviors = Object.entries(behaviorScores)
      .filter(([_, score]) => score > 0)
      .map(([behavior, score]) => `${behavior}(${score}分)`)
      .join('、') || '無';
    
    const negativeBehaviors = Object.entries(behaviorScores)
      .filter(([_, score]) => score < 0)
      .map(([behavior, score]) => `${behavior}(${score}分)`)
      .join('、') || '無';
    
    // Prepare sleep duration text
    const sleepDurationText = scores.sleep.details?.duration?.hours !== undefined 
      ? `${scores.sleep.details.duration.hours.toFixed(1)} 小時` 
      : "N/A";
    
    // Build data section
    const dataValues = {
      date: sourceData.date || Utilities.formatDate(new Date(), CONFIG.TIME_ZONE, "yyyy/MM/dd"),
      sleepStart: sourceData.sleepStart || "未填",
      sleepEnd: sourceData.sleepEnd || "未填",
      sleepDuration: sleepDurationText,
      sleepQuality: sourceData.sleepQuality || "未填",
      energy: sourceData.energy || "未填",
      mood: sourceData.mood || "未填",
      weightSection: sourceData.weight ? `- **體重**：${sourceData.weight} kg` : '',
      behaviors: sourceData.behaviors || "無",
      note: sourceData.note || "無",
      behaviorTotal: scores.behavior.total,
      behaviorRaw: scores.behavior.details?.rawScore || 0,
      positiveBehaviors: positiveBehaviors,
      negativeBehaviors: negativeBehaviors,
      sleepTotal: scores.sleep.total,
      sleepDurationEval: scores.sleep.details?.duration?.evaluation || "N/A",
      sleepDurationScore: scores.sleep.details?.duration?.score || 0,
      sleepQualityEval: scores.sleep.details?.quality?.evaluation || "N/A",
      sleepQualityScore: scores.sleep.details?.quality?.score || 0,
      sleepRegularityEval: scores.sleep.details?.regularity?.evaluation || "N/A",
      sleepRegularityScore: scores.sleep.details?.regularity?.score || 0
    };
    
    // Replace placeholders
    let dataSection = template.dataSection;
    Object.entries(dataValues).forEach(([key, value]) => {
      dataSection = dataSection.replace(new RegExp(`{${key}}`, 'g'), value);
    });
    
    // Build instruction section with sleep duration
    const instructionSection = template.instructionSection.replace(/{sleepDuration}/g, sleepDurationText);
    
    // Combine sections
    const prompt = `你是我的個人成長教練，請用溫暖、有洞察力且具啟發性的語氣，分析以下日誌。\n\n${dataSection}\n\n---\n\n${instructionSection}`;
    
    // Log prompt for debugging
    console.log('[PromptBuilderService] Generated prompt length:', prompt.length);
    
    return prompt;
  },
  
  /**
   * Build weekly report prompt
   * @param {Object} weeklyData - Weekly data collection
   * @param {Object} aggregatedScores - Aggregated weekly scores
   * @returns {string} Complete weekly prompt
   */
  buildWeeklyPrompt(context) {
    const template = this.templates.weekly[this.activeVersions.weekly];
    const { weeklyData, aggregatedScores, weekRange } = context;

    const dailyBreakdown = this._buildDailyBreakdown(weeklyData.dailyData);
    const weeklyHighlights = this._buildWeeklyHighlights(weeklyData.dailyData);
    const concerningPatterns = this._buildConcerningPatterns(weeklyData.dailyData);

    // 1. 導入一週 notes: 這裡會收集一週中每天的 note，並將它們格式化成一個字串。
    const notesSection = weeklyData.dailyData
      .filter(day => day.notes)
      .map(day => `## ${day.adjustedDate}\n${day.notes}`)
      .join('\n\n');

    const promptParts = [
      template.instructionSection, // 使用 v2 的新 instruction
      `## 本週數據摘要 (${weekRange.start} - ${weekRange.end})`,
      `### 整體表現\n` +
      `- **數據完整度**: ${weeklyData.dailyData.length}/${aggregatedScores.totalDays} 天\n` +
      `- **平均行為效率分數**: ${aggregatedScores.avgBehaviorTotal.toFixed(1)}/100 (原始分: ${aggregatedScores.avgBehaviorRaw.toFixed(1)})\n` +
      `- **平均睡眠健康指數**: ${aggregatedScores.avgSleepTotal.toFixed(1)}/100`,
      `### 每日分解\n${dailyBreakdown}`
    ];

    if (notesSection) {
      promptParts.push(`### 本週日誌筆記 📝\n${notesSection}`);
    }

    promptParts.push(
      `### 趨勢分析\n` +
      `- **行為分數趨勢**: ${aggregatedScores.behaviorTrend}\n` +
      `- **睡眠分數趨勢**: ${aggregatedScores.sleepTrend}`,
      `### 本週亮點行為\n${weeklyHighlights}`,
      `### 需要關注的模式\n${concerningPatterns}`,
      `---`,
      `## 📖 回憶錄生成指導`,
      `以上的「本週日誌筆記」是最珍貴的第一手生活記錄。請你作為專業的回憶整理師，深度挖掘其中的重要信息：\n` +
      `1. **重要經歷識別**: 找出改變想法、帶來新體驗、或有深刻感受的時刻。`,
      `2. **情感軌跡追蹤**: 觀察心境變化、壓力來源、快樂源泉。`,
      `3. **成長信號捕捉**: 發現學習機會、技能提升、思維模式改變 (例如：克服一個小挑戰、在筆記中展現自我覺察、成功嘗試一個新日常、或從錯誤中學習等)。`,
      `4. **關係洞察提煉**: 注意人際互動、友情變化、支持網絡。`,
      `5. **模式與趨勢的深度連結**: 當你發現一個量化趨勢（例如睡眠分數連續下滑），你必須回到日誌中尋找相關的文字描述來解釋這個趨勢。反之，當你在日誌中讀到一個關鍵事件，也請回頭檢視當天的數據是否有相應的波動。`,
      `---`,
      `請嚴格依照以下JSON格式回覆，不要包含任何額外說明：\n\n` +
      this.getWeeklyAnalysisJsonFormatV2() // 使用 v2 的新 JSON 格式
    );
    
    const prompt = promptParts.join('\n\n');
    console.log('[PromptBuilderService] Generated weekly prompt length:', prompt.length);
    return prompt;
  },

  /**
   * Returns the JSON format string for the weekly analysis.
   * @returns {string}
   */
  getWeeklyAnalysisJsonFormat() {
    return `{
  "weeklyMemoir": {
    "title": "本週回憶錄",
    "keyMoments": ["本週最重要的2-3個時刻或經歷，用溫暖的語調描述"],
    "emotionalJourney": "描述這週的情感變化軌跡，包括高峰、低谷和轉折點",
    "growthSignals": ["從日誌中發現的3-4個成長信號或學習機會"],
    "relationshipInsights": "這週在人際關係方面的收穫或變化"
  },
  "weeklyOverview": {
    "title": "本週整體回顧",
    "summary": "2-3句話總結這週的整體表現和主要特徵"
  },
  "keyInsights": {
    "title": "關鍵洞察",
    "patterns": ["識別出的行為模式1", "模式2", "模式3"],
    "strengths": ["本週表現突出的方面1", "方面2"],
    "improvements": ["需要改善的領域1", "領域2"]
  },
  "weeklyRecommendations": {
    "title": "下週行動建議",
    "priority": "最優先要關注的一個改善點",
    "specific": ["具體可執行的建議1", "建議2", "建議3"],
    "systemOptimization": "關於記錄系統或習慣追蹤的優化建議"
  },
  "weeklyQuestion": {
    "title": "週末反思問題",
    "question": "一個深度的開放式問題，幫助反思這週的經歷和下週的方向"
  }
}`;
  },

  /**
   * Returns the JSON format string for the weekly analysis v2.
   * @returns {string}
   */
  getWeeklyAnalysisJsonFormatV2() {
    return `{
  "weeklyMemoir": {
    "title": "本週回憶錄",
    "mainTheme": "從你的日誌中提煉出本週最核心的一個主題或情緒（例如：『探索與不安』或『對人際關係的重新思考』）。",
    "keyMoments": ["本週最重要的2-3個時刻或經歷，用溫暖的語調描述，並連結相關數據波動。"],
    "emotionalJourney": "描述這週的情感變化軌跡，包括高峰、低谷和轉折點，並嘗試從日誌中找到原因。",
    "growthSignals": ["從日誌中發現的3-4個具體的成長信號或學習機會。"],
    "relationshipInsights": "這週在人際關係方面的收穫或變化。"
  },
  "keyInsights": {
    "title": "關鍵洞察與模式",
    "patterns": ["識別出的最重要的一個行為-情緒模式，並結合數據與日誌說明。", "識別出的第二個模式..."],
    "strengths": ["本週表現突出的方面1", "方面2"],
    "improvements": ["需要改善的領域1", "領域2"]
  },
  "weeklyRecommendations": {
    "title": "下週行動建議",
    "priority": "基於本週洞察，下週最值得關注和投入的一個改善點。",
    "specific": ["具體可執行的建議1", "建議2"],
    "systemOptimization": "根據本週記錄情況，提供 1 個可以優化『記錄流程』或『生活系統』的建議。"
  },
  "weeklyQuestion": {
    "title": "週末反思問題",
    "question": "一個深度的開放式問題，幫助我反思這週的核心主題和下週的方向。"
  }
}`;
  },
  
  /**
   * Build daily breakdown for weekly report
   * @private
   */
  _buildDailyBreakdown(dailyData) {
    // Check if we have any data
    if (!dailyData || dailyData.length === 0) {
      return '本週暫無數據記錄';
    }
    
    return dailyData.map(entry => {
      // Ensure timestamp is a valid Date object
      let timestamp = entry.timestamp;
      if (!(timestamp instanceof Date)) {
        // If timestamp is a string, try to parse it
        if (typeof timestamp === 'string') {
          timestamp = new Date(timestamp);
        } else {
          // Fallback to using adjustedDate if available
          timestamp = entry.adjustedDate ? new Date(entry.adjustedDate) : new Date();
        }
      }
      
      const date = Utilities.formatDate(timestamp, CONFIG.TIME_ZONE, "MM/dd");
      const behaviorScore = entry.behaviorTotal || 0;
      const sleepScore = entry.sleepTotal || 0;
      return `- ${date}: 行為 ${behaviorScore}/100, 睡眠 ${sleepScore}/100`;
    }).join('\n');
  },

  /**
   * Build weekly highlights summary
   * @private
   */
  _buildWeeklyHighlights(dailyData) {
    const highlights = [];
    
    // Check if we have any data
    if (!dailyData || dailyData.length === 0) {
      return '本週暫無數據記錄';
    }
    
    // Find best behavior day
    const bestBehaviorDay = dailyData.reduce((best, current) => 
      (current.behaviorTotal || 0) > (best.behaviorTotal || 0) ? current : best
    , dailyData[0]); // Provide initial value
    
    if (bestBehaviorDay.behaviorTotal > 0) {
      // Ensure timestamp is a valid Date object
      let timestamp = bestBehaviorDay.timestamp;
      if (!(timestamp instanceof Date)) {
        if (typeof timestamp === 'string') {
          timestamp = new Date(timestamp);
        } else {
          timestamp = bestBehaviorDay.adjustedDate ? new Date(bestBehaviorDay.adjustedDate) : new Date();
        }
      }
      const date = Utilities.formatDate(timestamp, CONFIG.TIME_ZONE, "MM/dd");
      highlights.push(`最佳行為表現日: ${date} (${bestBehaviorDay.behaviorTotal}/100)`);
    }
    
    // Find best sleep day
    const bestSleepDay = dailyData.reduce((best, current) => 
      (current.sleepTotal || 0) > (best.sleepTotal || 0) ? current : best
    , dailyData[0]); // Provide initial value
    
    if (bestSleepDay.sleepTotal > 0) {
      // Ensure timestamp is a valid Date object
      let timestamp = bestSleepDay.timestamp;
      if (!(timestamp instanceof Date)) {
        if (typeof timestamp === 'string') {
          timestamp = new Date(timestamp);
        } else {
          timestamp = bestSleepDay.adjustedDate ? new Date(bestSleepDay.adjustedDate) : new Date();
        }
      }
      const date = Utilities.formatDate(timestamp, CONFIG.TIME_ZONE, "MM/dd");
      highlights.push(`最佳睡眠品質日: ${date} (${bestSleepDay.sleepTotal}/100)`);
    }
    
    return highlights.length > 0 ? highlights.join('\n') : '本週持續努力中...';
  },

  /**
   * Build concerning patterns summary
   * @private
   */
  _buildConcerningPatterns(dailyData) {
    const patterns = [];
    
    // Check for low behavior scores
    const lowBehaviorDays = dailyData.filter(entry => (entry.behaviorTotal || 0) < 50);
    if (lowBehaviorDays.length >= 2) {
      patterns.push(`行為效率偏低的天數: ${lowBehaviorDays.length} 天`);
    }
    
    // Check for low sleep scores
    const lowSleepDays = dailyData.filter(entry => (entry.sleepTotal || 0) < 60);
    if (lowSleepDays.length >= 2) {
      patterns.push(`睡眠品質待改善的天數: ${lowSleepDays.length} 天`);
    }
    
    return patterns.length > 0 ? patterns.join('\n') : '整體表現穩定';
  },
  
  /**
   * Register a new template version
   * @param {string} type - Type of template ('daily' or 'weekly')
   * @param {string} version - Version identifier
   * @param {Object} template - Template definition
   */
  registerTemplate(type, version, template) {
    if (!this.templates[type]) {
      this.templates[type] = {};
    }
    
    this.templates[type][version] = template;
    console.log(`[PromptBuilderService] Registered ${type} template version ${version}`);
  },
  
  /**
   * Set active template version
   * @param {string} type - Type of template
   * @param {string} version - Version to activate
   */
  setActiveVersion(type, version) {
    if (!this.templates[type] || !this.templates[type][version]) {
      throw new Error(`Template version ${version} not found for type ${type}`);
    }
    
    this.activeVersions[type] = version;
    console.log(`[PromptBuilderService] Set ${type} template to version ${version}`);
  },
  
  /**
   * Get system message for LLM
   * @param {string} type - Type of template ('daily' or 'weekly')
   * @returns {string} System message
   */
  getSystemMessage(type = 'daily') {
    const template = this.templates[type][this.activeVersions[type]];
    return template.system || "You are a helpful assistant.";
  }
};
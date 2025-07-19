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
      }
    }
  },
  
  activeVersions: {
    daily: 'v1',
    weekly: 'v1'
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
      `你是我的個人成長教練和回憶整理師，請深度分析這週的整體表現模式，並從日誌中提取珍貴的生活回憶。`,
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
      `## 📖 回憶錄生成指導\n` +
      `以上的「本週日誌筆記」是最珍貴的第一手生活記錄。請你作為專業的回憶整理師，深度挖掘其中的重要信息：\n\n` +
      `**重要經歷識別**: 找出改變想法、帶來新體驗、或有深刻感受的時刻\n` +
      `**情感軌跡追蹤**: 觀察心境變化、壓力來源、快樂源泉\n` +
      `**成長信號捕捉**: 發現學習機會、技能提升、思維模式改變\n` +
      `**關係洞察提煉**: 注意人際互動、友情變化、支持網絡\n` +
      `**隱藏模式發現**: 結合量化數據，發現行為背後的深層動機`,
      `---`,
      template.instructionSection,
      `請用以下JSON格式回覆：\n\n` +
      this.getWeeklyAnalysisJsonFormat()
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
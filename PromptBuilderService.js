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
      // Weekly template can be added here
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
   * @param {string} type - Type of template
   * @returns {string} System message
   */
  getSystemMessage(type = 'daily') {
    const template = this.templates[type][this.activeVersions[type]];
    return template.system || "You are a helpful assistant.";
  }
}; 
/**
 * Behavior Score Service
 * Responsible for all behavior score-related calculations, configuration management, and data retrieval.
 *
 * @version 3.0.0
 */
const BehaviorScoreService = {
  // --- Internal Properties ---
  _config: {
    DAILY_GOAL: 20,   // ▸ Target score: Daily raw score reaching this value equals 100 points
  },
  _cachedScores: null,

  // ==================================================================
  // ===================== Public Methods =============================
  // ==================================================================

  /**
   * [New Method] Get daily score (ensures scores are up to date).
   * This method first triggers the Manager to check and score new behaviors, then performs calculations.
   * This is the main entry point for external services (like DailyReport).
   * @param {string[]} behaviors - List of daily behaviors.
   * @returns {{ total:number, details:Object }}
   */
  getUpToDateDailyScore: function(behaviors) {
    console.log('[Service Coordination] BehaviorScoreService received calculation request, starting pre-update check...');
    
    // 1. Call Manager to update score sheet
    const scoresWereUpdated = updateBehaviorScores();

    // 2. If score sheet was just updated, clear local cache
    if (scoresWereUpdated) {
      this.clearCache();
    }
    
    // 3. Calculate using ensured up-to-date data
    return this.calculateDailyScore(behaviors);
  },

  /**
   * Calculate DES (Daily Efficiency Score): Fixed scale 0-100, capped at 100 when exceeding DAILY_GOAL.
   * @param {string[]} behaviors - List of daily behaviors.
   * @returns {{ total:number, details:Object }} Object containing total score and detailed information.
   */
  calculateDailyScore: function(behaviors) {
    const cleanBehaviors = behaviors.map(b => String(b).trim()).filter(Boolean);
    let positive = 0;
    let negative = 0;
    const behaviorScoresDetail = {};

    cleanBehaviors.forEach(behavior => {
      // [Modified] Internal call using this.
      const score = this.getBehaviorScore(behavior);
      behaviorScoresDetail[behavior] = score;

      if (score > 0) {
        positive += score;
      } else if (score < 0) {
        negative += Math.abs(score);
      }
    });

    const rawScore = positive - negative;
    // [Modified] Reading internal config using this.
    const goal = this._config.DAILY_GOAL;
    const clampedScore = Math.max(0, Math.min(rawScore, goal));
    const dailyScore = goal > 0 ? Math.round((clampedScore / goal) * 100) : 0;

    return {
      total: dailyScore,
      details: { rawScore, positive, negative, behaviorScores: behaviorScoresDetail, goal: goal }
    };
  },

  /**
   * Calculate Efficiency Index (LBI): Normalizes daily actual total score to 0-100 range.
   * @param {string[]} behaviors - List of daily behaviors.
   * @returns {{ total:number, details:Object }} Object containing index total and detailed information.
   */
  calculateEfficiencyIndex: function(behaviors) {
    const cleanBehaviors = behaviors.map(b => String(b).trim()).filter(Boolean);
    if (cleanBehaviors.length === 0) {
      return { total: 0, details: {} };
    }

    const rawScores = cleanBehaviors.map(b => this.getBehaviorScore(b));
    const totalScore = rawScores.reduce((sum, score) => sum + score, 0);
    const maxPossibleScore = cleanBehaviors.length * this.getMaxBehaviorScore();
    const minPossibleScore = cleanBehaviors.length * this.getMinBehaviorScore();
    const range = maxPossibleScore - minPossibleScore;
    let normalizedScore = 0;

    if (range > 0) {
      normalizedScore = Math.round(((totalScore - minPossibleScore) / range) * 100);
    } else if (totalScore >= maxPossibleScore) {
      normalizedScore = 100;
    }

    return {
      total: normalizedScore,
      details: { rawScores, totalScore, maxPossibleScore, minPossibleScore }
    };
  },

  // ==================================================================
  // ================ Helpers & Internal Methods =======================
  // ==================================================================

  /**
   * [New Method] (Public) Clear internal cache.
   */
  clearCache: function() {
    console.log('[Service Coordination] Behavior score cache cleared, will be reloaded from sheet next time.');
    this._cachedScores = null;
  },
  
  /**
   * (Public) Get behavior score table, this function includes caching mechanism.
   */
  getScores: function() {
    // [Modified] Reading internal property using this.
    if (this._cachedScores === null) {
      this._cachedScores = this._loadScoresFromSheet();
    }
    return this._cachedScores;
  },

  /**
   * (Private) Internal function to actually read scores from Google Sheet.
   * @private
   */
  _loadScoresFromSheet: function() {
    try {
      console.log('Reading behavior scores from Google Sheet...');
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      // [Fixed] Use the sheet name from the global CONFIG object
      const sheetName = CONFIG.OUTPUT.BEHAVIOR_SHEET;
      const scoreSheet = ss.getSheetByName(sheetName);
      
      if (!scoreSheet) {
        // [Fixed] Improved error message
        throw new Error(`Sheet named '${sheetName}' not found! Please check CONFIG.OUTPUT.BEHAVIOR_SHEET.`);
      }
      const lastRow = scoreSheet.getLastRow();
      if (lastRow <= 1) return {};

      const data = scoreSheet.getRange(2, 1, lastRow - 1, 2).getValues();
      const scores = {};
      data.forEach(row => {
        const behavior = row[0];
        const score = row[1];
        if (behavior && String(behavior).trim() !== '' && !isNaN(score) && score !== null && score !== '') {
          scores[String(behavior).trim()] = Number(score);
        }
      });
      console.log(`Successfully read and cached ${Object.keys(scores).length} behavior scores.`);
      return scores;
    } catch(e) {
      console.error(e.message);
      // [Fixed] Removed SpreadsheetApp.getUi() which is not available in all contexts
      // SpreadsheetApp.getUi().alert(e.message);
      return {};
    }
  },

  getBehaviorScore: function(behavior) {
    const scores = this.getScores();
    return scores[behavior] || 0;
  },

  getAllBehaviors: function() {
    const scores = this.getScores();
    return Object.keys(scores);
  },

  getMaxBehaviorScore: function() {
    const scoreValues = Object.values(this.getScores());
    return scoreValues.length > 0 ? Math.max(...scoreValues) : 0;
  },

  getMinBehaviorScore: function() {
    const scoreValues = Object.values(this.getScores());
    return scoreValues.length > 0 ? Math.min(...scoreValues) : 0;
  }
};
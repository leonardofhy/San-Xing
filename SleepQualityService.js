/**
 * Sleep Quality Service
 * Provides comprehensive assessment of sleep duration, quality, and regularity.
 * All functionality is encapsulated in this service.
 *
 * @version 2.0.0
 */
const SleepQualityService = {

  // ==================================================================
  // ===================== Public Methods =============================
  // ==================================================================

  /**
   * [Core] Calculate sleep health index. This is the only entry point for this service.
   * @param {Object} sleepData - Sleep data
   * @param {string} sleepData.start - Sleep start time (HHMM)
   * @param {string} sleepData.end - Wake up time (HHMM)
   * @param {number} sleepData.quality - Sleep quality (1-5)
   * @returns {Object} Object containing total score and detailed information
   */
  calculateSleepHealthIndex: function(sleepData) {
    // Gracefully handle missing fields. Each sub-score becomes null when data is absent.
    if (!sleepData) sleepData = {};

    const hasStart = !!sleepData.start;
    const hasEnd = !!sleepData.end;
    const hasQuality = sleepData.quality !== undefined && sleepData.quality !== null && sleepData.quality !== '';

    // Duration & regularity rely on start/end
    let durationHours = null;
    let durationScore = null;
    let regularityScore = null;

    if (hasStart && hasEnd) {
      const startTime = this._parseTime(sleepData.start);
      const endTime = this._parseTime(sleepData.end);
      durationHours = endTime - startTime;
      if (durationHours < 0) durationHours += 24;
      durationScore = this._calculateDurationScore(durationHours);
      regularityScore = this._calculateSleepRegularityScore(sleepData.start);
    }

    // Quality score
    let qualityScore = null;
    if (hasQuality) {
      qualityScore = (Number(sleepData.quality) / 5) * 40;
    }

    // Total only when all parts are present
    const parts = [durationScore, qualityScore, regularityScore];
    const totalScore = parts.every(v => v !== null) ? (durationScore + qualityScore + regularityScore) : null;

    return {
      total: totalScore !== null ? Math.round(totalScore) : null,
      details: {
        duration: {
          hours: durationHours,
          score: durationScore,
          evaluation: durationScore !== null ? this._getDurationEvaluation(durationHours) : 'Missing data'
        },
        quality: {
          rating: hasQuality ? sleepData.quality : null,
          score: qualityScore,
          evaluation: qualityScore !== null ? this._getQualityEvaluation(sleepData.quality) : 'Missing data'
        },
        regularity: {
          score: regularityScore,
          evaluation: regularityScore !== null ? this._getRegularityEvaluation(regularityScore) : 'Missing data'
        }
      },
      summary: totalScore !== null ? this._generateSleepSummary(durationHours, sleepData.quality, regularityScore) : {}
    };
  },

  // ==================================================================
  // =================== Private Helper Methods =======================
  // ==================================================================

  _parseTime: function(timeStr) {
    const time = String(timeStr).padStart(4, '0');
    const hours = parseInt(time.substring(0, 2), 10);
    const minutes = parseInt(time.substring(2, 4), 10);
    return hours + minutes / 60;
  },

  _calculateDurationScore: function(duration) {
    if (duration >= 7 && duration <= 9) return 40;
    if ((duration >= 6 && duration < 7) || (duration > 9 && duration <= 10)) return 30;
    if ((duration >= 5 && duration < 6) || (duration > 10 && duration <= 11)) return 20;
    if ((duration >= 4 && duration < 5) || (duration > 11)) return 10;
    return 0;
  },

  _calculateSleepRegularityScore: function(sleepStart) {
    const startHour = this._parseTime(sleepStart);
    if (startHour >= 22 && startHour < 24) return 20; // Ideal sleep time (22:00-23:59)
    if ((startHour >= 21 && startHour < 22) || (startHour >= 0 && startHour < 1)) return 15; // Slightly early/late
    if ((startHour >= 20 && startHour < 21) || (startHour >= 1 && startHour < 2)) return 10; // Early/late
    return 5; // Irregular
  },

  _getDurationEvaluation: function(duration) {
    if (duration >= 7 && duration <= 9) return "Ideal sleep duration";
    if (duration >= 6 && duration < 7) return "Slightly short sleep duration";
    if (duration > 9 && duration <= 10) return "Slightly long sleep duration";
    if (duration >= 5 && duration < 6) return "Short sleep duration";
    if (duration > 10 && duration <= 11) return "Long sleep duration";
    if (duration >= 4 && duration < 5) return "Very short sleep duration";
    if (duration > 11) return "Excessive sleep duration";
    return "Severely insufficient sleep duration";
  },

  _getQualityEvaluation: function(quality) {
    if (quality >= 4.5) return "Excellent sleep quality";
    if (quality >= 4) return "Good sleep quality";
    if (quality >= 3) return "Average sleep quality";
    if (quality >= 2) return "Poor sleep quality";
    return "Very poor sleep quality";
  },

  _getRegularityEvaluation: function(score) {
    if (score >= 18) return "Very regular sleep schedule";
    if (score >= 15) return "Regular sleep schedule";
    if (score >= 10) return "Moderately regular sleep schedule";
    return "Irregular sleep schedule";
  },

  _generateSleepSummary: function(duration, quality, regularityScore) {
    return {
      overall: this._getOverallEvaluation(duration, quality, regularityScore),
      suggestions: this._generateSleepSuggestions(duration, quality, regularityScore),
      details: {
        duration: this._getDurationEvaluation(duration),
        quality: this._getQualityEvaluation(quality),
        regularity: this._getRegularityEvaluation(regularityScore)
      }
    };
  },

  _getOverallEvaluation: function(duration, quality, regularityScore) {
    const durationScore = this._calculateDurationScore(duration);
    const qualityScore = (Number(quality) / 5) * 40;
    const totalScore = durationScore + qualityScore + regularityScore;
    
    if (totalScore >= 90) return "Excellent sleep condition";
    if (totalScore >= 80) return "Good sleep condition";
    if (totalScore >= 70) return "Average sleep condition";
    if (totalScore >= 60) return "Sleep condition needs improvement";
    return "Sleep condition needs attention";
  },

  _generateSleepSuggestions: function(duration, quality, regularityScore) {
    const suggestions = [];
    if (duration < 6) {
      suggestions.push("Consider increasing sleep duration to ensure at least 6 hours of sleep daily.");
    } else if (duration > 10) {
      suggestions.push("Sleep duration may be too long, consider keeping it under 10 hours.");
    }
    if (quality < 3) {
      suggestions.push("Sleep quality is poor, consider checking sleep environment and pre-sleep habits.");
    }
    if (regularityScore < 15) {
      suggestions.push("Consider maintaining a regular sleep schedule, preferably falling asleep between 22:00-23:59.");
    }
    if (suggestions.length === 0) {
      suggestions.push("Overall sleep condition is good, keep it up!");
    }
    return suggestions;
  }
};
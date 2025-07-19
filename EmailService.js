/**
 * EmailService - Template-based email generation and sending
 * Handles all email-related operations with retry logic
 */
const EmailService = {
  templates: {
    daily: {
      v1: {
        subjectTemplate: '{date} 每日摘要｜心情: {mood}｜行為: {behaviorScore}｜睡眠: {sleepScore}',
        
        cssStyles: `body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;line-height:1.7;color:#34495e;max-width:680px;margin:20px auto;padding:0;background-color:#f4f7f6}.container{background-color:#fff;padding:20px 30px 30px;border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,.06)}h1{color:#2c3e50;font-size:24px;border-bottom:2px solid #e0e0e0;padding-bottom:12px;margin:0 0 20px}h2{color:#2980b9;font-size:18px;margin-top:30px;margin-bottom:15px;border-left:4px solid #3498db;padding-left:12px;font-weight:600}ul{list-style-type:none;padding-left:5px;margin:0}li{margin-bottom:10px;padding-left:20px;position:relative}li::before{content:'•';color:#3498db;font-size:20px;position:absolute;left:0;top:-3px}strong{color:#c0392b;font-weight:600}.feedback-section{margin-top:30px;background-color:#e8f4fd;padding:20px;border-radius:8px;border:1px solid #d0e0f0}.feedback-section h2{margin-top:0;color:#2c3e50;border-color:#2980b9}.feedback-section li::before{color:#2980b9}.score-section{margin-top:20px;background-color:#f8f9fa;padding:15px;border-radius:8px;border:1px solid #e9ecef}.score-section h3{color:#2c3e50;margin-top:0;font-size:16px}.score-value{font-size:24px;color:#2980b9;font-weight:700;margin:10px 0}.score-details{font-size:14px;color:#7f8c8d}`,
        
        bodyTemplate: `<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>{css}</style></head>
<body>
<div class="container">
<h1>每日摘要報告 - {date}</h1>
<div class="score-section">
<h3>今日評分</h3>
<div class="score-value">行為效率分數：{behaviorTotal}/100</div>
<div class="score-details">(原始分: {behaviorRaw}, 正向: {behaviorPositive}, 負向: {behaviorNegative})</div>
<div class="score-value">睡眠健康指數：{sleepTotal}/100</div>
<div class="score-details">(時長: {sleepDuration}, 品質: {sleepQuality}, 規律: {sleepRegularity})</div>
</div>
{analysisContent}
</div>
</body>
</html>`
      }
    },
    weekly: {
      v1: {
        subjectTemplate: '週報告 | {dateRange} | 平均分數: {avgScore}',
        bodyTemplate: `<!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><style>{css}</style></head>
    <body>
    <div class="container">
    <h1>週報告 - {dateRange}</h1>
    <div class="score-section">
    <h3>本週平均表現</h3>
    <div class="score-value">平均行為效率分數：{avgBehaviorTotal}/100</div>
    <div class="score-value">平均睡眠健康指數：{avgSleepTotal}/100</div>
    <div class="score-details">數據完整度：{daysWithData}/{totalDays} 天</div>
    </div>
    {analysisContent}
    </div>
    </body>
    </html>`,
        cssStyles: `body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;line-height:1.7;color:#34495e;max-width:680px;margin:20px auto;padding:0;background-color:#f4f7f6}.container{background-color:#fff;padding:20px 30px 30px;border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,.06)}h1{color:#2c3e50;font-size:24px;border-bottom:2px solid #e0e0e0;padding-bottom:12px;margin:0 0 20px}h2{color:#2980b9;font-size:18px;margin-top:30px;margin-bottom:15px;border-left:4px solid #3498db;padding-left:12px;font-weight:600}h3{color:#2c3e50;margin-top:0;font-size:16px}ul{list-style-type:none;padding-left:5px;margin:0}li{margin-bottom:10px;padding-left:20px;position:relative}li::before{content:'•';color:#3498db;font-size:20px;position:absolute;left:0;top:-3px}strong{color:#c0392b;font-weight:600}.feedback-section{margin-top:30px;background-color:#e8f4fd;padding:20px;border-radius:8px;border:1px solid #d0e0f0}.feedback-section h2{margin-top:0;color:#2c3e50;border-color:#2980b9}.feedback-section li::before{color:#2980b9}.score-section{margin-top:20px;background-color:#f8f9fa;padding:15px;border-radius:8px;border:1px solid #e9ecef}.score-value{font-size:20px;color:#2980b9;font-weight:700;margin:8px 0}.score-details{font-size:14px;color:#7f8c8d;margin-top:5px}.daily-scores-table{width:100%;border-collapse:collapse;margin:20px 0;background-color:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 4px rgba(0,0,0,0.1)}.daily-scores-table th{background-color:#3498db;color:#fff;padding:12px 15px;text-align:left;font-weight:600;font-size:14px}.daily-scores-table td{padding:12px 15px;border-bottom:1px solid #e9ecef;font-size:14px}.daily-scores-table tr:last-child td{border-bottom:none}.daily-scores-table tr:nth-child(even){background-color:#f8f9fa}.score-high{color:#27ae60;font-weight:600}.score-medium{color:#f39c12;font-weight:600}.score-low{color:#e74c3c;font-weight:600}`
      }
    },
  },
  
  activeVersions: {
    daily: 'v1',
    weekly: 'v1'
  },
  
  labelConfig: {
    basePath: 'Meta-Awareness',
    daily: 'Daily',
    weekly: 'Weekly'
  },
  
  retryConfig: {
    maxAttempts: 4,
    delayMs: 3000,
    firstDelayMs: 2000
  },
  
  /**
   * Send daily report email
   * @param {Object} reportData - Report data
   * @returns {Promise<boolean>} Success status
   */
  async sendDailyReport(reportData) {
    const { date, analysis, scores, mood } = reportData;
    
    // Build subject
    const subject = this.buildSubject('daily', {
      date: date,
      mood: mood || 'N/A',
      behaviorScore: scores.behavior.total,
      sleepScore: scores.sleep.total
    });
    
    // Build HTML body
    const htmlBody = this.buildHtmlBody('daily', {
      date: date,
      analysis: analysis,
      scores: scores
    });
    
    // Send email with retry logic
    console.log(`[EmailService] Sending daily report email: ${subject}`);
    
    try {
      await this._sendEmailWithRetry(CONFIG.RECIPIENT_EMAIL, subject, htmlBody);
      
      // Apply Gmail label
      await this._applyGmailLabel(CONFIG.RECIPIENT_EMAIL, subject, 'daily');
      
      console.log('[EmailService] Email sent successfully');
      return true;
      
    } catch (error) {
      console.error('[EmailService] Failed to send email:', error);
      EventBus.emit('EMAIL_SEND_FAILED', {
        error: error.message,
        recipient: CONFIG.RECIPIENT_EMAIL,
        subject: subject
      });
      throw error;
    }
  },

  // Add sendWeeklyReport method
async sendWeeklyReport(reportData) {
  const { weekStart, weekEnd, analysis, aggregatedScores, weeklyData } = reportData;
  const dateRange = `${weekStart} - ${weekEnd}`;
  
  const subject = this.buildSubject('weekly', {
    dateRange: dateRange,
    avgScore: aggregatedScores.avgBehaviorTotal.toFixed(1)
  });
  
  const htmlBody = this.buildHtmlBody('weekly', {
    dateRange: dateRange,
    analysis: analysis,
    scores: aggregatedScores,
    daysWithData: reportData.daysWithData,
    totalDays: 7,
    dailyData: weeklyData?.dailyData || []
  });
  
  console.log(`[EmailService] Sending weekly report email: ${subject}`);
  
  try {
      await this._sendEmailWithRetry(CONFIG.RECIPIENT_EMAIL, subject, htmlBody);
      await this._applyGmailLabel(CONFIG.RECIPIENT_EMAIL, subject, 'weekly');
      console.log('[EmailService] Weekly email sent successfully');
      return true;
  } catch (error) {
      console.error('[EmailService] Failed to send weekly email:', error);
      EventBus.emit('EMAIL_SEND_FAILED', {
        error: error.message,
        recipient: CONFIG.RECIPIENT_EMAIL,
        subject: subject,
        type: 'weekly'
      });
      throw error;
    }
  },

  
  /**
   * Build email subject from template
   * @private
   */
  buildSubject(type, data) {
    const template = this.templates[type][this.activeVersions[type]];
    let subject = template.subjectTemplate;
    
    Object.entries(data).forEach(([key, value]) => {
      subject = subject.replace(new RegExp(`{${key}}`, 'g'), value);
    });
    
    return subject;
  },
  
  /**
   * Build HTML body from template
   * @private
   */
  buildHtmlBody(type, data) {
    const template = this.templates[type][this.activeVersions[type]];
    
    // Generate analysis content HTML with type info
    const analysisHtml = this._renderAnalysisHtml(data.analysis, type, data.dailyData);
    
    let templateData = {
      css: template.cssStyles,
      analysisContent: analysisHtml
    };
    
    // Handle different data structures for daily vs weekly reports
    if (type === 'daily') {
      const { date, scores } = data;
      templateData = {
        ...templateData,
        date: date,
        behaviorTotal: scores.behavior.total,
        behaviorRaw: scores.behavior.details?.rawScore || 0,
        behaviorPositive: scores.behavior.details?.positive || 0,
        behaviorNegative: scores.behavior.details?.negative || 0,
        sleepTotal: scores.sleep.total,
        sleepDuration: scores.sleep.details?.duration?.score || 0,
        sleepQuality: scores.sleep.details?.quality?.score || 0,
        sleepRegularity: scores.sleep.details?.regularity?.score || 0
      };
    } else if (type === 'weekly') {
      const { dateRange, scores, daysWithData, totalDays, dailyData } = data;
      templateData = {
        ...templateData,
        dateRange: dateRange,
        avgBehaviorTotal: scores.avgBehaviorTotal.toFixed(1),
        avgSleepTotal: scores.avgSleepTotal.toFixed(1),
        daysWithData: daysWithData,
        totalDays: totalDays,
        dailyData: dailyData || []
      };
    }
    
    // Replace placeholders
    let html = template.bodyTemplate;
    Object.entries(templateData).forEach(([key, value]) => {
      html = html.replace(new RegExp(`{${key}}`, 'g'), value);
    });
    
    return html;
  },
  
  /**
   * Render analysis JSON to HTML
   * @private
   */
  _renderAnalysisHtml(analysis, type = 'daily', dailyData = []) {
    if (!analysis) {
      return '<h2>分析生成失敗</h2><p>無法從 AI 服務獲取有效的分析結果。</p>';
    }
    
    const escapeHtml = (text) => {
      if (typeof text !== 'string') return '';
      return text.replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    };
    
    if (type === 'weekly') {
      return this._renderWeeklyAnalysisHtml(analysis, escapeHtml, dailyData);
    } else {
      return this._renderDailyAnalysisHtml(analysis, escapeHtml);
    }
  },

  /**
   * Render daily analysis HTML
   * @private
   */
  _renderDailyAnalysisHtml(analysis, escapeHtml) {
    const br = analysis.behaviorReview || {};
    const sa = analysis.sleepAnalysis || {};
    const ss = analysis.statusSummary || {};
    const cf = analysis.coachFeedback || {};
    
    return `
      <h2>${escapeHtml(br.title || '1. 行為盤點')}</h2>
      <ul>
        <li><strong>正向行為</strong>：${(br.positive && br.positive.length > 0) ? escapeHtml(br.positive.join('、')) : '無'}</li>
        <li><strong>負向行為</strong>：${(br.negative && br.negative.length > 0) ? escapeHtml(br.negative.join('、')) : '無'}</li>
        <li><strong>中性行為</strong>：${(br.neutral && br.neutral.length > 0) ? escapeHtml(br.neutral.join('、')) : '無'}</li>
      </ul>
      
      <h2>${escapeHtml(sa.title || '2. 睡眠分析與洞察')}</h2>
      <ul>
        ${sa.insight ? `<li>${escapeHtml(sa.insight)}</li>` : ''}
        ${(sa.recommendations || []).map(rec => `<li>${escapeHtml(rec)}</li>`).join('')}
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
  },

  /**
   * Render weekly analysis HTML
   * @private
   */
  _renderWeeklyAnalysisHtml(analysis, escapeHtml, dailyData = []) {
    const wm = analysis.weeklyMemoir || {};
    const wo = analysis.weeklyOverview || {};
    const ki = analysis.keyInsights || {};
    const wr = analysis.weeklyRecommendations || {};
    const wq = analysis.weeklyQuestion || {};
    
    // Build daily scores table
    const dailyScoresTable = this._buildDailyScoresTable(dailyData, escapeHtml);
    
    return `
      ${dailyScoresTable}
      
      <div class="feedback-section">
        <h2>${escapeHtml(wm.title || '本週回憶錄')}</h2>
        ${wm.keyMoments && wm.keyMoments.length > 0 ? `
          <h3>重要時刻</h3>
          <ul>
            ${wm.keyMoments.map(moment => `<li>${escapeHtml(moment)}</li>`).join('')}
          </ul>
        ` : ''}
        ${wm.emotionalJourney ? `
          <h3>情感軌跡</h3>
          <p>${escapeHtml(wm.emotionalJourney)}</p>
        ` : ''}
        ${wm.growthSignals && wm.growthSignals.length > 0 ? `
          <h3>成長信號</h3>
          <ul>
            ${wm.growthSignals.map(signal => `<li>${escapeHtml(signal)}</li>`).join('')}
          </ul>
        ` : ''}
        ${wm.relationshipInsights ? `
          <h3>人際關係洞察</h3>
          <p>${escapeHtml(wm.relationshipInsights)}</p>
        ` : ''}
      </div>
      
      <h2>${escapeHtml(wo.title || '本週整體回顧')}</h2>
      <p>${escapeHtml(wo.summary || '')}</p>
      
      <h2>${escapeHtml(ki.title || '關鍵洞察')}</h2>
      <ul>
        ${ki.patterns && ki.patterns.length > 0 ? `<li><strong>行為模式</strong>：${escapeHtml(ki.patterns.join('、'))}</li>` : ''}
        ${ki.strengths && ki.strengths.length > 0 ? `<li><strong>表現優勢</strong>：${escapeHtml(ki.strengths.join('、'))}</li>` : ''}
        ${ki.improvements && ki.improvements.length > 0 ? `<li><strong>改善領域</strong>：${escapeHtml(ki.improvements.join('、'))}</li>` : ''}
      </ul>
      
      <div class="feedback-section">
        <h2>${escapeHtml(wr.title || '下週行動建議')}</h2>
        <ul>
          ${wr.priority ? `<li><strong>優先重點</strong>：${escapeHtml(wr.priority)}</li>` : ''}
          ${wr.specific && wr.specific.length > 0 ? `<li><strong>具體行動</strong>：${escapeHtml(wr.specific.join('、'))}</li>` : ''}
          ${wr.systemOptimization ? `<li><strong>系統優化</strong>：${escapeHtml(wr.systemOptimization)}</li>` : ''}
        </ul>
      </div>

      <div class="feedback-section">
        <h2>${escapeHtml(wq.title || '週末反思問題')}</h2>
        <p><strong>${escapeHtml(wq.question || '')}</strong></p>
      </div>
    `;
  },
  
  /**
   * Send email with retry logic
   * @private
   */
  async _sendEmailWithRetry(recipient, subject, htmlBody) {
    const maxAttempts = 1; // Email sending usually doesn't need retry
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        GmailApp.sendEmail(recipient, subject, "", { htmlBody: htmlBody });
        return;
      } catch (error) {
        if (attempt === maxAttempts) {
          throw error;
        }
        console.log(`[EmailService] Email send failed, attempt ${attempt}/${maxAttempts}`);
        Utilities.sleep(this.retryConfig.delayMs);
      }
    }
  },
  
  /**
   * Apply Gmail label to sent email
   * @private
   */
  async _applyGmailLabel(recipient, subject, reportType) {
    const labelPath = `${this.labelConfig.basePath}/${reportType === 'daily' ? this.labelConfig.daily : this.labelConfig.weekly}`;
    const label = GmailApp.getUserLabelByName(labelPath) || GmailApp.createLabel(labelPath);
    
    // Sanitize subject for search
    const sanitizedSubject = subject.replace(/[|]/g, ' ').replace(/\s+/g, ' ').trim();
    const searchQuery = `subject:("${sanitizedSubject}") to:(${recipient}) from:me newer_than:2m`;
    
    let attempts = 0;
    let delay = this.retryConfig.firstDelayMs;
    
    while (attempts < this.retryConfig.maxAttempts) {
      attempts++;
      
      if (attempts > 1) {
        Utilities.sleep(delay);
        delay = this.retryConfig.delayMs;
      } else {
        Utilities.sleep(this.retryConfig.firstDelayMs);
      }
      
      console.log(`[EmailService] Searching for email to label (attempt ${attempts}/${this.retryConfig.maxAttempts})`);
      const threads = GmailApp.search(searchQuery, 0, 1);
      
      if (threads.length > 0) {
        threads[0].addLabel(label);
        console.log(`[EmailService] Successfully applied label '${labelPath}'`);
        return;
      }
    }
    
    console.warn('[EmailService] Could not find email to apply label');
  },
  
  /**
   * Register email template
   * @param {string} type - Template type
   * @param {string} version - Version identifier
   * @param {Object} template - Template definition
   */
  registerTemplate(type, version, template) {
    if (!this.templates[type]) {
      this.templates[type] = {};
    }
    
    this.templates[type][version] = template;
    console.log(`[EmailService] Registered ${type} template version ${version}`);
  },
  
  /**
   * Build daily scores table HTML
   * @private
   */
  _buildDailyScoresTable(dailyData, escapeHtml) {
    if (!dailyData || dailyData.length === 0) {
      return '<p>本週暫無每日分數記錄</p>';
    }
    
    // Helper function to get score class for styling
    const getScoreClass = (score) => {
      if (score >= 80) return 'score-high';
      if (score >= 60) return 'score-medium';
      return 'score-low';
    };
    
    // Format date from YYYY/MM/DD to more readable format
    const formatDate = (dateStr) => {
      try {
        const [year, month, day] = dateStr.split('/');
        const date = new Date(year, month - 1, day);
        const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
        const weekday = weekdays[date.getDay()];
        return `${month}/${day} (${weekday})`;
      } catch (error) {
        return dateStr;
      }
    };
    
    const tableRows = dailyData.map(day => {
      const behaviorScore = day.behaviorTotal || 0;
      const sleepScore = day.sleepTotal || 0;
      const formattedDate = formatDate(day.date || day.adjustedDate);
      
      return `
        <tr>
          <td>${escapeHtml(formattedDate)}</td>
          <td class="${getScoreClass(behaviorScore)}">${behaviorScore}</td>
          <td class="${getScoreClass(sleepScore)}">${sleepScore}</td>
        </tr>
      `;
    }).join('');
    
    return `
      <h2>本週每日表現</h2>
      <table class="daily-scores-table">
        <thead>
          <tr>
            <th>日期</th>
            <th>行為分數</th>
            <th>睡眠分數</th>
          </tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>
    `;
  }
}; 
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
    }
  },
  
  activeVersions: {
    daily: 'v1'
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
    const { date, analysis, scores } = data;
    
    // Generate analysis content HTML
    const analysisHtml = this._renderAnalysisHtml(analysis);
    
    // Prepare template data
    const templateData = {
      css: template.cssStyles,
      date: date,
      behaviorTotal: scores.behavior.total,
      behaviorRaw: scores.behavior.details?.rawScore || 0,
      behaviorPositive: scores.behavior.details?.positive || 0,
      behaviorNegative: scores.behavior.details?.negative || 0,
      sleepTotal: scores.sleep.total,
      sleepDuration: scores.sleep.details?.duration?.score || 0,
      sleepQuality: scores.sleep.details?.quality?.score || 0,
      sleepRegularity: scores.sleep.details?.regularity?.score || 0,
      analysisContent: analysisHtml
    };
    
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
  _renderAnalysisHtml(analysis) {
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
  }
}; 
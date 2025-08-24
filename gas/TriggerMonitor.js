/**
 * TriggerMonitor.js - Trigger 监控和健康检查系统
 * 
 * 功能包括：
 * - 记录每次 trigger 执行的状态和结果
 * - 提供健康检查功能，确保系统正常运行
 * - 自动发送失败通知
 * - 提供测试功能确保 trigger 正常工作
 * - 监控系统运行状态和性能
 */

const TriggerMonitor = {
  
  // 配置
  config: {
    // 监控数据保存的 sheet 名称
    MONITOR_SHEET: 'TriggerMonitor',
    // 保留多少天的历史记录
    RETENTION_DAYS: 30,
    // 健康检查失败时是否发送邮件
    SEND_FAILURE_EMAIL: true,
    // 最多连续失败次数，超过则发送警告
    MAX_CONSECUTIVE_FAILURES: 3
  },
  
  /**
   * 初始化监控系统
   */
  init() {
    try {
      // 确保监控 sheet 存在
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      let sheet = ss.getSheetByName(this.config.MONITOR_SHEET);
      
      if (!sheet) {
        // 创建监控 sheet
        sheet = ss.insertSheet(this.config.MONITOR_SHEET);
        
        // 设置表头
        const headers = [
          'Timestamp',
          'Function',
          'Status',
          'Data Date',
          'Execution Time (ms)',
          'Email Sent',
          'Error Message',
          'Details'
        ];
        
        sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
        sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
        sheet.setFrozenRows(1);
        
        console.log('[TriggerMonitor] Monitor sheet created');
      }
      
      return true;
    } catch (error) {
      console.error('[TriggerMonitor] Init failed:', error);
      return false;
    }
  },
  
  /**
   * 记录 trigger 执行结果
   * @param {string} functionName - 执行的函数名
   * @param {string} status - 执行状态 (success/failed/warning)
   * @param {Object} details - 执行详情
   */
  logExecution(functionName, status, details = {}) {
    try {
      this.init();
      
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      const sheet = ss.getSheetByName(this.config.MONITOR_SHEET);
      
      if (!sheet) {
        console.error('[TriggerMonitor] Monitor sheet not found');
        return;
      }
      
      // 准备记录数据
      const row = [
        new Date(),                                    // Timestamp
        functionName,                                  // Function
        status,                                        // Status
        details.dataDate || '',                        // Data Date
        details.executionTime || 0,                    // Execution Time
        details.emailSent ? 'Yes' : 'No',             // Email Sent
        details.error || '',                           // Error Message
        JSON.stringify(details)                        // Details
      ];
      
      // 追加到 sheet
      sheet.appendRow(row);
      
      // 检查是否需要发送警告
      this._checkForAlerts(functionName, status);
      
      // 清理旧记录
      this._cleanupOldRecords();
      
    } catch (error) {
      console.error('[TriggerMonitor] Failed to log execution:', error);
    }
  },
  
  /**
   * 包装 trigger 函数，自动添加监控
   * @param {string} functionName - 函数名
   * @param {Function} fn - 原始函数
   * @returns {Function} 包装后的函数
   */
  wrapFunction(functionName, fn) {
    return async function(...args) {
      const startTime = new Date();
      let status = 'success';
      let result = null;
      const details = {};
      
      try {
        console.log(`[TriggerMonitor] Starting ${functionName}`);
        
        // 执行原函数
        result = await fn.apply(this, args);
        
        // 提取结果信息
        if (result) {
          details.dataDate = result.date;
          details.emailSent = result.emailSent || false;
          details.wasUpdated = result.wasUpdated || false;
        }
        
      } catch (error) {
        status = 'failed';
        details.error = error.message;
        details.stack = error.stack;
        
        console.error(`[TriggerMonitor] ${functionName} failed:`, error);
        
        // 重新抛出错误，让 GAS 的错误通知也能工作
        throw error;
        
      } finally {
        // 记录执行时间
        details.executionTime = new Date() - startTime;
        
        // 记录到监控系统
        TriggerMonitor.logExecution(functionName, status, details);
      }
      
      return result;
    };
  },
  
  /**
   * 获取最近的执行历史
   * @param {number} limit - 获取记录数
   * @returns {Array} 执行历史
   */
  getExecutionHistory(limit = 20) {
    try {
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      const sheet = ss.getSheetByName(this.config.MONITOR_SHEET);
      
      if (!sheet) {
        return [];
      }
      
      const lastRow = sheet.getLastRow();
      if (lastRow <= 1) {
        return [];
      }
      
      // 获取最近的记录
      const startRow = Math.max(2, lastRow - limit + 1);
      const numRows = lastRow - startRow + 1;
      
      const data = sheet.getRange(startRow, 1, numRows, 8).getValues();
      
      // 转换为对象数组
      return data.map(row => ({
        timestamp: row[0],
        functionName: row[1],
        status: row[2],
        dataDate: row[3],
        executionTime: row[4],
        emailSent: row[5],
        error: row[6],
        details: row[7] ? JSON.parse(row[7]) : {}
      })).reverse(); // 最新的在前
      
    } catch (error) {
      console.error('[TriggerMonitor] Failed to get history:', error);
      return [];
    }
  },
  
  /**
   * 运行健康检查
   * @returns {Object} 健康检查结果
   */
  healthCheck() {
    console.log('========== Trigger Health Check ==========');
    
    const results = {
      overall: 'healthy',
      checks: {},
      issues: [],
      recommendations: []
    };
    
    try {
      // 1. 检查最近执行情况
      const recentHistory = this.getExecutionHistory(10);
      results.checks.recentExecutions = recentHistory.length;
      
      if (recentHistory.length === 0) {
        results.issues.push('No recent executions found');
        results.recommendations.push('Run testTriggerExecution() to verify trigger works');
      } else {
        // 检查失败率
        const failures = recentHistory.filter(h => h.status === 'failed').length;
        const failureRate = failures / recentHistory.length;
        results.checks.failureRate = `${(failureRate * 100).toFixed(1)}%`;
        
        if (failureRate > 0.3) {
          results.overall = 'unhealthy';
          results.issues.push(`High failure rate: ${results.checks.failureRate}`);
        }
        
        // 检查最后执行时间
        const lastExecution = recentHistory[0];
        const hoursSinceLastRun = (new Date() - new Date(lastExecution.timestamp)) / (1000 * 60 * 60);
        results.checks.lastExecutionHoursAgo = hoursSinceLastRun.toFixed(1);
        
        if (hoursSinceLastRun > 25) {
          results.overall = 'warning';
          results.issues.push('No execution in the last 24 hours');
          results.recommendations.push('Check if trigger is properly configured');
        }
        
        // 检查连续失败
        let consecutiveFailures = 0;
        for (const exec of recentHistory) {
          if (exec.status === 'failed') {
            consecutiveFailures++;
          } else {
            break;
          }
        }
        results.checks.consecutiveFailures = consecutiveFailures;
        
        if (consecutiveFailures >= this.config.MAX_CONSECUTIVE_FAILURES) {
          results.overall = 'critical';
          results.issues.push(`${consecutiveFailures} consecutive failures`);
          results.recommendations.push('Immediate investigation required');
        }
      }
      
      // 2. 检查系统配置
      const configCheck = checkSystemConfiguration();
      results.checks.systemConfig = configCheck.issues.length === 0 ? 'OK' : 'Issues found';
      
      if (configCheck.issues.length > 0) {
        results.overall = results.overall === 'healthy' ? 'warning' : results.overall;
        results.issues.push(...configCheck.issues);
      }
      
      // 3. 检查数据可用性
      try {
        SheetAdapter.init();
        const recentData = SheetAdapter.readData(CONFIG.SHEET_NAME, { numRows: 1 });
        results.checks.dataAvailable = recentData.length > 0 ? 'Yes' : 'No';
        
        if (recentData.length === 0) {
          results.issues.push('No data available in MetaLog');
          results.recommendations.push('Add test data or wait for form submission');
        }
      } catch (error) {
        results.checks.dataAvailable = 'Error';
        results.issues.push('Cannot read data from MetaLog');
      }
      
      // 4. 检查 trigger 配置
      const triggers = ScriptApp.getProjectTriggers();
      const dailyTrigger = triggers.find(t => 
        t.getHandlerFunction() === 'runDailyReportGeneration'
      );
      
      results.checks.triggerConfigured = dailyTrigger ? 'Yes' : 'No';
      
      if (!dailyTrigger) {
        results.overall = 'critical';
        results.issues.push('Daily report trigger not found');
        results.recommendations.push('Set up trigger: Edit > Current project\'s triggers');
      }
      
      // 输出结果
      console.log('\nHealth Check Results:');
      console.log('Overall Status:', results.overall.toUpperCase());
      console.log('\nChecks:');
      Object.entries(results.checks).forEach(([check, value]) => {
        console.log(`  ${check}: ${value}`);
      });
      
      if (results.issues.length > 0) {
        console.log('\nIssues Found:');
        results.issues.forEach(issue => {
          console.log(`  ❌ ${issue}`);
        });
      }
      
      if (results.recommendations.length > 0) {
        console.log('\nRecommendations:');
        results.recommendations.forEach(rec => {
          console.log(`  💡 ${rec}`);
        });
      }
      
      // 如果状态不健康，发送警告邮件
      if (results.overall !== 'healthy' && this.config.SEND_FAILURE_EMAIL) {
        this._sendHealthAlert(results);
      }
      
      return results;
      
    } catch (error) {
      console.error('Health check failed:', error);
      results.overall = 'error';
      results.issues.push(`Health check error: ${error.message}`);
      return results;
    }
  },
  
  /**
   * 测试 trigger 执行（不等待真实时间）
   * @returns {Object} 测试结果
   */
  async testTriggerExecution() {
    console.log('========== Testing Trigger Execution ==========');
    
    const testResults = {
      tested: new Date(),
      results: {}
    };
    
    try {
      // 1. 测试使用最新数据生成报告
      console.log('\n1. Testing with latest data...');
      try {
        const result = await runDailyReportWithLatestData();
        testResults.results.latestData = {
          success: true,
          dataDate: result.date,
          emailSent: result.emailSent,
          executionTime: result.executionTime
        };
        console.log('✅ Latest data test passed');
      } catch (error) {
        testResults.results.latestData = {
          success: false,
          error: error.message
        };
        console.log('❌ Latest data test failed:', error.message);
      }
      
      // 2. 测试系统配置
      console.log('\n2. Testing system configuration...');
      const configTest = checkSystemConfiguration();
      testResults.results.configuration = {
        success: configTest.issues.length === 0,
        issues: configTest.issues
      };
      console.log(configTest.issues.length === 0 ? '✅ Configuration test passed' : '❌ Configuration has issues');
      
      // 3. 测试 API 连接
      console.log('\n3. Testing API connection...');
      try {
        const testPrompt = 'Test prompt: Please respond with "OK"';
        const apiResponse = await ApiService.callLLM(testPrompt);
        testResults.results.api = {
          success: true,
          response: apiResponse ? 'Connected' : 'No response'
        };
        console.log('✅ API test passed');
      } catch (error) {
        testResults.results.api = {
          success: false,
          error: error.message
        };
        console.log('❌ API test failed:', error.message);
      }
      
      // 4. 测试邮件发送（dry run）
      console.log('\n4. Testing email capability...');
      try {
        // 检查邮件配置
        const emailConfigured = CONFIG.RECIPIENT_EMAIL && CONFIG.ENABLE_DAILY_EMAIL;
        testResults.results.email = {
          success: emailConfigured,
          configured: emailConfigured,
          recipient: CONFIG.RECIPIENT_EMAIL ? 'Set' : 'Not set'
        };
        console.log(emailConfigured ? '✅ Email test passed' : '⚠️ Email not configured');
      } catch (error) {
        testResults.results.email = {
          success: false,
          error: error.message
        };
      }
      
      // 5. 性能测试
      console.log('\n5. Testing performance...');
      const perfStart = new Date();
      try {
        // 读取数据性能
        SheetAdapter.init();
        const data = SheetAdapter.readData(CONFIG.SHEET_NAME, { numRows: 10 });
        const readTime = new Date() - perfStart;
        
        testResults.results.performance = {
          success: true,
          dataReadTime: readTime,
          dataRows: data.length
        };
        console.log(`✅ Performance test passed (${readTime}ms for ${data.length} rows)`);
      } catch (error) {
        testResults.results.performance = {
          success: false,
          error: error.message
        };
      }
      
      // 总结
      const allPassed = Object.values(testResults.results).every(r => r.success);
      testResults.overall = allPassed ? 'passed' : 'failed';
      
      console.log('\n========== Test Summary ==========');
      console.log(`Overall: ${testResults.overall.toUpperCase()}`);
      Object.entries(testResults.results).forEach(([test, result]) => {
        console.log(`${test}: ${result.success ? '✅ Passed' : '❌ Failed'}`);
      });
      
      // 记录测试结果
      this.logExecution('testTriggerExecution', allPassed ? 'success' : 'failed', {
        testResults: testResults
      });
      
      return testResults;
      
    } catch (error) {
      console.error('Test execution failed:', error);
      testResults.overall = 'error';
      testResults.error = error.message;
      return testResults;
    }
  },
  
  /**
   * 设置监控 trigger
   * 每小时运行一次健康检查
   */
  setupMonitoringTrigger() {
    try {
      // 检查是否已存在
      const triggers = ScriptApp.getProjectTriggers();
      const existingTrigger = triggers.find(t => 
        t.getHandlerFunction() === 'runTriggerHealthCheck'
      );
      
      if (existingTrigger) {
        console.log('Monitoring trigger already exists');
        return false;
      }
      
      // 创建新的监控 trigger
      ScriptApp.newTrigger('runTriggerHealthCheck')
        .timeBased()
        .everyHours(1)
        .create();
      
      console.log('✅ Monitoring trigger created successfully');
      return true;
      
    } catch (error) {
      console.error('Failed to setup monitoring trigger:', error);
      return false;
    }
  },
  
  /**
   * 检查是否需要发送警告
   * @private
   */
  _checkForAlerts(functionName, status) {
    if (status !== 'failed') return;
    
    try {
      // 获取最近的执行历史
      const history = this.getExecutionHistory(this.config.MAX_CONSECUTIVE_FAILURES);
      
      // 检查连续失败次数
      let consecutiveFailures = 0;
      for (const exec of history) {
        if (exec.functionName === functionName && exec.status === 'failed') {
          consecutiveFailures++;
        } else {
          break;
        }
      }
      
      // 如果连续失败次数达到阈值，发送警告
      if (consecutiveFailures >= this.config.MAX_CONSECUTIVE_FAILURES) {
        this._sendFailureAlert(functionName, consecutiveFailures);
      }
      
    } catch (error) {
      console.error('[TriggerMonitor] Alert check failed:', error);
    }
  },
  
  /**
   * 发送失败警告邮件
   * @private
   */
  _sendFailureAlert(functionName, failureCount) {
    if (!this.config.SEND_FAILURE_EMAIL || !CONFIG.RECIPIENT_EMAIL) {
      return;
    }
    
    try {
      const subject = `⚠️ Trigger Alert: ${functionName} has failed ${failureCount} times`;
      const body = `
        <h2>Trigger Failure Alert</h2>
        <p>The function <strong>${functionName}</strong> has failed ${failureCount} consecutive times.</p>
        
        <h3>Recent Execution History:</h3>
        ${this._formatExecutionHistory()}
        
        <h3>Recommended Actions:</h3>
        <ol>
          <li>Check the execution transcript in Apps Script editor</li>
          <li>Run <code>TriggerMonitor.healthCheck()</code> for detailed diagnostics</li>
          <li>Run <code>debugDailyReportGeneration()</code> to debug the issue</li>
          <li>Check if there's new data in the MetaLog sheet</li>
        </ol>
        
        <p><small>This alert was sent by TriggerMonitor</small></p>
      `;
      
      MailApp.sendEmail({
        to: CONFIG.RECIPIENT_EMAIL,
        subject: subject,
        htmlBody: body
      });
      
      console.log('[TriggerMonitor] Failure alert sent');
      
    } catch (error) {
      console.error('[TriggerMonitor] Failed to send alert:', error);
    }
  },
  
  /**
   * 发送健康检查警告
   * @private
   */
  _sendHealthAlert(healthResults) {
    if (!CONFIG.RECIPIENT_EMAIL) return;
    
    try {
      const subject = `⚠️ Trigger Health Check: ${healthResults.overall.toUpperCase()}`;
      const body = `
        <h2>Trigger Health Check Alert</h2>
        <p>Overall Status: <strong>${healthResults.overall.toUpperCase()}</strong></p>
        
        <h3>Issues Found:</h3>
        <ul>
          ${healthResults.issues.map(issue => `<li>${issue}</li>`).join('')}
        </ul>
        
        <h3>Recommendations:</h3>
        <ul>
          ${healthResults.recommendations.map(rec => `<li>${rec}</li>`).join('')}
        </ul>
        
        <h3>Check Results:</h3>
        <pre>${JSON.stringify(healthResults.checks, null, 2)}</pre>
        
        <p><small>Run TriggerMonitor.testTriggerExecution() to test the system</small></p>
      `;
      
      MailApp.sendEmail({
        to: CONFIG.RECIPIENT_EMAIL,
        subject: subject,
        htmlBody: body
      });
      
    } catch (error) {
      console.error('[TriggerMonitor] Failed to send health alert:', error);
    }
  },
  
  /**
   * 格式化执行历史为 HTML
   * @private
   */
  _formatExecutionHistory() {
    const history = this.getExecutionHistory(5);
    
    if (history.length === 0) {
      return '<p>No execution history available</p>';
    }
    
    const rows = history.map(h => `
      <tr>
        <td>${Utilities.formatDate(new Date(h.timestamp), CONFIG.TIME_ZONE, "MM/dd HH:mm")}</td>
        <td>${h.status}</td>
        <td>${h.error || '-'}</td>
      </tr>
    `).join('');
    
    return `
      <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr>
          <th>Time</th>
          <th>Status</th>
          <th>Error</th>
        </tr>
        ${rows}
      </table>
    `;
  },
  
  /**
   * 清理旧记录
   * @private
   */
  _cleanupOldRecords() {
    try {
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      const sheet = ss.getSheetByName(this.config.MONITOR_SHEET);
      
      if (!sheet || sheet.getLastRow() <= 1) return;
      
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - this.config.RETENTION_DAYS);
      
      // 获取所有数据
      const data = sheet.getDataRange().getValues();
      
      // 找到需要保留的行
      let firstRowToKeep = 1; // 保留表头
      for (let i = 1; i < data.length; i++) {
        if (new Date(data[i][0]) > cutoffDate) {
          firstRowToKeep = i;
          break;
        }
      }
      
      // 删除旧数据
      if (firstRowToKeep > 1) {
        sheet.deleteRows(2, firstRowToKeep - 1);
        console.log(`[TriggerMonitor] Cleaned up ${firstRowToKeep - 1} old records`);
      }
      
    } catch (error) {
      console.error('[TriggerMonitor] Cleanup failed:', error);
    }
  }
};

// ========== 全局函数（供 trigger 和手动调用）==========

/**
 * 运行 trigger 健康检查
 * 这个函数可以被时间触发器调用
 */
function runTriggerHealthCheck() {
  return TriggerMonitor.healthCheck();
}

/**
 * 测试 trigger 系统
 */
function testTriggerSystem() {
  return TriggerMonitor.testTriggerExecution();
}

/**
 * 查看 trigger 执行历史
 */
function viewTriggerHistory(limit = 20) {
  const history = TriggerMonitor.getExecutionHistory(limit);
  
  console.log(`========== Last ${limit} Trigger Executions ==========`);
  
  if (history.length === 0) {
    console.log('No execution history found');
    return;
  }
  
  history.forEach((exec, index) => {
    console.log(`\n${index + 1}. ${exec.functionName}`);
    console.log(`   Time: ${Utilities.formatDate(new Date(exec.timestamp), CONFIG.TIME_ZONE, "yyyy/MM/dd HH:mm:ss")}`);
    console.log(`   Status: ${exec.status}`);
    console.log(`   Data Date: ${exec.dataDate || 'N/A'}`);
    console.log(`   Execution Time: ${exec.executionTime}ms`);
    console.log(`   Email Sent: ${exec.emailSent}`);
    if (exec.error) {
      console.log(`   Error: ${exec.error}`);
    }
  });
  
  // 计算统计信息
  const successCount = history.filter(h => h.status === 'success').length;
  const failureCount = history.filter(h => h.status === 'failed').length;
  const avgTime = history.reduce((sum, h) => sum + (h.executionTime || 0), 0) / history.length;
  
  console.log('\n========== Statistics ==========');
  console.log(`Total executions: ${history.length}`);
  console.log(`Success rate: ${((successCount / history.length) * 100).toFixed(1)}%`);
  console.log(`Failures: ${failureCount}`);
  console.log(`Average execution time: ${avgTime.toFixed(0)}ms`);
  
  return history;
}

/**
 * 设置监控系统
 */
function setupTriggerMonitoring() {
  console.log('========== Setting up Trigger Monitoring ==========');
  
  // 1. 初始化监控系统
  if (TriggerMonitor.init()) {
    console.log('✅ Monitor sheet initialized');
  }
  
  // 2. 设置监控 trigger
  if (TriggerMonitor.setupMonitoringTrigger()) {
    console.log('✅ Monitoring trigger created');
  }
  
  // 3. 运行初始健康检查
  console.log('\nRunning initial health check...');
  const health = TriggerMonitor.healthCheck();
  
  console.log('\n✅ Trigger monitoring setup complete!');
  console.log('Monitor sheet:', TriggerMonitor.config.MONITOR_SHEET);
  console.log('Health status:', health.overall);
  
  return true;
}

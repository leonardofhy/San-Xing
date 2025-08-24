/**
 * TimeFormatService.js - 时间格式统一处理服务
 * 专门处理 Google Sheets 中时间字段格式的统一和标准化
 * 
 * 功能包括：
 * - 将各种时间格式统一为 HHMM 格式（24小时制，4位数）
 * - 处理 Google Sheets 自动省略前导0的问题
 * - 支持 Date 对象、字符串等多种输入格式
 */

const TimeFormatService = {
  
  /**
   * 获取时间相关字段的内部名称
   * @returns {Array} 时间字段的内部名称数组
   */
  getTimeFieldNames() {
    return ['sleepStart', 'sleepEnd', 'sleepPlanned'];
  },

  /**
   * 标准化单个时间值为 HHMM 格式
   * @param {*} value - 原始时间值
   * @returns {string} 标准化后的 HHMM 格式
   */
  standardizeValue(value) {
    if (!value || value === '') {
      return '';
    }
    
    // 如果是 Date 对象，提取时间部分
    if (value instanceof Date) {
      const hours = value.getHours().toString().padStart(2, '0');
      const minutes = value.getMinutes().toString().padStart(2, '0');
      return hours + minutes;
    }
    
    // 如果是字符串，尝试解析各种格式
    if (typeof value === 'string') {
      const trimmed = value.trim();
      
      // 优先检查是否已经是 HHMM 格式（4位数）
      if (/^\d{4}$/.test(trimmed)) {
        const hours = parseInt(trimmed.substring(0, 2));
        const minutes = parseInt(trimmed.substring(2, 4));
        if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
          // 确保格式正确（补充前导0）
          return hours.toString().padStart(2, '0') + minutes.toString().padStart(2, '0');
        }
      }
      
      // 检查是否是 HMM 格式（3位数，如 "130" = 01:30）
      if (/^\d{3}$/.test(trimmed)) {
        const hours = parseInt(trimmed.substring(0, 1));
        const minutes = parseInt(trimmed.substring(1, 3));
        if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
          return hours.toString().padStart(2, '0') + minutes.toString().padStart(2, '0');
        }
      }
      
      // 检查是否是 HH 格式（2位数，只有小时）
      if (/^\d{2}$/.test(trimmed)) {
        const hours = parseInt(trimmed);
        if (hours >= 0 && hours <= 23) {
          return hours.toString().padStart(2, '0') + '00';
        }
      }
      
      // 检查是否是 H 格式（1位数，只有小时）
      if (/^\d{1}$/.test(trimmed)) {
        const hours = parseInt(trimmed);
        if (hours >= 0 && hours <= 23) {
          return hours.toString().padStart(2, '0') + '00';
        }
      }
      
      // 尝试解析 HH:MM 或 H:MM 格式
      const colonMatch = trimmed.match(/^(\d{1,2}):(\d{1,2})$/);
      if (colonMatch) {
        const hours = parseInt(colonMatch[1]);
        const minutes = parseInt(colonMatch[2]);
        if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
          return hours.toString().padStart(2, '0') + minutes.toString().padStart(2, '0');
        }
      }
      
      // 尝试解析带 AM/PM 的格式（如 "9:30 AM"）
      const ampmMatch = trimmed.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
      if (ampmMatch) {
        let hours = parseInt(ampmMatch[1]);
        const minutes = parseInt(ampmMatch[2]);
        const ampm = ampmMatch[3].toUpperCase();
        
        // 转换为24小时制
        if (ampm === 'PM' && hours !== 12) {
          hours += 12;
        } else if (ampm === 'AM' && hours === 12) {
          hours = 0;
        }
        
        if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
          return hours.toString().padStart(2, '0') + minutes.toString().padStart(2, '0');
        }
      }
      
      // 尝试解析其他可能的分隔符格式
      const anyTimeMatch = trimmed.match(/^(\d{1,2})[\.\-\s](\d{1,2})$/);
      if (anyTimeMatch) {
        const hours = parseInt(anyTimeMatch[1]);
        const minutes = parseInt(anyTimeMatch[2]);
        if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
          return hours.toString().padStart(2, '0') + minutes.toString().padStart(2, '0');
        }
      }
      
      console.warn(`[TimeFormatService] Unable to parse time value: "${value}"`);
      return value; // 返回原值如果无法解析
    }
    
    // 其他类型，尝试转换为字符串再处理
    return this.standardizeValue(value.toString());
  },

  /**
   * 获取时间字段的列索引
   * @param {Array} headers - 表头数组
   * @param {string} sheetName - 工作表名称
   * @returns {Object} 字段名到列索引的映射
   */
  getTimeColumnIndexes(headers, sheetName = CONFIG.SHEET_NAME) {
    const timeColumnIndexes = {};
    const timeFieldNames = this.getTimeFieldNames();
    const schema = SchemaService.getSchema(sheetName);
    
    // 遍历时间字段，找到对应的列索引
    timeFieldNames.forEach(fieldName => {
      const headerName = schema[fieldName];
      if (headerName) {
        const index = headers.indexOf(headerName);
        if (index !== -1) {
          timeColumnIndexes[fieldName] = index;
          console.log(`[TimeFormatService] Found ${fieldName} at column ${index + 1}: ${headerName}`);
        } else {
          console.warn(`[TimeFormatService] Time field not found in headers: ${headerName}`);
        }
      } else {
        console.warn(`[TimeFormatService] Field ${fieldName} not found in schema`);
      }
    });
    
    return timeColumnIndexes;
  },

  /**
   * 设置时间列为文本格式，保留前导0
   * @param {string} sheetName - 工作表名称
   * @returns {Object} 操作结果
   */
  setColumnsToTextFormat(sheetName = CONFIG.SHEET_NAME) {
    console.log('[TimeFormatService] Setting time columns to text format...');
    
    try {
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      const sheet = ss.getSheetByName(sheetName);
      
      if (!sheet) {
        throw new Error(`Sheet not found: ${sheetName}`);
      }
      
      const lastRow = sheet.getLastRow();
      const lastCol = sheet.getLastColumn();
      
      if (lastRow < 1) {
        console.log('[TimeFormatService] No data to format');
        return { columnsFormatted: 0 };
      }
      
      // 获取表头
      const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
      const timeColumnIndexes = this.getTimeColumnIndexes(headers, sheetName);
      
      if (Object.keys(timeColumnIndexes).length === 0) {
        console.log('[TimeFormatService] No time fields found to format');
        return { columnsFormatted: 0 };
      }
      
      // 设置每个时间列为文本格式
      let formattedColumns = 0;
      Object.entries(timeColumnIndexes).forEach(([fieldKey, colIndex]) => {
        // 包括表头的整列格式设置
        const columnRange = sheet.getRange(1, colIndex + 1, lastRow, 1);
        columnRange.setNumberFormat('@'); // @ 表示文本格式
        
        console.log(`[TimeFormatService] Set column ${colIndex + 1} (${fieldKey}) to text format`);
        formattedColumns++;
      });
      
      // 强制刷新以应用格式
      SpreadsheetApp.flush();
      
      console.log(`[TimeFormatService] ✅ Time columns formatting completed!`);
      console.log(`   - Columns formatted: ${formattedColumns}`);
      
      return {
        columnsFormatted: formattedColumns,
        affectedRows: lastRow,
        timeFields: Object.keys(timeColumnIndexes)
      };
      
    } catch (error) {
      console.error('[TimeFormatService] Time columns formatting failed:', error);
      throw error;
    }
  },

  /**
   * 标准化所有时间格式
   * @param {string} sheetName - 工作表名称
   * @returns {Object} 处理结果
   */
  standardizeAllFormats(sheetName = CONFIG.SHEET_NAME) {
    console.log('[TimeFormatService] Starting time format standardization...');
    
    try {
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      const sheet = ss.getSheetByName(sheetName);
      
      if (!sheet) {
        throw new Error(`Sheet not found: ${sheetName}`);
      }
      
      const lastRow = sheet.getLastRow();
      const lastCol = sheet.getLastColumn();
      
      if (lastRow < 2) {
        console.log('[TimeFormatService] No data to process');
        return { processedCount: 0, updatedRows: 0 };
      }
      
      // 获取表头
      const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
      const timeColumnIndexes = this.getTimeColumnIndexes(headers, sheetName);
      
      if (Object.keys(timeColumnIndexes).length === 0) {
        console.log('[TimeFormatService] No time fields found to process');
        return { processedCount: 0, updatedRows: 0 };
      }
      
      console.log(`[TimeFormatService] Found time fields:`, Object.keys(timeColumnIndexes));
      
      // 读取所有数据
      const dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol);
      const data = dataRange.getValues();
      
      let processedCount = 0;
      let updatedRows = [];
      
      console.log(`[TimeFormatService] Processing ${data.length} rows...`);
      
      // 处理每一行
      data.forEach((row, rowIndex) => {
        let rowUpdated = false;
        
        Object.entries(timeColumnIndexes).forEach(([fieldKey, colIndex]) => {
          const originalValue = row[colIndex];
          const standardizedValue = this.standardizeValue(originalValue);
          
          if (standardizedValue !== originalValue) {
            console.log(`[TimeFormatService] Row ${rowIndex + 2}, ${fieldKey}: "${originalValue}" → "${standardizedValue}"`);
            row[colIndex] = standardizedValue;
            rowUpdated = true;
            processedCount++;
          }
        });
        
        if (rowUpdated) {
          updatedRows.push(rowIndex + 2);
        }
      });
      
      // 写回更新的数据
      if (processedCount > 0) {
        console.log(`[TimeFormatService] Updating ${processedCount} time values in ${updatedRows.length} rows...`);
        
        // 先设置时间列为文本格式，防止前导0被省略
        Object.values(timeColumnIndexes).forEach(colIndex => {
          const columnRange = sheet.getRange(2, colIndex + 1, lastRow - 1, 1);
          columnRange.setNumberFormat('@'); // @ 表示文本格式
        });
        
        // 写入数据
        dataRange.setValues(data);
        
        console.log(`[TimeFormatService] ✅ Time format standardization completed!`);
        console.log(`   - Total values processed: ${processedCount}`);
        console.log(`   - Rows affected: ${updatedRows.length}`);
        console.log(`   - Time columns set to text format to preserve leading zeros`);
      } else {
        console.log('[TimeFormatService] ✅ No time values needed standardization');
      }
      
      return {
        processedCount: processedCount,
        updatedRows: updatedRows.length,
        affectedRowNumbers: updatedRows
      };
      
    } catch (error) {
      console.error('[TimeFormatService] Time format standardization failed:', error);
      throw error;
    }
  },

  /**
   * 强制刷新时间列的显示格式
   * @param {string} sheetName - 工作表名称
   * @returns {Object} 处理结果
   */
  refreshFormats(sheetName = CONFIG.SHEET_NAME) {
    console.log('[TimeFormatService] Refreshing time columns format...');
    
    try {
      // 先设置为文本格式
      const formatResult = this.setColumnsToTextFormat(sheetName);
      
      // 读取当前数据
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      const sheet = ss.getSheetByName(sheetName);
      const lastRow = sheet.getLastRow();
      const lastCol = sheet.getLastColumn();
      
      if (lastRow < 2) {
        console.log('[TimeFormatService] No data to refresh');
        return formatResult;
      }
      
      // 获取表头
      const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
      const timeColumnIndexes = this.getTimeColumnIndexes(headers, sheetName);
      
      // 读取所有数据并重新写入，强制应用文本格式
      const dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol);
      const data = dataRange.getValues();
      
      // 对时间列的数据添加前导0（如果需要）
      let refreshedCells = 0;
      data.forEach((row, rowIndex) => {
        Object.entries(timeColumnIndexes).forEach(([fieldKey, colIndex]) => {
          const currentValue = row[colIndex];
          if (currentValue && typeof currentValue === 'string') {
            // 确保时间格式有前导0
            if (/^\d{3,4}$/.test(currentValue.trim())) {
              const trimmed = currentValue.trim();
              let formattedValue = trimmed;
              
              if (trimmed.length === 3) {
                // 3位数变4位数
                formattedValue = '0' + trimmed;
              } else if (trimmed.length === 4) {
                // 确保有前导0
                formattedValue = trimmed.padStart(4, '0');
              }
              
              if (formattedValue !== currentValue) {
                row[colIndex] = formattedValue;
                refreshedCells++;
                console.log(`[TimeFormatService] Row ${rowIndex + 2}, ${fieldKey}: "${currentValue}" → "${formattedValue}"`);
              }
            }
          }
        });
      });
      
      if (refreshedCells > 0) {
        console.log(`[TimeFormatService] Updating ${refreshedCells} cells with corrected format...`);
        dataRange.setValues(data);
      }
      
      console.log(`[TimeFormatService] ✅ Time columns format refresh completed!`);
      console.log(`   - Cells refreshed: ${refreshedCells}`);
      
      return {
        ...formatResult,
        cellsRefreshed: refreshedCells
      };
      
    } catch (error) {
      console.error('[TimeFormatService] Time columns format refresh failed:', error);
      throw error;
    }
  },

  /**
   * 预览时间格式标准化（不实际修改数据）
   * @param {string} sheetName - 工作表名称
   * @param {number} previewRows - 预览行数
   * @returns {Object} 预览结果
   */
  previewStandardization(sheetName = CONFIG.SHEET_NAME, previewRows = 20) {
    console.log('[TimeFormatService] Previewing time format standardization...');
    
    try {
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      const sheet = ss.getSheetByName(sheetName);
      
      if (!sheet) {
        throw new Error(`Sheet not found: ${sheetName}`);
      }
      
      const lastRow = sheet.getLastRow();
      const lastCol = sheet.getLastColumn();
      
      if (lastRow < 2) {
        console.log('[TimeFormatService] No data to preview');
        return { previewedRows: 0, changesCount: 0 };
      }
      
      // 获取表头
      const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
      const timeColumnIndexes = this.getTimeColumnIndexes(headers, sheetName);
      
      if (Object.keys(timeColumnIndexes).length === 0) {
        console.log('[TimeFormatService] No time fields found');
        return { previewedRows: 0, changesCount: 0 };
      }
      
      // 读取数据（只预览指定行数）
      const actualPreviewRows = Math.min(previewRows, lastRow - 1);
      const dataRange = sheet.getRange(2, 1, actualPreviewRows, lastCol);
      const data = dataRange.getValues();
      
      console.log(`[TimeFormatService] Previewing first ${actualPreviewRows} rows:`);
      console.log('');
      
      let changesCount = 0;
      
      data.forEach((row, rowIndex) => {
        let hasChanges = false;
        const changes = [];
        
        Object.entries(timeColumnIndexes).forEach(([fieldKey, colIndex]) => {
          const originalValue = row[colIndex];
          const standardizedValue = this.standardizeValue(originalValue);
          
          if (standardizedValue !== originalValue) {
            changes.push(`${fieldKey}: "${originalValue}" → "${standardizedValue}"`);
            hasChanges = true;
            changesCount++;
          }
        });
        
        if (hasChanges) {
          console.log(`Row ${rowIndex + 2}:`);
          changes.forEach(change => console.log(`  ${change}`));
          console.log('');
        }
      });
      
      console.log(`[TimeFormatService] Summary:`);
      console.log(`  - Rows previewed: ${actualPreviewRows}`);
      console.log(`  - Values that would be changed: ${changesCount}`);
      console.log('');
      console.log('To apply these changes, run: TimeFormatService.standardizeAllFormats()');
      
      return {
        previewedRows: actualPreviewRows,
        changesCount: changesCount
      };
      
    } catch (error) {
      console.error('[TimeFormatService] Time format preview failed:', error);
      throw error;
    }
  },

  /**
   * 运行测试用例验证时间格式转换
   * @returns {Object} 测试结果
   */
  runTests() {
    console.log('[TimeFormatService] Running time format standardization tests...');
    
    // 测试用例：[输入, 期望输出, 描述]
    const testCases = [
      // 4位数格式
      ['0030', '0030', '4位数 - 凌晨'],
      ['0130', '0130', '4位数 - 凌晨'],
      ['0930', '0930', '4位数 - 上午'],
      ['2330', '2330', '4位数 - 晚上'],
      
      // 3位数格式
      ['030', '0030', '3位数 - 凌晨'],
      ['130', '0130', '3位数 - 凌晨'],
      ['930', '0930', '3位数 - 上午'],
      
      // 冒号格式
      ['00:30', '0030', 'HH:MM - 凌晨'],
      ['01:30', '0130', 'HH:MM - 凌晨'],
      ['9:30', '0930', 'H:MM - 上午'],
      ['23:45', '2345', 'HH:MM - 晚上'],
      ['7:00', '0700', 'H:MM - 早上'],
      ['0:30', '0030', 'H:MM - 凌晨'],
      
      // AM/PM 格式
      ['9:30 AM', '0930', 'AM 格式'],
      ['11:45 PM', '2345', 'PM 格式'],
      ['12:00 AM', '0000', '午夜'],
      ['12:00 PM', '1200', '正午'],
      
      // 其他分隔符
      ['9.30', '0930', '点号分隔'],
      ['9-30', '0930', '短横线分隔'],
      ['9 30', '0930', '空格分隔'],
      
      // 只有小时
      ['9', '0900', '单位数小时'],
      ['09', '0900', '双位数小时'],
      ['23', '2300', '晚上小时'],
      
      // 边界情况
      ['', '', '空字符串'],
      ['00:00', '0000', '午夜'],
      ['23:59', '2359', '23:59'],
      
      // Date 对象测试
      [new Date(2024, 0, 1, 9, 30), '0930', 'Date 对象 - 9:30'],
      [new Date(2024, 0, 1, 0, 30), '0030', 'Date 对象 - 0:30'],
      [new Date(2024, 0, 1, 23, 45), '2345', 'Date 对象 - 23:45'],
      
      // 无效格式（应该保持原样）
      ['invalid', 'invalid', '无效格式'],
      ['25:00', '25:00', '无效小时'],
      ['12:70', '12:70', '无效分钟']
    ];
    
    let passedTests = 0;
    let failedTests = 0;
    
    console.log('[TimeFormatService] Running tests...\n');
    
    testCases.forEach((testCase, index) => {
      const [input, expected, description] = testCase;
      const result = this.standardizeValue(input);
      const passed = result === expected;
      
      if (passed) {
        passedTests++;
        console.log(`✅ Test ${index + 1}: ${description}`);
        console.log(`   Input: ${typeof input === 'object' ? input.toString() : `"${input}"`} → Output: "${result}"`);
      } else {
        failedTests++;
        console.log(`❌ Test ${index + 1}: ${description}`);
        console.log(`   Input: ${typeof input === 'object' ? input.toString() : `"${input}"`}`);
        console.log(`   Expected: "${expected}", Got: "${result}"`);
      }
      console.log('');
    });
    
    console.log('[TimeFormatService] ========== Test Results ==========');
    console.log(`Total tests: ${testCases.length}`);
    console.log(`Passed: ${passedTests}`);
    console.log(`Failed: ${failedTests}`);
    console.log(`Success rate: ${((passedTests / testCases.length) * 100).toFixed(1)}%`);
    
    if (failedTests === 0) {
      console.log('🎉 All tests passed! Time format standardization is working correctly.');
    } else {
      console.log('⚠️ Some tests failed. Please review the failed cases above.');
    }
    
    return {
      total: testCases.length,
      passed: passedTests,
      failed: failedTests,
      successRate: (passedTests / testCases.length) * 100
    };
  }
};

// ------------------------------------------------------------------
// Convenience wrappers (moved from Main.js for easy manual triggering)
// ------------------------------------------------------------------

function standardizeTimeFormats() {
  return TimeFormatService.standardizeAllFormats();
}

function standardizeTimeValue(value) {
  return TimeFormatService.standardizeValue(value);
}

function testTimeFormatStandardization() {
  return TimeFormatService.runTests();
}

function setTimeColumnsToTextFormat() {
  return TimeFormatService.setColumnsToTextFormat();
}

function refreshTimeColumnsFormat() {
  return TimeFormatService.refreshFormats();
}

function previewTimeFormatStandardization() {
  return TimeFormatService.previewStandardization();
}

function testTimeFormatServiceIntegration() {
  console.log('========== Testing TimeFormatService Integration ==========');
  try {
    const fieldNames = TimeFormatService.getTimeFieldNames();
    console.log('Field names:', fieldNames);
    const schema = SchemaService.getSchema(CONFIG.SHEET_NAME);
    fieldNames.forEach(f => console.log(`${f} → ${schema[f]}`));
  } catch (e) {
    console.error('Integration test failed:', e);
    throw e;
  }
} 
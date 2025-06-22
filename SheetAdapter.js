/**
 * SheetAdapter - Unified interface for all sheet operations
 * Provides abstraction layer with caching and error handling
 */
const SheetAdapter = {
  spreadsheet: null,
  cache: {},
  cacheTimeout: 300000, // 5 minutes
  
  /**
   * Initialize the adapter with a spreadsheet
   */
  init() {
    if (!this.spreadsheet) {
      this.spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    }
    // Ensure schema versions for core sheets are up to date
    try {
      const sheetsToCheck = [CONFIG.SHEET_NAME, CONFIG.OUTPUT.DAILY_SHEET, CONFIG.OUTPUT.BEHAVIOR_SHEET];
      sheetsToCheck.forEach(name => {
        try {
          SchemaService.ensureVersion(name);
        } catch (e) {
          console.warn('[SheetAdapter] ensureVersion failed for', name, e.message);
        }
      });
    } catch (e) {
      console.warn('[SheetAdapter] schema ensureVersion skipped:', e.message);
    }
    return this;
  },
  
  /**
   * Get sheet by name with caching (auto-creates if not exist)
   * @param {string} sheetName - Name of the sheet
   * @returns {Sheet} Google Sheet object
   */
  getSheet(sheetName) {
    const cacheKey = `sheet_${sheetName}`;
    
    if (this._isCacheValid(cacheKey)) {
      return this.cache[cacheKey].data;
    }
    
    let sheet = this.spreadsheet.getSheetByName(sheetName);
    
    // Auto-create sheet if not exist and enabled in config
    if (!sheet && CONFIG.OUTPUT.AUTO_CREATE_SHEETS) {
      console.log(`[SheetAdapter] Sheet '${sheetName}' not found, creating new sheet...`);
      sheet = this.spreadsheet.insertSheet(sheetName);
      
      // Initialize with headers if schema exists
      try {
        const headers = SchemaService.getHeaders(sheetName);
        sheet.appendRow(headers);
        console.log(`[SheetAdapter] Created sheet '${sheetName}' with headers`);
      } catch (e) {
        console.log(`[SheetAdapter] Created sheet '${sheetName}' without headers (no schema defined)`);
      }
      
      EventBus.emit('SHEET_CREATED', { 
        sheetName: sheetName,
        withHeaders: !!headers 
      });
    } else if (!sheet) {
      throw new Error(`Sheet not found: ${sheetName}`);
    }
    
    this._setCache(cacheKey, sheet);
    return sheet;
  },
  
  /**
   * Read data from sheet with schema mapping
   * @param {string} sheetName - Name of the sheet
   * @param {Object} options - Read options
   * @returns {Array} Array of mapped objects
   */
  readData(sheetName, options = {}) {
    const sheet = this.getSheet(sheetName);
    const lastRow = sheet.getLastRow();
    
    if (lastRow < 1) {
      return [];
    }
    
    // Get headers
    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    
    // Check for schema changes
    const schemaChanges = SchemaService.detectSchemaChanges(sheetName, headers);
    if (schemaChanges.hasChanges) {
      console.warn(`[SheetAdapter] Schema mismatch detected for ${sheetName}:`, schemaChanges);
      EventBus.emit('SCHEMA_MISMATCH_DETECTED', {
        sheet: sheetName,
        changes: schemaChanges
      });
      
      // After detecting schemaChanges
      // Sync headers
      if (CONFIG.OUTPUT.AUTO_CREATE_SHEETS) {
        console.log(`[SheetAdapter] Syncing headers for ${sheetName}...`);
        const newHeaders = SchemaService.getHeaders(sheetName);
        sheet.getRange(1, 1, 1, newHeaders.length).setValues([newHeaders]);
        console.log(`[SheetAdapter] Headers synced for ${sheetName}`);
      }
    }
    
    // Read data rows
    const startRow = options.startRow || 2;
    const numRows = options.numRows || (lastRow - startRow + 1);
    
    if (numRows <= 0) {
      return [];
    }
    
    const dataRange = sheet.getRange(startRow, 1, numRows, headers.length);
    const dataValues = dataRange.getValues();
    
    // Map to objects using schema
    return dataValues.map(row => 
      SchemaService.mapRowToObject(sheetName, headers, row)
    );
  },
  
  /**
   * Write data to sheet with schema validation
   * @param {string} sheetName - Name of the sheet
   * @param {Array} data - Data to write
   * @param {Object} options - Write options
   */
  writeData(sheetName, data, options = {}) {
    const sheet = this.getSheet(sheetName);
    
    // Ensure headers exist
    if (sheet.getLastRow() === 0) {
      const headers = SchemaService.getHeaders(sheetName);
      sheet.appendRow(headers);
      console.log(`[SheetAdapter] Added headers to ${sheetName}`);
    }
    
    // Convert objects to row arrays based on schema
    const schema = SchemaService.getSchema(sheetName);
    const fieldNames = Object.keys(schema);
    
    const rows = data.map(obj => {
      return fieldNames.map(field => obj[field] || '');
    });
    
    // Write data
    if (options.append) {
      rows.forEach(row => sheet.appendRow(row));
    } else if (options.rowIndex) {
      const range = sheet.getRange(options.rowIndex, 1, rows.length, rows[0].length);
      range.setValues(rows);
    } else {
      // Default: append
      rows.forEach(row => sheet.appendRow(row));
    }
    
    // Clear cache for this sheet
    this._clearSheetCache(sheetName);
    
    EventBus.emit('SHEET_DATA_WRITTEN', {
      sheet: sheetName,
      rowCount: rows.length,
      operation: options.append ? 'append' : 'update'
    });
  },
  
  /**
   * Find row by date
   * @param {string} sheetName - Name of the sheet
   * @param {string} targetDate - Date to find (yyyy/MM/dd format)
   * @param {number} dateColumnIndex - Column index for date (1-based)
   * @returns {number|null} Row index or null if not found
   */
  findRowByDate(sheetName, targetDate, dateColumnIndex = 2) {
    const data = this.readData(sheetName);
    
    for (let i = data.length - 1; i >= 0; i--) {
      const rowData = data[i];
      let dateValue;
      
      // Handle different column specifications
      if (typeof dateColumnIndex === 'string') {
        dateValue = rowData[dateColumnIndex];
      } else {
        // Convert from 1-based to field name
        const headers = SchemaService.getHeaders(sheetName);
        const schema = SchemaService.getSchema(sheetName);
        const fieldName = Object.keys(schema)[dateColumnIndex - 1];
        dateValue = rowData[fieldName];
      }
      
      if (dateValue instanceof Date) {
        const rowDate = Utilities.formatDate(dateValue, CONFIG.TIME_ZONE, "yyyy/MM/dd");
        if (rowDate === targetDate) {
          return i + 2; // +2 because: +1 for 0-based to 1-based, +1 for header row
        }
      }
    }
    
    return null;
  },
  
  /**
   * Batch operations for performance
   * @param {Function} operations - Function containing multiple operations
   */
  batch(operations) {
    // Disable auto-calculation during batch
    const originalCalc = this.spreadsheet.getRecalculationInterval();
    this.spreadsheet.setRecalculationInterval(SpreadsheetApp.RecalculationInterval.HOUR);
    
    try {
      operations();
    } finally {
      // Restore original calculation
      this.spreadsheet.setRecalculationInterval(originalCalc);
      SpreadsheetApp.flush();
    }
  },
  
  // Cache management
  _isCacheValid(key) {
    const cached = this.cache[key];
    if (!cached) return false;
    return Date.now() - cached.timestamp < this.cacheTimeout;
  },
  
  _setCache(key, data) {
    this.cache[key] = {
      data: data,
      timestamp: Date.now()
    };
  },
  
  _clearSheetCache(sheetName) {
    Object.keys(this.cache).forEach(key => {
      if (key.includes(sheetName)) {
        delete this.cache[key];
      }
    });
  }
}; 
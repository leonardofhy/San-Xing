/**
 * ScoreCalculatorFactory - Plugin architecture for score calculations
 * Addresses Issue #006 - Dynamic score calculation adjustment
 */
const ScoreCalculatorFactory = {
  calculators: {
    behavior: {},
    sleep: {}
  },
  
  activeVersions: {
    behavior: 'v1',
    sleep: 'v1'
  },
  
  /**
   * Register a calculator version
   * @param {string} type - Type of calculator ('behavior' or 'sleep')
   * @param {string} version - Version identifier
   * @param {Object} calculator - Calculator implementation
   */
  registerCalculator(type, version, calculator) {
    if (!this.calculators[type]) {
      throw new Error(`Unknown calculator type: ${type}`);
    }
    
    // Validate calculator interface
    const requiredMethods = ['calculate', 'getMetadata'];
    requiredMethods.forEach(method => {
      if (typeof calculator[method] !== 'function') {
        throw new Error(`Calculator must implement ${method} method`);
      }
    });
    
    this.calculators[type][version] = calculator;
    console.log(`[ScoreCalculatorFactory] Registered ${type} calculator version ${version}`);
  },
  
  /**
   * Get active calculator for a type
   * @param {string} type - Type of calculator
   * @returns {Object} Active calculator instance
   */
  getCalculator(type) {
    const version = this.activeVersions[type];
    const calculator = this.calculators[type][version];
    
    if (!calculator) {
      throw new Error(`No calculator found for ${type} version ${version}`);
    }
    
    return calculator;
  },
  
  /**
   * Get specific version of calculator
   * @param {string} type - Type of calculator
   * @param {string} version - Version identifier
   * @returns {Object} Calculator instance
   */
  getCalculatorVersion(type, version) {
    const calculator = this.calculators[type][version];
    
    if (!calculator) {
      throw new Error(`No calculator found for ${type} version ${version}`);
    }
    
    return calculator;
  },
  
  /**
   * Set active calculator version
   * @param {string} type - Type of calculator
   * @param {string} version - Version to activate
   */
  setActiveVersion(type, version) {
    if (!this.calculators[type][version]) {
      throw new Error(`Calculator version ${version} not found for type ${type}`);
    }
    
    const oldVersion = this.activeVersions[type];
    this.activeVersions[type] = version;
    
    console.log(`[ScoreCalculatorFactory] Changed ${type} calculator from ${oldVersion} to ${version}`);
    
    // Emit event for version change
    if (typeof EventBus !== 'undefined') {
      EventBus.emit('CALCULATOR_VERSION_CHANGED', {
        type: type,
        oldVersion: oldVersion,
        newVersion: version
      });
    }
  },
  
  /**
   * Calculate score using active calculator
   * @param {string} type - Type of calculator
   * @param {*} data - Data to calculate score for
   * @returns {Object} Calculated score result
   */
  calculate(type, data) {
    const calculator = this.getCalculator(type);
    return calculator.calculate(data);
  },
  
  /**
   * Recalculate historical data with specific version
   * @param {string} type - Type of calculator
   * @param {string} version - Version to use for recalculation
   * @param {Array} historicalData - Array of historical data entries
   * @returns {Array} Recalculated results
   */
  recalculateHistorical(type, version, historicalData) {
    const calculator = this.getCalculatorVersion(type, version);
    
    return historicalData.map(entry => {
      try {
        const score = calculator.calculate(entry.data);
        return {
          date: entry.date,
          originalScore: entry.score,
          recalculatedScore: score,
          version: version,
          success: true
        };
      } catch (error) {
        return {
          date: entry.date,
          originalScore: entry.score,
          error: error.message,
          version: version,
          success: false
        };
      }
    });
  }
};

// Register default calculators
ScoreCalculatorFactory.registerCalculator('behavior', 'v1', {
  calculate(behaviors) {
    // Use existing BehaviorScoreService logic
    if (typeof BehaviorScoreService !== 'undefined') {
      return BehaviorScoreService.getUpToDateDailyScore(behaviors);
    }
    // Fallback implementation
    return { total: 0, details: {} };
  },
  
  getMetadata() {
    return {
      version: 'v1',
      description: 'Original behavior scoring algorithm',
      lastUpdated: '2024-03-01'
    };
  }
});

ScoreCalculatorFactory.registerCalculator('sleep', 'v1', {
  calculate(sleepData) {
    // Use existing SleepQualityService logic
    if (typeof SleepQualityService !== 'undefined') {
      return SleepQualityService.calculateSleepHealthIndex(sleepData);
    }
    // Fallback implementation
    return { total: 0, details: {} };
  },
  
  getMetadata() {
    return {
      version: 'v1',
      description: 'Original sleep quality scoring',
      lastUpdated: '2024-03-01'
    };
  }
}); 
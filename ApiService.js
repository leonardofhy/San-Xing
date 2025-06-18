/**
 * ApiService - Unified API interface with adapter pattern
 * Supports multiple LLM providers and future local deployment
 */
const ApiService = {
  providers: {
    deepseek: {
      url: "https://api.deepseek.com/chat/completions",
      
      buildPayload(prompt, options = {}) {
        return {
          model: options.model || CONFIG.DAILY_MODEL,
          messages: [
            { 
              role: "system", 
              content: options.systemMessage || PromptBuilderService.getSystemMessage() 
            },
            { role: "user", content: prompt }
          ],
          response_format: { type: "json_object" },
          stream: false,
          temperature: options.temperature || 0.7
        };
      },
      
      buildHeaders() {
        return {
          "Authorization": "Bearer " + CONFIG.DEEPSEEK_API_KEY,
          "Content-Type": "application/json"
        };
      },
      
      parseResponse(response) {
        const data = JSON.parse(response);
        const content = data.choices[0].message.content;
        return JSON.parse(content);
      }
    },
    
    // Future provider for local LLM
    local: {
      url: "http://localhost:11434/api/generate",
      
      buildPayload(prompt, options = {}) {
        return {
          model: options.model || "llama2",
          prompt: prompt,
          format: "json",
          stream: false
        };
      },
      
      buildHeaders() {
        return {
          "Content-Type": "application/json"
        };
      },
      
      parseResponse(response) {
        const data = JSON.parse(response);
        return JSON.parse(data.response);
      }
    }
  },
  
  activeProvider: 'deepseek',
  retryConfig: {
    maxAttempts: 3,
    delayMs: 2000,
    backoffMultiplier: 1.5
  },
  
  /**
   * Call LLM with automatic retry and error handling
   * @param {string} prompt - The prompt to send
   * @param {Object} options - Call options
   * @returns {Promise<Object>} Parsed response
   */
  async callLLM(prompt, options = {}) {
    const provider = this.providers[options.provider || this.activeProvider];
    if (!provider) {
      throw new Error(`Unknown API provider: ${options.provider || this.activeProvider}`);
    }
    
    let lastError;
    let delay = this.retryConfig.delayMs;
    
    for (let attempt = 1; attempt <= this.retryConfig.maxAttempts; attempt++) {
      try {
        console.log(`[ApiService] Calling ${this.activeProvider} API (attempt ${attempt}/${this.retryConfig.maxAttempts})`);
        
        const payload = provider.buildPayload(prompt, options);
        const headers = provider.buildHeaders();
        
        const response = await this._makeRequest(provider.url, {
          method: "post",
          headers: headers,
          payload: JSON.stringify(payload),
          muteHttpExceptions: true
        });
        
        if (response.getResponseCode() === 200) {
          const responseText = response.getContentText();
          const result = provider.parseResponse(responseText);
          
          console.log('[ApiService] API call successful');
          EventBus.emit('API_CALL_SUCCESS', {
            provider: this.activeProvider,
            attempt: attempt,
            promptLength: prompt.length
          });
          
          return result;
        } else {
          const error = new Error(`API returned status ${response.getResponseCode()}: ${response.getContentText()}`);
          error.statusCode = response.getResponseCode();
          throw error;
        }
        
      } catch (error) {
        lastError = error;
        console.error(`[ApiService] API call failed on attempt ${attempt}:`, error.message);
        
        EventBus.emit('API_CALL_FAILED', {
          provider: this.activeProvider,
          attempt: attempt,
          error: error.message,
          statusCode: error.statusCode
        });
        
        // Retry only for server errors or network issues
        if (attempt < this.retryConfig.maxAttempts && 
            (!error.statusCode || error.statusCode >= 500)) {
          console.log(`[ApiService] Retrying in ${delay}ms...`);
          Utilities.sleep(delay);
          delay *= this.retryConfig.backoffMultiplier;
        }
      }
    }
    
    // All attempts failed
    throw new Error(`API call failed after ${this.retryConfig.maxAttempts} attempts: ${lastError.message}`);
  },
  
  /**
   * Make HTTP request (wrapped for testing)
   * @private
   */
  _makeRequest(url, options) {
    return UrlFetchApp.fetch(url, options);
  },
  
  /**
   * Set active provider
   * @param {string} providerName - Name of the provider
   */
  setProvider(providerName) {
    if (!this.providers[providerName]) {
      throw new Error(`Unknown provider: ${providerName}`);
    }
    
    const oldProvider = this.activeProvider;
    this.activeProvider = providerName;
    
    console.log(`[ApiService] Switched from ${oldProvider} to ${providerName}`);
    EventBus.emit('API_PROVIDER_CHANGED', {
      oldProvider: oldProvider,
      newProvider: providerName
    });
  },
  
  /**
   * Register a new provider
   * @param {string} name - Provider name
   * @param {Object} implementation - Provider implementation
   */
  registerProvider(name, implementation) {
    // Validate required methods
    const required = ['buildPayload', 'buildHeaders', 'parseResponse'];
    required.forEach(method => {
      if (typeof implementation[method] !== 'function') {
        throw new Error(`Provider must implement ${method} method`);
      }
    });
    
    this.providers[name] = implementation;
    console.log(`[ApiService] Registered provider: ${name}`);
  },
  
  /**
   * Test connection to current provider
   * @returns {Promise<boolean>} Connection test result
   */
  async testConnection() {
    try {
      const result = await this.callLLM("Test connection. Respond with: {\"status\": \"ok\"}", {
        temperature: 0
      });
      return result.status === 'ok';
    } catch (error) {
      console.error('[ApiService] Connection test failed:', error);
      return false;
    }
  }
}; 
/**
 * EventBus Service - Central event management for loose coupling
 * Enables event-driven architecture across all services
 */
const EventBus = {
  listeners: {},
  eventHistory: [],
  
  /**
   * Subscribe to an event
   * @param {string} eventName - Name of the event
   * @param {Function} callback - Function to call when event is emitted
   * @param {Object} context - Context to bind to callback
   */
  on(eventName, callback, context = null) {
    if (!this.listeners[eventName]) {
      this.listeners[eventName] = [];
    }
    this.listeners[eventName].push({ callback, context });
    console.log(`[EventBus] Registered listener for: ${eventName}`);
  },
  
  /**
   * Emit an event with data
   * @param {string} eventName - Name of the event
   * @param {*} data - Data to pass to listeners
   */
  emit(eventName, data = null) {
    console.log(`[EventBus] Emitting event: ${eventName}`, data);
    
    // Record event for audit trail
    this.eventHistory.push({
      timestamp: new Date(),
      event: eventName,
      data: data
    });
    
    if (!this.listeners[eventName]) return;
    
    this.listeners[eventName].forEach(listener => {
      try {
        if (listener.context) {
          listener.callback.call(listener.context, data);
        } else {
          listener.callback(data);
        }
      } catch (error) {
        console.error(`[EventBus] Error in listener for ${eventName}:`, error);
        this.emit('ERROR_OCCURRED', { 
          originalEvent: eventName, 
          error: error.message,
          stack: error.stack 
        });
      }
    });
  },
  
  /**
   * Remove a listener
   */
  off(eventName, callback) {
    if (!this.listeners[eventName]) return;
    this.listeners[eventName] = this.listeners[eventName].filter(
      listener => listener.callback !== callback
    );
  },
  
  /**
   * Get event history for debugging/audit
   */
  getEventHistory(limit = 50) {
    return this.eventHistory.slice(-limit);
  }
}; 
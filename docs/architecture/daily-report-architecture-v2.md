# Daily Report Architecture v2.0 - Enhanced Microservices Design

**Version**: 2.0
**Last Updated**: 2025-06-17

## 1. Overview

This document describes the enhanced microservices architecture for the Meta-Awareness Daily Report system. The new design addresses all issues identified in the original monolithic architecture while providing a flexible, maintainable, and extensible foundation for future enhancements.

## 2. Architecture Highlights

### Event-Driven Architecture
- **EventBus** enables loose coupling between services
- Services communicate through events, not direct calls
- Easy to add new features without modifying existing code
- Complete audit trail of all operations

### Plugin Architecture
- **ScoreCalculatorFactory** manages versioned calculators
- Easy to add new scoring algorithms
- Historical data can be recalculated with specific versions
- Addresses Issue #006 completely

### Dynamic Schema Management
- **SchemaService** provides centralized header configuration
- Automatic detection of schema changes
- Version control for schema evolution
- Addresses Issues #002, #004, #005

### Unified Data Access
- **SheetAdapter** provides consistent interface for all sheet operations
- Built-in caching for performance
- Batch operation support
- Schema-aware data mapping

## 3. Service Catalog

### Core Infrastructure Services

#### EventBus.js
- **Purpose**: Central event management system
- **Key Features**:
  - Publish/subscribe pattern
  - Error propagation
  - Event history for debugging
  - Asynchronous event handling

#### SchemaService.js
- **Purpose**: Dynamic schema management
- **Key Features**:
  - Version control for schemas
  - Header mapping and validation
  - Schema change detection
  - Migration support

#### SheetAdapter.js
- **Purpose**: Unified sheet operations
- **Key Features**:
  - Read/write operations with schema mapping
  - Caching layer
  - Batch operations
  - Date-based queries

### Business Logic Services

#### ScoreCalculatorFactory.js
- **Purpose**: Plugin-based score calculation
- **Key Features**:
  - Multiple calculator versions
  - Hot-swappable calculators
  - Historical recalculation
  - Extensible design

#### PromptBuilderService.js
- **Purpose**: Template-based prompt generation
- **Key Features**:
  - Versioned prompt templates
  - Placeholder replacement
  - Multi-language support ready
  - Easy customization

### Integration Services

#### ApiService.js
- **Purpose**: LLM provider abstraction
- **Key Features**:
  - Multiple provider support (DeepSeek, Local LLM)
  - Automatic retry with backoff
  - Provider hot-swapping
  - Connection testing

#### EmailService.js
- **Purpose**: Email generation and sending
- **Key Features**:
  - Template-based HTML generation
  - Gmail label management
  - Retry logic
  - CSS styling support

### Orchestration Layer

#### ReportOrchestrator.js
- **Purpose**: Coordinate all services
- **Key Features**:
  - Event-driven workflow
  - Error handling and recovery
  - Batch processing
  - Progress tracking

#### Main.js
- **Purpose**: Public API and entry points
- **Key Features**:
  - Backward compatibility
  - Testing utilities
  - Schema migration tools
  - System maintenance functions

## 4. Event Flow

### Daily Report Generation Flow

```
1. Trigger → Main.runDailyReportGeneration()
2. Main → ReportOrchestrator.generateDailyReport()
3. ReportOrchestrator → EventBus.emit('REPORT_GENERATION_STARTED')
4. EventBus → Multiple services listen and process in sequence:
   - SheetAdapter reads data → emit('DATA_READ_COMPLETED')
   - ScoreCalculatorFactory calculates → emit('SCORES_CALCULATED')
   - PromptBuilderService builds prompt → emit('PROMPT_READY')
   - ApiService calls LLM → emit('ANALYSIS_COMPLETED')
   - SheetAdapter saves report → emit('REPORT_SAVED')
   - EmailService sends email → emit('REPORT_GENERATION_COMPLETED')
```

### Error Handling Flow

```
1. Any service encounters error
2. Service → EventBus.emit('ERROR_OCCURRED', errorDetails)
3. Service → EventBus.emit('REPORT_GENERATION_FAILED', context)
4. ReportOrchestrator catches and logs
5. Main.js re-throws for Apps Script notification
```

## 5. Key Benefits

### Modularity (Addresses Issue #001)
- Each service has a single responsibility
- Easy to understand and modify
- Clear boundaries between components
- Testable in isolation

### Flexibility (Addresses Issues #002, #004, #005)
- Schema changes are automatically detected
- Headers can be versioned and migrated
- New fields can be added without breaking existing code
- Centralized configuration management

### Extensibility (Addresses Issue #006)
- New score calculators can be added as plugins
- Historical data can be recalculated
- Multiple LLM providers supported
- Easy to add new report types

### Maintainability
- Event-driven architecture reduces coupling
- Comprehensive logging and debugging tools
- Error recovery mechanisms
- Performance optimization built-in

## 6. Migration Path

### From v1 to v2

1. **Keep existing files**: Don't delete the old DailyReport.js immediately
2. **Deploy new services**: Add all new service files to the project
3. **Update entry points**: The functions in Main.js maintain backward compatibility
4. **Test thoroughly**: Use `testMicroservicesArchitecture()` to verify setup
5. **Monitor**: Use `viewEventHistory()` to debug any issues
6. **Gradual cutover**: Update triggers to use new entry points

### Rollback Strategy

If issues arise, the original DailyReport.js remains intact and can be used by updating the trigger functions.

## 7. Future Enhancements

### Planned Features
- Weekly report generation using same architecture
- Real-time dashboard with event streaming
- Multi-user support with tenant isolation
- Advanced analytics with trend detection
- Mobile app integration

### Architecture Ready For
- Local LLM deployment (privacy enhancement)
- Multiple data sources beyond Google Sheets
- Webhook integrations
- REST API exposure
- Automated testing framework

## 8. Performance Considerations

### Caching Strategy
- SheetAdapter caches sheet references (5-minute TTL)
- Schema mappings are cached in memory
- API responses could be cached for retry scenarios

### Batch Processing
- Sequential processing to avoid rate limits
- Progress tracking for long-running operations
- Graceful failure handling

### Resource Optimization
- Lazy initialization of services
- Event-driven prevents unnecessary processing
- Batch sheet operations when possible

## 9. Security Considerations

### API Keys
- Stored in Config.js (should use PropertiesService in production)
- Never logged or exposed in events
- Provider abstraction hides implementation details

### Data Privacy
- Ready for local LLM deployment
- Minimal data exposure to external services
- Event history can be cleared regularly

## 10. Debugging and Monitoring

### Built-in Tools
- `testMicroservicesArchitecture()` - Verify all services
- `viewEventHistory()` - See event flow
- `detectSchemaChanges()` - Check for header mismatches
- `systemCleanup()` - Optimize and clean data

### Logging Strategy
- Each service prefixes logs with `[ServiceName]`
- Events provide audit trail
- Errors include context and stack traces
- Performance metrics in event data 
# Software Requirements Specification (SRS)
## San-Xing Visualization Dashboard

**Document Version:** 2.0  
**Date:** August 27, 2025  
**Project:** San-Xing (三省) - Personal Analytics Visualization System  

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for the San-Xing Visualization Dashboard, an interactive web-based interface for analyzing personal diary data, health metrics, and behavioral patterns. The dashboard provides real-time visualization and analytics for the San-Xing meta-awareness coaching system.

### 1.2 Scope
The visualization system encompasses:
- **Bulletproof Interactive Dashboard** built with Streamlit with robust data loading fallbacks
- **Multi-format Data Integration** supporting JSON snapshots, Google Sheets, and synthetic data
- **Comprehensive KPI Analytics** including wellbeing scoring, balance indices, and trend analysis
- **Advanced Sleep Quality Analysis** with both objective and subjective metrics
- **Interactive Raw Data Explorer** with date filtering and CSV export capabilities
- **Statistical Significance Testing** with correlation analysis and confidence intervals
- **Modular Component Architecture** with reusable UI components and analytics modules

### 1.3 Definitions and Acronyms
- **San-Xing (三省)**: "Three daily examinations" - Confucian self-reflection practice
- **Dashboard**: Bulletproof interactive web interface for data visualization
- **DataProcessor**: Enhanced backend module processing multiple time formats and Chinese field mapping
- **RobustDataLoader**: Fallback system ensuring dashboard always functions with real or synthetic data
- **KPICalculator**: Advanced analytics engine computing wellbeing scores and trend indicators
- **SleepQualityCalculator**: Specialized module for objective sleep analysis using timing patterns
- **Streamlit**: Python web application framework
- **Plotly**: Interactive charting library for dashboard visualizations

### 1.4 References
- San-Xing Main SRS: `docs/SRS_SanXing.md`
- Architecture Documentation: `docs/architecture-v2-quick-reference.md`
- Data Processing Documentation: `src/data_processor.py`

---

## 2. Overall Description

### 2.1 Product Perspective
The visualization dashboard is a component of the larger San-Xing ecosystem:
```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Google Sheets     │    │   Python CLI         │    │  Visualization      │
│   (Data Collection) │───▶│   (Data Processing)  │───▶│  Dashboard          │
│                     │    │                      │    │  (Analysis & UI)    │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

### 2.2 Product Functions
Primary functions include:
- **Data Visualization**: Multi-panel health metrics dashboard
- **Activity Analysis**: Pattern recognition and trend analysis
- **Sleep Tracking**: Duration trends and quality correlations
- **Interactive Filtering**: Date ranges and data source selection
- **Real-time Updates**: Automatic data refresh capabilities
- **Cross-platform Access**: Web-based interface accessible via URL

### 2.3 User Characteristics
**Primary Users:**
- Individual practitioners of self-reflection and personal analytics
- Health-conscious individuals tracking behavioral patterns
- Researchers analyzing personal development metrics

**Technical Proficiency:** Basic to intermediate computer users comfortable with web interfaces

### 2.4 Constraints
- **Platform**: Web-based (requires modern web browser)
- **Dependencies**: Python 3.11+, Streamlit, Plotly, Pandas
- **Data Sources**: Limited to JSON files and Google Sheets
- **Performance**: Single-user concurrent access design
- **Security**: Local deployment or trusted network environment

---

## 3. System Features

### 3.1 Bulletproof Data Integration System

#### 3.1.1 Description
Robust multi-source data integration with intelligent fallbacks ensuring dashboard always functions.

#### 3.1.2 Functional Requirements
- **REQ-3.1.1**: System SHALL load data from processed snapshots via enhanced DataProcessor
- **REQ-3.1.2**: System SHALL connect to Google Sheets with proper Chinese field mapping
- **REQ-3.1.3**: System SHALL handle multiple time formats (HH:MM:SS and HHMM) automatically
- **REQ-3.1.4**: System SHALL provide intelligent fallback hierarchy: Real Data → Synthetic Data → Emergency Data
- **REQ-3.1.5**: System SHALL map Chinese column names to English field names seamlessly
- **REQ-3.1.6**: System SHALL validate sleep timing data with realistic duration checks (2-16 hours)
- **REQ-3.1.7**: System SHALL handle cross-midnight sleep calculations correctly
- **REQ-3.1.8**: System SHALL never crash - always display functional dashboard with clear data source indicators

#### 3.1.3 Input Specifications
**Enhanced Data Processing Formats:**
```json
{
  "Timestamp": "DD/MM/YYYY HH:MM:SS",
  "今日整體心情感受": "1-10 numeric scale",
  "今日整體精力水平如何？": "1-10 numeric scale", 
  "昨晚睡眠品質如何？": "1-10 numeric scale",
  "昨晚實際入睡時間": "HH:MM:SS or HHMM format",
  "今天實際起床時間": "HH:MM:SS or HHMM format",
  "今天完成了哪些？": "Comma-separated activity list",
  "體重紀錄": "Numeric weight in kg",
  "今日手機螢幕使用時間": "Numeric hours"
}
```

**Time Format Support:**
- **HH:MM:SS Format**: "04:40:00", "23:07:00" (standard format)
- **HHMM Format**: "0420", "2307" (compact format from Google Sheets)
- **Validation**: Automatic validation of hours (0-23) and minutes (0-59)

**Chinese Column Mapping:**
- `昨晚實際入睡時間` → `sleep_bedtime`
- `今天實際起床時間` → `wake_time`
- `昨晚睡眠品質如何？` → `sleep_quality`

### 3.2 Enhanced Key Performance Indicators (KPIs) Dashboard

#### 3.2.1 Description
Comprehensive KPI system displaying four primary wellness indicators with detailed explanations and actionable insights.

#### 3.2.2 Functional Requirements
- **REQ-3.2.1**: System SHALL display 4 primary KPI cards (Wellbeing Score, Balance Index, Trend Indicator, Sleep Quality)
- **REQ-3.2.2**: System SHALL calculate composite Wellbeing Score from mood and energy levels with data quality indicators
- **REQ-3.2.3**: System SHALL compute Balance Index from activity balance and life balance metrics  
- **REQ-3.2.4**: System SHALL determine trend direction using statistical significance testing
- **REQ-3.2.5**: System SHALL provide both objective and subjective sleep quality analysis
- **REQ-3.2.6**: System SHALL include expandable explanations for each KPI with "ℹ️ What is..." sections
- **REQ-3.2.7**: System SHALL handle missing data gracefully with appropriate fallback messages
- **REQ-3.2.8**: System SHALL display confidence levels and sample sizes for statistical metrics

#### 3.2.3 KPI Definitions
1. **Wellbeing Score (0-10)**: Combines mood and energy levels with weighted average calculation
2. **Balance Index (0-100%)**: Measures life balance between activities, sleep, and overall wellness
3. **Trend Indicator**: Statistical trend analysis showing improving/stable/declining patterns with confidence
4. **Sleep Quality (1-5)**: Dual analysis combining subjective ratings and objective timing-based calculations

#### 3.2.4 Sleep Quality Analysis Components
- **Subjective Analysis**: User-reported sleep quality ratings
- **Objective Analysis**: Calculated from sleep timing patterns with 4 components:
  - Duration Score (40%): Optimal 7-9 hours range
  - Timing Score (30%): Circadian rhythm alignment
  - Regularity Score (20%): Sleep schedule consistency  
  - Efficiency Score (10%): Weekend vs weekday patterns

### 3.3 Activity Impact Analysis

#### 3.3.1 Description
Focused activity analysis showing statistical relationships between activities and wellbeing outcomes.

#### 3.3.2 Functional Requirements
- **REQ-3.3.1**: System SHALL categorize activities into positive, neutral, and negative types
- **REQ-3.3.2**: System SHALL calculate activity balance score (positive - negative)
- **REQ-3.3.3**: System SHALL identify top 3 activities with strongest correlation to next-day mood/energy
- **REQ-3.3.4**: System SHALL display only statistically significant activity-outcome relationships
- **REQ-3.3.5**: System SHALL show activity impact summary with confidence levels
- **REQ-3.3.6**: System SHALL handle both string and list activity data formats

#### 3.3.3 Activity Categories
**Positive Activities:**
- 英文學習, 閱讀論文, 看書, 戶外活動, 實體社交活動
- 看知識型視頻, 看英文視頻, 額外完成任務 (1-3+)

**Neutral Activities:**
- 做家務, 頭髮護理, 面部護理, 久坐

**Negative Activities:**
- 打遊戲, 滑手機, 看娛樂視頻

### 3.4 Sleep Analysis System

#### 3.4.1 Description
Sleep pattern tracking with duration analysis and quality correlation.

#### 3.4.2 Functional Requirements
- **REQ-3.4.1**: System SHALL calculate sleep duration from bedtime and wake time
- **REQ-3.4.2**: System SHALL display sleep duration trends with recommended guidelines
- **REQ-3.4.3**: System SHALL show sleep quality vs duration correlation
- **REQ-3.4.4**: System SHALL handle overnight sleep calculations (cross-midnight)
- **REQ-3.4.5**: System SHALL provide sleep quality indicators sized by energy levels

#### 3.4.3 Sleep Metrics
- **Duration Calculation**: Handle 18:00+ bedtimes as previous day
- **Quality Scale**: 1-10 subjective sleep quality rating
- **Recommendations**: 7-hour minimum, 8-hour optimal guidelines
- **Energy Correlation**: Sleep impact on next-day energy levels

### 3.5 Actionable Insights System

#### 3.5.1 Description
Statistical analysis system that identifies and presents top 3 actionable insights with confidence levels.

#### 3.5.2 Functional Requirements
- **REQ-3.5.1**: System SHALL identify statistically significant relationships (p < 0.05) between metrics
- **REQ-3.5.2**: System SHALL rank insights by effect size and practical significance
- **REQ-3.5.3**: System SHALL display only top 3 most actionable insights
- **REQ-3.5.4**: System SHALL include confidence levels and sample sizes for each insight
- **REQ-3.5.5**: System SHALL provide plain-language interpretation of statistical findings

#### 3.5.3 Insight Categories
- **Activity Impact**: "Your mood increases X points when you do Y activity"
- **Sleep Optimization**: "Your energy peaks at X hours of sleep (Z% confidence)"
- **Behavioral Patterns**: "Screen time above X hours reduces next-day wellbeing by Y%"

### 3.6 Interactive Raw Data Explorer

#### 3.6.1 Description
Comprehensive data exploration interface with filtering, analysis, and export capabilities.

#### 3.6.2 Functional Requirements
- **REQ-3.6.1**: System SHALL provide interactive date range filtering with calendar widget
- **REQ-3.6.2**: System SHALL allow selective column display with multiselect interface
- **REQ-3.6.3**: System SHALL implement data quality filters (Complete Sleep Data, Complete Mood/Energy, Records with Notes)
- **REQ-3.6.4**: System SHALL display filtered data in sortable, paginated table format
- **REQ-3.6.5**: System SHALL show real-time summary statistics (record count, date span, completeness)
- **REQ-3.6.6**: System SHALL provide column-by-column statistics (completeness, means, unique values)
- **REQ-3.6.7**: System SHALL enable CSV export of filtered data with timestamp-based filenames
- **REQ-3.6.8**: System SHALL be accessible via expandable "📋 Interactive Raw Data Explorer" section

### 3.7 Enhanced User Interface System

#### 3.7.1 Description
Streamlit-based web interface with responsive design, robust error handling, and user-friendly controls.

#### 3.7.2 Functional Requirements
- **REQ-3.7.1**: System SHALL provide comprehensive sidebar configuration panel with organized sections
- **REQ-3.7.2**: System SHALL support synthetic data mode for testing and demonstration
- **REQ-3.7.3**: System SHALL implement configurable display options (KPI layout, statistical details)
- **REQ-3.7.4**: System SHALL provide manual data refresh functionality with cache clearing
- **REQ-3.7.5**: System SHALL organize analysis content in tabbed interfaces (Trends, Correlations, Distributions)
- **REQ-3.7.6**: System SHALL display appropriate loading states, error messages, and data source indicators
- **REQ-3.7.7**: System SHALL include drill-down analysis tabs (Sleep Analysis, Activity Impact, Pattern Analysis)

#### 3.6.3 Interface Layout
```
┌─────────────────────────────────────────────────────────┐
│  Header: San-Xing Dashboard Title                       │
├─────────────────────────────────────────────────────────┤
│  Primary KPIs (3 cards)                                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                  │
│  │Wellbeing│ │Balance  │ │Trend    │                  │
│  │Score 7.2│ │Index 85%│ │↗ +0.3   │                  │
│  └─────────┘ └─────────┘ └─────────┘                  │
├─────────────────────────────────────────────────────────┤
│  Top 3 Actionable Insights (Rotated)                   │
│  • "Your energy peaks with 7.5h sleep (87% confidence)"│
│  • "Outdoor activities increase mood by 1.3 points"    │
│  • "Screen time >5h reduces next-day wellbeing by 15%" │
├─────────────────────────────────────────────────────────┤
│  Drill-down Tabs: [Sleep] [Activities] [Patterns]      │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Expandable Detail Views                            │ │
│  │  - Statistical Analysis                             │ │
│  │  - Confidence Intervals                             │ │
│  │  - Historical Context                               │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  Sidebar: Settings, Filters, Data Source               │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements
- **PERF-4.1.1**: Dashboard SHALL load initial data within 5 seconds
- **PERF-4.1.2**: Chart interactions SHALL respond within 1 second
- **PERF-4.1.3**: Data refresh SHALL complete within 10 seconds for typical datasets
- **PERF-4.1.4**: System SHALL cache data for 5 minutes to reduce load times

### 4.2 Reliability Requirements
- **REL-4.2.1**: System SHALL gracefully handle missing data points
- **REL-4.2.2**: System SHALL provide informative error messages for data loading failures
- **REL-4.2.3**: System SHALL maintain functionality when Google Sheets is unavailable
- **REL-4.2.4**: System SHALL recover from visualization rendering errors

### 4.3 Usability Requirements
- **USA-4.3.1**: Interface SHALL be intuitive for users with basic computer skills
- **USA-4.3.2**: Charts SHALL be interactive with hover information
- **USA-4.3.3**: System SHALL provide clear visual indicators for data states
- **USA-4.3.4**: Dashboard SHALL be responsive on desktop and tablet devices

### 4.4 Security Requirements
- **SEC-4.4.1**: Google Sheets access SHALL use service account authentication only
- **SEC-4.4.2**: Credentials SHALL be stored in local files outside version control
- **SEC-4.4.3**: System SHALL run on localhost or trusted networks only
- **SEC-4.4.4**: No personal data SHALL be transmitted to external services (except configured Google Sheets)

### 4.5 Compatibility Requirements
- **COMP-4.5.1**: System SHALL run on Python 3.11 or higher
- **COMP-4.5.2**: Dashboard SHALL be compatible with Chrome, Firefox, Safari browsers
- **COMP-4.5.3**: System SHALL work on macOS, Windows, Linux operating systems
- **COMP-4.5.4**: Mobile browsers SHALL display functional responsive interface

---

## 5. Technical Specifications

### 5.1 Architecture Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Layer    │    │  Processing     │    │  Presentation   │
│                 │    │  Layer          │    │  Layer          │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │JSON Files │  │───▶│  │DataProcessor│  │───▶│  │Streamlit  │  │
│  └───────────┘  │    │  └───────────┘  │    │  │Dashboard  │  │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  └───────────┘  │
│  │G Sheets   │  │───▶│  │Column     │  │    │  ┌───────────┐  │
│  └───────────┘  │    │  │Normalizer │  │    │  │Plotly     │  │
│                 │    │  └───────────┘  │    │  │Charts     │  │
└─────────────────┘    └─────────────────┘    │  └───────────┘  │
                                              └─────────────────┘
```

### 5.2 Core Dependencies
```python
# Required packages with minimum versions
streamlit >= 1.32.0      # Web application framework
plotly >= 5.17.0         # Interactive charting library
pandas >= 2.0.0          # Data manipulation and analysis
matplotlib >= 3.7.0      # Additional plotting capabilities
seaborn >= 0.12.0        # Statistical data visualization
requests >= 2.31.0       # HTTP library for external data
watchdog >= 3.0.0        # File system monitoring (dev)
```

### 5.3 Current File Structure (Post-Cleanup)
```
visualization/
├── dashboard.py                     # Main bulletproof Streamlit dashboard
├── launch_dashboard.py              # Dashboard launcher script
├── robust_data_loader.py            # Data loading with fallback system
├── analytics/                       # Analytics modules
│   ├── __init__.py                  # Analytics module exports
│   ├── kpi_calculator.py            # KPI calculations and analysis
│   ├── sleep_quality_calculator.py  # Objective sleep quality analysis
│   └── statistical_utils.py        # Statistical functions and testing
├── components/                      # Reusable UI components
│   ├── __init__.py                  # Component exports
│   ├── data_viz.py                  # Interactive charts and visualizations
│   ├── drill_down_views.py          # Detailed analysis views
│   ├── insight_display.py           # Statistical insights display
│   └── kpi_cards.py                 # KPI display cards with explanations
├── tests/                           # Comprehensive test suite
│   ├── __init__.py
│   ├── test_kpi_calculator.py       # KPI calculation tests
│   ├── test_statistical_utils.py    # Statistical function tests
│   └── test_ui_components.py        # UI component tests
├── DATA_LOADING_ANALYSIS.md         # Technical documentation
└── README.md                        # Setup and usage guide
```

**Removed in Cleanup:**
- 9 PNG files (~2.8MB of old static visualizations)
- `.venv/` directory (virtual environment)
- `data/` directories (empty)
- `analytics/insight_engine.py` (unused placeholder module)

### 5.4 Configuration Requirements
```toml
# config.local.toml - Required configuration
spreadsheet_id = "Google Sheets ID"
credentials_path = "./secrets/service_account.json"
tab_name = "MetaLog"
```

### 5.5 Data Processing Pipeline
1. **Data Ingestion**: Load from JSON or Google Sheets
2. **Column Normalization**: Map source columns to standard names
3. **Data Type Conversion**: Ensure proper numeric/datetime types
4. **Metric Calculation**: Compute derived metrics (moving averages, activity balance)
5. **Visualization Preparation**: Structure data for chart rendering
6. **Interactive Rendering**: Generate Plotly charts with Streamlit

---

## 6. Interface Requirements

### 6.1 User Interface
- **Web-based interface** accessible via browser at `http://localhost:8501`
- **Responsive design** supporting desktop (1920x1080) to tablet (768x1024) viewports
- **Interactive controls** for data source selection and date filtering
- **Tabbed navigation** for different analysis views
- **Sidebar configuration** panel for settings and filters

### 6.2 External Interfaces

#### 6.2.1 Data Source Interfaces
**JSON File Interface:**
- File format: UTF-8 encoded JSON
- Structure: Array of diary entry objects
- Location: `visualization/raw_data.json`

**Google Sheets Interface:**
- Authentication: Service account JSON key
- API: Google Sheets API v4
- Format: Structured spreadsheet with defined columns

#### 6.2.2 Configuration Interface
- **Config File**: TOML format configuration file
- **Environment Variables**: Optional override support
- **Command Line**: Launch parameters for port and address

### 6.3 Hardware Interfaces
- **Minimum RAM**: 4GB for typical datasets (100-1000 entries)
- **Storage**: 100MB for application and dependencies
- **Network**: Internet connection required for Google Sheets integration
- **Display**: Minimum 1280x720 resolution recommended

---

## 7. Quality Assurance

### 7.1 Testing Requirements
- **Unit Testing**: Core data processing functions
- **Integration Testing**: Data source connectivity
- **User Interface Testing**: Interactive functionality
- **Performance Testing**: Load times and responsiveness
- **Cross-browser Testing**: Chrome, Firefox, Safari compatibility

### 7.2 Error Handling
- **Data Loading Errors**: Clear error messages with resolution guidance
- **Missing Data**: Graceful degradation with empty state indicators
- **Chart Rendering Errors**: Fallback to table view or error message
- **Network Failures**: Automatic fallback to cached or JSON data

### 7.3 Data Validation
- **Input Validation**: Verify data types and ranges
- **Column Validation**: Ensure required columns exist
- **Date Validation**: Proper timestamp parsing and range checking
- **Numeric Validation**: Handle NaN values and outliers

---

## 8. Deployment Requirements

### 8.1 Development Environment
```bash
# Installation steps
uv sync                                         # Install dependencies

# Launch dashboard (recommended)
uv run streamlit run visualization/dashboard.py --server.port 8509

# Alternative launcher
python visualization/launch_dashboard.py

# Run test suite
uv run pytest visualization/tests/ -v
```

### 8.2 Production Deployment Options

#### 8.2.1 Local Network Deployment
```bash
uv run streamlit run visualization/dashboard.py --server.address 0.0.0.0 --server.port 8509
# Accessible at http://YOUR_IP:8509 on local network
```

#### 8.2.2 Cloud Deployment (Streamlit Cloud)
- Repository: Public GitHub repository
- Requirements: `requirements.txt` file
- Configuration: Streamlit secrets management
- URL: Assigned subdomain.streamlit.app

#### 8.2.3 Container Deployment (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "visualization/dashboard.py", "--server.address", "0.0.0.0"]
```

### 8.3 Security Deployment
- **Credentials**: Store service account JSON in `secrets/` directory
- **Environment**: Use environment variables for production secrets
- **Network**: Deploy behind VPN or restricted network access
- **HTTPS**: Use reverse proxy (nginx) for SSL termination

---

## 9. Maintenance and Support

### 9.1 Monitoring Requirements
- **Error Logging**: Structured logging for troubleshooting
- **Performance Monitoring**: Track load times and resource usage  
- **Data Quality Monitoring**: Detect anomalies in source data
- **User Analytics**: Basic usage statistics (optional)

### 9.2 Backup and Recovery
- **Configuration Backup**: Store config files in version control
- **Data Backup**: Snapshot data periodically
- **Credential Backup**: Secure storage of service account keys
- **Recovery Procedures**: Documented restoration steps

### 9.3 Version Control and Updates
- **Code Versioning**: Git-based version control
- **Dependency Management**: UV lock file for reproducible environments
- **Update Procedures**: Testing and deployment protocols
- **Rollback Capability**: Previous version restoration

---

## 10. Acceptance Criteria

### 10.1 Functional Acceptance
- Dashboard loads successfully with sample data
- 3 primary KPIs display correctly with proper calculations
- Top 3 actionable insights appear with confidence levels
- Data source switching works correctly
- Date filtering updates KPIs and insights
- Statistical significance testing filters irrelevant correlations
- Google Sheets integration functions when configured
- Error states display appropriate messages

### 10.2 Performance Acceptance
- Initial load completes within 5 seconds
- Chart interactions respond within 1 second
- Data refresh completes within 10 seconds
- Memory usage remains under 1GB for typical datasets

### 10.3 User Experience Acceptance
- Primary insights visible without scrolling or clicks
- KPIs provide immediate understanding of wellbeing status
- Insights are actionable and include confidence levels
- Interface reduces cognitive load compared to multi-chart approach
- Drill-down details available for users wanting deeper analysis

---

## Appendices

### Appendix A: Sample Data Format
```json
{
  "Timestamp": "25/08/2025 23:59:44",
  "今日整體心情感受": 8,
  "今日整體精力水平如何？": 7,
  "昨晚睡眠品質如何？": 8,
  "昨晚實際入睡時間": "2330",
  "今天實際起床時間": "0730",
  "體重紀錄": 70.5,
  "今日手機螢幕使用時間": 4.2,
  "今天完成了哪些？": "英文學習, 閱讀論文, 戶外活動",
  "今天想記點什麼？": "Today was productive with good focus on learning goals."
}
```

### Appendix B: Column Mapping Reference
| Source (DataProcessor) | Target (Dashboard) | Type | Description |
|----------------------|-------------------|------|-------------|
| `timestamp` | `date` | datetime | Entry timestamp |
| `mood_level` | `mood` | float | Mood rating 1-10 |
| `energy_level` | `energy` | float | Energy rating 1-10 |
| `sleep_quality` | `sleep_quality` | float | Sleep quality 1-10 |
| `sleep_duration_hours` | `sleep_duration` | float | Sleep duration in hours |
| `completed_activities` | `今天完成了哪些？` | string/list | Activity list |
| `positive_activities` | `positive_activities` | int | Count of positive activities |
| `negative_activities` | `negative_activities` | int | Count of negative activities |
| `activity_balance` | `activity_balance` | int | Positive - negative activities |

### Appendix C: Error Code Reference
| Code | Message | Resolution |
|------|---------|------------|
| DATA-001 | "No data available" | Check data source configuration |
| CONFIG-001 | "config.local.toml not found" | Create configuration file |
| AUTH-001 | "Credentials not found" | Set up service account JSON |
| CONN-001 | "Google Sheets connection failed" | Verify network and permissions |
| RENDER-001 | "Chart rendering error" | Check data format and types |

---

**Document Control:**
- **Author**: San-Xing Development Team
- **Reviewers**: Product Owner, Technical Lead
- **Approval**: Project Manager
- **Next Review**: September 26, 2025
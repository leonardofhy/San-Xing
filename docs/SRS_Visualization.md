# Software Requirements Specification (SRS)
## San-Xing Visualization Dashboard

**Document Version:** 1.0  
**Date:** August 26, 2025  
**Project:** San-Xing (三省) - Personal Analytics Visualization System  

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for the San-Xing Visualization Dashboard, an interactive web-based interface for analyzing personal diary data, health metrics, and behavioral patterns. The dashboard provides real-time visualization and analytics for the San-Xing meta-awareness coaching system.

### 1.2 Scope
The visualization system encompasses:
- Interactive web dashboard built with Streamlit
- Multi-source data integration (JSON files and Google Sheets)
- Real-time health metrics visualization
- Activity pattern analysis
- Sleep quality tracking
- Correlation analysis tools
- Responsive design for multiple devices

### 1.3 Definitions and Acronyms
- **San-Xing (三省)**: "Three daily examinations" - Confucian self-reflection practice
- **Dashboard**: Interactive web interface for data visualization
- **DataProcessor**: Backend module for processing raw diary data
- **Streamlit**: Python web application framework
- **JSON**: JavaScript Object Notation data format
- **CSV**: Comma-Separated Values file format

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

### 3.1 Data Integration System

#### 3.1.1 Description
Dual-source data integration supporting both static JSON files and live Google Sheets connectivity.

#### 3.1.2 Functional Requirements
- **REQ-3.1.1**: System SHALL load data from JSON files in standardized format
- **REQ-3.1.2**: System SHALL connect to Google Sheets via service account authentication
- **REQ-3.1.3**: System SHALL automatically detect and use latest data snapshots
- **REQ-3.1.4**: System SHALL provide fallback from Google Sheets to JSON when connectivity fails
- **REQ-3.1.5**: System SHALL normalize column names between different data sources
- **REQ-3.1.6**: System SHALL cache data for 5 minutes to improve performance

#### 3.1.3 Input Specifications
**JSON Format:**
```json
{
  "Timestamp": "DD/MM/YYYY HH:MM:SS",
  "今日整體心情感受": "1-10 numeric scale",
  "今日整體精力水平如何？": "1-10 numeric scale",
  "昨晚睡眠品質如何？": "1-10 numeric scale",
  "今天完成了哪些？": "Comma-separated activity list",
  "體重紀錄": "Numeric weight in kg",
  "今日手機螢幕使用時間": "Numeric hours"
}
```

**Google Sheets Format:**
- Service account JSON authentication
- Spreadsheet ID configuration
- Tab name specification (default: "MetaLog")

### 3.2 Health Metrics Dashboard

#### 3.2.1 Description
Multi-panel visualization system displaying key health and wellness indicators.

#### 3.2.2 Functional Requirements
- **REQ-3.2.1**: System SHALL display 4 key metric cards (entries, mood, energy, sleep)
- **REQ-3.2.2**: System SHALL render 6-panel health dashboard with interactive charts
- **REQ-3.2.3**: System SHALL calculate and display 7-day weight moving average
- **REQ-3.2.4**: System SHALL show mood vs energy correlation with coefficient
- **REQ-3.2.5**: System SHALL handle missing data gracefully with appropriate indicators

#### 3.2.3 Dashboard Panels
1. **Daily Mood Levels**: Time series with 1-10 scale
2. **Daily Energy Levels**: Time series with 1-10 scale  
3. **Screen Time**: Daily usage hours over time
4. **Weight Trends**: Raw data with 7-day moving average overlay
5. **Sleep Quality**: Time series with 1-10 quality scale
6. **Mood vs Energy**: Scatter plot with correlation analysis

### 3.3 Activity Analysis System

#### 3.3.1 Description
Comprehensive activity pattern analysis with categorization and trend visualization.

#### 3.3.2 Functional Requirements
- **REQ-3.3.1**: System SHALL categorize activities into positive, neutral, and negative types
- **REQ-3.3.2**: System SHALL calculate activity balance score (positive - negative)
- **REQ-3.3.3**: System SHALL display activity trends over time as stacked area chart
- **REQ-3.3.4**: System SHALL show correlation between activity balance and mood
- **REQ-3.3.5**: System SHALL generate top 10 most common activities ranking
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

### 3.5 Correlation Analysis System

#### 3.5.1 Description
Interactive correlation matrix for identifying relationships between health metrics.

#### 3.5.2 Functional Requirements
- **REQ-3.5.1**: System SHALL generate correlation matrix for all numeric health metrics
- **REQ-3.5.2**: System SHALL display correlation heatmap with color-coded strength
- **REQ-3.5.3**: System SHALL handle missing data in correlation calculations
- **REQ-3.5.4**: System SHALL provide interactive correlation visualization

#### 3.5.3 Analyzed Metrics
- Mood, Energy, Sleep Quality, Sleep Duration
- Weight, Screen Time
- Positive Activities, Negative Activities, Activity Balance

### 3.6 User Interface System

#### 3.6.1 Description
Streamlit-based web interface with responsive design and interactive controls.

#### 3.6.2 Functional Requirements
- **REQ-3.6.1**: System SHALL provide sidebar configuration panel
- **REQ-3.6.2**: System SHALL support data source selection (JSON/Google Sheets)
- **REQ-3.6.3**: System SHALL implement date range filtering
- **REQ-3.6.4**: System SHALL provide manual data refresh functionality
- **REQ-3.6.5**: System SHALL organize content in tabbed interface
- **REQ-3.6.6**: System SHALL display appropriate loading states and error messages

#### 3.6.3 Interface Layout
```
┌─────────────────────────────────────────────────────────┐
│  Header: San-Xing Dashboard Title                       │
├─────────────────────────────────────────────────────────┤
│  Overview: Key Metrics Cards (4 columns)               │
├─────────────────────────────────────────────────────────┤
│  Tabs: [Health] [Activities] [Sleep] [Correlations]    │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Tab Content Area                                   │ │
│  │  - Interactive Charts                               │ │
│  │  - Data Visualizations                              │ │
│  │  - Statistical Summaries                            │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  Sidebar: Settings, Filters, Controls                  │
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

### 5.3 File Structure
```
visualization/
├── dashboard.py                 # Main Streamlit application
├── generate_sample_data.py      # Sample data generator
├── run_dashboard.py            # Convenience launcher
├── README_DASHBOARD.md         # Setup and deployment guide
├── activity_analysis.py        # Standalone activity analyzer
├── health_dashboard.py         # Standalone health visualizer
├── sleep_analysis.py           # Standalone sleep analyzer
└── download_data.py            # Data fetching utility
```

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
uv sync                                    # Install dependencies
uv run python visualization/generate_sample_data.py  # Generate test data
uv run python run_dashboard.py           # Launch dashboard
```

### 8.2 Production Deployment Options

#### 8.2.1 Local Network Deployment
```bash
uv run streamlit run visualization/dashboard.py --server.address 0.0.0.0
# Accessible at http://YOUR_IP:8501 on local network
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
- All 4 main tabs render without errors
- Data source switching works correctly
- Date filtering updates visualizations
- Charts are interactive with hover information
- Google Sheets integration functions when configured
- Error states display appropriate messages

### 10.2 Performance Acceptance
- Initial load completes within 5 seconds
- Chart interactions respond within 1 second
- Data refresh completes within 10 seconds
- Memory usage remains under 1GB for typical datasets

### 10.3 User Experience Acceptance
- Interface is intuitive without training
- Responsive design works on tablet devices
- Error messages are clear and actionable
- All features accessible within 3 clicks

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
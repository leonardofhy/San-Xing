# San-Xing Visualization Dashboard

## 🎯 Simplified Structure

The visualization module has been cleaned up and now contains only essential files:

### 📊 Main Dashboard
- **`dashboard.py`** - Main dashboard with robust data loading and fallbacks
- **`launch_dashboard.py`** - Simple launcher script
- **`robust_data_loader.py`** - Reliable data loading utilities

### 🧩 Core Modules
- **`analytics/`** - KPI calculations and statistical analysis
  - `kpi_calculator.py` - Wellbeing score, balance index, trend analysis
  - `statistical_utils.py` - Correlation testing, significance analysis
  - `insight_engine.py` - Advanced pattern recognition
  
- **`components/`** - Reusable UI components
  - `kpi_cards.py` - KPI display cards
  - `insight_display.py` - Statistical insights and correlations
  - `data_viz.py` - Interactive charts and visualizations
  - `drill_down_views.py` - Detailed analysis views

### 🧪 Testing
- **`tests/`** - Comprehensive test suite
  - `test_kpi_calculator.py` - KPI calculation tests
  - `test_statistical_utils.py` - Statistical function tests  
  - `test_ui_components.py` - UI component tests

### 📋 Documentation
- **`DATA_LOADING_ANALYSIS.md`** - Technical analysis of data loading solutions
- **`README.md`** - This file

## 🚀 Quick Start

```bash
# Launch the dashboard
cd /Users/leonardo/Workspace/San-Xing
python visualization/launch_dashboard.py

# Or run directly
uv run streamlit run visualization/dashboard.py
```

## 🛡️ Features

### Bulletproof Data Loading
- **Real Google Sheets data** when available
- **Intelligent fallbacks** to synthetic data when needed
- **Never crashes** - always displays functional dashboard
- **Clear status indicators** showing data source

### Comprehensive Analytics
- **KPI Calculations**: Wellbeing score, balance index, trend analysis
- **Statistical Rigor**: Correlation testing with significance analysis
- **Interactive Visualizations**: Trends, distributions, correlation matrices
- **Drill-down Analysis**: Sleep, activity, and pattern analysis

### Robust Architecture
- **Component-based design** for maintainability
- **Comprehensive error handling** with graceful degradation
- **Full test coverage** ensuring reliability
- **Modular structure** for easy extension

## 🧪 Testing

```bash
# Run all tests
cd /Users/leonardo/Workspace/San-Xing
uv run pytest visualization/tests/ -v
```

## 📈 Data Sources

The dashboard intelligently handles multiple data sources:

1. **Primary**: Real Google Sheets data from Meta-Awareness Log
2. **Fallback**: High-quality synthetic data with realistic patterns  
3. **Emergency**: Basic synthetic data if all else fails

Users always know which data source is active through clear UI indicators.

## 🔧 Architecture

```
visualization/
├── dashboard.py                # Main dashboard (robust & reliable)
├── launch_dashboard.py         # Simple launcher
├── robust_data_loader.py       # Data loading utilities
├── analytics/                  # Core analytics
├── components/                 # UI components  
├── tests/                      # Test suite
└── data/                       # Generated visualizations
```

This simplified structure focuses on the essential components while maintaining full functionality and reliability.
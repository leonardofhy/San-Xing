# San-Xing Real Data Dashboard

## ✅ Fixed Real Data Integration

The real data loading issue has been resolved! The dashboard now successfully loads and analyzes your actual Google Sheets data.

## 🔧 What Was Fixed

**Problem**: `"Failed to load real data. Falling back to synthetic data."`

**Root Cause**: The Config class initialization was using the wrong method, causing parameter mapping errors.

**Solution**: Updated to use the proper `Config.from_file()` method which handles field mapping automatically.

## 📊 Real Data Pipeline

The dashboard now successfully processes:

- **126 Google Sheets entries** from your Meta-Awareness Log
- **116 valid processed records** (after filtering)
- **8 key metrics**: mood, energy, sleep quality, sleep duration, activity balance, positive/negative activities
- **Real correlations** and statistical analysis from your actual behavioral patterns

## 🚀 Usage Options

### Option 1: Dedicated Real Data Dashboard
```bash
cd /Users/leonardo/Workspace/San-Xing
uv run streamlit run visualization/real_data_dashboard.py
```

### Option 2: Enhanced Demo with Data Source Toggle
```bash
cd /Users/leonardo/Workspace/San-Xing
uv run streamlit run visualization/advanced_dashboard_demo.py
# Select "Real Google Sheets Data" from sidebar dropdown
```

### Option 3: Launch Script
```bash
python visualization/run_real_dashboard.py
```

## 📈 Real Data Features

### Data Source Verification
- Live connection indicator showing Google Sheets source
- Data quality metrics (100% completeness from your 116 entries)
- Date range display (your actual logging period)

### Personalized KPIs
- **Wellbeing Score**: Calculated from your actual mood/energy/sleep data
- **Balance Index**: Based on your real positive vs negative activity ratios
- **Trend Indicator**: Statistical significance testing on your behavioral trends

### Real Insights
- Mood patterns from your actual daily ratings
- Sleep analysis from your recorded bedtime/wake times
- Activity impact analysis from your tracked behaviors
- Correlation discoveries between your mood, sleep, and activities

### Statistical Rigor
- Mann-Kendall trend testing on your real data
- Pearson correlations with Bonferroni correction
- Confidence intervals and effect size calculations
- Significance testing with proper sample size validation

## 🔍 Debugging Utilities

If you encounter issues, use the debug script:
```bash
cd /Users/leonardo/Workspace/San-Xing
uv run python visualization/debug_data_loading.py
```

This will test each step of the data loading pipeline and identify any problems.

## 📋 Data Quality Summary

- **Source**: Google Sheets Meta-Awareness Log (Traditional Chinese entries)
- **Raw Records**: 126 entries
- **Processed Records**: 116 valid entries (92% success rate)
- **Date Coverage**: Your actual logging period from Google Sheets
- **Key Metrics**: Mood, energy, sleep patterns, activity tracking
- **Analysis**: Real correlations and trends from your personal data

The dashboard now provides genuine insights from your actual wellbeing tracking data!
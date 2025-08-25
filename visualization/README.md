# San-Xing Data Visualization

Data visualization tools for analyzing San-Xing diary data exported from HuggingFace.

## Setup

1. Initialize the uv environment:

```bash
cd visualization
uv sync
```

2. Download your data:

```bash
uv run python download_data.py
```

## Available Analyses

### Sleep Analysis (`sleep_analysis.py`)

- Sleep duration trends over time
- Sleep quality correlation with duration and energy
- Sleep statistics summary
- Generates: `sleep_duration_trends.png`, `sleep_quality_correlation.png`

### Health Dashboard (`health_dashboard.py`)

- Multi-factor health dashboard (mood, energy, weight, screen time, sleep quality)
- Correlation heatmap between all health metrics
- Screen time vs sleep quality analysis
- Generates: `health_dashboard.png`, `correlation_heatmap.png`, `screen_time_vs_sleep.png`

### Activity Analysis (`activity_analysis.py`)

- Activity categorization (positive, neutral, negative)
- Activity vs mood correlation
- Most common activities frequency
- Weekly activity patterns by day of week
- Generates: `activities_vs_mood.png`, `activity_trends.png`, `top_activities.png`, `weekly_patterns.png`

## Usage

Run individual analyses:

```bash
# Sleep patterns
uv run python sleep_analysis.py

# Comprehensive health dashboard
uv run python health_dashboard.py

# Activity and mood analysis
uv run python activity_analysis.py
```

Or run all analyses (from project root or inside visualization/):

```bash
# From project root
uv run python visualization/run_all.py

# Or inside visualization directory
cd visualization
uv run python run_all.py
```

## Generated Files

All visualizations are saved as high-resolution PNG files:

**Sleep Analysis:**

- `sleep_duration_trends.png` - Sleep duration over time with recommended hours
- `sleep_quality_correlation.png` - Sleep duration vs quality with energy levels

**Health Dashboard:**

- `health_dashboard.png` - 6-panel comprehensive health overview
- `correlation_heatmap.png` - Correlation matrix of all health metrics
- `screen_time_vs_sleep.png` - Digital wellness analysis

**Activity Analysis:**

- `activities_vs_mood.png` - Activity categories vs mood correlation
- `activity_trends.png` - Activity types over time (stacked area)
- `top_activities.png` - Most frequently performed activities
- `weekly_patterns.png` - Activity and mood patterns by day of week

## Data Format

The scripts expect `raw_data.json` containing your HuggingFace dataset with fields:

- `Timestamp` - Entry timestamp
- `昨晚實際入睡時間` - Bedtime (HHMM format)
- `今天實際起床時間` - Wake time (HHMM format)
- `昨晚睡眠品質如何？` - Sleep quality (1-10)
- `今日整體心情感受` - Daily mood (1-10)
- `今日整體精力水平如何？` - Energy level (1-10)
- `體重紀錄` - Weight records
- `今日手機螢幕使用時間` - Daily screen time
- `今天完成了哪些？` - Daily activities (comma-separated)

## Requirements

- Python 3.11+
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- plotly >= 5.17.0
- requests >= 2.31.0

### Non-blocking / Headless Mode

Plots are generated and saved without opening GUI windows by default. To enable interactive windows, set:

```bash
export SHOW_PLOTS=1
uv run python visualization/health_dashboard.py
```

Unset (or leave blank) to keep headless behavior.

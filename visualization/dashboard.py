#!/usr/bin/env python3
"""
San-Xing (三省) Interactive Dashboard
Streamlit-based web dashboard for personal analytics and insights
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Add parent directory to path to import from src
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.data_processor import DataProcessor
    from src.config import Config
    HAS_SRC = True
except ImportError:
    HAS_SRC = False


# Page configuration
st.set_page_config(
    page_title="三省 (San-Xing) Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stMetric > label {
        font-size: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_json(data_file: str = "raw_data.json") -> pd.DataFrame:
    """Load and preprocess raw diary data from JSON file."""
    file_path = Path(__file__).parent / data_file
    
    if not file_path.exists():
        st.error(f"Data file not found: {data_file}")
        st.info("Please run download_data.py first to generate the data file.")
        return pd.DataFrame()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        if 'Timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['Timestamp'], format='%d/%m/%Y %H:%M:%S')
            df = df.sort_values('date')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_data_from_sheets() -> pd.DataFrame:
    """Load data directly from Google Sheets using San-Xing data processor."""
    if not HAS_SRC:
        st.error("San-Xing source modules not available. Using JSON fallback.")
        return pd.DataFrame()
    
    try:
        config_path = Path(__file__).parent.parent / "config.local.toml"
        if not config_path.exists():
            st.error("config.local.toml not found. Please set up configuration.")
            return pd.DataFrame()
        
        config = Config.from_file(config_path)
        processor = DataProcessor(config)
        
        # Load from latest snapshot or fetch fresh data
        snapshot_dir = Path(config.output_dir) / "raw"
        latest_snapshot = None
        
        if snapshot_dir.exists():
            snapshots = list(snapshot_dir.glob("snapshot_*.json"))
            if snapshots:
                latest_snapshot = max(snapshots, key=lambda p: p.stat().st_mtime)
        
        if latest_snapshot:
            processor.load_from_snapshot(latest_snapshot)
        else:
            # Would need to implement fresh data fetch
            st.warning("No snapshot found. Using JSON fallback.")
            return pd.DataFrame()
        
        return processor.process_all()
        
    except Exception as e:
        st.error(f"Error loading from sheets: {e}")
        return pd.DataFrame()


def process_health_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Process all health-related metrics."""
    if df.empty:
        return df
    
    # Basic health metrics
    df['mood'] = pd.to_numeric(df.get('今日整體心情感受', pd.Series()), errors='coerce')
    df['energy'] = pd.to_numeric(df.get('今日整體精力水平如何？', pd.Series()), errors='coerce')
    df['sleep_quality'] = pd.to_numeric(df.get('昨晚睡眠品質如何？', pd.Series()), errors='coerce')
    df['weight'] = pd.to_numeric(df.get('體重紀錄', pd.Series()), errors='coerce')
    df['screen_time'] = pd.to_numeric(df.get('今日手機螢幕使用時間', pd.Series()), errors='coerce')
    
    # Calculate weight moving average
    df['weight_ma'] = df['weight'].rolling(window=7, min_periods=1).mean()
    
    return df


def parse_time(time_str):
    """Parse time string in HHMM format to time object."""
    if pd.isna(time_str) or time_str == '':
        return None
    try:
        return datetime.strptime(str(time_str).zfill(4), '%H%M').time()
    except ValueError:
        return None


def calc_sleep_duration(bedtime, wake_time):
    """Calculate sleep duration handling overnight sleep."""
    if pd.isna(bedtime) or pd.isna(wake_time) or bedtime is None or wake_time is None:
        return None
    
    bed_dt = datetime.combine(datetime.today(), bedtime)
    wake_dt = datetime.combine(datetime.today(), wake_time)
    
    # If bedtime is after 18:00, assume it's previous day
    if bedtime.hour >= 18:
        bed_dt -= timedelta(days=1)
    
    duration = wake_dt - bed_dt
    return duration.total_seconds() / 3600  # Convert to hours


def process_sleep_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process sleep-related data."""
    if df.empty:
        return df
    
    # Parse sleep times
    df['bedtime'] = df.get('昨晚實際入睡時間', pd.Series()).apply(parse_time)
    df['wake_time'] = df.get('今天實際起床時間', pd.Series()).apply(parse_time)
    
    # Calculate sleep duration
    df['sleep_duration'] = df.apply(
        lambda row: calc_sleep_duration(row.get('bedtime'), row.get('wake_time')), axis=1
    )
    
    return df


def process_activities(df: pd.DataFrame) -> pd.DataFrame:
    """Process and categorize activities."""
    if df.empty:
        return df
    
    # Define activity categories
    positive_activities = [
        '英文學習', '閱讀論文', '看書', '戶外活動', '實體社交活動', 
        '看知識型視頻', '看英文視頻', '額外完成一個任務', '額外完成兩個任務', 
        '額外完成三個或以上任務'
    ]
    
    neutral_activities = [
        '做家務', '頭髮護理', '面部護理', '久坐'
    ]
    
    negative_activities = [
        '打遊戲', '滑手機', '看娛樂視頻'
    ]
    
    # Count activities by category
    def count_activities_by_category(activities_str, category_list):
        if pd.isna(activities_str):
            return 0
        return sum(1 for activity in category_list if activity in str(activities_str))
    
    activities_col = df.get('今天完成了哪些？', pd.Series())
    df['positive_activities'] = activities_col.apply(
        lambda x: count_activities_by_category(x, positive_activities)
    )
    df['neutral_activities'] = activities_col.apply(
        lambda x: count_activities_by_category(x, neutral_activities)
    )
    df['negative_activities'] = activities_col.apply(
        lambda x: count_activities_by_category(x, negative_activities)
    )
    
    # Calculate activity balance score
    df['activity_balance'] = df['positive_activities'] - df['negative_activities']
    
    return df


def render_overview_metrics(df: pd.DataFrame):
    """Render key metrics overview."""
    st.markdown('<p class="main-header">📊 三省 (San-Xing) Personal Analytics Dashboard</p>', 
                unsafe_allow_html=True)
    
    if df.empty:
        st.warning("No data available")
        return
    
    # Calculate key metrics
    total_entries = len(df)
    date_range = f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📝 Total Entries",
            value=total_entries
        )
    
    with col2:
        avg_mood = df['mood'].mean() if not df['mood'].isna().all() else 0
        st.metric(
            label="😊 Average Mood",
            value=f"{avg_mood:.1f}/10"
        )
    
    with col3:
        avg_energy = df['energy'].mean() if not df['energy'].isna().all() else 0
        st.metric(
            label="⚡ Average Energy",
            value=f"{avg_energy:.1f}/10"
        )
    
    with col4:
        avg_sleep = df['sleep_duration'].mean() if not df['sleep_duration'].isna().all() else 0
        st.metric(
            label="🛌 Average Sleep",
            value=f"{avg_sleep:.1f}h"
        )
    
    st.markdown(f"**Data Range:** {date_range}")
    st.divider()


def render_health_dashboard(df: pd.DataFrame):
    """Render comprehensive health dashboard."""
    st.subheader("🏥 Health Metrics Dashboard")
    
    if df.empty:
        st.warning("No health data available")
        return
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=['Daily Mood Levels', 'Daily Energy Levels', 'Screen Time', 
                       'Weight Trends', 'Sleep Quality', 'Mood vs Energy'],
        specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": True}, {"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Mood over time
    valid_mood = df[df['mood'].notna()]
    if not valid_mood.empty:
        fig.add_trace(
            go.Scatter(x=valid_mood['date'], y=valid_mood['mood'], 
                      mode='lines+markers', name='Mood', 
                      line=dict(color='green')),
            row=1, col=1
        )
    
    # Energy over time
    valid_energy = df[df['energy'].notna()]
    if not valid_energy.empty:
        fig.add_trace(
            go.Scatter(x=valid_energy['date'], y=valid_energy['energy'], 
                      mode='lines+markers', name='Energy', 
                      line=dict(color='blue')),
            row=1, col=2
        )
    
    # Screen time
    valid_screen = df[df['screen_time'].notna()]
    if not valid_screen.empty:
        fig.add_trace(
            go.Scatter(x=valid_screen['date'], y=valid_screen['screen_time'], 
                      mode='lines+markers', name='Screen Time', 
                      line=dict(color='red')),
            row=1, col=3
        )
    
    # Weight trends
    valid_weight = df[df['weight'].notna()]
    if not valid_weight.empty:
        fig.add_trace(
            go.Scatter(x=valid_weight['date'], y=valid_weight['weight'], 
                      mode='markers', name='Daily Weight', 
                      marker=dict(color='orange', size=6)),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=valid_weight['date'], y=valid_weight['weight_ma'], 
                      mode='lines', name='7-Day Average', 
                      line=dict(color='darkorange', width=3)),
            row=2, col=1
        )
    
    # Sleep quality
    valid_sleep = df[df['sleep_quality'].notna()]
    if not valid_sleep.empty:
        fig.add_trace(
            go.Scatter(x=valid_sleep['date'], y=valid_sleep['sleep_quality'], 
                      mode='lines+markers', name='Sleep Quality', 
                      line=dict(color='purple')),
            row=2, col=2
        )
    
    # Mood vs Energy correlation
    valid_both = df[(df['mood'].notna()) & (df['energy'].notna())]
    if not valid_both.empty:
        fig.add_trace(
            go.Scatter(x=valid_both['mood'], y=valid_both['energy'], 
                      mode='markers', name='Mood vs Energy', 
                      marker=dict(color='teal', size=8)),
            row=2, col=3
        )
    
    fig.update_layout(height=800, showlegend=False, title_text="Health Metrics Overview")
    st.plotly_chart(fig, use_container_width=True)


def render_activity_analysis(df: pd.DataFrame):
    """Render activity analysis section."""
    st.subheader("🎯 Activity Analysis")
    
    if df.empty:
        st.warning("No activity data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Activity trends over time
        fig_trends = go.Figure()
        
        if 'positive_activities' in df.columns:
            fig_trends.add_trace(go.Scatter(
                x=df['date'], 
                y=df['positive_activities'], 
                fill='tonexty',
                mode='lines',
                name='Positive Activities',
                line=dict(color='green')
            ))
        
        if 'negative_activities' in df.columns:
            fig_trends.add_trace(go.Scatter(
                x=df['date'], 
                y=df['negative_activities'], 
                fill='tonexty',
                mode='lines',
                name='Negative Activities',
                line=dict(color='red')
            ))
        
        fig_trends.update_layout(
            title="Activity Trends Over Time",
            xaxis_title="Date",
            yaxis_title="Number of Activities",
            height=400
        )
        st.plotly_chart(fig_trends, use_container_width=True)
    
    with col2:
        # Activity balance vs mood
        if 'activity_balance' in df.columns and 'mood' in df.columns:
            valid_balance = df[(df['activity_balance'].notna()) & (df['mood'].notna())]
            
            if not valid_balance.empty:
                # Handle energy column for sizing - filter out NaN values
                size_col = None
                if 'energy' in df.columns:
                    # Only use energy for sizing if we have valid energy data
                    valid_balance_with_energy = valid_balance[valid_balance['energy'].notna()]
                    if not valid_balance_with_energy.empty:
                        valid_balance = valid_balance_with_energy
                        size_col = 'energy'
                
                fig_balance = px.scatter(
                    valid_balance, 
                    x='activity_balance', 
                    y='mood',
                    size=size_col,
                    title="Activity Balance vs Mood" + (" (Size = Energy)" if size_col else ""),
                    labels={'activity_balance': 'Activity Balance Score', 'mood': 'Mood (1-10)'}
                )
                fig_balance.update_layout(height=400)
                st.plotly_chart(fig_balance, use_container_width=True)
    
    # Most common activities
    if '今天完成了哪些？' in df.columns:
        st.subheader("Top Activities")
        all_activities = []
        
        for activities_str in df['今天完成了哪些？'].dropna():
            if activities_str and activities_str.strip():
                activities = [act.strip() for act in str(activities_str).split(',')]
                all_activities.extend(activities)
        
        if all_activities:
            activity_counts = Counter(all_activities)
            top_activities = activity_counts.most_common(10)
            
            if top_activities:
                activities_df = pd.DataFrame(top_activities, columns=['Activity', 'Count'])
                
                fig_top = px.bar(
                    activities_df, 
                    x='Count', 
                    y='Activity',
                    orientation='h',
                    title="Top 10 Most Common Activities"
                )
                fig_top.update_layout(height=400)
                st.plotly_chart(fig_top, use_container_width=True)


def render_sleep_analysis(df: pd.DataFrame):
    """Render sleep analysis section."""
    st.subheader("🛌 Sleep Analysis")
    
    if df.empty:
        st.warning("No sleep data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sleep duration trends
        if 'sleep_duration' in df.columns:
            valid_sleep = df[df['sleep_duration'].notna()]
            
            if not valid_sleep.empty:
                fig_duration = go.Figure()
                
                fig_duration.add_trace(go.Scatter(
                    x=valid_sleep['date'],
                    y=valid_sleep['sleep_duration'],
                    mode='lines+markers',
                    name='Sleep Duration',
                    line=dict(color='blue')
                ))
                
                # Add recommended sleep lines
                fig_duration.add_hline(
                    y=8, line_dash="dash", 
                    annotation_text="Recommended 8h", 
                    line_color="green"
                )
                fig_duration.add_hline(
                    y=7, line_dash="dash", 
                    annotation_text="Minimum 7h", 
                    line_color="orange"
                )
                
                fig_duration.update_layout(
                    title="Sleep Duration Trends",
                    xaxis_title="Date",
                    yaxis_title="Sleep Duration (Hours)",
                    height=400
                )
                st.plotly_chart(fig_duration, use_container_width=True)
    
    with col2:
        # Sleep quality correlation
        if 'sleep_duration' in df.columns and 'sleep_quality' in df.columns:
            valid_corr = df[(df['sleep_duration'].notna()) & (df['sleep_quality'].notna())]
            
            if not valid_corr.empty:
                # Handle energy column for sizing - filter out NaN values
                size_col = None
                if 'energy' in df.columns:
                    # Only use energy for sizing if we have valid energy data
                    valid_corr_with_energy = valid_corr[valid_corr['energy'].notna()]
                    if not valid_corr_with_energy.empty:
                        valid_corr = valid_corr_with_energy
                        size_col = 'energy'
                
                fig_quality = px.scatter(
                    valid_corr,
                    x='sleep_duration',
                    y='sleep_quality',
                    size=size_col,
                    title="Sleep Duration vs Quality" + (" (Size = Energy)" if size_col else ""),
                    labels={'sleep_duration': 'Sleep Duration (Hours)', 
                           'sleep_quality': 'Sleep Quality (1-10)'}
                )
                fig_quality.update_layout(height=400)
                st.plotly_chart(fig_quality, use_container_width=True)


def main():
    """Main dashboard function."""
    # Sidebar
    st.sidebar.title("⚙️ Dashboard Settings")
    
    # Data source selection
    data_source = st.sidebar.selectbox(
        "Data Source",
        ["JSON File", "Google Sheets (Live)"],
        help="Choose between static JSON file or live Google Sheets data"
    )
    
    # Load data based on selection
    if data_source == "Google Sheets (Live)":
        df = load_data_from_sheets()
        if df.empty:  # Fallback to JSON if sheets loading fails
            st.sidebar.warning("Falling back to JSON file")
            df = load_data_from_json()
    else:
        df = load_data_from_json()
    
    if df.empty:
        st.error("No data available. Please check your data source.")
        return
    
    # Process data
    df = process_health_metrics(df)
    df = process_sleep_data(df)
    df = process_activities(df)
    
    # Date filter
    if 'date' in df.columns and not df['date'].isna().all():
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", help="Refresh dashboard data"):
        st.cache_data.clear()
        st.rerun()
    
    # Main dashboard
    render_overview_metrics(df)
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Health Overview", "🎯 Activities", "🛌 Sleep", "📈 Correlations"])
    
    with tab1:
        render_health_dashboard(df)
    
    with tab2:
        render_activity_analysis(df)
    
    with tab3:
        render_sleep_analysis(df)
    
    with tab4:
        st.subheader("📈 Correlation Analysis")
        # Correlation matrix
        numeric_cols = ['mood', 'energy', 'sleep_quality', 'sleep_duration', 
                       'weight', 'screen_time', 'positive_activities', 'negative_activities']
        available_cols = [col for col in numeric_cols if col in df.columns]
        
        if len(available_cols) > 1:
            corr_data = df[available_cols].corr()
            
            fig_corr = px.imshow(
                corr_data,
                title="Health Metrics Correlation Matrix",
                aspect="auto",
                color_continuous_scale="RdBu_r"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.warning("Insufficient data for correlation analysis")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**三省 (San-Xing)**")
    st.sidebar.markdown("*Automated meta-awareness & reflective coaching*")


if __name__ == "__main__":
    main()
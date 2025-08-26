#!/usr/bin/env python3
"""
Real Data San-Xing Dashboard
Uses actual Google Sheets data for comprehensive wellbeing analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import toml

# Add parent directory to path to import San-Xing modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.data_processor import DataProcessor
from src.config import Config

# Import our analytics modules
from analytics.kpi_calculator import KPICalculator
from analytics.statistical_utils import correlation_with_significance

# Import our new UI components
from components.kpi_cards import (
    render_wellbeing_card,
    render_balance_card,
    render_trend_card,
    render_kpi_overview
)
from components.insight_display import (
    render_statistical_insights,
    render_correlation_matrix,
    render_trend_analysis
)
from components.data_viz import (
    create_kpi_gauge,
    create_trend_chart,
    create_correlation_heatmap,
    create_statistical_summary_chart
)
from components.drill_down_views import (
    render_sleep_analysis_drilldown,
    render_activity_impact_drilldown,
    render_pattern_analysis_drilldown
)

# Page configuration
st.set_page_config(
    page_title="San-Xing Real Data Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .dashboard-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .metric-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    
    .data-source-info {
        background: #e8f5e8;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_real_data():
    """Load and process real Google Sheets data"""
    try:
        # Load configuration
        config_path = parent_dir / "config.local.toml"
        with open(config_path, 'r') as f:
            config_dict = toml.load(f)
        
        config = Config(**config_dict)
        
        # Load latest snapshot
        snapshot_path = parent_dir / "data" / "raw" / "snapshot_010f189dd4de4959.json"
        
        if not snapshot_path.exists():
            st.error(f"Snapshot file not found: {snapshot_path}")
            return None, None, None
        
        # Process data
        processor = DataProcessor(config)
        processor.load_from_snapshot(snapshot_path)
        df = processor.process_all()
        
        # Get summary stats
        summary_stats = processor.get_summary_stats()
        
        return df, summary_stats, processor
    
    except Exception as e:
        st.error(f"Error loading real data: {str(e)}")
        return None, None, None

def prepare_kpi_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for KPI calculations"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Create a simplified DataFrame for KPI calculations
    kpi_data = pd.DataFrame()
    
    # Map real data columns to expected KPI calculator columns
    if 'logical_date' in df.columns:
        kpi_data['date'] = pd.to_datetime(df['logical_date'])
    
    if 'mood_level' in df.columns:
        kpi_data['mood'] = df['mood_level']
    
    if 'energy_level' in df.columns:
        kpi_data['energy'] = df['energy_level']
    
    if 'sleep_quality' in df.columns:
        kpi_data['sleep_quality'] = df['sleep_quality']
    
    if 'sleep_duration_hours' in df.columns:
        kpi_data['sleep_duration'] = df['sleep_duration_hours']
    
    if 'activity_balance' in df.columns:
        kpi_data['activity_balance'] = df['activity_balance']
    
    if 'positive_activities' in df.columns:
        kpi_data['positive_activities'] = df['positive_activities']
    
    if 'negative_activities' in df.columns:
        kpi_data['negative_activities'] = df['negative_activities']
    
    # Remove rows with all NaN values in key metrics
    key_columns = ['mood', 'energy', 'sleep_quality']
    available_key_columns = [col for col in key_columns if col in kpi_data.columns]
    
    if available_key_columns:
        kpi_data = kpi_data.dropna(subset=available_key_columns, how='all')
    
    return kpi_data

def render_data_source_info(summary_stats: dict, df: pd.DataFrame):
    """Render information about the data source"""
    st.markdown("""
    <div class="data-source-info">
        <h4>📋 Real Data Source</h4>
        <p><strong>Google Sheets:</strong> San-Xing Meta-Awareness Log</p>
        <p><strong>Live data integration:</strong> Your actual daily entries and reflections</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Entries", summary_stats.get('total_entries', 0))
    
    with col2:
        date_range = summary_stats.get('date_range', {})
        if date_range.get('start') and date_range.get('end'):
            start_date = datetime.fromisoformat(date_range['start']).strftime('%Y-%m-%d')
            end_date = datetime.fromisoformat(date_range['end']).strftime('%Y-%m-%d')
            st.metric("Date Range", f"{start_date} to {end_date}")
        else:
            st.metric("Date Range", "N/A")
    
    with col3:
        mood_stats = summary_stats.get('mood_stats', {})
        if mood_stats.get('mean'):
            st.metric("Avg Mood", f"{mood_stats['mean']:.1f}/10")
        else:
            st.metric("Avg Mood", "N/A")
    
    with col4:
        sleep_stats = summary_stats.get('sleep_stats', {})
        if sleep_stats.get('avg_duration'):
            st.metric("Avg Sleep", f"{sleep_stats['avg_duration']:.1f}h")
        else:
            st.metric("Avg Sleep", "N/A")

def render_insights_from_real_data(df: pd.DataFrame):
    """Generate insights from real data patterns"""
    st.markdown("## 🔍 Insights from Your Data")
    
    if df is None or df.empty:
        st.warning("No data available for insights generation")
        return
    
    insights = []
    
    # Mood patterns
    if 'mood_level' in df.columns:
        mood_data = df['mood_level'].dropna()
        if len(mood_data) > 0:
            avg_mood = mood_data.mean()
            mood_trend = "improving" if mood_data.iloc[-5:].mean() > mood_data.iloc[:5].mean() else "stable"
            insights.append({
                'title': 'Mood Pattern',
                'content': f"Your average mood level is {avg_mood:.1f}/10 with a {mood_trend} recent trend.",
                'type': 'info'
            })
    
    # Sleep patterns
    if 'sleep_duration_hours' in df.columns:
        sleep_data = df['sleep_duration_hours'].dropna()
        if len(sleep_data) > 0:
            avg_sleep = sleep_data.mean()
            optimal_range = (sleep_data >= 7) & (sleep_data <= 9)
            optimal_nights = optimal_range.sum()
            total_nights = len(sleep_data)
            optimal_pct = (optimal_nights / total_nights * 100) if total_nights > 0 else 0
            
            insights.append({
                'title': 'Sleep Quality',
                'content': f"Average sleep duration: {avg_sleep:.1f}h. {optimal_pct:.0f}% of nights in optimal 7-9h range.",
                'type': 'success' if optimal_pct > 70 else 'warning'
            })
    
    # Activity balance
    if 'positive_activities' in df.columns and 'negative_activities' in df.columns:
        pos_activities = df['positive_activities'].sum()
        neg_activities = df['negative_activities'].sum()
        if pos_activities + neg_activities > 0:
            balance_ratio = pos_activities / (pos_activities + neg_activities)
            insights.append({
                'title': 'Activity Balance',
                'content': f"Positive activities make up {balance_ratio:.0%} of tracked behaviors.",
                'type': 'success' if balance_ratio > 0.6 else 'info'
            })
    
    # Display insights
    for insight in insights:
        if insight['type'] == 'success':
            st.success(f"**{insight['title']}**: {insight['content']}")
        elif insight['type'] == 'warning':
            st.warning(f"**{insight['title']}**: {insight['content']}")
        else:
            st.info(f"**{insight['title']}**: {insight['content']}")

def main():
    """Main dashboard application with real data"""
    
    # Header
    st.markdown('<h1 class="main-header">San-Xing Real Data Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Your personal wellbeing analytics from Google Sheets data")
    
    # Load real data
    with st.spinner("Loading your real data from Google Sheets..."):
        df, summary_stats, processor = load_real_data()
    
    if df is None or df.empty:
        st.error("Failed to load real data. Please check your configuration and data source.")
        st.stop()
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("## 🔧 Dashboard Configuration")
        
        # Data filtering options
        st.markdown("### 📊 Data Filtering")
        
        # Date range filter
        if 'logical_date' in df.columns:
            min_date = df['logical_date'].min()
            max_date = df['logical_date'].max()
            
            date_filter = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_filter) == 2:
                start_date, end_date = date_filter
                df_filtered = df[(df['logical_date'] >= pd.to_datetime(start_date)) & 
                               (df['logical_date'] <= pd.to_datetime(end_date))]
            else:
                df_filtered = df
        else:
            df_filtered = df
        
        # Display options
        st.markdown("### 🎨 Display Options")
        kpi_layout = st.selectbox("KPI Layout", ["columns", "rows", "grid"], index=0)
        show_raw_data = st.checkbox("Show Raw Data Preview", False)
        show_statistical_details = st.checkbox("Show Statistical Methodology", False)
        
        # Analysis options
        st.markdown("### 📈 Analysis Options")
        correlation_alpha = st.slider("Significance Level (α)", 0.01, 0.10, 0.05, 0.01)
        show_only_significant = st.checkbox("Highlight Only Significant Correlations", False)
        
        st.markdown("---")
        st.markdown(f"**Filtered Data:** {len(df_filtered)} entries")
    
    # Display data source information
    render_data_source_info(summary_stats, df_filtered)
    
    # Show raw data if requested
    if show_raw_data:
        with st.expander("📋 Raw Data Preview", expanded=False):
            st.dataframe(df_filtered.head(20))
            st.write(f"**Dataset shape:** {df_filtered.shape[0]} entries × {df_filtered.shape[1]} columns")
    
    # Prepare data for KPI calculations
    kpi_data = prepare_kpi_data(df_filtered)
    
    if kpi_data.empty:
        st.warning("Insufficient data for KPI calculations. Need mood, energy, or sleep quality data.")
        st.stop()
    
    # Calculate KPIs and statistics
    with st.spinner("Analyzing your data and calculating KPIs..."):
        try:
            kpis = KPICalculator.calculate_all_kpis(kpi_data)
            
            # Calculate correlations on numeric columns only
            numeric_cols = kpi_data.select_dtypes(include=[np.number])
            if len(numeric_cols.columns) > 1:
                correlations = correlation_with_significance(
                    numeric_cols, 
                    alpha=correlation_alpha
                )
            else:
                correlations = {'significant_correlations': [], 'all_correlations': {}, 'total_tests': 0}
        except Exception as e:
            st.error(f"Error calculating KPIs: {str(e)}")
            st.stop()
    
    # === MAIN DASHBOARD SECTIONS ===
    
    # 1. KPI Overview
    st.markdown("## 📊 Key Performance Indicators")
    render_kpi_overview(kpis, layout=kpi_layout)
    
    st.divider()
    
    # 2. Real Data Insights
    render_insights_from_real_data(df_filtered)
    
    st.divider()
    
    # 3. Statistical Analysis
    if len(numeric_cols.columns) > 1:
        render_statistical_insights(
            correlations, 
            show_methodology=show_statistical_details
        )
        st.divider()
    
    # 4. Interactive Visualizations
    st.markdown("## 📈 Interactive Visualizations")
    
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Trends", "Correlations", "Distributions"])
    
    with viz_tab1:
        # Trend analysis with real data
        trend_cols = ['mood', 'energy', 'sleep_quality']
        available_cols = [col for col in trend_cols if col in kpi_data.columns and not kpi_data[col].isna().all()]
        
        if available_cols:
            trend_chart = create_trend_chart(
                data=kpi_data,
                value_columns=available_cols,
                date_column='date',
                title="Your Wellbeing Metrics Over Time",
                show_trend_lines=True
            )
            st.plotly_chart(trend_chart, use_container_width=True)
        
        # Individual KPI gauges
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'wellbeing_score' in kpis:
                gauge_fig = create_kpi_gauge(
                    value=kpis['wellbeing_score']['score'],
                    max_value=10,
                    title="Wellbeing Score",
                    color_scheme="blue"
                )
                st.plotly_chart(gauge_fig, use_container_width=True)
        
        with col2:
            if 'balance_index' in kpis:
                gauge_fig = create_kpi_gauge(
                    value=kpis['balance_index']['index'],
                    max_value=100,
                    title="Balance Index (%)",
                    color_scheme="green"
                )
                st.plotly_chart(gauge_fig, use_container_width=True)
        
        with col3:
            # Trend confidence gauge
            if 'trend_indicator' in kpis:
                confidence_map = {'high': 0.9, 'medium': 0.6, 'low': 0.3}
                confidence_val = confidence_map.get(kpis['trend_indicator']['confidence'], 0.3)
                
                gauge_fig = create_kpi_gauge(
                    value=confidence_val,
                    max_value=1.0,
                    title="Trend Confidence",
                    color_scheme="purple"
                )
                st.plotly_chart(gauge_fig, use_container_width=True)
    
    with viz_tab2:
        # Correlation analysis
        if len(numeric_cols.columns) > 1:
            render_correlation_matrix(
                data=numeric_cols,
                correlation_results=correlations,
                show_only_significant=show_only_significant
            )
        else:
            st.info("Need at least 2 numeric variables for correlation analysis")
    
    with viz_tab3:
        # Distribution analysis
        dist_type = st.selectbox("Distribution View", ["box", "violin", "histogram"])
        wellbeing_cols = ['mood', 'energy', 'sleep_quality', 'sleep_duration']
        available_dist_cols = [col for col in wellbeing_cols if col in kpi_data.columns and not kpi_data[col].isna().all()]
        
        if available_dist_cols:
            dist_chart = create_statistical_summary_chart(
                data=kpi_data,
                columns=available_dist_cols,
                chart_type=dist_type
            )
            st.plotly_chart(dist_chart, use_container_width=True)
        else:
            st.info("No numeric data available for distribution analysis")
    
    st.divider()
    
    # 5. Drill-down Analysis Tabs
    st.markdown("## 🔍 Detailed Analysis")
    
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["Sleep Analysis", "Activity Impact", "Pattern Analysis"])
    
    with analysis_tab1:
        render_sleep_analysis_drilldown(kpi_data, kpis)
    
    with analysis_tab2:
        render_activity_impact_drilldown(kpi_data, kpis)
    
    with analysis_tab3:
        render_pattern_analysis_drilldown(kpi_data, correlations, kpis)
    
    st.divider()
    
    # 6. Dashboard Summary
    st.markdown("## 📋 Dashboard Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        completeness = (1 - kpi_data.isnull().sum().sum() / (len(kpi_data) * len(kpi_data.columns))) * 100
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>Data Quality</h3>
            <p><strong>{completeness:.0f}%</strong> completeness</p>
            <p><strong>{len(df_filtered)}</strong> entries analyzed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col2:
        sig_count = len(correlations.get('significant_correlations', []))
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>Statistical Findings</h3>
            <p><strong>{sig_count}</strong> significant correlations</p>
            <p><strong>{correlations.get('total_tests', 0)}</strong> tests performed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col3:
        avg_confidence = np.mean([
            kpi_data.get('confidence', 0) 
            for kpi_data in kpis.values() 
            if isinstance(kpi_data.get('confidence'), (int, float))
        ])
        
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>KPI Reliability</h3>
            <p><strong>{avg_confidence:.0%}</strong> avg confidence</p>
            <p><strong>{len(kpis)}</strong> KPIs calculated</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <strong>San-Xing Real Data Dashboard</strong> - Powered by your Google Sheets data<br>
        Live integration with Meta-Awareness Log for personalized insights
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
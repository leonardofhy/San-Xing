#!/usr/bin/env python3
"""
Advanced San-Xing Dashboard Demo
Showcases all new UI components with KPI calculations and statistical analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px

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
    create_correlation_heatmap
)
from components.drill_down_views import (
    render_sleep_analysis_drilldown,
    render_activity_impact_drilldown,
    render_pattern_analysis_drilldown
)

# Page configuration
st.set_page_config(
    page_title="San-Xing Advanced Dashboard",
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
</style>
""", unsafe_allow_html=True)

def load_real_data_option() -> pd.DataFrame:
    """Try to load real Google Sheets data if available"""
    try:
        import sys
        from pathlib import Path
        
        # Add parent directory to path
        parent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(parent_dir))
        
        from src.data_processor import DataProcessor
        from src.config import Config
        
        # Load configuration using the proper Config.from_file method
        config_path = parent_dir / "config.local.toml"
        if not config_path.exists():
            return None
            
        config = Config.from_file(config_path)
        
        # Load latest snapshot
        snapshot_path = parent_dir / "data" / "raw" / "snapshot_010f189dd4de4959.json"
        if not snapshot_path.exists():
            return None
        
        # Process data
        processor = DataProcessor(config)
        processor.load_from_snapshot(snapshot_path)
        df = processor.process_all()
        
        # Convert to format expected by KPI calculator
        kpi_data = pd.DataFrame()
        
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
        
        # Filter out rows with all NaN values in key metrics
        key_columns = ['mood', 'energy', 'sleep_quality']
        available_key_columns = [col for col in key_columns if col in kpi_data.columns]
        
        if available_key_columns:
            kpi_data = kpi_data.dropna(subset=available_key_columns, how='all')
        
        return kpi_data if not kpi_data.empty else None
        
    except Exception:
        return None

def create_enhanced_sample_data(days: int = 60) -> pd.DataFrame:
    """Create enhanced sample data with realistic patterns."""
    np.random.seed(42)
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=days, freq='D')
    
    # Create base trends
    trend = np.linspace(0, 0.8, days)  # Slight improving trend
    weekly_pattern = 0.3 * np.sin(2 * np.pi * np.arange(days) / 7)  # Weekly variation
    
    # Generate correlated data
    base_wellbeing = 6.5 + trend + weekly_pattern + np.random.normal(0, 0.8, days)
    
    data = pd.DataFrame({
        'date': dates,
        'mood': np.clip(base_wellbeing + np.random.normal(0, 0.5, days), 1, 10),
        'energy': np.clip(base_wellbeing - 0.5 + np.random.normal(0, 0.6, days), 1, 10),
        'sleep_quality': np.clip(base_wellbeing + 0.3 + np.random.normal(0, 0.4, days), 1, 10),
        'sleep_duration': np.clip(7.5 + 0.3 * trend + np.random.normal(0, 0.8, days), 4, 12),
        'activity_balance': np.random.randint(-3, 4, days),
        'positive_activities': np.random.randint(1, 6, days),
        'negative_activities': np.random.randint(0, 3, days)
    })
    
    # Add some correlation between sleep and mood
    data['mood'] += 0.2 * (data['sleep_quality'] - 7)
    data['mood'] = np.clip(data['mood'], 1, 10)
    
    # Round to realistic precision
    for col in ['mood', 'energy', 'sleep_quality', 'sleep_duration']:
        data[col] = data[col].round(1)
    
    return data

def main():
    """Main dashboard application."""
    
    # Header
    st.markdown('<h1 class="main-header">San-Xing Advanced Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Comprehensive wellbeing analytics with statistical rigor")
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("##  Dashboard Configuration")
        
        # Data source options
        data_source = st.selectbox("Data Source", ["Synthetic Data", "Real Google Sheets Data"])
        
        # Data generation options (only for synthetic)
        if data_source == "Synthetic Data":
            data_days = st.slider("Dataset Size (days)", 14, 90, 60)
        else:
            st.info("Using real data from Google Sheets")
        
        show_raw_data = st.checkbox("Show Raw Data", False)
        
        st.divider()
        
        # Display options
        st.markdown("##  Display Options")
        kpi_layout = st.selectbox("KPI Layout", ["columns", "rows", "grid"], index=0)
        show_confidence_intervals = st.checkbox("Show Confidence Intervals", True)
        show_statistical_details = st.checkbox("Show Statistical Methodology", False)
        
        st.divider()
        
        # Analysis options
        st.markdown("##  Analysis Options")
        correlation_alpha = st.slider("Significance Level (α)", 0.01, 0.10, 0.05, 0.01)
        show_only_significant = st.checkbox("Highlight Only Significant Correlations", False)
    
    # Generate or load data based on selection
    if data_source == "Real Google Sheets Data":
        if 'real_data' not in st.session_state or st.sidebar.button("Reload Real Data"):
            with st.spinner("Loading real data from Google Sheets..."):
                real_data = load_real_data_option()
                if real_data is not None and not real_data.empty:
                    st.session_state.real_data = real_data
                    st.success(f"✓ Loaded {len(real_data)} entries of real data")
                else:
                    st.error("Failed to load real data. Falling back to synthetic data.")
                    st.session_state.real_data = create_enhanced_sample_data(60)
        
        data = st.session_state.get('real_data', create_enhanced_sample_data(60))
        
        # Add data source indicator
        st.markdown("""
        <div style='background: #e8f5e8; padding: 10px; border-radius: 5px; border-left: 4px solid #28a745; margin: 10px 0;'>
            📊 <strong>Real Data Source:</strong> Google Sheets Meta-Awareness Log
        </div>
        """, unsafe_allow_html=True)
        
    else:
        # Synthetic data
        if 'dashboard_data' not in st.session_state or st.sidebar.button("Regenerate Sample Data"):
            with st.spinner("Generating enhanced sample data..."):
                st.session_state.dashboard_data = create_enhanced_sample_data(data_days)
                st.success(f"✓ Generated {data_days} days of sample data")
        
        data = st.session_state.dashboard_data
    
    # Show raw data if requested
    if show_raw_data:
        with st.expander(" Raw Data Preview", expanded=False):
            st.dataframe(data.head(10))
            st.write(f"**Dataset shape:** {data.shape[0]} days × {data.shape[1]} metrics")
            st.write(f"**Date range:** {data['date'].min().date()} to {data['date'].max().date()}")
    
    # Calculate KPIs and statistics
    with st.spinner("Calculating KPIs and statistical analysis..."):
        kpis = KPICalculator.calculate_all_kpis(data)
        correlations = correlation_with_significance(
            data.select_dtypes(include=[np.number]), 
            alpha=correlation_alpha
        )
    
    # === MAIN DASHBOARD SECTIONS ===
    
    # 1. KPI Overview
    st.markdown("##  Key Performance Indicators")
    render_kpi_overview(kpis, layout=kpi_layout)
    
    st.divider()
    
    # 2. Statistical Insights
    render_statistical_insights(
        correlations, 
        show_methodology=show_statistical_details
    )
    
    st.divider()
    
    # 3. Interactive Visualizations
    st.markdown("##  Interactive Visualizations")
    
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Trends", "Correlations", "Distributions"])
    
    with viz_tab1:
        # Trend analysis
        trend_cols = ['mood', 'energy', 'sleep_quality']
        available_cols = [col for col in trend_cols if col in data.columns]
        
        if available_cols:
            trend_chart = create_trend_chart(
                data=data,
                value_columns=available_cols,
                date_column='date',
                title="Wellbeing Metrics Over Time",
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
        numeric_data = data.select_dtypes(include=[np.number])
        if len(numeric_data.columns) > 1:
            render_correlation_matrix(
                data=numeric_data,
                correlation_results=correlations,
                show_only_significant=show_only_significant
            )
    
    with viz_tab3:
        # Distribution analysis
        from components.data_viz import create_statistical_summary_chart
        
        dist_type = st.selectbox("Distribution View", ["box", "violin", "histogram"])
        wellbeing_cols = ['mood', 'energy', 'sleep_quality', 'sleep_duration']
        available_dist_cols = [col for col in wellbeing_cols if col in data.columns]
        
        if available_dist_cols:
            dist_chart = create_statistical_summary_chart(
                data=data,
                columns=available_dist_cols,
                chart_type=dist_type
            )
            st.plotly_chart(dist_chart, use_container_width=True)
    
    st.divider()
    
    # 4. Drill-down Analysis Tabs
    st.markdown("##  Detailed Analysis")
    
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([" Sleep Analysis", " Activity Impact", " Pattern Analysis"])
    
    with analysis_tab1:
        render_sleep_analysis_drilldown(data, kpis)
    
    with analysis_tab2:
        render_activity_impact_drilldown(data, kpis)
    
    with analysis_tab3:
        render_pattern_analysis_drilldown(data, correlations, kpis)
    
    st.divider()
    
    # 5. Dashboard Summary
    st.markdown("##  Dashboard Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.markdown("""
        <div class="metric-highlight">
            <h3> Data Quality</h3>
            <p><strong>{:.0f}%</strong> completeness</p>
            <p><strong>{}</strong> days analyzed</p>
        </div>
        """.format(
            (1 - data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100,
            len(data)
        ), unsafe_allow_html=True)
    
    with summary_col2:
        sig_count = len(correlations.get('significant_correlations', []))
        st.markdown(f"""
        <div class="metric-highlight">
            <h3> Statistical Findings</h3>
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
            <h3> KPI Reliability</h3>
            <p><strong>{avg_confidence:.0%}</strong> avg confidence</p>
            <p><strong>3</strong> KPIs calculated</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
         <strong>San-Xing Advanced Dashboard</strong> - Comprehensive wellbeing analytics with statistical rigor<br>
        Built with KPI Calculator, Statistical Utilities, and Interactive UI Components
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
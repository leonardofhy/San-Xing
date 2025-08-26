#!/usr/bin/env python3
"""
Bulletproof San-Xing Dashboard
Handles all data loading failures gracefully with comprehensive fallbacks
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import our robust data loader
from robust_data_loader import RobustDataLoader, display_data_loading_status, create_fallback_data

# Import analytics modules
from analytics.kpi_calculator import KPICalculator
from analytics.statistical_utils import correlation_with_significance

# Import UI components
from components.kpi_cards import render_kpi_overview
from components.insight_display import render_statistical_insights
from components.data_viz import (
    create_trend_chart,
    create_kpi_gauge,
    create_statistical_summary_chart
)
from components.drill_down_views import (
    render_sleep_analysis_drilldown,
    render_activity_impact_drilldown,
    render_pattern_analysis_drilldown
)

# Page configuration
st.set_page_config(
    page_title="San-Xing Bulletproof Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    
    .data-source-success {
        background: #e8f5e8;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    
    .data-source-fallback {
        background: #fff3e0;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ff9800;
        margin: 10px 0;
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

def main():
    """Main dashboard application with bulletproof data loading"""
    
    # Header
    st.markdown('<h1 class="main-header">🛡️ San-Xing Bulletproof Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Reliable wellbeing analytics with robust data handling")
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("## 🔧 Dashboard Configuration")
        
        # Data loading options
        st.markdown("### 📊 Data Source")
        force_fallback = st.checkbox("Force Synthetic Data (for testing)")
        
        if not force_fallback:
            st.info("Will attempt to load real Google Sheets data first")
        else:
            st.warning("Using synthetic data only")
        
        st.divider()
        
        # Display options
        st.markdown("### 🎨 Display Options")
        kpi_layout = st.selectbox("KPI Layout", ["columns", "rows", "grid"], index=0)
        show_raw_data = st.checkbox("Show Raw Data Preview", False)
        show_statistical_details = st.checkbox("Show Statistical Methodology", False)
        
        st.divider()
        
        # Analysis options
        st.markdown("### 📈 Analysis Options")
        correlation_alpha = st.slider("Significance Level (α)", 0.01, 0.10, 0.05, 0.01)
        show_only_significant = st.checkbox("Highlight Only Significant Correlations", False)
        
        st.divider()
        
        # Data refresh
        if st.button("🔄 Reload Data"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    # === DATA LOADING WITH ROBUST FALLBACK ===
    
    data_source_type = "unknown"
    kpi_data = None
    data_info = None
    
    if force_fallback:
        # Use synthetic data
        st.markdown("""
        <div class="data-source-fallback">
            ⚠️ <strong>Synthetic Data Mode:</strong> Using generated sample data for demonstration
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("Generating synthetic data..."):
            kpi_data = create_fallback_data(60)
            data_source_type = "synthetic"
        
        st.success(f"✅ Generated {len(kpi_data)} days of synthetic data")
    
    else:
        # Try to load real data first
        try:
            kpi_data, data_info = display_data_loading_status()
            
            if kpi_data is not None:
                # Real data loaded successfully
                st.markdown("""
                <div class="data-source-success">
                    ✅ <strong>Real Data Source:</strong> Google Sheets Meta-Awareness Log
                </div>
                """, unsafe_allow_html=True)
                data_source_type = "real"
            
            else:
                # Real data failed, use fallback
                st.warning("Real data loading failed. Using synthetic data as fallback.")
                st.markdown("""
                <div class="data-source-fallback">
                    🔄 <strong>Fallback Mode:</strong> Using synthetic data due to loading issues
                </div>
                """, unsafe_allow_html=True)
                
                with st.spinner("Generating fallback data..."):
                    kpi_data = create_fallback_data(60)
                    data_source_type = "fallback"
        
        except Exception as e:
            # Complete failure, use fallback
            st.error(f"Unexpected error during data loading: {e}")
            st.markdown("""
            <div class="data-source-fallback">
                🚨 <strong>Emergency Fallback:</strong> Using synthetic data due to system error
            </div>
            """, unsafe_allow_html=True)
            
            kpi_data = create_fallback_data(60)
            data_source_type = "emergency"
    
    # Ensure we have data at this point
    if kpi_data is None or kpi_data.empty:
        st.error("❌ Complete data loading failure. Cannot proceed.")
        st.stop()
    
    # Show data source information
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Data Source", data_source_type.title())
    
    with col2:
        st.metric("Total Entries", len(kpi_data))
    
    with col3:
        if 'date' in kpi_data.columns:
            try:
                date_range = f"{kpi_data['date'].min().strftime('%m-%d')} to {kpi_data['date'].max().strftime('%m-%d')}"
                st.metric("Date Range", date_range)
            except Exception:
                st.metric("Date Range", "N/A")
        else:
            st.metric("Date Range", "N/A")
    
    with col4:
        # Calculate data completeness
        numeric_cols = kpi_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            completeness = (1 - kpi_data[numeric_cols].isnull().sum().sum() / (len(kpi_data) * len(numeric_cols))) * 100
            st.metric("Completeness", f"{completeness:.0f}%")
        else:
            st.metric("Completeness", "N/A")
    
    # Show raw data preview if requested
    if show_raw_data:
        with st.expander("📋 Raw Data Preview", expanded=False):
            st.dataframe(kpi_data.head(20))
            st.write(f"**Dataset shape:** {kpi_data.shape[0]} entries × {kpi_data.shape[1]} columns")
            
            # Show column info
            st.write("**Column Information:**")
            for col in kpi_data.columns:
                non_null_count = kpi_data[col].count()
                st.write(f"- {col}: {non_null_count}/{len(kpi_data)} non-null ({non_null_count/len(kpi_data)*100:.0f}%)")
    
    # === ANALYTICS PROCESSING ===
    
    with st.spinner("Calculating KPIs and statistical analysis..."):
        try:
            # Calculate KPIs
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
            st.error(f"Analytics calculation failed: {e}")
            # Use minimal analytics as fallback
            kpis = {}
            correlations = {'significant_correlations': [], 'all_correlations': {}, 'total_tests': 0}
    
    st.success(f"✅ Analytics completed: {len(kpis)} KPIs calculated")
    
    # === MAIN DASHBOARD SECTIONS ===
    
    # 1. KPI Overview
    if kpis:
        st.markdown("## 📊 Key Performance Indicators")
        render_kpi_overview(kpis, layout=kpi_layout)
        st.divider()
    
    # 2. Statistical Insights
    if len(numeric_cols.columns) > 1:
        render_statistical_insights(
            correlations, 
            show_methodology=show_statistical_details
        )
        st.divider()
    
    # 3. Interactive Visualizations
    st.markdown("## 📈 Interactive Visualizations")
    
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Trends", "Correlations", "Distributions"])
    
    with viz_tab1:
        # Trend analysis
        trend_cols = ['mood', 'energy', 'sleep_quality']
        available_cols = [col for col in trend_cols if col in kpi_data.columns and not kpi_data[col].isna().all()]
        
        if available_cols:
            try:
                trend_chart = create_trend_chart(
                    data=kpi_data,
                    value_columns=available_cols,
                    date_column='date',
                    title=f"Wellbeing Metrics Over Time ({data_source_type.title()} Data)",
                    show_trend_lines=True
                )
                st.plotly_chart(trend_chart, use_container_width=True)
            except Exception as e:
                st.error(f"Trend chart failed: {e}")
        else:
            st.info("No trend data available for visualization")
        
        # Individual KPI gauges
        if kpis:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'wellbeing_score' in kpis:
                    try:
                        gauge_fig = create_kpi_gauge(
                            value=kpis['wellbeing_score']['score'],
                            max_value=10,
                            title="Wellbeing Score",
                            color_scheme="blue"
                        )
                        st.plotly_chart(gauge_fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Wellbeing gauge failed: {e}")
            
            with col2:
                if 'balance_index' in kpis:
                    try:
                        gauge_fig = create_kpi_gauge(
                            value=kpis['balance_index']['index'],
                            max_value=100,
                            title="Balance Index (%)",
                            color_scheme="green"
                        )
                        st.plotly_chart(gauge_fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Balance gauge failed: {e}")
            
            with col3:
                if 'trend_indicator' in kpis:
                    try:
                        confidence_map = {'high': 0.9, 'medium': 0.6, 'low': 0.3}
                        confidence_val = confidence_map.get(kpis['trend_indicator']['confidence'], 0.3)
                        
                        gauge_fig = create_kpi_gauge(
                            value=confidence_val,
                            max_value=1.0,
                            title="Trend Confidence",
                            color_scheme="purple"
                        )
                        st.plotly_chart(gauge_fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Trend gauge failed: {e}")
    
    with viz_tab2:
        # Correlation analysis
        if len(numeric_cols.columns) > 1:
            try:
                from components.insight_display import render_correlation_matrix
                render_correlation_matrix(
                    data=numeric_cols,
                    correlation_results=correlations,
                    show_only_significant=show_only_significant
                )
            except Exception as e:
                st.error(f"Correlation matrix failed: {e}")
        else:
            st.info("Need at least 2 numeric variables for correlation analysis")
    
    with viz_tab3:
        # Distribution analysis
        try:
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
        except Exception as e:
            st.error(f"Distribution analysis failed: {e}")
    
    st.divider()
    
    # 4. Drill-down Analysis (with error handling)
    st.markdown("## 🔍 Detailed Analysis")
    
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["Sleep Analysis", "Activity Impact", "Pattern Analysis"])
    
    with analysis_tab1:
        try:
            render_sleep_analysis_drilldown(kpi_data, kpis)
        except Exception as e:
            st.error(f"Sleep analysis failed: {e}")
    
    with analysis_tab2:
        try:
            render_activity_impact_drilldown(kpi_data, kpis)
        except Exception as e:
            st.error(f"Activity analysis failed: {e}")
    
    with analysis_tab3:
        try:
            render_pattern_analysis_drilldown(kpi_data, correlations, kpis)
        except Exception as e:
            st.error(f"Pattern analysis failed: {e}")
    
    st.divider()
    
    # 5. Dashboard Summary
    st.markdown("## 📋 Dashboard Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        completeness = (1 - kpi_data.isnull().sum().sum() / (len(kpi_data) * len(kpi_data.columns))) * 100 if not kpi_data.empty else 0
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>Data Quality</h3>
            <p><strong>{completeness:.0f}%</strong> completeness</p>
            <p><strong>{len(kpi_data)}</strong> entries analyzed</p>
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
        data_source_desc = {
            "real": "Live Google Sheets",
            "synthetic": "Generated Sample",
            "fallback": "Backup Data",
            "emergency": "Emergency Backup"
        }.get(data_source_type, "Unknown")
        
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>Data Source</h3>
            <p><strong>{data_source_desc}</strong></p>
            <p><strong>{len(kpis)}</strong> KPIs calculated</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666; padding: 20px;'>
        🛡️ <strong>San-Xing Bulletproof Dashboard</strong> - Reliable wellbeing analytics<br>
        Data Source: {data_source_desc} | Robust error handling ensures dashboard always works
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Example: Integrating KPI Calculator with Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import our new analytics modules
from analytics.kpi_calculator import KPICalculator
from analytics.statistical_utils import correlation_with_significance

def create_kpi_section(data: pd.DataFrame):
    """Create KPI section for dashboard."""
    st.header("📊 Key Performance Indicators")
    
    # Calculate KPIs
    kpis = KPICalculator.calculate_all_kpis(data)
    
    # Create three columns for KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        wellbeing = kpis['wellbeing_score']
        st.metric(
            label="🌟 Wellbeing Score", 
            value=f"{wellbeing['score']}/10",
            help=f"Confidence: {wellbeing['confidence']:.2f} | Trend: {wellbeing['trend']}"
        )
        
        # Progress bar
        progress = wellbeing['score'] / 10
        st.progress(progress)
        
        # Components breakdown
        if wellbeing['components']:
            st.write("**Components:**")
            for comp, values in wellbeing['components'].items():
                st.write(f"• {comp.title()}: {values['mean']:.1f}")
    
    with col2:
        balance = kpis['balance_index']
        st.metric(
            label="⚖️ Balance Index",
            value=f"{balance['index']:.1f}%",
            help=f"Confidence: {balance['confidence']:.2f}"
        )
        
        # Progress bar
        progress = balance['index'] / 100
        st.progress(progress)
        
        # Components
        st.write("**Components:**")
        st.write(f"• Activity: {balance['activity_component']:.1%}")
        st.write(f"• Sleep: {balance['sleep_component']:.1%}")
    
    with col3:
        trend = kpis['trend_indicator']
        
        # Color coding for trend
        trend_color = {
            'improving': '🟢',
            'stable': '🟡', 
            'declining': '🔴'
        }
        
        st.metric(
            label="📈 Trend Indicator",
            value=f"{trend_color[trend['direction']]} {trend['direction'].title()}",
            help=f"Confidence: {trend['confidence']} | Magnitude: {trend['magnitude']:.3f}"
        )
        
        # Trend details
        st.write(f"**7-day trend analysis:**")
        st.write(f"• Direction: {trend['direction']}")
        st.write(f"• Magnitude: {trend['magnitude']:.3f}/day")
        st.write(f"• Sample: {trend['sample_size']} days")

def create_stats_section(data: pd.DataFrame):
    """Create statistical analysis section."""
    st.header("🔬 Statistical Analysis")
    
    # Correlation analysis
    numeric_data = data.select_dtypes(include=[np.number])
    if len(numeric_data.columns) > 1:
        correlations = correlation_with_significance(numeric_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Significant Correlations")
            if correlations['significant_correlations']:
                for corr in correlations['significant_correlations']:
                    st.write(f"**{corr['variable_1']} ↔ {corr['variable_2']}**")
                    st.write(f"• Correlation: {corr['correlation']:.3f}")
                    st.write(f"• p-value: {corr['p_value']:.4f}")
                    st.write(f"• Sample: {corr['sample_size']}")
                    st.write("---")
            else:
                st.info("No statistically significant correlations found.")
        
        with col2:
            st.subheader("Analysis Summary")
            st.write(f"**Total tests:** {correlations['total_tests']}")
            st.write(f"**Alpha level:** {correlations['alpha_level']}")
            st.write(f"**Corrected α:** {correlations['corrected_alpha']:.4f}")
            st.write(f"**Significant pairs:** {len(correlations['significant_correlations'])}")

def main():
    """Main dashboard function."""
    st.title("🌟 San-Xing KPI Dashboard")
    st.write("Advanced analytics with statistical rigor")
    
    # Create sample data for demo
    if st.button("Generate Sample Data"):
        np.random.seed(42)
        dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
        
        data = pd.DataFrame({
            'date': dates,
            'mood': np.random.normal(6.5, 1.5, 30).clip(1, 10).round(1),
            'energy': np.random.normal(6.0, 1.2, 30).clip(1, 10).round(1),
            'sleep_quality': np.random.normal(7.0, 1.0, 30).clip(1, 10).round(1),
            'sleep_duration': np.random.normal(7.5, 0.8, 30).clip(4, 12).round(1),
            'activity_balance': np.random.randint(-3, 4, 30)
        })
        
        # Store in session state
        st.session_state['demo_data'] = data
        st.success("✅ Sample data generated!")
    
    # Check if data exists
    if 'demo_data' in st.session_state:
        data = st.session_state['demo_data']
        
        # Show data overview
        with st.expander("📊 Data Overview", expanded=False):
            st.dataframe(data.head(10))
            st.write(f"**Shape:** {data.shape[0]} days × {data.shape[1]} metrics")
        
        # KPI Section
        create_kpi_section(data)
        
        st.divider()
        
        # Statistics Section
        create_stats_section(data)
        
    else:
        st.info("👆 Click 'Generate Sample Data' to see the KPI dashboard in action!")
        
        # Show implementation info
        st.subheader("🔧 Implementation Status")
        st.success("✅ KPI Calculator: Ready")
        st.success("✅ Statistical Utils: Ready") 
        st.success("✅ Dashboard Integration: Ready")
        
        st.subheader("📚 Available KPIs")
        st.write("""
        1. **Wellbeing Score** (0-10): Composite of mood, energy, and sleep quality
           - Formula: mood(40%) + energy(40%) + sleep_quality(20%)
           - Includes confidence levels and trend analysis
        
        2. **Balance Index** (0-100%): Activity balance and sleep goal achievement
           - Formula: activity_balance(60%) + sleep_target(40%)
           - Sleep target: 7-8 hours per night
        
        3. **Trend Indicator**: 7-day statistical trend analysis
           - Uses linear regression on recent wellbeing scores
           - Confidence based on sample size and trend strength
        """)

if __name__ == "__main__":
    main()
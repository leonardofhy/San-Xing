"""KPI Card Components for San-Xing Dashboard.

This module provides reusable Streamlit components for displaying
Key Performance Indicators with professional styling and interactivity.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional


def _get_confidence_color(confidence: float) -> str:
    """Get color based on confidence level."""
    if confidence >= 0.8:
        return "#28a745"  # Green
    elif confidence >= 0.5:
        return "#ffc107"  # Yellow
    else:
        return "#dc3545"  # Red


def _get_trend_icon(trend: str) -> str:
    """Get icon for trend direction."""
    icons = {
        'improving': '↑',
        'stable': '→', 
        'declining': '↓'
    }
    return icons.get(trend, '→')


def _create_gauge_chart(value: float, max_value: float, title: str, 
                       color: str = "#1f77b4") -> go.Figure:
    """Create a gauge chart for KPI display."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [None, max_value], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, max_value * 0.3], 'color': "#ffebee"},
                {'range': [max_value * 0.3, max_value * 0.7], 'color': "#fff3e0"},
                {'range': [max_value * 0.7, max_value], 'color': "#e8f5e8"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig


def render_wellbeing_card(wellbeing_data: Dict[str, Any], 
                         show_details: bool = True) -> None:
    """Render wellbeing score KPI card.
    
    Args:
        wellbeing_data: Dictionary from KPICalculator.calculate_wellbeing_score()
        show_details: Whether to show component breakdown
    """
    score = wellbeing_data.get('score', 0.0)
    confidence = wellbeing_data.get('confidence', 0.0)
    trend = wellbeing_data.get('trend', 'stable')
    components = wellbeing_data.get('components', {})
    sample_size = wellbeing_data.get('sample_size', 0)
    
    # Simple card display
    with st.container():
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        '>
            <h3 style='margin: 0 0 15px 0; color: white; font-weight: 600;'>Wellbeing Score</h3>
            <h1 style='margin: 0 0 10px 0; font-size: 3.5em; color: white; font-weight: 700;'>
                {score:.1f}<span style='font-size: 0.4em; opacity: 0.8;'>/10</span>
            </h1>
            <p style='margin: 0; opacity: 0.9; font-size: 0.95em;'>
                {_get_trend_icon(trend)} {trend.title()} • 
                {confidence:.0%} confidence • 
                {sample_size} days
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Component breakdown (collapsible)
        if show_details and components:
            with st.expander("Component Breakdown", expanded=False):
                comp_cols = st.columns(len(components))
                
                for i, (comp_name, comp_data) in enumerate(components.items()):
                    with comp_cols[i]:
                        mean_val = comp_data.get('mean', 0.0)
                        count = comp_data.get('count', 0)
                        
                        st.metric(
                            label=comp_name.replace('_', ' ').title(),
                            value=f"{mean_val:.1f}",
                            help=f"Based on {count} entries"
                        )
                        
                        # Mini progress bar
                        progress = mean_val / 10
                        st.progress(progress)


def render_balance_card(balance_data: Dict[str, Any], 
                       show_details: bool = True) -> None:
    """Render balance index KPI card.
    
    Args:
        balance_data: Dictionary from KPICalculator.calculate_balance_index()
        show_details: Whether to show component breakdown
    """
    index = balance_data.get('index', 0.0)
    confidence = balance_data.get('confidence', 0.0)
    activity_component = balance_data.get('activity_component', 0.0)
    sleep_component = balance_data.get('sleep_component', 0.0)
    sample_size = balance_data.get('sample_size', 0)
    
    # Simple card display
    with st.container():
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        '>
            <h3 style='margin: 0 0 15px 0; color: white; font-weight: 600;'>Balance Index</h3>
            <h1 style='margin: 0 0 10px 0; font-size: 3.5em; color: white; font-weight: 700;'>
                {index:.1f}<span style='font-size: 0.4em; opacity: 0.8;'>%</span>
            </h1>
            <p style='margin: 0; opacity: 0.9; font-size: 0.95em;'>
                {confidence:.0%} confidence • 
                {sample_size} days
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Component breakdown
        if show_details:
            with st.expander("Balance Components", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        label="Activity Balance",
                        value=f"{activity_component:.1%}",
                        help="Activity variety and balance (60% weight)"
                    )
                    st.progress(activity_component)
                
                with col2:
                    st.metric(
                        label="Sleep Target Achievement", 
                        value=f"{sleep_component:.1%}",
                        help="Nights with 7-8 hours sleep (40% weight)"
                    )
                    st.progress(sleep_component)


def render_trend_card(trend_data: Dict[str, Any], 
                     show_details: bool = True) -> None:
    """Render trend indicator KPI card.
    
    Args:
        trend_data: Dictionary from KPICalculator.calculate_trend_indicator()
        show_details: Whether to show trend analysis details
    """
    direction = trend_data.get('direction', 'stable')
    magnitude = trend_data.get('magnitude', 0.0)
    confidence = trend_data.get('confidence', 'low')
    sample_size = trend_data.get('sample_size', 0)
    significance = trend_data.get('significance', 1.0)
    
    # Color based on direction
    direction_colors = {
        'improving': '#28a745',
        'stable': '#6c757d',
        'declining': '#dc3545'
    }
    
    card_color = direction_colors.get(direction, '#6c757d')
    
    # Simple card display
    with st.container():
        trend_icon = _get_trend_icon(direction)
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, {card_color} 0%, {card_color}dd 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        '>
            <h3 style='margin: 0 0 15px 0; color: white; font-weight: 600;'>Trend Indicator</h3>
            <h1 style='margin: 0 0 10px 0; font-size: 2.8em; color: white; font-weight: 700;'>
                {trend_icon} {direction.title()}
            </h1>
            <p style='margin: 0; opacity: 0.9; font-size: 0.95em;'>
                {magnitude:+.3f}/day • 
                {confidence} confidence • 
                {sample_size} days
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Trend analysis details
        if show_details:
            with st.expander("Trend Analysis Details", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="Direction",
                        value=direction.title(),
                        help="7-day trend direction"
                    )
                
                with col2:
                    st.metric(
                        label="Daily Change",
                        value=f"{magnitude:+.3f}",
                        help="Average change per day"
                    )
                
                with col3:
                    st.metric(
                        label="Statistical Power",
                        value=confidence.title(),
                        help=f"Based on {sample_size} data points"
                    )


def render_kpi_overview(kpi_results: Dict[str, Dict[str, Any]], 
                       layout: str = "columns") -> None:
    """Render overview of all KPIs in specified layout.
    
    Args:
        kpi_results: Dictionary from KPICalculator.calculate_all_kpis()
        layout: Layout style ('columns', 'rows', 'grid')
    """
    if not kpi_results:
        st.warning("No KPI data available")
        return
    
    st.markdown("## KPI Overview")
    
    if layout == "columns":
        # Three column layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'wellbeing_score' in kpi_results:
                render_wellbeing_card(kpi_results['wellbeing_score'], show_details=False)
        
        with col2:
            if 'balance_index' in kpi_results:
                render_balance_card(kpi_results['balance_index'], show_details=False)
        
        with col3:
            if 'trend_indicator' in kpi_results:
                render_trend_card(kpi_results['trend_indicator'], show_details=False)
    
    elif layout == "rows":
        # Stacked row layout
        if 'wellbeing_score' in kpi_results:
            render_wellbeing_card(kpi_results['wellbeing_score'])
        
        if 'balance_index' in kpi_results:
            render_balance_card(kpi_results['balance_index'])
        
        if 'trend_indicator' in kpi_results:
            render_trend_card(kpi_results['trend_indicator'])
    
    elif layout == "grid":
        # 2x2 grid with summary
        col1, col2 = st.columns(2)
        
        with col1:
            if 'wellbeing_score' in kpi_results:
                render_wellbeing_card(kpi_results['wellbeing_score'], show_details=False)
            
            if 'balance_index' in kpi_results:
                render_balance_card(kpi_results['balance_index'], show_details=False)
        
        with col2:
            if 'trend_indicator' in kpi_results:
                render_trend_card(kpi_results['trend_indicator'], show_details=False)
            
            # Summary stats
            _render_kpi_summary(kpi_results)
    
    else:
        st.error(f"Unknown layout: {layout}")


def _render_kpi_summary(kpi_results: Dict[str, Dict[str, Any]]) -> None:
    """Render KPI summary statistics."""
    st.markdown("""
    <div style='
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
    '>
    """, unsafe_allow_html=True)
    
    st.markdown("### Summary")
    
    # Calculate summary metrics
    total_sample_size = 0
    avg_confidence = 0
    kpi_count = 0
    
    for kpi_name, kpi_data in kpi_results.items():
        if 'sample_size' in kpi_data:
            total_sample_size = max(total_sample_size, kpi_data['sample_size'])
        
        if 'confidence' in kpi_data:
            confidence_val = kpi_data['confidence']
            if isinstance(confidence_val, (int, float)):
                avg_confidence += confidence_val
                kpi_count += 1
    
    if kpi_count > 0:
        avg_confidence /= kpi_count
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Data Points", f"{total_sample_size} days")
    
    with col2:
        st.metric("Avg. Confidence", f"{avg_confidence:.0%}")
    
    st.markdown("</div>", unsafe_allow_html=True)
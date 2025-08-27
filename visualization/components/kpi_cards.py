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
        
        # Explanation section
        with st.expander("ℹ️ What is Wellbeing Score?", expanded=False):
            st.markdown("""
            **Wellbeing Score** combines your daily mood and energy levels into a single score (0-10).
            
            **How it works:**
            - Takes your daily mood and energy ratings
            - Calculates weighted average (higher = better wellbeing)
            - Considers data consistency and sample size
            
            **Score ranges:**
            - 🟢 **8-10**: Excellent wellbeing
            - 🟡 **6-8**: Good wellbeing  
            - 🟠 **4-6**: Moderate wellbeing
            - 🔴 **0-4**: Needs attention
            
            This helps you track your overall mental and physical state over time.
            """)
        
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
        
        # Explanation section
        with st.expander("ℹ️ What is Balance Index?", expanded=False):
            st.markdown("""
            **Balance Index** measures how well you're balancing different aspects of your life (0-100%).
            
            **How it works:**
            - Analyzes your daily activities (positive vs. negative)
            - Considers sleep consistency (7-9 hours target)
            - Weighted formula: 60% activities + 40% sleep habits
            
            **Score ranges:**
            - 🟢 **80-100%**: Excellent life balance
            - 🟡 **60-80%**: Good balance with room for improvement
            - 🟠 **40-60%**: Moderate balance, focus needed  
            - 🔴 **0-40%**: Significant imbalance, needs attention
            
            Higher scores indicate better balance between healthy activities and sleep habits.
            """)
        
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


def render_sleep_quality_card(sleep_data: Dict[str, Any], 
                             show_details: bool = True) -> None:
    """Render sleep quality analysis KPI card.
    
    Args:
        sleep_data: Dictionary from KPICalculator.calculate_sleep_quality_analysis()
        show_details: Whether to show component breakdown
    """
    if 'error' in sleep_data:
        st.warning(f"Sleep Quality: {sleep_data['error']}")
        return
    
    subjective_avg = sleep_data.get('subjective_avg')
    objective_data = sleep_data.get('objective_quality', {})
    
    # Handle both error cases and normal structure
    if isinstance(objective_data, dict) and 'error' in objective_data:
        # Show a more user-friendly message
        error_msg = objective_data['error']
        if 'Missing required columns' in error_msg:
            friendly_msg = "Sleep timing data not available for objective analysis"
        elif 'Insufficient valid sleep timing data' in error_msg:
            friendly_msg = "Need more sleep timing entries for objective analysis"
        else:
            friendly_msg = error_msg
            
        # Still show subjective data if available
        if subjective_avg is not None:
            st.markdown(f"""
            <div style='
                background: linear-gradient(135deg, #6f42c1 0%, #6f42c1dd 100%);
                padding: 25px;
                border-radius: 15px;
                color: white;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            '>
                <h3 style='margin: 0 0 15px 0; color: white; font-weight: 600;'>Sleep Quality</h3>
                <h1 style='margin: 0 0 10px 0; font-size: 3.5em; color: white; font-weight: 700;'>
                    {subjective_avg:.1f}<span style='font-size: 0.4em; opacity: 0.8;'>/5</span>
                </h1>
                <p style='margin: 0; opacity: 0.9; font-size: 0.95em;'>
                    Subjective Rating Only
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("ℹ️ About Sleep Quality", expanded=False):
                st.info(f"💡 {friendly_msg}")
                st.markdown("""
                **Sleep Quality** measures how well you sleep. Currently showing your **subjective rating** (1-5):
                
                **What this means:**
                - Based on your daily self-assessment of sleep quality
                - Reflects how rested and satisfied you feel
                - Higher scores = better perceived sleep quality
                
                **Score ranges:**
                - 🟢 **4-5**: Excellent - you feel well-rested
                - 🟡 **3-4**: Good - generally satisfied with sleep  
                - 🟠 **2-3**: Fair - sometimes tired, room for improvement
                - 🔴 **1-2**: Poor - often tired, needs attention
                
                **For objective analysis, we also need:**
                - Sleep bedtime data 📅
                - Wake up time data ⏰
                - At least 7 days of complete records
                
                This would add scientific analysis based on circadian rhythms and sleep timing.
                """)
        return
    
    objective_quality = objective_data.get('objective_sleep_quality')
    correlation = sleep_data.get('comparison', {}).get('correlation')
    sample_size = objective_data.get('metrics', {}).get('sample_size', 0)
    
    # Determine primary display value and color
    if objective_quality is not None:
        primary_score = objective_quality
        score_type = "Objective"
        if primary_score >= 4.0:
            card_color = "#28a745"  # Green
        elif primary_score >= 3.0:
            card_color = "#ffc107"  # Yellow
        else:
            card_color = "#dc3545"  # Red
    elif subjective_avg is not None:
        primary_score = subjective_avg
        score_type = "Subjective"
        card_color = "#6f42c1"  # Purple
    else:
        st.warning("No sleep quality data available")
        return
    
    # Simple card display
    with st.container():
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
            <h3 style='margin: 0 0 15px 0; color: white; font-weight: 600;'>Sleep Quality</h3>
            <h1 style='margin: 0 0 10px 0; font-size: 3.5em; color: white; font-weight: 700;'>
                {primary_score:.1f}<span style='font-size: 0.4em; opacity: 0.8;'>/5</span>
            </h1>
            <p style='margin: 0; opacity: 0.9; font-size: 0.95em;'>
                {score_type} Rating • 
                {sample_size} nights analyzed
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Explanation section
        with st.expander("ℹ️ What is Sleep Quality?", expanded=False):
            st.markdown("""
            **Sleep Quality** measures how well you sleep using two different approaches:
            
            **Subjective Rating (1-5):**
            - How YOU feel about your sleep quality
            - Based on your daily self-assessment
            - Considers factors like restfulness and satisfaction
            
            **Objective Score (1-5):**
            - Calculated from your sleep timing patterns
            - Based on circadian rhythm science
            - Considers 4 key components:
              - **Duration**: 7-9 hours is optimal
              - **Timing**: Bedtime 10 PM-12 AM, wake 6-8 AM
              - **Regularity**: Consistent sleep schedule
              - **Efficiency**: Weekend vs. weekday patterns
            
            **Score ranges:**
            - 🟢 **4-5**: Excellent sleep quality
            - 🟡 **3-4**: Good sleep quality
            - 🟠 **2-3**: Fair sleep quality (room for improvement)
            - 🔴 **1-2**: Poor sleep quality (needs attention)
            
            **Agreement**: How well your feelings match the objective patterns.
            """)
        
        # Component breakdown
        if show_details:
            with st.expander("Sleep Quality Analysis", expanded=False):
                if subjective_avg is not None and objective_quality is not None:
                    # Show comparison
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            label="Subjective Rating",
                            value=f"{subjective_avg:.1f}/5",
                            help="How you rated your sleep quality"
                        )
                    
                    with col2:
                        st.metric(
                            label="Objective Score", 
                            value=f"{objective_quality:.1f}/5",
                            help="Based on sleep timing patterns"
                        )
                    
                    with col3:
                        if correlation is not None:
                            correlation_desc = "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.3 else "Weak"
                            st.metric(
                                label="Agreement",
                                value=correlation_desc,
                                help=f"Correlation: {correlation:.3f}"
                            )
                        else:
                            st.metric(
                                label="Agreement",
                                value="N/A",
                                help="Not enough data for correlation"
                            )
                    
                    # Show objective components if available
                    obj_components = sleep_data.get('objective_quality', {}).get('components', {})
                    if obj_components:
                        st.markdown("**Objective Quality Components:**")
                        comp_cols = st.columns(len(obj_components))
                        
                        for i, (comp_name, comp_score) in enumerate(obj_components.items()):
                            with comp_cols[i]:
                                clean_name = comp_name.replace('_score', '').replace('_', ' ').title()
                                st.metric(
                                    label=clean_name,
                                    value=f"{comp_score:.2f}",
                                    help=f"Component score (0-1 scale)"
                                )
                                st.progress(comp_score)
                
                else:
                    # Show single rating
                    if subjective_avg is not None:
                        st.metric("Average Subjective Rating", f"{subjective_avg:.1f}/5")
                    if objective_quality is not None:
                        st.metric("Objective Quality Score", f"{objective_quality:.1f}/5")


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
        
        # Explanation section
        with st.expander("ℹ️ What is Trend Indicator?", expanded=False):
            st.markdown("""
            **Trend Indicator** shows whether your wellbeing is improving, stable, or declining over recent days.
            
            **How it works:**
            - Analyzes your wellbeing score changes over the past 7 days
            - Uses Mann-Kendall statistical test to detect genuine trends
            - Shows daily change rate and confidence level
            
            **Trend directions:**
            - 🟢 **↑ Improving**: Your wellbeing is getting better over time
            - 🟡 **→ Stable**: Your wellbeing is consistent (no significant change)
            - 🔴 **↓ Declining**: Your wellbeing is decreasing (needs attention)
            
            **Confidence levels:**
            - **High**: Strong statistical evidence of trend
            - **Medium**: Moderate evidence of trend  
            - **Low**: Weak evidence, trend may not be significant
            
            This helps you understand the direction your mental health is heading.
            """)
        
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
        # Four column layout to include sleep quality
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'wellbeing_score' in kpi_results:
                render_wellbeing_card(kpi_results['wellbeing_score'], show_details=False)
        
        with col2:
            if 'balance_index' in kpi_results:
                render_balance_card(kpi_results['balance_index'], show_details=False)
        
        with col3:
            if 'trend_indicator' in kpi_results:
                render_trend_card(kpi_results['trend_indicator'], show_details=False)
        
        with col4:
            if 'sleep_quality_analysis' in kpi_results:
                render_sleep_quality_card(kpi_results['sleep_quality_analysis'], show_details=False)
    
    elif layout == "rows":
        # Stacked row layout
        if 'wellbeing_score' in kpi_results:
            render_wellbeing_card(kpi_results['wellbeing_score'])
        
        if 'balance_index' in kpi_results:
            render_balance_card(kpi_results['balance_index'])
        
        if 'trend_indicator' in kpi_results:
            render_trend_card(kpi_results['trend_indicator'])
        
        if 'sleep_quality_analysis' in kpi_results:
            render_sleep_quality_card(kpi_results['sleep_quality_analysis'])
    
    elif layout == "grid":
        # 2x2 grid with sleep quality and summary
        col1, col2 = st.columns(2)
        
        with col1:
            if 'wellbeing_score' in kpi_results:
                render_wellbeing_card(kpi_results['wellbeing_score'], show_details=False)
            
            if 'balance_index' in kpi_results:
                render_balance_card(kpi_results['balance_index'], show_details=False)
        
        with col2:
            if 'trend_indicator' in kpi_results:
                render_trend_card(kpi_results['trend_indicator'], show_details=False)
            
            if 'sleep_quality_analysis' in kpi_results:
                render_sleep_quality_card(kpi_results['sleep_quality_analysis'], show_details=False)
        
        # Summary row
        st.markdown("---")
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
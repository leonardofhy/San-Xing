"""Enhanced KPI Grid Component for San-Xing Dashboard.

This module provides the new unified KPI grid layout with progressive disclosure
and improved visual hierarchy for Phase 1 UI redesign.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional


def _get_kpi_color(value: float, max_value: float, kpi_type: str) -> str:
    """Get color for KPI based on value and type."""
    percentage = value / max_value
    
    if kpi_type == 'wellbeing':
        if percentage >= 0.8: return "#2E86AB"  # Excellent - Blue
        elif percentage >= 0.6: return "#F18F01"  # Good - Orange
        else: return "#C73E1D"  # Needs attention - Red
    elif kpi_type == 'balance':
        if percentage >= 0.8: return "#2E86AB"
        elif percentage >= 0.6: return "#F18F01" 
        else: return "#C73E1D"
    elif kpi_type == 'sleep':
        if value >= 4.0: return "#2E86AB"
        elif value >= 3.0: return "#F18F01"
        else: return "#C73E1D"
    else:
        return "#2E86AB"


def _get_trend_display(trend_data: Dict[str, Any]) -> tuple:
    """Get trend icon and color for display."""
    trend = trend_data.get('trend', 'stable')
    change = trend_data.get('change', 0.0)
    confidence = trend_data.get('confidence', 'medium')
    
    icons = {'improving': '↗', 'stable': '→', 'declining': '↘'}
    colors = {'improving': '#2E86AB', 'stable': '#F18F01', 'declining': '#C73E1D'}
    
    icon = icons.get(trend, '→')
    color = colors.get(trend, '#F18F01')
    
    if abs(change) > 0.1:
        change_text = f"{change:+.1f}"
    else:
        change_text = "Stable"
        
    return icon, color, change_text, confidence


def render_kpi_card_enhanced(title: str, value: str, subtitle: str = "", 
                           trend_data: Optional[Dict[str, Any]] = None,
                           color: str = "#2E86AB",
                           explanation: str = "") -> None:
    """Render a single enhanced KPI card with consistent styling using Streamlit components."""
    
    # Get trend display if available
    trend_display = ""
    if trend_data:
        icon, trend_color, change_text, confidence = _get_trend_display(trend_data)
        trend_display = f"{icon} {change_text}"
    
    # Use Streamlit container for better layout control
    with st.container():
        # Create a styled container using st.markdown for the card
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(46, 134, 171, 0.05) 0%, rgba(255,255,255,1) 100%);
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h4 style="
                color: {color}; 
                font-size: 0.9rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin: 0 0 0.5rem 0;
            ">{title}</h4>
            <div style="
                font-size: 2rem; 
                font-weight: 700; 
                color: {color}; 
                margin: 0.5rem 0;
                line-height: 1.1;
            ">{value}</div>
            {f'<div style="font-size: 0.8rem; color: #666; margin: 0.25rem 0;">{subtitle}</div>' if subtitle else ''}
            {f'<div style="font-size: 0.85rem; color: {_get_trend_display(trend_data)[1] if trend_data else "#666"}; font-weight: 500;">{trend_display}</div>' if trend_display else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # Add explanation as expandable section if provided
        if explanation:
            with st.expander(f"ℹ️ About {title}", expanded=False):
                st.markdown(explanation)


def render_kpi_overview_enhanced(kpis: Dict[str, Any]) -> None:
    """Render the enhanced KPI overview with unified grid layout.
    
    Args:
        kpis: Dictionary of KPI data from KPICalculator
    """
    
    # Clean section header
    st.markdown("## 🎯 Your Wellbeing At-a-Glance")
    st.markdown("")
    
    # Create responsive 4-column grid for KPIs
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="small")
    
    with col1:
        # Wellbeing Score
        if 'wellbeing_score' in kpis:
            wb_data = kpis['wellbeing_score']
            score = wb_data.get('score', 0.0)
            confidence = wb_data.get('confidence', 0.0)
            trend = wb_data.get('trend_data', {})
            sample_size = wb_data.get('sample_size', 0)
            
            color = _get_kpi_color(score, 10.0, 'wellbeing')
            subtitle = f"{confidence:.0%} confidence • {sample_size} days"
            
            explanation = """
            **Wellbeing Score** combines your daily mood and energy levels into a single metric (0-10).
            
            **How it works:**
            - Averages your mood and energy ratings
            - Considers data consistency and sample size  
            - Higher scores indicate better overall wellbeing
            
            **Score ranges:**
            - 🟢 **8-10**: Excellent wellbeing
            - 🟡 **6-8**: Good wellbeing
            - 🟠 **4-6**: Moderate wellbeing  
            - 🔴 **0-4**: Needs attention
            """
            
            render_kpi_card_enhanced(
                title="Wellbeing Score",
                value=f"{score:.1f}/10",
                subtitle=subtitle,
                trend_data=trend,
                color=color,
                explanation=explanation
            )
        else:
            st.info("Wellbeing data not available")
    
    with col2:
        # Balance Index
        if 'balance_index' in kpis:
            balance_data = kpis['balance_index']
            index = balance_data.get('index', 0.0)
            components = balance_data.get('components', {})
            
            color = _get_kpi_color(index, 100.0, 'balance')
            subtitle = f"Activity & Sleep Balance"
            
            explanation = """
            **Balance Index** measures how well you balance different aspects of your life (0-100%).
            
            **Components:**
            - **Activity Balance**: Variety in your daily activities
            - **Sleep Achievement**: Meeting sleep duration goals
            - **Overall Harmony**: Integration of wellness factors
            
            **Index ranges:**
            - 🟢 **80-100%**: Excellent balance
            - 🟡 **60-80%**: Good balance
            - 🟠 **40-60%**: Moderate balance
            - 🔴 **0-40%**: Needs rebalancing
            """
            
            render_kpi_card_enhanced(
                title="Balance Index",
                value=f"{index:.0f}%",
                subtitle=subtitle,
                color=color,
                explanation=explanation
            )
        else:
            st.info("Balance data not available")
    
    with col3:
        # Trend Indicator
        if 'trend_indicator' in kpis:
            trend_data = kpis['trend_indicator']
            trend = trend_data.get('trend', 'stable')
            change = trend_data.get('change', 0.0)
            confidence = trend_data.get('confidence', 'medium')
            timeframe = trend_data.get('timeframe', 7)
            
            trend_colors = {'improving': '#2E86AB', 'stable': '#F18F01', 'declining': '#C73E1D'}
            color = trend_colors.get(trend, '#F18F01')
            
            # Format the main display
            trend_icons = {'improving': '↗ Improving', 'stable': '→ Stable', 'declining': '↘ Declining'}
            value_display = trend_icons.get(trend, '→ Stable')
            
            subtitle = f"{confidence.title()} confidence • {timeframe} days"
            
            explanation = """
            **Trend Indicator** shows the direction of your wellbeing over recent days.
            
            **Analysis method:**
            - Statistical trend analysis over the selected timeframe
            - Considers both mood and energy patterns
            - Confidence levels based on data consistency
            
            **Trend meanings:**
            - 🟢 **↗ Improving**: Your wellbeing is trending upward
            - 🟡 **→ Stable**: Your wellbeing is consistent
            - 🔴 **↘ Declining**: Your wellbeing is trending downward
            """
            
            render_kpi_card_enhanced(
                title="Trend Direction",
                value=value_display,
                subtitle=subtitle,
                color=color,
                explanation=explanation
            )
        else:
            st.info("Trend data not available")
    
    with col4:
        # Sleep Quality
        if 'sleep_quality_analysis' in kpis:
            sleep_data = kpis['sleep_quality_analysis']
            
            if 'error' in sleep_data:
                st.warning(f"Sleep Quality: {sleep_data['error']}")
            else:
                subjective_avg = sleep_data.get('subjective_avg')
                objective_data = sleep_data.get('objective_quality', {})
                sample_size = sleep_data.get('sample_size', 0)
                
                # Determine primary display value
                if subjective_avg is not None and not (isinstance(objective_data, dict) and 'error' in objective_data):
                    # Both available
                    objective_score = objective_data.get('objective_sleep_quality', 0)
                    value_display = f"{subjective_avg:.1f}/5"
                    subtitle = f"Subjective • Obj: {objective_score:.1f}/5"
                    color = _get_kpi_color(subjective_avg, 5.0, 'sleep')
                elif subjective_avg is not None:
                    # Only subjective
                    value_display = f"{subjective_avg:.1f}/5"
                    subtitle = f"Subjective only • {sample_size} days"
                    color = _get_kpi_color(subjective_avg, 5.0, 'sleep')
                elif not (isinstance(objective_data, dict) and 'error' in objective_data):
                    # Only objective
                    objective_score = objective_data.get('objective_sleep_quality', 0)
                    value_display = f"{objective_score:.1f}/5"
                    subtitle = f"Objective only • Timing-based"
                    color = _get_kpi_color(objective_score, 5.0, 'sleep')
                else:
                    value_display = "N/A"
                    subtitle = "Insufficient data"
                    color = "#666666"
                
                explanation = """
                **Sleep Quality** analyzes your sleep using two approaches (1-5 scale).
                
                **Subjective Analysis:**
                - Based on your daily sleep quality ratings
                - Reflects how rested you feel
                
                **Objective Analysis:**
                - Duration Score (40%): 7-9 hours optimal
                - Timing Score (30%): Circadian rhythm alignment
                - Regularity Score (20%): Schedule consistency
                - Efficiency Score (10%): Weekend patterns
                
                **Quality ranges:**
                - 🟢 **4-5**: Excellent sleep
                - 🟡 **3-4**: Good sleep
                - 🟠 **2-3**: Fair sleep
                - 🔴 **1-2**: Poor sleep
                """
                
                render_kpi_card_enhanced(
                    title="Sleep Quality",
                    value=value_display,
                    subtitle=subtitle,
                    color=color,
                    explanation=explanation
                )
        else:
            st.info("Sleep data not available")


def render_top_insights(correlations: Dict[str, Any], kpis: Dict[str, Any], 
                       data_sample_size: int = 0) -> None:
    """Render top 3 actionable insights section.
    
    Args:
        correlations: Correlation analysis results
        kpis: KPI calculation results  
        data_sample_size: Number of data points analyzed
    """
    
    st.markdown("## 💡 Your Top 3 Insights This Week")
    
    insights = []
    
    # First, try to generate insights from correlations
    significant_correlations = correlations.get('significant_correlations', [])
    all_correlations = correlations.get('all_correlations', {})
    
    # Debug: Check what correlation data we have
    correlation_insights_added = 0
    
    for corr in significant_correlations[:2]:  # Take top 2 correlations
        # Handle different correlation data structures
        if isinstance(corr, dict):
            var1 = corr.get('var1', corr.get('variables', ['', ''])[0] if isinstance(corr.get('variables'), list) else '')
            var2 = corr.get('var2', corr.get('variables', ['', ''])[1] if isinstance(corr.get('variables'), list) else '')
            correlation = corr.get('correlation', corr.get('r', 0))
            p_value = corr.get('p_value', corr.get('p', 1))
        else:
            # Fallback for other data structures
            var1, var2, correlation, p_value = '', '', 0, 1
            
        confidence = (1 - p_value) * 100
        
        # Skip if no variable names found
        if not var1 or not var2:
            continue
            
        # Clean variable names for display
        var1_clean = var1.replace('_', ' ').title()
        var2_clean = var2.replace('_', ' ').title()
        
        # Generate insight text based on variables
        if any(sleep_word in var1.lower() for sleep_word in ['sleep', 'bedtime', 'wake']):
            other_var = var2_clean
            if correlation > 0:
                insight_text = f"Better sleep patterns are linked to improved {other_var.lower()}"
            else:
                insight_text = f"Sleep disruption appears to negatively affect {other_var.lower()}"
        elif any(sleep_word in var2.lower() for sleep_word in ['sleep', 'bedtime', 'wake']):
            other_var = var1_clean
            if correlation > 0:
                insight_text = f"Better sleep patterns are linked to improved {other_var.lower()}"
            else:
                insight_text = f"Sleep disruption appears to negatively affect {other_var.lower()}"
        elif any(mood_word in var1.lower() for mood_word in ['mood', 'energy', 'wellbeing']):
            other_var = var2_clean
            if correlation > 0:
                insight_text = f"Higher {var1_clean.lower()} correlates with better {other_var.lower()}"
            else:
                insight_text = f"Lower {var1_clean.lower()} may impact {other_var.lower()}"
        elif any(mood_word in var2.lower() for mood_word in ['mood', 'energy', 'wellbeing']):
            other_var = var1_clean
            if correlation > 0:
                insight_text = f"Higher {var2_clean.lower()} correlates with better {other_var.lower()}"
            else:
                insight_text = f"Lower {var2_clean.lower()} may impact {other_var.lower()}"
        else:
            direction = 'positive' if correlation > 0 else 'negative'
            insight_text = f"{var1_clean} and {var2_clean.lower()} show a {direction} relationship (r={correlation:.2f})"
        
        insights.append({
            'text': insight_text,
            'confidence': confidence,
            'type': 'correlation'
        })
        correlation_insights_added += 1
    
    # If no significant correlations, try to find some strong correlations from all_correlations
    if correlation_insights_added == 0 and all_correlations:
        # Look for the strongest correlations even if not statistically significant
        strong_correlations = []
        for pair, corr_value in all_correlations.items():
            if isinstance(pair, str) and isinstance(corr_value, (int, float)):
                # Parse the pair string (assumes format like "var1_var2")
                if '_' in pair and abs(corr_value) > 0.3:  # Moderate correlation threshold
                    vars = pair.split('_')
                    if len(vars) >= 2:
                        strong_correlations.append({
                            'var1': vars[0], 
                            'var2': '_'.join(vars[1:]), 
                            'correlation': corr_value,
                            'confidence': 70  # Lower confidence for non-significant
                        })
        
        # Add up to 1 strong correlation insight
        for corr_data in strong_correlations[:1]:
            var1_clean = corr_data['var1'].replace('_', ' ').title()
            var2_clean = corr_data['var2'].replace('_', ' ').title()
            correlation = corr_data['correlation']
            direction = 'positive' if correlation > 0 else 'negative'
            
            insights.append({
                'text': f"{var1_clean} and {var2_clean.lower()} show a {direction} relationship worth monitoring",
                'confidence': corr_data['confidence'],
                'type': 'correlation'
            })
            correlation_insights_added += 1
    
    # Add KPI-based insights
    if 'wellbeing_score' in kpis:
        wb_data = kpis['wellbeing_score']
        score = wb_data.get('score', 0)
        trend_data = wb_data.get('trend_data', {})
        trend = trend_data.get('trend', 'stable')
        
        if trend == 'improving':
            insights.append({
                'text': f"Your wellbeing is trending upward - current score of {score:.1f}/10 shows positive momentum",
                'confidence': 85,
                'type': 'trend'
            })
        elif score >= 8:
            insights.append({
                'text': f"Excellent wellbeing score of {score:.1f}/10 - you're maintaining strong mental health patterns",
                'confidence': 90,
                'type': 'achievement'
            })
        elif score < 5:
            insights.append({
                'text': f"Wellbeing score of {score:.1f}/10 suggests focusing on mood and energy improvement",
                'confidence': 80,
                'type': 'attention'
            })
    
    # Add sleep-based insights if we need more
    if len(insights) < 3 and 'sleep_quality' in kpis:
        sleep_data = kpis['sleep_quality']
        quality = sleep_data.get('quality', 0)
        if quality >= 4:
            insights.append({
                'text': f"Your sleep quality of {quality:.1f}/5 indicates good rest patterns contributing to wellbeing",
                'confidence': 85,
                'type': 'achievement'
            })
        else:
            insights.append({
                'text': f"Sleep quality of {quality:.1f}/5 suggests optimizing bedtime routines for better recovery",
                'confidence': 82,
                'type': 'attention'
            })
    
    # Add balance-based insights if we need more
    if len(insights) < 3 and 'balance_index' in kpis:
        balance_data = kpis['balance_index']
        index = balance_data.get('index', 0)
        if index >= 70:
            insights.append({
                'text': f"Balance index of {index:.0f}% shows good harmony between activities and rest",
                'confidence': 88,
                'type': 'achievement'
            })
        else:
            insights.append({
                'text': f"Balance index of {index:.0f}% suggests exploring more variety in daily activities",
                'confidence': 85,
                'type': 'attention'
            })
    
    # Fill remaining slots with general insights
    fallback_insights = [
        {
            'text': f"With {data_sample_size} days of tracking, your data reveals meaningful patterns for optimization",
            'confidence': 75,
            'type': 'general'
        },
        {
            'text': f"Consistent tracking over {data_sample_size} days enables personalized wellbeing recommendations",
            'confidence': 70,
            'type': 'general'
        },
        {
            'text': f"Your {data_sample_size}-day data history provides rich insights into lifestyle patterns",
            'confidence': 68,
            'type': 'general'
        }
    ]
    
    # Add fallback insights if needed
    for fallback in fallback_insights:
        if len(insights) < 3:
            insights.append(fallback)
        else:
            break
    
    # Display top 3 insights
    for i, insight in enumerate(insights[:3]):
        confidence = insight.get('confidence', 75)
        insight_type = insight.get('type', 'general')
        
        # Color based on insight type
        type_colors = {
            'correlation': '#2E86AB',
            'trend': '#F18F01', 
            'achievement': '#2E86AB',
            'attention': '#C73E1D',
            'general': '#666666'
        }
        color = type_colors.get(insight_type, '#666666')
        
        # Icon based on type
        type_icons = {
            'correlation': '🔗',
            'trend': '📈',
            'achievement': '⭐',
            'attention': '⚠️',
            'general': '💡'
        }
        icon = type_icons.get(insight_type, '💡')
        
        insight_html = f"""
        <div style="
            background: white;
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">{icon}</span>
                <span style="
                    background: {color};
                    color: white;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 0.8rem;
                    font-weight: 600;
                ">{confidence:.0f}% confidence</span>
            </div>
            <p style="
                margin: 0;
                font-size: 1.1rem;
                line-height: 1.5;
                color: #333;
            ">{insight['text']}</p>
        </div>
        """
        
        st.markdown(insight_html, unsafe_allow_html=True)


def render_progressive_disclosure_sections(kpi_data, kpis, correlations) -> None:
    """Render the accordion-style progressive disclosure sections.
    
    Args:
        kpi_data: Processed data DataFrame
        kpis: KPI calculation results
        correlations: Correlation analysis results
    """
    
    st.markdown("## 🔍 Detailed Analysis")
    st.markdown("*Expand any section below for deeper insights*")
    
    # Sleep Analysis Section
    with st.expander("😴 Sleep Analysis Details", expanded=False):
        if 'sleep_quality_analysis' in kpis:
            from components.drill_down_views import render_sleep_analysis_drilldown
            render_sleep_analysis_drilldown(kpi_data, kpis)
        else:
            st.info("Sleep analysis requires sleep timing or quality data")
    
    # Activity Impact Section  
    with st.expander("🏃 Activity Impact Analysis", expanded=False):
        from components.drill_down_views import render_activity_impact_drilldown
        render_activity_impact_drilldown(kpi_data, kpis)
    
    # Statistical Patterns Section
    with st.expander("📊 Statistical Patterns & Correlations", expanded=False):
        from components.insight_display import render_statistical_insights
        render_statistical_insights(correlations, show_methodology=True)
    
    # Raw Data Explorer Section
    with st.expander("📋 Interactive Raw Data Explorer", expanded=False):
        st.markdown("### 🔍 Filter & Explore Your Data")
        
        if kpi_data is not None and not kpi_data.empty:
            # Create filter controls
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                # Date range filter
                if 'date' in kpi_data.columns and not kpi_data['date'].isna().all():
                    min_date = kpi_data['date'].min()
                    max_date = kpi_data['date'].max()
                    
                    date_range = st.date_input(
                        "📅 Date Range",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    # Apply date filter
                    if isinstance(date_range, tuple) and len(date_range) == 2:
                        start_date, end_date = date_range
                        filtered_data = kpi_data[
                            (kpi_data['date'] >= pd.Timestamp(start_date)) & 
                            (kpi_data['date'] <= pd.Timestamp(end_date))
                        ].copy()
                    else:
                        filtered_data = kpi_data.copy()
                else:
                    st.info("No date column available for filtering")
                    filtered_data = kpi_data.copy()
            
            with filter_col2:
                # Column selection
                available_cols = list(kpi_data.columns)
                key_cols = ['date', 'mood', 'energy', 'sleep_quality', 'sleep_bedtime', 'wake_time']
                default_cols = [col for col in key_cols if col in available_cols]
                
                selected_columns = st.multiselect(
                    "📊 Columns",
                    options=available_cols,
                    default=default_cols if default_cols else available_cols[:5],
                    help="Choose columns to display"
                )
            
            with filter_col3:
                # Data quality filter
                quality_filter = st.selectbox(
                    "🎯 Filter",
                    options=["All Records", "Complete Sleep Data", "Complete Mood/Energy"],
                    help="Filter by data completeness"
                )
            
            # Apply quality filter
            if quality_filter == "Complete Sleep Data":
                sleep_cols = ['sleep_bedtime', 'wake_time']
                available_sleep_cols = [col for col in sleep_cols if col in filtered_data.columns]
                if available_sleep_cols:
                    filtered_data = filtered_data.dropna(subset=available_sleep_cols)
                    
            elif quality_filter == "Complete Mood/Energy":
                mood_energy_cols = ['mood', 'energy']
                available_me_cols = [col for col in mood_energy_cols if col in filtered_data.columns]
                if available_me_cols:
                    filtered_data = filtered_data.dropna(subset=available_me_cols)
            
            # Display filtered data
            if selected_columns and not filtered_data.empty:
                display_cols = [col for col in selected_columns if col in filtered_data.columns]
                display_data = filtered_data[display_cols].copy()
                
                # Sort by date if available
                if 'date' in display_data.columns:
                    display_data = display_data.sort_values('date', ascending=False)
                
                st.markdown(f"#### 📋 Filtered Data ({len(display_data)} records)")
                st.dataframe(display_data, use_container_width=True, hide_index=True, height=300)
                
                # Summary stats
                summary_col1, summary_col2, summary_col3 = st.columns(3)
                
                with summary_col1:
                    st.metric("📊 Records", len(display_data))
                    
                with summary_col2:
                    if 'date' in display_data.columns and len(display_data) > 0:
                        date_span = (display_data['date'].max() - display_data['date'].min()).days + 1
                        st.metric("📅 Days", f"{date_span}")
                    else:
                        st.metric("📅 Days", "N/A")
                
                with summary_col3:
                    completeness = (1 - display_data.isnull().sum().sum() / (len(display_data) * len(display_data.columns))) * 100
                    st.metric("✅ Complete", f"{completeness:.0f}%")
                
                # Export option
                if st.button("📥 Download as CSV"):
                    csv = display_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"san_xing_data_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("⚠️ No data matches your current filters")
        else:
            st.warning("No data available for exploration")
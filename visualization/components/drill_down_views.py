"""Drill-down Analysis Views for San-Xing Dashboard.

This module provides detailed analysis views that users can access
for deeper insights into their wellbeing patterns and correlations.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from .data_viz import create_trend_chart, create_correlation_heatmap

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from analytics.statistical_utils import (
    calculate_significance,
    trend_significance,
    calculate_confidence_interval
)


def render_sleep_analysis_drilldown(data: pd.DataFrame, 
                                  kpi_results: Dict[str, Any]) -> None:
    """Render detailed sleep analysis drill-down view.
    
    Args:
        data: DataFrame with sleep-related columns
        kpi_results: KPI calculation results containing sleep metrics
    """
    st.markdown("## Sleep Analysis Deep Dive")
    
    # Check for required columns
    sleep_cols = ['sleep_duration', 'sleep_quality']
    available_sleep_cols = [col for col in sleep_cols if col in data.columns]
    
    if not available_sleep_cols:
        st.warning("No sleep data available for analysis")
        return
    
    # Sleep overview metrics
    with st.container():
        st.markdown("### Sleep Metrics Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        if 'sleep_duration' in data.columns:
            duration_data = data['sleep_duration'].dropna()
            avg_duration = duration_data.mean()
            target_nights = len(duration_data[(duration_data >= 7) & (duration_data <= 8)])
            target_percentage = target_nights / len(duration_data) * 100 if len(duration_data) > 0 else 0
            
            with col1:
                st.metric(
                    "Average Duration", 
                    f"{avg_duration:.1f} hrs",
                    help="Your average nightly sleep duration"
                )
            
            with col2:
                st.metric(
                    "Target Achievement",
                    f"{target_percentage:.1f}%",
                    help="Nights with 7-8 hours sleep"
                )
        
        if 'sleep_quality' in data.columns:
            quality_data = data['sleep_quality'].dropna()
            avg_quality = quality_data.mean()
            quality_ci = calculate_confidence_interval(quality_data)
            
            with col3:
                st.metric(
                    "Average Quality",
                    f"{avg_quality:.1f}/10",
                    help=f"95% CI: {quality_ci[0]:.1f}-{quality_ci[1]:.1f}"
                )
            
            with col4:
                consistency = 1 - (quality_data.std() / avg_quality) if avg_quality > 0 else 0
                st.metric(
                    "Consistency Score",
                    f"{consistency:.2f}",
                    help="Lower variability indicates better consistency"
                )
    
    st.divider()
    
    # Sleep patterns visualization
    st.markdown("###  Sleep Patterns Over Time")
    
    if len(available_sleep_cols) > 0:
        # Create dual-axis chart for duration and quality
        date_col = 'date' if 'date' in data.columns else data.index
        
        if 'date' in data.columns:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            if 'sleep_duration' in data.columns:
                duration_data = data.dropna(subset=['sleep_duration'])
                fig.add_trace(
                    go.Scatter(
                        x=duration_data['date'],
                        y=duration_data['sleep_duration'],
                        mode='lines+markers',
                        name='Sleep Duration',
                        line=dict(color='#1f77b4', width=2),
                        marker=dict(size=6),
                        hovertemplate="<b>Sleep Duration</b><br>" +
                                     "Date: %{x}<br>" +
                                     "Hours: %{y:.1f}<br>" +
                                     "<extra></extra>"
                    ),
                    secondary_y=False
                )
                
                # Add target range
                fig.add_hrect(
                    y0=7, y1=8,
                    fillcolor="rgba(0,255,0,0.1)",
                    layer="below",
                    line_width=0,
                    secondary_y=False
                )
            
            if 'sleep_quality' in data.columns:
                quality_data = data.dropna(subset=['sleep_quality'])
                fig.add_trace(
                    go.Scatter(
                        x=quality_data['date'],
                        y=quality_data['sleep_quality'],
                        mode='lines+markers',
                        name='Sleep Quality',
                        line=dict(color='#ff7f0e', width=2),
                        marker=dict(size=6),
                        hovertemplate="<b>Sleep Quality</b><br>" +
                                     "Date: %{x}<br>" +
                                     "Rating: %{y:.1f}/10<br>" +
                                     "<extra></extra>"
                    ),
                    secondary_y=True
                )
            
            # Update axes
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Sleep Duration (hours)", secondary_y=False)
            fig.update_yaxes(title_text="Sleep Quality (1-10)", secondary_y=True)
            
            fig.update_layout(
                title="Sleep Duration vs Quality Over Time",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Sleep correlation analysis
    st.markdown("###  Sleep Impact Analysis")
    
    # Correlate sleep with other wellbeing metrics
    wellbeing_cols = ['mood', 'energy', 'sleep_quality', 'sleep_duration']
    available_wellbeing_cols = [col for col in wellbeing_cols if col in data.columns]
    
    if len(available_wellbeing_cols) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Sleep Duration Correlations:**")
            if 'sleep_duration' in data.columns:
                for col in ['mood', 'energy', 'sleep_quality']:
                    if col in data.columns:
                        result = calculate_significance(
                            data['sleep_duration'], 
                            data[col], 
                            test_type='correlation'
                        )
                        
                        correlation = result['test_statistic']
                        p_value = result['p_value']
                        significant = result['significant']
                        
                        sig_indicator = "✓" if significant else "-"
                        st.write(f"{sig_indicator} {col.title()}: r={correlation:.3f} (p={p_value:.3f})")
                        
                        if significant:
                            if correlation > 0:
                                st.success(f"Longer sleep correlates with better {col}")
                            else:
                                st.warning(f"Longer sleep correlates with lower {col}")
        
        with col2:
            st.markdown("**Sleep Quality Correlations:**")
            if 'sleep_quality' in data.columns:
                for col in ['mood', 'energy', 'sleep_duration']:
                    if col in data.columns:
                        result = calculate_significance(
                            data['sleep_quality'], 
                            data[col], 
                            test_type='correlation'
                        )
                        
                        correlation = result['test_statistic']
                        p_value = result['p_value']
                        significant = result['significant']
                        
                        sig_indicator = "✓" if significant else "-"
                        st.write(f"{sig_indicator} {col.title()}: r={correlation:.3f} (p={p_value:.3f})")
    
    st.divider()
    
    # Sleep recommendations
    st.markdown("###  Sleep Optimization Recommendations")
    
    recommendations = []
    
    if 'sleep_duration' in data.columns:
        avg_duration = data['sleep_duration'].mean()
        target_achievement = len(data[(data['sleep_duration'] >= 7) & (data['sleep_duration'] <= 8)]) / len(data)
        
        if avg_duration < 7:
            recommendations.append(" **Increase Sleep Duration**: Your average sleep is below the recommended 7-8 hours. Consider earlier bedtimes.")
        elif avg_duration > 8.5:
            recommendations.append(" **Optimize Sleep Duration**: You may be oversleeping. Try maintaining 7-8 hours for better sleep efficiency.")
        
        if target_achievement < 0.7:
            recommendations.append(f" **Consistency Goal**: Currently {target_achievement:.0%} of nights meet the 7-8 hour target. Aim for 70%+ consistency.")
    
    if 'sleep_quality' in data.columns:
        avg_quality = data['sleep_quality'].mean()
        quality_std = data['sleep_quality'].std()
        
        if avg_quality < 6:
            recommendations.append(" **Improve Sleep Quality**: Average quality is below 6/10. Consider sleep hygiene improvements.")
        
        if quality_std > 1.5:
            recommendations.append(" **Reduce Variability**: Sleep quality varies significantly. Look for patterns affecting consistency.")
    
    # Sleep trend analysis
    if 'sleep_duration' in data.columns and len(data) >= 7:
        duration_trend = trend_significance(data['sleep_duration'])
        if duration_trend['significant']:
            if duration_trend['direction'] == 'improving':
                recommendations.append(" **Positive Trend**: Your sleep duration is improving - keep up the good habits!")
            elif duration_trend['direction'] == 'declining':
                recommendations.append(" **Concerning Trend**: Sleep duration is declining. Consider what changes might be affecting your sleep.")
    
    if not recommendations:
        recommendations.append("✓ **Great Job**: Your sleep patterns look healthy! Continue maintaining consistent sleep habits.")
    
    for rec in recommendations:
        st.markdown(f"""
        <div style='
            background: #e7f3ff;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid #007bff;
            margin: 10px 0;
        '>
            {rec}
        </div>
        """, unsafe_allow_html=True)


def render_activity_impact_drilldown(data: pd.DataFrame,
                                   kpi_results: Dict[str, Any]) -> None:
    """Render detailed activity impact analysis drill-down view.
    
    Args:
        data: DataFrame with activity-related columns
        kpi_results: KPI calculation results
    """
    st.markdown("##  Activity Impact Analysis")
    
    # Check for activity columns
    activity_cols = ['activity_balance', 'positive_activities', 'negative_activities']
    available_activity_cols = [col for col in activity_cols if col in data.columns]
    
    if not available_activity_cols:
        st.warning("No activity data available for analysis")
        return
    
    # Activity overview
    with st.container():
        st.markdown("###  Activity Metrics Overview")
        
        cols = st.columns(len(available_activity_cols))
        
        for i, col in enumerate(available_activity_cols):
            with cols[i]:
                col_data = data[col].dropna()
                if len(col_data) > 0:
                    mean_val = col_data.mean()
                    std_val = col_data.std()
                    
                    if col == 'activity_balance':
                        st.metric(
                            "Activity Balance",
                            f"{mean_val:+.2f}",
                            help=f"Std Dev: {std_val:.2f}"
                        )
                    elif col == 'positive_activities':
                        st.metric(
                            "Positive Activities",
                            f"{mean_val:.1f}/day",
                            help=f"Average daily positive activities"
                        )
                    elif col == 'negative_activities':
                        st.metric(
                            "Negative Activities", 
                            f"{mean_val:.1f}/day",
                            help=f"Average daily negative activities"
                        )
    
    st.divider()
    
    # Activity patterns over time
    if 'date' in data.columns and available_activity_cols:
        st.markdown("###  Activity Patterns Over Time")
        
        activity_chart = create_trend_chart(
            data=data,
            value_columns=available_activity_cols,
            date_column='date',
            title="Activity Metrics Trends",
            show_trend_lines=True
        )
        
        st.plotly_chart(activity_chart, use_container_width=True)
    
    st.divider()
    
    # Activity impact on wellbeing
    st.markdown("###  Activity Impact on Wellbeing")
    
    wellbeing_metrics = ['mood', 'energy']
    impact_results = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Activity Balance Impact:**")
        if 'activity_balance' in data.columns:
            for metric in wellbeing_metrics:
                if metric in data.columns:
                    result = calculate_significance(
                        data['activity_balance'],
                        data[metric],
                        test_type='correlation'
                    )
                    
                    correlation = result['test_statistic']
                    p_value = result['p_value']
                    significant = result['significant']
                    effect_size = result['effect_size']
                    
                    impact_results[f"balance_vs_{metric}"] = result
                    
                    sig_indicator = "✓" if significant else "-"
                    effect_text = "Strong" if effect_size > 0.5 else ("Moderate" if effect_size > 0.3 else "Weak")
                    
                    st.write(f"{sig_indicator} **{metric.title()}**: r={correlation:.3f}")
                    st.write(f"   Effect: {effect_text} (p={p_value:.3f})")
                    
                    if significant and correlation > 0.3:
                        st.success(f" Balanced activities strongly boost {metric}!")
                    elif significant and correlation < -0.3:
                        st.warning(f" Activity imbalance may reduce {metric}")
    
    with col2:
        st.markdown("**Positive vs Negative Activities:**")
        if 'positive_activities' in data.columns and 'negative_activities' in data.columns:
            # Calculate ratio
            data_with_ratio = data.copy()
            data_with_ratio['activity_ratio'] = (
                data_with_ratio['positive_activities'] / 
                (data_with_ratio['negative_activities'] + 1)  # Add 1 to avoid division by zero
            )
            
            for metric in wellbeing_metrics:
                if metric in data.columns:
                    result = calculate_significance(
                        data_with_ratio['activity_ratio'],
                        data_with_ratio[metric],
                        test_type='correlation'
                    )
                    
                    correlation = result['test_statistic']
                    p_value = result['p_value']
                    significant = result['significant']
                    
                    sig_indicator = "✓" if significant else "-"
                    st.write(f"{sig_indicator} **{metric.title()} vs Ratio**: r={correlation:.3f}")
                    st.write(f"   p-value: {p_value:.3f}")
    
    st.divider()
    
    # Activity recommendations
    st.markdown("###  Activity Optimization Recommendations")
    
    recommendations = []
    
    # Analyze activity balance
    if 'activity_balance' in data.columns:
        balance_mean = data['activity_balance'].mean()
        balance_std = data['activity_balance'].std()
        
        if balance_mean < -1:
            recommendations.append(" **Increase Positive Activities**: Your activity balance skews negative. Try adding more enjoyable or fulfilling activities.")
        elif balance_mean > 2:
            recommendations.append(" **Maintain Balance**: Great activity balance! Continue diversifying your activities.")
        
        if balance_std > 2:
            recommendations.append(" **Stabilize Activity Patterns**: High variability in activities. Consider creating more consistent routines.")
    
    # Analyze positive/negative ratio
    if 'positive_activities' in data.columns and 'negative_activities' in data.columns:
        pos_mean = data['positive_activities'].mean()
        neg_mean = data['negative_activities'].mean()
        ratio = pos_mean / (neg_mean + 0.1)  # Avoid division by zero
        
        if ratio < 1.5:
            recommendations.append(" **Boost Positive Activities**: Consider increasing positive activities relative to negative ones. Aim for a 2:1 ratio.")
        elif ratio > 3:
            recommendations.append("✓ **Excellent Activity Ratio**: Great balance of positive to negative activities!")
    
    # Check correlations with wellbeing
    strong_correlations = []
    for key, result in impact_results.items():
        if result.get('significant') and result.get('effect_size', 0) > 0.3:
            strong_correlations.append(key)
    
    if strong_correlations:
        recommendations.append(" **Leverage Activity Impact**: Strong correlations found between activities and wellbeing. Focus on optimizing these patterns.")
    
    if not recommendations:
        recommendations.append("✓ **Well Balanced**: Your activity patterns appear healthy and balanced!")
    
    for rec in recommendations:
        st.markdown(f"""
        <div style='
            background: #fff3e0;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid #ff9800;
            margin: 10px 0;
        '>
            {rec}
        </div>
        """, unsafe_allow_html=True)


def render_pattern_analysis_drilldown(data: pd.DataFrame,
                                    correlation_results: Dict[str, Any],
                                    kpi_results: Dict[str, Any]) -> None:
    """Render comprehensive pattern analysis drill-down view.
    
    Args:
        data: DataFrame with all available data
        correlation_results: Results from correlation analysis
        kpi_results: KPI calculation results
    """
    st.markdown("##  Advanced Pattern Analysis")
    
    # Weekly patterns
    if 'date' in data.columns:
        st.markdown("###  Weekly Patterns")
        
        # Add day of week
        data_with_dow = data.copy()
        data_with_dow['day_of_week'] = pd.to_datetime(data_with_dow['date']).dt.day_name()
        data_with_dow['weekday'] = pd.to_datetime(data_with_dow['date']).dt.weekday
        
        # Analyze patterns by day of week
        wellbeing_cols = ['mood', 'energy', 'sleep_quality', 'sleep_duration']
        available_wellbeing_cols = [col for col in wellbeing_cols if col in data.columns]
        
        if available_wellbeing_cols:
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            # Create weekly pattern visualization
            fig = make_subplots(
                rows=len(available_wellbeing_cols),
                cols=1,
                subplot_titles=[col.replace('_', ' ').title() for col in available_wellbeing_cols],
                vertical_spacing=0.1
            )
            
            colors = px.colors.qualitative.Set2
            
            for i, col in enumerate(available_wellbeing_cols):
                # Calculate daily averages
                daily_avg = data_with_dow.groupby('day_of_week')[col].mean().reindex(day_order)
                daily_std = data_with_dow.groupby('day_of_week')[col].std().reindex(day_order)
                
                fig.add_trace(
                    go.Scatter(
                        x=daily_avg.index,
                        y=daily_avg.values,
                        mode='lines+markers',
                        name=col.replace('_', ' ').title(),
                        line=dict(color=colors[i], width=3),
                        marker=dict(size=8),
                        error_y=dict(
                            type='data',
                            array=daily_std.values,
                            visible=True
                        ),
                        showlegend=False
                    ),
                    row=i+1,
                    col=1
                )
            
            fig.update_layout(
                title="Weekly Patterns (Mean ± SD)",
                height=200 * len(available_wellbeing_cols),
                showlegend=False
            )
            
            for i in range(len(available_wellbeing_cols)):
                fig.update_xaxes(title_text="Day of Week" if i == len(available_wellbeing_cols)-1 else "",
                               row=i+1, col=1)
                fig.update_yaxes(title_text=available_wellbeing_cols[i].replace('_', ' ').title(),
                               row=i+1, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Weekly insights
            st.markdown("**Weekly Pattern Insights:**")
            for col in available_wellbeing_cols:
                daily_avg = data_with_dow.groupby('day_of_week')[col].mean().reindex(day_order)
                
                best_day = daily_avg.idxmax()
                worst_day = daily_avg.idxmin()
                variation = daily_avg.std()
                
                if variation > daily_avg.mean() * 0.1:  # Significant variation
                    st.write(f" **{col.title()}**: Best on {best_day} ({daily_avg[best_day]:.1f}), lowest on {worst_day} ({daily_avg[worst_day]:.1f})")
                else:
                    st.write(f" **{col.title()}**: Consistent across all days (variation: {variation:.2f})")
    
    st.divider()
    
    # Correlation network analysis
    st.markdown("###  Correlation Network")
    
    if correlation_results.get('all_correlations'):
        # Create network-style correlation display
        significant_pairs = correlation_results.get('significant_correlations', [])
        
        if significant_pairs:
            st.markdown("**Significant Relationships Found:**")
            
            # Create a more visual representation
            fig = go.Figure()
            
            # Get all variables involved in significant correlations
            variables = set()
            for pair in significant_pairs:
                variables.add(pair['variable_1'])
                variables.add(pair['variable_2'])
            
            variables = list(variables)
            n_vars = len(variables)
            
            if n_vars > 1:
                # Position variables in a circle
                angles = np.linspace(0, 2*np.pi, n_vars, endpoint=False)
                x_pos = np.cos(angles)
                y_pos = np.sin(angles)
                
                # Add variable nodes
                fig.add_trace(go.Scatter(
                    x=x_pos,
                    y=y_pos,
                    mode='markers+text',
                    marker=dict(size=30, color='lightblue', line=dict(width=2, color='darkblue')),
                    text=[var.replace('_', ' ').title() for var in variables],
                    textposition="middle center",
                    textfont=dict(size=10, color='darkblue'),
                    showlegend=False,
                    hoverinfo='text',
                    hovertext=[f"{var.replace('_', ' ').title()}" for var in variables]
                ))
                
                # Add correlation edges
                for pair in significant_pairs:
                    var1_idx = variables.index(pair['variable_1'])
                    var2_idx = variables.index(pair['variable_2'])
                    
                    correlation = pair['correlation']
                    color = 'green' if correlation > 0 else 'red'
                    width = min(abs(correlation) * 10, 10)
                    
                    fig.add_trace(go.Scatter(
                        x=[x_pos[var1_idx], x_pos[var2_idx]],
                        y=[y_pos[var1_idx], y_pos[var2_idx]],
                        mode='lines',
                        line=dict(color=color, width=width),
                        opacity=0.6,
                        showlegend=False,
                        hoverinfo='text',
                        hovertext=f"{pair['variable_1']} ↔ {pair['variable_2']}<br>r = {correlation:.3f}"
                    ))
                
                fig.update_layout(
                    title="Correlation Network Visualization",
                    showlegend=False,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    height=400,
                    margin=dict(l=20, r=20, t=60, b=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No significant correlations found in current dataset.")
    
    st.divider()
    
    # Trend summary
    st.markdown("###  Trend Summary")
    
    trend_cols = ['mood', 'energy', 'sleep_quality', 'sleep_duration']
    available_trend_cols = [col for col in trend_cols if col in data.columns]
    
    if available_trend_cols and len(data) >= 7:
        trend_results = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Individual Metric Trends:**")
            for col in available_trend_cols:
                result = trend_significance(data[col])
                trend_results[col] = result
                
                direction = result.get('trend_direction', 'stable')
                significant = result.get('significant', False)
                
                icon = {'improving': '↑', 'stable': '→', 'declining': '↓'}.get(direction, '→')
                sig_text = " (significant)" if significant else " (not significant)"
                
                st.write(f"{icon} **{col.title()}**: {direction}{sig_text}")
                st.write(f"   τ = {result.get('tau', 0):.3f}, p = {result.get('p_value', 1):.3f}")
        
        with col2:
            st.markdown("**Trend Insights:**")
            
            improving_count = sum(1 for r in trend_results.values() if r.get('trend_direction') == 'improving' and r.get('significant', False))
            declining_count = sum(1 for r in trend_results.values() if r.get('trend_direction') == 'declining' and r.get('significant', False))
            
            if improving_count > declining_count:
                st.success(f"✓ **Overall Positive**: {improving_count} metrics improving significantly")
            elif declining_count > improving_count:
                st.warning(f" **Attention Needed**: {declining_count} metrics declining significantly") 
            else:
                st.info("- **Stable Patterns**: No dominant trend direction detected")
            
            # Trend strength analysis
            strong_trends = [col for col, r in trend_results.items() if abs(r.get('tau', 0)) > 0.3]
            if strong_trends:
                st.write(f" **Strong trends detected in**: {', '.join([col.title() for col in strong_trends])}")
    
    st.divider()
    
    # Advanced insights
    st.markdown("###  Advanced Insights")
    
    insights = []
    
    # Multi-factor analysis
    if len(available_wellbeing_cols) >= 3:
        insights.append("🔬 **Multi-factor Analysis**: With 3+ wellbeing metrics, you have sufficient data for comprehensive pattern analysis.")
    
    # Data quality assessment
    total_days = len(data)
    complete_days = len(data.dropna(subset=available_wellbeing_cols))
    completeness = complete_days / total_days if total_days > 0 else 0
    
    if completeness > 0.8:
        insights.append(f" **High Data Quality**: {completeness:.0%} of days have complete data, enabling robust statistical analysis.")
    elif completeness > 0.5:
        insights.append(f" **Moderate Data Quality**: {completeness:.0%} data completeness. Consider more consistent tracking for stronger insights.")
    else:
        insights.append(f" **Data Quality Alert**: Only {completeness:.0%} data completeness. More consistent tracking would improve analysis reliability.")
    
    # Seasonal patterns (if enough data)
    if total_days > 30:
        insights.append(" **Seasonal Analysis**: With 30+ days of data, seasonal patterns may be detectable in future analyses.")
    
    for insight in insights:
        st.markdown(f"""
        <div style='
            background: #f0f8f0;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid #28a745;
            margin: 10px 0;
        '>
            {insight}
        </div>
        """, unsafe_allow_html=True)
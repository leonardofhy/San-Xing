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

from .data_viz import (
    create_trend_chart, 
    create_correlation_heatmap,
    create_sleep_quality_comparison,
    create_sleep_components_radar,
    create_sleep_timing_chart
)

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
    st.markdown("## 😴 Sleep Analysis Deep Dive")
    
    # Check for required columns
    sleep_cols = ['sleep_duration_hours', 'sleep_quality', 'sleep_bedtime', 'wake_time']
    available_sleep_cols = [col for col in sleep_cols if col in data.columns]
    
    if not available_sleep_cols:
        st.warning("No sleep data available for analysis")
        return
    
    # === OBJECTIVE SLEEP QUALITY ANALYSIS (Enhanced Section) ===
    sleep_quality_data = kpi_results.get('sleep_quality_analysis', {})
    objective_data = sleep_quality_data.get('objective_quality', {}) if sleep_quality_data else {}
    
    # Check if we have objective sleep data to display
    if not objective_data or 'error' in objective_data:
        st.info("💡 **Objective sleep analysis requires sleep timing data** (bedtime and wake time). Currently showing available sleep metrics.")
    
    if objective_data and 'error' not in objective_data and objective_data.get('objective_sleep_quality'):
        st.markdown("### 🎯 Objective Sleep Quality Analysis")
        st.markdown("*Based on sleep timing patterns and circadian science*")
        
        # Overall objective score prominently displayed
        overall_score = objective_data.get('objective_sleep_quality', 0)
        score_color = "#2E86AB" if overall_score >= 4.0 else "#F18F01" if overall_score >= 3.0 else "#C73E1D"
        
        score_col1, score_col2, score_col3 = st.columns([2, 1, 1])
        with score_col1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {score_color}15 0%, white 100%);
                border-left: 4px solid {score_color};
                padding: 1.5rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            ">
                <h2 style="color: {score_color}; margin: 0; font-size: 2.5rem;">{overall_score:.1f}/5</h2>
                <p style="margin: 0.5rem 0 0 0; color: #666;">Objective Sleep Quality</p>
            </div>
            """, unsafe_allow_html=True)
        
        with score_col2:
            metrics = objective_data.get('metrics', {})
            sample_size = metrics.get('sample_size', 0)
            st.metric("Data Sample", f"{sample_size} nights", help="Number of nights with complete sleep timing data")
        
        with score_col3:
            avg_duration = metrics.get('avg_duration', 0)
            st.metric("Avg Duration", f"{avg_duration:.1f}h", help="Average sleep duration across all nights")
        
        # Component Breakdown
        st.markdown("#### 📊 Sleep Quality Component Analysis")
        components = objective_data.get('components', {})
        
        if components:
            comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)
            
            with comp_col1:
                duration_score = components.get('duration_score', 0)
                duration_pct = duration_score * 100
                duration_color = "#2E86AB" if duration_pct >= 80 else "#F18F01" if duration_pct >= 60 else "#C73E1D"
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 2px solid {duration_color}; border-radius: 8px;">
                    <h3 style="color: {duration_color}; margin: 0;">{duration_pct:.0f}%</h3>
                    <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Duration</p>
                    <p style="margin: 0; font-size: 0.8rem; color: #666;">Weight: 40%</p>
                </div>
                """, unsafe_allow_html=True)
                st.caption("7-9 hours optimal")
            
            with comp_col2:
                timing_score = components.get('timing_score', 0) 
                timing_pct = timing_score * 100
                timing_color = "#2E86AB" if timing_pct >= 80 else "#F18F01" if timing_pct >= 60 else "#C73E1D"
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 2px solid {timing_color}; border-radius: 8px;">
                    <h3 style="color: {timing_color}; margin: 0;">{timing_pct:.0f}%</h3>
                    <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Timing</p>
                    <p style="margin: 0; font-size: 0.8rem; color: #666;">Weight: 30%</p>
                </div>
                """, unsafe_allow_html=True)
                st.caption("10PM-12AM bedtime optimal")
            
            with comp_col3:
                regularity_score = components.get('regularity_score', 0)
                regularity_pct = regularity_score * 100
                regularity_color = "#2E86AB" if regularity_pct >= 80 else "#F18F01" if regularity_pct >= 60 else "#C73E1D"
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 2px solid {regularity_color}; border-radius: 8px;">
                    <h3 style="color: {regularity_color}; margin: 0;">{regularity_pct:.0f}%</h3>
                    <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Regularity</p>
                    <p style="margin: 0; font-size: 0.8rem; color: #666;">Weight: 20%</p>
                </div>
                """, unsafe_allow_html=True)
                st.caption("±1 hour variation ideal")
            
            with comp_col4:
                efficiency_score = components.get('efficiency_score', 0)
                efficiency_pct = efficiency_score * 100
                efficiency_color = "#2E86AB" if efficiency_pct >= 80 else "#F18F01" if efficiency_pct >= 60 else "#C73E1D"
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 2px solid {efficiency_color}; border-radius: 8px;">
                    <h3 style="color: {efficiency_color}; margin: 0;">{efficiency_pct:.0f}%</h3>
                    <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Efficiency</p>
                    <p style="margin: 0; font-size: 0.8rem; color: #666;">Weight: 10%</p>
                </div>
                """, unsafe_allow_html=True)
                st.caption("Consistent patterns")
        
        # Sleep Pattern Analysis
        st.markdown("#### 📈 Sleep Pattern Insights")
        analysis_text = objective_data.get('analysis', '')
        if analysis_text:
            st.info(f"💡 {analysis_text}")
        
        # Average Sleep Times
        avg_bedtime = metrics.get('avg_bedtime', 'N/A')
        avg_wake_time = metrics.get('avg_wake_time', 'N/A')
        
        if avg_bedtime != 'N/A' and avg_wake_time != 'N/A':
            time_col1, time_col2 = st.columns(2)
            with time_col1:
                st.metric("📅 Average Bedtime", avg_bedtime, help="Average time you go to bed")
            with time_col2:
                st.metric("🌅 Average Wake Time", avg_wake_time, help="Average time you wake up")
        
        # Actionable Recommendations
        st.markdown("#### 💡 Personalized Sleep Optimization Recommendations")
        recommendations = []
        
        if components:
            duration_score = components.get('duration_score', 0)
            timing_score = components.get('timing_score', 0)
            regularity_score = components.get('regularity_score', 0)
            efficiency_score = components.get('efficiency_score', 0)
            
            # Duration recommendations
            if duration_score < 0.6:  # < 60%
                avg_dur = metrics.get('avg_duration', 0)
                if avg_dur < 7:
                    recommendations.append("🕒 **Extend sleep duration**: Aim for 7-9 hours. Try going to bed 30 minutes earlier.")
                elif avg_dur > 9:
                    recommendations.append("⏰ **Optimize sleep duration**: 9+ hours may indicate inefficient sleep. Consider gradual reduction.")
            
            # Timing recommendations  
            if timing_score < 0.6:  # < 60%
                recommendations.append("🌙 **Optimize sleep timing**: Try shifting bedtime closer to 10-11 PM for better circadian alignment.")
            
            # Regularity recommendations
            if regularity_score < 0.6:  # < 60%
                recommendations.append("📅 **Improve sleep consistency**: Keep bedtime and wake time within ±1 hour, even on weekends.")
            
            # Efficiency recommendations
            if efficiency_score < 0.6:  # < 60%
                recommendations.append("⚖️ **Maintain consistent patterns**: Avoid large weekend sleep shifts to prevent social jet lag.")
        
        # Display top 3 recommendations
        if recommendations:
            for i, rec in enumerate(recommendations[:3], 1):
                st.markdown(f"{i}. {rec}")
        else:
            st.success("🎉 Excellent sleep patterns! Your objective sleep quality is well-optimized.")
        
    # === SUBJECTIVE VS OBJECTIVE COMPARISON ===
    if sleep_quality_data and 'error' not in sleep_quality_data:
        subjective_avg = sleep_quality_data.get('subjective_avg')
        comparison_data = sleep_quality_data.get('comparison', {})
        
        if subjective_avg is not None and objective_data.get('objective_sleep_quality'):
            st.markdown("### ⚖️ Subjective vs Objective Sleep Quality Comparison")
            
            comp_col1, comp_col2, comp_col3 = st.columns(3)
            
            with comp_col1:
                subj_color = "#2E86AB" if subjective_avg >= 4.0 else "#F18F01" if subjective_avg >= 3.0 else "#C73E1D"
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem; border: 2px solid {subj_color}; border-radius: 8px;">
                    <h3 style="color: {subj_color}; margin: 0; font-size: 2rem;">{subjective_avg:.1f}/5</h3>
                    <p style="margin: 0.5rem 0 0 0; font-weight: 600;">How You Feel</p>
                    <p style="margin: 0; font-size: 0.8rem; color: #666;">Subjective Rating</p>
                </div>
                """, unsafe_allow_html=True)
                
            with comp_col2:
                correlation = comparison_data.get('correlation')
                if correlation is not None:
                    corr_strength = "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.3 else "Weak"
                    corr_color = "#2E86AB" if abs(correlation) > 0.7 else "#F18F01" if abs(correlation) > 0.3 else "#C73E1D"
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1.5rem; border: 2px solid {corr_color}; border-radius: 8px;">
                        <h3 style="color: {corr_color}; margin: 0; font-size: 1.5rem;">{corr_strength}</h3>
                        <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Agreement</p>
                        <p style="margin: 0; font-size: 0.8rem; color: #666;">r={correlation:.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Insufficient data\nfor correlation")
            
            with comp_col3:
                obj_score = objective_data.get('objective_sleep_quality', 0)
                obj_color = "#2E86AB" if obj_score >= 4.0 else "#F18F01" if obj_score >= 3.0 else "#C73E1D"
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem; border: 2px solid {obj_color}; border-radius: 8px;">
                    <h3 style="color: {obj_color}; margin: 0; font-size: 2rem;">{obj_score:.1f}/5</h3>
                    <p style="margin: 0.5rem 0 0 0; font-weight: 600;">Timing Patterns</p>
                    <p style="margin: 0; font-size: 0.8rem; color: #666;">Objective Score</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Agreement analysis
            if correlation is not None:
                agreement_analysis = comparison_data.get('agreement_analysis', '')
                recommendations_text = comparison_data.get('recommendations', '')
                
                if agreement_analysis:
                    st.info(f"📊 **Agreement Analysis**: {agreement_analysis}")
                
                if recommendations_text:
                    st.success(f"💡 **Insight**: {recommendations_text}")
            
            st.divider()
    
    # === SLEEP PATTERNS OVER TIME ===
    st.markdown("### 📈 Sleep Patterns Over Time")
    
    # Bedtime and Wake Time Patterns
    if 'sleep_bedtime' in data.columns and 'wake_time' in data.columns and 'date' in data.columns:
        timing_data = data[['date', 'sleep_bedtime', 'wake_time']].dropna()
        
        if len(timing_data) > 1:
            # Convert times to minutes for plotting
            def time_to_minutes(time_str):
                try:
                    if pd.isna(time_str) or not time_str:
                        return None
                    hours, minutes = map(int, str(time_str).split(':'))
                    total_minutes = hours * 60 + minutes
                    # Adjust for bedtime after midnight (add 24 hours)
                    if hours < 12:  # Assume times < 12:00 are bedtimes after midnight
                        total_minutes += 24 * 60
                    return total_minutes
                except:
                    return None
            
            def minutes_to_time_str(minutes):
                if pd.isna(minutes):
                    return "N/A"
                # Handle times after midnight
                if minutes >= 24 * 60:
                    minutes = minutes - 24 * 60
                hours = int(minutes // 60) % 24
                mins = int(minutes % 60)
                return f"{hours:02d}:{mins:02d}"
            
            # Process timing data
            timing_processed = timing_data.copy()
            timing_processed['bedtime_minutes'] = timing_processed['sleep_bedtime'].apply(time_to_minutes)
            timing_processed['wake_minutes'] = timing_processed['wake_time'].apply(time_to_minutes)
            timing_processed = timing_processed.dropna(subset=['bedtime_minutes', 'wake_minutes'])
            
            if len(timing_processed) > 1:
                # Create dual-axis plot for bedtime and wake time
                fig = make_subplots(rows=2, cols=1, 
                                  subplot_titles=['Bedtime Pattern', 'Wake Time Pattern'],
                                  vertical_spacing=0.1,
                                  shared_xaxes=True)
                
                # Bedtime trend
                fig.add_trace(
                    go.Scatter(
                        x=timing_processed['date'],
                        y=timing_processed['bedtime_minutes'],
                        mode='lines+markers',
                        name='Bedtime',
                        line=dict(color='#9467bd', width=2),
                        marker=dict(size=6),
                        hovertemplate="Date: %{x}<br>Bedtime: %{text}<extra></extra>",
                        text=[minutes_to_time_str(m) for m in timing_processed['bedtime_minutes']]
                    ),
                    row=1, col=1
                )
                
                # Add optimal bedtime range (22:00-24:00 = 1320-1440 minutes)
                fig.add_hrect(y0=22*60, y1=24*60, fillcolor="rgba(148, 103, 189, 0.1)", 
                             line_width=0, annotation_text="Optimal Bedtime Range (10-12 PM)",
                             row=1, col=1)
                
                # Wake time trend
                fig.add_trace(
                    go.Scatter(
                        x=timing_processed['date'],
                        y=timing_processed['wake_minutes'],
                        mode='lines+markers',
                        name='Wake Time',
                        line=dict(color='#ff7f0e', width=2),
                        marker=dict(size=6),
                        hovertemplate="Date: %{x}<br>Wake Time: %{text}<extra></extra>",
                        text=[minutes_to_time_str(m) for m in timing_processed['wake_minutes']]
                    ),
                    row=2, col=1
                )
                
                # Add optimal wake time range (6:00-8:00 = 360-480 minutes)
                fig.add_hrect(y0=6*60, y1=8*60, fillcolor="rgba(255, 127, 14, 0.1)", 
                             line_width=0, annotation_text="Optimal Wake Range (6-8 AM)",
                             row=2, col=1)
                
                # Update y-axis to show time format
                bedtime_tickvals = [20*60, 21*60, 22*60, 23*60, 24*60, 25*60, 26*60]  # 8PM to 2AM
                bedtime_ticktext = ["20:00", "21:00", "22:00", "23:00", "00:00", "01:00", "02:00"]
                
                wake_tickvals = [5*60, 6*60, 7*60, 8*60, 9*60, 10*60, 11*60]  # 5AM to 11AM  
                wake_ticktext = ["05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00"]
                
                fig.update_yaxes(tickvals=bedtime_tickvals, ticktext=bedtime_ticktext, 
                               title_text="Bedtime", row=1, col=1)
                fig.update_yaxes(tickvals=wake_tickvals, ticktext=wake_ticktext, 
                               title_text="Wake Time", row=2, col=1)
                
                fig.update_layout(
                    title="Sleep Timing Patterns Over Time",
                    height=500,
                    showlegend=False
                )
                fig.update_xaxes(title_text="Date", row=2, col=1)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Sleep timing insights
                avg_bedtime = timing_processed['bedtime_minutes'].mean()
                avg_wake = timing_processed['wake_minutes'].mean()
                bedtime_std = timing_processed['bedtime_minutes'].std() / 60  # Convert to hours
                wake_std = timing_processed['wake_minutes'].std() / 60
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Avg Bedtime", minutes_to_time_str(avg_bedtime))
                with col2:
                    st.metric("Avg Wake Time", minutes_to_time_str(avg_wake))
                with col3:
                    st.metric("Bedtime Regularity", f"±{bedtime_std:.1f}h", 
                             help="Lower variation = more consistent")
                with col4:
                    st.metric("Wake Time Regularity", f"±{wake_std:.1f}h",
                             help="Lower variation = more consistent")
                
                # Sleep Schedule Consistency Visualization
                st.markdown("#### 🎯 Sleep Schedule Consistency")
                
                # Create a scatter plot showing bedtime vs wake time consistency
                fig_consistency = go.Figure()
                
                # Calculate sleep duration for each day
                sleep_durations = []
                for _, row in timing_processed.iterrows():
                    bedtime_min = row['bedtime_minutes']
                    wake_min = row['wake_minutes']
                    
                    # Handle cross-midnight sleep
                    if wake_min < bedtime_min:
                        duration = (24 * 60 - bedtime_min) + wake_min
                    else:
                        duration = wake_min - bedtime_min
                    
                    sleep_durations.append(duration / 60)  # Convert to hours
                
                timing_processed['sleep_duration_calc'] = sleep_durations
                
                # Create consistency scatter plot
                fig_consistency.add_trace(go.Scatter(
                    x=timing_processed['bedtime_minutes'],
                    y=timing_processed['wake_minutes'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=timing_processed['sleep_duration_calc'],
                        colorscale='Viridis',
                        colorbar=dict(title="Sleep Duration (h)"),
                        opacity=0.7
                    ),
                    text=[f"Date: {d}<br>Bedtime: {minutes_to_time_str(b)}<br>Wake: {minutes_to_time_str(w)}<br>Duration: {dur:.1f}h" 
                          for d, b, w, dur in zip(timing_processed['date'], 
                                                  timing_processed['bedtime_minutes'],
                                                  timing_processed['wake_minutes'],
                                                  timing_processed['sleep_duration_calc'])],
                    hovertemplate="%{text}<extra></extra>",
                    name="Sleep Schedule"
                ))
                
                # Add optimal ranges
                fig_consistency.add_hrect(y0=6*60, y1=8*60, fillcolor="rgba(255, 127, 14, 0.1)", 
                                        line_width=0, annotation_text="Optimal Wake Range")
                fig_consistency.add_vrect(x0=22*60, x1=24*60, fillcolor="rgba(148, 103, 189, 0.1)", 
                                        line_width=0, annotation_text="Optimal Bedtime Range")
                
                # Update layout
                fig_consistency.update_layout(
                    title="Sleep Schedule Consistency Map",
                    xaxis_title="Bedtime",
                    yaxis_title="Wake Time", 
                    height=400
                )
                
                # Update axes to show time format
                fig_consistency.update_xaxes(tickvals=bedtime_tickvals, ticktext=bedtime_ticktext)
                fig_consistency.update_yaxes(tickvals=wake_tickvals, ticktext=wake_ticktext)
                
                st.plotly_chart(fig_consistency, use_container_width=True)
                
                # Consistency insights
                consistency_score = 100 - min(bedtime_std * 20, 100)  # Convert std to consistency score
                
                if consistency_score >= 80:
                    st.success(f"🎉 **Excellent Consistency**: {consistency_score:.0f}% schedule regularity")
                elif consistency_score >= 60:
                    st.info(f"📊 **Good Consistency**: {consistency_score:.0f}% schedule regularity - room for improvement")
                else:
                    st.warning(f"⚠️ **Inconsistent Schedule**: {consistency_score:.0f}% regularity - focus on consistent sleep times")
    
    # Combined Sleep Timing Chart (if original function works)
    elif 'sleep_bedtime' in data.columns and 'wake_time' in data.columns:
        try:
            timing_chart = create_sleep_timing_chart(data)
            st.plotly_chart(timing_chart, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not create timing chart: {e}")
    
    # Sleep Quality Over Time Chart
    if 'sleep_quality' in data.columns and 'date' in data.columns:
        sleep_trend_data = data[['date', 'sleep_quality']].dropna()
        if len(sleep_trend_data) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=sleep_trend_data['date'],
                y=sleep_trend_data['sleep_quality'],
                mode='lines+markers',
                name='Sleep Quality',
                line=dict(color='#2E86AB', width=2),
                marker=dict(size=6)
            ))
            fig.update_layout(
                title="Sleep Quality Trend",
                xaxis_title="Date",
                yaxis_title="Sleep Quality (1-5)",
                yaxis=dict(range=[0.5, 5.5]),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Sleep Duration Over Time Chart  
    if 'sleep_duration_hours' in data.columns and 'date' in data.columns:
        duration_trend_data = data[['date', 'sleep_duration_hours']].dropna()
        if len(duration_trend_data) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=duration_trend_data['date'],
                y=duration_trend_data['sleep_duration_hours'],
                mode='lines+markers',
                name='Sleep Duration',
                line=dict(color='#F18F01', width=2),
                marker=dict(size=6)
            ))
            # Add optimal sleep range
            fig.add_hrect(y0=7, y1=9, fillcolor="rgba(46, 134, 171, 0.1)", 
                         line_width=0, annotation_text="Optimal Range")
            fig.update_layout(
                title="Sleep Duration Trend",
                xaxis_title="Date", 
                yaxis_title="Sleep Duration (hours)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # === SLEEP IMPACT ANALYSIS ===
    st.markdown("### 🔍 Sleep Impact Analysis")
    
    # Sleep vs Mood Analysis
    if 'sleep_quality' in data.columns and 'mood' in data.columns:
        mood_sleep_data = data[['sleep_quality', 'mood']].dropna()
        if len(mood_sleep_data) > 5:
            correlation = mood_sleep_data['sleep_quality'].corr(mood_sleep_data['mood'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Sleep-Mood Correlation", f"{correlation:.3f}", 
                         help="How closely sleep quality relates to mood")
                if abs(correlation) > 0.5:
                    st.success("Strong relationship between sleep and mood")
                elif abs(correlation) > 0.3:
                    st.info("Moderate relationship between sleep and mood")
                else:
                    st.warning("Weak relationship - other factors may influence mood more")
            
            with col2:
                # Scatter plot
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=mood_sleep_data['sleep_quality'],
                    y=mood_sleep_data['mood'],
                    mode='markers',
                    marker=dict(color='#2E86AB', opacity=0.6),
                    name='Sleep vs Mood'
                ))
                fig.update_layout(
                    title="Sleep Quality vs Mood",
                    xaxis_title="Sleep Quality (1-5)",
                    yaxis_title="Mood (1-10)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Sleep vs Energy Analysis
    if 'sleep_quality' in data.columns and 'energy' in data.columns:
        energy_sleep_data = data[['sleep_quality', 'energy']].dropna()
        if len(energy_sleep_data) > 5:
            correlation = energy_sleep_data['sleep_quality'].corr(energy_sleep_data['energy'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Sleep-Energy Correlation", f"{correlation:.3f}",
                         help="How closely sleep quality relates to energy")
            
            with col2:
                # Scatter plot
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=energy_sleep_data['sleep_quality'],
                    y=energy_sleep_data['energy'],
                    mode='markers',
                    marker=dict(color='#F18F01', opacity=0.6),
                    name='Sleep vs Energy'
                ))
                fig.update_layout(
                    title="Sleep Quality vs Energy",
                    xaxis_title="Sleep Quality (1-5)",
                    yaxis_title="Energy (1-10)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # === SLEEP OPTIMIZATION RECOMMENDATIONS ===
    st.markdown("### 💡 Sleep Optimization Recommendations")
    
    # Generate comprehensive recommendations based on data analysis
    recommendations = []
    
    # Duration-based recommendations
    if 'sleep_duration_hours' in data.columns:
        duration_data = data['sleep_duration_hours'].dropna()
        if len(duration_data) > 0:
            avg_duration = duration_data.mean()
            if avg_duration < 7:
                recommendations.append({
                    'priority': 'High',
                    'category': '🕒 Duration',
                    'issue': f'Average sleep duration ({avg_duration:.1f}h) below recommended 7-9 hours',
                    'action': 'Try going to bed 30-60 minutes earlier each night until reaching 7+ hours'
                })
            elif avg_duration > 9:
                recommendations.append({
                    'priority': 'Medium', 
                    'category': '⏰ Duration',
                    'issue': f'Average sleep duration ({avg_duration:.1f}h) exceeds optimal range',
                    'action': 'Consider if long sleep indicates underlying sleep quality issues'
                })
    
    # Consistency-based recommendations
    if 'sleep_bedtime' in data.columns:
        bedtime_data = data['sleep_bedtime'].dropna()
        if len(bedtime_data) > 3:
            # Simple consistency check - convert times and check variation
            def time_to_minutes(time_str):
                try:
                    hours, minutes = map(int, str(time_str).split(':'))
                    return hours * 60 + minutes
                except:
                    return None
            
            bedtime_minutes = [time_to_minutes(t) for t in bedtime_data if time_to_minutes(t) is not None]
            if bedtime_minutes:
                bedtime_std = pd.Series(bedtime_minutes).std() / 60  # Convert to hours
                if bedtime_std > 1.5:  # More than 1.5 hours variation
                    recommendations.append({
                        'priority': 'High',
                        'category': '📅 Consistency', 
                        'issue': f'Bedtime varies by ±{bedtime_std:.1f} hours - inconsistent schedule',
                        'action': 'Set a consistent bedtime within ±1 hour, even on weekends'
                    })
    
    # Quality-based recommendations  
    if 'sleep_quality' in data.columns:
        quality_data = data['sleep_quality'].dropna()
        if len(quality_data) > 0:
            avg_quality = quality_data.mean()
            if avg_quality < 3.0:
                recommendations.append({
                    'priority': 'High',
                    'category': '💤 Quality',
                    'issue': f'Low average sleep quality ({avg_quality:.1f}/5)',
                    'action': 'Focus on sleep hygiene: dark room, cool temperature, no screens 1h before bed'
                })
    
    # Display recommendations by priority
    if recommendations:
        high_priority = [r for r in recommendations if r['priority'] == 'High']
        medium_priority = [r for r in recommendations if r['priority'] == 'Medium']
        
        if high_priority:
            st.markdown("#### 🔴 High Priority Actions")
            for rec in high_priority:
                st.markdown(f"**{rec['category']}**: {rec['issue']}")
                st.markdown(f"➤ *Action*: {rec['action']}")
                st.markdown("")
        
        if medium_priority:
            st.markdown("#### 🟡 Medium Priority Actions")  
            for rec in medium_priority:
                st.markdown(f"**{rec['category']}**: {rec['issue']}")
                st.markdown(f"➤ *Action*: {rec['action']}")
                st.markdown("")
    else:
        st.success("🎉 Your sleep patterns look good! Keep maintaining consistent habits.")
    
    # General sleep hygiene tips
    with st.expander("💡 General Sleep Hygiene Tips", expanded=False):
        st.markdown("""
        **Optimize Your Sleep Environment:**
        - Keep bedroom cool (65-68°F / 18-20°C)
        - Use blackout curtains or eye mask
        - Minimize noise or use white noise
        - Comfortable mattress and pillows
        
        **Pre-Sleep Routine:**
        - No screens 1 hour before bed
        - Light reading or relaxation exercises
        - Consistent wind-down activities
        - Avoid caffeine 6 hours before sleep
        - Limit alcohol, especially late evening
        
        **Timing Optimization:**
        - Consistent bedtime and wake time
        - Get morning sunlight exposure
        - Limit naps to 20-30 minutes before 3 PM
        - Exercise regularly, but not close to bedtime
        """)
    
    st.divider()


def render_activity_impact_drilldown(data: pd.DataFrame,
                                   kpi_results: Dict[str, Any]) -> None:
    """Render detailed activity impact analysis drill-down view.
    
    Args:
        data: DataFrame with activity-related columns
        kpi_results: KPI calculation results
    """
    st.markdown("## 🏃 Activity Impact Analysis")
    
    # Check for activity columns
    activity_cols = ['activity_balance', 'positive_activities', 'negative_activities']
    available_activity_cols = [col for col in activity_cols if col in data.columns]
    
    if not available_activity_cols:
        st.info("Activity analysis requires activity tracking data")
        return
    
    st.markdown("Activity impact analysis coming soon...")
    st.info("This section will show how your activities correlate with mood, energy, and sleep quality.")


def render_pattern_analysis_drilldown(data: pd.DataFrame,
                                    correlation_results: Dict[str, Any],
                                    kpi_results: Dict[str, Any]) -> None:
    """Render comprehensive pattern analysis drill-down view.
    
    Args:
        data: DataFrame with all available data
        correlation_results: Results from correlation analysis
        kpi_results: KPI calculation results
    """
    st.markdown("## 📊 Advanced Pattern Analysis")
    
    # Check for sufficient data
    if len(data) < 7:
        st.warning("Pattern analysis requires at least 7 days of data")
        return
    
    # Weekly patterns analysis
    if 'date' in data.columns:
        st.markdown("### 📅 Weekly Patterns")
        
        # Add day of week analysis
        data_with_dow = data.copy()
        try:
            data_with_dow['day_of_week'] = pd.to_datetime(data_with_dow['date']).dt.day_name()
            data_with_dow['weekday'] = pd.to_datetime(data_with_dow['date']).dt.weekday
            
            # Analyze patterns by day of week for key metrics
            wellbeing_cols = ['mood', 'energy', 'sleep_quality']
            available_cols = [col for col in wellbeing_cols if col in data.columns]
            
            if available_cols:
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                for col in available_cols[:2]:  # Show top 2 metrics
                    daily_avg = data_with_dow.groupby('day_of_week')[col].mean().reindex(day_order)
                    
                    if not daily_avg.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=daily_avg.index,
                            y=daily_avg.values,
                            mode='lines+markers',
                            name=col.replace('_', ' ').title(),
                            line=dict(width=3),
                            marker=dict(size=8)
                        ))
                        
                        fig.update_layout(
                            title=f"{col.replace('_', ' ').title()} by Day of Week",
                            xaxis_title="Day of Week",
                            yaxis_title=col.replace('_', ' ').title(),
                            height=300
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show insights
                        best_day = daily_avg.idxmax()
                        worst_day = daily_avg.idxmin()
                        st.info(f"**{col.title()}**: Best on {best_day} ({daily_avg[best_day]:.1f}), lowest on {worst_day} ({daily_avg[worst_day]:.1f})")
            
        except Exception as e:
            st.warning(f"Could not analyze weekly patterns: {e}")
    
    st.divider()
    
    # Correlation analysis
    st.markdown("### 🔗 Correlation Analysis")
    
    significant_correlations = correlation_results.get('significant_correlations', [])
    if significant_correlations:
        st.markdown("**Significant Relationships Found:**")
        
        for i, corr in enumerate(significant_correlations[:5]):  # Show top 5
            if isinstance(corr, dict):
                var1 = corr.get('variable_1', corr.get('var1', 'Unknown'))
                var2 = corr.get('variable_2', corr.get('var2', 'Unknown'))
                correlation = corr.get('correlation', corr.get('r', 0))
                p_value = corr.get('p_value', corr.get('p', 1))
                
                strength = "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.3 else "Weak"
                direction = "positive" if correlation > 0 else "negative"
                
                st.markdown(f"**{i+1}.** {var1.replace('_', ' ').title()} ↔ {var2.replace('_', ' ').title()}")
                st.markdown(f"   {strength} {direction} correlation: r={correlation:.3f} (p={p_value:.3f})")
    else:
        st.info("No statistically significant correlations found")
    
    st.divider()
    
    # Data quality summary
    st.markdown("### 📋 Data Quality Summary")
    
    total_days = len(data)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Days", total_days)
    
    with col2:
        # Calculate completeness for key columns
        key_cols = ['mood', 'energy', 'sleep_quality']
        available_key_cols = [col for col in key_cols if col in data.columns]
        if available_key_cols:
            complete_days = len(data.dropna(subset=available_key_cols))
            completeness = complete_days / total_days if total_days > 0 else 0
            st.metric("Data Completeness", f"{completeness:.0%}")
    
    with col3:
        # Count numeric columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        st.metric("Tracked Metrics", len(numeric_cols))
    
    # Data quality insights
    if total_days > 30:
        st.success("🎉 **Rich Dataset**: 30+ days enables robust pattern analysis")
    elif total_days > 14:
        st.info("📊 **Growing Dataset**: 14+ days provides meaningful trends")
    else:
        st.warning("📈 **Building Dataset**: Continue tracking for stronger insights")
    
    st.divider()

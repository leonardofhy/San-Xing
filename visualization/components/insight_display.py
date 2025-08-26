"""Insight Display Components for San-Xing Dashboard.

This module provides components for displaying statistical insights,
correlations, and trend analysis with actionable recommendations.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


def _get_significance_badge(p_value: float, alpha: float = 0.05) -> str:
    """Generate HTML badge for significance level."""
    if p_value < 0.001:
        return "<span style='background: #28a745; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;'>p&lt;0.001 ***</span>"
    elif p_value < 0.01:
        return "<span style='background: #28a745; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;'>p&lt;0.01 **</span>"
    elif p_value < alpha:
        return "<span style='background: #28a745; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;'>p&lt;0.05 *</span>"
    else:
        return "<span style='background: #6c757d; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;'>n.s.</span>"


def _get_effect_size_badge(effect_size: float, interpretation: str) -> str:
    """Generate HTML badge for effect size."""
    colors = {
        'large': '#dc3545',
        'medium': '#fd7e14', 
        'small': '#ffc107',
        'negligible': '#6c757d'
    }
    
    color = colors.get(interpretation, '#6c757d')
    return f"<span style='background: {color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;'>{interpretation.title()}</span>"


def render_statistical_insights(correlation_data: Dict[str, Any], 
                               trend_data: Optional[Dict[str, Any]] = None,
                               show_methodology: bool = False) -> None:
    """Render statistical insights with significance testing.
    
    Args:
        correlation_data: Results from correlation_with_significance()
        trend_data: Optional trend analysis results
        show_methodology: Whether to show statistical methodology details
    """
    st.markdown("##  Statistical Insights")
    
    # Main insights container
    with st.container():
        if not correlation_data.get('significant_correlations'):
            st.info(" No statistically significant correlations found in current dataset.")
            
            # Show methodology if requested
            if show_methodology:
                with st.expander(" Statistical Methodology", expanded=False):
                    st.markdown("""
                    **Correlation Analysis:**
                    - Test: Pearson correlation with Bonferroni correction
                    - Alpha level: {:.3f} (corrected from 0.05)
                    - Total comparisons: {}
                    - Sample size requirements: ≥10 observations per variable
                    
                    **Interpretation:**
                    - ***: p < 0.001 (highly significant)
                    - **: p < 0.01 (very significant) 
                    - *: p < 0.05 (significant)
                    - n.s.: not significant
                    """.format(
                        correlation_data.get('corrected_alpha', 0.05),
                        correlation_data.get('total_tests', 0)
                    ))
            
            return
        
        # Significant correlations found
        st.success(f"✓ Found {len(correlation_data['significant_correlations'])} significant correlation(s)")
        
        # Display each significant correlation
        for i, corr in enumerate(correlation_data['significant_correlations']):
            with st.container():
                st.markdown(f"""
                <div style='
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 10px;
                    border-left: 4px solid #007bff;
                    margin: 10px 0;
                '>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    var1 = corr['variable_1'].replace('_', ' ').title()
                    var2 = corr['variable_2'].replace('_', ' ').title()
                    
                    st.markdown(f"""
                    **{var1} ↔ {var2}**
                    
                    Correlation coefficient: **{corr['correlation']:.3f}**
                    
                    Sample size: {corr['sample_size']} observations
                    """)
                
                with col2:
                    sig_badge = _get_significance_badge(corr['p_value'])
                    st.markdown(f"**Significance:**<br>{sig_badge}", unsafe_allow_html=True)
                    st.markdown(f"p-value: {corr['p_value']:.4f}")
                
                with col3:
                    # Effect size interpretation (placeholder - would need actual interpretation)
                    effect_size = abs(corr['correlation'])
                    if effect_size >= 0.5:
                        interpretation = 'large'
                    elif effect_size >= 0.3:
                        interpretation = 'medium'
                    elif effect_size >= 0.1:
                        interpretation = 'small'
                    else:
                        interpretation = 'negligible'
                    
                    effect_badge = _get_effect_size_badge(effect_size, interpretation)
                    st.markdown(f"**Effect Size:**<br>{effect_badge}", unsafe_allow_html=True)
                    st.markdown(f"r = {effect_size:.3f}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Actionable insight
                _render_correlation_insight(corr, i + 1)
        
        # Show methodology
        if show_methodology:
            with st.expander(" Statistical Methodology", expanded=False):
                st.markdown(f"""
                **Correlation Analysis:**
                - Test: Pearson correlation coefficient
                - Multiple comparison correction: Bonferroni
                - Original α: 0.05 → Corrected α: {correlation_data.get('corrected_alpha', 0.05):.4f}
                - Total comparisons: {correlation_data.get('total_tests', 0)}
                
                **Effect Size Interpretation (Cohen's conventions):**
                - Large: |r| ≥ 0.5
                - Medium: 0.3 ≤ |r| < 0.5  
                - Small: 0.1 ≤ |r| < 0.3
                - Negligible: |r| < 0.1
                """)


def render_correlation_matrix(data: pd.DataFrame, 
                            correlation_results: Dict[str, Any],
                            show_only_significant: bool = False) -> None:
    """Render interactive correlation matrix heatmap.
    
    Args:
        data: DataFrame with numeric columns
        correlation_results: Results from correlation_with_significance()
        show_only_significant: Whether to highlight only significant correlations
    """
    st.markdown("## 🔗 Correlation Matrix")
    
    # Get numeric columns
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        st.warning("Need at least 2 numeric variables for correlation analysis")
        return
    
    # Calculate correlation matrix
    corr_matrix = data[numeric_cols].corr()
    
    # Create significance mask if requested
    significance_mask = None
    if show_only_significant and correlation_results.get('all_correlations'):
        significance_mask = np.ones_like(corr_matrix, dtype=bool)
        
        for pair_key, result in correlation_results['all_correlations'].items():
            if '_vs_' in pair_key:
                var1, var2 = pair_key.split('_vs_')
                if var1 in numeric_cols and var2 in numeric_cols:
                    i, j = numeric_cols.index(var1), numeric_cols.index(var2)
                    if result.get('significant', False):
                        significance_mask[i, j] = False
                        significance_mask[j, i] = False
    
    # Create heatmap
    fig = px.imshow(
        corr_matrix.values,
        labels=dict(x="Variables", y="Variables", color="Correlation"),
        x=corr_matrix.columns,
        y=corr_matrix.index,
        color_continuous_scale="RdBu_r",
        aspect="auto",
        zmin=-1,
        zmax=1
    )
    
    # Customize layout
    fig.update_layout(
        title="Correlation Heatmap",
        height=min(600, 50 * len(numeric_cols) + 200),
        font=dict(size=12)
    )
    
    # Add correlation values as text
    annotations = []
    for i, row in enumerate(corr_matrix.index):
        for j, col in enumerate(corr_matrix.columns):
            value = corr_matrix.iloc[i, j]
            
            # Skip if masked
            if significance_mask is not None and significance_mask[i, j]:
                continue
            
            # Color text based on correlation strength
            text_color = "white" if abs(value) > 0.6 else "black"
            
            annotations.append(
                dict(
                    x=j, y=i,
                    text=f"{value:.2f}",
                    showarrow=False,
                    font=dict(color=text_color, size=10)
                )
            )
    
    fig.update_layout(annotations=annotations)
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        strongest_corr = corr_matrix.abs().unstack().drop_duplicates().nlargest(2).iloc[1]
        st.metric("Strongest Correlation", f"{strongest_corr:.3f}")
    
    with col2:
        avg_corr = corr_matrix.abs().unstack().drop_duplicates().mean()
        st.metric("Average |Correlation|", f"{avg_corr:.3f}")
    
    with col3:
        sig_count = len(correlation_results.get('significant_correlations', []))
        st.metric("Significant Pairs", sig_count)


def render_trend_analysis(trend_results: Dict[str, Any], 
                         time_series_data: Optional[pd.DataFrame] = None) -> None:
    """Render trend analysis with statistical significance.
    
    Args:
        trend_results: Results from trend_significance()
        time_series_data: Optional DataFrame with time series for visualization
    """
    st.markdown("##  Trend Analysis")
    
    direction = trend_results.get('trend_direction', 'stable')
    p_value = trend_results.get('p_value', 1.0)
    tau = trend_results.get('tau', 0.0)
    significant = trend_results.get('significant', False)
    sample_size = trend_results.get('sample_size', 0)
    
    # Main trend container
    with st.container():
        st.markdown("""
        <div style='
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin: 10px 0;
        '>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            trend_icon = {'improving': '↑', 'stable': '→', 'declining': '↓'}.get(direction, '→')
            st.markdown(f"""
            <h2 style='color: white; margin: 0;'>{trend_icon} {direction.title()} Trend</h2>
            <p style='opacity: 0.9; margin: 10px 0;'>Mann-Kendall Test Results</p>
            """, unsafe_allow_html=True)
        
        with col2:
            sig_status = "Significant" if significant else "Not Significant"
            sig_color = "#28a745" if significant else "#6c757d"
            st.markdown(f"""
            <div style='text-align: center;'>
                <h3 style='color: {sig_color}; margin: 0;'>{sig_status}</h3>
                <p style='margin: 5px 0;'>p-value: {p_value:.4f}</p>
                <p style='margin: 5px 0;'>Kendall's τ: {tau:.3f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='text-align: center;'>
                <h3 style='color: white; margin: 0;'>Sample Size</h3>
                <p style='margin: 5px 0; font-size: 1.5em;'>{sample_size} points</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Interpretation
    _render_trend_interpretation(trend_results)
    
    # Time series visualization if data provided
    if time_series_data is not None and not time_series_data.empty:
        st.markdown("###  Time Series Visualization")
        
        # Simple line chart of the trend
        if 'date' in time_series_data.columns:
            numeric_cols = time_series_data.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) > 0:
                # Use the first numeric column for trend visualization
                col_name = numeric_cols[0]
                
                fig = px.line(
                    time_series_data, 
                    x='date', 
                    y=col_name,
                    title=f"{col_name.replace('_', ' ').title()} Over Time"
                )
                
                # Add trend line if significant
                if significant:
                    # Simple linear trendline
                    fig.add_traces(
                        px.scatter(time_series_data, x='date', y=col_name, trendline='ols')
                        .update_traces(showlegend=False)
                        .data[1:]
                    )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)


def _render_correlation_insight(correlation: Dict[str, Any], insight_number: int) -> None:
    """Render actionable insight for a correlation."""
    var1 = correlation['variable_1'].replace('_', ' ').title()
    var2 = correlation['variable_2'].replace('_', ' ').title()
    corr_value = correlation['correlation']
    
    # Generate insight based on variable pair (simplified)
    insights = {
        ('mood', 'sleep_quality'): {
            'positive': f"**Insight {insight_number}:** Better sleep quality is associated with improved mood. Consider optimizing your sleep routine for consistent mood benefits.",
            'negative': f"**Insight {insight_number}:** There may be factors affecting both mood and sleep quality simultaneously. Consider tracking environmental or lifestyle factors."
        },
        ('energy', 'activity_balance'): {
            'positive': f"**Insight {insight_number}:** Balanced activities correlate with higher energy levels. Maintain variety in your daily activities.",
            'negative': f"**Insight {insight_number}:** Imbalanced activities may be draining your energy. Consider redistributing your activity types."
        },
        'default': {
            'positive': f"**Insight {insight_number}:** {var1} and {var2} show a positive relationship (r={corr_value:.3f}). Improvements in one may benefit the other.",
            'negative': f"**Insight {insight_number}:** {var1} and {var2} show an inverse relationship (r={corr_value:.3f}). Consider the trade-offs between these factors."
        }
    }
    
    # Find matching insight
    var_key = tuple(sorted([var1.lower().replace(' ', '_'), var2.lower().replace(' ', '_')]))
    insight_text = insights.get(var_key, insights['default'])
    
    # Select positive or negative insight
    direction = 'positive' if corr_value > 0 else 'negative'
    text = insight_text[direction]
    
    # Use Streamlit's native markdown with custom CSS-like styling via containers
    with st.container():
        st.markdown(f"""
        <div style='
            background: #e7f3ff;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid #007bff;
            margin: 10px 0;
        '></div>
        """, unsafe_allow_html=True)
        
        # Use native markdown for proper formatting
        st.markdown(text)


def _render_trend_interpretation(trend_results: Dict[str, Any]) -> None:
    """Render trend interpretation and recommendations."""
    direction = trend_results.get('trend_direction', 'stable')
    significant = trend_results.get('significant', False)
    tau = trend_results.get('tau', 0.0)
    
    # Interpretation based on results
    if significant:
        if direction == 'improving':
            interpretation = "**Great news!** Your wellbeing metrics show a statistically significant improving trend. Whatever you've been doing lately is working well."
            recommendation = "**Recommendation:** Continue your current practices and consider identifying the specific factors driving this positive change."
        
        elif direction == 'declining':
            interpretation = "**Alert:** Your wellbeing metrics show a statistically significant declining trend. This warrants attention and possible lifestyle adjustments."
            recommendation = "**Recommendation:** Review recent changes in sleep, activities, or stress levels. Consider consulting the correlation insights for potential factors."
        
        else:  # stable but significant (edge case)
            interpretation = "**Steady state:** Your metrics are stable with some statistical variation detected."
            recommendation = "**Recommendation:** Maintain current routines while exploring opportunities for targeted improvements."
    
    else:
        interpretation = "**Stable pattern:** No significant trend detected in your wellbeing metrics. This suggests consistent patterns in your lifestyle."
        recommendation = "**Recommendation:** If you want to see changes, consider making deliberate adjustments to sleep, activities, or other tracked factors."
    
    # Effect size interpretation
    if abs(tau) > 0.3:
        strength = "strong"
    elif abs(tau) > 0.1:
        strength = "moderate"
    else:
        strength = "weak"
    
    # Use separate markdown blocks for proper formatting
    st.markdown(f"""
    <div style='
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 15px 0;
    '></div>
    """, unsafe_allow_html=True)
    
    # Use native markdown for proper bold text rendering
    st.markdown(interpretation)
    st.markdown(f"**Statistical Details:** Kendall's τ = {tau:.3f} indicates a {strength} trend magnitude.")
    st.markdown(recommendation)
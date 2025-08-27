"""Data Visualization Components for San-Xing Dashboard.

This module provides interactive Plotly visualizations for KPIs,
trends, and statistical analysis with consistent styling.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta


def create_kpi_gauge(value: float, max_value: float, title: str, 
                    thresholds: Optional[Dict[str, float]] = None,
                    color_scheme: str = "blue") -> go.Figure:
    """Create an interactive gauge chart for KPI display.
    
    Args:
        value: Current KPI value
        max_value: Maximum possible value
        title: Chart title
        thresholds: Optional dict with 'poor', 'fair', 'good' threshold values
        color_scheme: Color scheme ('blue', 'green', 'red', 'purple')
        
    Returns:
        Plotly Figure object
    """
    # Default thresholds if not provided
    if thresholds is None:
        thresholds = {
            'poor': max_value * 0.3,
            'fair': max_value * 0.7,
            'good': max_value * 0.9
        }
    
    # Color schemes
    color_schemes = {
        'blue': {'main': '#1f77b4', 'poor': '#ffebee', 'fair': '#fff3e0', 'good': '#e8f5e8'},
        'green': {'main': '#2ca02c', 'poor': '#ffebee', 'fair': '#fff3e0', 'good': '#e8f5e8'},
        'red': {'main': '#d62728', 'poor': '#ffebee', 'fair': '#fff3e0', 'good': '#e8f5e8'},
        'purple': {'main': '#9467bd', 'poor': '#ffebee', 'fair': '#fff3e0', 'good': '#e8f5e8'}
    }
    
    colors = color_schemes.get(color_scheme, color_schemes['blue'])
    
    # Create gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20, 'color': '#2c3e50'}},
        number={'font': {'size': 40, 'color': colors['main']}},
        gauge={
            'axis': {
                'range': [None, max_value], 
                'tickwidth': 2,
                'tickcolor': colors['main'],
                'tickfont': {'color': colors['main'], 'size': 12}
            },
            'bar': {'color': colors['main'], 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': colors['main'],
            'steps': [
                {'range': [0, thresholds['poor']], 'color': colors['poor']},
                {'range': [thresholds['poor'], thresholds['fair']], 'color': colors['fair']},
                {'range': [thresholds['fair'], max_value], 'color': colors['good']}
            ],
            'threshold': {
                'line': {'color': colors['main'], 'width': 6},
                'thickness': 0.8,
                'value': thresholds['good']
            }
        }
    ))
    
    # Update layout
    fig.update_layout(
        height=300,
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': "Arial, sans-serif"}
    )
    
    return fig


def create_trend_chart(data: pd.DataFrame, 
                      value_columns: List[str],
                      date_column: str = 'date',
                      title: str = "Trend Analysis",
                      show_trend_lines: bool = True,
                      height: int = 400) -> go.Figure:
    """Create an interactive trend chart with multiple series.
    
    Args:
        data: DataFrame with time series data
        value_columns: List of column names to plot
        date_column: Name of date column
        title: Chart title
        show_trend_lines: Whether to show trend lines
        height: Chart height in pixels
        
    Returns:
        Plotly Figure object
    """
    # Create subplots if multiple columns
    if len(value_columns) > 1:
        fig = make_subplots(
            rows=len(value_columns), 
            cols=1,
            subplot_titles=[col.replace('_', ' ').title() for col in value_columns],
            vertical_spacing=0.1
        )
    else:
        fig = go.Figure()
    
    # Color palette
    colors = px.colors.qualitative.Set2[:len(value_columns)]
    
    for i, col in enumerate(value_columns):
        if col not in data.columns:
            continue
        
        # Clean data
        plot_data = data[[date_column, col]].dropna()
        
        if plot_data.empty:
            continue
        
        # Main line
        if len(value_columns) > 1:
            fig.add_trace(
                go.Scatter(
                    x=plot_data[date_column],
                    y=plot_data[col],
                    mode='lines+markers',
                    name=col.replace('_', ' ').title(),
                    line=dict(color=colors[i], width=2),
                    marker=dict(size=4, color=colors[i]),
                    hovertemplate=f"<b>{col.replace('_', ' ').title()}</b><br>" +
                                 "Date: %{x}<br>" +
                                 "Value: %{y:.2f}<br>" +
                                 "<extra></extra>"
                ),
                row=i+1, 
                col=1
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=plot_data[date_column],
                    y=plot_data[col],
                    mode='lines+markers',
                    name=col.replace('_', ' ').title(),
                    line=dict(color=colors[i], width=3),
                    marker=dict(size=6, color=colors[i]),
                    hovertemplate=f"<b>{col.replace('_', ' ').title()}</b><br>" +
                                 "Date: %{x}<br>" +
                                 "Value: %{y:.2f}<br>" +
                                 "<extra></extra>"
                )
            )
        
        # Add trend line if requested
        if show_trend_lines and len(plot_data) >= 3:
            # Simple linear trend
            x_numeric = pd.to_numeric(pd.to_datetime(plot_data[date_column]))
            y_values = plot_data[col].values
            
            # Linear regression
            coeffs = np.polyfit(x_numeric, y_values, 1)
            trend_line = np.poly1d(coeffs)
            
            if len(value_columns) > 1:
                fig.add_trace(
                    go.Scatter(
                        x=plot_data[date_column],
                        y=trend_line(x_numeric),
                        mode='lines',
                        name=f"{col} Trend",
                        line=dict(color=colors[i], width=2, dash='dash'),
                        opacity=0.7,
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=i+1,
                    col=1
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=plot_data[date_column],
                        y=trend_line(x_numeric),
                        mode='lines',
                        name="Trend Line",
                        line=dict(color='rgba(255,0,0,0.6)', width=2, dash='dash'),
                        hovertemplate="Trend Line<br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>"
                    )
                )
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        height=height * len(value_columns) if len(value_columns) > 1 else height,
        showlegend=True,
        hovermode='x unified',
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    # Update axes
    if len(value_columns) == 1:
        fig.update_xaxes(title_text="Date", gridcolor='lightgray')
        fig.update_yaxes(title_text=value_columns[0].replace('_', ' ').title(), gridcolor='lightgray')
    else:
        for i in range(len(value_columns)):
            fig.update_xaxes(title_text="Date" if i == len(value_columns)-1 else "", 
                           gridcolor='lightgray', row=i+1, col=1)
            fig.update_yaxes(title_text=value_columns[i].replace('_', ' ').title(), 
                           gridcolor='lightgray', row=i+1, col=1)
    
    return fig


def create_correlation_heatmap(correlation_matrix: pd.DataFrame,
                              significance_data: Optional[Dict[str, Any]] = None,
                              title: str = "Correlation Heatmap") -> go.Figure:
    """Create an interactive correlation heatmap.
    
    Args:
        correlation_matrix: Pandas correlation matrix
        significance_data: Optional significance test results
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
    # Prepare data
    z_data = correlation_matrix.values
    x_labels = correlation_matrix.columns.tolist()
    y_labels = correlation_matrix.index.tolist()
    
    # Create custom hover text
    hover_text = []
    for i, y_var in enumerate(y_labels):
        hover_row = []
        for j, x_var in enumerate(x_labels):
            corr_value = z_data[i][j]
            
            # Add significance info if available
            sig_info = ""
            if significance_data and 'all_correlations' in significance_data:
                pair_key1 = f"{y_var}_vs_{x_var}"
                pair_key2 = f"{x_var}_vs_{y_var}"
                
                sig_result = (significance_data['all_correlations'].get(pair_key1) or 
                            significance_data['all_correlations'].get(pair_key2))
                
                if sig_result:
                    p_val = sig_result.get('p_value', 1.0)
                    if p_val < 0.001:
                        sig_info = " (p<0.001 ***)"
                    elif p_val < 0.01:
                        sig_info = " (p<0.01 **)"
                    elif p_val < 0.05:
                        sig_info = " (p<0.05 *)"
                    else:
                        sig_info = " (n.s.)"
            
            hover_text_cell = (f"<b>{y_var} vs {x_var}</b><br>"
                             f"Correlation: {corr_value:.3f}{sig_info}<br>"
                             f"<extra></extra>")
            hover_row.append(hover_text_cell)
        hover_text.append(hover_row)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_labels,
        y=y_labels,
        hovertemplate='%{hovertext}',
        hovertext=hover_text,
        colorscale='RdBu_r',
        zmid=0,
        zmin=-1,
        zmax=1,
        colorbar=dict(
            title="Correlation",
            tickmode="linear",
            tick0=-1,
            dtick=0.5
        )
    ))
    
    # Add correlation values as annotations
    annotations = []
    for i, y_var in enumerate(y_labels):
        for j, x_var in enumerate(x_labels):
            value = z_data[i][j]
            
            # Determine text color for readability
            text_color = "white" if abs(value) > 0.6 else "black"
            
            # Add significance stars if available
            star_text = ""
            if significance_data and 'all_correlations' in significance_data:
                pair_key1 = f"{y_var}_vs_{x_var}"
                pair_key2 = f"{x_var}_vs_{y_var}"
                
                sig_result = (significance_data['all_correlations'].get(pair_key1) or 
                            significance_data['all_correlations'].get(pair_key2))
                
                if sig_result:
                    p_val = sig_result.get('p_value', 1.0)
                    if p_val < 0.001:
                        star_text = "***"
                    elif p_val < 0.01:
                        star_text = "**"
                    elif p_val < 0.05:
                        star_text = "*"
            
            annotations.append(dict(
                x=j,
                y=i,
                text=f"{value:.2f}<br><sub>{star_text}</sub>",
                showarrow=False,
                font=dict(color=text_color, size=12)
            ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        annotations=annotations,
        height=min(600, 50 * len(y_labels) + 200),
        margin=dict(l=100, r=100, t=100, b=100),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_kpi_comparison_chart(kpi_history: List[Dict[str, Any]], 
                               kpi_names: List[str],
                               title: str = "KPI Comparison Over Time") -> go.Figure:
    """Create a comparison chart for multiple KPIs over time.
    
    Args:
        kpi_history: List of KPI calculation results with dates
        kpi_names: List of KPI names to display
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
    if not kpi_history:
        return go.Figure()
    
    # Create subplot with secondary y-axis for percentage values
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, kpi_name in enumerate(kpi_names):
        dates = []
        values = []
        confidence_values = []
        
        for entry in kpi_history:
            if 'date' in entry and kpi_name in entry:
                dates.append(entry['date'])
                kpi_data = entry[kpi_name]
                
                # Extract main value based on KPI type
                if kpi_name == 'wellbeing_score':
                    values.append(kpi_data.get('score', 0))
                elif kpi_name == 'balance_index':
                    values.append(kpi_data.get('index', 0))
                elif kpi_name == 'trend_indicator':
                    # Convert trend direction to numeric
                    direction = kpi_data.get('direction', 'stable')
                    magnitude = kpi_data.get('magnitude', 0)
                    trend_value = magnitude if direction == 'improving' else (-magnitude if direction == 'declining' else 0)
                    values.append(trend_value)
                
                confidence_values.append(kpi_data.get('confidence', 0))
        
        if not dates:
            continue
        
        # Determine which y-axis to use
        secondary_y = kpi_name == 'balance_index'  # Percentage values go on secondary axis
        
        # Main line
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name=kpi_name.replace('_', ' ').title(),
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=6),
                hovertemplate=f"<b>{kpi_name.replace('_', ' ').title()}</b><br>" +
                             "Date: %{x}<br>" +
                             "Value: %{y:.2f}<br>" +
                             "<extra></extra>"
            ),
            secondary_y=secondary_y
        )
        
        # Add confidence bands if data available
        if len(confidence_values) == len(values) and any(c > 0 for c in confidence_values):
            # Calculate confidence bands (simplified)
            upper_band = [v * (1 + (1 - c) * 0.1) for v, c in zip(values, confidence_values)]
            lower_band = [v * (1 - (1 - c) * 0.1) for v, c in zip(values, confidence_values)]
            
            fig.add_trace(
                go.Scatter(
                    x=dates + dates[::-1],
                    y=upper_band + lower_band[::-1],
                    fill='toself',
                    fillcolor=f'rgba{tuple([int(colors[i % len(colors)][j:j+2], 16) for j in range(1, 7, 2)] + [0.2])}',
                    line=dict(color='rgba(255,255,255,0)'),
                    name=f'{kpi_name} Confidence',
                    showlegend=False,
                    hoverinfo='skip'
                ),
                secondary_y=secondary_y
            )
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        height=500,
        hovermode='x unified',
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes
    fig.update_xaxes(title_text="Date", gridcolor='lightgray')
    fig.update_yaxes(title_text="Wellbeing Score / Trend", gridcolor='lightgray', secondary_y=False)
    fig.update_yaxes(title_text="Balance Index (%)", gridcolor='lightgray', secondary_y=True)
    
    return fig


def create_statistical_summary_chart(data: pd.DataFrame, 
                                    columns: List[str],
                                    chart_type: str = "box") -> go.Figure:
    """Create a statistical summary visualization.
    
    Args:
        data: DataFrame with the data to summarize
        columns: List of columns to include
        chart_type: Type of chart ('box', 'violin', 'histogram')
        
    Returns:
        Plotly Figure object
    """
    if chart_type == "box":
        fig = go.Figure()
        
        for col in columns:
            if col in data.columns:
                fig.add_trace(go.Box(
                    y=data[col].dropna(),
                    name=col.replace('_', ' ').title(),
                    boxpoints='outliers',
                    jitter=0.3,
                    pointpos=-1.8,
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                 "Value: %{y:.2f}<br>" +
                                 "<extra></extra>"
                ))
        
        fig.update_layout(
            title="Statistical Distribution Summary",
            yaxis_title="Values",
            height=400
        )
    
    elif chart_type == "violin":
        fig = go.Figure()
        
        for col in columns:
            if col in data.columns:
                fig.add_trace(go.Violin(
                    y=data[col].dropna(),
                    name=col.replace('_', ' ').title(),
                    box_visible=True,
                    meanline_visible=True,
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                 "Value: %{y:.2f}<br>" +
                                 "<extra></extra>"
                ))
        
        fig.update_layout(
            title="Distribution Shapes",
            yaxis_title="Values", 
            height=400
        )
    
    elif chart_type == "histogram":
        fig = make_subplots(
            rows=len(columns),
            cols=1,
            subplot_titles=[col.replace('_', ' ').title() for col in columns],
            vertical_spacing=0.1
        )
        
        colors = px.colors.qualitative.Set2[:len(columns)]
        
        for i, col in enumerate(columns):
            if col in data.columns:
                fig.add_trace(
                    go.Histogram(
                        x=data[col].dropna(),
                        name=col.replace('_', ' ').title(),
                        nbinsx=20,
                        marker_color=colors[i],
                        opacity=0.7,
                        showlegend=False
                    ),
                    row=i+1,
                    col=1
                )
        
        fig.update_layout(
            title="Distribution Histograms",
            height=300 * len(columns)
        )
    
    # Common layout updates
    fig.update_layout(
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': "Arial, sans-serif"}
    )
    
    return fig


def create_sleep_quality_comparison(sleep_data: Dict[str, Any], 
                                   historical_data: Optional[pd.DataFrame] = None,
                                   title: str = "Sleep Quality Analysis") -> go.Figure:
    """Create a visualization comparing subjective and objective sleep quality.
    
    Args:
        sleep_data: Sleep quality analysis results from KPICalculator
        historical_data: Optional DataFrame with historical sleep data
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
    if 'error' in sleep_data:
        # Create empty figure with error message
        fig = go.Figure()
        fig.add_annotation(
            text=f"Sleep Quality Data Error:<br>{sleep_data['error']}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title=title,
            height=300,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        return fig
    
    # Extract data
    subjective_avg = sleep_data.get('subjective_avg')
    objective_data = sleep_data.get('objective_quality', {})
    objective_quality = objective_data.get('objective_sleep_quality')
    correlation = sleep_data.get('comparison', {}).get('correlation')
    
    # Create comparison chart
    fig = go.Figure()
    
    if subjective_avg is not None and objective_quality is not None:
        # Both ratings available - create comparison
        categories = ['Subjective Rating', 'Objective Score']
        values = [subjective_avg, objective_quality]
        colors = ['#6f42c1', '#28a745']
        
        # Add bars
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f"{val:.1f}/5" for val in values],
            textposition='auto',
            hovertemplate="<b>%{x}</b><br>Rating: %{y:.2f}/5<extra></extra>"
        ))
        
        # Add correlation annotation if available
        if correlation is not None:
            correlation_desc = "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.3 else "Weak"
            fig.add_annotation(
                x=0.5, y=max(values) * 0.8,
                xref="x", yref="y",
                text=f"Agreement: {correlation_desc}<br>(r = {correlation:.3f})",
                showarrow=False,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="gray",
                borderwidth=1,
                font=dict(size=12)
            )
        
        fig.update_layout(
            yaxis=dict(range=[0, 5], title="Sleep Quality Rating"),
            xaxis_title="Rating Type"
        )
    
    elif subjective_avg is not None:
        # Only subjective rating
        fig.add_trace(go.Bar(
            x=['Subjective Rating'],
            y=[subjective_avg],
            marker_color='#6f42c1',
            text=f"{subjective_avg:.1f}/5",
            textposition='auto',
            hovertemplate="<b>Subjective Rating</b><br>Rating: %{y:.2f}/5<extra></extra>"
        ))
        
        fig.update_layout(
            yaxis=dict(range=[0, 5], title="Sleep Quality Rating"),
            xaxis_title="Rating Type"
        )
    
    elif objective_quality is not None:
        # Only objective rating
        fig.add_trace(go.Bar(
            x=['Objective Score'],
            y=[objective_quality],
            marker_color='#28a745',
            text=f"{objective_quality:.1f}/5",
            textposition='auto',
            hovertemplate="<b>Objective Score</b><br>Rating: %{y:.2f}/5<extra></extra>"
        ))
        
        fig.update_layout(
            yaxis=dict(range=[0, 5], title="Sleep Quality Rating"),
            xaxis_title="Rating Type"
        )
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig


def create_sleep_components_radar(objective_data: Dict[str, Any],
                                 title: str = "Sleep Quality Components") -> go.Figure:
    """Create a radar chart showing objective sleep quality components.
    
    Args:
        objective_data: Objective sleep quality data from SleepQualityCalculator
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
    if 'components' not in objective_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No component data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    components = objective_data['components']
    
    # Map component keys to display names
    component_mapping = {
        'duration_score': 'Duration',
        'timing_score': 'Timing',
        'regularity_score': 'Regularity', 
        'efficiency_score': 'Efficiency'
    }
    
    # Extract values (convert from 0-1 to 0-100 scale for better visualization)
    values = []
    actual_names = []
    
    for comp_key, display_name in component_mapping.items():
        if comp_key in components:
            values.append(components[comp_key] * 100)  # Convert to percentage
            actual_names.append(display_name)
    
    if not values:
        fig = go.Figure()
        fig.add_annotation(
            text="No component scores available",
            xref="paper", yref="paper", 
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # Close the polygon
        theta=actual_names + [actual_names[0]], 
        fill='toself',
        fillcolor='rgba(40, 167, 69, 0.3)',
        line_color='rgba(40, 167, 69, 0.8)',
        line_width=3,
        marker=dict(size=8, color='rgba(40, 167, 69, 1)'),
        name='Sleep Quality',
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.1f}%<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickmode='linear',
                tick0=0,
                dtick=20,
                ticksuffix='%'
            ),
            angularaxis=dict(
                tickfont=dict(size=12)
            )
        ),
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig


def create_sleep_timing_chart(data: pd.DataFrame, 
                             title: str = "Sleep Timing Patterns") -> go.Figure:
    """Create a visualization showing sleep timing patterns over time.
    
    Args:
        data: DataFrame with sleep timing data (sleep_bedtime, wake_time, logical_date)
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
    # Filter data with both bedtime and wake time
    sleep_data = data.dropna(subset=['sleep_bedtime', 'wake_time']).copy()
    
    if sleep_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No sleep timing data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Convert time strings to datetime for plotting
    def time_to_minutes(time_str):
        """Convert HH:MM to minutes since midnight"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except:
            return None
    
    sleep_data['bedtime_minutes'] = sleep_data['sleep_bedtime'].apply(time_to_minutes)
    sleep_data['wake_minutes'] = sleep_data['wake_time'].apply(time_to_minutes)
    
    # Remove invalid conversions
    sleep_data = sleep_data.dropna(subset=['bedtime_minutes', 'wake_minutes'])
    
    if sleep_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Could not parse sleep timing data",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Create the plot
    fig = go.Figure()
    
    # Add bedtime line
    fig.add_trace(go.Scatter(
        x=sleep_data['logical_date'],
        y=sleep_data['bedtime_minutes'],
        mode='lines+markers',
        name='Bedtime',
        line=dict(color='#dc3545', width=2),
        marker=dict(size=6),
        hovertemplate="<b>Bedtime</b><br>Date: %{x}<br>Time: %{text}<extra></extra>",
        text=sleep_data['sleep_bedtime']
    ))
    
    # Add wake time line
    fig.add_trace(go.Scatter(
        x=sleep_data['logical_date'],
        y=sleep_data['wake_minutes'],
        mode='lines+markers',
        name='Wake Time',
        line=dict(color='#ffc107', width=2),
        marker=dict(size=6),
        hovertemplate="<b>Wake Time</b><br>Date: %{x}<br>Time: %{text}<extra></extra>",
        text=sleep_data['wake_time']
    ))
    
    # Add optimal ranges as shaded areas
    fig.add_hrect(
        y0=22*60, y1=24*60,  # 10 PM to midnight
        fillcolor="rgba(40, 167, 69, 0.2)",
        layer="below",
        line_width=0,
        annotation_text="Optimal Bedtime",
        annotation_position="left"
    )
    
    fig.add_hrect(
        y0=6*60, y1=8*60,  # 6 AM to 8 AM
        fillcolor="rgba(255, 193, 7, 0.2)",
        layer="below", 
        line_width=0,
        annotation_text="Optimal Wake Time",
        annotation_position="left"
    )
    
    # Update layout with custom y-axis formatting
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        xaxis_title="Date",
        yaxis_title="Time of Day",
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right", 
            x=1
        )
    )
    
    # Custom y-axis with time labels
    time_ticks = []
    time_labels = []
    
    # Create 4-hour intervals
    for hour in range(0, 24, 4):
        time_ticks.append(hour * 60)
        time_labels.append(f"{hour:02d}:00")
    
    # Add midnight and noon markers
    time_ticks.extend([0, 12*60])
    time_labels.extend(["00:00", "12:00"])
    
    fig.update_yaxes(
        tickmode='array',
        tickvals=sorted(set(time_ticks)),
        ticktext=[time_labels[i] for i, _ in enumerate(sorted(set(time_ticks)))],
        gridcolor='lightgray'
    )
    
    fig.update_xaxes(gridcolor='lightgray')
    
    return fig
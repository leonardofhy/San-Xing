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
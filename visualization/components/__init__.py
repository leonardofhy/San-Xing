"""UI Components for San-Xing Dashboard.

This module contains reusable Streamlit components for displaying KPIs,
insights, and statistical analysis with consistent styling and behavior.
"""

from .kpi_cards import (
    render_wellbeing_card,
    render_balance_card, 
    render_trend_card,
    render_kpi_overview
)

from .insight_display import (
    render_statistical_insights,
    render_correlation_matrix,
    render_trend_analysis
)

from .data_viz import (
    create_kpi_gauge,
    create_trend_chart,
    create_correlation_heatmap
)

__all__ = [
    'render_wellbeing_card',
    'render_balance_card',
    'render_trend_card', 
    'render_kpi_overview',
    'render_statistical_insights',
    'render_correlation_matrix',
    'render_trend_analysis',
    'create_kpi_gauge',
    'create_trend_chart',
    'create_correlation_heatmap'
]
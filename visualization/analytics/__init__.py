"""Analytics module for San-Xing visualization dashboard.

This module provides statistical analysis, KPI calculations, and insight generation
for the San-Xing personal analytics system.
"""

from .kpi_calculator import KPICalculator
from .insight_engine import InsightEngine
from .statistical_utils import (
    calculate_significance,
    minimum_sample_size_check,
    correlation_with_significance,
    trend_significance
)

__all__ = [
    'KPICalculator',
    'InsightEngine', 
    'calculate_significance',
    'minimum_sample_size_check',
    'correlation_with_significance',
    'trend_significance'
]
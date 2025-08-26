"""Unit tests for UI Components."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from components.data_viz import (
    create_kpi_gauge,
    create_trend_chart,
    create_correlation_heatmap,
    create_statistical_summary_chart
)
from analytics.kpi_calculator import KPICalculator
from analytics.statistical_utils import correlation_with_significance


class TestDataVisualization:
    """Test cases for data visualization components."""
    
    def setup_method(self):
        """Set up test data."""
        np.random.seed(42)
        dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
        
        self.test_data = pd.DataFrame({
            'date': dates,
            'mood': np.random.normal(6.5, 1.5, 30).clip(1, 10).round(1),
            'energy': np.random.normal(6.0, 1.2, 30).clip(1, 10).round(1),
            'sleep_quality': np.random.normal(7.0, 1.0, 30).clip(1, 10).round(1),
            'sleep_duration': np.random.normal(7.5, 0.8, 30).clip(4, 12).round(1)
        })
        
        self.kpis = KPICalculator.calculate_all_kpis(self.test_data)
    
    def test_create_kpi_gauge(self):
        """Test KPI gauge chart creation."""
        fig = create_kpi_gauge(
            value=7.5,
            max_value=10,
            title="Test Gauge",
            color_scheme="blue"
        )
        
        assert fig is not None
        assert fig.data[0].value == 7.5
        assert fig.data[0].gauge['axis']['range'] == (None, 10)
        assert "Test Gauge" in fig.data[0].title['text']
    
    def test_create_trend_chart(self):
        """Test trend chart creation."""
        fig = create_trend_chart(
            data=self.test_data,
            value_columns=['mood', 'energy'],
            date_column='date',
            title="Test Trends"
        )
        
        assert fig is not None
        assert len(fig.data) >= 2  # At least 2 traces for 2 columns
        assert fig.layout.title.text == "Test Trends"
    
    def test_create_trend_chart_single_column(self):
        """Test trend chart with single column."""
        fig = create_trend_chart(
            data=self.test_data,
            value_columns=['mood'],
            date_column='date',
            show_trend_lines=True
        )
        
        assert fig is not None
        assert len(fig.data) >= 1  # At least 1 trace
    
    def test_create_correlation_heatmap(self):
        """Test correlation heatmap creation."""
        corr_matrix = self.test_data[['mood', 'energy', 'sleep_quality']].corr()
        
        fig = create_correlation_heatmap(
            correlation_matrix=corr_matrix,
            title="Test Correlation"
        )
        
        assert fig is not None
        assert fig.data[0].z.shape == (3, 3)  # 3x3 correlation matrix
        assert fig.layout.title.text == "Test Correlation"
    
    def test_create_statistical_summary_box(self):
        """Test statistical summary with box plots."""
        fig = create_statistical_summary_chart(
            data=self.test_data,
            columns=['mood', 'energy'],
            chart_type="box"
        )
        
        assert fig is not None
        assert len(fig.data) == 2  # 2 box plots
    
    def test_create_statistical_summary_violin(self):
        """Test statistical summary with violin plots."""
        fig = create_statistical_summary_chart(
            data=self.test_data,
            columns=['mood', 'energy'],
            chart_type="violin"
        )
        
        assert fig is not None
        assert len(fig.data) == 2  # 2 violin plots
    
    def test_create_statistical_summary_histogram(self):
        """Test statistical summary with histograms."""
        fig = create_statistical_summary_chart(
            data=self.test_data,
            columns=['mood', 'energy'],
            chart_type="histogram"
        )
        
        assert fig is not None
        assert len(fig.data) == 2  # 2 histograms


class TestComponentIntegration:
    """Test integration between components and analytics."""
    
    def setup_method(self):
        """Set up test data."""
        np.random.seed(42)
        dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
        
        self.test_data = pd.DataFrame({
            'date': dates,
            'mood': np.random.normal(6.5, 1.5, 30).clip(1, 10).round(1),
            'energy': np.random.normal(6.0, 1.2, 30).clip(1, 10).round(1),
            'sleep_quality': np.random.normal(7.0, 1.0, 30).clip(1, 10).round(1),
            'sleep_duration': np.random.normal(7.5, 0.8, 30).clip(4, 12).round(1),
            'activity_balance': np.random.randint(-3, 4, 30)
        })
    
    def test_kpi_to_visualization_pipeline(self):
        """Test complete pipeline from KPI calculation to visualization."""
        # Calculate KPIs
        kpis = KPICalculator.calculate_all_kpis(self.test_data)
        
        # Create visualizations for each KPI
        wellbeing_gauge = create_kpi_gauge(
            value=kpis['wellbeing_score']['score'],
            max_value=10,
            title="Wellbeing Score"
        )
        
        balance_gauge = create_kpi_gauge(
            value=kpis['balance_index']['index'],
            max_value=100,
            title="Balance Index"
        )
        
        # Verify both charts are created successfully
        assert wellbeing_gauge is not None
        assert balance_gauge is not None
        assert wellbeing_gauge.data[0].value == kpis['wellbeing_score']['score']
        assert balance_gauge.data[0].value == kpis['balance_index']['index']
    
    def test_statistical_to_visualization_pipeline(self):
        """Test pipeline from statistical analysis to visualization."""
        # Calculate correlations
        correlations = correlation_with_significance(
            self.test_data.select_dtypes(include=[np.number])
        )
        
        # Create correlation heatmap
        corr_matrix = self.test_data[['mood', 'energy', 'sleep_quality']].corr()
        heatmap = create_correlation_heatmap(
            correlation_matrix=corr_matrix,
            significance_data=correlations
        )
        
        # Verify heatmap is created with significance data
        assert heatmap is not None
        assert len(heatmap.data) >= 1  # At least heatmap trace
        assert len(heatmap.layout.annotations) > 0  # Correlation annotations
    
    def test_trend_analysis_integration(self):
        """Test trend analysis integration with visualizations."""
        # Create trend chart
        trend_chart = create_trend_chart(
            data=self.test_data,
            value_columns=['mood', 'energy', 'sleep_quality'],
            date_column='date',
            show_trend_lines=True
        )
        
        # Verify trend chart with trend lines
        assert trend_chart is not None
        assert len(trend_chart.data) >= 3  # At least 3 main traces
        
        # Should have additional trend line traces
        total_traces = len(trend_chart.data)
        assert total_traces >= 6  # 3 main + 3 trend lines
    
    def test_empty_data_handling(self):
        """Test handling of empty or invalid data."""
        empty_data = pd.DataFrame()
        
        # Should handle empty data gracefully
        fig = create_statistical_summary_chart(
            data=empty_data,
            columns=['nonexistent'],
            chart_type="box"
        )
        
        assert fig is not None  # Should not crash
    
    def test_missing_columns_handling(self):
        """Test handling of missing columns in data."""
        # Create chart with non-existent columns
        fig = create_trend_chart(
            data=self.test_data,
            value_columns=['nonexistent_column'],
            date_column='date'
        )
        
        assert fig is not None  # Should not crash
        # Should have minimal or no data traces
        assert len(fig.data) >= 0


class TestChartConfigurations:
    """Test various chart configuration options."""
    
    def setup_method(self):
        """Set up test data."""
        np.random.seed(42)
        self.test_data = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=20, freq='D'),
            'metric1': np.random.normal(5, 1, 20),
            'metric2': np.random.normal(7, 1.5, 20)
        })
    
    def test_gauge_color_schemes(self):
        """Test different color schemes for gauge charts."""
        color_schemes = ['blue', 'green', 'red', 'purple']
        
        for scheme in color_schemes:
            fig = create_kpi_gauge(
                value=5.0,
                max_value=10,
                title=f"Test {scheme}",
                color_scheme=scheme
            )
            
            assert fig is not None
            assert fig.data[0].value == 5.0
    
    def test_gauge_thresholds(self):
        """Test custom thresholds for gauge charts."""
        custom_thresholds = {
            'poor': 3.0,
            'fair': 6.0,
            'good': 8.5
        }
        
        fig = create_kpi_gauge(
            value=7.0,
            max_value=10,
            title="Custom Thresholds",
            thresholds=custom_thresholds
        )
        
        assert fig is not None
        assert fig.data[0].value == 7.0
        # Verify custom thresholds are applied
        steps = fig.data[0].gauge.steps
        assert len(steps) == 3  # Three threshold ranges
    
    def test_trend_chart_heights(self):
        """Test different heights for trend charts."""
        heights = [300, 500, 800]
        
        for height in heights:
            fig = create_trend_chart(
                data=self.test_data,
                value_columns=['metric1'],
                height=height
            )
            
            assert fig is not None
            assert fig.layout.height == height


if __name__ == '__main__':
    # Allow running tests directly
    pytest.main([__file__, '-v'])
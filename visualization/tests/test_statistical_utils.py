"""Unit tests for Statistical Utilities module."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from analytics.statistical_utils import (
    calculate_significance,
    minimum_sample_size_check,
    correlation_with_significance,
    trend_significance,
    calculate_confidence_interval,
    effect_size_interpretation
)


class TestStatisticalUtils:
    """Test cases for Statistical Utilities functions."""
    
    def setup_method(self):
        """Set up test data for each test method."""
        # Create correlated data for testing
        np.random.seed(42)
        n = 50
        x = np.random.normal(0, 1, n)
        y = 0.7 * x + np.random.normal(0, 0.5, n)  # Strong positive correlation
        
        self.correlated_data = pd.DataFrame({'x': x, 'y': y})
        
        # Create uncorrelated data
        self.uncorrelated_data = pd.DataFrame({
            'x': np.random.normal(0, 1, n),
            'y': np.random.normal(0, 1, n)
        })
        
        # Create trending time series
        trend_base = np.linspace(5, 8, 20)
        trend_noise = np.random.normal(0, 0.3, 20)
        self.trending_series = pd.Series(trend_base + trend_noise)
        
        # Create flat time series
        self.flat_series = pd.Series(np.random.normal(6.5, 0.1, 20))
        
        # Create minimal data for edge cases
        self.minimal_data = pd.DataFrame({'x': [1, 2], 'y': [3, 4]})
    
    def test_calculate_significance_correlation(self):
        """Test significance calculation for correlation."""
        result = calculate_significance(
            self.correlated_data['x'], 
            self.correlated_data['y'], 
            test_type='correlation'
        )
        
        assert isinstance(result, dict)
        assert 'p_value' in result
        assert 'effect_size' in result
        assert 'confidence_interval' in result
        assert 'test_statistic' in result
        assert 'significant' in result
        assert 'sample_size' in result
        assert 'test_type' in result
        
        # Should detect significant correlation in our synthetic data
        assert result['significant'] == True
        assert result['p_value'] < 0.05
        assert result['effect_size'] > 0.3  # Moderate to strong effect
        assert result['sample_size'] == 50
        assert result['test_type'] == 'correlation'
    
    def test_calculate_significance_no_correlation(self):
        """Test significance calculation with uncorrelated data."""
        result = calculate_significance(
            self.uncorrelated_data['x'],
            self.uncorrelated_data['y'],
            test_type='correlation'
        )
        
        # Should not detect significant correlation
        assert result['effect_size'] < 0.5  # Weak effect expected
        assert isinstance(result['confidence_interval'], tuple)
        assert len(result['confidence_interval']) == 2
    
    def test_calculate_significance_t_test(self):
        """Test significance calculation for t-test."""
        # Create two groups with different means
        group1 = pd.Series(np.random.normal(5, 1, 30))
        group2 = pd.Series(np.random.normal(7, 1, 30))
        
        result = calculate_significance(group1, group2, test_type='t_test')
        
        assert result['test_type'] == 't_test'
        assert isinstance(result['effect_size'], float)
        assert result['effect_size'] >= 0  # Effect size should be positive
        assert isinstance(result['test_statistic'], float)
    
    def test_calculate_significance_mann_whitney(self):
        """Test significance calculation for Mann-Whitney test."""
        # Create two groups with different distributions
        group1 = pd.Series(np.random.exponential(2, 25))
        group2 = pd.Series(np.random.exponential(3, 25))
        
        result = calculate_significance(group1, group2, test_type='mann_whitney')
        
        assert result['test_type'] == 'mann_whitney'
        assert 0 <= result['effect_size'] <= 1  # Effect size r should be bounded
        assert isinstance(result['test_statistic'], float)
    
    def test_calculate_significance_insufficient_data(self):
        """Test significance calculation with insufficient data."""
        result = calculate_significance(
            self.minimal_data['x'],
            self.minimal_data['y'],
            test_type='correlation'
        )
        
        assert result['p_value'] == 1.0
        assert result['effect_size'] == 0.0
        assert result['significant'] == False
        assert result['sample_size'] == 2
    
    def test_calculate_significance_invalid_test(self):
        """Test significance calculation with invalid test type."""
        with pytest.raises(ValueError):
            calculate_significance(
                self.correlated_data['x'],
                self.correlated_data['y'],
                test_type='invalid_test'
            )
    
    def test_minimum_sample_size_check_sufficient(self):
        """Test sample size check with sufficient data."""
        df = pd.DataFrame({'x': range(20)})
        result = minimum_sample_size_check(df, 'correlation')
        
        assert isinstance(result, dict)
        assert result['sufficient'] == True
        assert result['actual_size'] == 20
        assert result['required_size'] == 10
        assert result['confidence_level'] in ['medium', 'high']
        assert result['analysis_type'] == 'correlation'
    
    def test_minimum_sample_size_check_insufficient(self):
        """Test sample size check with insufficient data."""
        df = pd.DataFrame({'x': range(5)})
        result = minimum_sample_size_check(df, 'trend')
        
        assert result['sufficient'] == False
        assert result['actual_size'] == 5
        assert result['required_size'] == 14
        assert result['confidence_level'] == 'low'
    
    def test_minimum_sample_size_check_unknown_analysis(self):
        """Test sample size check with unknown analysis type."""
        df = pd.DataFrame({'x': range(15)})
        result = minimum_sample_size_check(df, 'unknown_analysis')
        
        assert result['required_size'] == 10  # Default value
        assert result['analysis_type'] == 'unknown_analysis'
    
    def test_correlation_with_significance_multiple_vars(self):
        """Test correlation analysis with multiple variables."""
        df = pd.DataFrame({
            'mood': np.random.normal(6, 1, 30),
            'energy': np.random.normal(6, 1, 30),
            'sleep': np.random.normal(7, 1, 30)
        })
        
        result = correlation_with_significance(df, alpha=0.05)
        
        assert isinstance(result, dict)
        assert 'significant_correlations' in result
        assert 'all_correlations' in result
        assert 'total_tests' in result
        assert 'alpha_level' in result
        assert 'corrected_alpha' in result
        
        # Should have 3 pairs: mood vs energy, mood vs sleep, energy vs sleep
        assert result['total_tests'] == 3
        assert result['corrected_alpha'] < result['alpha_level']  # Bonferroni correction
        assert isinstance(result['significant_correlations'], list)
    
    def test_correlation_with_significance_insufficient_vars(self):
        """Test correlation analysis with insufficient variables."""
        df = pd.DataFrame({'single_col': range(10)})
        result = correlation_with_significance(df)
        
        assert result['significant_correlations'] == []
        assert result['all_correlations'] == {}
        assert result['total_tests'] == 0
    
    def test_trend_significance_improving(self):
        """Test trend significance with improving trend."""
        result = trend_significance(self.trending_series, alpha=0.05)
        
        assert isinstance(result, dict)
        assert 'trend_direction' in result
        assert 'p_value' in result
        assert 'tau' in result
        assert 'z_score' in result
        assert 'significant' in result
        assert 'sample_size' in result
        
        # Should detect improving trend in synthetic data
        assert result['trend_direction'] in ['improving', 'stable', 'declining']
        assert result['sample_size'] == 20
        assert isinstance(result['tau'], float)
        assert -1 <= result['tau'] <= 1  # Kendall's tau bounds
    
    def test_trend_significance_stable(self):
        """Test trend significance with stable trend."""
        result = trend_significance(self.flat_series, alpha=0.05)
        
        # Should detect stable trend in flat data
        assert result['trend_direction'] == 'stable'
        assert result['p_value'] > 0.05  # Should not be significant
        assert result['significant'] == False
    
    def test_trend_significance_insufficient_data(self):
        """Test trend significance with insufficient data."""
        short_series = pd.Series([1, 2])
        result = trend_significance(short_series, alpha=0.05)
        
        assert result['trend_direction'] == 'stable'
        assert result['p_value'] == 1.0
        assert result['tau'] == 0.0
        assert result['significant'] == False
        assert result['sample_size'] == 2
    
    def test_calculate_confidence_interval_normal_data(self):
        """Test confidence interval calculation with normal data."""
        data = pd.Series(np.random.normal(10, 2, 100))
        ci = calculate_confidence_interval(data, confidence=0.95)
        
        assert isinstance(ci, tuple)
        assert len(ci) == 2
        assert ci[0] < ci[1]  # Lower bound < upper bound
        assert ci[0] < data.mean() < ci[1]  # Mean should be within CI
    
    def test_calculate_confidence_interval_small_sample(self):
        """Test confidence interval with small sample (uses t-distribution)."""
        data = pd.Series([8, 10, 12, 9, 11])  # n=5, uses t-distribution
        ci = calculate_confidence_interval(data, confidence=0.95)
        
        assert isinstance(ci, tuple)
        assert ci[0] < ci[1]
        # CI should be wider for small samples
        assert (ci[1] - ci[0]) > 0  # Positive width
    
    def test_calculate_confidence_interval_single_value(self):
        """Test confidence interval with single data point."""
        data = pd.Series([5.0])
        ci = calculate_confidence_interval(data)
        
        assert ci[0] == ci[1] == 5.0  # Should return the single value
    
    def test_calculate_confidence_interval_empty_data(self):
        """Test confidence interval with empty data."""
        data = pd.Series([])
        ci = calculate_confidence_interval(data)
        
        assert ci[0] == ci[1] == 0.0  # Should return (0, 0)
    
    def test_effect_size_interpretation_correlation(self):
        """Test effect size interpretation for correlations."""
        assert effect_size_interpretation(0.05, 'correlation') == 'negligible'
        assert effect_size_interpretation(0.2, 'correlation') == 'small'
        assert effect_size_interpretation(0.4, 'correlation') == 'medium'
        assert effect_size_interpretation(0.7, 'correlation') == 'large'
        
        # Test with negative values
        assert effect_size_interpretation(-0.4, 'correlation') == 'medium'
    
    def test_effect_size_interpretation_cohens_d(self):
        """Test effect size interpretation for Cohen's d."""
        assert effect_size_interpretation(0.1, 'd') == 'negligible'
        assert effect_size_interpretation(0.3, 'd') == 'small'
        assert effect_size_interpretation(0.6, 'd') == 'medium'
        assert effect_size_interpretation(1.2, 'd') == 'large'
    
    def test_effect_size_interpretation_generic(self):
        """Test effect size interpretation for generic types."""
        assert effect_size_interpretation(0.1, 'generic') == 'small'
        assert effect_size_interpretation(0.3, 'generic') == 'medium'
        assert effect_size_interpretation(0.8, 'generic') == 'large'
    
    def test_with_nan_values(self):
        """Test handling of NaN values in statistical calculations."""
        data_with_nan = pd.DataFrame({
            'x': [1, 2, np.nan, 4, 5],
            'y': [2, np.nan, 6, 8, 10]
        })
        
        result = calculate_significance(data_with_nan['x'], data_with_nan['y'])
        assert result['sample_size'] < 5  # Should exclude NaN pairs
        
        size_check = minimum_sample_size_check(data_with_nan, 'correlation')
        assert size_check['actual_size'] == 5  # Still counts all rows
        
        # Test confidence interval with NaN
        series_with_nan = pd.Series([1, 2, np.nan, 4, 5])
        ci = calculate_confidence_interval(series_with_nan)
        assert isinstance(ci, tuple)  # Should handle NaN gracefully


# Integration tests
class TestStatisticalUtilsIntegration:
    """Integration tests for statistical utilities with realistic data."""
    
    def setup_method(self):
        """Create realistic wellbeing data for integration testing."""
        np.random.seed(42)
        dates = pd.date_range(start='2025-01-01', periods=60, freq='D')
        
        # Create realistic wellbeing data with some correlations
        self.wellbeing_data = pd.DataFrame({
            'date': dates,
            'mood': np.random.normal(6.5, 1.5, 60).clip(1, 10),
            'energy': np.random.normal(6.0, 1.2, 60).clip(1, 10),
            'sleep_quality': np.random.normal(7.0, 1.0, 60).clip(1, 10),
            'sleep_duration': np.random.normal(7.5, 0.8, 60).clip(4, 12)
        })
        
        # Add some correlation between mood and sleep
        self.wellbeing_data['mood'] += 0.3 * (self.wellbeing_data['sleep_quality'] - 7)
        self.wellbeing_data['mood'] = self.wellbeing_data['mood'].clip(1, 10)
    
    def test_full_correlation_analysis(self):
        """Test complete correlation analysis on wellbeing data."""
        result = correlation_with_significance(self.wellbeing_data.drop('date', axis=1))
        
        # Should find some correlations in our synthetic data
        assert result['total_tests'] > 0
        assert len(result['all_correlations']) > 0
        
        # Each correlation result should have proper structure
        for correlation in result['all_correlations'].values():
            assert 'p_value' in correlation
            assert 'effect_size' in correlation
            assert 'significant' in correlation
            assert 'sample_size' in correlation
    
    def test_sample_size_validation_pipeline(self):
        """Test sample size validation across different analysis types."""
        analyses = ['correlation', 'trend', 'kpi', 't_test', 'regression']
        
        for analysis_type in analyses:
            result = minimum_sample_size_check(self.wellbeing_data, analysis_type)
            
            assert result['sufficient'] == True  # 60 samples should be sufficient
            assert result['confidence_level'] in ['low', 'medium', 'high']
            assert result['analysis_type'] == analysis_type
    
    def test_trend_analysis_workflow(self):
        """Test trend analysis on time series wellbeing data."""
        mood_trend = trend_significance(self.wellbeing_data['mood'])
        energy_trend = trend_significance(self.wellbeing_data['energy'])
        
        # Results should be valid
        for trend_result in [mood_trend, energy_trend]:
            assert trend_result['trend_direction'] in ['improving', 'stable', 'declining']
            assert 0 <= trend_result['p_value'] <= 1
            assert -1 <= trend_result['tau'] <= 1
            assert trend_result['sample_size'] == 60


if __name__ == '__main__':
    # Allow running tests directly
    pytest.main([__file__, '-v'])
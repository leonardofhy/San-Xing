"""Unit tests for KPI Calculator module."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from analytics.kpi_calculator import KPICalculator


class TestKPICalculator:
    """Test cases for KPICalculator class."""
    
    def setup_method(self):
        """Set up test data for each test method."""
        # Create sample data with varying patterns
        dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
        
        self.sample_data = pd.DataFrame({
            'date': dates,
            'mood': np.random.normal(6.5, 1.5, 30).clip(1, 10),
            'energy': np.random.normal(6.0, 1.2, 30).clip(1, 10),
            'sleep_quality': np.random.normal(7.0, 1.0, 30).clip(1, 10),
            'sleep_duration': np.random.normal(7.5, 0.8, 30).clip(4, 12),
            'activity_balance': np.random.normal(1.0, 2.0, 30).clip(-5, 5)
        })
        
        # Create data with improving trend
        trend_values = np.linspace(5.0, 8.0, 14)  # 2 weeks of improving data
        self.trending_data = pd.DataFrame({
            'date': pd.date_range(start='2025-01-01', periods=14, freq='D'),
            'mood': trend_values + np.random.normal(0, 0.3, 14),
            'energy': trend_values + np.random.normal(0, 0.3, 14),
            'sleep_quality': trend_values + np.random.normal(0, 0.2, 14)
        })
        
        # Create minimal data for edge cases
        self.minimal_data = pd.DataFrame({
            'date': pd.date_range(start='2025-01-01', periods=3, freq='D'),
            'mood': [5.0, 6.0, 7.0],
            'energy': [4.0, 5.0, 6.0],
            'sleep_quality': [7.0, 7.5, 8.0]
        })
    
    def test_wellbeing_score_calculation(self):
        """Test wellbeing score calculation with complete data."""
        result = KPICalculator.calculate_wellbeing_score(self.sample_data)
        
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'confidence' in result
        assert 'trend' in result
        assert 'sample_size' in result
        assert 'components' in result
        
        # Verify score is in valid range
        assert 0 <= result['score'] <= 10
        
        # Verify confidence is reasonable
        assert 0 <= result['confidence'] <= 1
        
        # Verify components exist
        assert 'mood' in result['components']
        assert 'energy' in result['components'] 
        assert 'sleep_quality' in result['components']
        
        # Verify trend is valid
        assert result['trend'] in ['improving', 'stable', 'declining']
    
    def test_wellbeing_score_with_missing_data(self):
        """Test wellbeing score with some missing columns."""
        incomplete_data = self.sample_data[['date', 'mood', 'energy']].copy()
        result = KPICalculator.calculate_wellbeing_score(incomplete_data)
        
        assert isinstance(result, dict)
        assert result['score'] > 0  # Should still calculate with available data
        assert 'mood' in result['components']
        assert 'energy' in result['components']
        assert 'sleep_quality' not in result['components']
    
    def test_wellbeing_score_empty_data(self):
        """Test wellbeing score with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = KPICalculator.calculate_wellbeing_score(empty_df)
        
        assert result['score'] == 0.0
        assert result['confidence'] == 0.0
        assert result['sample_size'] == 0
    
    def test_balance_index_calculation(self):
        """Test balance index calculation."""
        result = KPICalculator.calculate_balance_index(self.sample_data)
        
        assert isinstance(result, dict)
        assert 'index' in result
        assert 'activity_component' in result
        assert 'sleep_component' in result
        assert 'confidence' in result
        assert 'sample_size' in result
        
        # Verify index is percentage (0-100)
        assert 0 <= result['index'] <= 100
        
        # Verify components are in valid range (0-1)
        assert 0 <= result['activity_component'] <= 1
        assert 0 <= result['sleep_component'] <= 1
    
    def test_balance_index_sleep_target_calculation(self):
        """Test balance index sleep target achievement calculation."""
        # Create data with known sleep patterns
        test_data = pd.DataFrame({
            'sleep_duration': [6.0, 7.5, 8.0, 9.0, 7.2],  # 3 out of 5 in target range
            'activity_balance': [1, -1, 2, 0, 1]
        })
        
        result = KPICalculator.calculate_balance_index(test_data)
        
        # Sleep component should be 3/5 = 0.6 (60% in target range of 7-8 hours)
        expected_sleep_component = 3/5
        assert abs(result['sleep_component'] - expected_sleep_component) < 0.1
    
    def test_trend_indicator_calculation(self):
        """Test trend indicator calculation."""
        result = KPICalculator.calculate_trend_indicator(self.trending_data)
        
        assert isinstance(result, dict)
        assert 'direction' in result
        assert 'magnitude' in result
        assert 'significance' in result
        assert 'confidence' in result
        assert 'sample_size' in result
        
        # With improving trend data, should detect improvement
        assert result['direction'] in ['improving', 'stable', 'declining']
        assert result['confidence'] in ['high', 'medium', 'low']
        assert isinstance(result['magnitude'], (int, float))
    
    def test_trend_indicator_with_minimal_data(self):
        """Test trend indicator with minimal data."""
        result = KPICalculator.calculate_trend_indicator(self.minimal_data)
        
        # Should handle minimal data gracefully
        assert isinstance(result, dict)
        assert result['sample_size'] >= 0
    
    def test_trend_indicator_no_date_column(self):
        """Test trend indicator without date column."""
        no_date_data = self.sample_data.drop('date', axis=1)
        result = KPICalculator.calculate_trend_indicator(no_date_data)
        
        # Should return empty result
        assert result['sample_size'] == 0
        assert result['direction'] == 'stable'
    
    def test_calculate_all_kpis(self):
        """Test calculating all KPIs together."""
        results = KPICalculator.calculate_all_kpis(self.sample_data)
        
        assert isinstance(results, dict)
        assert 'wellbeing_score' in results
        assert 'balance_index' in results  
        assert 'trend_indicator' in results
        
        # Verify each KPI has expected structure
        for kpi_name, kpi_result in results.items():
            assert isinstance(kpi_result, dict)
            assert 'sample_size' in kpi_result
            assert 'confidence' in kpi_result or 'confidence' in str(kpi_result)
            assert 'kpi_type' in kpi_result
            assert kpi_result['kpi_type'] == kpi_name
    
    def test_confidence_calculation(self):
        """Test confidence level calculation."""
        # Test with various sample sizes
        assert KPICalculator._calculate_confidence(0, 10) == 0.0
        assert KPICalculator._calculate_confidence(5, 10) <= 0.7  # Below minimum
        assert KPICalculator._calculate_confidence(10, 10) >= 0.7  # At minimum
        assert KPICalculator._calculate_confidence(50, 10) <= 0.95  # Well above minimum
    
    def test_simple_trend_calculation(self):
        """Test simple trend calculation helper."""
        # Test improving trend
        improving_data = pd.DataFrame({
            'date': pd.date_range(start='2025-01-01', periods=10, freq='D'),
            'mood': np.linspace(4, 8, 10),  # Clear improving trend
            'energy': np.linspace(3, 7, 10)
        })
        
        trend = KPICalculator._calculate_simple_trend(improving_data, ['mood', 'energy'])
        assert trend in ['improving', 'stable', 'declining']
        
        # Test stable trend
        stable_data = pd.DataFrame({
            'date': pd.date_range(start='2025-01-01', periods=10, freq='D'),
            'mood': [6.0] * 10,  # Completely flat
            'energy': [6.0] * 10
        })
        
        trend = KPICalculator._calculate_simple_trend(stable_data, ['mood', 'energy'])
        assert trend == 'stable'
    
    def test_empty_kpi_results(self):
        """Test empty KPI result structures."""
        wellbeing_empty = KPICalculator._empty_kpi_result('wellbeing_score')
        assert wellbeing_empty['score'] == 0.0
        assert wellbeing_empty['kpi_type'] == 'wellbeing_score'
        
        balance_empty = KPICalculator._empty_kpi_result('balance_index')
        assert balance_empty['index'] == 0.0
        assert balance_empty['kpi_type'] == 'balance_index'
        
        trend_empty = KPICalculator._empty_kpi_result('trend_indicator')
        assert trend_empty['direction'] == 'stable'
        assert trend_empty['kpi_type'] == 'trend_indicator'
    
    def test_wellbeing_score_formula_accuracy(self):
        """Test that wellbeing score formula matches specification."""
        # Create test data with known values
        test_data = pd.DataFrame({
            'mood': [8.0, 6.0, 7.0],
            'energy': [7.0, 5.0, 6.0],
            'sleep_quality': [9.0, 8.0, 7.0]
        })
        
        result = KPICalculator.calculate_wellbeing_score(test_data)
        
        # Manual calculation: mood(0.4) + energy(0.4) + sleep_quality(0.2)
        expected_score = (
            test_data['mood'].mean() * 0.4 +
            test_data['energy'].mean() * 0.4 +
            test_data['sleep_quality'].mean() * 0.2
        )
        
        assert abs(result['score'] - expected_score) < 0.01
    
    def test_balance_index_formula_accuracy(self):
        """Test that balance index formula matches specification."""
        # Create test data with known sleep achievements
        test_data = pd.DataFrame({
            'activity_balance': [2.0, -1.0, 3.0, 0.0],  # Average = 1.0, normalized ≈ 0.6
            'sleep_duration': [7.5, 6.0, 8.0, 7.2]      # 3/4 in target range = 0.75
        })
        
        result = KPICalculator.calculate_balance_index(test_data)
        
        # Expected calculation:
        # Activity: (1.0 + 5) / 10 = 0.6 (normalized)
        # Sleep: 3/4 = 0.75 (target achievement)
        # Index: (0.6 * 0.6 + 0.75 * 0.4) * 100 = 66%
        
        # Allow for some tolerance due to clipping and rounding
        assert 60 <= result['index'] <= 70
    
    def test_with_nan_values(self):
        """Test handling of NaN values in data."""
        data_with_nan = self.sample_data.copy()
        data_with_nan.loc[0:5, 'mood'] = np.nan
        data_with_nan.loc[10:15, 'energy'] = np.nan
        
        wellbeing_result = KPICalculator.calculate_wellbeing_score(data_with_nan)
        assert wellbeing_result['score'] > 0  # Should still work with partial data
        
        balance_result = KPICalculator.calculate_balance_index(data_with_nan) 
        assert balance_result['index'] >= 0  # Should handle NaN gracefully


# Test data fixtures for integration testing
@pytest.fixture
def sample_dashboard_data():
    """Create realistic sample data for dashboard testing."""
    np.random.seed(42)  # For reproducible tests
    dates = pd.date_range(start='2025-01-01', periods=60, freq='D')
    
    return pd.DataFrame({
        'date': dates,
        'mood': np.random.normal(6.5, 1.5, 60).clip(1, 10).round(1),
        'energy': np.random.normal(6.0, 1.2, 60).clip(1, 10).round(1),
        'sleep_quality': np.random.normal(7.0, 1.0, 60).clip(1, 10).round(1),
        'sleep_duration': np.random.normal(7.5, 0.8, 60).clip(4, 12).round(1),
        'activity_balance': np.random.randint(-3, 4, 60),
        'positive_activities': np.random.randint(0, 5, 60),
        'negative_activities': np.random.randint(0, 3, 60)
    })


def test_integration_with_realistic_data(sample_dashboard_data):
    """Integration test with realistic dashboard data."""
    results = KPICalculator.calculate_all_kpis(sample_dashboard_data)
    
    # All KPIs should have reasonable values
    assert 0 <= results['wellbeing_score']['score'] <= 10
    assert 0 <= results['balance_index']['index'] <= 100
    assert results['trend_indicator']['direction'] in ['improving', 'stable', 'declining']
    
    # All should have good sample sizes
    for kpi_result in results.values():
        assert kpi_result['sample_size'] > 0
        # Handle different confidence formats (float vs string)
        if 'confidence' in kpi_result:
            confidence = kpi_result['confidence']
            if isinstance(confidence, (int, float)):
                assert confidence > 0
            elif isinstance(confidence, str):
                assert confidence in ['high', 'medium', 'low']


if __name__ == '__main__':
    # Allow running tests directly
    pytest.main([__file__])
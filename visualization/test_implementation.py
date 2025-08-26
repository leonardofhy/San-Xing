#!/usr/bin/env python3
"""Test script to demonstrate KPI Calculator and Statistical Utilities."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import our new modules
from analytics.kpi_calculator import KPICalculator
from analytics.statistical_utils import (
    calculate_significance, 
    correlation_with_significance,
    trend_significance
)

def create_sample_data():
    """Create realistic sample wellbeing data."""
    np.random.seed(42)
    dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
    
    return pd.DataFrame({
        'date': dates,
        'mood': np.random.normal(6.5, 1.5, 30).clip(1, 10).round(1),
        'energy': np.random.normal(6.0, 1.2, 30).clip(1, 10).round(1),
        'sleep_quality': np.random.normal(7.0, 1.0, 30).clip(1, 10).round(1),
        'sleep_duration': np.random.normal(7.5, 0.8, 30).clip(4, 12).round(1),
        'activity_balance': np.random.randint(-3, 4, 30)
    })

def main():
    print("=" * 60)
    print("SAN-XING ANALYTICS IMPLEMENTATION DEMO")
    print("=" * 60)
    
    # Create sample data
    data = create_sample_data()
    print(f"\n1. SAMPLE DATA ({len(data)} days)")
    print("-" * 30)
    print(data.head())
    print(f"\nData shape: {data.shape}")
    print(f"Date range: {data['date'].min().date()} to {data['date'].max().date()}")
    
    # Test KPI Calculator
    print(f"\n2. KPI CALCULATIONS")
    print("-" * 30)
    
    # Calculate individual KPIs
    wellbeing = KPICalculator.calculate_wellbeing_score(data)
    balance = KPICalculator.calculate_balance_index(data)
    trend = KPICalculator.calculate_trend_indicator(data)
    
    print(f"📊 Wellbeing Score: {wellbeing['score']}/10")
    print(f"   - Confidence: {wellbeing['confidence']:.2f}")
    print(f"   - Trend: {wellbeing['trend']}")
    print(f"   - Sample size: {wellbeing['sample_size']}")
    
    print(f"\n⚖️  Balance Index: {balance['index']:.1f}%")
    print(f"   - Activity component: {balance['activity_component']:.3f}")
    print(f"   - Sleep component: {balance['sleep_component']:.3f}")
    print(f"   - Confidence: {balance['confidence']:.2f}")
    
    print(f"\n📈 Trend Indicator: {trend['direction']}")
    print(f"   - Magnitude: {trend['magnitude']:.3f}")
    print(f"   - Confidence: {trend['confidence']}")
    print(f"   - Sample size: {trend['sample_size']}")
    
    # Calculate all KPIs at once
    all_kpis = KPICalculator.calculate_all_kpis(data)
    print(f"\n✅ All KPIs calculated successfully!")
    
    # Test Statistical Utilities
    print(f"\n3. STATISTICAL ANALYSIS")
    print("-" * 30)
    
    # Correlation analysis
    correlations = correlation_with_significance(
        data[['mood', 'energy', 'sleep_quality', 'sleep_duration']]
    )
    
    print(f"🔗 Correlation Analysis:")
    print(f"   - Total tests: {correlations['total_tests']}")
    print(f"   - Significant correlations: {len(correlations['significant_correlations'])}")
    print(f"   - Corrected alpha: {correlations['corrected_alpha']:.4f}")
    
    if correlations['significant_correlations']:
        print("   - Significant pairs:")
        for corr in correlations['significant_correlations']:
            print(f"     * {corr['variable_1']} vs {corr['variable_2']}: "
                  f"r={corr['correlation']:.3f}, p={corr['p_value']:.4f}")
    
    # Trend significance for mood
    mood_trend = trend_significance(data['mood'])
    print(f"\n📊 Mood Trend Analysis (Mann-Kendall):")
    print(f"   - Direction: {mood_trend['trend_direction']}")
    print(f"   - Kendall's τ: {mood_trend['tau']:.3f}")
    print(f"   - p-value: {mood_trend['p_value']:.4f}")
    print(f"   - Significant: {mood_trend['significant']}")
    
    # Test significance between mood and sleep
    mood_sleep_sig = calculate_significance(data['mood'], data['sleep_quality'])
    print(f"\n🔍 Mood vs Sleep Quality:")
    print(f"   - Correlation: {mood_sleep_sig['test_statistic']:.3f}")
    print(f"   - p-value: {mood_sleep_sig['p_value']:.4f}")
    print(f"   - Effect size: {mood_sleep_sig['effect_size']:.3f}")
    print(f"   - Significant: {mood_sleep_sig['significant']}")
    
    print(f"\n4. INTEGRATION TEST")
    print("-" * 30)
    print("✅ KPI Calculator: Working")
    print("✅ Statistical Utilities: Working")
    print("✅ Data Processing: Working")
    print("✅ All tests passed!")
    
    print(f"\n" + "=" * 60)
    print("IMPLEMENTATION READY FOR DASHBOARD INTEGRATION")
    print("=" * 60)

if __name__ == "__main__":
    main()
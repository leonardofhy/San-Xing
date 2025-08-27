"""KPI Calculator for San-Xing Dashboard.

This module implements the composite scoring algorithms for the three primary KPIs:
1. Wellbeing Score: Composite of mood, energy, and sleep quality
2. Balance Index: Activity balance and sleep goal achievement
3. Trend Indicator: Statistical trend analysis with significance testing

All calculations include confidence levels based on sample sizes and statistical rigor.
"""

from typing import Dict, Any
from datetime import timedelta

import pandas as pd
import numpy as np

from .sleep_quality_calculator import SleepQualityCalculator


class KPICalculator:
    """Calculator for dashboard Key Performance Indicators."""
    # Configuration constants
    WELLBEING_WEIGHTS = {
        'mood': 0.4,
        'energy': 0.4, 
        'sleep_quality': 0.2
    }

    BALANCE_WEIGHTS = {
        'activity': 0.6,
        'sleep': 0.4
    }

    # Sleep targets (hours)
    SLEEP_TARGET_MIN = 7.0
    SLEEP_TARGET_MAX = 8.0

    # Minimum sample sizes for confidence
    MIN_SAMPLE_WELLBEING = 7   # 1 week minimum
    MIN_SAMPLE_BALANCE = 10    # 10 days minimum
    MIN_SAMPLE_TREND = 14      # 2 weeks minimum

    @classmethod
    def calculate_wellbeing_score(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate composite wellbeing score.
        
        Formula: mood(0.4) + energy(0.4) + sleep_quality(0.2)
        
        Args:
            df: DataFrame with mood, energy, sleep_quality columns
            
        Returns:
            dict: {
                'score': float (0-10 scale),
                'confidence': float (0-1 scale),
                'trend': str ('improving'|'stable'|'declining'),
                'sample_size': int,
                'components': dict with individual component scores
            }
        """
        if df.empty:
            return cls._empty_kpi_result('wellbeing_score')

        # Get required columns
        required_cols = ['mood', 'energy', 'sleep_quality']
        available_cols = [col for col in required_cols if col in df.columns]

        if not available_cols:
            return cls._empty_kpi_result('wellbeing_score')

        # Calculate component scores
        components = {}

        for col in available_cols:
            component_data = df[col].dropna()
            if len(component_data) > 0:
                components[col] = {
                    'mean': float(component_data.mean()),
                    'count': len(component_data)
                }

        if not components:
            return cls._empty_kpi_result('wellbeing_score')

        # Calculate weighted composite score
        total_weight = 0
        weighted_sum = 0

        for col, weight in cls.WELLBEING_WEIGHTS.items():
            if col in components:
                weighted_sum += components[col]['mean'] * weight
                total_weight += weight

        if total_weight == 0:
            return cls._empty_kpi_result('wellbeing_score')

        # Normalize by actual available weights
        composite_score = weighted_sum / total_weight

        # Calculate sample size (minimum across components)
        sample_size = min(comp['count'] for comp in components.values())

        # Calculate confidence based on sample size
        confidence = cls._calculate_confidence(sample_size, cls.MIN_SAMPLE_WELLBEING)

        # Calculate trend (7-day trend analysis)
        trend = cls._calculate_simple_trend(df, available_cols, days=7)

        return {
            'score': round(float(composite_score), 2),
            'confidence': confidence,
            'trend': trend,
            'sample_size': sample_size,
            'components': components,
            'kpi_type': 'wellbeing_score'
        }

    @classmethod
    def calculate_balance_index(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate balance index from activity and sleep metrics.
        
        Formula: (activity_balance * 0.6 + sleep_goal_achievement * 0.4) * 100
        
        Args:
            df: DataFrame with activity_balance, sleep_duration columns
            
        Returns:
            dict: {
                'index': float (0-100 percentage),
                'activity_component': float,
                'sleep_component': float,
                'confidence': float,
                'sample_size': int
            }
        """
        if df.empty:
            return cls._empty_kpi_result('balance_index')

        # Activity balance component
        activity_component = 0.0
        activity_sample_size = 0

        if 'activity_balance' in df.columns:
            activity_data = df['activity_balance'].dropna()
            if len(activity_data) > 0:
                # Normalize activity balance to 0-1 scale
                # Assuming activity_balance ranges from -5 to +5 (rough estimate)
                activity_normalized = (activity_data + 5) / 10
                activity_normalized = activity_normalized.clip(0, 1)
                activity_component = float(activity_normalized.mean())
                activity_sample_size = len(activity_data)

        # Sleep goal achievement component
        sleep_component = 0.0
        sleep_sample_size = 0

        if 'sleep_duration' in df.columns:
            sleep_data = df['sleep_duration'].dropna()
            if len(sleep_data) > 0:
                # Calculate percentage of days meeting 7-8 hour target
                in_target_range = (
                    (sleep_data >= cls.SLEEP_TARGET_MIN) &
                    (sleep_data <= cls.SLEEP_TARGET_MAX)
                )
                sleep_component = float(in_target_range.mean())
                sleep_sample_size = len(sleep_data)

        # Check if we have any components
        if activity_sample_size == 0 and sleep_sample_size == 0:
            return cls._empty_kpi_result('balance_index')

        # Calculate weighted balance index
        total_weight = 0
        weighted_sum = 0

        if activity_sample_size > 0:
            weighted_sum += activity_component * cls.BALANCE_WEIGHTS['activity']
            total_weight += cls.BALANCE_WEIGHTS['activity']

        if sleep_sample_size > 0:
            weighted_sum += sleep_component * cls.BALANCE_WEIGHTS['sleep']
            total_weight += cls.BALANCE_WEIGHTS['sleep']

        if total_weight == 0:
            return cls._empty_kpi_result('balance_index')

        # Normalize and convert to percentage
        balance_index = (weighted_sum / total_weight) * 100

        # Sample size is minimum of available components
        sample_size = min(
            size for size in [activity_sample_size, sleep_sample_size]
            if size > 0
        )

        # Calculate confidence
        confidence = cls._calculate_confidence(sample_size, cls.MIN_SAMPLE_BALANCE)

        return {
            'index': round(float(balance_index), 1),
            'activity_component': round(activity_component, 3),
            'sleep_component': round(sleep_component, 3),
            'confidence': confidence,
            'sample_size': sample_size,
            'kpi_type': 'balance_index'
        }

    @classmethod
    def calculate_trend_indicator(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate 7-day trend direction with statistical significance.
        
        Args:
            df: DataFrame with date column and wellbeing metrics
            
        Returns:
            dict: {
                'direction': str ('improving'|'stable'|'declining'),
                'magnitude': float (change per day),
                'significance': float (p-value),
                'confidence': str ('high'|'medium'|'low'),
                'sample_size': int
            }
        """
        if df.empty or 'date' not in df.columns:
            return cls._empty_kpi_result('trend_indicator')

        # Ensure date is datetime
        df_sorted = df.copy()
        df_sorted['date'] = pd.to_datetime(df_sorted['date'])
        df_sorted = df_sorted.sort_values('date')

        # Get last 7 days of data
        latest_date = df_sorted['date'].max()
        cutoff_date = latest_date - timedelta(days=7)
        recent_data = df_sorted[df_sorted['date'] >= cutoff_date].copy()

        if len(recent_data) < 3:  # Need at least 3 points for trend
            return cls._empty_kpi_result('trend_indicator')

        # Calculate composite wellbeing for trend analysis
        wellbeing_cols = ['mood', 'energy', 'sleep_quality']
        available_cols = [col for col in wellbeing_cols if col in recent_data.columns]

        if not available_cols:
            return cls._empty_kpi_result('trend_indicator')

        # Calculate daily wellbeing scores
        daily_scores = []
        for _, row in recent_data.iterrows():
            total_weight = 0
            weighted_sum = 0

            for col in available_cols:
                if pd.notna(row[col]):
                    weight = cls.WELLBEING_WEIGHTS.get(col, 0)
                    weighted_sum += row[col] * weight
                    total_weight += weight

            if total_weight > 0:
                daily_scores.append(weighted_sum / total_weight)

        if len(daily_scores) < 3:
            return cls._empty_kpi_result('trend_indicator')

        # Simple linear trend analysis
        x = np.arange(len(daily_scores))
        y = np.array(daily_scores)

        # Calculate linear regression slope
        if len(x) > 1 and np.var(x) > 0:
            slope = np.corrcoef(x, y)[0, 1] * (np.std(y) / np.std(x))
        else:
            slope = 0.0

        # Determine direction
        if abs(slope) < 0.1:  # Threshold for "stable"
            direction = 'stable'
        elif slope > 0:
            direction = 'improving'
        else:
            direction = 'declining'

        # Simple significance estimate (proper statistical test would be better)
        # This is a placeholder - we'll improve this in statistical_utils.py
        significance = 0.5  # Placeholder

        # Confidence based on sample size and trend strength
        sample_size = len(daily_scores)
        base_confidence = cls._calculate_confidence(sample_size, cls.MIN_SAMPLE_TREND)

        # Adjust confidence based on trend strength
        trend_strength = min(abs(slope), 1.0)
        adjusted_confidence = base_confidence * (0.5 + 0.5 * trend_strength)

        if adjusted_confidence > 0.8:
            confidence_level = 'high'
        elif adjusted_confidence > 0.5:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'

        return {
            'direction': direction,
            'magnitude': round(float(slope), 3),
            'significance': significance,
            'confidence': confidence_level,
            'sample_size': sample_size,
            'kpi_type': 'trend_indicator'
        }

    @classmethod
    def calculate_all_kpis(cls, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Calculate all KPIs in one call.
        
        Args:
            df: DataFrame with all required columns
            
        Returns:
            dict: {
                'wellbeing_score': {...},
                'balance_index': {...},
                'trend_indicator': {...},
                'sleep_quality_analysis': {...}
            }
        """
        results = {}

        try:
            results['wellbeing_score'] = cls.calculate_wellbeing_score(df)
        except Exception as e:
            results['wellbeing_score'] = cls._empty_kpi_result('wellbeing_score', str(e))

        try:
            results['balance_index'] = cls.calculate_balance_index(df)
        except Exception as e:
            results['balance_index'] = cls._empty_kpi_result('balance_index', str(e))

        try:
            results['trend_indicator'] = cls.calculate_trend_indicator(df)
        except Exception as e:
            results['trend_indicator'] = cls._empty_kpi_result('trend_indicator', str(e))

        try:
            results['sleep_quality_analysis'] = cls.calculate_sleep_quality_analysis(df)
        except Exception as e:
            results['sleep_quality_analysis'] = cls._empty_kpi_result('sleep_quality_analysis', str(e))

        return results

    @classmethod
    def calculate_sleep_quality_analysis(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive sleep quality analysis (both subjective and objective)
        
        Args:
            df: DataFrame with sleep timing and rating data
            
        Returns:
            dict: Sleep quality analysis with both subjective and objective metrics
        """
        if df.empty:
            return cls._empty_kpi_result('sleep_quality_analysis')

        # Calculate objective sleep quality
        objective_result = SleepQualityCalculator.calculate_objective_sleep_quality(df)
        
        # Get subjective sleep quality stats if available
        subjective_stats = {}
        if 'sleep_quality' in df.columns:
            subj_data = df['sleep_quality'].dropna()
            if len(subj_data) > 0:
                subjective_stats = {
                    'avg_rating': float(subj_data.mean()),
                    'rating_std': float(subj_data.std()) if len(subj_data) > 1 else 0.0,
                    'sample_size': len(subj_data),
                    'rating_range': [float(subj_data.min()), float(subj_data.max())]
                }
        
        # Compare subjective vs objective if both available
        comparison_result = {}
        if subjective_stats and 'objective_sleep_quality' in objective_result and objective_result['objective_sleep_quality'] is not None:
            comparison_result = SleepQualityCalculator.compare_subjective_vs_objective(df)
        
        # Calculate confidence based on data availability
        sample_size = objective_result.get('metrics', {}).get('sample_size', 0)
        confidence = cls._calculate_confidence(sample_size, 7)  # 7 days minimum for sleep analysis
        
        return {
            'objective_quality': objective_result,  # Return full objective result
            'subjective_avg': subjective_stats.get('avg_rating'),  # Add subjective average
            'subjective_stats': subjective_stats,
            'comparison': comparison_result,
            'confidence': confidence,
            'sample_size': sample_size,
            'kpi_type': 'sleep_quality_analysis'
        }
    
    @staticmethod
    def _calculate_confidence(sample_size: int, min_sample: int) -> float:
        """Calculate confidence level based on sample size.
        
        Args:
            sample_size: Actual sample size
            min_sample: Minimum required sample size
            
        Returns:
            float: Confidence level (0.0 to 1.0)
        """
        if sample_size <= 0:
            return 0.0
        elif sample_size < min_sample:
            return sample_size / min_sample * 0.7  # Max 70% confidence below minimum
        else:
            # Logarithmic confidence curve above minimum
            excess_ratio = (sample_size - min_sample) / min_sample
            confidence = 0.7 + 0.25 * (1 - np.exp(-excess_ratio))
            return min(confidence, 0.95)  # Cap at 95% confidence
    
    @staticmethod
    def _calculate_simple_trend(df: pd.DataFrame, columns: list, days: int = 7) -> str:
        """Calculate simple trend direction over specified days.
        
        Args:
            df: DataFrame with date column
            columns: List of columns to analyze
            days: Number of days to look back
            
        Returns:
            str: 'improving', 'stable', or 'declining'
        """
        if 'date' not in df.columns or len(df) < 3:
            return 'stable'
        
        try:
            df_sorted = df.copy()
            df_sorted['date'] = pd.to_datetime(df_sorted['date'])
            df_sorted = df_sorted.sort_values('date')
            
            # Get recent data
            latest_date = df_sorted['date'].max()
            cutoff_date = latest_date - timedelta(days=days)
            recent_data = df_sorted[df_sorted['date'] >= cutoff_date]
            
            if len(recent_data) < 3:
                return 'stable'
            
            # Calculate average values for first half vs second half
            mid_point = len(recent_data) // 2
            first_half = recent_data.iloc[:mid_point]
            second_half = recent_data.iloc[mid_point:]
            
            first_avg = first_half[columns].mean().mean()
            second_avg = second_half[columns].mean().mean()
            
            if pd.isna(first_avg) or pd.isna(second_avg):
                return 'stable'
            
            change = second_avg - first_avg
            
            if abs(change) < 0.2:  # Threshold for stable
                return 'stable'
            elif change > 0:
                return 'improving'
            else:
                return 'declining'
                
        except Exception:
            return 'stable'
    
    @staticmethod
    def _empty_kpi_result(kpi_type: str, error_msg: str = None) -> Dict[str, Any]:
        """Return empty/default KPI result structure.
        
        Args:
            kpi_type: Type of KPI ('wellbeing_score', 'balance_index', 'trend_indicator')
            
        Returns:
            dict: Default empty result structure
        """
        base_result = {
            'sample_size': 0,
            'confidence': 0.0,
            'kpi_type': kpi_type
        }
        
        if error_msg:
            base_result['error'] = error_msg
        
        if kpi_type == 'wellbeing_score':
            return {
                **base_result,
                'score': 0.0,
                'trend': 'stable',
                'components': {}
            }
        elif kpi_type == 'balance_index':
            return {
                **base_result,
                'index': 0.0,
                'activity_component': 0.0,
                'sleep_component': 0.0
            }
        elif kpi_type == 'trend_indicator':
            return {
                **base_result,
                'direction': 'stable',
                'magnitude': 0.0,
                'significance': 1.0,
                'confidence': 'low'
            }
        elif kpi_type == 'sleep_quality_analysis':
            return {
                **base_result,
                'subjective_avg': None,
                'objective_quality': {},
                'comparison': {}
            }
        else:
            return base_result

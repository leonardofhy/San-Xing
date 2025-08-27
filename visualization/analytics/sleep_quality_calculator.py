"""
Objective Sleep Quality Calculator for San-Xing Dashboard
Calculates sleep quality based on sleep timing patterns and duration
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class SleepQualityCalculator:
    """Calculate objective sleep quality metrics from sleep timing data"""
    
    # Sleep quality thresholds and parameters
    OPTIMAL_SLEEP_DURATION = (7.0, 9.0)  # Hours
    OPTIMAL_BEDTIME = (22, 24)  # 10 PM to midnight (24-hour format)
    OPTIMAL_WAKE_TIME = (6, 8)  # 6 AM to 8 AM
    
    # Circadian rhythm preferences
    IDEAL_SLEEP_MIDPOINT = 2.5  # 2:30 AM (optimal sleep midpoint)
    REGULARITY_THRESHOLD = 1.0  # Hours of variation considered "regular"
    
    # Scoring weights
    DURATION_WEIGHT = 0.4
    TIMING_WEIGHT = 0.3
    REGULARITY_WEIGHT = 0.2
    EFFICIENCY_WEIGHT = 0.1
    
    @classmethod
    def calculate_objective_sleep_quality(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate objective sleep quality score (1-5 scale) from sleep timing data
        
        Args:
            df: DataFrame with columns: sleep_bedtime, wake_time, sleep_duration_hours, logical_date
            
        Returns:
            Dict with objective sleep quality metrics
        """
        if df.empty:
            return cls._empty_result()
        
        # Filter valid sleep data
        sleep_data = cls._prepare_sleep_data(df)
        
        if sleep_data.empty:
            # Check if columns exist at all
            missing_cols = [col for col in ['sleep_bedtime', 'wake_time'] if col not in df.columns]
            if missing_cols:
                return {
                    'error': f'Missing required columns: {missing_cols}',
                    'objective_sleep_quality': None,
                    'components': {},
                    'metrics': {},
                    'analysis': 'Required sleep timing columns not found in data'
                }
            else:
                # Columns exist but no valid data after filtering
                return {
                    'error': 'Insufficient valid sleep timing data for objective analysis',
                    'objective_sleep_quality': None,
                    'components': {},
                    'metrics': {},
                    'analysis': 'Sleep timing columns found but contain insufficient valid data'
                }
        
        # Calculate individual components
        duration_score = cls._calculate_duration_score(sleep_data)
        timing_score = cls._calculate_timing_score(sleep_data)
        regularity_score = cls._calculate_regularity_score(sleep_data)
        efficiency_score = cls._calculate_efficiency_score(sleep_data)
        
        # Calculate weighted overall score
        overall_score = (
            duration_score * cls.DURATION_WEIGHT +
            timing_score * cls.TIMING_WEIGHT +
            regularity_score * cls.REGULARITY_WEIGHT +
            efficiency_score * cls.EFFICIENCY_WEIGHT
        )
        
        # Convert to 1-5 scale (matching subjective ratings)
        objective_quality = cls._normalize_to_1_5_scale(overall_score)
        
        return {
            'objective_sleep_quality': round(objective_quality, 2),
            'components': {
                'duration_score': round(duration_score, 2),
                'timing_score': round(timing_score, 2),
                'regularity_score': round(regularity_score, 2),
                'efficiency_score': round(efficiency_score, 2)
            },
            'metrics': {
                'avg_duration': round(sleep_data['duration_hours'].mean(), 2),
                'avg_bedtime': cls._format_average_time(sleep_data, 'bedtime_minutes'),
                'avg_wake_time': cls._format_average_time(sleep_data, 'wake_minutes'),
                'sleep_regularity': round(regularity_score, 2),
                'sample_size': len(sleep_data)
            },
            'analysis': cls._generate_sleep_analysis(sleep_data, objective_quality)
        }
    
    @classmethod
    def compare_subjective_vs_objective(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compare subjective sleep quality ratings with objective calculations
        
        Args:
            df: DataFrame with sleep_quality (subjective) and timing data
            
        Returns:
            Dict with comparison metrics and insights
        """
        if 'sleep_quality' not in df.columns:
            return {'error': 'No subjective sleep quality data available'}
        
        # Get objective quality
        obj_result = cls.calculate_objective_sleep_quality(df)
        if 'error' in obj_result:
            return obj_result
        
        # Filter data with both subjective and objective measures
        valid_data = df.dropna(subset=['sleep_quality'])
        
        if valid_data.empty:
            return {'error': 'No valid subjective ratings to compare'}
        
        # Calculate correlation if we have enough data
        correlation = None
        if len(valid_data) > 2:
            try:
                # Calculate objective quality for each day
                daily_objective = []
                for _, row in valid_data.iterrows():
                    day_data = pd.DataFrame([row])
                    day_obj = cls.calculate_objective_sleep_quality(day_data)
                    if 'error' not in day_obj:
                        daily_objective.append(day_obj['objective_sleep_quality'])
                    else:
                        daily_objective.append(None)
                
                # Filter out None values
                valid_pairs = [(subj, obj) for subj, obj in zip(valid_data['sleep_quality'], daily_objective) if obj is not None]
                
                if len(valid_pairs) > 2:
                    subjective_vals = [pair[0] for pair in valid_pairs]
                    objective_vals = [pair[1] for pair in valid_pairs]
                    correlation = np.corrcoef(subjective_vals, objective_vals)[0, 1]
            
            except Exception:
                correlation = None
        
        return {
            'subjective_avg': round(valid_data['sleep_quality'].mean(), 2),
            'objective_avg': obj_result['objective_sleep_quality'],
            'correlation': round(correlation, 3) if correlation is not None else None,
            'sample_size': len(valid_data),
            'agreement_analysis': cls._analyze_agreement(valid_data, obj_result),
            'recommendations': cls._generate_comparison_insights(valid_data, obj_result, correlation)
        }
    
    @classmethod
    def _prepare_sleep_data(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate sleep timing data"""
        # Required columns
        required_cols = ['sleep_bedtime', 'wake_time']
        
        # Check if required columns exist
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return pd.DataFrame()
        
        # Filter rows with timing data
        sleep_df = df.dropna(subset=required_cols).copy()
        
        if sleep_df.empty:
            return pd.DataFrame()
        
        # Convert time strings to minutes since midnight
        sleep_df['bedtime_minutes'] = sleep_df['sleep_bedtime'].apply(cls._time_to_minutes)
        sleep_df['wake_minutes'] = sleep_df['wake_time'].apply(cls._time_to_minutes)
        
        # Calculate duration if not provided
        if 'sleep_duration_hours' in sleep_df.columns:
            sleep_df['duration_hours'] = sleep_df['sleep_duration_hours']
        else:
            sleep_df['duration_hours'] = sleep_df.apply(cls._calculate_sleep_duration, axis=1)
        
        # Filter realistic durations (2-16 hours)
        sleep_df = sleep_df[(sleep_df['duration_hours'] >= 2) & (sleep_df['duration_hours'] <= 16)]
        
        return sleep_df
    
    @classmethod
    def _time_to_minutes(cls, time_str: str) -> Optional[int]:
        """Convert time string (HH:MM) to minutes since midnight"""
        if pd.isna(time_str) or not time_str:
            return None
        
        try:
            # Handle different time formats
            time_str = str(time_str).strip()
            
            if ':' in time_str:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
            elif len(time_str) == 4:  # HHMM format
                hours = int(time_str[:2])
                minutes = int(time_str[2:])
            else:
                return None
            
            return hours * 60 + minutes
        
        except (ValueError, IndexError):
            return None
    
    @classmethod
    def _calculate_sleep_duration(cls, row) -> float:
        """Calculate sleep duration from bedtime and wake time"""
        bedtime_min = row['bedtime_minutes']
        wake_min = row['wake_minutes']
        
        if pd.isna(bedtime_min) or pd.isna(wake_min):
            return np.nan
        
        # Handle cross-midnight sleep
        if wake_min < bedtime_min:  # Slept past midnight
            duration_min = (24 * 60 - bedtime_min) + wake_min
        else:
            duration_min = wake_min - bedtime_min
        
        return duration_min / 60.0
    
    @classmethod
    def _calculate_duration_score(cls, sleep_data: pd.DataFrame) -> float:
        """Score sleep duration (0-1 scale)"""
        durations = sleep_data['duration_hours'].dropna()
        
        if durations.empty:
            return 0.5
        
        avg_duration = durations.mean()
        
        # Optimal range gets score of 1.0
        if cls.OPTIMAL_SLEEP_DURATION[0] <= avg_duration <= cls.OPTIMAL_SLEEP_DURATION[1]:
            return 1.0
        
        # Score decreases with distance from optimal range
        if avg_duration < cls.OPTIMAL_SLEEP_DURATION[0]:
            # Too little sleep
            deficit = cls.OPTIMAL_SLEEP_DURATION[0] - avg_duration
            return max(0.0, 1.0 - deficit / 3.0)  # Drops to 0 at 4 hours deficit
        
        else:
            # Too much sleep
            excess = avg_duration - cls.OPTIMAL_SLEEP_DURATION[1]
            return max(0.0, 1.0 - excess / 4.0)  # Drops to 0 at 4 hours excess
    
    @classmethod
    def _calculate_timing_score(cls, sleep_data: pd.DataFrame) -> float:
        """Score sleep timing based on circadian rhythms (0-1 scale)"""
        if 'bedtime_minutes' not in sleep_data.columns or 'wake_minutes' not in sleep_data.columns:
            return 0.5
        
        bedtimes = sleep_data['bedtime_minutes'].dropna()
        wake_times = sleep_data['wake_minutes'].dropna()
        
        if bedtimes.empty or wake_times.empty:
            return 0.5
        
        # Calculate average bedtime and wake time
        avg_bedtime = bedtimes.mean()
        avg_wake = wake_times.mean()
        
        # Score bedtime (10 PM - 12 AM is optimal)
        bedtime_hours = avg_bedtime / 60.0
        if bedtime_hours >= 24:
            bedtime_hours -= 24
        
        bedtime_score = cls._score_time_in_range(bedtime_hours, cls.OPTIMAL_BEDTIME[0], cls.OPTIMAL_BEDTIME[1])
        
        # Score wake time (6 AM - 8 AM is optimal)  
        wake_hours = avg_wake / 60.0
        wake_score = cls._score_time_in_range(wake_hours, cls.OPTIMAL_WAKE_TIME[0], cls.OPTIMAL_WAKE_TIME[1])
        
        # Combined timing score
        return (bedtime_score + wake_score) / 2.0
    
    @classmethod
    def _score_time_in_range(cls, time_hours: float, opt_start: int, opt_end: int) -> float:
        """Score how well a time falls within optimal range"""
        if opt_start <= time_hours <= opt_end:
            return 1.0
        
        # Calculate distance from optimal range
        if time_hours < opt_start:
            distance = opt_start - time_hours
        elif time_hours > opt_end:
            distance = time_hours - opt_end
        else:
            distance = 0
        
        # Score decreases with distance (max penalty of 4 hours)
        return max(0.0, 1.0 - distance / 4.0)
    
    @classmethod
    def _calculate_regularity_score(cls, sleep_data: pd.DataFrame) -> float:
        """Score sleep regularity/consistency (0-1 scale)"""
        if len(sleep_data) < 3:
            return 0.5  # Can't assess regularity with too few data points
        
        bedtimes = sleep_data['bedtime_minutes'].dropna()
        wake_times = sleep_data['wake_minutes'].dropna()
        
        if len(bedtimes) < 3 or len(wake_times) < 3:
            return 0.5
        
        # Calculate standard deviation in hours
        bedtime_std = bedtimes.std() / 60.0
        wake_std = wake_times.std() / 60.0
        
        # Score regularity (lower std = higher score)
        bedtime_reg = max(0.0, 1.0 - bedtime_std / 3.0)  # Perfect score if std < 1 hour
        wake_reg = max(0.0, 1.0 - wake_std / 3.0)
        
        return (bedtime_reg + wake_reg) / 2.0
    
    @classmethod
    def _calculate_efficiency_score(cls, sleep_data: pd.DataFrame) -> float:
        """Score sleep efficiency based on consistency and patterns"""
        if len(sleep_data) < 2:
            return 0.5
        
        # Check for weekend vs weekday patterns
        if 'logical_date' in sleep_data.columns:
            sleep_data_copy = sleep_data.copy()
            sleep_data_copy['weekday'] = pd.to_datetime(sleep_data_copy['logical_date']).dt.weekday
            
            weekday_data = sleep_data_copy[sleep_data_copy['weekday'] < 5]  # Mon-Fri
            weekend_data = sleep_data_copy[sleep_data_copy['weekday'] >= 5]  # Sat-Sun
            
            if len(weekday_data) > 0 and len(weekend_data) > 0:
                # Penalize large weekend shifts
                weekday_bedtime = weekday_data['bedtime_minutes'].mean()
                weekend_bedtime = weekend_data['bedtime_minutes'].mean()
                
                bedtime_shift = abs(weekend_bedtime - weekday_bedtime) / 60.0
                shift_penalty = min(1.0, bedtime_shift / 2.0)  # Max penalty for 2+ hour shift
                
                return max(0.0, 1.0 - shift_penalty)
        
        # Default efficiency based on duration consistency
        duration_std = sleep_data['duration_hours'].std()
        return max(0.0, 1.0 - duration_std / 2.0)
    
    @classmethod
    def _normalize_to_1_5_scale(cls, score_0_1: float) -> float:
        """Convert 0-1 score to 1-5 scale to match subjective ratings"""
        # 0.0-1.0 -> 1.0-5.0
        return 1.0 + (score_0_1 * 4.0)
    
    @classmethod
    def _format_average_time(cls, sleep_data: pd.DataFrame, column: str) -> str:
        """Format average time in HH:MM format"""
        if column not in sleep_data.columns:
            return "N/A"
        
        avg_minutes = sleep_data[column].mean()
        if pd.isna(avg_minutes):
            return "N/A"
        
        hours = int(avg_minutes // 60) % 24
        minutes = int(avg_minutes % 60)
        
        return f"{hours:02d}:{minutes:02d}"
    
    @classmethod
    def _generate_sleep_analysis(cls, sleep_data: pd.DataFrame, objective_quality: float) -> str:
        """Generate human-readable sleep pattern analysis"""
        avg_duration = sleep_data['duration_hours'].mean()
        
        if objective_quality >= 4.0:
            quality_desc = "excellent"
        elif objective_quality >= 3.0:
            quality_desc = "good"
        elif objective_quality >= 2.0:
            quality_desc = "fair"
        else:
            quality_desc = "poor"
        
        duration_desc = "optimal" if 7.0 <= avg_duration <= 9.0 else ("short" if avg_duration < 7.0 else "long")
        
        return f"Your sleep patterns show {quality_desc} objective quality with {duration_desc} average duration ({avg_duration:.1f}h)."
    
    @classmethod
    def _analyze_agreement(cls, valid_data: pd.DataFrame, obj_result: Dict) -> str:
        """Analyze agreement between subjective and objective measures"""
        subj_avg = valid_data['sleep_quality'].mean()
        obj_avg = obj_result['objective_sleep_quality']
        
        diff = abs(subj_avg - obj_avg)
        
        if diff < 0.5:
            return "Strong agreement between subjective feelings and objective metrics"
        elif diff < 1.0:
            return "Moderate agreement between subjective and objective measures"
        else:
            return "Notable difference between how you feel vs. objective sleep metrics"
    
    @classmethod
    def _generate_comparison_insights(cls, valid_data: pd.DataFrame, obj_result: Dict, correlation: Optional[float]) -> str:
        """Generate insights from subjective vs objective comparison"""
        subj_avg = valid_data['sleep_quality'].mean()
        obj_avg = obj_result['objective_sleep_quality']
        
        if obj_avg > subj_avg + 0.5:
            return "Your sleep timing patterns are better than you feel - consider factors affecting sleep perception"
        elif subj_avg > obj_avg + 0.5:
            return "You feel better about your sleep than timing suggests - good sleep satisfaction despite suboptimal timing"
        else:
            return "Your sleep feelings align well with objective timing patterns"
    
    @classmethod
    def _empty_result(cls) -> Dict[str, Any]:
        """Return empty result for insufficient data"""
        return {
            'error': 'Insufficient sleep timing data for objective quality calculation',
            'objective_sleep_quality': None,
            'components': {},
            'metrics': {},
            'analysis': 'Not enough data available'
        }

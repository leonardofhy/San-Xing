"""Data processing module for visualization and analysis.

Processes raw diary data into structured formats suitable for visualization
and statistical analysis before LLM processing.
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
import re

from .models import DiaryEntry
from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class DataProcessor:
    """Process diary data for visualization and analysis"""
    
    def __init__(self, config: Config):
        self.config = config
        self.raw_data: List[Dict[str, Any]] = []
        self.processed_df: Optional[pd.DataFrame] = None
        
    def load_from_snapshot(self, snapshot_path: Path) -> 'DataProcessor':
        """Load data from a snapshot file"""
        try:
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.raw_data = data.get("records", [])
            logger.info("Loaded %d records from snapshot: %s", len(self.raw_data), snapshot_path)
            return self
        except Exception as e:
            logger.error("Failed to load snapshot %s: %s", snapshot_path, str(e))
            raise
            
    def load_from_records(self, records: List[Dict[str, Any]]) -> 'DataProcessor':
        """Load data from raw records"""
        self.raw_data = records
        logger.info("Loaded %d records from raw data", len(records))
        return self
        
    def process_all(self) -> pd.DataFrame:
        """Process all data and return comprehensive DataFrame"""
        if not self.raw_data:
            raise ValueError("No raw data loaded. Call load_from_snapshot() or load_from_records() first")
            
        processed_records = []
        
        for record in self.raw_data:
            processed_record = self._process_single_record(record)
            if processed_record:
                processed_records.append(processed_record)
                
        if not processed_records:
            logger.warning("No valid records after processing")
            self.processed_df = pd.DataFrame()
            return self.processed_df
            
        self.processed_df = pd.DataFrame(processed_records)
        
        # Convert date columns
        if 'timestamp' in self.processed_df.columns:
            self.processed_df['timestamp'] = pd.to_datetime(self.processed_df['timestamp'], errors='coerce')
        if 'logical_date' in self.processed_df.columns:
            self.processed_df['logical_date'] = pd.to_datetime(self.processed_df['logical_date'], errors='coerce')
            
        # Sort by timestamp
        if 'timestamp' in self.processed_df.columns:
            self.processed_df = self.processed_df.sort_values('timestamp').reset_index(drop=True)
            
        logger.info("Processed %d valid records into DataFrame", len(self.processed_df))
        return self.processed_df
        
    def _process_single_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single record into structured format"""
        try:
            # Parse timestamp
            raw_timestamp = str(record.get("Timestamp", "")).strip()
            if not raw_timestamp:
                return None
                
            parsed_dt = self._parse_timestamp(raw_timestamp)
            if not parsed_dt:
                return None
                
            # Early morning adjustment (same logic as DiaryEntry)
            is_early_morning = parsed_dt.hour < self.config.EARLY_MORNING_HOUR
            logical_date = (parsed_dt.date() if not is_early_morning 
                           else (parsed_dt - pd.Timedelta(days=1)).date())
            
            # Extract diary text
            diary_text = str(record.get(self.config.DIARY_COLUMN, "")).strip()
            if len(diary_text) < self.config.MIN_DIARY_LENGTH:
                return None
                
            # Process structured fields
            processed = {
                'raw_timestamp': raw_timestamp,
                'timestamp': parsed_dt,
                'logical_date': logical_date,
                'is_early_morning': is_early_morning,
                'diary_text': diary_text,
                'diary_length': len(diary_text),
                
                # Mood and energy
                'mood_level': self._extract_numeric_value(record.get('今日整體心情感受')),
                'energy_level': self._extract_numeric_value(record.get('今日整體精力水平如何？')),
                
                # Sleep data
                'sleep_bedtime': self._parse_time_value(record.get('昨晚實際入睡時間')),
                'wake_time': self._parse_time_value(record.get('今天實際起床時間')),
                'planned_bedtime': self._parse_time_value(record.get('今晚預計幾點入睡？')),
                'sleep_quality': self._extract_numeric_value(record.get('昨晚睡眠品質如何？')),
                
                # Activities and habits
                'completed_activities': self._parse_activity_list(record.get('今天完成了哪些？')),
                'weight': self._extract_numeric_value(record.get('體重紀錄')),
                'screen_time': record.get('今日手機螢幕使用時間', ''),
                'most_used_app': record.get('今日使用最多的 App', ''),
            }
            
            # Calculate derived metrics
            processed.update(self._calculate_derived_metrics(processed))
            
            return processed
            
        except Exception as e:
            logger.debug("Failed to process record: %s", str(e))
            return None
            
    def _parse_timestamp(self, raw: str) -> Optional[datetime]:
        """Parse timestamp using configured patterns"""
        for pattern in self.config.TIMESTAMP_PATTERNS:
            try:
                return datetime.strptime(raw, pattern)
            except ValueError:
                continue
        return None
        
    def _extract_numeric_value(self, value: Any) -> Optional[float]:
        """Extract numeric value from string or return None"""
        if not value or str(value).strip() == '':
            return None
        try:
            # Handle string representations of numbers
            cleaned = re.sub(r'[^\d.-]', '', str(value))
            if cleaned:
                return float(cleaned)
        except (ValueError, TypeError):
            pass
        return None
        
    def _parse_time_value(self, value: Any) -> Optional[str]:
        """Parse time value and return in HH:MM format"""
        if not value or str(value).strip() == '':
            return None
        
        time_str = str(value).strip()
        
        # Match HH:MM:SS or HH:MM format
        time_match = re.match(r'(\d{1,2}):(\d{2})(?::\d{2})?', time_str)
        if time_match:
            hour, minute = time_match.groups()
            hour_int, minute_int = int(hour), int(minute)
            if 0 <= hour_int <= 23 and 0 <= minute_int <= 59:  # Validate time
                return f"{hour_int:02d}:{minute_int:02d}"
        
        # Match HHMM format (4 digits)
        if re.match(r'^\d{4}$', time_str) and len(time_str) == 4:
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            if 0 <= hour <= 23 and 0 <= minute <= 59:  # Validate time
                return f"{hour:02d}:{minute:02d}"
        
        return None
        
    def _parse_activity_list(self, value: Any) -> List[str]:
        """Parse comma-separated activity list"""
        if not value or str(value).strip() == '':
            return []
        
        activities = [activity.strip() for activity in str(value).split(',')]
        return [activity for activity in activities if activity]
        
    def _calculate_derived_metrics(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived metrics from processed record"""
        derived = {}
        
        # Sleep duration (if both bedtime and wake time available)
        if record['sleep_bedtime'] and record['wake_time']:
            try:
                bedtime = datetime.strptime(record['sleep_bedtime'], '%H:%M').time()
                wake_time = datetime.strptime(record['wake_time'], '%H:%M').time()
                
                # Handle cross-midnight sleep
                bed_datetime = datetime.combine(record['logical_date'], bedtime)
                wake_datetime = datetime.combine(record['logical_date'], wake_time)
                
                if wake_time < bedtime:  # Slept past midnight
                    wake_datetime += pd.Timedelta(days=1)
                
                sleep_duration = (wake_datetime - bed_datetime).total_seconds() / 3600
                derived['sleep_duration_hours'] = round(sleep_duration, 2)
            except Exception:
                derived['sleep_duration_hours'] = None
        else:
            derived['sleep_duration_hours'] = None
            
        # Activity metrics
        activities = record.get('completed_activities', [])
        derived['activity_count'] = len(activities)
        
        # Positive vs negative activities (basic classification)
        positive_keywords = ['運動', '閱讀', '英文', '工作有實質進展', '自我反思', '社交活動']
        negative_keywords = ['賴床', '重口味飲食', '久坐', '含糖飲料']
        
        positive_count = sum(1 for activity in activities 
                           if any(keyword in activity for keyword in positive_keywords))
        negative_count = sum(1 for activity in activities 
                           if any(keyword in activity for keyword in negative_keywords))
        
        derived['positive_activities'] = positive_count
        derived['negative_activities'] = negative_count
        derived['activity_balance'] = positive_count - negative_count
        
        return derived
        
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of processed data"""
        if self.processed_df is None or self.processed_df.empty:
            return {}
            
        df = self.processed_df
        stats = {
            'total_entries': len(df),
            'date_range': {
                'start': df['logical_date'].min().isoformat() if 'logical_date' in df.columns else None,
                'end': df['logical_date'].max().isoformat() if 'logical_date' in df.columns else None,
            },
            'mood_stats': {
                'mean': df['mood_level'].mean() if 'mood_level' in df.columns else None,
                'median': df['mood_level'].median() if 'mood_level' in df.columns else None,
                'std': df['mood_level'].std() if 'mood_level' in df.columns else None,
            },
            'sleep_stats': {
                'avg_duration': df['sleep_duration_hours'].mean() if 'sleep_duration_hours' in df.columns else None,
                'avg_bedtime': self._calculate_avg_time(df, 'sleep_bedtime'),
                'avg_wake_time': self._calculate_avg_time(df, 'wake_time'),
            },
            'activity_stats': {
                'avg_total': df['activity_count'].mean() if 'activity_count' in df.columns else None,
                'avg_positive': df['positive_activities'].mean() if 'positive_activities' in df.columns else None,
                'avg_negative': df['negative_activities'].mean() if 'negative_activities' in df.columns else None,
            },
            'text_stats': {
                'avg_length': df['diary_length'].mean() if 'diary_length' in df.columns else None,
                'median_length': df['diary_length'].median() if 'diary_length' in df.columns else None,
            }
        }
        
        return stats
        
    def _calculate_avg_time(self, df: pd.DataFrame, column: str) -> Optional[str]:
        """Calculate average time from time strings"""
        try:
            if column not in df.columns:
                return None
                
            times = df[column].dropna()
            if times.empty:
                return None
                
            # Convert to minutes since midnight
            minutes_list = []
            for time_str in times:
                try:
                    hours, minutes = map(int, time_str.split(':'))
                    total_minutes = hours * 60 + minutes
                    minutes_list.append(total_minutes)
                except (ValueError, AttributeError):
                    continue
                    
            if not minutes_list:
                return None
                
            avg_minutes = sum(minutes_list) / len(minutes_list)
            avg_hours = int(avg_minutes // 60)
            avg_mins = int(avg_minutes % 60)
            
            return f"{avg_hours:02d}:{avg_mins:02d}"
            
        except Exception:
            return None
            
    def export_csv(self, output_path: Path) -> Path:
        """Export processed data to CSV"""
        if self.processed_df is None or self.processed_df.empty:
            raise ValueError("No processed data to export")
            
        self.processed_df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info("Exported processed data to CSV: %s", output_path)
        return output_path
        
    def export_analysis_ready(self, output_path: Path) -> Path:
        """Export analysis-ready JSON with summary stats"""
        if self.processed_df is None or self.processed_df.empty:
            raise ValueError("No processed data to export")
            
        # Convert DataFrame to JSON-serializable format
        df_records = self.processed_df.copy()
        
        # Convert datetime columns to strings
        for col in df_records.columns:
            if df_records[col].dtype == 'datetime64[ns]':
                df_records[col] = df_records[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            elif col == 'logical_date':
                df_records[col] = df_records[col].astype(str)
                
        analysis_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_records': len(df_records),
                'config_version': self.config.VERSION,
            },
            'summary_stats': self.get_summary_stats(),
            'records': df_records.to_dict('records'),
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
            
        logger.info("Exported analysis-ready data: %s", output_path)
        return output_path
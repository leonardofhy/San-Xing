"""
Robust Data Loader for San-Xing Dashboard
Addresses common data loading failures with comprehensive error handling and fallbacks
"""

import streamlit as st
import pandas as pd
import json
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import traceback

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

class RobustDataLoader:
    """
    Robust data loader with comprehensive error handling and fallback mechanisms
    """
    
    def __init__(self):
        self.parent_dir = parent_dir
        self.config = None
        self.processor = None
        self.last_error = None
        
    def load_config(self) -> bool:
        """Load configuration with multiple fallback strategies"""
        try:
            # Strategy 1: Try Config.from_file (preferred)
            from src.config import Config
            config_path = self.parent_dir / "config.local.toml"
            
            if not config_path.exists():
                self.last_error = f"Config file not found: {config_path}"
                return False
            
            self.config = Config.from_file(config_path)
            return True
            
        except ImportError as e:
            self.last_error = f"Failed to import Config class: {e}"
            return False
        except Exception as e:
            self.last_error = f"Config loading failed: {e}"
            return False
    
    def find_best_snapshot(self) -> Optional[Path]:
        """Find the best available snapshot file"""
        raw_dir = self.parent_dir / "data" / "raw"
        
        if not raw_dir.exists():
            self.last_error = f"Raw data directory not found: {raw_dir}"
            return None
        
        # Priority order for snapshot files
        snapshot_priorities = [
            "snapshot_latest.json",
            "snapshot_010f189dd4de4959.json",  # Specific known file
        ]
        
        # First try priority files
        for snapshot_name in snapshot_priorities:
            snapshot_path = raw_dir / snapshot_name
            if snapshot_path.exists():
                # For snapshot_latest.json, check if it's a redirect
                if snapshot_name == "snapshot_latest.json":
                    try:
                        with open(snapshot_path, 'r') as f:
                            content = json.load(f)
                        
                        # If it's a redirect, use the actual file
                        if 'file' in content:
                            actual_file = raw_dir / content['file']
                            if actual_file.exists():
                                return actual_file
                    except Exception:
                        pass
                
                return snapshot_path
        
        # If no priority files, find any snapshot
        snapshot_files = list(raw_dir.glob("snapshot_*.json"))
        snapshot_files = [f for f in snapshot_files if f.name != "snapshot_latest.json"]
        
        if snapshot_files:
            # Sort by modification time, newest first
            snapshot_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return snapshot_files[0]
        
        self.last_error = "No snapshot files found"
        return None
    
    def load_and_process_data(self) -> Optional[pd.DataFrame]:
        """Load and process data with robust error handling"""
        try:
            # Step 1: Load config
            if not self.load_config():
                return None
            
            # Step 2: Import processor
            from src.data_processor import DataProcessor
            self.processor = DataProcessor(self.config)
            
            # Step 3: Find snapshot
            snapshot_path = self.find_best_snapshot()
            if not snapshot_path:
                return None
            
            # Step 4: Load snapshot
            try:
                self.processor.load_from_snapshot(snapshot_path)
            except Exception as e:
                # Try loading directly from JSON
                with open(snapshot_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                records = data.get('records', [])
                if not records:
                    self.last_error = f"No records found in snapshot: {snapshot_path}"
                    return None
                
                self.processor.load_from_records(records)
            
            # Step 5: Process data
            df = self.processor.process_all()
            
            if df is None or df.empty:
                self.last_error = "Data processing resulted in empty DataFrame"
                return None
            
            return df
            
        except Exception as e:
            self.last_error = f"Data loading failed: {e}\n{traceback.format_exc()}"
            return None
    
    def convert_to_kpi_format(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Convert processed data to KPI format"""
        try:
            if df is None or df.empty:
                self.last_error = "Input DataFrame is empty"
                return None
            
            # Create KPI data format with robust column mapping
            kpi_data = pd.DataFrame()
            
            column_mapping = {
                'logical_date': 'date',
                'mood_level': 'mood',
                'energy_level': 'energy',  
                'sleep_quality': 'sleep_quality',
                'sleep_duration_hours': 'sleep_duration',
                'activity_balance': 'activity_balance',
                'positive_activities': 'positive_activities',
                'negative_activities': 'negative_activities'
            }
            
            mapped_columns = []
            for orig_col, new_col in column_mapping.items():
                if orig_col in df.columns:
                    kpi_data[new_col] = df[orig_col]
                    mapped_columns.append(f"{orig_col} -> {new_col}")
            
            if kpi_data.empty:
                self.last_error = f"No mappable columns found. Available: {list(df.columns)}"
                return None
            
            # Convert date column with error handling
            if 'date' in kpi_data.columns:
                try:
                    kpi_data['date'] = pd.to_datetime(kpi_data['date'], errors='coerce')
                except Exception as e:
                    self.last_error = f"Date conversion failed: {e}"
                    return None
            
            # Filter data intelligently
            key_columns = ['mood', 'energy', 'sleep_quality']
            available_key_columns = [col for col in key_columns if col in kpi_data.columns]
            
            if available_key_columns:
                before_filter = len(kpi_data)
                kpi_data = kpi_data.dropna(subset=available_key_columns, how='all')
                after_filter = len(kpi_data)
                
                if after_filter == 0:
                    self.last_error = f"All rows filtered out. Before: {before_filter}, After: {after_filter}"
                    return None
            else:
                self.last_error = f"No key columns available. Mapped: {mapped_columns}"
                return None
            
            return kpi_data
            
        except Exception as e:
            self.last_error = f"KPI conversion failed: {e}\n{traceback.format_exc()}"
            return None
    
    def get_data_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get comprehensive data information"""
        if df is None or df.empty:
            return {"error": "No data available"}
        
        info = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "date_range": {},
            "data_quality": {},
            "sample_data": df.head().to_dict('records') if not df.empty else []
        }
        
        # Date range
        if 'date' in df.columns:
            try:
                date_col = pd.to_datetime(df['date'], errors='coerce')
                valid_dates = date_col.dropna()
                if len(valid_dates) > 0:
                    info["date_range"] = {
                        "start": valid_dates.min().strftime('%Y-%m-%d'),
                        "end": valid_dates.max().strftime('%Y-%m-%d'),
                        "valid_dates": len(valid_dates),
                        "invalid_dates": len(date_col) - len(valid_dates)
                    }
            except Exception:
                pass
        
        # Data quality metrics
        for col in df.columns:
            non_null_count = df[col].count()
            null_count = len(df) - non_null_count
            info["data_quality"][col] = {
                "non_null": non_null_count,
                "null": null_count,
                "completeness": non_null_count / len(df) if len(df) > 0 else 0,
                "dtype": str(df[col].dtype)
            }
        
        return info

# Streamlit integration functions
@st.cache_data
def load_real_data_robust() -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]], Optional[str]]:
    """
    Robust data loading with caching
    Returns: (kpi_data, data_info, error_message)
    """
    loader = RobustDataLoader()
    
    # Load and process
    df = loader.load_and_process_data()
    if df is None:
        return None, None, loader.last_error
    
    # Convert to KPI format
    kpi_data = loader.convert_to_kpi_format(df)
    if kpi_data is None:
        return None, None, loader.last_error
    
    # Get data info
    data_info = loader.get_data_info(kpi_data)
    
    return kpi_data, data_info, None

def display_data_loading_status():
    """Display data loading status with detailed diagnostics"""
    st.subheader("📊 Real Data Loading Status")
    
    with st.spinner("Loading real data from Google Sheets..."):
        kpi_data, data_info, error = load_real_data_robust()
    
    if error:
        st.error(f"❌ Data Loading Failed")
        st.error(error)
        
        # Show diagnostic information
        with st.expander("🔍 Diagnostic Information"):
            loader = RobustDataLoader()
            
            # Check environment
            st.write("**Environment Check:**")
            config_path = loader.parent_dir / "config.local.toml"
            raw_dir = loader.parent_dir / "data" / "raw"
            
            st.write(f"- Config file exists: {config_path.exists()}")
            st.write(f"- Raw data directory exists: {raw_dir.exists()}")
            
            if raw_dir.exists():
                snapshot_files = list(raw_dir.glob("snapshot_*.json"))
                st.write(f"- Available snapshots: {len(snapshot_files)}")
                for f in snapshot_files[:5]:  # Show first 5
                    st.write(f"  - {f.name}")
            
            # Try to find the specific issue
            st.write("**Detailed Error Analysis:**")
            if not config_path.exists():
                st.error("Config file missing - this is likely the main issue")
            elif not raw_dir.exists():
                st.error("Raw data directory missing - no data to load")
            elif len(snapshot_files) == 0:
                st.error("No snapshot files found - need to run data collection first")
            else:
                st.warning("Data exists but processing failed - check error details above")
        
        return None, None
    
    else:
        st.success(f"✅ Real Data Loaded Successfully!")
        st.success(f"📈 {data_info['total_rows']} entries ready for analysis")
        
        # Show data summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Entries", data_info['total_rows'])
        
        with col2:
            date_range = data_info.get('date_range', {})
            if date_range:
                st.metric("Date Range", f"{date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}")
            else:
                st.metric("Date Range", "N/A")
        
        with col3:
            # Calculate average completeness
            quality = data_info.get('data_quality', {})
            if quality:
                avg_completeness = sum(col_info['completeness'] for col_info in quality.values()) / len(quality)
                st.metric("Data Completeness", f"{avg_completeness:.0%}")
            else:
                st.metric("Data Completeness", "N/A")
        
        # Show detailed info in expander
        with st.expander("📋 Detailed Data Information"):
            st.json(data_info)
        
        return kpi_data, data_info

# Fallback data generation
def create_fallback_data(days: int = 30) -> pd.DataFrame:
    """Create fallback synthetic data when real data fails"""
    import numpy as np
    from datetime import datetime, timedelta
    
    np.random.seed(42)
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=days, freq='D')
    
    # Create realistic synthetic data
    trend = np.linspace(0, 0.5, days)
    weekly_pattern = 0.3 * np.sin(2 * np.pi * np.arange(days) / 7)
    base_wellbeing = 6.0 + trend + weekly_pattern + np.random.normal(0, 0.8, days)
    
    fallback_data = pd.DataFrame({
        'date': dates,
        'mood': np.clip(base_wellbeing + np.random.normal(0, 0.5, days), 1, 10),
        'energy': np.clip(base_wellbeing - 0.3 + np.random.normal(0, 0.6, days), 1, 10),
        'sleep_quality': np.clip(base_wellbeing + 0.2 + np.random.normal(0, 0.4, days), 1, 10),
        'sleep_duration': np.clip(7.5 + 0.2 * trend + np.random.normal(0, 0.8, days), 4, 12),
        'activity_balance': np.random.randint(-2, 4, days),
        'positive_activities': np.random.randint(1, 5, days),
        'negative_activities': np.random.randint(0, 3, days)
    })
    
    # Round to realistic precision
    for col in ['mood', 'energy', 'sleep_quality', 'sleep_duration']:
        fallback_data[col] = fallback_data[col].round(1)
    
    return fallback_data
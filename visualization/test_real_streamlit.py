#!/usr/bin/env python3
"""
Test real data loading in actual Streamlit context
This will help identify the real issues with data loading in Streamlit
"""

import streamlit as st
import sys
import traceback
from pathlib import Path
import pandas as pd

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

st.set_page_config(
    page_title="Data Loading Test", 
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 San-Xing Data Loading Test")

def test_step_by_step():
    """Test each step and show detailed error information"""
    
    st.header("Step-by-Step Data Loading Test")
    
    # Step 1: Test imports
    st.subheader("1. Testing Module Imports")
    try:
        from src.config import Config
        from src.data_processor import DataProcessor
        st.success("✅ Successfully imported Config and DataProcessor")
        import_success = True
    except Exception as e:
        st.error(f"❌ Import failed: {str(e)}")
        st.code(traceback.format_exc())
        import_success = False
        return
    
    # Step 2: Test config loading
    st.subheader("2. Testing Config Loading")
    try:
        config_path = parent_dir / "config.local.toml"
        st.write(f"Config path: {config_path}")
        st.write(f"Config exists: {config_path.exists()}")
        
        if not config_path.exists():
            st.error("❌ Config file not found")
            return
            
        config = Config.from_file(config_path)
        st.success("✅ Config loaded successfully")
        st.write(f"SPREADSHEET_ID: {config.SPREADSHEET_ID}")
        st.write(f"TAB_NAME: {config.TAB_NAME}")
        config_success = True
    except Exception as e:
        st.error(f"❌ Config loading failed: {str(e)}")
        st.code(traceback.format_exc())
        return
    
    # Step 3: Test snapshot file
    st.subheader("3. Testing Snapshot File")
    try:
        snapshot_path = parent_dir / "data" / "raw" / "snapshot_010f189dd4de4959.json"
        st.write(f"Snapshot path: {snapshot_path}")
        st.write(f"Snapshot exists: {snapshot_path.exists()}")
        
        if not snapshot_path.exists():
            # Look for other snapshot files
            raw_dir = parent_dir / "data" / "raw"
            if raw_dir.exists():
                snapshot_files = list(raw_dir.glob("snapshot_*.json"))
                st.warning(f"❌ Specific snapshot not found, but found {len(snapshot_files)} other snapshots:")
                for f in snapshot_files:
                    st.write(f"  - {f.name}")
                if snapshot_files:
                    snapshot_path = snapshot_files[0]  # Use the first one
                    st.info(f"Using: {snapshot_path.name}")
                else:
                    st.error("No snapshot files found at all")
                    return
            else:
                st.error("Raw data directory doesn't exist")
                return
        
        st.success(f"✅ Snapshot file available: {snapshot_path.name}")
        snapshot_success = True
    except Exception as e:
        st.error(f"❌ Snapshot check failed: {str(e)}")
        st.code(traceback.format_exc())
        return
    
    # Step 4: Test data processing
    st.subheader("4. Testing Data Processing")
    try:
        processor = DataProcessor(config)
        processor.load_from_snapshot(snapshot_path)
        st.success("✅ Data loaded into processor")
        
        df = processor.process_all()
        st.success(f"✅ Data processed: {len(df)} rows, {len(df.columns)} columns")
        
        # Show column info
        st.write("**Processed columns:**")
        col_info = []
        for col in df.columns:
            non_null_count = df[col].count()
            col_info.append(f"- {col}: {non_null_count}/{len(df)} non-null values")
        st.write("\n".join(col_info))
        
        process_success = True
    except Exception as e:
        st.error(f"❌ Data processing failed: {str(e)}")
        st.code(traceback.format_exc())
        return
    
    # Step 5: Test KPI data conversion
    st.subheader("5. Testing KPI Data Conversion")
    try:
        # Convert to KPI format
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
        
        for orig_col, new_col in column_mapping.items():
            if orig_col in df.columns:
                kpi_data[new_col] = df[orig_col]
        
        # Convert date column
        if 'date' in kpi_data.columns:
            kpi_data['date'] = pd.to_datetime(kpi_data['date'])
        
        # Filter out rows with all NaN values in key metrics
        key_columns = ['mood', 'energy', 'sleep_quality']
        available_key_columns = [col for col in key_columns if col in kpi_data.columns]
        
        if available_key_columns:
            before_filter = len(kpi_data)
            kpi_data = kpi_data.dropna(subset=available_key_columns, how='all')
            after_filter = len(kpi_data)
            st.success(f"✅ KPI data ready: {after_filter} rows (filtered from {before_filter})")
        else:
            st.warning("⚠️ No key columns available for filtering")
        
        # Show sample data
        if not kpi_data.empty:
            st.write("**Sample KPI data:**")
            st.dataframe(kpi_data.head())
            
            # Show data types and non-null counts
            st.write("**KPI Data Info:**")
            for col in kpi_data.columns:
                non_null = kpi_data[col].count()
                dtype = kpi_data[col].dtype
                st.write(f"- {col}: {non_null}/{len(kpi_data)} non-null, type: {dtype}")
        
        conversion_success = True
        return kpi_data
        
    except Exception as e:
        st.error(f"❌ KPI conversion failed: {str(e)}")
        st.code(traceback.format_exc())
        return None

def test_streamlit_caching():
    """Test if Streamlit caching causes issues"""
    st.header("Testing Streamlit Caching Behavior")
    
    @st.cache_data
    def cached_load_attempt():
        try:
            from src.config import Config
            from src.data_processor import DataProcessor
            
            config_path = parent_dir / "config.local.toml"
            config = Config.from_file(config_path)
            
            snapshot_path = parent_dir / "data" / "raw" / "snapshot_010f189dd4de4959.json"
            if not snapshot_path.exists():
                raw_dir = parent_dir / "data" / "raw"
                snapshot_files = list(raw_dir.glob("snapshot_*.json"))
                if snapshot_files:
                    snapshot_path = snapshot_files[0]
                else:
                    raise FileNotFoundError("No snapshot files found")
            
            processor = DataProcessor(config)
            processor.load_from_snapshot(snapshot_path)
            df = processor.process_all()
            
            # Convert to KPI format
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
            
            for orig_col, new_col in column_mapping.items():
                if orig_col in df.columns:
                    kpi_data[new_col] = df[orig_col]
            
            if 'date' in kpi_data.columns:
                kpi_data['date'] = pd.to_datetime(kpi_data['date'])
            
            key_columns = ['mood', 'energy', 'sleep_quality']
            available_key_columns = [col for col in key_columns if col in kpi_data.columns]
            
            if available_key_columns:
                kpi_data = kpi_data.dropna(subset=available_key_columns, how='all')
            
            return kpi_data, None
            
        except Exception as e:
            return None, str(e)
    
    kpi_data, error = cached_load_attempt()
    
    if error:
        st.error(f"❌ Cached loading failed: {error}")
    else:
        st.success(f"✅ Cached loading successful: {len(kpi_data)} rows")
        st.dataframe(kpi_data.head())

def main():
    """Main test function"""
    
    st.write("This test will help identify why real data loading fails in Streamlit.")
    
    with st.expander("🔍 Detailed Step-by-Step Test", expanded=True):
        kpi_data = test_step_by_step()
    
    st.divider()
    
    with st.expander("💾 Streamlit Caching Test"):
        test_streamlit_caching()
    
    st.divider()
    
    # Show environment info
    with st.expander("🖥️ Environment Info"):
        st.write(f"**Python version:** {sys.version}")
        st.write(f"**Working directory:** {Path.cwd()}")
        st.write(f"**Parent directory:** {parent_dir}")
        st.write(f"**Python path includes parent:** {str(parent_dir) in sys.path}")
        
        # Check if files exist
        st.write("**File existence check:**")
        config_path = parent_dir / "config.local.toml"
        st.write(f"- Config file: {config_path.exists()}")
        
        raw_dir = parent_dir / "data" / "raw"
        st.write(f"- Raw data dir: {raw_dir.exists()}")
        
        if raw_dir.exists():
            snapshot_files = list(raw_dir.glob("snapshot_*.json"))
            st.write(f"- Snapshot files: {len(snapshot_files)}")

if __name__ == "__main__":
    main()
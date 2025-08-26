#!/usr/bin/env python3
"""
Debug script to test real data loading
"""

import sys
import traceback
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

def test_config_loading():
    """Test configuration loading"""
    try:
        import toml
        config_path = parent_dir / "config.local.toml"
        print(f"Config path: {config_path}")
        print(f"Config exists: {config_path.exists()}")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_dict = toml.load(f)
            print("✓ Config loaded successfully")
            print(f"Config keys: {list(config_dict.keys())}")
            return config_dict
        else:
            print("❌ Config file not found")
            return None
    except Exception as e:
        print(f"❌ Config loading error: {e}")
        traceback.print_exc()
        return None

def test_config_class():
    """Test Config class import and initialization"""
    try:
        from src.config import Config
        print("✓ Config class imported successfully")
        
        # Use the proper Config.from_file method
        config_path = parent_dir / "config.local.toml"
        if config_path.exists():
            config = Config.from_file(config_path)
            print("✓ Config object created successfully")
            print(f"Config attributes available: SPREADSHEET_ID={config.SPREADSHEET_ID}, TAB_NAME={config.TAB_NAME}")
            return config
        else:
            print("❌ Config file not found")
            return None
    except Exception as e:
        print(f"❌ Config class error: {e}")
        traceback.print_exc()
        return None

def test_snapshot_loading():
    """Test snapshot file loading"""
    try:
        snapshot_path = parent_dir / "data" / "raw" / "snapshot_010f189dd4de4959.json"
        print(f"Snapshot path: {snapshot_path}")
        print(f"Snapshot exists: {snapshot_path.exists()}")
        
        if snapshot_path.exists():
            import json
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("✓ Snapshot loaded successfully")
            print(f"Records count: {len(data.get('records', []))}")
            return data
        else:
            print("❌ Snapshot file not found")
            # Check what files are available
            raw_dir = parent_dir / "data" / "raw"
            if raw_dir.exists():
                print(f"Available files in {raw_dir}:")
                for f in raw_dir.glob("*.json"):
                    print(f"  - {f.name}")
            return None
    except Exception as e:
        print(f"❌ Snapshot loading error: {e}")
        traceback.print_exc()
        return None

def test_data_processor():
    """Test DataProcessor class"""
    try:
        from src.data_processor import DataProcessor
        print("✓ DataProcessor imported successfully")
        
        config = test_config_class()
        if not config:
            return None
            
        processor = DataProcessor(config)
        print("✓ DataProcessor created successfully")
        
        snapshot_data = test_snapshot_loading()
        if not snapshot_data:
            return None
            
        # Load from records directly
        processor.load_from_records(snapshot_data.get('records', []))
        print("✓ Records loaded into processor")
        
        df = processor.process_all()
        print(f"✓ Data processed successfully: {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ DataProcessor error: {e}")
        traceback.print_exc()
        return None

def test_kpi_data_conversion(df):
    """Test converting processed data to KPI format"""
    try:
        import pandas as pd
        
        if df is None or df.empty:
            print("❌ No data to convert")
            return None
            
        print(f"Input DataFrame shape: {df.shape}")
        print(f"Input columns: {list(df.columns)}")
        
        # Create KPI data format
        kpi_data = pd.DataFrame()
        
        # Map columns
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
                print(f"✓ Mapped {orig_col} -> {new_col}")
            else:
                print(f"❌ Missing column: {orig_col}")
        
        # Convert date column
        if 'date' in kpi_data.columns:
            kpi_data['date'] = pd.to_datetime(kpi_data['date'])
            print("✓ Date column converted")
        
        # Filter out rows with all NaN values in key metrics
        key_columns = ['mood', 'energy', 'sleep_quality']
        available_key_columns = [col for col in key_columns if col in kpi_data.columns]
        
        if available_key_columns:
            before_filter = len(kpi_data)
            kpi_data = kpi_data.dropna(subset=available_key_columns, how='all')
            after_filter = len(kpi_data)
            print(f"✓ Filtered data: {before_filter} -> {after_filter} rows")
        
        print(f"Final KPI data shape: {kpi_data.shape}")
        print(f"Final columns: {list(kpi_data.columns)}")
        
        # Show sample data
        if not kpi_data.empty:
            print("\nSample data:")
            print(kpi_data.head())
        
        return kpi_data
        
    except Exception as e:
        print(f"❌ KPI conversion error: {e}")
        traceback.print_exc()
        return None

def main():
    """Run all tests"""
    print("🔧 Debugging San-Xing Real Data Loading")
    print("=" * 50)
    
    # Test step by step
    print("\n1. Testing Config Loading...")
    config = test_config_class()
    
    print("\n2. Testing Snapshot Loading...")
    snapshot_data = test_snapshot_loading()
    
    print("\n3. Testing Data Processing...")
    df = test_data_processor()
    
    print("\n4. Testing KPI Data Conversion...")
    kpi_data = test_kpi_data_conversion(df)
    
    print("\n" + "=" * 50)
    if kpi_data is not None and not kpi_data.empty:
        print("✅ SUCCESS: Real data loading pipeline works!")
        print(f"Final result: {len(kpi_data)} entries ready for KPI calculations")
    else:
        print("❌ FAILURE: Real data loading pipeline has issues")
    
    return kpi_data

if __name__ == "__main__":
    main()
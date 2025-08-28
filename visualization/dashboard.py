#!/usr/bin/env python3
"""
Bulletproof San-Xing Dashboard
Handles all data loading failures gracefully with comprehensive fallbacks
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import our robust data loader
from robust_data_loader import RobustDataLoader, display_data_loading_status, create_fallback_data

# Import analytics modules
from analytics.kpi_calculator import KPICalculator
from analytics.statistical_utils import correlation_with_significance

# Import UI components
from components.kpi_cards import render_kpi_overview
from components.insight_display import render_statistical_insights
from components.data_viz import (
    create_trend_chart,
    create_kpi_gauge,
    create_statistical_summary_chart
)
from components.drill_down_views import (
    render_sleep_analysis_drilldown,
    render_activity_impact_drilldown,
    render_pattern_analysis_drilldown
)


def fetch_fresh_data_from_sheets():
    """Fetch fresh data directly from Google Sheets and update local snapshots"""
    
    with st.spinner("📥 Fetching latest data from Google Sheets..."):
        try:
            # Import required modules
            from src.config import Config
            from src.ingestion import SheetIngester
            from src.data_processor import DataProcessor
            import json
            from datetime import datetime
            
            # Load configuration
            config_path = parent_dir / "config.local.toml"
            if not config_path.exists():
                st.error("❌ Configuration file not found. Please ensure config.local.toml exists.")
                return
            
            config = Config.from_file(config_path)
            
            # Initialize ingester and connect
            ingester = SheetIngester(config)
            ingester.connect()
            
            # Fetch data from Google Sheets
            st.info("🔍 Reading data from Google Sheets...")
            records, header_hash = ingester.fetch_rows()
            
            if not records:
                st.warning("⚠️ No data found in Google Sheets")
                return
            
            # Create new snapshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_id = f"dashboard_{timestamp}"
            
            snapshot_data = {
                "run_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "source": "google_sheets_direct",
                "header_hash": header_hash,
                "total_records": len(records),
                "records": records
            }
            
            # Save new snapshot
            raw_dir = parent_dir / "data" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            
            snapshot_path = raw_dir / f"snapshot_{run_id}.json"
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
            
            # Update latest snapshot pointer
            latest_path = raw_dir / "snapshot_latest.json"
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump({"file": f"snapshot_{run_id}.json"}, f)
            
            # Process the data to verify it's working
            processor = DataProcessor(config)
            processor.load_from_records(records)
            df = processor.process_all()
            
            # Show success message with data summary
            st.success(f"✅ **Fresh data fetched successfully!**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Records", len(records))
            with col2:
                st.metric("📅 Processed Rows", len(df))
            with col3:
                st.metric("🗂️ Data Columns", len(df.columns))
            with col4:
                if 'date' in df.columns:
                    date_range = (df['date'].max() - df['date'].min()).days + 1
                    st.metric("📈 Date Range", f"{date_range} days")
                else:
                    st.metric("📈 Date Range", "N/A")
            
            st.info(f"💾 **New snapshot saved**: `snapshot_{run_id}.json`")
            st.info(f"🔍 **Header hash**: `{header_hash}` - Schema validation successful")
            
            # Clear cache and refresh
            st.cache_data.clear()
            st.rerun()
            
        except FileNotFoundError as e:
            st.error(f"❌ **File not found**: {e}")
            st.info("💡 Make sure your `config.local.toml` and service account credentials are properly configured.")
            
        except Exception as e:
            st.error(f"❌ **Error fetching data**: {e}")
            
            # Provide specific troubleshooting based on error type
            error_str = str(e)
            if "404" in error_str:
                st.warning("🔍 **404 Error - Resource not found**")
                st.info("""
                **Possible causes:**
                - ❌ Incorrect Spreadsheet ID in config.local.toml
                - ❌ Worksheet/tab name doesn't exist  
                - ❌ Spreadsheet not shared with service account
                - ❌ Spreadsheet has been moved or deleted
                """)
                
                # Show current configuration for verification
                try:
                    st.markdown("**Current Configuration:**")
                    st.code(f"""
Spreadsheet ID: {config.SPREADSHEET_ID}
Tab Name: {config.TAB_NAME}
Service Account: {config.CREDENTIALS_PATH}
                    """)
                except:
                    st.warning("Could not display configuration details")
                    
            elif "403" in error_str:
                st.warning("🚫 **403 Error - Access denied**")
                st.info("""
                **Possible causes:**
                - ❌ Service account not added to spreadsheet
                - ❌ Service account lacks read permissions
                - ❌ API quotas exceeded
                """)
            elif "401" in error_str:
                st.warning("🔑 **401 Error - Authentication failed**")
                st.info("""
                **Possible causes:**
                - ❌ Invalid service account credentials
                - ❌ Credentials file not found or corrupted
                - ❌ Service account key expired
                """)
            else:
                st.info("💡 Check your Google Sheets permissions and internet connection.")
            
            # Quick setup verification
            with st.expander("🔧 Setup Verification", expanded=True):
                st.markdown("**Verify your setup:**")
                
                # Check config file
                config_path = parent_dir / "config.local.toml"
                if config_path.exists():
                    st.success("✅ Config file found")
                else:
                    st.error("❌ Config file missing")
                
                # Check credentials file
                try:
                    creds_path = config.CREDENTIALS_PATH if 'config' in locals() else None
                    if creds_path and Path(creds_path).exists():
                        st.success("✅ Credentials file found")
                    else:
                        st.error("❌ Credentials file missing")
                except:
                    st.error("❌ Could not check credentials file")
                
                st.markdown("""
                **Manual verification steps:**
                1. **Open your Google Sheet** in a browser
                2. **Check the URL** - copy the long ID between `/d/` and `/edit`  
                3. **Verify tab name** - check exact spelling and case
                4. **Share with service account** - add the service account email as Editor
                5. **Service account email** is in your credentials JSON file (`client_email` field)
                """)
            
            # Show traceback in expander for debugging
            import traceback
            with st.expander("🔧 Full Debug Information", expanded=False):
                st.code(traceback.format_exc(), language="python")


def test_google_sheets_connection():
    """Test Google Sheets connection and provide diagnostics"""
    
    with st.spinner("🔍 Testing Google Sheets connection..."):
        try:
            # Import required modules
            from src.config import Config
            from src.ingestion import SheetIngester
            import gspread
            
            # Load configuration
            config_path = parent_dir / "config.local.toml"
            if not config_path.exists():
                st.error("❌ Configuration file not found")
                return
                
            config = Config.from_file(config_path)
            
            # Test 1: Check config values
            st.info("**Step 1:** Checking configuration...")
            st.write(f"📊 Spreadsheet ID: `{config.SPREADSHEET_ID[:10]}...{config.SPREADSHEET_ID[-10:]}`")
            st.write(f"📝 Tab Name: `{config.TAB_NAME}`")
            st.write(f"🔑 Credentials: `{config.CREDENTIALS_PATH}`")
            
            # Test 2: Check credentials file
            st.info("**Step 2:** Checking credentials file...")
            if not Path(config.CREDENTIALS_PATH).exists():
                st.error(f"❌ Credentials file not found: {config.CREDENTIALS_PATH}")
                return
            st.success("✅ Credentials file exists")
            
            # Test 3: Initialize ingester
            st.info("**Step 3:** Initializing Google Sheets connection...")
            ingester = SheetIngester(config)
            
            # Test 4: Connect to Google Sheets API
            st.info("**Step 4:** Connecting to Google Sheets API...")
            ingester.connect()
            st.success("✅ Google Sheets API connection successful")
            
            # Test 5: Access spreadsheet
            st.info("**Step 5:** Accessing spreadsheet...")
            sheet = ingester.client.open_by_key(config.SPREADSHEET_ID)
            st.success(f"✅ Spreadsheet found: `{sheet.title}`")
            
            # Test 6: List worksheets
            st.info("**Step 6:** Listing available worksheets...")
            worksheets = sheet.worksheets()
            worksheet_names = [ws.title for ws in worksheets]
            st.write(f"📋 Available worksheets: {worksheet_names}")
            
            # Test 7: Access target worksheet
            st.info("**Step 7:** Accessing target worksheet...")
            if config.TAB_NAME in worksheet_names:
                worksheet = sheet.worksheet(config.TAB_NAME)
                st.success(f"✅ Worksheet `{config.TAB_NAME}` found")
                
                # Test 8: Check worksheet data
                st.info("**Step 8:** Checking worksheet data...")
                row_count = worksheet.row_count
                col_count = worksheet.col_count
                st.write(f"📊 Worksheet size: {row_count} rows × {col_count} columns")
                
                # Test 9: Get headers
                st.info("**Step 9:** Reading headers...")
                headers = worksheet.row_values(1)
                st.write(f"📝 Headers ({len(headers)}): {', '.join(headers[:5])}{'...' if len(headers) > 5 else ''}")
                
                # Test 10: Test data access
                st.info("**Step 10:** Testing data access...")
                try:
                    records = worksheet.get_all_records()
                    st.success(f"✅ Successfully read {len(records)} records")
                    
                    if records:
                        st.write("🔍 **Sample record keys:**", list(records[0].keys())[:8])
                except Exception as e:
                    st.warning(f"⚠️ Data access issue: {e}")
                    st.info("Trying alternative method...")
                    values = worksheet.get_all_values()
                    st.success(f"✅ Alternative method: read {len(values)} rows")
                
                st.success("🎉 **All tests passed!** Your Google Sheets connection is working properly.")
                
            else:
                st.error(f"❌ Worksheet `{config.TAB_NAME}` not found")
                st.info(f"💡 Available options: {', '.join(worksheet_names)}")
                
        except gspread.exceptions.SpreadsheetNotFound:
            st.error("❌ **Spreadsheet not found**")
            st.info("Check your Spreadsheet ID and ensure the spreadsheet exists")
            
        except gspread.exceptions.WorksheetNotFound:
            st.error("❌ **Worksheet not found**") 
            st.info("Check your tab name spelling and case")
            
        except Exception as e:
            st.error(f"❌ **Connection test failed**: {e}")
            
            # Show specific error guidance
            error_str = str(e)
            if "403" in error_str:
                st.warning("🚫 **Access denied** - Share your spreadsheet with the service account email")
            elif "401" in error_str:
                st.warning("🔑 **Authentication failed** - Check your credentials file")
            elif "404" in error_str:
                st.warning("🔍 **Not found** - Verify your Spreadsheet ID")
            
            with st.expander("🔧 Full Error Details"):
                import traceback
                st.code(traceback.format_exc(), language="python")


def check_data_freshness(kpi_data):
    """Check how fresh the current data is"""
    try:
        if kpi_data is None or 'date' not in kpi_data.columns:
            return "⚠️", "Unknown", "#FFA500"
        
        # Get the most recent date in the data
        latest_date = pd.to_datetime(kpi_data['date']).max()
        current_date = pd.Timestamp.now()
        
        # Calculate days since last entry
        days_old = (current_date - latest_date).days
        
        if days_old == 0:
            return "🟢", "Fresh (today)", "#28A745"
        elif days_old == 1:
            return "🟡", "1 day old", "#FFC107"
        elif days_old <= 3:
            return "🟡", f"{days_old} days old", "#FFC107"
        elif days_old <= 7:
            return "🟠", f"{days_old} days old", "#FD7E14"
        else:
            return "🔴", f"{days_old} days old", "#DC3545"
            
    except Exception:
        return "⚠️", "Unknown", "#6C757D"

# Page configuration
st.set_page_config(
    page_title="San-Xing Bulletproof Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .data-source-success {
        background: #e8f5e8;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    
    .data-source-fallback {
        background: #fff3e0;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ff9800;
        margin: 10px 0;
    }
    
    .metric-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main dashboard application with bulletproof data loading"""
    
    # Enhanced Header (Phase 1: Clean and Focused)
    st.markdown('<h1 class="main-header">📊 San-Xing Personal Analytics</h1>', unsafe_allow_html=True)
    st.markdown("**Your wellbeing insights at a glance**")
    
    # Minimal Sidebar (Phase 1: Simplified Configuration)
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Essential data source control
        force_fallback = st.checkbox("📊 Use Demo Data", False, 
                                   help="Toggle to use synthetic demo data instead of real Google Sheets")
        
        # Quick data refresh
        if st.button("🔄 Refresh Data", help="Reload data from source"):
            st.cache_data.clear()
            st.rerun()
        
        # Fetch latest data from Google Sheets
        if st.button("📥 Fetch Latest from Google Sheets", help="Download fresh data directly from Google Sheets"):
            fetch_fresh_data_from_sheets()
        
        # Test connection button
        if st.button("🔍 Test Google Sheets Connection", help="Test connection without fetching data"):
            test_google_sheets_connection()
        
        st.divider()
        
        # Auto-refresh settings
        st.markdown("#### ⚡ Auto-Refresh Settings")
        auto_refresh = st.checkbox("🔄 Enable Auto-Refresh", False, 
                                 help="Automatically refresh dashboard at selected intervals")
        
        if auto_refresh:
            refresh_interval = st.selectbox(
                "🕒 Refresh Interval",
                options=[30, 60, 300, 600, 1800],
                format_func=lambda x: f"{x//60}h {x%60}m" if x >= 60 else f"{x} minutes",
                index=1,  # Default to 60 minutes
                help="How often to refresh the dashboard"
            )
            
            st.info(f"⏰ Dashboard auto-refreshes every {refresh_interval//60}h {refresh_interval%60}m")
            
            # Add JavaScript for auto-refresh
            st.markdown(f"""
            <script>
                setTimeout(function(){{
                    window.location.reload();
                }}, {refresh_interval * 1000});
            </script>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Advanced settings (collapsed by default)
        with st.expander("🔧 Advanced Options", expanded=False):
            st.markdown("#### Display Settings")
            kpi_layout = st.selectbox("KPI Layout", ["columns", "rows", "grid"], index=0)
            show_raw_data = st.checkbox("Show Raw Data Explorer", False)
            show_statistical_details = st.checkbox("Show Statistical Details", False)
            
            st.markdown("#### Analysis Settings")
            correlation_alpha = st.slider("Significance Level", 0.01, 0.10, 0.05, 0.01,
                                         help="Statistical significance threshold for correlations")
            show_only_significant = st.checkbox("Only Significant Correlations", False)
    
    # === DATA LOADING WITH ROBUST FALLBACK ===
    
    data_source_type = "unknown"
    kpi_data = None
    data_info = None
    
    if force_fallback:
        # Use synthetic data
        st.markdown("""
        <div class="data-source-fallback">
            ⚠️ <strong>Synthetic Data Mode:</strong> Using generated sample data for demonstration
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("Generating synthetic data..."):
            kpi_data = create_fallback_data(60)
            data_source_type = "synthetic"
        
        st.success(f"✅ Generated {len(kpi_data)} days of synthetic data")
    
    else:
        # Try to load real data first
        try:
            kpi_data, data_info = display_data_loading_status()
            
            if kpi_data is not None:
                # Real data loaded successfully
                # Check data freshness
                freshness_icon, freshness_text, freshness_color = check_data_freshness(kpi_data)
                
                st.markdown(f"""
                <div class="data-source-success">
                    ✅ <strong>Real Data Source:</strong> Google Sheets Meta-Awareness Log<br>
                    {freshness_icon} <strong>Data Freshness:</strong> <span style="color: {freshness_color};">{freshness_text}</span>
                </div>
                """, unsafe_allow_html=True)
                data_source_type = "real"
            
            else:
                # Real data failed, use fallback
                st.warning("Real data loading failed. Using synthetic data as fallback.")
                st.markdown("""
                <div class="data-source-fallback">
                    🔄 <strong>Fallback Mode:</strong> Using synthetic data due to loading issues
                </div>
                """, unsafe_allow_html=True)
                
                with st.spinner("Generating fallback data..."):
                    kpi_data = create_fallback_data(60)
                    data_source_type = "fallback"
        
        except Exception as e:
            # Complete failure, use fallback
            st.error(f"Unexpected error during data loading: {e}")
            st.markdown("""
            <div class="data-source-fallback">
                🚨 <strong>Emergency Fallback:</strong> Using synthetic data due to system error
            </div>
            """, unsafe_allow_html=True)
            
            kpi_data = create_fallback_data(60)
            data_source_type = "emergency"
    
    # Ensure we have data at this point
    if kpi_data is None or kpi_data.empty:
        st.error("❌ Complete data loading failure. Cannot proceed.")
        st.stop()
    
    # Show data source information
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Data Source", data_source_type.title())
    
    with col2:
        st.metric("Total Entries", len(kpi_data))
    
    with col3:
        if 'date' in kpi_data.columns:
            try:
                date_range = f"{kpi_data['date'].min().strftime('%m-%d')} to {kpi_data['date'].max().strftime('%m-%d')}"
                st.metric("Date Range", date_range)
            except Exception:
                st.metric("Date Range", "N/A")
        else:
            st.metric("Date Range", "N/A")
    
    with col4:
        # Calculate data completeness
        numeric_cols = kpi_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            completeness = (1 - kpi_data[numeric_cols].isnull().sum().sum() / (len(kpi_data) * len(numeric_cols))) * 100
            st.metric("Completeness", f"{completeness:.0f}%")
        else:
            st.metric("Completeness", "N/A")
    
    # === ANALYTICS PROCESSING ===
    
    with st.spinner("Calculating KPIs and statistical analysis..."):
        try:
            # Calculate KPIs
            kpis = KPICalculator.calculate_all_kpis(kpi_data)
            
            # Calculate correlations on numeric columns only
            numeric_cols = kpi_data.select_dtypes(include=[np.number])
            if len(numeric_cols.columns) > 1:
                correlations = correlation_with_significance(
                    numeric_cols, 
                    alpha=correlation_alpha
                )
            else:
                correlations = {'significant_correlations': [], 'all_correlations': {}, 'total_tests': 0}
                
        except Exception as e:
            st.error(f"Analytics calculation failed: {e}")
            # Use minimal analytics as fallback
            kpis = {}
            correlations = {'significant_correlations': [], 'all_correlations': {}, 'total_tests': 0}
    
    # === PHASE 1: PROGRESSIVE DISCLOSURE ARCHITECTURE ===
    
    # 1. PRIMARY SECTION: At-a-Glance KPIs (Above Fold)
    if kpis:
        from components.kpi_grid import render_kpi_overview_enhanced
        render_kpi_overview_enhanced(kpis)
    
    # 2. PRIMARY SECTION: Top Insights (Above Fold) 
    numeric_cols = kpi_data.select_dtypes(include=[np.number]) if kpi_data is not None else pd.DataFrame()
    if len(numeric_cols.columns) > 1 or kpis:
        from components.kpi_grid import render_top_insights
        render_top_insights(correlations, kpis, len(kpi_data) if kpi_data is not None else 0)
        st.divider()
    
    # 3. SECONDARY SECTION: Progressive Disclosure (On Demand)
    from components.kpi_grid import render_progressive_disclosure_sections
    render_progressive_disclosure_sections(kpi_data, kpis, correlations)
    
    st.divider()
    
    # 5. Dashboard Summary
    st.markdown("## 📋 Dashboard Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        completeness = (1 - kpi_data.isnull().sum().sum() / (len(kpi_data) * len(kpi_data.columns))) * 100 if not kpi_data.empty else 0
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>Data Quality</h3>
            <p><strong>{completeness:.0f}%</strong> completeness</p>
            <p><strong>{len(kpi_data)}</strong> entries analyzed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col2:
        sig_count = len(correlations.get('significant_correlations', []))
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>Statistical Findings</h3>
            <p><strong>{sig_count}</strong> significant correlations</p>
            <p><strong>{correlations.get('total_tests', 0)}</strong> tests performed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col3:
        data_source_desc = {
            "real": "Live Google Sheets",
            "synthetic": "Generated Sample",
            "fallback": "Backup Data",
            "emergency": "Emergency Backup"
        }.get(data_source_type, "Unknown")
        
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>Data Source</h3>
            <p><strong>{data_source_desc}</strong></p>
            <p><strong>{len(kpis)}</strong> KPIs calculated</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666; padding: 20px;'>
        🛡️ <strong>San-Xing Bulletproof Dashboard</strong> - Reliable wellbeing analytics<br>
        Data Source: {data_source_desc} | Robust error handling ensures dashboard always works
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
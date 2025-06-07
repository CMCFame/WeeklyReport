# components/data_diagnostics.py
"""Data persistence diagnostics for the Weekly Report app."""

import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime
from utils.file_ops import diagnose_data_persistence, get_data_directory, ensure_data_directory

def render_data_diagnostics():
    """Render data persistence diagnostics page."""
    st.title("🔍 Data Persistence Diagnostics")
    st.write("Check and troubleshoot data storage issues")
    
    # Run diagnostics
    if st.button("🔄 Run Diagnostics", type="primary"):
        run_full_diagnostics()
    
    # Quick status check
    render_quick_status_check()
    
    # Manual tests
    render_manual_tests()
    
    # Directory browser
    render_directory_browser()

def run_full_diagnostics():
    """Run comprehensive diagnostics."""
    st.subheader("📊 Diagnostic Results")
    
    with st.spinner("Running diagnostics..."):
        diagnosis = diagnose_data_persistence()
    
    # Show overall status
    status = diagnosis.get("status", "unknown")
    if status == "healthy":
        st.success("✅ Data persistence is healthy!")
    elif status == "warning":
        st.warning("⚠️ Data persistence has some issues")
    elif status == "critical":
        st.error("🚨 Critical data persistence issues detected!")
    else:
        st.error("❌ Unable to determine data persistence status")
    
    # Show detailed information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 Directory Information")
        info = diagnosis.get("info", {})
        
        st.write(f"**Working Directory:** `{info.get('working_directory', 'Unknown')}`")
        st.write(f"**Data Directory:** `{info.get('data_directory', 'Unknown')}`")
        st.write(f"**Directory Exists:** {'✅' if info.get('data_directory_exists') else '❌'}")
        st.write(f"**Readable:** {'✅' if info.get('data_directory_readable') else '❌'}")
        st.write(f"**Writable:** {'✅' if info.get('data_directory_writable') else '❌'}")
        st.write(f"**Write Test:** {'✅' if info.get('write_test_passed') else '❌'}")
        
        if 'existing_reports_count' in info:
            st.write(f"**Existing Reports:** {info['existing_reports_count']} files")
        
        if 'free_disk_space_mb' in info:
            st.write(f"**Free Disk Space:** {info['free_disk_space_mb']} MB")
    
    with col2:
        st.subheader("⚠️ Issues Detected")
        issues = diagnosis.get("issues", [])
        
        if not issues:
            st.success("No issues detected!")
        else:
            for issue in issues:
                st.error(f"• {issue}")
        
        st.subheader("💡 Recommendations")
        recommendations = diagnosis.get("recommendations", [])
        
        if recommendations:
            for rec in recommendations:
                st.info(f"• {rec}")
        else:
            st.success("No recommendations needed!")

def render_quick_status_check():
    """Render quick status indicators."""
    st.subheader("⚡ Quick Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        data_dir = get_data_directory()
        dir_exists = os.path.exists(data_dir)
        st.metric("Data Directory", "✅ Exists" if dir_exists else "❌ Missing")
    
    with col2:
        if dir_exists:
            writable = os.access(data_dir, os.W_OK)
            st.metric("Write Access", "✅ Yes" if writable else "❌ No")
        else:
            st.metric("Write Access", "❓ Unknown")
    
    with col3:
        if dir_exists:
            json_files = list(Path(data_dir).glob("*.json"))
            st.metric("Report Files", len(json_files))
        else:
            st.metric("Report Files", "❓ Unknown")
    
    with col4:
        if dir_exists:
            try:
                stat_info = os.statvfs(data_dir)
                free_space_mb = round((stat_info.f_bavail * stat_info.f_frsize) / (1024 * 1024), 1)
                st.metric("Free Space", f"{free_space_mb} MB")
            except:
                st.metric("Free Space", "❓ Unknown")
        else:
            st.metric("Free Space", "❓ Unknown")

def render_manual_tests():
    """Render manual testing interface."""
    st.subheader("🧪 Manual Tests")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Test File Creation**")
        if st.button("Test Write Operation"):
            test_write_operation()
    
    with col2:
        st.write("**Test Report Save**")
        if st.button("Test Report Creation"):
            test_report_creation()
    
    # Repair operations
    st.subheader("🔧 Repair Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Create Data Directory"):
            try:
                if ensure_data_directory():
                    st.success("✅ Data directory created/verified!")
                else:
                    st.error("❌ Failed to create data directory")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with col2:
        if st.button("Fix Permissions"):
            fix_permissions()
    
    with col3:
        if st.button("Clean Temp Files"):
            clean_temp_files()

def test_write_operation():
    """Test basic write operation."""
    try:
        data_dir = get_data_directory()
        test_file = os.path.join(data_dir, f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        with open(test_file, 'w') as f:
            f.write(f"Test file created at {datetime.now()}")
        
        # Verify file exists
        if os.path.exists(test_file):
            file_size = os.path.getsize(test_file)
            st.success(f"✅ Write test successful! File: {test_file} ({file_size} bytes)")
            
            # Clean up
            os.remove(test_file)
            st.info("🧹 Test file cleaned up")
        else:
            st.error("❌ File was not created")
            
    except Exception as e:
        st.error(f"❌ Write test failed: {e}")

def test_report_creation():
    """Test creating a sample report."""
    try:
        from utils.file_ops import save_report
        
        # Create sample report data
        test_report = {
            'name': 'Test User',
            'reporting_week': f'Test-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'current_activities': [
                {
                    'description': 'Test activity',
                    'project': 'Test Project',
                    'priority': 'Medium',
                    'status': 'In Progress',
                    'progress': 50
                }
            ],
            'accomplishments': ['Test accomplishment'],
            'followups': ['Test followup'],
            'nextsteps': ['Test next step'],
            'status': 'test'
        }
        
        # Try to save
        report_id = save_report(test_report)
        
        if report_id:
            st.success(f"✅ Test report created successfully! ID: {report_id}")
            
            # Offer to delete test report
            if st.button("🗑️ Delete Test Report"):
                from utils.file_ops import delete_report
                if delete_report(report_id):
                    st.success("✅ Test report deleted!")
                else:
                    st.error("❌ Failed to delete test report")
        else:
            st.error("❌ Failed to create test report")
            
    except Exception as e:
        st.error(f"❌ Report creation test failed: {e}")

def fix_permissions():
    """Attempt to fix directory permissions."""
    try:
        data_dir = get_data_directory()
        
        if not os.path.exists(data_dir):
            st.warning("Data directory doesn't exist. Creating it first...")
            ensure_data_directory()
        
        # Try to fix permissions (Unix/Linux only)
        try:
            os.chmod(data_dir, 0o755)
            st.success("✅ Directory permissions updated!")
        except:
            st.warning("⚠️ Cannot change permissions automatically. Manual intervention may be required.")
            
        # Show current permissions
        try:
            stat_info = os.stat(data_dir)
            permissions = oct(stat_info.st_mode)[-3:]
            st.info(f"📋 Current permissions: {permissions}")
        except:
            pass
            
    except Exception as e:
        st.error(f"❌ Permission fix failed: {e}")

def clean_temp_files():
    """Clean temporary and backup files."""
    try:
        data_dir = get_data_directory()
        
        if not os.path.exists(data_dir):
            st.info("Data directory doesn't exist - nothing to clean")
            return
        
        # Find temp files
        temp_patterns = ['*.tmp', '*.backup', '*.deleted', '.write_test', '.persistence_test']
        cleaned_files = []
        
        for pattern in temp_patterns:
            for file_path in Path(data_dir).glob(pattern):
                try:
                    os.remove(file_path)
                    cleaned_files.append(str(file_path))
                except Exception as e:
                    st.warning(f"Could not remove {file_path}: {e}")
        
        if cleaned_files:
            st.success(f"✅ Cleaned {len(cleaned_files)} temporary files")
            with st.expander("View cleaned files"):
                for file_path in cleaned_files:
                    st.text(file_path)
        else:
            st.info("No temporary files found to clean")
            
    except Exception as e:
        st.error(f"❌ Cleanup failed: {e}")

def render_directory_browser():
    """Render directory browser for data folder."""
    st.subheader("📂 Directory Browser")
    
    data_dir = get_data_directory()
    
    if not os.path.exists(data_dir):
        st.warning(f"Data directory does not exist: {data_dir}")
        return
    
    try:
        # List all files
        files = list(Path(data_dir).iterdir())
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Sort by modification time
        
        st.write(f"**Directory:** `{data_dir}`")
        st.write(f"**Total files:** {len(files)}")
        
        if not files:
            st.info("Directory is empty")
            return
        
        # File list
        file_data = []
        for file_path in files:
            try:
                stat_info = file_path.stat()
                file_data.append({
                    'Name': file_path.name,
                    'Size (bytes)': stat_info.st_size,
                    'Modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'Type': 'Directory' if file_path.is_dir() else 'File'
                })
            except Exception as e:
                file_data.append({
                    'Name': file_path.name,
                    'Size (bytes)': 'Error',
                    'Modified': 'Error',
                    'Type': 'Error'
                })
        
        # Display as table
        import pandas as pd
        df = pd.DataFrame(file_data)
        st.dataframe(df, use_container_width=True)
        
        # File inspection
        st.subheader("🔍 File Inspector")
        
        json_files = [f['Name'] for f in file_data if f['Name'].endswith('.json')]
        if json_files:
            selected_file = st.selectbox("Select a file to inspect:", [''] + json_files)
            
            if selected_file:
                inspect_file(os.path.join(data_dir, selected_file))
        
    except Exception as e:
        st.error(f"Error browsing directory: {e}")

def inspect_file(file_path):
    """Inspect a specific file."""
    try:
        st.write(f"**Inspecting:** `{file_path}`")
        
        # File info
        stat_info = os.stat(file_path)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Size", f"{stat_info.st_size} bytes")
        with col2:
            st.metric("Modified", datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d'))
        with col3:
            readable = os.access(file_path, os.R_OK)
            st.metric("Readable", "✅ Yes" if readable else "❌ No")
        
        # Try to read as JSON
        if file_path.endswith('.json'):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                st.success("✅ Valid JSON file")
                
                # Show basic info
                if isinstance(data, dict):
                    st.write("**Report Information:**")
                    st.write(f"- ID: {data.get('id', 'Not found')}")
                    st.write(f"- Name: {data.get('name', 'Not found')}")
                    st.write(f"- Week: {data.get('reporting_week', 'Not found')}")
                    st.write(f"- Timestamp: {data.get('timestamp', 'Not found')}")
                    st.write(f"- Status: {data.get('status', 'Not found')}")
                    
                    # Count sections
                    activities = len(data.get('current_activities', []))
                    accomplishments = len([a for a in data.get('accomplishments', []) if a])
                    st.write(f"- Activities: {activities}")
                    st.write(f"- Accomplishments: {accomplishments}")
                
                # Show raw content
                with st.expander("View raw JSON"):
                    st.json(data)
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {e}")
                
                # Show raw content for debugging
                with st.expander("View raw content"):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    st.text_area("File content", content, height=200)
            
    except Exception as e:
        st.error(f"Error inspecting file: {e}")

# Add this to your main app navigation
def add_diagnostics_to_sidebar():
    """Add diagnostics link to sidebar for admin users."""
    if st.session_state.get("user_info", {}).get("role") == "admin":
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 Admin Tools")
        
        if st.sidebar.button("🔍 Data Diagnostics"):
            st.session_state.nav_page = "Data Diagnostics"
            st.session_state.nav_section = "admin"
            st.rerun()
# utils/file_ops.py
"""File operations for saving and loading reports with improved error handling."""

import json
import uuid
import os
import traceback
import stat
from pathlib import Path
import streamlit as st
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_data_directory():
    """Get the absolute path to the data directory."""
    # Use absolute path to avoid working directory issues
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_root = os.path.dirname(current_dir)  # Go up one level from utils/
    data_dir = os.path.join(app_root, "data", "reports")
    return data_dir

def ensure_data_directory():
    """Ensure the data directory exists with proper error handling."""
    try:
        data_dir = get_data_directory()
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        
        # Check if directory is writable
        test_file = os.path.join(data_dir, ".write_test")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"Data directory verified: {data_dir}")
            return True
        except Exception as e:
            logger.error(f"Data directory not writable: {data_dir}, Error: {e}")
            st.error(f"❌ Cannot write to data directory: {data_dir}")
            st.error(f"Permission error: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to create data directory: {e}")
        st.error(f"❌ Failed to create data directory: {e}")
        return False

def save_report(report_data):
    """Save report data to a JSON file with comprehensive error handling.
    
    Args:
        report_data (dict): Report data to save
        
    Returns:
        str: Report ID if successful, None if failed
    """
    try:
        # Ensure data directory exists and is writable
        if not ensure_data_directory():
            st.error("❌ Cannot save report: Data directory is not accessible")
            return None
        
        # Get or generate report ID
        report_id = report_data.get('id', str(uuid.uuid4()))
        report_data['id'] = report_id
        
        # Add user_id from session state if authenticated
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            report_data['user_id'] = st.session_state.user_info.get("id")
            
        # Check if this is an update to an existing report
        is_update = st.session_state.get('editing_report', False)
        
        # Handle timestamp based on whether it's an update or a new report
        if is_update and 'original_timestamp' in st.session_state:
            # Preserve the original timestamp
            report_data['timestamp'] = st.session_state.original_timestamp
            # Add last_updated field
            report_data['last_updated'] = datetime.now().isoformat()
        else:
            # New report, set the timestamp
            report_data['timestamp'] = datetime.now().isoformat()
        
        # Validate report data
        if not validate_report_data_before_save(report_data):
            st.error("❌ Cannot save report: Invalid data structure")
            return None
        
        # Get full file path
        data_dir = get_data_directory()
        file_path = os.path.join(data_dir, f"{report_id}.json")
        
        # Create backup if file exists
        if os.path.exists(file_path):
            backup_path = os.path.join(data_dir, f"{report_id}.json.backup")
            try:
                with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
                logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")
        
        # Save the report
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Verify the file was written correctly
        if not os.path.exists(file_path):
            st.error(f"❌ File was not created: {file_path}")
            return None
        
        # Verify file content
        try:
            with open(file_path, 'r') as f:
                saved_data = json.load(f)
            if saved_data.get('id') != report_id:
                st.error("❌ File verification failed: Data corruption detected")
                return None
        except Exception as e:
            st.error(f"❌ File verification failed: {e}")
            return None
        
        # Log successful save
        file_size = os.path.getsize(file_path)
        logger.info(f"Report saved successfully: {file_path} ({file_size} bytes)")
        
        # Show success message with file info
        st.success(f"✅ Report saved successfully!")
        st.info(f"📁 Saved to: {file_path}")
        st.info(f"📊 File size: {file_size} bytes")
        
        return report_id
        
    except PermissionError as e:
        error_msg = f"Permission denied when saving report: {e}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        st.error("💡 This might be a server permission issue. Contact your administrator.")
        return None
        
    except OSError as e:
        error_msg = f"Operating system error when saving report: {e}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        st.error("💡 This might be a disk space or file system issue.")
        return None
        
    except Exception as e:
        error_msg = f"Unexpected error saving report: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        st.error(f"❌ {error_msg}")
        
        # Show debugging information
        with st.expander("🔍 Debug Information"):
            st.text(f"Report ID: {report_data.get('id', 'None')}")
            st.text(f"User ID: {report_data.get('user_id', 'None')}")
            st.text(f"Data Directory: {get_data_directory()}")
            st.text(f"Working Directory: {os.getcwd()}")
            st.text(f"Error Details: {traceback.format_exc()}")
        
        return None

def validate_report_data_before_save(report_data):
    """Validate report data before saving."""
    try:
        # Check if it's a dictionary
        if not isinstance(report_data, dict):
            st.error("Report data is not a dictionary")
            return False
        
        # Check required fields
        required_fields = ['id', 'timestamp']
        for field in required_fields:
            if field not in report_data:
                st.error(f"Missing required field: {field}")
                return False
        
        # Check data types
        if 'current_activities' in report_data:
            if not isinstance(report_data['current_activities'], list):
                st.error("current_activities must be a list")
                return False
        
        if 'accomplishments' in report_data:
            if not isinstance(report_data['accomplishments'], list):
                st.error("accomplishments must be a list")
                return False
        
        # Try to serialize to JSON
        try:
            json.dumps(report_data)
        except (TypeError, ValueError) as e:
            st.error(f"Report data is not JSON serializable: {e}")
            return False
        
        return True
        
    except Exception as e:
        st.error(f"Validation error: {e}")
        return False

def load_report(report_id):
    """Load report data from a JSON file with improved error handling.
    
    Args:
        report_id (str): ID of the report to load
        
    Returns:
        dict: Report data or None if not found
    """
    try:
        data_dir = get_data_directory()
        file_path = os.path.join(data_dir, f"{report_id}.json")
        
        if not os.path.exists(file_path):
            st.error(f"Report file not found: {file_path}")
            return None
        
        with open(file_path, 'r') as f:
            report_data = json.load(f)
            
        # Check if user has access to this report
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            user_id = st.session_state.user_info.get("id")
            user_role = st.session_state.user_info.get("role")
            report_user_id = report_data.get("user_id")
            
            # Admin can access all reports
            if user_role == "admin":
                return report_data
            
            # Managers can access their team members' reports
            if user_role == "manager":
                return report_data
            
            # Normal users can only access their own reports
            if report_user_id and report_user_id != user_id:
                st.error("You don't have permission to access this report.")
                return None
                
        return report_data
        
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON in report file {report_id}: {e}")
        return None
    except Exception as e:
        st.error(f"Error loading report {report_id}: {str(e)}")
        logger.error(f"Error loading report: {traceback.format_exc()}")
        return None

def get_all_reports(filter_by_user=True):
    """Get a list of all saved reports with improved error handling.
    
    Args:
        filter_by_user (bool): If True, only return reports for the current user
    
    Returns:
        list: List of report data dictionaries, sorted by timestamp (newest first)
    """
    try:
        data_dir = get_data_directory()
        
        if not os.path.exists(data_dir):
            logger.warning(f"Data directory does not exist: {data_dir}")
            return []
        
        reports = []
        
        # Get current user ID if authenticated
        current_user_id = None
        user_role = None
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            current_user_id = st.session_state.user_info.get("id")
            user_role = st.session_state.user_info.get("role")
        
        # Scan for JSON files
        json_files = list(Path(data_dir).glob("*.json"))
        logger.info(f"Found {len(json_files)} report files in {data_dir}")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    report = json.load(f)
                    
                    # Validate the report has minimum required fields
                    if not isinstance(report, dict) or 'timestamp' not in report:
                        logger.warning(f"Skipping invalid report format in {file_path}")
                        continue
                    
                    # Filter by user if requested and not admin/manager
                    if filter_by_user and current_user_id and user_role != "admin":
                        report_user_id = report.get("user_id")
                        
                        # Managers can see all reports
                        if user_role == "manager":
                            reports.append(report)
                        # Team members can only see their own reports
                        elif report_user_id and report_user_id == current_user_id:
                            reports.append(report)
                    else:
                        reports.append(report)
                        
            except Exception as e:
                logger.warning(f"Error loading report {file_path}: {str(e)}")
        
        logger.info(f"Successfully loaded {len(reports)} reports")
        return sorted(reports, key=lambda x: x.get('timestamp', ''), reverse=True)
        
    except Exception as e:
        error_msg = f"Error retrieving reports: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        st.error(f"❌ {error_msg}")
        return []

def delete_report(report_id):
    """Delete a report file with improved error handling.
    
    Args:
        report_id (str): ID of the report to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        data_dir = get_data_directory()
        file_path = os.path.join(data_dir, f"{report_id}.json")
        
        # Check if user has permission to delete this report
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            try:
                with open(file_path, 'r') as f:
                    report_data = json.load(f)
                
                user_id = st.session_state.user_info.get("id")
                user_role = st.session_state.user_info.get("role")
                report_user_id = report_data.get("user_id")
                
                # Only the report owner, managers, and admins can delete
                if user_role not in ["admin", "manager"] and report_user_id != user_id:
                    st.error("You don't have permission to delete this report.")
                    return False
            except:
                # If we can't open the file, proceed with deletion attempt
                pass
        
        if not os.path.exists(file_path):
            st.error(f"Report file not found: {file_path}")
            return False
        
        # Create backup before deletion
        backup_path = os.path.join(data_dir, f"{report_id}.json.deleted")
        try:
            with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            logger.info(f"Created deletion backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Could not create deletion backup: {e}")
        
        # Delete the file
        os.remove(file_path)
        logger.info(f"Report deleted: {file_path}")
        return True
        
    except Exception as e:
        error_msg = f"Error deleting report {report_id}: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return False

def diagnose_data_persistence():
    """Diagnose data persistence issues and return diagnostic information."""
    diagnosis = {
        "status": "unknown",
        "issues": [],
        "info": {},
        "recommendations": []
    }
    
    try:
        # Check working directory
        current_dir = os.getcwd()
        diagnosis["info"]["working_directory"] = current_dir
        
        # Check data directory
        data_dir = get_data_directory()
        diagnosis["info"]["data_directory"] = data_dir
        
        # Check if data directory exists
        if os.path.exists(data_dir):
            diagnosis["info"]["data_directory_exists"] = True
            
            # Check permissions
            try:
                # Test read permission
                readable = os.access(data_dir, os.R_OK)
                diagnosis["info"]["data_directory_readable"] = readable
                if not readable:
                    diagnosis["issues"].append("Data directory is not readable")
                
                # Test write permission
                writable = os.access(data_dir, os.W_OK)
                diagnosis["info"]["data_directory_writable"] = writable
                if not writable:
                    diagnosis["issues"].append("Data directory is not writable")
                
                # Count existing files
                json_files = list(Path(data_dir).glob("*.json"))
                diagnosis["info"]["existing_reports_count"] = len(json_files)
                
                # Test write capability
                test_file = os.path.join(data_dir, ".persistence_test")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    diagnosis["info"]["write_test_passed"] = True
                except Exception as e:
                    diagnosis["info"]["write_test_passed"] = False
                    diagnosis["issues"].append(f"Write test failed: {e}")
                
            except Exception as e:
                diagnosis["issues"].append(f"Permission check failed: {e}")
        else:
            diagnosis["info"]["data_directory_exists"] = False
            diagnosis["issues"].append("Data directory does not exist")
            
            # Try to create it
            try:
                Path(data_dir).mkdir(parents=True, exist_ok=True)
                diagnosis["info"]["directory_creation_attempted"] = True
                if os.path.exists(data_dir):
                    diagnosis["info"]["directory_creation_successful"] = True
                else:
                    diagnosis["issues"].append("Failed to create data directory")
            except Exception as e:
                diagnosis["issues"].append(f"Could not create data directory: {e}")
        
        # Check disk space
        try:
            stat_info = os.statvfs(data_dir if os.path.exists(data_dir) else current_dir)
            free_space = stat_info.f_bavail * stat_info.f_frsize
            diagnosis["info"]["free_disk_space_bytes"] = free_space
            diagnosis["info"]["free_disk_space_mb"] = round(free_space / (1024 * 1024), 2)
            
            if free_space < 10 * 1024 * 1024:  # Less than 10 MB
                diagnosis["issues"].append("Low disk space (less than 10 MB)")
        except:
            diagnosis["info"]["disk_space_check"] = "Not available"
        
        # Overall status
        if not diagnosis["issues"]:
            diagnosis["status"] = "healthy"
        elif any("not writable" in issue for issue in diagnosis["issues"]):
            diagnosis["status"] = "critical"
            diagnosis["recommendations"].append("Fix directory permissions")
        else:
            diagnosis["status"] = "warning"
        
        # Generate recommendations
        if "Data directory does not exist" in diagnosis["issues"]:
            diagnosis["recommendations"].append("Create the data directory manually")
        
        if "not writable" in str(diagnosis["issues"]):
            diagnosis["recommendations"].append("Check and fix file permissions")
            diagnosis["recommendations"].append("Ensure the web server has write access")
        
        if "Low disk space" in str(diagnosis["issues"]):
            diagnosis["recommendations"].append("Free up disk space")
        
    except Exception as e:
        diagnosis["status"] = "error"
        diagnosis["issues"].append(f"Diagnostic failed: {e}")
    
    return diagnosis

def export_report_as_pdf(report_data):
    """Export report data as PDF - placeholder for existing functionality."""
    st.info("PDF export functionality is available in the PDF export module.")
    return False

def validate_report_data(report_data):
    """Validate report data structure - enhanced version."""
    errors = []
    
    if not isinstance(report_data, dict):
        return False, ["Report data is not a dictionary"]
    
    # Check required fields
    for field in ['timestamp']:  # Reduced required fields
        if field not in report_data:
            errors.append(f"Missing required field: {field}")
    
    # Validate lists
    for list_field in ['current_activities', 'upcoming_activities', 'accomplishments', 'followups', 'nextsteps']:
        if list_field in report_data and not isinstance(report_data[list_field], list):
            errors.append(f"Field {list_field} should be a list")
    
    # Validate nested structures
    if 'current_activities' in report_data:
        for i, activity in enumerate(report_data['current_activities']):
            if not isinstance(activity, dict):
                errors.append(f"Current activity at index {i} is not a dictionary")
    
    if 'upcoming_activities' in report_data:
        for i, activity in enumerate(report_data['upcoming_activities']):
            if not isinstance(activity, dict):
                errors.append(f"Upcoming activity at index {i} is not a dictionary")
    
    # Check JSON serializability
    try:
        json.dumps(report_data)
    except (TypeError, ValueError) as e:
        errors.append(f"Data is not JSON serializable: {e}")
    
    return len(errors) == 0, errors
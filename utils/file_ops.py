# utils/file_ops.py
"""File operations for saving and loading reports."""

import json
import uuid
import os
import traceback
from pathlib import Path
import streamlit as st

def ensure_data_directory():
    """Ensure the data directory exists."""
    Path("data/reports").mkdir(parents=True, exist_ok=True)

def save_report(report_data):
    """Save report data to a JSON file.
    
    Args:
        report_data (dict): Report data to save
        
    Returns:
        str: Report ID
    """
    try:
        ensure_data_directory()
        report_id = report_data.get('id', str(uuid.uuid4()))
        report_data['id'] = report_id
        
        # Add user_id from session state if authenticated
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            report_data['user_id'] = st.session_state.user_info.get("id")
            
        with open(f"data/reports/{report_id}.json", 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return report_id
    except Exception as e:
        st.error(f"Error saving report: {str(e)}")
        st.error(traceback.format_exc())
        return None

def load_report(report_id):
    """Load report data from a JSON file.
    
    Args:
        report_id (str): ID of the report to load
        
    Returns:
        dict: Report data or None if not found
    """
    try:
        with open(f"data/reports/{report_id}.json", 'r') as f:
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
                # For now, assume managers can see all reports
                # In a more sophisticated system, we'd check if the report belongs to their team
                return report_data
            
            # Normal users can only access their own reports
            if report_user_id and report_user_id != user_id:
                st.error("You don't have permission to access this report.")
                return None
                
        return report_data
    except FileNotFoundError:
        st.error(f"Report with ID {report_id} not found.")
        return None
    except json.JSONDecodeError:
        st.error(f"Invalid JSON in report file {report_id}.")
        return None
    except Exception as e:
        st.error(f"Error loading report {report_id}: {str(e)}")
        st.error(traceback.format_exc())
        return None

def get_all_reports(filter_by_user=True):
    """Get a list of all saved reports.
    
    Args:
        filter_by_user (bool): If True, only return reports for the current user
    
    Returns:
        list: List of report data dictionaries, sorted by timestamp (newest first)
    """
    try:
        ensure_data_directory()
        reports = []
        
        # Get current user ID if authenticated
        current_user_id = None
        user_role = None
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            current_user_id = st.session_state.user_info.get("id")
            user_role = st.session_state.user_info.get("role")
        
        for file_path in Path("data/reports").glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    report = json.load(f)
                    
                    # Validate the report has minimum required fields
                    if not isinstance(report, dict) or 'timestamp' not in report:
                        st.warning(f"Skipping invalid report format in {file_path}")
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
                st.warning(f"Error loading report {file_path}: {str(e)}")
        
        return sorted(reports, key=lambda x: x.get('timestamp', ''), reverse=True)
    except Exception as e:
        st.error(f"Error retrieving reports: {str(e)}")
        st.error(traceback.format_exc())
        return []

def delete_report(report_id):
    """Delete a report file.
    
    Args:
        report_id (str): ID of the report to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        # Check if user has permission to delete this report
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            try:
                with open(f"data/reports/{report_id}.json", 'r') as f:
                    report_data = json.load(f)
                
                user_id = st.session_state.user_info.get("id")
                user_role = st.session_state.user_info.get("role")
                report_user_id = report_data.get("user_id")
                
                # Only the report owner, managers, and admins can delete
                if user_role not in ["admin", "manager"] and report_user_id != user_id:
                    st.error("You don't have permission to delete this report.")
                    return False
            except:
                # If we can't open the file, just try to delete it
                pass
        
        os.remove(f"data/reports/{report_id}.json")
        return True
    except FileNotFoundError:
        st.error(f"Report with ID {report_id} not found.")
        return False
    except Exception as e:
        st.error(f"Error deleting report {report_id}: {str(e)}")
        st.error(traceback.format_exc())
        return False

def export_report_as_pdf(report_data):
    """Export report data as PDF.
    
    This is a placeholder function. Actual PDF export would require additional libraries.
    
    Args:
        report_data (dict): Report data to export
        
    Returns:
        bool: Always returns False in this placeholder
    """
    # This would be implemented with a PDF generation library
    st.info("PDF export functionality would be implemented here.")
    return False

def validate_report_data(report_data):
    """Validate report data structure.
    
    Args:
        report_data (dict): Report data to validate
        
    Returns:
        tuple: (is_valid, errors) - Boolean indicating if valid and list of error messages
    """
    errors = []
    
    if not isinstance(report_data, dict):
        return False, ["Report data is not a dictionary"]
    
    # Check required fields
    for field in ['name', 'reporting_week', 'timestamp']:
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
    
    return len(errors) == 0, errors
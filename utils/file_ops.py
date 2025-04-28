# utils/file_ops.py
"""File operations for saving and loading reports."""

import json
import uuid
import os
from pathlib import Path
import streamlit as st

def ensure_data_directory():
    """Ensure the data directory exists."""
    Path("data").mkdir(exist_ok=True)

def save_report(report_data):
    """Save report data to a JSON file.
    
    Args:
        report_data (dict): Report data to save
        
    Returns:
        str: Report ID
    """
    ensure_data_directory()
    report_id = report_data.get('id', str(uuid.uuid4()))
    report_data['id'] = report_id
    
    with open(f"data/{report_id}.json", 'w') as f:
        json.dump(report_data, f, indent=2)
    
    return report_id

def load_report(report_id):
    """Load report data from a JSON file.
    
    Args:
        report_id (str): ID of the report to load
        
    Returns:
        dict: Report data or None if not found
    """
    try:
        with open(f"data/{report_id}.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Report with ID {report_id} not found.")
        return None

def get_all_reports():
    """Get a list of all saved reports.
    
    Returns:
        list: List of report data dictionaries, sorted by timestamp (newest first)
    """
    ensure_data_directory()
    reports = []
    for file_path in Path("data").glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                report = json.load(f)
                reports.append(report)
        except Exception as e:
            st.error(f"Error loading report {file_path}: {e}")
    
    return sorted(reports, key=lambda x: x.get('timestamp', ''), reverse=True)

def delete_report(report_id):
    """Delete a report file.
    
    Args:
        report_id (str): ID of the report to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        os.remove(f"data/{report_id}.json")
        return True
    except FileNotFoundError:
        st.error(f"Report with ID {report_id} not found.")
        return False
    except Exception as e:
        st.error(f"Error deleting report {report_id}: {e}")
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
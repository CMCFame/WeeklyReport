# components/report_import.py
"""Report import component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime
import io
from utils import file_ops, session

def render_report_import():
    """Render the report import interface for admins."""
    st.title("Import Reports")
    st.write("Upload reports from external systems in CSV or JSON format.")
    
    # Template downloads
    st.subheader("Download Templates")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV template
        template_df = create_csv_template()
        csv = template_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV Template",
            data=csv,
            file_name="report_import_template.csv",
            mime="text/csv"
        )
    
    with col2:
        # JSON template
        template_json = create_json_template()
        json_str = json.dumps(template_json, indent=2)
        st.download_button(
            label="📥 Download JSON Template",
            data=json_str,
            file_name="report_import_template.json",
            mime="application/json"
        )
    
    # Import type selection
    st.subheader("Import Reports")
    import_type = st.radio("Choose import format:", ["CSV", "JSON"])
    
    if import_type == "CSV":
        render_csv_import()
    else:
        render_json_import()

def render_csv_import():
    """Render CSV import interface."""
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="csv_report_upload")
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Validate columns
            required_columns = ['name', 'reporting_week', 'current_activities', 
                               'upcoming_activities', 'accomplishments', 'followups', 'nextsteps']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Error: Your CSV is missing these required columns: {', '.join(missing_columns)}")
                return
            
            # Show preview
            st.subheader("Preview Import Data")
            st.dataframe(df.head())
            
            # Count of reports to be imported
            st.info(f"Ready to import {len(df)} reports")
            
            # Import button
            if st.button("Import Reports from CSV"):
                results = import_reports_from_csv(df)
                
                # Show results
                st.subheader("Import Results")
                success_count = sum(1 for r in results if r['status'] == 'success')
                st.success(f"Successfully imported {success_count} out of {len(df)} reports")
                
                # Show details in expander
                with st.expander("View Detailed Results"):
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df)
        
        except Exception as e:
            st.error(f"Error processing CSV file: {str(e)}")

def render_json_import():
    """Render JSON import interface."""
    uploaded_file = st.file_uploader("Choose a JSON file", type="json", key="json_report_upload")
    
    if uploaded_file is not None:
        try:
            # Read JSON
            content = uploaded_file.read()
            json_data = json.loads(content)
            
            # Determine if it's a list of reports or a single report
            if isinstance(json_data, list):
                reports = json_data
            else:
                reports = [json_data]
            
            # Show preview
            st.subheader("Preview Import Data")
            preview_df = pd.json_normalize(reports, max_level=1)
            st.dataframe(preview_df.head())
            
            # Count of reports to be imported
            st.info(f"Ready to import {len(reports)} reports")
            
            # Import button
            if st.button("Import Reports from JSON"):
                results = import_reports_from_json(reports)
                
                # Show results
                st.subheader("Import Results")
                success_count = sum(1 for r in results if r['status'] == 'success')
                st.success(f"Successfully imported {success_count} out of {len(reports)} reports")
                
                # Show details in expander
                with st.expander("View Detailed Results"):
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df)
        
        except Exception as e:
            st.error(f"Error processing JSON file: {str(e)}")

def import_reports_from_csv(df):
    """Import reports from a CSV dataframe.
    
    Args:
        df (pandas.DataFrame): Dataframe containing report data
        
    Returns:
        list: List of dictionaries with import results
    """
    results = []
    
    # Process each row
    for i, row in df.iterrows():
        try:
            # Convert row to dict
            row_dict = row.to_dict()
            
            # Parse list fields (stored as strings in CSV)
            list_fields = ['current_activities', 'upcoming_activities', 'accomplishments', 'followups', 'nextsteps']
            for field in list_fields:
                if field in row_dict and isinstance(row_dict[field], str):
                    try:
                        row_dict[field] = json.loads(row_dict[field].replace("'", "\""))
                    except:
                        # If JSON parsing fails, split by comma
                        row_dict[field] = [item.strip() for item in row_dict[field].split(',') if item.strip()]
            
            # Add required fields
            row_dict['id'] = str(uuid.uuid4())
            if 'timestamp' not in row_dict or not row_dict['timestamp']:
                row_dict['timestamp'] = datetime.now().isoformat()
                
            # Handle user association
            if 'user_id' not in row_dict or not row_dict['user_id']:
                # Assign to current user if admin is importing
                if st.session_state.get("user_info"):
                    row_dict['user_id'] = st.session_state.user_info.get("id")
            
            # Save report
            report_id = file_ops.save_report(row_dict)
            
            if report_id:
                results.append({
                    'name': row_dict.get('name', 'Unknown'),
                    'reporting_week': row_dict.get('reporting_week', 'Unknown'),
                    'status': 'success',
                    'message': 'Report created successfully',
                    'id': report_id
                })
            else:
                results.append({
                    'name': row_dict.get('name', 'Unknown'),
                    'reporting_week': row_dict.get('reporting_week', 'Unknown'),
                    'status': 'error',
                    'message': 'Failed to save report'
                })
        
        except Exception as e:
            results.append({
                'name': row.get('name', f'Row {i+1}'),
                'reporting_week': row.get('reporting_week', 'Unknown'),
                'status': 'error',
                'message': str(e)
            })
    
    return results

def import_reports_from_json(reports):
    """Import reports from JSON data.
    
    Args:
        reports (list): List of report dictionaries
        
    Returns:
        list: List of dictionaries with import results
    """
    results = []
    
    # Process each report
    for i, report in enumerate(reports):
        try:
            # Add required fields
            if 'id' not in report or not report['id']:
                report['id'] = str(uuid.uuid4())
                
            if 'timestamp' not in report or not report['timestamp']:
                report['timestamp'] = datetime.now().isoformat()
                
            # Handle user association
            if 'user_id' not in report or not report['user_id']:
                # Assign to current user if admin is importing
                if st.session_state.get("user_info"):
                    report['user_id'] = st.session_state.user_info.get("id")
            
            # Save report
            report_id = file_ops.save_report(report)
            
            if report_id:
                results.append({
                    'name': report.get('name', 'Unknown'),
                    'reporting_week': report.get('reporting_week', 'Unknown'),
                    'status': 'success',
                    'message': 'Report created successfully',
                    'id': report_id
                })
            else:
                results.append({
                    'name': report.get('name', 'Unknown'),
                    'reporting_week': report.get('reporting_week', 'Unknown'),
                    'status': 'error',
                    'message': 'Failed to save report'
                })
        
        except Exception as e:
            results.append({
                'name': report.get('name', f'Report {i+1}'),
                'reporting_week': report.get('reporting_week', 'Unknown'),
                'status': 'error',
                'message': str(e)
            })
    
    return results

def create_csv_template():
    """Create a template dataframe for CSV imports."""
    # Sample activities
    current_activities = json.dumps([
        {
            "project": "Project A",
            "milestone": "Phase 1",
            "priority": "High",
            "status": "In Progress",
            "customer": "Internal",
            "billable": "No",
            "deadline": "2023-12-31",
            "progress": 75,
            "description": "Implementing feature X"
        }
    ])
    
    upcoming_activities = json.dumps([
        {
            "project": "Project B",
            "milestone": "Planning",
            "priority": "Medium",
            "expected_start": "2024-01-15",
            "description": "Begin work on new module"
        }
    ])
    
    # Sample lists
    accomplishments = json.dumps(["Completed task 1", "Fixed bug in module Y"])
    followups = json.dumps(["Follow up with team about issue Z"])
    nextsteps = json.dumps(["Begin planning for Q1 projects", "Schedule training session"])
    
    # Create template
    template_df = pd.DataFrame({
        'name': ['John Doe', 'Jane Smith'],
        'reporting_week': ['W48 2023', 'W49 2023'],
        'current_activities': [current_activities, current_activities],
        'upcoming_activities': [upcoming_activities, upcoming_activities],
        'accomplishments': [accomplishments, accomplishments],
        'followups': [followups, followups],
        'nextsteps': [nextsteps, nextsteps],
        'challenges': ['Challenge description here', ''],
        'slow_projects': ['Description of slow projects', ''],
        'user_id': ['', ''],  # Leave blank to assign to current user
        'status': ['submitted', 'draft']
    })
    
    return template_df

def create_json_template():
    """Create a template object for JSON imports."""
    template = [
        {
            "name": "John Doe",
            "reporting_week": "W48 2023",
            "current_activities": [
                {
                    "project": "Project A",
                    "milestone": "Phase 1",
                    "priority": "High",
                    "status": "In Progress",
                    "customer": "Internal",
                    "billable": "No",
                    "deadline": "2023-12-31",
                    "progress": 75,
                    "description": "Implementing feature X"
                }
            ],
            "upcoming_activities": [
                {
                    "project": "Project B",
                    "milestone": "Planning",
                    "priority": "Medium",
                    "expected_start": "2024-01-15",
                    "description": "Begin work on new module"
                }
            ],
            "accomplishments": [
                "Completed task 1",
                "Fixed bug in module Y"
            ],
            "followups": [
                "Follow up with team about issue Z"
            ],
            "nextsteps": [
                "Begin planning for Q1 projects",
                "Schedule training session"
            ],
            "challenges": "Challenge description here",
            "slow_projects": "Description of slow projects",
            "user_id": "",  # Leave blank to assign to current user
            "status": "submitted"
        }
    ]
    
    return template
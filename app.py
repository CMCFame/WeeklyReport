# app.py

"""
Weekly Activity Report Application

A Streamlit application for tracking and reporting weekly work activities,
designed to standardize interaction recording between managers and team members.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
from pathlib import Path

# Import utility modules
from utils.session import (
    init_session_state,
    reset_form,
    calculate_completion_percentage,
    collect_form_data,
    load_report_data
)
from utils.file_ops import save_report
from utils.user_auth import create_admin_if_needed
from utils.csv_utils import ensure_project_data_file
from utils.team_utils import ensure_teams_directory
from utils.meeting_utils import ensure_meetings_directory

# Import component modules
from components.user_info import render_user_info
from components.enhanced_current_activities import render_enhanced_current_activities
from components.section_selector import render_section_selector
from components.upcoming_activities import render_upcoming_activities
from components.simple_accomplishments import render_simple_accomplishments
from components.simple_action_items import render_simple_action_items
from components.optional_sections import (
    render_optional_section_toggles,
    render_all_optional_sections
)
from components.past_reports import render_past_reports
from components.auth import (
    check_authentication, 
    render_user_profile,
    render_admin_user_management
)
from components.user_import import render_user_import
from components.report_import import render_report_import
from components.objectives_import import render_objectives_import
from components.navigation import render_navigation, get_current_page
from components.report_templates import render_report_templates
from components.placeholder import (
    render_system_settings
)
from components.weekly_report_analytics import render_weekly_report_analytics
from components.team_structure import render_team_structure
from components.one_on_one_meetings import render_one_on_one_meetings
from components.advanced_analytics import render_advanced_analytics
from components.batch_export import render_batch_export
from components.team_objectives import render_team_objectives
from components.goal_dashboard import render_goal_dashboard
from components.okr_management import render_okr_management
# ADD THIS LINE:
from components.scoping_process import render_scoping_process

# --- CALLBACK TO CLEAR FORM & RERUN ---
def clear_form_callback():
    """Callback to reset all fields and rerun the app."""
    reset_form()
    st.rerun()

# Set page configuration
st.set_page_config(
    page_title="Weekly Activity Report",
    page_icon="📋",
    layout="wide"
)

def handle_csv_upload():
    """Handle upload of project data CSV file."""
    uploaded_file = st.file_uploader("Upload Project Data CSV", type="csv")
    
    if uploaded_file is not None:
        # Display file info
        file_details = {"Filename": uploaded_file.name, "Size": uploaded_file.size}
        st.write(file_details)
        
        try:
            # Read uploaded CSV to validate format
            df = pd.read_csv(uploaded_file)
            
            # Check required columns
            required_columns = ["Project", "Milestone: Milestone Name", "Timecard: Owner Name"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Upload failed! CSV file is missing required columns: {', '.join(missing_columns)}")
                return
            
            # Save the file to the data directory
            Path("data").mkdir(exist_ok=True)
            temp_path = f"data/temp_{uploaded_file.name}"
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Move to final location
            os.rename(temp_path, "data/project_data.csv")
            
            # Display success message with row counts
            st.success(f"✅ Project data uploaded successfully! Imported {len(df)} rows with {len(df['Project'].unique())} unique projects.")
            
            # Show preview of the data
            with st.expander("Preview Imported Data"):
                st.dataframe(df.head(10))
                
        except Exception as e:
            st.error(f"Error processing CSV file: {str(e)}")

def main():
    """Main application function."""
    # Initialize session state
    init_session_state()
    
    # Handle cancellation request
    if st.session_state.get('cancel_editing', False):
        # Reset form safely at the beginning of the app run
        reset_form()
        st.session_state.editing_report = False
        # Reset the flag
        st.session_state.cancel_editing = False
        # Go back to past reports
        st.session_state.nav_page = "Past Reports"
        st.session_state.nav_section = "reporting"
        st.rerun()
    
    # Ensure required directories exist
    ensure_project_data_file()
    ensure_teams_directory() 
    ensure_meetings_directory()
    
    # Create admin user if no users exist
    create_admin_if_needed()
    
    # Check authentication (shows login page if not authenticated)
    if not check_authentication():
        return
    
    # Display user info in sidebar
    if st.session_state.get("user_info"):
        user_role = st.session_state.user_info.get("role", "team_member")
        user_name = st.session_state.user_info.get("full_name", "User")
        
        st.sidebar.write(f"**Logged in as:** {user_name}")
        st.sidebar.write(f"**Role:** {user_role.capitalize()}")
        
        # Render navigation menu
        render_navigation()
        
        # Get current page
        current_page = get_current_page()
        
        # Render the selected page
        render_selected_page(current_page)
    else:
        st.error("Session error. Please log out and log in again.")

def render_selected_page(page_name):
    """Render the page based on the navigation selection.
    
    Args:
        page_name (str): Name of the page to render
    """
    # Reporting section
    if page_name == "Weekly Report":
        render_weekly_report_page()
    elif page_name == "Past Reports":
        st.title("Past Reports")
        render_past_reports()
    elif page_name == "Report Templates":
        render_report_templates()
    elif page_name == "Report Analytics":
        render_weekly_report_analytics()
    elif page_name == "Advanced Analytics":
        render_advanced_analytics()
    elif page_name == "Batch Export":
        render_batch_export()

    # Scoping & Sales section
    elif page_name == "Scoping Process":
        render_scoping_process()
    
    # Goals & Tracking section
    elif page_name == "Team Objectives":
        render_team_objectives()
    elif page_name == "Goal Dashboard":
        render_goal_dashboard()
    elif page_name == "OKR Management":
        render_okr_management()
    elif page_name == "Import Objectives":
        render_objectives_import()
    
    # Team Management section
    elif page_name == "User Management":
        render_admin_user_management()
    elif page_name == "Team Structure":
        render_team_structure()
    elif page_name == "1:1 Meetings":
        render_one_on_one_meetings()
    
    # Administration section
    elif page_name == "User Profile":
        render_user_profile()
    elif page_name == "Project Data":
        render_project_data_page()
    elif page_name == "Import Users":
        render_user_import()
    elif page_name == "Import Reports":
        render_report_import()
    elif page_name == "System Settings":
        render_system_settings()
    
    # Fallback
    else:
        st.error(f"Page '{page_name}' not found.")

def render_project_data_page():
    """Render the project data management page."""
    st.title("Project Data Management")
    st.write("Upload and manage project data for reporting.")
    
    # Handle CSV upload
    handle_csv_upload()
    
    # Show current project data if available
    try:
        if os.path.exists("data/project_data.csv"):
            st.subheader("Current Project Data")
            df = pd.read_csv("data/project_data.csv")
            
            # Show counts
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Unique Projects", len(df["Project"].unique()))
            with col3:
                st.metric("Unique Team Members", len(df["Timecard: Owner Name"].unique()))
            
            # Display the data
            with st.expander("View All Project Data"):
                st.dataframe(df)
            
            # Option to show projects per user
            st.subheader("Projects by Team Member")
            
            # Get unique team members
            team_members = sorted(df["Timecard: Owner Name"].unique().tolist())
            selected_member = st.selectbox("Select Team Member", ["All Team Members"] + team_members)
            
            if selected_member == "All Team Members":
                # Show counts for all team members
                member_counts = df.groupby("Timecard: Owner Name")["Project"].nunique().reset_index()
                member_counts.columns = ["Team Member", "Project Count"]
                st.dataframe(member_counts)
            else:
                # Filter projects for selected team member
                member_df = df[df["Timecard: Owner Name"] == selected_member]
                member_projects = member_df[["Project", "Milestone: Milestone Name"]].drop_duplicates()
                st.dataframe(member_projects)
                
        else:
            st.info("No project data found. Please upload a CSV file with project data.")
            
    except Exception as e:
        st.error(f"Error displaying project data: {str(e)}")

def render_weekly_report_page():
    """Render the main weekly report form with modular sections."""
    # Check if we're in edit mode
    is_editing = st.session_state.get('editing_report', False)
    
    # Header
    if is_editing:
        st.title('📝 Edit Weekly Activity Report')
        st.write('Update your previous report')
    else:
        st.title('📋 Weekly Activity Report')
        st.write('Use the sections below to document your week\'s work')

    # User Information Section (always visible)
    render_user_info()
    
    # Section Selector - compact multiselect at the top
    render_section_selector()
    
    # Progress bar
    completion_percentage = calculate_completion_percentage()
    st.progress(completion_percentage / 100)
    
    # Render each section based on toggle state
    if st.session_state.get('show_current_activities', True):
        render_enhanced_current_activities()
    
    if st.session_state.get('show_upcoming_activities', False):
        render_upcoming_activities()
    
    if st.session_state.get('show_accomplishments', False):
        render_simple_accomplishments()
    
    if st.session_state.get('show_action_items', False):
        render_simple_action_items()

    # Optional Sections Content
    render_all_optional_sections()

    # Form Actions (modified for edit mode)
    render_form_actions(is_editing)

def render_form_actions(is_editing=False):
    """Render the form action buttons.
    
    Args:
        is_editing (bool): Whether we're in edit mode
    """
    st.divider()
    
    if is_editing:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button('Save Changes', use_container_width=True, type="primary"):
                save_current_report('submitted', is_update=True)

        with col2:
            # Cancel editing button
            if st.button('Cancel Editing', use_container_width=True):
                # Mark for cancellation instead of immediate reset
                # This avoids modifying session state after widgets render
                st.session_state.cancel_editing = True
                st.rerun()

        with col3:
            # Use an on_click callback rather than inline mutation
            st.button(
                'Reset Changes',
                use_container_width=True,
                on_click=clear_form_callback
            )
    else:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button('Save Draft', use_container_width=True):
                save_current_report('draft')

        with col2:
            # Use an on_click callback rather than inline mutation
            st.button(
                'Clear Form',
                use_container_width=True,
                on_click=clear_form_callback
            )

        with col3:
            if st.button('Submit Report', use_container_width=True, type="primary"):
                save_current_report('submitted')

def save_current_report(status, is_update=False):
    """Save the current report.

    Args:
        status (str): Status of the report ('draft' or 'submitted')
        is_update (bool): Whether this is an update to an existing report
    """
    # Validate required fields for submission
    if status == 'submitted' and not st.session_state.name:
        st.error('Please enter your name before submitting')
        return

    if status == 'submitted' and not st.session_state.reporting_week:
        st.error('Please enter the reporting week before submitting')
        return

    # Collect and save form data
    report_data = collect_form_data()
    report_data['status'] = status
    
    # If editing, preserve the original timestamp when it was created
    if is_update and 'original_timestamp' in st.session_state:
        report_data['timestamp'] = st.session_state.original_timestamp
        # Add last_updated timestamp
        from datetime import datetime
        report_data['last_updated'] = datetime.now().isoformat()
    
    report_id = save_report(report_data)
    st.session_state.report_id = report_id

    # Show success message
    if is_update:
        st.success('Report updated successfully!')
        # Clear editing flag
        st.session_state.editing_report = False
        # Go back to past reports
        st.session_state.nav_page = "Past Reports"
        st.session_state.nav_section = "reporting"
        st.rerun()
    elif status == 'draft':
        st.success('Draft saved successfully!')
    else:
        st.success('Report submitted successfully!')

# Run the app
if __name__ == '__main__':
    main()
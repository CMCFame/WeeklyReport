# app.py
"""
Weekly Activity Report Application

A Streamlit application for tracking and reporting weekly work activities,
designed to standardize interaction recording between managers and team members.
"""

import streamlit as st
from datetime import datetime

# Import utility modules
from utils.session import (
    init_session_state,
    reset_form,
    calculate_completion_percentage,
    collect_form_data
)
from utils.file_ops import save_report
from utils.user_auth import create_admin_if_needed

# Import component modules
from components.user_info import render_user_info
from components.current_activities import render_current_activities
from components.upcoming_activities import render_upcoming_activities
from components.accomplishments import render_accomplishments
from components.action_items import render_action_items
from components.optional_sections import (
    render_optional_section_toggles,
    render_all_optional_sections
)
from components.past_reports import render_past_reports
from components.auth import (
    check_authentication, 
    render_user_profile,
    render_admin_user_management,
    render_forgot_password_page,
    render_reset_password_page
)

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

def main():
    """Main application function."""
    # Initialize session state
    init_session_state()
    
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
        
        # Navigation in sidebar
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Go to",
            ["Weekly Report", "Past Reports", "User Profile"] + 
            (["User Management"] if user_role == "admin" else [])
        )
        
        # Render selected page
        if page == "Weekly Report":
            render_weekly_report_page()
        elif page == "Past Reports":
            st.title("Past Reports")
            render_past_reports()
        elif page == "User Profile":
            render_user_profile()
        elif page == "User Management" and user_role == "admin":
            render_admin_user_management()
    else:
        st.error("Session error. Please log out and log in again.")

def render_weekly_report_page():
    """Render the main weekly report form."""
    # Header
    st.title('📋 Weekly Activity Report')
    st.write('Quickly document your week\'s work in under 5 minutes')

    # Progress bar
    completion_percentage = calculate_completion_percentage()
    st.progress(completion_percentage / 100)
    
    # Pre-fill name from user profile if empty
    if not st.session_state.get("name") and st.session_state.get("user_info"):
        st.session_state.name = st.session_state.user_info.get("full_name", "")

    # User Information Section
    render_user_info()

    # Current Activities Section
    render_current_activities()

    # Upcoming Activities Section
    render_upcoming_activities()

    # Last Week's Accomplishments Section
    render_accomplishments()

    # Action Items Section
    render_action_items()

    # Optional Sections Toggle
    render_optional_section_toggles()

    # Optional Sections Content
    render_all_optional_sections()

    # Form Actions
    render_form_actions()

def render_form_actions():
    """Render the form action buttons."""
    st.divider()
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

def save_current_report(status):
    """Save the current report.

    Args:
        status (str): Status of the report ('draft' or 'submitted')
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
    report_id = save_report(report_data)
    st.session_state.report_id = report_id

    # Show success message
    if status == 'draft':
        st.success('Draft saved successfully!')
    else:
        st.success('Report submitted successfully!')

# Run the app
if __name__ == '__main__':
    main()
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

    # Header
    st.title('📋 Weekly Activity Report')
    st.write('Quickly document your week\'s work in under 5 minutes')

    # Progress bar
    completion_percentage = calculate_completion_percentage()
    st.progress(completion_percentage / 100)

    # Tabs for main form vs past reports
    tab1, tab2 = st.tabs(["Report Form", "Past Reports"])

    with tab1:
        render_report_form()

    with tab2:
        render_past_reports()

def render_report_form():
    """Render the main report form."""
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

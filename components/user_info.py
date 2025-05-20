# components/user_info.py
"""User information component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
from utils import file_ops, session

def render_user_info():
    """Render the user information section with date selector for reporting week."""
    st.header("Your Information")

    # 1) Allow loading a past report (filtered by the authenticated user)
    render_previous_reports_dropdown()

    # 2) Render Name and Reporting Week fields
    col1, col2 = st.columns(2)

    with col1:
        # If user is authenticated, use their name but allow edits
        default_name = ""
        if st.session_state.get("user_info"):
            default_name = st.session_state.user_info.get("full_name", "")
            
        # Only set if name isn't already defined (to avoid overwriting)
        if not st.session_state.get("name") and default_name:
            st.session_state.name = default_name
        
        # Use unique key for the name input
        name_value = st.text_input(
            "Name",
            value=st.session_state.get("name", ""),
            key="modular_report_name_input",  # Completely new key
            help="Enter your full name"
        )
        
        # Manually update the session state
        st.session_state.name = name_value

    with col2:
        # Use a date picker to select any date within the reporting week
        # Get default date from session state if available
        default_date = None
        if st.session_state.get("reporting_week_date"):
            try:
                default_date = st.session_state.reporting_week_date
            except:
                default_date = datetime.now().date()
        else:
            default_date = datetime.now().date()
            
        # Use unique key for the date input
        week_date = st.date_input(
            "Reporting Week (select any date within that week)",
            value=default_date,
            key="modular_report_week_date",  # Completely new key
            help="Pick a date; the app will infer the ISO week number"
        )
        
        # Store the selected date in session state
        st.session_state.reporting_week_date = week_date
        
        # Derive ISO week number and year
        year, week_num, _ = week_date.isocalendar()
        week_str = f"W{week_num} {year}"
        
        # Store as the reporting_week used elsewhere
        st.session_state.reporting_week = week_str
        
        # Show the formatted week to the user
        st.caption(f"Reporting Week: {week_str}")

def render_previous_reports_dropdown():
    """Render a dropdown of past reports and load on change."""
    try:
        # Get reports for current user only
        reports = file_ops.get_all_reports(filter_by_user=True)
        if not reports:
            return

        # Cache for callback access
        st.session_state._cached_reports = reports

        # Build labels, with an empty placeholder first
        labels = [""] + [
            f"{r.get('name','Anonymous')} – "
            f"{r.get('reporting_week','Unknown')} "
            f"({r.get('timestamp','')[:10]})"
            for r in reports
        ]

        # Create a unique key for the report selection index
        if 'modular_report_selection_index' not in st.session_state:
            st.session_state.modular_report_selection_index = 0
            
        # Selectbox with a completely new, unique key
        selected_index = st.selectbox(
            "Load Previous Report",
            options=list(range(len(labels))),
            format_func=lambda i: labels[i],
            key="modular_report_selection_dropdown",  # Completely new key
            index=st.session_state.modular_report_selection_index,
            help="Choose a past report to preload the form"
        )
        
        # Store the selected index
        st.session_state.modular_report_selection_index = selected_index
        
        # Handle selection change
        if selected_index > 0:  # If not the empty option
            # Load the selected report
            idx = selected_index - 1
            report_data = reports[idx].copy()
            session.load_report_data(report_data)
            st.rerun()

    except Exception as e:
        st.error(f"Error loading reports: {e}")
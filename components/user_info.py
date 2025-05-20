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
        
        # Instead of using key parameter, we'll use a completely different approach
        # We'll generate a unique widget label that includes a timestamp
        unique_timestamp = str(datetime.now().timestamp()).replace(".", "_")
        widget_label = f"Name##{unique_timestamp}"
        
        name_value = st.text_input(
            widget_label,  # Use unique label instead of key
            value=st.session_state.get("name", ""),
            help="Enter your full name",
            label_visibility="collapsed"  # Hide the unique timestamp label
        )
        
        # Display a visible label manually
        st.caption("Name")
        
        # Manually update the session state
        st.session_state.name = name_value

    with col2:
        # Similar approach for date input
        unique_timestamp2 = str(datetime.now().timestamp() + 1).replace(".", "_")
        date_label = f"Reporting Week##{unique_timestamp2}"
        
        # Get default date from session state if available
        default_date = None
        if st.session_state.get("reporting_week_date"):
            try:
                default_date = st.session_state.reporting_week_date
            except:
                default_date = datetime.now().date()
        else:
            default_date = datetime.now().date()
            
        # Use unique label for the date input
        week_date = st.date_input(
            date_label,
            value=default_date,
            help="Pick a date; the app will infer the ISO week number",
            label_visibility="collapsed"
        )
        
        # Display a visible label manually
        st.caption("Reporting Week (select any date within that week)")
        
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

        # Cache reports in a global variable instead of session state
        global cached_reports
        cached_reports = reports

        # Build labels, with an empty placeholder first
        labels = [""] + [
            f"{r.get('name','Anonymous')} – "
            f"{r.get('reporting_week','Unknown')} "
            f"({r.get('timestamp','')[:10]})"
            for r in reports
        ]

        # Create a unique label for the selectbox
        unique_timestamp = str(datetime.now().timestamp() + 2).replace(".", "_")
        select_label = f"Load Previous Report##{unique_timestamp}"
        
        # Selectbox with a unique label
        selected_index = st.selectbox(
            select_label,
            options=list(range(len(labels))),
            format_func=lambda i: labels[i],
            index=0,
            help="Choose a past report to preload the form",
            label_visibility="collapsed"
        )
        
        # Display a visible label manually
        st.caption("Load Previous Report")
        
        # Handle selection change
        if selected_index > 0:  # If not the empty option
            # Load the selected report
            idx = selected_index - 1
            report_data = reports[idx].copy()
            session.load_report_data(report_data)
            st.rerun()

    except Exception as e:
        st.error(f"Error loading reports: {e}")
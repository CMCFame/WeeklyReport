# components/user_info.py - fixed version

import streamlit as st
from datetime import datetime
from utils import file_ops, session
import time

def render_user_info():
    """Render the user information section with date selector for reporting week."""
    st.header("Your Information")

    # Generate a unique timestamp for this component
    timestamp_base = int(time.time() * 1000)

    # 1) Allow loading a past report (filtered by the authenticated user)
    render_previous_reports_dropdown(timestamp_base)

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
        
        # Use a unique key for the name input
        name_value = st.text_input(
            "Name",
            value=st.session_state.get("name", ""),
            help="Enter your full name",
            key=f"name_input_{timestamp_base}"
        )
        
        # Manually update the session state
        st.session_state.name = name_value

    with col2:
        # Get default date from session state if available
        default_date = None
        if st.session_state.get("reporting_week_date"):
            try:
                default_date = st.session_state.reporting_week_date
            except:
                default_date = datetime.now().date()
        else:
            default_date = datetime.now().date()
            
        # Use a unique key for the date input
        week_date = st.date_input(
            "Reporting Week",
            value=default_date,
            help="Pick a date; the app will infer the ISO week number",
            key=f"reporting_week_date_{timestamp_base}"
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

def render_previous_reports_dropdown(timestamp_base):
    """Render a dropdown of past reports and load on change."""
    try:
        # Get reports for current user only
        reports = file_ops.get_all_reports(filter_by_user=True)
        if not reports:
            return

        # Build labels, with an empty placeholder first
        labels = [""] + [
            f"{r.get('name','Anonymous')} – "
            f"{r.get('reporting_week','Unknown')} "
            f"({r.get('timestamp','')[:10]})"
            for r in reports
        ]

        # Create a unique key for the selectbox
        select_key = f"load_previous_report_{timestamp_base}"
        
        # Selectbox with a unique key
        st.write("Load Previous Report:")
        selected_index = st.selectbox(
            "Choose a past report to preload the form",
            options=list(range(len(labels))),
            format_func=lambda i: labels[i],
            index=0,
            key=select_key
        )
        
        # Handle selection change
        if selected_index > 0:  # If not the empty option
            # Load the selected report
            idx = selected_index - 1
            report_data = reports[idx].copy()
            session.load_report_data(report_data)
            st.rerun()

    except Exception as e:
        st.error(f"Error loading reports: {e}")
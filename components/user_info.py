# components/user_info.py
"""User information component for the Weekly Report app."""

import streamlit as st
from utils import file_ops, session

def _on_report_select():
    """
    Callback triggered by the selectbox.
    Loads the selected report into session_state, then reruns,
    so subsequent widgets pick up the new values.
    """
    idx = st.session_state.selected_report_idx - 1
    if idx >= 0:
        reports = st.session_state._cached_reports
        report_data = reports[idx].copy()
        session.load_report_data(report_data)
        st.rerun()


def render_user_info():
    """Render the user information section with date selector for reporting week."""
    st.header("Your Information")

    # 1) First, allow loading a past report
    render_previous_reports_dropdown()

    # 2) Then render Name and Reporting Week fields
    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            "Name",
            key="name",
            help="Enter your full name"
        )

    with col2:
        # Use a date picker to select any date within the reporting week
        week_date = st.date_input(
            "Reporting Week (select any date within that week)",
            key="reporting_week_date",
            help="Pick a date; the app will infer the ISO week number"
        )
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
        reports = file_ops.get_all_reports()
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

        # Selectbox over integer indices
        st.selectbox(
            "Load Previous Report",
            options=list(range(len(labels))),
            format_func=lambda i: labels[i],
            key="selected_report_idx",
            help="Choose a past report to preload the form",
            on_change=_on_report_select
        )

    except Exception as e:
        st.error(f"Error loading reports: {e}")

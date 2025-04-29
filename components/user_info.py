# components/user_info.py
"""User information component for the Weekly Report app."""

import streamlit as st
from utils import file_ops, session

def _load_cached_report():
    """Callback: load the report selected in `selected_report_idx`."""
    # selected_report_idx is an integer: 0 means “none”
    idx = st.session_state.selected_report_idx - 1
    if idx >= 0:
        # Retrieve the cached list
        reports = st.session_state._cached_reports
        # Copy to avoid mutating the original
        report_data = reports[idx].copy()
        session.load_report_data(report_data)
        st.success('Report loaded successfully!')
        # Now restart so text_input widgets pick up the new state
        st.rerun()

def render_user_info():
    """Render the user information section."""
    st.header('Your Information')
    col1, col2 = st.columns(2)

    with col1:
        # The text_input shows whatever is already in session_state.name
        st.text_input(
            'Name',
            key='name',
            help='Enter your full name'
        )

    with col2:
        # The text_input shows whatever is already in session_state.reporting_week
        st.text_input(
            'Reporting Week (e.g., W17 2025)',
            key='reporting_week',
            help="Enter the reporting week (e.g., 'W17 2025', 'Apr 22-26')"
        )

    render_previous_reports_dropdown()


def render_previous_reports_dropdown():
    """Render a dropdown of past reports and load on change."""
    try:
        reports = file_ops.get_all_reports()
        if not reports:
            return

        # Cache the list so the callback can access it
        st.session_state._cached_reports = reports

        # Build display labels; index 0 is an empty choice
        labels = [""] + [
            f"{r.get('name','Anonymous')} - "
            f"{r.get('reporting_week','Unknown')} "
            f"({r.get('timestamp','')[:10]})"
            for r in reports
        ]

        # Create a selectbox over the range of indices
        st.selectbox(
            'Load Previous Report',
            options=list(range(len(labels))),
            format_func=lambda i: labels[i],
            key='selected_report_idx',
            help='Select a past report to load into the form',
            on_change=_load_cached_report
        )

    except Exception as e:
        st.error(f"Error loading reports: {e}")

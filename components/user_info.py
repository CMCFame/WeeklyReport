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
    """Render the user information section."""
    st.header("Your Information")

    # 1) Load dropdown first, so loading happens before the text inputs below
    render_previous_reports_dropdown()

    # 2) Now render Name / Reporting Week inputs, 
    #    which will pick up whatever is in st.session_state
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(
            "Name",
            key="name",
            help="Enter your full name"
        )
    with col2:
        st.text_input(
            "Reporting Week (e.g., W17 2025)",
            key="reporting_week",
            help="Enter the reporting week in any format (e.g., 'W17 2025', 'Apr 22-26')"
        )


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

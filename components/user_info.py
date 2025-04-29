# components/user_info.py
"""User information component for the Weekly Report app."""

import streamlit as st
from utils import file_ops, session

def render_user_info():
    """Render the user information section."""
    st.header('Your Information')
    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            'Name',
            key='name',
            help='Enter your full name'
        )

    with col2:
        st.text_input(
            'Reporting Week (e.g., W17 2025)',
            key='reporting_week',
            help="Enter the reporting week in any format (e.g., 'Week 17 2025', 'W17', 'Apr 22-26')"
        )

    # Previous Reports Dropdown
    render_previous_reports_dropdown()


def render_previous_reports_dropdown():
    """Render dropdown to load previous reports immediately on select."""
    try:
        reports = file_ops.get_all_reports()
        if not reports:
            return

        # Build the list of options, with an empty placeholder first
        labels = [
            "",
            *[
                f"{r.get('name','Anonymous')} - "
                f"{r.get('reporting_week','Unknown')} "
                f"({r.get('timestamp','')[:10]})"
                for r in reports
            ]
        ]

        selected = st.selectbox(
            'Load Previous Report',
            options=labels,
            key='selected_report',
            help='Select a past report to load into the form'
        )

        if selected:
            # Compute index in reports list (subtract the initial empty entry)
            idx = labels.index(selected) - 1
            report_data = reports[idx].copy()
            session.load_report_data(report_data)
            st.success('Report loaded successfully!')
            st.experimental_rerun()

    except Exception as e:
        st.error(f"Error loading reports: {e}")

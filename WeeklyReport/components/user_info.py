# components/user_info.py
"""User information component for the Weekly Report app."""

import streamlit as st
from utils import file_ops, session

def render_user_info():
    """Render the user information section.
    
    This includes:
    - Name input
    - Reporting week input
    - Load previous report dropdown
    """
    st.header('Your Information')
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input('Name', key='name', 
                     help="Enter your full name")
    
    with col2:
        st.text_input('Reporting Week (e.g., W17 2025)', key='reporting_week',
                     help="Enter the reporting week in any format (e.g., 'Week 17 2025', 'W17', 'Apr 22-26')")
    
    # Previous Reports Dropdown
    render_previous_reports_dropdown()

def render_previous_reports_dropdown():
    """Render dropdown to load previous reports."""
    reports = file_ops.get_all_reports()
    
    if reports:
        # Create a dictionary mapping display names to report indices
        report_options = {f"{r.get('name', 'Anonymous')} - {r.get('reporting_week', 'Unknown')} ({r.get('timestamp', '')[:10]})": i 
                         for i, r in enumerate(reports)}
        # Add empty option at the top
        report_options[""] = -1
        
        selected_report = st.selectbox(
            'Load Previous Report', 
            options=list(report_options.keys()), 
            index=len(report_options)-1,
            help="Select a previous report to load as a starting point"
        )
        
        if selected_report and report_options[selected_report] >= 0:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button('Load Selected Report', use_container_width=True):
                    selected_index = report_options[selected_report]
                    session.load_report_data(reports[selected_index])
                    st.success('Report loaded successfully!')
                    st.rerun()
            
            with col2:
                if st.button('Use as Template', use_container_width=True, 
                            help="Load the report but create a new copy when saving"):
                    selected_index = report_options[selected_report]
                    report_data = reports[selected_index].copy()
                    # Clear the ID to ensure it's saved as a new report
                    report_data.pop('id', None)
                    session.load_report_data(report_data)
                    st.success('Report loaded as template!')
                    st.rerun()
# components/report_templates.py
"""Report templates component for the Weekly Report app."""

import streamlit as st
import json
import os
from datetime import datetime
from utils import session, file_ops
from pathlib import Path

def render_report_templates():
    """Render the report templates page focused on using past reports as templates."""
    st.title("Report Templates")
    st.write("Use your past reports as templates to streamline the reporting process.")
    
    # Get all past reports
    reports = file_ops.get_all_reports(filter_by_user=True)
    
    if not reports:
        st.info("You don't have any past reports yet. Create your first report to get started!")
        
        # Provide a button to go to the report creation page
        if st.button("Create My First Report", type="primary"):
            st.session_state.nav_page = "Weekly Report"
            st.session_state.nav_section = "reporting"
            st.rerun()
        return
    
    # Filter out empty or draft reports that might not be good templates
    valid_reports = [report for report in reports if 
                    report.get('status', '') == 'submitted' and 
                    (report.get('current_activities', []) or 
                     report.get('upcoming_activities', []) or 
                     report.get('accomplishments', []))]
    
    if not valid_reports:
        st.warning("You have reports, but none are complete enough to use as templates. Complete and submit a report first.")
        return
    
    # Organize reports by reporting period
    reports_by_period = {}
    for report in valid_reports:
        period = report.get('reporting_week', 'Unknown')
        if period not in reports_by_period:
            reports_by_period[period] = []
        reports_by_period[period].append(report)
    
    # Display reports by period
    st.subheader("Select a Past Report to Use as Template")
    
    for period, period_reports in sorted(reports_by_period.items(), reverse=True):
        with st.expander(f"Period: {period} ({len(period_reports)} reports)"):
            # Display each report in this period
            for i, report in enumerate(period_reports):
                report_date = report.get('timestamp', '')[:10] if report.get('timestamp') else 'Unknown date'
                
                st.markdown(f"### Report from {report_date}")
                
                # Show a summary of the report
                if report.get('current_activities'):
                    st.write(f"**Current Activities:** {len(report.get('current_activities'))} activities")
                    # Show the first activity title
                    if report['current_activities']:
                        st.write(f"- {report['current_activities'][0].get('description', '')[:50]}...")
                
                if report.get('upcoming_activities'):
                    st.write(f"**Upcoming Activities:** {len(report.get('upcoming_activities'))} planned")
                
                if report.get('accomplishments'):
                    st.write(f"**Accomplishments:** {len(report.get('accomplishments'))} items")
                    # Show the first accomplishment
                    if report['accomplishments']:
                        st.write(f"- {report['accomplishments'][0][:50]}...")
                
                # Action buttons
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Status:** {report.get('status', 'Unknown').capitalize()}")
                
                with col2:
                    if st.button("Use as Template", key=f"use_report_{i}_{period}", use_container_width=True):
                        # Use this report as a template
                        use_report_as_template(report)
                        
                        # Display success and redirect
                        st.success("Report loaded as template! Redirecting to Weekly Report...")
                        st.session_state.nav_page = "Weekly Report"
                        st.session_state.nav_section = "reporting"
                        st.rerun()
                
                # Put a divider between reports
                if i < len(period_reports) - 1:
                    st.divider()

def use_report_as_template(report):
    """Load a past report as a template for a new report.
    
    Args:
        report (dict): Report data to use as template
    """
    try:
        # Reset the form first
        session.reset_form()
        
        # Pre-fill basic info
        st.session_state.name = report.get('name', '')
        
        # Current activities
        if report.get('current_activities'):
            # Deep copy to avoid modifying the original
            st.session_state.current_activities = []
            for activity in report.get('current_activities', []):
                # Create a copy of the activity
                new_activity = activity.copy()
                # Reset progress to show it's a new report
                new_activity['progress'] = 50  # Set to mid-point as default
                st.session_state.current_activities.append(new_activity)
        
        # Upcoming activities
        if report.get('upcoming_activities'):
            # Deep copy to avoid modifying the original
            st.session_state.upcoming_activities = []
            for activity in report.get('upcoming_activities', []):
                st.session_state.upcoming_activities.append(activity.copy())
        
        # Accomplishments - empty by default since these will be new
        st.session_state.accomplishments = [""]
        
        # Action items
        st.session_state.followups = [""]
        
        # Copy next steps from previous report to followups in new report
        if report.get('nextsteps'):
            st.session_state.followups = [step for step in report.get('nextsteps') if step]
        
        # Start with empty next steps
        st.session_state.nextsteps = [""]
        
        # Optional sections - enable and copy content
        for section in session.OPTIONAL_SECTIONS:
            key = section['key']
            content_key = section['content_key']
            
            # Enable the section if it had content in the original report
            if content_key in report and report[content_key]:
                st.session_state[key] = True
                st.session_state[content_key] = report[content_key]
            else:
                st.session_state[key] = False
                st.session_state[content_key] = ""
        
        # This is a new report, so clear the ID
        st.session_state.report_id = None
        
    except Exception as e:
        st.error(f"Error using report as template: {str(e)}")
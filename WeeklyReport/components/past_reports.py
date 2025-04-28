# components/past_reports.py
"""Past reports component for the Weekly Report app."""

import streamlit as st
from utils import file_ops, session

def render_past_reports():
    """Render the past reports view.
    
    Displays all saved reports with options to view details,
    load them as templates, or delete them.
    """
    st.header('Past Reports')
    reports = file_ops.get_all_reports()
    
    if not reports:
        st.info('No past reports found.')
        return
    
    # Optionally add search and filters here if needed
    
    # Display reports
    for i, report in enumerate(reports):
        with st.expander(f"{report.get('name', 'Anonymous')} - {report.get('reporting_week', 'Unknown')} ({report.get('timestamp', '')[:10]})"):
            render_report_details(report, i)

def render_report_details(report, index):
    """Render the details of a specific report.
    
    Args:
        report (dict): Report data to display
        index (int): Report index for unique keys
    """
    # Basic info
    st.write(f"**Name:** {report.get('name', 'Anonymous')}")
    st.write(f"**Reporting Week:** {report.get('reporting_week', 'Unknown')}")
    st.write(f"**Submitted:** {report.get('timestamp', '')[:19].replace('T', ' ')}")
    
    # Current Activities
    if report.get('current_activities'):
        st.subheader('Current Activities')
        for activity in report['current_activities']:
            st.markdown(f"- **{activity.get('description', '')}** "
                        f"(Priority: {activity.get('priority')}, "
                        f"Status: {activity.get('status')}, "
                        f"Progress: {activity.get('progress')}%)")
    
    # Upcoming Activities
    if report.get('upcoming_activities'):
        st.subheader('Upcoming Activities')
        for activity in report['upcoming_activities']:
            st.markdown(f"- **{activity.get('description', '')}** "
                        f"(Priority: {activity.get('priority')}, "
                        f"Expected Start: {activity.get('expected_start', 'Not specified')})")
    
    # Accomplishments
    if report.get('accomplishments'):
        st.subheader('Last Week\'s Accomplishments')
        for accomplishment in report['accomplishments']:
            st.markdown(f"- {accomplishment}")
    
    # Action Items
    if report.get('followups'):
        st.subheader('Follow-ups')
        for followup in report['followups']:
            st.markdown(f"- {followup}")
    
    if report.get('nextsteps'):
        st.subheader('Next Steps')
        for nextstep in report['nextsteps']:
            st.markdown(f"- {nextstep}")
    
    # Optional sections
    render_optional_report_sections(report)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button('Use as Template', key=f"template_{index}"):
            # Create a copy without the ID to ensure it's saved as a new report
            report_copy = report.copy()
            report_copy.pop('id', None)
            session.load_report_data(report_copy)
            st.success('Report loaded as template!')
            st.rerun()
    
    with col2:
        if st.button('Export as PDF', key=f"export_{index}"):
            file_ops.export_report_as_pdf(report)
    
    with col3:
        if st.button('Delete Report', key=f"delete_{index}"):
            if file_ops.delete_report(report.get('id')):
                st.success('Report deleted successfully!')
                st.rerun()

def render_optional_report_sections(report):
    """Render optional sections of a report if they exist.
    
    Args:
        report (dict): Report data
    """
    # Challenges
    if report.get('challenges'):
        st.subheader('Challenges & Assistance')
        st.write(report['challenges'])
    
    # Slow Projects
    if report.get('slow_projects'):
        st.subheader('Slow-Moving Projects')
        st.write(report['slow_projects'])
    
    # Other Topics
    if report.get('other_topics'):
        st.subheader('Other Discussion Topics')
        st.write(report['other_topics'])
    
    # Key Accomplishments
    if report.get('key_accomplishments'):
        st.subheader('Key Accomplishments')
        st.write(report['key_accomplishments'])
    
    # Concerns
    if report.get('concerns'):
        st.subheader('Concerns')
        st.write(report['concerns'])
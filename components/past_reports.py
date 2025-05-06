# components/past_reports.py
"""Past reports component for the Weekly Report app."""

import streamlit as st
from utils import file_ops, session
import json

def render_past_reports():
    """Render the past reports view.
    
    Displays all saved reports with options to view details,
    load them as templates, or delete them.
    """
    st.header('Past Reports')
    try:
        reports = file_ops.get_all_reports()
        
        if not reports:
            st.info('No past reports found.')
            return
        
        # Add search and filter options
        st.subheader("Filter Reports")
        
        # Get unique weeks and names for filtering
        weeks = sorted(list(set([r.get('reporting_week', 'Unknown') for r in reports])), reverse=True)
        names = sorted(list(set([r.get('name', 'Anonymous') for r in reports])))
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_week = st.selectbox("Filter by Week", ["All Weeks"] + weeks)
        
        with col2:
            selected_name = st.selectbox("Filter by Name", ["All Names"] + names)
        
        # Apply filters
        filtered_reports = reports
        
        if selected_week != "All Weeks":
            filtered_reports = [r for r in filtered_reports if r.get('reporting_week') == selected_week]
            
        if selected_name != "All Names":
            filtered_reports = [r for r in filtered_reports if r.get('name') == selected_name]
            
        if not filtered_reports:
            st.info("No reports match your filter criteria.")
            return
            
        # Display reports
        st.subheader(f"Found {len(filtered_reports)} Report(s)")
        
        for i, report in enumerate(filtered_reports):
            report_title = f"{report.get('name', 'Anonymous')} - {report.get('reporting_week', 'Unknown')}"
            report_status = report.get('status', 'submitted')
            report_date = report.get('timestamp', '')[:10]
            
            # Use different icons based on status
            status_icon = "📝" if report_status == "draft" else "✅"
            
            with st.expander(f"{status_icon} {report_title} ({report_date})"):
                render_report_details(report, i)
                
    except Exception as e:
        st.error(f"Error rendering past reports: {str(e)}")

def render_report_details(report, index):
    """Render the details of a specific report.
    
    Args:
        report (dict): Report data to display
        index (int): Report index for unique keys
    """
    try:
        # Basic info
        st.write(f"**Name:** {report.get('name', 'Anonymous')}")
        st.write(f"**Reporting Week:** {report.get('reporting_week', 'Unknown')}")
        st.write(f"**Submitted:** {report.get('timestamp', '')[:19].replace('T', ' ')}")
        st.write(f"**Status:** {report.get('status', 'submitted').capitalize()}")
        
        # Current Activities
        if report.get('current_activities'):
            st.subheader('Current Activities')
            for activity in report['current_activities']:
                # Include project and milestone if they exist
                project_info = ""
                if activity.get('project'):
                    project_info = f"Project: {activity.get('project')}"
                    if activity.get('milestone'):
                        project_info += f", Milestone: {activity.get('milestone')}"
                    project_info += " | "
                
                st.markdown(f"- **{activity.get('description', '')}** "
                            f"({project_info}Priority: {activity.get('priority')}, "
                            f"Status: {activity.get('status')}, "
                            f"Progress: {activity.get('progress')}%)")
        
        # Upcoming Activities
        if report.get('upcoming_activities'):
            st.subheader('Upcoming Activities')
            for activity in report['upcoming_activities']:
                # Include project and milestone if they exist
                project_info = ""
                if activity.get('project'):
                    project_info = f"Project: {activity.get('project')}"
                    if activity.get('milestone'):
                        project_info += f", Milestone: {activity.get('milestone')}"
                    project_info += " | "
                
                st.markdown(f"- **{activity.get('description', '')}** "
                            f"({project_info}Priority: {activity.get('priority')}, "
                            f"Expected Start: {activity.get('expected_start', 'Not specified')})")
        
        # Accomplishments
        if report.get('accomplishments'):
            st.subheader('Last Week\'s Accomplishments')
            for accomplishment in report['accomplishments']:
                # Check if the accomplishment is in JSON format
                if isinstance(accomplishment, str) and accomplishment.startswith('{') and accomplishment.endswith('}'):
                    try:
                        acc_data = json.loads(accomplishment)
                        text = acc_data.get('text', accomplishment)
                        project = acc_data.get('project', '')
                        milestone = acc_data.get('milestone', '')
                        
                        # Format with project/milestone info if available
                        project_info = ""
                        if project:
                            project_info = f" (Project: {project}"
                            if milestone:
                                project_info += f", Milestone: {milestone}"
                            project_info += ")"
                            
                        st.markdown(f"- {text}{project_info}")
                    except:
                        st.markdown(f"- {accomplishment}")
                else:
                    st.markdown(f"- {accomplishment}")
        
        # Action Items
        if report.get('followups'):
            st.subheader('Follow-ups')
            for followup in report['followups']:
                # Check if the followup is in JSON format
                if isinstance(followup, str) and followup.startswith('{') and followup.endswith('}'):
                    try:
                        data = json.loads(followup)
                        text = data.get('text', followup)
                        project = data.get('project', '')
                        milestone = data.get('milestone', '')
                        
                        # Format with project/milestone info if available
                        project_info = ""
                        if project:
                            project_info = f" (Project: {project}"
                            if milestone:
                                project_info += f", Milestone: {milestone}"
                            project_info += ")"
                            
                        st.markdown(f"- {text}{project_info}")
                    except:
                        st.markdown(f"- {followup}")
                else:
                    st.markdown(f"- {followup}")
        
        if report.get('nextsteps'):
            st.subheader('Next Steps')
            for nextstep in report['nextsteps']:
                # Check if the nextstep is in JSON format
                if isinstance(nextstep, str) and nextstep.startswith('{') and nextstep.endswith('}'):
                    try:
                        data = json.loads(nextstep)
                        text = data.get('text', nextstep)
                        project = data.get('project', '')
                        milestone = data.get('milestone', '')
                        
                        # Format with project/milestone info if available
                        project_info = ""
                        if project:
                            project_info = f" (Project: {project}"
                            if milestone:
                                project_info += f", Milestone: {milestone}"
                            project_info += ")"
                            
                        st.markdown(f"- {text}{project_info}")
                    except:
                        st.markdown(f"- {nextstep}")
                else:
                    st.markdown(f"- {nextstep}")
        
        # Optional sections
        render_optional_report_sections(report)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button('Use as Template', key=f"template_{index}", use_container_width=True):
                try:
                    # Create a deep copy of the report data
                    report_copy = {}
                    for key, value in report.items():
                        if isinstance(value, list):
                            report_copy[key] = value.copy() if value else []
                        else:
                            report_copy[key] = value
                            
                    # Clear the ID to ensure it's saved as a new report
                    report_copy.pop('id', None)
                    session.load_report_data(report_copy)
                    st.success('Report loaded as template!')
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading template: {str(e)}")
                    # Show more detailed debug info
                    with st.expander("Debug Information"):
                        debug_info = session.debug_report_data(report)
                        for line in debug_info:
                            st.text(line)
        
        with col2:
            if st.button('Export as PDF', key=f"export_{index}", use_container_width=True):
                file_ops.export_report_as_pdf(report)
        
        with col3:
            if st.button('Delete Report', key=f"delete_{index}", use_container_width=True):
                # Add a confirmation dialog
                confirm = st.button(f"Confirm Delete", key=f"confirm_delete_{index}")
                if confirm:
                    if file_ops.delete_report(report.get('id')):
                        st.success('Report deleted successfully!')
                        st.rerun()
    except Exception as e:
        st.error(f"Error rendering report details: {str(e)}")

def render_optional_report_sections(report):
    """Render optional sections of a report if they exist.
    
    Args:
        report (dict): Report data
    """
    try:
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
    except Exception as e:
        st.error(f"Error rendering optional sections: {str(e)}")
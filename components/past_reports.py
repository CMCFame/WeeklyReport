# components/past_reports.py - Updated with manager feedback
"""Past reports component for the Weekly Report app with manager feedback integration."""

import streamlit as st
from utils import file_ops, session
from components.pdf_export import render_report_export_button, render_batch_export_reports
from components.manager_feedback import render_manager_feedback_section, render_feedback_summary_card

def render_past_reports():
    """Render the past reports view.
    
    Displays all saved reports with options to view details,
    load them as templates, or delete them.
    """
    st.header('Past Reports')
    
    # Initialize delete confirmation state
    if 'delete_confirmation' not in st.session_state:
        st.session_state.delete_confirmation = {}
    
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_week = st.selectbox("Filter by Week", ["All Weeks"] + weeks)
        
        with col2:
            selected_name = st.selectbox("Filter by Name", ["All Names"] + names)
        
        with col3:
            # NEW: Filter by feedback status
            feedback_filter = st.selectbox("Filter by Feedback", [
                "All Reports", 
                "Has Feedback", 
                "Needs Feedback",
                "Excellent", 
                "Good", 
                "Needs Improvement"
            ])
        
        # Apply filters
        filtered_reports = reports
        
        if selected_week != "All Weeks":
            filtered_reports = [r for r in filtered_reports if r.get('reporting_week') == selected_week]
            
        if selected_name != "All Names":
            filtered_reports = [r for r in filtered_reports if r.get('name') == selected_name]
        
        # NEW: Apply feedback filter
        if feedback_filter != "All Reports":
            if feedback_filter == "Has Feedback":
                filtered_reports = [r for r in filtered_reports if r.get('manager_feedback')]
            elif feedback_filter == "Needs Feedback":
                filtered_reports = [r for r in filtered_reports if not r.get('manager_feedback') and r.get('status') == 'submitted']
            elif feedback_filter.lower() in ["excellent", "good", "needs improvement"]:
                status_key = feedback_filter.lower().replace(' ', '_')
                filtered_reports = [r for r in filtered_reports 
                                 if r.get('manager_feedback', {}).get('status') == status_key]
            
        if not filtered_reports:
            st.info("No reports match your filter criteria.")
            return
        
        # Add batch export option
        render_batch_export_reports(filtered_reports)
            
        # Display reports
        st.subheader(f"Found {len(filtered_reports)} Report(s)")
        
        for i, report in enumerate(filtered_reports):
            report_title = f"{report.get('name', 'Anonymous')} - {report.get('reporting_week', 'Unknown')}"
            report_status = report.get('status', 'submitted')
            report_date = report.get('timestamp', '')[:10]
            
            # Use different icons based on status
            status_icon = "📝" if report_status == "draft" else "✅"
            
            # NEW: Add feedback status to title
            feedback_summary = render_feedback_summary_card(report)
            title_with_feedback = f"{status_icon} {report_title} ({report_date}) | {feedback_summary}"
            
            with st.expander(title_with_feedback):
                render_report_details_with_feedback(report, i)
                
    except Exception as e:
        st.error(f"Error rendering past reports: {str(e)}")

def render_report_details_with_feedback(report, index):
    """Render the details of a specific report with feedback section.
    
    Args:
        report (dict): Report data to display
        index (int): Report index for unique keys
    """
    try:
        report_id = report.get('id')
        
        # Create tabs for better organization
        tab1, tab2 = st.tabs(["📄 Report Content", "💬 Manager Feedback"])
        
        with tab1:
            render_report_content(report, index)
        
        with tab2:
            # Manager feedback section
            render_manager_feedback_section(report, report_index=index)
                    
    except Exception as e:
        st.error(f"Error rendering report details: {str(e)}")

def render_report_content(report, index):
    """Render the main report content (separated for cleaner tabs)."""
    try:
        report_id = report.get('id')
        
        # Basic info
        st.write(f"**Name:** {report.get('name', 'Anonymous')}")
        st.write(f"**Reporting Week:** {report.get('reporting_week', 'Unknown')}")
        st.write(f"**Submitted:** {report.get('timestamp', '')[:19].replace('T', ' ')}")
        
        # Add last updated info if available
        if report.get('last_updated'):
            st.write(f"**Last Updated:** {report.get('last_updated', '')[:19].replace('T', ' ')}")
        
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
                # Simple display of accomplishments
                st.markdown(f"- {accomplishment}")
        
        # Action Items
        if report.get('followups'):
            st.subheader('Follow-ups')
            for followup in report['followups']:
                # Simple display of followups
                st.markdown(f"- {followup}")
        
        if report.get('nextsteps'):
            st.subheader('Next Steps')
            for nextstep in report['nextsteps']:
                # Simple display of nextsteps
                st.markdown(f"- {nextstep}")
        
        # Optional sections
        render_optional_report_sections(report)
        
        # Action buttons section
        render_report_action_buttons(report, index)
        
    except Exception as e:
        st.error(f"Error rendering report content: {str(e)}")

def render_report_action_buttons(report, index):
    """Render action buttons for the report."""
    report_id = report.get('id')
    
    # Check if this report is in delete confirmation state
    is_delete_pending = st.session_state.delete_confirmation.get(report_id, False)
    
    if is_delete_pending:
        # Show delete confirmation
        st.warning("⚠️ Are you sure you want to delete this report? This action cannot be undone.")
        
        confirm_col1, confirm_col2 = st.columns(2)
        
        with confirm_col1:
            if st.button("✅ Yes, Delete", key=f"confirm_delete_{index}", type="primary"):
                if file_ops.delete_report(report_id):
                    st.success('Report deleted successfully!')
                    # Clear the confirmation state
                    st.session_state.delete_confirmation[report_id] = False
                    st.rerun()
                else:
                    st.error("Failed to delete report.")
        
        with confirm_col2:
            if st.button("❌ Cancel", key=f"cancel_delete_{index}"):
                # Clear the confirmation state
                st.session_state.delete_confirmation[report_id] = False
                st.rerun()
    else:
        # Show normal action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button('Use as Template', key=f"template_{index}", use_container_width=True):
                try:
                    # Create a deep copy of the report data (excluding feedback)
                    report_copy = {}
                    for key, value in report.items():
                        # Skip feedback when using as template
                        if key == 'manager_feedback':
                            continue
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
        
        with col2:
            # PDF export button
            render_report_export_button(report, button_text="Export as PDF", key_suffix=str(index))
        
        with col3:
            # Add Edit button
            if st.button('Edit Report', key=f"edit_{index}", use_container_width=True):
                # Load report data into session state
                session.load_report_data(report)
                # Set a flag to indicate we're editing a report
                st.session_state.editing_report = True
                # Navigate to the weekly report page
                st.session_state.nav_page = "Weekly Report"
                st.session_state.nav_section = "reporting"
                st.rerun()
        
        with col4:
            if st.button('Delete Report', key=f"delete_{index}", use_container_width=True):
                # Set the confirmation state for this report
                st.session_state.delete_confirmation[report_id] = True
                st.rerun()

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

# Legacy function for backward compatibility
def render_report_details(report, index):
    """Legacy function that calls the new tabbed version."""
    render_report_details_with_feedback(report, index)
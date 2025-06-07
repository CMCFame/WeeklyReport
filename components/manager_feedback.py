# components/manager_feedback.py
"""Manager feedback component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
from utils.file_ops import save_report, load_report
from utils.user_auth import require_role

def render_manager_feedback_section(report_data, report_index=None):
    """Render manager feedback section for a report.
    
    Args:
        report_data (dict): The report data
        report_index (int): Index for unique keys if rendering multiple reports
    """
    if not report_data:
        return
    
    # Check if current user is manager or admin
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    is_manager_or_admin = user_role in ["manager", "admin"]
    
    # Get current user info
    current_user = st.session_state.get("user_info", {})
    current_user_name = current_user.get("full_name", "Unknown")
    current_user_id = current_user.get("id")
    
    # Get existing feedback
    feedback_data = report_data.get('manager_feedback', {})
    
    st.subheader("📝 Manager Feedback")
    
    # Show existing feedback if any
    if feedback_data:
        render_existing_feedback(feedback_data)
        st.divider()
    
    # Manager interface to add/edit feedback
    if is_manager_or_admin:
        render_manager_feedback_form(report_data, current_user_name, current_user_id, report_index)
    else:
        if not feedback_data:
            st.info("No manager feedback yet.")

def render_existing_feedback(feedback_data):
    """Render existing feedback in a clean format."""
    feedback_text = feedback_data.get('feedback', '')
    feedback_author = feedback_data.get('author_name', 'Unknown Manager')
    feedback_date = feedback_data.get('date', '')
    feedback_status = feedback_data.get('status', 'pending')
    
    # Status indicator
    status_colors = {
        'excellent': '🌟',
        'good': '👍',
        'needs_improvement': '⚠️',
        'pending': '⏳'
    }
    
    status_icon = status_colors.get(feedback_status, '📝')
    
    st.markdown(f"**{status_icon} Feedback Status:** {feedback_status.replace('_', ' ').title()}")
    
    if feedback_date:
        try:
            # Format date nicely
            date_obj = datetime.fromisoformat(feedback_date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%B %d, %Y at %I:%M %p')
            st.markdown(f"**📅 Date:** {formatted_date}")
        except:
            st.markdown(f"**📅 Date:** {feedback_date}")
    
    st.markdown(f"**👤 From:** {feedback_author}")
    
    if feedback_text:
        st.markdown("**💬 Comments:**")
        # Display feedback in a nice container
        with st.container():
            st.info(feedback_text)
    else:
        st.markdown("*No additional comments provided.*")

def render_manager_feedback_form(report_data, manager_name, manager_id, report_index):
    """Render the form for managers to add/edit feedback."""
    
    # Get existing feedback
    existing_feedback = report_data.get('manager_feedback', {})
    
    # Use report_index for unique keys if provided
    key_suffix = f"_{report_index}" if report_index is not None else ""
    
    with st.form(f"manager_feedback_form{key_suffix}"):
        st.markdown("**Add/Update Feedback:**")
        
        # Status selection
        status_options = {
            'excellent': '🌟 Excellent Work',
            'good': '👍 Good Progress', 
            'needs_improvement': '⚠️ Needs Improvement',
            'pending': '⏳ Under Review'
        }
        
        current_status = existing_feedback.get('status', 'pending')
        status = st.selectbox(
            "Overall Assessment",
            options=list(status_options.keys()),
            format_func=lambda x: status_options[x],
            index=list(status_options.keys()).index(current_status) if current_status in status_options else 0,
            key=f"feedback_status{key_suffix}"
        )
        
        # Feedback text
        feedback_text = st.text_area(
            "Comments & Suggestions",
            value=existing_feedback.get('feedback', ''),
            height=120,
            placeholder="Provide specific feedback on accomplishments, suggestions for improvement, recognition, etc.",
            key=f"feedback_text{key_suffix}"
        )
        
        # Quick feedback templates
        st.markdown("**Quick Templates:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("➕ Add Recognition"):
                st.session_state[f"feedback_text{key_suffix}"] = feedback_text + "\n\n🌟 Great work on "
                st.rerun()
        
        with col2:
            if st.form_submit_button("➕ Add Suggestion"):
                st.session_state[f"feedback_text{key_suffix}"] = feedback_text + "\n\n💡 Consider "
                st.rerun()
        
        with col3:
            if st.form_submit_button("➕ Add Question"):
                st.session_state[f"feedback_text{key_suffix}"] = feedback_text + "\n\n❓ Can you clarify "
                st.rerun()
        
        # Submit feedback
        if st.form_submit_button("💾 Save Feedback", type="primary"):
            save_manager_feedback(report_data, status, feedback_text, manager_name, manager_id)

def save_manager_feedback(report_data, status, feedback_text, manager_name, manager_id):
    """Save manager feedback to the report."""
    try:
        # Create feedback data
        feedback_data = {
            'feedback': feedback_text.strip(),
            'status': status,
            'author_name': manager_name,
            'author_id': manager_id,
            'date': datetime.now().isoformat()
        }
        
        # Add feedback to report data
        report_data['manager_feedback'] = feedback_data
        
        # Update the last_updated timestamp
        report_data['last_updated'] = datetime.now().isoformat()
        
        # Save the updated report
        report_id = save_report(report_data)
        
        if report_id:
            st.success("✅ Feedback saved successfully!")
            st.balloons()
            # Small delay to show success, then rerun to refresh the display
            import time
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Failed to save feedback. Please try again.")
            
    except Exception as e:
        st.error(f"❌ Error saving feedback: {str(e)}")

def render_feedback_summary_card(report_data):
    """Render a compact feedback summary card for report lists."""
    feedback_data = report_data.get('manager_feedback')
    
    if not feedback_data:
        return "⏳ No feedback"
    
    status = feedback_data.get('status', 'pending')
    status_icons = {
        'excellent': '🌟',
        'good': '👍', 
        'needs_improvement': '⚠️',
        'pending': '⏳'
    }
    
    icon = status_icons.get(status, '📝')
    status_text = status.replace('_', ' ').title()
    
    return f"{icon} {status_text}"

def get_reports_needing_feedback(filter_by_manager=False):
    """Get reports that need manager feedback.
    
    Args:
        filter_by_manager (bool): If True, only return reports for team members of current manager
        
    Returns:
        list: Reports that need feedback
    """
    from utils.file_ops import get_all_reports
    
    try:
        # Get all reports
        all_reports = get_all_reports(filter_by_user=False)
        
        # Filter reports that need feedback
        reports_needing_feedback = []
        
        for report in all_reports:
            # Skip if already has feedback
            if report.get('manager_feedback'):
                continue
            
            # Skip draft reports
            if report.get('status') == 'draft':
                continue
            
            # If filtering by manager, add team member filtering logic here
            # For now, include all submitted reports without feedback
            if report.get('status') == 'submitted':
                reports_needing_feedback.append(report)
        
        return sorted(reports_needing_feedback, key=lambda x: x.get('timestamp', ''), reverse=True)
        
    except Exception as e:
        st.error(f"Error getting reports needing feedback: {str(e)}")
        return []

def render_feedback_dashboard():
    """Render a dashboard for managers to see reports needing feedback."""
    st.title("📋 Feedback Dashboard")
    st.write("Review and provide feedback on team member reports")
    
    # Check permissions
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    if user_role not in ["manager", "admin"]:
        st.error("Access denied. This page is for managers and administrators only.")
        return
    
    # Get reports needing feedback
    reports_needing_feedback = get_reports_needing_feedback()
    
    if not reports_needing_feedback:
        st.success("🎉 All reports have been reviewed!")
        st.info("Check back later for new reports to review.")
        return
    
    st.subheader(f"📊 {len(reports_needing_feedback)} Report(s) Awaiting Feedback")
    
    # Display reports in tabs or expandable sections
    for i, report in enumerate(reports_needing_feedback):
        report_title = f"{report.get('name', 'Anonymous')} - {report.get('reporting_week', 'Unknown')}"
        report_date = report.get('timestamp', '')[:10] if report.get('timestamp') else 'Unknown'
        
        with st.expander(f"📄 {report_title} ({report_date})", expanded=(i==0)):
            # Show report summary
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Quick report overview
                st.write("**Quick Overview:**")
                
                activities_count = len(report.get('current_activities', []))
                accomplishments_count = len([a for a in report.get('accomplishments', []) if a.strip()])
                
                st.write(f"• {activities_count} current activities")
                st.write(f"• {accomplishments_count} accomplishments")
                
                # Show top accomplishment
                accomplishments = report.get('accomplishments', [])
                if accomplishments:
                    top_accomplishment = next((a for a in accomplishments if a.strip()), None)
                    if top_accomplishment:
                        st.write(f"• Key accomplishment: *{top_accomplishment[:100]}...*" if len(top_accomplishment) > 100 else f"• Key accomplishment: *{top_accomplishment}*")
            
            with col2:
                # Quick stats
                st.metric("Activities", activities_count)
                st.metric("Accomplishments", accomplishments_count)
            
            # View full report button
            if st.button(f"👁️ View Full Report", key=f"view_report_{i}"):
                st.session_state[f"show_full_report_{i}"] = True
                st.rerun()
            
            # Show full report if requested
            if st.session_state.get(f"show_full_report_{i}", False):
                st.markdown("---")
                st.markdown("### Full Report Details")
                
                # Import and use the existing report rendering
                from components.past_reports import render_report_details
                render_report_details(report, i)
                
                if st.button(f"🔼 Hide Details", key=f"hide_report_{i}"):
                    st.session_state[f"show_full_report_{i}"] = False
                    st.rerun()
            
            st.markdown("---")
            
            # Feedback section
            render_manager_feedback_section(report, report_index=i)
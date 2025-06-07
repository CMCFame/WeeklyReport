# components/feedback_notifications.py
"""Feedback notification component for managers."""

import streamlit as st
from components.manager_feedback import get_reports_needing_feedback

def render_feedback_notifications():
    """Render feedback notifications in the sidebar for managers."""
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    
    # Only show for managers and admins
    if user_role not in ["manager", "admin"]:
        return
    
    try:
        # Get reports needing feedback
        reports_needing_feedback = get_reports_needing_feedback()
        
        if reports_needing_feedback:
            count = len(reports_needing_feedback)
            
            # Show notification in sidebar
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📋 Pending Reviews")
            
            if count == 1:
                message = f"**{count} report** needs your feedback"
            else:
                message = f"**{count} reports** need your feedback"
            
            st.sidebar.warning(message)
            
            # Quick action button
            if st.sidebar.button("🚀 Review Reports", use_container_width=True):
                st.session_state.nav_section = "team"
                st.session_state.nav_page = "Feedback Dashboard"
                st.rerun()
            
            # Show quick preview of reports needing feedback
            with st.sidebar.expander("📋 Quick Preview"):
                for report in reports_needing_feedback[:3]:  # Show max 3
                    name = report.get('name', 'Anonymous')
                    week = report.get('reporting_week', 'Unknown')
                    st.write(f"• {name} - {week}")
                
                if count > 3:
                    st.write(f"• ... and {count - 3} more")
        else:
            # Optional: Show a small success indicator when all reports are reviewed
            if user_role in ["manager", "admin"]:
                st.sidebar.markdown("---")
                st.sidebar.success("✅ All reports reviewed!")
                
    except Exception as e:
        # Silently fail to avoid disrupting the main app
        pass

def render_feedback_badge(report_data):
    """Render a small feedback status badge for a report.
    
    Args:
        report_data (dict): Report data
        
    Returns:
        str: Badge emoji/text
    """
    feedback = report_data.get('manager_feedback')
    
    if not feedback:
        if report_data.get('status') == 'submitted':
            return "⏳"  # Pending feedback
        else:
            return ""  # Draft, no feedback needed
    
    status = feedback.get('status', 'pending')
    status_badges = {
        'excellent': '🌟',
        'good': '👍',
        'needs_improvement': '⚠️',
        'pending': '⏳'
    }
    
    return status_badges.get(status, '📝')

def get_feedback_stats():
    """Get feedback statistics for dashboard widgets.
    
    Returns:
        dict: Feedback statistics
    """
    try:
        from utils.file_ops import get_all_reports
        
        all_reports = get_all_reports(filter_by_user=False)
        
        stats = {
            'total_reports': len(all_reports),
            'reports_with_feedback': 0,
            'reports_needing_feedback': 0,
            'excellent_count': 0,
            'good_count': 0,
            'needs_improvement_count': 0
        }
        
        for report in all_reports:
            # Skip drafts
            if report.get('status') != 'submitted':
                continue
                
            feedback = report.get('manager_feedback')
            
            if feedback:
                stats['reports_with_feedback'] += 1
                status = feedback.get('status', 'pending')
                
                if status == 'excellent':
                    stats['excellent_count'] += 1
                elif status == 'good':
                    stats['good_count'] += 1
                elif status == 'needs_improvement':
                    stats['needs_improvement_count'] += 1
            else:
                stats['reports_needing_feedback'] += 1
        
        return stats
        
    except Exception as e:
        return {
            'total_reports': 0,
            'reports_with_feedback': 0,
            'reports_needing_feedback': 0,
            'excellent_count': 0,
            'good_count': 0,
            'needs_improvement_count': 0
        }

def render_feedback_stats_widget():
    """Render feedback statistics widget for dashboards."""
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    
    if user_role not in ["manager", "admin"]:
        return
    
    stats = get_feedback_stats()
    
    st.subheader("📊 Feedback Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Pending Reviews", 
            stats['reports_needing_feedback'],
            delta=None
        )
    
    with col2:
        st.metric(
            "Reviewed", 
            stats['reports_with_feedback'],
            delta=None
        )
    
    with col3:
        coverage = 0
        if stats['total_reports'] > 0:
            coverage = round((stats['reports_with_feedback'] / stats['total_reports']) * 100)
        st.metric(
            "Coverage", 
            f"{coverage}%",
            delta=None
        )
    
    with col4:
        if stats['reports_with_feedback'] > 0:
            excellent_pct = round((stats['excellent_count'] / stats['reports_with_feedback']) * 100)
            st.metric(
                "Excellent", 
                f"{excellent_pct}%",
                delta=None
            )
        else:
            st.metric("Excellent", "0%")
    
    # Quick breakdown
    if stats['reports_with_feedback'] > 0:
        st.write("**Feedback Breakdown:**")
        
        feedback_col1, feedback_col2, feedback_col3 = st.columns(3)
        
        with feedback_col1:
            st.write(f"🌟 Excellent: {stats['excellent_count']}")
        with feedback_col2:
            st.write(f"👍 Good: {stats['good_count']}")
        with feedback_col3:
            st.write(f"⚠️ Needs Improvement: {stats['needs_improvement_count']}")

# Add this to your main app.py file in the navigation section:
def add_feedback_notifications_to_sidebar():
    """Add this function call to your main app after render_navigation()"""
    render_feedback_notifications()
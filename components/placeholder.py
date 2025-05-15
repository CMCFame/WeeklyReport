# components/placeholder.py
"""Placeholder components for pages not yet implemented."""

import streamlit as st

def render_placeholder(title, description, coming_soon=True):
    """Render a placeholder for features not yet implemented.
    
    Args:
        title (str): Page title
        description (str): Description of the feature
        coming_soon (bool): Whether to show "Coming Soon" badge
    """
    st.title(title)
    
    if coming_soon:
        st.markdown(
            """
            <div style="display: inline-block; background-color: #ffcc00; color: #000; padding: 0.2rem 0.5rem; 
                border-radius: 0.5rem; font-size: 0.8rem; margin-bottom: 1rem;">
                COMING SOON
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    st.write(description)
    
    # Placeholder illustration
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://via.placeholder.com/600x300?text=Feature+Coming+Soon", use_column_width=True)
    
    # Expand with more details depending on the feature
    with st.expander("What to expect"):
        if "Objectives" in title or "Goal" in title or "OKR" in title:
            st.write("""
            ### Goal Setting and Tracking Features
            
            * Create and manage OKRs (Objectives and Key Results)
            * Track progress toward goals
            * Connect team and individual goals
            * View dashboards showing goal achievement
            * Generate reports on goal progress
            """)
        elif "Template" in title:
            st.write("""
            ### Report Templates Features
            
            * Create custom report templates
            * Save frequently used report structures
            * Share templates with team members
            * Set default templates for different teams
            * Import and export templates
            """)
        elif "Team Structure" in title or "1:1" in title:
            st.write("""
            ### Team Management Features
            
            * Define team hierarchy and structure
            * Schedule and track 1:1 meetings
            * Create meeting agendas and notes
            * Set up recurring team check-ins
            * Track action items from meetings
            """)
        else:
            st.write("""
            ### Feature Currently Under Development
            
            This feature is currently being developed and will be available in a future update.
            Check back soon for more information!
            """)

def render_report_templates():
    """Render the report templates page placeholder."""
    render_placeholder(
        "Report Templates",
        "Create and manage templates for weekly reports to streamline the reporting process."
    )

def render_team_objectives():
    """Render the team objectives page."""
    # This function is just a wrapper now that calls our actual implementation
    # We need to keep it for backward compatibility
    from components.team_objectives import render_team_objectives as render_real_team_objectives
    render_real_team_objectives()

def render_goal_dashboard():
    """Render the goal dashboard page."""
    # This function is just a wrapper now that calls our actual implementation
    # We need to keep it for backward compatibility
    from components.goal_dashboard import render_goal_dashboard as render_real_goal_dashboard
    render_real_goal_dashboard()

def render_okr_management():
    """Render the OKR management page placeholder."""
    # This function is just a wrapper now that calls our actual implementation
    # We need to keep it for backward compatibility
    from components.okr_management import render_okr_management as render_real_okr_management
    render_real_okr_management()

def render_team_structure():
    """Render the team structure page placeholder."""
    render_placeholder(
        "Team Structure",
        "Define and visualize your team organization and reporting structure."
    )

def render_one_on_one_meetings():
    """Render the 1:1 meetings page placeholder."""
    render_placeholder(
        "1:1 Meetings",
        "Schedule, prepare for, and track outcomes of one-on-one meetings with team members."
    )

def render_system_settings():
    """Render the system settings page placeholder."""
    render_placeholder(
        "System Settings",
        "Configure system-wide settings and preferences.",
        coming_soon=False
    )
    
    # Add some actual settings
    st.subheader("Display Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Use simplified UI for reports", value=True)
        st.checkbox("Enable dark mode", value=False)
    
    with col2:
        st.selectbox("Default report view", ["Compact", "Standard", "Detailed"])
        st.selectbox("Default date format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
    
    st.subheader("Email Notifications")
    st.checkbox("Weekly report reminders", value=True)
    st.checkbox("Report submission notifications", value=True)
    st.checkbox("Team activity updates", value=False)
    
    st.button("Save Settings", type="primary")
# components/goals/goals_page.py
"""Goals page component for the Weekly Report app."""

import streamlit as st
from utils.goal_session import init_goal_session_state, reset_goal_form
from components.goals.goal_dashboard import render_goal_dashboard
from components.goals.goal_form import render_goal_form
from components.goals.goal_detail import render_goal_detail

def render_goals_page():
    """Render the main goals page with navigation."""
    # Initialize goal-related session state
    init_goal_session_state()
    
    # Set up navigation if not already set
    if 'goal_page' not in st.session_state:
        st.session_state.goal_page = "dashboard"
    
    # Sidebar navigation
    st.sidebar.title("Goal Management")
    
    navigation_option = st.sidebar.radio(
        "Navigate to:",
        ["Goals Dashboard", "Create New Goal"],
        index=0 if st.session_state.goal_page == "dashboard" else 1 if st.session_state.goal_page == "new" else 0
    )
    
    # Update page based on navigation selection
    if navigation_option == "Goals Dashboard":
        st.session_state.goal_page = "dashboard"
    elif navigation_option == "Create New Goal":
        st.session_state.goal_page = "new"
        # Reset form when navigating to create new
        reset_goal_form()
    
    # Render the appropriate page
    if st.session_state.goal_page == "dashboard":
        render_goal_dashboard()
    elif st.session_state.goal_page == "new":
        render_goal_form()
    elif st.session_state.goal_page == "edit":
        render_goal_form()
    elif st.session_state.goal_page == "detail":
        render_goal_detail()
# components/goals/goal_dashboard.py
"""Goal dashboard component for the Weekly Report app."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.goal_ops import get_all_goals, delete_goal, calculate_goal_progress
from utils.goal_session import load_goal_to_form

def render_goal_dashboard():
    """Render the goal dashboard with summary metrics and goal lists."""
    st.title('🎯 Goals Dashboard')
    
    # Fetch all goals for the current user
    goals = get_all_goals(filter_by_user=True)
    
    if not goals:
        st.info("You don't have any goals yet. Create your first goal to get started!")
        return
    
    # Display summary metrics
    render_goal_summary_metrics(goals)
    
    # Goal filtering options
    col1, col2 = st.columns(2)
    
    with col1:
        goal_filter = st.radio(
            "Filter by type:", 
            ["All Goals", "Objectives", "KPIs", "Projects"],
            horizontal=True
        )
    
    with col2:
        status_filter = st.radio(
            "Filter by status:", 
            ["Active", "All", "Completed", "Archived"],
            horizontal=True
        )
    
    # Filter goals based on selection
    filtered_goals = goals.copy()
    
    # Apply type filter
    if goal_filter == "Objectives":
        filtered_goals = [g for g in filtered_goals if g.get('goal_type') == 'objective']
    elif goal_filter == "KPIs":
        filtered_goals = [g for g in filtered_goals if g.get('goal_type') == 'kpi']
    elif goal_filter == "Projects":
        filtered_goals = [g for g in filtered_goals if g.get('goal_type') == 'project']
    
    # Apply status filter
    if status_filter == "Active":
        filtered_goals = [g for g in filtered_goals if g.get('status') == 'active']
    elif status_filter == "Completed":
        filtered_goals = [g for g in filtered_goals if g.get('status') == 'completed']
    elif status_filter == "Archived":
        filtered_goals = [g for g in filtered_goals if g.get('status') == 'archived']
    
    # Display goals in cards
    render_goal_cards(filtered_goals)

def render_goal_summary_metrics(goals):
    """Render summary metrics for goals.
    
    Args:
        goals (list): List of goal data dictionaries
    """
    # Calculate metrics
    total_goals = len(goals)
    active_goals = len([g for g in goals if g.get('status') == 'active'])
    completed_goals = len([g for g in goals if g.get('status') == 'completed'])
    
    # Calculate due soon (next 7 days)
    now = datetime.now().date()
    week_later = now + timedelta(days=7)
    due_soon = 0
    
    for goal in goals:
        if goal.get('status') != 'active':
            continue
            
        if goal.get('due_date'):
            try:
                due_date = datetime.strptime(goal['due_date'], '%Y-%m-%d').date()
                if now <= due_date <= week_later:
                    due_soon += 1
            except ValueError:
                pass
    
    # Calculate average progress of active goals
    progress_values = []
    for goal in goals:
        if goal.get('status') == 'active':
            goal_id = goal.get('id')
            if goal_id:
                progress = calculate_goal_progress(goal_id)
                progress_values.append(progress)
    
    avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Goals", total_goals)
    
    with col2:
        st.metric("Active Goals", active_goals)
    
    with col3:
        st.metric("Due Soon", due_soon)
    
    with col4:
        st.metric("Avg Progress", f"{avg_progress:.1f}%")
    
    # Add a progress bar for overall progress
    st.progress(avg_progress / 100)

def render_goal_cards(goals):
    """Render goals as cards.
    
    Args:
        goals (list): List of goal data dictionaries
    """
    if not goals:
        st.info("No goals match your current filter criteria.")
        return
    
    # Create two columns for cards
    for i in range(0, len(goals), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            if i < len(goals):
                render_goal_card(goals[i])
        
        with col2:
            if i + 1 < len(goals):
                render_goal_card(goals[i + 1])

def render_goal_card(goal):
    """Render a single goal card.
    
    Args:
        goal (dict): Goal data dictionary
    """
    # Determine card color and icon based on goal type
    goal_type = goal.get('goal_type', 'objective')
    goal_id = goal.get('id')
    goal_status = goal.get('status', 'active')
    
    if goal_type == 'objective':
        icon = "🎯"
        header_color = "#1E88E5"  # Blue
    elif goal_type == 'kpi':
        icon = "📊"
        header_color = "#43A047"  # Green
    elif goal_type == 'project':
        icon = "📁"
        header_color = "#E53935"  # Red
    else:
        icon = "🏆"
        header_color = "#FB8C00"  # Orange
    
    # Calculate progress
    progress = calculate_goal_progress(goal_id) if goal_id else 0
    
    # Create card with custom styling
    with st.container():
        # Header
        st.markdown(
            f"""
            <div style="
                padding: 5px 10px; 
                border-radius: 5px 5px 0 0; 
                background-color: {header_color};
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>{icon} {goal.get('title', 'Untitled Goal')}</div>
                <div style="font-size: 0.8em;">
                    {goal_type.capitalize()} • {goal_status.capitalize()}
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Card body
        st.markdown(
            f"""
            <div style="
                padding: 10px; 
                border: 1px solid #ddd;
                border-top: none;
                border-radius: 0 0 5px 5px;
                margin-bottom: 15px;
            ">
                <div style="color: #555; margin-bottom: 10px;">
                    {goal.get('description', 'No description provided.')}
                </div>
                <div style="margin-bottom: 10px;">
                    <div style="font-size: 0.8em; color: #777; margin-bottom: 5px;">Progress:</div>
                    <div style="
                        background-color: #f0f0f0;
                        border-radius: 5px;
                        height: 10px;
                        position: relative;
                    ">
                        <div style="
                            position: absolute;
                            height: 10px;
                            width: {progress}%;
                            background-color: {header_color};
                            border-radius: 5px;
                        "></div>
                    </div>
                    <div style="text-align: right; font-size: 0.8em; margin-top: 2px;">
                        {progress:.1f}%
                    </div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Card actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Edit", key=f"edit_{goal_id}", use_container_width=True):
                load_goal_to_form(goal_id)
                # Switch to edit form
                st.session_state.goal_page = "edit"
                st.rerun()
        
        with col2:
            if st.button("Details", key=f"detail_{goal_id}", use_container_width=True):
                load_goal_to_form(goal_id)
                # Switch to detail view
                st.session_state.goal_page = "detail"
                st.rerun()
        
        with col3:
            if st.button("Delete", key=f"delete_{goal_id}", type="secondary", use_container_width=True):
                confirm = st.checkbox(f"Confirm delete '{goal.get('title')}'", key=f"confirm_{goal_id}")
                if confirm:
                    if delete_goal(goal_id):
                        st.success("Goal deleted successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to delete goal.")
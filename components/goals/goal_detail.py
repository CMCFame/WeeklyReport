# components/goals/goal_detail.py
"""Goal detail view component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
from utils.goal_ops import calculate_goal_progress, get_linked_kpis, get_linked_objectives

def render_goal_detail():
    """Render detailed view of a goal."""
    # Ensure we have a goal loaded in session state
    if not st.session_state.current_goal.get('id'):
        st.error("No goal selected. Please select a goal from the dashboard.")
        if st.button("Return to Dashboard"):
            st.session_state.goal_page = "dashboard"
            st.rerun()
        return
    
    goal = st.session_state.current_goal
    goal_type = goal.get('goal_type', 'objective')
    goal_id = goal.get('id')
    
    # Common header
    st.title(f"{get_goal_icon(goal_type)} {goal.get('title', 'Untitled Goal')}")
    
    # Display status, dates, progress
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("Status")
        st.write(goal.get('status', 'active').capitalize())
    
    with col2:
        st.subheader("Type")
        st.write(goal_type.capitalize())
    
    with col3:
        st.subheader("Start Date")
        if goal.get('start_date'):
            try:
                start_date = datetime.strptime(goal['start_date'], '%Y-%m-%d').date()
                st.write(start_date.strftime('%b %d, %Y'))
            except ValueError:
                st.write("Not set")
        else:
            st.write("Not set")
    
    with col4:
        st.subheader("Due Date")
        if goal.get('due_date'):
            try:
                due_date = datetime.strptime(goal['due_date'], '%Y-%m-%d').date()
                st.write(due_date.strftime('%b %d, %Y'))
            except ValueError:
                st.write("Not set")
        else:
            st.write("Not set")
    
    # Description
    st.subheader("Description")
    st.write(goal.get('description', 'No description provided.'))
    
    # Progress
    progress = calculate_goal_progress(goal_id)
    st.subheader("Progress")
    st.progress(progress / 100)
    st.write(f"{progress:.1f}%")
    
    # Type-specific details
    if goal_type == 'kpi':
        render_kpi_details(goal)
    elif goal_type == 'objective':
        render_objective_details(goal)
    elif goal_type == 'project':
        render_project_details(goal)
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Edit Goal", use_container_width=True):
            st.session_state.goal_page = "edit"
            st.rerun()
    
    with col2:
        if st.button("Back to Dashboard", use_container_width=True):
            # Clear the current goal
            st.session_state.current_goal = {}
            st.session_state.goal_page = "dashboard"
            st.rerun()

def get_goal_icon(goal_type):
    """Get icon for a goal type.
    
    Args:
        goal_type (str): Type of goal
        
    Returns:
        str: Emoji icon
    """
    if goal_type == 'objective':
        return "🎯"
    elif goal_type == 'kpi':
        return "📊"
    elif goal_type == 'project':
        return "📁"
    else:
        return "🏆"

def render_kpi_details(goal):
    """Render KPI-specific details.
    
    Args:
        goal (dict): Goal data dictionary
    """
    st.subheader("KPI Details")
    
    # Current and target values
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Current Value", 
            f"{goal.get('current_value', 0)}{goal.get('unit', '')}"
        )
    
    with col2:
        st.metric(
            "Target Value", 
            f"{goal.get('target_value', 0)}{goal.get('unit', '')}"
        )
    
    with col3:
        st.metric(
            "Comparison", 
            get_comparison_type_display(goal.get('comparison_type', 'greater'))
        )
    
    # Linked objective
    linked_objective_id = goal.get('linked_objective')
    if linked_objective_id:
        st.subheader("Linked Objective")
        
        # We'd need to load the objective data here
        from utils.goal_ops import load_goal
        objective = load_goal(linked_objective_id)
        
        if objective:
            st.write(f"This KPI is linked to: **{objective.get('title', 'Unknown Objective')}**")
        else:
            st.write("Linked to an objective that no longer exists.")

def render_objective_details(goal):
    """Render objective-specific details.
    
    Args:
        goal (dict): Goal data dictionary
    """
    goal_id = goal.get('id')
    
    # Linked KPIs
    st.subheader("Linked KPIs")
    linked_kpis = get_linked_kpis(goal_id)
    
    if not linked_kpis:
        st.info("No KPIs are linked to this objective.")
    else:
        # Display KPIs as a table
        kpi_data = []
        for kpi in linked_kpis:
            kpi_progress = calculate_goal_progress(kpi.get('id'))
            kpi_data.append({
                "Title": kpi.get('title', 'Untitled KPI'),
                "Current": f"{kpi.get('current_value', 0)}{kpi.get('unit', '')}",
                "Target": f"{kpi.get('target_value', 0)}{kpi.get('unit', '')}",
                "Progress": f"{kpi_progress:.1f}%"
            })
        
        if kpi_data:
            kpi_df = pd.DataFrame(kpi_data)
            st.dataframe(kpi_df, hide_index=True)

def render_project_details(goal):
    """Render project-specific details.
    
    Args:
        goal (dict): Goal data dictionary
    """
    # Team members
    st.subheader("Team Members")
    team_members = goal.get('team_members', [])
    
    if not team_members:
        st.info("No team members assigned to this project.")
    else:
        for member in team_members:
            st.write(f"• {member}")
    
    # Milestones
    st.subheader("Milestones")
    milestones = goal.get('milestones', [])
    
    if not milestones:
        st.info("No milestones defined for this project.")
    else:
        for milestone in milestones:
            # Create a colored status badge
            status = milestone.get('status', 'not_started')
            status_display = status.replace('_', ' ').capitalize()
            
            if status == 'completed':
                status_color = "#4CAF50"  # Green
            elif status == 'in_progress':
                status_color = "#2196F3"  # Blue
            elif status == 'blocked':
                status_color = "#F44336"  # Red
            else:
                status_color = "#9E9E9E"  # Grey
            
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 10px;
                ">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 5px;
                    ">
                        <div style="font-weight: bold;">{milestone.get('title', 'Untitled Milestone')}</div>
                        <div style="
                            background-color: {status_color};
                            color: white;
                            padding: 2px 8px;
                            border-radius: 10px;
                            font-size: 0.8em;
                        ">{status_display}</div>
                    </div>
                    <div style="color: #555; font-size: 0.9em;">
                        Due: {format_date(milestone.get('due_date'))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

def get_comparison_type_display(comparison_type):
    """Get display text for comparison type.
    
    Args:
        comparison_type (str): Comparison type code
        
    Returns:
        str: Display text
    """
    if comparison_type == 'greater':
        return "Higher is better"
    elif comparison_type == 'less':
        return "Lower is better"
    else:
        return "Equal is target"

def format_date(date_str):
    """Format a date string for display.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        str: Formatted date string
    """
    if not date_str:
        return "Not set"
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        return date_obj.strftime('%b %d, %Y')
    except ValueError:
        return "Invalid date"
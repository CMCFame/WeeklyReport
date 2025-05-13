# components/goals/goal_form.py
"""Goal form component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
from utils.goal_session import (
    reset_goal_form, 
    save_goal_from_form,
    add_project_milestone,
    update_project_milestone,
    remove_project_milestone
)
from utils.goal_ops import get_goals_by_type

def render_goal_form():
    """Render the goal creation/editing form."""
    # Check if we're editing an existing goal
    editing = bool(st.session_state.current_goal.get('id'))
    
    if editing:
        st.title(f"Edit Goal: {st.session_state.goal_title}")
    else:
        st.title("Create New Goal")
    
    # Main form
    with st.form("goal_form"):
        # Title and description
        st.text_input("Goal Title", key="goal_title")
        st.text_area("Description", key="goal_description", height=100)
        
        # Type, status, dates
        col1, col2 = st.columns(2)
        
        with col1:
            goal_type = st.selectbox(
                "Goal Type", 
                ["Objective", "KPI", "Project"],
                index=0 if st.session_state.goal_type == "objective" else 
                       1 if st.session_state.goal_type == "kpi" else 2,
                key="goal_type_select"
            )
            # Map selection to session state value
            st.session_state.goal_type = goal_type.lower()
            
            st.date_input("Start Date", key="goal_start_date")
        
        with col2:
            goal_status = st.selectbox(
                "Status", 
                ["Active", "Completed", "Archived"],
                index=0 if st.session_state.goal_status == "active" else 
                       1 if st.session_state.goal_status == "completed" else 2,
                key="goal_status_select"
            )
            # Map selection to session state value
            st.session_state.goal_status = goal_status.lower()
            
            st.date_input("Due Date", key="goal_due_date", value=None)
        
        # Type-specific fields
        if st.session_state.goal_type == "kpi":
            render_kpi_fields()
        elif st.session_state.goal_type == "objective":
            render_objective_fields()
        elif st.session_state.goal_type == "project":
            render_project_fields()
        
        # Submit buttons
        col1, col2 = st.columns(2)
        
        with col1:
            submit = st.form_submit_button("Save Goal")
        
        with col2:
            cancel = st.form_submit_button("Cancel")
    
    # Form submission handling
    if submit:
        goal_id = save_goal_from_form()
        if goal_id:
            st.success(f"Goal {'updated' if editing else 'created'} successfully!")
            # Reset form and redirect to dashboard
            reset_goal_form()
            st.session_state.goal_page = "dashboard"
            st.rerun()
    
    if cancel:
        reset_goal_form()
        st.session_state.goal_page = "dashboard"
        st.rerun()

def render_kpi_fields():
    """Render KPI-specific form fields."""
    st.subheader("KPI Details")
    
    # KPI value fields
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.number_input("Current Value", key="kpi_current_value", step=0.1)
    
    with col2:
        st.number_input("Target Value", key="kpi_target_value", step=0.1)
    
    with col3:
        st.text_input("Unit (optional)", key="kpi_unit", placeholder="e.g., %, $, hours")
    
    # Comparison type
    st.selectbox(
        "Comparison Type", 
        ["Greater is better", "Less is better", "Equal is target"],
        index=0 if st.session_state.kpi_comparison_type == "greater" else 
               1 if st.session_state.kpi_comparison_type == "less" else 2,
        key="kpi_comparison_type_select"
    )
    # Map selection to session state value
    if st.session_state.kpi_comparison_type_select == "Greater is better":
        st.session_state.kpi_comparison_type = "greater"
    elif st.session_state.kpi_comparison_type_select == "Less is better":
        st.session_state.kpi_comparison_type = "less"
    else:
        st.session_state.kpi_comparison_type = "equal"
    
    # Link to objective
    objectives = get_goals_by_type('objective')
    objective_options = [("", "None")] + [(obj['id'], obj['title']) for obj in objectives]
    
    selected_objective = st.selectbox(
        "Link to Objective",
        options=[opt[0] for opt in objective_options],
        format_func=lambda x: next((opt[1] for opt in objective_options if opt[0] == x), "None"),
        index=next((i for i, opt in enumerate(objective_options) if opt[0] == st.session_state.linked_objective), 0),
        key="linked_objective_select"
    )
    # Update session state
    st.session_state.linked_objective = selected_objective if selected_objective else None

def render_objective_fields():
    """Render objective-specific form fields."""
    st.subheader("Objective Details")
    
    # Manual progress input if no KPIs are linked
    if not st.session_state.linked_kpis:
        manual_progress = st.session_state.current_goal.get('manual_progress', 0)
        st.slider("Progress", 0, 100, manual_progress, 1, key="objective_manual_progress")
        st.info("Link KPIs to this objective for automatic progress calculation, or set manual progress above.")
    
    # Linked KPIs section
    st.subheader("Linked KPIs")
    
    # Get all KPIs
    kpis = get_goals_by_type('kpi')
    
    if not kpis:
        st.info("No KPIs available to link. Create KPIs first, then link them to this objective.")
    else:
        # Create a multiselect for KPIs
        kpi_options = {kpi['id']: f"{kpi['title']} ({kpi.get('current_value', 0)}/{kpi.get('target_value', 0)} {kpi.get('unit', '')})" for kpi in kpis}
        
        selected_kpis = st.multiselect(
            "Select KPIs to link to this objective:",
            options=list(kpi_options.keys()),
            default=st.session_state.linked_kpis,
            format_func=lambda x: kpi_options.get(x, "Unknown KPI"),
            key="linked_kpis_select"
        )
        
        # Update session state
        st.session_state.linked_kpis = selected_kpis
        
        # Display selected KPIs
        if selected_kpis:
            st.write("Selected KPIs:")
            for kpi_id in selected_kpis:
                kpi = next((k for k in kpis if k['id'] == kpi_id), None)
                if kpi:
                    st.write(f"• {kpi['title']} - Current: {kpi.get('current_value', 0)}{kpi.get('unit', '')}, Target: {kpi.get('target_value', 0)}{kpi.get('unit', '')}")

def render_project_fields():
    """Render project-specific form fields."""
    st.subheader("Project Details")
    
    # Manual progress
    manual_progress = st.session_state.current_goal.get('manual_progress', 0)
    st.slider("Progress", 0, 100, manual_progress, 1, key="project_manual_progress")
    
    # Team members
    team_members_str = ", ".join(st.session_state.project_team_members)
    new_team_members = st.text_input(
        "Team Members (comma-separated names)", 
        value=team_members_str,
        key="project_team_members_input"
    )
    # Update session state
    st.session_state.project_team_members = [member.strip() for member in new_team_members.split(",") if member.strip()]
    
    # Milestones
    st.subheader("Project Milestones")
    
    # Add milestone button
    if st.button("Add Milestone", key="add_milestone_button"):
        add_project_milestone()
        st.rerun()
    
    # Display existing milestones
    milestones = st.session_state.project_milestones
    
    if not milestones:
        st.info("No milestones added yet. Click 'Add Milestone' to create one.")
    else:
        for i, milestone in enumerate(milestones):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    title = st.text_input(
                        "Title", 
                        value=milestone.get('title', ''),
                        key=f"milestone_title_{i}"
                    )
                    update_project_milestone(i, 'title', title)
                
                with col2:
                    # Handle date conversion
                    milestone_date = None
                    if milestone.get('due_date'):
                        try:
                            milestone_date = datetime.strptime(milestone['due_date'], '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            milestone_date = None
                    
                    due_date = st.date_input(
                        "Due Date",
                        value=milestone_date,
                        key=f"milestone_date_{i}"
                    )
                    update_project_milestone(i, 'due_date', due_date.strftime('%Y-%m-%d') if due_date else None)
                
                with col3:
                    status = st.selectbox(
                        "Status",
                        ["Not Started", "In Progress", "Completed", "Blocked"],
                        index=0 if milestone.get('status') == 'not_started' else
                               1 if milestone.get('status') == 'in_progress' else
                               2 if milestone.get('status') == 'completed' else 3,
                        key=f"milestone_status_{i}"
                    )
                    # Map to session state value
                    status_value = status.lower().replace(" ", "_")
                    update_project_milestone(i, 'status', status_value)
                
                with col4:
                    st.write("")  # Spacer
                    st.write("")  # Align with inputs
                    if st.button("🗑️", key=f"delete_milestone_{i}"):
                        remove_project_milestone(i)
                        st.rerun()
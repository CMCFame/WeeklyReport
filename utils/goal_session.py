# utils/goal_session.py
"""Goal-related session state management functions."""

import streamlit as st
from datetime import datetime
from utils.goal_ops import save_goal, load_goal

def init_goal_session_state():
    """Initialize goal-related session state variables."""
    # Current goal being edited
    if 'current_goal' not in st.session_state:
        st.session_state.current_goal = {}
    
    # Goal form input fields
    if 'goal_title' not in st.session_state:
        st.session_state.goal_title = ""
    if 'goal_description' not in st.session_state:
        st.session_state.goal_description = ""
    if 'goal_type' not in st.session_state:
        st.session_state.goal_type = "objective"  # Default: objective, kpi, project
    if 'goal_status' not in st.session_state:
        st.session_state.goal_status = "active"   # Default: active, completed, archived
    if 'goal_due_date' not in st.session_state:
        st.session_state.goal_due_date = None
    if 'goal_start_date' not in st.session_state:
        st.session_state.goal_start_date = datetime.now().date()
    
    # KPI-specific fields
    if 'kpi_current_value' not in st.session_state:
        st.session_state.kpi_current_value = 0
    if 'kpi_target_value' not in st.session_state:
        st.session_state.kpi_target_value = 100
    if 'kpi_unit' not in st.session_state:
        st.session_state.kpi_unit = ""
    if 'kpi_comparison_type' not in st.session_state:
        st.session_state.kpi_comparison_type = "greater"  # greater, less, equal
    
    # OKR linking
    if 'linked_kpis' not in st.session_state:
        st.session_state.linked_kpis = []
    if 'linked_objective' not in st.session_state:
        st.session_state.linked_objective = None
    
    # Project-specific fields
    if 'project_team_members' not in st.session_state:
        st.session_state.project_team_members = []
    if 'project_milestones' not in st.session_state:
        st.session_state.project_milestones = []
    
    # Goal list display state
    if 'show_completed_goals' not in st.session_state:
        st.session_state.show_completed_goals = False
    if 'goal_filter_type' not in st.session_state:
        st.session_state.goal_filter_type = "all"  # all, objective, kpi, project

def reset_goal_form():
    """Reset the goal form to its initial state."""
    st.session_state.current_goal = {}
    st.session_state.goal_title = ""
    st.session_state.goal_description = ""
    st.session_state.goal_type = "objective"
    st.session_state.goal_status = "active"
    st.session_state.goal_due_date = None
    st.session_state.goal_start_date = datetime.now().date()
    
    # KPI-specific fields
    st.session_state.kpi_current_value = 0
    st.session_state.kpi_target_value = 100
    st.session_state.kpi_unit = ""
    st.session_state.kpi_comparison_type = "greater"
    
    # OKR linking
    st.session_state.linked_kpis = []
    st.session_state.linked_objective = None
    
    # Project-specific fields
    st.session_state.project_team_members = []
    st.session_state.project_milestones = []

def load_goal_to_form(goal_id):
    """Load a goal into the form for editing.
    
    Args:
        goal_id (str): ID of the goal to load
    
    Returns:
        bool: True if loaded successfully, False otherwise
    """
    goal = load_goal(goal_id)
    if not goal:
        return False
    
    # Set common fields
    st.session_state.current_goal = goal
    st.session_state.goal_title = goal.get('title', '')
    st.session_state.goal_description = goal.get('description', '')
    st.session_state.goal_type = goal.get('goal_type', 'objective')
    st.session_state.goal_status = goal.get('status', 'active')
    
    # Convert date strings to date objects
    if goal.get('due_date'):
        try:
            st.session_state.goal_due_date = datetime.strptime(goal['due_date'], '%Y-%m-%d').date()
        except ValueError:
            st.session_state.goal_due_date = None
    
    if goal.get('start_date'):
        try:
            st.session_state.goal_start_date = datetime.strptime(goal['start_date'], '%Y-%m-%d').date()
        except ValueError:
            st.session_state.goal_start_date = datetime.now().date()
    
    # KPI-specific fields
    if goal.get('goal_type') == 'kpi':
        st.session_state.kpi_current_value = goal.get('current_value', 0)
        st.session_state.kpi_target_value = goal.get('target_value', 100)
        st.session_state.kpi_unit = goal.get('unit', '')
        st.session_state.kpi_comparison_type = goal.get('comparison_type', 'greater')
    
    # OKR linking
    st.session_state.linked_kpis = goal.get('linked_kpis', [])
    st.session_state.linked_objective = goal.get('linked_objective')
    
    # Project-specific fields
    if goal.get('goal_type') == 'project':
        st.session_state.project_team_members = goal.get('team_members', [])
        st.session_state.project_milestones = goal.get('milestones', [])
    
    return True

def collect_goal_form_data():
    """Collect goal data from session state.
    
    Returns:
        dict: Goal data from form
    """
    # Start with current goal data (if editing)
    goal_data = st.session_state.current_goal.copy() if st.session_state.current_goal else {}
    
    # Add common fields
    goal_data.update({
        'title': st.session_state.goal_title,
        'description': st.session_state.goal_description,
        'goal_type': st.session_state.goal_type,
        'status': st.session_state.goal_status,
        'start_date': st.session_state.goal_start_date.strftime('%Y-%m-%d') if st.session_state.goal_start_date else None,
        'due_date': st.session_state.goal_due_date.strftime('%Y-%m-%d') if st.session_state.goal_due_date else None,
        'updated_at': datetime.now().isoformat()
    })
    
    # Add type-specific fields
    if st.session_state.goal_type == 'kpi':
        goal_data.update({
            'current_value': st.session_state.kpi_current_value,
            'target_value': st.session_state.kpi_target_value,
            'unit': st.session_state.kpi_unit,
            'comparison_type': st.session_state.kpi_comparison_type,
            'linked_objective': st.session_state.linked_objective
        })
    
    elif st.session_state.goal_type == 'objective':
        goal_data.update({
            'linked_kpis': st.session_state.linked_kpis,
            'manual_progress': goal_data.get('manual_progress', 0)  # Preserve existing progress if any
        })
    
    elif st.session_state.goal_type == 'project':
        goal_data.update({
            'team_members': st.session_state.project_team_members,
            'milestones': st.session_state.project_milestones,
            'manual_progress': goal_data.get('manual_progress', 0)  # Preserve existing progress if any
        })
    
    return goal_data

def save_goal_from_form():
    """Save goal data from form to storage.
    
    Returns:
        str: Goal ID if saved successfully, None otherwise
    """
    goal_data = collect_goal_form_data()
    
    if not goal_data.get('title'):
        st.error('Please enter a title for the goal')
        return None
    
    return save_goal(goal_data)

def add_project_milestone():
    """Add an empty milestone to the project."""
    milestones = st.session_state.project_milestones.copy()
    milestones.append({
        'title': '',
        'due_date': None,
        'status': 'not_started'
    })
    st.session_state.project_milestones = milestones

def update_project_milestone(index, field, value):
    """Update a field in a project milestone.
    
    Args:
        index (int): Index of the milestone
        field (str): Field to update
        value: New value
    """
    milestones = st.session_state.project_milestones.copy()
    if 0 <= index < len(milestones):
        milestones[index][field] = value
        st.session_state.project_milestones = milestones

def remove_project_milestone(index):
    """Remove a milestone at the specified index.
    
    Args:
        index (int): Index of the milestone to remove
    """
    milestones = st.session_state.project_milestones.copy()
    if 0 <= index < len(milestones):
        milestones.pop(index)
        st.session_state.project_milestones = milestones
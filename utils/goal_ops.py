# utils/goal_ops.py
"""Goal and objective operations for the Weekly Report app."""

import json
import uuid
import os
from datetime import datetime
from pathlib import Path
import streamlit as st

def ensure_goals_directory():
    """Ensure the goals directory exists."""
    Path("data/goals").mkdir(parents=True, exist_ok=True)

def save_goal(goal_data):
    """Save goal data to a JSON file.
    
    Args:
        goal_data (dict): Goal data to save
        
    Returns:
        str: Goal ID
    """
    try:
        ensure_goals_directory()
        goal_id = goal_data.get('id', str(uuid.uuid4()))
        goal_data['id'] = goal_id
        
        # Add user_id from session state if authenticated
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            goal_data['user_id'] = st.session_state.user_info.get("id")
            
        # Add timestamp if not present
        if 'created_at' not in goal_data:
            goal_data['created_at'] = datetime.now().isoformat()
            
        goal_data['updated_at'] = datetime.now().isoformat()
        
        with open(f"data/goals/{goal_id}.json", 'w') as f:
            json.dump(goal_data, f, indent=2)
        
        return goal_id
    except Exception as e:
        st.error(f"Error saving goal: {str(e)}")
        return None

def load_goal(goal_id):
    """Load goal data from a JSON file.
    
    Args:
        goal_id (str): ID of the goal to load
        
    Returns:
        dict: Goal data or None if not found
    """
    try:
        with open(f"data/goals/{goal_id}.json", 'r') as f:
            goal_data = json.load(f)
            
        # Check if user has access to this goal
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            user_id = st.session_state.user_info.get("id")
            user_role = st.session_state.user_info.get("role")
            goal_user_id = goal_data.get("user_id")
            
            # Admin can access all goals
            if user_role == "admin":
                return goal_data
            
            # Managers can access their team members' goals
            if user_role == "manager":
                # For now, assume managers can see all goals
                # In a more sophisticated system, we'd check if the goal belongs to their team
                return goal_data
            
            # Normal users can only access their own goals
            if goal_user_id and goal_user_id != user_id:
                st.error("You don't have permission to access this goal.")
                return None
                
        return goal_data
    except FileNotFoundError:
        st.error(f"Goal with ID {goal_id} not found.")
        return None
    except json.JSONDecodeError:
        st.error(f"Invalid JSON in goal file {goal_id}.")
        return None
    except Exception as e:
        st.error(f"Error loading goal {goal_id}: {str(e)}")
        return None

def get_all_goals(filter_by_user=True):
    """Get a list of all saved goals.
    
    Args:
        filter_by_user (bool): If True, only return goals for the current user
    
    Returns:
        list: List of goal data dictionaries, sorted by updated timestamp (newest first)
    """
    try:
        ensure_goals_directory()
        goals = []
        
        # Get current user ID if authenticated
        current_user_id = None
        user_role = None
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            current_user_id = st.session_state.user_info.get("id")
            user_role = st.session_state.user_info.get("role")
        
        for file_path in Path("data/goals").glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    goal = json.load(f)
                    
                    # Filter by user if requested and not admin/manager
                    if filter_by_user and current_user_id and user_role != "admin":
                        goal_user_id = goal.get("user_id")
                        
                        # Managers can see all goals
                        if user_role == "manager":
                            goals.append(goal)
                        # Team members can only see their own goals
                        elif goal_user_id and goal_user_id == current_user_id:
                            goals.append(goal)
                    else:
                        goals.append(goal)
                        
            except Exception as e:
                st.warning(f"Error loading goal {file_path}: {str(e)}")
        
        return sorted(goals, key=lambda x: x.get('updated_at', ''), reverse=True)
    except Exception as e:
        st.error(f"Error retrieving goals: {str(e)}")
        return []

def delete_goal(goal_id):
    """Delete a goal file.
    
    Args:
        goal_id (str): ID of the goal to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        # Check if user has permission to delete this goal
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            try:
                with open(f"data/goals/{goal_id}.json", 'r') as f:
                    goal_data = json.load(f)
                
                user_id = st.session_state.user_info.get("id")
                user_role = st.session_state.user_info.get("role")
                goal_user_id = goal_data.get("user_id")
                
                # Only the goal owner, managers, and admins can delete
                if user_role not in ["admin", "manager"] and goal_user_id != user_id:
                    st.error("You don't have permission to delete this goal.")
                    return False
            except:
                # If we can't open the file, just try to delete it
                pass
        
        os.remove(f"data/goals/{goal_id}.json")
        return True
    except FileNotFoundError:
        st.error(f"Goal with ID {goal_id} not found.")
        return False
    except Exception as e:
        st.error(f"Error deleting goal {goal_id}: {str(e)}")
        return False

def get_goals_by_type(goal_type, filter_by_user=True):
    """Get goals filtered by type.
    
    Args:
        goal_type (str): Type of goals to filter by (objective, kpi, project)
        filter_by_user (bool): If True, only return goals for the current user
    
    Returns:
        list: List of goals of the specified type
    """
    all_goals = get_all_goals(filter_by_user)
    return [goal for goal in all_goals if goal.get('goal_type') == goal_type]

def get_linked_objectives(kpi_id):
    """Get objectives linked to a specific KPI.
    
    Args:
        kpi_id (str): ID of the KPI
    
    Returns:
        list: List of objectives linked to the KPI
    """
    objectives = get_goals_by_type('objective')
    return [obj for obj in objectives if kpi_id in obj.get('linked_kpis', [])]

def get_linked_kpis(objective_id):
    """Get KPIs linked to a specific objective.
    
    Args:
        objective_id (str): ID of the objective
    
    Returns:
        list: List of KPIs linked to the objective
    """
    objective = load_goal(objective_id)
    if not objective:
        return []
    
    linked_kpi_ids = objective.get('linked_kpis', [])
    kpis = []
    
    for kpi_id in linked_kpi_ids:
        kpi = load_goal(kpi_id)
        if kpi:
            kpis.append(kpi)
    
    return kpis

def calculate_goal_progress(goal_id):
    """Calculate the progress of a goal.
    
    Args:
        goal_id (str): ID of the goal
    
    Returns:
        float: Progress as a percentage (0-100)
    """
    goal = load_goal(goal_id)
    if not goal:
        return 0
    
    goal_type = goal.get('goal_type')
    
    if goal_type == 'kpi':
        # For KPIs, use the current value and target
        current = goal.get('current_value', 0)
        target = goal.get('target_value', 1)  # Avoid division by zero
        
        # Handle different comparison types
        comparison_type = goal.get('comparison_type', 'greater')
        if comparison_type == 'greater':
            # Higher is better
            return min(100, max(0, (current / target) * 100)) if target != 0 else 0
        elif comparison_type == 'less':
            # Lower is better
            return min(100, max(0, (target / current) * 100)) if current != 0 else 100
        else:
            # Exact match
            return 100 if current == target else 0
    
    elif goal_type == 'objective':
        # For objectives, average the progress of linked KPIs
        linked_kpis = get_linked_kpis(goal_id)
        if not linked_kpis:
            # Use manual progress if no KPIs are linked
            return goal.get('manual_progress', 0)
        
        total_progress = sum(calculate_goal_progress(kpi.get('id')) for kpi in linked_kpis)
        return total_progress / len(linked_kpis)
    
    elif goal_type == 'project':
        # For projects, use manual progress
        return goal.get('manual_progress', 0)
    
    return 0
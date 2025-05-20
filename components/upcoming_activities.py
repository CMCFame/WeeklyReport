# components/upcoming_activities.py - Updated with unique keys
"""Upcoming activities component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
import time  # Import time for unique keys
from utils import session
from utils.constants import PRIORITY_OPTIONS
from utils.csv_utils import get_user_projects, get_project_milestones

def render_upcoming_activities():
    """Render the upcoming activities section.
    
    This section allows users to add, edit, and remove planned future activities
    with details like project, milestone, priority and expected start date.
    """
    st.header('📅 Upcoming Activities')
    st.write('What activities are planned for the near future? Include expected start date.')
    
    # Generate unique timestamp for keys
    timestamp = int(time.time() * 1000)
    
    # Handle empty state - add a default activity if none exist
    if not st.session_state.upcoming_activities:
        if st.button('+ Add First Upcoming Activity', 
                    use_container_width=True, 
                    key=f"add_first_upcoming_{timestamp}"):  # Added unique key
            session.add_upcoming_activity()
            st.rerun()
        return
    
    # Render existing activities
    for i, activity in enumerate(st.session_state.upcoming_activities):
        # Generate unique timestamp for each activity
        activity_timestamp = int(time.time() * 1000) + i
        
        activity_title = activity.get('description', '')[:30]
        activity_title = f"{activity_title}..." if activity_title else "New Upcoming Activity"
        
        with st.expander(f"Upcoming Activity {i+1}: {activity_title}", expanded=i==0):
            render_upcoming_activity_form(i, activity, activity_timestamp)
    
    # Add activity button - with unique key
    if st.button('+ Add Another Upcoming Activity', 
                use_container_width=True, 
                key=f"add_more_upcoming_{timestamp}"):  # Added unique key
        session.add_upcoming_activity()
        st.rerun()

def render_upcoming_activity_form(index, activity, timestamp_base):
    """Render form fields for an upcoming activity."""
    # Get username for project filtering
    username = ""
    if st.session_state.get("user_info"):
        username = st.session_state.user_info.get("username", "")
    
    # First row: Project and Milestone
    col_proj, col_mile = st.columns(2)
    
    with col_proj:
        # Get available projects for the user
        available_projects = get_user_projects(username)
        
        # Current value
        current_project = activity.get('project', '')
        
        # If current value not in available projects, add it to avoid errors
        if current_project and current_project not in available_projects:
            available_projects.append(current_project)
        
        # Empty option first
        if not available_projects or available_projects[0] != '':
            available_projects = [''] + available_projects
            
        # Project selection - with unique key
        project = st.selectbox(
            'Project', 
            options=available_projects,
            index=available_projects.index(current_project) if current_project in available_projects else 0,
            key=f"up_proj_{index}_{timestamp_base}",  # Updated key to be unique
            help="Select the project for this upcoming activity"
        )
        session.update_upcoming_activity(index, 'project', project)
    
    with col_mile:
        # Get available milestones for the selected project
        available_milestones = get_project_milestones(activity.get('project', ''))
        
        # Current value
        current_milestone = activity.get('milestone', '')
        
        # If current value not in available milestones, add it to avoid errors
        if current_milestone and current_milestone not in available_milestones:
            available_milestones.append(current_milestone)
        
        # Empty option first
        if not available_milestones or available_milestones[0] != '':
            available_milestones = [''] + available_milestones
            
        # Milestone selection - with unique key
        milestone = st.selectbox(
            'Milestone', 
            options=available_milestones,
            index=available_milestones.index(current_milestone) if current_milestone in available_milestones else 0,
            key=f"up_mile_{index}_{timestamp_base}",  # Updated key to be unique
            help="Select the milestone for this upcoming activity"
        )
        session.update_upcoming_activity(index, 'milestone', milestone)
    
    # Second row: Priority and Expected Start
    col1, col2 = st.columns(2)
    
    with col1:
        priority = st.selectbox(
            'Priority', 
            options=PRIORITY_OPTIONS, 
            index=PRIORITY_OPTIONS.index(activity.get('priority', 'Medium')) if activity.get('priority') in PRIORITY_OPTIONS else 1,
            key=f"up_prio_{index}_{timestamp_base}"  # Updated key to be unique
        )
        session.update_upcoming_activity(index, 'priority', priority)
    
    with col2:
        # Handle date conversion for expected start
        expected_start_date = None
        expected_start = activity.get('expected_start', session.get_next_monday())
        
        if expected_start:
            try:
                expected_start_date = datetime.strptime(expected_start, '%Y-%m-%d').date()
            except ValueError:
                expected_start_date = None
        
        start_date = st.date_input(
            'Expected Start', 
            value=expected_start_date,
            key=f"up_start_{index}_{timestamp_base}"  # Updated key to be unique
        )
        session.update_upcoming_activity(index, 'expected_start', start_date.strftime('%Y-%m-%d'))
    
    # Description
    description = st.text_area(
        'Description', 
        value=activity.get('description', ''), 
        key=f"up_desc_{index}_{timestamp_base}",  # Updated key to be unique
        height=100
    )
    session.update_upcoming_activity(index, 'description', description)
    
    # Remove button - with unique key
    if st.button('Remove Activity', 
                key=f"remove_up_{index}_{timestamp_base}"):  # Updated key to be unique
        session.remove_upcoming_activity(index)
        st.rerun()
# components/upcoming_activities.py
"""Upcoming activities component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
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
    
    # Handle empty state - add a default activity if none exist
    if not st.session_state.upcoming_activities:
        if st.button('+ Add First Upcoming Activity', use_container_width=True):
            session.add_upcoming_activity()
            st.rerun()
        return
    
    # Render existing activities
    for i, activity in enumerate(st.session_state.upcoming_activities):
        activity_title = activity.get('description', '')[:30]
        activity_title = f"{activity_title}..." if activity_title else "New Upcoming Activity"
        
        with st.expander(f"Upcoming Activity {i+1}: {activity_title}", expanded=i==0):
            render_upcoming_activity_form(i, activity)
    
    # Add activity button
    if st.button('+ Add Another Upcoming Activity', use_container_width=True):
        session.add_upcoming_activity()
        st.rerun()

def render_upcoming_activity_form(index, activity):
    """Render form fields for an upcoming activity.
    
    Args:
        index (int): Activity index in the session state
        activity (dict): Activity data
    """
    # Get username for project filtering
    username = ""
    if st.session_state.get("user_info"):
        username = st.session_state.user_info.get("username", "")
    
    # Description (always shown)
    description = st.text_area(
        'Description', 
        value=activity.get('description', ''), 
        key=f"up_desc_{index}",
        height=100,
        help="Describe what you're planning to work on"
    )
    session.update_upcoming_activity(index, 'description', description)
    
    # First row: Project and Milestone (essential information)
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
            
        # Project selection
        project = st.selectbox(
            'Project', 
            options=available_projects,
            index=available_projects.index(current_project) if current_project in available_projects else 0,
            key=f"up_proj_{index}",
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
            
        # Milestone selection
        milestone = st.selectbox(
            'Milestone', 
            options=available_milestones,
            index=available_milestones.index(current_milestone) if current_milestone in available_milestones else 0,
            key=f"up_mile_{index}",
            help="Select the milestone for this upcoming activity"
        )
        session.update_upcoming_activity(index, 'milestone', milestone)
    
    # Second row: Priority (essential information)
    priority = st.selectbox(
        'Priority', 
        options=PRIORITY_OPTIONS, 
        index=PRIORITY_OPTIONS.index(activity.get('priority', 'Medium')) if activity.get('priority') in PRIORITY_OPTIONS else 1,
        key=f"up_prio_{index}"
    )
    session.update_upcoming_activity(index, 'priority', priority)
    
    # Show advanced options toggle for progressive disclosure
    if 'show_advanced_options' not in activity:
        activity['show_advanced_options'] = False
    
    show_advanced = st.checkbox(
        'Show advanced options',
        value=activity.get('show_advanced_options', False),
        key=f"up_show_adv_{index}"
    )
    session.update_upcoming_activity(index, 'show_advanced_options', show_advanced)
    
    # Advanced options (shown only if toggle is on)
    if show_advanced:
        st.write("#### Expected Start Date")
        
        # Handle date conversion for expected start
        expected_start_date = None
        expected_start = activity.get('expected_start', session.get_next_monday())
        
        if expected_start:
            try:
                expected_start_date = datetime.strptime(expected_start, '%Y-%m-%d').date()
            except ValueError:
                expected_start_date = None
        
        # Option to set a start date
        has_start_date = st.checkbox(
            'Set a start date',
            value=activity.get('has_start_date', True),
            key=f"up_has_start_{index}"
        )
        session.update_upcoming_activity(index, 'has_start_date', has_start_date)
        
        if has_start_date:
            start_date = st.date_input(
                'Expected Start', 
                value=expected_start_date,
                key=f"up_start_{index}"
            )
            session.update_upcoming_activity(index, 'expected_start', start_date.strftime('%Y-%m-%d'))
        
        # Recurrence options
        st.write("#### Recurrence")
        is_recurring = st.checkbox(
            'This is a recurring activity',
            value=activity.get('is_recurring', False),
            key=f"up_is_recurring_{index}"
        )
        session.update_upcoming_activity(index, 'is_recurring', is_recurring)
        
        if is_recurring:
            recurrence_options = ["Daily", "Weekly", "Monthly"]
            recurrence = st.selectbox(
                'Recurrence Pattern',
                options=recurrence_options,
                index=recurrence_options.index(activity.get('recurrence', 'Weekly')) if activity.get('recurrence') in recurrence_options else 1,
                key=f"up_recurrence_{index}"
            )
            session.update_upcoming_activity(index, 'recurrence', recurrence)
    
    # Remove button
    st.divider()
    if st.button('Remove Activity', key=f"remove_up_{index}"):
        session.remove_upcoming_activity(index)
        st.rerun()
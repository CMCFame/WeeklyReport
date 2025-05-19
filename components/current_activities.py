# components/current_activities.py
"""Current activities component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
from utils import session
from utils.constants import PRIORITY_OPTIONS, STATUS_OPTIONS, BILLABLE_OPTIONS
from utils.csv_utils import get_user_projects, get_project_milestones

def render_current_activities():
    """Render the current activities section.
    
    This section allows users to add, edit, and remove current work activities
    with details like project, milestone, priority, status, customer, etc.
    """
    st.header('📊 Current Activities')
    st.write('What are you currently working on? Include priority and status.')
    
    # Handle empty state - add a default activity if none exist
    if not st.session_state.current_activities:
        if st.button('+ Add First Activity', use_container_width=True):
            session.add_current_activity()
            st.rerun()
        return
    
    # Render existing activities
    for i, activity in enumerate(st.session_state.current_activities):
        activity_title = activity.get('description', '')[:30] 
        activity_title = f"{activity_title}..." if activity_title else "New Activity"
        
        with st.expander(f"Activity {i+1}: {activity_title}", expanded=i==0):
            render_current_activity_form(i, activity)
    
    # Add activity button
    if st.button('+ Add Another Activity', use_container_width=True):
        session.add_current_activity()
        st.rerun()

def render_current_activity_form(index, activity):
    """Render form fields for a current activity."""
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
            
        # Project selection
        project = st.selectbox(
            'Project', 
            options=available_projects,
            index=available_projects.index(current_project) if current_project in available_projects else 0,
            key=f"curr_proj_{index}",
            help="Select the project for this activity"
        )
        session.update_current_activity(index, 'project', project)
    
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
            key=f"curr_mile_{index}",
            help="Select the milestone for this activity"
        )
        session.update_current_activity(index, 'milestone', milestone)
    
    # Second row: Priority, Status, Customer, Billable
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        priority = st.selectbox(
            'Priority', 
            options=PRIORITY_OPTIONS, 
            index=PRIORITY_OPTIONS.index(activity.get('priority', 'Medium')) if activity.get('priority') in PRIORITY_OPTIONS else 1,
            key=f"curr_prio_{index}"
        )
        session.update_current_activity(index, 'priority', priority)
    
    with col2:
        status = st.selectbox(
            'Status', 
            options=STATUS_OPTIONS, 
            index=STATUS_OPTIONS.index(activity.get('status', 'In Progress')) if activity.get('status') in STATUS_OPTIONS else 1,
            key=f"curr_status_{index}"
        )
        session.update_current_activity(index, 'status', status)
    
    with col3:
        customer = st.text_input(
            'Customer', 
            value=activity.get('customer', ''), 
            key=f"curr_cust_{index}",
            help="Client or internal team this work is for"
        )
        session.update_current_activity(index, 'customer', customer)
    
    with col4:
        billable = st.selectbox(
            'Billable', 
            options=BILLABLE_OPTIONS, 
            index=BILLABLE_OPTIONS.index(activity.get('billable', '')) if activity.get('billable') in BILLABLE_OPTIONS else 0,
            key=f"curr_bill_{index}"
        )
        session.update_current_activity(index, 'billable', billable)
    
    # Third row: Recurrence, Deadline, Progress
    col5, col6, col7 = st.columns(3)
    
    with col5:
        # Add recurrence option
        recurrence_options = ["", "Daily", "Weekly", "Monthly"]
        recurrence = st.selectbox(
            'Recurrence',
            options=recurrence_options,
            index=recurrence_options.index(activity.get('recurrence', '')) if activity.get('recurrence') in recurrence_options else 0,
            key=f"curr_recur_{index}",
            help="Select if this is a recurring activity"
        )
        session.update_current_activity(index, 'recurrence', recurrence)
    
    with col6:
        # Only show deadline if not recurring
        if not recurrence:
            # Handle date conversion
            deadline_date = None
            if activity.get('deadline'):
                try:
                    deadline_date = datetime.strptime(activity['deadline'], '%Y-%m-%d').date()
                except ValueError:
                    deadline_date = None
            
            deadline = st.date_input(
                'Deadline', 
                value=deadline_date,
                key=f"curr_dead_{index}"
            )
            session.update_current_activity(index, 'deadline', deadline.strftime('%Y-%m-%d') if deadline else '')
        else:
            # Clear deadline if recurring
            session.update_current_activity(index, 'deadline', '')
            st.write("")
    
    with col7:
        # Allow entering progress directly or using slider
        st.write("Progress:")
        progress_col1, progress_col2 = st.columns([3, 1])
        
        with progress_col1:
            # Slider for progress
            progress_slider = st.slider(
                'Progress Slider', 
                min_value=0, 
                max_value=100, 
                value=activity.get('progress', 50), 
                key=f"curr_prog_slider_{index}",
                label_visibility="collapsed"
            )
        
        with progress_col2:
            # Text input for progress
            progress_text = st.number_input(
                'Progress %',
                min_value=0,
                max_value=100,
                value=activity.get('progress', 50),
                key=f"curr_prog_text_{index}",
                label_visibility="collapsed"
            )
        
        # Use the most recently changed input (slider or text)
        if f"curr_prog_slider_{index}" in st.session_state and f"curr_prog_text_{index}" in st.session_state:
            # Check which widget was most recently changed
            if st.session_state[f"curr_prog_slider_{index}"] != activity.get('progress', 50):
                progress = progress_slider
            else:
                progress = progress_text
        else:
            # Default to text input value
            progress = progress_text
            
        session.update_current_activity(index, 'progress', progress)
    
    # Description
    description = st.text_area(
        'Description', 
        value=activity.get('description', ''), 
        key=f"curr_desc_{index}",
        height=100
    )
    session.update_current_activity(index, 'description', description)
    
    # Remove button
    if st.button('Remove Activity', key=f"remove_curr_{index}"):
        session.remove_current_activity(index)
        st.rerun()
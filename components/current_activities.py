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
    """Render form fields for a current activity with progressive disclosure."""
    # Get username for project filtering
    username = ""
    if st.session_state.get("user_info"):
        username = st.session_state.user_info.get("username", "")
    
    # First, get the essential details
    col_desc, col_expand = st.columns([5, 1])
    
    with col_desc:
        description = st.text_area(
            'Description', 
            value=activity.get('description', ''), 
            key=f"curr_desc_{index}",
            height=80
        )
        session.update_current_activity(index, 'description', description)
    
    with col_expand:
        # Create a session state key for this activity's expanded state
        expand_key = f"expand_activity_{index}"
        if expand_key not in st.session_state:
            st.session_state[expand_key] = False
            
        if st.button('Details ▼' if not st.session_state[expand_key] else 'Details ▲', key=f"expand_btn_{index}"):
            st.session_state[expand_key] = not st.session_state[expand_key]
    
    # Only show additional fields if expanded
    if st.session_state[expand_key]:
        # Project and Milestone
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
        
        # Priority, Status, Customer, Billable
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
        
        # Third row: Deadline toggle, Progress input
        col5, col6 = st.columns(2)
        
        with col5:
            # Add deadline toggle
            deadline_key = f"curr_deadline_enabled_{index}"
            if deadline_key not in st.session_state:
                st.session_state[deadline_key] = bool(activity.get('deadline', ''))
            
            deadline_enabled = st.checkbox('Set Deadline', value=st.session_state[deadline_key], key=deadline_key)
            st.session_state[deadline_key] = deadline_enabled
            
            # Show date picker only if deadline is enabled
            if deadline_enabled:
                # Handle date conversion
                deadline_date = None
                if activity.get('deadline'):
                    try:
                        deadline_date = datetime.strptime(activity['deadline'], '%Y-%m-%d').date()
                    except ValueError:
                        deadline_date = None
                
                deadline = st.date_input(
                    'Deadline Date', 
                    value=deadline_date,
                    key=f"curr_dead_{index}"
                )
                session.update_current_activity(index, 'deadline', deadline.strftime('%Y-%m-%d') if deadline else '')
            else:
                # Clear deadline if disabled
                session.update_current_activity(index, 'deadline', '')
        
        with col6:
            # Add option to type % completion directly
            col_slider, col_input = st.columns([3, 1])
            
            with col_slider:
                progress = st.slider(
                    '% Complete', 
                    min_value=0, 
                    max_value=100, 
                    value=activity.get('progress', 50), 
                    key=f"curr_prog_slider_{index}"
                )
            
            with col_input:
                # Allow direct input of percentage
                progress_input = st.number_input(
                    'Enter %', 
                    min_value=0, 
                    max_value=100, 
                    value=activity.get('progress', 50),
                    key=f"curr_prog_input_{index}"
                )
                
                # Synchronize the two inputs (whichever was last changed)
                if progress != activity.get('progress', 50):
                    progress_input = progress
                else:
                    progress = progress_input
                
            session.update_current_activity(index, 'progress', progress_input)
        
        # Recurrence settings
        recurrence_key = f"curr_recurrence_enabled_{index}"
        if recurrence_key not in st.session_state:
            st.session_state[recurrence_key] = activity.get('is_recurring', False)
        
        is_recurring = st.checkbox('Recurring Activity', value=st.session_state[recurrence_key], key=recurrence_key)
        session.update_current_activity(index, 'is_recurring', is_recurring)
        
        # Show recurrence options if enabled
        if is_recurring:
            recurrence_options = ["Daily", "Weekly", "Monthly"]
            current_recurrence = activity.get('recurrence_type', 'Weekly')
            recurrence_index = recurrence_options.index(current_recurrence) if current_recurrence in recurrence_options else 1
            
            recurrence_type = st.selectbox(
                'Recurrence Pattern',
                options=recurrence_options,
                index=recurrence_index,
                key=f"curr_recurrence_type_{index}"
            )
            session.update_current_activity(index, 'recurrence_type', recurrence_type)
    
    # Remove button - always visible
    if st.button('Remove Activity', key=f"remove_curr_{index}"):
        session.remove_current_activity(index)
        st.rerun()
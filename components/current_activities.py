# components/current_activities.py
"""Current activities component for the Weekly Report app with progressive disclosure."""

import streamlit as st
from datetime import datetime
from utils import session
from utils.constants import PRIORITY_OPTIONS, STATUS_OPTIONS, BILLABLE_OPTIONS
from utils.csv_utils import get_user_projects, get_project_milestones

def render_current_activities():
    """Render the current activities section with progressive disclosure."""
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
        
        # Create a container for each activity instead of an expander
        with st.container():
            st.subheader(f"Activity {i+1}: {activity_title}")
            
            # Track if we should show additional details for this activity
            show_details_key = f"show_details_{i}"
            if show_details_key not in st.session_state:
                st.session_state[show_details_key] = False
                
            # Render the activity form
            render_current_activity_form(i, activity, st.session_state[show_details_key])
            
            # Toggle button for additional details
            if st.session_state[show_details_key]:
                if st.button("Hide Additional Details", key=f"hide_details_{i}"):
                    st.session_state[show_details_key] = False
                    st.rerun()
            else:
                if st.button("Show Additional Details", key=f"show_details_{i}"):
                    st.session_state[show_details_key] = True
                    st.rerun()
                    
            st.divider()  # Add a divider between activities
    
    # Add activity button
    if st.button('+ Add Another Activity', use_container_width=True):
        session.add_current_activity()
        st.rerun()

def render_current_activity_form(index, activity, show_additional_details=False):
    """Render form fields for a current activity with progressive disclosure.
    
    Args:
        index (int): Activity index
        activity (dict): Activity data
        show_additional_details (bool): Whether to show additional details
    """
    # Get username for project filtering
    username = ""
    if st.session_state.get("user_info"):
        username = st.session_state.user_info.get("username", "")
    
    # Essential Fields Section (always visible)
    # -------------------------------------------
    
    # Description - most important field first
    description = st.text_area(
        'Description', 
        value=activity.get('description', ''), 
        key=f"curr_desc_{index}",
        height=100
    )
    session.update_current_activity(index, 'description', description)
    
    # First row: Project, Priority, Status
    col_essential1, col_essential2, col_essential3 = st.columns(3)
    
    with col_essential1:
        # Project selection
        available_projects = get_user_projects(username)
        current_project = activity.get('project', '')
        
        # If current value not in available projects, add it
        if current_project and current_project not in available_projects:
            available_projects.append(current_project)
        
        # Empty option first
        if not available_projects or available_projects[0] != '':
            available_projects = [''] + available_projects
            
        project = st.selectbox(
            'Project', 
            options=available_projects,
            index=available_projects.index(current_project) if current_project in available_projects else 0,
            key=f"curr_proj_{index}"
        )
        session.update_current_activity(index, 'project', project)
    
    with col_essential2:
        priority = st.selectbox(
            'Priority', 
            options=PRIORITY_OPTIONS, 
            index=PRIORITY_OPTIONS.index(activity.get('priority', 'Medium')) if activity.get('priority') in PRIORITY_OPTIONS else 1,
            key=f"curr_prio_{index}"
        )
        session.update_current_activity(index, 'priority', priority)
    
    with col_essential3:
        status = st.selectbox(
            'Status', 
            options=STATUS_OPTIONS, 
            index=STATUS_OPTIONS.index(activity.get('status', 'In Progress')) if activity.get('status') in STATUS_OPTIONS else 1,
            key=f"curr_status_{index}"
        )
        session.update_current_activity(index, 'status', status)
    
    # Progress slider - always visible
    st.write("Progress:")
    progress_col1, progress_col2 = st.columns([4, 1])
    
    with progress_col1:
        progress = st.slider(
            'Progress', 
            min_value=0, 
            max_value=100, 
            value=activity.get('progress', 50), 
            key=f"curr_prog_slider_{index}",
            label_visibility="collapsed"
        )
    
    with progress_col2:
        st.metric("", f"{progress}%", label_visibility="collapsed")
    
    session.update_current_activity(index, 'progress', progress)
    
    # Advanced Fields Section (shown only when requested)
    # -------------------------------------------------
    if show_additional_details:
        st.markdown("### Additional Details")
        
        # First row of additional details: Milestone and Customer
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            # Get available milestones for the selected project
            available_milestones = get_project_milestones(activity.get('project', ''))
            current_milestone = activity.get('milestone', '')
            
            # If current value not in available milestones, add it
            if current_milestone and current_milestone not in available_milestones:
                available_milestones.append(current_milestone)
            
            # Empty option first
            if not available_milestones or available_milestones[0] != '':
                available_milestones = [''] + available_milestones
                
            milestone = st.selectbox(
                'Milestone', 
                options=available_milestones,
                index=available_milestones.index(current_milestone) if current_milestone in available_milestones else 0,
                key=f"curr_mile_{index}"
            )
            session.update_current_activity(index, 'milestone', milestone)
        
        with col_adv2:
            customer = st.text_input(
                'Customer', 
                value=activity.get('customer', ''), 
                key=f"curr_cust_{index}",
                help="Client or internal team this work is for"
            )
            session.update_current_activity(index, 'customer', customer)
        
        # Second row of additional details: Recurrence and Billable
        col_adv3, col_adv4 = st.columns(2)
        
        with col_adv3:
            recurrence_options = ["", "Daily", "Weekly", "Monthly"]
            recurrence = st.selectbox(
                'Recurrence',
                options=recurrence_options,
                index=recurrence_options.index(activity.get('recurrence', '')) if activity.get('recurrence') in recurrence_options else 0,
                key=f"curr_recur_{index}",
                help="Select if this is a recurring activity"
            )
            session.update_current_activity(index, 'recurrence', recurrence)
        
        with col_adv4:
            billable = st.selectbox(
                'Billable', 
                options=BILLABLE_OPTIONS, 
                index=BILLABLE_OPTIONS.index(activity.get('billable', '')) if activity.get('billable') in BILLABLE_OPTIONS else 0,
                key=f"curr_bill_{index}"
            )
            session.update_current_activity(index, 'billable', billable)
        
        # Third row: Deadline (only if not recurring)
        if not recurrence:
            # Handle date conversion
            deadline_date = None
            if activity.get('deadline'):
                try:
                    deadline_date = datetime.strptime(activity['deadline'], '%Y-%m-%d').date()
                except ValueError:
                    deadline_date = None
            
            deadline = st.date_input(
                'Deadline (Optional)', 
                value=deadline_date,
                key=f"curr_dead_{index}"
            )
            session.update_current_activity(index, 'deadline', deadline.strftime('%Y-%m-%d') if deadline else '')
        else:
            # Clear deadline if recurring
            session.update_current_activity(index, 'deadline', '')
            st.write("No deadline for recurring activities")
    
    # Remove button
    if st.button('Remove Activity', key=f"remove_curr_{index}"):
        session.remove_current_activity(index)
        st.rerun()
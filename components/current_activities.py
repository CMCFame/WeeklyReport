# components/current_activities.py
"""Current activities component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
from utils import session
from utils.constants import PRIORITY_OPTIONS, STATUS_OPTIONS, BILLABLE_OPTIONS

def render_current_activities():
    """Render the current activities section.
    
    This section allows users to add, edit, and remove current work activities
    with details like priority, status, customer, etc.
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
    # First row: Priority, Status, Customer, Billable
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
    
    # Second row: Deadline, Progress
    col5, col6 = st.columns(2)
    
    with col5:
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
    
    with col6:
        progress = st.slider(
            '% Complete', 
            min_value=0, 
            max_value=100, 
            value=activity.get('progress', 50), 
            key=f"curr_prog_{index}"
        )
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
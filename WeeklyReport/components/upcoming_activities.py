# components/upcoming_activities.py
"""Upcoming activities component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
from utils import session
from utils.constants import PRIORITY_OPTIONS

def render_upcoming_activities():
    """Render the upcoming activities section.
    
    This section allows users to add, edit, and remove planned future activities
    with details like priority and expected start date.
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
    """Render form fields for an upcoming activity."""
    # Priority and Expected Start
    col1, col2 = st.columns(2)
    
    with col1:
        priority = st.selectbox(
            'Priority', 
            options=PRIORITY_OPTIONS, 
            index=PRIORITY_OPTIONS.index(activity.get('priority', 'Medium')) if activity.get('priority') in PRIORITY_OPTIONS else 1,
            key=f"up_prio_{index}"
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
            key=f"up_start_{index}"
        )
        session.update_upcoming_activity(index, 'expected_start', start_date.strftime('%Y-%m-%d'))
    
    # Description
    description = st.text_area(
        'Description', 
        value=activity.get('description', ''), 
        key=f"up_desc_{index}",
        height=100
    )
    session.update_upcoming_activity(index, 'description', description)
    
    # Remove button
    if st.button('Remove Activity', key=f"remove_up_{index}"):
        session.remove_upcoming_activity(index)
        st.rerun()
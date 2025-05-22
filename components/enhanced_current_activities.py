# components/enhanced_current_activities.py
"""Enhanced current activities component with ASDF phase tracking for tactical management visibility."""

import streamlit as st
from datetime import datetime
from utils import session
from utils.constants import (
    PRIORITY_OPTIONS, STATUS_OPTIONS, BILLABLE_OPTIONS, 
    ASDF_PHASES, ASDF_PHASE_DESCRIPTIONS, ASDF_PHASE_COLORS
)
from utils.csv_utils import get_user_projects, get_project_milestones

def render_enhanced_current_activities():
    """Render the enhanced current activities section with ASDF phase tracking."""
    st.header('📊 Current Activities')
    st.write('What are you currently working on? Include priority, status, and project phase.')
    
    # Handle empty state - add a default activity if none exist
    if not st.session_state.current_activities:
        if st.button('+ Add First Activity', use_container_width=True):
            session.add_current_activity()
            st.rerun()
        return
    
    # Show ASDF Phase Distribution (Tactical Management View)
    if len(st.session_state.current_activities) > 1:
        render_phase_distribution_preview()
    
    # Render existing activities
    for i, activity in enumerate(st.session_state.current_activities):
        activity_title = activity.get('description', '')[:30] 
        activity_phase = activity.get('asdf_phase', '')
        phase_indicator = f"[{activity_phase}] " if activity_phase else ""
        activity_title = f"{phase_indicator}{activity_title}..." if activity_title else "New Activity"
        
        # Color-code the expander based on ASDF phase
        phase_color = ASDF_PHASE_COLORS.get(activity_phase, "#f8f9fa")
        
        with st.expander(f"Activity {i+1}: {activity_title}", expanded=i==0):
            # Add subtle phase indicator
            if activity_phase:
                st.markdown(
                    f'<div style="background-color: {phase_color}; padding: 4px 8px; border-radius: 4px; '
                    f'margin-bottom: 10px; font-size: 12px; color: #333;">'
                    f'📋 ASDF Phase: {activity_phase}</div>',
                    unsafe_allow_html=True
                )
            
            render_enhanced_current_activity_form(i, activity)
    
    # Add activity button
    if st.button('+ Add Another Activity', use_container_width=True):
        session.add_current_activity()
        st.rerun()

def render_phase_distribution_preview():
    """Show a quick visual preview of ASDF phase distribution for management insights."""
    st.subheader("📈 Project Phase Overview")
    
    # Count activities by phase
    phase_counts = {}
    for activity in st.session_state.current_activities:
        phase = activity.get('asdf_phase', 'Unspecified')
        if not phase:
            phase = 'Unspecified'
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
    
    # Create columns for phase indicators
    cols = st.columns(len(ASDF_PHASES) if len(ASDF_PHASES) <= 6 else 6)
    
    for i, phase in enumerate(ASDF_PHASES):
        if i < len(cols):
            with cols[i]:
                count = phase_counts.get(phase, 0)
                phase_name = phase if phase else "Unspecified"
                color = ASDF_PHASE_COLORS.get(phase, "#f8f9fa")
                
                # Create a mini metric card
                st.markdown(
                    f'<div style="background-color: {color}; padding: 8px; border-radius: 6px; '
                    f'text-align: center; margin-bottom: 5px;">'
                    f'<div style="font-size: 16px; font-weight: bold; color: #333;">{count}</div>'
                    f'<div style="font-size: 10px; color: #666;">{phase_name}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

def render_enhanced_current_activity_form(index, activity):
    """Render form fields for a current activity with ASDF phase tracking."""
    # Get username for project filtering
    username = ""
    if st.session_state.get("user_info"):
        username = st.session_state.user_info.get("username", "")
    
    # First row: Project, Milestone, and ASDF Phase
    col_proj, col_mile, col_phase = st.columns(3)
    
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
    
    with col_phase:
        # ASDF Phase selection - The key tactical addition
        current_phase = activity.get('asdf_phase', '')
        
        phase_index = 0
        if current_phase in ASDF_PHASES:
            phase_index = ASDF_PHASES.index(current_phase)
        
        asdf_phase = st.selectbox(
            'ASDF Phase',
            options=ASDF_PHASES,
            index=phase_index,
            key=f"curr_phase_{index}",
            help="Select the ASDF project phase - helps management track project lifecycle",
            format_func=lambda x: f"{x}" if x else "Not specified"
        )
        session.update_current_activity(index, 'asdf_phase', asdf_phase)
        
        # Show phase description if selected
        if asdf_phase and asdf_phase in ASDF_PHASE_DESCRIPTIONS:
            st.caption(f"💡 {ASDF_PHASE_DESCRIPTIONS[asdf_phase]}")
    
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
    
    # Third row: Deadline and Progress
    col5, col6 = st.columns(2)
    
    with col5:
        # Initialize has_deadline field if not present
        if 'has_deadline' not in activity:
            activity['has_deadline'] = bool(activity.get('deadline', ''))
            
        has_deadline = st.checkbox(
            'Has Deadline',
            value=activity.get('has_deadline', False),
            key=f"curr_has_deadline_{index}",
            help="Check if this activity has a deadline"
        )
        session.update_current_activity(index, 'has_deadline', has_deadline)
        
        if has_deadline:
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
            # Clear deadline if checkbox is unchecked
            session.update_current_activity(index, 'deadline', '')
    
    with col6:
        # Progress with both slider and number input
        st.write("Progress")
        progress_cols = st.columns([3, 1])
        
        # Get current progress
        current_progress = activity.get('progress', 50)
        
        with progress_cols[0]:
            progress_slider = st.slider(
                'Progress Slider',
                min_value=0,
                max_value=100,
                value=current_progress,
                key=f"curr_prog_slider_{index}",
                label_visibility="collapsed"
            )
        
        with progress_cols[1]:
            progress_number = st.number_input(
                'Progress %',
                min_value=0,
                max_value=100,
                value=progress_slider,
                step=1,
                key=f"curr_prog_num_{index}",
                label_visibility="collapsed"
            )
        
        # Sync progress between slider and number input
        if progress_slider != progress_number:
            if st.session_state.get(f"curr_prog_num_{index}") != progress_slider:
                progress = progress_number
            else:
                progress = progress_slider
        else:
            progress = progress_slider
        
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
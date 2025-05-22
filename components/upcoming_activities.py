# components/upcoming_activities.py
"""Upcoming activities component for the Weekly Report app."""

import streamlit as st
from datetime import datetime
from utils import session
from utils.constants import PRIORITY_OPTIONS
from utils.csv_utils import get_user_projects, get_project_milestones

# components/upcoming_activities.py
"""Enhanced upcoming activities component with ASDF phase tracking."""

import streamlit as st
from datetime import datetime
from utils import session
from utils.constants import PRIORITY_OPTIONS, ASDF_PHASES, ASDF_PHASE_DESCRIPTIONS, ASDF_PHASE_COLORS
from utils.csv_utils import get_user_projects, get_project_milestones

def render_upcoming_activities():
    """Render the upcoming activities section with ASDF phase tracking."""
    st.header('📅 Upcoming Activities')
    st.write('What activities are planned for the near future? Include expected start date and project phase.')
    
    # Handle empty state - add a default activity if none exist
    if not st.session_state.upcoming_activities:
        if st.button('+ Add First Upcoming Activity', use_container_width=True):
            session.add_upcoming_activity()
            st.rerun()
        return
    
    # Show upcoming phase distribution preview
    if len(st.session_state.upcoming_activities) > 1:
        render_upcoming_phase_preview()
    
    # Render existing activities
    for i, activity in enumerate(st.session_state.upcoming_activities):
        activity_title = activity.get('description', '')[:30]
        activity_phase = activity.get('asdf_phase', '')
        phase_indicator = f"[{activity_phase}] " if activity_phase else ""
        activity_title = f"{phase_indicator}{activity_title}..." if activity_title else "New Upcoming Activity"
        
        with st.expander(f"Upcoming Activity {i+1}: {activity_title}", expanded=i==0):
            # Add phase indicator
            if activity_phase:
                phase_color = ASDF_PHASE_COLORS.get(activity_phase, "#f8f9fa")
                st.markdown(
                    f'<div style="background-color: {phase_color}; padding: 4px 8px; border-radius: 4px; '
                    f'margin-bottom: 10px; font-size: 12px; color: #333;">'
                    f'🔮 Planned Phase: {activity_phase}</div>',
                    unsafe_allow_html=True
                )
            
            render_upcoming_activity_form(i, activity)
    
    # Add activity button
    if st.button('+ Add Another Upcoming Activity', use_container_width=True):
        session.add_upcoming_activity()
        st.rerun()

def render_upcoming_phase_preview():
    """Show upcoming activities phase distribution."""
    st.subheader("🔮 Upcoming Pipeline Preview")
    
    # Count upcoming activities by phase
    phase_counts = {}
    for activity in st.session_state.upcoming_activities:
        phase = activity.get('asdf_phase', 'Unspecified')
        if not phase:
            phase = 'Unspecified'
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
    
    # Create mini preview cards
    cols = st.columns(min(len(phase_counts), 6))
    
    for i, (phase, count) in enumerate(phase_counts.items()):
        if i < len(cols):
            with cols[i]:
                color = ASDF_PHASE_COLORS.get(phase, "#f8f9fa")
                phase_name = phase if phase != 'Unspecified' else "TBD"
                
                st.markdown(
                    f'<div style="background-color: {color}; padding: 8px; border-radius: 6px; '
                    f'text-align: center; margin-bottom: 5px; border: 2px dashed #ccc;">'
                    f'<div style="font-size: 16px; font-weight: bold; color: #333;">{count}</div>'
                    f'<div style="font-size: 10px; color: #666;">Future {phase_name}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

def render_upcoming_activity_form(index, activity):
    """Render form fields for an upcoming activity with ASDF phase tracking."""
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
    
    with col_phase:
        # ASDF Phase selection for upcoming activities
        current_phase = activity.get('asdf_phase', '')
        
        phase_index = 0
        if current_phase in ASDF_PHASES:
            phase_index = ASDF_PHASES.index(current_phase)
        
        asdf_phase = st.selectbox(
            'ASDF Phase',
            options=ASDF_PHASES,
            index=phase_index,
            key=f"up_phase_{index}",
            help="Select the expected ASDF project phase for this upcoming activity",
            format_func=lambda x: f"{x}" if x else "Not specified"
        )
        session.update_upcoming_activity(index, 'asdf_phase', asdf_phase)
        
        # Show phase description if selected
        if asdf_phase and asdf_phase in ASDF_PHASE_DESCRIPTIONS:
            st.caption(f"💡 {ASDF_PHASE_DESCRIPTIONS[asdf_phase]}")
    
    # Second row: Priority and Expected Start
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
        height=100,
        help="Describe what this upcoming activity involves"
    )
    session.update_upcoming_activity(index, 'description', description)
    
    # ASDF Phase-specific guidance
    if asdf_phase:
        render_phase_specific_guidance(asdf_phase)
    
    # Remove button
    if st.button('Remove Activity', key=f"remove_up_{index}"):
        session.remove_upcoming_activity(index)
        st.rerun()

def render_phase_specific_guidance(phase):
    """Render phase-specific guidance and tips."""
    guidance_map = {
        "Qualification": {
            "icon": "🎯",
            "tips": [
                "Ensure BANT criteria are met (Budget, Authority, Need, Timeline)",
                "Schedule discovery calls with decision makers",
                "Prepare demo materials relevant to client needs"
            ]
        },
        "Scoping": {
            "icon": "🔍", 
            "tips": [
                "Schedule whiteboard session with technical stakeholders",
                "Prepare current state analysis questions",
                "Plan ROM (Rough Order of Magnitude) development"
            ]
        },
        "Initiation": {
            "icon": "🚀",
            "tips": [
                "Coordinate team onboarding sessions",
                "Prepare project kickoff materials",
                "Schedule customer logistics calls"
            ]
        },
        "Delivery": {
            "icon": "⚡",
            "tips": [
                "Review project plan and milestones",
                "Confirm resource availability",
                "Prepare deliverable review sessions"
            ]
        },
        "Support": {
            "icon": "🛠️",
            "tips": [
                "Plan transition documentation",
                "Schedule knowledge transfer sessions",
                "Prepare ongoing support procedures"
            ]
        }
    }
    
    if phase in guidance_map:
        guidance = guidance_map[phase]
        
        with st.expander(f"{guidance['icon']} {phase} Phase Tips", expanded=False):
            st.write("**Recommended preparation activities:**")
            for tip in guidance['tips']:
                st.write(f"• {tip}")
    
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
    
    # Second row: Priority and Expected Start
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
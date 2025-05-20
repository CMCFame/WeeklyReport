# components/modular_weekly_report.py
"""Modular weekly report component for the Weekly Report app."""

import streamlit as st
from utils import session
from components.user_info import render_user_info
from components.current_activities import render_current_activities
from components.upcoming_activities import render_upcoming_activities
from components.simple_accomplishments import render_simple_accomplishments
from components.simple_action_items import render_simple_action_items
from components.optional_sections import render_optional_section_toggles, render_all_optional_sections

def render_modular_weekly_report(is_editing=False):
    """Render the modular weekly report form with unified section selection toolbar.
    
    Args:
        is_editing (bool): Whether we're in edit mode
    """
    # Header
    if is_editing:
        st.title('📝 Edit Weekly Activity Report')
        st.write('Update your previous report')
    else:
        st.title('📋 Weekly Activity Report')
        st.write('Use the sections below to document your week\'s work')

    # Progress bar
    from utils.session import calculate_completion_percentage
    completion_percentage = calculate_completion_percentage()
    st.progress(completion_percentage / 100)
    
    # Pre-fill name from user profile if empty
    if not st.session_state.get("name") and st.session_state.get("user_info"):
        st.session_state.name = st.session_state.user_info.get("full_name", "")

    # User Information Section (always shown)
    render_user_info()

    # Initialize section visibility in session state if not present
    if "show_current_activities" not in st.session_state:
        st.session_state.show_current_activities = True
    if "show_upcoming_activities" not in st.session_state:
        st.session_state.show_upcoming_activities = True
    if "show_accomplishments" not in st.session_state:
        st.session_state.show_accomplishments = True
    if "show_action_items" not in st.session_state:
        st.session_state.show_action_items = True

    # Unified Section Toolbar - use icons and consistent styling
    st.subheader("Report Sections")
    st.write("Select which sections to include in your report:")
    
    # Define section info with icons and descriptions
    section_info = [
        {
            "id": "current_activities",
            "name": "Current Activities",
            "icon": "📊",
            "description": "What are you currently working on?"
        },
        {
            "id": "upcoming_activities",
            "name": "Upcoming Activities",
            "icon": "📅",
            "description": "What activities are planned for the future?"
        },
        {
            "id": "accomplishments",
            "name": "Last Week's Accomplishments",
            "icon": "✓",
            "description": "What did you accomplish last week?"
        },
        {
            "id": "action_items",
            "name": "Action Items",
            "icon": "📋",
            "description": "Follow-ups and next steps"
        }
    ]
    
    # Create a container for a stylized toolbar
    toolbar = st.container()
    
    with toolbar:
        cols = st.columns(len(section_info))
        
        for i, section in enumerate(section_info):
            section_id = section["id"]
            key_name = f"show_{section_id}"
            
            with cols[i]:
                # Create a card-like appearance for each section toggle
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 5px;">
                        <div style="font-size: 24px;">{section["icon"]}</div>
                        <div style="font-weight: bold;">{section["name"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Use checkbox with the section_id to make keys unique
                st.session_state[key_name] = st.checkbox(
                    "Include",
                    value=st.session_state.get(key_name, True),
                    key=f"section_toggle_{section_id}",
                    help=section["description"]
                )
    
    st.divider()

    # Conditional rendering of sections
    if st.session_state.show_current_activities:
        render_enhanced_current_activities()

    if st.session_state.show_upcoming_activities:
        render_upcoming_activities()

    if st.session_state.show_accomplishments:
        render_simple_accomplishments()

    if st.session_state.show_action_items:
        render_simple_action_items()

    # Optional Sections - now also as a toolbar
    st.subheader("Additional Sections")
    st.write("Select which additional sections you'd like to include:")
    
    # Get the list of optional sections
    from utils.constants import OPTIONAL_SECTIONS
    
    # Create a stylized toolbar for optional sections
    opt_cols = st.columns(len(OPTIONAL_SECTIONS))
    
    for i, section in enumerate(OPTIONAL_SECTIONS):
        with opt_cols[i]:
            # Create a card-like appearance for each optional section toggle
            st.markdown(
                f"""
                <div style="text-align: center; padding: 5px;">
                    <div style="font-size: 24px;">{section["icon"]}</div>
                    <div style="font-weight: bold;">{section["label"]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Use checkbox with a unique key
            st.session_state[section["key"]] = st.checkbox(
                "Include",
                value=st.session_state.get(section["key"], False),
                key=f"optional_section_{section['key']}",
                help=section["description"]
            )
    
    # Render the optional sections content
    render_all_optional_sections()

    # Form Actions
    render_form_actions(is_editing)

def render_enhanced_current_activities():
    """Render current activities with enhanced options."""
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
            render_enhanced_current_activity_form(i, activity)
    
    # Add activity button
    if st.button('+ Add Another Activity', use_container_width=True):
        session.add_current_activity()
        st.rerun()

def render_enhanced_current_activity_form(index, activity):
    """Render form fields for a current activity with enhanced options."""
    # Get username for project filtering
    username = ""
    if st.session_state.get("user_info"):
        username = st.session_state.user_info.get("username", "")
    
    # First row: Project and Milestone
    col_proj, col_mile = st.columns(2)
    
    with col_proj:
        # Get available projects for the user
        from utils.csv_utils import get_user_projects
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
        from utils.csv_utils import get_project_milestones
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
        from utils.constants import PRIORITY_OPTIONS
        priority = st.selectbox(
            'Priority', 
            options=PRIORITY_OPTIONS, 
            index=PRIORITY_OPTIONS.index(activity.get('priority', 'Medium')) if activity.get('priority') in PRIORITY_OPTIONS else 1,
            key=f"curr_prio_{index}"
        )
        session.update_current_activity(index, 'priority', priority)
    
    with col2:
        from utils.constants import STATUS_OPTIONS
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
        from utils.constants import BILLABLE_OPTIONS
        billable = st.selectbox(
            'Billable', 
            options=BILLABLE_OPTIONS, 
            index=BILLABLE_OPTIONS.index(activity.get('billable', '')) if activity.get('billable') in BILLABLE_OPTIONS else 0,
            key=f"curr_bill_{index}"
        )
        session.update_current_activity(index, 'billable', billable)
    
    # Third row: Deadline toggle and Recurrent toggle
    col5, col6 = st.columns(2)
    
    with col5:
        # Initialize has_deadline in activity if it doesn't exist
        if 'has_deadline' not in activity:
            activity['has_deadline'] = bool(activity.get('deadline', ''))
        
        has_deadline = st.checkbox(
            'Has Deadline', 
            value=activity.get('has_deadline', False),
            key=f"curr_has_deadline_{index}"
        )
        session.update_current_activity(index, 'has_deadline', has_deadline)
        
        # Only show date picker if has_deadline is checked
        if has_deadline:
            # Handle date conversion
            deadline_date = None
            if activity.get('deadline'):
                try:
                    from datetime import datetime
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
            # Clear deadline if has_deadline is unchecked
            session.update_current_activity(index, 'deadline', '')
    
    with col6:
        # Initialize is_recurrent in activity if it doesn't exist
        if 'is_recurrent' not in activity:
            activity['is_recurrent'] = False
        
        is_recurrent = st.checkbox(
            'Recurrent Activity', 
            value=activity.get('is_recurrent', False),
            key=f"curr_recurrent_{index}",
            help="Check if this is a recurring task"
        )
        session.update_current_activity(index, 'is_recurrent', is_recurrent)
    
    # Fourth row: Progress with slider and manual input
    st.write('Progress:')
    prog_col1, prog_col2 = st.columns([5, 1])
    
    with prog_col1:
        # Use slider for progress
        progress = st.slider(
            'Progress %', 
            min_value=0, 
            max_value=100, 
            value=activity.get('progress', 50), 
            key=f"curr_prog_slider_{index}",
            label_visibility="collapsed"
        )
    
    with prog_col2:
        # Manual progress input as a small number input
        manual_progress = st.number_input(
            '%', 
            min_value=0, 
            max_value=100, 
            value=progress,
            key=f"curr_prog_manual_{index}",
            label_visibility="visible"
        )
        # Use manual input if it differs from slider
        if manual_progress != progress:
            progress = manual_progress
    
    # Update progress in activity
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

def render_form_actions(is_editing=False):
    """Render the form action buttons."""
    st.divider()
    
    if is_editing:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button('Save Changes', use_container_width=True, type="primary"):
                save_current_report('submitted', is_update=True)

        with col2:
            # Cancel editing button
            if st.button('Cancel Editing', use_container_width=True):
                # Mark for cancellation
                st.session_state.cancel_editing = True
                st.rerun()

        with col3:
            # Reset changes button
            if st.button('Reset Changes', use_container_width=True):
                clear_form_callback()
    else:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button('Save Draft', use_container_width=True):
                save_current_report('draft')

        with col2:
            if st.button('Clear Form', use_container_width=True):
                clear_form_callback()

        with col3:
            if st.button('Submit Report', use_container_width=True, type="primary"):
                save_current_report('submitted')

def clear_form_callback():
    """Callback to reset all fields and rerun the app."""
    from utils.session import reset_form
    reset_form()
    st.rerun()

def save_current_report(status, is_update=False):
    """Save the current report."""
    # Validate required fields for submission
    if status == 'submitted' and not st.session_state.name:
        st.error('Please enter your name before submitting')
        return

    if status == 'submitted' and not st.session_state.reporting_week:
        st.error('Please enter the reporting week before submitting')
        return

    # Collect and save form data
    from utils.session import collect_form_data
    from utils.file_ops import save_report
    from datetime import datetime
    
    report_data = collect_form_data()
    report_data['status'] = status
    
    # If editing, preserve the original timestamp when it was created
    if is_update and 'original_timestamp' in st.session_state:
        report_data['timestamp'] = st.session_state.original_timestamp
        # Add last_updated timestamp
        report_data['last_updated'] = datetime.now().isoformat()
    
    report_id = save_report(report_data)
    st.session_state.report_id = report_id

    # Show success message
    if is_update:
        st.success('Report updated successfully!')
        # Clear editing flag
        st.session_state.editing_report = False
        # Go back to past reports
        st.session_state.nav_page = "Past Reports"
        st.session_state.nav_section = "reporting"
        st.rerun()
    elif status == 'draft':
        st.success('Draft saved successfully!')
    else:
        st.success('Report submitted successfully!')
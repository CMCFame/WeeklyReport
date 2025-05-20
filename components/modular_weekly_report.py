# components/modular_weekly_report.py

import streamlit as st
import time
from utils import session
from components.user_info import render_user_info
from components.current_activities import render_current_activities
from components.upcoming_activities import render_upcoming_activities
from components.simple_accomplishments import render_simple_accomplishments
from components.simple_action_items import render_simple_action_items
from components.optional_sections import render_optional_section, render_all_optional_sections
from utils.constants import OPTIONAL_SECTIONS

def render_modular_weekly_report(is_editing=False):
    """Render the modular weekly report form with consolidated section selection.
    
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

    # Generate a unique timestamp for this component
    timestamp_base = int(time.time() * 1000)

    # Consolidated section selection dropdown
    st.subheader("Report Sections")
    st.write("Select which sections to include in your report:")
    
    # Define ALL available sections (main + optional) with their IDs, names and icons
    available_sections = [
        {"id": "current_activities", "type": "main", "name": "Current Activities", "icon": "📊", "key": "show_current_activities"},
        {"id": "upcoming_activities", "type": "main", "name": "Upcoming Activities", "icon": "📅", "key": "show_upcoming_activities"},
        {"id": "accomplishments", "type": "main", "name": "Last Week's Accomplishments", "icon": "✓", "key": "show_accomplishments"},
        {"id": "action_items", "type": "main", "name": "Action Items", "icon": "📋", "key": "show_action_items"}
    ]
    
    # Add optional sections to the list
    for section in OPTIONAL_SECTIONS:
        available_sections.append({
            "id": section["content_key"],
            "type": "optional",
            "name": section["label"],
            "icon": section["icon"],
            "key": section["key"]
        })
    
    # Initialize section visibility in session state if not present
    for section in available_sections:
        if section["key"] not in st.session_state:
            # Default to having NO sections selected
            st.session_state[section["key"]] = False
    
    # Create options for the multiselect with icons
    section_options = [f"{section['icon']} {section['name']}" for section in available_sections]
    
    # Determine which options are currently selected
    current_selections = []
    for i, section in enumerate(available_sections):
        if st.session_state.get(section["key"], False):
            current_selections.append(section_options[i])
    
    # Use multiselect for section selection with unique key
    selected_sections = st.multiselect(
        "Sections to include",
        options=section_options,
        default=current_selections,
        key=f"consolidated_sections_multiselect_{timestamp_base}"
    )
    
    # Check for sections that were deselected and have data
    sections_with_data = {}
    for i, section in enumerate(available_sections):
        section_key = section["key"]
        section_option = section_options[i]
        
        # Check if section was previously selected but is now being deselected
        if st.session_state.get(section_key, False) and section_option not in selected_sections:
            # Check if section has data
            has_data = False
            
            # Check for data in main sections
            if section["id"] == "current_activities" and st.session_state.get("current_activities", []):
                has_data = True
            elif section["id"] == "upcoming_activities" and st.session_state.get("upcoming_activities", []):
                has_data = True
            elif section["id"] == "accomplishments" and any(st.session_state.get("accomplishments", [""])):
                has_data = True
            elif section["id"] == "action_items" and (any(st.session_state.get("followups", [""])) or any(st.session_state.get("nextsteps", [""]))):
                has_data = True
            # Check for data in optional sections
            elif section["type"] == "optional" and st.session_state.get(section["id"], ""):
                has_data = True
            
            if has_data:
                sections_with_data[section_option] = section_key
    
    # Show confirmation dialog if there are sections with data being deselected
    if sections_with_data:
        st.warning("⚠️ The following sections contain data that will be lost if disabled:")
        for section_name in sections_with_data.keys():
            st.write(f"- {section_name}")
        
        confirm_col1, confirm_col2 = st.columns(2)
        with confirm_col1:
            if st.button("Confirm Section Changes", type="primary", key=f"confirm_changes_{timestamp_base}"):
                # Update section states based on selections
                for i, section in enumerate(available_sections):
                    section_key = section["key"]
                    section_option = section_options[i]
                    st.session_state[section_key] = section_option in selected_sections
                    
                    # Clear data for deselected sections
                    if section_option not in selected_sections:
                        if section["id"] == "current_activities":
                            st.session_state.current_activities = []
                        elif section["id"] == "upcoming_activities":
                            st.session_state.upcoming_activities = []
                        elif section["id"] == "accomplishments":
                            st.session_state.accomplishments = [""]
                        elif section["id"] == "action_items":
                            st.session_state.followups = [""]
                            st.session_state.nextsteps = [""]
                        elif section["type"] == "optional":
                            st.session_state[section["id"]] = ""
                            st.session_state[section_key] = False
                
                st.success("Section changes applied!")
                st.rerun()
        
        with confirm_col2:
            if st.button("Cancel Changes", key=f"cancel_changes_{timestamp_base}"):
                # Reset the multiselect to match the current state
                st.rerun()
    else:
        # Update section states based on selections without confirmation
        for i, section in enumerate(available_sections):
            section_key = section["key"]
            section_option = section_options[i]
            st.session_state[section_key] = section_option in selected_sections
    
    st.divider()

    # Render sections based on selections
    if st.session_state.get("show_current_activities", False):
        render_enhanced_current_activities()

    if st.session_state.get("show_upcoming_activities", False):
        render_upcoming_activities()

    if st.session_state.get("show_accomplishments", False):
        render_simple_accomplishments()

    if st.session_state.get("show_action_items", False):
        render_simple_action_items()

    # Render optional sections
    for section in OPTIONAL_SECTIONS:
        if st.session_state.get(section["key"], False):
            render_optional_section(section)

    # Form Actions
    render_form_actions(is_editing)

def render_enhanced_current_activities():
    """Render current activities with enhanced options."""
    st.header('📊 Current Activities')
    st.write('What are you currently working on? Include priority and status.')
    
    # Handle empty state - add a default activity if none exist
    if not st.session_state.current_activities:
        import time
        timestamp = int(time.time() * 1000)
        if st.button('+ Add First Activity', use_container_width=True, key=f"btn_add_first_activity_{timestamp}"):
            session.add_current_activity()
            st.rerun()
        return
    
    # Render existing activities
    import time
    for i, activity in enumerate(st.session_state.current_activities):
        timestamp = int(time.time() * 1000)
        activity_title = activity.get('description', '')[:30] 
        activity_title = f"{activity_title}..." if activity_title else "New Activity"
        
        with st.expander(f"Activity {i+1}: {activity_title}", expanded=i==0):
            render_enhanced_current_activity_form(i, activity)
    
    # Add activity button
    import time
    timestamp = int(time.time() * 1000)
    if st.button('+ Add Another Activity', use_container_width=True, key=f"btn_add_another_activity_{timestamp}"):
        session.add_current_activity()
        st.rerun()

def render_enhanced_current_activity_form(index, activity):
    """Render form fields for a current activity with enhanced options."""
    import time
    timestamp_base = int(time.time() * 1000) + index
    
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
            key=f"curr_proj_{index}_{timestamp_base}",
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
            key=f"curr_mile_{index}_{timestamp_base}",
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
            key=f"curr_prio_{index}_{timestamp_base}"
        )
        session.update_current_activity(index, 'priority', priority)
    
    with col2:
        from utils.constants import STATUS_OPTIONS
        status = st.selectbox(
            'Status', 
            options=STATUS_OPTIONS, 
            index=STATUS_OPTIONS.index(activity.get('status', 'In Progress')) if activity.get('status') in STATUS_OPTIONS else 1,
            key=f"curr_status_{index}_{timestamp_base}"
        )
        session.update_current_activity(index, 'status', status)
    
    with col3:
        customer = st.text_input(
            'Customer', 
            value=activity.get('customer', ''), 
            key=f"curr_cust_{index}_{timestamp_base}",
            help="Client or internal team this work is for"
        )
        session.update_current_activity(index, 'customer', customer)
    
    with col4:
        from utils.constants import BILLABLE_OPTIONS
        billable = st.selectbox(
            'Billable', 
            options=BILLABLE_OPTIONS, 
            index=BILLABLE_OPTIONS.index(activity.get('billable', '')) if activity.get('billable') in BILLABLE_OPTIONS else 0,
            key=f"curr_bill_{index}_{timestamp_base}"
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
            key=f"curr_has_deadline_{index}_{timestamp_base}"
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
                key=f"curr_dead_{index}_{timestamp_base}"
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
            key=f"curr_recurrent_{index}_{timestamp_base}",
            help="Check if this is a recurring task"
        )
        session.update_current_activity(index, 'is_recurrent', is_recurrent)
    
    # Fourth row: Progress with slider and manual input
    st.write('Progress:')
    prog_col1, prog_col2 = st.columns([5, 1])
    
    with prog_col1:
        # Use slider for progress - Fix with a proper label
        progress = st.slider(
            'Progress Percentage', 
            min_value=0, 
            max_value=100, 
            value=activity.get('progress', 50), 
            key=f"curr_prog_slider_{index}_{timestamp_base}",
            label_visibility="collapsed"  # Hide the label visually but provide one for accessibility
        )
    
    with prog_col2:
        # Manual progress input as a small number input - Fix empty label warning
        manual_progress = st.number_input(
            'Progress Value', 
            min_value=0, 
            max_value=100, 
            value=progress,
            key=f"curr_prog_manual_{index}_{timestamp_base}",
            label_visibility="collapsed"  # Hide the label visually but provide one for accessibility
        )
        st.write('%')  # Add percentage sign
        
        # Use manual input if it differs from slider
        if manual_progress != progress:
            progress = manual_progress
    
    # Update progress in activity
    session.update_current_activity(index, 'progress', progress)
    
    # Description
    description = st.text_area(
        'Description', 
        value=activity.get('description', ''), 
        key=f"curr_desc_{index}_{timestamp_base}",
        height=100
    )
    session.update_current_activity(index, 'description', description)
    
    # Remove button
    if st.button('Remove Activity', key=f"remove_curr_{index}_{timestamp_base}"):
        session.remove_current_activity(index)
        st.rerun()

def render_form_actions(is_editing=False):
    """Render the form action buttons."""
    st.divider()
    
    import time
    timestamp = int(time.time() * 1000)
    
    if is_editing:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button('Save Changes', use_container_width=True, type="primary", key=f"btn_save_changes_{timestamp}"):
                save_current_report('submitted', is_update=True)

        with col2:
            # Cancel editing button
            if st.button('Cancel Editing', use_container_width=True, key=f"btn_cancel_editing_{timestamp}"):
                # Mark for cancellation
                st.session_state.cancel_editing = True
                st.rerun()

        with col3:
            # Reset changes button
            if st.button('Reset Changes', use_container_width=True, key=f"btn_reset_changes_{timestamp}"):
                clear_form_callback()
    else:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button('Save Draft', use_container_width=True, key=f"btn_save_draft_{timestamp}"):
                save_current_report('draft')

        with col2:
            if st.button('Clear Form', use_container_width=True, key=f"btn_clear_form_{timestamp}"):
                clear_form_callback()

        with col3:
            if st.button('Submit Report', use_container_width=True, type="primary", key=f"btn_submit_report_{timestamp}"):
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

    # Additional validation - Check if required sections are filled
    has_required_data = True
    error_msgs = []
    
    # Current activities validation
    if st.session_state.get("show_current_activities", False):
        has_current_activities = False
        if st.session_state.get("current_activities"):
            # Check if at least one activity has a description
            for activity in st.session_state.current_activities:
                if activity.get("description", "").strip():
                    has_current_activities = True
                    break
        
        if not has_current_activities:
            has_required_data = False
            error_msgs.append("Please add at least one current activity with a description.")
    
    # Upcoming activities validation
    if st.session_state.get("show_upcoming_activities", False):
        has_upcoming_activities = False
        if st.session_state.get("upcoming_activities"):
            # Check if at least one activity has a description
            for activity in st.session_state.upcoming_activities:
                if activity.get("description", "").strip():
                    has_upcoming_activities = True
                    break
        
        if not has_upcoming_activities:
            has_required_data = False
            error_msgs.append("Please add at least one upcoming activity with a description.")
    
    # Accomplishments validation
    if st.session_state.get("show_accomplishments", False):
        has_accomplishments = False
        if st.session_state.get("accomplishments"):
            # Check if at least one accomplishment is not empty
            for accomplishment in st.session_state.accomplishments:
                if accomplishment and accomplishment.strip():
                    has_accomplishments = True
                    break
        
        if not has_accomplishments:
            has_required_data = False
            error_msgs.append("Please add at least one accomplishment.")
    
    # Action items validation
    if st.session_state.get("show_action_items", False):
        has_action_items = False
        # Check followups
        if st.session_state.get("followups"):
            for followup in st.session_state.followups:
                if followup and followup.strip():
                    has_action_items = True
                    break
        
        # Check nextsteps
        if not has_action_items and st.session_state.get("nextsteps"):
            for nextstep in st.session_state.nextsteps:
                if nextstep and nextstep.strip():
                    has_action_items = True
                    break
        
        if not has_action_items:
            has_required_data = False
            error_msgs.append("Please add at least one follow-up or next step.")
    
    # Validate optional sections if they are enabled
    for section in OPTIONAL_SECTIONS:
        if st.session_state.get(section["key"], False):
            content_key = section["content_key"]
            content = st.session_state.get(content_key, "")
            
            if not content or not content.strip():
                has_required_data = False
                error_msgs.append(f"Please add content to the {section['label']} section or disable it.")
    
    # Check if there are any validation errors
    if status == 'submitted' and not has_required_data:
        for error_msg in error_msgs:
            st.error(error_msg)
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
        # Optional: reset form after successful submission
        from utils.session import reset_form
        reset_form()
        st.rerun()
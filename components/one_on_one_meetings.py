# components/one_on_one_meetings.py (with fixes for duplicate keys)

"""1:1 Meeting component for the Weekly Report app."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import uuid  # Added for generating unique IDs
from utils.meeting_utils import (
    load_meeting_templates, save_meeting_templates, 
    add_meeting_template, update_meeting_template, delete_meeting_template,
    get_template_by_id, get_meetings, create_meeting, update_meeting, 
    delete_meeting, get_meeting_by_id, add_action_item_to_meeting,
    update_action_item, get_all_action_items, get_upcoming_meetings,
    convert_action_items_to_next_steps
)
from utils.team_utils import (
    get_team_members, get_member_by_user_id
)
from utils.session import (
    update_item_list
)

def render_one_on_one_meetings():
    """Render the 1:1 meetings page."""
    st.title("1:1 Meetings")
    st.write("Schedule, prepare for, and track outcomes of one-on-one meetings with team members.")
    
    # User permissions and role
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    current_user_id = st.session_state.get("user_info", {}).get("id")
    current_user_name = st.session_state.get("user_info", {}).get("full_name", "User")
    can_manage = user_role in ["admin", "manager"]
    
    # Get team member context
    team_member = None
    if current_user_id:
        team_member = get_member_by_user_id(current_user_id)
    
    # Generate unique IDs for each tab to avoid key conflicts
    if "meeting_tab_ids" not in st.session_state:
        st.session_state.meeting_tab_ids = {
            "upcoming": str(uuid.uuid4()),
            "all": str(uuid.uuid4()),
            "action_items": str(uuid.uuid4()),
            "templates": str(uuid.uuid4())
        }
    
    # Tabs for different views
    tabs = ["Upcoming Meetings", "All Meetings", "Action Items"]
    
    if can_manage:
        tabs.append("Templates")
    
    tab1, tab2, tab3, *extra_tabs = st.tabs(tabs)
    
    with tab1:
        render_upcoming_meetings(current_user_id, current_user_name, team_member, can_manage, 
                                 tab_id=st.session_state.meeting_tab_ids["upcoming"])
    
    with tab2:
        render_all_meetings(current_user_id, current_user_name, team_member, can_manage,
                            tab_id=st.session_state.meeting_tab_ids["all"])
    
    with tab3:
        render_action_items(current_user_id, current_user_name, team_member, can_manage,
                            tab_id=st.session_state.meeting_tab_ids["action_items"])
    
    if can_manage and len(extra_tabs) > 0:
        with extra_tabs[0]:
            render_meeting_templates(tab_id=st.session_state.meeting_tab_ids["templates"])

def render_upcoming_meetings(current_user_id, current_user_name, team_member, can_manage, tab_id):
    """Render the upcoming meetings view.
    
    Args:
        current_user_id (str): Current user ID
        current_user_name (str): Current user name
        team_member (dict): Team member data
        can_manage (bool): Whether user has management permissions
        tab_id (str): Unique ID for this tab to prefix keys
    """
    st.subheader("Upcoming Meetings")
    
    # Get upcoming meetings
    upcoming_meetings = get_upcoming_meetings(days=14)  # Next 2 weeks
    
    # Create a new meeting
    with st.expander("Schedule a New 1:1 Meeting", expanded=False):
        render_new_meeting_form(current_user_id, current_user_name, team_member, can_manage, form_id=f"{tab_id}_new_meeting")
    
    # Display upcoming meetings
    if upcoming_meetings:
        st.write(f"You have {len(upcoming_meetings)} upcoming meetings in the next 14 days:")
        
        # Group by week
        this_week = []
        next_week = []
        later = []
        
        today = datetime.now().date()
        week_end = today + timedelta(days=7-today.weekday())  # End of this week (Sunday)
        next_week_end = week_end + timedelta(days=7)  # End of next week
        
        for meeting in upcoming_meetings:
            try:
                meeting_date = datetime.strptime(meeting.get("scheduled_date", ""), "%Y-%m-%d").date()
                if meeting_date <= week_end:
                    this_week.append(meeting)
                elif meeting_date <= next_week_end:
                    next_week.append(meeting)
                else:
                    later.append(meeting)
            except:
                later.append(meeting)
        
        # This week
        if this_week:
            st.write("### This Week")
            for i, meeting in enumerate(this_week):
                render_meeting_card(meeting, current_user_id, can_manage, f"{tab_id}_this_week_{i}")
        
        # Next week
        if next_week:
            st.write("### Next Week")
            for i, meeting in enumerate(next_week):
                render_meeting_card(meeting, current_user_id, can_manage, f"{tab_id}_next_week_{i}")
        
        # Later
        if later:
            st.write("### Later")
            for i, meeting in enumerate(later):
                render_meeting_card(meeting, current_user_id, can_manage, f"{tab_id}_later_{i}")
    else:
        st.info("No upcoming meetings scheduled. Use the form above to schedule a new meeting.")

def render_all_meetings(current_user_id, current_user_name, team_member, can_manage, tab_id):
    """Render all meetings view.
    
    Args:
        current_user_id (str): Current user ID
        current_user_name (str): Current user name
        team_member (dict): Team member data
        can_manage (bool): Whether user has management permissions
        tab_id (str): Unique ID for this tab to prefix keys
    """
    st.subheader("All Meetings")
    
    # Get all meetings
    all_meetings = get_meetings()
    
    # Filter options
    status_options = ["All", "Scheduled", "In Progress", "Completed", "Cancelled"]
    selected_status = st.selectbox("Filter by Status", status_options, key=f"{tab_id}_status_filter")
    
    # Apply filters
    if selected_status != "All":
        filtered_meetings = [m for m in all_meetings if m.get("status") == selected_status]
    else:
        filtered_meetings = all_meetings
    
    # Sort options
    sort_options = ["Date (Latest First)", "Date (Oldest First)", "Team Member", "Status"]
    selected_sort = st.selectbox("Sort by", sort_options, key=f"{tab_id}_sort_option")
    
    # Apply sorting
    if selected_sort == "Date (Latest First)":
        sorted_meetings = sorted(filtered_meetings, key=lambda x: x.get("scheduled_date", ""), reverse=True)
    elif selected_sort == "Date (Oldest First)":
        sorted_meetings = sorted(filtered_meetings, key=lambda x: x.get("scheduled_date", ""))
    elif selected_sort == "Team Member":
        sorted_meetings = sorted(filtered_meetings, key=lambda x: x.get("team_member_name", ""))
    elif selected_sort == "Status":
        # Custom status order: Scheduled, In Progress, Completed, Cancelled
        status_order = {"Scheduled": 0, "In Progress": 1, "Completed": 2, "Cancelled": 3}
        sorted_meetings = sorted(filtered_meetings, key=lambda x: status_order.get(x.get("status"), 4))
    else:
        sorted_meetings = filtered_meetings
    
    # Display all meetings
    if sorted_meetings:
        st.write(f"Showing {len(sorted_meetings)} meetings:")
        
        for i, meeting in enumerate(sorted_meetings):
            render_meeting_card(meeting, current_user_id, can_manage, f"{tab_id}_meeting_{i}")
    else:
        st.info("No meetings match the selected filters.")

def render_action_items(current_user_id, current_user_name, team_member, can_manage, tab_id):
    """Render action items view.
    
    Args:
        current_user_id (str): Current user ID
        current_user_name (str): Current user name
        team_member (dict): Team member data
        can_manage (bool): Whether user has management permissions
        tab_id (str): Unique ID for this tab to prefix keys
    """
    st.subheader("Action Items")
    
    # Get all action items
    all_items = get_all_action_items()
    
    # Filter options
    status_options = ["All", "Pending", "In Progress", "Completed"]
    selected_status = st.selectbox("Filter by Status", status_options, key=f"{tab_id}_action_status_filter")
    
    # Apply filters
    if selected_status != "All":
        filtered_items = [item for item in all_items if item.get("status") == selected_status]
    else:
        filtered_items = all_items
    
    # Display action items
    if filtered_items:
        st.write(f"Showing {len(filtered_items)} action items:")
        
        # Group by status
        pending = [item for item in filtered_items if item.get("status") == "Pending"]
        in_progress = [item for item in filtered_items if item.get("status") == "In Progress"]
        completed = [item for item in filtered_items if item.get("status") == "Completed"]
        other = [item for item in filtered_items if item.get("status") not in ["Pending", "In Progress", "Completed"]]
        
        # Pending items
        if pending and (selected_status == "All" or selected_status == "Pending"):
            with st.expander("Pending", expanded=True):
                render_action_item_list(pending, current_user_id, f"{tab_id}_pending")
        
        # In Progress items
        if in_progress and (selected_status == "All" or selected_status == "In Progress"):
            with st.expander("In Progress", expanded=True):
                render_action_item_list(in_progress, current_user_id, f"{tab_id}_in_progress")
        
        # Completed items
        if completed and (selected_status == "All" or selected_status == "Completed"):
            with st.expander("Completed", expanded=False):
                render_action_item_list(completed, current_user_id, f"{tab_id}_completed")
        
        # Other items
        if other and selected_status == "All":
            with st.expander("Other", expanded=False):
                render_action_item_list(other, current_user_id, f"{tab_id}_other")
        
        # Add to weekly report button
        st.divider()
        st.write("### Add Action Items to Weekly Report")
        st.write("You can add pending action items to your weekly report as next steps.")
        
        if st.button("Add Pending Action Items to Weekly Report", key=f"{tab_id}_add_to_report_btn"):
            # Get pending items assigned to the current user
            my_pending_items = [
                item for item in pending 
                if (item.get("assigned_to") == current_user_name or
                   (can_manage and item.get("assigned_to") == item.get("team_member_name")))
            ]
            
            if my_pending_items:
                # Convert to next steps format
                next_steps = []
                for item in my_pending_items:
                    description = item.get("description", "")
                    due_date = item.get("due_date", "")
                    
                    step = description
                    if due_date:
                        step += f" - Due: {due_date}"
                    
                    next_steps.append(step)
                
                # Add to session state
                for step in next_steps:
                    if "nextsteps" in st.session_state:
                        # If the first item is empty, replace it, otherwise add
                        if len(st.session_state.nextsteps) == 1 and not st.session_state.nextsteps[0]:
                            st.session_state.nextsteps[0] = step
                        else:
                            st.session_state.nextsteps.append(step)
                
                st.success(f"Added {len(next_steps)} action items to your weekly report!")
            else:
                st.info("No pending action items assigned to you.")
    else:
        st.info("No action items match the selected filters.")

def render_meeting_templates(tab_id):
    """Render the meeting templates management view.
    
    Args:
        tab_id (str): Unique ID for this tab to prefix keys
    """
    st.subheader("Meeting Templates")
    
    # Load existing templates
    templates = load_meeting_templates()
    
    # Create new template form
    with st.expander("Create New Template", expanded=False):
        with st.form(f"{tab_id}_new_template_form"):
            template_name = st.text_input("Template Name")
            template_description = st.text_area("Description")
            
            # Sections
            st.write("#### Sections")
            st.write("Add sections to structure your 1:1 meetings")
            
            # Use session state to track number of sections
            if "template_sections" not in st.session_state:
                st.session_state.template_sections = [
                    {"title": "Check-in", "description": "How are you doing?"},
                    {"title": "Progress Update", "description": "What progress have you made since our last meeting?"},
                    {"title": "Challenges", "description": "What challenges are you facing?"},
                    {"title": "Action Items", "description": "What actions need to be taken?"}
                ]
            
            # Display current sections
            for i, section in enumerate(st.session_state.template_sections):
                col1, col2 = st.columns([1, 3])
                with col1:
                    section_title = st.text_input(f"Title {i+1}", value=section["title"], key=f"{tab_id}_section_title_{i}")
                with col2:
                    section_desc = st.text_input(f"Description {i+1}", value=section["description"], key=f"{tab_id}_section_desc_{i}")
                
                # Update session state
                st.session_state.template_sections[i] = {"title": section_title, "description": section_desc}
            
            # Save button
            submit = st.form_submit_button("Save Template")
            
            if submit and template_name:
                # Create new template
                template_id = add_meeting_template(template_name, template_description, st.session_state.template_sections)
                if template_id:
                    st.success(f"Template '{template_name}' created successfully!")
                    
                    # Clear form
                    st.session_state.template_sections = [
                        {"title": "Check-in", "description": "How are you doing?"},
                        {"title": "Progress Update", "description": "What progress have you made since our last meeting?"},
                        {"title": "Challenges", "description": "What challenges are you facing?"},
                        {"title": "Action Items", "description": "What actions need to be taken?"}
                    ]
                    
                    st.rerun()
    
    # Button to add/remove sections (outside the form)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+ Add Section", key=f"{tab_id}_add_section_btn"):
            st.session_state.template_sections.append({"title": "", "description": ""})
            st.rerun()
    with col2:
        if st.button("- Remove Last Section", key=f"{tab_id}_remove_section_btn") and len(st.session_state.template_sections) > 1:
            st.session_state.template_sections.pop()
            st.rerun()
    
    # Display existing templates
    if templates:
        st.write("### Existing Templates")
        
        for i, template in enumerate(templates):
            with st.expander(f"{template.get('name', 'Untitled Template')}", expanded=False):
                # Display template details
                st.write(f"**Description:** {template.get('description', 'No description')}")
                
                # Display sections
                st.write("**Sections:**")
                for j, section in enumerate(template.get("sections", [])):
                    st.markdown(f"**{j+1}. {section.get('title', 'Untitled')}**")
                    st.write(f"{section.get('description', 'No description')}")
                
                # Edit/Delete buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Edit Template", key=f"{tab_id}_edit_{i}"):
                        # Load template into session state for editing
                        st.session_state.edit_template_id = template.get("id")
                        st.session_state.edit_template_name = template.get("name")
                        st.session_state.edit_template_description = template.get("description")
                        st.session_state.edit_template_sections = template.get("sections", [])
                        st.rerun()
                
                with col2:
                    if st.button("Delete Template", key=f"{tab_id}_delete_{i}"):
                        if delete_meeting_template(template.get("id")):
                            st.success(f"Template '{template.get('name')}' deleted successfully!")
                            st.rerun()
        
        # Edit template form (shown when editing)
        if hasattr(st.session_state, "edit_template_id"):
            st.write("### Edit Template")
            
            with st.form(f"{tab_id}_edit_template_form"):
                edit_name = st.text_input("Template Name", value=st.session_state.edit_template_name)
                edit_description = st.text_area("Description", value=st.session_state.edit_template_description)
                
                # Sections
                st.write("#### Sections")
                
                edited_sections = []
                for i, section in enumerate(st.session_state.edit_template_sections):
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        section_title = st.text_input(f"Title {i+1}", value=section.get("title", ""), key=f"{tab_id}_edit_section_title_{i}")
                    with col2:
                        section_desc = st.text_input(f"Description {i+1}", value=section.get("description", ""), key=f"{tab_id}_edit_section_desc_{i}")
                    
                    edited_sections.append({"title": section_title, "description": section_desc})
                
                # Save button
                update_submit = st.form_submit_button("Update Template")
                
                if update_submit:
                    # Update template
                    if update_meeting_template(st.session_state.edit_template_id, edit_name, edit_description, edited_sections):
                        st.success(f"Template '{edit_name}' updated successfully!")
                        
                        # Clear form
                        delattr(st.session_state, "edit_template_id")
                        delattr(st.session_state, "edit_template_name")
                        delattr(st.session_state, "edit_template_description")
                        delattr(st.session_state, "edit_template_sections")
                        
                        st.rerun()
            
            # Button to add/remove sections for edit form (outside the form)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("+ Add Section", key=f"{tab_id}_edit_add_section"):
                    st.session_state.edit_template_sections.append({"title": "", "description": ""})
                    st.rerun()
            with col2:
                if st.button("- Remove Last Section", key=f"{tab_id}_edit_remove_section") and len(st.session_state.edit_template_sections) > 1:
                    st.session_state.edit_template_sections.pop()
                    st.rerun()
            
            # Cancel button
            if st.button("Cancel Editing", key=f"{tab_id}_cancel_edit"):
                delattr(st.session_state, "edit_template_id")
                delattr(st.session_state, "edit_template_name")
                delattr(st.session_state, "edit_template_description")
                delattr(st.session_state, "edit_template_sections")
                st.rerun()
    else:
        st.info("No templates have been created yet.")

def render_new_meeting_form(current_user_id, current_user_name, team_member, can_manage, form_id):
    """Render the form to create a new meeting.
    
    Args:
        current_user_id (str): Current user ID
        current_user_name (str): Current user name
        team_member (dict): Team member data
        can_manage (bool): Whether user has management permissions
        form_id (str): Unique ID for this form
    """
    with st.form(form_id):
        st.write("### Schedule a New 1:1 Meeting")
        
        # Get team members
        all_members = get_team_members()
        
        # For managers, show all team members
        if can_manage:
            # Manager is scheduling with a team member
            manager_name = current_user_name
            manager_id = current_user_id
            
            # Filter out the current user from the list
            team_members = [m for m in all_members if m.get("user_id") != current_user_id]
            
            if team_members:
                # Select team member
                team_member_options = [(m.get("id"), m.get("name")) for m in team_members]
                selected_member_id = st.selectbox(
                    "Team Member",
                    options=[tmid for tmid, _ in team_member_options],
                    format_func=lambda x: next((name for tid, name in team_member_options if tid == x), "Unknown"),
                    key=f"{form_id}_team_member"
                )
                
                # Get the selected member
                selected_member = next((m for m in team_members if m.get("id") == selected_member_id), None)
                
                if selected_member:
                    team_member_name = selected_member.get("name")
                    team_member_id = selected_member.get("user_id")
                else:
                    team_member_name = "Unknown"
                    team_member_id = None
            else:
                st.warning("No team members available. Add team members in the Team Structure page.")
                team_member_name = "Unknown"
                team_member_id = None
                selected_member_id = None
        else:
            # Team member is scheduling with their manager
            team_member_name = current_user_name
            team_member_id = current_user_id
            
            # Find the manager for this team member
            if team_member and team_member.get("manager_id"):
                manager = next((m for m in all_members if m.get("id") == team_member.get("manager_id")), None)
                if manager:
                    manager_name = manager.get("name")
                    manager_id = manager.get("user_id")
                else:
                    manager_name = "Your Manager"
                    manager_id = None
            else:
                manager_name = "Your Manager"
                manager_id = None
        
        # Meeting date
        meeting_date = st.date_input(
            "Meeting Date",
            value=datetime.now().date() + timedelta(days=1),  # Default to tomorrow
            key=f"{form_id}_meeting_date"
        )
        
        # Meeting template
        templates = load_meeting_templates()
        template_options = [{"id": None, "name": "No Template"}] + templates
        selected_template = st.selectbox(
            "Meeting Template",
            options=[t.get("id") for t in template_options],
            format_func=lambda x: next((t.get("name") for t in template_options if t.get("id") == x), "Custom"),
            key=f"{form_id}_template"
        )
        
        # Submit button
        submit = st.form_submit_button("Schedule Meeting")
        
        if submit:
            # Create meeting
            meeting_id = create_meeting(
                manager_name=manager_name,
                team_member_name=team_member_name,
                scheduled_date=meeting_date.strftime("%Y-%m-%d"),
                template_id=selected_template if selected_template else None,
                manager_user_id=manager_id,
                team_member_user_id=team_member_id
            )
            
            if meeting_id:
                st.success(f"Meeting scheduled for {meeting_date.strftime('%Y-%m-%d')}!")
                st.rerun()

def render_meeting_card(meeting, current_user_id, can_manage, card_id):
    """Render a card for a meeting.
    
    Args:
        meeting (dict): Meeting data
        current_user_id (str): Current user ID
        can_manage (bool): Whether user has management permissions
        card_id (str): Unique ID for this card
    """
    meeting_id = meeting.get("id")
    manager_name = meeting.get("manager_name", "Unknown")
    team_member_name = meeting.get("team_member_name", "Unknown")
    scheduled_date = meeting.get("scheduled_date", "Unknown")
    status = meeting.get("status", "Scheduled")
    template_name = meeting.get("template_name", "Custom")
    
    # Format date
    try:
        formatted_date = datetime.strptime(scheduled_date, "%Y-%m-%d").strftime("%B %d, %Y")
    except:
        formatted_date = scheduled_date
    
    # Create a container for the card
    card = st.container()
    
    # Status badge
    status_color = {
        "Scheduled": "blue",
        "In Progress": "orange",
        "Completed": "green",
        "Cancelled": "red"
    }.get(status, "gray")
    
    with card:
        # Use columns for layout
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"#### {manager_name} & {team_member_name}")
            st.write(f"**Date:** {formatted_date}")
            st.write(f"**Template:** {template_name}")
        
        with col2:
            st.markdown(f"<div style='background-color:{status_color};color:white;padding:3px 8px;border-radius:10px;display:inline-block;margin-top:10px;'>{status}</div>", unsafe_allow_html=True)
        
        with col3:
            # View/Edit button
            if st.button("View/Edit", key=f"{card_id}_view_btn"):
                st.session_state.meeting_to_view = meeting_id
                st.rerun()
    
    st.divider()
    
    # Show meeting details if selected
    if hasattr(st.session_state, "meeting_to_view") and st.session_state.meeting_to_view == meeting_id:
        render_meeting_details(meeting, current_user_id, can_manage, card_id)

def render_meeting_details(meeting, current_user_id, can_manage, meeting_prefix):
    """Render detailed view of a meeting.
    
    Args:
        meeting (dict): Meeting data
        current_user_id (str): Current user ID
        can_manage (bool): Whether user has management permissions
        meeting_prefix (str): Unique prefix for this meeting's widgets
    """
    meeting_id = meeting.get("id")
    manager_name = meeting.get("manager_name", "Unknown")
    team_member_name = meeting.get("team_member_name", "Unknown")
    scheduled_date = meeting.get("scheduled_date", "Unknown")
    status = meeting.get("status", "Scheduled")
    template_name = meeting.get("template_name", "Custom")
    sections = meeting.get("sections", [])
    action_items = meeting.get("action_items", [])
    notes = meeting.get("notes", "")
    
    # Format date
    try:
        formatted_date = datetime.strptime(scheduled_date, "%Y-%m-%d").strftime("%B %d, %Y")
    except:
        formatted_date = scheduled_date
    
    # Show the full meeting details
    with st.container():
        st.markdown(f"## 1:1 Meeting: {manager_name} & {team_member_name}")
        st.markdown(f"**Date:** {formatted_date} | **Status:** {status} | **Template:** {template_name}")
        
        # Status update buttons
        st.write("### Update Status")
        status_col1, status_col2, status_col3, status_col4 = st.columns(4)
        
        with status_col1:
            if st.button("Mark as Scheduled", disabled=(status == "Scheduled"), key=f"{meeting_prefix}_status_scheduled"):
                if update_meeting(meeting_id, status="Scheduled"):
                    st.success("Meeting status updated!")
                    st.rerun()
        
        with status_col2:
            if st.button("Start Meeting", disabled=(status == "In Progress"), key=f"{meeting_prefix}_status_progress"):
                if update_meeting(meeting_id, status="In Progress"):
                    st.success("Meeting started!")
                    st.rerun()
        
        with status_col3:
            if st.button("Complete Meeting", disabled=(status == "Completed"), key=f"{meeting_prefix}_status_complete"):
                if update_meeting(meeting_id, status="Completed"):
                    st.success("Meeting completed!")
                    st.rerun()
        
        with status_col4:
            if st.button("Cancel Meeting", disabled=(status == "Cancelled"), key=f"{meeting_prefix}_status_cancel"):
                if update_meeting(meeting_id, status="Cancelled"):
                    st.success("Meeting cancelled!")
                    st.rerun()
        
        # Tabs for different meeting sections
        meeting_tab1, meeting_tab2, meeting_tab3 = st.tabs(["Meeting Notes", "Action Items", "Meeting Details"])
        
        with meeting_tab1:
            # Meeting notes and sections
            st.write("### Meeting Agenda & Notes")
            
            updated_sections = []
            meeting_notes = notes
            
            # Create a form for meeting notes
            with st.form(f"{meeting_prefix}_meeting_notes_form"):
                # Display each section with editable content field
                for i, section in enumerate(sections):
                    st.markdown(f"#### {section.get('title', 'Section')}")
                    st.write(section.get('description', ''))
                    section_content = st.text_area(
                        "Notes",
                        value=section.get('content', ''),
                        key=f"{meeting_prefix}_section_{i}",
                        label_visibility="collapsed",
                        height=100
                    )
                    
                    # Update the section
                    updated_section = section.copy()
                    updated_section['content'] = section_content
                    updated_sections.append(updated_section)
                
                # Additional notes
                st.markdown("#### Additional Notes")
                meeting_notes = st.text_area(
                    "Additional Notes",
                    value=notes,
                    key=f"{meeting_prefix}_notes",
                    height=150
                )
                
                # Save button
                save_notes = st.form_submit_button("Save Notes")
                
                if save_notes:
                    if update_meeting(meeting_id, sections=updated_sections, notes=meeting_notes):
                        st.success("Meeting notes saved!")
                        st.rerun()
        
        with meeting_tab2:
            # Action items
            st.write("### Action Items")
            
            # Form to add a new action item
            with st.form(f"{meeting_prefix}_new_action_item_form"):
                st.write("Add a new action item:")
                item_description = st.text_input("Description", key=f"{meeting_prefix}_new_item_desc")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    assigned_options = [manager_name, team_member_name]
                    assigned_to = st.selectbox(
                        "Assigned To", 
                        assigned_options, 
                        key=f"{meeting_prefix}_new_item_assigned"
                    )
                
                with col2:
                    due_date = st.date_input(
                        "Due Date", 
                        key=f"{meeting_prefix}_new_item_due"
                    )
                
                with col3:
                    priority = st.selectbox(
                        "Priority", 
                        ["High", "Medium", "Low"], 
                        key=f"{meeting_prefix}_new_item_priority"
                    )
                    add_item = st.form_submit_button("Add Action Item")
                
                if add_item and item_description:
                    if add_action_item_to_meeting(
                        meeting_id,
                        description=item_description,
                        assigned_to=assigned_to,
                        due_date=due_date.strftime("%Y-%m-%d"),
                        priority=priority
                    ):
                        st.success("Action item added!")
                        st.rerun()
            
            # Display existing action items
            if action_items:
                for i, item in enumerate(action_items):
                    item_id = item.get("id")
                    with st.expander(f"{item.get('description', 'Action Item')}"):
                        # Display item details
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**Assigned To:** {item.get('assigned_to', 'Unassigned')}")
                        
                        with col2:
                            st.write(f"**Due Date:** {item.get('due_date', 'No date')}")
                        
                        with col3:
                            st.write(f"**Priority:** {item.get('priority', 'Medium')}")
                        
                        with col4:
                            st.write(f"**Status:** {item.get('status', 'Pending')}")
                        
                        # Form to update action item status
                        with st.form(f"{meeting_prefix}_update_action_item_{i}"):
                            new_status = st.selectbox(
                                "Update Status",
                                ["Pending", "In Progress", "Completed", "Cancelled"],
                                index=["Pending", "In Progress", "Completed", "Cancelled"].index(item.get("status", "Pending")),
                                key=f"{meeting_prefix}_update_status_{i}"
                            )
                            
                            update_status = st.form_submit_button("Update Status")
                            
                            if update_status:
                                if update_action_item(meeting_id, item_id, status=new_status):
                                    st.success("Action item updated!")
                                    st.rerun()
                
                # Button to add all action items to the weekly report
                add_to_report = st.button("Add Action Items to Weekly Report", key=f"{meeting_prefix}_add_to_report")
                
                if add_to_report:
                    next_steps = convert_action_items_to_next_steps(meeting_id)
                    
                    if next_steps:
                        # Add to session state
                        for step in next_steps:
                            if "nextsteps" in st.session_state:
                                # If the first item is empty, replace it, otherwise add
                                if len(st.session_state.nextsteps) == 1 and not st.session_state.nextsteps[0]:
                                    st.session_state.nextsteps[0] = step
                                else:
                                    st.session_state.nextsteps.append(step)
                        
                        st.success(f"Added {len(next_steps)} action items to your weekly report!")
                    else:
                        st.info("No action items to add to report.")
            else:
                st.info("No action items added yet.")
        
        with meeting_tab3:
            # Meeting details
            st.write("### Meeting Details")
            
            # Form to update meeting details
            with st.form(f"{meeting_prefix}_update_meeting_form"):
                # Reschedule meeting
                new_date = st.date_input(
                    "Reschedule Meeting",
                    value=datetime.strptime(scheduled_date, "%Y-%m-%d").date() if scheduled_date else datetime.now().date(),
                    key=f"{meeting_prefix}_reschedule_date"
                )
                
                update_meeting_btn = st.form_submit_button("Update Meeting")
                
                if update_meeting_btn:
                    if update_meeting(meeting_id, scheduled_date=new_date.strftime("%Y-%m-%d")):
                        st.success("Meeting updated!")
                        st.rerun()
            
            # Delete meeting button
            if st.button("Delete Meeting", key=f"{meeting_prefix}_delete_meeting"):
                # Confirm delete
                st.warning("Are you sure you want to delete this meeting?")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Yes, Delete Meeting", key=f"{meeting_prefix}_confirm_delete"):
                        if delete_meeting(meeting_id):
                            st.success("Meeting deleted!")
                            # Remove from session state
                            delattr(st.session_state, "meeting_to_view")
                            st.rerun()
                
                with col2:
                    if st.button("Cancel", key=f"{meeting_prefix}_cancel_delete"):
                        st.rerun()
        
        # Close button
        if st.button("Close", key=f"{meeting_prefix}_close"):
            delattr(st.session_state, "meeting_to_view")
            st.rerun()

def render_action_item_list(items, current_user_id, list_id):
    """Render a list of action items.
    
    Args:
        items (list): List of action items
        current_user_id (str): Current user ID
        list_id (str): Unique ID for this list to generate unique keys
    """
    if not items:
        st.info("No action items in this category.")
        return
    
    # Create a table of action items
    data = []
    for item in items:
        data.append({
            "Description": item.get("description", ""),
            "Assigned To": item.get("assigned_to", "Unassigned"),
            "Due Date": item.get("due_date", ""),
            "Priority": item.get("priority", "Medium"),
            "Meeting Date": item.get("meeting_date", ""),
            "Status": item.get("status", "Pending"),
            "Meeting ID": item.get("meeting_id", ""),
            "Action Item ID": item.get("id", "")
        })
    
    # Convert to dataframe for display
    df = pd.DataFrame(data)
    display_df = df[["Description", "Assigned To", "Due Date", "Priority", "Meeting Date", "Status"]]
    
    # Add color coding to priority and status
    def color_priority(val):
        if val == "High":
            return "background-color: #ffcccc"
        elif val == "Medium":
            return "background-color: #ffffcc"
        else:
            return "background-color: #ccffcc"
    
    def color_status(val):
        if val == "Completed":
            return "background-color: #ccffcc"
        elif val == "In Progress":
            return "background-color: #ffffcc"
        elif val == "Pending":
            return "background-color: #ffddff"
        else:
            return "background-color: #ffcccc"
    
    # Apply styling
    styled_df = display_df.style.applymap(color_priority, subset=["Priority"]).applymap(color_status, subset=["Status"])
    
    # Display the table
    st.dataframe(styled_df, use_container_width=True)
    
    # Add update functionality for each item
    st.write("### Update Action Items")
    
    for i, item in enumerate(items):
        with st.expander(f"Update: {item.get('description', 'Action Item')}", expanded=False):
            meeting_id = item.get("meeting_id")
            item_id = item.get("id")
            
            # Form to update status
            with st.form(f"{list_id}_update_form_{i}_{item_id}"):
                new_status = st.selectbox(
                    "Update Status",
                    ["Pending", "In Progress", "Completed", "Cancelled"],
                    index=["Pending", "In Progress", "Completed", "Cancelled"].index(item.get("status", "Pending")),
                    key=f"{list_id}_status_select_{i}_{item_id}"
                )
                
                update_btn = st.form_submit_button("Update Status")
                
                if update_btn and meeting_id and item_id:
                    if update_action_item(meeting_id, item_id, status=new_status):
                        st.success("Action item updated!")
                        st.rerun()
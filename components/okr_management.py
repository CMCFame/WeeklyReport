# components/okr_management.py
"""OKR Management component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import plotly.express as px
import numpy as np

def render_okr_management():
    """Render the OKR management interface."""
    st.title("OKR Management")
    st.write("Create, track, and manage Objectives and Key Results (OKRs).")
    
    # User permissions and role
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    user_id = st.session_state.get("user_info", {}).get("id")
    user_name = st.session_state.get("user_info", {}).get("full_name", "Unknown")
    can_manage = user_role in ["admin", "manager"]
    
    # Create tabs for different OKR management views
    tab1, tab2, tab3, tab4 = st.tabs([
        "My OKRs", "Create/Edit OKRs", "Progress Updates", "History"
    ])
    
    with tab1:
        render_my_okrs(user_id, user_name, can_manage)
    
    with tab2:
        render_create_edit_okrs(user_id, user_name, can_manage)
    
    with tab3:
        render_progress_updates(user_id, user_name, can_manage)
    
    with tab4:
        render_okr_history(user_id, user_name, can_manage)

def render_my_okrs(user_id, user_name, can_manage):
    """Render the user's OKRs and progress.
    
    Args:
        user_id (str): Current user ID
        user_name (str): Current user name
        can_manage (bool): Whether user can manage all OKRs
    """
    st.subheader("My OKRs")
    
    # Period selector
    current_quarter = (datetime.now().month - 1) // 3 + 1
    current_year = datetime.now().year
    default_period = f"Q{current_quarter} {current_year}"
    
    # Generate period options
    period_options = []
    for year in range(current_year - 1, current_year + 2):
        for quarter in range(1, 5):
            period_options.append(f"Q{quarter} {year}")
    
    # Get default period index
    try:
        default_index = period_options.index(default_period)
    except ValueError:
        default_index = 0
    
    selected_period = st.selectbox(
        "Select Period",
        options=period_options,
        index=default_index
    )
    
    # Get objectives for the selected period
    objectives = get_objectives_for_user(user_id, selected_period, can_manage)
    
    if not objectives:
        st.info(f"No OKRs found for {selected_period}. Create your first OKR in the 'Create/Edit OKRs' tab.")
        return
    
    # Display objectives in cards
    st.write(f"### Your objectives for {selected_period}")
    
    # Calculate overall progress
    if objectives:
        total_progress = calculate_overall_progress(objectives)
        
        # Progress meter
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(total_progress / 100)
        with col2:
            st.metric("Overall Progress", f"{total_progress:.1f}%")
    
    # Sort objectives by progress (lowest first to focus on those needing attention)
    sorted_objectives = sorted(objectives, key=lambda x: calculate_objective_progress(x))
    
    # Display each objective
    for obj in sorted_objectives:
        with st.expander(f"{obj.get('title', 'Untitled Objective')} - {calculate_objective_progress(obj):.1f}%", expanded=True):
            render_objective_card(obj)
            
            # Quick update button
            if st.button("Update Progress", key=f"quick_update_{obj.get('id')}"):
                st.session_state.objective_to_update = obj.get('id')
                st.session_state.active_tab = "Progress Updates"
                st.rerun()

def render_create_edit_okrs(user_id, user_name, can_manage):
    """Render the interface to create and edit OKRs.
    
    Args:
        user_id (str): Current user ID
        user_name (str): Current user name
        can_manage (bool): Whether user can manage all OKRs
    """
    st.subheader("Create/Edit OKRs")
    
    # Check if editing an existing objective
    if hasattr(st.session_state, 'edit_objective_id'):
        objective = get_objective_by_id(st.session_state.edit_objective_id)
        if objective:
            render_objective_form(objective, user_id, user_name, can_manage)
        else:
            st.error("Objective not found. It may have been deleted.")
            if hasattr(st.session_state, 'edit_objective_id'):
                delattr(st.session_state, 'edit_objective_id')
    else:
        # Create new objective
        # Period selector for new objective
        current_quarter = (datetime.now().month - 1) // 3 + 1
        current_year = datetime.now().year
        default_period = f"Q{current_quarter} {current_year}"
        
        # Generate period options
        period_options = []
        for year in range(current_year - 1, current_year + 2):
            for quarter in range(1, 5):
                period_options.append(f"Q{quarter} {year}")
        
        # Get default period index
        try:
            default_index = period_options.index(default_period)
        except ValueError:
            default_index = 0
        
        selected_period = st.selectbox(
            "Select Period for New Objective",
            options=period_options,
            index=default_index
        )
        
        # Initialize new objective
        new_objective = {
            'period': selected_period,
            'level': 'individual',
            'status': 'On Track',
            'key_results': [{'description': '', 'progress': 0}],
            'owner_id': user_id,
            'owner_name': user_name
        }
        
        # Render form for new objective
        render_objective_form(new_objective, user_id, user_name, can_manage)
    
    # Show existing objectives that can be edited
    st.divider()
    st.subheader("Edit Existing Objectives")
    
    # Period selector
    current_quarter = (datetime.now().month - 1) // 3 + 1
    current_year = datetime.now().year
    default_period = f"Q{current_quarter} {current_year}"
    
    # Generate period options
    period_options = []
    for year in range(current_year - 1, current_year + 2):
        for quarter in range(1, 5):
            period_options.append(f"Q{quarter} {year}")
    
    # Get default period index
    try:
        default_index = period_options.index(default_period)
    except ValueError:
        default_index = 0
    
    selected_period = st.selectbox(
        "Select Period to Edit",
        options=period_options,
        index=default_index,
        key="edit_period_selector"
    )
    
    # Get objectives for the selected period
    editable_objectives = get_objectives_for_user(user_id, selected_period, can_manage)
    
    if not editable_objectives:
        st.info(f"No OKRs found for {selected_period} that you can edit.")
        return
    
    # Display each objective with edit button
    for obj in editable_objectives:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{obj.get('title', 'Untitled Objective')}** ({obj.get('level', 'individual').capitalize()})")
        
        with col2:
            if st.button("Edit", key=f"edit_{obj.get('id')}"):
                st.session_state.edit_objective_id = obj.get('id')
                st.rerun()

def render_progress_updates(user_id, user_name, can_manage):
    """Render the interface to update OKR progress.
    
    Args:
        user_id (str): Current user ID
        user_name (str): Current user name
        can_manage (bool): Whether user can manage all OKRs
    """
    st.subheader("Progress Updates")
    
    # Check if updating a specific objective
    objective_to_update = None
    if hasattr(st.session_state, 'objective_to_update'):
        objective_to_update = get_objective_by_id(st.session_state.objective_to_update)
    
    if objective_to_update:
        render_objective_update_form(objective_to_update, user_id, user_name, can_manage)
    else:
        # Period selector
        current_quarter = (datetime.now().month - 1) // 3 + 1
        current_year = datetime.now().year
        default_period = f"Q{current_quarter} {current_year}"
        
        # Generate period options
        period_options = []
        for year in range(current_year - 1, current_year + 2):
            for quarter in range(1, 5):
                period_options.append(f"Q{quarter} {year}")
        
        # Get default period index
        try:
            default_index = period_options.index(default_period)
        except ValueError:
            default_index = 0
        
        selected_period = st.selectbox(
            "Select Period",
            options=period_options,
            index=default_index,
            key="update_period_selector"
        )
        
        # Get objectives for the selected period
        updateable_objectives = get_objectives_for_user(user_id, selected_period, can_manage)
        
        if not updateable_objectives:
            st.info(f"No OKRs found for {selected_period} that you can update.")
            return
        
        # Display each objective with update button
        for obj in updateable_objectives:
            with st.expander(f"{obj.get('title', 'Untitled Objective')} - {calculate_objective_progress(obj):.1f}%", expanded=False):
                # Show objective information
                st.write(f"**Description:** {obj.get('description', 'No description')}")
                st.write(f"**Level:** {obj.get('level', 'individual').capitalize()}")
                st.write(f"**Status:** {obj.get('status', 'On Track')}")
                
                # Key Results summary
                for i, kr in enumerate(obj.get('key_results', [])):
                    st.write(f"**KR{i+1}:** {kr.get('description', 'No description')} - {kr.get('progress', 0)}%")
                
                # Update button
                if st.button("Update Progress", key=f"update_{obj.get('id')}"):
                    st.session_state.objective_to_update = obj.get('id')
                    st.rerun()

def render_okr_history(user_id, user_name, can_manage):
    """Render the OKR history and trends.
    
    Args:
        user_id (str): Current user ID
        user_name (str): Current user name
        can_manage (bool): Whether user can manage all OKRs
    """
    st.subheader("OKR History & Trends")
    
    # Get all objectives for the user (current and past)
    all_objectives = get_all_objectives_for_user(user_id, can_manage)
    
    if not all_objectives:
        st.info("No OKR history found.")
        return
    
    # Group objectives by period
    objectives_by_period = {}
    for obj in all_objectives:
        period = obj.get('period', 'Unknown')
        if period not in objectives_by_period:
            objectives_by_period[period] = []
        objectives_by_period[period].append(obj)
    
    # Calculate progress for each period
    progress_by_period = {}
    for period, objectives in objectives_by_period.items():
        progress_by_period[period] = calculate_overall_progress(objectives)
    
    # Create a dataframe for the chart
    periods = list(progress_by_period.keys())
    progress = list(progress_by_period.values())
    
    # Sort by period (assuming format is Qn YYYY)
    period_data = [(p, int(p.split()[1]), int(p[1])) for p in periods]  # (period, year, quarter)
    sorted_indices = [i for i, _ in sorted(enumerate(period_data), key=lambda x: (x[1][1], x[1][2]))]
    
    sorted_periods = [periods[i] for i in sorted_indices]
    sorted_progress = [progress[i] for i in sorted_indices]
    
    df = pd.DataFrame({
        'Period': sorted_periods,
        'Progress': sorted_progress
    })
    
    # Create a bar chart
    fig = px.bar(
        df,
        x='Period',
        y='Progress',
        title='OKR Completion by Period',
        labels={'Progress': 'Completion Rate (%)'},
        text=df['Progress'].apply(lambda x: f"{x:.1f}%"),
        color='Progress',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Historical objectives
    st.subheader("Historical Objectives")
    
    # Display historical objectives grouped by period
    for period in sorted_periods:
        with st.expander(f"{period} - {progress_by_period[period]:.1f}%"):
            objectives = objectives_by_period[period]
            
            for obj in objectives:
                st.write(f"**{obj.get('title', 'Untitled Objective')}** - {calculate_objective_progress(obj):.1f}%")
                
                # Progress bar
                st.progress(calculate_objective_progress(obj) / 100)
                
                # Details button
                if st.button("View Details", key=f"history_{obj.get('id')}"):
                    st.session_state.view_objective_id = obj.get('id')
                    st.rerun()
    
    # Show details if an objective is selected
    if hasattr(st.session_state, 'view_objective_id'):
        objective = get_objective_by_id(st.session_state.view_objective_id)
        if objective:
            st.divider()
            st.subheader(f"Details: {objective.get('title', 'Untitled Objective')}")
            render_objective_details(objective)
            
            # Close button
            if st.button("Close", key="close_details"):
                delattr(st.session_state, 'view_objective_id')
                st.rerun()

def render_objective_form(objective, user_id, user_name, can_manage):
    """Render a form to create or edit an objective.
    
    Args:
        objective (dict): Objective data
        user_id (str): Current user ID
        user_name (str): Current user name
        can_manage (bool): Whether user can manage all OKRs
    """
    # Check if this is a new or existing objective
    is_new = 'id' not in objective
    form_title = "Create New Objective" if is_new else "Edit Objective"
    
    st.write(f"### {form_title}")
    
    # Form for objective data
    with st.form(key="objective_form"):
        # Basic objective info
        title = st.text_input("Objective Title", value=objective.get('title', ''))
        description = st.text_area("Description", value=objective.get('description', ''), height=100)
        
        # Level selection
        if can_manage:
            level_options = ["individual", "team", "company"]
            level = st.selectbox(
                "Level",
                options=level_options,
                index=level_options.index(objective.get('level', 'individual')),
                format_func=lambda x: x.capitalize()
            )
        else:
            # Non-managers can only create individual objectives
            level = "individual"
            st.write(f"**Level:** Individual")
        
        # Team selection (if team level and can_manage)
        team = None
        if level == "team" and can_manage:
            teams = get_teams()
            if teams:
                team_index = 0
                if objective.get('team') in teams:
                    team_index = teams.index(objective.get('team'))
                
                team = st.selectbox(
                    "Team",
                    options=teams,
                    index=team_index
                )
            else:
                st.warning("No teams available. Please create teams first.")
                team = "General"
        
        # Owner selection (for managers creating objectives for others)
        owner_id = user_id
        owner_name = user_name
        
        if can_manage and level == "individual":
            # Get all users
            users = get_users()
            
            if users:
                # Create options for selectbox
                user_ids = [user.get('id') for user in users]
                
                default_index = 0
                if objective.get('owner_id') in user_ids:
                    default_index = user_ids.index(objective.get('owner_id'))
                
                selected_owner_id = st.selectbox(
                    "Owner",
                    options=user_ids,
                    index=default_index,
                    format_func=lambda x: next((user.get('full_name') for user in users if user.get('id') == x), "Unknown")
                )
                
                # Get owner name for display
                owner_id = selected_owner_id
                owner_name = next((user.get('full_name') for user in users if user.get('id') == owner_id), "Unknown")
            else:
                st.warning("No users available.")
        
        # Status
        status_options = ["On Track", "At Risk", "Behind", "Completed"]
        status = st.selectbox(
            "Status",
            options=status_options,
            index=status_options.index(objective.get('status', 'On Track'))
        )
        
        # Key Results section
        st.write("### Key Results")
        st.write("Define measurable outcomes that will indicate success.")
        
        # Use session state to track key results
        if "key_results" not in st.session_state:
            # Initialize with existing key results or a single empty one
            st.session_state.key_results = objective.get('key_results', [{'description': '', 'progress': 0}])
        
        # Ensure we have at least one key result
        if not st.session_state.key_results:
            st.session_state.key_results = [{'description': '', 'progress': 0}]
        
        # Display key results fields
        for i, kr in enumerate(st.session_state.key_results):
            st.write(f"**Key Result {i+1}**")
            
            # Description
            kr_description = st.text_input(
                "Description",
                value=kr.get('description', ''),
                key=f"kr_desc_{i}"
            )
            
            # Progress (only for existing objectives)
            kr_progress = 0
            if not is_new:
                kr_progress = st.slider(
                    "Progress",
                    min_value=0,
                    max_value=100,
                    value=int(kr.get('progress', 0)),
                    key=f"kr_prog_{i}"
                )
            
            # Update key result in session state
            st.session_state.key_results[i]['description'] = kr_description
            st.session_state.key_results[i]['progress'] = kr_progress
            
            # Divider between key results
            if i < len(st.session_state.key_results) - 1:
                st.divider()
        
        # Submit button
        submit_label = "Create Objective" if is_new else "Update Objective"
        submit = st.form_submit_button(submit_label, type="primary")
        
        if submit:
            if not title:
                st.error("Please provide an objective title.")
            elif not any(kr.get('description') for kr in st.session_state.key_results):
                st.error("Please provide at least one key result.")
            else:
                # Prepare objective data
                objective_data = {
                    'title': title,
                    'description': description,
                    'level': level,
                    'status': status,
                    'period': objective.get('period'),
                    'key_results': st.session_state.key_results,
                    'owner_id': owner_id,
                    'owner_name': owner_name,
                    'last_updated': datetime.now().isoformat()
                }
                
                # Add ID if editing existing objective
                if not is_new:
                    objective_data['id'] = objective.get('id')
                    objective_data['created_at'] = objective.get('created_at')
                
                # Add team if applicable
                if level == "team" and team:
                    objective_data['team'] = team
                
                # Save objective
                result = save_objective(objective_data)
                
                if result:
                    if is_new:
                        st.success("Objective created successfully!")
                    else:
                        st.success("Objective updated successfully!")
                    
                    # Clear form state
                    st.session_state.key_results = [{'description': '', 'progress': 0}]
                    if hasattr(st.session_state, 'edit_objective_id'):
                        delattr(st.session_state, 'edit_objective_id')
                    
                    # Rerun to refresh the page
                    st.rerun()
                else:
                    st.error("Error saving objective. Please try again.")
    
    # Button to add/remove key results (outside the form)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+ Add Key Result", key="add_kr"):
            st.session_state.key_results.append({'description': '', 'progress': 0})
            st.rerun()
    
    with col2:
        if st.button("- Remove Last Key Result", key="remove_kr") and len(st.session_state.key_results) > 1:
            st.session_state.key_results.pop()
            st.rerun()
    
    # Cancel button
    if not is_new:
        if st.button("Cancel Edit", key="cancel_edit"):
            if hasattr(st.session_state, 'edit_objective_id'):
                delattr(st.session_state, 'edit_objective_id')
            st.session_state.key_results = [{'description': '', 'progress': 0}]
            st.rerun()

def render_objective_update_form(objective, user_id, user_name, can_manage):
    """Render a form to update objective progress.
    
    Args:
        objective (dict): Objective data
        user_id (str): Current user ID
        user_name (str): Current user name
        can_manage (bool): Whether user can manage all OKRs
    """
    st.write(f"### Update Progress: {objective.get('title', 'Untitled Objective')}")
    
    # Display objective details
    st.write(f"**Description:** {objective.get('description', 'No description')}")
    st.write(f"**Period:** {objective.get('period', 'Unknown')}")
    st.write(f"**Level:** {objective.get('level', 'individual').capitalize()}")
    
    if objective.get('level') == 'team':
        st.write(f"**Team:** {objective.get('team', 'General')}")
    
    st.write(f"**Owner:** {objective.get('owner_name', 'Unknown')}")
    
    # Form for updating progress
    with st.form(key="update_progress_form"):
        # Status update
        status_options = ["On Track", "At Risk", "Behind", "Completed"]
        status = st.selectbox(
            "Status",
            options=status_options,
            index=status_options.index(objective.get('status', 'On Track'))
        )
        
        # Progress update for each key result
        st.write("### Key Results Progress")
        
        updated_key_results = []
        
        for i, kr in enumerate(objective.get('key_results', [])):
            st.write(f"**Key Result {i+1}:** {kr.get('description', 'No description')}")
            
            # Current progress
            current_progress = kr.get('progress', 0)
            
            # Progress slider
            new_progress = st.slider(
                "Progress",
                min_value=0,
                max_value=100,
                value=int(current_progress),
                key=f"update_kr_prog_{i}"
            )
            
            # Update notes
            update_note = st.text_area(
                "Update Notes",
                key=f"update_kr_note_{i}",
                placeholder="Add context about your progress or any blockers..."
            )
            
            # Create updated key result
            updated_kr = kr.copy()
            updated_kr['progress'] = new_progress
            
            # Add update entry
            if 'updates' not in updated_kr:
                updated_kr['updates'] = []
            
            # Only add update if there's a change or note
            if new_progress != current_progress or update_note:
                updated_kr['updates'].append({
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'previous': current_progress,
                    'current': new_progress,
                    'note': update_note
                })
            
            updated_key_results.append(updated_kr)
            
            # Divider between key results
            if i < len(objective.get('key_results', [])) - 1:
                st.divider()
        
        # Submit button
        submit = st.form_submit_button("Save Progress Update", type="primary")
        
        if submit:
            # Update the objective
            updated_objective = objective.copy()
            updated_objective['key_results'] = updated_key_results
            updated_objective['status'] = status
            updated_objective['last_updated'] = datetime.now().isoformat()
            
            # Save the updated objective
            result = save_objective(updated_objective)
            
            if result:
                st.success("Progress updated successfully!")
                
                # Clear the updating state
                if hasattr(st.session_state, 'objective_to_update'):
                    delattr(st.session_state, 'objective_to_update')
                
                st.rerun()
            else:
                st.error("Error updating progress. Please try again.")
    
    # Cancel button
    if st.button("Cancel Update", key="cancel_update"):
        if hasattr(st.session_state, 'objective_to_update'):
            delattr(st.session_state, 'objective_to_update')
        st.rerun()

def render_objective_card(objective):
    """Render a card with objective details.
    
    Args:
        objective (dict): Objective data
    """
    # Basic info
    st.write(f"**Description:** {objective.get('description', 'No description')}")
    
    if objective.get('level') == 'team':
        st.write(f"**Team:** {objective.get('team', 'General')}")
    
    st.write(f"**Owner:** {objective.get('owner_name', 'Unknown')}")
    st.write(f"**Status:** {objective.get('status', 'On Track')}")
    
    # Get the most recent update date
    latest_update = None
    for kr in objective.get('key_results', []):
        if kr.get('updates'):
            for update in kr.get('updates'):
                update_date = update.get('date')
                if update_date:
                    if not latest_update or update_date > latest_update:
                        latest_update = update_date
    
    if latest_update:
        st.write(f"**Last Updated:** {latest_update}")
    
    # Progress bars for key results
    st.write("### Key Results")
    
    for i, kr in enumerate(objective.get('key_results', [])):
        progress = kr.get('progress', 0)
        
        st.write(f"**KR{i+1}:** {kr.get('description', 'No description')}")
        
        # Progress bar
        col1, col2 = st.columns([4, 1])
        with col1:
            st.progress(progress / 100)
        with col2:
            st.write(f"{progress}%")
        
        # Show latest update if available
        if kr.get('updates') and kr['updates']:
            latest_kr_update = kr['updates'][-1]
            st.write(f"*Last update ({latest_kr_update.get('date', '')}): {latest_kr_update.get('note', '')}*")

def render_objective_details(objective):
    """Render detailed information about an objective.
    
    Args:
        objective (dict): Objective data
    """
    # Basic info
    st.write(f"**Description:** {objective.get('description', 'No description')}")
    st.write(f"**Period:** {objective.get('period', 'Unknown')}")
    st.write(f"**Level:** {objective.get('level', 'individual').capitalize()}")
    
    if objective.get('level') == 'team':
        st.write(f"**Team:** {objective.get('team', 'General')}")
    
    st.write(f"**Owner:** {objective.get('owner_name', 'Unknown')}")
    st.write(f"**Status:** {objective.get('status', 'On Track')}")
    st.write(f"**Created:** {objective.get('created_at', '')[:10]}")
    st.write(f"**Last Updated:** {objective.get('last_updated', '')[:10]}")
    
    # Progress
    progress = calculate_objective_progress(objective)
    st.write(f"**Overall Progress:** {progress:.1f}%")
    st.progress(progress / 100)
    
    # Key Results
    st.write("### Key Results")
    
    for i, kr in enumerate(objective.get('key_results', [])):
        with st.expander(f"KR{i+1}: {kr.get('description', 'No description')} - {kr.get('progress', 0)}%", expanded=True):
            # Progress history
            st.write("**Progress History:**")
            
            # Show updates
            if kr.get('updates'):
                # Create a dataframe for the updates
                updates_data = []
                for update in kr.get('updates'):
                    updates_data.append({
                        'Date': update.get('date', ''),
                        'Previous': update.get('previous', 0),
                        'New': update.get('current', 0),
                        'Change': update.get('current', 0) - update.get('previous', 0),
                        'Notes': update.get('note', '')
                    })
                
                if updates_data:
                    updates_df = pd.DataFrame(updates_data)
                    st.dataframe(updates_df, use_container_width=True)
                else:
                    st.write("No progress updates recorded.")
            else:
                st.write("No progress updates recorded.")

# Helper functions for OKR management

def get_objectives_for_user(user_id, period, can_manage=False):
    """Get objectives for a user and period.
    
    Args:
        user_id (str): User ID
        period (str): Period (e.g., Q1 2023)
        can_manage (bool): Whether user can access all objectives
        
    Returns:
        list: List of objective dictionaries
    """
    try:
        # Ensure the objectives directory exists
        Path("data/objectives").mkdir(parents=True, exist_ok=True)
        
        # Get all objective files
        objectives = []
        objective_files = list(Path("data/objectives").glob("*.json"))
        
        for file_path in objective_files:
            try:
                with open(file_path, 'r') as f:
                    objective = json.load(f)
                
                # Check if it matches the period
                if objective.get('period') == period:
                    # Check permissions
                    if can_manage:
                        # Admins/managers can see all objectives
                        objectives.append(objective)
                    else:
                        # Regular users can only see their own objectives or company/team objectives
                        if (objective.get('owner_id') == user_id or 
                            objective.get('level') in ['company', 'team']):
                            objectives.append(objective)
            except Exception as e:
                st.warning(f"Error loading objective {file_path}: {str(e)}")
        
        return objectives
        
    except Exception as e:
        st.error(f"Error retrieving objectives: {str(e)}")
        return []

def get_all_objectives_for_user(user_id, can_manage=False):
    """Get all objectives for a user across all periods.
    
    Args:
        user_id (str): User ID
        can_manage (bool): Whether user can access all objectives
        
    Returns:
        list: List of objective dictionaries
    """
    try:
        # Ensure the objectives directory exists
        Path("data/objectives").mkdir(parents=True, exist_ok=True)
        
        # Get all objective files
        objectives = []
        objective_files = list(Path("data/objectives").glob("*.json"))
        
        for file_path in objective_files:
            try:
                with open(file_path, 'r') as f:
                    objective = json.load(f)
                
                # Check permissions
                if can_manage:
                    # Admins/managers can see all objectives
                    objectives.append(objective)
                else:
                    # Regular users can only see their own objectives or company/team objectives
                    if (objective.get('owner_id') == user_id or 
                        objective.get('level') in ['company', 'team']):
                        objectives.append(objective)
            except Exception as e:
                st.warning(f"Error loading objective {file_path}: {str(e)}")
        
        return objectives
        
    except Exception as e:
        st.error(f"Error retrieving objectives: {str(e)}")
        return []

def get_objective_by_id(objective_id):
    """Get an objective by its ID.
    
    Args:
        objective_id (str): Objective ID
        
    Returns:
        dict: Objective data if found, None otherwise
    """
    try:
        file_path = Path(f"data/objectives/{objective_id}.json")
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        st.error(f"Error retrieving objective: {str(e)}")
        return None

def save_objective(objective):
    """Save an objective to file.
    
    Args:
        objective (dict): Objective data to save
        
    Returns:
        str: Objective ID if saved successfully, None otherwise
    """
    try:
        # Ensure the objectives directory exists
        Path("data/objectives").mkdir(parents=True, exist_ok=True)
        
        # Generate ID if needed
        if 'id' not in objective:
            objective['id'] = str(uuid.uuid4())
        
        # Set timestamps
        if 'created_at' not in objective:
            objective['created_at'] = datetime.now().isoformat()
        objective['last_updated'] = datetime.now().isoformat()
        
        # Save to file
        with open(f"data/objectives/{objective['id']}.json", 'w') as f:
            json.dump(objective, f, indent=2)
        
        return objective['id']
        
    except Exception as e:
        st.error(f"Error saving objective: {str(e)}")
        return None

def calculate_objective_progress(objective):
    """Calculate the overall progress of an objective.
    
    Args:
        objective (dict): Objective data
        
    Returns:
        float: Progress percentage (0-100)
    """
    key_results = objective.get('key_results', [])
    if not key_results:
        return 0
    
    # Calculate average progress
    progress_sum = sum(kr.get('progress', 0) for kr in key_results)
    progress = progress_sum / len(key_results)
    
    return progress

def calculate_overall_progress(objectives):
    """Calculate the overall progress across multiple objectives.
    
    Args:
        objectives (list): List of objective dictionaries
        
    Returns:
        float: Overall progress percentage (0-100)
    """
    if not objectives:
        return 0
    
    # Calculate average progress across all objectives
    progress_sum = sum(calculate_objective_progress(obj) for obj in objectives)
    progress = progress_sum / len(objectives)
    
    return progress

def get_teams():
    """Get list of teams.
    
    Returns:
        list: List of team names
    """
    try:
        # This is a placeholder for a more sophisticated implementation
        # that would retrieve teams from a database or other source
        
        # For now, return some hardcoded teams
        default_teams = ["Management", "Engineering", "Marketing", "Sales", "Product", "Customer Success"]
        
        # Check if there's a teams file
        teams_file = Path("data/teams.json")
        if teams_file.exists():
            try:
                with open(teams_file, 'r') as f:
                    teams_data = json.load(f)
                return teams_data.get('teams', default_teams)
            except:
                return default_teams
        
        return default_teams
        
    except Exception as e:
        st.error(f"Error retrieving teams: {str(e)}")
        return ["General"]

def get_users():
    """Get list of users.
    
    Returns:
        list: List of user dictionaries
    """
    from utils.user_auth import get_all_users
    
    try:
        # Use the existing function to get all users
        return get_all_users()
        
    except Exception as e:
        st.error(f"Error retrieving users: {str(e)}")
        return []
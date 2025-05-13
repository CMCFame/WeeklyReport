# components/team_objectives.py
"""Team objectives component for the Weekly Report app."""

import streamlit as st
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import os

def render_team_objectives():
    """Render the team objectives management page."""
    st.title("Team Objectives")
    st.write("Set, track, and manage team objectives and key results (OKRs).")
    
    # Initialize state for objective tracking
    if 'objective_period' not in st.session_state:
        # Default to current quarter
        now = datetime.now()
        current_quarter = (now.month - 1) // 3 + 1
        year = now.year
        st.session_state.objective_period = f"Q{current_quarter} {year}"
    
    # Initialize key results state if creating a new objective
    if 'kr_count' not in st.session_state:
        st.session_state.kr_count = 1
    
    # Get user role for permissions
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    can_manage = user_role in ["admin", "manager"]
    
    # Tab navigation
    tabs = ["Current Objectives", "Progress Tracking"]
    if can_manage:
        tabs.append("Manage Objectives")
    
    selected_tabs = st.tabs(tabs)
    
    with selected_tabs[0]:
        render_current_objectives()
    
    with selected_tabs[1]:
        render_progress_tracking()
    
    if can_manage and len(selected_tabs) > 2:
        with selected_tabs[2]:
            render_manage_objectives()

def render_current_objectives():
    """Render the current objectives view."""
    # Period selector
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(f"Objectives for {st.session_state.objective_period}")
    
    with col2:
        # Generate period options
        now = datetime.now()
        year = now.year
        periods = []
        
        # Add quarters for current and next year
        for y in range(year - 1, year + 2):
            for q in range(1, 5):
                periods.append(f"Q{q} {y}")
        
        # Find the index of the current period
        try:
            current_period_idx = periods.index(st.session_state.objective_period)
        except ValueError:
            current_period_idx = 0
        
        # Period selector
        selected_period = st.selectbox(
            "Select Period",
            options=periods,
            index=current_period_idx
        )
        
        if selected_period != st.session_state.objective_period:
            st.session_state.objective_period = selected_period
            st.rerun()
    
    # Get objectives for the selected period
    objectives = get_objectives(st.session_state.objective_period)
    
    if not objectives:
        st.info(f"No objectives found for {st.session_state.objective_period}.")
        
        # Get user role for permissions
        user_role = st.session_state.get("user_info", {}).get("role", "team_member")
        can_manage = user_role in ["admin", "manager"]
        
        if can_manage:
            if st.button("Create Objectives for this Period"):
                st.session_state.creating_objective = True
                st.session_state.editing_objective = None
                st.rerun()
        return
    
    # Display company-level objectives first
    company_objectives = [obj for obj in objectives if obj.get('level') == 'company']
    if company_objectives:
        st.write("### Company Objectives")
        
        # Display each company objective
        for objective in company_objectives:
            render_objective_card(objective)
    
    # Display department/team objectives
    team_objectives = [obj for obj in objectives if obj.get('level') == 'team']
    if team_objectives:
        st.write("### Team Objectives")
        
        # Group by team
        teams = {}
        for objective in team_objectives:
            team = objective.get('team', 'Uncategorized')
            if team not in teams:
                teams[team] = []
            teams[team].append(objective)
        
        # Display by team
        for team, objs in teams.items():
            st.write(f"#### {team}")
            
            # Display each team objective
            for objective in objs:
                render_objective_card(objective)
    
    # Display individual objectives
    individual_objectives = [obj for obj in objectives if obj.get('level') == 'individual']
    
    # Only show individual objectives to the person they belong to or managers/admins
    user_id = st.session_state.get("user_info", {}).get("id")
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    
    # Filter individual objectives if user is not admin/manager
    if user_role not in ["admin", "manager"]:
        individual_objectives = [obj for obj in individual_objectives if obj.get('owner_id') == user_id]
    
    if individual_objectives:
        st.write("### Individual Objectives")
        
        # Group by owner
        owners = {}
        for objective in individual_objectives:
            owner = objective.get('owner_name', 'Unknown')
            if owner not in owners:
                owners[owner] = []
            owners[owner].append(objective)
        
        # Display by owner
        for owner, objs in owners.items():
            st.write(f"#### {owner}")
            
            # Display each individual objective
            for objective in objs:
                render_objective_card(objective)

def render_objective_card(objective):
    """Render a card for an objective.
    
    Args:
        objective (dict): Objective data
    """
    # Calculate overall progress
    key_results = objective.get('key_results', [])
    if key_results:
        total_progress = sum(kr.get('progress', 0) for kr in key_results) / len(key_results)
    else:
        total_progress = 0
    
    # Create a colored background based on progress
    progress_color = get_progress_color(total_progress)
    
    # Display the card
    with st.container():
        # First row: Title and progress
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"##### {objective.get('title', 'Untitled Objective')}")
        
        with col2:
            # Progress indicator
            st.progress(total_progress / 100)
            st.write(f"Progress: {total_progress:.0f}%")
        
        # Description
        st.write(objective.get('description', 'No description provided.'))
        
        # Key Results
        if key_results:
            with st.expander("Key Results", expanded=True):
                for i, kr in enumerate(key_results):
                    progress = kr.get('progress', 0)
                    kr_color = get_progress_color(progress)
                    
                    # Display progress bar and description
                    st.markdown(f"**KR{i+1}:** {kr.get('description', 'No description')}")
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.progress(progress / 100)
                    
                    with col2:
                        st.write(f"{progress:.0f}%")
                        
                    # Show latest updates if available
                    if 'updates' in kr and kr['updates']:
                        latest_update = kr['updates'][-1]
                        st.markdown(f"*Last update: {latest_update.get('date', '')} - {latest_update.get('note', '')}*")
        
        # Owner and status
        col1, col2 = st.columns(2)
        
        with col1:
            owner = objective.get('owner_name', 'Unassigned')
            st.write(f"**Owner:** {owner}")
        
        with col2:
            status = objective.get('status', 'In Progress')
            st.write(f"**Status:** {status}")
        
        # Add update button
        if st.button("Update Progress", key=f"update_{objective.get('id')}"):
            st.session_state.updating_objective = objective
            st.rerun()
        
        st.divider()
    
    # Show update form if this objective is being updated
    if hasattr(st.session_state, 'updating_objective') and st.session_state.updating_objective:
        if st.session_state.updating_objective.get('id') == objective.get('id'):
            with st.form(key=f"update_form_{objective.get('id')}"):
                st.write(f"### Update Progress for: {objective.get('title')}")
                
                # Allow updating each key result
                updated_key_results = []
                
                for i, kr in enumerate(key_results):
                    st.write(f"**Key Result {i+1}:** {kr.get('description')}")
                    
                    # Current progress
                    current_progress = kr.get('progress', 0)
                    
                    # New progress slider
                    new_progress = st.slider(
                        "Progress", 
                        min_value=0, 
                        max_value=100, 
                        value=int(current_progress),
                        key=f"kr_progress_{i}"
                    )
                    
                    # Update note
                    update_note = st.text_area(
                        "Update Note",
                        key=f"kr_note_{i}",
                        placeholder="Describe your progress or any challenges..."
                    )
                    
                    # Create an updated key result
                    updated_kr = kr.copy()
                    updated_kr['progress'] = new_progress
                    
                    # Add an update entry if there's a change or note
                    if new_progress != current_progress or update_note:
                        if 'updates' not in updated_kr:
                            updated_kr['updates'] = []
                        
                        updated_kr['updates'].append({
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'previous': current_progress,
                            'current': new_progress,
                            'note': update_note
                        })
                    
                    updated_key_results.append(updated_kr)
                    
                    st.divider()
                
                # Overall status update
                new_status = st.selectbox(
                    "Objective Status",
                    options=["On Track", "At Risk", "Behind", "Completed"],
                    index=["On Track", "At Risk", "Behind", "Completed"].index(objective.get('status', 'On Track'))
                )
                
                # Submit button
                submitted = st.form_submit_button("Save Progress Update")
                
                if submitted:
                    # Update the objective
                    updated_objective = objective.copy()
                    updated_objective['key_results'] = updated_key_results
                    updated_objective['status'] = new_status
                    updated_objective['last_updated'] = datetime.now().isoformat()
                    
                    # Save the updated objective
                    save_objective(updated_objective)
                    
                    # Clear the updating state
                    st.session_state.updating_objective = None
                    
                    st.success("Progress updated successfully!")
                    st.rerun()

def render_progress_tracking():
    """Render the progress tracking dashboard."""
    st.subheader("Progress Tracking")
    
    # Get objectives for the selected period
    objectives = get_objectives(st.session_state.objective_period)
    
    if not objectives:
        st.info(f"No objectives found for {st.session_state.objective_period}.")
        return
    
    # Calculate summary metrics
    total_objectives = len(objectives)
    total_key_results = sum(len(obj.get('key_results', [])) for obj in objectives)
    
    # Calculate overall progress
    all_key_results = []
    for obj in objectives:
        all_key_results.extend(obj.get('key_results', []))
    
    if all_key_results:
        overall_progress = sum(kr.get('progress', 0) for kr in all_key_results) / len(all_key_results)
    else:
        overall_progress = 0
    
    # Status counts
    status_counts = {
        "On Track": len([obj for obj in objectives if obj.get('status') == "On Track"]),
        "At Risk": len([obj for obj in objectives if obj.get('status') == "At Risk"]),
        "Behind": len([obj for obj in objectives if obj.get('status') == "Behind"]),
        "Completed": len([obj for obj in objectives if obj.get('status') == "Completed"])
    }
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Progress", f"{overall_progress:.0f}%")
    
    with col2:
        st.metric("Total Objectives", total_objectives)
    
    with col3:
        st.metric("Total Key Results", total_key_results)
    
    with col4:
        st.metric("Completed", status_counts["Completed"])
    
    # Progress by category
    st.subheader("Progress by Category")
    
    # Create data for visualizations
    data = {
        "Category": [],
        "Progress": []
    }
    
    # Company progress
    company_objectives = [obj for obj in objectives if obj.get('level') == 'company']
    if company_objectives:
        company_krs = []
        for obj in company_objectives:
            company_krs.extend(obj.get('key_results', []))
        
        if company_krs:
            company_progress = sum(kr.get('progress', 0) for kr in company_krs) / len(company_krs)
            data["Category"].append("Company")
            data["Progress"].append(company_progress)
    
    # Team progress
    team_objectives = [obj for obj in objectives if obj.get('level') == 'team']
    if team_objectives:
        # Group by team
        teams = {}
        for obj in team_objectives:
            team = obj.get('team', 'Uncategorized')
            if team not in teams:
                teams[team] = []
            teams[team].extend(obj.get('key_results', []))
        
        # Calculate progress by team
        for team, krs in teams.items():
            if krs:
                team_progress = sum(kr.get('progress', 0) for kr in krs) / len(krs)
                data["Category"].append(team)
                data["Progress"].append(team_progress)
    
    # Individual progress
    individual_objectives = [obj for obj in objectives if obj.get('level') == 'individual']
    if individual_objectives:
        # Group by owner
        owners = {}
        for obj in individual_objectives:
            owner = obj.get('owner_name', 'Unknown')
            if owner not in owners:
                owners[owner] = []
            owners[owner].extend(obj.get('key_results', []))
        
        # Calculate progress by owner
        for owner, krs in owners.items():
            if krs:
                owner_progress = sum(kr.get('progress', 0) for kr in krs) / len(krs)
                data["Category"].append(owner)
                data["Progress"].append(owner_progress)
    
    # Create a dataframe for visualization
    if data["Category"]:
        df = pd.DataFrame(data)
        
        # Display as bar chart
        st.bar_chart(df.set_index("Category"))
    else:
        st.info("No data available for visualization.")
    
    # Status breakdown
    st.subheader("Status Breakdown")
    
    # Create status data
    status_data = {
        "Status": list(status_counts.keys()),
        "Count": list(status_counts.values())
    }
    
    status_df = pd.DataFrame(status_data)
    
    # Display as bar chart
    st.bar_chart(status_df.set_index("Status"))
    
    # Recent updates
    st.subheader("Recent Updates")
    
    # Collect all updates
    all_updates = []
    
    for obj in objectives:
        for kr in obj.get('key_results', []):
            for update in kr.get('updates', []):
                all_updates.append({
                    "date": update.get('date', ''),
                    "objective": obj.get('title', 'Untitled'),
                    "key_result": kr.get('description', 'Untitled'),
                    "progress": f"{update.get('previous', 0):.0f}% → {update.get('current', 0):.0f}%",
                    "note": update.get('note', ''),
                    "owner": obj.get('owner_name', 'Unknown')
                })
    
    # Sort by date (most recent first)
    all_updates.sort(key=lambda x: x['date'], reverse=True)
    
    # Display recent updates
    if all_updates:
        updates_df = pd.DataFrame(all_updates)
        st.dataframe(updates_df, use_container_width=True)
    else:
        st.info("No updates recorded yet.")

def render_manage_objectives():
    """Render the objective management interface (for admins and managers)."""
    st.subheader("Manage Objectives")
    
    # Check if user has permission
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    if user_role not in ["admin", "manager"]:
        st.warning("You do not have permission to manage objectives.")
        return
    
    # Get objectives for the selected period
    objectives = get_objectives(st.session_state.objective_period)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Create New Objective", type="primary"):
            st.session_state.creating_objective = True
            st.session_state.editing_objective = None
            st.session_state.kr_count = 1  # Initialize with one key result
            st.rerun()
    
    with col2:
        if st.button("Delete All Objectives for Period"):
            # Show a confirmation dialog
            st.warning(f"Are you sure you want to delete ALL objectives for {st.session_state.objective_period}?")
            
            confirm_col1, confirm_col2 = st.columns(2)
            
            with confirm_col1:
                if st.button("Yes, delete all"):
                    delete_all_objectives(st.session_state.objective_period)
                    st.success(f"All objectives for {st.session_state.objective_period} deleted.")
                    st.rerun()
            
            with confirm_col2:
                if st.button("Cancel"):
                    st.rerun()
    
    with col3:
        if st.button("Copy Objectives from Previous Period"):
            # Show a form to select the source period
            periods = []
            
            # Generate period options
            now = datetime.now()
            year = now.year
            
            # Add quarters for current and previous year
            for y in range(year - 1, year + 1):
                for q in range(1, 5):
                    period = f"Q{q} {y}"
                    if period != st.session_state.objective_period:
                        periods.append(period)
            
            source_period = st.selectbox(
                "Copy from period",
                options=periods
            )
            
            if st.button("Copy Objectives", key="confirm_copy"):
                # Get objectives from the source period
                source_objectives = get_objectives(source_period)
                
                if not source_objectives:
                    st.error(f"No objectives found for {source_period}.")
                else:
                    # Copy objectives to new period
                    copied_count = copy_objectives(source_objectives, st.session_state.objective_period)
                    st.success(f"Copied {copied_count} objectives from {source_period} to {st.session_state.objective_period}.")
                    st.rerun()
    
    # Display existing objectives in a management table
    if objectives:
        st.subheader(f"Objectives for {st.session_state.objective_period}")
        
        # Create a table-like display
        for obj in objectives:
            with st.expander(f"{obj.get('title', 'Untitled')} ({obj.get('level', 'unknown').capitalize()})"):
                # Display objective details
                st.write(f"**Description:** {obj.get('description', 'No description')}")
                st.write(f"**Level:** {obj.get('level', 'unknown').capitalize()}")
                
                if obj.get('level') == 'team':
                    st.write(f"**Team:** {obj.get('team', 'Unassigned')}")
                
                st.write(f"**Owner:** {obj.get('owner_name', 'Unassigned')}")
                st.write(f"**Status:** {obj.get('status', 'In Progress')}")
                
                # Display key results
                st.write("**Key Results:**")
                for i, kr in enumerate(obj.get('key_results', [])):
                    st.write(f"{i+1}. {kr.get('description', 'No description')} - {kr.get('progress', 0):.0f}%")
                
                # Action buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Edit", key=f"edit_{obj.get('id')}"):
                        st.session_state.editing_objective = obj
                        st.session_state.creating_objective = False
                        st.session_state.kr_count = len(obj.get('key_results', []))
                        st.rerun()
                
                with col2:
                    if st.button("Delete", key=f"delete_{obj.get('id')}"):
                        if delete_objective(obj.get('id')):
                            st.success("Objective deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete objective.")
    else:
        st.info(f"No objectives found for {st.session_state.objective_period}.")
    
    # Display creation/editing form if needed
    if hasattr(st.session_state, 'creating_objective') and st.session_state.creating_objective:
        render_objective_form(None, st.session_state.objective_period)
    
    if hasattr(st.session_state, 'editing_objective') and st.session_state.editing_objective:
        render_objective_form(st.session_state.editing_objective, st.session_state.objective_period)

def render_objective_form(objective, period):
    """Render form for creating or editing an objective.
    
    Args:
        objective (dict): Objective data if editing, None if creating
        period (str): The period for the objective
    """
    # Set title based on mode
    if objective:
        st.subheader("Edit Objective")
        form_key = f"edit_objective_{objective.get('id')}"
    else:
        st.subheader("Create New Objective")
        form_key = "create_objective"
        objective = {
            'period': period,
            'level': 'company',
            'status': 'On Track',
            'key_results': [{'description': '', 'progress': 0}]
        }
    
    # Key results management controls OUTSIDE the form
    kr_count = st.session_state.kr_count
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+ Add Key Result", key="add_kr_outside_form"):
            st.session_state.kr_count += 1
            st.rerun()
    
    with col2:
        if kr_count > 1 and st.button("- Remove Last Key Result", key="remove_kr_outside_form"):
            st.session_state.kr_count -= 1
            st.rerun()
            
    # Now create the form with no buttons inside except the submit button
    with st.form(key=form_key):
        # Basic info
        title = st.text_input(
            "Objective Title",
            value=objective.get('title', ''),
            help="A concise statement of what you want to achieve"
        )
        
        description = st.text_area(
            "Description",
            value=objective.get('description', ''),
            help="More detailed explanation of the objective"
        )
        
        # Objective level
        level = st.selectbox(
            "Level",
            options=["company", "team", "individual"],
            index=["company", "team", "individual"].index(objective.get('level', 'company')),
            format_func=lambda x: x.capitalize(),
            help="The scope of this objective"
        )
        
        # Team selection (if team level)
        team = None
        if level == "team":
            # Get user's teams
            teams = get_teams()
            
            default_index = 0
            if objective.get('team') in teams:
                default_index = teams.index(objective.get('team'))
            
            team = st.selectbox(
                "Team",
                options=teams,
                index=default_index,
                help="The team this objective belongs to"
            )
        
        # Owner selection
        if level == "individual":
            # Get all users
            users = get_users()
            
            # Create options for selectbox
            user_ids = [user.get('id') for user in users]
            
            default_index = 0
            if objective.get('owner_id') in user_ids:
                default_index = user_ids.index(objective.get('owner_id'))
            
            owner_id = st.selectbox(
                "Owner",
                options=user_ids,
                index=default_index,
                format_func=lambda x: next((user.get('full_name') for user in users if user.get('id') == x), "Unknown"),
                help="The person responsible for this objective"
            )
            
            # Get owner name for display
            owner_name = next((user.get('full_name') for user in users if user.get('id') == owner_id), "Unknown")
        else:
            # For company and team levels, owner is the current user
            owner_id = st.session_state.user_info.get('id')
            owner_name = st.session_state.user_info.get('full_name', 'Unknown')
        
        # Status
        status = st.selectbox(
            "Status",
            options=["On Track", "At Risk", "Behind", "Completed"],
            index=["On Track", "At Risk", "Behind", "Completed"].index(objective.get('status', 'On Track')),
            help="Current status of this objective"
        )
        
        # Key Results
        st.subheader("Key Results")
        st.write("Define measurable outcomes that will indicate success.")
        
        # Get existing key results or initialize new ones
        existing_key_results = objective.get('key_results', [])
        
        # Make sure we have the right number based on kr_count
        while len(existing_key_results) < kr_count:
            existing_key_results.append({'description': '', 'progress': 0})
        
        # Limit to current kr_count
        key_results = existing_key_results[:kr_count]
        
        # Render key result fields
        updated_key_results = []
        for i in range(kr_count):
            kr = key_results[i] if i < len(key_results) else {'description': '', 'progress': 0}
            
            with st.container():
                st.write(f"**Key Result {i+1}**")
                
                # Description
                kr_description = st.text_area(
                    "Description",
                    value=kr.get('description', ''),
                    key=f"kr_desc_{i}",
                    help="What specific, measurable outcome will indicate success?",
                    height=100
                )
                
                # Progress (if editing)
                kr_progress = 0
                if objective.get('id'):  # Existing objective
                    kr_progress = st.slider(
                        "Progress",
                        min_value=0,
                        max_value=100,
                        value=int(kr.get('progress', 0)),
                        key=f"kr_prog_{i}"
                    )
                
                # Update key result
                updated_kr = {
                    'description': kr_description,
                    'progress': kr_progress
                }
                
                # Preserve updates if they exist
                if 'updates' in kr:
                    updated_kr['updates'] = kr['updates']
                
                updated_key_results.append(updated_kr)
                
                if i < kr_count - 1:  # Add divider between key results but not after the last one
                    st.divider()
        
        # Submit button (ONLY BUTTON INSIDE THE FORM)
        submit_label = "Update Objective" if objective.get('id') else "Create Objective"
        submitted = st.form_submit_button(submit_label, type="primary")
        
        if submitted:
            if not title:
                st.error("Please provide an objective title.")
            elif not updated_key_results or not any(kr.get('description') for kr in updated_key_results):
                st.error("Please provide at least one key result.")
            else:
                # Prepare objective data
                objective_data = {
                    'id': objective.get('id', str(uuid.uuid4())),
                    'title': title,
                    'description': description,
                    'level': level,
                    'status': status,
                    'period': period,
                    'key_results': updated_key_results,
                    'owner_id': owner_id,
                    'owner_name': owner_name,
                    'created_at': objective.get('created_at', datetime.now().isoformat()),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Add team if applicable
                if level == "team" and team:
                    objective_data['team'] = team
                
                # Save objective
                save_objective(objective_data)
                
                # Success message
                if objective.get('id'):
                    st.success("Objective updated successfully!")
                else:
                    st.success("Objective created successfully!")
                
                # Clear form state
                st.session_state.creating_objective = False
                st.session_state.editing_objective = None
                
                # Rerun to refresh the page
                st.rerun()

def get_objectives(period):
    """Get objectives for a specific period.
    
    Args:
        period (str): Period (e.g., Q1 2023)
        
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
                    objectives.append(objective)
                    
            except Exception as e:
                st.warning(f"Error loading objective {file_path}: {str(e)}")
        
        return objectives
        
    except Exception as e:
        st.error(f"Error retrieving objectives: {str(e)}")
        return []

def save_objective(objective):
    """Save an objective to file.
    
    Args:
        objective (dict): Objective data to save
        
    Returns:
        str: Objective ID
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

def delete_objective(objective_id):
    """Delete an objective file.
    
    Args:
        objective_id (str): ID of the objective to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        # Check if file exists
        file_path = Path(f"data/objectives/{objective_id}.json")
        if not file_path.exists():
            st.error(f"Objective with ID {objective_id} not found.")
            return False
        
        # Delete file
        file_path.unlink()
        return True
        
    except Exception as e:
        st.error(f"Error deleting objective: {str(e)}")
        return False

def delete_all_objectives(period):
    """Delete all objectives for a specific period.
    
    Args:
        period (str): Period (e.g., Q1 2023)
        
    Returns:
        int: Number of objectives deleted
    """
    try:
        # Get all objectives for the period
        objectives = get_objectives(period)
        
        # Delete each objective
        deleted_count = 0
        for objective in objectives:
            if delete_objective(objective.get('id')):
                deleted_count += 1
        
        return deleted_count
        
    except Exception as e:
        st.error(f"Error deleting objectives: {str(e)}")
        return 0

def copy_objectives(source_objectives, target_period):
    """Copy objectives from one period to another.
    
    Args:
        source_objectives (list): List of source objective dictionaries
        target_period (str): Target period (e.g., Q1 2023)
        
    Returns:
        int: Number of objectives copied
    """
    try:
        # Copy each objective
        copied_count = 0
        for objective in source_objectives:
            # Create a new objective based on the source
            new_objective = objective.copy()
            
            # Clear ID and timestamps
            new_objective.pop('id', None)
            new_objective.pop('created_at', None)
            new_objective.pop('last_updated', None)
            
            # Update period
            new_objective['period'] = target_period
            
            # Reset progress and status
            new_objective['status'] = 'On Track'
            
            # Reset key results progress and updates
            for kr in new_objective.get('key_results', []):
                kr['progress'] = 0
                kr.pop('updates', None)
            
            # Save the new objective
            if save_objective(new_objective):
                copied_count += 1
        
        return copied_count
        
    except Exception as e:
        st.error(f"Error copying objectives: {str(e)}")
        return 0

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

def get_progress_color(progress):
    """Get a color based on progress value.
    
    Args:
        progress (float): Progress value (0-100)
        
    Returns:
        str: Hex color code
    """
    if progress >= 80:
        return "#28a745"  # Green
    elif progress >= 50:
        return "#17a2b8"  # Blue
    elif progress >= 25:
        return "#ffc107"  # Yellow
    else:
        return "#dc3545"  # Red
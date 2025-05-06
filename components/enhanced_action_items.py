# components/enhanced_action_items.py
"""Enhanced action items component for the Weekly Report app."""

import streamlit as st
from utils import session
from utils.csv_utils import get_user_projects, get_project_milestones
import pandas as pd
import json

def render_enhanced_action_items():
    """Render the enhanced action items section.
    
    This section has two parts with improved UI:
    1. Follow-up tasks from the last meeting
    2. Next steps planned for the coming week
    """
    st.header('📋 Action Items')
    
    # Follow-up tasks from last meeting
    st.subheader('From Last Meeting')
    st.write('What follow-up tasks were assigned to you?')
    render_enhanced_item_list('followups', 'Follow-up')
    
    if st.button('+ Add Another Follow-up'):
        session.add_item_to_list('followups')
        st.rerun()
    
    # Next steps
    st.subheader('Next Steps')
    st.write('What action items are planned for next week?')
    render_enhanced_item_list('nextsteps', 'Next Step')
    
    # Button to add preloaded next steps from previous reports
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button('+ Add Another Next Step'):
            session.add_item_to_list('nextsteps')
            st.rerun()
    
    with col2:
        if st.button('Load Next Steps from Previous Report'):
            load_next_steps_from_previous_report()
            st.rerun()

def render_enhanced_item_list(key, label_prefix):
    """Render a list of items with enhanced functionality.
    
    Args:
        key (str): Session state key for the list
        label_prefix (str): Label prefix for each item
    """
    item_list = st.session_state.get(key, [""])
    
    # Get username for project filtering
    username = ""
    if st.session_state.get("user_info"):
        username = st.session_state.user_info.get("username", "")
    
    # Get all projects for the user
    all_projects = get_user_projects(username)
    if not all_projects:
        all_projects = []
    
    # Add empty option
    all_projects = [''] + all_projects
    
    # Display reordering UI if there's more than one item
    if len(item_list) > 1:
        st.write("Drag to reorder items (higher items = higher priority)")
        
        # Create a dataframe for reordering
        df = pd.DataFrame({
            "index": range(len(item_list)),
            "item": item_list
        })
        
        # Use the experimental data editor for drag and drop
        edited_df = st.data_editor(
            df,
            column_config={
                "index": st.column_config.NumberColumn(
                    "Order",
                    help="Drag to reorder",
                    width="small",
                ),
                "item": st.column_config.TextColumn(
                    f"{label_prefix}s",
                    width="large",
                ),
            },
            disabled=["index"],
            hide_index=True,
            key=f"editor_{key}"
        )
        
        # Update the session state if the order changed
        if not edited_df.equals(df):
            # Get the new order of items
            new_items = edited_df["item"].tolist()
            st.session_state[key] = new_items
    
    # Render each item with enhanced features
    for i, item in enumerate(item_list):
        st.markdown("---")
        
        # Item content
        content_col, proj_col = st.columns([2, 1])
        
        with content_col:
            updated_item = st.text_area(
                f"{label_prefix} {i+1}" if i > 0 else label_prefix, 
                value=item, 
                key=f"{key}_{i}_content", 
                label_visibility="collapsed",
                height=80
            )
            
            # Extract project and milestone from the item if they exist
            item_data = {}
            if updated_item and updated_item.startswith('{') and updated_item.endswith('}'):
                try:
                    item_data = json.loads(updated_item)
                    updated_item = item_data.get('text', '')
                except:
                    pass
            
            # Update the content
            if isinstance(updated_item, str):
                if not updated_item.startswith('{'):
                    if 'project' in item_data or 'milestone' in item_data:
                        # Preserve the project/milestone data
                        item_data['text'] = updated_item
                        session.update_item_list(key, i, json.dumps(item_data))
                    else:
                        session.update_item_list(key, i, updated_item)
        
        with proj_col:
            # Add project and milestone selectors
            sel_project = ""
            sel_milestone = ""
            
            # Extract existing project/milestone if in JSON format
            if item and item.startswith('{') and item.endswith('}'):
                try:
                    item_data = json.loads(item)
                    sel_project = item_data.get('project', '')
                    sel_milestone = item_data.get('milestone', '')
                except:
                    pass
            
            # Project selector
            selected_project = st.selectbox(
                "Related Project", 
                options=all_projects,
                index=all_projects.index(sel_project) if sel_project in all_projects else 0,
                key=f"{key}_{i}_project"
            )
            
            # Milestone selector (only show if project is selected)
            milestones = ['']
            if selected_project:
                project_milestones = get_project_milestones(selected_project)
                if project_milestones:
                    milestones.extend(project_milestones)
            
            selected_milestone = st.selectbox(
                "Related Milestone",
                options=milestones,
                index=milestones.index(sel_milestone) if sel_milestone in milestones else 0,
                key=f"{key}_{i}_milestone"
            )
            
            # If project or milestone changed, update the item
            if (selected_project != sel_project or selected_milestone != sel_milestone):
                # Get the current item text
                text = updated_item
                if item and item.startswith('{') and item.endswith('}'):
                    try:
                        item_data = json.loads(item)
                        text = item_data.get('text', '')
                    except:
                        pass
                
                # Create new item data
                new_item_data = {
                    'text': text,
                    'project': selected_project,
                    'milestone': selected_milestone
                }
                
                # Update the session state
                session.update_item_list(key, i, json.dumps(new_item_data))
        
        # Remove button
        if len(item_list) > 1 and st.button('🗑️ Remove', key=f"remove_{key}_{i}"):
            session.remove_item_from_list(key, i)
            st.rerun()

def load_next_steps_from_previous_report():
    """Load next steps from the most recent previous report into current followups."""
    from utils.file_ops import get_all_reports
    
    # Get previous reports
    reports = get_all_reports(filter_by_user=True)
    
    if not reports or len(reports) < 1:
        st.warning("No previous reports found.")
        return
    
    # Get the most recent report
    latest_report = reports[0]
    
    # Check if it has next steps
    next_steps = latest_report.get('nextsteps', [])
    
    if not next_steps:
        st.info("No next steps found in your most recent report.")
        return
    
    # Convert next steps to followups
    current_followups = st.session_state.get('followups', [""])
    
    # Remove empty items
    if len(current_followups) == 1 and not current_followups[0]:
        current_followups = []
    
    # Add the next steps from previous report
    for step in next_steps:
        if step:  # Only add non-empty steps
            current_followups.append(step)
    
    # Update session state
    st.session_state.followups = current_followups
    
    # Success message
    st.success(f"Loaded {len(next_steps)} next steps from your previous report.")
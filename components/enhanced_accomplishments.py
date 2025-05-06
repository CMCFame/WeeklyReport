# components/enhanced_accomplishments.py
"""Enhanced accomplishments component for the Weekly Report app."""

import streamlit as st
from utils import session
from utils.csv_utils import get_user_projects, get_project_milestones
import pandas as pd
import json

def render_enhanced_accomplishments():
    """Render the enhanced last week's accomplishments section.
    
    This section allows users to add, edit, and remove accomplishments
    with improved UI including project linking and reordering.
    """
    st.header('✓ Last Week\'s Accomplishments')
    st.write('What did you accomplish last week? (Bullet points work best)')
    
    # Add templates/suggestions
    with st.expander("Need inspiration? Click here for templates"):
        st.write("Click a template to add it to your accomplishments:")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Completed task"):
                add_template_accomplishment("Completed [task] for [project]")
            
            if st.button("📊 Made progress"):
                add_template_accomplishment("Made progress on [task] by [specific action]")
            
            if st.button("🛠️ Fixed issue"):
                add_template_accomplishment("Fixed [issue] that was affecting [impact area]")
        
        with col2:
            if st.button("📢 Conducted meeting"):
                add_template_accomplishment("Conducted meeting with [team/stakeholder] to discuss [topic]")
            
            if st.button("🎯 Reached milestone"):
                add_template_accomplishment("Reached milestone: [milestone] on [project]")
            
            if st.button("📝 Created document"):
                add_template_accomplishment("Created [document/report] for [purpose]")
    
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
    accomplishments = st.session_state.get('accomplishments', [""])
    
    if len(accomplishments) > 1:
        st.write("Drag to reorder accomplishments (most important at the top)")
        
        # Create a dataframe for reordering
        df = pd.DataFrame({
            "index": range(len(accomplishments)),
            "accomplishment": accomplishments
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
                "accomplishment": st.column_config.TextColumn(
                    "Accomplishment",
                    width="large",
                ),
            },
            disabled=["index"],
            hide_index=True,
            key="editor_accomplishments"
        )
        
        # Update the session state if the order changed
        if not edited_df.equals(df):
            # Get the new order of items
            new_items = edited_df["accomplishment"].tolist()
            st.session_state.accomplishments = new_items
    
    # Render each accomplishment item with enhanced features
    for i, accomplishment in enumerate(st.session_state.accomplishments):
        st.markdown("---")
        
        # Accomplishment content
        content_col, proj_col = st.columns([2, 1])
        
        with content_col:
            # Extract actual text if stored as JSON
            display_text = accomplishment
            if accomplishment and accomplishment.startswith('{') and accomplishment.endswith('}'):
                try:
                    acc_data = json.loads(accomplishment)
                    display_text = acc_data.get('text', accomplishment)
                except:
                    pass
            
            updated_accomplishment = st.text_area(
                f"Accomplishment {i+1}" if i > 0 else "Accomplishment", 
                value=display_text, 
                key=f"accomplishment_{i}_content", 
                label_visibility="collapsed",
                height=80
            )
            
            # Extract project and milestone if they exist
            acc_data = {}
            if accomplishment and accomplishment.startswith('{') and accomplishment.endswith('}'):
                try:
                    acc_data = json.loads(accomplishment)
                except:
                    pass
            
            # Update the content
            if updated_accomplishment != display_text:
                if 'project' in acc_data or 'milestone' in acc_data:
                    # Preserve the project/milestone data
                    acc_data['text'] = updated_accomplishment
                    session.update_item_list('accomplishments', i, json.dumps(acc_data))
                else:
                    session.update_item_list('accomplishments', i, updated_accomplishment)
        
        with proj_col:
            # Add project and milestone selectors
            sel_project = ""
            sel_milestone = ""
            
            # Extract existing project/milestone if in JSON format
            if accomplishment and accomplishment.startswith('{') and accomplishment.endswith('}'):
                try:
                    acc_data = json.loads(accomplishment)
                    sel_project = acc_data.get('project', '')
                    sel_milestone = acc_data.get('milestone', '')
                except:
                    pass
            
            # Project selector
            selected_project = st.selectbox(
                "Related Project", 
                options=all_projects,
                index=all_projects.index(sel_project) if sel_project in all_projects else 0,
                key=f"accomplishment_{i}_project"
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
                key=f"accomplishment_{i}_milestone"
            )
            
            # If project or milestone changed, update the item
            if (selected_project != sel_project or selected_milestone != sel_milestone):
                # Get the current text
                text = updated_accomplishment
                if accomplishment and accomplishment.startswith('{') and accomplishment.endswith('}'):
                    try:
                        acc_data = json.loads(accomplishment)
                        text = acc_data.get('text', updated_accomplishment)
                    except:
                        pass
                
                # Create new item data
                new_acc_data = {
                    'text': text,
                    'project': selected_project,
                    'milestone': selected_milestone
                }
                
                # Update the session state
                session.update_item_list('accomplishments', i, json.dumps(new_acc_data))
        
        # Remove button in a new row for cleaner layout
        if len(st.session_state.accomplishments) > 1:
            if st.button('🗑️ Remove', key=f"remove_acc_{i}"):
                session.remove_item_from_list('accomplishments', i)
                st.rerun()
    
    # Add button
    if st.button('+ Add Another Accomplishment'):
        session.add_item_to_list('accomplishments')
        st.rerun()

def add_template_accomplishment(template_text):
    """Add a template accomplishment to the list.
    
    Args:
        template_text (str): Template text to add
    """
    accomplishments = st.session_state.get('accomplishments', [""])
    
    # If the first item is empty, replace it
    if len(accomplishments) == 1 and not accomplishments[0]:
        accomplishments[0] = template_text
    else:
        # Otherwise add a new item
        accomplishments.append(template_text)
    
    st.session_state.accomplishments = accomplishments
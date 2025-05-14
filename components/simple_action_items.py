# components/simple_action_items.py
"""Simplified action items component for the Weekly Report app."""

import streamlit as st
from utils import session
from utils.file_ops import get_all_reports

def render_simple_action_items():
    """Render the simplified action items section.
    
    This section has two parts with improved UI but minimal complexity:
    1. Follow-up tasks from the last meeting
    2. Next steps planned for the coming week
    """
    st.header('📋 Action Items')
    
    # Follow-up tasks from last meeting
    st.subheader('From Last Meeting')
    st.write('What follow-up tasks were assigned to you?')
    
    # Button to load next steps from previous reports as follow-ups
    load_col1, load_col2 = st.columns([3, 1])
    
    with load_col1:
        st.write("Load from your previous report to save time:")
    
    with load_col2:
        if st.button('Load Previous Next Steps', help="Import next steps from your last report as follow-ups"):
            load_next_steps_from_previous_report()
            st.rerun()
    
    # Render follow-up items
    render_simple_item_list('followups', 'Follow-up')
    
    if st.button('+ Add Another Follow-up', use_container_width=True):
        session.add_item_to_list('followups')
        st.rerun()
    
    # Next steps
    st.subheader('Next Steps')
    st.write('What action items are planned for next week?')
    
    # Quick-add buttons for common next steps
    st.write("Quick-add common next steps:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📆 Schedule Meeting", use_container_width=True):
            add_template_next_step("Schedule meeting with [person/team] for [topic]")
    
    with col2:
        if st.button("📝 Create Document", use_container_width=True):
            add_template_next_step("Create [document/report] for [purpose]")
    
    with col3:
        if st.button("✅ Complete Task", use_container_width=True):
            add_template_next_step("Complete [task] by [date]")
    
    # Render next step items
    render_simple_item_list('nextsteps', 'Next Step')
    
    if st.button('+ Add Another Next Step', use_container_width=True):
        session.add_item_to_list('nextsteps')
        st.rerun()

def render_simple_item_list(key, label_prefix):
    """Render a list of items with simplified UI.
    
    Args:
        key (str): Session state key for the list
        label_prefix (str): Label prefix for each item
    """
    item_list = st.session_state.get(key, [""])
    
    for i, item in enumerate(item_list):
        col1, col2 = st.columns([10, 1])
        
        with col1:
            # Generate placeholder based on the type of item
            placeholder = "Describe this follow-up task..." if key == 'followups' else "Describe this planned action..."
            
            updated_item = st.text_area(
                f"{label_prefix} {i+1}" if i > 0 else label_prefix, 
                value=item, 
                key=f"{key}_{i}", 
                label_visibility="collapsed",
                height=80,
                placeholder=placeholder
            )
            session.update_item_list(key, i, updated_item)
        
        with col2:
            if len(item_list) > 1 and st.button('🗑️', key=f"remove_{key}_{i}"):
                session.remove_item_from_list(key, i)
                st.rerun()

def load_next_steps_from_previous_report():
    """Load next steps from the most recent previous report into current followups."""
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

def add_template_next_step(template_text):
    """Add a template next step to the list.
    
    Args:
        template_text (str): Template text to add
    """
    next_steps = st.session_state.get('nextsteps', [""])
    
    # If the first item is empty, replace it
    if len(next_steps) == 1 and not next_steps[0]:
        next_steps[0] = template_text
    else:
        # Otherwise add a new item
        next_steps.append(template_text)
    
    st.session_state.nextsteps = next_steps
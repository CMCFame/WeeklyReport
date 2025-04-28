# components/action_items.py
"""Action items component for the Weekly Report app."""

import streamlit as st
from utils import session

def render_action_items():
    """Render the action items section.
    
    This section has two parts:
    1. Follow-up tasks from the last meeting
    2. Next steps planned for the coming week
    """
    st.header('📋 Action Items')
    
    # Follow-up tasks from last meeting
    st.subheader('From Last Meeting')
    st.write('What follow-up tasks were assigned to you?')
    render_item_list('followups', 'Follow-up')
    
    if st.button('+ Add Another Follow-up'):
        session.add_item_to_list('followups')
        st.rerun()
    
    # Next steps
    st.subheader('Next Steps')
    st.write('What action items are planned for next week?')
    render_item_list('nextsteps', 'Next Step')
    
    if st.button('+ Add Another Next Step'):
        session.add_item_to_list('nextsteps')
        st.rerun()

def render_item_list(key, label_prefix):
    """Render a list of items with add/remove functionality.
    
    Args:
        key (str): Session state key for the list
        label_prefix (str): Label prefix for each item
    """
    item_list = st.session_state.get(key, [""])
    
    for i, item in enumerate(item_list):
        col1, col2 = st.columns([10, 1])
        
        with col1:
            updated_item = st.text_area(
                f"{label_prefix} {i+1}" if i > 0 else label_prefix, 
                value=item, 
                key=f"{key}_{i}", 
                label_visibility="collapsed",
                height=80
            )
            session.update_item_list(key, i, updated_item)
        
        with col2:
            if len(item_list) > 1 and st.button('🗑️', key=f"remove_{key}_{i}"):
                session.remove_item_from_list(key, i)
                st.rerun()
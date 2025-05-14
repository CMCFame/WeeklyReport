# components/simple_accomplishments.py
"""Simplified accomplishments component for the Weekly Report app."""

import streamlit as st
from utils import session

def render_simple_accomplishments():
    """Render the simplified last week's accomplishments section.
    
    This section allows users to add, edit, and remove accomplishments
    with helpful templates and minimal complexity.
    """
    st.header('✓ Last Week\'s Accomplishments')
    st.write('What did you accomplish last week? (Bullet points work best)')
    
    # Quick-add buttons for common accomplishment types
    st.write("Quick-add common accomplishments:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Completed Task", use_container_width=True):
            add_template_accomplishment("Completed [task] for [project]")
    
    with col2:
        if st.button("📊 Made Progress", use_container_width=True):
            add_template_accomplishment("Made progress on [task] by [specific action]")
    
    with col3:
        if st.button("🛠️ Fixed Issue", use_container_width=True):
            add_template_accomplishment("Fixed [issue] that was affecting [impact]")
    
    # Quick-add buttons for additional accomplishment types
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📢 Meeting/Discussion", use_container_width=True):
            add_template_accomplishment("Held meeting with [team/person] about [topic]")
    
    with col2:
        if st.button("🎯 Milestone Reached", use_container_width=True):
            add_template_accomplishment("Reached milestone: [milestone] on [project]")
    
    with col3:
        if st.button("📝 Created Document", use_container_width=True):
            add_template_accomplishment("Created [document/report] for [purpose]")
    
    # Render each accomplishment item with simplified UI
    for i, accomplishment in enumerate(st.session_state.accomplishments):
        col1, col2 = st.columns([10, 1])
        
        with col1:
            updated_accomplishment = st.text_area(
                f"Accomplishment {i+1}" if i > 0 else "Accomplishment", 
                value=accomplishment, 
                key=f"accomplishment_{i}", 
                label_visibility="collapsed",
                height=80,
                placeholder="Describe your accomplishment here..."
            )
            session.update_item_list('accomplishments', i, updated_accomplishment)
        
        with col2:
            if len(st.session_state.accomplishments) > 1 and st.button('🗑️', key=f"remove_acc_{i}"):
                session.remove_item_from_list('accomplishments', i)
                st.rerun()
    
    # Add button
    if st.button('+ Add Another Accomplishment', use_container_width=True):
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
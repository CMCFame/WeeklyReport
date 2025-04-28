# components/accomplishments.py
"""Accomplishments component for the Weekly Report app."""

import streamlit as st
from utils import session

def render_accomplishments():
    """Render the last week's accomplishments section.
    
    This section allows users to add, edit, and remove accomplishments
    from the previous week in a bullet-point format.
    """
    st.header('✓ Last Week\'s Accomplishments')
    st.write('What did you accomplish last week? (Bullet points work best)')
    
    # Render each accomplishment item
    for i, accomplishment in enumerate(st.session_state.accomplishments):
        col1, col2 = st.columns([10, 1])
        
        with col1:
            updated_accomplishment = st.text_area(
                f"Accomplishment {i+1}" if i > 0 else "Accomplishment", 
                value=accomplishment, 
                key=f"accomplishment_{i}", 
                label_visibility="collapsed",
                height=80
            )
            session.update_item_list('accomplishments', i, updated_accomplishment)
        
        with col2:
            if len(st.session_state.accomplishments) > 1 and st.button('🗑️', key=f"remove_acc_{i}"):
                session.remove_item_from_list('accomplishments', i)
                st.rerun()
    
    # Add button
    if st.button('+ Add Another Accomplishment'):
        session.add_item_to_list('accomplishments')
        st.rerun()
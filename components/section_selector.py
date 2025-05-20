# components/section_selector.py
"""Section selector component for the Weekly Report app."""

import streamlit as st
from utils.constants import OPTIONAL_SECTIONS

def render_section_selector():
    """Render a section selector for customizing the weekly report."""
    st.header('Report Sections')
    st.write('Select which sections to include in your report:')
    
    # Define the core sections that are available to toggle
    CORE_SECTIONS = [
        {
            'key': 'show_current_activities',
            'label': 'Current Activities',
            'icon': '📊',
            'description': 'What are you currently working on?'
        },
        {
            'key': 'show_upcoming_activities',
            'label': 'Upcoming Activities',
            'icon': '📅',
            'description': 'What activities are planned for the near future?'
        },
        {
            'key': 'show_accomplishments',
            'label': 'Last Week\'s Accomplishments',
            'icon': '✓',
            'description': 'What did you accomplish last week?'
        },
        {
            'key': 'show_action_items',
            'label': 'Action Items',
            'icon': '📋',
            'description': 'What follow-up tasks and next steps do you have?'
        }
    ]
    
    # Initialize session state for section toggles if they don't exist
    for section in CORE_SECTIONS:
        if section['key'] not in st.session_state:
            st.session_state[section['key']] = True  # Core sections are on by default
    
    # Core sections
    st.subheader('Core Sections')
    
    # Create two columns for better layout
    col1, col2 = st.columns(2)
    
    # Split sections between columns
    half = len(CORE_SECTIONS) // 2 + len(CORE_SECTIONS) % 2
    
    with col1:
        for section in CORE_SECTIONS[:half]:
            st.session_state[section['key']] = st.toggle(
                f"{section['icon']} {section['label']}", 
                value=st.session_state.get(section['key'], True),
                help=section['description']
            )
    
    with col2:
        for section in CORE_SECTIONS[half:]:
            st.session_state[section['key']] = st.toggle(
                f"{section['icon']} {section['label']}", 
                value=st.session_state.get(section['key'], True),
                help=section['description']
            )
    
    # Optional sections
    st.subheader('Additional Sections')
    
    # Create two columns to display toggles
    col1, col2 = st.columns(2)
    
    # Split sections between columns
    half = len(OPTIONAL_SECTIONS) // 2 + len(OPTIONAL_SECTIONS) % 2
    
    with col1:
        for section in OPTIONAL_SECTIONS[:half]:
            st.session_state[section['key']] = st.toggle(
                f"{section['icon']} {section['label']}", 
                value=st.session_state.get(section['key'], False),
                help=section['description']
            )
    
    with col2:
        for section in OPTIONAL_SECTIONS[half:]:
            st.session_state[section['key']] = st.toggle(
                f"{section['icon']} {section['label']}", 
                value=st.session_state.get(section['key'], False),
                help=section['description']
            )
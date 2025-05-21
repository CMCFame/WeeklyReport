# components/section_selector.py
"""Section selector component for the Weekly Report app."""

import streamlit as st
from utils.constants import OPTIONAL_SECTIONS

def render_section_selector():
    """Render a section selector for customizing the weekly report."""
    st.header('Report Sections')
    st.write('Select which sections to include in your report:')
    
    # Define all sections in a single list
    ALL_SECTIONS = [
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
    
    # Add optional sections to the main list
    for section in OPTIONAL_SECTIONS:
        ALL_SECTIONS.append({
            'key': section['key'],
            'label': section['label'],
            'icon': section['icon'],
            'description': section['description']
        })
    
    # Initialize session state for section toggles if they don't exist
    # Only enable Current Activities by default
    for section in ALL_SECTIONS:
        if section['key'] not in st.session_state:
            # Set default: only Current Activities is enabled
            st.session_state[section['key']] = (section['key'] == 'show_current_activities')
    
    # Create 3 columns to display all toggles in a single row
    cols = st.columns(3)
    
    # Distribute sections across the columns
    num_sections = len(ALL_SECTIONS)
    sections_per_col = (num_sections + 2) // 3  # Divide evenly, rounding up
    
    for i, section in enumerate(ALL_SECTIONS):
        col_idx = i // sections_per_col
        with cols[col_idx]:
            st.session_state[section['key']] = st.toggle(
                f"{section['icon']} {section['label']}", 
                value=st.session_state.get(section['key'], section['key'] == 'show_current_activities'),
                help=section['description']
            )
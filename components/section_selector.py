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
    
    # Create a list of section labels with icons for the multiselect
    section_labels = [f"{section['icon']} {section['label']}" for section in ALL_SECTIONS]
    
    # Create a mapping from label to key for easier lookup
    label_to_key = {f"{section['icon']} {section['label']}": section['key'] for section in ALL_SECTIONS}
    
    # Get currently selected sections
    current_selections = [f"{section['icon']} {section['label']}" for section in ALL_SECTIONS 
                         if st.session_state.get(section['key'], section['key'] == 'show_current_activities')]
    
    # Create a multiselect widget
    st.write("Sections to include")
    selected_sections = st.multiselect(
        label="",
        options=section_labels,
        default=current_selections,
        label_visibility="collapsed"
    )
    
    # Update session state based on selections
    for section in ALL_SECTIONS:
        section_label = f"{section['icon']} {section['label']}"
        is_selected = section_label in selected_sections
        st.session_state[section['key']] = is_selected
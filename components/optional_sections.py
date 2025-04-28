# components/optional_sections.py
"""Optional sections component for the Weekly Report app."""

import streamlit as st
from utils.constants import OPTIONAL_SECTIONS

def render_optional_section_toggles():
    """Render toggles for optional sections."""
    st.header('Additional Sections')
    st.write('Select which additional sections you\'d like to include:')
    
    # Create two columns to display toggles
    col1, col2 = st.columns(2)
    
    # Split sections between columns
    half = len(OPTIONAL_SECTIONS) // 2 + len(OPTIONAL_SECTIONS) % 2
    
    with col1:
        for section in OPTIONAL_SECTIONS[:half]:
            st.session_state[section['key']] = st.toggle(
                section['label'], 
                value=st.session_state.get(section['key'], False),
                help=section['description']
            )
    
    with col2:
        for section in OPTIONAL_SECTIONS[half:]:
            st.session_state[section['key']] = st.toggle(
                section['label'], 
                value=st.session_state.get(section['key'], False),
                help=section['description']
            )

def render_optional_section(section):
    """Render an optional section if enabled.
    
    Args:
        section (dict): Section configuration from OPTIONAL_SECTIONS
    
    Returns:
        bool: True if section was rendered, False otherwise
    """
    if not st.session_state.get(section['key'], False):
        return False
    
    st.header(f"{section['icon']} {section['label']}")
    st.write(section['description'])
    
    content_key = section['content_key']
    st.session_state[content_key] = st.text_area(
        '', 
        value=st.session_state.get(content_key, ''), 
        key=f"{content_key}_area",
        height=150
    )
    
    return True

def render_all_optional_sections():
    """Render all enabled optional sections."""
    for section in OPTIONAL_SECTIONS:
        render_optional_section(section)
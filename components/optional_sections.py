# components/optional_sections.py
"""Optional sections component for the Weekly Report app."""

import streamlit as st
import time
from utils.constants import OPTIONAL_SECTIONS

def render_optional_section_toggles():
    """Render toggles for optional sections."""
    st.header('Additional Sections')
    st.write('Select which additional sections you\'d like to include:')
    
    # Create two columns to display toggles
    col1, col2 = st.columns(2)
    
    # Split sections between columns
    half = len(OPTIONAL_SECTIONS) // 2 + len(OPTIONAL_SECTIONS) % 2
    
    # Generate a unique timestamp for keys
    timestamp = int(time.time() * 1000)
    
    with col1:
        for section in OPTIONAL_SECTIONS[:half]:
            st.session_state[section['key']] = st.toggle(
                section['label'], 
                value=st.session_state.get(section['key'], False),
                help=section['description'],
                key=f"{section['key']}_{timestamp}"  # Add unique timestamp to key
            )
    
    with col2:
        for section in OPTIONAL_SECTIONS[half:]:
            st.session_state[section['key']] = st.toggle(
                section['label'], 
                value=st.session_state.get(section['key'], False),
                help=section['description'],
                key=f"{section['key']}_{timestamp+1}"  # Add unique timestamp to key
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
    
    # Generate a unique timestamp for this section
    timestamp = int(time.time() * 1000)
    
    st.header(f"{section['icon']} {section['label']}")
    st.write(section['description'])
    
    content_key = section['content_key']
    st.session_state[content_key] = st.text_area(
        f"{section['label']} content", 
        value=st.session_state.get(content_key, ''), 
        key=f"{content_key}_area_{timestamp}",  # Add unique timestamp to key
        height=150,
        label_visibility="collapsed"  # Hide label but provide one for accessibility
    )
    
    return True

def render_all_optional_sections():
    """Render all enabled optional sections."""
    for section in OPTIONAL_SECTIONS:
        render_optional_section(section)
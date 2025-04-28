# utils/session.py
"""Session state management functions."""

import streamlit as st
from datetime import datetime, timedelta
from utils.constants import DEFAULT_CURRENT_ACTIVITY, DEFAULT_UPCOMING_ACTIVITY, OPTIONAL_SECTIONS

def get_next_monday():
    """Return the date of next Monday as string in YYYY-MM-DD format."""
    today = datetime.now()
    days_ahead = (0 - today.weekday()) % 7
    if days_ahead == 0:  # Today is Monday
        days_ahead = 7
    next_monday = today + timedelta(days=days_ahead)
    return next_monday.strftime('%Y-%m-%d')

def init_session_state():
    """Initialize session state variables."""
    # User information
    if 'name' not in st.session_state:
        st.session_state.name = ""
    if 'reporting_week' not in st.session_state:
        st.session_state.reporting_week = ""
    
    # Activities
    if 'current_activities' not in st.session_state:
        st.session_state.current_activities = []
    if 'upcoming_activities' not in st.session_state:
        st.session_state.upcoming_activities = []
    
    # Lists
    if 'accomplishments' not in st.session_state:
        st.session_state.accomplishments = [""]
    if 'followups' not in st.session_state:
        st.session_state.followups = [""]
    if 'nextsteps' not in st.session_state:
        st.session_state.nextsteps = [""]
    
    # Optional sections visibility
    for section in OPTIONAL_SECTIONS:
        if section['key'] not in st.session_state:
            st.session_state[section['key']] = False
        if section['content_key'] not in st.session_state:
            st.session_state[section['content_key']] = ""
    
    # Report ID
    if 'report_id' not in st.session_state:
        st.session_state.report_id = None

def reset_form():
    """Reset the form to its initial state."""
    st.session_state.name = ""
    st.session_state.reporting_week = ""
    st.session_state.current_activities = []
    st.session_state.upcoming_activities = []
    st.session_state.accomplishments = [""]
    st.session_state.followups = [""]
    st.session_state.nextsteps = [""]
    
    # Reset optional sections
    for section in OPTIONAL_SECTIONS:
        st.session_state[section['key']] = False
        st.session_state[section['content_key']] = ""
    
    st.session_state.report_id = None

def add_current_activity():
    """Add a new current activity."""
    activity = DEFAULT_CURRENT_ACTIVITY.copy()
    st.session_state.current_activities.append(activity)

def remove_current_activity(index):
    """Remove a current activity."""
    if index < len(st.session_state.current_activities):
        st.session_state.current_activities.pop(index)

def update_current_activity(index, field, value):
    """Update a field in a current activity."""
    if index < len(st.session_state.current_activities):
        st.session_state.current_activities[index][field] = value

def add_upcoming_activity():
    """Add a new upcoming activity."""
    activity = DEFAULT_UPCOMING_ACTIVITY.copy()
    activity['expected_start'] = get_next_monday()
    st.session_state.upcoming_activities.append(activity)

def remove_upcoming_activity(index):
    """Remove an upcoming activity."""
    if index < len(st.session_state.upcoming_activities):
        st.session_state.upcoming_activities.pop(index)

def update_upcoming_activity(index, field, value):
    """Update a field in an upcoming activity."""
    if index < len(st.session_state.upcoming_activities):
        st.session_state.upcoming_activities[index][field] = value

def update_item_list(key, index, value):
    """Update an item in a list at a specific index."""
    current_list = st.session_state.get(key, [])
    if index < len(current_list):
        current_list[index] = value
    st.session_state[key] = current_list

def add_item_to_list(key):
    """Add an empty item to a list."""
    current_list = st.session_state.get(key, [])
    current_list.append("")
    st.session_state[key] = current_list

def remove_item_from_list(key, index):
    """Remove an item from a list at a specific index."""
    current_list = st.session_state.get(key, [])
    if index < len(current_list) and len(current_list) > 1:
        current_list.pop(index)
        st.session_state[key] = current_list

def calculate_completion_percentage():
    """Calculate the form completion percentage."""
    total_sections = 4  # Core sections (current, upcoming, accomplishments, action items)
    completed_sections = 0
    
    # Check current activities
    if len(st.session_state.get('current_activities', [])) > 0:
        completed_sections += 1
    
    # Check upcoming activities
    if len(st.session_state.get('upcoming_activities', [])) > 0:
        completed_sections += 1
    
    # Check accomplishments
    if len(st.session_state.get('accomplishments', [])) > 0 and any(a for a in st.session_state.accomplishments):
        completed_sections += 1
    
    # Check action items
    if (len(st.session_state.get('followups', [])) > 0 and any(f for f in st.session_state.followups)) or \
       (len(st.session_state.get('nextsteps', [])) > 0 and any(n for n in st.session_state.nextsteps)):
        completed_sections += 1
    
    # Add optional sections if enabled and have content
    for section in OPTIONAL_SECTIONS:
        if st.session_state.get(section['key'], False) and st.session_state.get(section['content_key'], ''):
            total_sections += 1
            completed_sections += 1
    
    return int((completed_sections / total_sections) * 100) if total_sections > 0 else 0

def collect_form_data():
    """Collect form data from session state."""
    data = {
        'id': st.session_state.get('report_id'),
        'name': st.session_state.name,
        'reporting_week': st.session_state.reporting_week,
        'current_activities': [a for a in st.session_state.current_activities if a.get('description')],
        'upcoming_activities': [a for a in st.session_state.upcoming_activities if a.get('description')],
        'accomplishments': [a for a in st.session_state.accomplishments if a],
        'followups': [f for f in st.session_state.followups if f],
        'nextsteps': [n for n in st.session_state.nextsteps if n],
        'timestamp': datetime.now().isoformat()
    }
    
    # Add optional sections if enabled
    for section in OPTIONAL_SECTIONS:
        if st.session_state.get(section['key'], False):
            data[section['content_key']] = st.session_state.get(section['content_key'], '')
    
    return data

def load_report_data(report_data):
    """Load report data into session state."""
    st.session_state.name = report_data.get('name', '')
    st.session_state.reporting_week = report_data.get('reporting_week', '')
    
    # Load activities
    st.session_state.current_activities = report_data.get('current_activities', [])
    st.session_state.upcoming_activities = report_data.get('upcoming_activities', [])
    
    # Load lists
    st.session_state.accomplishments = report_data.get('accomplishments', [''])
    if not st.session_state.accomplishments:
        st.session_state.accomplishments = ['']
        
    st.session_state.followups = report_data.get('followups', [''])
    if not st.session_state.followups:
        st.session_state.followups = ['']
        
    st.session_state.nextsteps = report_data.get('nextsteps', [''])
    if not st.session_state.nextsteps:
        st.session_state.nextsteps = ['']
    
    # Load optional sections
    for section in OPTIONAL_SECTIONS:
        content = report_data.get(section['content_key'], '')
        st.session_state[section['content_key']] = content
        # Toggle section if it has content
        st.session_state[section['key']] = bool(content)
    
    st.session_state.report_id = report_data.get('id')
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
    
    # Section visibility
    if 'show_current_activities' not in st.session_state:
        st.session_state.show_current_activities = True
    if 'show_upcoming_activities' not in st.session_state:
        st.session_state.show_upcoming_activities = True
    if 'show_accomplishments' not in st.session_state:
        st.session_state.show_accomplishments = True
    if 'show_action_items' not in st.session_state:
        st.session_state.show_action_items = True
    
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
    
    # Editing flag
    if 'editing_report' not in st.session_state:
        st.session_state.editing_report = False
    
    # Original timestamp for edits
    if 'original_timestamp' not in st.session_state:
        st.session_state.original_timestamp = None
        
    # Cancellation flag
    if 'cancel_editing' not in st.session_state:
        st.session_state.cancel_editing = False

def reset_form():
    """Reset the form to its initial state."""
    # Store values that need to be reset in a dictionary for deferred processing
    reset_values = {
        'name': "",
        'reporting_week': "",
        'current_activities': [],
        'upcoming_activities': [],
        'accomplishments': [""],
        'followups': [""],
        'nextsteps': [""],
        'report_id': None,
        'editing_report': False,
        'original_timestamp': None
    }
    
    # Reset optional sections
    for section in OPTIONAL_SECTIONS:
        reset_values[section['key']] = False
        reset_values[section['content_key']] = ""
    
    # Apply all resets at once using setdefault
    # This approach is less likely to cause issues with widget rendering
    for key, value in reset_values.items():
        if key in st.session_state:
            try:
                # Try to safely reset the value
                st.session_state[key] = value
            except Exception:
                # If we can't set it directly, we'll defer to the next rerun
                pass

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
    total_sections = 0
    completed_sections = 0
    
    # Check current activities (only if section is enabled)
    if st.session_state.get('show_current_activities', True):
        total_sections += 1
        if len(st.session_state.get('current_activities', [])) > 0:
            completed_sections += 1
    
    # Check upcoming activities (only if section is enabled)
    if st.session_state.get('show_upcoming_activities', True):
        total_sections += 1
        if len(st.session_state.get('upcoming_activities', [])) > 0:
            completed_sections += 1
    
    # Check accomplishments (only if section is enabled)
    if st.session_state.get('show_accomplishments', True):
        total_sections += 1
        if len(st.session_state.get('accomplishments', [])) > 0 and any(a for a in st.session_state.accomplishments):
            completed_sections += 1
    
    # Check action items (only if section is enabled)
    if st.session_state.get('show_action_items', True):
        total_sections += 1
        if ((len(st.session_state.get('followups', [])) > 0 and any(f for f in st.session_state.followups)) or
            (len(st.session_state.get('nextsteps', [])) > 0 and any(n for n in st.session_state.nextsteps))):
            completed_sections += 1
    
    # Add optional sections if enabled and have content
    for section in OPTIONAL_SECTIONS:
        if st.session_state.get(section['key'], False):
            total_sections += 1
            if st.session_state.get(section['content_key'], ''):
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
    """Load report data into session state with improved error handling."""
    if not report_data:
        st.error("No report data to load")
        return
    
    try:
        # Load basic user information with safe defaults
        st.session_state.name = report_data.get('name', '')
        st.session_state.reporting_week = report_data.get('reporting_week', '')
        
        # Safely load activities lists
        st.session_state.current_activities = report_data.get('current_activities', [])
        if not isinstance(st.session_state.current_activities, list):
            st.session_state.current_activities = []
            
        st.session_state.upcoming_activities = report_data.get('upcoming_activities', [])
        if not isinstance(st.session_state.upcoming_activities, list):
            st.session_state.upcoming_activities = []
        
        # Safely load list items, ensuring they're never empty
        accomplishments = report_data.get('accomplishments', [''])
        st.session_state.accomplishments = accomplishments if accomplishments else ['']
        
        followups = report_data.get('followups', [''])
        st.session_state.followups = followups if followups else ['']
        
        nextsteps = report_data.get('nextsteps', [''])
        st.session_state.nextsteps = nextsteps if nextsteps else ['']
        
        # Load optional sections
        for section in OPTIONAL_SECTIONS:
            content_key = section['content_key']
            content = report_data.get(content_key, '')
            st.session_state[content_key] = content
            # Toggle section visibility based on content
            st.session_state[section['key']] = bool(content)
        
        # Set report ID
        st.session_state.report_id = report_data.get('id')
        
        # Store original timestamp for updates
        if 'timestamp' in report_data:
            st.session_state.original_timestamp = report_data.get('timestamp')
        
    except Exception as e:
        st.error(f"Error loading report data: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")

def debug_report_data(report_data, prefix=""):
    """Debug function to print report data structure."""
    debug_info = []
    if not report_data:
        return ["Report data is None or empty"]
    
    for key, value in report_data.items():
        if isinstance(value, dict):
            debug_info.extend(debug_report_data(value, prefix + key + "."))
        elif isinstance(value, list):
            debug_info.append(f"{prefix}{key}: {type(value)} = list with {len(value)} items")
            if value and len(value) > 0:
                debug_info.append(f"{prefix}{key}[0]: {type(value[0])} = {value[0]}")
        else:
            debug_info.append(f"{prefix}{key}: {type(value)} = {value}")
    
    return debug_info
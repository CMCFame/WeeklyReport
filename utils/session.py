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
    
    # Section visibility - only Current Activities enabled by default
    if 'show_current_activities' not in st.session_state:
        st.session_state.show_current_activities = True
    if 'show_upcoming_activities' not in st.session_state:
        st.session_state.show_upcoming_activities = False
    if 'show_accomplishments' not in st.session_state:
        st.session_state.show_accomplishments = False
    if 'show_action_items' not in st.session_state:
        st.session_state.show_action_items = False
    
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
    
    # Optional sections visibility - all disabled by default
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
    # Helper function to safely get session state values
    def safe_get_session_value(key, default):
        """Safely get value from session state, handling None values."""
        value = st.session_state.get(key, default)
        return value if value is not None else default
    
    # Get basic values with safe defaults
    name = safe_get_session_value('name', '')
    reporting_week = safe_get_session_value('reporting_week', '')
    
    # Get activities lists with safe defaults
    current_activities = safe_get_session_value('current_activities', [])
    upcoming_activities = safe_get_session_value('upcoming_activities', [])
    
    # Get text lists with safe defaults
    accomplishments = safe_get_session_value('accomplishments', [''])
    followups = safe_get_session_value('followups', [''])
    nextsteps = safe_get_session_value('nextsteps', [''])
    
    # Ensure activities are properly formatted
    def clean_activities(activities_list):
        """Clean activities list, ensuring all items are dicts with required fields."""
        if not isinstance(activities_list, list):
            return []
        
        cleaned = []
        for activity in activities_list:
            if isinstance(activity, dict) and activity.get('description'):
                # Safely convert progress to int
                def safe_int_conversion(value, default=50):
                    """Safely convert value to int, handling empty strings and None."""
                    if value is None or value == '':
                        return default
                    try:
                        return int(float(value))  # Convert via float first to handle decimal strings
                    except (ValueError, TypeError):
                        return default
                
                # Ensure all required fields exist with safe defaults
                cleaned_activity = {
                    'description': str(activity.get('description', '')),
                    'project': str(activity.get('project', '')),
                    'milestone': str(activity.get('milestone', '')),
                    'priority': str(activity.get('priority', 'Medium')),
                    'status': str(activity.get('status', 'In Progress')),
                    'progress': safe_int_conversion(activity.get('progress', 50)),
                }
                # Add any additional fields that might exist
                for key, value in activity.items():
                    if key not in cleaned_activity and value is not None:
                        if key in ['has_deadline', 'is_recurring']:
                            # Boolean fields
                            cleaned_activity[key] = bool(value)
                        else:
                            cleaned_activity[key] = str(value) if value != '' else ''
                cleaned.append(cleaned_activity)
        return cleaned
    
    # Clean text lists
    def clean_text_list(text_list):
        """Clean text list, removing None values and empty strings."""
        if not isinstance(text_list, list):
            return []
        return [str(item).strip() for item in text_list if item is not None and str(item).strip()]
    
    data = {
        'id': safe_get_session_value('report_id', None),
        'name': str(name) if name else '',
        'reporting_week': str(reporting_week) if reporting_week else '',
        'current_activities': clean_activities(current_activities),
        'upcoming_activities': clean_activities(upcoming_activities),
        'accomplishments': clean_text_list(accomplishments),
        'followups': clean_text_list(followups),
        'nextsteps': clean_text_list(nextsteps),
        'timestamp': datetime.now().isoformat()
    }
    
    # Add optional sections if enabled
    from utils.constants import OPTIONAL_SECTIONS
    for section in OPTIONAL_SECTIONS:
        section_key = section['key']
        content_key = section['content_key']
        
        if safe_get_session_value(section_key, False):
            content = safe_get_session_value(content_key, '')
            data[content_key] = str(content) if content is not None else ''
    
    return data

def load_report_data(report_data):
    """Load report data into session state with improved error handling."""
    if not report_data:
        st.error("No report data to load")
        return
    
    try:
        # Helper function to safely set session state values
        def safe_set_session_value(key, value, default):
            """Safely set session state value with proper type checking."""
            if value is not None:
                st.session_state[key] = value
            else:
                st.session_state[key] = default
        
        # Helper function to safely get and validate list data
        def safe_get_list(data, key, default=None):
            """Safely get list data, ensuring it's actually a list."""
            if default is None:
                default = []
            
            value = data.get(key, default)
            if isinstance(value, list):
                return [item for item in value if item is not None]
            elif value is not None:
                # If it's not a list but has a value, try to convert
                return [str(value)]
            else:
                return default
        
        # Helper function to safely get string data
        def safe_get_string(data, key, default=''):
            """Safely get string data."""
            value = data.get(key, default)
            return str(value) if value is not None else default
        
        # Load basic user information with safe defaults
        st.session_state.name = safe_get_string(report_data, 'name', '')
        st.session_state.reporting_week = safe_get_string(report_data, 'reporting_week', '')
        
        # Safely load activities lists
        current_activities = safe_get_list(report_data, 'current_activities', [])
        if current_activities:
            # Ensure each activity is properly formatted
            cleaned_activities = []
            for activity in current_activities:
                if isinstance(activity, dict):
                    # Create a clean activity dict with all required fields
                    clean_activity = {
                        'description': safe_get_string(activity, 'description', ''),
                        'project': safe_get_string(activity, 'project', ''),
                        'milestone': safe_get_string(activity, 'milestone', ''),
                        'priority': safe_get_string(activity, 'priority', 'Medium'),
                        'status': safe_get_string(activity, 'status', 'In Progress'),
                        'customer': safe_get_string(activity, 'customer', ''),
                        'billable': safe_get_string(activity, 'billable', ''),
                        'deadline': safe_get_string(activity, 'deadline', ''),
                        'has_deadline': bool(activity.get('has_deadline', False)),
                        'is_recurring': bool(activity.get('is_recurring', False)),
                    }
                    
                    # Handle progress field specially
                    try:
                        progress = activity.get('progress', 50)
                        clean_activity['progress'] = int(progress) if progress is not None else 50
                    except (ValueError, TypeError):
                        clean_activity['progress'] = 50
                    
                    # Add any other fields that might exist
                    for key, value in activity.items():
                        if key not in clean_activity and value is not None:
                            clean_activity[key] = value
                    
                    cleaned_activities.append(clean_activity)
                elif activity:  # Non-dict but has value
                    # Create a minimal activity from string
                    cleaned_activities.append({
                        'description': str(activity),
                        'project': '',
                        'milestone': '',
                        'priority': 'Medium',
                        'status': 'In Progress',
                        'customer': '',
                        'billable': '',
                        'deadline': '',
                        'has_deadline': False,
                        'is_recurring': False,
                        'progress': 50
                    })
            st.session_state.current_activities = cleaned_activities
        else:
            st.session_state.current_activities = []
        
        # Handle upcoming activities similarly
        upcoming_activities = safe_get_list(report_data, 'upcoming_activities', [])
        if upcoming_activities:
            cleaned_upcoming = []
            for activity in upcoming_activities:
                if isinstance(activity, dict):
                    clean_activity = {
                        'description': safe_get_string(activity, 'description', ''),
                        'project': safe_get_string(activity, 'project', ''),
                        'milestone': safe_get_string(activity, 'milestone', ''),
                        'priority': safe_get_string(activity, 'priority', 'Medium'),
                        'expected_start': safe_get_string(activity, 'expected_start', get_next_monday()),
                    }
                    # Add any other fields
                    for key, value in activity.items():
                        if key not in clean_activity and value is not None:
                            clean_activity[key] = value
                    cleaned_upcoming.append(clean_activity)
            st.session_state.upcoming_activities = cleaned_upcoming
        else:
            st.session_state.upcoming_activities = []
        
        # Safely load list items, ensuring they're never empty lists
        accomplishments = safe_get_list(report_data, 'accomplishments', [''])
        st.session_state.accomplishments = accomplishments if accomplishments else ['']
        
        followups = safe_get_list(report_data, 'followups', [''])
        st.session_state.followups = followups if followups else ['']
        
        nextsteps = safe_get_list(report_data, 'nextsteps', [''])
        st.session_state.nextsteps = nextsteps if nextsteps else ['']
        
        # Load optional sections safely
        for section in OPTIONAL_SECTIONS:
            content_key = section['content_key']
            content = safe_get_string(report_data, content_key, '')
            st.session_state[content_key] = content
            # Toggle section visibility based on content
            st.session_state[section['key']] = bool(content.strip())
        
        # Set report ID
        st.session_state.report_id = report_data.get('id')
        
        # Store original timestamp for updates
        if 'timestamp' in report_data:
            st.session_state.original_timestamp = report_data.get('timestamp')
        
        st.success("Report data loaded successfully!")
        
    except Exception as e:
        st.error(f"Error loading report data: {str(e)}")
        
        # Initialize with safe defaults if loading fails
        st.session_state.name = ''
        st.session_state.reporting_week = ''
        st.session_state.current_activities = []
        st.session_state.upcoming_activities = []
        st.session_state.accomplishments = ['']
        st.session_state.followups = ['']
        st.session_state.nextsteps = ['']
        
        # Initialize optional sections
        for section in OPTIONAL_SECTIONS:
            st.session_state[section['key']] = False
            st.session_state[section['content_key']] = ''
        
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")

def debug_report_data(report_data, prefix=""):
    """Enhanced debug function to analyze report data structure."""
    debug_info = []
    if not report_data:
        return ["Report data is None or empty"]
    
    try:
        for key, value in report_data.items():
            if isinstance(value, dict):
                debug_info.append(f"{prefix}{key}: {type(value)} = dict with {len(value)} items")
                debug_info.extend(debug_report_data(value, prefix + key + "."))
            elif isinstance(value, list):
                debug_info.append(f"{prefix}{key}: {type(value)} = list with {len(value)} items")
                if value and len(value) > 0:
                    for i, item in enumerate(value[:3]):  # Show first 3 items
                        if isinstance(item, dict):
                            debug_info.append(f"{prefix}{key}[{i}]: {type(item)} = dict with keys: {list(item.keys())}")
                        else:
                            debug_info.append(f"{prefix}{key}[{i}]: {type(item)} = {repr(item)[:100]}")
                        if i == 2 and len(value) > 3:
                            debug_info.append(f"{prefix}{key}[...]: ({len(value) - 3} more items)")
                            break
            elif value is None:
                debug_info.append(f"{prefix}{key}: None")
            else:
                debug_info.append(f"{prefix}{key}: {type(value)} = {repr(value)[:100]}")
    except Exception as e:
        debug_info.append(f"Error analyzing report data: {str(e)}")
    
    return debug_info

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
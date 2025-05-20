# utils/constants.py
"""Constants used throughout the application."""

# Priority, status and billable options
PRIORITY_OPTIONS = ["High", "Medium", "Low"]
STATUS_OPTIONS = ["Not Started", "In Progress", "Blocked", "Completed"]
BILLABLE_OPTIONS = ["", "Yes", "No"]

# utils/constants.py (update the DEFAULT_CURRENT_ACTIVITY)

# Current activities default
DEFAULT_CURRENT_ACTIVITY = {
    'project': '',
    'milestone': '',
    'priority': 'Medium',
    'status': 'In Progress',
    'customer': '',
    'billable': '',
    'deadline': '',
    'has_deadline': False,  # New field
    'is_recurring': False,  # New field
    'progress': 50,
    'description': ''
}

# Upcoming activities default
DEFAULT_UPCOMING_ACTIVITY = {
    'project': '',
    'milestone': '',
    'priority': 'Medium',
    'expected_start': '',  # This will be set to next Monday dynamically
    'description': ''
}

# Optional sections
OPTIONAL_SECTIONS = [
    {'key': 'show_challenges', 'label': 'Challenges & Assistance', 'icon': '⚠️', 
     'content_key': 'challenges', 'description': 'What challenges are you facing? What help do you need?'},
    {'key': 'show_slow_projects', 'label': 'Slow-Moving Projects', 'icon': '🐢', 
     'content_key': 'slow_projects', 'description': 'Are any projects moving slower than expected? Why?'},
    {'key': 'show_other_topics', 'label': 'Other Discussion Topics', 'icon': '💬', 
     'content_key': 'other_topics', 'description': 'Anything else that needs to be discussed?'},
    {'key': 'show_key_accomplishments', 'label': 'Key Accomplishments', 'icon': '🏆', 
     'content_key': 'key_accomplishments', 'description': 'What are you most proud of accomplishing this week?'},
    {'key': 'show_concerns', 'label': 'Concerns', 'icon': '⁉️', 
     'content_key': 'concerns', 'description': 'Any concerns about upcoming work or deadlines?'}
]
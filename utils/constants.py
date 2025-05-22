# utils/constants.py
"""Constants used throughout the application."""

# Priority, status and billable options
PRIORITY_OPTIONS = ["High", "Medium", "Low"]
STATUS_OPTIONS = ["Not Started", "In Progress", "Blocked", "Completed"]
BILLABLE_OPTIONS = ["", "Yes", "No"]

# ASDF Project Phases - New addition for tactical management visibility
ASDF_PHASES = [
    "",  # Empty option for non-project activities
    "Qualification", 
    "Scoping", 
    "Initiation", 
    "Delivery", 
    "Support"
]

# Phase descriptions for help text
ASDF_PHASE_DESCRIPTIONS = {
    "": "Not project-related or general activity",
    "Qualification": "Opportunity identification and BANT qualification",
    "Scoping": "Whiteboard sessions, ROM development, SOW creation",
    "Initiation": "Project onboarding, resourcing, team preparation",
    "Delivery": "Active project execution and deliverable creation",
    "Support": "Ongoing maintenance and customer support"
}

# Phase colors for visualizations
ASDF_PHASE_COLORS = {
    "": "#f8f9fa",  # Light gray for unspecified
    "Qualification": "#28a745",  # Green - early opportunity
    "Scoping": "#17a2b8",  # Blue - analysis phase
    "Initiation": "#ffc107",  # Yellow - preparation
    "Delivery": "#dc3545",  # Red - active execution
    "Support": "#6c757d"  # Gray - ongoing support
}

# Current activities default - Enhanced with ASDF phase
DEFAULT_CURRENT_ACTIVITY = {
    'project': '',
    'milestone': '',
    'priority': 'Medium',
    'status': 'In Progress',
    'customer': '',
    'billable': '',
    'deadline': '',
    'has_deadline': False,
    'is_recurring': False,
    'progress': 50,
    'description': '',
    'asdf_phase': ''  # New field for ASDF phase tracking
}

# Upcoming activities default - Enhanced with ASDF phase
DEFAULT_UPCOMING_ACTIVITY = {
    'project': '',
    'milestone': '',
    'priority': 'Medium',
    'expected_start': '',
    'description': '',
    'asdf_phase': ''  # New field for ASDF phase tracking
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
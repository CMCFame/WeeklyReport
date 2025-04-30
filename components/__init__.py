# components/__init__.py
"""Component modules for the Weekly Report app."""

# Import all components for easier access
from components.user_info import render_user_info
from components.current_activities import render_current_activities
from components.upcoming_activities import render_upcoming_activities
from components.accomplishments import render_accomplishments
from components.action_items import render_action_items
from components.optional_sections import render_optional_section_toggles, render_optional_section, render_all_optional_sections
from components.past_reports import render_past_reports
from components.auth import (
    check_authentication, 
    render_login_page, 
    render_register_page,
    render_user_profile,
    render_logout_button,
    render_admin_user_management
)
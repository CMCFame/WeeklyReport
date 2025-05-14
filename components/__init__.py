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
    render_admin_user_management,
    render_forgot_password_page,
    render_reset_password_page
)

# Import simplified components
from components.simple_accomplishments import render_simple_accomplishments
from components.simple_action_items import render_simple_action_items

# Import enhanced components
from components.enhanced_accomplishments import render_enhanced_accomplishments
from components.enhanced_action_items import render_enhanced_action_items

# Import import components
from components.user_import import render_user_import
from components.report_import import render_report_import
from components.objectives_import import render_objectives_import

# Import placeholder components
from components.placeholder import (
    render_okr_management,
    render_team_structure,
    render_one_on_one_meetings,
    render_system_settings
)

# Import dashboard components
from components.goal_dashboard import render_goal_dashboard
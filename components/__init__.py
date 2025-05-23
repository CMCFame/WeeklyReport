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
from components.enhanced_current_activities import render_enhanced_current_activities

# Import import components
from components.user_import import render_user_import
from components.report_import import render_report_import
from components.objectives_import import render_objectives_import
from components.section_selector import render_section_selector

# Import real implementations of previously placeholder components
from components.report_templates import render_report_templates as render_real_report_templates
from components.team_objectives import render_team_objectives as render_real_team_objectives
from components.goal_dashboard import render_goal_dashboard as render_real_goal_dashboard
from components.okr_management import render_okr_management as render_real_okr_management
from components.team_structure import render_team_structure as render_real_team_structure
from components.one_on_one_meetings import render_one_on_one_meetings as render_real_one_on_one_meetings

# Import placeholders (these now call the real implementations for backward compatibility)
from components.placeholder import (
    render_report_templates,
    render_team_objectives,
    render_goal_dashboard,
    render_okr_management,
    render_team_structure,
    render_one_on_one_meetings,
    render_system_settings
)

# Import dashboard components
from components.weekly_report_analytics import render_weekly_report_analytics
from components.advanced_analytics import render_advanced_analytics
from components.batch_export import render_batch_export

# Import PDF export components
from components.pdf_export import (
    render_report_export_button,
    render_objective_export_button,
    render_batch_export_reports,
    render_batch_export_objectives
)

# NEW AI COMPONENTS - Import all AI features
from components.ai_voice_assistant import (
    render_ai_voice_assistant,
    render_voice_assistant_tips,
    render_voice_analytics
)

from components.ai_smart_suggestions import (
    render_smart_suggestions_panel,
    render_suggestions_dashboard,
    render_real_time_suggestions,
    render_smart_autocomplete
)

from components.team_health_dashboard import render_team_health_dashboard

from components.predictive_intelligence import render_predictive_intelligence

from components.executive_summary_generator import render_executive_summary_generator
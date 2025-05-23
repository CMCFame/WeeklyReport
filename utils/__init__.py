# utils/__init__.py
"""Utility modules for the Weekly Report app."""

# Import all utilities for easier access
from utils.constants import (
    PRIORITY_OPTIONS, 
    STATUS_OPTIONS, 
    BILLABLE_OPTIONS,
    OPTIONAL_SECTIONS
)

from utils.session import (
    init_session_state,
    reset_form,
    calculate_completion_percentage,
    collect_form_data,
    load_report_data,
    get_next_monday
)

from utils.file_ops import (
    save_report,
    load_report,
    get_all_reports,
    delete_report,
    export_report_as_pdf
)

# Import auth functions
from utils.user_auth import (
    login_user, 
    logout_user, 
    create_user, 
    update_user, 
    get_user, 
    get_all_users, 
    delete_user,
    generate_reset_code, 
    reset_password, 
    verify_reset_code,
    ROLES, 
    init_session_auth, 
    require_auth, 
    require_role,
    create_admin_if_needed
)

# Import CSV utilities
from utils.csv_utils import (
    load_project_data,
    get_user_projects,
    get_project_milestones,
    ensure_project_data_file
)

# Import team utilities
from utils.team_utils import (
    load_team_structure,
    save_team_structure,
    get_team_members,
    get_teams,
    get_relationships,
    add_team,
    update_team,
    delete_team,
    add_member,
    update_member,
    delete_member,
    get_member_by_user_id,
    get_team_by_id,
    get_member_by_id,
    get_team_members_by_team_id,
    get_direct_reports,
    import_organization_from_users
)

# Import meeting utilities
from utils.meeting_utils import (
    ensure_meetings_directory,
    load_meeting_templates,
    save_meeting_templates,
    get_meetings,
    add_meeting_template,
    update_meeting_template,
    delete_meeting_template,
    get_template_by_id,
    create_meeting,
    update_meeting,
    delete_meeting,
    get_meeting_by_id,
    add_action_item_to_meeting,
    update_action_item,
    get_all_action_items,
    get_upcoming_meetings,
    convert_action_items_to_next_steps
)

# Import permissions
from utils.permissions import (
    ensure_permissions_directory,
    get_default_permissions,
    load_permissions,
    save_permissions,
    check_section_access,
    render_section_permissions_settings
)

# Import import CSV utilities
from utils.import_csv import (
    import_project_data
)

# Import PDF export utilities
from utils.pdf_export import (
    export_report_to_pdf,
    export_objective_to_pdf
)

# NEW AI UTILITIES - Import AI functions
from utils.ai_utils import (
    setup_openai_api,
    analyze_sentiment,
    detect_stress_indicators,
    calculate_workload_score,
    predict_burnout_risk,
    generate_ai_suggestions,
    generate_executive_summary,
    transcribe_audio,
    structure_voice_input,
    calculate_report_readiness_score
)
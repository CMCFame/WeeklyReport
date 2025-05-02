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
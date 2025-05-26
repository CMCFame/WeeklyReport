# utils/permissions.py
"""Section permissions management for the Weekly Report app."""

import streamlit as st
import json
from pathlib import Path
from utils.user_auth import get_user, AVAILABLE_FEATURES # Import get_user and AVAILABLE_FEATURES

def ensure_permissions_directory():
    """Ensure the permissions directory exists."""
    Path("data/permissions").mkdir(parents=True, exist_ok=True)

def get_default_permissions():
    """Get default permissions configuration."""
    # Default permissions - all sections enabled by default at the role level
    return {
        "goals_tracking": True,  # Goals & Tracking section
        "team_management": True,  # Team Management section
        "advanced_analytics": True,  # Advanced Analytics
        "batch_export": True,     # Batch Export
        "ai_assistant": True,     # AI Assistant features (all users)
        "ai_intelligence": True,  # AI Intelligence features (managers/admins)
        "admin_features": {       # Admin-only features by role
            "admin": True,        # Admin sees all admin features
            "manager": True,      # Managers see manager-level admin features
            "team_member": False  # Team members don't see admin features
        }
    }

def load_permissions():
    """Load permissions configuration."""
    ensure_permissions_directory()
    
    config_file = Path("data/permissions/section_permissions.json")
    if not config_file.exists():
        permissions = get_default_permissions()
        save_permissions(permissions)
        return permissions
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading permissions: {str(e)}")
        return get_default_permissions()

def save_permissions(permissions):
    """Save permissions configuration."""
    ensure_permissions_directory()
    
    try:
        config_file = Path("data/permissions/section_permissions.json")
        with open(config_file, 'w') as f:
            json.dump(permissions, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving permissions: {str(e)}")
        return False

def check_section_access(section_name, user_role="team_member", username=None): 
    """
    Check if a user has access to a section.
    Considers role-based general section permissions and user-specific feature flags.
    
    Args:
        section_name (str): The name of the section/page being checked (e.g., "AI Voice Assistant").
                            This should match a key in AVAILABLE_FEATURES.
        user_role (str): The role of the current user (e.g., "admin", "manager", "team_member").
        username (str): The username of the current user. Required for user-specific checks.
        
    Returns:
        bool: True if the user has access, False otherwise.
    """
    # 1. Admin always has access to all sections and features, regardless of other settings
    if user_role == "admin":
        return True
    
    # 2. Check user-specific feature flag first (if username is provided and feature is defined)
    if username and section_name in AVAILABLE_FEATURES:
        user_data = get_user(username) # Retrieve the user's full data
        if user_data:
            user_feature_permissions = user_data.get("feature_permissions", {})
            # If the feature is explicitly set to False for this user, deny access.
            # If it's True or not found in their specific permissions, proceed to role-based check.
            if not user_feature_permissions.get(section_name, True): # Default to True if not in user's specific settings
                return False # User-specific setting denies access, overrides role permission

    # 3. If no user-specific override denied access, check role-based permissions
    role_permissions = load_permissions() # Load general role-based permissions

    # Check specific admin feature pages (these are typically restricted by role in permissions.json)
    admin_feature_pages = ["Import Users", "Import Reports", "System Settings", "User Management", "Import Objectives"]
    if section_name in admin_feature_pages:
        return role_permissions.get("admin_features", {}).get(user_role, False)
        
    # Check Goals & Tracking category pages
    goals_tracking_pages = ["Team Objectives", "Goal Dashboard", "OKR Management"]
    if section_name in goals_tracking_pages:
        return role_permissions.get("goals_tracking", True)
        
    # Check Team Management category pages (User Management is an admin_feature_page, handled above)
    team_management_pages = ["Team Structure", "1:1 Meetings"]
    if section_name in team_management_pages:
        # Managers always have access to these specific team management pages by role definition
        if user_role == "manager":
            return True
        return role_permissions.get("team_management", True) # For team members if allowed
    
    # Check AI Features: ai_assistant (all users), ai_intelligence (manager/admin)
    ai_assistant_pages = ["AI Voice Assistant", "Smart Suggestions"]
    if section_name in ai_assistant_pages:
        return role_permissions.get("ai_assistant", True)
    
    ai_intelligence_pages = ["Team Health Dashboard", "Predictive Intelligence", "Executive Summary"]
    if section_name in ai_intelligence_pages:
        if user_role in ["admin", "manager"]: 
            return role_permissions.get("ai_intelligence", True)
        return False # Team members don't get these by default

    # Direct check for other top-level permission keys (e.g., "Advanced Analytics", "Batch Export")
    # These are often directly named in permissions.json
    if section_name in role_permissions:
        return role_permissions.get(section_name, True) 

    # For general pages not explicitly listed in categories or as direct keys in permissions.json,
    # and not explicitly denied by user-specific flags, default to True.
    # This covers core pages like "Weekly Report", "Past Reports", "User Profile", "Project Data"
    # unless they are explicitly in AVAILABLE_FEATURES and disabled for the user.
    return True


def render_section_permissions_settings():
    """Render section permissions settings."""
    st.subheader("Section Permissions (Role-Based)")
    st.write("Enable or disable sections for different user roles. User-specific feature permissions can further restrict access and are managed under 'User Actions & Permissions' in the User Management page.")
    
    # Load current permissions
    permissions = load_permissions()
    
    # Create form for updating permissions
    with st.form("section_permissions_form"):
        # Main sections
        st.write("### Main Sections")
        
        goals_tracking = st.checkbox(
            "Goals & Tracking (Team Objectives, Goal Dashboard, OKR Management)",
            value=permissions.get("goals_tracking", True)
        )
        
        team_management = st.checkbox(
            "Team Management (Team Structure, 1:1 Meetings)", 
            value=permissions.get("team_management", True)
        )
        
        advanced_analytics = st.checkbox(
            "Advanced Analytics", 
            value=permissions.get("advanced_analytics", True)
        )
        
        batch_export = st.checkbox(
            "Batch Export", 
            value=permissions.get("batch_export", True)
        )
        
        # AI PERMISSIONS
        st.write("### AI Features")
        
        ai_assistant = st.checkbox(
            "AI Assistant (Voice Assistant, Smart Suggestions) - All Users", 
            value=permissions.get("ai_assistant", True),
            help="AI features available to all team members"
        )
        
        ai_intelligence = st.checkbox(
            "AI Intelligence (Team Health, Predictive Intelligence, Executive Summary) - Managers/Admins Only", 
            value=permissions.get("ai_intelligence", True),
            help="Advanced AI analytics for managers and administrators"
        )
        
        # Admin features by role
        st.write("### Admin Features (e.g., Import Users/Reports, System Settings, User Management)")
        st.write("Which roles can access these admin-level pages:")
        
        admin_features = permissions.get("admin_features", {})
        
        # Admin always has access - disabled checkbox
        st.checkbox(
            "Admin",
            value=True,
            disabled=True,
            help="Admins always have access to all features"
        )
        
        manager_admin = st.checkbox(
            "Manager",
            value=admin_features.get("manager", True), 
            help="Allow managers to access admin-level pages"
        )
        
        team_member_admin = st.checkbox(
            "Team Member",
            value=admin_features.get("team_member", False), 
            help="Allow team members to access admin-level pages"
        )
        
        # Submit button
        submit = st.form_submit_button("Save Role-Based Section Permissions")
        
        if submit:
            # Update permissions
            new_permissions = {
                "goals_tracking": goals_tracking,
                "team_management": team_management,
                "advanced_analytics": advanced_analytics,
                "batch_export": batch_export,
                "ai_assistant": ai_assistant,
                "ai_intelligence": ai_intelligence,
                "admin_features": {
                    "admin": True, 
                    "manager": manager_admin,
                    "team_member": team_member_admin
                }
            }
            
            if save_permissions(new_permissions):
                st.success("Role-based section permissions updated successfully!")
            else:
                st.error("Failed to update role-based section permissions.")


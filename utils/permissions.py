"""Section permissions management for the Weekly Report app."""

import streamlit as st
import json
from pathlib import Path

def ensure_permissions_directory():
    """Ensure the permissions directory exists."""
    Path("data/permissions").mkdir(parents=True, exist_ok=True)

def get_default_permissions():
    """Get default permissions configuration."""
    # Default permissions - all sections enabled by default
    return {
        "goals_tracking": True,  # Goals & Tracking section
        "team_management": True,  # Team Management section
        "advanced_analytics": True,  # Advanced Analytics
        "batch_export": True,     # Batch Export
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
        # Create default permissions file
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

def check_section_access(section_name, user_role="team_member"):
    """Check if a user has access to a section."""
    # Load permissions
    permissions = load_permissions()
    
    # Admin always has access to all sections
    if user_role == "admin":
        return True
    
    # Check admin features for managers and team members
    if section_name in ["Import Users", "Import Reports", "System Settings", "Import Objectives"]:
        return permissions.get("admin_features", {}).get(user_role, False)
        
    # Check specific section permissions
    if section_name in ["Team Objectives", "Goal Dashboard", "OKR Management"]:
        return permissions.get("goals_tracking", True)
        
    if section_name in ["User Management", "Team Structure", "1:1 Meetings"]:
        # Managers always have access to team management
        if user_role == "manager":
            return True
        return permissions.get("team_management", True)
    
    if section_name == "Advanced Analytics":
        return permissions.get("advanced_analytics", True)
        
    if section_name == "Batch Export":
        return permissions.get("batch_export", True)
    
    # By default, allow access
    return True

def render_section_permissions_settings():
    """Render section permissions settings."""
    st.subheader("Section Permissions")
    st.write("Enable or disable sections for different user roles.")
    
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
        
        # Admin features by role
        st.write("### Admin Features")
        st.write("Which roles can access admin features:")
        
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
            help="Allow managers to access admin features"
        )
        
        team_member_admin = st.checkbox(
            "Team Member",
            value=admin_features.get("team_member", False),
            help="Allow team members to access admin features"
        )
        
        # Submit button
        submit = st.form_submit_button("Save Permissions")
        
        if submit:
            # Update permissions
            new_permissions = {
                "goals_tracking": goals_tracking,
                "team_management": team_management,
                "advanced_analytics": advanced_analytics,
                "batch_export": batch_export,
                "admin_features": {
                    "admin": True,  # Always true
                    "manager": manager_admin,
                    "team_member": team_member_admin
                }
            }
            
            if save_permissions(new_permissions):
                st.success("Permissions updated successfully!")
            else:
                st.error("Failed to update permissions.")
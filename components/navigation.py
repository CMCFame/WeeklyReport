# components/navigation.py

"""Navigation component for the Weekly Report app."""

import streamlit as st

def render_navigation():
    """Render the main navigation sidebar."""
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    
    # Store the current section and page in session state
    if "nav_section" not in st.session_state:
        st.session_state.nav_section = "reporting"
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "Weekly Report"
    
    # Define sections and their pages based on user role
    sections = {
        "reporting": {
            "icon": "📋",
            "title": "REPORTING",
            "pages": ["Weekly Report", "Past Reports", "Report Templates", "Report Analytics", "Advanced Analytics", "Batch Export"] 
        },
        "goals": {
            "icon": "🎯",
            "title": "GOALS & TRACKING",
            "pages": ["Team Objectives", "Goal Dashboard", "OKR Management"]
        },
        "team": {
            "icon": "👥",
            "title": "TEAM MANAGEMENT",
            "pages": ["Team Structure", "1:1 Meetings"]
        },
        "admin": {
            "icon": "⚙️",
            "title": "ADMINISTRATION",
            "pages": ["User Profile", "Project Data"]
        }
    }
    
    # Add role-specific pages
    if user_role == "admin":
        sections["team"]["pages"].insert(0, "User Management")
        sections["admin"]["pages"].extend(["Import Users", "Import Reports", "System Settings"])
        sections["goals"]["pages"].append("Import Objectives")
    elif user_role == "manager":
        sections["team"]["pages"].insert(0, "User Management")
        sections["admin"]["pages"].append("Import Reports")
        sections["goals"]["pages"].append("Import Objectives")
    
    # Render each section
    for section_key, section in sections.items():
        # Don't show Team Management to regular users
        if section_key == "team" and user_role == "team_member":
            continue
            
        # Create expandable section
        expanded = st.session_state.nav_section == section_key
        with st.sidebar.expander(f"{section['icon']} {section['title']}", expanded=expanded):
            # Render pages in this section
            for page_idx, page in enumerate(section["pages"]):
                # Skip pages that require higher permissions
                if page in ["User Management", "Import Users", "Import Reports", "System Settings", "Import Objectives"] and user_role == "team_member":
                    continue
                    
                # Select page button - use a unique key combining section, page and index
                is_active = st.session_state.nav_page == page
                label = f"**{page}**" if is_active else page
                
                # Generate unique key using section, page name and index for absolute uniqueness
                unique_key = f"nav_{section_key}_{page_idx}_{page.replace(' ', '_')}"
                
                if st.button(label, key=unique_key, use_container_width=True):
                    st.session_state.nav_section = section_key
                    st.session_state.nav_page = page
                    st.rerun()

def get_current_page():
    """Get the currently selected page."""
    return st.session_state.get("nav_page", "Weekly Report")

def set_page(page_name):
    """Set the current page programmatically."""
    # Determine the section for this page
    for section_key, section in {
        "reporting": ["Weekly Report", "Past Reports", "Report Templates", "Report Analytics", "Advanced Analytics", "Batch Export"],
        "goals": ["Team Objectives", "Goal Dashboard", "OKR Management", "Import Objectives"],
        "team": ["User Management", "Team Structure", "1:1 Meetings"],
        "admin": ["User Profile", "Project Data", "Import Users", "Import Reports", "System Settings"]
    }.items():
        if page_name in section:
            st.session_state.nav_section = section_key
            break
            
    st.session_state.nav_page = page_name
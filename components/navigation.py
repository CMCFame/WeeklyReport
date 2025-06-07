# components/navigation.py - Updated with Feedback Dashboard

"""Navigation component for the Weekly Report app."""

import streamlit as st
import uuid  
from utils.permissions import check_section_access

def render_navigation():
    """Render the main navigation sidebar with permission checks."""
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    username = st.session_state.get("user_info", {}).get("username") # Get username for individual permissions
    
    # Store the current section and page in session state
    if "nav_section" not in st.session_state:
        st.session_state.nav_section = "reporting"
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "Weekly Report"
    
    # Define sections and their pages based on user role
    # These page names are used as 'section_name' in check_section_access
    sections = {
        "reporting": {
            "icon": "📝",
            "title": "REPORTING",
            "pages": ["Weekly Report", "Past Reports", "Report Templates", "Report Analytics", "Advanced Analytics", "Batch Export"] 
        },
        "ai": {
            "icon": "🤖",
            "title": "AI ASSISTANT",
            "pages": ["AI Voice Assistant", "Smart Suggestions"]
        },
        "intelligence": {
            "icon": "🧠",
            "title": "AI INTELLIGENCE",
            "pages": ["Team Health Dashboard", "Predictive Intelligence", "Executive Summary"]
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
    
    # Add role-specific pages based on permissions
    # These additions are still subject to check_section_access which now includes user-specific flags
    if user_role == "admin":
        sections["team"]["pages"].insert(0, "User Management")
        sections["team"]["pages"].insert(1, "Feedback Dashboard")  # NEW: Add feedback dashboard for admins
        sections["admin"]["pages"].extend(["Import Users", "Import Reports", "System Settings"])
        sections["goals"]["pages"].append("Import Objectives")
    elif user_role == "manager":
        # Check permissions for each page before adding to manager's view
        if check_section_access("User Management", user_role, username):
            sections["team"]["pages"].insert(0, "User Management")
        
        # NEW: Always add Feedback Dashboard for managers
        sections["team"]["pages"].insert(-1 if "User Management" in sections["team"]["pages"] else 0, "Feedback Dashboard")
        
        if check_section_access("Import Reports", user_role, username):
            sections["admin"]["pages"].append("Import Reports")
        if check_section_access("Import Objectives", user_role, username):
            sections["goals"]["pages"].append("Import Objectives")
    
    # AI Intelligence section is only for managers and admins by default role-based permission
    # The check_section_access function will handle the individual user override.
    if user_role not in ["admin", "manager"]:
        sections.pop("intelligence", None)
    
    # Generate unique IDs for each section if they don't exist yet
    if "nav_section_ids" not in st.session_state:
        st.session_state.nav_section_ids = {}

    # Initialize unique IDs for sections and pages
    for section_key in sections:
        if section_key not in st.session_state.nav_section_ids:
            st.session_state.nav_section_ids[section_key] = {}
        
        section_pages = sections[section_key]["pages"]
        for page in section_pages:
            if page not in st.session_state.nav_section_ids[section_key]:
                # Generate a new unique ID and store it
                st.session_state.nav_section_ids[section_key][page] = str(uuid.uuid4())[:8]
    
    # Render each section with permission checks
    for section_key, section in sections.items():
        # A section (like "Goals" or "Team") might contain pages that are restricted.
        # We only expand the section if at least one page within it is accessible.
        # This is a simplification; a more robust check would iterate pages to see if any are accessible.
        # For now, we'll let check_section_access handle individual page visibility.
        
        # Check if the section itself should be displayed based on any of its pages being accessible
        # This prevents empty sections from appearing.
        has_accessible_page = False
        for page in section["pages"]:
            if check_section_access(page, user_role, username):
                has_accessible_page = True
                break
        
        if not has_accessible_page:
            continue

        # Create expandable section
        expanded = st.session_state.nav_section == section_key
        with st.sidebar.expander(f"{section['icon']} {section['title']}", expanded=expanded):
            # Render pages in this section
            for page_idx, page in enumerate(section["pages"]):
                # Check permission for each individual page
                if not check_section_access(page, user_role, username): # Pass username
                    continue
                    
                # Select page button - use a unique key combining section, page and index
                is_active = st.session_state.nav_page == page
                label = f"**{page}**" if is_active else page
                
                # Use the stored unique ID for this page
                unique_id = st.session_state.nav_section_ids[section_key][page]
                unique_key = f"nav_{section_key}_{page.replace(' ', '_')}_{unique_id}"
                
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
    # This mapping should be kept consistent with the 'sections' dict above
    page_to_section_map = {
        "Weekly Report": "reporting", "Past Reports": "reporting", "Report Templates": "reporting",
        "Report Analytics": "reporting", "Advanced Analytics": "reporting", "Batch Export": "reporting",
        "AI Voice Assistant": "ai", "Smart Suggestions": "ai",
        "Team Health Dashboard": "intelligence", "Predictive Intelligence": "intelligence", "Executive Summary": "intelligence",
        "Team Objectives": "goals", "Goal Dashboard": "goals", "OKR Management": "goals", "Import Objectives": "goals",
        "User Management": "team", "Team Structure": "team", "1:1 Meetings": "team", "Feedback Dashboard": "team",  # NEW: Add Feedback Dashboard mapping
        "User Profile": "admin", "Project Data": "admin", "Import Users": "admin", "Import Reports": "admin", "System Settings": "admin"
    }
    
    if page_name in page_to_section_map:
        st.session_state.nav_section = page_to_section_map[page_name]
            
    st.session_state.nav_page = page_name
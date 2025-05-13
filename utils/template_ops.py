# utils/template_ops.py
"""Template operations for the Weekly Report app."""

import json
import uuid
import os
from datetime import datetime
from pathlib import Path
import streamlit as st

def ensure_templates_directory():
    """Ensure the templates directory exists."""
    try:
        templates_dir = Path("data/templates")
        templates_dir.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        st.error(f"Error creating templates directory: {str(e)}")
        return False

def save_template(template_data):
    """Save template data to a JSON file.
    
    Args:
        template_data (dict): Template data to save
        
    Returns:
        str: Template ID
    """
    try:
        ensure_templates_directory()
        template_id = template_data.get('id', str(uuid.uuid4()))
        template_data['id'] = template_id
        
        # Add user_id from session state if authenticated
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            template_data['user_id'] = st.session_state.user_info.get("id")
            template_data['user_name'] = st.session_state.user_info.get("full_name", "")
            
        # Add timestamp if not present
        if 'created_at' not in template_data:
            template_data['created_at'] = datetime.now().isoformat()
            
        template_data['updated_at'] = datetime.now().isoformat()
        
        with open(f"data/templates/{template_id}.json", 'w') as f:
            json.dump(template_data, f, indent=2)
        
        return template_id
    except Exception as e:
        st.error(f"Error saving template: {str(e)}")
        return None

def load_template(template_id):
    """Load template data from a JSON file.
    
    Args:
        template_id (str): ID of the template to load
        
    Returns:
        dict: Template data or None if not found
    """
    try:
        with open(f"data/templates/{template_id}.json", 'r') as f:
            template_data = json.load(f)
            
        # Check if user has access to this template
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            user_id = st.session_state.user_info.get("id")
            user_role = st.session_state.user_info.get("role")
            template_user_id = template_data.get("user_id")
            
            # Admin can access all templates
            if user_role == "admin":
                return template_data
            
            # Managers can access their team members' templates
            if user_role == "manager":
                # For now, assume managers can see all templates
                return template_data
            
            # Check if template is shared
            if template_data.get("is_shared", False):
                return template_data
                
            # Normal users can only access their own templates
            if template_user_id and template_user_id != user_id:
                st.error("You don't have permission to access this template.")
                return None
                
        return template_data
    except FileNotFoundError:
        st.error(f"Template with ID {template_id} not found.")
        return None
    except json.JSONDecodeError:
        st.error(f"Invalid JSON in template file {template_id}.")
        return None
    except Exception as e:
        st.error(f"Error loading template {template_id}: {str(e)}")
        return None

def get_all_templates(filter_by_user=True):
    """Get a list of all saved templates.
    
    Args:
        filter_by_user (bool): If True, only return templates for the current user
    
    Returns:
        list: List of template data dictionaries, sorted by updated timestamp (newest first)
    """
    try:
        ensure_templates_directory()
        templates = []
        
        # Get current user ID if authenticated
        current_user_id = None
        user_role = None
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            current_user_id = st.session_state.user_info.get("id")
            user_role = st.session_state.user_info.get("role")
        
        for file_path in Path("data/templates").glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    template = json.load(f)
                    
                    # Filter by user if requested and not admin/manager
                    if filter_by_user and current_user_id and user_role != "admin":
                        template_user_id = template.get("user_id")
                        
                        # Managers can see all templates
                        if user_role == "manager":
                            templates.append(template)
                        # Include shared templates
                        elif template.get("is_shared", False):
                            templates.append(template)
                        # Team members can only see their own templates
                        elif template_user_id and template_user_id == current_user_id:
                            templates.append(template)
                    else:
                        templates.append(template)
                        
            except Exception as e:
                st.warning(f"Error loading template {file_path}: {str(e)}")
        
        return sorted(templates, key=lambda x: x.get('updated_at', ''), reverse=True)
    except Exception as e:
        st.error(f"Error retrieving templates: {str(e)}")
        return []

def delete_template(template_id):
    """Delete a template file.
    
    Args:
        template_id (str): ID of the template to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        # Check if user has permission to delete this template
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            try:
                with open(f"data/templates/{template_id}.json", 'r') as f:
                    template_data = json.load(f)
                
                user_id = st.session_state.user_info.get("id")
                user_role = st.session_state.user_info.get("role")
                template_user_id = template_data.get("user_id")
                
                # Only the template owner, managers, and admins can delete
                if user_role not in ["admin", "manager"] and template_user_id != user_id:
                    st.error("You don't have permission to delete this template.")
                    return False
            except:
                # If we can't open the file, just try to delete it
                pass
        
        os.remove(f"data/templates/{template_id}.json")
        return True
    except FileNotFoundError:
        st.error(f"Template with ID {template_id} not found.")
        return False
    except Exception as e:
        st.error(f"Error deleting template {template_id}: {str(e)}")
        return False

def apply_template_to_session(template_id):
    """Apply a template to the current session state.
    
    Args:
        template_id (str): ID of the template to apply
        
    Returns:
        bool: True if applied successfully, False otherwise
    """
    try:
        template_data = load_template(template_id)
        if not template_data:
            return False
        
        # Apply template fields to session state
        if template_data.get('current_activities'):
            st.session_state.current_activities = template_data['current_activities'].copy()
        
        if template_data.get('upcoming_activities'):
            st.session_state.upcoming_activities = template_data['upcoming_activities'].copy()
            
        # Apply optional sections
        for section_key in template_data.get('optional_sections', {}):
            if section_key in st.session_state:
                st.session_state[section_key] = template_data['optional_sections'][section_key]
                
            # Also copy the content if available
            content_key = section_key.replace('show_', '') if section_key.startswith('show_') else None
            if content_key and content_key in template_data.get('optional_section_contents', {}):
                st.session_state[content_key] = template_data['optional_section_contents'][content_key]
        
        return True
    except Exception as e:
        st.error(f"Error applying template: {str(e)}")
        return False

def create_template_from_session():
    """Create a template from the current session state.
    
    Returns:
        dict: Template data
    """
    from utils.session import collect_form_data
    
    # Collect current form data
    report_data = collect_form_data()
    
    # Extract relevant fields for template
    template_data = {
        'title': '',  # Will be set by user
        'description': '',  # Will be set by user
        'is_shared': False,  # Default not shared
        'current_activities': report_data.get('current_activities', []),
        'upcoming_activities': report_data.get('upcoming_activities', []),
        'optional_sections': {},
        'optional_section_contents': {}
    }
    
    # Save which optional sections are enabled
    from utils.constants import OPTIONAL_SECTIONS
    for section in OPTIONAL_SECTIONS:
        section_key = section['key']
        content_key = section['content_key']
        
        # Save section visibility state
        template_data['optional_sections'][section_key] = st.session_state.get(section_key, False)
        
        # Save section content
        if st.session_state.get(section_key, False) and st.session_state.get(content_key):
            template_data['optional_section_contents'][content_key] = st.session_state.get(content_key)
    
    return template_data
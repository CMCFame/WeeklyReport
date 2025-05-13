# components/report_templates.py
"""Report templates component for the Weekly Report app."""

import streamlit as st
import json
import uuid
from datetime import datetime
from utils import session, file_ops

def render_report_templates():
    """Render the report templates management page."""
    st.title("Report Templates")
    st.write("Create and manage templates to streamline your weekly reporting process.")
    
    # Tab navigation for template actions
    tab1, tab2, tab3 = st.tabs(["My Templates", "Create Template", "Team Templates"])
    
    with tab1:
        render_templates_list()
    
    with tab2:
        render_create_template()
    
    with tab3:
        render_team_templates()

def render_templates_list():
    """Render the list of user's templates."""
    st.subheader("My Templates")
    
    # Get templates for current user
    templates = get_user_templates()
    
    if not templates:
        st.info("You don't have any saved templates yet. Create your first template to get started!")
        
        # Show a quick button to create a template
        if st.button("Create My First Template"):
            # Switch to the Create Template tab
            # In a real implementation, we'd need JavaScript to do this
            # For now, we'll just show a message
            st.success("Click on the 'Create Template' tab above to create a new template.")
        return
    
    # Display each template with action buttons
    for i, template in enumerate(templates):
        with st.expander(f"{template.get('name', 'Unnamed Template')}"):
            # Template info
            st.write(f"**Description:** {template.get('description', 'No description')}")
            st.write(f"**Created:** {template.get('created_at', '')[:10]}")
            
            # Preview Template Structure
            st.write("**Template Structure:**")
            
            # Show which sections are included
            sections = []
            if template.get('include_current_activities', True):
                sections.append("✓ Current Activities")
            if template.get('include_upcoming_activities', True):
                sections.append("✓ Upcoming Activities")
            if template.get('include_accomplishments', True):
                sections.append("✓ Last Week's Accomplishments")
            if template.get('include_followups', True):
                sections.append("✓ Follow-ups")
            if template.get('include_nextsteps', True):
                sections.append("✓ Next Steps")
                
            # Add optional sections
            for section in template.get('optional_sections', []):
                sections.append(f"✓ {section.get('label', 'Custom Section')}")
            
            # Display sections as pills
            cols = st.columns(3)
            for idx, section in enumerate(sections):
                cols[idx % 3].markdown(f"""
                <div style="background-color: #f0f2f6; padding: 5px 10px; 
                     border-radius: 15px; margin-bottom: 10px; display: inline-block;">
                    {section}
                </div>
                """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Use Template", key=f"use_template_{i}"):
                    load_template(template)
                    st.success("Template loaded! Redirecting to Weekly Report...")
                    # Ideally this would redirect to the Weekly Report page
                    st.session_state.nav_page = "Weekly Report"
                    st.session_state.nav_section = "reporting"
                    st.rerun()
            
            with col2:
                if st.button("Edit Template", key=f"edit_template_{i}"):
                    # Set the selected template for editing
                    st.session_state.editing_template = template
                    st.rerun()
            
            with col3:
                if st.button("Delete", key=f"delete_template_{i}"):
                    # Confirm deletion
                    st.warning("Are you sure you want to delete this template?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Yes, delete", key=f"confirm_delete_{i}"):
                            delete_template(template.get('id'))
                            st.success("Template deleted successfully!")
                            st.rerun()
                    with col_no:
                        if st.button("Cancel", key=f"cancel_delete_{i}"):
                            st.rerun()

def render_create_template():
    """Render the template creation form."""
    # Check if we're editing an existing template
    editing_mode = False
    if hasattr(st.session_state, 'editing_template') and st.session_state.editing_template:
        editing_mode = True
        template = st.session_state.editing_template
        st.subheader("Edit Template")
    else:
        template = {}
        st.subheader("Create New Template")
    
    # Template basic info
    template_name = st.text_input(
        "Template Name",
        value=template.get('name', ''),
        help="Give your template a descriptive name"
    )
    
    template_description = st.text_area(
        "Description",
        value=template.get('description', ''),
        help="Describe what this template is best used for"
    )
    
    # Section toggles
    st.subheader("Include Sections")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_current_activities = st.toggle(
            "Current Activities", 
            value=template.get('include_current_activities', True),
            help="Track what you're working on now"
        )
        
        include_upcoming_activities = st.toggle(
            "Upcoming Activities", 
            value=template.get('include_upcoming_activities', True),
            help="Plan future work"
        )
        
        include_accomplishments = st.toggle(
            "Last Week's Accomplishments", 
            value=template.get('include_accomplishments', True),
            help="Document what you've completed"
        )
    
    with col2:
        include_followups = st.toggle(
            "Follow-ups", 
            value=template.get('include_followups', True),
            help="Track action items from previous meetings"
        )
        
        include_nextsteps = st.toggle(
            "Next Steps", 
            value=template.get('include_nextsteps', True),
            help="Plan action items for next week"
        )
    
    # Optional sections
    st.subheader("Optional Sections")
    
    # Get the current optional sections
    from utils.constants import OPTIONAL_SECTIONS
    
    # Initialize selected_optional_sections if not already in template
    if 'optional_sections' not in template:
        template['optional_sections'] = []
    
    # Convert to a dict for easier lookup
    selected_sections = {
        section.get('key'): section
        for section in template.get('optional_sections', [])
    }
    
    # Show toggles for each optional section
    for section in OPTIONAL_SECTIONS:
        is_selected = section['key'] in selected_sections
        
        if st.toggle(
            section['label'],
            value=is_selected,
            help=section['description'],
            key=f"template_section_{section['key']}"
        ):
            # Add to selected if not already there
            if section['key'] not in selected_sections:
                selected_sections[section['key']] = {
                    'key': section['key'],
                    'label': section['label'],
                    'icon': section['icon'],
                    'content_key': section['content_key'],
                    'description': section['description']
                }
        else:
            # Remove if it was selected
            if section['key'] in selected_sections:
                del selected_sections[section['key']]
    
    # Default content options
    st.subheader("Default Content")
    
    with st.expander("Pre-filled Template Content (Optional)"):
        st.write("You can provide default content that will be pre-filled when using this template:")
        
        if include_accomplishments:
            st.write("**Default Accomplishments:**")
            default_accomplishments = template.get('default_accomplishments', [""])
            
            # Display text areas for existing items
            for i, item in enumerate(default_accomplishments):
                default_accomplishments[i] = st.text_area(
                    f"Accomplishment {i+1}" if i > 0 else "Accomplishment",
                    value=item,
                    key=f"default_acc_{i}"
                )
            
            # Add button for new item
            if st.button("+ Add Accomplishment", key="add_default_acc"):
                default_accomplishments.append("")
                st.rerun()
        
        if include_nextsteps:
            st.write("**Default Next Steps:**")
            default_nextsteps = template.get('default_nextsteps', [""])
            
            # Display text areas for existing items
            for i, item in enumerate(default_nextsteps):
                default_nextsteps[i] = st.text_area(
                    f"Next Step {i+1}" if i > 0 else "Next Step",
                    value=item,
                    key=f"default_next_{i}"
                )
            
            # Add button for new item
            if st.button("+ Add Next Step", key="add_default_next"):
                default_nextsteps.append("")
                st.rerun()
        
        # Optional sections default content
        for key, section in selected_sections.items():
            content_key = section['content_key']
            st.write(f"**Default {section['label']}:**")
            
            # Get the current default value
            default_content = template.get(f'default_{content_key}', "")
            
            # Display a text area for this section
            updated_content = st.text_area(
                section['label'],
                value=default_content,
                key=f"default_{content_key}"
            )
            
            # Update the value
            template[f'default_{content_key}'] = updated_content
    
    # Save Button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Collect all the data into a template object
        new_template = {
            'id': template.get('id', str(uuid.uuid4())),
            'user_id': st.session_state.user_info.get('id'),
            'name': template_name,
            'description': template_description,
            'include_current_activities': include_current_activities,
            'include_upcoming_activities': include_upcoming_activities,
            'include_accomplishments': include_accomplishments,
            'include_followups': include_followups,
            'include_nextsteps': include_nextsteps,
            'optional_sections': list(selected_sections.values()),
            'created_at': template.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat(),
            'is_team_template': template.get('is_team_template', False)
        }
        
        # Add default content if provided
        if include_accomplishments:
            new_template['default_accomplishments'] = [
                acc for acc in default_accomplishments if acc.strip()
            ]
        
        if include_nextsteps:
            new_template['default_nextsteps'] = [
                step for step in default_nextsteps if step.strip()
            ]
    
    with col2:
        save_label = "Update Template" if editing_mode else "Save Template"
        if st.button(save_label, type="primary", use_container_width=True):
            if not template_name:
                st.error("Please provide a template name.")
            else:
                save_template(new_template)
                if editing_mode:
                    st.success("Template updated successfully!")
                    # Clear the editing state
                    st.session_state.editing_template = None
                else:
                    st.success("Template created successfully!")
                st.rerun()

def render_team_templates():
    """Render team-shared templates."""
    st.subheader("Team Templates")
    
    user_role = st.session_state.user_info.get('role', 'team_member')
    
    # Check if user is admin or manager
    is_manager = user_role in ["admin", "manager"]
    
    # Get team templates
    team_templates = get_team_templates()
    
    if not team_templates:
        if is_manager:
            st.info("No team templates yet. As a manager, you can create team templates that will be available to all team members.")
            if st.button("Create Team Template"):
                # Initialize a new team template
                st.session_state.creating_team_template = True
                st.rerun()
        else:
            st.info("No team templates available. Team templates are created by managers and administrators.")
        return
    
    # Display team templates
    for i, template in enumerate(team_templates):
        with st.expander(f"{template.get('name', 'Unnamed Template')}"):
            # Template info
            st.write(f"**Description:** {template.get('description', 'No description')}")
            created_by = template.get('created_by', 'Unknown')
            st.write(f"**Created by:** {created_by}")
            st.write(f"**Created:** {template.get('created_at', '')[:10]}")
            
            # Preview Template Structure
            st.write("**Template Structure:**")
            
            # Show which sections are included
            sections = []
            if template.get('include_current_activities', True):
                sections.append("✓ Current Activities")
            if template.get('include_upcoming_activities', True):
                sections.append("✓ Upcoming Activities")
            if template.get('include_accomplishments', True):
                sections.append("✓ Last Week's Accomplishments")
            if template.get('include_followups', True):
                sections.append("✓ Follow-ups")
            if template.get('include_nextsteps', True):
                sections.append("✓ Next Steps")
                
            # Add optional sections
            for section in template.get('optional_sections', []):
                sections.append(f"✓ {section.get('label', 'Custom Section')}")
            
            # Display sections as pills
            cols = st.columns(3)
            for idx, section in enumerate(sections):
                cols[idx % 3].markdown(f"""
                <div style="background-color: #f0f2f6; padding: 5px 10px; 
                     border-radius: 15px; margin-bottom: 10px; display: inline-block;">
                    {section}
                </div>
                """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Use Template", key=f"use_team_template_{i}"):
                    load_template(template)
                    st.success("Template loaded! Redirecting to Weekly Report...")
                    # Ideally this would redirect to the Weekly Report page
                    st.session_state.nav_page = "Weekly Report"
                    st.session_state.nav_section = "reporting"
                    st.rerun()
            
            with col2:
                # Only managers can edit or delete team templates
                if is_manager:
                    if st.button("Edit Template", key=f"edit_team_template_{i}"):
                        # Set the selected template for editing
                        st.session_state.editing_template = template
                        st.rerun()
                    
                    if st.button("Delete", key=f"delete_team_template_{i}"):
                        # Confirm deletion
                        st.warning("Are you sure you want to delete this team template?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("Yes, delete", key=f"confirm_team_delete_{i}"):
                                delete_template(template.get('id'))
                                st.success("Team template deleted successfully!")
                                st.rerun()
                        with col_no:
                            if st.button("Cancel", key=f"cancel_team_delete_{i}"):
                                st.rerun()

def get_user_templates():
    """Get templates for the current user.
    
    Returns:
        list: List of template dictionaries
    """
    try:
        # Ensure the templates directory exists
        Path("data/templates").mkdir(parents=True, exist_ok=True)
        
        # Get user ID
        user_id = st.session_state.user_info.get('id')
        
        # Get all template files
        templates = []
        template_files = list(Path("data/templates").glob("*.json"))
        
        for file_path in template_files:
            try:
                with open(file_path, 'r') as f:
                    template = json.load(f)
                
                # Check if it belongs to current user and is not a team template
                if template.get('user_id') == user_id and not template.get('is_team_template', False):
                    templates.append(template)
                    
            except Exception as e:
                st.error(f"Error loading template {file_path}: {str(e)}")
        
        return sorted(templates, key=lambda x: x.get('name', '').lower())
        
    except Exception as e:
        st.error(f"Error retrieving templates: {str(e)}")
        return []

def get_team_templates():
    """Get team templates.
    
    Returns:
        list: List of team template dictionaries
    """
    try:
        # Ensure the templates directory exists
        Path("data/templates").mkdir(parents=True, exist_ok=True)
        
        # Get all template files
        templates = []
        template_files = list(Path("data/templates").glob("*.json"))
        
        for file_path in template_files:
            try:
                with open(file_path, 'r') as f:
                    template = json.load(f)
                
                # Check if it's a team template
                if template.get('is_team_template', False):
                    templates.append(template)
                    
            except Exception as e:
                st.error(f"Error loading template {file_path}: {str(e)}")
        
        return sorted(templates, key=lambda x: x.get('name', '').lower())
        
    except Exception as e:
        st.error(f"Error retrieving team templates: {str(e)}")
        return []

def save_template(template):
    """Save a template to file.
    
    Args:
        template (dict): Template data to save
        
    Returns:
        str: Template ID
    """
    try:
        # Ensure the templates directory exists
        Path("data/templates").mkdir(parents=True, exist_ok=True)
        
        # Generate ID if needed
        if 'id' not in template:
            template['id'] = str(uuid.uuid4())
        
        # Set timestamps
        if 'created_at' not in template:
            template['created_at'] = datetime.now().isoformat()
        template['updated_at'] = datetime.now().isoformat()
        
        # Add user info
        if 'user_id' not in template:
            template['user_id'] = st.session_state.user_info.get('id')
        if 'created_by' not in template:
            template['created_by'] = st.session_state.user_info.get('full_name')
        
        # Save to file
        with open(f"data/templates/{template['id']}.json", 'w') as f:
            json.dump(template, f, indent=2)
        
        return template['id']
        
    except Exception as e:
        st.error(f"Error saving template: {str(e)}")
        return None

def delete_template(template_id):
    """Delete a template file.
    
    Args:
        template_id (str): ID of the template to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        # Check if file exists
        file_path = Path(f"data/templates/{template_id}.json")
        if not file_path.exists():
            st.error(f"Template with ID {template_id} not found.")
            return False
        
        # Delete file
        file_path.unlink()
        return True
        
    except Exception as e:
        st.error(f"Error deleting template: {str(e)}")
        return False

def load_template(template):
    """Load a template into the session state for use in Weekly Report.
    
    Args:
        template (dict): Template data to load
    """
    try:
        # Reset the form first
        session.reset_form()
        
        # Load included sections
        
        # Current activities
        if template.get('include_current_activities', True):
            # We just add one empty activity
            session.add_current_activity()
        
        # Upcoming activities
        if template.get('include_upcoming_activities', True):
            # Add one empty upcoming activity
            session.add_upcoming_activity()
        
        # Accomplishments
        if template.get('include_accomplishments', True):
            # Load default accomplishments if any
            default_accomplishments = template.get('default_accomplishments', [""])
            if default_accomplishments:
                st.session_state.accomplishments = default_accomplishments
        
        # Action items - followups
        if template.get('include_followups', True):
            # Just initialize with empty list
            st.session_state.followups = [""]
        
        # Action items - next steps
        if template.get('include_nextsteps', True):
            # Load default next steps if any
            default_nextsteps = template.get('default_nextsteps', [""])
            if default_nextsteps:
                st.session_state.nextsteps = default_nextsteps
        
        # Optional sections
        for section in template.get('optional_sections', []):
            key = section.get('key')
            content_key = section.get('content_key')
            
            if key and content_key:
                # Enable the section
                st.session_state[key] = True
                
                # Set default content if available
                default_content = template.get(f'default_{content_key}', "")
                if default_content:
                    st.session_state[content_key] = default_content
        
    except Exception as e:
        st.error(f"Error loading template: {str(e)}")
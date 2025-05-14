# utils/meeting_utils.py
"""Meeting utilities for the Weekly Report app."""

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st

def ensure_meetings_directory():
    """Ensure the meetings directory exists."""
    Path("data/meetings").mkdir(parents=True, exist_ok=True)
    
def load_meeting_templates():
    """Load the meeting templates from file.
    
    Returns:
        list: List of meeting templates
    """
    ensure_meetings_directory()
    
    # Check if templates file exists
    templates_file = Path("data/meetings/templates.json")
    if not templates_file.exists():
        # Create default templates
        default_templates = [
            {
                "id": str(uuid.uuid4()),
                "name": "Standard 1:1",
                "description": "General 1:1 meeting template",
                "sections": [
                    {"title": "Check-in", "description": "How are you doing?"},
                    {"title": "Progress Update", "description": "What progress have you made since our last meeting?"},
                    {"title": "Challenges", "description": "What challenges are you facing?"},
                    {"title": "Support Needed", "description": "How can I help you?"},
                    {"title": "Goals", "description": "What are your goals for the next period?"},
                    {"title": "Action Items", "description": "What actions need to be taken?"}
                ],
                "created_at": datetime.now().isoformat()
            }
        ]
        save_meeting_templates(default_templates)
        return default_templates
    
    try:
        with open(templates_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading meeting templates: {str(e)}")
        return []

def save_meeting_templates(templates):
    """Save the meeting templates to file.
    
    Args:
        templates (list): List of meeting templates
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    ensure_meetings_directory()
    
    try:
        with open("data/meetings/templates.json", 'w') as f:
            json.dump(templates, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving meeting templates: {str(e)}")
        return False

def get_meetings():
    """Get a list of all meetings.
    
    Returns:
        list: List of meeting dictionaries
    """
    ensure_meetings_directory()
    
    meetings = []
    
    try:
        # Get current user ID for filtering
        current_user_id = None
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            current_user_id = st.session_state.user_info.get("id")
        
        # Get all meeting files
        for meeting_file in Path("data/meetings").glob("meeting_*.json"):
            try:
                with open(meeting_file, 'r') as f:
                    meeting = json.load(f)
                
                # Filter for meetings involving the current user
                if current_user_id:
                    if (meeting.get("manager_user_id") == current_user_id or 
                        meeting.get("team_member_user_id") == current_user_id):
                        meetings.append(meeting)
                else:
                    meetings.append(meeting)
                
            except Exception as e:
                st.warning(f"Error loading meeting {meeting_file}: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading meetings: {str(e)}")
    
    # Sort by scheduled date (most recent first)
    return sorted(meetings, key=lambda x: x.get("scheduled_date", ""), reverse=True)

def add_meeting_template(name, description, sections):
    """Add a new meeting template.
    
    Args:
        name (str): Template name
        description (str): Template description
        sections (list): List of section dictionaries
        
    Returns:
        str: Template ID if added successfully, None otherwise
    """
    templates = load_meeting_templates()
    
    # Create new template
    template_id = str(uuid.uuid4())
    new_template = {
        "id": template_id,
        "name": name,
        "description": description,
        "sections": sections,
        "created_at": datetime.now().isoformat()
    }
    
    # Add to list
    templates.append(new_template)
    
    # Save updated templates
    if save_meeting_templates(templates):
        return template_id
    
    return None

def update_meeting_template(template_id, name=None, description=None, sections=None):
    """Update a meeting template.
    
    Args:
        template_id (str): Template ID
        name (str): New template name (optional)
        description (str): New template description (optional)
        sections (list): New sections (optional)
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    templates = load_meeting_templates()
    
    # Find template
    for template in templates:
        if template["id"] == template_id:
            # Update fields if provided
            if name is not None:
                template["name"] = name
            if description is not None:
                template["description"] = description
            if sections is not None:
                template["sections"] = sections
            
            # Save updated templates
            return save_meeting_templates(templates)
    
    st.error(f"Template with ID {template_id} not found.")
    return False

def delete_meeting_template(template_id):
    """Delete a meeting template.
    
    Args:
        template_id (str): Template ID
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    templates = load_meeting_templates()
    
    # Remove template
    templates = [t for t in templates if t["id"] != template_id]
    
    # Save updated templates
    return save_meeting_templates(templates)

def get_template_by_id(template_id):
    """Get a meeting template by ID.
    
    Args:
        template_id (str): Template ID
        
    Returns:
        dict: Template data if found, None otherwise
    """
    templates = load_meeting_templates()
    
    for template in templates:
        if template["id"] == template_id:
            return template
    
    return None

def create_meeting(
    manager_name, team_member_name, 
    scheduled_date, template_id=None,
    manager_user_id=None, team_member_user_id=None
):
    """Create a new 1:1 meeting.
    
    Args:
        manager_name (str): Manager name
        team_member_name (str): Team member name
        scheduled_date (str): Scheduled date (YYYY-MM-DD format)
        template_id (str): Template ID (optional)
        manager_user_id (str): Manager user ID (optional)
        team_member_user_id (str): Team member user ID (optional)
        
    Returns:
        str: Meeting ID if created successfully, None otherwise
    """
    ensure_meetings_directory()
    
    # Generate meeting ID
    meeting_id = str(uuid.uuid4())
    
    # Load template if provided
    sections = []
    template_name = "Custom"
    
    if template_id:
        template = get_template_by_id(template_id)
        if template:
            sections = template["sections"]
            template_name = template["name"]
    
    # Create meeting object
    meeting = {
        "id": meeting_id,
        "manager_name": manager_name,
        "team_member_name": team_member_name,
        "manager_user_id": manager_user_id,
        "team_member_user_id": team_member_user_id,
        "scheduled_date": scheduled_date,
        "template_name": template_name,
        "template_id": template_id,
        "status": "Scheduled",
        "sections": [{"title": s["title"], "description": s["description"], "content": ""} for s in sections],
        "action_items": [],
        "notes": "",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Save meeting
    try:
        with open(f"data/meetings/meeting_{meeting_id}.json", 'w') as f:
            json.dump(meeting, f, indent=2)
        return meeting_id
    except Exception as e:
        st.error(f"Error creating meeting: {str(e)}")
        return None

def update_meeting(
    meeting_id, status=None, sections=None, 
    action_items=None, notes=None, scheduled_date=None
):
    """Update a meeting.
    
    Args:
        meeting_id (str): Meeting ID
        status (str): New status (optional)
        sections (list): Updated sections (optional)
        action_items (list): Updated action items (optional)
        notes (str): Updated notes (optional)
        scheduled_date (str): New scheduled date (optional)
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        # Load meeting
        with open(f"data/meetings/meeting_{meeting_id}.json", 'r') as f:
            meeting = json.load(f)
        
        # Update fields if provided
        if status is not None:
            meeting["status"] = status
        if sections is not None:
            meeting["sections"] = sections
        if action_items is not None:
            meeting["action_items"] = action_items
        if notes is not None:
            meeting["notes"] = notes
        if scheduled_date is not None:
            meeting["scheduled_date"] = scheduled_date
        
        # Update timestamp
        meeting["updated_at"] = datetime.now().isoformat()
        
        # Save updated meeting
        with open(f"data/meetings/meeting_{meeting_id}.json", 'w') as f:
            json.dump(meeting, f, indent=2)
        
        return True
    except Exception as e:
        st.error(f"Error updating meeting: {str(e)}")
        return False

def delete_meeting(meeting_id):
    """Delete a meeting.
    
    Args:
        meeting_id (str): Meeting ID
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        file_path = Path(f"data/meetings/meeting_{meeting_id}.json")
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting meeting: {str(e)}")
        return False

def get_meeting_by_id(meeting_id):
    """Get a meeting by ID.
    
    Args:
        meeting_id (str): Meeting ID
        
    Returns:
        dict: Meeting data if found, None otherwise
    """
    try:
        with open(f"data/meetings/meeting_{meeting_id}.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Error loading meeting: {str(e)}")
        return None

def add_action_item_to_meeting(
    meeting_id, description, assigned_to=None, 
    due_date=None, status="Pending", priority="Medium"
):
    """Add an action item to a meeting.
    
    Args:
        meeting_id (str): Meeting ID
        description (str): Action item description
        assigned_to (str): Person assigned to (optional)
        due_date (str): Due date (optional)
        status (str): Status (optional)
        priority (str): Priority (optional)
        
    Returns:
        bool: True if added successfully, False otherwise
    """
    try:
        # Load meeting
        with open(f"data/meetings/meeting_{meeting_id}.json", 'r') as f:
            meeting = json.load(f)
        
        # Create new action item
        action_item = {
            "id": str(uuid.uuid4()),
            "description": description,
            "assigned_to": assigned_to,
            "due_date": due_date,
            "status": status,
            "priority": priority,
            "created_at": datetime.now().isoformat()
        }
        
        # Add to meeting
        if "action_items" not in meeting:
            meeting["action_items"] = []
        
        meeting["action_items"].append(action_item)
        
        # Update timestamp
        meeting["updated_at"] = datetime.now().isoformat()
        
        # Save updated meeting
        with open(f"data/meetings/meeting_{meeting_id}.json", 'w') as f:
            json.dump(meeting, f, indent=2)
        
        return True
    except Exception as e:
        st.error(f"Error adding action item: {str(e)}")
        return False

def update_action_item(
    meeting_id, action_item_id, description=None, 
    assigned_to=None, due_date=None, status=None, priority=None
):
    """Update an action item.
    
    Args:
        meeting_id (str): Meeting ID
        action_item_id (str): Action item ID
        description (str): New description (optional)
        assigned_to (str): New person assigned to (optional)
        due_date (str): New due date (optional)
        status (str): New status (optional)
        priority (str): New priority (optional)
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        # Load meeting
        with open(f"data/meetings/meeting_{meeting_id}.json", 'r') as f:
            meeting = json.load(f)
        
        # Find action item
        for action_item in meeting.get("action_items", []):
            if action_item["id"] == action_item_id:
                # Update fields if provided
                if description is not None:
                    action_item["description"] = description
                if assigned_to is not None:
                    action_item["assigned_to"] = assigned_to
                if due_date is not None:
                    action_item["due_date"] = due_date
                if status is not None:
                    action_item["status"] = status
                if priority is not None:
                    action_item["priority"] = priority
                
                # Update timestamp
                meeting["updated_at"] = datetime.now().isoformat()
                
                # Save updated meeting
                with open(f"data/meetings/meeting_{meeting_id}.json", 'w') as f:
                    json.dump(meeting, f, indent=2)
                
                return True
        
        return False
    except Exception as e:
        st.error(f"Error updating action item: {str(e)}")
        return False

def get_all_action_items():
    """Get all action items across all meetings.
    
    Returns:
        list: List of action item dictionaries with meeting info
    """
    all_items = []
    
    try:
        # Get current user ID for filtering
        current_user_id = None
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            current_user_id = st.session_state.user_info.get("id")
        
        # Get all meeting files
        for meeting_file in Path("data/meetings").glob("meeting_*.json"):
            try:
                with open(meeting_file, 'r') as f:
                    meeting = json.load(f)
                
                # Skip if not related to current user
                if current_user_id:
                    if (meeting.get("manager_user_id") != current_user_id and 
                        meeting.get("team_member_user_id") != current_user_id):
                        continue
                
                # Process action items
                for item in meeting.get("action_items", []):
                    # Add meeting context to action item
                    enriched_item = item.copy()
                    enriched_item["meeting_id"] = meeting.get("id")
                    enriched_item["meeting_date"] = meeting.get("scheduled_date")
                    enriched_item["manager_name"] = meeting.get("manager_name")
                    enriched_item["team_member_name"] = meeting.get("team_member_name")
                    
                    all_items.append(enriched_item)
                
            except Exception as e:
                st.warning(f"Error loading action items from {meeting_file}: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading action items: {str(e)}")
    
    # Sort by due date (soonest first)
    return sorted(all_items, key=lambda x: x.get("due_date", "9999-12-31"))

def get_upcoming_meetings(days=7):
    """Get upcoming meetings within a specified number of days.
    
    Args:
        days (int): Number of days to look ahead
        
    Returns:
        list: List of upcoming meeting dictionaries
    """
    meetings = get_meetings()
    
    # Filter for upcoming meetings
    today = datetime.now().date()
    cutoff = today + timedelta(days=days)
    
    upcoming = []
    for meeting in meetings:
        try:
            meeting_date = datetime.strptime(meeting.get("scheduled_date", ""), "%Y-%m-%d").date()
            if today <= meeting_date <= cutoff and meeting.get("status") != "Completed":
                upcoming.append(meeting)
        except:
            pass
    
    # Sort by scheduled date
    return sorted(upcoming, key=lambda x: x.get("scheduled_date", ""))

def convert_action_items_to_next_steps(meeting_id):
    """Convert action items from a meeting to next steps in a weekly report.
    
    Args:
        meeting_id (str): Meeting ID
        
    Returns:
        list: List of next step strings
    """
    try:
        # Load meeting
        meeting = get_meeting_by_id(meeting_id)
        if not meeting:
            return []
        
        # Extract action items
        next_steps = []
        for item in meeting.get("action_items", []):
            description = item.get("description", "")
            assigned_to = item.get("assigned_to", "")
            due_date = item.get("due_date", "")
            
            step = description
            if assigned_to:
                step += f" ({assigned_to})"
            if due_date:
                step += f" - Due: {due_date}"
            
            next_steps.append(step)
        
        return next_steps
    
    except Exception as e:
        st.error(f"Error converting action items: {str(e)}")
        return []
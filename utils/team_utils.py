# utils/team_utils.py
"""Team management utilities for the Weekly Report app."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import streamlit as st

def ensure_teams_directory():
    """Ensure the teams directory exists."""
    Path("data/teams").mkdir(parents=True, exist_ok=True)
    
def load_team_structure():
    """Load the team structure from file.
    
    Returns:
        dict: Team structure data
    """
    ensure_teams_directory()
    
    # Check if team structure file exists
    structure_file = Path("data/teams/structure.json")
    if not structure_file.exists():
        # Create default structure
        default_structure = {
            "teams": [],
            "members": [],
            "relationships": []
        }
        save_team_structure(default_structure)
        return default_structure
    
    try:
        with open(structure_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading team structure: {str(e)}")
        return {"teams": [], "members": [], "relationships": []}

def save_team_structure(structure_data):
    """Save the team structure to file.
    
    Args:
        structure_data (dict): Team structure data to save
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    ensure_teams_directory()
    
    try:
        with open("data/teams/structure.json", 'w') as f:
            json.dump(structure_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving team structure: {str(e)}")
        return False

def get_team_members():
    """Get a list of all team members.
    
    Returns:
        list: List of team member dictionaries
    """
    structure = load_team_structure()
    return structure.get("members", [])

def get_teams():
    """Get a list of all teams.
    
    Returns:
        list: List of team dictionaries
    """
    structure = load_team_structure()
    return structure.get("teams", [])

def get_relationships():
    """Get a list of all reporting relationships.
    
    Returns:
        list: List of relationship dictionaries
    """
    structure = load_team_structure()
    return structure.get("relationships", [])

def add_team(name, description="", color="#3366cc"):
    """Add a new team.
    
    Args:
        name (str): Team name
        description (str): Team description
        color (str): Team color (hex code)
        
    Returns:
        str: Team ID if added successfully, None otherwise
    """
    structure = load_team_structure()
    
    # Check if team name already exists
    if any(team["name"] == name for team in structure["teams"]):
        st.error(f"Team '{name}' already exists.")
        return None
    
    # Create new team
    team_id = str(uuid.uuid4())
    new_team = {
        "id": team_id,
        "name": name,
        "description": description,
        "color": color,
        "created_at": datetime.now().isoformat()
    }
    
    # Add to structure
    structure["teams"].append(new_team)
    
    # Save updated structure
    if save_team_structure(structure):
        return team_id
    
    return None

def update_team(team_id, name=None, description=None, color=None):
    """Update a team.
    
    Args:
        team_id (str): Team ID
        name (str): New team name (optional)
        description (str): New team description (optional)
        color (str): New team color (optional)
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    structure = load_team_structure()
    
    # Find team
    for team in structure["teams"]:
        if team["id"] == team_id:
            # Update fields if provided
            if name is not None:
                team["name"] = name
            if description is not None:
                team["description"] = description
            if color is not None:
                team["color"] = color
            
            # Save updated structure
            return save_team_structure(structure)
    
    st.error(f"Team with ID {team_id} not found.")
    return False

def delete_team(team_id):
    """Delete a team.
    
    Args:
        team_id (str): Team ID
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    structure = load_team_structure()
    
    # Check if team exists
    team_exists = any(team["id"] == team_id for team in structure["teams"])
    
    if not team_exists:
        st.error(f"Team with ID {team_id} not found.")
        return False
    
    # Remove team
    structure["teams"] = [team for team in structure["teams"] if team["id"] != team_id]
    
    # Remove relationships involving this team
    for member in structure["members"]:
        if member.get("team_id") == team_id:
            member["team_id"] = None
    
    # Save updated structure
    return save_team_structure(structure)

def add_member(name, title="", email="", team_id=None, manager_id=None, user_id=None):
    """Add a new team member.
    
    Args:
        name (str): Member name
        title (str): Job title
        email (str): Email address
        team_id (str): Team ID (optional)
        manager_id (str): Manager ID (optional)
        user_id (str): User ID from authentication system (optional)
        
    Returns:
        str: Member ID if added successfully, None otherwise
    """
    structure = load_team_structure()
    
    # Create new member
    member_id = str(uuid.uuid4())
    new_member = {
        "id": member_id,
        "name": name,
        "title": title,
        "email": email,
        "team_id": team_id,
        "manager_id": manager_id,
        "user_id": user_id,
        "created_at": datetime.now().isoformat()
    }
    
    # Add to structure
    structure["members"].append(new_member)
    
    # Add relationship if manager is specified
    if manager_id:
        structure["relationships"].append({
            "manager_id": manager_id,
            "member_id": member_id
        })
    
    # Save updated structure
    if save_team_structure(structure):
        return member_id
    
    return None

def update_member(member_id, name=None, title=None, email=None, team_id=None, manager_id=None):
    """Update a team member.
    
    Args:
        member_id (str): Member ID
        name (str): New name (optional)
        title (str): New job title (optional)
        email (str): New email address (optional)
        team_id (str): New team ID (optional)
        manager_id (str): New manager ID (optional)
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    structure = load_team_structure()
    
    # Find member
    member_found = False
    old_manager_id = None
    
    for member in structure["members"]:
        if member["id"] == member_id:
            member_found = True
            old_manager_id = member.get("manager_id")
            
            # Update fields if provided
            if name is not None:
                member["name"] = name
            if title is not None:
                member["title"] = title
            if email is not None:
                member["email"] = email
            if team_id is not None:
                member["team_id"] = team_id
            if manager_id is not None:
                member["manager_id"] = manager_id
            
            break
    
    if not member_found:
        st.error(f"Team member with ID {member_id} not found.")
        return False
    
    # Update relationships if manager changed
    if manager_id is not None and manager_id != old_manager_id:
        # Remove old relationship
        if old_manager_id:
            structure["relationships"] = [
                r for r in structure["relationships"] 
                if not (r["manager_id"] == old_manager_id and r["member_id"] == member_id)
            ]
        
        # Add new relationship
        if manager_id:
            structure["relationships"].append({
                "manager_id": manager_id,
                "member_id": member_id
            })
    
    # Save updated structure
    return save_team_structure(structure)

def delete_member(member_id):
    """Delete a team member.
    
    Args:
        member_id (str): Member ID
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    structure = load_team_structure()
    
    # Check if member exists
    member_exists = any(member["id"] == member_id for member in structure["members"])
    
    if not member_exists:
        st.error(f"Team member with ID {member_id} not found.")
        return False
    
    # Remove member
    structure["members"] = [member for member in structure["members"] if member["id"] != member_id]
    
    # Remove relationships involving this member
    structure["relationships"] = [
        r for r in structure["relationships"] 
        if r["member_id"] != member_id and r["manager_id"] != member_id
    ]
    
    # Update manager references
    for member in structure["members"]:
        if member.get("manager_id") == member_id:
            member["manager_id"] = None
    
    # Save updated structure
    return save_team_structure(structure)

def get_member_by_user_id(user_id):
    """Get a team member by user ID.
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: Member data if found, None otherwise
    """
    structure = load_team_structure()
    
    for member in structure["members"]:
        if member.get("user_id") == user_id:
            return member
    
    return None

def get_team_by_id(team_id):
    """Get a team by ID.
    
    Args:
        team_id (str): Team ID
        
    Returns:
        dict: Team data if found, None otherwise
    """
    structure = load_team_structure()
    
    for team in structure["teams"]:
        if team["id"] == team_id:
            return team
    
    return None

def get_member_by_id(member_id):
    """Get a team member by ID.
    
    Args:
        member_id (str): Member ID
        
    Returns:
        dict: Member data if found, None otherwise
    """
    structure = load_team_structure()
    
    for member in structure["members"]:
        if member["id"] == member_id:
            return member
    
    return None

def get_team_members_by_team_id(team_id):
    """Get all team members in a specific team.
    
    Args:
        team_id (str): Team ID
        
    Returns:
        list: List of team member dictionaries
    """
    structure = load_team_structure()
    
    return [member for member in structure["members"] if member.get("team_id") == team_id]

def get_direct_reports(manager_id):
    """Get all direct reports for a manager.
    
    Args:
        manager_id (str): Manager ID
        
    Returns:
        list: List of team member dictionaries
    """
    structure = load_team_structure()
    
    return [member for member in structure["members"] if member.get("manager_id") == manager_id]

def import_organization_from_users():
    """Create team members from registered users.
    
    Returns:
        bool: True if imported successfully, False otherwise
    """
    from utils.user_auth import get_all_users
    
    try:
        # Get all users
        users = get_all_users()
        
        # Load current structure
        structure = load_team_structure()
        
        # Track imported users
        imported_count = 0
        
        # Process each user
        for user in users:
            user_id = user.get("id")
            
            # Skip if already imported
            if any(member.get("user_id") == user_id for member in structure["members"]):
                continue
            
            # Create new member
            member_id = str(uuid.uuid4())
            new_member = {
                "id": member_id,
                "name": user.get("full_name", user.get("username", "Unknown")),
                "title": "",
                "email": user.get("email", ""),
                "team_id": None,
                "manager_id": None,
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Add to structure
            structure["members"].append(new_member)
            imported_count += 1
        
        # Save updated structure
        if save_team_structure(structure):
            return imported_count
        
        return 0
    
    except Exception as e:
        st.error(f"Error importing organization from users: {str(e)}")
        return 0
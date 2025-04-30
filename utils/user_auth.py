# utils/user_auth.py
"""User authentication and management functions."""

import json
import os
import hashlib
import uuid
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
from pathlib import Path

# User roles
ROLES = {
    "admin": "Administrator",
    "manager": "Manager",
    "team_member": "Team Member"
}

def ensure_user_directory():
    """Ensure the user data directory exists."""
    Path("data/users").mkdir(parents=True, exist_ok=True)

def hash_password(password):
    """Simple password hashing using SHA-256.
    
    In a production environment, use a proper password hashing library 
    like bcrypt or Argon2.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, email, full_name, role="team_member"):
    """Create a new user.
    
    Args:
        username (str): Unique username
        password (str): Password
        email (str): Email address
        full_name (str): User's full name
        role (str): User role (admin, manager, team_member)
        
    Returns:
        dict: User data if created successfully, None otherwise
    """
    ensure_user_directory()
    
    # Check if user already exists
    if os.path.exists(f"data/users/{username}.json"):
        return None
    
    # Create user record
    user_data = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": hash_password(password),
        "email": email,
        "full_name": full_name,
        "role": role,
        "created_at": datetime.now().isoformat(),
        "last_login": None
    }
    
    # Save user data
    try:
        with open(f"data/users/{username}.json", 'w') as f:
            json.dump(user_data, f, indent=2)
        return user_data
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return None

def authenticate_user(username, password):
    """Authenticate a user login.
    
    Args:
        username (str): Username
        password (str): Password
        
    Returns:
        dict: User data if authentication successful, None otherwise
    """
    try:
        # Check if user exists
        user_file = f"data/users/{username}.json"
        if not os.path.exists(user_file):
            return None
        
        # Load user data
        with open(user_file, 'r') as f:
            user_data = json.load(f)
        
        # Verify password
        if user_data.get("password_hash") == hash_password(password):
            # Update last login time
            user_data["last_login"] = datetime.now().isoformat()
            with open(user_file, 'w') as f:
                json.dump(user_data, f, indent=2)
            return user_data
        
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

def get_all_users():
    """Get a list of all users.
    
    Returns:
        list: List of user data dictionaries
    """
    ensure_user_directory()
    users = []
    
    try:
        for file_path in Path("data/users").glob("*.json"):
            with open(file_path, 'r') as f:
                user_data = json.load(f)
                # Remove sensitive information
                if "password_hash" in user_data:
                    user_data.pop("password_hash")
                users.append(user_data)
        
        return users
    except Exception as e:
        st.error(f"Error retrieving users: {str(e)}")
        return []

def get_user(username):
    """Get user data by username.
    
    Args:
        username (str): Username
        
    Returns:
        dict: User data if found, None otherwise
    """
    try:
        user_file = f"data/users/{username}.json"
        if not os.path.exists(user_file):
            return None
        
        with open(user_file, 'r') as f:
            user_data = json.load(f)
        
        return user_data
    except Exception as e:
        st.error(f"Error retrieving user: {str(e)}")
        return None

def update_user(username, updates):
    """Update user data.
    
    Args:
        username (str): Username
        updates (dict): Dictionary of fields to update
        
    Returns:
        dict: Updated user data if successful, None otherwise
    """
    try:
        user_file = f"data/users/{username}.json"
        if not os.path.exists(user_file):
            return None
        
        with open(user_file, 'r') as f:
            user_data = json.load(f)
        
        # Apply updates
        for key, value in updates.items():
            # Don't allow changing username or id
            if key not in ["username", "id"]:
                user_data[key] = value
        
        # Handle password change separately
        if "password" in updates:
            user_data["password_hash"] = hash_password(updates["password"])
        
        with open(user_file, 'w') as f:
            json.dump(user_data, f, indent=2)
        
        return user_data
    except Exception as e:
        st.error(f"Error updating user: {str(e)}")
        return None

def delete_user(username):
    """Delete a user.
    
    Args:
        username (str): Username
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        user_file = f"data/users/{username}.json"
        if not os.path.exists(user_file):
            return False
        
        os.remove(user_file)
        return True
    except Exception as e:
        st.error(f"Error deleting user: {str(e)}")
        return False

def init_session_auth():
    """Initialize authentication-related session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "login_error" not in st.session_state:
        st.session_state.login_error = None

def login_user(username, password):
    """Process login attempt and update session state."""
    user_data = authenticate_user(username, password)
    if user_data:
        st.session_state.authenticated = True
        st.session_state.user_info = user_data
        st.session_state.login_error = None
        return True
    else:
        st.session_state.login_error = "Invalid username or password"
        return False

def logout_user():
    """Log out current user."""
    st.session_state.authenticated = False
    st.session_state.user_info = None

def require_auth():
    """Redirect to login page if user is not authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    init_session_auth()
    return st.session_state.authenticated

def require_role(required_role):
    """Check if current user has the required role.
    
    Args:
        required_role (str): Required role
        
    Returns:
        bool: True if user has required role, False otherwise
    """
    if not require_auth():
        return False
    
    user_role = st.session_state.user_info.get("role")
    
    # Admin has access to everything
    if user_role == "admin":
        return True
    
    # Manager has access to manager and team_member roles
    if user_role == "manager" and required_role in ["manager", "team_member"]:
        return True
    
    # Exact role match
    return user_role == required_role

def create_admin_if_needed():
    """Create default admin user if no users exist."""
    ensure_user_directory()
    
    # Check if users directory is empty
    if not list(Path("data/users").glob("*.json")):
        create_user(
            username="admin",
            password="admin123",  # Should be changed immediately
            email="admin@example.com",
            full_name="System Administrator",
            role="admin"
        )
        st.warning("Default admin user created! Username: admin, Password: admin123")
        st.warning("Please change the default password immediately!")
# components/auth.py
"""Authentication components for the Weekly Report app."""

import streamlit as st
from utils.user_auth import (
    login_user, logout_user, create_user, 
    update_user, ROLES, get_user
)

def render_login_page():
    """Render the login page."""
    st.title("📋 Weekly Activity Report")
    st.subheader("Login")
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if login_user(username, password):
                st.rerun()
    
    # Display login error if any
    if st.session_state.get("login_error"):
        st.error(st.session_state.login_error)
    
    # Link to registration
    st.write("---")
    st.write("Don't have an account?")
    
    if st.button("Register New Account"):
        st.session_state.show_register = True
        st.rerun()

def render_register_page():
    """Render the registration page."""
    st.title("📋 Weekly Activity Report")
    st.subheader("Create New Account")
    
    # Registration form
    with st.form("register_form"):
        username = st.text_input("Username", help="Choose a unique username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        
        # Only show role selection for admins
        role = "team_member"
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            if st.session_state.user_info.get("role") == "admin":
                role = st.selectbox("Role", options=list(ROLES.keys()), format_func=lambda x: ROLES[x])
        
        submitted = st.form_submit_button("Register")
        
        if submitted:
            # Validate input
            if not username or not password or not full_name or not email:
                st.error("All fields are required.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Create new user
                user_data = create_user(username, password, email, full_name, role)
                if user_data:
                    st.success("Account created successfully! You can now log in.")
                    # Clear registration flag
                    if "show_register" in st.session_state:
                        del st.session_state.show_register
                    st.rerun()
                else:
                    st.error("Username already exists. Please choose a different one.")
    
    # Back to login
    if st.button("Back to Login"):
        if "show_register" in st.session_state:
            del st.session_state.show_register
        st.rerun()

def render_user_profile():
    """Render the user profile page."""
    st.title("User Profile")
    
    if not st.session_state.get("authenticated") or not st.session_state.get("user_info"):
        st.error("You must be logged in to view this page.")
        return
    
    user_info = st.session_state.user_info
    current_username = user_info.get("username")
    
    # Refresh user data
    fresh_user_data = get_user(current_username)
    if not fresh_user_data:
        st.error("Unable to retrieve user data.")
        return
    
    # Display current info
    st.write(f"**Username:** {fresh_user_data.get('username')}")
    st.write(f"**Full Name:** {fresh_user_data.get('full_name')}")
    st.write(f"**Email:** {fresh_user_data.get('email')}")
    st.write(f"**Role:** {ROLES.get(fresh_user_data.get('role'), 'Unknown')}")
    st.write(f"**Last Login:** {fresh_user_data.get('last_login', 'Never')}")
    
    st.divider()
    
    # Update profile form
    st.subheader("Update Profile")
    with st.form("update_profile_form"):
        new_full_name = st.text_input("Full Name", value=fresh_user_data.get("full_name", ""))
        new_email = st.text_input("Email", value=fresh_user_data.get("email", ""))
        
        st.write("**Change Password (leave blank to keep current password)**")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Update Profile")
        
        if submitted:
            updates = {
                "full_name": new_full_name,
                "email": new_email
            }
            
            # Validate password change
            if new_password:
                if new_password != confirm_new_password:
                    st.error("New passwords do not match.")
                    return
                updates["password"] = new_password
            
            # Update user
            updated_user = update_user(current_username, updates)
            if updated_user:
                # Update session state
                st.session_state.user_info = updated_user
                st.success("Profile updated successfully!")
                st.rerun()
            else:
                st.error("Failed to update profile.")

def render_logout_button():
    """Render a logout button in the sidebar."""
    if st.session_state.get("authenticated"):
        if st.sidebar.button("Logout"):
            logout_user()
            st.rerun()

def render_admin_user_management():
    """Render the admin user management page."""
    if not st.session_state.get("authenticated") or not st.session_state.get("user_info"):
        st.error("You must be logged in to view this page.")
        return
    
    if st.session_state.user_info.get("role") != "admin":
        st.error("You do not have permission to access this page.")
        return
    
    st.title("User Management")
    st.write("Manage user accounts")
    
    # User creation form
    st.subheader("Create New User")
    with st.form("create_user_form"):
        username = st.text_input("Username", key="admin_new_username")
        password = st.text_input("Password", type="password", key="admin_new_password")
        full_name = st.text_input("Full Name", key="admin_new_fullname")
        email = st.text_input("Email", key="admin_new_email")
        role = st.selectbox(
            "Role", 
            options=list(ROLES.keys()), 
            format_func=lambda x: ROLES[x],
            key="admin_new_role"
        )
        
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            # Validate input
            if not username or not password or not full_name or not email:
                st.error("All fields are required.")
            else:
                # Create new user
                user_data = create_user(username, password, email, full_name, role)
                if user_data:
                    st.success(f"User '{username}' created successfully!")
                    st.rerun()
                else:
                    st.error("Username already exists. Please choose a different one.")
    
    # List and manage existing users
    # This would be expanded in a real application to include editing and deleting users
    st.subheader("Existing Users")
    st.write("User management features would be expanded here.")

def check_authentication():
    """Check if user is authenticated and show login page if not.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    # Initialize authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "login_error" not in st.session_state:
        st.session_state.login_error = None
    if "show_register" not in st.session_state:
        st.session_state.show_register = False
        
    # Show registration page if requested
    if st.session_state.get("show_register", False):
        render_register_page()
        return False
        
    # Check if user is authenticated
    if not st.session_state.authenticated:
        render_login_page()
        return False
        
    # User is authenticated, render logout button in sidebar
    render_logout_button()
    return True
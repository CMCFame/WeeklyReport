# components/auth.py
"""Authentication components for the Weekly Report app."""

import streamlit as st
import pandas as pd
# Import the whole module instead of individual functions
from utils import user_auth

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
            if user_auth.login_user(username, password):
                st.rerun()
    
    # Display login error if any
    if st.session_state.get("login_error"):
        st.error(st.session_state.login_error)
    
    # Links to registration and password reset
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Don't have an account?")
        if st.button("Register New Account"):
            st.session_state.show_register = True
            st.rerun()
    
    with col2:
        st.write("Forgot your password?")
        if st.button("Reset Password"):
            st.session_state.show_forgot_password = True
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
                role = st.selectbox("Role", options=list(user_auth.ROLES.keys()), 
                                    format_func=lambda x: user_auth.ROLES[x])
        
        submitted = st.form_submit_button("Register")
        
        if submitted:
            # Validate input
            if not username or not password or not full_name or not email:
                st.error("All fields are required.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Create new user
                user_data = user_auth.create_user(username, password, email, full_name, role)
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
    fresh_user_data = user_auth.get_user(current_username)
    if not fresh_user_data:
        st.error("Unable to retrieve user data.")
        return
    
    # Display current info
    st.write(f"**Username:** {fresh_user_data.get('username')}")
    st.write(f"**Full Name:** {fresh_user_data.get('full_name')}")
    st.write(f"**Email:** {fresh_user_data.get('email')}")
    st.write(f"**Role:** {user_auth.ROLES.get(fresh_user_data.get('role'), 'Unknown')}")
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
            updated_user = user_auth.update_user(current_username, updates)
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
            user_auth.logout_user()
            st.rerun()

def render_forgot_password_page():
    """Render the forgot password page."""
    st.title("📋 Weekly Activity Report")
    st.subheader("Reset Password")
    st.write("Enter your username or email address to receive a password reset code.")
    
    with st.form("forgot_password_form"):
        username_or_email = st.text_input("Username or Email")
        submitted = st.form_submit_button("Request Reset Code")
        
        if submitted:
            if not username_or_email:
                st.error("Please enter your username or email.")
            else:
                # Generate reset code
                success, message, code = user_auth.generate_reset_code(username_or_email)
                
                if success:
                    # In a real app, the code would be emailed
                    # Here we just display it and store it in session state
                    st.success(f"Reset code generated successfully. In a real application, this would be emailed to you.")
                    st.info(f"For demo purposes, here's your code: **{code}**")
                    
                    # Store username for the reset page
                    if '@' in username_or_email:
                        # If email was provided, get the associated username
                        all_users = user_auth.get_all_users(include_sensitive=True)
                        for user in all_users:
                            if user.get("email") == username_or_email:
                                st.session_state.reset_username = user.get("username")
                                break
                    else:
                        st.session_state.reset_username = username_or_email
                    
                    # Show reset password page next
                    st.session_state.show_forgot_password = False
                    st.session_state.show_reset_password = True
                    st.rerun()
                else:
                    st.error(message)
    
    # Back to login
    if st.button("Back to Login"):
        st.session_state.show_forgot_password = False
        st.rerun()

def render_reset_password_page():
    """Render the reset password page."""
    st.title("📋 Weekly Activity Report")
    st.subheader("Enter Reset Code")
    
    if not st.session_state.get("reset_username"):
        st.error("No reset request found. Please start over.")
        if st.button("Back to Forgot Password"):
            st.session_state.show_reset_password = False
            st.session_state.show_forgot_password = True
            st.rerun()
        return
    
    with st.form("reset_password_form"):
        st.write(f"Resetting password for: **{st.session_state.reset_username}**")
        
        reset_code = st.text_input("Reset Code", help="Enter the 6-digit code you received")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Reset Password")
        
        if submitted:
            if not reset_code or not new_password or not confirm_password:
                st.error("All fields are required.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Reset the password
                success = user_auth.reset_password(st.session_state.reset_username, new_password, reset_code)
                
                if success:
                    st.success("Password reset successfully! You can now log in with your new password.")
                    
                    # Clear reset state and return to login
                    st.session_state.reset_username = None
                    st.session_state.show_reset_password = False
                    
                    # Show a button to go back to login
                    if st.button("Go to Login"):
                        st.rerun()
                else:
                    st.error("Invalid or expired reset code. Please try again or request a new code.")
    
    # Back to forgot password
    if st.button("Back to Forgot Password"):
        st.session_state.show_reset_password = False
        st.session_state.show_forgot_password = True
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
            options=list(user_auth.ROLES.keys()), 
            format_func=lambda x: user_auth.ROLES[x],
            key="admin_new_role"
        )
        
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            # Validate input
            if not username or not password or not full_name or not email:
                st.error("All fields are required.")
            else:
                # Create new user
                user_data = user_auth.create_user(username, password, email, full_name, role)
                if user_data:
                    st.success(f"User '{username}' created successfully!")
                    st.rerun()
                else:
                    st.error("Username already exists. Please choose a different one.")
    
    # Initialize session state variables for user management
    if "edit_user" not in st.session_state:
        st.session_state.edit_user = None
    
    if "delete_confirmation_user" not in st.session_state:
        st.session_state.delete_confirmation_user = None
    
    # Get all users
    users = user_auth.get_all_users()
    
    if not users:
        st.info("No users found.")
        return
    
    # List and manage existing users
    st.subheader("Existing Users")
    
    # Display users in a table
    user_data = []
    for user in users:
        user_data.append({
            "Username": user.get("username", ""),
            "Full Name": user.get("full_name", ""),
            "Email": user.get("email", ""),
            "Role": user_auth.ROLES.get(user.get("role", ""), "Unknown"),
            "Last Login": user.get("last_login", "Never")[:19].replace("T", " ") if user.get("last_login") else "Never"
        })
    
    # Create a dataframe for display
    if user_data:
        df = pd.DataFrame(user_data)
        st.dataframe(df, use_container_width=True)
        
        # Add action buttons for each user
        st.subheader("User Actions")
        
        # Check if we're in edit mode
        if st.session_state.edit_user:
            # Get the user to edit
            edit_username = st.session_state.edit_user
            user_to_edit = next((user for user in users if user.get("username") == edit_username), None)
            
            if user_to_edit:
                st.write(f"### Edit User: {user_to_edit.get('full_name', '')}")
                
                # Edit user form
                with st.form("edit_user_form"):
                    edit_full_name = st.text_input("Full Name", value=user_to_edit.get("full_name", ""))
                    edit_email = st.text_input("Email", value=user_to_edit.get("email", ""))
                    edit_role = st.selectbox(
                        "Role",
                        options=list(user_auth.ROLES.keys()),
                        format_func=lambda x: user_auth.ROLES[x],
                        index=list(user_auth.ROLES.keys()).index(user_to_edit.get("role", "team_member"))
                    )
                    
                    # Password fields
                    st.write("Leave password fields blank to keep current password")
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("Update User")
                    with col2:
                        cancel_btn = st.form_submit_button("Cancel")
                    
                    if update_btn:
                        # Validate passwords if provided
                        if new_password or confirm_password:
                            if new_password != confirm_password:
                                st.error("Passwords do not match.")
                                return
                        
                        # Prepare updates
                        updates = {
                            "full_name": edit_full_name,
                            "email": edit_email,
                            "role": edit_role
                        }
                        
                        # Add password if provided
                        if new_password:
                            updates["password"] = new_password
                        
                        # Update user
                        if user_auth.update_user(edit_username, updates):
                            st.success("User updated successfully!")
                            st.session_state.edit_user = None
                            st.rerun()
                        else:
                            st.error("Failed to update user.")
                    
                    if cancel_btn:
                        st.session_state.edit_user = None
                        st.rerun()
            else:
                st.error(f"User '{edit_username}' not found.")
                st.session_state.edit_user = None
                st.rerun()
        else:
            # Show user actions
            for i, user in enumerate(users):
                username = user.get("username", "")
                full_name = user.get("full_name", "")
                role = user_auth.ROLES.get(user.get("role", ""), "Unknown")
                
                st.write(f"**{full_name}** ({username}) - *{role}*")
                
                # Can't delete admin user
                if username != "admin":
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Edit", key=f"edit_{i}"):
                            st.session_state.edit_user = username
                            st.rerun()
                    
                    with col2:
                        # Show delete button or confirmation dialog
                        if st.session_state.delete_confirmation_user == username:
                            st.warning(f"Are you sure you want to delete user '{username}'?")
                            confirm_col1, confirm_col2 = st.columns(2)
                            
                            with confirm_col1:
                                # The key issue was here - the unique key for confirm buttons
                                if st.button("Yes, Delete", key=f"confirm_{i}"):
                                    success = user_auth.delete_user(username)
                                    if success:
                                        st.success(f"User {username} deleted successfully!")
                                        st.session_state.delete_confirmation_user = None
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete user {username}.")
                            
                            with confirm_col2:
                                if st.button("Cancel", key=f"cancel_{i}"):
                                    st.session_state.delete_confirmation_user = None
                                    st.rerun()
                        else:
                            if st.button("Delete", key=f"delete_{i}"):
                                st.session_state.delete_confirmation_user = username
                                st.rerun()
                
                st.divider()

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
    if "show_forgot_password" not in st.session_state:
        st.session_state.show_forgot_password = False
    if "show_reset_password" not in st.session_state:
        st.session_state.show_reset_password = False
    if "reset_username" not in st.session_state:
        st.session_state.reset_username = None
    if "reset_code" not in st.session_state:
        st.session_state.reset_code = None
        
    # Show password reset pages if requested
    if st.session_state.get("show_forgot_password", False):
        render_forgot_password_page()
        return False
        
    if st.session_state.get("show_reset_password", False):
        render_reset_password_page()
        return False
        
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
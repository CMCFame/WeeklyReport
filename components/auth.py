# components/auth.py
"""Authentication components for the Weekly Report app."""

ALLOW_NEW_REGISTRATIONS = True  # Set to False to disable, True to enable

import streamlit as st
import pandas as pd
# Import the whole module instead of individual functions
from utils import user_auth 

def render_login_page():
    """Render the login page."""
    st.title("搭 Weekly Activity Report")
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
    
    # Conditionally show the registration link
    if ALLOW_NEW_REGISTRATIONS:
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
    else:
        # If registration is disabled, only show the "Forgot Password" option
        # This will now be centered as it's the only item in this section
        st.write("Forgot your password?")
        if st.button("Reset Password", use_container_width=True): # Added use_container_width for better centering
            st.session_state.show_forgot_password = True
            st.rerun()

def render_register_page():
    """Render the registration page."""
    st.title("搭 Weekly Activity Report")
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
        
        submitted_create = st.form_submit_button("Register")
        
        if submitted_create: 
            # Validate input
            if not username or not password or not full_name or not email:
                st.error("All fields are required.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Create new user (this will initialize feature_permissions)
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
    st.title("搭 Weekly Activity Report")
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
    st.title("搭 Weekly Activity Report")
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
    st.write("Manage user accounts and their feature permissions.")
    
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
        
        submitted_create = st.form_submit_button("Create User")
        
        if submitted_create: 
            # Validate input
            if not username or not password or not full_name or not email:
                st.error("All fields are required.")
            else:
                # Create new user (this will initialize feature_permissions)
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
    user_data_display = [] 
    for user in users:
        user_data_display.append({
            "Username": user.get("username", ""),
            "Full Name": user.get("full_name", ""),
            "Email": user.get("email", ""),
            "Role": user_auth.ROLES.get(user.get("role", ""), "Unknown"),
            "Last Login": user.get("last_login", "Never")[:19].replace("T", " ") if user.get("last_login") else "Never"
        })
    
    # Create a dataframe for display
    if user_data_display:
        df = pd.DataFrame(user_data_display)
        st.dataframe(df, use_container_width=True)
        
        st.subheader("User Actions & Permissions")
        
        if st.session_state.edit_user:
            edit_username_val = st.session_state.edit_user 
            user_to_edit = user_auth.get_user(edit_username_val) 
            
            if user_to_edit:
                st.write(f"### Edit User: {user_to_edit.get('full_name', '')} ({user_to_edit.get('username')})")
                
                with st.form(f"edit_user_form_{edit_username_val}"): 
                    edit_full_name = st.text_input("Full Name", value=user_to_edit.get("full_name", ""), key=f"edit_fn_{edit_username_val}")
                    edit_email = st.text_input("Email", value=user_to_edit.get("email", ""), key=f"edit_em_{edit_username_val}")
                    
                    current_role_index = list(user_auth.ROLES.keys()).index(user_to_edit.get("role", "team_member"))
                    edit_role = st.selectbox(
                        "Role",
                        options=list(user_auth.ROLES.keys()),
                        format_func=lambda x: user_auth.ROLES[x],
                        index=current_role_index,
                        key=f"edit_role_{edit_username_val}"
                    )
                    
                    st.write("**Change Password (leave blank to keep current password)**")
                    new_password = st.text_input("New Password", type="password", key=f"edit_pw_{edit_username_val}")
                    confirm_password = st.text_input("Confirm New Password", type="password", key=f"edit_cpw_{edit_username_val}")
                    
                    # Feature Permissions - only for non-admin users
                    if user_to_edit.get("role") != "admin":
                        st.subheader("Feature Permissions")
                        st.write(f"Toggle features for {user_to_edit.get('full_name', '')}. (Admins always have all features enabled)")
                        
                        # Get current feature permissions for this user
                        user_feature_permissions = user_to_edit.get("feature_permissions", {})
                        
                        # Create a temporary dictionary to hold the updated selections for the form submission
                        current_feature_permissions_update = {}
                        
                        # Sort features alphabetically by their display label for consistent UI
                        feature_keys_sorted = sorted(user_auth.AVAILABLE_FEATURES.keys(), key=lambda k: user_auth.AVAILABLE_FEATURES[k])

                        num_features = len(feature_keys_sorted)
                        cols = st.columns(2)  # Display in 2 columns for better layout
                        
                        for idx, feature_key in enumerate(feature_keys_sorted):
                            feature_label = user_auth.AVAILABLE_FEATURES[feature_key]
                            # Get the current value for the checkbox (True if not explicitly set)
                            default_value = user_feature_permissions.get(feature_key, True)
                            with cols[idx % 2]: # Distribute checkboxes across columns
                                current_feature_permissions_update[feature_key] = st.checkbox(
                                    feature_label, 
                                    value=default_value, 
                                    key=f"perm_{edit_username_val}_{feature_key}" # Unique key for each checkbox
                                )
                    else:
                        st.info("Admins have all features enabled by default. Feature permissions cannot be changed for admin users.")
                        # For admin users, we still need to pass their existing (all True) permissions
                        # to the update function to ensure the field is preserved.
                        current_feature_permissions_update = user_to_edit.get("feature_permissions", {})


                    submit_update = st.form_submit_button("Update User") 
                    cancel_edit = st.form_submit_button("Cancel") 
                    
                    if submit_update:
                        if new_password and new_password != confirm_password:
                            st.error("New passwords do not match.")
                        else:
                            updates = {
                                "full_name": edit_full_name,
                                "email": edit_email,
                                "role": edit_role,
                            }
                            if new_password:
                                updates["password"] = new_password
                            
                            # Add feature permissions to updates if user is not admin
                            # Or if it's an admin, pass their (all True) permissions to preserve the field
                            updates["feature_permissions"] = current_feature_permissions_update
                            
                            if user_auth.update_user(edit_username_val, updates):
                                st.success("User updated successfully!")
                                st.session_state.edit_user = None
                                st.rerun()
                            else:
                                st.error("Failed to update user.")
                    
                    if cancel_edit:
                        st.session_state.edit_user = None
                        st.rerun()
            else:
                st.error(f"User '{st.session_state.edit_user}' not found for editing.")
                st.session_state.edit_user = None 
                st.rerun()
        else:
            # Display list of users with action buttons
            for i, user_obj in enumerate(users): 
                username_val = user_obj.get("username", "") 
                full_name_val = user_obj.get("full_name", "") 
                role_val = user_auth.ROLES.get(user_obj.get("role", ""), "Unknown") 
                
                st.write(f"**{full_name_val}** ({username_val}) - *{role_val}*")
                
                action_cols = st.columns(2)
                with action_cols[0]:
                    if st.button("Edit", key=f"edit_btn_{i}_{username_val}"): 
                        st.session_state.edit_user = username_val
                        st.rerun()
                
                if username_val != "admin": # Admin user cannot be deleted
                    with action_cols[1]:
                        if st.session_state.delete_confirmation_user == username_val:
                            st.warning(f"Are you sure you want to delete user '{username_val}'?")
                            confirm_del_cols = st.columns(2)
                            with confirm_del_cols[0]:
                                if st.button("Yes, Delete", key=f"confirm_del_btn_{i}_{username_val}"): 
                                    if user_auth.delete_user(username_val):
                                        st.success(f"User {username_val} deleted successfully!")
                                        st.session_state.delete_confirmation_user = None
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete user {username_val}.")
                            with confirm_del_cols[1]:
                                if st.button("Cancel Delete", key=f"cancel_del_btn_{i}_{username_val}"): 
                                    st.session_state.delete_confirmation_user = None
                                    st.rerun()
                        else:
                            if st.button("Delete", key=f"delete_btn_{i}_{username_val}", type="secondary"): 
                                st.session_state.delete_confirmation_user = username_val
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
# components/user_import.py
"""User import component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import io
from utils import user_auth

def render_user_import():
    """Render the user import interface for admins."""
    st.title("Import Users")
    st.write("Upload a CSV file to bulk create user accounts.")
    
    # Template download
    st.subheader("Download Template")
    st.write("Use this template for importing users:")
    
    # Create template dataframe
    template_df = pd.DataFrame({
        'username': ['user1', 'user2', 'user3'],
        'password': ['password1', 'password2', 'password3'],
        'email': ['user1@example.com', 'user2@example.com', 'user3@example.com'],
        'full_name': ['User One', 'User Two', 'User Three'],
        'role': ['team_member', 'team_member', 'manager']
    })
    
    # Create a download link
    csv = template_df.to_csv(index=False)
    st.download_button(
        label="📥 Download User Import Template",
        data=csv,
        file_name="user_import_template.csv",
        mime="text/csv"
    )
    
    # File upload
    st.subheader("Upload User CSV")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="user_upload")
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Validate columns
            required_columns = ['username', 'password', 'email', 'full_name', 'role']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Error: Your CSV is missing these required columns: {', '.join(missing_columns)}")
                return
            
            # Show preview with option to proceed
            st.subheader("Preview Import Data")
            st.dataframe(df)
            
            # Count of users to be imported
            st.info(f"Ready to import {len(df)} users")
            
            # Import button
            if st.button("Import Users"):
                results = import_users(df)
                
                # Show results
                st.subheader("Import Results")
                success_count = sum(1 for r in results if r['status'] == 'success')
                st.success(f"Successfully imported {success_count} out of {len(df)} users")
                
                # Show details in expander
                with st.expander("View Detailed Results"):
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df)
        
        except Exception as e:
            st.error(f"Error processing CSV file: {str(e)}")

def import_users(df):
    """Import users from a dataframe.
    
    Args:
        df (pandas.DataFrame): Dataframe containing user data
        
    Returns:
        list: List of dictionaries with import results
    """
    results = []
    
    # Process each row
    for i, row in df.iterrows():
        try:
            # Extract user data
            username = str(row['username']).strip()
            password = str(row['password']).strip()
            email = str(row['email']).strip()
            full_name = str(row['full_name']).strip()
            role = str(row['role']).strip().lower()
            
            # Validate role
            if role not in user_auth.ROLES:
                results.append({
                    'username': username,
                    'status': 'error',
                    'message': f"Invalid role '{role}'. Must be one of: {', '.join(user_auth.ROLES.keys())}"
                })
                continue
            
            # Check if user already exists
            existing_user = user_auth.get_user(username)
            if existing_user:
                results.append({
                    'username': username,
                    'status': 'error',
                    'message': 'User already exists'
                })
                continue
            
            # Create user
            user_data = user_auth.create_user(
                username=username,
                password=password,
                email=email,
                full_name=full_name,
                role=role
            )
            
            if user_data:
                results.append({
                    'username': username,
                    'status': 'success',
                    'message': 'User created successfully'
                })
            else:
                results.append({
                    'username': username,
                    'status': 'error',
                    'message': 'Failed to create user'
                })
        
        except Exception as e:
            results.append({
                'username': row.get('username', f'Row {i+1}'),
                'status': 'error',
                'message': str(e)
            })
    
    return results
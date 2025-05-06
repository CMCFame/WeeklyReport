# utils/csv_utils.py
"""Utility functions for processing project and milestone CSV data."""

import pandas as pd
import streamlit as st
from pathlib import Path
import os

def load_project_data():
    """Load project and milestone data from CSV file.
    
    Returns:
        pandas.DataFrame: DataFrame containing project, milestone, and owner data
    """
    try:
        # Path to the CSV file (relative to the app directory)
        csv_path = Path("data/project_data.csv")
        
        # Check if file exists
        if not csv_path.exists():
            st.warning("Project data file not found. Please ensure 'data/project_data.csv' exists.")
            return pd.DataFrame(columns=["Project", "Milestone: Milestone Name", "Timecard: Owner Name"])
        
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Ensure required columns exist
        required_columns = ["Project", "Milestone: Milestone Name", "Timecard: Owner Name"]
        for column in required_columns:
            if column not in df.columns:
                st.warning(f"Required column '{column}' not found in project data file.")
                return pd.DataFrame(columns=required_columns)
        
        return df
    except Exception as e:
        st.error(f"Error loading project data: {str(e)}")
        return pd.DataFrame(columns=["Project", "Milestone: Milestone Name", "Timecard: Owner Name"])

def get_user_projects(username):
    """Get projects associated with a specific user.
    
    Args:
        username (str): Username to filter projects by
        
    Returns:
        list: List of unique project names for the user
    """
    df = load_project_data()
    
    # If dataframe is empty or user not found, return empty list
    if df.empty:
        return []
    
    # Get the user's full name if available
    user_full_name = None
    if st.session_state.get("user_info"):
        user_full_name = st.session_state.user_info.get("full_name")
    
    # Filter projects by owner name (using either username or full name)
    filtered_df = df[
        (df["Timecard: Owner Name"].str.lower() == username.lower()) |
        (user_full_name and df["Timecard: Owner Name"].str.lower() == user_full_name.lower())
    ]
    
    # Get unique project names
    projects = filtered_df["Project"].unique().tolist()
    
    # If manager or admin, return all projects
    if st.session_state.get("user_info"):
        user_role = st.session_state.user_info.get("role")
        if user_role in ["admin", "manager"]:
            projects = df["Project"].unique().tolist()
    
    return sorted(projects)

def get_project_milestones(project_name):
    """Get milestones associated with a specific project.
    
    Args:
        project_name (str): Project name to filter milestones by
        
    Returns:
        list: List of unique milestone names for the project
    """
    df = load_project_data()
    
    # If dataframe is empty or project not found, return empty list
    if df.empty or project_name not in df["Project"].values:
        return []
    
    # Filter milestones by project
    filtered_df = df[df["Project"] == project_name]
    
    # Get unique milestone names
    milestones = filtered_df["Milestone: Milestone Name"].unique().tolist()
    
    return sorted(milestones)

def ensure_project_data_file():
    """Ensure the project data directory and file exist.
    Creates the file with headers if it doesn't exist.
    """
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Path to the CSV file
    csv_path = Path("data/project_data.csv")
    
    # Create file with headers if it doesn't exist
    if not csv_path.exists():
        headers = "Project,Milestone: Milestone Name,Timecard: Owner Name\n"
        with open(csv_path, 'w') as f:
            f.write(headers)
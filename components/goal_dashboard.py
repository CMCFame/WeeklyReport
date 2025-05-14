# components/goal_dashboard.py
"""Goal Dashboard component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

def render_goal_dashboard():
    """Render the goal dashboard view."""
    st.title("Goal Dashboard")
    st.write("Track and visualize progress on objectives across the organization.")
    
    # Period selector and filters
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        # Generate period options
        now = datetime.now()
        year = now.year
        periods = []
        
        # Add quarters for current and next year
        for y in range(year - 1, year + 2):
            for q in range(1, 5):
                periods.append(f"Q{q} {y}")
        
        # Default to current quarter
        current_quarter = (now.month - 1) // 3 + 1
        default_period = f"Q{current_quarter} {year}"
        default_index = periods.index(default_period) if default_period in periods else 0
        
        # Period selector
        selected_period = st.selectbox(
            "Time Period",
            options=periods,
            index=default_index
        )
    
    with col2:
        # Get all teams
        teams = get_teams()
        selected_team = st.selectbox(
            "Team Filter",
            options=["All Teams"] + teams
        )
    
    with col3:
        # Status filter
        status_options = ["All Statuses", "On Track", "At Risk", "Behind", "Completed"]
        selected_status = st.selectbox(
            "Status Filter",
            options=status_options
        )
    
    # Get objectives based on filters
    objectives = get_filtered_objectives(selected_period, selected_team, selected_status)
    
    if not objectives:
        st.info(f"No objectives found for the selected filters.")
        return
    
    # Dashboard sections using tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Summary", "Objectives by Team", "Progress by Person", "Completion Trends"
    ])
    
    with tab1:
        render_summary_view(objectives)
    
    with tab2:
        render_team_view(objectives)
    
    with tab3:
        render_person_view(objectives)
    
    with tab4:
        render_trends_view(objectives)

def render_summary_view(objectives):
    """Render summary metrics and charts.
    
    Args:
        objectives (list): List of filtered objectives
    """
    st.subheader("Summary Overview")
    
    # Calculate summary metrics
    total_objectives = len(objectives)
    total_key_results = sum(len(obj.get('key_results', [])) for obj in objectives)
    
    # Calculate overall progress and status counts
    all_key_results = []
    for obj in objectives:
        all_key_results.extend(obj.get('key_results', []))
    
    if all_key_results:
        overall_progress = sum(kr.get('progress', 0) for kr in all_key_results) / len(all_key_results)
    else:
        overall_progress = 0
    
    # Status counts
    status_counts = {
        "On Track": len([obj for obj in objectives if obj.get('status') == "On Track"]),
        "At Risk": len([obj for obj in objectives if obj.get('status') == "At Risk"]),
        "Behind": len([obj for obj in objectives if obj.get('status') == "Behind"]),
        "Completed": len([obj for obj in objectives if obj.get('status') == "Completed"])
    }
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Use a progress box with percentage for overall progress
        st.markdown(f"""
        <div style="border-radius: 10px; border: 1px solid #ddd; padding: 15px; text-align: center;">
            <h1 style="font-size: 36px; margin: 0; color: {'green' if overall_progress >= 70 else 'orange' if overall_progress >= 40 else 'red'};">
                {overall_progress:.0f}%
            </h1>
            <p style="margin: 5px 0 0 0;">Overall Progress</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="border-radius: 10px; border: 1px solid #ddd; padding: 15px; text-align: center;">
            <h1 style="font-size: 36px; margin: 0; color: #3366cc;">
                {total_objectives}
            </h1>
            <p style="margin: 5px 0 0 0;">Total Objectives</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="border-radius: 10px; border: 1px solid #ddd; padding: 15px; text-align: center;">
            <h1 style="font-size: 36px; margin: 0; color: #3366cc;">
                {total_key_results}
            </h1>
            <p style="margin: 5px 0 0 0;">Key Results</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="border-radius: 10px; border: 1px solid #ddd; padding: 15px; text-align: center;">
            <h1 style="font-size: 36px; margin: 0; color: {'green' if status_counts['Completed'] > 0 else '#666'};">
                {status_counts["Completed"]}
            </h1>
            <p style="margin: 5px 0 0 0;">Completed</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Status distribution chart
    st.subheader("Status Distribution")
    
    # Create status data
    status_data = {
        "Status": list(status_counts.keys()),
        "Count": list(status_counts.values())
    }
    
    status_df = pd.DataFrame(status_data)
    
    # Create a more visually appealing chart with Plotly
    status_colors = {
        "On Track": "#28a745",     # Green
        "At Risk": "#ffc107",      # Yellow
        "Behind": "#dc3545",       # Red
        "Completed": "#17a2b8"     # Blue
    }
    
    colors = [status_colors[status] for status in status_counts.keys()]
    
    fig = px.bar(
        status_df, 
        x="Status", 
        y="Count",
        color="Status",
        color_discrete_map={status: status_colors[status] for status in status_counts.keys()},
        text="Count",
        title="Objectives by Status"
    )
    
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Number of Objectives",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("Recent Updates")
    render_recent_updates(objectives, limit=5)

def render_team_view(objectives):
    """Render team-based objective view.
    
    Args:
        objectives (list): List of filtered objectives
    """
    st.subheader("Objectives by Team")
    
    # Categorize objectives by team
    team_objectives = {}
    for obj in objectives:
        if obj.get('level') == 'team':
            team = obj.get('team', 'Uncategorized')
        elif obj.get('level') == 'individual':
            # For individual objectives, try to determine team from other data
            # This is a simplification - in a real system, you'd have proper user-team mapping
            team = "Uncategorized"
        else:
            # Company objectives
            team = "Company-Wide"
        
        if team not in team_objectives:
            team_objectives[team] = []
        team_objectives[team].append(obj)
    
    # Create data for team progress chart
    team_data = []
    for team, objs in team_objectives.items():
        # Calculate team progress
        all_krs = []
        for obj in objs:
            all_krs.extend(obj.get('key_results', []))
        
        if all_krs:
            progress = sum(kr.get('progress', 0) for kr in all_krs) / len(all_krs)
        else:
            progress = 0
        
        team_data.append({
            "Team": team,
            "Progress": progress,
            "Objectives": len(objs)
        })
    
    # Sort by progress
    team_data.sort(key=lambda x: x["Progress"], reverse=True)
    
    # Create DataFrame
    if team_data:
        team_df = pd.DataFrame(team_data)
        
        # Create horizontal bar chart
        fig = px.bar(
            team_df, 
            y="Team", 
            x="Progress",
            orientation='h',
            text=team_df["Progress"].apply(lambda x: f"{x:.0f}%"),
            color="Progress",
            color_continuous_scale=["red", "orange", "green"],
            range_color=[0, 100],
            title="Team Progress",
            hover_data=["Objectives"]
        )
        
        fig.update_layout(
            yaxis=dict(autorange="reversed"),  # Highest value at the top
            xaxis_title="Progress (%)",
            yaxis_title="",
            coloraxis_showscale=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No team data available for visualization.")
    
    # Display objectives by team
    for team, objs in team_objectives.items():
        with st.expander(f"{team} ({len(objs)} objectives)"):
            render_objective_table(objs)

def render_person_view(objectives):
    """Render person-based objective view.
    
    Args:
        objectives (list): List of filtered objectives
    """
    st.subheader("Progress by Person")
    
    # Categorize objectives by owner
    person_objectives = {}
    for obj in objectives:
        owner = obj.get('owner_name', 'Unassigned')
        
        if owner not in person_objectives:
            person_objectives[owner] = []
        person_objectives[owner].append(obj)
    
    # Create data for person progress chart
    person_data = []
    for person, objs in person_objectives.items():
        # Calculate person progress
        all_krs = []
        for obj in objs:
            all_krs.extend(obj.get('key_results', []))
        
        if all_krs:
            progress = sum(kr.get('progress', 0) for kr in all_krs) / len(all_krs)
        else:
            progress = 0
        
        # Count objectives by status
        on_track = len([obj for obj in objs if obj.get('status') == "On Track"])
        at_risk = len([obj for obj in objs if obj.get('status') == "At Risk"])
        behind = len([obj for obj in objs if obj.get('status') == "Behind"])
        completed = len([obj for obj in objs if obj.get('status') == "Completed"])
        
        person_data.append({
            "Person": person,
            "Progress": progress,
            "Objectives": len(objs),
            "On Track": on_track,
            "At Risk": at_risk,
            "Behind": behind,
            "Completed": completed
        })
    
    # Sort by progress
    person_data.sort(key=lambda x: x["Progress"], reverse=True)
    
    # Create DataFrame
    if person_data:
        person_df = pd.DataFrame(person_data)
        
        # Create horizontal bar chart
        fig = px.bar(
            person_df, 
            y="Person", 
            x="Progress",
            orientation='h',
            text=person_df["Progress"].apply(lambda x: f"{x:.0f}%"),
            color="Progress",
            color_continuous_scale=["red", "orange", "green"],
            range_color=[0, 100],
            title="Individual Progress",
            hover_data=["Objectives", "On Track", "At Risk", "Behind", "Completed"]
        )
        
        fig.update_layout(
            yaxis=dict(autorange="reversed"),  # Highest value at the top
            xaxis_title="Progress (%)",
            yaxis_title="",
            coloraxis_showscale=False,
            height=max(400, 100 + 50 * len(person_df))  # Dynamic height based on number of people
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No individual data available for visualization.")
    
    # Display objectives by person
    for person, objs in person_objectives.items():
        with st.expander(f"{person} ({len(objs)} objectives)"):
            render_objective_table(objs)

def render_trends_view(objectives):
    """Render trends and completion analysis.
    
    Args:
        objectives (list): List of filtered objectives
    """
    st.subheader("Completion Trends")
    
    # Get update history
    updates_by_date = get_updates_history(objectives)
    
    if not updates_by_date:
        st.info("No historical data available for trend analysis.")
        return
    
    # Create progress over time chart
    progress_data = []
    dates = sorted(updates_by_date.keys())
    
    for date in dates:
        updates = updates_by_date[date]
        daily_progress = sum(update.get('current', 0) for update in updates) / len(updates)
        progress_data.append({
            "Date": date,
            "Progress": daily_progress,
            "Updates": len(updates)
        })
    
    # Create DataFrame
    progress_df = pd.DataFrame(progress_data)
    
    # Create line chart
    fig = px.line(
        progress_df, 
        x="Date", 
        y="Progress",
        markers=True,
        line_shape="spline",
        title="Average Progress Over Time",
        hover_data=["Updates"]
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Average Progress (%)",
        hovermode="x unified",
        height=400
    )
    
    # Add goal line at 100%
    fig.add_shape(
        type="line",
        x0=min(dates),
        y0=100,
        x1=max(dates),
        y1=100,
        line=dict(color="green", width=1, dash="dash"),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add completion projection
    st.subheader("Completion Projection")
    render_completion_projection(objectives, progress_data)

def render_completion_projection(objectives, progress_data):
    """Render completion projection analysis.
    
    Args:
        objectives (list): List of filtered objectives
        progress_data (list): Progress over time data
    """
    if not progress_data or len(progress_data) < 2:
        st.info("Insufficient data for completion projection.")
        return
    
    # Calculate current overall progress
    all_key_results = []
    for obj in objectives:
        all_key_results.extend(obj.get('key_results', []))
    
    if all_key_results:
        current_progress = sum(kr.get('progress', 0) for kr in all_key_results) / len(all_key_results)
    else:
        current_progress = 0
    
    # Calculate average daily progress increase
    first_date = datetime.strptime(progress_data[0]["Date"], "%Y-%m-%d")
    last_date = datetime.strptime(progress_data[-1]["Date"], "%Y-%m-%d")
    first_progress = progress_data[0]["Progress"]
    last_progress = progress_data[-1]["Progress"]
    
    date_diff = (last_date - first_date).days
    if date_diff > 0:
        daily_progress_rate = (last_progress - first_progress) / date_diff
    else:
        daily_progress_rate = 0
    
    # Project completion date (if rate > 0)
    if daily_progress_rate > 0:
        days_to_completion = (100 - current_progress) / daily_progress_rate
        projected_completion_date = datetime.now() + timedelta(days=days_to_completion)
        
        # Format dates for display
        formatted_projection = projected_completion_date.strftime("%B %d, %Y")
        
        # Calculate whether completion is on time
        # For this example, let's assume "on time" means within the current quarter
        now = datetime.now()
        quarter_end_month = ((now.month - 1) // 3 + 1) * 3
        quarter_end_date = datetime(now.year, quarter_end_month, 1) + timedelta(days=32)
        quarter_end_date = datetime(quarter_end_date.year, quarter_end_date.month, 1) - timedelta(days=1)
        
        on_time = projected_completion_date <= quarter_end_date
        
        # Display projection
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Progress bar with markers
            progress_color = "green" if on_time else "orange"
            st.progress(current_progress / 100)
            
            # Create a custom milestone display
            st.markdown(f"""
            <div style="margin-top: 5px; display: flex; justify-content: space-between; font-size: 14px;">
                <div>0%</div>
                <div>25%</div>
                <div>50%</div>
                <div>75%</div>
                <div>100%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            status_color = "green" if on_time else "orange"
            status_icon = "✅" if on_time else "⚠️"
            status_text = "On Track" if on_time else "At Risk"
            
            st.markdown(f"""
            <div style="border: 1px solid {status_color}; border-radius: 5px; padding: 10px; text-align: center;">
                <div style="font-size: 24px;">{status_icon}</div>
                <div style="color: {status_color}; font-weight: bold;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write(f"**Projected Completion:** {formatted_projection}")
        st.write(f"**Current Progress Rate:** {daily_progress_rate:.2f}% per day")
        
        # Risk indicators
        if daily_progress_rate <= 0:
            st.warning("⚠️ **Risk Alert:** Progress has stalled. Intervention required to meet goals.")
        elif not on_time:
            st.warning("⚠️ **Risk Alert:** Current progress rate may not meet deadline. Consider adjusting scope or resources.")
    else:
        st.warning("Cannot project completion date with current data. Need more progress updates.")

def render_objective_table(objectives):
    """Render a table of objectives.
    
    Args:
        objectives (list): List of objectives to display
    """
    # Create a dataframe for display
    data = []
    for obj in objectives:
        # Calculate progress
        key_results = obj.get('key_results', [])
        if key_results:
            progress = sum(kr.get('progress', 0) for kr in key_results) / len(key_results)
        else:
            progress = 0
        
        # Add to data
        data.append({
            "Title": obj.get('title', 'Untitled'),
            "Progress": f"{progress:.0f}%",
            "Status": obj.get('status', 'Unknown'),
            "Owner": obj.get('owner_name', 'Unassigned'),
            "Last Updated": obj.get('last_updated', '')[:10],
            "ID": obj.get('id')  # For reference
        })
    
    # Convert to dataframe
    df = pd.DataFrame(data)
    
    # Sort by progress (ascending)
    df = df.sort_values(by="Progress", key=lambda x: x.str.rstrip('%').astype(float))
    
    # Display as an interactive table
    # Customize display with colors based on status
    def highlight_status(val):
        if val == "On Track":
            return 'background-color: rgba(40, 167, 69, 0.2)'
        elif val == "At Risk":
            return 'background-color: rgba(255, 193, 7, 0.2)'
        elif val == "Behind":
            return 'background-color: rgba(220, 53, 69, 0.2)'
        elif val == "Completed":
            return 'background-color: rgba(23, 162, 184, 0.2)'
        return ''
    
    # Apply styling
    styled_df = df.style.applymap(highlight_status, subset=['Status'])
    
    # Drop ID column for display
    display_df = df.drop(columns=['ID'])
    st.dataframe(display_df, use_container_width=True)
    
    # Add option to view detailed objective
    st.write("Click on an objective to view details:")
    
    # Dropdown to select objective
    selected_obj_title = st.selectbox(
        "Select Objective",
        options=df["Title"].tolist(),
        key=f"select_obj_{hash(tuple(df['ID']))}"
    )
    
    # Find the selected objective
    selected_obj_id = df[df["Title"] == selected_obj_title]["ID"].iloc[0]
    selected_obj = next((obj for obj in objectives if obj.get('id') == selected_obj_id), None)
    
    if selected_obj:
        with st.expander("Objective Details", expanded=True):
            render_objective_details(selected_obj)

def render_objective_details(objective):
    """Render detailed view of a single objective.
    
    Args:
        objective (dict): Objective data
    """
    # Title and description
    st.markdown(f"### {objective.get('title', 'Untitled Objective')}")
    st.write(objective.get('description', 'No description provided.'))
    
    # Metadata
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**Level:** {objective.get('level', 'unknown').capitalize()}")
        if objective.get('level') == 'team':
            st.write(f"**Team:** {objective.get('team', 'Unassigned')}")
    
    with col2:
        st.write(f"**Owner:** {objective.get('owner_name', 'Unassigned')}")
        st.write(f"**Status:** {objective.get('status', 'Unknown')}")
    
    with col3:
        st.write(f"**Period:** {objective.get('period', 'Unknown')}")
        st.write(f"**Last Updated:** {objective.get('last_updated', '')[:10]}")
    
    # Key Results
    st.subheader("Key Results")
    
    key_results = objective.get('key_results', [])
    for i, kr in enumerate(key_results):
        progress = kr.get('progress', 0)
        
        st.write(f"**KR{i+1}:** {kr.get('description', 'No description')}")
        
        # Progress bar with percentage
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.progress(progress / 100)
        
        with col2:
            st.write(f"{progress:.0f}%")
        
        # Show updates if available
        if 'updates' in kr and kr['updates']:
            with st.expander("View Updates"):
                for update in kr['updates']:
                    st.write(f"**{update.get('date', '')}:** {update.get('previous', 0):.0f}% → {update.get('current', 0):.0f}%")
                    if update.get('note'):
                        st.write(f"*\"{update.get('note')}\"*")
                    st.divider()

def render_recent_updates(objectives, limit=5):
    """Render a list of recent updates across all objectives.
    
    Args:
        objectives (list): List of objectives
        limit (int): Maximum number of updates to show
    """
    # Collect all updates
    all_updates = []
    
    for obj in objectives:
        for kr in obj.get('key_results', []):
            for update in kr.get('updates', []):
                all_updates.append({
                    "date": update.get('date', ''),
                    "objective": obj.get('title', 'Untitled'),
                    "key_result": kr.get('description', 'Untitled'),
                    "progress": f"{update.get('previous', 0):.0f}% → {update.get('current', 0):.0f}%",
                    "note": update.get('note', ''),
                    "owner": obj.get('owner_name', 'Unknown')
                })
    
    # Sort by date (most recent first)
    all_updates.sort(key=lambda x: x['date'], reverse=True)
    
    # Limit to specified number
    recent_updates = all_updates[:limit]
    
    if recent_updates:
        # Format as cards for better presentation
        for update in recent_updates:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div><strong>{update['date']}</strong></div>
                        <div>{update['owner']}</div>
                    </div>
                    <div style="margin: 5px 0;"><strong>{update['objective']}</strong> - {update['key_result']}</div>
                    <div style="display: flex; justify-content: space-between;">
                        <div style="color: #666;">{update['progress']}</div>
                        <div style="font-style: italic;">{update['note']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No recent updates available.")

def get_filtered_objectives(period, team, status):
    """Get objectives filtered by period, team, and status.
    
    Args:
        period (str): Selected period
        team (str): Selected team (or "All Teams")
        status (str): Selected status (or "All Statuses")
    
    Returns:
        list: Filtered list of objectives
    """
    try:
        # Get all objectives for the period
        objectives = get_objectives(period)
        
        # Apply team filter
        if team != "All Teams":
            objectives = [
                obj for obj in objectives 
                if (obj.get('level') == 'team' and obj.get('team') == team) or 
                   (obj.get('level') != 'team')  # Keep non-team objectives
            ]
        
        # Apply status filter
        if status != "All Statuses":
            objectives = [obj for obj in objectives if obj.get('status') == status]
        
        return objectives
        
    except Exception as e:
        st.error(f"Error retrieving filtered objectives: {str(e)}")
        return []

def get_updates_history(objectives):
    """Get updates history organized by date.
    
    Args:
        objectives (list): List of objectives
    
    Returns:
        dict: Dictionary of updates by date
    """
    updates_by_date = {}
    
    for obj in objectives:
        for kr in obj.get('key_results', []):
            for update in kr.get('updates', []):
                date = update.get('date', '')
                if date:
                    if date not in updates_by_date:
                        updates_by_date[date] = []
                    updates_by_date[date].append(update)
    
    return updates_by_date

def get_objectives(period):
    """Get objectives for a specific period.
    
    Args:
        period (str): Period (e.g., Q1 2023)
        
    Returns:
        list: List of objective dictionaries
    """
    try:
        # Ensure the objectives directory exists
        Path("data/objectives").mkdir(parents=True, exist_ok=True)
        
        # Get all objective files
        objectives = []
        objective_files = list(Path("data/objectives").glob("*.json"))
        
        for file_path in objective_files:
            try:
                with open(file_path, 'r') as f:
                    objective = json.load(f)
                
                # Check if it matches the period
                if objective.get('period') == period:
                    objectives.append(objective)
                    
            except Exception as e:
                st.warning(f"Error loading objective {file_path}: {str(e)}")
        
        return objectives
        
    except Exception as e:
        st.error(f"Error retrieving objectives: {str(e)}")
        return []

def get_teams():
    """Get list of teams.
    
    Returns:
        list: List of team names
    """
    try:
        # This is a placeholder for a more sophisticated implementation
        # that would retrieve teams from a database or other source
        
        # Get objectives and extract team names
        objectives = []
        objective_files = list(Path("data/objectives").glob("*.json"))
        
        for file_path in objective_files:
            try:
                with open(file_path, 'r') as f:
                    objective = json.load(f)
                    objectives.append(objective)
            except:
                pass
        
        # Extract unique team names
        teams = set()
        for obj in objectives:
            if obj.get('level') == 'team' and obj.get('team'):
                teams.add(obj.get('team'))
        
        # If no teams found, return defaults
        if not teams:
            return ["Management", "Engineering", "Marketing", "Sales", "Product", "Customer Success"]
        
        return sorted(list(teams))
        
    except Exception as e:
        st.error(f"Error retrieving teams: {str(e)}")
        return ["General"]
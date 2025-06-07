# components/weekly_report_analytics.py
"""Weekly Report Analytics component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

def render_weekly_report_analytics():
    """Render the weekly report analytics dashboard."""
    st.title("Weekly Report Analytics")
    st.write("Analyze trends and insights across all submitted weekly reports.")
    
    # Get all reports
    reports = get_all_reports()
    if not reports:
        st.info("No reports found. Analytics will be available once reports are submitted.")
        return
    
    # Date range selection
    st.subheader("Select Date Range")
    col1, col2 = st.columns(2)
    
    with col1:
        # Get min and max dates from reports
        all_dates = [datetime.fromisoformat(r.get('timestamp', datetime.now().isoformat())[:10]) 
                     for r in reports if 'timestamp' in r]
        if all_dates:
            min_date = min(all_dates).date()
            max_date = max(all_dates).date()
        else:
            min_date = (datetime.now() - timedelta(days=30)).date()
            max_date = datetime.now().date()
        
        start_date = st.date_input(
            "Start Date", 
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Filter reports by date range
    filtered_reports = [
        r for r in reports 
        if 'timestamp' in r and 
        start_date <= datetime.fromisoformat(r['timestamp'][:10]).date() <= end_date
    ]
    
    if not filtered_reports:
        st.warning(f"No reports found in the selected date range ({start_date} to {end_date}).")
        return
    
    # Display summary metrics
    st.subheader("Summary Metrics")
    render_summary_metrics(filtered_reports)
    
    # Different views using tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Team Activity", "Project Status", "Accomplishments", "Concerns & Challenges"
    ])
    
    with tab1:
        render_team_activity_view(filtered_reports)
    
    with tab2:
        render_project_status_view(filtered_reports)
    
    with tab3:
        render_accomplishments_view(filtered_reports)
    
    with tab4:
        render_concerns_view(filtered_reports)

# En components/weekly_report_analytics.py

def render_summary_metrics(reports):
    """Render summary metrics for the filtered reports.
    
    Args:
        reports (list): List of filtered report dictionaries
    """
    # Calculate metrics
    total_reports = len(reports)
    total_team_members = len(set([r.get('name', 'Unknown') for r in reports]))
    
    # Count activities
    all_current_activities = []
    for report in reports:
        all_current_activities.extend(report.get('current_activities', []))
    
    total_activities = len(all_current_activities)
    
    # Count activities by status
    status_counts = {}
    for activity in all_current_activities:
        status = activity.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # --- INICIO DE LA CORRECCIÓN ---
    # Calculate average completion percentage across activities safely
    if all_current_activities:
        progress_values = []
        for activity in all_current_activities:
            try:
                # Safely convert progress to a number, handling strings like "50" or "50.0"
                progress_values.append(int(float(activity.get('progress', 0))))
            except (ValueError, TypeError):
                # If conversion fails, default to 0
                progress_values.append(0)
        
        avg_completion = sum(progress_values) / len(all_current_activities)
    else:
        avg_completion = 0
    # --- FIN DE LA CORRECCIÓN ---

    # Calculate unique projects
    unique_projects = set()
    for activity in all_current_activities:
        project = activity.get('project', '')
        if project:
            unique_projects.add(project)
    
    # Display metrics in a grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Reports", total_reports)
        st.metric("Team Members", total_team_members)
    
    with col2:
        st.metric("Total Activities", total_activities)
        st.metric("Average Progress", f"{avg_completion:.1f}%")
    
    with col3:
        st.metric("Unique Projects", len(unique_projects))
        
        # Most common status
        if status_counts:
            most_common_status = max(status_counts, key=status_counts.get)
            st.metric("Most Common Status", most_common_status)
    
    with col4:
        # Activities at risk
        at_risk = sum(1 for a in all_current_activities if a.get('priority') == 'High' and a.get('status') not in ['Completed'])
        st.metric("High Priority Activities", at_risk)
        
        # Show a completion indicator
        # FIX: Check if total_activities is zero before division
        completion_delta = f"{status_counts.get('Completed', 0)/total_activities*100:.1f}%" if total_activities > 0 else "0%"
        st.metric("Completed Activities", status_counts.get('Completed', 0), 
                  delta=completion_delta)

def render_team_activity_view(reports):
    """Render team activity analysis view.
    
    Args:
        reports (list): List of filtered report dictionaries
    """
    st.subheader("Team Member Activity")
    
    # Organize reports by team member
    team_member_reports = {}
    for report in reports:
        name = report.get('name', 'Unknown')
        if name not in team_member_reports:
            team_member_reports[name] = []
        team_member_reports[name].append(report)
    
    # Create activity data
    activity_data = []
    for name, member_reports in team_member_reports.items():
        # Count activities
        current_activities = []
        for report in member_reports:
            current_activities.extend(report.get('current_activities', []))
        
        upcoming_activities = []
        for report in member_reports:
            upcoming_activities.extend(report.get('upcoming_activities', []))
        
        # Count statuses
        status_counts = {}
        for activity in current_activities:
            status = activity.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count priorities
        priority_counts = {}
        for activity in current_activities:
            priority = activity.get('priority', 'Unknown')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # --- INICIO DE LA CORRECCIÓN ---
        # Calculate average progress safely
        if current_activities:
            progress_values = []
            for activity in current_activities:
                try:
                    # Safely convert progress to a number
                    progress_values.append(int(float(activity.get('progress', 0))))
                except (ValueError, TypeError):
                    progress_values.append(0) # Default to 0 if conversion fails
            avg_progress = sum(progress_values) / len(current_activities)
        else:
            avg_progress = 0
        # --- FIN DE LA CORRECCIÓN ---
        
        # Get unique projects
        projects = set()
        for activity in current_activities:
            project = activity.get('project', '')
            if project:
                projects.add(project)
        
        # Add to data
        activity_data.append({
            "Team Member": name,
            "Current Activities": len(current_activities),
            "Upcoming Activities": len(upcoming_activities),
            "Completed": status_counts.get('Completed', 0),
            "In Progress": status_counts.get('In Progress', 0),
            "Blocked": status_counts.get('Blocked', 0),
            "Not Started": status_counts.get('Not Started', 0),
            "High Priority": priority_counts.get('High', 0),
            "Medium Priority": priority_counts.get('Medium', 0),
            "Low Priority": priority_counts.get('Low', 0),
            "Average Progress": avg_progress,
            "Projects": len(projects),
            "Reports": len(member_reports)
        })
    
    # Create dataframe
    df = pd.DataFrame(activity_data)
    
    # Sort by current activities count
    df = df.sort_values(by="Current Activities", ascending=False)
    
    # Display activity metrics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Visualization of activity distribution
        selected_metric = st.selectbox(
            "Select Metric to Visualize", 
            options=[
                "Current Activities", "Upcoming Activities", "Average Progress", 
                "Completed", "In Progress", "Blocked", "Not Started",
                "High Priority", "Medium Priority", "Low Priority", "Projects"
            ],
            index=0
        )
        
        # Create bar chart
        fig = px.bar(
            df, 
            x="Team Member", 
            y=selected_metric,
            color=selected_metric,
            color_continuous_scale="Viridis",
            title=f"{selected_metric} by Team Member",
            text=selected_metric
        )
        
        fig.update_layout(
            xaxis_title="Team Member",
            yaxis_title=selected_metric,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Show top performers
        if "Average Progress" in df.columns:
            top_progress = df.sort_values(by="Average Progress", ascending=False).head(3)
            st.subheader("Top Progress")
            
            for _, row in top_progress.iterrows():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                    <h4 style="margin: 0">{row['Team Member']}</h4>
                    <p style="margin: 5px 0">Progress: <strong>{row['Average Progress']:.1f}%</strong></p>
                    <p style="margin: 0">Activities: {row['Current Activities']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Show detailed activity table
    st.subheader("Team Activity Details")
    
    # Add calculated columns for visualization
    # FIX: Ensure "Current Activities" is not zero before division
    if "Current Activities" in df.columns and "Completed" in df.columns:
        df["Completion Rate"] = df.apply(
            lambda row: (row["Completed"] / row["Current Activities"] * 100) if row["Current Activities"] > 0 else 0,
            axis=1
        )
        df["Completion Rate"] = df["Completion Rate"].round(1).astype(str) + '%'
    else:
        df["Completion Rate"] = "0.0%"


    # Select columns for display
    display_columns = [
        "Team Member", "Current Activities", "Upcoming Activities", 
        "Completed", "In Progress", "Blocked", "Average Progress", "Projects", "Reports"
    ]
    
    # Display table
    st.dataframe(df[display_columns], use_container_width=True)

def render_project_status_view(reports):
    """Render project status analysis view.
    
    Args:
        reports (list): List of filtered report dictionaries
    """
    st.subheader("Project Status")
    
    # Extract all activities
    all_activities = []
    for report in reports:
        for activity in report.get('current_activities', []):
            # Add report metadata to activity
            activity_copy = activity.copy()
            activity_copy['report_name'] = report.get('name', 'Unknown')
            activity_copy['report_date'] = report.get('timestamp', '')[:10]
            all_activities.append(activity_copy)
    
    if not all_activities:
        st.info("No activities found in the selected reports.")
        return
    
    # Group activities by project
    project_activities = {}
    for activity in all_activities:
        project = activity.get('project', 'Uncategorized')
        if project not in project_activities:
            project_activities[project] = []
        project_activities[project].append(activity)
    
    # Create project status data
    project_data = []
    for project, activities in project_activities.items():
        # Count statuses
        status_counts = {}
        for activity in activities:
            status = activity.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate average progress
        if activities:
            avg_progress = sum(activity.get('progress', 0) for activity in activities) / len(activities)
        else:
            avg_progress = 0
        
        # Count team members
        team_members = set()
        for activity in activities:
            team_members.add(activity.get('report_name', 'Unknown'))
        
        # Count milestones
        milestones = set()
        for activity in activities:
            milestone = activity.get('milestone', '')
            if milestone:
                milestones.add(milestone)
        
        # Add to data
        project_data.append({
            "Project": project,
            "Activities": len(activities),
            "Completed": status_counts.get('Completed', 0),
            "In Progress": status_counts.get('In Progress', 0),
            "Blocked": status_counts.get('Blocked', 0),
            "Not Started": status_counts.get('Not Started', 0),
            "Average Progress": avg_progress,
            "Team Members": len(team_members),
            "Milestones": len(milestones)
        })
    
    # Create dataframe
    df = pd.DataFrame(project_data)
    
    # Sort by activities count
    df = df.sort_values(by="Activities", ascending=False)
    
    # Visualization of project progress
    project_progress_df = df[["Project", "Average Progress"]].sort_values(by="Average Progress")
    
    # Create horizontal bar chart for project progress
    fig = px.bar(
        project_progress_df, 
        y="Project", 
        x="Average Progress",
        orientation='h',
        text=project_progress_df["Average Progress"].apply(lambda x: f"{x:.1f}%"),
        color="Average Progress",
        color_continuous_scale="Viridis",
        title="Project Progress",
        range_x=[0, 100]
    )
    
    fig.update_layout(
        yaxis=dict(autorange="reversed"),  # Highest value at the top
        xaxis_title="Average Progress (%)",
        yaxis_title="",
        height=max(400, 50 * len(project_progress_df))  # Dynamic height based on number of projects
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Project status breakdown
    st.subheader("Project Status Breakdown")
    
    # Allow selecting a project for detailed status
    if len(project_activities) > 1:
        selected_project = st.selectbox(
            "Select Project",
            options=list(project_activities.keys())
        )
        selected_activities = project_activities[selected_project]
    else:
        # If only one project, use that one
        selected_project = next(iter(project_activities.keys()))
        selected_activities = project_activities[selected_project]
    
    # Create status data
    status_df = pd.DataFrame([
        {"Status": status, "Count": count}
        for status, count in {
            'Completed': sum(1 for a in selected_activities if a.get('status') == 'Completed'),
            'In Progress': sum(1 for a in selected_activities if a.get('status') == 'In Progress'),
            'Blocked': sum(1 for a in selected_activities if a.get('status') == 'Blocked'),
            'Not Started': sum(1 for a in selected_activities if a.get('status') == 'Not Started')
        }.items()
    ])
    
    # Create pie chart for status distribution
    fig = px.pie(
        status_df, 
        values="Count", 
        names="Status",
        title=f"Status Distribution for {selected_project}",
        color="Status",
        color_discrete_map={
            'Completed': '#28a745',
            'In Progress': '#17a2b8',
            'Blocked': '#dc3545',
            'Not Started': '#6c757d'
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show activities for the selected project
    st.subheader(f"Activities for {selected_project}")
    
    # Create activity dataframe
    activity_df = pd.DataFrame([
        {
            "Description": a.get('description', 'No description'),
            "Status": a.get('status', 'Unknown'),
            "Progress": a.get('progress', 0),
            "Priority": a.get('priority', 'Medium'),
            "Team Member": a.get('report_name', 'Unknown'),
            "Milestone": a.get('milestone', 'None'),
            "Deadline": a.get('deadline', 'Not set')
        }
        for a in selected_activities
    ])
    
    # Display activities
    st.dataframe(activity_df, use_container_width=True)

def render_accomplishments_view(reports):
    """Render accomplishments analysis view.
    
    Args:
        reports (list): List of filtered report dictionaries
    """
    st.subheader("Accomplishments Analysis")
    
    # Extract all accomplishments
    all_accomplishments = []
    for report in reports:
        for accomplishment in report.get('accomplishments', []):
            if accomplishment:  # Skip empty strings
                all_accomplishments.append({
                    'text': accomplishment,
                    'report_name': report.get('name', 'Unknown'),
                    'report_date': report.get('timestamp', '')[:10]
                })
    
    if not all_accomplishments:
        st.info("No accomplishments found in the selected reports.")
        return
    
    # Display total accomplishments count
    st.metric("Total Accomplishments", len(all_accomplishments))
    
    # Word cloud of accomplishments (placeholder - would require additional library)
    st.write("**Common Terms in Accomplishments**")
    st.info("A word cloud visualization would appear here with common terms from accomplishments.")
    
    # Accomplishments by team member
    team_accomplishments = {}
    for acc in all_accomplishments:
        name = acc['report_name']
        if name not in team_accomplishments:
            team_accomplishments[name] = []
        team_accomplishments[name].append(acc)
    
    # Create dataframe
    team_acc_data = [
        {"Team Member": name, "Accomplishments": len(accs)}
        for name, accs in team_accomplishments.items()
    ]
    
    team_acc_df = pd.DataFrame(team_acc_data)
    team_acc_df = team_acc_df.sort_values(by="Accomplishments", ascending=False)
    
    # Create bar chart
    fig = px.bar(
        team_acc_df, 
        x="Team Member", 
        y="Accomplishments",
        color="Accomplishments",
        color_continuous_scale="Viridis",
        title="Accomplishments by Team Member",
        text="Accomplishments"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent accomplishments
    st.subheader("Recent Accomplishments")
    
    # Sort by date (most recent first)
    sorted_accomplishments = sorted(
        all_accomplishments, 
        key=lambda x: x['report_date'], 
        reverse=True
    )
    
    # Display recent accomplishments
    for acc in sorted_accomplishments[:10]:  # Show top 10
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <div><strong>{acc['report_name']}</strong></div>
                <div>{acc['report_date']}</div>
            </div>
            <p style="margin: 5px 0">{acc['text']}</p>
        </div>
        """, unsafe_allow_html=True)

def render_concerns_view(reports):
    """Render concerns and challenges analysis view.
    
    Args:
        reports (list): List of filtered report dictionaries
    """
    st.subheader("Concerns & Challenges")
    
    # Extract all concerns, challenges and blockers
    concerns = []
    challenges = []
    blockers = []
    
    for report in reports:
        # Get challenges from optional section
        if 'challenges' in report and report['challenges']:
            challenges.append({
                'text': report['challenges'],
                'report_name': report.get('name', 'Unknown'),
                'report_date': report.get('timestamp', '')[:10]
            })
        
        # Get concerns from optional section
        if 'concerns' in report and report['concerns']:
            concerns.append({
                'text': report['concerns'],
                'report_name': report.get('name', 'Unknown'),
                'report_date': report.get('timestamp', '')[:10]
            })
        
        # Get blocked activities
        for activity in report.get('current_activities', []):
            if activity.get('status') == 'Blocked':
                blockers.append({
                    'text': activity.get('description', 'No description'),
                    'project': activity.get('project', 'Uncategorized'),
                    'priority': activity.get('priority', 'Medium'),
                    'report_name': report.get('name', 'Unknown'),
                    'report_date': report.get('timestamp', '')[:10]
                })
    
    # Display counts
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Challenges Reported", len(challenges))
    
    with col2:
        st.metric("Concerns Raised", len(concerns))
    
    with col3:
        st.metric("Blocked Activities", len(blockers))
    
    # Blocked activities by priority
    if blockers:
        st.subheader("Blocked Activities by Priority")
        
        # Count by priority
        priority_counts = {}
        for blocker in blockers:
            priority = blocker.get('priority', 'Medium')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Create data
        priority_data = [
            {"Priority": priority, "Count": count}
            for priority, count in priority_counts.items()
        ]
        
        priority_df = pd.DataFrame(priority_data)
        
        # Create bar chart with custom colors
        fig = px.bar(
            priority_df, 
            x="Priority", 
            y="Count",
            color="Priority",
            color_discrete_map={
                'High': '#dc3545',
                'Medium': '#ffc107',
                'Low': '#28a745'
            },
            title="Blocked Activities by Priority",
            text="Count"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent challenges
    if challenges:
        st.subheader("Recent Challenges")
        
        # Sort by date (most recent first)
        sorted_challenges = sorted(
            challenges, 
            key=lambda x: x['report_date'], 
            reverse=True
        )
        
        # Display recent challenges
        for challenge in sorted_challenges[:5]:  # Show top 5
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between;">
                    <div><strong>{challenge['report_name']}</strong></div>
                    <div>{challenge['report_date']}</div>
                </div>
                <p style="margin: 5px 0">{challenge['text']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No challenges reported in the selected time period.")
    
    # Recent concerns
    if concerns:
        st.subheader("Recent Concerns")
        
        # Sort by date (most recent first)
        sorted_concerns = sorted(
            concerns, 
            key=lambda x: x['report_date'], 
            reverse=True
        )
        
        # Display recent concerns
        for concern in sorted_concerns[:5]:  # Show top 5
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between;">
                    <div><strong>{concern['report_name']}</strong></div>
                    <div>{concern['report_date']}</div>
                </div>
                <p style="margin: 5px 0">{concern['text']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No concerns raised in the selected time period.")

def get_all_reports():
    """Get all reports from the reports directory.
    
    Returns:
        list: List of report dictionaries
    """
    try:
        # Import file_ops to reuse existing functionality
        from utils.file_ops import get_all_reports as get_reports
        
        # Use the existing function with filter_by_user=False to get all reports
        reports = get_reports(filter_by_user=False)
        
        return reports
    except Exception as e:
        st.error(f"Error retrieving reports: {str(e)}")
        return []
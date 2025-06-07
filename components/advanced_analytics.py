# components/advanced_analytics.py
"""Advanced analytics component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import io
import base64
from utils.file_ops import get_all_reports

def render_advanced_analytics():
    """Render advanced analytics dashboard for weekly reports."""
    st.title("Advanced Report Analytics")
    st.write("Gain deeper insights into weekly reports and team performance.")
    
    # Get all reports
    reports = get_all_reports(filter_by_user=False)
    if not reports:
        st.info("No reports found. Analytics will be available once reports are submitted.")
        return
    
    # Filter section
    with st.expander("Filters", expanded=True):
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            # Get min and max dates from reports
            all_dates = [datetime.fromisoformat(r.get('timestamp', datetime.now().isoformat())[:10]) 
                        for r in reports if 'timestamp' in r]
            if all_dates:
                min_date = min(all_dates).date()
                max_date = max(all_dates).date()
            else:
                min_date = (datetime.now() - timedelta(days=90)).date()
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
        
        # Team member filter
        team_members = sorted(list(set([r.get('name', 'Anonymous') for r in reports])))
        selected_members = st.multiselect("Team Members", options=team_members, default=team_members)
        
        # Project filter
        all_projects = set()
        for report in reports:
            for activity in report.get('current_activities', []) + report.get('upcoming_activities', []):
                if 'project' in activity and activity['project']:
                    all_projects.add(activity['project'])
        
        projects = sorted(list(all_projects))
        selected_projects = st.multiselect("Projects", options=projects, default=[])
    
    # Apply filters
    filtered_reports = reports
    
    # Date filter
    filtered_reports = [
        r for r in filtered_reports 
        if 'timestamp' in r and 
        start_date <= datetime.fromisoformat(r['timestamp'][:10]).date() <= end_date
    ]
    
    # Team member filter
    if selected_members:
        filtered_reports = [r for r in filtered_reports if r.get('name', 'Anonymous') in selected_members]
    
    # Project filter
    if selected_projects:
        filtered_reports = [
            r for r in filtered_reports 
            if any(activity.get('project') in selected_projects 
                  for activity in r.get('current_activities', []) + r.get('upcoming_activities', []))
        ]
    
    if not filtered_reports:
        st.warning("No reports match your filter criteria.")
        return
    
    # Advanced analytics visualizations
    st.success(f"Analyzing {len(filtered_reports)} reports from {len(selected_members)} team members")
    
    # Data preparation
    activity_data = process_activity_data(filtered_reports)
    accomplishment_data = process_accomplishment_data(filtered_reports)
    
    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Progress Metrics", "Project Insights", "Accomplishment Analysis", "Export Data"])
    
    with tab1:
        render_progress_metrics(activity_data)
    
    with tab2:
        render_project_insights(activity_data)
    
    with tab3:
        render_accomplishment_analysis(accomplishment_data)
    
    with tab4:
        render_data_export(filtered_reports, activity_data, accomplishment_data)

def process_activity_data(reports):
    """Process activity data from reports.
    
    Args:
        reports (list): List of report dictionaries
        
    Returns:
        dict: Processed activity data
    """
    # Initialize data structures
    activities = []
    
    # Process each report
    for report in reports:
        name = report.get('name', 'Anonymous')
        report_date = report.get('timestamp', '')[:10] if report.get('timestamp') else 'Unknown'
        reporting_week = report.get('reporting_week', 'Unknown')
        
        # Process current activities
        for activity in report.get('current_activities', []):
            # --- INICIO DE LA CORRECCIÓN ---
            # Safely convert progress to an integer
            try:
                progress_val = int(float(activity.get('progress', 0)))
            except (ValueError, TypeError):
                progress_val = 0
            # --- FIN DE LA CORRECCIÓN ---
            
            activities.append({
                'team_member': name,
                'date': report_date,
                'week': reporting_week,
                'activity_type': 'Current',
                'project': activity.get('project', 'Uncategorized'),
                'milestone': activity.get('milestone', ''),
                'status': activity.get('status', 'Unknown'),
                'priority': activity.get('priority', 'Medium'),
                'progress': progress_val, # Usar el valor numérico limpio
                'description': activity.get('description', '')
            })
        
        # Process upcoming activities
        for activity in report.get('upcoming_activities', []):
            activities.append({
                'team_member': name,
                'date': report_date,
                'week': reporting_week,
                'activity_type': 'Upcoming',
                'project': activity.get('project', 'Uncategorized'),
                'milestone': activity.get('milestone', ''),
                'priority': activity.get('priority', 'Medium'),
                'expected_start': activity.get('expected_start', ''),
                'description': activity.get('description', '')
            })
    
    return {
        'activities': activities,
        'activity_df': pd.DataFrame(activities) if activities else None
    }

def process_accomplishment_data(reports):
    """Process accomplishment data from reports.
    
    Args:
        reports (list): List of report dictionaries
        
    Returns:
        dict: Processed accomplishment data
    """
    # Initialize data structures
    accomplishments = []
    
    # Process each report
    for report in reports:
        name = report.get('name', 'Anonymous')
        report_date = report.get('timestamp', '')[:10] if report.get('timestamp') else 'Unknown'
        reporting_week = report.get('reporting_week', 'Unknown')
        
        # Process accomplishments
        for accomplishment in report.get('accomplishments', []):
            # Check if accomplishment is a string or JSON (for enhanced accomplishments)
            text = accomplishment
            project = ''
            milestone = ''
            
            if isinstance(accomplishment, str) and accomplishment.startswith('{') and accomplishment.endswith('}'):
                try:
                    acc_data = json.loads(accomplishment)
                    if isinstance(acc_data, dict):
                        text = acc_data.get('text', accomplishment)
                        project = acc_data.get('project', '')
                        milestone = acc_data.get('milestone', '')
                except:
                    pass
            
            accomplishments.append({
                'team_member': name,
                'date': report_date,
                'week': reporting_week,
                'accomplishment': text,
                'project': project,
                'milestone': milestone
            })
    
    return {
        'accomplishments': accomplishments,
        'accomplishment_df': pd.DataFrame(accomplishments) if accomplishments else None
    }

def render_progress_metrics(activity_data):
    """Render progress metrics visualizations.
    
    Args:
        activity_data (dict): Processed activity data
    """
    st.subheader("Progress Metrics")
    
    # Check if we have data
    if activity_data['activity_df'] is None or len(activity_data['activity_df']) == 0:
        st.info("No activity data available for the selected filters.")
        return
    
    df = activity_data['activity_df']
    
    # Filter to current activities only for progress analysis
    current_df = df[df['activity_type'] == 'Current'].copy()
    
    if len(current_df) == 0:
        st.info("No current activities found for analysis.")
        return
    
    try:
        # Calculate average progress by team member
        progress_by_member = current_df.groupby('team_member')['progress'].mean().reset_index()
        progress_by_member = progress_by_member.sort_values('progress', ascending=False)
        
        fig = px.bar(
            progress_by_member,
            x='team_member',
            y='progress',
            title='Average Progress by Team Member',
            labels={'progress': 'Average Progress (%)', 'team_member': 'Team Member'},
            text=progress_by_member['progress'].round(1).astype(str) + '%',
            color='progress',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Progress by project
        progress_by_project = current_df.groupby('project')['progress'].mean().reset_index()
        progress_by_project = progress_by_project.sort_values('progress', ascending=False)
        
        fig = px.bar(
            progress_by_project,
            x='project',
            y='progress',
            title='Average Progress by Project',
            labels={'progress': 'Average Progress (%)', 'project': 'Project'},
            text=progress_by_project['progress'].round(1).astype(str) + '%',
            color='progress',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Status distribution
        status_counts = current_df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        fig = px.pie(
            status_counts, 
            values='Count', 
            names='Status',
            title='Activity Status Distribution',
            color='Status',
            color_discrete_map={
                'Completed': '#28a745',
                'In Progress': '#17a2b8',
                'Blocked': '#dc3545',
                'Not Started': '#6c757d'
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error generating progress metrics: {str(e)}")

def render_project_insights(activity_data):
    """Render project insights visualizations.
    
    Args:
        activity_data (dict): Processed activity data
    """
    st.subheader("Project Insights")
    
    # Check if we have data
    if activity_data['activity_df'] is None or len(activity_data['activity_df']) == 0:
        st.info("No activity data available for the selected filters.")
        return
    
    df = activity_data['activity_df']
    
    try:
        # Project activity counts
        project_counts = df['project'].value_counts().reset_index()
        project_counts.columns = ['Project', 'Activities']
        
        fig = px.bar(
            project_counts,
            x='Project',
            y='Activities',
            title='Activities per Project',
            color='Activities',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Project priority distribution
        priority_df = df[df['activity_type'] == 'Current'].copy()
        
        if len(priority_df) > 0:
            # Count activities by project and priority
            project_priority = priority_df.groupby(['project', 'priority']).size().reset_index(name='count')
            
            fig = px.bar(
                project_priority,
                x='project',
                y='count',
                color='priority',
                title='Project Priorities',
                labels={'count': 'Number of Activities', 'project': 'Project', 'priority': 'Priority'},
                color_discrete_map={
                    'High': '#dc3545',
                    'Medium': '#ffc107',
                    'Low': '#28a745'
                }
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Team member project allocation
        member_project = df.groupby(['team_member', 'project']).size().reset_index(name='activities')
        
        # Create a pivot table for better visualization
        pivot_df = member_project.pivot_table(
            index='team_member', 
            columns='project', 
            values='activities',
            fill_value=0
        ).reset_index()
        
        # Display as a heatmap
        projects = list(pivot_df.columns[1:])  # Skip the 'team_member' column
        team_members = pivot_df['team_member'].tolist()
        
        if projects and team_members:
            z_data = pivot_df[projects].values
            
            fig = go.Figure(data=go.Heatmap(
                z=z_data,
                x=projects,
                y=team_members,
                colorscale='Viridis',
                colorbar=dict(title='Activities'),
                hoverongaps=False
            ))
            
            fig.update_layout(
                title='Team Member Project Allocation',
                xaxis_title='Project',
                yaxis_title='Team Member',
                height=max(400, 100 + 30 * len(team_members))
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating project insights: {str(e)}")

# components/advanced_analytics.py (continued)

def render_accomplishment_analysis(accomplishment_data):
    """Render accomplishment analysis visualizations.
    
    Args:
        accomplishment_data (dict): Processed accomplishment data
    """
    st.subheader("Accomplishment Analysis")
    
    # Check if we have data
    if accomplishment_data['accomplishment_df'] is None or len(accomplishment_data['accomplishment_df']) == 0:
        st.info("No accomplishment data available for the selected filters.")
        return
    
    df = accomplishment_data['accomplishment_df']
    
    try:
        # Accomplishments per team member
        member_counts = df['team_member'].value_counts().reset_index()
        member_counts.columns = ['Team Member', 'Accomplishments']
        
        fig = px.bar(
            member_counts,
            x='Team Member',
            y='Accomplishments',
            title='Accomplishments per Team Member',
            color='Accomplishments',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Accomplishments over time
        if 'date' in df.columns:
            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Group by date
            time_trend = df.groupby(df['date']).size().reset_index(name='count')
            
            fig = px.line(
                time_trend,
                x='date',
                y='count',
                title='Accomplishments Over Time',
                markers=True
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Project-related accomplishments
        if 'project' in df.columns:
            # Filter to accomplishments with projects
            project_df = df[df['project'] != ''].copy()
            
            if len(project_df) > 0:
                project_counts = project_df['project'].value_counts().reset_index()
                project_counts.columns = ['Project', 'Accomplishments']
                
                fig = px.pie(
                    project_counts,
                    values='Accomplishments',
                    names='Project',
                    title='Accomplishments by Project'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Display recent accomplishments
        st.subheader("Recent Accomplishments")
        recent_df = df.sort_values('date', ascending=False).head(10)
        
        for _, row in recent_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div><strong>{row['team_member']}</strong></div>
                        <div>{row['date']}</div>
                    </div>
                    <p style="margin: 5px 0">{row['accomplishment']}</p>
                    {f'<div><em>Project: {row["project"]}</em></div>' if row["project"] else ''}
                </div>
                """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error generating accomplishment analysis: {str(e)}")

def render_data_export(reports, activity_data, accomplishment_data):
    """Render data export options.
    
    Args:
        reports (list): List of report dictionaries
        activity_data (dict): Processed activity data
        accomplishment_data (dict): Processed accomplishment data
    """
    st.subheader("Export Data")
    st.write("Export the filtered report data in different formats.")
    
    # Create export tabs
    export_tab1, export_tab2, export_tab3 = st.tabs(["CSV Export", "Excel Export", "Batch PDF Export"])
    
    with export_tab1:
        st.write("Export data as CSV files.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if activity_data['activity_df'] is not None and len(activity_data['activity_df']) > 0:
                csv = activity_data['activity_df'].to_csv(index=False)
                st.download_button(
                    "Download Activities CSV",
                    data=csv,
                    file_name="activities_export.csv",
                    mime="text/csv"
                )
            else:
                st.info("No activity data available to export.")
        
        with col2:
            if accomplishment_data['accomplishment_df'] is not None and len(accomplishment_data['accomplishment_df']) > 0:
                csv = accomplishment_data['accomplishment_df'].to_csv(index=False)
                st.download_button(
                    "Download Accomplishments CSV",
                    data=csv,
                    file_name="accomplishments_export.csv",
                    mime="text/csv"
                )
            else:
                st.info("No accomplishment data available to export.")
    
    with export_tab2:
        st.write("Export data as Excel worksheets.")
        
        if ((activity_data['activity_df'] is not None and len(activity_data['activity_df']) > 0) or
            (accomplishment_data['accomplishment_df'] is not None and len(accomplishment_data['accomplishment_df']) > 0)):
            
            # Create Excel file with multiple sheets
            excel_buffer = io.BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Add activities sheet
                if activity_data['activity_df'] is not None and len(activity_data['activity_df']) > 0:
                    activity_data['activity_df'].to_excel(writer, sheet_name='Activities', index=False)
                    
                    # Get the xlsxwriter workbook and worksheet objects
                    workbook = writer.book
                    worksheet = writer.sheets['Activities']
                    
                    # Add a format for headers
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#D7E4BC',
                        'border': 1
                    })
                    
                    # Write the column headers with the defined format
                    for col_num, value in enumerate(activity_data['activity_df'].columns.values):
                        worksheet.write(0, col_num, value, header_format)
                        
                    # Set column widths
                    worksheet.set_column('A:Z', 15)
                
                # Add accomplishments sheet
                if accomplishment_data['accomplishment_df'] is not None and len(accomplishment_data['accomplishment_df']) > 0:
                    accomplishment_data['accomplishment_df'].to_excel(writer, sheet_name='Accomplishments', index=False)
                    
                    # Get the xlsxwriter workbook and worksheet objects
                    workbook = writer.book
                    worksheet = writer.sheets['Accomplishments']
                    
                    # Add a format for headers
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#D7E4BC',
                        'border': 1
                    })
                    
                    # Write the column headers with the defined format
                    for col_num, value in enumerate(accomplishment_data['accomplishment_df'].columns.values):
                        worksheet.write(0, col_num, value, header_format)
                        
                    # Set column widths
                    worksheet.set_column('A:Z', 15)
                    worksheet.set_column('D:D', 40)  # Make accomplishment column wider
                
                # Add a summary sheet
                summary_data = {
                    'Metric': [
                        'Total Reports',
                        'Team Members',
                        'Date Range',
                        'Projects',
                        'Current Activities',
                        'Upcoming Activities',
                        'Accomplishments'
                    ],
                    'Value': [
                        len(reports),
                        len(set([r.get('name', 'Anonymous') for r in reports])),
                        f"{min([r.get('timestamp', '')[:10] for r in reports if 'timestamp' in r])} to {max([r.get('timestamp', '')[:10] for r in reports if 'timestamp' in r])}",
                        len(set([a.get('project', '') for r in reports for a in r.get('current_activities', []) + r.get('upcoming_activities', [])])),
                        sum(len(r.get('current_activities', [])) for r in reports),
                        sum(len(r.get('upcoming_activities', [])) for r in reports),
                        sum(len(r.get('accomplishments', [])) for r in reports)
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Format summary sheet
                worksheet = writer.sheets['Summary']
                
                # Add a format for headers
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Write the column headers with the defined format
                for col_num, value in enumerate(summary_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Set column widths
                worksheet.set_column('A:A', 20)
                worksheet.set_column('B:B', 40)
            
            # Create download button for Excel
            excel_data = excel_buffer.getvalue()
            st.download_button(
                "Download Excel Report",
                data=excel_data,
                file_name="weekly_reports_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No data available to export to Excel.")
    
    with export_tab3:
        st.write("Export batch PDF reports.")
        
        # Allow selecting reports to export
        if reports:
            report_options = [f"{r.get('name', 'Unknown')} - {r.get('reporting_week', 'Unknown')} ({r.get('timestamp', '')[:10]})" for r in reports]
            selected_indices = st.multiselect("Select Reports to Export", options=range(len(report_options)), format_func=lambda i: report_options[i])
            
            if selected_indices:
                if st.button("Export Selected Reports as PDF"):
                    try:
                        # Import PDF export function
                        from utils.pdf_export import export_report_to_pdf
                        
                        with st.spinner("Generating PDFs..."):
                            # Create PDF files for selected reports
                            for i in selected_indices:
                                report_data = reports[i]
                                pdf_path = export_report_to_pdf(report_data)
                                
                                # Create download link for individual report
                                with open(pdf_path, "rb") as f:
                                    pdf_bytes = f.read()
                                
                                filename = f"report_{report_data.get('name', 'unknown')}_{report_data.get('reporting_week', 'unknown')}.pdf"
                                b64_pdf = base64.b64encode(pdf_bytes).decode()
                                
                                st.markdown(
                                    f"### {report_data.get('name', 'Unknown')} - {report_data.get('reporting_week', 'Unknown')}\n"
                                    f"<a href='data:application/octet-stream;base64,{b64_pdf}' download='{filename}'>Download PDF</a>", 
                                    unsafe_allow_html=True
                                )
                            
                            st.success(f"Successfully generated {len(selected_indices)} PDF reports.")
                    except Exception as e:
                        st.error(f"Error generating PDFs: {str(e)}")
            else:
                st.info("Select reports to generate PDFs.")
        else:
            st.info("No reports available for PDF export.")
# components/batch_export.py
"""Batch export component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import json
import os
import tempfile
import shutil
import zipfile
import base64
import io
from datetime import datetime, timedelta
from utils.file_ops import get_all_reports

def render_batch_export():
    """Render the batch export page."""
    st.title("Batch Export")
    st.write("Export multiple reports and data in various formats.")
    
    # Get all reports
    reports = get_all_reports(filter_by_user=False)
    if not reports:
        st.info("No reports found. Export features will be available once reports are submitted.")
        return
    
    # Filter section
    with st.expander("Filter Reports", expanded=True):
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
        
        # Report status filter
        statuses = sorted(list(set([r.get('status', 'submitted') for r in reports])))
        selected_statuses = st.multiselect("Report Status", options=statuses, default=statuses)
    
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
    
    # Status filter
    if selected_statuses:
        filtered_reports = [r for r in filtered_reports if r.get('status', 'submitted') in selected_statuses]
    
    # Display count of filtered reports
    if filtered_reports:
        st.success(f"Found {len(filtered_reports)} reports matching your filters")
    else:
        st.warning("No reports match your filter criteria.")
        return
    
    # Create tabs for different export types
    tab1, tab2, tab3, tab4 = st.tabs(["PDF Export", "CSV Export", "Excel Export", "JSON Export"])
    
    with tab1:
        render_pdf_export(filtered_reports)
    
    with tab2:
        render_csv_export(filtered_reports)
    
    with tab3:
        render_excel_export(filtered_reports)
    
    with tab4:
        render_json_export(filtered_reports)

def render_pdf_export(reports):
    """Render PDF export options.
    
    Args:
        reports (list): List of filtered report dictionaries
    """
    st.subheader("PDF Export")
    st.write("Export reports as PDF files.")
    
    # Display reports in a table
    report_data = []
    for i, report in enumerate(reports):
        report_data.append({
            "Team Member": report.get('name', 'Anonymous'),
            "Week": report.get('reporting_week', 'Unknown'),
            "Date": report.get('timestamp', '')[:10] if report.get('timestamp') else 'Unknown',
            "Status": report.get('status', 'Unknown'),
            "Index": i  # Keep track of original index
        })
    
    report_df = pd.DataFrame(report_data)
    
    # Show table
    st.dataframe(report_df[["Team Member", "Week", "Date", "Status"]], use_container_width=True)
    
    # Select reports to export
    selected_indices = st.multiselect(
        "Select Reports to Export",
        options=list(range(len(reports))),
        format_func=lambda i: f"{reports[i].get('name', 'Anonymous')} - {reports[i].get('reporting_week', 'Unknown')} ({reports[i].get('timestamp', '')[:10] if reports[i].get('timestamp') else 'Unknown'})"
    )
    
    if selected_indices:
        # Individual PDF downloads
        if st.button("Generate Individual PDFs"):
            st.write("### Download Individual PDFs")
            
            try:
                # Import PDF export function
                from utils.pdf_export import export_report_to_pdf
                
                with st.spinner("Generating PDFs..."):
                    # Create a directory to store PDFs
                    temp_dir = tempfile.mkdtemp()
                    pdf_paths = []
                    
                    # Create PDF files for selected reports
                    for i in selected_indices:
                        report_data = reports[i]
                        pdf_path = export_report_to_pdf(report_data)
                        pdf_paths.append(pdf_path)
                        
                        # Create download link for individual report
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        
                        filename = f"report_{report_data.get('name', 'unknown')}_{report_data.get('reporting_week', 'unknown')}.pdf"
                        b64_pdf = base64.b64encode(pdf_bytes).decode()
                        
                        st.markdown(
                            f"#### {report_data.get('name', 'Unknown')} - {report_data.get('reporting_week', 'Unknown')}\n"
                            f"<a href='data:application/octet-stream;base64,{b64_pdf}' download='{filename}'>Download PDF</a>", 
                            unsafe_allow_html=True
                        )
            
            except Exception as e:
                st.error(f"Error generating PDFs: {str(e)}")
        
        # ZIP file with all PDFs
        if st.button("Download All as ZIP"):
            try:
                # Import PDF export function
                from utils.pdf_export import export_report_to_pdf
                
                with st.spinner("Creating ZIP file with all PDFs..."):
                    # Create a directory to store PDFs
                    temp_dir = tempfile.mkdtemp()
                    
                    # Create PDF files for selected reports
                    for i in selected_indices:
                        report_data = reports[i]
                        pdf_path = export_report_to_pdf(report_data)
                        
                        # Copy to temp dir with descriptive name
                        filename = f"report_{report_data.get('name', 'unknown').replace(' ', '_')}_{report_data.get('reporting_week', 'unknown').replace(' ', '_')}.pdf"
                        shutil.copy(pdf_path, os.path.join(temp_dir, filename))
                    
                    # Create ZIP file
                    zip_path = os.path.join(tempfile.gettempdir(), "weekly_reports.zip")
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                zipf.write(os.path.join(root, file), arcname=file)
                    
                    # Provide download link
                    with open(zip_path, "rb") as f:
                        zip_bytes = f.read()
                    
                    st.download_button(
                        "Download ZIP with PDFs",
                        data=zip_bytes,
                        file_name="weekly_reports.zip",
                        mime="application/zip"
                    )
            
            except Exception as e:
                st.error(f"Error creating ZIP file: {str(e)}")
    else:
        st.info("Select reports to export from the list above.")

def render_csv_export(reports):
    """Render CSV export options.
    
    Args:
        reports (list): List of filtered report dictionaries
    """
    st.subheader("CSV Export")
    st.write("Export report data as CSV files.")
    
    # Prepare data for CSV export
    activities = []
    upcoming_activities = []
    accomplishments = []
    action_items = []
    
    for report in reports:
        name = report.get('name', 'Anonymous')
        report_date = report.get('timestamp', '')[:10] if report.get('timestamp') else 'Unknown'
        reporting_week = report.get('reporting_week', 'Unknown')
        
        # Process current activities
        for activity in report.get('current_activities', []):
            activities.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Type': 'Current',
                'Project': activity.get('project', ''),
                'Milestone': activity.get('milestone', ''),
                'Status': activity.get('status', ''),
                'Priority': activity.get('priority', ''),
                'Progress': activity.get('progress', 0),
                'Description': activity.get('description', '')
            })
        
        # Process upcoming activities
        for activity in report.get('upcoming_activities', []):
            upcoming_activities.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Project': activity.get('project', ''),
                'Milestone': activity.get('milestone', ''),
                'Priority': activity.get('priority', ''),
                'Expected Start': activity.get('expected_start', ''),
                'Description': activity.get('description', '')
            })
        
        # Process accomplishments
        for accomplishment in report.get('accomplishments', []):
            # Handle possible JSON formatted accomplishments
            accomplishment_text = accomplishment
            project = ''
            milestone = ''
            
            if isinstance(accomplishment, str) and accomplishment.startswith('{') and accomplishment.endswith('}'):
                try:
                    acc_data = json.loads(accomplishment)
                    if isinstance(acc_data, dict):
                        accomplishment_text = acc_data.get('text', accomplishment)
                        project = acc_data.get('project', '')
                        milestone = acc_data.get('milestone', '')
                except:
                    pass
            
            accomplishments.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Project': project,
                'Milestone': milestone,
                'Accomplishment': accomplishment_text
            })
        
        # Process action items (followups and nextsteps)
        for followup in report.get('followups', []):
            # Handle possible JSON formatted action items
            followup_text = followup
            project = ''
            milestone = ''
            
            if isinstance(followup, str) and followup.startswith('{') and followup.endswith('}'):
                try:
                    followup_data = json.loads(followup)
                    if isinstance(followup_data, dict):
                        followup_text = followup_data.get('text', followup)
                        project = followup_data.get('project', '')
                        milestone = followup_data.get('milestone', '')
                except:
                    pass
            
            action_items.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Type': 'Follow-up',
                'Project': project,
                'Milestone': milestone,
                'Action Item': followup_text
            })
        
        for nextstep in report.get('nextsteps', []):
            # Handle possible JSON formatted action items
            nextstep_text = nextstep
            project = ''
            milestone = ''
            
            if isinstance(nextstep, str) and nextstep.startswith('{') and nextstep.endswith('}'):
                try:
                    nextstep_data = json.loads(nextstep)
                    if isinstance(nextstep_data, dict):
                        nextstep_text = nextstep_data.get('text', nextstep)
                        project = nextstep_data.get('project', '')
                        milestone = nextstep_data.get('milestone', '')
                except:
                    pass
            
            action_items.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Type': 'Next Step',
                'Project': project,
                'Milestone': milestone,
                'Action Item': nextstep_text
            })
    
    # Create DataFrames
    activities_df = pd.DataFrame(activities)
    upcoming_df = pd.DataFrame(upcoming_activities)
    accomplishments_df = pd.DataFrame(accomplishments)
    action_items_df = pd.DataFrame(action_items)
    
    # Create export buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if not activities_df.empty:
            st.download_button(
                "Download Current Activities CSV",
                data=activities_df.to_csv(index=False),
                file_name="current_activities.csv",
                mime="text/csv"
            )
        else:
            st.info("No current activities to export.")
        
        if not accomplishments_df.empty:
            st.download_button(
                "Download Accomplishments CSV",
                data=accomplishments_df.to_csv(index=False),
                file_name="accomplishments.csv",
                mime="text/csv"
            )
        else:
            st.info("No accomplishments to export.")
    
    with col2:
        if not upcoming_df.empty:
            st.download_button(
                "Download Upcoming Activities CSV",
                data=upcoming_df.to_csv(index=False),
                file_name="upcoming_activities.csv",
                mime="text/csv"
            )
        else:
            st.info("No upcoming activities to export.")
        
        if not action_items_df.empty:
            st.download_button(
                "Download Action Items CSV",
                data=action_items_df.to_csv(index=False),
                file_name="action_items.csv",
                mime="text/csv"
            )
        else:
            st.info("No action items to export.")

# components/batch_export.py (continued)

def render_excel_export(reports):
    """Render Excel export options.
    
    Args:
        reports (list): List of filtered report dictionaries
    """
    st.subheader("Excel Export")
    st.write("Export report data as Excel files.")
    
    # Prepare data for Excel export (using same data preparation as CSV export)
    activities = []
    upcoming_activities = []
    accomplishments = []
    action_items = []
    
    for report in reports:
        name = report.get('name', 'Anonymous')
        report_date = report.get('timestamp', '')[:10] if report.get('timestamp') else 'Unknown'
        reporting_week = report.get('reporting_week', 'Unknown')
        
        # Process current activities
        for activity in report.get('current_activities', []):
            activities.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Type': 'Current',
                'Project': activity.get('project', ''),
                'Milestone': activity.get('milestone', ''),
                'Status': activity.get('status', ''),
                'Priority': activity.get('priority', ''),
                'Progress': activity.get('progress', 0),
                'Description': activity.get('description', '')
            })
        
        # Process upcoming activities
        for activity in report.get('upcoming_activities', []):
            upcoming_activities.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Project': activity.get('project', ''),
                'Milestone': activity.get('milestone', ''),
                'Priority': activity.get('priority', ''),
                'Expected Start': activity.get('expected_start', ''),
                'Description': activity.get('description', '')
            })
        
        # Process accomplishments
        for accomplishment in report.get('accomplishments', []):
            # Handle possible JSON formatted accomplishments
            accomplishment_text = accomplishment
            project = ''
            milestone = ''
            
            if isinstance(accomplishment, str) and accomplishment.startswith('{') and accomplishment.endswith('}'):
                try:
                    acc_data = json.loads(accomplishment)
                    if isinstance(acc_data, dict):
                        accomplishment_text = acc_data.get('text', accomplishment)
                        project = acc_data.get('project', '')
                        milestone = acc_data.get('milestone', '')
                except:
                    pass
            
            accomplishments.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Project': project,
                'Milestone': milestone,
                'Accomplishment': accomplishment_text
            })
        
        # Process action items (followups and nextsteps)
        for followup in report.get('followups', []):
            # Handle possible JSON formatted action items
            followup_text = followup
            project = ''
            milestone = ''
            
            if isinstance(followup, str) and followup.startswith('{') and followup.endswith('}'):
                try:
                    followup_data = json.loads(followup)
                    if isinstance(followup_data, dict):
                        followup_text = followup_data.get('text', followup)
                        project = followup_data.get('project', '')
                        milestone = followup_data.get('milestone', '')
                except:
                    pass
            
            action_items.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Type': 'Follow-up',
                'Project': project,
                'Milestone': milestone,
                'Action Item': followup_text
            })
        
        for nextstep in report.get('nextsteps', []):
            # Handle possible JSON formatted action items
            nextstep_text = nextstep
            project = ''
            milestone = ''
            
            if isinstance(nextstep, str) and nextstep.startswith('{') and nextstep.endswith('}'):
                try:
                    nextstep_data = json.loads(nextstep)
                    if isinstance(nextstep_data, dict):
                        nextstep_text = nextstep_data.get('text', nextstep)
                        project = nextstep_data.get('project', '')
                        milestone = nextstep_data.get('milestone', '')
                except:
                    pass
            
            action_items.append({
                'Team Member': name,
                'Date': report_date,
                'Week': reporting_week,
                'Type': 'Next Step',
                'Project': project,
                'Milestone': milestone,
                'Action Item': nextstep_text
            })
    
    # Create DataFrames
    activities_df = pd.DataFrame(activities) if activities else pd.DataFrame()
    upcoming_df = pd.DataFrame(upcoming_activities) if upcoming_activities else pd.DataFrame()
    accomplishments_df = pd.DataFrame(accomplishments) if accomplishments else pd.DataFrame()
    action_items_df = pd.DataFrame(action_items) if action_items else pd.DataFrame()
    
    # Create report summary
    report_summary = []
    for report in reports:
        report_summary.append({
            'Team Member': report.get('name', 'Anonymous'),
            'Week': report.get('reporting_week', 'Unknown'),
            'Date': report.get('timestamp', '')[:10] if report.get('timestamp') else 'Unknown',
            'Status': report.get('status', 'Unknown'),
            'Current Activities': len(report.get('current_activities', [])),
            'Upcoming Activities': len(report.get('upcoming_activities', [])),
            'Accomplishments': len(report.get('accomplishments', [])),
            'Action Items': len(report.get('followups', [])) + len(report.get('nextsteps', []))
        })
    
    summary_df = pd.DataFrame(report_summary)
    
    # Create a single Excel workbook with all data
    if not (activities_df.empty and upcoming_df.empty and accomplishments_df.empty and action_items_df.empty):
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            # Summary sheet
            if not summary_df.empty:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Format summary sheet
                workbook = writer.book
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
                worksheet.set_column('A:A', 20)  # Team Member
                worksheet.set_column('B:C', 15)  # Week and Date
                
            # Current activities sheet
            if not activities_df.empty:
                activities_df.to_excel(writer, sheet_name='Current Activities', index=False)
                
                # Format sheet
                workbook = writer.book
                worksheet = writer.sheets['Current Activities']
                
                # Add a format for headers
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Write the column headers with the defined format
                for col_num, value in enumerate(activities_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Set column widths
                worksheet.set_column('A:J', 15)
                worksheet.set_column('J:J', 40)  # Description column wider
            
            # Upcoming activities sheet
            if not upcoming_df.empty:
                upcoming_df.to_excel(writer, sheet_name='Upcoming Activities', index=False)
                
                # Format sheet
                workbook = writer.book
                worksheet = writer.sheets['Upcoming Activities']
                
                # Add a format for headers
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Write the column headers with the defined format
                for col_num, value in enumerate(upcoming_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Set column widths
                worksheet.set_column('A:G', 15)
                worksheet.set_column('H:H', 40)  # Description column wider
            
            # Accomplishments sheet
            if not accomplishments_df.empty:
                accomplishments_df.to_excel(writer, sheet_name='Accomplishments', index=False)
                
                # Format sheet
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
                for col_num, value in enumerate(accomplishments_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Set column widths
                worksheet.set_column('A:E', 15)
                worksheet.set_column('F:F', 50)  # Accomplishment column wider
            
            # Action items sheet
            if not action_items_df.empty:
                action_items_df.to_excel(writer, sheet_name='Action Items', index=False)
                
                # Format sheet
                workbook = writer.book
                worksheet = writer.sheets['Action Items']
                
                # Add a format for headers
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Write the column headers with the defined format
                for col_num, value in enumerate(action_items_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Set column widths
                worksheet.set_column('A:F', 15)
                worksheet.set_column('G:G', 50)  # Action Item column wider
        
        # Download button for Excel file
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="Download Complete Excel Report",
            data=excel_data,
            file_name="weekly_reports_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No data available to export.")

def render_json_export(reports):
    """Render JSON export options.
    
    Args:
        reports (list): List of filtered report dictionaries
    """
    st.subheader("JSON Export")
    st.write("Export raw report data as JSON files.")
    
    # Check if we have reports to export
    if not reports:
        st.info("No reports available to export.")
        return
    
    # Create options to filter fields for export
    st.write("Select fields to include in the export:")
    
    # Get all possible fields from reports
    all_fields = set()
    for report in reports:
        all_fields.update(report.keys())
    
    # Common fields to include by default
    common_fields = ['id', 'name', 'reporting_week', 'timestamp', 'current_activities', 
                    'upcoming_activities', 'accomplishments', 'followups', 'nextsteps', 'status']
    
    # Create checkboxes for selecting fields
    selected_fields = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        select_all = st.checkbox("Select All Fields", value=True)
        
        if select_all:
            selected_fields = list(all_fields)
        else:
            # Display checkboxes for common fields
            st.write("Common Fields:")
            for field in common_fields:
                if field in all_fields:
                    if st.checkbox(field, value=True):
                        selected_fields.append(field)
    
    with col2:
        if not select_all:
            # Display checkboxes for other fields
            other_fields = [f for f in all_fields if f not in common_fields]
            if other_fields:
                st.write("Other Fields:")
                for field in other_fields:
                    if st.checkbox(field):
                        selected_fields.append(field)
    
    # Filter reports to include only selected fields
    filtered_reports = []
    for report in reports:
        filtered_report = {field: report.get(field) for field in selected_fields if field in report}
        filtered_reports.append(filtered_report)
    
    # Create JSON string
    json_str = json.dumps(filtered_reports, indent=2)
    
    # Download button
    st.download_button(
        "Download JSON Export",
        data=json_str,
        file_name="weekly_reports_export.json",
        mime="application/json"
    )
    
    # Advanced options
    with st.expander("Advanced JSON Export Options"):
        # Option to export individual JSON files
        st.write("Export individual JSON files for each report:")
        
        # Select reports to export individually
        individual_export = st.checkbox("Enable individual JSON exports")
        
        if individual_export:
            st.write("### Individual JSON Files")
            
            for i, report in enumerate(reports):
                filtered_report = {field: report.get(field) for field in selected_fields if field in report}
                report_name = f"{report.get('name', 'Unknown')} - {report.get('reporting_week', 'Unknown')}"
                
                json_data = json.dumps(filtered_report, indent=2)
                
                st.download_button(
                    f"Download {report_name}",
                    data=json_data,
                    file_name=f"report_{i}.json",
                    mime="application/json",
                    key=f"json_download_{i}"
                )
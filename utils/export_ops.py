# utils/export_ops.py
"""Export operations for the Weekly Report app."""

import streamlit as st
import pandas as pd
import json
import os
import base64
from datetime import datetime
from pathlib import Path
from io import BytesIO

def export_report_as_csv(report_data):
    """Export report data as CSV.
    
    Args:
        report_data (dict): Report data to export
        
    Returns:
        str: Base64 encoded CSV data
    """
    try:
        # Create various dataframes for different sections
        dfs = {}
        
        # Basic info
        basic_info = {
            'Name': [report_data.get('name', '')],
            'Reporting Week': [report_data.get('reporting_week', '')],
            'Created': [report_data.get('timestamp', '').split('T')[0] if report_data.get('timestamp') else ''],
            'Status': [report_data.get('status', 'submitted')]
        }
        dfs['basic_info'] = pd.DataFrame(basic_info)
        
        # Current activities
        if report_data.get('current_activities'):
            current_acts = []
            for act in report_data['current_activities']:
                current_acts.append({
                    'Description': act.get('description', ''),
                    'Project': act.get('project', ''),
                    'Milestone': act.get('milestone', ''),
                    'Priority': act.get('priority', ''),
                    'Status': act.get('status', ''),
                    'Progress': act.get('progress', 0),
                    'Deadline': act.get('deadline', ''),
                    'Customer': act.get('customer', ''),
                    'Billable': act.get('billable', '')
                })
            dfs['current_activities'] = pd.DataFrame(current_acts)
        
        # Upcoming activities
        if report_data.get('upcoming_activities'):
            upcoming_acts = []
            for act in report_data['upcoming_activities']:
                upcoming_acts.append({
                    'Description': act.get('description', ''),
                    'Project': act.get('project', ''),
                    'Milestone': act.get('milestone', ''),
                    'Priority': act.get('priority', ''),
                    'Expected Start': act.get('expected_start', '')
                })
            dfs['upcoming_activities'] = pd.DataFrame(upcoming_acts)
        
        # Accomplishments
        if report_data.get('accomplishments'):
            accomps = []
            for i, acc in enumerate(report_data['accomplishments']):
                if acc:  # Skip empty accomplishments
                    accomps.append({
                        'Number': i + 1,
                        'Accomplishment': acc
                    })
            dfs['accomplishments'] = pd.DataFrame(accomps)
        
        # Action items
        followups = []
        for i, item in enumerate(report_data.get('followups', [])):
            if item:  # Skip empty items
                followups.append({
                    'Number': i + 1,
                    'Follow-up': item,
                    'Type': 'Follow-up'
                })
                
        nextsteps = []
        for i, item in enumerate(report_data.get('nextsteps', [])):
            if item:  # Skip empty items
                nextsteps.append({
                    'Number': i + 1,
                    'Next Step': item,
                    'Type': 'Next Step'
                })
                
        if followups:
            dfs['followups'] = pd.DataFrame(followups)
        if nextsteps:
            dfs['nextsteps'] = pd.DataFrame(nextsteps)
        
        # Optional sections
        from utils.constants import OPTIONAL_SECTIONS
        for section in OPTIONAL_SECTIONS:
            content_key = section['content_key']
            if content_key in report_data and report_data[content_key]:
                section_df = pd.DataFrame({
                    'Section': [section['label']],
                    'Content': [report_data[content_key]]
                })
                dfs[content_key] = section_df
        
        # Create Excel file in memory
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Write each dataframe to a separate sheet
        for sheet_name, df in dfs.items():
            # Clean sheet name
            clean_name = sheet_name.replace('_', ' ').title()
            if len(clean_name) > 31:  # Excel sheet name limit
                clean_name = clean_name[:31]
            
            df.to_excel(writer, sheet_name=clean_name, index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets[clean_name]
            for i, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_len)
        
        writer.close()
        
        # Get the data
        data = output.getvalue()
        
        # Get base64 encoded string
        b64 = base64.b64encode(data).decode()
        
        return b64
    except Exception as e:
        st.error(f"Error exporting report as Excel: {str(e)}")
        return None

def get_csv_download_link(report_data, filename="weekly_report.xlsx"):
    """Generate a download link for CSV export.
    
    Args:
        report_data (dict): Report data to export
        filename (str): Name of the file to download
        
    Returns:
        str: HTML download link
    """
    b64 = export_report_as_csv(report_data)
    if b64:
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel Report</a>'
        return href
    return ""

def export_report_as_html(report_data):
    """Export report data as HTML.
    
    Args:
        report_data (dict): Report data to export
        
    Returns:
        str: HTML content
    """
    try:
        # Basic report info
        name = report_data.get('name', 'Anonymous')
        reporting_week = report_data.get('reporting_week', 'Unknown')
        timestamp = report_data.get('timestamp', '').split('T')[0] if report_data.get('timestamp') else ''
        
        # Start building HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Report - {name} - {reporting_week}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #ddd;
                }}
                .section {{
                    margin-bottom: 30px;
                }}
                .section-title {{
                    background-color: #f5f5f5;
                    padding: 8px 15px;
                    margin-bottom: 15px;
                    border-left: 4px solid #2196F3;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    padding: 12px 15px;
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                th {{
                    background-color: #f5f5f5;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .progress-container {{
                    width: 100%;
                    background-color: #e0e0e0;
                    border-radius: 5px;
                }}
                .progress-bar {{
                    height: 20px;
                    background-color: #4CAF50;
                    border-radius: 5px;
                    text-align: center;
                    color: white;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 50px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #777;
                }}
                .priority-high {{
                    color: #D32F2F;
                    font-weight: bold;
                }}
                .priority-medium {{
                    color: #FF9800;
                }}
                .status-completed {{
                    color: #4CAF50;
                    font-weight: bold;
                }}
                .status-in-progress {{
                    color: #2196F3;
                }}
                .status-blocked {{
                    color: #F44336;
                    font-weight: bold;
                }}
                .list-item {{
                    margin-bottom: 10px;
                    padding-left: 20px;
                    position: relative;
                }}
                .list-item:before {{
                    content: "•";
                    position: absolute;
                    left: 0;
                    color: #2196F3;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Weekly Activity Report</h1>
                <p><strong>{name}</strong> | Week: {reporting_week} | Generated: {timestamp}</p>
            </div>
        """
        
        # Current Activities
        if report_data.get('current_activities'):
            html += """
            <div class="section">
                <h2 class="section-title">📊 Current Activities</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Project</th>
                            <th>Priority</th>
                            <th>Status</th>
                            <th>Progress</th>
                            <th>Deadline</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for activity in report_data['current_activities']:
                # Skip empty activities
                if not activity.get('description'):
                    continue
                    
                # Format priority class
                priority_class = ""
                if activity.get('priority') == 'High':
                    priority_class = "priority-high"
                elif activity.get('priority') == 'Medium':
                    priority_class = "priority-medium"
                
                # Format status class
                status_class = ""
                if activity.get('status') == 'Completed':
                    status_class = "status-completed"
                elif activity.get('status') == 'In Progress':
                    status_class = "status-in-progress"
                elif activity.get('status') == 'Blocked':
                    status_class = "status-blocked"
                
                # Format progress bar
                progress = activity.get('progress', 0)
                progress_bar = f"""
                <div class="progress-container">
                    <div class="progress-bar" style="width: {progress}%">{progress}%</div>
                </div>
                """
                
                html += f"""
                <tr>
                    <td>{activity.get('description', '')}</td>
                    <td>{activity.get('project', '')}</td>
                    <td class="{priority_class}">{activity.get('priority', '')}</td>
                    <td class="{status_class}">{activity.get('status', '')}</td>
                    <td>{progress_bar}</td>
                    <td>{activity.get('deadline', '')}</td>
                </tr>
                """
            
            html += """
                    </tbody>
                </table>
            </div>
            """
        
        # Upcoming Activities
        if report_data.get('upcoming_activities'):
            html += """
            <div class="section">
                <h2 class="section-title">📅 Upcoming Activities</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Project</th>
                            <th>Priority</th>
                            <th>Expected Start</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for activity in report_data['upcoming_activities']:
                # Skip empty activities
                if not activity.get('description'):
                    continue
                    
                # Format priority class
                priority_class = ""
                if activity.get('priority') == 'High':
                    priority_class = "priority-high"
                elif activity.get('priority') == 'Medium':
                    priority_class = "priority-medium"
                
                html += f"""
                <tr>
                    <td>{activity.get('description', '')}</td>
                    <td>{activity.get('project', '')}</td>
                    <td class="{priority_class}">{activity.get('priority', '')}</td>
                    <td>{activity.get('expected_start', '')}</td>
                </tr>
                """
            
            html += """
                    </tbody>
                </table>
            </div>
            """
        
        # Accomplishments
        if report_data.get('accomplishments'):
            html += """
            <div class="section">
                <h2 class="section-title">✓ Last Week's Accomplishments</h2>
                <div>
            """
            
            for accomplishment in report_data['accomplishments']:
                if accomplishment:  # Skip empty accomplishments
                    html += f"""<div class="list-item">{accomplishment}</div>"""
            
            html += """
                </div>
            </div>
            """
        
        # Action Items
        has_followups = bool([f for f in report_data.get('followups', []) if f])
        has_nextsteps = bool([n for n in report_data.get('nextsteps', []) if n])
        
        if has_followups or has_nextsteps:
            html += """
            <div class="section">
                <h2 class="section-title">📋 Action Items</h2>
            """
            
            if has_followups:
                html += """
                <h3>From Last Meeting</h3>
                <div>
                """
                
                for followup in report_data.get('followups', []):
                    if followup:  # Skip empty items
                        html += f"""<div class="list-item">{followup}</div>"""
                
                html += """
                </div>
                """
            
            if has_nextsteps:
                html += """
                <h3>Next Steps</h3>
                <div>
                """
                
                for nextstep in report_data.get('nextsteps', []):
                    if nextstep:  # Skip empty items
                        html += f"""<div class="list-item">{nextstep}</div>"""
                
                html += """
                </div>
                """
            
            html += """
            </div>
            """
        
        # Optional Sections
        from utils.constants import OPTIONAL_SECTIONS
        for section in OPTIONAL_SECTIONS:
            content_key = section['content_key']
            if content_key in report_data and report_data[content_key]:
                html += f"""
                <div class="section">
                    <h2 class="section-title">{section['icon']} {section['label']}</h2>
                    <p>{report_data[content_key]}</p>
                </div>
                """
        
        # Footer
        html += f"""
            <div class="footer">
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        st.error(f"Error exporting report as HTML: {str(e)}")
        return None

def get_html_download_link(report_data, filename="weekly_report.html"):
    """Generate a download link for HTML export.
    
    Args:
        report_data (dict): Report data to export
        filename (str): Name of the file to download
        
    Returns:
        str: HTML download link
    """
    html = export_report_as_html(report_data)
    if html:
        b64 = base64.b64encode(html.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="{filename}">Download HTML Report</a>'
        return href
    return ""

def export_report_as_email(report_data):
    """Format report data as an email body.
    
    Args:
        report_data (dict): Report data to export
        
    Returns:
        str: Email body content
    """
    try:
        # Basic report info
        name = report_data.get('name', 'Anonymous')
        reporting_week = report_data.get('reporting_week', 'Unknown')
        
        # Start building email body
        email = f"""
Weekly Activity Report - {name} - {reporting_week}

Hi team,

Here's my weekly activity report for {reporting_week}:

"""
        
        # Accomplishments
        if report_data.get('accomplishments'):
            email += "\n**ACCOMPLISHMENTS:**\n"
            for accomplishment in report_data['accomplishments']:
                if accomplishment:  # Skip empty accomplishments
                    email += f"- {accomplishment}\n"
        
        # Current Activities
        if report_data.get('current_activities'):
            email += "\n**CURRENT ACTIVITIES:**\n"
            for activity in report_data['current_activities']:
                if activity.get('description'):  # Skip empty activities
                    email += f"- {activity.get('description')}"
                    
                    # Add project if available
                    if activity.get('project'):
                        email += f" (Project: {activity.get('project')}"
                        
                        # Add status if available
                        if activity.get('status'):
                            email += f", Status: {activity.get('status')}"
                            
                        # Add progress if available
                        if 'progress' in activity:
                            email += f", {activity.get('progress')}% complete"
                            
                        email += ")"
                    
                    email += "\n"
        
        # Upcoming Activities
        if report_data.get('upcoming_activities'):
            email += "\n**UPCOMING ACTIVITIES:**\n"
            for activity in report_data['upcoming_activities']:
                if activity.get('description'):  # Skip empty activities
                    email += f"- {activity.get('description')}"
                    
                    # Add project if available
                    if activity.get('project'):
                        email += f" (Project: {activity.get('project')}"
                        
                        # Add priority if available
                        if activity.get('priority'):
                            email += f", Priority: {activity.get('priority')}"
                            
                        # Add expected start if available
                        if activity.get('expected_start'):
                            email += f", Starting: {activity.get('expected_start')}"
                            
                        email += ")"
                    
                    email += "\n"
        
        # Action Items
        has_followups = bool([f for f in report_data.get('followups', []) if f])
        has_nextsteps = bool([n for n in report_data.get('nextsteps', []) if n])
        
        if has_followups or has_nextsteps:
            email += "\n**ACTION ITEMS:**\n"
            
            if has_followups:
                email += "\nFollow-ups from last meeting:\n"
                for followup in report_data.get('followups', []):
                    if followup:  # Skip empty items
                        email += f"- {followup}\n"
            
            if has_nextsteps:
                email += "\nNext steps:\n"
                for nextstep in report_data.get('nextsteps', []):
                    if nextstep:  # Skip empty items
                        email += f"- {nextstep}\n"
        
        # Optional Sections
        from utils.constants import OPTIONAL_SECTIONS
        for section in OPTIONAL_SECTIONS:
            content_key = section['content_key']
            if content_key in report_data and report_data[content_key]:
                email += f"\n**{section['label'].upper()}:**\n"
                email += f"{report_data[content_key]}\n"
        
        # Signature
        email += f"""
Best regards,
{name}
"""
        
        return email
    except Exception as e:
        st.error(f"Error formatting report as email: {str(e)}")
        return None

def get_email_copy_button(report_data):
    """Generate a copy to clipboard button for email export.
    
    Args:
        report_data (dict): Report data to export
        
    Returns:
        str: HTML button with JavaScript to copy email content
    """
    email = export_report_as_email(report_data)
    if email:
        # Escape quotes and newlines for JavaScript
        email_js = email.replace('\n', '\\n').replace('"', '\\"')
        
        html = f"""
        <button onclick="copyToClipboard()" style="background-color: #4CAF50; border: none; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 4px;">Copy Email Content</button>
        <div id="copyStatus" style="display: none; margin-top: 5px; padding: 5px; background-color: #f1f1f1; border-radius: 3px;"></div>
        <script>
        function copyToClipboard() {{
            const text = "{email_js}";
            navigator.clipboard.writeText(text).then(function() {{
                const status = document.getElementById('copyStatus');
                status.textContent = '✓ Email content copied to clipboard!';
                status.style.display = 'block';
                status.style.backgroundColor = '#dff0d8';
                status.style.color = '#3c763d';
                setTimeout(function() {{
                    status.style.display = 'none';
                }}, 3000);
            }}, function(err) {{
                const status = document.getElementById('copyStatus');
                status.textContent = '❌ Failed to copy: ' + err;
                status.style.display = 'block';
                status.style.backgroundColor = '#f2dede';
                status.style.color = '#a94442';
            }});
        }}
        </script>
        """
        return html
    return ""
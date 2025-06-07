# utils/pdf_export.py
"""PDF export utilities for the Weekly Report app."""

import os
from fpdf import FPDF
import tempfile
import streamlit as st
from datetime import datetime
from pathlib import Path
import json

class ReportPDF(FPDF):
    """Custom PDF class for report formatting that uses standard fonts."""
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.set_auto_page_break(auto=True, margin=15)
        # Use standard fonts instead of DejaVu
        self.set_font('Arial', '', 10)
        
    def header(self):
        """Add header to pages."""
        self.set_font('Arial', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, 'Weekly Activity Report', 0, 0, 'C')
        # Line break
        self.ln(20)
        
    def footer(self):
        """Add footer to pages."""
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')
        
    def chapter_title(self, title):
        """Add a chapter title."""
        self.set_font('Arial', 'B', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 8, title, 0, 1, 'L', 1)
        # Line break
        self.ln(4)
        
    def chapter_body(self, body):
        """Add chapter body."""
        self.set_font('Arial', '', 10)
        # Output justified text with proper text handling
        if body is not None and isinstance(body, str) and body.strip():
            # Split long text into smaller chunks to prevent layout issues
            max_line_length = 90
            lines = []
            words = body.split()
            current_line = ""
            
            for word in words:
                if len(current_line + " " + word) <= max_line_length:
                    current_line += " " + word if current_line else word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Output each line
            for line in lines:
                self.multi_cell(0, 5, line)
                
        # Line break
        self.ln()
        
    def section_title(self, title):
        """Add a section title."""
        self.set_font('Arial', 'B', 11)
        # Title with proper text handling
        if title is None:
            title = "Untitled"
        
        # Limit title length to prevent layout issues
        if len(title) > 100:
            title = title[:97] + "..."
        
        self.multi_cell(0, 6, title, 'B', 'L')
        self.ln(2)
        
    def add_progress_bar(self, progress, width=50):
        """Add a progress bar to the PDF."""
        try:
            progress = int(progress)
        except (ValueError, TypeError):
            progress = 0
            
        progress = max(0, min(100, progress))
        
        # Store current position
        x, y = self.get_x(), self.get_y()
        
        # Draw progress bar container
        self.set_draw_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)
        self.rect(x, y, width, 5, 'DF')
        
        # Draw progress fill
        if progress > 0:
            if progress <= 30:
                self.set_fill_color(255, 0, 0)
            elif progress <= 70:
                self.set_fill_color(255, 165, 0)
            else:
                self.set_fill_color(34, 139, 34)
                
            progress_width = (progress / 100) * width
            self.rect(x, y, progress_width, 5, 'F')
        
        # Add percentage text
        self.set_xy(x + width + 2, y)
        self.set_font('Arial', '', 8)
        self.cell(10, 5, f"{progress}%")
        
        # Reset position below the progress bar
        self.set_xy(x, y + 7)
        
    def add_text_with_label(self, label, text, bold_label=True):
        """Add text with a label."""
        if bold_label:
            self.set_font('Arial', 'B', 10)
        else:
            self.set_font('Arial', '', 10)
            
        self.cell(30, 5, label)
        self.set_font('Arial', '', 10)
        
        # Ensure text is a string and handle long text
        if not isinstance(text, str):
            text = str(text)
        
        # Limit text length to prevent layout issues
        if len(text) > 200:
            text = text[:197] + "..."
        
        remaining_width = self.w - self.r_margin - self.l_margin - 30
        self.multi_cell(remaining_width, 5, text)
        
    def add_list_item(self, text, indent=0, bullet='-'):
        """Add a list item."""
        self.set_x(self.get_x() + indent)
        self.set_font('Arial', '', 10)
        self.cell(5, 5, bullet)
        
        # Ensure text is a string and handle long text
        if not isinstance(text, str):
            text = str(text)
        
        # Limit text length and handle line breaks
        if len(text) > 150:
            text = text[:147] + "..."
        
        remaining_width = self.w - self.r_margin - self.x
        self.multi_cell(remaining_width, 5, text)

def clean_text_for_pdf(text):
    """Clean text to remove problematic unicode characters and ensure proper encoding."""
    if not isinstance(text, str):
        text = str(text)
    
    # Replace problematic unicode characters
    replacements = {
        '\u2019': "'",  # Right single quotation mark
        '\u2018': "'",  # Left single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2026': '...', # Horizontal ellipsis
        '\u00a0': ' ',  # Non-breaking space
        '\u2022': '•',  # Bullet point
    }
    
    for old_char, new_char in replacements.items():
        text = text.replace(old_char, new_char)
    
    # Remove any remaining non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Remove extra whitespace and line breaks that might cause issues
    text = ' '.join(text.split())
    
    return text

def extract_text_from_item(item):
    """Extract text content from an item that might be JSON or plain text."""
    if not item:
        return ""
    
    if isinstance(item, str):
        # Try to parse as JSON first
        try:
            json_data = json.loads(item)
            if isinstance(json_data, dict) and 'text' in json_data:
                return json_data['text']
            else:
                return item
        except (json.JSONDecodeError, TypeError):
            return item
    
    return str(item)

def export_report_to_pdf(report_data):
    """Export a report to PDF with improved error handling and layout."""
    try:
        # Ensure report_data is a dictionary
        if not isinstance(report_data, dict):
            report_data = {}
        
        # Create a temporary directory to store the PDF
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"report_{report_data.get('id', 'unknown')}.pdf")
        
        # Initialize PDF instance
        pdf = ReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Report metadata
        pdf.set_font('Arial', '', 12)
        
        # Clean all text fields
        clean_name = clean_text_for_pdf(report_data.get('name', 'Anonymous'))
        clean_week = clean_text_for_pdf(report_data.get('reporting_week', 'Unknown'))
        
        pdf.cell(0, 10, f"Name: {clean_name}", 0, 1)
        pdf.cell(0, 10, f"Week: {clean_week}", 0, 1)
        
        # Safely extract timestamp
        timestamp = report_data.get('timestamp', '')
        if timestamp and isinstance(timestamp, str) and len(timestamp) >= 10:
            pdf.cell(0, 10, f"Date: {timestamp[:10]}", 0, 1)
        else:
            pdf.cell(0, 10, f"Date: Unknown", 0, 1)
            
        pdf.ln(5)
        
        # Current activities
        current_activities = report_data.get('current_activities', [])
        if current_activities and isinstance(current_activities, list) and len(current_activities) > 0:
            pdf.chapter_title("Current Activities")
            
            for activity in current_activities:
                if not isinstance(activity, dict):
                    continue
                    
                activity_description = clean_text_for_pdf(activity.get('description', 'No description'))
                pdf.section_title(activity_description)
                
                # Project and milestone
                project_text = clean_text_for_pdf(activity.get('project', 'No project'))
                if activity.get('milestone'):
                    milestone_text = clean_text_for_pdf(activity.get('milestone'))
                    project_text += f" / {milestone_text}"
                pdf.add_text_with_label("Project:", project_text)
                
                # Status and priority
                status = clean_text_for_pdf(activity.get('status', 'Unknown'))
                priority = clean_text_for_pdf(activity.get('priority', 'Medium'))
                deadline = clean_text_for_pdf(activity.get('deadline', ''))
                
                status_line = f"Status: {status} | Priority: {priority}"
                if deadline:
                    status_line += f" | Deadline: {deadline}"
                
                pdf.multi_cell(0, 5, status_line, 0, 'L')
                
                # Progress bar
                pdf.cell(0, 5, "Progress:", 0, 1)
                try:
                    progress = int(activity.get('progress', 0))
                except (ValueError, TypeError):
                    progress = 0
                pdf.add_progress_bar(progress)
                
                # Customer and billable
                customer = clean_text_for_pdf(activity.get('customer', ''))
                billable = clean_text_for_pdf(activity.get('billable', ''))
                
                if customer:
                    pdf.cell(0, 5, f"Customer: {customer}", 0, 1)
                if billable:
                    pdf.cell(0, 5, f"Billable: {billable}", 0, 1)
                    
                pdf.ln(3)
        
        # Upcoming activities
        upcoming_activities = report_data.get('upcoming_activities', [])
        if upcoming_activities and isinstance(upcoming_activities, list) and len(upcoming_activities) > 0:
            pdf.chapter_title("Upcoming Activities")
            
            for activity in upcoming_activities:
                if not isinstance(activity, dict):
                    continue
                    
                activity_description = clean_text_for_pdf(activity.get('description', 'No description'))
                pdf.section_title(activity_description)
                
                # Project and milestone
                project_text = clean_text_for_pdf(activity.get('project', 'No project'))
                if activity.get('milestone'):
                    milestone_text = clean_text_for_pdf(activity.get('milestone'))
                    project_text += f" / {milestone_text}"
                pdf.add_text_with_label("Project:", project_text)
                
                # Priority and start date
                priority = clean_text_for_pdf(activity.get('priority', 'Medium'))
                expected_start = clean_text_for_pdf(activity.get('expected_start', ''))
                
                pdf.multi_cell(0, 5, f"Priority: {priority}", 0, 'L')
                if expected_start:
                    pdf.multi_cell(0, 5, f"Expected Start: {expected_start}", 0, 'L')
                    
                pdf.ln(3)
        
        # Accomplishments
        accomplishments = report_data.get('accomplishments', [])
        if accomplishments and isinstance(accomplishments, list) and len(accomplishments) > 0:
            pdf.chapter_title("Last Week's Accomplishments")
            
            for accomplishment in accomplishments:
                accomplishment_text = extract_text_from_item(accomplishment)
                accomplishment_text = clean_text_for_pdf(accomplishment_text)
                
                if accomplishment_text and accomplishment_text.strip().lower() not in ['nan', 'none', '']:
                    pdf.add_list_item(accomplishment_text)
            
            pdf.ln(3)
        
        # Action items
        followups = report_data.get('followups', [])
        nextsteps = report_data.get('nextsteps', [])
        
        # Filter out empty followups and nextsteps
        valid_followups = []
        for followup in followups:
            followup_text = extract_text_from_item(followup)
            followup_text = clean_text_for_pdf(followup_text)
            if followup_text and followup_text.strip().lower() not in ['nan', 'none', '']:
                valid_followups.append(followup_text)
        
        valid_nextsteps = []
        for nextstep in nextsteps:
            nextstep_text = extract_text_from_item(nextstep)
            nextstep_text = clean_text_for_pdf(nextstep_text)
            if nextstep_text and nextstep_text.strip().lower() not in ['nan', 'none', '']:
                valid_nextsteps.append(nextstep_text)
        
        if valid_followups or valid_nextsteps:
            pdf.chapter_title("Action Items")
            
            # Follow-ups
            if valid_followups:
                pdf.section_title("From Last Meeting")
                for followup_text in valid_followups:
                    pdf.add_list_item(followup_text)
                pdf.ln(3)
            
            # Next steps
            if valid_nextsteps:
                pdf.section_title("Next Steps")
                for nextstep_text in valid_nextsteps:
                    pdf.add_list_item(nextstep_text)
                pdf.ln(3)
        
        # Optional sections
        optional_sections = [
            {'key': 'challenges', 'title': 'Challenges & Assistance'},
            {'key': 'slow_projects', 'title': 'Slow-Moving Projects'},
            {'key': 'other_topics', 'title': 'Other Discussion Topics'},
            {'key': 'key_accomplishments', 'title': 'Key Accomplishments'},
            {'key': 'concerns', 'title': 'Concerns'}
        ]
        
        for section in optional_sections:
            key = section['key']
            if key in report_data:
                value = report_data[key]
                if value and isinstance(value, str) and value.strip().lower() not in ['nan', 'none', '']:
                    clean_value = clean_text_for_pdf(value)
                    if clean_value.strip():
                        pdf.chapter_title(section['title'])
                        pdf.chapter_body(clean_value)
        
        # Output the PDF to a file
        pdf.output(file_path, 'F')
        
        return file_path
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        # Create a simple error PDF instead of failing completely
        try:
            pdf = ReportPDF()
            pdf.add_page()
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, "Error generating detailed PDF report", 0, 1)
            pdf.cell(0, 10, f"Error: {str(e)}", 0, 1)
            pdf.cell(0, 10, f"Report ID: {report_data.get('id', 'unknown')}", 0, 1)
            pdf.output(file_path, 'F')
            return file_path
        except:
            raise e

def export_objective_to_pdf(objective_data):
    """Export an objective to PDF."""
    try:
        if not isinstance(objective_data, dict):
            objective_data = {}
            
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"objective_{objective_data.get('id', 'unknown')}.pdf")
        
        pdf = ReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        pdf.set_font('Arial', '', 12)
        title = clean_text_for_pdf(objective_data.get('title', 'Untitled Objective'))
        pdf.multi_cell(0, 10, title, 0, 'C')
        pdf.ln(5)
        
        pdf.multi_cell(0, 10, f"Level: {objective_data.get('level', 'unknown').capitalize()}", 0, 'L')
        
        if objective_data.get('level') == 'team':
            team_name = clean_text_for_pdf(objective_data.get('team', 'Unassigned'))
            pdf.multi_cell(0, 10, f"Team: {team_name}", 0, 'L')
        
        owner_name = clean_text_for_pdf(objective_data.get('owner_name', 'Unassigned'))
        period = clean_text_for_pdf(objective_data.get('period', 'Unknown'))
        status = clean_text_for_pdf(objective_data.get('status', 'Unknown'))
        
        pdf.multi_cell(0, 10, f"Owner: {owner_name}", 0, 'L')
        pdf.multi_cell(0, 10, f"Period: {period}", 0, 'L')
        pdf.multi_cell(0, 10, f"Status: {status}", 0, 'L')
        pdf.ln(5)
        
        # Description
        if 'description' in objective_data and objective_data['description']:
            description = clean_text_for_pdf(objective_data['description'])
            if description.strip():
                pdf.chapter_title("Description")
                pdf.chapter_body(description)
        
        # Key Results
        key_results = objective_data.get('key_results', [])
        if key_results and isinstance(key_results, list) and len(key_results) > 0:
            pdf.chapter_title("Key Results")
            
            for i, kr in enumerate(key_results):
                if not isinstance(kr, dict):
                    continue
                    
                try:
                    progress = int(kr.get('progress', 0))
                except (ValueError, TypeError):
                    progress = 0
                
                kr_description = clean_text_for_pdf(kr.get('description', 'No description'))
                pdf.section_title(f"KR{i+1}: {kr_description}")
                pdf.cell(30, 5, "Progress:")
                pdf.add_progress_bar(progress)
                
                updates = kr.get('updates', [])
                if updates and isinstance(updates, list) and len(updates) > 0:
                    pdf.section_title("Recent Updates")
                    
                    recent_updates = updates[-min(3, len(updates)):]
                    
                    for update in recent_updates:
                        if not isinstance(update, dict):
                            continue
                            
                        update_date = clean_text_for_pdf(update.get('date', ''))
                        previous = update.get('previous', 0)
                        current = update.get('current', 0)
                        note = clean_text_for_pdf(update.get('note', ''))
                        
                        update_text = f"{update_date}: {previous}% -> {current}%"
                        if note:
                            update_text += f"\n{note}"
                        
                        pdf.add_list_item(update_text)
                    
                    pdf.ln(3)
        
        # Last updated
        if 'last_updated' in objective_data:
            last_updated = objective_data['last_updated']
            if last_updated and isinstance(last_updated, str) and len(last_updated) >= 10:
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 10, f"Last Updated: {last_updated[:10]}", 0, 1)
        
        pdf.output(file_path, 'F')
        return file_path
        
    except Exception as e:
        st.error(f"Error generating objective PDF: {str(e)}")
        raise e
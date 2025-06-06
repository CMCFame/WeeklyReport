# utils/pdf_export.py
"""PDF export utilities for the Weekly Report app."""

import os
from fpdf import FPDF
import tempfile
import streamlit as st
from datetime import datetime
from pathlib import Path

class ReportPDF(FPDF):
    """Custom PDF class for report formatting that uses standard fonts."""
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.set_auto_page_break(auto=True, margin=15)
        # Use standard fonts instead of DejaVu
        self.set_font('Arial', '', 10)
        
    def header(self):
        """Add header to pages."""
        # Logo
        # self.image('logo.png', 10, 8, 33)
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
        self.cell(0, 6, title, 0, 1, 'L', 1)
        # Line break
        self.ln(4)
        
    def chapter_body(self, body):
        """Add chapter body."""
        self.set_font('Arial', '', 10)
        # Output justified text
        if body is not None and isinstance(body, str):
            self.multi_cell(0, 5, body)
        else:
            self.multi_cell(0, 5, "")  # Add empty text if body is invalid
        # Line break
        self.ln()
        
    def section_title(self, title):
        """Add a section title."""
        self.set_font('Arial', 'B', 11)
        # Title
        if title is None:
            title = "Untitled"
        
        # Use multi_cell instead of cell for section titles to enable wrapping
        self.multi_cell(0, 6, title, 'B', 'L')
        # Line break
        self.ln(4)
        
    def add_progress_bar(self, progress, width=50):
        """Add a progress bar to the PDF.
        
        Args:
            progress (int): Progress value (0-100)
            width (int): Width of the progress bar in mm
        """
        # Ensure progress is a number
        try:
            progress = int(progress)
        except (ValueError, TypeError):
            progress = 0  # Default to 0 if conversion fails
            
        # Ensure progress is within valid range
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
                self.set_fill_color(255, 0, 0)  # Red for low progress
            elif progress <= 70:
                self.set_fill_color(255, 165, 0)  # Orange for medium progress
            else:
                self.set_fill_color(34, 139, 34)  # Green for high progress
                
            progress_width = (progress / 100) * width
            self.rect(x, y, progress_width, 5, 'F')
        
        # Add percentage text
        self.set_xy(x + width + 2, y)
        self.set_font('Arial', '', 8)
        self.cell(10, 5, f"{progress}%")
        
        # Reset position below the progress bar
        self.set_xy(x, y + 7)
        
    def add_text_with_label(self, label, text, bold_label=True):
        """Add text with a label.
        
        Args:
            label (str): Label text
            text (str): Main text
            bold_label (bool): Whether to make the label bold
        """
        if bold_label:
            self.set_font('Arial', 'B', 10)
        else:
            self.set_font('Arial', '', 10)
            
        self.cell(30, 5, label)
        self.set_font('Arial', '', 10)
        
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
        
        # Use multi_cell instead of cell for main text to enable wrapping
        remaining_width = self.w - self.r_margin - self.l_margin - 30
        current_x = self.x
        self.multi_cell(remaining_width, 5, text)
        
    def add_list_item(self, text, indent=0, bullet='-'):  # Changed bullet to '-' character
        """Add a list item.
        
        Args:
            text (str): Item text
            indent (int): Indentation level in mm
            bullet (str): Bullet character to use
        """
        self.set_x(self.get_x() + indent)
        self.set_font('Arial', '', 10)
        self.cell(5, 5, bullet)
        
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
        
        # Calculate remaining width for the text
        remaining_width = self.w - self.r_margin - self.x
        # Use multi_cell with calculated width to enable wrapping
        self.multi_cell(remaining_width, 5, text)

def export_report_to_pdf(report_data):
    """Export a report to PDF with proper unicode handling."""
    try:
        # Ensure report_data is a dictionary
        if not isinstance(report_data, dict):
            report_data = {}
        
        # Helper function to clean text for PDF output
        def clean_text_for_pdf(text):
            """Clean text to remove problematic unicode characters."""
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
            }
            
            for old_char, new_char in replacements.items():
                text = text.replace(old_char, new_char)
            
            # Remove any remaining non-ASCII characters
            text = text.encode('ascii', 'ignore').decode('ascii')
            
            return text
            
        # Create a temporary directory to store the PDF
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"report_{report_data.get('id', 'unknown')}.pdf")
        
        # Initialize PDF instance
        pdf = ReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Report metadata (removed duplicate header)
        pdf.set_font('Arial', '', 12)
        
        # Clean all text fields
        clean_name = clean_text_for_pdf(report_data.get('name', 'Anonymous'))
        clean_week = clean_text_for_pdf(report_data.get('reporting_week', 'Unknown'))
        
        pdf.cell(0, 10, f"Name: {clean_name}", 0, 1)
        pdf.cell(0, 10, f"Week: {clean_week}", 0, 1)
        
        # Safely extract timestamp - fix potential index error
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
                if not isinstance(activity, dict):  # Skip if not a dictionary
                    continue
                    
                activity_description = clean_text_for_pdf(activity.get('description', 'No description'))
                pdf.section_title(activity_description)
                
                # Project and milestone
                project_text = clean_text_for_pdf(activity.get('project', 'No project'))
                if activity.get('milestone'):
                    project_text += f" / {clean_text_for_pdf(activity.get('milestone'))}"
                pdf.add_text_with_label("Project:", project_text)
                
                # Status and priority
                status = clean_text_for_pdf(activity.get('status', 'Unknown'))
                priority = clean_text_for_pdf(activity.get('priority', 'Medium'))
                deadline = clean_text_for_pdf(activity.get('deadline', ''))
                
                status_line = f"Status: {status} | Priority: {priority}"
                if deadline:
                    status_line += f" | Deadline: {deadline}"
                
                # Use multi_cell instead of cell for status_line to enable wrapping
                pdf.multi_cell(0, 5, status_line, 0, 'L')
                
                # Progress bar
                pdf.cell(0, 5, "Progress:", 0, 1)
                try:
                    progress = int(activity.get('progress', 0))
                except (ValueError, TypeError):
                    progress = 0  # Default to 0 if conversion fails
                pdf.add_progress_bar(progress)
                
                # Customer and billable
                customer = clean_text_for_pdf(activity.get('customer', ''))
                billable = clean_text_for_pdf(activity.get('billable', ''))
                
                if customer:
                    pdf.cell(0, 5, f"Customer: {customer}", 0, 1)
                if billable:
                    pdf.cell(0, 5, f"Billable: {billable}", 0, 1)
                    
                pdf.ln(5)
        
        # Upcoming activities
        upcoming_activities = report_data.get('upcoming_activities', [])
        if upcoming_activities and isinstance(upcoming_activities, list) and len(upcoming_activities) > 0:
            pdf.chapter_title("Upcoming Activities")
            
            for activity in upcoming_activities:
                if not isinstance(activity, dict):  # Skip if not a dictionary
                    continue
                    
                activity_description = clean_text_for_pdf(activity.get('description', 'No description'))
                pdf.section_title(activity_description)
                
                # Project and milestone
                project_text = clean_text_for_pdf(activity.get('project', 'No project'))
                if activity.get('milestone'):
                    project_text += f" / {clean_text_for_pdf(activity.get('milestone'))}"
                pdf.add_text_with_label("Project:", project_text)
                
                # Priority and start date - use multi_cell for better text wrapping
                priority = clean_text_for_pdf(activity.get('priority', 'Medium'))
                expected_start = clean_text_for_pdf(activity.get('expected_start', ''))
                
                pdf.multi_cell(0, 5, f"Priority: {priority}", 0, 'L')
                if expected_start:
                    pdf.multi_cell(0, 5, f"Expected Start: {expected_start}", 0, 'L')
                    
                pdf.ln(5)
        
        # Accomplishments
        accomplishments = report_data.get('accomplishments', [])
        if accomplishments and isinstance(accomplishments, list) and len(accomplishments) > 0:
            pdf.chapter_title("Last Week's Accomplishments")
            
            for accomplishment in accomplishments:
                # Check if the accomplishment is a string or potentially JSON data
                if isinstance(accomplishment, str):
                    # Try to parse as JSON in case it's stored as JSON string
                    try:
                        import json
                        json_data = json.loads(accomplishment)
                        if isinstance(json_data, dict) and 'text' in json_data:
                            accomplishment_text = json_data['text']
                        else:
                            accomplishment_text = accomplishment
                    except:
                        accomplishment_text = accomplishment
                        
                    accomplishment_text = clean_text_for_pdf(accomplishment_text)
                    if accomplishment_text and accomplishment_text.strip().lower() != "nan":  # Skip empty strings or "nan"
                        pdf.add_list_item(accomplishment_text)
            
            pdf.ln(5)
        
        # Action items
        followups = report_data.get('followups', [])
        nextsteps = report_data.get('nextsteps', [])
        
        if (followups and isinstance(followups, list) and len(followups) > 0) or \
           (nextsteps and isinstance(nextsteps, list) and len(nextsteps) > 0):
            pdf.chapter_title("Action Items")
            
            # Follow-ups
            if followups and isinstance(followups, list) and len(followups) > 0:
                pdf.section_title("From Last Meeting")
                
                for followup in followups:
                    # Check if the followup is a string or potentially JSON data
                    if isinstance(followup, str):
                        # Try to parse as JSON in case it's stored as JSON string
                        try:
                            import json
                            json_data = json.loads(followup)
                            if isinstance(json_data, dict) and 'text' in json_data:
                                followup_text = json_data['text']
                            else:
                                followup_text = followup
                        except:
                            followup_text = followup
                            
                        followup_text = clean_text_for_pdf(followup_text)
                        if followup_text and followup_text.strip().lower() != "nan":  # Skip empty strings or "nan"
                            pdf.add_list_item(followup_text)
                
                pdf.ln(5)
            
            # Next steps
            if nextsteps and isinstance(nextsteps, list) and len(nextsteps) > 0:
                pdf.section_title("Next Steps")
                
                for nextstep in nextsteps:
                    # Check if the nextstep is a string or potentially JSON data
                    if isinstance(nextstep, str):
                        # Try to parse as JSON in case it's stored as JSON string
                        try:
                            import json
                            json_data = json.loads(nextstep)
                            if isinstance(json_data, dict) and 'text' in json_data:
                                nextstep_text = json_data['text']
                            else:
                                nextstep_text = nextstep
                        except:
                            nextstep_text = nextstep
                            
                        nextstep_text = clean_text_for_pdf(nextstep_text)
                        if nextstep_text and nextstep_text.strip().lower() != "nan":  # Skip empty strings or "nan"
                            pdf.add_list_item(nextstep_text)
                
                pdf.ln(5)
        
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
                # Check if the value is valid
                value = report_data[key]
                if value and isinstance(value, str) and value.strip().lower() != 'nan':
                    clean_value = clean_text_for_pdf(value)
                    pdf.chapter_title(section['title'])
                    pdf.chapter_body(clean_value)
                    pdf.ln(5)
        
        # Output the PDF to a file
        pdf.output(file_path, 'F')
        
        return file_path
    except Exception as e:
        # Log the detailed error for debugging
        st.error(f"Error generating PDF: {str(e)}")
        raise e

def export_objective_to_pdf(objective_data):
    """Export an objective to PDF.
    
    Args:
        objective_data (dict): Objective data to export
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Ensure objective_data is a dictionary
        if not isinstance(objective_data, dict):
            objective_data = {}
            
        # Create a temporary directory to store the PDF
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"objective_{objective_data.get('id', 'unknown')}.pdf")
        
        # Initialize PDF instance
        pdf = ReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Objective metadata (no need for duplicate header)
        pdf.set_font('Arial', '', 12)
        title = objective_data.get('title', 'Untitled Objective')
        pdf.multi_cell(0, 10, title, 0, 'C')
        pdf.ln(5)
        
        pdf.multi_cell(0, 10, f"Level: {objective_data.get('level', 'unknown').capitalize()}", 0, 'L')
        
        if objective_data.get('level') == 'team':
            pdf.multi_cell(0, 10, f"Team: {objective_data.get('team', 'Unassigned')}", 0, 'L')
        
        pdf.multi_cell(0, 10, f"Owner: {objective_data.get('owner_name', 'Unassigned')}", 0, 'L')
        pdf.multi_cell(0, 10, f"Period: {objective_data.get('period', 'Unknown')}", 0, 'L')
        pdf.multi_cell(0, 10, f"Status: {objective_data.get('status', 'Unknown')}", 0, 'L')
        pdf.ln(5)
        
        # Description
        if 'description' in objective_data and objective_data['description'] and isinstance(objective_data['description'], str):
            pdf.chapter_title("Description")
            pdf.chapter_body(objective_data['description'])
            pdf.ln(5)
        
        # Key Results
        key_results = objective_data.get('key_results', [])
        if key_results and isinstance(key_results, list) and len(key_results) > 0:
            pdf.chapter_title("Key Results")
            
            for i, kr in enumerate(key_results):
                if not isinstance(kr, dict):  # Skip if not a dictionary
                    continue
                    
                # Get progress
                try:
                    progress = int(kr.get('progress', 0))
                except (ValueError, TypeError):
                    progress = 0  # Default to 0 if conversion fails
                
                # Key result title and progress
                kr_description = kr.get('description', 'No description')
                pdf.section_title(f"KR{i+1}: {kr_description}")
                pdf.cell(30, 5, "Progress:")
                pdf.add_progress_bar(progress)
                
                # Updates
                updates = kr.get('updates', [])
                if updates and isinstance(updates, list) and len(updates) > 0:
                    pdf.section_title("Recent Updates")
                    
                    # Get last 3 updates or fewer if there aren't 3
                    recent_updates = updates[-min(3, len(updates)):]
                    
                    for update in recent_updates:
                        if not isinstance(update, dict):  # Skip if not a dictionary
                            continue
                            
                        # Format update info
                        update_date = update.get('date', '')
                        previous = update.get('previous', 0)
                        current = update.get('current', 0)
                        note = update.get('note', '')
                        
                        # Replace Unicode arrow with standard ASCII
                        update_text = f"{update_date}: {previous}% -> {current}%"
                        if note:
                            update_text += f"\n{note}"
                        
                        pdf.add_list_item(update_text)
                    
                    pdf.ln(5)
        
        # Last updated
        if 'last_updated' in objective_data:
            last_updated = objective_data['last_updated']
            if last_updated and isinstance(last_updated, str) and len(last_updated) >= 10:
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 10, f"Last Updated: {last_updated[:10]}", 0, 1)
        
        # Output the PDF to a file
        pdf.output(file_path, 'F')
        
        return file_path
    except Exception as e:
        # Log the detailed error for debugging
        st.error(f"Error generating objective PDF: {str(e)}")
        raise e
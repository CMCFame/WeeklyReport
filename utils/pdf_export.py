# utils/pdf_export.py
"""PDF export utilities for the Weekly Report app."""

import os
from fpdf import FPDF
import tempfile
import streamlit as st
from datetime import datetime
from pathlib import Path

class ReportPDF(FPDF):
    """Custom PDF class for report formatting."""
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font('DejaVu', '', 'utils/fonts/DejaVuSansCondensed.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'utils/fonts/DejaVuSansCondensed-Bold.ttf', uni=True)
        self.add_font('DejaVu', 'I', 'utils/fonts/DejaVuSansCondensed-Oblique.ttf', uni=True)
        
    def header(self):
        """Add header to pages."""
        # Logo
        # self.image('logo.png', 10, 8, 33)
        # Arial bold 15
        self.set_font('DejaVu', 'B', 15)
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
        # Arial italic 8
        self.set_font('DejaVu', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')
        
    def chapter_title(self, title):
        """Add a chapter title."""
        # Arial 12
        self.set_font('DejaVu', 'B', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, title, 0, 1, 'L', 1)
        # Line break
        self.ln(4)
        
    def chapter_body(self, body):
        """Add chapter body."""
        # Times 12
        self.set_font('DejaVu', '', 10)
        # Output justified text
        self.multi_cell(0, 5, body)
        # Line break
        self.ln()
        
    def section_title(self, title):
        """Add a section title."""
        # Arial 12
        self.set_font('DejaVu', 'B', 11)
        # Title
        self.cell(0, 6, title, 'B', 1, 'L')
        # Line break
        self.ln(4)
        
    def add_progress_bar(self, progress, width=50):
        """Add a progress bar to the PDF.
        
        Args:
            progress (int): Progress value (0-100)
            width (int): Width of the progress bar in mm
        """
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
        self.set_font('DejaVu', '', 8)
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
            self.set_font('DejaVu', 'B', 10)
        else:
            self.set_font('DejaVu', '', 10)
            
        self.cell(30, 5, label)
        self.set_font('DejaVu', '', 10)
        self.multi_cell(0, 5, text)
        
    def add_list_item(self, text, indent=0, bullet='•'):
        """Add a list item.
        
        Args:
            text (str): Item text
            indent (int): Indentation level in mm
            bullet (str): Bullet character to use
        """
        self.set_x(self.get_x() + indent)
        self.set_font('DejaVu', '', 10)
        self.cell(5, 5, bullet)
        self.multi_cell(0, 5, text)

def ensure_font_directory():
    """Ensure the fonts directory exists and download DejaVu fonts if needed."""
    font_dir = Path("utils/fonts")
    font_dir.mkdir(parents=True, exist_ok=True)
    
    # Font URLs - these are direct links to DejaVu font files
    font_urls = {
        "DejaVuSansCondensed.ttf": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansCondensed.ttf",
        "DejaVuSansCondensed-Bold.ttf": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansCondensed-Bold.ttf",
        "DejaVuSansCondensed-Oblique.ttf": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansCondensed-Oblique.ttf"
    }
    
    # Check if fonts exist and download if needed
    import requests
    
    for font_file, url in font_urls.items():
        font_path = font_dir / font_file
        if not font_path.exists():
            try:
                # Download the font
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for 4XX/5XX responses
                
                # Save to file
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                
                st.success(f"Downloaded font: {font_file}")
            except Exception as e:
                st.warning(f"Could not download font {font_file}: {str(e)}")
                
                # Create an empty file as fallback
                with open(font_path, 'wb') as f:
                    pass  # Create empty file

def export_report_to_pdf(report_data):
    """Export a report to PDF.
    
    Args:
        report_data (dict): Report data to export
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Create a temporary directory to store the PDF
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"report_{report_data.get('id', 'unknown')}.pdf")
        
        # Ensure font directory exists
        ensure_font_directory()
        
        # Initialize PDF instance
        pdf = ReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Report header
        pdf.set_font('DejaVu', 'B', 16)
        pdf.cell(0, 10, "Weekly Activity Report", 0, 1, 'C')
        pdf.ln(5)
        
        # Report metadata
        pdf.set_font('DejaVu', '', 12)
        pdf.cell(0, 10, f"Name: {report_data.get('name', 'Anonymous')}", 0, 1)
        pdf.cell(0, 10, f"Week: {report_data.get('reporting_week', 'Unknown')}", 0, 1)
        
        # Safely extract timestamp - fix potential index error
        timestamp = report_data.get('timestamp', '')
        if timestamp and len(timestamp) >= 10:
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
                    
                pdf.section_title(activity.get('description', 'No description'))
                
                # Project and milestone
                project_text = f"{activity.get('project', 'No project')}"
                if activity.get('milestone'):
                    project_text += f" / {activity.get('milestone')}"
                pdf.add_text_with_label("Project:", project_text)
                
                # Status and priority
                status_line = f"Status: {activity.get('status', 'Unknown')} | Priority: {activity.get('priority', 'Medium')}"
                if activity.get('deadline'):
                    status_line += f" | Deadline: {activity.get('deadline')}"
                pdf.cell(0, 5, status_line, 0, 1)
                
                # Progress bar
                pdf.cell(0, 5, "Progress:", 0, 1)
                pdf.add_progress_bar(activity.get('progress', 0))
                
                # Customer and billable
                if activity.get('customer'):
                    pdf.cell(0, 5, f"Customer: {activity.get('customer')}", 0, 1)
                if activity.get('billable'):
                    pdf.cell(0, 5, f"Billable: {activity.get('billable')}", 0, 1)
                    
                pdf.ln(5)
        
        # Upcoming activities
        upcoming_activities = report_data.get('upcoming_activities', [])
        if upcoming_activities and isinstance(upcoming_activities, list) and len(upcoming_activities) > 0:
            pdf.chapter_title("Upcoming Activities")
            
            for activity in upcoming_activities:
                if not isinstance(activity, dict):  # Skip if not a dictionary
                    continue
                    
                pdf.section_title(activity.get('description', 'No description'))
                
                # Project and milestone
                project_text = f"{activity.get('project', 'No project')}"
                if activity.get('milestone'):
                    project_text += f" / {activity.get('milestone')}"
                pdf.add_text_with_label("Project:", project_text)
                
                # Priority and start date
                pdf.cell(0, 5, f"Priority: {activity.get('priority', 'Medium')}", 0, 1)
                if activity.get('expected_start'):
                    pdf.cell(0, 5, f"Expected Start: {activity.get('expected_start')}", 0, 1)
                    
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
                        
                    if accomplishment_text:  # Skip empty strings
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
                            
                        if followup_text:  # Skip empty strings
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
                            
                        if nextstep_text:  # Skip empty strings
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
            if key in report_data and report_data[key]:
                pdf.chapter_title(section['title'])
                pdf.chapter_body(report_data[key])
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
        # Create a temporary directory to store the PDF
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"objective_{objective_data.get('id', 'unknown')}.pdf")
        
        # Ensure font directory exists
        ensure_font_directory()
        
        # Initialize PDF instance
        pdf = ReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Objective header
        pdf.set_font('DejaVu', 'B', 16)
        title = objective_data.get('title', 'Untitled Objective')
        pdf.cell(0, 10, title, 0, 1, 'C')
        pdf.ln(5)
        
        # Objective metadata
        pdf.set_font('DejaVu', '', 12)
        pdf.cell(0, 10, f"Level: {objective_data.get('level', 'unknown').capitalize()}", 0, 1)
        
        if objective_data.get('level') == 'team':
            pdf.cell(0, 10, f"Team: {objective_data.get('team', 'Unassigned')}", 0, 1)
        
        pdf.cell(0, 10, f"Owner: {objective_data.get('owner_name', 'Unassigned')}", 0, 1)
        pdf.cell(0, 10, f"Period: {objective_data.get('period', 'Unknown')}", 0, 1)
        pdf.cell(0, 10, f"Status: {objective_data.get('status', 'Unknown')}", 0, 1)
        pdf.ln(5)
        
        # Description
        if 'description' in objective_data and objective_data['description']:
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
                progress = kr.get('progress', 0)
                
                # Key result title and progress
                pdf.section_title(f"KR{i+1}: {kr.get('description', 'No description')}")
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
                        update_text = f"{update.get('date', '')}: {update.get('previous', 0)}% → {update.get('current', 0)}%"
                        if update.get('note'):
                            update_text += f"\n{update.get('note')}"
                        
                        pdf.add_list_item(update_text)
                    
                    pdf.ln(5)
        
        # Last updated
        if 'last_updated' in objective_data:
            last_updated = objective_data['last_updated']
            if last_updated and len(last_updated) >= 10:
                pdf.set_font('DejaVu', 'I', 10)
                pdf.cell(0, 10, f"Last Updated: {last_updated[:10]}", 0, 1)
        
        # Output the PDF to a file
        pdf.output(file_path, 'F')
        
        return file_path
    except Exception as e:
        # Log the detailed error for debugging
        st.error(f"Error generating objective PDF: {str(e)}")
        raise e
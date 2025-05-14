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
        "DejaVuSansCondensed.ttf": "https://github.com/mps/fonts/tree/masterDejaVuSansCondensed.ttf",
        "DejaVuSansCondensed-Bold.ttf": "https://github.com/mps/fonts/tree/masterDejaVuSansCondensed-Bold.ttf",
        "DejaVuSansCondensed-Oblique.ttf": "https://github.com/mps/fonts/tree/masterDejaVuSansCondensed-Oblique.ttf"
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
    pdf.cell(0, 10, f"Date: {report_data.get('timestamp', '')[:10]}", 0, 1)
    pdf.ln(5)
    
    # Current activities
    if 'current_activities' in report_data and report_data['current_activities']:
        pdf.chapter_title("Current Activities")
        
        for activity in report_data['current_activities']:
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
    if 'upcoming_activities' in report_data and report_data['upcoming_activities']:
        pdf.chapter_title("Upcoming Activities")
        
        for activity in report_data['upcoming_activities']:
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
    if 'accomplishments' in report_data and report_data['accomplishments']:
        pdf.chapter_title("Last Week's Accomplishments")
        
        for accomplishment in report_data['accomplishments']:
            if accomplishment:  # Skip empty strings
                pdf.add_list_item(accomplishment)
        
        pdf.ln(5)
    
    # Action items
    pdf.chapter_title("Action Items")
    
    # Follow-ups
    if 'followups' in report_data and report_data['followups']:
        pdf.section_title("From Last Meeting")
        
        for followup in report_data['followups']:
            if followup:  # Skip empty strings
                pdf.add_list_item(followup)
        
        pdf.ln(5)
    
    # Next steps
    if 'nextsteps' in report_data and report_data['nextsteps']:
        pdf.section_title("Next Steps")
        
        for nextstep in report_data['nextsteps']:
            if nextstep:  # Skip empty strings
                pdf.add_list_item(nextstep)
        
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

def export_objective_to_pdf(objective_data):
    """Export an objective to PDF.
    
    Args:
        objective_data (dict): Objective data to export
        
    Returns:
        str: Path to the generated PDF file
    """
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
    if 'key_results' in objective_data and objective_data['key_results']:
        pdf.chapter_title("Key Results")
        
        for i, kr in enumerate(objective_data['key_results']):
            # Get progress
            progress = kr.get('progress', 0)
            
            # Key result title and progress
            pdf.section_title(f"KR{i+1}: {kr.get('description', 'No description')}")
            pdf.cell(30, 5, "Progress:")
            pdf.add_progress_bar(progress)
            
            # Updates
            if 'updates' in kr and kr['updates']:
                pdf.section_title("Recent Updates")
                
                for update in kr['updates'][-3:]:  # Show last 3 updates
                    # Format update info
                    update_text = f"{update.get('date', '')}: {update.get('previous', 0)}% → {update.get('current', 0)}%"
                    if update.get('note'):
                        update_text += f"\n{update.get('note')}"
                    
                    pdf.add_list_item(update_text)
                
                pdf.ln(5)
    
    # Last updated
    if 'last_updated' in objective_data:
        pdf.set_font('DejaVu', 'I', 10)
        pdf.cell(0, 10, f"Last Updated: {objective_data['last_updated'][:10]}", 0, 1)
    
    # Output the PDF to a file
    pdf.output(file_path, 'F')
    
    return file_path    
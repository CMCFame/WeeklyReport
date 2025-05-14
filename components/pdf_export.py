# components/pdf_export.py
"""PDF export component for the Weekly Report app."""

import streamlit as st
import tempfile
import os
import base64
from utils.pdf_export import export_report_to_pdf, export_objective_to_pdf

def render_report_export_button(report_data, button_text="Export as PDF", key_suffix=""):
    """Render a button to export a report as PDF.
    
    Args:
        report_data (dict): Report data to export
        button_text (str): Button text to display
        key_suffix (str): Suffix for the button key to avoid duplicates
    
    Returns:
        bool: True if button was clicked, False otherwise
    """
    if st.button(button_text, key=f"export_report_{key_suffix}"):
        try:
            with st.spinner("Generating PDF..."):
                # Generate PDF file
                pdf_path = export_report_to_pdf(report_data)
                
                # Create download link
                create_download_link(
                    pdf_path, 
                    f"weekly_report_{report_data.get('name', 'unknown')}_{report_data.get('reporting_week', 'unknown')}.pdf",
                    "Download PDF"
                )
            return True
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            return False
    return False

def render_objective_export_button(objective_data, button_text="Export as PDF", key_suffix=""):
    """Render a button to export an objective as PDF.
    
    Args:
        objective_data (dict): Objective data to export
        button_text (str): Button text to display
        key_suffix (str): Suffix for the button key to avoid duplicates
    
    Returns:
        bool: True if button was clicked, False otherwise
    """
    if st.button(button_text, key=f"export_objective_{key_suffix}"):
        try:
            with st.spinner("Generating PDF..."):
                # Generate PDF file
                pdf_path = export_objective_to_pdf(objective_data)
                
                # Create download link
                create_download_link(
                    pdf_path, 
                    f"objective_{objective_data.get('title', 'unknown')}_{objective_data.get('period', 'unknown')}.pdf",
                    "Download PDF"
                )
            return True
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            return False
    return False

def create_download_link(file_path, download_filename, link_text):
    """Create a download link for a file.
    
    Args:
        file_path (str): Path to the file to download
        download_filename (str): Filename to use for download
        link_text (str): Text to display for the download link
    """
    # Read file as bytes
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    
    # Encode as base64
    b64 = base64.b64encode(bytes_data).decode()
    
    # Create HTML link
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{download_filename}">{link_text}</a>'
    
    # Display link
    st.markdown(href, unsafe_allow_html=True)

def render_batch_export_reports(reports):
    """Render a batch export option for multiple reports.
    
    Args:
        reports (list): List of report dictionaries to export
    """
    if not reports:
        st.info("No reports available for export.")
        return
    
    st.subheader("Batch Export Reports")
    
    # Allow selecting reports to export
    selected_indices = st.multiselect(
        "Select Reports to Export",
        options=list(range(len(reports))),
        format_func=lambda i: f"{reports[i].get('name', 'Unknown')} - {reports[i].get('reporting_week', 'Unknown')} ({reports[i].get('timestamp', '')[:10]})"
    )
    
    if selected_indices and st.button("Export Selected Reports", use_container_width=True):
        try:
            with st.spinner("Generating PDFs..."):
                # Create a temporary directory for all PDFs
                temp_dir = tempfile.mkdtemp()
                
                # Generate PDFs for selected reports
                for i in selected_indices:
                    report_data = reports[i]
                    pdf_path = export_report_to_pdf(report_data)
                    
                    # Copy to the temporary directory with a descriptive name
                    filename = f"report_{report_data.get('name', 'unknown')}_{report_data.get('reporting_week', 'unknown')}.pdf"
                    dest_path = os.path.join(temp_dir, filename)
                    
                    # Copy the file
                    with open(pdf_path, "rb") as src, open(dest_path, "wb") as dest:
                        dest.write(src.read())
                    
                    # Create download link for individual report
                    st.markdown(f"### Report: {report_data.get('name', 'Unknown')} - {report_data.get('reporting_week', 'Unknown')}")
                    create_download_link(dest_path, filename, f"Download {filename}")
                
                st.success(f"Successfully generated {len(selected_indices)} PDF reports.")
        except Exception as e:
            st.error(f"Error generating PDFs: {str(e)}") 

def render_batch_export_objectives(objectives):
    """Render a batch export option for multiple objectives.
    
    Args:
        objectives (list): List of objective dictionaries to export
    """
    if not objectives:
        st.info("No objectives available for export.")
        return
    
    st.subheader("Batch Export Objectives")
    
    # Allow selecting objectives to export
    selected_indices = st.multiselect(
        "Select Objectives to Export",
        options=list(range(len(objectives))),
        format_func=lambda i: f"{objectives[i].get('title', 'Unknown')} ({objectives[i].get('level', 'unknown').capitalize()})"
    )
    
    if selected_indices and st.button("Export Selected Objectives", use_container_width=True):
        try:
            with st.spinner("Generating PDFs..."):
                # Create a temporary directory for all PDFs
                temp_dir = tempfile.mkdtemp()
                
                # Generate PDFs for selected objectives
                for i in selected_indices:
                    objective_data = objectives[i]
                    pdf_path = export_objective_to_pdf(objective_data)
                    
                    # Copy to the temporary directory with a descriptive name
                    filename = f"objective_{objective_data.get('title', 'unknown')}_{objective_data.get('period', 'unknown')}.pdf"
                    # Replace spaces with underscores for better filenames
                    filename = filename.replace(' ', '_')
                    dest_path = os.path.join(temp_dir, filename)
                    
                    # Copy the file
                    with open(pdf_path, "rb") as src, open(dest_path, "wb") as dest:
                        dest.write(src.read())
                    
                    # Create download link for individual objective
                    st.markdown(f"### Objective: {objective_data.get('title', 'Unknown')}")
                    create_download_link(dest_path, filename, f"Download {filename}")
                
                st.success(f"Successfully generated {len(selected_indices)} PDF files.")
        except Exception as e:
            st.error(f"Error generating PDFs: {str(e)}")
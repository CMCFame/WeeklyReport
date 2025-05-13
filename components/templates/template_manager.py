# components/export/export_panel.py
"""Export panel component for the Weekly Report app."""

import streamlit as st
from utils.export_ops import (
    get_csv_download_link,
    get_html_download_link,
    get_email_copy_button
)
from utils.file_ops import load_report

def render_export_panel(report_id=None):
    """Render the export panel for a report.
    
    Args:
        report_id (str, optional): Report ID to export. If None, uses current form.
    """
    if report_id:
        # Load report data
        report_data = load_report(report_id)
        if not report_data:
            st.error("Failed to load report for export.")
            return
    else:
        # Collect current form data
        from utils.session import collect_form_data
        report_data = collect_form_data()
    
    st.subheader("📤 Export Options")
    
    # Tabs for different export formats
    tab1, tab2, tab3 = st.tabs(["Excel", "HTML", "Email"])
    
    with tab1:
        st.write("Export your report as an Excel file with multiple sheets.")
        
        # Generate filename with date
        report_week = report_data.get('reporting_week', '').replace(' ', '_')
        name = report_data.get('name', 'Anonymous').replace(' ', '_')
        filename = f"weekly_report_{name}_{report_week}.xlsx"
        
        # Allow filename customization
        custom_filename = st.text_input("Filename:", value=filename)
        
        # Create download link
        excel_link = get_csv_download_link(report_data, custom_filename)
        st.markdown(excel_link, unsafe_allow_html=True)
        
        with st.expander("What's included in the Excel export?"):
            st.write("""
            The Excel export includes multiple sheets:
            - Basic information about the report
            - Current activities with all details
            - Upcoming activities with all details
            - Accomplishments list
            - Follow-up items and next steps
            - Any optional sections you've included
            
            This format is great for archiving or analysis.
            """)
    
    with tab2:
        st.write("Export your report as a formatted HTML document.")
        
        # Generate filename with date
        html_filename = f"weekly_report_{name}_{report_week}.html"
        
        # Allow filename customization
        custom_html_filename = st.text_input("HTML Filename:", value=html_filename)
        
        # Create download link
        html_link = get_html_download_link(report_data, custom_html_filename)
        st.markdown(html_link, unsafe_allow_html=True)
        
        with st.expander("What's included in the HTML export?"):
            st.write("""
            The HTML export creates a standalone web page with:
            - Header with your name and reporting week
            - Formatted tables for current and upcoming activities
            - Progress bars for activity completion
            - Color-coding for priorities and statuses
            - Bulleted lists for accomplishments and action items
            - All optional sections you've included
            
            This format is great for sharing via web or printing.
            """)
    
    with tab3:
        st.write("Export your report as formatted text for email.")
        
        # Create copy button for email content
        email_button = get_email_copy_button(report_data)
        st.markdown(email_button, unsafe_allow_html=True)
        
        with st.expander("Preview email content"):
            from utils.export_ops import export_report_as_email
            email_content = export_report_as_email(report_data)
            if email_content:
                st.text_area("Email Content", value=email_content, height=400)
        
        with st.expander("What's included in the email export?"):
            st.write("""
            The email export creates plain text content with:
            - Header with your name and reporting week
            - Accomplishments section (shown first for visibility)
            - Current and upcoming activities with key details
            - Action items (follow-ups and next steps)
            - Any optional sections you've included
            - A simple signature
            
            This format is optimized for email communication with your team.
            """)
    
    # Quick tips
    st.info("""
    💡 **Tip:** For best results when sharing, consider your audience:
    - Excel is best for managers who need to analyze or track multiple reports
    - HTML is best for stakeholders who want a visual, professional report
    - Email is best for quick updates in team communication channels
    """)

def render_export_page():
    """Render the export standalone page."""
    st.title("Export Reports")
    st.write("Export your weekly reports in various formats")
    
    # Get all reports
    from utils.file_ops import get_all_reports
    reports = get_all_reports(filter_by_user=True)
    
    if not reports:
        st.info("You don't have any reports to export. Create a report first!")
        return
    
    # Create a dropdown to select a report
    report_options = [(r.get('id'), f"{r.get('name', 'Anonymous')} - {r.get('reporting_week', 'Unknown')} ({r.get('timestamp', '')[:10]})") for r in reports]
    report_options.insert(0, ("", "Select a report to export..."))
    
    selected_report_id = st.selectbox(
        "Select a report to export:",
        options=[r[0] for r in report_options],
        format_func=lambda x: next((r[1] for r in report_options if r[0] == x), "Unknown"),
        key="export_report_selector"
    )
    
    if selected_report_id:
        render_export_panel(selected_report_id)
    else:
        st.info("Select a report from the dropdown above to export.")
        
    # Option to export current form
    st.divider()
    st.subheader("Export Current Form")
    
    if st.button("Export Current Form Instead"):
        render_export_panel(None)
        
    st.write("This will export the report form you're currently working on, without saving it first.")
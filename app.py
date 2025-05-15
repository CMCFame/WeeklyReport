# app.py (Updated with Report Editing) - continued

def render_weekly_report_page():
    """Render the main weekly report form."""
    # Check if we're in edit mode
    is_editing = st.session_state.get('editing_report', False)
    
    # Header
    if is_editing:
        st.title('📝 Edit Weekly Activity Report')
        st.write('Update your previous report')
    else:
        st.title('📋 Weekly Activity Report')
        st.write('Quickly document your week\'s work in under 5 minutes')

    # Progress bar
    completion_percentage = calculate_completion_percentage()
    st.progress(completion_percentage / 100)
    
    # Pre-fill name from user profile if empty
    if not st.session_state.get("name") and st.session_state.get("user_info"):
        st.session_state.name = st.session_state.user_info.get("full_name", "")

    # User Information Section
    render_user_info()

    # Current Activities Section
    render_current_activities()

    # Upcoming Activities Section
    render_upcoming_activities()

    # Simplified Last Week's Accomplishments Section
    render_simple_accomplishments()

    # Simplified Action Items Section
    render_simple_action_items()

    # Optional Sections Toggle
    render_optional_section_toggles()

    # Optional Sections Content
    render_all_optional_sections()

    # Form Actions (modified for edit mode)
    render_form_actions(is_editing)

def render_form_actions(is_editing=False):
    """Render the form action buttons.
    
    Args:
        is_editing (bool): Whether we're in edit mode
    """
    st.divider()
    
    if is_editing:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button('Save Changes', use_container_width=True, type="primary"):
                save_current_report('submitted', is_update=True)

        with col2:
            # Cancel editing button
            if st.button('Cancel Editing', use_container_width=True):
                # Reset form and clear editing flag
                reset_form()
                st.session_state.editing_report = False
                # Go back to past reports
                st.session_state.nav_page = "Past Reports"
                st.session_state.nav_section = "reporting"
                st.rerun()

        with col3:
            # Use an on_click callback rather than inline mutation
            st.button(
                'Reset Changes',
                use_container_width=True,
                on_click=clear_form_callback
            )
    else:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button('Save Draft', use_container_width=True):
                save_current_report('draft')

        with col2:
            # Use an on_click callback rather than inline mutation
            st.button(
                'Clear Form',
                use_container_width=True,
                on_click=clear_form_callback
            )

        with col3:
            if st.button('Submit Report', use_container_width=True, type="primary"):
                save_current_report('submitted')

def save_current_report(status, is_update=False):
    """Save the current report.

    Args:
        status (str): Status of the report ('draft' or 'submitted')
        is_update (bool): Whether this is an update to an existing report
    """
    # Validate required fields for submission
    if status == 'submitted' and not st.session_state.name:
        st.error('Please enter your name before submitting')
        return

    if status == 'submitted' and not st.session_state.reporting_week:
        st.error('Please enter the reporting week before submitting')
        return

    # Collect and save form data
    report_data = collect_form_data()
    report_data['status'] = status
    
    # If editing, preserve the original timestamp when it was created
    if is_update and 'original_timestamp' in st.session_state:
        report_data['timestamp'] = st.session_state.original_timestamp
        # Add last_updated timestamp
        from datetime import datetime
        report_data['last_updated'] = datetime.now().isoformat()
    
    report_id = save_report(report_data)
    st.session_state.report_id = report_id

    # Show success message
    if is_update:
        st.success('Report updated successfully!')
        # Clear editing flag
        st.session_state.editing_report = False
        # Go back to past reports
        st.session_state.nav_page = "Past Reports"
        st.session_state.nav_section = "reporting"
        st.rerun()
    elif status == 'draft':
        st.success('Draft saved successfully!')
    else:
        st.success('Report submitted successfully!')

# Run the app
if __name__ == '__main__':
    main()
# utils/session_cleanup.py
"""Session state cleanup utilities for the Weekly Report app."""

import streamlit as st

def clean_session_state():
    """Clean up potentially corrupted session state data."""
    try:
        # Helper function to ensure proper data types
        def ensure_string(value, default=''):
            """Ensure value is a string."""
            if value is None:
                return default
            return str(value)
        
        def ensure_list(value, default=None):
            """Ensure value is a list."""
            if default is None:
                default = []
            if value is None:
                return default
            if isinstance(value, list):
                return [item for item in value if item is not None]
            return default
        
        def ensure_dict_list(value, default=None):
            """Ensure value is a list of dictionaries."""
            if default is None:
                default = []
            if value is None:
                return default
            if isinstance(value, list):
                cleaned = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned.append(item)
                return cleaned
            return default
        
        # Clean basic fields
        st.session_state.name = ensure_string(st.session_state.get('name', ''))
        st.session_state.reporting_week = ensure_string(st.session_state.get('reporting_week', ''))
        
        # Clean activities
        st.session_state.current_activities = ensure_dict_list(
            st.session_state.get('current_activities', [])
        )
        st.session_state.upcoming_activities = ensure_dict_list(
            st.session_state.get('upcoming_activities', [])
        )
        
        # Clean text lists
        st.session_state.accomplishments = ensure_list(
            st.session_state.get('accomplishments', [''])
        )
        if not st.session_state.accomplishments:
            st.session_state.accomplishments = ['']
            
        st.session_state.followups = ensure_list(
            st.session_state.get('followups', [''])
        )
        if not st.session_state.followups:
            st.session_state.followups = ['']
            
        st.session_state.nextsteps = ensure_list(
            st.session_state.get('nextsteps', [''])
        )
        if not st.session_state.nextsteps:
            st.session_state.nextsteps = ['']
        
        # Clean optional sections
        from utils.constants import OPTIONAL_SECTIONS
        for section in OPTIONAL_SECTIONS:
            # Ensure boolean for section key
            section_key = section['key']
            if section_key not in st.session_state or not isinstance(st.session_state[section_key], bool):
                st.session_state[section_key] = False
            
            # Ensure string for content key
            content_key = section['content_key']
            st.session_state[content_key] = ensure_string(
                st.session_state.get(content_key, '')
            )
        
        return True
        
    except Exception as e:
        st.error(f"Error cleaning session state: {str(e)}")
        return False

def validate_session_state():
    """Validate that session state has proper data types."""
    issues = []
    
    # Check basic fields
    if not isinstance(st.session_state.get('name', ''), str):
        issues.append("name is not a string")
    
    if not isinstance(st.session_state.get('reporting_week', ''), str):
        issues.append("reporting_week is not a string")
    
    # Check activities
    current_activities = st.session_state.get('current_activities', [])
    if not isinstance(current_activities, list):
        issues.append("current_activities is not a list")
    else:
        for i, activity in enumerate(current_activities):
            if not isinstance(activity, dict):
                issues.append(f"current_activities[{i}] is not a dict")
    
    # Check text lists
    for field in ['accomplishments', 'followups', 'nextsteps']:
        value = st.session_state.get(field, [])
        if not isinstance(value, list):
            issues.append(f"{field} is not a list")
    
    return issues

def emergency_session_reset():
    """Emergency function to reset session state if completely corrupted."""
    try:
        # Store authentication info if it exists
        auth_info = {
            'authenticated': st.session_state.get('authenticated', False),
            'user_info': st.session_state.get('user_info', None)
        }
        
        # Clear all session state
        for key in list(st.session_state.keys()):
            if key not in ['authenticated', 'user_info']:
                del st.session_state[key]
        
        # Restore authentication
        st.session_state.authenticated = auth_info['authenticated']
        if auth_info['user_info']:
            st.session_state.user_info = auth_info['user_info']
        
        # Initialize fresh session state
        from utils.session import init_session_state
        init_session_state()
        
        st.success("Session state has been reset successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error during emergency reset: {str(e)}")
        return False

def render_session_diagnostics():
    """Render session diagnostics in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Session Diagnostics")
    
    if st.sidebar.button("🔍 Run Diagnostics"):
        st.sidebar.write("**Session State Analysis:**")
        
        # Check for None values in critical fields
        critical_fields = [
            'name', 'reporting_week', 'current_activities', 
            'upcoming_activities', 'accomplishments', 'followups', 'nextsteps'
        ]
        
        for field in critical_fields:
            value = st.session_state.get(field)
            if value is None:
                st.sidebar.error(f"❌ {field}: None")
            elif isinstance(value, list):
                st.sidebar.success(f"✅ {field}: List ({len(value)} items)")
                # Check for None items in lists
                none_count = sum(1 for item in value if item is None)
                if none_count > 0:
                    st.sidebar.warning(f"⚠️ {field}: {none_count} None items")
            elif isinstance(value, str):
                st.sidebar.success(f"✅ {field}: String ({len(value)} chars)")
            else:
                st.sidebar.info(f"ℹ️ {field}: {type(value)}")
        
        # Validation check
        issues = validate_session_state()
        if issues:
            st.sidebar.error("Issues found:")
            for issue in issues:
                st.sidebar.write(f"• {issue}")
        else:
            st.sidebar.success("✅ All validations passed!")
    
    if st.sidebar.button("🧹 Clean Session State"):
        if clean_session_state():
            st.sidebar.success("✅ Session state cleaned!")
            st.rerun()
        else:
            st.sidebar.error("❌ Cleaning failed")
    
    if st.sidebar.button("🚨 Emergency Reset"):
        if emergency_session_reset():
            st.rerun()
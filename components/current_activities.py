# components/current_activities.py
"""Compatibility module to maintain backward compatibility."""

# Import from the enhanced version to maintain backward compatibility
from components.enhanced_current_activities import render_enhanced_current_activities

# Create an alias for backward compatibility
def render_current_activities():
    """Render the current activities section (backward compatibility wrapper)."""
    return render_enhanced_current_activities()
# components/scoping_process.py
"""Scoping process tracking component for the Weekly Report app."""

import streamlit as st
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from utils import session

# Scoping phase options based on ARCOS framework
SCOPING_PHASES = [
    "Not Started",
    "Scoping Call/Whiteboard Scheduled",
    "Scoping Call/Whiteboard Completed", 
    "ROM Generation",
    "ROM Internal Review",
    "ROM Customer Review",
    "ROM Approved",
    "SOW Generation",
    "SOW Internal Review", 
    "SOW Customer Review",
    "SOW Approved",
    "Contract Signed",
    "Project Initiation"
]

# Priority levels
PRIORITY_LEVELS = ["High", "Medium", "Low"]

# Project types
PROJECT_TYPES = [
    "New Customer/Logo",
    "Existing Customer - New Project",
    "Existing Customer - Expansion", 
    "Multi-phase Project",
    "Single-phase Project"
]

# Customer readiness levels
READINESS_LEVELS = [
    "Ready to Proceed",
    "Budget Approval Pending",
    "Technical Review Pending",
    "Stakeholder Alignment Needed",
    "Timeline Constraints"
]

def ensure_scoping_directory():
    """Ensure the scoping data directory exists."""
    Path("data/scoping").mkdir(parents=True, exist_ok=True)

def render_scoping_process():
    """Render the scoping process tracking section."""
    st.header('🎯 Scoping Process Tracking')
    st.write('Track and manage the scoping process for potential projects according to ARCOS methodology.')
    
    # Initialize scoping activities if not present
    if 'scoping_activities' not in st.session_state:
        st.session_state.scoping_activities = load_scoping_activities()
    
    # Add new scoping activity button
    if st.button('+ Add New Scoping Activity', use_container_width=True):
        add_new_scoping_activity()
        st.rerun()
    
    # Display existing scoping activities
    if st.session_state.scoping_activities:
        st.subheader(f"Active Scoping Activities ({len(st.session_state.scoping_activities)})")
        
        # Summary metrics
        render_scoping_metrics()
        
        # Render each scoping activity
        for i, activity in enumerate(st.session_state.scoping_activities):
            render_scoping_activity_card(i, activity)
    else:
        st.info("No scoping activities tracked yet. Add your first scoping activity to get started.")

def render_scoping_metrics():
    """Render summary metrics for scoping activities."""
    activities = st.session_state.scoping_activities
    
    # Calculate metrics
    total_activities = len(activities)
    by_phase = {}
    by_priority = {}
    
    for activity in activities:
        phase = activity.get('current_phase', 'Not Started')
        priority = activity.get('priority', 'Medium')
        
        by_phase[phase] = by_phase.get(phase, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Activities", total_activities)
    
    with col2:
        completed_count = by_phase.get('Contract Signed', 0) + by_phase.get('Project Initiation', 0)
        st.metric("Contracts Signed", completed_count)
    
    with col3:
        active_count = total_activities - completed_count
        st.metric("Active Scoping", active_count)
    
    with col4:
        high_priority = by_priority.get('High', 0)
        st.metric("High Priority", high_priority)

def render_scoping_activity_card(index, activity):
    """Render a card for a scoping activity."""
    customer_name = activity.get('customer_name', 'Unknown Customer')
    project_title = activity.get('project_title', 'Untitled Project')
    current_phase = activity.get('current_phase', 'Not Started')
    priority = activity.get('priority', 'Medium')
    
    # Color coding for priority
    priority_colors = {
        'High': '🔴',
        'Medium': '🟡', 
        'Low': '🟢'
    }
    
    priority_icon = priority_colors.get(priority, '🟡')
    
    with st.expander(f"{priority_icon} {customer_name} - {project_title} ({current_phase})", expanded=False):
        render_scoping_activity_form(index, activity)

def render_scoping_activity_form(index, activity):
    """Render the form for a scoping activity."""
    
    # Basic Information Section
    st.subheader("📋 Project Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        customer_name = st.text_input(
            "Customer Name",
            value=activity.get('customer_name', ''),
            key=f"scoping_customer_{index}"
        )
        update_scoping_activity(index, 'customer_name', customer_name)
        
        project_title = st.text_input(
            "Project Title", 
            value=activity.get('project_title', ''),
            key=f"scoping_title_{index}"
        )
        update_scoping_activity(index, 'project_title', project_title)
        
        estimated_value = st.number_input(
            "Estimated Project Value ($)",
            min_value=0,
            value=activity.get('estimated_value', 0),
            step=1000,
            key=f"scoping_value_{index}"
        )
        update_scoping_activity(index, 'estimated_value', estimated_value)
    
    with col2:
        priority = st.selectbox(
            "Priority",
            options=PRIORITY_LEVELS,
            index=PRIORITY_LEVELS.index(activity.get('priority', 'Medium')),
            key=f"scoping_priority_{index}"
        )
        update_scoping_activity(index, 'priority', priority)
        
        project_type = st.selectbox(
            "Project Type",
            options=PROJECT_TYPES,
            index=PROJECT_TYPES.index(activity.get('project_type', 'Existing Customer - New Project')),
            key=f"scoping_type_{index}"
        )
        update_scoping_activity(index, 'project_type', project_type)
        
        expected_start = st.date_input(
            "Expected Project Start",
            value=datetime.strptime(activity.get('expected_start', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
            key=f"scoping_start_{index}"
        )
        update_scoping_activity(index, 'expected_start', expected_start.strftime('%Y-%m-%d'))
    
    # Current Phase and Progress Section
    st.subheader("📊 Scoping Progress")
    
    col3, col4 = st.columns(2)
    
    with col3:
        current_phase = st.selectbox(
            "Current Phase",
            options=SCOPING_PHASES,
            index=SCOPING_PHASES.index(activity.get('current_phase', 'Not Started')),
            key=f"scoping_phase_{index}"
        )
        update_scoping_activity(index, 'current_phase', current_phase)
        
        customer_readiness = st.selectbox(
            "Customer Readiness",
            options=READINESS_LEVELS,
            index=READINESS_LEVELS.index(activity.get('customer_readiness', 'Ready to Proceed')),
            key=f"scoping_readiness_{index}"
        )
        update_scoping_activity(index, 'customer_readiness', customer_readiness)
    
    with col4:
        # Key dates
        scoping_call_date = st.date_input(
            "Scoping Call Date",
            value=datetime.strptime(activity.get('scoping_call_date', ''), '%Y-%m-%d').date() if activity.get('scoping_call_date') else None,
            key=f"scoping_call_date_{index}"
        )
        if scoping_call_date:
            update_scoping_activity(index, 'scoping_call_date', scoping_call_date.strftime('%Y-%m-%d'))
        
        rom_target_date = st.date_input(
            "ROM Target Date",
            value=datetime.strptime(activity.get('rom_target_date', ''), '%Y-%m-%d').date() if activity.get('rom_target_date') else None,
            key=f"scoping_rom_date_{index}"
        )
        if rom_target_date:
            update_scoping_activity(index, 'rom_target_date', rom_target_date.strftime('%Y-%m-%d'))
    
    # Key Stakeholders Section
    st.subheader("👥 Key Stakeholders")
    
    col5, col6 = st.columns(2)
    
    with col5:
        primary_contact = st.text_input(
            "Primary Customer Contact",
            value=activity.get('primary_contact', ''),
            key=f"scoping_contact_{index}"
        )
        update_scoping_activity(index, 'primary_contact', primary_contact)
        
        arcos_lead = st.text_input(
            "ARCOS Lead Consultant",
            value=activity.get('arcos_lead', ''),
            key=f"scoping_lead_{index}"
        )
        update_scoping_activity(index, 'arcos_lead', arcos_lead)
    
    with col6:
        decision_maker = st.text_input(
            "Customer Decision Maker",
            value=activity.get('decision_maker', ''),
            key=f"scoping_decision_{index}"
        )
        update_scoping_activity(index, 'decision_maker', decision_maker)
        
        sales_rep = st.text_input(
            "Sales Representative",
            value=activity.get('sales_rep', ''),
            key=f"scoping_sales_{index}"
        )
        update_scoping_activity(index, 'sales_rep', sales_rep)
    
    # Project Details Section
    st.subheader("📝 Project Details")
    
    business_drivers = st.text_area(
        "Business Drivers & Goals",
        value=activity.get('business_drivers', ''),
        height=100,
        key=f"scoping_drivers_{index}",
        help="Why is the customer pursuing this project? What business value are they seeking?"
    )
    update_scoping_activity(index, 'business_drivers', business_drivers)
    
    current_state = st.text_area(
        "Current State Summary",
        value=activity.get('current_state', ''),
        height=80,
        key=f"scoping_current_{index}",
        help="Brief description of the customer's current environment and processes"
    )
    update_scoping_activity(index, 'current_state', current_state)
    
    future_state = st.text_area(
        "Future State Vision", 
        value=activity.get('future_state', ''),
        height=80,
        key=f"scoping_future_{index}",
        help="What the customer wants to achieve - their desired end state"
    )
    update_scoping_activity(index, 'future_state', future_state)
    
    # Assumptions and Risks Section  
    st.subheader("⚠️ Key Assumptions & Risks")
    
    key_assumptions = st.text_area(
        "Key Assumptions",
        value=activity.get('key_assumptions', ''),
        height=80,
        key=f"scoping_assumptions_{index}",
        help="Critical assumptions that could impact scope, timeline, or pricing"
    )
    update_scoping_activity(index, 'key_assumptions', key_assumptions)
    
    potential_risks = st.text_area(
        "Potential Risks & Concerns",
        value=activity.get('potential_risks', ''),
        height=80,
        key=f"scoping_risks_{index}",
        help="Technical, business, or project risks that could impact success"
    )
    update_scoping_activity(index, 'potential_risks', potential_risks)
    
    # Next Steps and Notes Section
    st.subheader("📅 Next Steps & Notes")
    
    next_steps = st.text_area(
        "Next Steps",
        value=activity.get('next_steps', ''),
        height=80,
        key=f"scoping_next_{index}",
        help="Immediate next actions required to move the scoping forward"
    )
    update_scoping_activity(index, 'next_steps', next_steps)
    
    internal_notes = st.text_area(
        "Internal Notes",
        value=activity.get('internal_notes', ''),
        height=80,
        key=f"scoping_notes_{index}",
        help="Internal team notes and observations not shared with customer"
    )
    update_scoping_activity(index, 'internal_notes', internal_notes)
    
    # Action Buttons
    col7, col8, col9 = st.columns(3)
    
    with col7:
        if st.button("📧 Generate ROM Template", key=f"rom_template_{index}"):
            generate_rom_template(activity)
    
    with col8:
        if st.button("📋 Generate SOW Template", key=f"sow_template_{index}"):
            generate_sow_template(activity)
    
    with col9:
        if st.button("🗑️ Remove Activity", key=f"remove_scoping_{index}"):
            remove_scoping_activity(index)
            st.rerun()
    
    # Save activity to persistent storage
    save_scoping_activities()

def add_new_scoping_activity():
    """Add a new scoping activity."""
    new_activity = {
        'id': str(uuid.uuid4()),
        'customer_name': '',
        'project_title': '',
        'priority': 'Medium',
        'project_type': 'Existing Customer - New Project',
        'current_phase': 'Not Started',
        'customer_readiness': 'Ready to Proceed',
        'estimated_value': 0,
        'expected_start': datetime.now().strftime('%Y-%m-%d'),
        'scoping_call_date': '',
        'rom_target_date': '',
        'primary_contact': '',
        'decision_maker': '',
        'arcos_lead': '',
        'sales_rep': '',
        'business_drivers': '',
        'current_state': '',
        'future_state': '',
        'key_assumptions': '',
        'potential_risks': '',
        'next_steps': '',
        'internal_notes': '',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    st.session_state.scoping_activities.append(new_activity)
    save_scoping_activities()

def update_scoping_activity(index, field, value):
    """Update a field in a scoping activity."""
    if index < len(st.session_state.scoping_activities):
        st.session_state.scoping_activities[index][field] = value
        st.session_state.scoping_activities[index]['updated_at'] = datetime.now().isoformat()

def remove_scoping_activity(index):
    """Remove a scoping activity."""
    if index < len(st.session_state.scoping_activities):
        st.session_state.scoping_activities.pop(index)
        save_scoping_activities()

def load_scoping_activities():
    """Load scoping activities from persistent storage."""
    ensure_scoping_directory()
    
    try:
        scoping_file = Path("data/scoping/scoping_activities.json")
        if scoping_file.exists():
            with open(scoping_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading scoping activities: {str(e)}")
    
    return []

def save_scoping_activities():
    """Save scoping activities to persistent storage."""
    ensure_scoping_directory()
    
    try:
        scoping_file = Path("data/scoping/scoping_activities.json")
        with open(scoping_file, 'w') as f:
            json.dump(st.session_state.scoping_activities, f, indent=2)
    except Exception as e:
        st.error(f"Error saving scoping activities: {str(e)}")

def generate_rom_template(activity):
    """Generate a ROM template based on the activity data."""
    template = f"""
# Rough Order of Magnitude (ROM)
**Customer:** {activity.get('customer_name', 'TBD')}  
**Project:** {activity.get('project_title', 'TBD')}  
**Date:** {datetime.now().strftime('%B %d, %Y')}

## Summary
{activity.get('business_drivers', 'TBD - Business drivers and objectives')}

**Current Environment:** {activity.get('current_state', 'TBD')}
**Customer Request:** {activity.get('future_state', 'TBD')}

## Deliverables
- TBD - Documents to be delivered
- TBD - Software/configurations
- TBD - Implementation services

## Assumptions
{activity.get('key_assumptions', 'TBD - Key assumptions about scope and environment')}

## Pricing Estimate
- Professional Services: $TBD
- Software Licensing: TBD
- Travel & Expenses: $TBD
- **Total:** $TBD

## Work Estimate and Timeline
- **Total Duration:** TBD weeks
- **Phase 1:** TBD (TBD weeks)
- **Phase 2:** TBD (TBD weeks)
- **Expected Start:** {activity.get('expected_start', 'TBD')}

---
*This ROM should be within 10% of actual pricing upon SOW approval*
"""
    
    st.text_area("ROM Template", value=template, height=400, key=f"rom_template_display")
    st.success("ROM template generated! Copy the content above and customize as needed.")

def generate_sow_template(activity):
    """Generate a SOW template based on the activity data."""
    project_type = activity.get('project_type', '')
    is_long_form = 'New Customer' in project_type or 'Multi-phase' in project_type
    
    template = f"""
# Statement of Work {'(Long Form)' if is_long_form else '(Short Form)'}
**Customer:** {activity.get('customer_name', 'TBD')}  
**Project:** {activity.get('project_title', 'TBD')}  
**Date:** {datetime.now().strftime('%B %d, %Y')}

## Project Specification
{activity.get('business_drivers', 'TBD - Primary objective and strategy')}

**Current Environment:** {activity.get('current_state', 'TBD')}
**Customer Request:** {activity.get('future_state', 'TBD')}

## Objective
The tangible work to be delivered:
- TBD - Documents and deliverables
- TBD - Software and configurations  
- TBD - Implementation and services

## Assumptions
{activity.get('key_assumptions', 'TBD - Scope limitations and assumptions')}

## Investment and Timeline
**Total Duration:** TBD weeks  
**Professional Services:** $TBD  
**Expected Start:** {activity.get('expected_start', 'TBD')}

### Phase Overview
- **Phase 1:** TBD - Description and deliverables
- **Phase 2:** TBD - Description and deliverables

## Scope
Detailed tasks and responsibilities for each phase:
- TBD - Specific tasks and outcomes
- TBD - Customer responsibilities
- TBD - ARCOS responsibilities

## Project Teams: Roles and Responsibilities
**Customer Team:**
- Project Sponsor: {activity.get('decision_maker', 'TBD')}
- Primary Contact: {activity.get('primary_contact', 'TBD')}

**ARCOS Team:**
- Lead Consultant: {activity.get('arcos_lead', 'TBD')}
- Sales Representative: {activity.get('sales_rep', 'TBD')}

## Proposal Acceptance
By signing below, both parties accept the terms of this Statement of Work.

**Customer Signature:** ______________________ **Date:** __________

**ARCOS Signature:** ______________________ **Date:** __________
"""
    
    st.text_area("SOW Template", value=template, height=500, key=f"sow_template_display")
    st.success(f"{'Long-form' if is_long_form else 'Short-form'} SOW template generated! Copy and customize as needed.")
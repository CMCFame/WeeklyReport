# components/objectives_import.py
"""Objectives import component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime
from pathlib import Path

def render_objectives_import():
    """Render the objectives import interface."""
    st.title("Import Objectives")
    st.write("Upload OKRs and goals for your team from CSV or JSON files.")
    
    # Tab navigation
    tab1, tab2 = st.tabs(["CSV Import", "JSON Import"])
    
    with tab1:
        render_csv_import()
    
    with tab2:
        render_json_import()

def render_csv_import():
    """Render CSV import interface."""
    st.subheader("Import from CSV")
    
    # Download template
    st.write("First, download our CSV template:")
    
    csv_template = create_csv_template()
    csv_data = csv_template.to_csv(index=False)
    
    st.download_button(
        label="📥 Download OKR Template (CSV)",
        data=csv_data,
        file_name="okr_template.csv",
        mime="text/csv"
    )
    
    # Upload file
    st.write("Then, fill in your objectives and upload:")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="csv_okr_upload")
    
    if uploaded_file:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Validate columns
            required_columns = ['objective_title', 'description', 'level', 'period', 'kr1_description']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Error: Your CSV is missing these required columns: {', '.join(missing_columns)}")
                return
            
            # Show preview
            st.subheader("Preview Import Data")
            st.dataframe(df, use_container_width=True)
            
            # Process button
            if st.button("Import Objectives", type="primary"):
                results = process_csv_import(df)
                
                # Show results
                st.success(f"Successfully imported {len(results)} objectives!")
                
                # Show details
                with st.expander("View Import Details"):
                    for result in results:
                        st.write(f"✅ **{result['title']}** - {len(result['key_results'])} key results")
                
        except Exception as e:
            st.error(f"Error processing CSV file: {str(e)}")

def render_json_import():
    """Render JSON import interface."""
    st.subheader("Import from JSON")
    
    # Download template
    st.write("First, download our JSON template:")
    
    json_template = create_json_template()
    json_data = json.dumps(json_template, indent=2)
    
    st.download_button(
        label="📥 Download OKR Template (JSON)",
        data=json_data,
        file_name="okr_template.json",
        mime="application/json"
    )
    
    # Upload file
    st.write("Then, fill in your objectives and upload:")
    uploaded_file = st.file_uploader("Choose a JSON file", type="json", key="json_okr_upload")
    
    if uploaded_file:
        try:
            # Read JSON
            content = uploaded_file.read()
            data = json.loads(content)
            
            # Validate format
            if not isinstance(data, list):
                st.error("JSON file must contain a list of objectives")
                return
            
            for i, obj in enumerate(data):
                if 'objective_title' not in obj:
                    st.error(f"Objective at index {i} is missing 'objective_title'")
                    return
                if 'key_results' not in obj or not isinstance(obj['key_results'], list):
                    st.error(f"Objective '{obj.get('objective_title')}' is missing key results")
                    return
            
            # Show preview
            st.subheader("Preview Import Data")
            
            for obj in data:
                with st.expander(f"{obj.get('objective_title')} - {obj.get('level', 'unknown').capitalize()}"):
                    st.write(f"**Description:** {obj.get('description', 'No description')}")
                    st.write(f"**Period:** {obj.get('period', 'Not specified')}")
                    st.write(f"**Level:** {obj.get('level', 'unknown').capitalize()}")
                    
                    if obj.get('level') == 'team':
                        st.write(f"**Team:** {obj.get('team', 'Not specified')}")
                    
                    if obj.get('level') == 'individual':
                        st.write(f"**Owner:** {obj.get('owner_name', 'Not specified')}")
                    
                    st.write("**Key Results:**")
                    for i, kr in enumerate(obj.get('key_results', [])):
                        st.write(f"{i+1}. {kr.get('description')}")
            
            # Process button
            if st.button("Import Objectives", type="primary", key="json_import_btn"):
                results = process_json_import(data)
                
                # Show results
                st.success(f"Successfully imported {len(results)} objectives!")
                
                # Show details
                with st.expander("View Import Details"):
                    for result in results:
                        st.write(f"✅ **{result['title']}** - {len(result['key_results'])} key results")
                
        except Exception as e:
            st.error(f"Error processing JSON file: {str(e)}")

def process_csv_import(df):
    """Process CSV import data.
    
    Args:
        df (pandas.DataFrame): DataFrame containing objectives data
    
    Returns:
        list: List of dictionaries with import results
    """
    results = []
    
    # Process each row as an objective
    for _, row in df.iterrows():
        try:
            # Extract objective data
            title = row['objective_title']
            description = row.get('description', '')
            level = row.get('level', 'company').lower()
            period = row.get('period', f"Q{datetime.now().month//4 + 1} {datetime.now().year}")
            status = row.get('status', 'On Track')
            
            # Team or owner information
            team = row.get('team', '') if level == 'team' else None
            owner_name = row.get('owner_name', '') if level == 'individual' else None
            owner_id = row.get('owner_id', str(uuid.uuid4())) if level == 'individual' else None
            
            # Extract key results
            key_results = []
            
            # Find all columns starting with 'kr' and ending with '_description'
            kr_columns = [col for col in df.columns if col.startswith('kr') and col.endswith('_description')]
            
            for kr_col in kr_columns:
                # Check if this key result has a description
                kr_desc = row.get(kr_col)
                if pd.notna(kr_desc) and kr_desc:
                    # Get KR number
                    kr_num = kr_col.split('_')[0][2:]
                    
                    # Check for target value
                    target_col = f'kr{kr_num}_target'
                    target = row.get(target_col, None)
                    
                    # Create key result
                    key_result = {
                        'description': kr_desc,
                        'progress': 0  # Start at 0 progress
                    }
                    
                    if pd.notna(target):
                        key_result['target'] = target
                    
                    key_results.append(key_result)
            
            # Only create objective if it has a title and at least one key result
            if title and key_results:
                # Create objective object
                objective = {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'description': description,
                    'level': level,
                    'period': period,
                    'status': status,
                    'key_results': key_results,
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Add team or owner data if applicable
                if level == 'team' and team:
                    objective['team'] = team
                
                if level == 'individual':
                    objective['owner_name'] = owner_name
                    objective['owner_id'] = owner_id
                else:
                    # For company/team levels, owner is the current user
                    objective['owner_id'] = st.session_state.user_info.get('id')
                    objective['owner_name'] = st.session_state.user_info.get('full_name', 'Unknown')
                
                # Save objective
                save_objective(objective)
                
                # Add to results
                results.append({
                    'title': title,
                    'key_results': key_results
                })
        
        except Exception as e:
            st.warning(f"Error processing objective '{row.get('objective_title', 'Unknown')}': {str(e)}")
    
    return results

def process_json_import(data):
    """Process JSON import data.
    
    Args:
        data (list): List of objectives data
    
    Returns:
        list: List of dictionaries with import results
    """
    results = []
    
    # Process each objective
    for obj_data in data:
        try:
            # Extract objective data
            title = obj_data['objective_title']
            description = obj_data.get('description', '')
            level = obj_data.get('level', 'company').lower()
            period = obj_data.get('period', f"Q{datetime.now().month//4 + 1} {datetime.now().year}")
            status = obj_data.get('status', 'On Track')
            
            # Team or owner information
            team = obj_data.get('team', '') if level == 'team' else None
            owner_name = obj_data.get('owner_name', '') if level == 'individual' else None
            owner_id = obj_data.get('owner_id', str(uuid.uuid4())) if level == 'individual' else None
            
            # Get key results
            key_results = []
            
            for kr_data in obj_data.get('key_results', []):
                if isinstance(kr_data, dict) and 'description' in kr_data:
                    # Create key result
                    key_result = {
                        'description': kr_data['description'],
                        'progress': kr_data.get('progress', 0)  # Default to 0 progress
                    }
                    
                    if 'target' in kr_data:
                        key_result['target'] = kr_data['target']
                    
                    key_results.append(key_result)
            
            # Only create objective if it has a title and at least one key result
            if title and key_results:
                # Create objective object
                objective = {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'description': description,
                    'level': level,
                    'period': period,
                    'status': status,
                    'key_results': key_results,
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Add team or owner data if applicable
                if level == 'team' and team:
                    objective['team'] = team
                
                if level == 'individual':
                    objective['owner_name'] = owner_name
                    objective['owner_id'] = owner_id
                else:
                    # For company/team levels, owner is the current user
                    objective['owner_id'] = st.session_state.user_info.get('id')
                    objective['owner_name'] = st.session_state.user_info.get('full_name', 'Unknown')
                
                # Save objective
                save_objective(objective)
                
                # Add to results
                results.append({
                    'title': title,
                    'key_results': key_results
                })
        
        except Exception as e:
            st.warning(f"Error processing objective '{obj_data.get('objective_title', 'Unknown')}': {str(e)}")
    
    return results

def save_objective(objective):
    """Save an objective to file.
    
    Args:
        objective (dict): Objective data to save
        
    Returns:
        str: Objective ID
    """
    try:
        # Ensure the objectives directory exists
        Path("data/objectives").mkdir(parents=True, exist_ok=True)
        
        # Generate ID if needed
        if 'id' not in objective:
            objective['id'] = str(uuid.uuid4())
        
        # Set timestamps
        if 'created_at' not in objective:
            objective['created_at'] = datetime.now().isoformat()
        objective['last_updated'] = datetime.now().isoformat()
        
        # Save to file
        with open(f"data/objectives/{objective['id']}.json", 'w') as f:
            json.dump(objective, f, indent=2)
        
        return objective['id']
        
    except Exception as e:
        st.error(f"Error saving objective: {str(e)}")
        return None

def create_csv_template():
    """Create a CSV template for objectives import."""
    # Create a sample dataframe with example data
    data = {
        'objective_title': [
            'Increase Market Share in Enterprise Segment',
            'Improve Product Quality',
            'Enhance Product Performance',
            'Increase Brand Awareness',
            'Improve User Onboarding Experience'
        ],
        'description': [
            'Expand our presence in the enterprise market segment',
            'Deliver a more stable and reliable product',
            'Make the product faster and more responsive',
            'Build greater awareness of our brand in target markets',
            'Make it easier for new users to get started with our product'
        ],
        'level': [
            'company',
            'company',
            'team',
            'team',
            'individual'
        ],
        'period': [
            'Q2 2025',
            'Q2 2025',
            'Q2 2025',
            'Q2 2025',
            'Q2 2025'
        ],
        'status': [
            'On Track',
            'On Track',
            'On Track',
            'At Risk',
            'On Track'
        ],
        'team': [
            '',
            '',
            'Engineering',
            'Marketing',
            ''
        ],
        'owner_name': [
            '',
            '',
            '',
            '',
            'John Smith'
        ],
        'owner_id': [
            '',
            '',
            '',
            '',
            ''
        ],
        'kr1_description': [
            'Increase enterprise customer base by 25%',
            'Reduce critical bugs by 40%',
            'Reduce page load time by 30%',
            'Increase social media engagement by 50%',
            'Increase new user 30-day retention by 20%'
        ],
        'kr1_target': [
            '25%',
            '40%',
            '30%',
            '50%',
            '20%'
        ],
        'kr2_description': [
            'Achieve 90% retention rate for enterprise customers',
            'Improve system uptime to 99.95%',
            'Decrease API response time by 25%',
            'Generate 25 media mentions in industry publications',
            'Reduce onboarding completion time from 15 to 5 minutes'
        ],
        'kr2_target': [
            '90%',
            '99.95%',
            '25%',
            '25',
            '5 minutes'
        ],
        'kr3_description': [
            'Launch 3 new enterprise-focused features',
            'Achieve average user satisfaction score of 4.5/5',
            'Implement monitoring for 100% of critical services',
            'Grow email subscriber list by 35%',
            'Achieve new user satisfaction score of 4.7/5'
        ],
        'kr3_target': [
            '3',
            '4.5',
            '100%',
            '35%',
            '4.7'
        ]
    }
    
    return pd.DataFrame(data)

def create_json_template():
    """Create a JSON template for objectives import."""
    template = [
        {
            "objective_title": "Increase Market Share in Enterprise Segment",
            "description": "Expand our presence in the enterprise market segment",
            "level": "company",
            "period": "Q2 2025",
            "status": "On Track",
            "key_results": [
                {
                    "description": "Increase enterprise customer base by 25%",
                    "progress": 0,
                    "target": "25%"
                },
                {
                    "description": "Achieve 90% retention rate for enterprise customers",
                    "progress": 0,
                    "target": "90%"
                },
                {
                    "description": "Launch 3 new enterprise-focused features",
                    "progress": 0,
                    "target": "3"
                }
            ]
        },
        {
            "objective_title": "Improve Product Quality",
            "description": "Deliver a more stable and reliable product",
            "level": "company",
            "period": "Q2 2025",
            "status": "On Track",
            "key_results": [
                {
                    "description": "Reduce critical bugs by 40%",
                    "progress": 0,
                    "target": "40%"
                },
                {
                    "description": "Improve system uptime to 99.95%",
                    "progress": 0,
                    "target": "99.95%"
                },
                {
                    "description": "Achieve average user satisfaction score of 4.5/5",
                    "progress": 0,
                    "target": "4.5"
                }
            ]
        },
        {
            "objective_title": "Enhance Product Performance",
            "description": "Make the product faster and more responsive",
            "level": "team",
            "team": "Engineering",
            "period": "Q2 2025",
            "status": "On Track",
            "key_results": [
                {
                    "description": "Reduce page load time by 30%",
                    "progress": 0,
                    "target": "30%"
                },
                {
                    "description": "Decrease API response time by 25%",
                    "progress": 0,
                    "target": "25%"
                },
                {
                    "description": "Implement monitoring for 100% of critical services",
                    "progress": 0,
                    "target": "100%"
                }
            ]
        },
        {
            "objective_title": "Increase Brand Awareness",
            "description": "Build greater awareness of our brand in target markets",
            "level": "team",
            "team": "Marketing",
            "period": "Q2 2025",
            "status": "At Risk",
            "key_results": [
                {
                    "description": "Increase social media engagement by 50%",
                    "progress": 0,
                    "target": "50%"
                },
                {
                    "description": "Generate 25 media mentions in industry publications",
                    "progress": 0,
                    "target": "25"
                },
                {
                    "description": "Grow email subscriber list by 35%",
                    "progress": 0,
                    "target": "35%"
                }
            ]
        },
        {
            "objective_title": "Improve User Onboarding Experience",
            "description": "Make it easier for new users to get started with our product",
            "level": "individual",
            "owner_name": "John Smith",
            "period": "Q2 2025",
            "status": "On Track",
            "key_results": [
                {
                    "description": "Increase new user 30-day retention by 20%",
                    "progress": 0,
                    "target": "20%"
                },
                {
                    "description": "Reduce onboarding completion time from 15 to 5 minutes",
                    "progress": 0,
                    "target": "5 minutes"
                },
                {
                    "description": "Achieve new user satisfaction score of 4.7/5",
                    "progress": 0,
                    "target": "4.7"
                }
            ]
        }
    ]
    
    return template
# components/team_structure.py
"""Team structure component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from io import BytesIO
from utils.team_utils import (
    load_team_structure, save_team_structure, 
    add_team, update_team, delete_team,
    add_member, update_member, delete_member,
    get_team_by_id, get_member_by_id, import_organization_from_users
)

def render_team_structure():
    """Render the team structure visualization and management page."""
    st.title("Team Structure")
    st.write("Visualize and manage your team's organizational structure.")
    
    # User permissions
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    can_manage = user_role in ["admin", "manager"]
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Org Chart", "Team List", "Management"])
    
    with tab1:
        render_org_chart()
    
    with tab2:
        render_team_list()
    
    if can_manage:
        with tab3:
            render_team_management()
    
def render_org_chart():
    """Render the organization chart visualization."""
    st.subheader("Organization Chart")
    
    # Load team structure
    structure = load_team_structure()
    teams = structure.get("teams", [])
    members = structure.get("members", [])
    relationships = structure.get("relationships", [])
    
    if not members:
        st.info("No team members have been added yet. Add team members in the Management tab.")
        return
    
    # Create graph
    G = nx.DiGraph()
    
    # Add nodes (team members)
    node_colors = []
    labels = {}
    
    for member in members:
        member_id = member.get("id")
        member_name = member.get("name", "Unknown")
        member_title = member.get("title", "")
        
        # Add node
        G.add_node(member_id)
        
        # Set label
        labels[member_id] = f"{member_name}\n{member_title}"
        
        # Set color based on team
        team_id = member.get("team_id")
        if team_id:
            team = next((t for t in teams if t.get("id") == team_id), None)
            if team:
                color = team.get("color", "#3366cc")
                node_colors.append(color)
            else:
                node_colors.append("#cccccc")  # Default gray
        else:
            node_colors.append("#cccccc")  # Default gray
    
    # Add edges (reporting relationships)
    for relationship in relationships:
        manager_id = relationship.get("manager_id")
        member_id = relationship.get("member_id")
        
        if manager_id and member_id:
            G.add_edge(manager_id, member_id)
    
    # Render graph
    if len(G.nodes()) > 0:
        # Select layout algorithm based on size
        if len(G.nodes()) < 20:
            pos = nx.spring_layout(G, seed=42)  # For small graphs
        else:
            pos = nx.kamada_kawai_layout(G)  # For larger graphs
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Draw the graph
        nx.draw(
            G, pos, 
            with_labels=False,
            node_color=node_colors,
            node_size=1500,
            alpha=0.8,
            arrows=True,
            ax=ax
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            G, pos,
            labels=labels,
            font_size=9,
            font_family="sans-serif",
            font_weight="bold"
        )
        
        # Remove axis
        ax.axis("off")
        
        # Show the plot
        st.pyplot(fig)
        
        # Add legend for teams
        if teams:
            st.subheader("Teams")
            cols = st.columns(min(4, len(teams)))
            
            for i, team in enumerate(teams):
                with cols[i % 4]:
                    color = team.get("color", "#3366cc")
                    st.markdown(
                        f"<div style='display:flex;align-items:center;'>"
                        f"<div style='width:15px;height:15px;background-color:{color};margin-right:5px;border-radius:3px;'></div>"
                        f"<div>{team.get('name', 'Unknown')}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
    else:
        st.info("No data available to visualize. Add team members and reporting relationships.")

def render_team_list():
    """Render the team members list view."""
    st.subheader("Team Members List")
    
    # Load team structure
    structure = load_team_structure()
    teams = structure.get("teams", [])
    members = structure.get("members", [])
    
    if not members:
        st.info("No team members have been added yet.")
        return
    
    # Filter options
    all_teams = [{"id": "", "name": "All Teams"}] + teams
    selected_team = st.selectbox(
        "Filter by Team",
        options=[t.get("id") for t in all_teams],
        format_func=lambda x: next((t.get("name") for t in all_teams if t.get("id") == x), "Unknown"),
        index=0
    )
    
    # Apply filter
    if selected_team:
        filtered_members = [m for m in members if m.get("team_id") == selected_team]
    else:
        filtered_members = members
    
    # Prepare data for display
    display_data = []
    for member in filtered_members:
        team_id = member.get("team_id")
        manager_id = member.get("manager_id")
        
        team_name = next((t.get("name") for t in teams if t.get("id") == team_id), "None")
        manager_name = next((m.get("name") for m in members if m.get("id") == manager_id), "None")
        
        display_data.append({
            "Name": member.get("name", "Unknown"),
            "Title": member.get("title", ""),
            "Team": team_name,
            "Reports To": manager_name,
            "Email": member.get("email", "")
        })
    
    # Display as table
    if display_data:
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)
    else:
        st.info("No team members match the selected filter.")
    
    # Export options
    st.download_button(
        "Export to CSV",
        pd.DataFrame(display_data).to_csv(index=False).encode('utf-8'),
        "team_members.csv",
        "text/csv",
        key='download-csv'
    )

def render_team_management():
    """Render the team management interface."""
    st.subheader("Team Management")
    
    # Create tabs for teams and members
    mng_tab1, mng_tab2, mng_tab3 = st.tabs(["Teams", "Members", "Import"])
    
    with mng_tab1:
        render_team_management_section()
    
    with mng_tab2:
        render_member_management_section()
    
    with mng_tab3:
        render_import_section()

def render_team_management_section():
    """Render the team management section."""
    st.subheader("Manage Teams")
    
    # Load existing teams
    structure = load_team_structure()
    teams = structure.get("teams", [])
    
    # Create team form
    with st.form("create_team_form"):
        st.write("Add New Team")
        team_name = st.text_input("Team Name")
        team_description = st.text_area("Description")
        team_color = st.color_picker("Team Color", "#3366cc")
        
        submit_btn = st.form_submit_button("Add Team")
        
        if submit_btn and team_name:
            team_id = add_team(team_name, team_description, team_color)
            if team_id:
                st.success(f"Team '{team_name}' added successfully!")
                st.rerun()
    
    # Display existing teams
    if teams:
        st.subheader("Existing Teams")
        
        for i, team in enumerate(teams):
            with st.expander(f"{team.get('name', 'Unknown')}"):
                # Display team details
                st.write(f"**Description:** {team.get('description', 'No description')}")
                st.markdown(
                    f"<div style='display:flex;align-items:center;'>"
                    f"<div>Team Color: </div>"
                    f"<div style='width:15px;height:15px;background-color:{team.get('color', '#3366cc')};margin-left:5px;border-radius:3px;'></div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                
                # Edit team form
                with st.form(f"edit_team_{i}"):
                    edit_name = st.text_input("Team Name", value=team.get("name", ""))
                    edit_description = st.text_area("Description", value=team.get("description", ""))
                    edit_color = st.color_picker("Team Color", value=team.get("color", "#3366cc"))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("Update Team")
                    with col2:
                        delete_btn = st.form_submit_button("Delete Team", type="secondary")
                    
                    if update_btn:
                        if update_team(team.get("id"), edit_name, edit_description, edit_color):
                            st.success("Team updated successfully!")
                            st.rerun()
                    
                    if delete_btn:
                        if delete_team(team.get("id")):
                            st.success("Team deleted successfully!")
                            st.rerun()
    else:
        st.info("No teams have been created yet.")

def render_member_management_section():
    """Render the member management section."""
    st.subheader("Manage Team Members")
    
    # Load existing data
    structure = load_team_structure()
    teams = structure.get("teams", [])
    members = structure.get("members", [])
    
    # Create member form
    with st.form("create_member_form"):
        st.write("Add New Team Member")
        
        member_name = st.text_input("Name")
        member_title = st.text_input("Job Title")
        member_email = st.text_input("Email")
        
        # Team selection
        team_options = [{"id": None, "name": "No Team"}] + teams
        team_id = st.selectbox(
            "Team",
            options=[t.get("id") for t in team_options],
            format_func=lambda x: next((t.get("name") for t in team_options if t.get("id") == x), "Unknown")
        )
        
        # Manager selection
        manager_options = [{"id": None, "name": "No Manager"}] + members
        manager_id = st.selectbox(
            "Reports To",
            options=[m.get("id") for m in manager_options],
            format_func=lambda x: next((m.get("name") for m in manager_options if m.get("id") == x), "Unknown")
        )
        
        submit_btn = st.form_submit_button("Add Team Member")
        
        if submit_btn and member_name:
            member_id = add_member(member_name, member_title, member_email, team_id, manager_id)
            if member_id:
                st.success(f"Team member '{member_name}' added successfully!")
                st.rerun()
    
    # Display existing members
    if members:
        st.subheader("Existing Team Members")
        
        for i, member in enumerate(members):
            with st.expander(f"{member.get('name', 'Unknown')} ({member.get('title', 'No title')})"):
                # Display member details
                team_id = member.get("team_id")
                manager_id = member.get("manager_id")
                
                team_name = next((t.get("name") for t in teams if t.get("id") == team_id), "None")
                manager_name = next((m.get("name") for m in members if m.get("id") == manager_id), "None")
                
                st.write(f"**Team:** {team_name}")
                st.write(f"**Reports To:** {manager_name}")
                st.write(f"**Email:** {member.get('email', 'No email')}")
                
                # Edit member form
                with st.form(f"edit_member_{i}"):
                    edit_name = st.text_input("Name", value=member.get("name", ""))
                    edit_title = st.text_input("Job Title", value=member.get("title", ""))
                    edit_email = st.text_input("Email", value=member.get("email", ""))
                    
                    # Team selection
                    edit_team_id = st.selectbox(
                        "Team",
                        options=[t.get("id") for t in team_options],
                        format_func=lambda x: next((t.get("name") for t in team_options if t.get("id") == x), "Unknown"),
                        index=next((i for i, t in enumerate(team_options) if t.get("id") == team_id), 0)
                    )
                    
                    # Manager selection - filter out self and direct reports to avoid cycles
                    member_id = member.get("id")
                    valid_managers = [m for m in manager_options if m.get("id") != member_id]
                    
                    # Recursively get all reports to exclude them as potential managers
                    def get_all_reports(mid):
                        direct_reports = [m.get("id") for m in members if m.get("manager_id") == mid]
                        all_reports = list(direct_reports)
                        for rid in direct_reports:
                            all_reports.extend(get_all_reports(rid))
                        return all_reports
                    
                    all_reports = get_all_reports(member_id)
                    valid_managers = [m for m in valid_managers if m.get("id") not in all_reports]
                    
                    edit_manager_id = st.selectbox(
                        "Reports To",
                        options=[m.get("id") for m in valid_managers],
                        format_func=lambda x: next((m.get("name") for m in valid_managers if m.get("id") == x), "Unknown"),
                        index=next((i for i, m in enumerate(valid_managers) if m.get("id") == manager_id), 0)
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("Update Member")
                    with col2:
                        delete_btn = st.form_submit_button("Delete Member", type="secondary")
                    
                    if update_btn:
                        if update_member(member_id, edit_name, edit_title, edit_email, edit_team_id, edit_manager_id):
                            st.success("Team member updated successfully!")
                            st.rerun()
                    
                    if delete_btn:
                        if delete_member(member_id):
                            st.success("Team member deleted successfully!")
                            st.rerun()
    else:
        st.info("No team members have been added yet.")

def render_import_section():
    """Render the import section."""
    st.subheader("Import Organization")
    
    # Import from users
    st.write("Import team members from registered users:")
    if st.button("Import from Users"):
        count = import_organization_from_users()
        if count > 0:
            st.success(f"Successfully imported {count} users as team members.")
            st.rerun()
        else:
            st.info("No new users to import.")
    
    # Import/export organization data
    st.divider()
    st.subheader("Import/Export Team Structure")
    
    # Export
    structure = load_team_structure()
    if structure.get("teams") or structure.get("members"):
        # Ensure the structure can be serialized to JSON
        serializable_structure = {
            "teams": [],
            "members": [],
            "relationships": []
        }
        
        # Copy teams with serializable data
        for team in structure.get("teams", []):
            serializable_team = {k: v for k, v in team.items() if not isinstance(v, (type, function))}
            serializable_structure["teams"].append(serializable_team)
        
        # Copy members with serializable data
        for member in structure.get("members", []):
            serializable_member = {k: v for k, v in member.items() if not isinstance(v, (type, function))}
            serializable_structure["members"].append(serializable_member)
        
        # Copy relationships with serializable data
        for rel in structure.get("relationships", []):
            serializable_rel = {k: v for k, v in rel.items() if not isinstance(v, (type, function))}
            serializable_structure["relationships"].append(serializable_rel)
        
        try:
            # Serialize to JSON
            json_str = json.dumps(serializable_structure, indent=2)
            
            st.download_button(
                "Export Team Structure",
                json_str,
                "team_structure.json",
                "application/json",
                key='download-structure'
            )
        except Exception as e:
            st.error(f"Error exporting structure: {str(e)}")
    
    # Import
    uploaded_file = st.file_uploader("Import Team Structure from JSON", type="json")
    if uploaded_file is not None:
        try:
            imported_structure = json.load(uploaded_file)
            
            # Validate structure
            if "teams" in imported_structure and "members" in imported_structure and "relationships" in imported_structure:
                if st.button("Confirm Import"):
                    if save_team_structure(imported_structure):
                        st.success("Team structure imported successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to import team structure.")
            else:
                st.error("Invalid team structure file format.")
        except Exception as e:
            st.error(f"Error importing team structure: {str(e)}")
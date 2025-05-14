import streamlit as st
import pandas as pd

def render_current_activities():
    st.subheader("📋 Current Activities")
    st.write("What are you currently working on? Include priority and status.")

    # Initialize DataFrame in session state
    if "current_activities" not in st.session_state:
        st.session_state.current_activities = pd.DataFrame(
            columns=[
                "Project",
                "Milestone",
                "Priority",
                "Status",
                "Deadline",
                "Customer",
                "Billable",
                "% Complete",
                "Description",
            ]
        )

    # Render data editor
    edited_df = st.data_editor(
        st.session_state.current_activities,
        column_config={
            "Project": st.column_config.TextColumn(),
            "Milestone": st.column_config.TextColumn(),
            "Priority": st.column_config.SelectboxColumn(
                "Priority", options=["High", "Medium", "Low"]
            ),
            "Status": st.column_config.SelectboxColumn(
                "Status", options=["Not Started", "In Progress", "Blocked", "Complete"]
            ),
            "Deadline": st.column_config.DateColumn("Deadline"),
            "Customer": st.column_config.TextColumn(),
            "Billable": st.column_config.SelectboxColumn(
                "Billable", options=["Yes", "No"]
            ),
            "% Complete": st.column_config.SliderColumn(
                "% Complete", min_value=0, max_value=100
            ),
            "Description": st.column_config.TextColumn(),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="current_activities_editor",
    )

    # Save back to session state
    st.session_state.current_activities = edited_df

import streamlit as st
import pandas as pd

def render_action_items():
    st.subheader("📝 Action Items")
    st.write("What follow-up tasks were assigned to you?")

    # Initialize DataFrame in session state
    if "action_items" not in st.session_state:
        st.session_state.action_items = pd.DataFrame(columns=["Action Item"])

    # Render data editor
    edited_df = st.data_editor(
        st.session_state.action_items,
        column_config={
            "Action Item": st.column_config.TextColumn(
                "Action Item",
                placeholder="Describe this follow-up task…"
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        key="action_items_editor",
    )

    # Save back to session state
    st.session_state.action_items = edited_df

import streamlit as st
import pandas as pd

def render_accomplishments():
    st.subheader("✓ Last Week's Accomplishments")
    st.write("What did you accomplish last week? (Bullet points work best)")

    # Initialize DataFrame in session state
    if "accomplishments" not in st.session_state:
        st.session_state.accomplishments = pd.DataFrame(columns=["Accomplishment"])

    # Render data editor
    edited_df = st.data_editor(
        st.session_state.accomplishments,
        column_config={
            "Accomplishment": st.column_config.TextColumn(
                "Accomplishment",
                placeholder="Describe what you completed…"
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        key="accomplishments_editor",
    )

    # Save back to session state
    st.session_state.accomplishments = edited_df

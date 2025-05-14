import streamlit as st
import pandas as pd

def render_simple_action_items():
    """
    Render the simplified action items section.
    
    This covers both:
      1. Follow-up tasks from last meeting
      2. Next steps planned for next week
    using a single dynamic DataFrame each.
    """
    st.subheader("📝 Action Items")

    # FOLLOW-UPS from last meeting
    st.write("**From Last Meeting** – What follow-up tasks were assigned to you?")
    if "followups" not in st.session_state:
        st.session_state.followups = pd.DataFrame(columns=["Follow-up Task"])
    followups_df = st.data_editor(
        st.session_state.followups,
        column_config={
            "Follow-up Task": st.column_config.TextColumn(
                "Follow-up Task",
                placeholder="Describe this follow-up task…"
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        key="followups_editor",
    )
    st.session_state.followups = followups_df

    st.markdown("---")

    # NEXT STEPS for coming week
    st.write("**Next Steps** – What action items are planned for next week?")
    if "nextsteps" not in st.session_state:
        st.session_state.nextsteps = pd.DataFrame(columns=["Next Step"])
    nextsteps_df = st.data_editor(
        st.session_state.nextsteps,
        column_config={
            "Next Step": st.column_config.TextColumn(
                "Next Step",
                placeholder="Describe this planned action…"
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        key="nextsteps_editor",
    )
    st.session_state.nextsteps = nextsteps_df

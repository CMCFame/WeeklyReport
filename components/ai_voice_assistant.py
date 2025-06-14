# components/ai_voice_assistant.py
"""AI Voice Assistant for speech-to-text report creation."""

import streamlit as st
from audio_recorder_streamlit import audio_recorder
from utils.ai_utils import (
    transcribe_audio,
    structure_voice_input,
    setup_openai_api,
    calculate_report_readiness_score
)
from utils.session import (
    init_session_state,
    collect_form_data,
    load_report_data
)
from utils.file_ops import save_report
from datetime import datetime
import json
import time

# --- Helper function to add log messages ---
def add_log_message(message, level="info"):
    """Adds a message to the session's log."""
    if 'log_messages' not in st.session_state:
        st.session_state.log_messages = []
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    # Prepend new messages to the list
    st.session_state.log_messages.insert(0, f'<div class="log-entry"><span class="log-timestamp">[{timestamp}]</span> <span class="log-{level}">{message}</span></div>')
    # Keep the log from getting too long
    st.session_state.log_messages = st.session_state.log_messages[:50]

def render_ai_voice_assistant():
    """Render the AI Voice Assistant for creating reports via speech."""
    st.title("🎤 AI Voice Assistant")
    st.write("Create your weekly report by speaking naturally - AI will structure your update automatically")

    # --- START: Log Display Setup ---
    st.subheader("Diagnostic Log")
    st.markdown("""
    <style>
        .log-container {
            background-color: #262730;
            color: #FAFAFA;
            border-radius: 10px;
            padding: 15px;
            height: 250px;
            overflow-y: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
        }
        .log-entry { margin-bottom: 5px; }
        .log-timestamp { color: #A9A9A9; }
        .log-success { color: #28a745; }
        .log-error { color: #dc3545; }
        .log-info { color: #17a2b8; }
    </style>
    """, unsafe_allow_html=True)

    log_placeholder = st.empty()
    # --- END: Log Display Setup ---
    
    # --- START: State Initialization and Logging Fix ---
    # This flag ensures initialization only happens once per session/page visit.
    if 'voice_assistant_initialized' not in st.session_state:
        st.session_state.voice_assistant_initialized = False
        st.session_state.log_messages = [] # Clear logs on first load
    
    if not st.session_state.voice_assistant_initialized:
        add_log_message("Voice assistant initialized. Waiting for user action.")
        st.session_state.voice_assistant_initialized = True # Set flag to true
    # --- END: State Initialization and Logging Fix ---

    # Check if OpenAI API is configured
    if not setup_openai_api():
        add_log_message("OpenAI API key not configured. Voice features disabled.", "error")
        log_placeholder.markdown(f'<div class="log-container">{"".join(st.session_state.log_messages)}</div>', unsafe_allow_html=True)
        st.info("👆 Please configure your OpenAI API key above to use the Voice Assistant.")
        return
    
    # Initialize session state for the report form itself
    init_session_state()

    # Initialize processing state variables if they don't exist
    if 'is_processing_audio' not in st.session_state:
        st.session_state.is_processing_audio = False
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None
    if 'audio_bytes_to_process' not in st.session_state:
        st.session_state.audio_bytes_to_process = None
    if 'transcription_source' not in st.session_state:
        st.session_state.transcription_source = None
    if 'processing_started_this_run' not in st.session_state:
        st.session_state.processing_started_this_run = False
    if 'audio_recorded_but_not_processed' not in st.session_state:
        st.session_state.audio_recorded_but_not_processed = False

    if st.button("Clear Log and Start Over"):
        clear_voice_session_data()
        st.session_state.log_messages = []
        add_log_message("Session cleared. Ready to start over.")
        st.session_state.voice_assistant_initialized = False # Allow re-initialization
        st.rerun()

    # Voice recording section
    render_voice_recording_section()
    
    # This block runs on every rerun if processing is active
    if st.session_state.is_processing_audio and not st.session_state.get('processing_started_this_run', False):
        st.session_state.processing_started_this_run = True
        with st.spinner(st.session_state.get('processing_status', "Processing...")):
            _run_audio_processing_pipeline(
                st.session_state.audio_bytes_to_process,
                st.session_state.transcription_source
            )

    # Processing and review sections
    if st.session_state.get('voice_transcription') or st.session_state.get('structured_voice_data'):
        render_transcription_review()
    
    if st.session_state.get('structured_voice_data'):
        render_structured_data_review()

    # Display the log at the end of the render function
    log_placeholder.markdown(f'<div class="log-container">{"".join(st.session_state.log_messages)}</div>', unsafe_allow_html=True)

def _run_audio_processing_pipeline(input_data, transcription_source):
    """
    Internal function to handle the long-running audio processing pipeline.
    Updates session state with progress and status.
    """
    if transcription_source == "audio":
        st.session_state.voice_session_stats['recordings_made'] += 1
        add_log_message("Recording captured. Incrementing session stats.", "info")

    try:
        if transcription_source == "audio":
            st.session_state.processing_status = "🎯 Step 1: Converting speech to text..."
            add_log_message("Starting audio transcription...", "info")
            transcription = transcribe_audio(input_data)
            
            if transcription.startswith("Transcription failed") or transcription.startswith("Transcription unavailable"):
                st.error(f"❌ {transcription}")
                add_log_message(f"Transcription failed: {transcription}", "error")
                st.session_state.processing_status = "Transcription failed."
                return
            
            add_log_message("Transcription successful.", "success")
            st.session_state.voice_transcription = transcription
        else:
            transcription = st.session_state.voice_transcription
            add_log_message("Using edited text for processing.", "info")
            
        st.session_state.processing_status = "🧠 Step 2: Analyzing and structuring content with AI..."
        add_log_message("Structuring text with AI...", "info")
        structured_data = structure_voice_input(transcription)
        
        if 'error' in structured_data:
            st.error(f"❌ {structured_data['error']}")
            add_log_message(f"AI structuring failed: {structured_data['error']}", "error")
            st.session_state.processing_status = "Structuring failed."
            return
        
        st.session_state.structured_voice_data = structured_data
        st.session_state.voice_session_stats['transcriptions_processed'] += 1
        
        st.success("✅ Processing complete! Review your structured report below.")
        add_log_message("Processing complete!", "success")
        st.session_state.processing_status = "Processing complete."
        
    except Exception as e:
        st.error(f"An unexpected error occurred during processing: {str(e)}")
        add_log_message(f"An unexpected error occurred: {str(e)}", "error")
        st.session_state.processing_status = f"Error: {str(e)}"
    finally:
        st.session_state.is_processing_audio = False
        st.session_state.processing_started_this_run = False
        st.session_state.audio_bytes_to_process = None
        st.session_state.transcription_source = None
        st.session_state.audio_recorded_but_not_processed = False
        st.rerun()

def render_voice_recording_section():
    """Render the voice recording interface."""
    st.subheader("🎙️ Voice Recording")
    
    with st.expander("📋 Recording Tips & Guidelines", expanded=False):
        st.markdown("""
        ### What to Include in Your Update:
        
        **Current Work (2-3 minutes):**
        - Projects you're working on this week
        - Progress percentages (e.g., "about 80% complete")
        - Current status and priorities
        - Any blockers or dependencies
        
        **Accomplishments (1-2 minutes):**
        - What you completed last week
        - Specific outcomes and deliverables
        - Wins and milestones reached
        
        **Challenges & Next Steps (1-2 minutes):**
        - Any challenges you're facing
        - Support or resources needed
        - Plans for next week
        
        ### Speaking Tips:
        - Speak clearly at normal pace
        - Mention specific project names
        - Use phrases like "high priority," "medium priority"
        - Be specific about percentages and timelines
        - Pause briefly between different topics
        
        ### Example Opening:
        *"This week I'm working on three main projects. First is the mobile app authentication module, which is about 80% complete and high priority. I'm currently integrating with the new API..."*
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Start Recording Your Update")
        st.info("💡 **Optimal length:** 3-5 minutes for a complete update")
        
        status_message_placeholder = st.empty()
        
        if st.session_state.is_processing_audio:
            status_message_placeholder.info(st.session_state.get('processing_status', "Processing..."))
        elif st.session_state.audio_recorded_but_not_processed:
            status_message_placeholder.success("🎵 Recording captured! Click 'Process Recording' below to continue.")
        elif st.session_state.get('processing_status') == "Processing complete.":
            status_message_placeholder.success("✅ Processing complete! Review your structured report below.")
        elif st.session_state.get('processing_status') and "failed" in st.session_state.get('processing_status', '').lower():
            status_message_placeholder.error(st.session_state.get('processing_status'))
        else:
            status_message_placeholder.info("Click the microphone to start recording. Pause for 3 seconds to stop.")
        
        audio_bytes = audio_recorder(
            text="Click to start recording (button color changes when recording)",
            recording_color="#e74c3c",
            neutral_color="#34495e",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=3.0,
            sample_rate=16000,
        )
        
        if audio_bytes and not st.session_state.is_processing_audio and not st.session_state.get('audio_bytes_to_process_already_set', False):
            st.audio(audio_bytes, format="audio/wav")
            add_log_message("Audio recording detected.", "info")
            st.session_state.audio_recorded_but_not_processed = True
            st.session_state.audio_bytes_to_process = audio_bytes
            st.session_state.transcription_source = "audio"
            st.session_state.audio_bytes_to_process_already_set = True
            st.rerun()
        
    with col2:
        st.write("### Quick Stats")
        
        if 'voice_session_stats' not in st.session_state:
            st.session_state.voice_session_stats = {'recordings_made': 0, 'transcriptions_processed': 0, 'reports_created': 0}
        
        stats = st.session_state.voice_session_stats
        st.metric("Recordings Made", stats['recordings_made'])
        st.metric("Processed", stats['transcriptions_processed'])
        st.metric("Reports Created", stats['reports_created'])
        
        if st.session_state.get('audio_bytes_to_process'):
            audio_size = len(st.session_state.audio_bytes_to_process)
            duration_estimate = audio_size / 32000 
            
            if duration_estimate > 30: 
                st.success(f"✅ Good length ({duration_estimate:.1f} seconds)")
            elif duration_estimate > 10: 
                st.warning(f"⚠️ Short recording ({duration_estimate:.1f} seconds)")
            else:
                st.error(f"❌ Too short ({duration_estimate:.1f} seconds)")
            
            st.write(f"**Estimated duration:** ~{duration_estimate:.1f} seconds")

    if st.session_state.get('audio_bytes_to_process') and not st.session_state.is_processing_audio:
        col_process1, col_process2 = st.columns(2)
        with col_process1:
            if st.button("🔄 Record Again", use_container_width=True, key="record_again_btn"):
                add_log_message("User chose to record again. Clearing previous audio.", "info")
                clear_voice_session_data()
                st.rerun()
        with col_process2:
            if st.button("🚀 Process Recording", type="primary", use_container_width=True, key="process_recording_btn"):
                add_log_message("User initiated processing.", "info")
                st.session_state.is_processing_audio = True
                st.session_state.processing_status = "Initiating processing..."
                st.session_state.audio_recorded_but_not_processed = False
                st.rerun()

def render_transcription_review():
    """Render the transcription review section."""
    st.subheader("📝 Speech Transcription")
    
    transcription = st.session_state.voice_transcription
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        edited_transcription = st.text_area(
            "Review and edit your transcription:",
            value=transcription,
            height=200,
            help="You can edit the transcription if there are any errors",
            key="voice_transcription_edit" 
        )
        
        if edited_transcription != st.session_state.voice_transcription:
            st.session_state.voice_transcription = edited_transcription
            if 'structured_voice_data' in st.session_state:
                del st.session_state.structured_voice_data
            st.session_state.processing_status = "Transcription edited. Click 'Re-process' to update structured data."
            add_log_message("Transcription edited by user.", "info")
            st.info("Transcription edited. Click 'Re-process' to update structured data.")
            st.rerun() 
    
    with col2:
        st.write("### Transcription Quality")
        
        word_count = len(st.session_state.voice_transcription.split())
        
        if word_count > 200:
            quality = "Excellent"
            quality_color = "green"
        elif word_count > 100:
            quality = "Good"
            quality_color = "blue"
        elif word_count > 50:
            quality = "Fair"
            quality_color = "orange"
        else:
            quality = "Poor"
            quality_color = "red"
        
        st.markdown(f"<span style='color: {quality_color};'>**Quality:** {quality}</span>", unsafe_allow_html=True)
        st.write(f"**Word count:** {word_count}")
        
        content_keywords = {
            'Projects': ['project', 'working on', 'developing', 'building'],
            'Progress': ['percent', '%', 'complete', 'finished', 'progress'],
            'Challenges': ['challenge', 'blocker', 'blocked', 'difficult', 'problem'],
            'Accomplishments': ['completed', 'finished', 'accomplished', 'delivered']
        }
        
        st.write("**Detected content:**")
        detected_content = []
        for category, keywords in content_keywords.items():
            if any(keyword in st.session_state.voice_transcription.lower() for keyword in keywords):
                detected_content.append(category)
        
        if detected_content:
            for content in detected_content:
                st.write(f"✅ {content}")
        else:
            st.write("No key content detected. Try speaking more clearly.")
        
        is_reprocess_enabled = (st.session_state.get('processing_status') == "Transcription edited. Click 'Re-process' to update structured data." or \
                                st.session_state.get('processing_status') == "Structuring failed.") and \
                                not st.session_state.is_processing_audio
        
        if st.button("🔄 Re-process", use_container_width=True, disabled=not is_reprocess_enabled, key="reprocess_transcription_btn"):
            add_log_message("User initiated re-processing from edited text.", "info")
            st.session_state.is_processing_audio = True
            st.session_state.processing_status = "Initiating re-processing from edited text..."
            st.session_state.audio_bytes_to_process = st.session_state.voice_transcription
            st.session_state.transcription_source = "text"
            st.rerun()

def render_structured_data_review():
    """Render the structured data review and form population."""
    st.subheader("🧠 AI-Structured Report Data")
    
    structured_data = st.session_state.structured_voice_data
    
    with st.expander("🔍 View AI Analysis", expanded=False):
        st.json(structured_data)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Review Extracted Information")
        
        if structured_data.get('current_activities'):
            st.write("**Current Activities:**")
            for i, activity in enumerate(structured_data['current_activities']):
                with st.expander(f"Activity {i+1}: {activity.get('description', 'No description')[:50]}..."):
                    activity['description'] = st.text_area("Description", value=activity.get('description', ''), key=f"voice_act_desc_{i}")
                    col_proj, col_prio = st.columns(2)
                    with col_proj:
                        activity['project'] = st.text_input("Project", value=activity.get('project', ''), key=f"voice_act_proj_{i}")
                    with col_prio:
                        priority_options = ["High", "Medium", "Low"]
                        current_priority = activity.get('priority', 'Medium')
                        if current_priority not in priority_options:
                            priority_options.append(current_priority)
                        activity['priority'] = st.selectbox("Priority", options=priority_options, index=priority_options.index(current_priority), key=f"voice_act_prio_{i}")
                    col_status, col_progress = st.columns(2)
                    with col_status:
                        status_options = ["Not Started", "In Progress", "Blocked", "Completed"]
                        current_status = activity.get('status', 'In Progress')
                        if current_status not in status_options:
                            status_options.append(current_status)
                        activity['status'] = st.selectbox("Status", options=status_options, index=status_options.index(current_status), key=f"voice_act_status_{i}")
                    with col_progress:
                        activity['progress'] = st.slider("Progress", min_value=0, max_value=100, value=int(activity.get('progress', 50)), key=f"voice_act_progress_{i}")
        
        if structured_data.get('accomplishments'):
            st.write("**Accomplishments:**")
            for i, accomplishment in enumerate(structured_data['accomplishments']):
                structured_data['accomplishments'][i] = st.text_area(f"Accomplishment {i+1}", value=accomplishment, key=f"voice_acc_{i}")
        
        if structured_data.get('challenges'):
            st.write("**Challenges:**")
            structured_data['challenges'] = st.text_area("Challenges", value=structured_data['challenges'], key="voice_challenges")
        
        if structured_data.get('nextsteps'):
            st.write("**Next Steps:**")
            for i, step in enumerate(structured_data['nextsteps']):
                structured_data['nextsteps'][i] = st.text_area(f"Next Step {i+1}", value=step, key=f"voice_next_{i}")
    
    with col2:
        st.write("### Report Readiness")
        
        report_data = {
            'current_activities': structured_data.get('current_activities', []),
            'accomplishments': structured_data.get('accomplishments', []),
            'challenges': structured_data.get('challenges', ''),
            'nextsteps': structured_data.get('nextsteps', []),
            'name': st.session_state.get('name', ''),
            'reporting_week': st.session_state.get('reporting_week', '')
        }
        
        readiness = calculate_report_readiness_score(report_data)
        
        score = readiness['score']
        if score >= 80:
            st.success(f"**Score:** {score}/100")
        elif score >= 60:
            st.warning(f"**Score:** {score}/100")
        else:
            st.error(f"**Score:** {score}/100")
        
        st.write(f"**Level:** {readiness['readiness_level']}")
        
        if readiness['feedback']:
            st.write("**Suggestions:**")
            for feedback in readiness['feedback']:
                st.write(f"• {feedback}")
        
        st.write("### Actions")
        
        if st.button("📋 Load to Form", type="primary", use_container_width=True, key="load_to_form_btn"):
            load_voice_data_to_form(structured_data)
        
        if st.button("💾 Save as Draft", use_container_width=True, key="save_draft_btn"):
            save_voice_report_as_draft(structured_data)
        
        if score >= 70:
            if st.button("🚀 Submit Report", use_container_width=True, key="submit_report_btn"):
                save_voice_report_as_final(structured_data)
        else:
            st.info("Complete missing sections to enable submission")
        
        if st.button("🔄 Start Over", use_container_width=True, key="start_over_btn"):
            clear_voice_session_data()
            st.rerun()

def load_voice_data_to_form(structured_data):
    """Load voice data into the main report form."""
    try:
        if structured_data.get('current_activities'):
            st.session_state.current_activities = structured_data['current_activities']
            st.session_state.show_current_activities = True
        
        if structured_data.get('accomplishments'):
            st.session_state.accomplishments = structured_data['accomplishments']
            st.session_state.show_accomplishments = True
        
        if structured_data.get('challenges'):
            st.session_state.challenges = structured_data['challenges']
            st.session_state.show_challenges = True
        
        if structured_data.get('nextsteps'):
            st.session_state.nextsteps = structured_data['nextsteps']
            st.session_state.show_action_items = True
        
        clear_voice_session_data()
        
        st.success("✅ Voice data loaded into report form! Navigate to 'Weekly Report' to continue editing.")
        
        st.session_state.nav_page = "Weekly Report"
        st.session_state.nav_section = "reporting"
        
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error loading data to form: {str(e)}")

def save_voice_report_as_draft(structured_data):
    """Save the voice report as a draft."""
    try:
        report_data = create_report_from_voice_data(structured_data)
        report_data['status'] = 'draft'
        
        report_id = save_report(report_data)
        
        if report_id:
            st.session_state.voice_session_stats['reports_created'] += 1
            st.success("📝 Report saved as draft!")
            
            clear_voice_session_data()
            
            time.sleep(2)
            st.rerun()
        else:
            st.error("Failed to save report")
    
    except Exception as e:
        st.error(f"Error saving draft: {str(e)}")

def save_voice_report_as_final(structured_data):
    """Save the voice report as final submission."""
    try:
        report_data = create_report_from_voice_data(structured_data)
        report_data['status'] = 'submitted'
        
        if not report_data.get('name'):
            st.error("Please set your name in the session first")
            return
        
        report_id = save_report(report_data)
        
        if report_id:
            st.session_state.voice_session_stats['reports_created'] += 1
            st.success("🎉 Report submitted successfully!")
            
            clear_voice_session_data()
            
            time.sleep(2)
            st.rerun()
        else:
            st.error("Failed to submit report")
    
    except Exception as e:
        st.error(f"Error submitting report: {str(e)}")

def create_report_from_voice_data(structured_data):
    """Create a complete report data structure from voice data."""
    return {
        'name': st.session_state.get('name', 'Voice User'),
        'reporting_week': st.session_state.get('reporting_week', f"W{datetime.now().isocalendar()[1]} {datetime.now().year}"),
        'current_activities': structured_data.get('current_activities', []),
        'upcoming_activities': [],
        'accomplishments': structured_data.get('accomplishments', []),
        'followups': [],
        'nextsteps': structured_data.get('nextsteps', []),
        'challenges': structured_data.get('challenges', ''),
        'timestamp': datetime.now().isoformat()
    }

def clear_voice_session_data():
    """Clear all voice-related session data."""
    keys_to_clear = [
        'voice_transcription', 'structured_voice_data', 'processing_status',
        'audio_bytes_to_process', 'transcription_source', 'processing_started_this_run',
        'audio_recorded_but_not_processed', 'audio_bytes_to_process_already_set'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # This flag should also be reset to allow the "initialized" message on the next visit
    if 'voice_assistant_initialized' in st.session_state:
        del st.session_state['voice_assistant_initialized']

def render_voice_assistant_tips():
    """Render tips for using the voice assistant effectively."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎤 Voice Assistant Tips")
    
    tips = [
        "Speak clearly and at normal pace",
        "Mention specific project names",
        "Include progress percentages",
        "State priorities explicitly",
        "Describe challenges you're facing",
        "Keep recordings 3-5 minutes long"
    ]
    
    for tip in tips:
        st.sidebar.write(f"• {tip}")
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Best Practice:** Review and edit the AI-structured content before submitting your report.")

def get_voice_usage_stats():
    """Get usage statistics for the voice assistant."""
    if 'voice_session_stats' not in st.session_state:
        return {
            'recordings_made': 0,
            'transcriptions_processed': 0,
            'reports_created': 0,
            'success_rate': 0
        }
    
    stats = st.session_state.voice_session_stats
    success_rate = (stats['reports_created'] / max(stats['recordings_made'], 1)) * 100
    
    return {
        **stats,
        'success_rate': success_rate
    }

def render_voice_analytics():
    """Render analytics for voice assistant usage."""
    with st.expander("📊 Voice Assistant Analytics"):
        stats = get_voice_usage_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Recordings", stats['recordings_made'])
        with col2:
            st.metric("Processed", stats['transcriptions_processed'])
        with col3:
            st.metric("Reports Created", stats['reports_created'])
        with col4:
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
        
        if stats['recordings_made'] > 0:
            st.progress(stats['success_rate'] / 100)
            
            if stats['success_rate'] >= 80:
                st.success("🌟 Excellent voice assistant usage!")
            elif stats['success_rate'] >= 60:
                st.info("👍 Good voice assistant usage")
            else:
                st.warning("💡 Consider reviewing voice recording tips for better results")
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

def render_ai_voice_assistant():
    """Render the AI Voice Assistant for creating reports via speech."""
    st.title("🎤 AI Voice Assistant")
    st.write("Create your weekly report by speaking naturally - AI will structure your update automatically")
    
    # Check if OpenAI API is configured
    if not setup_openai_api():
        st.info("👆 Please configure your OpenAI API key above to use the Voice Assistant.")
        return
    
    # Initialize session state
    init_session_state()
    
    # Initialize processing state variables if they don't exist
    if 'is_processing_audio' not in st.session_state:
        st.session_state.is_processing_audio = False
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None # Clear status when starting fresh
    if 'audio_bytes_to_process' not in st.session_state: # To store audio across reruns
        st.session_state.audio_bytes_to_process = None
    if 'transcription_source' not in st.session_state: # To indicate if processing audio or edited text
        st.session_state.transcription_source = None
    if 'processing_started_this_run' not in st.session_state: # Flag to ensure pipeline runs only once per trigger
        st.session_state.processing_started_this_run = False

    # Voice recording section
    render_voice_recording_section()
    
    # This block runs on every rerun. If processing is active, it initiates the pipeline.
    # It must be placed here, outside any button's if block, to run on subsequent reruns.
    if st.session_state.is_processing_audio and not st.session_state.get('processing_started_this_run', False):
        st.session_state.processing_started_this_run = True # Set flag to prevent re-entry in same run
        with st.spinner(st.session_state.get('processing_status', "Processing...")):
            # Call the actual processing function
            _run_audio_processing_pipeline(
                st.session_state.audio_bytes_to_process,
                st.session_state.transcription_source
            )
        # The _run_audio_processing_pipeline will handle the final rerun itself.

    # Processing and review section
    # Only show these sections if transcription or structured data is available
    if st.session_state.get('voice_transcription') or st.session_state.get('structured_voice_data'):
        render_transcription_review()
    
    if st.session_state.get('structured_voice_data'):
        render_structured_data_review()

# New helper function to encapsulate the heavy processing logic
def _run_audio_processing_pipeline(input_data, transcription_source):
    """
    Internal function to handle the long-running audio processing pipeline.
    Updates session state with progress and status.
    This function is called on a subsequent rerun after a trigger.
    """
    # Update stats (only for initial audio processing, not re-processing text)
    if transcription_source == "audio":
        st.session_state.voice_session_stats['recordings_made'] += 1
    
    # Progress bar for internal steps (optional, as spinner covers overall progress)
    progress_bar = st.progress(0) # Initialize a local progress bar for steps

    try:
        if transcription_source == "audio":
            st.session_state.processing_status = "🎯 Step 1: Converting speech to text..."
            progress_bar.progress(33)
            transcription = transcribe_audio(input_data)
            
            if transcription.startswith("Transcription failed") or transcription.startswith("Transcription unavailable"):
                st.error(f"❌ {transcription}")
                st.session_state.processing_status = "Transcription failed."
                return # Exit early, finally block will clean up
            
            st.session_state.voice_transcription = transcription
            progress_bar.progress(66)
        else: # Already have transcription from edited text
            transcription = st.session_state.voice_transcription
            progress_bar.progress(66) # Skip transcription step progress
            
        st.session_state.processing_status = "🧠 Step 2: Analyzing and structuring content with AI..."
        structured_data = structure_voice_input(transcription)
        
        progress_bar.progress(100) # Full progress on completion
        
        if 'error' in structured_data:
            st.error(f"❌ {structured_data['error']}")
            st.session_state.processing_status = "Structuring failed."
            return # Exit early, finally block will clean up
        
        st.session_state.structured_voice_data = structured_data
        st.session_state.voice_session_stats['transcriptions_processed'] += 1
        
        st.success("✅ Processing complete! Review your structured report below.")
        st.session_state.processing_status = "Processing complete."
        
    except Exception as e:
        st.error(f"An unexpected error occurred during processing: {str(e)}")
        st.session_state.processing_status = f"Error: {str(e)}"
    finally:
        st.session_state.is_processing_audio = False # Ensure flag is reset
        st.session_state.processing_started_this_run = False # Reset this flag for future triggers
        # Clear temporary audio bytes after processing
        st.session_state.audio_bytes_to_process = None
        st.session_state.transcription_source = None
        st.rerun() # Always rerun to update UI with final state


def render_voice_recording_section():
    """Render the voice recording interface."""
    st.subheader("🎙️ Voice Recording")
    
    # Instructions
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
        
        # Placeholder for dynamic recording/processing status message
        status_message_placeholder = st.empty()
        
        # Display current processing status
        if st.session_state.is_processing_audio:
            status_message_placeholder.info(st.session_state.get('processing_status', "Processing..."))
        elif st.session_state.get('processing_status') == "Processing complete.":
            status_message_placeholder.success("🎵 Recording complete! Audio captured and processed.")
        elif st.session_state.get('processing_status') and "failed" in st.session_state.get('processing_status').lower():
            status_message_placeholder.error(st.session_state.get('processing_status'))
        else:
            status_message_placeholder.info("Click the microphone to start recording. Pause for 3 seconds to stop.")
        
        # Audio recorder
        # Disable the recorder if processing is active
        audio_bytes = audio_recorder(
            text="Click to start recording",
            recording_color="#e74c3c", # Red when recording
            neutral_color="#34495e",   # Dark blue/gray when idle
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=3.0,  # Pause for 3 seconds to stop
            sample_rate=16000,
            # Disable recorder if processing is active
            # This is a limitation of audio-recorder-streamlit, it doesn't have a disabled param.
            # We'll rely on the button disabling and clear session state for re-recording.
        )
        
        # This block executes AFTER recording is finished and audio_bytes is available
        if audio_bytes:
            # Display audio player
            st.audio(audio_bytes, format="audio/wav")
            
            # Processing buttons
            col_process1, col_process2 = st.columns(2)
            
            with col_process1:
                if st.button("🔄 Record Again", use_container_width=True, key="record_again_btn"):
                    clear_voice_session_data()
                    st.rerun()
            
            with col_process2:
                # Disable process button if already processing
                if st.session_state.is_processing_audio:
                    st.button("Processing...", disabled=True, use_container_width=True, key="process_disabled_btn")
                else:
                    if st.button("🚀 Process Recording", type="primary", use_container_width=True, key="process_recording_btn"):
                        # Set processing flag and status, then rerun to show spinner
                        st.session_state.is_processing_audio = True
                        st.session_state.processing_status = "Initiating processing..."
                        st.session_state.audio_bytes_to_process = audio_bytes # Store audio bytes for next run
                        st.session_state.transcription_source = "audio" # Indicate source is audio
                        st.rerun() # Trigger rerun to show spinner and start processing pipeline
        
    with col2:
        st.write("### Quick Stats")
        
        # Show current session stats
        if 'voice_session_stats' not in st.session_state:
            st.session_state.voice_session_stats = {
                'recordings_made': 0,
                'transcriptions_processed': 0,
                'reports_created': 0
            }
        
        stats = st.session_state.voice_session_stats
        st.metric("Recordings Made", stats['recordings_made'])
        st.metric("Processed", stats['transcriptions_processed'])
        st.metric("Reports Created", stats['reports_created'])
        
        # Recording quality indicator
        if audio_bytes:
            audio_size = len(audio_bytes)
            duration_estimate = audio_size / 32000  
            
            if duration_estimate > 30: 
                st.success(f"✅ Good length ({duration_estimate:.1f} seconds)")
            elif duration_estimate > 10: 
                st.warning(f"⚠️ Short recording ({duration_estimate:.1f} seconds)")
            else:
                st.error(f"❌ Too short ({duration_estimate:.1f} seconds)")
            
            st.write(f"**Estimated duration:** ~{duration_estimate:.1f} seconds")


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
        
        # Check if transcription was edited and update session state
        if edited_transcription != st.session_state.voice_transcription:
            st.session_state.voice_transcription = edited_transcription
            # If transcription is edited, clear structured data to force re-processing
            if 'structured_voice_data' in st.session_state:
                del st.session_state.structured_voice_data
            st.session_state.processing_status = "Transcription edited. Click 'Re-process' to update structured data."
            st.info("Transcription edited. Click 'Re-process' to update structured data.")
            st.rerun() 
    
    with col2:
        st.write("### Transcription Quality")
        
        # Analyze transcription quality
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
        
        # Content analysis
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
        
        # Re-process button - enabled if transcription has been edited or if structuring failed, and not currently processing
        is_reprocess_enabled = (st.session_state.get('processing_status') == "Transcription edited. Click 'Re-process' to update structured data." or \
                                st.session_state.get('processing_status') == "Structuring failed.") and \
                                not st.session_state.is_processing_audio
        
        if st.button("🔄 Re-process", use_container_width=True, disabled=not is_reprocess_enabled, key="reprocess_transcription_btn"):
            # Set processing flag and status, then rerun to show spinner
            st.session_state.is_processing_audio = True
            st.session_state.processing_status = "Initiating re-processing from edited text..."
            st.session_state.audio_bytes_to_process = st.session_state.voice_transcription # Store edited text for next run
            st.session_state.transcription_source = "text" # Indicate source is text
            st.rerun() # Trigger rerun to show spinner and start processing pipeline


def render_structured_data_review():
    """Render the structured data review and form population."""
    st.subheader("🧠 AI-Structured Report Data")
    
    structured_data = st.session_state.structured_voice_data
    
    # Show what AI extracted
    with st.expander("🔍 View AI Analysis", expanded=False):
        st.json(structured_data)
    
    # Review and edit structured data
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Review Extracted Information")
        
        # Current Activities
        if structured_data.get('current_activities'):
            st.write("**Current Activities:**")
            for i, activity in enumerate(structured_data['current_activities']):
                with st.expander(f"Activity {i+1}: {activity.get('description', 'No description')[:50]}..."):
                    
                    # Allow editing of each field
                    activity['description'] = st.text_area(
                        "Description",
                        value=activity.get('description', ''),
                        key=f"voice_act_desc_{i}"
                    )
                    
                    col_proj, col_prio = st.columns(2)
                    with col_proj:
                        activity['project'] = st.text_input(
                            "Project",
                            value=activity.get('project', ''),
                            key=f"voice_act_proj_{i}"
                        )
                    
                    with col_prio:
                        priority_options = ["High", "Medium", "Low"]
                        current_priority = activity.get('priority', 'Medium')
                        if current_priority not in priority_options:
                            priority_options.append(current_priority)
                        
                        activity['priority'] = st.selectbox(
                            "Priority",
                            options=priority_options,
                            index=priority_options.index(current_priority),
                            key=f"voice_act_prio_{i}"
                        )
                    
                    col_status, col_progress = st.columns(2)
                    with col_status:
                        status_options = ["Not Started", "In Progress", "Blocked", "Completed"]
                        current_status = activity.get('status', 'In Progress')
                        if current_status not in status_options:
                            status_options.append(current_status)
                        
                        activity['status'] = st.selectbox(
                            "Status",
                            options=status_options,
                            index=status_options.index(current_status),
                            key=f"voice_act_status_{i}"
                        )
                    
                    with col_progress:
                        activity['progress'] = st.slider(
                            "Progress",
                            min_value=0,
                            max_value=100,
                            value=int(activity.get('progress', 50)),
                            key=f"voice_act_progress_{i}"
                        )
        
        # Accomplishments
        if structured_data.get('accomplishments'):
            st.write("**Accomplishments:**")
            for i, accomplishment in enumerate(structured_data['accomplishments']):
                structured_data['accomplishments'][i] = st.text_area(
                    f"Accomplishment {i+1}",
                    value=accomplishment,
                    key=f"voice_acc_{i}"
                )
        
        # Challenges
        if structured_data.get('challenges'):
            st.write("**Challenges:**")
            structured_data['challenges'] = st.text_area(
                "Challenges",
                value=structured_data['challenges'],
                key="voice_challenges"
            )
        
        # Next Steps
        if structured_data.get('nextsteps'):
            st.write("**Next Steps:**")
            for i, step in enumerate(structured_data['nextsteps']):
                structured_data['nextsteps'][i] = st.text_area(
                    f"Next Step {i+1}",
                    value=step,
                    key=f"voice_next_{i}"
                )
    
    with col2:
        st.write("### Report Readiness")
        
        # Calculate readiness score
        report_data = {
            'current_activities': structured_data.get('current_activities', []),
            'accomplishments': structured_data.get('accomplishments', []),
            'challenges': structured_data.get('challenges', ''),
            'nextsteps': structured_data.get('nextsteps', []),
            'name': st.session_state.get('name', ''),
            'reporting_week': st.session_state.get('reporting_week', '')
        }
        
        readiness = calculate_report_readiness_score(report_data)
        
        # Display readiness score
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
        
        # Action buttons
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
        # Populate current activities
        if structured_data.get('current_activities'):
            st.session_state.current_activities = structured_data['current_activities']
            st.session_state.show_current_activities = True
        
        # Populate accomplishments
        if structured_data.get('accomplishments'):
            st.session_state.accomplishments = structured_data['accomplishments']
            st.session_state.show_accomplishments = True
        
        # Populate challenges
        if structured_data.get('challenges'):
            st.session_state.challenges = structured_data['challenges']
            st.session_state.show_challenges = True
        
        # Populate next steps
        if structured_data.get('nextsteps'):
            st.session_state.nextsteps = structured_data['nextsteps']
            st.session_state.show_action_items = True
        
        # Clear voice data
        clear_voice_session_data()
        
        st.success("✅ Voice data loaded into report form! Navigate to 'Weekly Report' to continue editing.")
        
        # Redirect to weekly report page
        st.session_state.nav_page = "Weekly Report"
        st.session_state.nav_section = "reporting"
        
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error loading data to form: {str(e)}")

def save_voice_report_as_draft(structured_data):
    """Save the voice report as a draft."""
    try:
        # Create report data
        report_data = create_report_from_voice_data(structured_data)
        report_data['status'] = 'draft'
        
        # Save report
        report_id = save_report(report_data)
        
        if report_id:
            st.session_state.voice_session_stats['reports_created'] += 1
            st.success("📝 Report saved as draft!")
            
            # Clear voice data
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
        # Create report data
        report_data = create_report_from_voice_data(structured_data)
        report_data['status'] = 'submitted'
        
        # Validate required fields
        if not report_data.get('name'):
            st.error("Please set your name in the session first")
            return
        
        # Save report
        report_id = save_report(report_data)
        
        if report_id:
            st.session_state.voice_session_stats['reports_created'] += 1
            st.success("🎉 Report submitted successfully!")
            
            # Clear voice data
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
        'upcoming_activities': [],  # Voice assistant doesn't capture upcoming activities yet
        'accomplishments': structured_data.get('accomplishments', []),
        'followups': [],  # Not captured in current voice processing
        'nextsteps': structured_data.get('nextsteps', []),
        'challenges': structured_data.get('challenges', ''),
        'timestamp': datetime.now().isoformat()
    }

def clear_voice_session_data():
    """Clear all voice-related session data."""
    keys_to_clear = [
        'voice_transcription',
        'structured_voice_data',
        'processing_status', # Clear the processing status message
        'audio_bytes_to_process', # Clear stored audio
        'transcription_source', # Clear source flag
        'processing_started_this_run' # Reset the flag
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# Additional helper functions for voice assistant

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


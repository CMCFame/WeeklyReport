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
    
    # Voice recording section
    render_voice_recording_section()
    
    # Processing and review section
    if st.session_state.get('voice_transcription'):
        render_transcription_review()
    
    if st.session_state.get('structured_voice_data'):
        render_structured_data_review()

def render_voice_recording_section():
    """Render the voice recording interface."""
    st.subheader("🎙️ Voice Recording")
    
    # Instructions
    with st.expander("📋 Recording Tips & Guidelines", expanded=False):
        st.markdown("""
        ### What to Include in Your Update:
        
        **Current Work (2-3 minutes):**
        - Projects you're working on this week
        - Progress percentages (e.g., "about 70% complete")
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
    
    # Recording interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Start Recording Your Update")
        st.info("💡 **Optimal length:** 3-5 minutes for a complete update")
        
        # Audio recorder
        audio_bytes = audio_recorder(
            text="Click to start recording",
            recording_color="#e74c3c",
            neutral_color="#34495e",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=3.0,  # Pause for 3 seconds to stop
            sample_rate=16000
        )
        
        if audio_bytes:
            st.success("🎵 Audio recorded successfully!")
            
            # Display audio player
            st.audio(audio_bytes, format="audio/wav")
            
            # Processing buttons
            col_process1, col_process2 = st.columns(2)
            
            with col_process1:
                if st.button("🔄 Record Again", use_container_width=True):
                    # Clear previous data
                    clear_voice_session_data()
                    st.rerun()
            
            with col_process2:
                if st.button("🚀 Process Recording", type="primary", use_container_width=True):
                    process_audio_recording(audio_bytes)
    
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
            if audio_size > 100000:  # > 100KB, roughly 30+ seconds
                st.success("✅ Good length")
            elif audio_size > 50000:  # > 50KB, roughly 15+ seconds
                st.warning("⚠️ Short recording")
            else:
                st.error("❌ Too short")
            
            duration_estimate = audio_size / 32000  # Rough estimate
            st.write(f"**Estimated duration:** ~{duration_estimate:.1f} seconds")

def process_audio_recording(audio_bytes):
    """Process the audio recording through transcription and structuring."""
    
    # Update stats
    st.session_state.voice_session_stats['recordings_made'] += 1
    
    with st.spinner("🤖 Processing your recording..."):
        
        # Step 1: Transcribe audio
        st.write("🎯 **Step 1:** Converting speech to text...")
        progress_bar = st.progress(0)
        
        transcription = transcribe_audio(audio_bytes)
        progress_bar.progress(33)
        
        if transcription.startswith("Transcription failed") or transcription.startswith("Transcription unavailable"):
            st.error(f"❌ {transcription}")
            return
        
        # Store transcription
        st.session_state.voice_transcription = transcription
        progress_bar.progress(66)
        
        # Step 2: Structure the content
        st.write("🧠 **Step 2:** Analyzing and structuring content...")
        
        structured_data = structure_voice_input(transcription)
        progress_bar.progress(100)
        
        if 'error' in structured_data:
            st.error(f"❌ {structured_data['error']}")
            return
        
        # Store structured data
        st.session_state.structured_voice_data = structured_data
        st.session_state.voice_session_stats['transcriptions_processed'] += 1
        
        st.success("✅ Processing complete! Review your structured report below.")
        time.sleep(1)  # Brief pause for user experience
        st.rerun()

def render_transcription_review():
    """Render the transcription review section."""
    st.subheader("📝 Speech Transcription")
    
    transcription = st.session_state.voice_transcription
    
    # Show transcription with edit capability
    col1, col2 = st.columns([3, 1])
    
    with col1:
        edited_transcription = st.text_area(
            "Review and edit your transcription:",
            value=transcription,
            height=200,
            help="You can edit the transcription if there are any errors"
        )
        
        # Update if edited
        if edited_transcription != transcription:
            st.session_state.voice_transcription = edited_transcription
    
    with col2:
        st.write("### Transcription Quality")
        
        # Analyze transcription quality
        word_count = len(edited_transcription.split())
        
        if word_count > 200:
            quality = "Excellent"
            quality_color = "success"
        elif word_count > 100:
            quality = "Good"
            quality_color = "info"
        elif word_count > 50:
            quality = "Fair"
            quality_color = "warning"
        else:
            quality = "Poor"
            quality_color = "error"
        
        eval(f"st.{quality_color}")(f"**Quality:** {quality}")
        st.write(f"**Word count:** {word_count}")
        
        # Content analysis
        content_keywords = {
            'Projects': ['project', 'working on', 'developing', 'building'],
            'Progress': ['percent', '%', 'complete', 'finished', 'progress'],
            'Challenges': ['challenge', 'blocker', 'blocked', 'difficult', 'problem'],
            'Accomplishments': ['completed', 'finished', 'accomplished', 'delivered']
        }
        
        detected_content = []
        for category, keywords in content_keywords.items():
            if any(keyword in edited_transcription.lower() for keyword in keywords):
                detected_content.append(category)
        
        st.write("**Detected content:**")
        for content in detected_content:
            st.write(f"✅ {content}")
        
        # Re-process button
        if st.button("🔄 Re-process", use_container_width=True):
            if edited_transcription != transcription:
                structured_data = structure_voice_input(edited_transcription)
                if 'error' not in structured_data:
                    st.session_state.structured_voice_data = structured_data
                    st.success("✅ Re-processed successfully!")
                    st.rerun()

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
        
        if st.button("📋 Load to Form", type="primary", use_container_width=True):
            load_voice_data_to_form(structured_data)
        
        if st.button("💾 Save as Draft", use_container_width=True):
            save_voice_report_as_draft(structured_data)
        
        if score >= 70:
            if st.button("🚀 Submit Report", use_container_width=True):
                save_voice_report_as_final(structured_data)
        else:
            st.info("Complete missing sections to enable submission")
        
        if st.button("🔄 Start Over", use_container_width=True):
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
        'structured_voice_data'
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
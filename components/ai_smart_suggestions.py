# components/ai_smart_suggestions.py
"""AI Smart Suggestions System for real-time writing assistance."""

import streamlit as st
from utils.ai_utils import (
    generate_ai_suggestions,
    calculate_report_readiness_score,
    setup_openai_api,
    analyze_sentiment,
    detect_stress_indicators
)
from utils.file_ops import get_all_reports
from utils.session import collect_form_data
import asyncio
import re
from datetime import datetime, timedelta
from collections import Counter
import numpy as np

def render_smart_suggestions_panel():
    """Render the smart suggestions panel for the current form."""
    
    # Check if OpenAI API is configured
    if not setup_openai_api():
        return
    
    # Only show suggestions if user is actively working on a report
    if not (st.session_state.get('show_current_activities') or 
            st.session_state.get('show_accomplishments') or 
            st.session_state.get('show_action_items')):
        return
    
    # Create a sidebar panel for suggestions
    with st.sidebar:
        st.markdown("---")
        render_suggestions_sidebar()

def render_suggestions_sidebar():
    """Render suggestions in the sidebar."""
    st.subheader("💡 Smart Suggestions")
    
    # Get current report data for analysis
    current_data = collect_form_data()
    
    # Calculate readiness score
    readiness = calculate_report_readiness_score(current_data)
    
    # Display readiness score
    score = readiness['score']
    if score >= 90:
        st.success(f"🌟 Excellent! ({score}/100)")
    elif score >= 75:
        st.info(f"👍 Good ({score}/100)")
    elif score >= 60:
        st.warning(f"📝 Fair ({score}/100)")
    else:
        st.error(f"📋 Needs work ({score}/100)")
    
    # Show specific feedback
    if readiness['feedback']:
        st.write("**Quick Improvements:**")
        for feedback in readiness['feedback'][:3]:  # Show top 3
            st.write(f"• {feedback}")
    
    # Section-specific suggestions
    render_section_suggestions(current_data)
    
    # Historical insights
    render_historical_insights()
    
    # Writing quality suggestions
    render_writing_suggestions(current_data)

def render_section_suggestions(current_data):
    """Render suggestions for specific sections."""
    
    # Current Activities suggestions
    if st.session_state.get('show_current_activities'):
        activities = current_data.get('current_activities', [])
        if activities:
            st.write("### 📊 Current Activities")
            
            # Check for missing information
            missing_info = []
            for i, activity in enumerate(activities):
                if not activity.get('project'):
                    missing_info.append(f"Activity {i+1}: Add project name")
                if not activity.get('priority'):
                    missing_info.append(f"Activity {i+1}: Set priority")
                if activity.get('progress', 0) == 50:  # Default value
                    missing_info.append(f"Activity {i+1}: Update progress")
            
            if missing_info:
                for info in missing_info[:2]:  # Show top 2
                    st.write(f"⚠️ {info}")
            else:
                st.write("✅ Activities look complete!")
    
    # Accomplishments suggestions
    if st.session_state.get('show_accomplishments'):
        accomplishments = current_data.get('accomplishments', [])
        valid_accomplishments = [a for a in accomplishments if a.strip()]
        
        st.write("### 🏆 Accomplishments")
        
        if len(valid_accomplishments) == 0:
            st.write("💡 Add your wins from this week")
        elif len(valid_accomplishments) < 3:
            st.write("💡 Consider adding more accomplishments")
            
            # Suggest accomplishment ideas
            suggestions = generate_accomplishment_ideas()
            if suggestions:
                st.write("**Ideas:**")
                for suggestion in suggestions[:2]:
                    st.write(f"• {suggestion}")
        else:
            # Check accomplishment quality
            short_accomplishments = [a for a in valid_accomplishments if len(a.strip()) < 20]
            if short_accomplishments:
                st.write("💡 Add more detail to accomplishments")
            else:
                st.write("✅ Great accomplishments!")
    
    # Action Items suggestions
    if st.session_state.get('show_action_items'):
        nextsteps = current_data.get('nextsteps', [])
        valid_nextsteps = [n for n in nextsteps if n.strip()]
        
        st.write("### 📋 Next Steps")
        
        if len(valid_nextsteps) == 0:
            st.write("💡 What's planned for next week?")
        elif len(valid_nextsteps) < 2:
            st.write("💡 Add more next steps")
        else:
            st.write("✅ Good planning ahead!")

def generate_accomplishment_ideas():
    """Generate accomplishment ideas based on current activities."""
    ideas = [
        "Completed a project milestone",
        "Resolved a technical challenge",
        "Improved a process or workflow",
        "Learned a new skill or technology",
        "Helped a team member",
        "Fixed a bug or issue",
        "Created documentation",
        "Attended training or conference"
    ]
    
    # Randomize and return subset
    import random
    random.shuffle(ideas)
    return ideas[:4]

def render_historical_insights():
    """Render insights based on historical reports."""
    st.write("### 📈 Insights")
    
    # Get user's previous reports
    all_reports = get_all_reports(filter_by_user=True)
    
    if len(all_reports) < 2:
        st.info("🔄 More insights will appear as you submit reports")
        return
    
    # Analyze patterns
    recent_reports = all_reports[:5]  # Last 5 reports
    
    # Project consistency
    all_projects = []
    for report in recent_reports:
        for activity in report.get('current_activities', []):
            project = activity.get('project', '').strip()
            if project:
                all_projects.append(project)
    
    if all_projects:
        project_counts = Counter(all_projects)
        most_common_project = project_counts.most_common(1)[0]
        
        if most_common_project[1] >= 3:
            st.write(f"🎯 You're consistently working on **{most_common_project[0]}**")
    
    # Completion patterns
    completion_rates = []
    for report in recent_reports:
        activities = report.get('current_activities', [])
        if activities:
            completed = sum(1 for a in activities if a.get('status') == 'Completed')
            rate = completed / len(activities) * 100
            completion_rates.append(rate)
    
    if completion_rates:
        avg_completion = np.mean(completion_rates)
        if avg_completion > 75:
            st.write("🌟 Great completion rate trend!")
        elif avg_completion < 50:
            st.write("💡 Consider breaking down tasks into smaller pieces")
    
    # Sentiment trend
    sentiments = []
    for report in recent_reports:
        content = ' '.join([
            ' '.join(report.get('accomplishments', [])),
            report.get('challenges', ''),
            report.get('concerns', '')
        ])
        if content.strip():
            sentiment = analyze_sentiment(content)
            sentiments.append(sentiment['sentiment_score'])
    
    if len(sentiments) >= 3:
        recent_sentiment = np.mean(sentiments[:2])  # Last 2 reports
        older_sentiment = np.mean(sentiments[2:])   # Earlier reports
        
        if recent_sentiment > older_sentiment + 0.5:
            st.write("📈 Your sentiment is improving!")
        elif recent_sentiment < older_sentiment - 0.5:
            st.write("💙 Consider discussing any concerns")

def render_writing_suggestions(current_data):
    """Render writing quality suggestions."""
    st.write("### ✍️ Writing Tips")
    
    # Analyze current content
    all_content = []
    
    # Collect accomplishments
    accomplishments = current_data.get('accomplishments', [])
    for acc in accomplishments:
        if acc.strip():
            all_content.append(acc)
    
    # Collect activity descriptions
    activities = current_data.get('current_activities', [])
    for activity in activities:
        desc = activity.get('description', '').strip()
        if desc:
            all_content.append(desc)
    
    if not all_content:
        st.write("💡 Add content to get writing suggestions")
        return
    
    # Analyze writing patterns
    suggestions = []
    
    # Check for specific metrics
    has_numbers = any(re.search(r'\d+%|\d+\.\d+%|\d+\s*percent', content) for content in all_content)
    if not has_numbers:
        suggestions.append("Add specific numbers and percentages")
    
    # Check for action words
    action_words = ['completed', 'delivered', 'implemented', 'resolved', 'improved', 'created', 'designed']
    has_action_words = any(any(word in content.lower() for word in action_words) for content in all_content)
    if not has_action_words:
        suggestions.append("Use strong action verbs")
    
    # Check length
    short_items = [content for content in all_content if len(content.split()) < 5]
    if len(short_items) > len(all_content) * 0.5:
        suggestions.append("Add more detail to descriptions")
    
    # Show suggestions
    if suggestions:
        for suggestion in suggestions[:2]:
            st.write(f"💡 {suggestion}")
    else:
        st.write("✅ Good writing quality!")

def render_real_time_suggestions(section_type, content, key_suffix=""):
    """Render real-time suggestions for specific content."""
    
    if not content or len(content.strip()) < 10:
        return
    
    # Only show suggestions periodically to avoid API overuse
    suggestion_key = f"suggestions_{section_type}_{key_suffix}"
    last_suggestion_time = st.session_state.get(f"{suggestion_key}_time", 0)
    current_time = datetime.now().timestamp()
    
    # Update suggestions every 30 seconds max
    if current_time - last_suggestion_time < 30:
        # Show cached suggestions if available
        cached_suggestions = st.session_state.get(suggestion_key, [])
        if cached_suggestions:
            render_suggestions_ui(cached_suggestions, section_type)
        return
    
    # Check if OpenAI is available
    if not setup_openai_api():
        return
    
    # Generate new suggestions
    with st.spinner("🤖 Getting AI suggestions..."):
        try:
            suggestions = asyncio.run(generate_ai_suggestions(content, section_type))
            
            # Cache suggestions
            st.session_state[suggestion_key] = suggestions
            st.session_state[f"{suggestion_key}_time"] = current_time
            
            render_suggestions_ui(suggestions, section_type)
            
        except Exception as e:
            st.error(f"Suggestions temporarily unavailable: {str(e)}")

def render_suggestions_ui(suggestions, section_type):
    """Render the suggestions UI."""
    if not suggestions or suggestions == ["AI suggestions unavailable - please configure OpenAI API key"]:
        return
    
    with st.expander("💡 AI Suggestions", expanded=False):
        st.write(f"**Improve your {section_type.lower()}:**")
        
        for i, suggestion in enumerate(suggestions, 1):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"{i}. {suggestion}")
            
            with col2:
                if st.button("✅", key=f"apply_suggestion_{section_type}_{i}", help="Mark as helpful"):
                    st.success("Thanks for the feedback!")

def render_smart_autocomplete(field_type, current_value=""):
    """Render smart autocomplete suggestions."""
    
    if field_type == "project":
        return render_project_autocomplete(current_value)
    elif field_type == "accomplishment":
        return render_accomplishment_autocomplete(current_value)
    elif field_type == "next_step":
        return render_next_step_autocomplete(current_value)
    
    return current_value

def render_project_autocomplete(current_value):
    """Render project name autocomplete."""
    # Get historical project names
    all_reports = get_all_reports(filter_by_user=True)
    project_names = set()
    
    for report in all_reports:
        for activity in report.get('current_activities', []):
            project = activity.get('project', '').strip()
            if project:
                project_names.add(project)
    
    if project_names and current_value:
        # Find matching projects
        matches = [p for p in project_names if current_value.lower() in p.lower()]
        if matches:
            st.info(f"💡 Similar projects: {', '.join(matches[:3])}")
    
    return current_value

def render_accomplishment_autocomplete(current_value):
    """Render accomplishment autocomplete."""
    if len(current_value) > 5:
        # Analyze sentiment
        sentiment = analyze_sentiment(current_value)
        
        if sentiment['sentiment_score'] < 6:
            st.info("💡 Consider highlighting the positive impact")
        elif sentiment['sentiment_score'] > 8:
            st.success("✨ Great positive accomplishment!")
    
    return current_value

def render_next_step_autocomplete(current_value):
    """Render next step autocomplete."""
    if current_value:
        # Check if it's specific enough
        if not re.search(r'\b(by|due|before|next|this|week|monday|tuesday|wednesday|thursday|friday)\b', current_value.lower()):
            st.info("💡 Consider adding a timeline (e.g., 'by Friday')")
    
    return current_value

def render_suggestions_dashboard():
    """Render a full suggestions dashboard page."""
    st.title("💡 AI Smart Suggestions")
    st.write("Get intelligent writing assistance and report improvements")
    
    # Check API setup
    if not setup_openai_api():
        st.info("👆 Please configure your OpenAI API key above to use Smart Suggestions.")
        return
    
    # Current report analysis
    current_data = collect_form_data()
    
    if not any([
        current_data.get('current_activities'),
        current_data.get('accomplishments'),
        current_data.get('nextsteps')
    ]):
        st.info("Start working on your weekly report to get personalized suggestions!")
        
        # Show general tips
        render_general_writing_tips()
        return
    
    # Report readiness analysis
    st.subheader("📊 Report Readiness Analysis")
    
    readiness = calculate_report_readiness_score(current_data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = readiness['score']
        if score >= 80:
            st.success(f"**Readiness Score**\n{score}/100")
        elif score >= 60:
            st.warning(f"**Readiness Score**\n{score}/100")
        else:
            st.error(f"**Readiness Score**\n{score}/100")
    
    with col2:
        st.info(f"**Quality Level**\n{readiness['readiness_level']}")
    
    with col3:
        completion_sections = 5 - len(readiness['feedback'])
        st.metric("Completed Sections", f"{completion_sections}/5")
    
    # Detailed feedback
    if readiness['feedback']:
        st.subheader("🎯 Improvement Suggestions")
        
        for i, feedback in enumerate(readiness['feedback'], 1):
            st.write(f"**{i}.** {feedback}")
    
    # Section-by-section analysis
    render_detailed_section_analysis(current_data)
    
    # Historical comparison
    render_historical_comparison()

def render_general_writing_tips():
    """Render general writing tips for new users."""
    st.subheader("✍️ Writing Tips for Great Reports")
    
    tips = [
        {
            "title": "Be Specific with Numbers",
            "description": "Instead of 'made progress', say 'completed 80% of the API integration'",
            "example": "✅ Completed 3 out of 5 user stories (60% of sprint goal)"
        },
        {
            "title": "Use Action Verbs",
            "description": "Start accomplishments with strong action words",
            "example": "✅ Delivered, Implemented, Resolved, Optimized, Created"
        },
        {
            "title": "Include Impact",
            "description": "Explain why your work matters",
            "example": "✅ Fixed login bug that was affecting 20% of users"
        },
        {
            "title": "Be Clear About Blockers",
            "description": "Clearly state what's preventing progress",
            "example": "✅ Waiting for API documentation from external team"
        },
        {
            "title": "Set Specific Next Steps",
            "description": "Include timelines and ownership",
            "example": "✅ Schedule code review with team by Thursday"
        }
    ]
    
    for tip in tips:
        with st.expander(f"💡 {tip['title']}"):
            st.write(tip['description'])
            st.code(tip['example'])

def render_detailed_section_analysis(current_data):
    """Render detailed analysis for each section."""
    
    # Current Activities Analysis
    activities = current_data.get('current_activities', [])
    if activities:
        st.subheader("📊 Current Activities Analysis")
        
        for i, activity in enumerate(activities, 1):
            with st.expander(f"Activity {i}: {activity.get('description', 'No description')[:50]}..."):
                
                # Analyze description
                description = activity.get('description', '')
                if description:
                    # Check for specificity
                    has_numbers = bool(re.search(r'\d+', description))
                    has_timeline = bool(re.search(r'\b(by|due|before|next|this|week|day)\b', description.lower()))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if has_numbers:
                            st.success("✅ Includes specific numbers")
                        else:
                            st.warning("💡 Consider adding specific numbers")
                    
                    with col2:
                        if has_timeline:
                            st.success("✅ Has timeline information")
                        else:
                            st.info("💡 Could include timeline details")
                
                # Check completeness
                missing_fields = []
                if not activity.get('project'):
                    missing_fields.append("Project name")
                if not activity.get('priority'):
                    missing_fields.append("Priority level")
                if activity.get('progress', 0) == 50:  # Default value
                    missing_fields.append("Actual progress percentage")
                
                if missing_fields:
                    st.warning(f"Missing: {', '.join(missing_fields)}")
                else:
                    st.success("✅ All fields completed")
    
    # Accomplishments Analysis
    accomplishments = current_data.get('accomplishments', [])
    valid_accomplishments = [a for a in accomplishments if a.strip()]
    
    if valid_accomplishments:
        st.subheader("🏆 Accomplishments Analysis")
        
        for i, accomplishment in enumerate(valid_accomplishments, 1):
            with st.expander(f"Accomplishment {i}: {accomplishment[:50]}..."):
                
                # Sentiment analysis
                sentiment = analyze_sentiment(accomplishment)
                
                col1, col2 = st.columns(2)
                with col1:
                    if sentiment['sentiment_score'] >= 7:
                        st.success(f"✅ Positive tone ({sentiment['sentiment_score']:.1f}/10)")
                    elif sentiment['sentiment_score'] >= 5:
                        st.info(f"😐 Neutral tone ({sentiment['sentiment_score']:.1f}/10)")
                    else:
                        st.warning(f"💡 Could be more positive ({sentiment['sentiment_score']:.1f}/10)")
                
                with col2:
                    word_count = len(accomplishment.split())
                    if word_count >= 10:
                        st.success(f"✅ Good detail ({word_count} words)")
                    else:
                        st.info(f"💡 Could add more detail ({word_count} words)")
                
                # Impact analysis
                impact_words = ['improved', 'increased', 'reduced', 'saved', 'delivered', 'helped']
                has_impact = any(word in accomplishment.lower() for word in impact_words)
                
                if has_impact:
                    st.success("✅ Shows impact")
                else:
                    st.info("💡 Consider highlighting the impact")

def render_historical_comparison():
    """Render comparison with historical reports."""
    st.subheader("📈 Historical Trends")
    
    all_reports = get_all_reports(filter_by_user=True)
    
    if len(all_reports) < 3:
        st.info("Submit more reports to see trend analysis")
        return
    
    # Analyze recent vs historical
    recent_reports = all_reports[:3]
    older_reports = all_reports[3:6] if len(all_reports) > 3 else []
    
    if not older_reports:
        st.info("Need more historical data for comparison")
        return
    
    # Compare activity counts
    recent_activity_count = np.mean([len(r.get('current_activities', [])) for r in recent_reports])
    older_activity_count = np.mean([len(r.get('current_activities', [])) for r in older_reports])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Avg Activities (Recent)",
            f"{recent_activity_count:.1f}",
            delta=f"{recent_activity_count - older_activity_count:.1f}" if older_activity_count > 0 else None
        )
    
    with col2:
        # Compare accomplishment counts
        recent_acc_count = np.mean([len([a for a in r.get('accomplishments', []) if a.strip()]) for r in recent_reports])
        older_acc_count = np.mean([len([a for a in r.get('accomplishments', []) if a.strip()]) for r in older_reports])
        
        st.metric(
            "Avg Accomplishments (Recent)",
            f"{recent_acc_count:.1f}",
            delta=f"{recent_acc_count - older_acc_count:.1f}" if older_acc_count > 0 else None
        )
    
    # Insights
    insights = []
    
    if recent_activity_count > older_activity_count * 1.2:
        insights.append("📈 Your workload has increased significantly")
    elif recent_activity_count < older_activity_count * 0.8:
        insights.append("📉 Your workload has decreased")
    
    if recent_acc_count > older_acc_count * 1.1:
        insights.append("🌟 You're reporting more accomplishments")
    
    if insights:
        st.write("**Insights:**")
        for insight in insights:
            st.write(f"• {insight}")
    else:
        st.success("📊 Your reporting patterns are consistent")
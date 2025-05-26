# utils/ai_utils.py
"""AI utilities for the Weekly Report app."""

import streamlit as st
import openai
import json
import re
from datetime import datetime, timedelta
from textblob import TextBlob
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_openai_api():
    """Setup OpenAI API key by fetching it from Streamlit secrets."""
    # Try to get the API key from Streamlit secrets
    api_key = st.secrets.get("OPENAI_API_KEY")

    if api_key:
        openai.api_key = api_key
        # You might want to add a lightweight test call here if desired,
        # but generally, if the key is in secrets, it's assumed to be valid.
        # For simplicity, we'll assume it's valid if present.
        # You can log that the key was successfully loaded if needed.
        # logger.info("OpenAI API key loaded successfully from secrets.")
        return True
    else:
        # Inform the user if the API key is not found in secrets
        st.warning("🔑 OpenAI API key not found in Streamlit secrets.")
        st.info(
            "To enable AI features, please add your OpenAI API key to your Streamlit secrets. "
            "You can do this by creating a `secrets.toml` file in a `.streamlit` directory "
            "in your app's root folder with the following content:\n\n"
            "```toml\n"
            "OPENAI_API_KEY = \"your_api_key_here\"\n"
            "```\n\n"
            "Alternatively, if deploying on Streamlit Community Cloud, add it via the app's settings."
        )
        return False

def analyze_sentiment(text: str) -> Dict:
    """Analyze sentiment of text using TextBlob."""
    try:
        if not text or len(text.strip()) < 5:
            return {
                'sentiment_score': 5.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0
            }
        
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # Convert polarity to 1-10 scale
        sentiment_score = ((polarity + 1) / 2) * 9 + 1  # Maps -1,1 to 1,10
        
        # Determine label
        if sentiment_score >= 7:
            sentiment_label = 'positive'
        elif sentiment_score >= 4:
            sentiment_label = 'neutral'
        else:
            sentiment_label = 'negative'
        
        return {
            'sentiment_score': round(sentiment_score, 1),
            'sentiment_label': sentiment_label,
            'confidence': round(subjectivity, 2),
            'polarity': round(polarity, 2)
        }
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return {
            'sentiment_score': 5.0,
            'sentiment_label': 'neutral',
            'confidence': 0.0
        }

def detect_stress_indicators(text: str) -> Dict:
    """Detect stress indicators in text."""
    stress_keywords = {
        'high_stress': ['overwhelmed', 'stressed', 'burned out', 'exhausted', 'impossible', 'too much'],
        'medium_stress': ['challenging', 'difficult', 'struggling', 'behind', 'delayed', 'concerned'],
        'workload': ['overloaded', 'too many', 'not enough time', 'deadline pressure', 'tight schedule'],
        'blockers': ['blocked', 'waiting for', 'stuck', 'delayed', 'can\'t proceed', 'dependencies']
    }
    
    text_lower = text.lower()
    detected = {'high_stress': [], 'medium_stress': [], 'workload': [], 'blockers': []}
    
    for category, keywords in stress_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected[category].append(keyword)
    
    # Calculate stress score
    stress_score = len(detected['high_stress']) * 3 + len(detected['medium_stress']) * 2 + len(detected['workload']) * 2 + len(detected['blockers']) * 1
    stress_level = 'low'
    
    if stress_score >= 6:
        stress_level = 'high'
    elif stress_score >= 3:
        stress_level = 'medium'
    
    return {
        'stress_score': min(stress_score, 10),
        'stress_level': stress_level,
        'indicators': detected,
        'total_indicators': sum(len(v) for v in detected.values())
    }

def calculate_workload_score(activities: List[Dict]) -> float:
    """Calculate workload score based on activities."""
    if not activities:
        return 0.0
    
    total_workload = 0
    high_priority = sum(1 for a in activities if a.get('priority') == 'High')
    in_progress = sum(1 for a in activities if a.get('status') == 'In Progress')
    blocked = sum(1 for a in activities if a.get('status') == 'Blocked')
    
    # Base score from number of activities
    total_workload += len(activities) * 10
    
    # Penalty for high priority items
    total_workload += high_priority * 15
    
    # Penalty for blocked items
    total_workload += blocked * 10
    
    # Normalize to 0-100 scale
    normalized_score = min(total_workload, 100)
    
    return round(normalized_score, 1)

def predict_burnout_risk(user_reports: List[Dict]) -> Dict:
    """Predict burnout risk based on historical data."""
    if len(user_reports) < 2:
        return {
            'risk_level': 'unknown',
            'risk_score': 0,
            'weeks_to_burnout': None,
            'trends': {},
            'recommendations': ['Insufficient data for prediction']
        }
    
    # Analyze trends over last few reports
    recent_reports = sorted(user_reports, key=lambda x: x.get('timestamp', ''), reverse=True)[:8]
    
    sentiment_trend = []
    workload_trend = []
    stress_trend = []
    
    for report in recent_reports:
        # Analyze sentiment from accomplishments and challenges
        text_content = ' '.join([
            ' '.join(report.get('accomplishments', [])),
            report.get('challenges', ''),
            report.get('concerns', '')
        ])
        
        sentiment = analyze_sentiment(text_content)
        stress = detect_stress_indicators(text_content)
        workload = calculate_workload_score(report.get('current_activities', []))
        
        sentiment_trend.append(sentiment['sentiment_score'])
        stress_trend.append(stress['stress_score'])
        workload_trend.append(workload)
    
    # Calculate risk factors
    avg_sentiment = np.mean(sentiment_trend) if sentiment_trend else 5.0
    avg_stress = np.mean(stress_trend) if stress_trend else 0.0
    avg_workload = np.mean(workload_trend) if workload_trend else 0.0
    
    # Trend analysis (are things getting worse?)
    sentiment_declining = len(sentiment_trend) >= 3 and sentiment_trend[0] < sentiment_trend[2]
    stress_increasing = len(stress_trend) >= 3 and stress_trend[0] > stress_trend[2]
    workload_increasing = len(workload_trend) >= 3 and workload_trend[0] > workload_trend[2]
    
    # Calculate overall risk score
    risk_score = 0
    if avg_sentiment < 4:
        risk_score += 30
    elif avg_sentiment < 6:
        risk_score += 15
    
    if avg_stress > 5:
        risk_score += 25
    elif avg_stress > 3:
        risk_score += 15
    
    if avg_workload > 80:
        risk_score += 25
    elif avg_workload > 60:
        risk_score += 15
    
    # Trend penalties
    if sentiment_declining:
        risk_score += 15
    if stress_increasing:
        risk_score += 15
    if workload_increasing:
        risk_score += 10
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = 'high'
        weeks_to_burnout = 2
    elif risk_score >= 40:
        risk_level = 'medium'
        weeks_to_burnout = 6
    else:
        risk_level = 'low'
        weeks_to_burnout = None
    
    # Generate recommendations
    recommendations = []
    if avg_sentiment < 5:
        recommendations.append("Consider one-on-one meeting to discuss concerns")
    if avg_workload > 75:
        recommendations.append("Review workload distribution and priorities")
    if avg_stress > 4:
        recommendations.append("Identify and address stress factors")
    if sentiment_declining:
        recommendations.append("Monitor closely - sentiment declining")
    
    return {
        'risk_level': risk_level,
        'risk_score': min(risk_score, 100),
        'weeks_to_burnout': weeks_to_burnout,
        'trends': {
            'sentiment': sentiment_trend,
            'stress': stress_trend,
            'workload': workload_trend,
            'sentiment_declining': sentiment_declining,
            'stress_increasing': stress_increasing,
            'workload_increasing': workload_increasing
        },
        'recommendations': recommendations or ['Continue monitoring']
    }

async def generate_ai_suggestions(content: str, section_type: str) -> List[str]:
    """Generate AI suggestions for report content."""
    if not setup_openai_api(): # This will now use st.secrets
        return ["AI suggestions unavailable - please configure OpenAI API key in Streamlit secrets."]
    
    try:
        prompt = f"""
        As an AI assistant for workplace reporting, analyze this {section_type} content and provide 3 brief, actionable suggestions to improve it:
        
        Content: "{content}"
        
        Focus on:
        - Clarity and specificity
        - Professional tone
        - Completeness
        - Actionable details
        
        Provide exactly 3 suggestions, each on a new line starting with "•"
        """
        
        response = await openai.chat.completions.create( # Assuming async version of openai library
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        
        suggestions_text = response.choices[0].message.content
        suggestions = [s.strip().lstrip('•').strip() for s in suggestions_text.split('\n') if s.strip().startswith('•')]
        
        return suggestions[:3] if suggestions else ["Consider adding more specific details"]
        
    except Exception as e:
        logger.error(f"AI suggestions error: {e}")
        return ["AI suggestions temporarily unavailable"]

def generate_executive_summary(reports: List[Dict], summary_type: str = "Executive") -> str:
    """Generate executive summary from reports."""
    if not setup_openai_api(): # This will now use st.secrets
        return "Executive summary unavailable - please configure OpenAI API key in Streamlit secrets."
    
    try:
        # Prepare report data
        team_size = len(set(r.get('name', 'Unknown') for r in reports))
        time_period = f"{reports[-1].get('reporting_week', 'Unknown')} - {reports[0].get('reporting_week', 'Unknown')}" if len(reports) > 1 else reports[0].get('reporting_week', 'Unknown')
        
        # Extract key metrics
        total_activities = sum(len(r.get('current_activities', [])) for r in reports)
        completed_activities = sum(len([a for a in r.get('current_activities', []) if a.get('status') == 'Completed']) for r in reports)
        blocked_activities = sum(len([a for a in r.get('current_activities', []) if a.get('status') == 'Blocked']) for r in reports)
        
        # Extract accomplishments and challenges
        all_accomplishments = []
        all_challenges = []
        
        for report in reports:
            all_accomplishments.extend(report.get('accomplishments', []))
            if report.get('challenges'):
                all_challenges.append(report.get('challenges'))
        
        # Create prompt based on summary type
        if summary_type == "Executive":
            prompt = f"""
            Create an executive summary for leadership based on {team_size} team members' weekly reports from {time_period}.
            
            Key Metrics:
            - Total activities: {total_activities}
            - Completed: {completed_activities}
            - Blocked: {blocked_activities}
            
            Major Accomplishments:
            {chr(10).join(all_accomplishments[:10])}
            
            Key Challenges:
            {chr(10).join(all_challenges[:5])}
            
            Format as a concise executive summary focusing on business impact, key achievements, and critical risks requiring leadership attention.
            """
        elif summary_type == "Operational":
            prompt = f"""
            Create an operational summary for middle management based on {team_size} team members' weekly reports from {time_period}.
            
            Focus on:
            - Resource allocation and workload
            - Process blockers and dependencies
            - Team productivity metrics
            - Immediate action items needed
            
            Accomplishments: {chr(10).join(all_accomplishments[:10])}
            Challenges: {chr(10).join(all_challenges[:5])}
            """
        else:  # Strategic
            prompt = f"""
            Create a strategic summary based on {team_size} team members' weekly reports from {time_period}.
            
            Focus on:
            - Progress toward strategic objectives
            - Trend analysis and patterns
            - Resource optimization opportunities
            - Long-term risk assessment
            
            Accomplishments: {chr(10).join(all_accomplishments[:10])}
            Challenges: {chr(10).join(all_challenges[:5])}
            """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Executive summary generation error: {e}")
        return f"Unable to generate summary: {str(e)}"

def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio using OpenAI Whisper."""
    if not setup_openai_api(): # This will now use st.secrets
        return "Transcription unavailable - please configure OpenAI API key in Streamlit secrets."
    
    try:
        # Save audio to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        # Transcribe using Whisper
        with open(temp_audio_path, "rb") as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        # Clean up temp file
        import os
        os.unlink(temp_audio_path)
        
        return response # This is a string, not response.text
        
    except Exception as e:
        logger.error(f"Audio transcription error: {e}")
        return f"Transcription failed: {str(e)}"

def structure_voice_input(transcription: str) -> Dict:
    """Structure voice input into report sections using AI."""
    if not setup_openai_api(): # This will now use st.secrets
        return {"error": "AI structuring unavailable - please configure OpenAI API key in Streamlit secrets."}
    
    try:
        prompt = f"""
        Parse this spoken weekly report transcript and structure it into JSON format:
        
        Transcript: "{transcription}"
        
        Extract and organize into this exact JSON structure:
        {{
            "current_activities": [
                {{
                    "description": "extracted activity description",
                    "project": "project name if mentioned",
                    "priority": "High/Medium/Low",
                    "status": "In Progress/Completed/Blocked/Not Started",
                    "progress": 50
                }}
            ],
            "accomplishments": ["accomplishment 1", "accomplishment 2"],
            "challenges": "any challenges mentioned",
            "nextsteps": ["next step 1", "next step 2"]
        }}
        
        Rules:
        - Extract specific activities, projects, and progress percentages mentioned
        - Infer priority and status from context
        - Only include content that was actually mentioned
        - Keep descriptions concise but complete
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2
        )
        
        # Parse JSON response
        import json
        structured_data_str = response.choices[0].message.content
        # It's good practice to clean the string before parsing,
        # as GPT models can sometimes include leading/trailing characters or markdown.
        match = re.search(r"\{.*\}", structured_data_str, re.DOTALL)
        if match:
            json_string = match.group(0)
            structured_data = json.loads(json_string)
            return structured_data
        else:
            logger.error(f"Failed to extract JSON from AI response: {structured_data_str}")
            return {"error": "Failed to parse structured data from AI response."}

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}. Response was: {response.choices[0].message.content}")
        return {"error": "AI returned invalid JSON."}
    except Exception as e:
        logger.error(f"Voice structuring error: {e}")
        return {"error": f"Failed to structure voice input: {str(e)}"}

def calculate_report_readiness_score(report_data: Dict) -> Dict:
    """Calculate how complete and ready a report is."""
    score = 0
    max_score = 100
    feedback = []
    
    # Check basic info (20 points)
    if report_data.get('name'):
        score += 10
    else:
        feedback.append("Add your name")
    
    if report_data.get('reporting_week'):
        score += 10
    else:
        feedback.append("Specify the reporting week")
    
    # Check current activities (30 points)
    activities = report_data.get('current_activities', [])
    if activities:
        score += 15
        # Quality check
        detailed_activities = sum(1 for a in activities if len(a.get('description', '')) > 20)
        if detailed_activities >= len(activities) * 0.7:
            score += 15
        else:
            feedback.append("Add more detail to activity descriptions")
    else:
        feedback.append("Add current activities")
    
    # Check accomplishments (25 points)
    accomplishments = report_data.get('accomplishments', [])
    if accomplishments and any(a.strip() for a in accomplishments):
        score += 15
        # Quality check
        detailed_accomplishments = sum(1 for a in accomplishments if len(a.strip()) > 15)
        if detailed_accomplishments >= 2:
            score += 10
        else:
            feedback.append("Provide more detailed accomplishments")
    else:
        feedback.append("Add accomplishments from last week")
    
    # Check action items (15 points)
    has_followups = any(f.strip() for f in report_data.get('followups', []))
    has_nextsteps = any(n.strip() for n in report_data.get('nextsteps', []))
    
    if has_followups:
        score += 8
    if has_nextsteps:
        score += 7
    
    if not has_followups and not has_nextsteps:
        feedback.append("Add follow-ups or next steps")
    
    # Quality bonus (10 points)
    total_content = ' '.join([
        str(report_data.get('name', '')),
        ' '.join(a.get('description', '') for a in activities),
        ' '.join(accomplishments),
        report_data.get('challenges', ''),
        ' '.join(report_data.get('followups', [])),
        ' '.join(report_data.get('nextsteps', []))
    ])
    
    if len(total_content.strip()) > 200:
        score += 10
    else:
        feedback.append("Provide more detailed content overall")
    
    # Determine readiness level
    if score >= 90:
        readiness_level = "Excellent"
    elif score >= 75:
        readiness_level = "Good"
    elif score >= 60:
        readiness_level = "Fair"
    else:
        readiness_level = "Needs Improvement"
    
    return {
        'score': min(score, max_score),
        'readiness_level': readiness_level,
        'feedback': feedback,
        'max_score': max_score
    }
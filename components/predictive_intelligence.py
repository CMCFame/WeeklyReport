# components/predictive_intelligence.py
"""Predictive Intelligence Hub for AI-powered project and team predictions."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from utils.file_ops import get_all_reports
from utils.ai_utils import (
    analyze_sentiment,
    detect_stress_indicators,
    calculate_workload_score,
    predict_burnout_risk,
    setup_openai_api
)
import numpy as np
import openai
from collections import Counter, defaultdict
import re

def render_predictive_intelligence():
    """Render the predictive intelligence dashboard."""
    st.title("🔮 Predictive Intelligence Hub")
    st.write("AI-powered predictions and pattern analysis for proactive team management")
    
    # Check permissions
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    if user_role not in ["admin", "manager"]:
        st.error("Access denied. This feature is available to managers and administrators only.")
        return
    
    # Get all reports for analysis
    reports = get_all_reports(filter_by_user=False)
    if not reports:
        st.info("No reports available for analysis. Predictive insights will appear once reports are submitted.")
        return
    
    # Analysis parameters
    st.subheader("Analysis Parameters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Prediction timeframe
        prediction_weeks = st.selectbox(
            "Prediction Timeframe",
            options=[2, 4, 6, 8],
            index=1,
            help="How many weeks ahead to predict"
        )
    
    with col2:
        # Confidence threshold
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.5,
            max_value=0.95,
            value=0.7,
            help="Minimum confidence level for predictions"
        )
    
    with col3:
        # Analysis depth
        analysis_depth = st.selectbox(
            "Analysis Depth",
            options=["Quick", "Standard", "Deep"],
            index=1,
            help="How thorough the analysis should be"
        )
    
    # Filter recent reports for better predictions
    recent_cutoff = datetime.now() - timedelta(weeks=12)
    recent_reports = []
    
    for r in reports:
        if 'timestamp' in r:
            try:
                # FIXED: Properly parse the date part of the timestamp
                report_date = date.fromisoformat(r['timestamp'][:10])
                if report_date >= recent_cutoff.date():
                    recent_reports.append(r)
            except (ValueError, TypeError):
                # Skip reports with invalid timestamps
                continue
    
    if len(recent_reports) < 5:
        st.warning("Limited data available. Predictions improve with more historical reports.")
    
    # Run predictions
    predictions = generate_predictions(recent_reports, prediction_weeks, confidence_threshold)
    
    # Create tabs for different prediction types
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Project Risks", "👥 Team Predictions", "🔄 Pattern Analysis", "💡 AI Recommendations"
    ])
    
    with tab1:
        render_project_risk_predictions(predictions.get('project_risks', []))
    
    with tab2:
        render_team_predictions(predictions.get('team_predictions', []))
    
    with tab3:
        render_pattern_analysis(predictions.get('patterns', {}))
    
    with tab4:
        render_ai_recommendations(predictions.get('recommendations', []))

def generate_predictions(reports, prediction_weeks, confidence_threshold):
    """Generate comprehensive predictions from report data."""
    predictions = {
        'project_risks': [],
        'team_predictions': [],
        'patterns': {},
        'recommendations': []
    }
    
    # Analyze projects
    project_data = analyze_project_patterns(reports)
    predictions['project_risks'] = predict_project_risks(project_data, prediction_weeks, confidence_threshold)
    
    # Analyze team members
    team_data = analyze_team_patterns(reports)
    predictions['team_predictions'] = predict_team_outcomes(team_data, prediction_weeks, confidence_threshold)
    
    # Detect patterns
    predictions['patterns'] = detect_behavioral_patterns(reports)
    
    # Generate AI recommendations
    predictions['recommendations'] = generate_ai_recommendations(reports, predictions)
    
    return predictions

def analyze_project_patterns(reports):
    """Analyze patterns in project data."""
    project_data = defaultdict(lambda: {
        'activities': [],
        'statuses': [],
        'priorities': [],
        'progress_history': [],
        'blockers': [],
        'completion_rates': [],
        'team_members': set(),
        'last_activity': None
    })
    
    for report in reports:
        for activity in report.get('current_activities', []):
            project = activity.get('project', 'Uncategorized')
            if not project or project == 'Uncategorized':
                continue
            
            data = project_data[project]
            data['activities'].append(activity)
            data['statuses'].append(activity.get('status', 'Unknown'))
            data['priorities'].append(activity.get('priority', 'Medium'))
            data['progress_history'].append(activity.get('progress', 0))
            data['team_members'].add(report.get('name', 'Unknown'))
            
            if activity.get('status') == 'Blocked':
                data['blockers'].append({
                    'description': activity.get('description', ''),
                    'date': report.get('timestamp', '')[:10],
                    'reporter': report.get('name', 'Unknown')
                })
            
            # Track completion
            if activity.get('status') == 'Completed':
                data['completion_rates'].append(100)
            else:
                data['completion_rates'].append(activity.get('progress', 0))
            
            # Update last activity
            activity_date = report.get('timestamp', '')
            if not data['last_activity'] or activity_date > data['last_activity']:
                data['last_activity'] = activity_date
    
    # Convert defaultdict to regular dict and clean up
    return {k: dict(v) for k, v in project_data.items() if len(v['activities']) >= 2}

def predict_project_risks(project_data, prediction_weeks, confidence_threshold):
    """Predict project risks using pattern analysis."""
    risk_predictions = []
    
    for project_name, data in project_data.items():
        risk_factors = []
        risk_score = 0
        confidence = 0.5
        
        # Analyze completion trends
        if len(data['progress_history']) >= 3:
            recent_progress = data['progress_history'][-3:]
            if all(p <= prev for p, prev in zip(recent_progress[1:], recent_progress[:-1])):
                risk_factors.append("Progress declining over time")
                risk_score += 25
        
        # Check for frequent blockers
        blocker_count = len(data['blockers'])
        if blocker_count > 2:
            risk_factors.append(f"Multiple blockers reported ({blocker_count})")
            risk_score += 20
        
        # Analyze status distribution
        status_counts = Counter(data['statuses'])
        blocked_ratio = status_counts.get('Blocked', 0) / len(data['statuses'])
        if blocked_ratio > 0.3:
            risk_factors.append(f"High blocked activity ratio ({blocked_ratio:.1%})")
            risk_score += 30
        
        # Check for stagnant projects
        if data['last_activity']:
            try:
                # FIXED: Properly parse the date from timestamp
                last_activity_date = date.fromisoformat(data['last_activity'][:10])
                days_since_activity = (datetime.now().date() - last_activity_date).days
                if days_since_activity > 14:
                    risk_factors.append(f"No activity for {days_since_activity} days")
                    risk_score += 15
            except (ValueError, TypeError):
                # Skip if timestamp is invalid
                pass
        
        # Team size analysis
        team_size = len(data['team_members'])
        if team_size == 1:
            risk_factors.append("Single person dependency")
            risk_score += 10
        elif team_size > 5:
            risk_factors.append("Large team coordination complexity")
            risk_score += 5
        
        # Calculate confidence based on data quantity
        data_points = len(data['activities'])
        confidence = min(0.95, 0.5 + (data_points / 20))
        
        # Determine risk level
        if risk_score >= 60:
            risk_level = "High"
        elif risk_score >= 30:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # Only include predictions above confidence threshold
        if confidence >= confidence_threshold:
            risk_predictions.append({
                'project': project_name,
                'risk_level': risk_level,
                'risk_score': min(risk_score, 100),
                'confidence': confidence,
                'risk_factors': risk_factors,
                'team_size': team_size,
                'activities_count': len(data['activities']),
                'recent_blockers': data['blockers'][-2:] if data['blockers'] else [],
                'avg_progress': np.mean(data['progress_history']) if data['progress_history'] else 0
            })
    
    # Sort by risk score
    return sorted(risk_predictions, key=lambda x: x['risk_score'], reverse=True)

def analyze_team_patterns(reports):
    """Analyze patterns in team member behavior."""
    team_data = defaultdict(lambda: {
        'reports': [],
        'sentiment_trend': [],
        'workload_trend': [],
        'stress_trend': [],
        'completion_patterns': [],
        'challenge_keywords': [],
        'productivity_scores': [],
        'consistency_score': 0
    })
    
    for report in reports:
        name = report.get('name', 'Unknown')
        if name == 'Unknown':
            continue
        
        data = team_data[name]
        data['reports'].append(report)
        
        # Analyze sentiment
        content = ' '.join([
            ' '.join(report.get('accomplishments', [])),
            report.get('challenges', ''),
            report.get('concerns', '')
        ])
        
        sentiment = analyze_sentiment(content)
        stress = detect_stress_indicators(content)
        workload = calculate_workload_score(report.get('current_activities', []))
        
        data['sentiment_trend'].append(sentiment['sentiment_score'])
        data['stress_trend'].append(stress['stress_score'])
        data['workload_trend'].append(workload)
        
        # Track completion patterns
        activities = report.get('current_activities', [])
        if activities:
            completed_count = sum(1 for a in activities if a.get('status') == 'Completed')
            completion_rate = completed_count / len(activities)
            data['completion_patterns'].append(completion_rate)
        
        # Extract challenge keywords
        challenges = report.get('challenges', '')
        if challenges:
            # Simple keyword extraction
            words = re.findall(r'\b\w+\b', challenges.lower())
            data['challenge_keywords'].extend(words)
        
        # Calculate productivity score (simple metric)
        accomplishments = len([a for a in report.get('accomplishments', []) if len(a.strip()) > 10])
        productivity = min(accomplishments * 20, 100)  # Cap at 100
        data['productivity_scores'].append(productivity)
    
    # Calculate consistency scores
    for name, data in team_data.items():
        if len(data['reports']) >= 3:
            # Consistency in reporting (regularity)
            report_dates = [r.get('timestamp', '')[:10] for r in data['reports']]
            report_dates.sort()
            
            # Calculate gaps between reports
            gaps = []
            for i in range(1, len(report_dates)):
                try:
                    # FIXED: Use date.fromisoformat for date strings
                    date1 = date.fromisoformat(report_dates[i-1])
                    date2 = date.fromisoformat(report_dates[i])
                    gap = (date2 - date1).days
                    gaps.append(gap)
                except (ValueError, TypeError):
                    continue
            
            if gaps:
                avg_gap = np.mean(gaps)
                consistency = max(0, 100 - abs(avg_gap - 7) * 5)  # Ideal is 7 days
                data['consistency_score'] = consistency
    
    return {k: dict(v) for k, v in team_data.items() if len(v['reports']) >= 2}

def predict_team_outcomes(team_data, prediction_weeks, confidence_threshold):
    """Predict team member outcomes."""
    predictions = []
    
    for name, data in team_data.items():
        prediction = {
            'name': name,
            'predictions': [],
            'confidence': 0.5,
            'risk_factors': [],
            'positive_indicators': []
        }
        
        # Burnout prediction
        burnout_risk = predict_burnout_risk(data['reports'])
        if burnout_risk['risk_level'] != 'low':
            prediction['predictions'].append({
                'type': 'burnout_risk',
                'level': burnout_risk['risk_level'],
                'weeks_to_event': burnout_risk['weeks_to_burnout'],
                'description': f"Burnout risk: {burnout_risk['risk_level']}"
            })
        
        # Performance trend prediction
        if len(data['productivity_scores']) >= 3:
            recent_productivity = data['productivity_scores'][-3:]
            productivity_trend = np.polyfit(range(len(recent_productivity)), recent_productivity, 1)[0]
            
            if productivity_trend < -5:  # Declining productivity
                prediction['predictions'].append({
                    'type': 'productivity_decline',
                    'level': 'medium',
                    'weeks_to_event': 2,
                    'description': "Productivity showing declining trend"
                })
                prediction['risk_factors'].append("Declining productivity trend")
            elif productivity_trend > 5:  # Improving productivity
                prediction['positive_indicators'].append("Productivity trending upward")
        
        # Sentiment prediction
        if len(data['sentiment_trend']) >= 3:
            recent_sentiment = data['sentiment_trend'][-3:]
            sentiment_trend = np.polyfit(range(len(recent_sentiment)), recent_sentiment, 1)[0]
            
            if sentiment_trend < -0.5:  # Declining sentiment
                prediction['predictions'].append({
                    'type': 'sentiment_decline',
                    'level': 'medium',
                    'weeks_to_event': 3,
                    'description': "Sentiment declining over time"
                })
                prediction['risk_factors'].append("Negative sentiment trend")
        
        # Workload prediction
        if len(data['workload_trend']) >= 3:
            recent_workload = data['workload_trend'][-3:]
            avg_workload = np.mean(recent_workload)
            
            if avg_workload > 85:
                prediction['predictions'].append({
                    'type': 'overload_risk',
                    'level': 'high',
                    'weeks_to_event': 1,
                    'description': "Workload consistently high"
                })
                prediction['risk_factors'].append(f"High average workload ({avg_workload:.0f}/100)")
        
        # Consistency issues
        if data['consistency_score'] < 60:
            prediction['risk_factors'].append("Irregular reporting pattern")
        
        # Calculate overall confidence
        data_points = len(data['reports'])
        prediction['confidence'] = min(0.95, 0.4 + (data_points / 15))
        
        # Only include if above confidence threshold and has predictions
        if prediction['confidence'] >= confidence_threshold and (prediction['predictions'] or prediction['risk_factors']):
            predictions.append(prediction)
    
    return predictions

def detect_behavioral_patterns(reports):
    """Detect behavioral and temporal patterns in reports."""
    patterns = {
        'weekly_cycles': {},
        'recurring_blockers': {},
        'productivity_patterns': {},
        'collaboration_patterns': {},
        'seasonal_trends': {}
    }
    
    # Weekly cycle analysis
    day_productivity = defaultdict(list)
    for report in reports:
        if 'timestamp' in report:
            try:
                # FIXED: Properly parse the date from timestamp
                report_date = date.fromisoformat(report['timestamp'][:10])
                # Convert to datetime to get day name
                report_datetime = datetime.combine(report_date, datetime.min.time())
                day_name = report_datetime.strftime('%A')
                
                # Calculate productivity score
                accomplishments = len([a for a in report.get('accomplishments', []) if len(a.strip()) > 10])
                activities = len(report.get('current_activities', []))
                productivity = accomplishments * 2 + activities
                
                day_productivity[day_name].append(productivity)
            except (ValueError, TypeError):
                continue
    
    # Calculate average productivity by day
    for day, scores in day_productivity.items():
        if scores:
            patterns['weekly_cycles'][day] = {
                'avg_productivity': np.mean(scores),
                'report_count': len(scores)
            }
    
    # Recurring blocker analysis
    all_blockers = []
    for report in reports:
        for activity in report.get('current_activities', []):
            if activity.get('status') == 'Blocked':
                description = activity.get('description', '').lower()
                all_blockers.append(description)
    
    # Find common blocker keywords
    blocker_words = []
    for blocker in all_blockers:
        words = re.findall(r'\b\w{4,}\b', blocker)  # Words with 4+ characters
        blocker_words.extend(words)
    
    common_blockers = Counter(blocker_words).most_common(5)
    patterns['recurring_blockers'] = {
        'keywords': common_blockers,
        'total_blocked_activities': len(all_blockers)
    }
    
    # Collaboration patterns
    project_teams = defaultdict(set)
    for report in reports:
        name = report.get('name', 'Unknown')
        for activity in report.get('current_activities', []):
            project = activity.get('project', '')
            if project:
                project_teams[project].add(name)
    
    collaboration_scores = {}
    for project, team in project_teams.items():
        collaboration_scores[project] = len(team)
    
    patterns['collaboration_patterns'] = {
        'most_collaborative_projects': sorted(
            collaboration_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5],
        'solo_projects': [p for p, count in collaboration_scores.items() if count == 1]
    }
    
    return patterns

def generate_ai_recommendations(reports, predictions):
    """Generate AI-powered recommendations based on predictions."""
    if not setup_openai_api():
        return ["AI recommendations unavailable - please configure OpenAI API key"]
    
    try:
        # Prepare summary of predictions
        high_risk_projects = [p for p in predictions.get('project_risks', []) if p['risk_level'] == 'High']
        high_risk_team = [p for p in predictions.get('team_predictions', []) if any(pred['level'] == 'high' for pred in p['predictions'])]
        
        patterns_summary = predictions.get('patterns', {})
        
        prompt = f"""
        As an AI management consultant, analyze this team data and provide 5 specific, actionable recommendations:

        HIGH-RISK PROJECTS ({len(high_risk_projects)}):
        {[p['project'] + ': ' + ', '.join(p['risk_factors']) for p in high_risk_projects[:3]]}

        HIGH-RISK TEAM MEMBERS ({len(high_risk_team)}):
        {[p['name'] + ': ' + ', '.join([pred['description'] for pred in p['predictions']]) for p in high_risk_team[:3]]}

        PATTERNS DETECTED:
        - Recurring blockers: {patterns_summary.get('recurring_blockers', {}).get('keywords', [])[:3]}
        - Total reports analyzed: {len(reports)}

        Provide exactly 5 recommendations, each with:
        1. Priority level (High/Medium/Low)
        2. Specific action to take
        3. Expected timeline
        4. Success metric

        Format as: Priority: Action (Timeline) - Success Metric
        """
        
        response = openai.chat.completions.create(
            model="o4-mini-2025-04-16",
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=600  # Changed from max_tokens
        )
        
        recommendations_text = response.choices[0].message.content
        recommendations = [line.strip() for line in recommendations_text.split('\n') if line.strip() and any(p in line.lower() for p in ['high:', 'medium:', 'low:'])]
        
        return recommendations[:5] if recommendations else ["Continue monitoring team metrics and project progress"]
        
    except Exception as e:
        return [f"AI recommendations temporarily unavailable: {str(e)}"]

def render_project_risk_predictions(project_risks):
    """Render project risk predictions."""
    st.subheader("🎯 Project Risk Predictions")
    
    if not project_risks:
        st.info("No significant project risks detected. All projects appear to be on track.")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        high_risk_count = sum(1 for p in project_risks if p['risk_level'] == 'High')
        st.metric("High Risk Projects", high_risk_count)
    with col2:
        medium_risk_count = sum(1 for p in project_risks if p['risk_level'] == 'Medium')
        st.metric("Medium Risk Projects", medium_risk_count)
    with col3:
        avg_confidence = np.mean([p['confidence'] for p in project_risks])
        st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    
    # Risk visualization
    risk_df = pd.DataFrame(project_risks)
    
    fig = px.scatter(
        risk_df,
        x='confidence',
        y='risk_score',
        size='activities_count',
        color='risk_level',
        hover_name='project',
        color_discrete_map={
            'High': '#dc3545',
            'Medium': '#ffc107',
            'Low': '#28a745'
        },
        title="Project Risk vs Confidence",
        labels={
            'confidence': 'Prediction Confidence',
            'risk_score': 'Risk Score (0-100)'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed risk analysis
    st.subheader("Detailed Risk Analysis")
    
    for project in project_risks:
        risk_color = {
            'High': '🔴',
            'Medium': '🟡',
            'Low': '🟢'
        }.get(project['risk_level'], '⚪')
        
        with st.expander(f"{risk_color} {project['project']} - {project['risk_level']} Risk ({project['risk_score']}/100)"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Risk Factors:**")
                for factor in project['risk_factors']:
                    st.write(f"• {factor}")
                
                st.write(f"**Confidence Level:** {project['confidence']:.1%}")
                st.write(f"**Team Size:** {project['team_size']} members")
                st.write(f"**Activities Tracked:** {project['activities_count']}")
            
            with col2:
                st.write(f"**Average Progress:** {project['avg_progress']:.1f}%")
                
                if project['recent_blockers']:
                    st.write("**Recent Blockers:**")
                    for blocker in project['recent_blockers']:
                        st.write(f"• {blocker['description'][:50]}... ({blocker['date']})")
                
                # Recommendations based on risk factors
                st.write("**Recommended Actions:**")
                if any('blocker' in factor.lower() for factor in project['risk_factors']):
                    st.write("• Schedule blocker resolution meeting")
                if any('progress' in factor.lower() for factor in project['risk_factors']):
                    st.write("• Review project scope and timeline")
                if any('dependency' in factor.lower() for factor in project['risk_factors']):
                    st.write("• Add team members or redistribute work")

def render_team_predictions(team_predictions):
    """Render team member predictions."""
    st.subheader("👥 Team Member Predictions")
    
    if not team_predictions:
        st.info("No significant team risks detected. All team members appear to be performing well.")
        return
    
    # Summary
    total_risks = sum(len(p['predictions']) for p in team_predictions)
    high_priority = sum(1 for p in team_predictions for pred in p['predictions'] if pred.get('level') == 'high')
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Predictions", total_risks)
    with col2:
        st.metric("High Priority", high_priority)
    
    # Individual predictions
    for prediction in team_predictions:
        name = prediction['name']
        confidence = prediction['confidence']
        
        risk_icon = "🔴" if high_priority > 0 else "🟡" if prediction['predictions'] else "🟢"
        
        with st.expander(f"{risk_icon} {name} - Confidence: {confidence:.1%}"):
            col1, col2 = st.columns(2)
            
            with col1:
                if prediction['predictions']:
                    st.write("**Predictions:**")
                    for pred in prediction['predictions']:
                        weeks = pred.get('weeks_to_event', 'Unknown')
                        level_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(pred['level'], '⚪')
                        st.write(f"{level_icon} {pred['description']} (ETA: {weeks} weeks)")
                
                if prediction['risk_factors']:
                    st.write("**Risk Factors:**")
                    for factor in prediction['risk_factors']:
                        st.write(f"• {factor}")
            
            with col2:
                if prediction['positive_indicators']:
                    st.write("**Positive Indicators:**")
                    for indicator in prediction['positive_indicators']:
                        st.write(f"✅ {indicator}")
                
                st.write("**Recommended Actions:**")
                if any('burnout' in pred['type'] for pred in prediction['predictions']):
                    st.write("• Schedule immediate 1-on-1 meeting")
                    st.write("• Review workload distribution")
                if any('productivity' in pred['type'] for pred in prediction['predictions']):
                    st.write("• Identify productivity blockers")
                    st.write("• Provide additional support/training")
                if any('sentiment' in pred['type'] for pred in prediction['predictions']):
                    st.write("• Discuss concerns and challenges")
                    st.write("• Consider team/role adjustments")

def render_pattern_analysis(patterns):
    """Render behavioral pattern analysis."""
    st.subheader("🔄 Pattern Analysis")
    
    if not patterns:
        st.info("Insufficient data for pattern analysis.")
        return
    
    # Weekly cycles
    if patterns.get('weekly_cycles'):
        st.write("### Weekly Productivity Patterns")
        
        weekly_data = patterns['weekly_cycles']
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        productivity_scores = [weekly_data.get(day, {}).get('avg_productivity', 0) for day in days]
        
        fig = px.bar(
            x=days,
            y=productivity_scores,
            title="Average Productivity by Day of Week",
            labels={'x': 'Day', 'y': 'Productivity Score'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        best_day = days[np.argmax(productivity_scores)] if productivity_scores else "Unknown"
        worst_day = days[np.argmin(productivity_scores)] if productivity_scores else "Unknown"
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"🌟 **Best Day:** {best_day}")
        with col2:
            st.warning(f"📉 **Lowest Day:** {worst_day}")
    
    # Recurring blockers
    if patterns.get('recurring_blockers'):
        st.write("### Recurring Blockers")
        
        blocker_data = patterns['recurring_blockers']
        if blocker_data.get('keywords'):
            st.write("**Most Common Blocker Keywords:**")
            for keyword, count in blocker_data['keywords']:
                st.write(f"• **{keyword}**: {count} occurrences")
        
        total_blocked = blocker_data.get('total_blocked_activities', 0)
        st.write(f"**Total Blocked Activities:** {total_blocked}")
    
    # Collaboration patterns
    if patterns.get('collaboration_patterns'):
        st.write("### Collaboration Patterns")
        
        collab_data = patterns['collaboration_patterns']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Most Collaborative Projects:**")
            for project, team_size in collab_data.get('most_collaborative_projects', []):
                st.write(f"• {project}: {team_size} members")
        
        with col2:
            solo_projects = collab_data.get('solo_projects', [])
            st.write(f"**Solo Projects:** {len(solo_projects)}")
            if solo_projects:
                for project in solo_projects[:5]:
                    st.write(f"• {project}")

def render_ai_recommendations(recommendations):
    """Render AI-generated recommendations."""
    st.subheader("💡 AI-Powered Recommendations")
    
    if not recommendations:
        st.info("No specific recommendations available at this time.")
        return
    
    for i, rec in enumerate(recommendations, 1):
        # Parse priority from recommendation
        priority = "Medium"
        if rec.lower().startswith('high:'):
            priority = "High"
            priority_color = "🔴"
        elif rec.lower().startswith('medium:'):
            priority = "Medium"
            priority_color = "🟡"
        elif rec.lower().startswith('low:'):
            priority = "Low"
            priority_color = "🟢"
        else:
            priority_color = "⚪"
        
        with st.expander(f"{priority_color} Recommendation #{i} - {priority} Priority"):
            st.write(rec)
            
            # Add action tracking
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.checkbox(f"Mark as implemented", key=f"rec_{i}"):
                    st.success("✅ Recommendation marked as implemented")
            with col2:
                if st.button("Add to Tasks", key=f"task_{i}"):
                    st.info("Feature coming soon: Integration with task management systems")
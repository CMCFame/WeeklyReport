# components/executive_summary_generator.py
"""Executive Summary Generator for AI-powered leadership briefs."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.file_ops import get_all_reports
from utils.ai_utils import (
    generate_executive_summary,
    analyze_sentiment,
    detect_stress_indicators,
    calculate_workload_score,
    setup_openai_api
)
import json
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np

def render_executive_summary_generator():
    """Render the executive summary generator."""
    st.title("📊 Executive Summary Generator")
    st.write("AI-powered leadership briefs from team reports")
    
    # Check permissions
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    if user_role not in ["admin", "manager"]:
        st.error("Access denied. This feature is available to managers and administrators only.")
        return
    
    # Get all reports
    reports = get_all_reports(filter_by_user=False)
    if not reports:
        st.info("No reports available for summary generation. Summaries will be available once reports are submitted.")
        return
    
    # Configuration section
    st.subheader("Summary Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Time period selection
        period_options = {
            "Last Week": 7,
            "Last 2 Weeks": 14,
            "Last Month": 30,
            "Last Quarter": 90,
            "Custom Range": 0
        }
        
        selected_period = st.selectbox(
            "Reporting Period",
            options=list(period_options.keys()),
            index=1  # Default to Last 2 Weeks
        )
        
        # Custom date range if selected
        if selected_period == "Custom Range":
            start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=14))
            end_date = st.date_input("End Date", value=datetime.now().date())
        else:
            days_back = period_options[selected_period]
            start_date = datetime.now().date() - timedelta(days=days_back)
            end_date = datetime.now().date()
    
    with col2:
        # Summary type selection
        summary_type = st.selectbox(
            "Summary Type",
            options=["Executive", "Operational", "Strategic"],
            help="Executive: High-level overview for C-suite\nOperational: Detailed for middle management\nStrategic: Long-term focus for planning"
        )
        
        # Team filter
        all_team_members = list(set([r.get('name', 'Unknown') for r in reports if r.get('name')]))
        selected_members = st.multiselect(
            "Team Members",
            options=all_team_members,
            default=all_team_members,
            help="Select specific team members to include"
        )
    
    with col3:
        # Output format
        output_format = st.selectbox(
            "Output Format",
            options=["Text", "Email", "Presentation Slides"],
            help="Choose how to format the summary"
        )
        
        # Focus areas
        focus_areas = st.multiselect(
            "Focus Areas",
            options=[
                "Key Achievements",
                "Risk Factors",
                "Resource Allocation",
                "Team Health",
                "Project Status",
                "Strategic Alignment"
            ],
            default=["Key Achievements", "Risk Factors", "Project Status"]
        )
    
    # Filter reports based on selections
    filtered_reports = filter_reports(reports, start_date, end_date, selected_members)
    
    if not filtered_reports:
        st.warning(f"No reports found for the selected criteria ({start_date} to {end_date}).")
        return
    
    # Generate summary button
    if st.button("🚀 Generate Executive Summary", type="primary", use_container_width=True):
        generate_and_display_summary(
            filtered_reports, 
            summary_type, 
            output_format, 
            focus_areas,
            start_date,
            end_date,
            selected_members
        )
    
    # Show preview of data to be summarized
    st.subheader("Data Preview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Reports", len(filtered_reports))
    with col2:
        st.metric("Team Members", len(selected_members))
    with col3:
        total_activities = sum(len(r.get('current_activities', [])) for r in filtered_reports)
        st.metric("Total Activities", total_activities)
    with col4:
        completed_activities = sum(
            len([a for a in r.get('current_activities', []) if a.get('status') == 'Completed']) 
            for r in filtered_reports
        )
        completion_rate = (completed_activities / total_activities * 100) if total_activities > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")

def filter_reports(reports, start_date, end_date, selected_members):
    """Filter reports based on date range and team members."""
    filtered = []
    
    for report in reports:
        # Check date range
        if 'timestamp' in report:
            try:
                report_date = datetime.fromisoformat(report['timestamp'][:10]).date()
                if not (start_date <= report_date <= end_date):
                    continue
            except:
                continue
        
        # Check team member filter
        if report.get('name') in selected_members:
            filtered.append(report)
    
    return filtered

def generate_and_display_summary(reports, summary_type, output_format, focus_areas, start_date, end_date, selected_members):
    """Generate and display the executive summary."""
    
    with st.spinner("🤖 AI is analyzing your team data and generating summary..."):
        
        # Prepare enhanced summary data
        summary_data = prepare_summary_data(reports, focus_areas)
        
        # Generate AI summary
        ai_summary = generate_executive_summary(reports, summary_type)
        
        # Create comprehensive summary
        full_summary = create_comprehensive_summary(
            ai_summary, 
            summary_data, 
            summary_type, 
            start_date, 
            end_date, 
            selected_members
        )
        
        # Display based on output format
        if output_format == "Text":
            display_text_summary(full_summary)
        elif output_format == "Email":
            display_email_summary(full_summary, summary_type)
        elif output_format == "Presentation Slides":
            display_presentation_summary(full_summary, summary_data)

def prepare_summary_data(reports, focus_areas):
    """Prepare comprehensive data for summary generation."""
    data = {
        'metrics': {},
        'achievements': [],
        'risks': [],
        'team_health': {},
        'projects': {},
        'trends': {}
    }
    
    # Calculate key metrics
    total_activities = sum(len(r.get('current_activities', [])) for r in reports)
    completed_activities = sum(
        len([a for a in r.get('current_activities', []) if a.get('status') == 'Completed']) 
        for r in reports
    )
    blocked_activities = sum(
        len([a for a in r.get('current_activities', []) if a.get('status') == 'Blocked']) 
        for r in reports
    )
    
    data['metrics'] = {
        'total_reports': len(reports),
        'total_activities': total_activities,
        'completed_activities': completed_activities,
        'blocked_activities': blocked_activities,
        'completion_rate': (completed_activities / total_activities * 100) if total_activities > 0 else 0,
        'blocked_rate': (blocked_activities / total_activities * 100) if total_activities > 0 else 0
    }
    
    # Collect achievements
    if "Key Achievements" in focus_areas:
        all_accomplishments = []
        for report in reports:
            accomplishments = report.get('accomplishments', [])
            for acc in accomplishments:
                if acc and len(acc.strip()) > 15:  # Filter out trivial accomplishments
                    all_accomplishments.append({
                        'text': acc,
                        'author': report.get('name', 'Unknown'),
                        'date': report.get('timestamp', '')[:10]
                    })
        
        # Sort by length/quality and take top ones
        data['achievements'] = sorted(all_accomplishments, key=lambda x: len(x['text']), reverse=True)[:10]
    
    # Analyze risks
    if "Risk Factors" in focus_areas:
        risks = []
        
        # High stress indicators
        for report in reports:
            content = ' '.join([
                ' '.join(report.get('accomplishments', [])),
                report.get('challenges', ''),
                report.get('concerns', '')
            ])
            
            stress = detect_stress_indicators(content)
            if stress['stress_level'] in ['medium', 'high']:
                risks.append({
                    'type': 'stress',
                    'level': stress['stress_level'],
                    'person': report.get('name', 'Unknown'),
                    'indicators': stress['indicators']
                })
        
        # Blocked projects
        project_blocks = {}
        for report in reports:
            for activity in report.get('current_activities', []):
                if activity.get('status') == 'Blocked':
                    project = activity.get('project', 'Unknown')
                    if project not in project_blocks:
                        project_blocks[project] = 0
                    project_blocks[project] += 1
        
        for project, count in project_blocks.items():
            if count >= 2:  # Multiple blocked activities
                risks.append({
                    'type': 'project_blocked',
                    'level': 'high' if count >= 3 else 'medium',
                    'project': project,
                    'blocked_count': count
                })
        
        data['risks'] = risks
    
    # Team health analysis
    if "Team Health" in focus_areas:
        team_sentiments = []
        team_workloads = []
        
        for report in reports:
            content = ' '.join([
                ' '.join(report.get('accomplishments', [])),
                report.get('challenges', ''),
                report.get('concerns', '')
            ])
            
            sentiment = analyze_sentiment(content)
            workload = calculate_workload_score(report.get('current_activities', []))
            
            team_sentiments.append(sentiment['sentiment_score'])
            team_workloads.append(workload)
        
        data['team_health'] = {
            'avg_sentiment': np.mean(team_sentiments) if team_sentiments else 5.0,
            'avg_workload': np.mean(team_workloads) if team_workloads else 0.0,
            'sentiment_range': (min(team_sentiments), max(team_sentiments)) if team_sentiments else (5, 5),
            'workload_range': (min(team_workloads), max(team_workloads)) if team_workloads else (0, 0)
        }
    
    # Project analysis
    if "Project Status" in focus_areas:
        projects = {}
        
        for report in reports:
            for activity in report.get('current_activities', []):
                project = activity.get('project', 'Uncategorized')
                if project not in projects:
                    projects[project] = {
                        'activities': 0,
                        'completed': 0,
                        'blocked': 0,
                        'in_progress': 0,
                        'team_members': set(),
                        'avg_progress': []
                    }
                
                projects[project]['activities'] += 1
                projects[project]['team_members'].add(report.get('name', 'Unknown'))
                projects[project]['avg_progress'].append(activity.get('progress', 0))
                
                status = activity.get('status', 'Unknown')
                if status == 'Completed':
                    projects[project]['completed'] += 1
                elif status == 'Blocked':
                    projects[project]['blocked'] += 1
                elif status == 'In Progress':
                    projects[project]['in_progress'] += 1
        
        # Calculate averages and convert sets to counts
        for project_data in projects.values():
            project_data['team_size'] = len(project_data['team_members'])
            project_data['avg_progress'] = np.mean(project_data['avg_progress']) if project_data['avg_progress'] else 0
            del project_data['team_members']  # Remove set for JSON compatibility
        
        data['projects'] = projects
    
    return data

def create_comprehensive_summary(ai_summary, summary_data, summary_type, start_date, end_date, selected_members):
    """Create a comprehensive summary combining AI and data analysis."""
    
    summary = {
        'header': {
            'title': f"{summary_type} Summary",
            'period': f"{start_date} to {end_date}",
            'team_size': len(selected_members),
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        'ai_summary': ai_summary,
        'key_metrics': summary_data['metrics'],
        'achievements': summary_data.get('achievements', []),
        'risks': summary_data.get('risks', []),
        'team_health': summary_data.get('team_health', {}),
        'projects': summary_data.get('projects', {}),
        'recommendations': []
    }
    
    # Generate recommendations based on data
    recommendations = []
    
    # Completion rate recommendations
    completion_rate = summary_data['metrics']['completion_rate']
    if completion_rate < 60:
        recommendations.append("Consider reviewing project scopes and timelines - completion rate below 60%")
    elif completion_rate > 90:
        recommendations.append("Excellent execution! Consider taking on additional strategic initiatives")
    
    # Blocked activities recommendations
    blocked_rate = summary_data['metrics']['blocked_rate']
    if blocked_rate > 15:
        recommendations.append("High number of blocked activities - schedule dependency resolution sessions")
    
    # Team health recommendations
    if summary_data.get('team_health'):
        avg_sentiment = summary_data['team_health']['avg_sentiment']
        if avg_sentiment < 5:
            recommendations.append("Team sentiment below average - consider team wellness initiatives")
        
        avg_workload = summary_data['team_health']['avg_workload']
        if avg_workload > 80:
            recommendations.append("High team workload detected - review resource allocation")
    
    # Risk-based recommendations
    high_risks = [r for r in summary_data.get('risks', []) if r.get('level') == 'high']
    if high_risks:
        recommendations.append(f"{len(high_risks)} high-priority risks identified - immediate attention required")
    
    summary['recommendations'] = recommendations
    
    return summary

def display_text_summary(summary):
    """Display summary in text format."""
    st.success("✅ Executive summary generated successfully!")
    
    # Header
    st.markdown(f"# {summary['header']['title']}")
    st.markdown(f"**Period:** {summary['header']['period']} | **Team Size:** {summary['header']['team_size']} | **Generated:** {summary['header']['generated_at']}")
    
    # AI Summary
    st.subheader("📋 Executive Overview")
    st.write(summary['ai_summary'])
    
    # Key Metrics
    st.subheader("📊 Key Metrics")
    metrics = summary['key_metrics']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Reports", metrics['total_reports'])
    with col2:
        st.metric("Completion Rate", f"{metrics['completion_rate']:.1f}%")
    with col3:
        st.metric("Active Projects", len(summary['projects']))
    with col4:
        st.metric("Blocked Activities", metrics['blocked_activities'])
    
    # Team Health
    if summary['team_health']:
        st.subheader("🏥 Team Health")
        health = summary['team_health']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Sentiment", f"{health['avg_sentiment']:.1f}/10")
        with col2:
            st.metric("Average Workload", f"{health['avg_workload']:.0f}/100")
    
    # Key Achievements
    if summary['achievements']:
        st.subheader("🏆 Key Achievements")
        for i, achievement in enumerate(summary['achievements'][:5], 1):
            st.write(f"{i}. **{achievement['author']}**: {achievement['text']}")
    
    # Risk Factors
    if summary['risks']:
        st.subheader("⚠️ Risk Factors")
        high_risks = [r for r in summary['risks'] if r.get('level') == 'high']
        medium_risks = [r for r in summary['risks'] if r.get('level') == 'medium']
        
        if high_risks:
            st.error("**High Priority Risks:**")
            for risk in high_risks:
                if risk['type'] == 'stress':
                    st.write(f"• Team member {risk['person']} showing high stress indicators")
                elif risk['type'] == 'project_blocked':
                    st.write(f"• Project '{risk['project']}' has {risk['blocked_count']} blocked activities")
        
        if medium_risks:
            st.warning("**Medium Priority Risks:**")
            for risk in medium_risks:
                if risk['type'] == 'stress':
                    st.write(f"• Team member {risk['person']} showing moderate stress")
                elif risk['type'] == 'project_blocked':
                    st.write(f"• Project '{risk['project']}' has {risk['blocked_count']} blocked activities")
    
    # Recommendations
    if summary['recommendations']:
        st.subheader("💡 Recommendations")
        for i, rec in enumerate(summary['recommendations'], 1):
            st.write(f"{i}. {rec}")
    
    # Download options
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Text download
        summary_text = format_summary_as_text(summary)
        st.download_button(
            "Download as Text",
            summary_text,
            file_name=f"executive_summary_{summary['header']['period'].replace(' to ', '_')}.txt",
            mime="text/plain"
        )
    
    with col2:
        # JSON download for further processing
        summary_json = json.dumps(summary, indent=2, default=str)
        st.download_button(
            "Download as JSON",
            summary_json,
            file_name=f"executive_summary_{summary['header']['period'].replace(' to ', '_')}.json",
            mime="application/json"
        )

def display_email_summary(summary, summary_type):
    """Display summary in email format."""
    st.success("✅ Email summary generated successfully!")
    
    # Generate email content
    email_subject = f"{summary_type} Team Summary - {summary['header']['period']}"
    
    email_body = f"""
Subject: {email_subject}

Dear Leadership Team,

Please find below the {summary_type.lower()} summary for the period {summary['header']['period']}.

## EXECUTIVE OVERVIEW
{summary['ai_summary']}

## KEY METRICS
• Total Reports: {summary['key_metrics']['total_reports']}
• Completion Rate: {summary['key_metrics']['completion_rate']:.1f}%
• Active Projects: {len(summary['projects'])}
• Blocked Activities: {summary['key_metrics']['blocked_activities']}
"""
    
    if summary['team_health']:
        email_body += f"""
## TEAM HEALTH
• Average Sentiment: {summary['team_health']['avg_sentiment']:.1f}/10
• Average Workload: {summary['team_health']['avg_workload']:.0f}/100
"""
    
    if summary['achievements']:
        email_body += "\n## TOP ACHIEVEMENTS\n"
        for i, achievement in enumerate(summary['achievements'][:3], 1):
            email_body += f"{i}. {achievement['author']}: {achievement['text']}\n"
    
    if summary['risks']:
        high_risks = [r for r in summary['risks'] if r.get('level') == 'high']
        if high_risks:
            email_body += "\n## IMMEDIATE ATTENTION REQUIRED\n"
            for risk in high_risks:
                if risk['type'] == 'stress':
                    email_body += f"• High stress detected: {risk['person']}\n"
                elif risk['type'] == 'project_blocked':
                    email_body += f"• Project blocked: {risk['project']} ({risk['blocked_count']} activities)\n"
    
    if summary['recommendations']:
        email_body += "\n## ACTION ITEMS\n"
        for i, rec in enumerate(summary['recommendations'], 1):
            email_body += f"{i}. {rec}\n"
    
    email_body += f"""

This summary was automatically generated on {summary['header']['generated_at']}.

Best regards,
Weekly Report System
"""
    
    # Display email
    st.subheader("📧 Email Content")
    st.text_area("Email Subject", email_subject, height=50)
    st.text_area("Email Body", email_body, height=600)
    
    # Copy to clipboard option
    if st.button("📋 Copy Email Content"):
        st.success("Email content copied! (Use Ctrl+A, Ctrl+C to copy the content above)")

def display_presentation_summary(summary, summary_data):
    """Display summary in presentation slide format."""
    st.success("✅ Presentation slides generated successfully!")
    
    # Slide 1: Title
    st.markdown("---")
    st.markdown("# 📊 SLIDE 1: Title")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"## {summary['header']['title']}")
        st.markdown(f"### {summary['header']['period']}")
        st.markdown(f"**Team Size:** {summary['header']['team_size']} members")
        st.markdown(f"**Generated:** {summary['header']['generated_at']}")
    
    # Slide 2: Key Metrics
    st.markdown("---")
    st.markdown("# 📈 SLIDE 2: Key Performance Metrics")
    
    metrics = summary['key_metrics']
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Reports Submitted", metrics['total_reports'])
        st.metric("Total Activities", metrics['total_activities'])
    
    with col2:
        st.metric("Completion Rate", f"{metrics['completion_rate']:.1f}%", 
                 delta=f"{metrics['completion_rate'] - 75:.1f}%" if metrics['completion_rate'] != 75 else None)
        st.metric("Blocked Activities", metrics['blocked_activities'])
    
    # Slide 3: Project Status
    if summary['projects']:
        st.markdown("---")
        st.markdown("# 🎯 SLIDE 3: Project Status Overview")
        
        # Create project status chart
        project_data = []
        for project, data in summary['projects'].items():
            project_data.append({
                'Project': project,
                'Progress': data['avg_progress'],
                'Team Size': data['team_size'],
                'Completed': data['completed'],
                'Blocked': data['blocked']
            })
        
        if project_data:
            df = pd.DataFrame(project_data)
            
            fig = px.bar(
                df,
                x='Project',
                y='Progress',
                color='Team Size',
                title="Project Progress Overview",
                labels={'Progress': 'Average Progress (%)', 'Team Size': 'Team Members'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Slide 4: Team Health
    if summary['team_health']:
        st.markdown("---")
        st.markdown("# 🏥 SLIDE 4: Team Health Dashboard")
        
        health = summary['team_health']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment gauge
            sentiment_score = health['avg_sentiment']
            if sentiment_score >= 7:
                sentiment_status = "😊 Positive"
                sentiment_color = "green"
            elif sentiment_score >= 5:
                sentiment_status = "😐 Neutral"
                sentiment_color = "yellow"
            else:
                sentiment_status = "😟 Concerning"
                sentiment_color = "red"
            
            st.markdown(f"### Team Sentiment: {sentiment_score:.1f}/10")
            st.markdown(f"**Status:** {sentiment_status}")
            st.progress(sentiment_score / 10)
        
        with col2:
            # Workload gauge
            workload_score = health['avg_workload']
            if workload_score >= 85:
                workload_status = "🔴 Overloaded"
            elif workload_score >= 70:
                workload_status = "🟡 High"
            else:
                workload_status = "🟢 Manageable"
            
            st.markdown(f"### Average Workload: {workload_score:.0f}/100")
            st.markdown(f"**Status:** {workload_status}")
            st.progress(workload_score / 100)
    
    # Slide 5: Top Achievements
    if summary['achievements']:
        st.markdown("---")
        st.markdown("# 🏆 SLIDE 5: Key Achievements")
        
        for i, achievement in enumerate(summary['achievements'][:5], 1):
            st.markdown(f"**{i}.** {achievement['text']}")
            st.markdown(f"   *— {achievement['author']}*")
            st.markdown("")
    
    # Slide 6: Action Items
    st.markdown("---")
    st.markdown("# 💡 SLIDE 6: Action Items & Recommendations")
    
    if summary['recommendations']:
        for i, rec in enumerate(summary['recommendations'], 1):
            st.markdown(f"**{i}.** {rec}")
    
    # High priority risks
    high_risks = [r for r in summary.get('risks', []) if r.get('level') == 'high']
    if high_risks:
        st.markdown("### 🚨 Immediate Attention Required:")
        for risk in high_risks:
            if risk['type'] == 'stress':
                st.markdown(f"• **Team Member Alert:** {risk['person']} showing high stress indicators")
            elif risk['type'] == 'project_blocked':
                st.markdown(f"• **Project Alert:** {risk['project']} has {risk['blocked_count']} blocked activities")
    
    # Download as images (placeholder)
    st.markdown("---")
    st.info("💡 **Pro Tip:** Use your browser's print function to save these slides as PDF or take screenshots for presentation use.")

def format_summary_as_text(summary):
    """Format summary as plain text for download."""
    text = f"""
{summary['header']['title']}
Period: {summary['header']['period']}
Team Size: {summary['header']['team_size']} members
Generated: {summary['header']['generated_at']}

EXECUTIVE OVERVIEW
==================
{summary['ai_summary']}

KEY METRICS
===========
• Total Reports: {summary['key_metrics']['total_reports']}
• Completion Rate: {summary['key_metrics']['completion_rate']:.1f}%
• Total Activities: {summary['key_metrics']['total_activities']}
• Blocked Activities: {summary['key_metrics']['blocked_activities']}
"""
    
    if summary['team_health']:
        text += f"""
TEAM HEALTH
===========
• Average Sentiment: {summary['team_health']['avg_sentiment']:.1f}/10
• Average Workload: {summary['team_health']['avg_workload']:.0f}/100
"""
    
    if summary['achievements']:
        text += "\nKEY ACHIEVEMENTS\n================\n"
        for i, achievement in enumerate(summary['achievements'][:5], 1):
            text += f"{i}. {achievement['author']}: {achievement['text']}\n"
    
    if summary['risks']:
        high_risks = [r for r in summary['risks'] if r.get('level') == 'high']
        if high_risks:
            text += "\nHIGH PRIORITY RISKS\n==================\n"
            for risk in high_risks:
                if risk['type'] == 'stress':
                    text += f"• Team member {risk['person']} showing high stress indicators\n"
                elif risk['type'] == 'project_blocked':
                    text += f"• Project '{risk['project']}' has {risk['blocked_count']} blocked activities\n"
    
    if summary['recommendations']:
        text += "\nRECOMMENDATIONS\n===============\n"
        for i, rec in enumerate(summary['recommendations'], 1):
            text += f"{i}. {rec}\n"
    
    return text
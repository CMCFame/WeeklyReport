# components/team_health_dashboard.py
"""Team Health Dashboard component for AI-powered team wellness monitoring."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.file_ops import get_all_reports
from utils.ai_utils import (
    analyze_sentiment, 
    detect_stress_indicators, 
    calculate_workload_score,
    predict_burnout_risk
)
import numpy as np

def render_team_health_dashboard():
    """Render the team health and sentiment analysis dashboard."""
    st.title("🏥 Team Health & Sentiment Dashboard")
    st.write("AI-powered insights into team wellness, sentiment, and burnout risk")
    
    # Check permissions
    user_role = st.session_state.get("user_info", {}).get("role", "team_member")
    if user_role not in ["admin", "manager"]:
        st.error("Access denied. This feature is available to managers and administrators only.")
        return
    
    # Get all reports for analysis
    reports = get_all_reports(filter_by_user=False)
    if not reports:
        st.info("No reports available for analysis. Team health insights will appear once reports are submitted.")
        return
    
    # Date range filter
    st.subheader("Analysis Parameters")
    col1, col2 = st.columns(2)
    
    with col1:
        # Get date range from reports
        all_dates = [datetime.fromisoformat(r.get('timestamp', datetime.now().isoformat())[:10]) 
                    for r in reports if 'timestamp' in r]
        if all_dates:
            min_date = min(all_dates).date()
            max_date = max(all_dates).date()
        else:
            min_date = (datetime.now() - timedelta(days=30)).date()
            max_date = datetime.now().date()
        
        start_date = st.date_input(
            "Start Date", 
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Filter reports by date
    filtered_reports = [
        r for r in reports 
        if 'timestamp' in r and 
        start_date <= datetime.fromisoformat(r['timestamp'][:10]).date() <= end_date
    ]
    
    if not filtered_reports:
        st.warning(f"No reports found in the selected date range ({start_date} to {end_date}).")
        return
    
    # Analyze team health
    team_health_data = analyze_team_health(filtered_reports)
    
    # Display overview metrics
    render_health_overview(team_health_data)
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌡️ Team Temperature", "⚠️ Risk Assessment", "📊 Individual Analysis", "📈 Trends"
    ])
    
    with tab1:
        render_team_temperature(team_health_data)
    
    with tab2:
        render_risk_assessment(team_health_data)
    
    with tab3:
        render_individual_analysis(team_health_data, filtered_reports)
    
    with tab4:
        render_health_trends(filtered_reports)

def analyze_team_health(reports):
    """Analyze team health from reports."""
    team_data = {}
    
    for report in reports:
        name = report.get('name', 'Unknown')
        if name not in team_data:
            team_data[name] = {
                'reports': [],
                'sentiment_scores': [],
                'stress_scores': [],
                'workload_scores': [],
                'total_stress_indicators': 0,
                'last_report_date': None
            }
        
        # Analyze report content
        content = ' '.join([
            ' '.join(report.get('accomplishments', [])),
            report.get('challenges', ''),
            report.get('concerns', ''),
            ' '.join(f.get('description', '') for f in report.get('current_activities', []))
        ])
        
        sentiment = analyze_sentiment(content)
        stress = detect_stress_indicators(content)
        workload = calculate_workload_score(report.get('current_activities', []))
        
        # Store data
        team_data[name]['reports'].append(report)
        team_data[name]['sentiment_scores'].append(sentiment['sentiment_score'])
        team_data[name]['stress_scores'].append(stress['stress_score'])
        team_data[name]['workload_scores'].append(workload)
        team_data[name]['total_stress_indicators'] += stress['total_indicators']
        
        # Update last report date
        report_date = report.get('timestamp', '')[:10]
        if not team_data[name]['last_report_date'] or report_date > team_data[name]['last_report_date']:
            team_data[name]['last_report_date'] = report_date
    
    # Calculate averages and risk levels
    for name, data in team_data.items():
        data['avg_sentiment'] = np.mean(data['sentiment_scores']) if data['sentiment_scores'] else 5.0
        data['avg_stress'] = np.mean(data['stress_scores']) if data['stress_scores'] else 0.0
        data['avg_workload'] = np.mean(data['workload_scores']) if data['workload_scores'] else 0.0
        
        # Calculate burnout risk
        burnout_analysis = predict_burnout_risk(data['reports'])
        data['burnout_risk'] = burnout_analysis
        
        # Determine overall health status
        if data['avg_sentiment'] < 4 or data['avg_stress'] > 6 or data['avg_workload'] > 85:
            data['health_status'] = 'critical'
        elif data['avg_sentiment'] < 6 or data['avg_stress'] > 4 or data['avg_workload'] > 70:
            data['health_status'] = 'warning'
        else:
            data['health_status'] = 'healthy'
    
    return team_data

def render_health_overview(team_data):
    """Render team health overview metrics."""
    st.subheader("🎯 Team Health Overview")
    
    # Calculate team-wide metrics
    total_members = len(team_data)
    if total_members == 0:
        st.info("No team data available.")
        return
    
    critical_members = sum(1 for data in team_data.values() if data['health_status'] == 'critical')
    warning_members = sum(1 for data in team_data.values() if data['health_status'] == 'warning')
    healthy_members = sum(1 for data in team_data.values() if data['health_status'] == 'healthy')
    
    avg_team_sentiment = np.mean([data['avg_sentiment'] for data in team_data.values()])
    avg_team_stress = np.mean([data['avg_stress'] for data in team_data.values()])
    avg_team_workload = np.mean([data['avg_workload'] for data in team_data.values()])
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Team Members",
            total_members,
            delta=None
        )
        
    with col2:
        sentiment_color = "normal"
        if avg_team_sentiment < 4:
            sentiment_color = "inverse"
        elif avg_team_sentiment < 6:
            sentiment_color = "off"
            
        st.metric(
            "Avg Sentiment",
            f"{avg_team_sentiment:.1f}/10",
            delta=None
        )
    
    with col3:
        st.metric(
            "Avg Stress Level",
            f"{avg_team_stress:.1f}/10",
            delta=None
        )
    
    with col4:
        st.metric(
            "Avg Workload",
            f"{avg_team_workload:.0f}/100",
            delta=None
        )
    
    # Health status breakdown
    st.write("### Team Health Status")
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.metric("🟢 Healthy", healthy_members)
    with status_col2:
        st.metric("🟡 Warning", warning_members)
    with status_col3:
        st.metric("🔴 Critical", critical_members)
    
    # High-risk alerts
    if critical_members > 0:
        st.error(f"⚠️ {critical_members} team member(s) require immediate attention!")
        
        critical_names = [name for name, data in team_data.items() if data['health_status'] == 'critical']
        st.write("**Critical status members:**")
        for name in critical_names:
            burnout_risk = team_data[name]['burnout_risk']
            st.write(f"• **{name}** - Burnout risk: {burnout_risk['risk_level']} ({burnout_risk['risk_score']}/100)")

def render_team_temperature(team_data):
    """Render team temperature visualization."""
    st.subheader("🌡️ Team Temperature")
    st.write("Visual representation of team sentiment and stress levels")
    
    if not team_data:
        st.info("No data available for team temperature analysis.")
        return
    
    # Prepare data for visualization
    team_members = list(team_data.keys())
    sentiments = [team_data[name]['avg_sentiment'] for name in team_members]
    stress_levels = [team_data[name]['avg_stress'] for name in team_members]
    workloads = [team_data[name]['avg_workload'] for name in team_members]
    health_statuses = [team_data[name]['health_status'] for name in team_members]
    
    # Create temperature heatmap
    df = pd.DataFrame({
        'Team Member': team_members,
        'Sentiment': sentiments,
        'Stress Level': stress_levels,
        'Workload': workloads,
        'Health Status': health_statuses
    })
    
    # Sentiment vs Stress scatter plot
    fig = px.scatter(
        df,
        x='Sentiment',
        y='Stress Level',
        size='Workload',
        color='Health Status',
        hover_name='Team Member',
        color_discrete_map={
            'healthy': '#28a745',
            'warning': '#ffc107',
            'critical': '#dc3545'
        },
        title="Team Member Health Map",
        labels={
            'Sentiment': 'Sentiment Score (1-10)',
            'Stress Level': 'Stress Score (0-10)'
        }
    )
    
    # Add quadrant lines
    fig.add_hline(y=5, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=5, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Add quadrant labels
    fig.add_annotation(x=2.5, y=8.5, text="High Stress<br>Low Mood", showarrow=False, font=dict(color="red"))
    fig.add_annotation(x=7.5, y=8.5, text="High Stress<br>Good Mood", showarrow=False, font=dict(color="orange"))
    fig.add_annotation(x=2.5, y=1.5, text="Low Stress<br>Low Mood", showarrow=False, font=dict(color="blue"))
    fig.add_annotation(x=7.5, y=1.5, text="Low Stress<br>Good Mood", showarrow=False, font=dict(color="green"))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Team temperature gauge
    avg_sentiment = np.mean(sentiments)
    avg_stress = np.mean(stress_levels)
    
    # Calculate overall team temperature (0-100)
    team_temperature = ((avg_sentiment / 10) * 0.6 + (1 - avg_stress / 10) * 0.4) * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Temperature gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = team_temperature,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Team Temperature"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col2:
        st.write("### Temperature Interpretation")
        if team_temperature >= 80:
            st.success("🌟 **Excellent** - Team is thriving!")
        elif team_temperature >= 60:
            st.info("😊 **Good** - Team is doing well")
        elif team_temperature >= 40:
            st.warning("😐 **Fair** - Some areas need attention")
        else:
            st.error("😟 **Poor** - Team needs support")
        
        st.write(f"**Average Sentiment:** {avg_sentiment:.1f}/10")
        st.write(f"**Average Stress:** {avg_stress:.1f}/10")

def render_risk_assessment(team_data):
    """Render burnout risk assessment."""
    st.subheader("⚠️ Burnout Risk Assessment")
    
    if not team_data:
        st.info("No data available for risk assessment.")
        return
    
    # Prepare risk data
    risk_data = []
    for name, data in team_data.items():
        burnout_risk = data['burnout_risk']
        risk_data.append({
            'Name': name,
            'Risk Level': burnout_risk['risk_level'],
            'Risk Score': burnout_risk['risk_score'],
            'Weeks to Burnout': burnout_risk['weeks_to_burnout'] or 'N/A',
            'Last Report': data['last_report_date'] or 'Never',
            'Sentiment': f"{data['avg_sentiment']:.1f}",
            'Stress': f"{data['avg_stress']:.1f}",
            'Workload': f"{data['avg_workload']:.0f}"
        })
    
    # Sort by risk score (highest first)
    risk_data.sort(key=lambda x: x['Risk Score'], reverse=True)
    
    # Display risk table
    risk_df = pd.DataFrame(risk_data)
    
    # Color-code the risk levels
    def color_risk_level(val):
        if val == 'high':
            return 'background-color: #ffebee'
        elif val == 'medium':
            return 'background-color: #fff8e1'
        elif val == 'low':
            return 'background-color: #e8f5e8'
        return ''
    
    styled_df = risk_df.style.applymap(color_risk_level, subset=['Risk Level'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Risk distribution chart
    risk_counts = risk_df['Risk Level'].value_counts()
    fig = px.pie(
        values=risk_counts.values,
        names=risk_counts.index,
        title="Burnout Risk Distribution",
        color_discrete_map={
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#dc3545'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # High-risk recommendations
    high_risk_members = [item for item in risk_data if item['Risk Level'] == 'high']
    if high_risk_members:
        st.error("🚨 **Immediate Action Required**")
        st.write("The following team members require urgent attention:")
        
        for member in high_risk_members:
            with st.expander(f"🔴 {member['Name']} - Risk Score: {member['Risk Score']}/100"):
                data = team_data[member['Name']]
                recommendations = data['burnout_risk']['recommendations']
                
                st.write("**Recommended Actions:**")
                for rec in recommendations:
                    st.write(f"• {rec}")
                
                st.write("**Key Metrics:**")
                st.write(f"• Sentiment: {member['Sentiment']}/10")
                st.write(f"• Stress Level: {member['Stress']}/10")
                st.write(f"• Workload: {member['Workload']}/100")
                st.write(f"• Estimated weeks to burnout: {member['Weeks to Burnout']}")

def render_individual_analysis(team_data, reports):
    """Render individual team member analysis."""
    st.subheader("📊 Individual Analysis")
    
    if not team_data:
        st.info("No data available for individual analysis.")
        return
    
    # Team member selector
    selected_member = st.selectbox(
        "Select Team Member",
        options=list(team_data.keys()),
        help="Choose a team member to analyze in detail"
    )
    
    if not selected_member:
        return
    
    member_data = team_data[selected_member]
    
    # Display member overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Health Status", member_data['health_status'].title())
    with col2:
        st.metric("Avg Sentiment", f"{member_data['avg_sentiment']:.1f}/10")
    with col3:
        st.metric("Avg Stress", f"{member_data['avg_stress']:.1f}/10")
    with col4:
        st.metric("Avg Workload", f"{member_data['avg_workload']:.0f}/100")
    
    # Burnout risk details
    burnout_risk = member_data['burnout_risk']
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Burnout Risk Analysis")
        risk_color = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴'
        }.get(burnout_risk['risk_level'], '⚪')
        
        st.write(f"**Risk Level:** {risk_color} {burnout_risk['risk_level'].title()}")
        st.write(f"**Risk Score:** {burnout_risk['risk_score']}/100")
        
        if burnout_risk['weeks_to_burnout']:
            st.write(f"**Estimated weeks to burnout:** {burnout_risk['weeks_to_burnout']}")
        
        st.write("**Recommendations:**")
        for rec in burnout_risk['recommendations']:
            st.write(f"• {rec}")
    
    with col2:
        # Trend charts
        st.write("### Trends Over Time")
        
        if len(member_data['sentiment_scores']) > 1:
            trend_df = pd.DataFrame({
                'Report #': range(1, len(member_data['sentiment_scores']) + 1),
                'Sentiment': member_data['sentiment_scores'],
                'Stress': member_data['stress_scores'],
                'Workload': [w/10 for w in member_data['workload_scores']]  # Scale to 0-10
            })
            
            fig = px.line(
                trend_df,
                x='Report #',
                y=['Sentiment', 'Stress', 'Workload'],
                title=f"Trends for {selected_member}",
                labels={'value': 'Score (0-10)', 'variable': 'Metric'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need more reports to show trends")
    
    # Recent reports analysis
    st.write("### Recent Reports Analysis")
    
    recent_reports = sorted(member_data['reports'], key=lambda x: x.get('timestamp', ''), reverse=True)[:3]
    
    for i, report in enumerate(recent_reports):
        with st.expander(f"Report from {report.get('timestamp', 'Unknown')[:10]}"):
            # Analyze this specific report
            content = ' '.join([
                ' '.join(report.get('accomplishments', [])),
                report.get('challenges', ''),
                report.get('concerns', '')
            ])
            
            sentiment = analyze_sentiment(content)
            stress = detect_stress_indicators(content)
            
            st.write(f"**Sentiment:** {sentiment['sentiment_score']:.1f}/10 ({sentiment['sentiment_label']})")
            st.write(f"**Stress Indicators:** {stress['total_indicators']} detected")
            
            if stress['indicators']['high_stress']:
                st.warning(f"High stress keywords: {', '.join(stress['indicators']['high_stress'])}")
            
            if report.get('challenges'):
                st.write(f"**Challenges:** {report['challenges']}")

def render_health_trends(reports):
    """Render team health trends over time."""
    st.subheader("📈 Health Trends Over Time")
    
    if len(reports) < 2:
        st.info("Need more reports to show meaningful trends.")
        return
    
    # Group reports by week
    weekly_data = {}
    
    for report in reports:
        week = report.get('reporting_week', 'Unknown')
        if week not in weekly_data:
            weekly_data[week] = {
                'reports': [],
                'sentiments': [],
                'stress_scores': [],
                'workloads': []
            }
        
        # Analyze report
        content = ' '.join([
            ' '.join(report.get('accomplishments', [])),
            report.get('challenges', ''),
            report.get('concerns', '')
        ])
        
        sentiment = analyze_sentiment(content)
        stress = detect_stress_indicators(content)
        workload = calculate_workload_score(report.get('current_activities', []))
        
        weekly_data[week]['reports'].append(report)
        weekly_data[week]['sentiments'].append(sentiment['sentiment_score'])
        weekly_data[week]['stress_scores'].append(stress['stress_score'])
        weekly_data[week]['workloads'].append(workload)
    
    # Calculate weekly averages
    trend_data = []
    for week, data in weekly_data.items():
        trend_data.append({
            'Week': week,
            'Avg Sentiment': np.mean(data['sentiments']) if data['sentiments'] else 5.0,
            'Avg Stress': np.mean(data['stress_scores']) if data['stress_scores'] else 0.0,
            'Avg Workload': np.mean(data['workloads']) if data['workloads'] else 0.0,
            'Team Size': len(data['reports'])
        })
    
    # Sort by week
    trend_data.sort(key=lambda x: x['Week'])
    
    if not trend_data:
        st.info("No trend data available.")
        return
    
    # Create trend chart
    trend_df = pd.DataFrame(trend_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=trend_df['Week'],
        y=trend_df['Avg Sentiment'],
        mode='lines+markers',
        name='Sentiment',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=trend_df['Week'],
        y=trend_df['Avg Stress'],
        mode='lines+markers',
        name='Stress',
        line=dict(color='red'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Team Health Trends",
        xaxis_title="Week",
        yaxis_title="Sentiment Score (1-10)",
        yaxis2=dict(
            title="Stress Score (0-10)",
            overlaying='y',
            side='right'
        ),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend insights
    if len(trend_data) >= 3:
        recent_sentiment = trend_data[-1]['Avg Sentiment']
        previous_sentiment = trend_data[-2]['Avg Sentiment']
        sentiment_change = recent_sentiment - previous_sentiment
        
        recent_stress = trend_data[-1]['Avg Stress']
        previous_stress = trend_data[-2]['Avg Stress']
        stress_change = recent_stress - previous_stress
        
        st.write("### Recent Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if sentiment_change > 0.5:
                st.success(f"📈 Sentiment improving (+{sentiment_change:.1f})")
            elif sentiment_change < -0.5:
                st.warning(f"📉 Sentiment declining ({sentiment_change:.1f})")
            else:
                st.info("📊 Sentiment stable")
        
        with col2:
            if stress_change > 0.5:
                st.warning(f"📈 Stress increasing (+{stress_change:.1f})")
            elif stress_change < -0.5:
                st.success(f"📉 Stress decreasing ({stress_change:.1f})")
            else:
                st.info("📊 Stress level stable")
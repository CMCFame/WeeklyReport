# components/asdf_analytics_dashboard.py
"""ASDF Analytics Dashboard for tactical management insights with state-of-the-art visualizations."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from utils.file_ops import get_all_reports
from utils.constants import ASDF_PHASES, ASDF_PHASE_COLORS

def render_asdf_analytics_dashboard():
    """Render the ASDF Analytics Dashboard with tactical management insights."""
    st.title("🎯 ASDF Project Analytics")
    st.write("**Tactical insights into project lifecycle and resource allocation**")
    
    # Get all reports
    reports = get_all_reports(filter_by_user=False)
    if not reports:
        st.info("📊 Analytics will be available once team members submit reports with ASDF phase data.")
        return
    
    # Process ASDF data
    asdf_data = process_asdf_data(reports)
    
    if not asdf_data['activities']:
        st.warning("🔍 No ASDF phase data found in reports. Team members need to specify project phases in their activities.")
        return
    
    # Key metrics at the top
    render_asdf_key_metrics(asdf_data)
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌊 Pipeline Flow", "⚖️ Resource Balance", "🚨 Phase Alerts", "📈 Trends"
    ])
    
    with tab1:
        render_pipeline_flow_analysis(asdf_data)
    
    with tab2:
        render_resource_balance_analysis(asdf_data)
    
    with tab3:
        render_phase_alerts_analysis(asdf_data)
    
    with tab4:
        render_trends_analysis(asdf_data)

def process_asdf_data(reports):
    """Process reports to extract ASDF analytics data."""
    activities = []
    team_workload = {}
    
    for report in reports:
        team_member = report.get('name', 'Unknown')
        report_date = report.get('timestamp', '')[:10] if report.get('timestamp') else 'Unknown'
        
        # Initialize team member data
        if team_member not in team_workload:
            team_workload[team_member] = {
                'total_activities': 0,
                'phases': {phase: 0 for phase in ASDF_PHASES if phase}
            }
        
        # Process current activities
        for activity in report.get('current_activities', []):
            phase = activity.get('asdf_phase', '')
            if not phase:
                continue
                
            activities.append({
                'team_member': team_member,
                'date': report_date,
                'project': activity.get('project', 'Unspecified'),
                'phase': phase,
                'priority': activity.get('priority', 'Medium'),
                'status': activity.get('status', 'Unknown'),
                'progress': activity.get('progress', 0),
                'description': activity.get('description', '')
            })
            
            # Update team workload
            team_workload[team_member]['total_activities'] += 1
            team_workload[team_member]['phases'][phase] += 1
    
    return {
        'activities': activities,
        'team_workload': team_workload,
        'activity_df': pd.DataFrame(activities) if activities else None
    }

def render_asdf_key_metrics(asdf_data):
    """Render key ASDF metrics with tactical insights."""
    st.subheader("📊 Executive Summary")
    
    df = asdf_data['activity_df']
    
    # Calculate key metrics
    total_activities = len(df)
    active_projects = df['project'].nunique()
    team_members = df['team_member'].nunique()
    
    # Phase distribution
    phase_dist = df['phase'].value_counts()
    
    # Critical insights
    scoping_activities = phase_dist.get('Scoping', 0)
    scoping_percentage = (scoping_activities / total_activities * 100) if total_activities > 0 else 0
    
    delivery_activities = phase_dist.get('Delivery', 0)
    delivery_percentage = (delivery_activities / total_activities * 100) if total_activities > 0 else 0
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Active Projects", 
            active_projects,
            help="Total number of projects currently in progress"
        )
        
    with col2:
        st.metric(
            "Team Utilization", 
            f"{team_members} members",
            help="Number of team members actively reporting on projects"
        )
    
    with col3:
        st.metric(
            "Scoping Pipeline", 
            f"{scoping_activities} ({scoping_percentage:.1f}%)",
            delta=f"{scoping_percentage:.1f}% of total work",
            help="Activities in scoping phase - critical for pipeline health"
        )
    
    with col4:
        st.metric(
            "Active Delivery", 
            f"{delivery_activities} ({delivery_percentage:.1f}%)",
            delta=f"{delivery_percentage:.1f}% of total work",
            help="Activities in delivery phase - revenue generating work"
        )

def render_pipeline_flow_analysis(asdf_data):
    """Render pipeline flow visualization - shows project movement through ASDF phases."""
    st.subheader("🌊 Project Pipeline Flow")
    st.write("*Visualize how projects move through the ASDF lifecycle*")
    
    df = asdf_data['activity_df']
    
    # Create Sankey diagram data for pipeline flow
    phase_counts = df['phase'].value_counts()
    
    # Create a funnel chart showing ASDF phase distribution
    fig = go.Figure(go.Funnel(
        y = [phase for phase in ASDF_PHASES if phase and phase in phase_counts.index],
        x = [phase_counts.get(phase, 0) for phase in ASDF_PHASES if phase and phase in phase_counts.index],
        textposition = "inside",
        textinfo = "value+percent initial",
        opacity = 0.8,
        marker = {
            "color": [ASDF_PHASE_COLORS.get(phase, "#f8f9fa") for phase in ASDF_PHASES if phase and phase in phase_counts.index],
            "line": {"width": 2, "color": "white"}
        }
    ))
    
    fig.update_layout(
        title="Project Distribution Across ASDF Phases",
        font_size=12,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Phase transition matrix (advanced insight)
    col1, col2 = st.columns(2)
    
    with col1:
        # Projects by priority within each phase
        priority_phase = df.groupby(['phase', 'priority']).size().reset_index(name='count')
        
        fig = px.bar(
            priority_phase,
            x='phase',
            y='count',
            color='priority',
            title="Priority Distribution by Phase",
            color_discrete_map={
                'High': '#dc3545',
                'Medium': '#ffc107', 
                'Low': '#28a745'
            }
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Average progress by phase
        avg_progress = df.groupby('phase')['progress'].mean().reset_index()
        
        fig = px.bar(
            avg_progress,
            x='phase',
            y='progress',
            title="Average Progress by Phase",
            color='progress',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(height=300, yaxis_title="Average Progress (%)")
        st.plotly_chart(fig, use_container_width=True)

def render_resource_balance_analysis(asdf_data):
    """Render resource balance analysis - shows team allocation across phases."""
    st.subheader("⚖️ Resource Balance Analysis")
    st.write("*Optimize team allocation across ASDF phases*")
    
    team_workload = asdf_data['team_workload']
    
    # Create team workload heatmap
    team_names = list(team_workload.keys())
    phases = [phase for phase in ASDF_PHASES if phase]
    
    # Build workload matrix
    workload_matrix = []
    for team_member in team_names:
        row = [team_workload[team_member]['phases'].get(phase, 0) for phase in phases]
        workload_matrix.append(row)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=workload_matrix,
        x=phases,
        y=team_names,
        colorscale='Viridis',
        showscale=True,
        text=workload_matrix,
        texttemplate="%{text}",
        textfont={"size": 12},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="Team Member Workload by ASDF Phase",
        xaxis_title="ASDF Phase",
        yaxis_title="Team Member",
        height=max(400, 50 * len(team_names))
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Resource utilization insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Resource Utilization")
        
        # Calculate utilization metrics
        for team_member, data in team_workload.items():
            total = data['total_activities']
            if total > 0:
                # Find dominant phase
                dominant_phase = max(data['phases'], key=data['phases'].get)
                dominant_count = data['phases'][dominant_phase]
                specialization = (dominant_count / total * 100) if total > 0 else 0
                
                st.write(f"**{team_member}**")
                st.write(f"- Total Activities: {total}")
                st.write(f"- Primary Focus: {dominant_phase} ({specialization:.1f}%)")
                st.progress(specialization / 100)
                st.divider()
    
    with col2:
        st.subheader("🚦 Balance Recommendations")
        
        # Calculate phase totals
        phase_totals = {phase: 0 for phase in phases}
        for data in team_workload.values():
            for phase, count in data['phases'].items():
                if phase in phase_totals:
                    phase_totals[phase] += count
        
        total_work = sum(phase_totals.values())
        
        for phase in phases:
            count = phase_totals[phase]
            percentage = (count / total_work * 100) if total_work > 0 else 0
            
            # Provide tactical recommendations
            if phase == 'Scoping' and percentage < 15:
                st.warning(f"⚠️ **{phase}**: {percentage:.1f}% - Consider increasing scoping capacity")
            elif phase == 'Delivery' and percentage < 40:
                st.warning(f"⚠️ **{phase}**: {percentage:.1f}% - Low delivery capacity may impact revenue")
            else:
                st.success(f"✅ **{phase}**: {percentage:.1f}% - Good balance")

def render_phase_alerts_analysis(asdf_data):
    """Render phase-based alerts and recommendations."""
    st.subheader("🚨 Phase Alerts & Recommendations")
    st.write("*Proactive insights to prevent project bottlenecks*")
    
    df = asdf_data['activity_df']
    
    # Alert categories
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔴 Critical Alerts")
        
        # Stuck in scoping
        scoping_projects = df[df['phase'] == 'Scoping']['project'].unique()
        if len(scoping_projects) > 3:
            st.error(f"🚫 **{len(scoping_projects)} projects stuck in Scoping phase**")
            st.write("*Action: Review scoping capacity and process efficiency*")
        
        # High priority items not in delivery
        high_priority_non_delivery = df[
            (df['priority'] == 'High') & (df['phase'] != 'Delivery')
        ]
        if len(high_priority_non_delivery) > 0:
            st.error(f"🚫 **{len(high_priority_non_delivery)} high-priority items not in delivery**")
            st.write("*Action: Expedite these items to delivery phase*")
        
        # Blocked activities
        blocked_activities = df[df['status'] == 'Blocked']
        if len(blocked_activities) > 0:
            st.error(f"🚫 **{len(blocked_activities)} blocked activities**")
            for _, activity in blocked_activities.iterrows():
                st.write(f"- {activity['project']} ({activity['phase']})")
    
    with col2:
        st.subheader("🟡 Optimization Opportunities")
        
        # Qualification phase projects
        qualification_count = len(df[df['phase'] == 'Qualification'])
        if qualification_count > 0:
            st.warning(f"⚠️ **{qualification_count} projects in Qualification**")
            st.write("*Opportunity: Convert qualified leads to scoping*")
        
        # Low progress items
        low_progress = df[df['progress'] < 25]
        if len(low_progress) > 0:
            st.warning(f"⚠️ **{len(low_progress)} activities with <25% progress**")
            st.write("*Opportunity: Review blockers and accelerate progress*")
        
        # Initiation phase bottleneck
        initiation_count = len(df[df['phase'] == 'Initiation'])
        if initiation_count > 2:
            st.warning(f"⚠️ **{initiation_count} projects in Initiation phase**")
            st.write("*Opportunity: Streamline project kickoff process*")

def render_trends_analysis(asdf_data):
    """Render trend analysis over time."""
    st.subheader("📈 ASDF Trends Analysis")
    st.write("*Track project lifecycle patterns and team performance over time*")
    
    df = asdf_data['activity_df']
    
    if len(df) == 0:
        st.info("No trend data available yet. Trends will appear as more reports are submitted.")
        return
    
    # Convert date column to datetime for trend analysis
    df['date'] = pd.to_datetime(df['date'])
    
    # Phase trends over time
    st.subheader("🌊 Phase Distribution Trends")
    
    # Group by date and phase
    date_phase_trends = df.groupby(['date', 'phase']).size().reset_index(name='count')
    
    # Create stacked area chart for phase trends
    fig = px.area(
        date_phase_trends,
        x='date',
        y='count',
        color='phase',
        title="Project Phase Distribution Over Time",
        color_discrete_map=ASDF_PHASE_COLORS
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="Number of Activities",
        legend_title="ASDF Phase"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Progress trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Progress Velocity")
        
        # Average progress by date
        progress_trends = df.groupby('date')['progress'].mean().reset_index()
        
        fig = px.line(
            progress_trends,
            x='date',
            y='progress',
            title="Average Progress Over Time",
            markers=True
        )
        
        fig.update_layout(
            height=300,
            yaxis_title="Average Progress (%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Priority Focus")
        
        # Priority distribution over time
        priority_trends = df.groupby(['date', 'priority']).size().reset_index(name='count')
        
        fig = px.bar(
            priority_trends,
            x='date',
            y='count',
            color='priority',
            title="Priority Distribution Over Time",
            color_discrete_map={
                'High': '#dc3545',
                'Medium': '#ffc107',
                'Low': '#28a745'
            }
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Predictive insights
    st.subheader("🔮 Predictive Insights")
    
    # Simple trend predictions
    latest_data = df[df['date'] == df['date'].max()]
    phase_momentum = latest_data['phase'].value_counts()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📋 Scoping Pipeline")
        scoping_count = phase_momentum.get('Scoping', 0)
        if scoping_count > 3:
            st.success(f"✅ Strong pipeline ({scoping_count} projects)")
            st.write("*Expect increased delivery capacity in 2-4 weeks*")
        elif scoping_count > 0:
            st.warning(f"⚠️ Moderate pipeline ({scoping_count} projects)")
            st.write("*Consider increasing lead generation*")
        else:
            st.error("🚨 Weak pipeline")
            st.write("*Urgent: Focus on qualification and lead generation*")
    
    with col2:
        st.markdown("### 🚀 Delivery Capacity")
        delivery_count = phase_momentum.get('Delivery', 0)
        if delivery_count > 5:
            st.success(f"✅ High capacity ({delivery_count} projects)")
            st.write("*Revenue impact: Positive*")
        elif delivery_count > 2:
            st.info(f"ℹ️ Normal capacity ({delivery_count} projects)")
            st.write("*Revenue impact: Stable*")
        else:
            st.warning(f"⚠️ Low capacity ({delivery_count} projects)")
            st.write("*Revenue impact: Monitor closely*")
    
    with col3:
        st.markdown("### ⚖️ Resource Balance")
        total_active = len(latest_data)
        if total_active > 0:
            delivery_ratio = delivery_count / total_active
            if delivery_ratio > 0.5:
                st.success("✅ Well balanced")
                st.write("*Good execution focus*")
            elif delivery_ratio > 0.3:
                st.info("ℹ️ Moderately balanced")
                st.write("*Room for optimization*")
            else:
                st.warning("⚠️ Imbalanced")
                st.write("*Too much non-delivery work*")

def render_executive_summary_card(asdf_data):
    """Render a compact executive summary card for upper management."""
    st.markdown("### 📋 Executive Summary")
    
    df = asdf_data['activity_df']
    
    # Key insights for executives
    total_projects = df['project'].nunique()
    scoping_projects = len(df[df['phase'] == 'Scoping']['project'].unique())
    delivery_projects = len(df[df['phase'] == 'Delivery']['project'].unique())
    blocked_count = len(df[df['status'] == 'Blocked'])
    
    # Create summary metrics
    summary_html = f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="text-align: center;">
                <h3 style="color: #007bff; margin: 0;">{total_projects}</h3>
                <p style="margin: 0; font-size: 12px;">Active Projects</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: #17a2b8; margin: 0;">{scoping_projects}</h3>
                <p style="margin: 0; font-size: 12px;">In Scoping</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: #28a745; margin: 0;">{delivery_projects}</h3>
                <p style="margin: 0; font-size: 12px;">In Delivery</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: #dc3545; margin: 0;">{blocked_count}</h3>
                <p style="margin: 0; font-size: 12px;">Blocked</p>
            </div>
        </div>
    </div>
    """
    
    st.markdown(summary_html, unsafe_allow_html=True)
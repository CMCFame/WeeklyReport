# components/prioritization/priority_matrix.py
"""Priority matrix component for the Weekly Report app."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def render_priority_matrix():
    """Render a priority matrix for activities in the weekly report."""
    st.subheader("📊 Priority Matrix")
    st.write("Visualize your activities based on importance and urgency")
    
    # Get activities from session state
    current_activities = st.session_state.get('current_activities', [])
    upcoming_activities = st.session_state.get('upcoming_activities', [])
    
    if not current_activities and not upcoming_activities:
        st.info("Add some current or upcoming activities to visualize in the priority matrix.")
        return
    
    # Process activities for the matrix
    matrix_data = []
    
    for activity in current_activities:
        if not activity.get('description'):
            continue
            
        # Calculate urgency based on status and deadline
        urgency = 0
        
        # Status contributes to urgency
        status = activity.get('status', '').lower()
        if status == 'in progress':
            urgency += 2
        elif status == 'blocked':
            urgency += 3
        
        # Deadline contributes to urgency
        if activity.get('deadline'):
            from datetime import datetime
            try:
                deadline = datetime.strptime(activity.get('deadline'), '%Y-%m-%d').date()
                today = datetime.now().date()
                days_remaining = (deadline - today).days
                
                if days_remaining < 0:  # Overdue
                    urgency += 4
                elif days_remaining <= 3:  # Very soon
                    urgency += 3
                elif days_remaining <= 7:  # This week
                    urgency += 2
                elif days_remaining <= 14:  # Within two weeks
                    urgency += 1
            except:
                pass
        
        # Importance based on priority
        importance = 0
        priority = activity.get('priority', '').lower()
        
        if priority == 'high':
            importance = 3
        elif priority == 'medium':
            importance = 2
        elif priority == 'low':
            importance = 1
        
        # Cap values at 4
        urgency = min(4, urgency)
        importance = min(4, importance)
        
        # Add to matrix data
        matrix_data.append({
            'description': activity.get('description', 'Unnamed Activity'),
            'project': activity.get('project', 'No Project'),
            'importance': importance,
            'urgency': urgency,
            'type': 'Current',
            'activity': activity
        })
    
    # Add upcoming activities
    for activity in upcoming_activities:
        if not activity.get('description'):
            continue
            
        # Importance based on priority
        importance = 0
        priority = activity.get('priority', '').lower()
        
        if priority == 'high':
            importance = 3
        elif priority == 'medium':
            importance = 2
        elif priority == 'low':
            importance = 1
        
        # Urgency based on expected start
        urgency = 0
        
        if activity.get('expected_start'):
            from datetime import datetime
            try:
                start_date = datetime.strptime(activity.get('expected_start'), '%Y-%m-%d').date()
                today = datetime.now().date()
                days_until_start = (start_date - today).days
                
                if days_until_start < 0:  # Should have started already
                    urgency = 3
                elif days_until_start <= 3:  # Very soon
                    urgency = 2
                elif days_until_start <= 7:  # This week
                    urgency = 1
            except:
                pass
        
        # Cap values at 4
        urgency = min(4, urgency)
        importance = min(4, importance)
        
        # Add to matrix data
        matrix_data.append({
            'description': activity.get('description', 'Unnamed Activity'),
            'project': activity.get('project', 'No Project'),
            'importance': importance,
            'urgency': urgency,
            'type': 'Upcoming',
            'activity': activity
        })
    
    # Create the priority matrix
    if matrix_data:
        create_priority_matrix_visual(matrix_data)
        display_priority_recommendations(matrix_data)

def create_priority_matrix_visual(matrix_data):
    """Create a visual priority matrix using Plotly.
    
    Args:
        matrix_data (list): List of activity data dictionaries
    """
    # Create a dataframe for easier plotting
    df = pd.DataFrame(matrix_data)
    
    # Add some jitter to avoid perfect overlaps
    jitter = 0.1
    df['importance_jitter'] = df['importance'] + np.random.uniform(-jitter, jitter, size=len(df))
    df['urgency_jitter'] = df['urgency'] + np.random.uniform(-jitter, jitter, size=len(df))
    
    # Create the plot
    fig = go.Figure()
    
    # Add current activities
    current_df = df[df['type'] == 'Current']
    if not current_df.empty:
        fig.add_trace(go.Scatter(
            x=current_df['urgency_jitter'],
            y=current_df['importance_jitter'],
            mode='markers',
            marker=dict(
                size=12,
                color='#1E88E5',  # Blue
                line=dict(width=1, color='darkgrey')
            ),
            text=current_df['description'] + '<br>Project: ' + current_df['project'] + '<br>Type: Current',
            hoverinfo='text',
            name='Current Activities'
        ))
    
    # Add upcoming activities
    upcoming_df = df[df['type'] == 'Upcoming']
    if not upcoming_df.empty:
        fig.add_trace(go.Scatter(
            x=upcoming_df['urgency_jitter'],
            y=upcoming_df['importance_jitter'],
            mode='markers',
            marker=dict(
                size=12,
                color='#43A047',  # Green
                line=dict(width=1, color='darkgrey')
            ),
            text=upcoming_df['description'] + '<br>Project: ' + upcoming_df['project'] + '<br>Type: Upcoming',
            hoverinfo='text',
            name='Upcoming Activities'
        ))
    
    # Add quadrant lines
    fig.add_shape(
        type="line",
        x0=2, y0=0,
        x1=2, y1=4,
        line=dict(color="grey", dash="dash")
    )
    
    fig.add_shape(
        type="line",
        x0=0, y0=2,
        x1=4, y1=2,
        line=dict(color="grey", dash="dash")
    )
    
    # Add quadrant labels
    fig.add_annotation(
        x=1, y=3,
        text="Important<br>Not Urgent",
        showarrow=False,
        font=dict(size=10)
    )
    
    fig.add_annotation(
        x=3, y=3,
        text="Important<br>Urgent",
        showarrow=False,
        font=dict(size=10)
    )
    
    fig.add_annotation(
        x=1, y=1,
        text="Not Important<br>Not Urgent",
        showarrow=False,
        font=dict(size=10)
    )
    
    fig.add_annotation(
        x=3, y=1,
        text="Not Important<br>Urgent",
        showarrow=False,
        font=dict(size=10)
    )
    
    # Set axis ranges and labels
    fig.update_layout(
        xaxis=dict(
            title="Urgency",
            range=[0, 4],
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["", "Low", "Medium", "High", "Very High"]
        ),
        yaxis=dict(
            title="Importance",
            range=[0, 4],
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["", "Low", "Medium", "High", "Very High"]
        ),
        title="Priority Matrix",
        height=500,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    # Display the plot
    st.plotly_chart(fig, use_container_width=True)

def display_priority_recommendations(matrix_data):
    """Display activity recommendations based on the priority matrix.
    
    Args:
        matrix_data (list): List of activity data dictionaries
    """
    # Group activities by quadrant
    q1 = []  # Important & Urgent
    q2 = []  # Important & Not Urgent
    q3 = []  # Not Important & Urgent
    q4 = []  # Not Important & Not Urgent
    
    for item in matrix_data:
        importance = item['importance']
        urgency = item['urgency']
        
        if importance >= 2 and urgency >= 2:
            q1.append(item)
        elif importance >= 2 and urgency < 2:
            q2.append(item)
        elif importance < 2 and urgency >= 2:
            q3.append(item)
        else:
            q4.append(item)
    
    # Display recommendations
    st.subheader("Priority Recommendations")
    
    with st.expander("Focus on these first (Important & Urgent)", expanded=True):
        if q1:
            for item in q1:
                st.markdown(f"**{item['description']}** - {item['project']}")
        else:
            st.info("No activities in this quadrant.")
    
    with st.expander("Schedule time for these (Important & Not Urgent)"):
        if q2:
            for item in q2:
                st.markdown(f"**{item['description']}** - {item['project']}")
        else:
            st.info("No activities in this quadrant.")
    
    with st.expander("Delegate if possible (Not Important & Urgent)"):
        if q3:
            for item in q3:
                st.markdown(f"**{item['description']}** - {item['project']}")
        else:
            st.info("No activities in this quadrant.")
    
    with st.expander("Consider eliminating (Not Important & Not Urgent)"):
        if q4:
            for item in q4:
                st.markdown(f"**{item['description']}** - {item['project']}")
        else:
            st.info("No activities in this quadrant.")
            
    # Overall recommendation
    st.write("### Summary")
    if q1:
        st.info(f"You have {len(q1)} important and urgent activities to focus on first.")
    
    # Tips based on matrix distribution
    total = len(matrix_data)
    if total > 0:
        q1_pct = len(q1) / total * 100
        
        if q1_pct > 50:
            st.warning("⚠️ You have a high number of urgent and important activities. Consider if some could be rescheduled or delegated to reduce potential burnout.")
        elif q1_pct < 10 and len(q2) > len(q1):
            st.success("✅ Good job at planning ahead! You have more important but not yet urgent activities than crisis items.")
            
        if len(q4) > total * 0.3:
            st.warning("⚠️ You might be spending too much time on low-priority activities. Consider eliminating some of these tasks or delegating them.")
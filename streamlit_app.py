"""
Smart Schedule Manager - STREAMLIT WEB VERSION
Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import datetime
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# ============ YOUR EXISTING SCHEDULE DATA ============
CLASSES = [
    ("Sunday", 8, 30, 10, 0, "CSE405"),
    ("Sunday", 10, 10, 11, 40, "CSE303"),
    ("Sunday", 13, 30, 15, 30, "CSE303 Lab"),
    ("Monday", 8, 0, 10, 0, "CSE347 Lab"),
    ("Monday", 10, 10, 11, 40, "CSE347"),
    ("Monday", 16, 50, 18, 20, "FIN101"),
    ("Tuesday", 8, 30, 10, 0, "CSE405"),
    ("Wednesday", 10, 10, 11, 40, "CSE347"),
    ("Wednesday", 16, 50, 18, 20, "FIN101"),
    ("Thursday", 8, 0, 10, 0, "CSE405 Lab"),
    ("Thursday", 10, 10, 11, 40, "CSE303"),
]

DAILY_ROUTINE = [
    (6, 30, 7, 30, "SQL practice + revision", "study"),
    (7, 30, 8, 0, "Travel / breakfast buffer", "break"),
    (10, 0, 10, 10, "Short break", "break"),
    (11, 40, 13, 30, "Assignments / self‑study / lunch", "study"),
    (15, 30, 16, 50, "DataCamp + mini dataset practice", "study"),
    (18, 20, 19, 30, "Dinner + break", "break"),
    (19, 30, 20, 30, "DataCamp track", "study"),
    (20, 30, 21, 30, "Kaggle practice", "study"),
    (21, 30, 22, 0, "GitHub update & review", "study"),
    (22, 0, 23, 0, "Light reading (AI news)", "study"),
]

COURSE_NOTES = {
    "CSE405": "💻 Bring laptop, final project due",
    "CSE303": "📘 Review chapter 5 before class",
    "CSE347": "🗄️ Database design - bring ER diagram",
    "FIN101": "💰 Bring calculator"
}

# ============ HELPER FUNCTIONS ============
def to_minutes(h, m):
    return h * 60 + m

def format_time(hour, minute):
    period = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    return f"{hour_12}:{minute:02d}{period}"

def get_current_activity():
    """Get current activity"""
    now = datetime.datetime.now()
    weekday = now.strftime("%A")
    current_min = to_minutes(now.hour, now.minute)
    
    if weekday in ["Friday", "Saturday"]:
        return "WEEKEND - Free day!", None, None
    
    # Check classes
    for cls in CLASSES:
        if cls[0] == weekday:
            _, sh, sm, eh, em, name = cls
            start = to_minutes(sh, sm)
            end = to_minutes(eh, em)
            if start <= current_min < end:
                remaining = end - current_min
                return f"📚 CLASS: {name}", remaining, (start, end)
    
    # Check routine
    for sh, sm, eh, em, desc, act_type in DAILY_ROUTINE:
        start = to_minutes(sh, sm)
        end = to_minutes(eh, em)
        if start <= current_min < end:
            remaining = end - current_min
            icon = "📖" if act_type == "study" else "☕"
            return f"{icon} {desc}", remaining, (start, end)
    
    return "✨ Free time - Study or rest", None, None

def get_today_schedule():
    """Get today's full schedule"""
    now = datetime.datetime.now()
    weekday = now.strftime("%A")
    current_min = to_minutes(now.hour, now.minute)
    
    if weekday in ["Friday", "Saturday"]:
        return []
    
    schedule = []
    
    # Add classes
    for cls in CLASSES:
        if cls[0] == weekday:
            _, sh, sm, eh, em, name = cls
            schedule.append({
                'start': format_time(sh, sm),
                'end': format_time(eh, em),
                'activity': f"📚 {name}",
                'type': 'class',
                'start_min': to_minutes(sh, sm),
                'end_min': to_minutes(eh, em),
                'duration': to_minutes(eh, em) - to_minutes(sh, sm)
            })
    
    # Add routine
    for sh, sm, eh, em, desc, act_type in DAILY_ROUTINE:
        icon = "📖" if act_type == "study" else "☕"
        schedule.append({
            'start': format_time(sh, sm),
            'end': format_time(eh, em),
            'activity': f"{icon} {desc}",
            'type': act_type,
            'start_min': to_minutes(sh, sm),
            'end_min': to_minutes(eh, em),
            'duration': to_minutes(eh, em) - to_minutes(sh, sm)
        })
    
    # Sort by start time
    schedule.sort(key=lambda x: x['start_min'])
    
    # Mark current activity
    for item in schedule:
        item['is_current'] = item['start_min'] <= current_min < item['end_min']
    
    return schedule

def get_time_distribution():
    """Get time distribution for pie chart"""
    schedule = get_today_schedule()
    
    distribution = {}
    for item in schedule:
        if 'class' in item['type']:
            distribution['📚 Classes'] = distribution.get('📚 Classes', 0) + item['duration']
        elif item['type'] == 'study':
            distribution['📖 Study'] = distribution.get('📖 Study', 0) + item['duration']
        elif item['type'] == 'break':
            distribution['☕ Breaks'] = distribution.get('☕ Breaks', 0) + item['duration']
    
    return distribution

def get_weekly_stats():
    """Get weekly statistics for bar chart"""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    stats = []
    
    for day in days:
        class_hours = 0
        study_hours = 0
        
        # Calculate class hours
        for cls in CLASSES:
            if cls[0] == day:
                _, sh, sm, eh, em, _ = cls
                class_hours += (to_minutes(eh, em) - to_minutes(sh, sm)) / 60
        
        # Calculate study hours
        if day not in ["Friday", "Saturday"]:
            for sh, sm, eh, em, _, act_type in DAILY_ROUTINE:
                if act_type == "study":
                    study_hours += (to_minutes(eh, em) - to_minutes(sh, sm)) / 60
        
        stats.append({
            'day': day,
            'class_hours': round(class_hours, 1),
            'study_hours': round(study_hours, 1),
            'total_hours': round(class_hours + study_hours, 1)
        })
    
    return stats

# ============ MAIN STREAMLIT APP ============
def main():
    # Page configuration
    st.set_page_config(
        page_title="Smart Schedule Manager",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stButton button {
            width: 100%;
        }
        .task-completed {
            text-decoration: line-through;
            opacity: 0.6;
        }
        .current-activity {
            background-color: #f0f2ff;
            padding: 10px;
            border-radius: 10px;
            border-left: 4px solid #4CAF50;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for tasks
    if 'completed_tasks' not in st.session_state:
        st.session_state.completed_tasks = set()
    
    # Header
    st.title("🎓 Smart Schedule Manager")
    st.caption("Your personal academic assistant")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Overview")
        now = datetime.datetime.now()
        st.metric("Current Time", now.strftime("%I:%M %p"))
        st.metric("Today's Date", now.strftime("%B %d, %Y"))
        st.metric("Day", now.strftime("%A"))
        
        st.divider()
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        if st.button("🍅 Start Pomodoro", use_container_width=True):
            st.session_state.show_timer = True
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Current Activity Card
        st.subheader("🟢 Current Activity")
        activity, remaining, _ = get_current_activity()
        
        if remaining:
            remaining_str = f"{remaining // 60}h {remaining % 60}m remaining"
        else:
            remaining_str = "Enjoy your free time!"
        
        st.info(f"**{activity}**  \n⏱️ {remaining_str}")
        
        # Today's Schedule
        st.subheader("📋 Today's Schedule")
        schedule = get_today_schedule()
        
        if schedule:
            # Convert to DataFrame for display
            df = pd.DataFrame(schedule)
            df_display = df[['start', 'end', 'activity']].copy()
            
            # Add completion checkboxes
            for idx, row in df.iterrows():
                col1, col2, col3 = st.columns([1, 3, 1])
                task_key = row['activity']
                is_current = row.get('is_current', False)
                
                with col1:
                    checked = st.checkbox(
                        "✓",
                        key=f"task_{idx}",
                        value=task_key in st.session_state.completed_tasks
                    )
                    if checked:
                        st.session_state.completed_tasks.add(task_key)
                    elif task_key in st.session_state.completed_tasks:
                        st.session_state.completed_tasks.remove(task_key)
                
                with col2:
                    if is_current:
                        st.markdown(f"**▶ {row['start']} - {row['end']}: {row['activity']}**")
                    else:
                        if task_key in st.session_state.completed_tasks:
                            st.markdown(f"~~{row['start']} - {row['end']}: {row['activity']}~~")
                        else:
                            st.markdown(f"{row['start']} - {row['end']}: {row['activity']}")
                
                with col3:
                    if is_current:
                        st.caption("🟢 CURRENT")
        
        else:
            st.info("🎉 Weekend! Time to relax or work on personal projects!")
    
    with col2:
        # Today's Progress
        st.subheader("📈 Today's Progress")
        schedule = get_today_schedule()
        if schedule:
            total_duration = sum(item['duration'] for item in schedule)
            completed_duration = 0
            
            now_min = to_minutes(datetime.datetime.now().hour, datetime.datetime.now().minute)
            for item in schedule:
                if item['end_min'] <= now_min:
                    completed_duration += item['duration']
                elif item['activity'] in st.session_state.completed_tasks:
                    completed_duration += item['duration']
            
            progress = int((completed_duration / total_duration) * 100) if total_duration > 0 else 0
            
            st.progress(progress, text=f"{progress}% Complete")
            st.metric("Tasks Completed", f"{len(st.session_state.completed_tasks)}")
    
    # Charts Section
    st.divider()
    st.subheader("📊 Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie Chart - Time Distribution
        st.write("**Today's Time Distribution**")
        distribution = get_time_distribution()
        if distribution:
            fig = go.Figure(data=[go.Pie(
                labels=list(distribution.keys()),
                values=list(distribution.values()),
                hole=0.4,
                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#FFE66D'])
            )])
            fig.update_layout(height=400, margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for today (weekend)")
    
    with col2:
        # Bar Chart - Weekly Overview
        st.write("**Weekly Study Hours**")
        weekly_stats = get_weekly_stats()
        df_weekly = pd.DataFrame(weekly_stats)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['study_hours'],
            name='Study Hours',
            marker_color='#4ECDC4'
        ))
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['class_hours'],
            name='Class Hours',
            marker_color='#FF6B6B'
        ))
        fig.update_layout(
            barmode='group',
            height=400,
            margin=dict(t=0, l=0, r=0, b=0),
            yaxis_title="Hours"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Course Notes Section
    st.divider()
    st.subheader("📝 Course Notes")
    
    now = datetime.datetime.now()
    weekday = now.strftime("%A")
    today_courses = set()
    for cls in CLASSES:
        if cls[0] == weekday:
            course_code = cls[5]
            if any(course_code.startswith(prefix) for prefix in ['CSE', 'FIN']):
                today_courses.add(course_code)
    
    if today_courses:
        cols = st.columns(len(today_courses))
        for idx, course in enumerate(today_courses):
            with cols[idx]:
                note = COURSE_NOTES.get(course, "No notes available")
                st.info(f"**{course}**  \n{note}")
    
    # Pomodoro Timer Modal
    if st.session_state.get('show_timer', False):
        st.divider()
        st.subheader("🍅 Pomodoro Timer")
        
        timer_minutes = st.selectbox("Select duration:", [25, 45, 60], index=0)
        
        if st.button("Start Timer"):
            with st.spinner(f"Focus for {timer_minutes} minutes..."):
                # Simple countdown
                placeholder = st.empty()
                for remaining in range(timer_minutes * 60, 0, -1):
                    mins = remaining // 60
                    secs = remaining % 60
                    placeholder.markdown(f"### ⏰ Time remaining: {mins:02d}:{secs:02d}")
                    time.sleep(1)
                placeholder.markdown("### 🎉 Time's up! Great work!")
                st.balloons()
            st.session_state.show_timer = False
            st.rerun()

# Add time import
import time

if __name__ == "__main__":
    main()
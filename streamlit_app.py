"""
Smart Schedule Manager - STREAMLIT WEB VERSION (FIXED)
Now with proper sleep time detection
"""

import streamlit as st
import datetime
import time
import pandas as pd
import plotly.graph_objects as go

# ============ YOUR SCHEDULE DATA ============
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
    """Get current activity - Enhanced with sleep time detection"""
    now = datetime.datetime.now()
    weekday = now.strftime("%A")
    current_min = to_minutes(now.hour, now.minute)
    
    # Sleep hours: 11 PM to 5 AM
    is_sleep_time = current_min < to_minutes(5, 0) or current_min >= to_minutes(23, 0)
    
    if weekday in ["Friday", "Saturday"]:
        return "WEEKEND - Free day!", None, is_sleep_time
    
    # Check if it's sleeping hours
    if is_sleep_time:
        # Find first activity of the day
        first_start = None
        first_name = None
        
        for cls in CLASSES:
            if cls[0] == weekday:
                _, sh, sm, _, _, name = cls
                start = to_minutes(sh, sm)
                if first_start is None or start < first_start:
                    first_start = start
                    first_name = f"📚 {name}"
        
        for sh, sm, _, _, desc, act_type in DAILY_ROUTINE:
            start = to_minutes(sh, sm)
            if first_start is None or start < first_start:
                first_start = start
                icon = "📖" if act_type == "study" else "☕"
                first_name = f"{icon} {desc}"
        
        if first_start and first_name:
            time_until = first_start - current_min
            hours = time_until // 60
            mins = time_until % 60
            first_time = format_time(first_start//60, first_start%60)
            return f"😴 Sleep time! First activity at {first_time}: {first_name} (in {hours}h {mins}m)", None, True
    
    # Check classes
    for cls in CLASSES:
        if cls[0] == weekday:
            _, sh, sm, eh, em, name = cls
            start = to_minutes(sh, sm)
            end = to_minutes(eh, em)
            if start <= current_min < end:
                remaining = end - current_min
                return f"📚 CLASS: {name}", remaining, False
    
    # Check routine
    for sh, sm, eh, em, desc, act_type in DAILY_ROUTINE:
        start = to_minutes(sh, sm)
        end = to_minutes(eh, em)
        if start <= current_min < end:
            remaining = end - current_min
            icon = "📖" if act_type == "study" else "☕"
            return f"{icon} {desc}", remaining, False
    
    # Find next activity
    next_start = None
    next_name = None
    
    for cls in CLASSES:
        if cls[0] == weekday:
            _, sh, sm, _, _, name = cls
            start = to_minutes(sh, sm)
            if start > current_min:
                if next_start is None or start < next_start:
                    next_start = start
                    next_name = f"📚 {name}"
    
    for sh, sm, _, _, desc, act_type in DAILY_ROUTINE:
        start = to_minutes(sh, sm)
        if start > current_min:
            if next_start is None or start < next_start:
                next_start = start
                icon = "📖" if act_type == "study" else "☕"
                next_name = f"{icon} {desc}"
    
    if next_start and next_name:
        time_until = next_start - current_min
        hours = time_until // 60
        mins = time_until % 60
        return f"✨ Free time until {next_name} (in {hours}h {mins}m)", None, False
    
    return "✨ Free time - Day complete!", None, False

def get_today_schedule():
    """Get today's full schedule"""
    now = datetime.datetime.now()
    weekday = now.strftime("%A")
    current_min = to_minutes(now.hour, now.minute)
    
    if weekday in ["Friday", "Saturday"]:
        return []
    
    schedule = []
    
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
    
    schedule.sort(key=lambda x: x['start_min'])
    
    for item in schedule:
        item['is_current'] = item['start_min'] <= current_min < item['end_min']
    
    return schedule

def get_time_distribution():
    """Get time distribution for pie chart"""
    schedule = get_today_schedule()
    
    distribution = {}
    for item in schedule:
        if item['type'] == 'class':
            distribution['📚 Classes'] = distribution.get('📚 Classes', 0) + item['duration']
        elif item['type'] == 'study':
            distribution['📖 Study'] = distribution.get('📖 Study', 0) + item['duration']
        elif item['type'] == 'break':
            distribution['☕ Breaks'] = distribution.get('☕ Breaks', 0) + item['duration']
    
    return distribution

def get_weekly_stats():
    """Get weekly statistics"""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    stats = []
    
    for day in days:
        class_hours = 0
        study_hours = 0
        
        for cls in CLASSES:
            if cls[0] == day:
                _, sh, sm, eh, em, _ = cls
                class_hours += (to_minutes(eh, em) - to_minutes(sh, sm)) / 60
        
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

# ============ MAIN APP ============
def main():
    st.set_page_config(page_title="Smart Schedule Manager", page_icon="🎓", layout="wide")
    
    if 'completed_tasks' not in st.session_state:
        st.session_state.completed_tasks = set()
    if 'show_timer' not in st.session_state:
        st.session_state.show_timer = False
    
    st.title("🎓 Smart Schedule Manager")
    st.caption("Your personal academic assistant")
    
    with st.sidebar:
        st.header("📊 Overview")
        now = datetime.datetime.now()
        st.metric("Current Time", now.strftime("%I:%M %p"))
        st.metric("Today's Date", now.strftime("%B %d, %Y"))
        st.metric("Day", now.strftime("%A"))
        
        st.divider()
        
        st.subheader("⚡ Quick Actions")
        if st.button("🍅 Start Pomodoro", use_container_width=True):
            st.session_state.show_timer = True
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🟢 Current Activity")
        activity, remaining, is_sleep_time = get_current_activity()
        
        if is_sleep_time:
            st.warning(f"**{activity}**")
        elif remaining:
            st.info(f"**{activity}**  \n⏱️ {remaining // 60}h {remaining % 60}m remaining")
        else:
            st.info(f"**{activity}**")
        
        st.subheader("📋 Today's Schedule")
        schedule = get_today_schedule()
        
        if schedule:
            for idx, row in enumerate(schedule):
                col_a, col_b, col_c = st.columns([0.5, 3, 1])
                task_key = row['activity']
                is_current = row.get('is_current', False)
                
                with col_a:
                    checked = st.checkbox("✓", key=f"task_{idx}", value=task_key in st.session_state.completed_tasks)
                    if checked:
                        st.session_state.completed_tasks.add(task_key)
                    elif task_key in st.session_state.completed_tasks:
                        st.session_state.completed_tasks.remove(task_key)
                
                with col_b:
                    if is_current:
                        st.markdown(f"**▶ {row['start']} - {row['end']}: {row['activity']}**")
                    elif task_key in st.session_state.completed_tasks:
                        st.markdown(f"~~{row['start']} - {row['end']}: {row['activity']}~~")
                    else:
                        st.markdown(f"{row['start']} - {row['end']}: {row['activity']}")
                
                with col_c:
                    if is_current:
                        st.caption("🟢 NOW")
        else:
            st.info("🎉 Weekend! Time to relax!")
    
    with col2:
        st.subheader("📈 Today's Progress")
        if schedule:
            total = sum(item['duration'] for item in schedule)
            completed = 0
            now_min = to_minutes(datetime.datetime.now().hour, datetime.datetime.now().minute)
            for item in schedule:
                if item['end_min'] <= now_min or item['activity'] in st.session_state.completed_tasks:
                    completed += item['duration']
            
            progress = int((completed / total) * 100) if total > 0 else 0
            st.progress(progress, text=f"{progress}% Complete")
            st.metric("Tasks Completed", f"{len(st.session_state.completed_tasks)}")
    
    # Charts
    st.divider()
    st.subheader("📊 Analytics")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.write("**Today's Time Distribution**")
        distribution = get_time_distribution()
        if distribution:
            fig = go.Figure(data=[go.Pie(labels=list(distribution.keys()), values=list(distribution.values()), hole=0.4)])
            fig.update_layout(height=400, margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        st.write("**Weekly Study Hours**")
        weekly_stats = get_weekly_stats()
        df_weekly = pd.DataFrame(weekly_stats)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_weekly['day'], y=df_weekly['study_hours'], name='Study', marker_color='#4ECDC4'))
        fig.add_trace(go.Bar(x=df_weekly['day'], y=df_weekly['class_hours'], name='Class', marker_color='#FF6B6B'))
        fig.update_layout(barmode='group', height=400, margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    # Course Notes
    st.divider()
    st.subheader("📝 Course Notes")
    
    now = datetime.datetime.now()
    weekday = now.strftime("%A")
    today_courses = set()
    for cls in CLASSES:
        if cls[0] == weekday:
            today_courses.add(cls[5])
    
    if today_courses:
        cols = st.columns(len(today_courses))
        for idx, course in enumerate(today_courses):
            with cols[idx]:
                note = COURSE_NOTES.get(course, "No notes available")
                st.info(f"**{course}**  \n{note}")
    
    # Pomodoro Timer
    if st.session_state.get('show_timer', False):
        st.divider()
        st.subheader("🍅 Pomodoro Timer")
        minutes = st.selectbox("Duration:", [25, 45, 60], index=0)
        if st.button("Start Timer"):
            with st.spinner(f"Focus for {minutes} minutes..."):
                placeholder = st.empty()
                for remaining in range(minutes * 60, 0, -1):
                    mins = remaining // 60
                    secs = remaining % 60
                    placeholder.markdown(f"### ⏰ {mins:02d}:{secs:02d}")
                    time.sleep(1)
                placeholder.markdown("### 🎉 Done! Great work!")
                st.balloons()
            st.session_state.show_timer = False
            st.rerun()

if __name__ == "__main__":
    main()

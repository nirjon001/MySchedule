"""
Smart Schedule Manager - ENHANCED VERSION
Tracks actual completed activities, study time, and gap utilization
"""

import streamlit as st
import datetime
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import pytz

# ============ BANGLADESH TIMEZONE ============
DHAKA_TZ = pytz.timezone('Asia/Dhaka')

def get_now():
    """Get current time in Bangladesh timezone"""
    return datetime.datetime.now(DHAKA_TZ)

# ============ SCHEDULE DATA ============
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

def get_all_activities():
    """Get all activities for today"""
    now = get_now()
    weekday = now.strftime("%A")
    
    if weekday in ["Friday", "Saturday"]:
        return []
    
    activities = []
    
    # Add classes
    for cls in CLASSES:
        if cls[0] == weekday:
            _, sh, sm, eh, em, name = cls
            activities.append({
                'name': f"📚 {name}",
                'start': (sh, sm),
                'end': (eh, em),
                'type': 'class',
                'start_min': to_minutes(sh, sm),
                'end_min': to_minutes(eh, em),
                'duration': to_minutes(eh, em) - to_minutes(sh, sm)
            })
    
    # Add routine
    for sh, sm, eh, em, desc, act_type in DAILY_ROUTINE:
        icon = "📖" if act_type == "study" else "☕"
        activities.append({
            'name': f"{icon} {desc}",
            'start': (sh, sm),
            'end': (eh, em),
            'type': act_type,
            'start_min': to_minutes(sh, sm),
            'end_min': to_minutes(eh, em),
            'duration': to_minutes(eh, em) - to_minutes(sh, sm)
        })
    
    activities.sort(key=lambda x: x['start_min'])
    return activities

def get_current_activity():
    """Get current activity"""
    now = get_now()
    weekday = now.strftime("%A")
    current_min = to_minutes(now.hour, now.minute)
    
    if weekday in ["Friday", "Saturday"]:
        return "WEEKEND - Free day!", None
    
    activities = get_all_activities()
    
    for act in activities:
        if act['start_min'] <= current_min < act['end_min']:
            remaining = act['end_min'] - current_min
            return act['name'], remaining
    
    # Find next activity
    for act in activities:
        if act['start_min'] > current_min:
            time_until = act['start_min'] - current_min
            hours = time_until // 60
            mins = time_until % 60
            return f"✨ Free until {act['name']} (in {hours}h {mins}m)", None
    
    return "✨ Free time - Day complete!", None

def get_gaps_and_utilization(completed_activities):
    """Find gaps between activities and mark if utilized"""
    activities = get_all_activities()
    
    if len(activities) < 2:
        return []
    
    gaps = []
    now = get_now()
    current_min = to_minutes(now.hour, now.minute)
    
    for i in range(len(activities) - 1):
        current_end = activities[i]['end_min']
        next_start = activities[i + 1]['start_min']
        gap_duration = next_start - current_end
        
        if gap_duration > 5:  # Only show gaps longer than 5 minutes
            # Check if gap has passed
            is_passed = current_end <= current_min
            
            # Check if gap was utilized (any study activity done during this time)
            utilized = False
            utilized_note = ""
            
            # Look for study blocks that fall within this gap
            for act in activities:
                if act['type'] == 'study':
                    if current_end <= act['start_min'] <= next_start:
                        # Check if this study block was completed
                        if act['name'] in completed_activities:
                            utilized = True
                            utilized_note = "✓ Used for study"
                        elif act['start_min'] <= current_min:
                            utilized_note = "⏳ In progress"
                        else:
                            utilized_note = "⏰ Upcoming"
            
            gaps.append({
                'start_time': activities[i]['end'],
                'end_time': activities[i + 1]['start'],
                'start_min': current_end,
                'end_min': next_start,
                'duration': gap_duration,
                'is_passed': is_passed,
                'utilized': utilized,
                'utilized_note': utilized_note,
                'between': f"{activities[i]['name'].split(' ', 1)[1]} → {activities[i+1]['name'].split(' ', 1)[1]}"
            })
    
    return gaps

def get_todays_stats(completed_activities):
    """Get today's statistics based on ACTUAL completed activities"""
    activities = get_all_activities()
    now = get_now()
    current_min = to_minutes(now.hour, now.minute)
    
    # Calculate completed study time (only activities marked complete OR passed)
    total_study_minutes = 0
    completed_study_minutes = 0
    total_class_minutes = 0
    attended_class_minutes = 0
    
    for act in activities:
        if act['type'] == 'study':
            total_study_minutes += act['duration']
            # Consider complete if marked or time has passed
            if act['name'] in completed_activities or act['end_min'] <= current_min:
                completed_study_minutes += act['duration']
        elif act['type'] == 'class':
            total_class_minutes += act['duration']
            if act['end_min'] <= current_min:
                attended_class_minutes += act['duration']
    
    # Count completed tasks
    completed_tasks = len([a for a in activities if a['name'] in completed_activities])
    total_tasks = len([a for a in activities if a['type'] == 'study'])
    
    # Calculate progress percentage
    study_progress = int((completed_study_minutes / total_study_minutes) * 100) if total_study_minutes > 0 else 0
    class_progress = int((attended_class_minutes / total_class_minutes) * 100) if total_class_minutes > 0 else 0
    
    return {
        'total_study_minutes': total_study_minutes,
        'completed_study_minutes': completed_study_minutes,
        'study_progress': study_progress,
        'total_class_minutes': total_class_minutes,
        'attended_class_minutes': attended_class_minutes,
        'class_progress': class_progress,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'activities': activities
    }

def get_weekly_stats():
    """Get weekly statistics for bar chart"""
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

def create_completed_pie_chart(stats):
    """Create pie chart showing ONLY completed vs remaining"""
    completed = stats['completed_study_minutes']
    remaining = stats['total_study_minutes'] - completed
    
    if completed == 0 and remaining == 0:
        return None
    
    fig = go.Figure(data=[go.Pie(
        labels=['✅ Completed Study', '⏳ Remaining Study'],
        values=[completed, remaining],
        hole=0.4,
        marker=dict(colors=['#4ECDC4', '#FF6B6B']),
        textinfo='label+percent',
        textposition='auto'
    )])
    fig.update_layout(height=400, margin=dict(t=0, l=0, r=0, b=0))
    return fig

# ============ MAIN APP ============
def main():
    st.set_page_config(page_title="Smart Schedule Manager", page_icon="🎓", layout="wide")
    
    # Initialize session state
    if 'completed_activities' not in st.session_state:
        st.session_state.completed_activities = set()
    if 'show_timer' not in st.session_state:
        st.session_state.show_timer = False
    
    st.title("🎓 Smart Schedule Manager")
    st.caption("Your personal academic assistant")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Overview")
        now = get_now()
        st.metric("Current Time", now.strftime("%I:%M %p"))
        st.metric("Today's Date", now.strftime("%B %d, %Y"))
        st.metric("Day", now.strftime("%A"))
        st.caption("🇧🇩 Bangladesh Time (UTC+6)")
        
        st.divider()
        
        st.subheader("⚡ Quick Actions")
        if st.button("🍅 Start Pomodoro", use_container_width=True):
            st.session_state.show_timer = True
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        st.divider()
        
        # Reset button for testing
        if st.button("🗑️ Reset Today's Progress", use_container_width=True):
            st.session_state.completed_activities = set()
            st.rerun()
    
    # Get current stats
    stats = get_todays_stats(st.session_state.completed_activities)
    
    # Main content - 3 columns
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("🟢 Current Activity")
        activity, remaining = get_current_activity()
        
        if remaining:
            remaining_str = f"{remaining // 60}h {remaining % 60}m remaining"
            st.info(f"**{activity}**  \n⏱️ {remaining_str}")
        else:
            st.info(f"**{activity}**")
        
        st.subheader("📋 Today's Schedule")
        activities = stats['activities']
        
        if activities:
            for idx, act in enumerate(activities):
                col_a, col_b, col_c = st.columns([0.5, 3, 1])
                is_completed = act['name'] in st.session_state.completed_activities
                is_current = act['start_min'] <= to_minutes(get_now().hour, get_now().minute) < act['end_min']
                
                with col_a:
                    if act['type'] == 'study':  # Only study tasks are checkable
                        checked = st.checkbox(
                            "✓",
                            key=f"task_{idx}",
                            value=is_completed
                        )
                        if checked and not is_completed:
                            st.session_state.completed_activities.add(act['name'])
                            st.rerun()
                        elif not checked and is_completed:
                            st.session_state.completed_activities.remove(act['name'])
                            st.rerun()
                    else:
                        st.write("📌")
                
                with col_b:
                    if is_current:
                        st.markdown(f"**▶ {act['name']}**")
                        st.caption(f"_{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}_")
                    elif is_completed:
                        st.markdown(f"~~{act['name']}~~")
                        st.caption(f"_{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}_")
                    else:
                        st.markdown(act['name'])
                        st.caption(f"{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}")
                
                with col_c:
                    if is_current:
                        st.caption("🟢 NOW")
                    elif is_completed:
                        st.caption("✅ DONE")
        else:
            st.info("🎉 Weekend! Time to relax!")
    
    with col2:
        st.subheader("📊 Today's Study Progress")
        
        # Show total study time
        total_hours = stats['total_study_minutes'] // 60
        total_mins = stats['total_study_minutes'] % 60
        completed_hours = stats['completed_study_minutes'] // 60
        completed_mins = stats['completed_study_minutes'] % 60
        
        st.metric(
            "📖 Total Study Time",
            f"{completed_hours}h {completed_mins}m / {total_hours}h {total_mins}m",
            delta=f"{stats['study_progress']}% complete"
        )
        
        # Progress bar
        st.progress(stats['study_progress'] / 100, text=f"{stats['study_progress']}% of study goals met")
        
        st.divider()
        
        st.subheader("✅ Task Completion")
        st.metric(
            "Study Tasks",
            f"{stats['completed_tasks']} / {stats['total_tasks']}",
            delta=f"{int(stats['completed_tasks']/stats['total_tasks']*100) if stats['total_tasks']>0 else 0}%"
        )
        
        st.divider()
        
        st.subheader("📚 Class Attendance")
        class_hours = stats['attended_class_minutes'] // 60
        class_mins = stats['attended_class_minutes'] % 60
        total_class_hours = stats['total_class_minutes'] // 60
        total_class_mins = stats['total_class_minutes'] % 60
        
        st.metric(
            "Classes Attended",
            f"{class_hours}h {class_mins}m / {total_class_hours}h {total_class_mins}m",
            delta=f"{stats['class_progress']}%"
        )
    
    with col3:
        st.subheader("⏰ Time Gaps")
        
        gaps = get_gaps_and_utilization(st.session_state.completed_activities)
        
        if gaps:
            for gap in gaps:
                duration_hours = gap['duration'] // 60
                duration_mins = gap['duration'] % 60
                
                if gap['utilized']:
                    st.success(f"✅ **{duration_hours}h {duration_mins}m gap**")
                    st.caption(f"_{gap['between']}_")
                    st.caption(f"✓ Utilized: {gap['utilized_note']}")
                elif gap['is_passed']:
                    st.error(f"❌ **{duration_hours}h {duration_mins}m gap WASTED**")
                    st.caption(f"_{gap['between']}_")
                    st.caption("⚠️ Free time not used for studying")
                else:
                    st.warning(f"⏰ **{duration_hours}h {duration_mins}m gap ahead**")
                    st.caption(f"_{gap['between']}_")
                    st.caption("💡 Plan to use this time for study!")
                st.divider()
        else:
            st.info("No significant gaps today! 🎉")
    
    # Analytics Section - ONLY SHOWS COMPLETED DATA
    st.divider()
    st.subheader("📊 Your Achievements Today")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Pie chart of completed vs remaining
        st.write("**Study Time Breakdown**")
        pie_chart = create_completed_pie_chart(stats)
        if pie_chart:
            st.plotly_chart(pie_chart, use_container_width=True)
        else:
            st.info("No study data yet. Start studying! 📚")
    
    with col_b:
        # Bar chart - Weekly comparison (planned vs what you've done this week)
        st.write("**Weekly Study Hours (Planned)**")
        weekly_stats = get_weekly_stats()
        df_weekly = pd.DataFrame(weekly_stats)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['study_hours'],
            name='Planned Study',
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
    
    # Today's timeline with completion status
    st.divider()
    st.subheader("📅 Today's Timeline")
    
    if activities:
        timeline_data = []
        for act in activities:
            is_completed = act['name'] in st.session_state.completed_activities
            status = "✅ Completed" if is_completed else "⏳ Pending"
            if act['start_min'] <= to_minutes(get_now().hour, get_now().minute) < act['end_min']:
                status = "🟢 In Progress"
            
            timeline_data.append({
                'Time': f"{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}",
                'Activity': act['name'],
                'Status': status,
                'Duration': f"{act['duration'] // 60}h {act['duration'] % 60}m"
            })
        
        df_timeline = pd.DataFrame(timeline_data)
        st.dataframe(df_timeline, use_container_width=True, hide_index=True)
    
    # Course Notes
    st.divider()
    st.subheader("📝 Course Notes")
    
    now = get_now()
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
        
        timer_minutes = st.selectbox("Select duration:", [25, 45, 60], index=0)
        
        if st.button("Start Timer"):
            with st.spinner(f"Focus for {timer_minutes} minutes..."):
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

if __name__ == "__main__":
    main()

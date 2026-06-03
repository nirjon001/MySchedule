"""
Smart Schedule Manager - COMPACT TABBED VERSION
All features organized in tabs for a clean interface
"""

import streamlit as st
import datetime
import time
import pandas as pd
import plotly.graph_objects as go
import pytz

# ============ BANGLADESH TIMEZONE ============
DHAKA_TZ = pytz.timezone('Asia/Dhaka')

def get_now():
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
    (6, 30, 7, 30, "SQL practice", "study"),
    (7, 30, 8, 0, "Travel/Breakfast", "break"),
    (10, 0, 10, 10, "Short break", "break"),
    (11, 40, 13, 30, "Assignments/Lunch", "study"),
    (15, 30, 16, 50, "DataCamp", "study"),
    (18, 20, 19, 30, "Dinner break", "break"),
    (19, 30, 20, 30, "DataCamp track", "study"),
    (20, 30, 21, 30, "Kaggle practice", "study"),
    (21, 30, 22, 0, "GitHub update", "study"),
    (22, 0, 23, 0, "AI reading", "study"),
]

COURSE_NOTES = {
    "CSE405": "💻 Bring laptop, final project due",
    "CSE303": "📘 Review chapter 5",
    "CSE347": "🗄️ Database design",
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
    now = get_now()
    weekday = now.strftime("%A")
    
    if weekday in ["Friday", "Saturday"]:
        return []
    
    activities = []
    
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
    now = get_now()
    weekday = now.strftime("%A")
    current_min = to_minutes(now.hour, now.minute)
    
    if weekday in ["Friday", "Saturday"]:
        return "🎉 Weekend!", None
    
    activities = get_all_activities()
    
    for act in activities:
        if act['start_min'] <= current_min < act['end_min']:
            remaining = act['end_min'] - current_min
            return act['name'], remaining
    
    for act in activities:
        if act['start_min'] > current_min:
            time_until = act['start_min'] - current_min
            hours = time_until // 60
            mins = time_until % 60
            return f"✨ Free until {act['name']}", None
    
    return "✨ Day complete!", None

def get_gaps_and_utilization(completed_activities):
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
        
        if gap_duration > 5:
            is_passed = current_end <= current_min
            
            utilized = False
            for act in activities:
                if act['type'] == 'study' and current_end <= act['start_min'] <= next_start:
                    if act['name'] in completed_activities:
                        utilized = True
                        break
            
            gaps.append({
                'duration': gap_duration,
                'is_passed': is_passed,
                'utilized': utilized,
                'between': f"{activities[i]['name'].split(' ',1)[1][:20]} → {activities[i+1]['name'].split(' ',1)[1][:20]}"
            })
    
    return gaps

def get_todays_stats(completed_activities):
    activities = get_all_activities()
    now = get_now()
    current_min = to_minutes(now.hour, now.minute)
    
    total_study = 0
    completed_study = 0
    total_tasks = 0
    completed_tasks = 0
    
    for act in activities:
        if act['type'] == 'study':
            total_study += act['duration']
            total_tasks += 1
            if act['name'] in completed_activities or act['end_min'] <= current_min:
                completed_study += act['duration']
                if act['name'] in completed_activities:
                    completed_tasks += 1
    
    study_progress = int((completed_study / total_study) * 100) if total_study > 0 else 0
    
    return {
        'total_study': total_study,
        'completed_study': completed_study,
        'study_progress': study_progress,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks
    }

def get_weekly_stats():
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    stats = []
    
    for day in days:
        class_hours = 0
        study_hours = 0
        
        full_day = day + 'day' if day != 'Sat' and day != 'Sun' else day + 'urday' if day == 'Sat' else day + 'day'
        for cls in CLASSES:
            if cls[0] == full_day:
                _, sh, sm, eh, em, _ = cls
                class_hours += (to_minutes(eh, em) - to_minutes(sh, sm)) / 60
        
        if full_day not in ["Friday", "Saturday"]:
            for sh, sm, eh, em, _, act_type in DAILY_ROUTINE:
                if act_type == "study":
                    study_hours += (to_minutes(eh, em) - to_minutes(sh, sm)) / 60
        
        stats.append({'day': day, 'class': round(class_hours, 1), 'study': round(study_hours, 1)})
    
    return stats

# ============ MAIN APP ============
def main():
    st.set_page_config(page_title="Schedule Manager", page_icon="🎓", layout="wide")
    
    if 'completed_activities' not in st.session_state:
        st.session_state.completed_activities = set()
    if 'show_timer' not in st.session_state:
        st.session_state.show_timer = False
    
    # Header with current time
    now = get_now()
    st.title("🎓 Smart Schedule Manager")
    
    # Top bar with key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🕐 Time", now.strftime("%I:%M %p"))
    with col2:
        st.metric("📅 Date", now.strftime("%d %b"))
    with col3:
        st.metric("📆 Day", now.strftime("%A")[:3])
    with col4:
        activity, _ = get_current_activity()
        st.metric("🎯 Now", activity[:15] + "..." if len(activity) > 15 else activity)
    with col5:
        stats = get_todays_stats(st.session_state.completed_activities)
        st.metric("📊 Progress", f"{stats['study_progress']}%")
    
    st.divider()
    
    # Create Tabs for organization
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Today", "✅ Tasks", "📊 Analytics", "⏰ Gaps", "📝 Notes"
    ])
    
    # ========== TAB 1: TODAY'S SCHEDULE ==========
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📅 Today's Schedule")
            activities = get_all_activities()
            
            if activities:
                for idx, act in enumerate(activities):
                    is_completed = act['name'] in st.session_state.completed_activities
                    is_current = act['start_min'] <= to_minutes(now.hour, now.minute) < act['end_min']
                    
                    # Use columns for compact display
                    cols = st.columns([0.3, 2, 1, 0.5])
                    
                    with cols[0]:
                        if act['type'] == 'study':
                            st.checkbox("", key=f"c_{idx}", value=is_completed, 
                                       on_change=lambda: st.rerun())
                        else:
                            st.write("📌")
                    
                    with cols[1]:
                        if is_current:
                            st.markdown(f"**{act['name']}**")
                        elif is_completed:
                            st.markdown(f"~~{act['name']}~~")
                        else:
                            st.write(act['name'])
                    
                    with cols[2]:
                        st.caption(f"{format_time(act['start'][0], act['start'][1])}")
                    
                    with cols[3]:
                        if is_current:
                            st.caption("▶️")
                        elif is_completed:
                            st.caption("✅")
            else:
                st.info("🎉 Weekend! Enjoy!")
        
        with col2:
            st.subheader("🎯 Current Focus")
            activity, remaining = get_current_activity()
            if remaining:
                st.info(f"**{activity}**\n\n⏱️ {remaining//60}h {remaining%60}m left")
            else:
                st.info(f"**{activity}**")
            
            st.divider()
            
            # Pomodoro quick button
            if st.button("🍅 Start Pomodoro", use_container_width=True):
                st.session_state.show_timer = True
    
    # ========== TAB 2: TASKS & PROGRESS ==========
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Today's Study Tasks")
            activities = get_all_activities()
            study_tasks = [a for a in activities if a['type'] == 'study']
            
            if study_tasks:
                for idx, task in enumerate(study_tasks):
                    is_completed = task['name'] in st.session_state.completed_activities
                    col_a, col_b, col_c = st.columns([0.5, 3, 1])
                    
                    with col_a:
                        checked = st.checkbox("", key=f"task_{idx}", value=is_completed)
                        if checked != is_completed:
                            if checked:
                                st.session_state.completed_activities.add(task['name'])
                            else:
                                st.session_state.completed_activities.remove(task['name'])
                            st.rerun()
                    
                    with col_b:
                        if is_completed:
                            st.markdown(f"~~{task['name']}~~")
                        else:
                            st.write(task['name'])
                    
                    with col_c:
                        duration = task['duration']
                        st.caption(f"{duration//60}h {duration%60}m")
            else:
                st.info("No study tasks today")
        
        with col2:
            st.subheader("📈 Progress")
            stats = get_todays_stats(st.session_state.completed_activities)
            
            # Study time progress
            st.write("**Study Time**")
            study_hours = stats['completed_study'] // 60
            study_mins = stats['completed_study'] % 60
            total_hours = stats['total_study'] // 60
            total_mins = stats['total_study'] % 60
            st.progress(stats['study_progress'] / 100)
            st.caption(f"{study_hours}h {study_mins}m / {total_hours}h {total_mins}m")
            
            st.divider()
            
            # Tasks progress
            st.write("**Tasks Completed**")
            st.progress(stats['completed_tasks'] / stats['total_tasks'] if stats['total_tasks'] > 0 else 0)
            st.caption(f"{stats['completed_tasks']} / {stats['total_tasks']} tasks")
    
    # ========== TAB 3: ANALYTICS ==========
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Today's Study Breakdown")
            stats = get_todays_stats(st.session_state.completed_activities)
            
            completed = stats['completed_study']
            remaining = stats['total_study'] - completed
            
            if completed > 0 or remaining > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=['✅ Completed', '⏳ Remaining'],
                    values=[completed, remaining],
                    hole=0.5,
                    marker=dict(colors=['#4ECDC4', '#FF6B6B'])
                )])
                fig.update_layout(height=350, margin=dict(t=0, l=0, r=0, b=0), showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No study data yet")
        
        with col2:
            st.subheader("📅 Weekly Overview")
            weekly = get_weekly_stats()
            df = pd.DataFrame(weekly)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df['day'], y=df['study'], name='Study', marker_color='#4ECDC4'))
            fig.add_trace(go.Bar(x=df['day'], y=df['class'], name='Class', marker_color='#FF6B6B'))
            fig.update_layout(barmode='group', height=350, margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    # ========== TAB 4: TIME GAPS ==========
    with tab4:
        st.subheader("⏰ Free Time Gaps")
        gaps = get_gaps_and_utilization(st.session_state.completed_activities)
        
        if gaps:
            for gap in gaps:
                hours = gap['duration'] // 60
                mins = gap['duration'] % 60
                
                if gap['utilized']:
                    st.success(f"✅ {hours}h {mins}m - Used productively")
                elif gap['is_passed']:
                    st.error(f"❌ {hours}h {mins}m - WASTED")
                else:
                    st.warning(f"⏰ {hours}h {mins}m - Plan to use this")
                st.caption(f"_{gap['between']}_")
                st.divider()
        else:
            st.info("🎉 No significant gaps! Perfect schedule!")
        
        # Productivity tip
        st.divider()
        st.caption("💡 **Tip:** Check off tasks as you complete them to track your productivity!")
    
    # ========== TAB 5: COURSE NOTES ==========
    with tab5:
        st.subheader("📝 Today's Course Notes")
        
        weekday = now.strftime("%A")
        today_courses = []
        for cls in CLASSES:
            if cls[0] == weekday:
                course = cls[5]
                if course not in today_courses:
                    today_courses.append(course)
        
        if today_courses:
            cols = st.columns(min(len(today_courses), 3))
            for idx, course in enumerate(today_courses):
                with cols[idx % 3]:
                    note = COURSE_NOTES.get(course, "No notes")
                    st.info(f"**{course}**\n\n{note}")
        else:
            st.info("No classes today - perfect for catching up!")
        
        st.divider()
        st.subheader("📚 All Course Notes")
        for course, note in COURSE_NOTES.items():
            st.write(f"**{course}:** {note}")
    
    # ========== POMODORO MODAL ==========
    if st.session_state.get('show_timer', False):
        with st.expander("🍅 Pomodoro Timer", expanded=True):
            minutes = st.selectbox("Duration:", [25, 45, 60], key="pomodoro_duration")
            if st.button("Start Focus Session"):
                with st.spinner(f"Focusing for {minutes} minutes..."):
                    placeholder = st.empty()
                    for remaining in range(minutes * 60, 0, -1):
                        mins = remaining // 60
                        secs = remaining % 60
                        placeholder.markdown(f"## ⏰ {mins:02d}:{secs:02d}")
                        time.sleep(1)
                    placeholder.markdown("## 🎉 Great work! Time's up!")
                    st.balloons()
                st.session_state.show_timer = False
                st.rerun()

if __name__ == "__main__":
    main()

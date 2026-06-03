"""
Smart Schedule Manager - COMPACT VERSION
Previous layout with smaller font to fit everything
"""

import streamlit as st
import datetime
import time
import pandas as pd
import plotly.graph_objects as go
import pytz

# ============ COMPACT CSS ============
st.markdown("""
    <style>
        /* Smaller fonts everywhere */
        .stMarkdown, .stText, .stCaption, div[data-testid="stMetric"] {
            font-size: 12px !important;
        }
        h1 {
            font-size: 24px !important;
        }
        h2, h3, .stSubheader {
            font-size: 16px !important;
        }
        .stButton button {
            font-size: 12px !important;
            padding: 4px 8px !important;
        }
        div[data-testid="stMetric"] label {
            font-size: 11px !important;
        }
        div[data-testid="stMetric"] div {
            font-size: 16px !important;
        }
        .stProgress > div > div {
            height: 8px !important;
        }
        /* Reduce padding */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        hr {
            margin: 0.5rem 0 !important;
        }
    </style>
""", unsafe_allow_html=True)

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
    (6, 30, 7, 30, "SQL practice + revision", "study"),
    (7, 30, 8, 0, "Travel / breakfast", "break"),
    (10, 0, 10, 10, "Short break", "break"),
    (11, 40, 13, 30, "Assignments / self-study / lunch", "study"),
    (15, 30, 16, 50, "DataCamp + dataset practice", "study"),
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
        return "WEEKEND - Free day!", None
    
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
            return f"✨ Free until {act['name']} (in {hours}h {mins}m)", None
    
    return "✨ Free time - Day complete!", None

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
            utilized_note = ""
            
            for act in activities:
                if act['type'] == 'study' and current_end <= act['start_min'] <= next_start:
                    if act['name'] in completed_activities:
                        utilized = True
                        utilized_note = "✓ Used for study"
                    elif act['start_min'] <= current_min:
                        utilized_note = "⏳ In progress"
                    else:
                        utilized_note = "⏰ Upcoming"
            
            gaps.append({
                'duration': gap_duration,
                'is_passed': is_passed,
                'utilized': utilized,
                'utilized_note': utilized_note,
                'between': f"{activities[i]['name'].split(' ', 1)[1][:25]} → {activities[i+1]['name'].split(' ', 1)[1][:25]}"
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
            'day': day[:3],
            'class_hours': round(class_hours, 1),
            'study_hours': round(study_hours, 1),
        })
    
    return stats

# ============ MAIN APP ============
def main():
    st.set_page_config(page_title="Schedule Manager", page_icon="🎓", layout="wide")
    
    if 'completed_activities' not in st.session_state:
        st.session_state.completed_activities = set()
    if 'show_timer' not in st.session_state:
        st.session_state.show_timer = False
    
    # Header
    st.title("🎓 Smart Schedule Manager")
    st.caption("🇧🇩 Bangladesh Time (UTC+6)")
    
    # Top metrics row (compact)
    now = get_now()
    stats = get_todays_stats(st.session_state.completed_activities)
    activity, _ = get_current_activity()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🕐 Time", now.strftime("%I:%M %p"))
    with col2:
        st.metric("📅 Date", now.strftime("%d %b"))
    with col3:
        st.metric("📆 Day", now.strftime("%A"))
    with col4:
        st.metric("🎯 Progress", f"{stats['study_progress']}%")
    with col5:
        st.metric("✅ Tasks", f"{stats['completed_tasks']}/{stats['total_tasks']}")
    
    st.divider()
    
    # Main 3-column layout
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("🟢 Current Activity")
        activity, remaining = get_current_activity()
        if remaining:
            st.info(f"**{activity}**  \n⏱️ {remaining // 60}h {remaining % 60}m remaining")
        else:
            st.info(f"**{activity}**")
        
        st.subheader("📋 Today's Schedule")
        activities = get_all_activities()
        
        if activities:
            for idx, act in enumerate(activities):
                is_completed = act['name'] in st.session_state.completed_activities
                is_current = act['start_min'] <= to_minutes(now.hour, now.minute) < act['end_min']
                
                col_a, col_b, col_c = st.columns([0.3, 3, 1])
                
                with col_a:
                    if act['type'] == 'study':
                        checked = st.checkbox("✓", key=f"task_{idx}", value=is_completed)
                        if checked != is_completed:
                            if checked:
                                st.session_state.completed_activities.add(act['name'])
                            else:
                                st.session_state.completed_activities.remove(act['name'])
                            st.rerun()
                    else:
                        st.write("📌")
                
                with col_b:
                    if is_current:
                        st.markdown(f"**▶ {act['name']}**")
                        st.caption(f"{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}")
                    elif is_completed:
                        st.markdown(f"~~{act['name']}~~")
                        st.caption(f"{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}")
                    else:
                        st.markdown(act['name'])
                        st.caption(f"{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}")
                
                with col_c:
                    if is_current:
                        st.caption("🟢 NOW")
                    elif is_completed:
                        st.caption("✅")
        else:
            st.info("🎉 Weekend! Time to relax!")
    
    with col2:
        st.subheader("📊 Progress Dashboard")
        
        # Study time progress
        st.write("**Study Time**")
        study_hours = stats['completed_study'] // 60
        study_mins = stats['completed_study'] % 60
        total_hours = stats['total_study'] // 60
        total_mins = stats['total_study'] % 60
        st.progress(stats['study_progress'] / 100)
        st.caption(f"{study_hours}h {study_mins}m / {total_hours}h {total_mins}m")
        
        st.divider()
        
        # Study breakdown pie chart
        st.write("**Study Breakdown**")
        completed = stats['completed_study']
        remaining = stats['total_study'] - completed
        
        if completed > 0 or remaining > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['✅ Done', '⏳ Left'],
                values=[completed, remaining],
                hole=0.5,
                marker=dict(colors=['#4ECDC4', '#FF6B6B']),
                textinfo='percent',
                showlegend=False
            )])
            fig.update_layout(height=200, margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No study data yet")
        
        st.divider()
        
        # Quick Pomodoro
        if st.button("🍅 Start Pomodoro", use_container_width=True):
            st.session_state.show_timer = True
    
    with col3:
        st.subheader("⏰ Time Gaps")
        
        gaps = get_gaps_and_utilization(st.session_state.completed_activities)
        
        if gaps:
            for gap in gaps[:3]:  # Show only first 3 gaps
                hours = gap['duration'] // 60
                mins = gap['duration'] % 60
                
                if gap['utilized']:
                    st.success(f"✅ {hours}h {mins}m - Used")
                elif gap['is_passed']:
                    st.error(f"❌ {hours}h {mins}m - Wasted")
                else:
                    st.warning(f"⏰ {hours}h {mins}m - Coming up")
                st.caption(f"_{gap['between'][:35]}..._")
            if len(gaps) > 3:
                st.caption(f"... and {len(gaps)-3} more gaps")
        else:
            st.info("No significant gaps!")
        
        st.divider()
        
        # Weekly overview (compact bar chart)
        st.subheader("📅 Weekly Overview")
        weekly_stats = get_weekly_stats()
        df_weekly = pd.DataFrame(weekly_stats)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['study_hours'],
            name='Study',
            marker_color='#4ECDC4',
            text=df_weekly['study_hours'],
            textposition='auto',
            textfont=dict(size=10)
        ))
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['class_hours'],
            name='Class',
            marker_color='#FF6B6B',
            text=df_weekly['class_hours'],
            textposition='auto',
            textfont=dict(size=10)
        ))
        fig.update_layout(
            barmode='group',
            height=250,
            margin=dict(t=10, l=0, r=0, b=0),
            legend=dict(orientation='h', yanchor='bottom', y=1, xanchor='right', x=1),
            font=dict(size=10)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Course notes at bottom
    st.divider()
    st.subheader("📝 Today's Course Notes")
    
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
                st.caption(f"**{course}**  \n{note}")
    else:
        st.caption("No classes today - catch up on studies!")
    
    # Pomodoro Timer Modal
    if st.session_state.get('show_timer', False):
        st.divider()
        with st.expander("🍅 Pomodoro Timer", expanded=True):
            timer_minutes = st.selectbox("Duration:", [25, 45, 60], index=0)
            if st.button("Start Focus Session"):
                with st.spinner(f"Focusing for {timer_minutes} minutes..."):
                    placeholder = st.empty()
                    for remaining in range(timer_minutes * 60, 0, -1):
                        mins = remaining // 60
                        secs = remaining % 60
                        placeholder.markdown(f"### ⏰ {mins:02d}:{secs:02d}")
                        time.sleep(1)
                    placeholder.markdown("### 🎉 Great work! Time's up!")
                    st.balloons()
                st.session_state.show_timer = False
                st.rerun()

if __name__ == "__main__":
    main()

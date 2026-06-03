"""
Smart Schedule Manager - ENHANCED COMPACT VERSION
All features with smaller fonts for better screen fit
"""

import streamlit as st
import datetime
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
            margin-bottom: 0.5rem !important;
        }
        h2, h3, .stSubheader {
            font-size: 16px !important;
            margin-bottom: 0.3rem !important;
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
            height: 6px !important;
        }
        /* Reduce padding */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        hr {
            margin: 0.3rem 0 !important;
        }
        /* Smaller dataframe */
        .stDataFrame {
            font-size: 11px !important;
        }
        /* Compact info/warning boxes */
        .stAlert {
            padding: 0.3rem !important;
            font-size: 12px !important;
        }
    </style>
""", unsafe_allow_html=True)

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
            
            # Check if gap was utilized
            utilized = False
            utilized_note = ""
            
            for act in activities:
                if act['type'] == 'study':
                    if current_end <= act['start_min'] <= next_start:
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
                'between': f"{activities[i]['name'].split(' ', 1)[1][:20]} → {activities[i+1]['name'].split(' ', 1)[1][:20]}"
            })
    
    return gaps

def get_todays_stats(completed_activities):
    """Get today's statistics based on ACTUAL completed activities"""
    activities = get_all_activities()
    now = get_now()
    current_min = to_minutes(now.hour, now.minute)
    
    total_study_minutes = 0
    completed_study_minutes = 0
    total_class_minutes = 0
    attended_class_minutes = 0
    
    for act in activities:
        if act['type'] == 'study':
            total_study_minutes += act['duration']
            if act['name'] in completed_activities or act['end_min'] <= current_min:
                completed_study_minutes += act['duration']
        elif act['type'] == 'class':
            total_class_minutes += act['duration']
            if act['end_min'] <= current_min:
                attended_class_minutes += act['duration']
    
    completed_tasks = len([a for a in activities if a['name'] in completed_activities])
    total_tasks = len([a for a in activities if a['type'] == 'study'])
    
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
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    full_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    stats = []
    
    for idx, day in enumerate(full_days):
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
            'day': days[idx],
            'class_hours': round(class_hours, 1),
            'study_hours': round(study_hours, 1),
        })
    
    return stats

# ============ MAIN APP ============
def main():
    st.set_page_config(page_title="Smart Schedule Manager", page_icon="🎓", layout="wide")
    
    # Initialize session state
    if 'completed_activities' not in st.session_state:
        st.session_state.completed_activities = set()
    if 'show_timer' not in st.session_state:
        st.session_state.show_timer = False
    
    # Header with compact title
    col_title, col_time = st.columns([3, 1])
    with col_title:
        st.title("🎓 Smart Schedule Manager")
        st.caption("🇧🇩 Bangladesh Time (UTC+6)")
    with col_time:
        now = get_now()
        st.metric("", now.strftime("%I:%M %p"), delta=now.strftime("%A"))
    
    # Sidebar
    with st.sidebar:
        st.header("⚡ Quick Actions")
        if st.button("🍅 Start Pomodoro", use_container_width=True):
            st.session_state.show_timer = True
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        if st.button("🗑️ Reset Progress", use_container_width=True):
            st.session_state.completed_activities = set()
            st.rerun()
        
        st.divider()
        stats = get_todays_stats(st.session_state.completed_activities)
        st.metric("📊 Progress", f"{stats['study_progress']}%")
        st.metric("✅ Tasks", f"{stats['completed_tasks']}/{stats['total_tasks']}")
    
    # Get current stats
    stats = get_todays_stats(st.session_state.completed_activities)
    
    # Main content - 3 columns
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("🟢 Current Activity")
        activity, remaining = get_current_activity()
        if remaining:
            st.info(f"**{activity}**  \n⏱️ {remaining // 60}h {remaining % 60}m remaining")
        else:
            st.info(f"**{activity}**")
        
        st.subheader("📋 Today's Schedule")
        activities = stats['activities']
        
        if activities:
            for idx, act in enumerate(activities):
                is_completed = act['name'] in st.session_state.completed_activities
                is_current = act['start_min'] <= to_minutes(get_now().hour, get_now().minute) < act['end_min']
                
                col_a, col_b, col_c = st.columns([0.3, 3, 0.8])
                
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
                    time_str = f"{format_time(act['start'][0], act['start'][1])}"
                    if is_current:
                        st.markdown(f"**▶ {act['name'][:35]}**")
                        st.caption(time_str)
                    elif is_completed:
                        st.markdown(f"~~{act['name'][:35]}~~")
                        st.caption(time_str)
                    else:
                        st.markdown(act['name'][:35])
                        st.caption(time_str)
                
                with col_c:
                    if is_current:
                        st.caption("🟢")
                    elif is_completed:
                        st.caption("✅")
        else:
            st.info("🎉 Weekend! Time to relax!")
    
    with col2:
        st.subheader("📊 Progress")
        
        # Study time
        total_hours = stats['total_study_minutes'] // 60
        total_mins = stats['total_study_minutes'] % 60
        completed_hours = stats['completed_study_minutes'] // 60
        completed_mins = stats['completed_study_minutes'] % 60
        
        st.metric("📖 Study Time", f"{completed_hours}h {completed_mins}m / {total_hours}h {total_mins}m")
        st.progress(stats['study_progress'] / 100)
        
        st.divider()
        
        # Study breakdown pie chart (smaller)
        completed = stats['completed_study_minutes']
        remaining = stats['total_study_minutes'] - completed
        
        if completed > 0 or remaining > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['✅ Done', '⏳ Left'],
                values=[completed, remaining],
                hole=0.5,
                marker=dict(colors=['#4ECDC4', '#FF6B6B']),
                textinfo='percent',
                showlegend=False
            )])
            fig.update_layout(height=180, margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Class attendance
        class_hours = stats['attended_class_minutes'] // 60
        class_mins = stats['attended_class_minutes'] % 60
        total_class_hours = stats['total_class_minutes'] // 60
        total_class_mins = stats['total_class_minutes'] % 60
        
        st.metric("📚 Classes", f"{class_hours}h {class_mins}m / {total_class_hours}h {total_class_mins}m")
        st.progress(stats['class_progress'] / 100)
    
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
                    st.warning(f"⏰ {hours}h {mins}m - Ahead")
                st.caption(f"_{gap['between'][:30]}...")
            if len(gaps) > 3:
                st.caption(f"... +{len(gaps)-3} more")
        else:
            st.info("No significant gaps!")
        
        st.divider()
        
        # Weekly overview (compact bar chart)
        st.subheader("📅 Weekly")
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
            textfont=dict(size=9)
        ))
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['class_hours'],
            name='Class',
            marker_color='#FF6B6B',
            text=df_weekly['class_hours'],
            textposition='auto',
            textfont=dict(size=9)
        ))
        fig.update_layout(
            barmode='group',
            height=200,
            margin=dict(t=10, l=0, r=0, b=0),
            legend=dict(orientation='h', yanchor='bottom', y=1, xanchor='right', x=1, font=dict(size=9)),
            font=dict(size=9)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Bottom section - Course Notes (compact)
    st.divider()
    
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
                note = COURSE_NOTES.get(course, "No notes")
                st.caption(f"**{course}**  \n{note}")
    
    # Today's timeline (collapsible to save space)
    with st.expander("📅 View Today's Timeline", expanded=False):
        if activities:
            timeline_data = []
            for act in activities:
                is_completed = act['name'] in st.session_state.completed_activities
                status = "✅ Done" if is_completed else "⏳ Pending"
                if act['start_min'] <= to_minutes(get_now().hour, get_now().minute) < act['end_min']:
                    status = "🟢 Now"
                
                timeline_data.append({
                    'Time': f"{format_time(act['start'][0], act['start'][1])}",
                    'Activity': act['name'][:40],
                    'Status': status,
                })
            
            df_timeline = pd.DataFrame(timeline_data)
            st.dataframe(df_timeline, use_container_width=True, hide_index=True)
    
    # Pomodoro Timer
    if st.session_state.get('show_timer', False):
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
                    placeholder.markdown("### 🎉 Great work!")
                    st.balloons()
                st.session_state.show_timer = False
                st.rerun()

if __name__ == "__main__":
    main()

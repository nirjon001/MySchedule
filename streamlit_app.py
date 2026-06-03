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

def get_gaps_and_utilization(completed_activities, wasted_activities):
    """Find gaps between activities and mark if utilized or wasted"""
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
            
            # Check if gap was utilized or wasted
            utilized = False
            wasted = False
            utilized_note = ""
            
            # Look for study blocks that fall within this gap
            for act in activities:
                if act['type'] == 'study':
                    if current_end <= act['start_min'] <= next_start:
                        # Check if this study block was completed or wasted
                        if act['name'] in completed_activities:
                            utilized = True
                            utilized_note = "✓ Used for study"
                        elif act['name'] in wasted_activities:
                            wasted = True
                            utilized_note = "✗ Marked as wasted"
                        elif act['end_min'] <= current_min:
                            wasted = True
                            utilized_note = "✗ Auto-wasted (time passed)"
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
                'wasted': wasted,
                'utilized_note': utilized_note,
                'between': f"{activities[i]['name'].split(' ', 1)[1]} → {activities[i+1]['name'].split(' ', 1)[1]}"
            })
    
    return gaps

def get_activity_status(activity, completed_activities, wasted_activities):
    """Determine the status of an activity"""
    now = get_now()
    current_min = to_minutes(now.hour, now.minute)
    start_min = activity['start_min']
    end_min = activity['end_min']
    
    # Check if marked as completed
    if activity['name'] in completed_activities:
        return "✅ Completed"
    
    # Check if marked as wasted
    if activity['name'] in wasted_activities:
        return "❌ Wasted"
    
    # Check if currently in progress
    if start_min <= current_min < end_min:
        return "🟢 In Progress"
    
    # Check if time has passed (automatically wasted for study tasks)
    if end_min <= current_min:
        if activity['type'] == 'study':
            return "❌ Wasted (Auto)"
        else:
            return "⏳ Passed"
    
    # Default pending
    return "⏳ Pending"

def get_todays_stats(completed_activities, wasted_activities):
    """Get today's statistics based on ACTUAL completed/wasted activities"""
    activities = get_all_activities()
    now = get_now()
    current_min = to_minutes(now.hour, now.minute)
    
    # Calculate completed and wasted study time
    total_study_minutes = 0
    completed_study_minutes = 0
    wasted_study_minutes = 0
    total_class_minutes = 0
    attended_class_minutes = 0
    
    for act in activities:
        if act['type'] == 'study':
            total_study_minutes += act['duration']
            # Check if marked as completed
            if act['name'] in completed_activities:
                completed_study_minutes += act['duration']
            # Check if marked as wasted
            elif act['name'] in wasted_activities:
                wasted_study_minutes += act['duration']
            # If time has passed and not marked, it's automatically wasted
            elif act['end_min'] <= current_min:
                wasted_study_minutes += act['duration']
        elif act['type'] == 'class':
            total_class_minutes += act['duration']
            if act['end_min'] <= current_min:
                attended_class_minutes += act['duration']
    
    # Count tasks
    completed_tasks = len([a for a in activities if a['name'] in completed_activities])
    wasted_tasks = len([a for a in activities if a['name'] in wasted_activities])
    
    # Auto-wasted tasks (time passed but not marked)
    auto_wasted_tasks = len([a for a in activities 
                            if a['type'] == 'study' 
                            and a['name'] not in completed_activities 
                            and a['name'] not in wasted_activities
                            and a['end_min'] <= current_min])
    
    total_tasks = len([a for a in activities if a['type'] == 'study'])
    
    # Calculate progress percentages
    study_progress = int((completed_study_minutes / total_study_minutes) * 100) if total_study_minutes > 0 else 0
    wasted_percentage = int((wasted_study_minutes / total_study_minutes) * 100) if total_study_minutes > 0 else 0
    class_progress = int((attended_class_minutes / total_class_minutes) * 100) if total_class_minutes > 0 else 0
    
    return {
        'total_study_minutes': total_study_minutes,
        'completed_study_minutes': completed_study_minutes,
        'wasted_study_minutes': wasted_study_minutes,
        'study_progress': study_progress,
        'wasted_percentage': wasted_percentage,
        'total_class_minutes': total_class_minutes,
        'attended_class_minutes': attended_class_minutes,
        'class_progress': class_progress,
        'completed_tasks': completed_tasks,
        'wasted_tasks': wasted_tasks + auto_wasted_tasks,
        'total_tasks': total_tasks,
        'activities': activities
    }

def get_weekly_stats(weekly_completed, weekly_wasted):
    """Get weekly statistics based on actual completed/wasted time"""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    stats = []
    
    for day in days:
        # Get actual completed study time from session state
        completed_mins = weekly_completed.get(day, 0)
        wasted_mins = weekly_wasted.get(day, 0)
        
        # Calculate planned hours
        class_hours = 0
        planned_study_hours = 0
        
        for cls in CLASSES:
            if cls[0] == day:
                _, sh, sm, eh, em, _ = cls
                class_hours += (to_minutes(eh, em) - to_minutes(sh, sm)) / 60
        
        if day not in ["Friday", "Saturday"]:
            for sh, sm, eh, em, _, act_type in DAILY_ROUTINE:
                if act_type == "study":
                    planned_study_hours += (to_minutes(eh, em) - to_minutes(sh, sm)) / 60
        
        stats.append({
            'day': day,
            'class_hours': round(class_hours, 1),
            'planned_study': round(planned_study_hours, 1),
            'completed_study': round(completed_mins / 60, 1),
            'wasted_study': round(wasted_mins / 60, 1),
            'total_hours': round(class_hours + planned_study_hours, 1)
        })
    
    return stats

def create_completed_pie_chart(stats):
    """Create pie chart showing completed vs wasted vs remaining"""
    completed = stats['completed_study_minutes']
    wasted = stats['wasted_study_minutes']
    remaining = stats['total_study_minutes'] - completed - wasted
    
    if completed == 0 and wasted == 0 and remaining == 0:
        return None
    
    labels = []
    values = []
    colors = []
    
    if completed > 0:
        labels.append('✅ Completed Study')
        values.append(completed)
        colors.append('#4ECDC4')
    
    if wasted > 0:
        labels.append('❌ Wasted Time')
        values.append(wasted)
        colors.append('#FF6B6B')
    
    if remaining > 0:
        labels.append('⏳ Remaining Study')
        values.append(remaining)
        colors.append('#FFE66D')
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='auto'
    )])
    fig.update_layout(height=400, margin=dict(t=0, l=0, r=0, b=0))
    return fig

# ============ MAIN APP ============
def main():
    st.set_page_config(page_title="Smart Schedule Manager", page_icon="🎓", layout="wide")
    
    # Apply smaller font CSS
    st.markdown("""
        <style>
        .stApp {
            font-size: 12px;
        }
        .stMarkdown {
            font-size: 12px;
        }
        .stMetric {
            font-size: 12px;
        }
        .stDataFrame {
            font-size: 11px;
        }
        div[data-testid="stMetricValue"] {
            font-size: 18px;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 11px;
        }
        .stButton button {
            font-size: 12px;
        }
        .stCheckbox label {
            font-size: 12px;
        }
        .stAlert {
            font-size: 12px;
        }
        .stSelectbox label {
            font-size: 12px;
        }
        .stCaption {
            font-size: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'completed_activities' not in st.session_state:
        st.session_state.completed_activities = set()
    if 'wasted_activities' not in st.session_state:
        st.session_state.wasted_activities = set()
    if 'show_timer' not in st.session_state:
        st.session_state.show_timer = False
    if 'weekly_completed' not in st.session_state:
        st.session_state.weekly_completed = {}
    if 'weekly_wasted' not in st.session_state:
        st.session_state.weekly_wasted = {}
    
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
            st.session_state.wasted_activities = set()
            st.rerun()
    
    # Get current stats
    stats = get_todays_stats(st.session_state.completed_activities, st.session_state.wasted_activities)
    
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
                col_a, col_b, col_c, col_d = st.columns([0.3, 3, 0.8, 0.8])
                status = get_activity_status(act, st.session_state.completed_activities, st.session_state.wasted_activities)
                
                with col_a:
                    st.write("")
                
                with col_b:
                    if status == "🟢 In Progress":
                        st.markdown(f"**▶ {act['name']}**")
                        st.caption(f"_{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}_")
                    elif status == "✅ Completed":
                        st.markdown(f"✅ **{act['name']}**")
                        st.caption(f"_{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}_")
                    elif "❌" in status:
                        st.markdown(f"❌ **{act['name']}**")
                        st.caption(f"_{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}_")
                    else:
                        st.markdown(act['name'])
                        st.caption(f"{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}")
                
                with col_c:
                    if act['type'] == 'study' and status == "⏳ Pending":
                        if st.button("✓ Complete", key=f"complete_{idx}"):
                            st.session_state.completed_activities.add(act['name'])
                            if act['name'] in st.session_state.wasted_activities:
                                st.session_state.wasted_activities.remove(act['name'])
                            st.rerun()
                    elif act['type'] == 'study' and "Wasted" not in status and status != "✅ Completed" and status != "🟢 In Progress":
                        if st.button("✗ Waste", key=f"waste_{idx}"):
                            st.session_state.wasted_activities.add(act['name'])
                            st.rerun()
                
                with col_d:
                    if status == "🟢 In Progress":
                        st.caption("▶ NOW")
                    elif status == "✅ Completed":
                        st.caption("✓ DONE")
                    elif "❌" in status:
                        st.caption("✗ WASTED")
        else:
            st.info("🎉 Weekend! Time to relax!")
    
    with col2:
        st.subheader("📊 Today's Study Progress")
        
        # Show total study time
        total_hours = stats['total_study_minutes'] // 60
        total_mins = stats['total_study_minutes'] % 60
        completed_hours = stats['completed_study_minutes'] // 60
        completed_mins = stats['completed_study_minutes'] % 60
        wasted_hours = stats['wasted_study_minutes'] // 60
        wasted_mins = stats['wasted_study_minutes'] % 60
        
        st.metric(
            "📖 Study Time",
            f"✅ {completed_hours}h {completed_mins}m | ❌ {wasted_hours}h {wasted_mins}m",
            delta=f"{stats['study_progress']}% completed"
        )
        
        # Progress bars
        st.progress(stats['study_progress'] / 100, text=f"📚 Completed: {stats['study_progress']}%")
        if stats['wasted_percentage'] > 0:
            st.progress(stats['wasted_percentage'] / 100, text=f"⚠️ Wasted: {stats['wasted_percentage']}%")
        
        st.divider()
        
        st.subheader("✅ Task Status")
        st.metric(
            "Study Tasks",
            f"✅ {stats['completed_tasks']} / ❌ {stats['wasted_tasks']} / 📋 {stats['total_tasks']}",
            delta=f"{int(stats['completed_tasks']/stats['total_tasks']*100) if stats['total_tasks']>0 else 0}% success rate"
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
        
        gaps = get_gaps_and_utilization(st.session_state.completed_activities, st.session_state.wasted_activities)
        
        if gaps:
            for gap in gaps:
                duration_hours = gap['duration'] // 60
                duration_mins = gap['duration'] % 60
                
                if gap['utilized']:
                    st.success(f"✅ **{duration_hours}h {duration_mins}m gap**")
                    st.caption(f"_{gap['between']}_")
                    st.caption(f"✓ {gap['utilized_note']}")
                elif gap['wasted']:
                    st.error(f"❌ **{duration_hours}h {duration_mins}m gap WASTED**")
                    st.caption(f"_{gap['between']}_")
                    st.caption(f"✗ {gap['utilized_note']}")
                elif gap['is_passed']:
                    st.warning(f"⚠️ **{duration_hours}h {duration_mins}m gap UNUSED**")
                    st.caption(f"_{gap['between']}_")
                    st.caption("💡 Mark tasks as completed or wasted!")
                else:
                    st.info(f"⏰ **{duration_hours}h {duration_mins}m gap ahead**")
                    st.caption(f"_{gap['between']}_")
                    st.caption("💡 Plan to use this time for study!")
                st.divider()
        else:
            st.info("No significant gaps today! 🎉")
    
    # Analytics Section - BASED ON COMPLETED/WASTED DATA
    st.divider()
    st.subheader("📊 Your Achievements Today")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Pie chart of completed vs wasted vs remaining
        st.write("**Study Time Breakdown**")
        pie_chart = create_completed_pie_chart(stats)
        if pie_chart:
            st.plotly_chart(pie_chart, use_container_width=True)
        else:
            st.info("No study data yet. Start studying! 📚")
    
    with col_b:
        # Save today's stats to weekly
        today = get_now().strftime("%A")
        st.session_state.weekly_completed[today] = stats['completed_study_minutes']
        st.session_state.weekly_wasted[today] = stats['wasted_study_minutes']
        
        # Bar chart - Weekly comparison (planned vs completed)
        st.write("**Weekly Study Hours (Planned vs Actual)**")
        weekly_stats = get_weekly_stats(st.session_state.weekly_completed, st.session_state.weekly_wasted)
        df_weekly = pd.DataFrame(weekly_stats)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['planned_study'],
            name='Planned Study',
            marker_color='#4ECDC4'
        ))
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['completed_study'],
            name='Actually Completed',
            marker_color='#00FF00'
        ))
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['wasted_study'],
            name='Wasted Time',
            marker_color='#FF6B6B'
        ))
        fig.add_trace(go.Bar(
            x=df_weekly['day'],
            y=df_weekly['class_hours'],
            name='Class Hours',
            marker_color='#FFE66D'
        ))
        fig.update_layout(
            barmode='group',
            height=400,
            margin=dict(t=0, l=0, r=0, b=0),
            yaxis_title="Hours"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Today's timeline with proper status
    st.divider()
    st.subheader("📅 Today's Timeline")
    
    if activities:
        timeline_data = []
        for act in activities:
            status = get_activity_status(act, st.session_state.completed_activities, st.session_state.wasted_activities)
            
            timeline_data.append({
                'Time': f"{format_time(act['start'][0], act['start'][1])} - {format_time(act['end'][0], act['end'][1])}",
                'Activity': act['name'],
                'Status': status,
                'Duration': f"{act['duration'] // 60}h {act['duration'] % 60}m"
            })
        
        df_timeline = pd.DataFrame(timeline_data)
        st.dataframe(df_timeline, use_container_width=True, hide_index=True)
        
        # Add explanation of status icons
        st.caption("""
        **Status Legend:**
        - ✅ Completed: Manually marked as done
        - ❌ Wasted: Manually marked as wasted OR auto-wasted when time passed without completion
        - 🟢 In Progress: Currently happening now
        - ⏳ Pending: Not started yet
        """)
    
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

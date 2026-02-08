"""
NERO-Time UI - Clean Professional Design with Event Filtering
FIXED: Unique button keys and purple theme
"""
import math
import random
import streamlit as st
from datetime import datetime, time, timedelta
from nero_logic import NeroTimeLogic
from Firebase_Function import load_from_firebase

# Page configuration
st.set_page_config(page_title="NERO-TIME", page_icon="🕛", layout="wide")

# Custom CSS - CLEAN PROFESSIONAL DESIGN WITH PURPLE THEME
st.markdown("""
<style>
/* --------------------------------------------------
   GLOBAL THEME-AWARE COLORS
-------------------------------------------------- */

:root {
    --bg: var(--background-color);
    --bg-secondary: var(--secondary-background-color);
    --text: var(--text-color);
    --primary: var(--primary-color);
    --purple: #B24BF3;
    --purple-dark: #9333EA;
    --purple-light: #D8B4FE;
    --purple-hover: #C678FF;
}

/* --------------------------------------------------
   BASE APP
-------------------------------------------------- */

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.stApp {
    background: var(--bg);
    color: var(--text);
}

.block-container {
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}

/* --------------------------------------------------
   HEADINGS & TEXT
-------------------------------------------------- */

h1, h2, h3, h4, h5, h6 {
    color: var(--text);
    font-weight: 600;
}

p, span, label, div {
    color: var(--text);
}

/* --------------------------------------------------
   BUTTONS - PURPLE THEME
-------------------------------------------------- */

.stButton > button {
    font-size: 14px;
    padding: 8px 16px;
    border-radius: 6px;
    border: 2px solid var(--purple-light);
    background: var(--bg);
    color: var(--purple);
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: var(--purple-light);
    color: white;
    border-color: var(--purple);
    box-shadow: 0 2px 8px rgba(156, 39, 176, 0.3);
}

.stButton > button[kind="primary"] {
    background: var(--purple);
    color: white;
    border: none;
    box-shadow: 0 2px 4px rgba(156, 39, 176, 0.3);
}

.stButton > button[kind="primary"]:hover {
    background: var(--purple-dark);
    box-shadow: 0 4px 12px rgba(156, 39, 176, 0.4);
}

.stButton > button:active {
    transform: translateY(1px);
}

/* --------------------------------------------------
   TABS - PURPLE THEME
-------------------------------------------------- */

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--bg);
    padding: 4px;
    border-radius: 8px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    padding: 12px 20px;
    border-radius: 6px;
    color: var(--text);
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}

.stTabs [data-baseweb="tab"]:hover {
    background: var(--purple-light);
    color: white;
}

.stTabs [aria-selected="true"] {
    background: var(--purple);
    color: white !important;
}

/* --------------------------------------------------
   INPUTS - PURPLE ACCENTS
-------------------------------------------------- */

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTimeInput input {
    border-radius: 6px;
    border: 1px solid rgba(128,128,128,0.4);
    background: var(--bg);
    color: var(--text);
}

.stTextInput input:focus,
.stNumberInput input:focus,
.stDateInput input:focus,
.stTimeInput input:focus {
    border-color: var(--purple);
    box-shadow: 0 0 0 2px rgba(156, 39, 176, 0.25);
}

.stSlider [data-baseweb="slider"] {
    background: var(--purple-light);
}

.stSlider [role="slider"] {
    background-color: var(--purple);
}

/* --------------------------------------------------
   METRICS - PURPLE ACCENTS
-------------------------------------------------- */

[data-testid="stMetricValue"] {
    font-size: 28px;
    font-weight: 600;
    color: var(--purple);
}

[data-testid="stMetricLabel"] {
    color: var(--text);
}

/* --------------------------------------------------
   EVENTS
-------------------------------------------------- */

.event-activity,
.event-school,
.event-compulsory,
.event-break {
    padding: 12px;
    margin: 8px 0;
    border-radius: 6px;
    background: var(--bg);
    color: var(--text);
}

.event-activity { 
    border-left: 6px solid var(--purple); 
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.event-school { 
    border-left: 6px solid #FF9800; 
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.event-compulsory { 
    border-left: 6px solid #F44336; 
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.event-break { 
    border-left: 6px solid #9E9E9E; 
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.happening-now {
    background: #4CAF50;
    color: white;
    padding: 6px 12px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 13px;
}

/* --------------------------------------------------
   EXPANDERS - PURPLE THEME
-------------------------------------------------- */

.streamlit-expanderHeader {
    background: var(--bg);
    border-radius: 6px;
    padding: 10px 14px;
    border: 1px solid var(--purple-light);
    color: var(--text);
    transition: all 0.2s ease;
}

.streamlit-expanderHeader:hover {
    background: var(--purple-light);
    color: white;
    border-color: var(--purple);
}

/* --------------------------------------------------
   ALERTS
-------------------------------------------------- */

.stSuccess, .stError, .stWarning, .stInfo {
    color: var(--text);
    background: var(--bg-secondary) !important;
}

/* --------------------------------------------------
   PROGRESS BAR - PURPLE
-------------------------------------------------- */

.stProgress > div > div > div {
    background-color: var(--purple);
}
</style>

""", unsafe_allow_html=True)

# Initialize session state
NeroTimeLogic.initialize_session_state()

# Initialize event filter
if 'event_filter' not in st.session_state:
    st.session_state.event_filter = 'weekly'

# Load data from Firebase
if not st.session_state.data_loaded and st.session_state.user_id:
    with st.spinner("Loading..."):
        loaded_activities = load_from_firebase(st.session_state.user_id, 'activities')
        loaded_events = load_from_firebase(st.session_state.user_id, 'events')
        loaded_school = load_from_firebase(st.session_state.user_id, 'school_schedule')
        loaded_timetable = load_from_firebase(st.session_state.user_id, 'timetable')
        loaded_progress = load_from_firebase(st.session_state.user_id, 'activity_progress')
        loaded_sessions = load_from_firebase(st.session_state.user_id, 'session_completion')
        loaded_pending = load_from_firebase(st.session_state.user_id, 'pending_verifications')
        loaded_edits = load_from_firebase(st.session_state.user_id, 'user_edits')
        loaded_month = load_from_firebase(st.session_state.user_id, 'current_month')
        loaded_year = load_from_firebase(st.session_state.user_id, 'current_year')
        
        if loaded_activities:
            st.session_state.list_of_activities = loaded_activities
        if loaded_events:
            st.session_state.list_of_compulsory_events = loaded_events
        if loaded_school:
            st.session_state.school_schedule = loaded_school
        if loaded_timetable:
            st.session_state.timetable = loaded_timetable
        if loaded_progress:
            st.session_state.activity_progress = loaded_progress
        if loaded_sessions:
            st.session_state.session_completion = loaded_sessions
        if loaded_pending:
            st.session_state.pending_verifications = loaded_pending
        if loaded_edits:
            st.session_state.user_edits = loaded_edits
        if loaded_month:
            st.session_state.current_month = loaded_month
        if loaded_year:
            st.session_state.current_year = loaded_year
        
        st.session_state.data_loaded = True

# ==================== LOGIN SCREEN ====================
if not st.session_state.user_id:
    st.markdown("""
    <div style='text-align: center; padding: 4rem 0 2rem 0;'>
        <h1 style='font-size: 4rem; margin-bottom: 0.5rem;'>🕛</h1>
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem; color: #B24BF3;'>NERO-Time</h1>
        <p style='font-size: 1.1rem; color: #757575; margin-bottom: 3rem;'>
            Simple. Powerful. Time Management.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Welcome")
        user_input = st.text_input(
          "Email",
          placeholder="your.email@example.com",
          label_visibility="collapsed",
          key="login_email"
      )

        
        if st.button("Sign In", type="primary", use_container_width=True, key="btn_signin"):
            if user_input:
                with st.spinner("Signing in..."):
                    result = NeroTimeLogic.login_user(user_input)
                if result["success"]:
                    st.success("✓ " + result["message"])
                    st.rerun()
                else:
                    st.error("✗ " + result["message"])
            else:
                st.error("Please enter your email")
    
    st.stop()

# ==================== MAIN APP ====================
st.markdown("<h1 style='text-align: center; margin-bottom: 2rem; color: #B24BF3;'>🕛 NERO-Time</h1>", unsafe_allow_html=True)

# Stats
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

dashboard_preview = NeroTimeLogic.get_dashboard_data()
activities_preview = NeroTimeLogic.get_activities_data()

total_activities = len(activities_preview['activities'])
completed_sessions = sum(
    sum(1 for sess in act.get('sessions_data', []) if sess.get('is_completed', False))
    for act in activities_preview['activities']
)
total_sessions = sum(
    len(act.get('sessions_data', []))
    for act in activities_preview['activities']
)
total_hours_completed = sum(act['progress']['completed'] for act in activities_preview['activities'])

with col_stat1:
    st.metric("Activities", total_activities)
with col_stat2:
    st.metric("Sessions", f"{completed_sessions}/{total_sessions}")
with col_stat3:
    st.metric("Hours", f"{total_hours_completed:.1f}h")
with col_stat4:
    completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    st.metric("Complete", f"{completion_rate:.0f}%")

st.caption(f"👤 {st.session_state.user_id}")
st.divider()

# Navigation
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Activities", "Events", "School", "Settings"])

# ==================== DASHBOARD TAB ====================
with tab1:
    dashboard_data = NeroTimeLogic.get_dashboard_data()
    
    # Month navigation
    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])
    
    with col2:
        if st.button("◀ Prev", use_container_width=True, key="btn_prev_month"):
            NeroTimeLogic.navigate_month("prev")
            st.rerun()
    
    with col3:
        st.markdown(f"<div style='text-align: center; padding: 8px; font-weight: 600; font-size: 16px;'>{dashboard_data['month_name']} {dashboard_data['year']}</div>", unsafe_allow_html=True)
    
    with col4:
        if st.button("Next ▶", use_container_width=True, key="btn_next_month"):
            NeroTimeLogic.navigate_month("next")
            st.rerun()
    
    with col5:
        if st.button("Today", use_container_width=True, key="btn_today_month"):
            NeroTimeLogic.navigate_month("today")
            st.rerun()
    
    st.divider()
    
    # Generate timetable - BIG BUTTON
    col_gen1, col_gen2, col_gen3 = st.columns([1, 1, 2])
    with col_gen1:
        min_session = st.number_input("Min Session (min)", 15, 180, 30, 15, key="gen_min_session")
    with col_gen2:
        max_session = st.number_input("Max Session (min)", 30, 240, 120, 15, key="gen_max_session")
    
    if st.button("🚀 GENERATE TIMETABLE", type="primary", use_container_width=True, key="btn_generate_timetable"):
        if st.session_state.list_of_activities or st.session_state.list_of_compulsory_events or st.session_state.school_schedule:
            with st.spinner("Generating your perfect schedule..."):
                result = NeroTimeLogic.generate_timetable(min_session, max_session)
            if result["success"]:
                st.success("✓ Timetable generated successfully!")
                st.rerun()
            else:
                st.error(result["message"])
        else:
            st.warning("⚠️ Please add activities, events, or school schedule first")
    
    st.divider()
    
    # Event filter
    st.markdown("### 📅 Events")
    
    # Filter buttons
    col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 3])
    
    with col_f1:
        if st.button("📅 Weekly", use_container_width=True, 
                    type="primary" if st.session_state.event_filter == 'weekly' else "secondary",
                    key="filter_weekly"):
            st.session_state.event_filter = 'weekly'
            st.rerun()
    
    with col_f2:
        if st.button("📆 Monthly", use_container_width=True,
                    type="primary" if st.session_state.event_filter == 'monthly' else "secondary",
                    key="filter_monthly"):
            st.session_state.event_filter = 'monthly'
            st.rerun()
    
    with col_f3:
        if st.button("🗓️ Yearly", use_container_width=True,
                    type="primary" if st.session_state.event_filter == 'yearly' else "secondary",
                    key="filter_yearly"):
            st.session_state.event_filter = 'yearly'
            st.rerun()
    
    st.divider()
    
    # Filter events based on selection
    def filter_events_by_period(month_days, filter_type):
        """Filter days based on weekly/monthly/yearly view"""
        today = datetime.now().date()
        
        if filter_type == 'weekly':
            # Show current week
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return [d for d in month_days if start_of_week <= d['date'].date() <= end_of_week]
        
        elif filter_type == 'monthly':
            # Show current month
            return [d for d in month_days if d['date'].month == today.month and d['date'].year == today.year]
        
        else:  # yearly
            # Show all events in current year
            return [d for d in month_days if d['date'].year == today.year]
    
    filtered_days = filter_events_by_period(dashboard_data['month_days'], st.session_state.event_filter)
    
    if dashboard_data['timetable'] and filtered_days:
        for day_info in filtered_days:
            day_display = day_info['display']
            
            if day_display in dashboard_data['timetable']:
                is_current_day = (day_display == dashboard_data['current_day'])
                events = dashboard_data['timetable'][day_display]
                
                if not events:
                    continue
                
                with st.expander(f"{'🟢 ' if is_current_day else ''}📅 {day_display}", expanded=is_current_day):
                    for idx, event in enumerate(events):
                        # Check if current
                        is_current_slot = False
                        if is_current_day and dashboard_data['current_time']:
                            from Timetable_Generation import time_str_to_minutes
                            event_start = time_str_to_minutes(event['start'])
                            event_end = time_str_to_minutes(event['end'])
                            current_minutes = time_str_to_minutes(dashboard_data['current_time'])
                            is_current_slot = event_start <= current_minutes < event_end
                        
                        if event["type"] == "ACTIVITY":
                            activity_name = event['name'].split(' (Session')[0]
                            progress = event['progress']
                            is_completed = event.get('is_completed', False)
                            is_user_edited = event.get('is_user_edited', False)
                            
                            if is_current_slot:
                                st.markdown('<div class="happening-now">● NOW</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-activity">', unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([0.85, 0.15])
                            with col1:
                                badge = '<span class="user-edited-badge">EDITED</span>' if is_user_edited else ''
                                status_icon = "✅" if is_completed else "⚫"
                                st.markdown(f"{badge}**{status_icon} {event['start']}-{event['end']}** {event['name']}", unsafe_allow_html=True)
                                st.progress(progress['percentage'] / 100)
                                st.caption(f"{progress['completed']:.1f}h / {progress['total']}h")
                            
                            with col2:
                                if is_completed:
                                    st.markdown("✓")
                                elif event['can_verify']:
                                    # FIXED: Unique key for each verify button
                                    if st.button("✓", key=f"verify_{day_display}_{idx}_{event.get('session_id', idx)}", use_container_width=True):
                                        result = NeroTimeLogic.verify_session(day_display, idx)
                                        if result["success"]:
                                            st.success("Completed!")
                                            st.rerun()
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        elif event["type"] == "SCHOOL":
                            if is_current_slot:
                                st.markdown('<div class="happening-now">● NOW</div>', unsafe_allow_html=True)
                            st.markdown('<div class="event-school">', unsafe_allow_html=True)
                            st.markdown(f"**🏫 {event['start']}-{event['end']}** {event['name']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        elif event["type"] == "COMPULSORY":
                            if is_current_slot:
                                st.markdown('<div class="happening-now">● NOW</div>', unsafe_allow_html=True)
                            st.markdown('<div class="event-compulsory">', unsafe_allow_html=True)
                            st.markdown(f"**🔴 {event['start']}-{event['end']}** {event['name']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        else:  # BREAK
                            st.markdown('<div class="event-break">', unsafe_allow_html=True)
                            st.markdown(f"*⚪ {event['start']}-{event['end']} Break*")
                            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No events for this period")

# ==================== ACTIVITIES TAB ====================
with tab2:
    st.header("Activities")
    
    with st.expander("➕ Add Activity", expanded=False):
        name = st.text_input("Name", key="activity_name")
        col1, col2 = st.columns(2)
        with col1:
            priority = st.slider("Priority", 1, 5, 3, key="activity_priority")
            deadline = st.date_input("Deadline", min_value=datetime.now().date(), key="activity_deadline")
        with col2:
            hours = st.number_input("Hours", 1, 100, 1, key="activity_hours")
        
        col3, col4 = st.columns(2)
        with col3:
            min_s = st.number_input("Min (min)", 15, 180, 30, 15, key="min_s")
        with col4:
            max_s = st.number_input("Max (min)", 30, 240, 120, 15, key="max_s")
            if max_s < min_s:
                max_s = min_s
        
        from Timetable_Generation import WEEKDAY_NAMES
        days = st.multiselect("Days", WEEKDAY_NAMES, WEEKDAY_NAMES, key="activity_days")
        
        if st.button("Add", type="primary", use_container_width=True, key="btn_add_activity"):
            if name:
                result = NeroTimeLogic.add_activity(name, priority, deadline.isoformat(), hours, min_s, max_s, days)
                if result["success"]:
                    st.success("✓ Added")
                    st.rerun()
                else:
                    st.error(result["message"])
    
    st.divider()
    
    activities_data = NeroTimeLogic.get_activities_data()
    
    if activities_data['activities']:
        for idx, act in enumerate(activities_data['activities']):
            with st.expander(f"{idx+1}. {act['activity']} ({act['progress']['completed']:.1f}h/{act['timing']}h)"):
                st.progress(act['progress']['percentage'] / 100)
                st.caption(f"Priority: {act['priority']} • Deadline: {act['deadline']} days")
                
                # Show sessions
                st.markdown("#### 📋 Sessions")
                sessions_data = act.get('sessions_data', [])
                
                if sessions_data:
                    for sess_idx, session in enumerate(sessions_data):
                        session_id = session.get('session_id', f"session_{sess_idx}")
                        is_completed = session.get('is_completed', False)
                        duration_hours = session.get('duration_hours', 0)
                        duration_minutes = session.get('duration_minutes', 0)
                        
                        # Create a container for each session
                        with st.container():
                            col_s1, col_s2, col_s3 = st.columns([2, 2, 1])
                            
                            with col_s1:
                                status = "✅ Completed" if is_completed else "⚫ Pending"
                                st.markdown(f"**Session {sess_idx + 1}** - {status}")
                                st.caption(f"Duration: {duration_hours:.1f}h ({duration_minutes} min)")
                            
                            with col_s2:
                                scheduled_day = session.get('scheduled_day')
                                scheduled_time = session.get('scheduled_time')
                                if scheduled_day and scheduled_time:
                                    st.caption(f"📅 {scheduled_day} at {scheduled_time}")
                                else:
                                    st.caption("📅 Not scheduled yet")
                            
                            with col_s3:
                                if not is_completed:
                                    edit_key = f"edit_session_{act['activity']}_{session_id}"
                                    if st.button("✏️ Edit", key=edit_key, use_container_width=True):
                                        st.session_state[f"editing_{edit_key}"] = True
                                        st.rerun()
                            
                            # Show edit form if editing
                            edit_state_key = f"editing_edit_session_{act['activity']}_{session_id}"
                            if st.session_state.get(edit_state_key, False):
                                with st.form(key=f"form_{act['activity']}_{session_id}"):
                                    st.markdown("**Edit Session**")
                                    
                                    from Timetable_Generation import WEEKDAY_NAMES
                                    col_e1, col_e2, col_e3 = st.columns(3)
                                    
                                    with col_e1:
                                        new_day = st.selectbox(
                                            "Day", 
                                            WEEKDAY_NAMES, 
                                            index=WEEKDAY_NAMES.index(scheduled_day) if scheduled_day in WEEKDAY_NAMES else 0,
                                            key=f"day_{session_id}"
                                        )
                                    
                                    with col_e2:
                                        # Parse current time or use default
                                        default_time = datetime.strptime(scheduled_time, "%H:%M").time() if scheduled_time else datetime.now().time()
                                        new_time = st.time_input(
                                            "Start Time",
                                            value=default_time,
                                            key=f"time_{session_id}"
                                        )
                                    
                                    with col_e3:
                                        new_duration = st.number_input(
                                            "Duration (min)",
                                            min_value=15,
                                            max_value=240,
                                            value=duration_minutes,
                                            step=15,
                                            key=f"dur_{session_id}"
                                        )
                                    
                                    col_btn1, col_btn2 = st.columns(2)
                                    with col_btn1:
                                        submitted = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
                                    with col_btn2:
                                        cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
                                    
                                    if submitted:
                                        # Check if it's past the deadline
                                        if act['deadline'] < 0:
                                            st.error("❌ Cannot edit - activity deadline has passed!")
                                        else:
                                            result = NeroTimeLogic.edit_session(
                                                act['activity'],
                                                session_id,
                                                new_day=new_day,
                                                new_start_time=new_time.strftime("%H:%M"),
                                                new_duration=new_duration
                                            )
                                            if result["success"]:
                                                st.session_state[edit_state_key] = False
                                                st.success("✓ Session updated!")
                                                st.rerun()
                                            else:
                                                st.error(result["message"])
                                    
                                    if cancelled:
                                        st.session_state[edit_state_key] = False
                                        st.rerun()
                            
                            st.divider()
                else:
                    st.info("No sessions generated yet")
                
                st.markdown("---")
                
                # Action buttons
                col1, col2 = st.columns(2)
                # FIXED: Unique keys for delete and reset buttons
                if col1.button("Delete", key=f"del_activity_{idx}_{act['activity']}"):
                    result = NeroTimeLogic.delete_activity(idx)
                    if result["success"]:
                        st.rerun()
                if col2.button("Reset", key=f"reset_activity_{idx}_{act['activity']}"):
                    result = NeroTimeLogic.reset_activity_progress(act['activity'])
                    if result["success"]:
                        st.rerun()
    else:
        st.info("No activities")

# ==================== EVENTS TAB ====================
with tab3:
    st.header("Events")
    
    with st.expander("➕ Add Event", expanded=False):
        event_name = st.text_input("Name", key="event_name")
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Date", min_value=datetime.now().date(), key="event_date")
        with col2:
            from Timetable_Generation import WEEKDAY_NAMES
            st.text_input("Day", value=WEEKDAY_NAMES[event_date.weekday()], disabled=True, key="event_day_display")
        
        col3, col4 = st.columns(2)
        with col3:
            start_t = st.time_input("Start", key="event_start_time")
        with col4:
            end_t = st.time_input("End", key="event_end_time")
        
        if st.button("Add", type="primary", use_container_width=True, key="btn_add_event"):
            if event_name:
                result = NeroTimeLogic.add_event(event_name, event_date.isoformat(), start_t.strftime("%H:%M"), end_t.strftime("%H:%M"))
                if result["success"]:
                    st.success("✓ Added")
                    st.rerun()
                else:
                    st.error(result["message"])
    
    st.divider()
    
    events_data = NeroTimeLogic.get_events_data()
    
    if events_data['events']:
        for idx, evt in enumerate(events_data['events']):
            with st.expander(f"{idx+1}. {evt['event']} - {evt['day']}"):
                st.write(f"{evt['start_time']} - {evt['end_time']}")
                # FIXED: Unique key for delete event button
                if st.button("Delete", key=f"del_event_{idx}_{evt['event']}"):
                    result = NeroTimeLogic.delete_event(idx)
                    if result["success"]:
                        st.rerun()
    else:
        st.info("No events")

# ==================== SCHOOL TAB ====================
with tab4:
    st.header("School Schedule")
    
    with st.expander("➕ Add Class", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            from Timetable_Generation import WEEKDAY_NAMES
            day = st.selectbox("Day", WEEKDAY_NAMES, key="school_day")
            subject = st.text_input("Subject (optional)", key="school_subject", placeholder="Class")
        with col2:
            start = st.time_input("Start", key="school_start")
            end = st.time_input("End", key="school_end")
        
        if st.button("Add", type="primary", use_container_width=True, key="btn_add_school"):
            # Use "Class" as default if subject is empty
            subject_name = subject.strip() if subject.strip() else "Class"
            result = NeroTimeLogic.add_school_schedule(day, start.strftime("%H:%M"), end.strftime("%H:%M"), subject_name)
            if result["success"]:
                st.success("✓ Added")
                st.rerun()
            else:
                st.error(result["message"])
    
    st.divider()
    
    school_data = NeroTimeLogic.get_school_schedule()
    
    if school_data['schedule']:
        from Timetable_Generation import WEEKDAY_NAMES
        for day in WEEKDAY_NAMES:
            if day in school_data['schedule']:
                with st.expander(f"{day} ({len(school_data['schedule'][day])} classes)"):
                    for idx, cls in enumerate(school_data['schedule'][day]):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"**{cls['subject']}**")
                            st.caption(f"{cls['start_time']} - {cls['end_time']}")
                        with col2:
                            # FIXED: Unique key for delete school button
                            if st.button("×", key=f"del_school_{day}_{idx}_{cls['subject']}"):
                                result = NeroTimeLogic.delete_school_schedule(day, idx)
                                if result["success"]:
                                    st.rerun()
    else:
        st.info("No classes")

# ==================== SETTINGS TAB ====================
with tab5:
    st.header("Settings")
    
    st.write(f"**User:** {st.session_state.user_id}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Logout", type="primary", use_container_width=True, key="btn_logout"):
            st.session_state.user_id = None
            st.session_state.data_loaded = False
            st.rerun()
    
    with col2:
        if st.button("Clear Data", use_container_width=True, key="btn_clear_data"):
            result = NeroTimeLogic.clear_all_data()
            if result["success"]:
                st.warning("Data cleared")
                st.rerun()

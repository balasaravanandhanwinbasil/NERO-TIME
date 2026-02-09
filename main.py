"""
NERO-Time UI
"""
import pytz
import math
import random
import streamlit as st
from datetime import datetime, time, timedelta
from nero_logic import NeroTimeLogic
from Firebase_Function import load_from_firebase

# Page configuration
st.set_page_config(page_title="NERO-TIME", page_icon="🕛", layout="wide")

# Custom CSS - TIMETABLE STYLE DESIGN
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
    --purple: #E91E63;
    --purple-dark: #C2185B;
    --purple-light: #F8BBD0;
    --purple-hover: #F48FB1;
    --activity-color: #E91E63;
    --school-color: #FF9800;
    --compulsory-color: #F44336;
    --break-color: #9E9E9E;
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
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
   LIVE CLOCK
-------------------------------------------------- */

.live-clock {
    text-align: center;
    padding: 1.5rem;
    background: linear-gradient(135deg, var(--purple-light) 0%, var(--purple) 100%);
    border-radius: 12px;
    margin: 1rem 0 2rem 0;
    box-shadow: 0 4px 12px rgba(233, 30, 99, 0.2);
}

.clock-time {
    font-size: 3rem;
    font-weight: 700;
    color: white;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.clock-date {
    font-size: 1.2rem;
    color: rgba(255,255,255,0.9);
    margin-top: 0.5rem;
}

/* --------------------------------------------------
   BUTTONS - PINKISH PURPLE THEME
-------------------------------------------------- */

.stButton > button {
    font-size: 14px;
    padding: 10px 20px;
    border-radius: 8px;
    border: 2px solid var(--purple-light);
    background: var(--bg);
    color: var(--purple);
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: var(--purple-light);
    color: white;
    border-color: var(--purple);
    box-shadow: 0 4px 12px rgba(233, 30, 99, 0.3);
    transform: translateY(-2px);
}

.stButton > button[kind="primary"] {
    background: var(--purple);
    color: white;
    border: none;
    box-shadow: 0 4px 8px rgba(233, 30, 99, 0.3);
}

.stButton > button[kind="primary"]:hover {
    background: var(--purple-dark);
    box-shadow: 0 6px 16px rgba(233, 30, 99, 0.4);
    transform: translateY(-2px);
}

.stButton > button:active {
    transform: translateY(0px);
}

/* --------------------------------------------------
   TABS - PINKISH PURPLE THEME
-------------------------------------------------- */

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: var(--bg);
    padding: 8px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    padding: 12px 24px;
    border-radius: 8px;
    color: var(--text);
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 500;
}

.stTabs [data-baseweb="tab"]:hover {
    background: var(--purple-light);
    color: white;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--purple) 0%, var(--purple-dark) 100%);
    color: white !important;
    box-shadow: 0 2px 8px rgba(233, 30, 99, 0.3);
}

/* --------------------------------------------------
   INPUTS - PURPLE ACCENTS
-------------------------------------------------- */

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTimeInput input {
    border-radius: 8px;
    border: 2px solid rgba(128,128,128,0.3);
    background: var(--bg);
    color: var(--text);
    transition: all 0.3s ease;
}

.stTextInput input:focus,
.stNumberInput input:focus,
.stDateInput input:focus,
.stTimeInput input:focus {
    border-color: var(--purple);
    box-shadow: 0 0 0 3px rgba(233, 30, 99, 0.15);
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
    font-size: 32px;
    font-weight: 700;
    color: var(--purple);
}

[data-testid="stMetricLabel"] {
    color: var(--text);
    font-weight: 600;
}

/* --------------------------------------------------
   TIMETABLE ROW - REORGANIZED LAYOUT
-------------------------------------------------- */

.timetable-row {
    display: flex;
    align-items: stretch;
    margin: 12px 0;
    min-height: 70px;
}

.event-content {
    flex: 1;
    padding: 16px 20px;
    border-radius: 10px;
    background: var(--bg);
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-left: 5px solid;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 20px;
}

.event-content:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    transform: translateX(4px);
}

.event-content.activity {
    border-left-color: var(--activity-color);
    background: linear-gradient(to right, rgba(233, 30, 99, 0.02), var(--bg));
}

.event-content.school {
    border-left-color: var(--school-color);
    background: linear-gradient(to right, rgba(255, 152, 0, 0.02), var(--bg));
}

.event-content.compulsory {
    border-left-color: var(--compulsory-color);
    background: linear-gradient(to right, rgba(244, 67, 54, 0.02), var(--bg));
}

.event-content.break {
    border-left-color: var(--break-color);
    opacity: 0.7;
}

.event-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.event-title {
    font-weight: 600;
    font-size: 1.05rem;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    line-height: 1.4;
}

.event-details {
    font-size: 0.88rem;
    opacity: 0.75;
    line-height: 1.5;
}

.event-right-section {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
    min-width: 130px;
}

.event-time {
    font-weight: 600;
    font-size: 1rem;
    color: var(--text);
    opacity: 0.85;
    white-space: nowrap;
    text-align: right;
    font-family: 'Courier New', monospace;
}

.event-actions {
    display: flex;
    gap: 6px;
    align-items: center;
}

.event-actions button {
    min-width: 36px !important;
    height: 36px !important;
    padding: 0 !important;
    font-size: 18px !important;
}

.happening-now {
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.7rem;
    display: inline-block;
    box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

.user-edited-badge {
    background: var(--purple);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* --------------------------------------------------
   EXPANDERS - PURPLE THEME
-------------------------------------------------- */

.streamlit-expanderHeader {
    background: var(--bg);
    border-radius: 8px;
    padding: 12px 16px;
    border: 2px solid var(--purple-light);
    color: var(--text);
    transition: all 0.3s ease;
    font-weight: 600;
}

.streamlit-expanderHeader:hover {
    background: var(--purple-light);
    color: white;
    border-color: var(--purple);
}

/* --------------------------------------------------
   PROGRESS BAR - PURPLE
-------------------------------------------------- */

.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--purple) 0%, var(--purple-dark) 100%);
}

/* Remove weird shape above expanders */
details summary::marker,
details summary::-webkit-details-marker {
    display: none;
}

</style>

""", unsafe_allow_html=True)

# Initialize session state
NeroTimeLogic.initialize_session_state()

# Initialize event filter
if 'event_filter' not in st.session_state:
    st.session_state.event_filter = 'weekly'

# Check for expired sessions on load
if st.session_state.user_id and st.session_state.data_loaded:
    NeroTimeLogic.check_expired_sessions()

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
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem; color: #E91E63;'>NERO-Time</h1>
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
st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; color: #E91E63;'>🕛 NERO-Time</h1>", unsafe_allow_html=True)

# Live Clock
sg_tz = pytz.timezone('Asia/Singapore')
now = datetime.now(sg_tz)
st.markdown(f"""
<div class='live-clock'>
    <div class='clock-time'>{now.strftime('%H:%M:%S')}</div>
    <div class='clock-date'>{now.strftime('%A, %B %d, %Y')}</div>
</div>
""", unsafe_allow_html=True)

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

# Ensure integers for session counts
completed_sessions = int(completed_sessions)
total_sessions = int(total_sessions)

with col_stat1:
    st.metric("Activities", total_activities)
with col_stat2:
    st.metric("Sessions", f"{completed_sessions}/{total_sessions}")
with col_stat3:
    st.metric("Hours", f"{total_hours_completed:.1f}h")
with col_stat4:
    completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    st.metric("Complete", f"{int(completion_rate)}%")

st.caption(f"👤 {st.session_state.user_id}")
st.divider()

# Navigation
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Dashboard", "Activities", "Events", "School", "Settings", "Achievements"])

# ==================== DASHBOARD TAB ====================
with tab1:
    dashboard_data = NeroTimeLogic.get_dashboard_data()
    
    # Month navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col2:
        if st.button("◀ Prev", use_container_width=True, key="btn_prev_month"):
            NeroTimeLogic.navigate_month("prev")
            st.rerun()
    
    with col3:
        st.markdown(f"<div style='text-align: center; padding: 8px; font-weight: 600; font-size: 18px;'>{dashboard_data['month_name']} {dashboard_data['year']}</div>", unsafe_allow_html=True)
    
    with col4:
        if st.button("Next ▶", use_container_width=True, key="btn_next_month"):
            NeroTimeLogic.navigate_month("next")
            st.rerun()
    
    with col5:
        if st.button("Today", use_container_width=True, key="btn_today_month"):
            NeroTimeLogic.navigate_month("today")
            st.rerun()
    
    st.divider()
    
    # Display warnings from last generation (BEFORE the button) - COLLAPSIBLE
    if 'timetable_warnings' in st.session_state and st.session_state.timetable_warnings:
        # Count warning types
        errors = sum(1 for w in st.session_state.timetable_warnings if w.startswith('❌'))
        warnings_count = sum(1 for w in st.session_state.timetable_warnings if w.startswith('⚠️'))
        success_count = sum(1 for w in st.session_state.timetable_warnings if w.startswith('✓'))
        
        # Create header based on content
        if errors > 0:
            header = f"⚠️ Timetable Warnings ({errors} error(s), {warnings_count} warning(s))"
            expanded = True
        elif warnings_count > 0:
            header = f"⚠️ Timetable Warnings ({warnings_count} warning(s))"
            expanded = True
        else:
            header = f"✓ Timetable Generation Info ({success_count} activity/activities)"
            expanded = False
        
        with st.expander(header, expanded=expanded):
            for warning in st.session_state.timetable_warnings:
                if warning.startswith('❌'):
                    st.error(warning)
                elif warning.startswith('⚠️'):
                    st.warning(warning)
                elif warning.startswith('✓'):
                    st.success(warning)
                else:
                    st.info(warning)
        st.divider()
    
    # Generate timetable - BIG BUTTON
    if st.button("🚀 GENERATE TIMETABLE", type="primary", use_container_width=True, key="btn_generate_timetable"):
        if st.session_state.list_of_activities or st.session_state.list_of_compulsory_events or st.session_state.school_schedule:
            with st.spinner("Generating your perfect schedule..."):
                result = NeroTimeLogic.generate_timetable()
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
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return [d for d in month_days if start_of_week <= d['date'].date() <= end_of_week]
        
        elif filter_type == 'monthly':
            return [d for d in month_days if d['date'].month == today.month and d['date'].year == today.year]
        
        else:  # yearly
            return [d for d in month_days if d['date'].year == today.year]
    
    filtered_days = filter_events_by_period(dashboard_data['month_days'], st.session_state.event_filter)
    
    if dashboard_data['timetable'] and filtered_days:
        for day_info in filtered_days:
            day_display = day_info['display']
            date_obj = day_info['date']
            formatted_date = date_obj.strftime("%d %B %Y - %A")
            
            if day_display in dashboard_data['timetable']:
                is_current_day = (day_display == dashboard_data['current_day'])
                events = dashboard_data['timetable'][day_display]
                
                if not events:
                    continue
                
                with st.expander(f"{'🟢 ' if is_current_day else ''}📅 {formatted_date}", expanded=is_current_day):
                    for idx, event in enumerate(events):
                        # Check if current
                        is_current_slot = False
                        if is_current_day and dashboard_data['current_time']:
                            from Timetable_Generation import time_str_to_minutes
                            event_start = time_str_to_minutes(event['start'])
                            event_end = time_str_to_minutes(event['end'])
                            current_minutes = time_str_to_minutes(dashboard_data['current_time'])
                            is_current_slot = event_start <= current_minutes < event_end
                        
                        # Create timetable row
                        if event["type"] == "ACTIVITY":
                            activity_name = event['name'].split(' (Session')[0]
                            session_part = event['name'].split(' (Session')[1].rstrip(')') if '(Session' in event['name'] else "1"
                            is_completed = event.get('is_completed', False)
                            is_user_edited = event.get('is_user_edited', False)
                            
                            st.markdown('<div class="timetable-row">', unsafe_allow_html=True)
                            st.markdown('<div class="event-content activity">', unsafe_allow_html=True)
                            
                            # Left: Event info
                            st.markdown('<div class="event-info">', unsafe_allow_html=True)
                            
                            # Title row with badges
                            title_parts = []
                            if is_current_slot:
                                title_parts.append('<span class="happening-now">● LIVE NOW</span>')
                            if is_user_edited:
                                title_parts.append('<span class="user-edited-badge">EDITED</span>')
                            
                            status_icon = "✅" if is_completed else "⚫"
                            title_parts.append(f'{status_icon} <strong>{activity_name}</strong>')
                            title_parts.append(f'<span style="opacity: 0.7;">Session {session_part}</span>')
                            
                            st.markdown(f'<div class="event-title">{" ".join(title_parts)}</div>', unsafe_allow_html=True)
                            
                            # Get activity details
                            activity_obj = next((a for a in st.session_state.list_of_activities if a['activity'] == activity_name), None)
                            if activity_obj:
                                sessions = activity_obj.get('sessions', [])
                                completed_sessions_act = sum(1 for s in sessions if s.get('is_completed', False))
                                total_sessions_act = len(sessions)
                                total_hours = activity_obj['timing']
                                completed_hours = sum(s.get('duration_hours', 0) for s in sessions if s.get('is_completed', False))
                                
                                st.markdown(
                                    f'<div class="event-details">'
                                    f'📊 Progress: {int(completed_sessions_act)}/{int(total_sessions_act)} sessions • '
                                    f'{completed_hours:.1f}h / {total_hours:.1f}h completed'
                                    f'</div>', 
                                    unsafe_allow_html=True
                                )
                            
                            st.markdown('</div>', unsafe_allow_html=True)  # Close event-info
                            
                            # Right: Time + Actions stacked vertically
                            st.markdown('<div class="event-right-section">', unsafe_allow_html=True)
                            st.markdown(f'<div class="event-time">{event["start"]} — {event["end"]}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)  # Close event-right-section
                            
                            st.markdown('</div>', unsafe_allow_html=True)  # Close event-content
                            st.markdown('</div>', unsafe_allow_html=True)  # Close timetable-row
                            
                            # Buttons OUTSIDE the card, right-aligned below it
                            if not is_completed and event['can_verify']:
                                col_spacer, col_buttons = st.columns([0.75, 0.25])
                                with col_buttons:
                                    col_check, col_skip = st.columns(2)
                                    with col_check:
                                        if st.button("✓", key=f"verify_{day_display}_{idx}_{event.get('session_id', idx)}", 
                                                   use_container_width=True, help="Mark as completed"):
                                            result = NeroTimeLogic.verify_session(day_display, idx, completed=True)
                                            if result["success"]:
                                                st.success("✅ Completed!")
                                                st.rerun()
                                    with col_skip:
                                        if st.button("✗", key=f"skip_{day_display}_{idx}_{event.get('session_id', idx)}", 
                                                   use_container_width=True, help="Mark as not done"):
                                            result = NeroTimeLogic.verify_session(day_display, idx, completed=False)
                                            if result["success"]:
                                                st.warning("⚠️ Skipped")
                                                st.rerun()
                            elif is_completed:
                                col_spacer, col_check_display = st.columns([0.85, 0.15])
                                with col_check_display:
                                    st.markdown('<div style="text-align: center; font-size: 24px;">✅</div>', unsafe_allow_html=True)
                        
                        elif event["type"] == "SCHOOL":
                            st.markdown('<div class="timetable-row">', unsafe_allow_html=True)
                            st.markdown('<div class="event-content school">', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-info">', unsafe_allow_html=True)
                            
                            title_parts = []
                            if is_current_slot:
                                title_parts.append('<span class="happening-now">● LIVE NOW</span>')
                            title_parts.append('🏫 <strong>School/Work</strong>')
                            
                            st.markdown(f'<div class="event-title">{" ".join(title_parts)}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="event-details">Recurring schedule</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-right-section">', unsafe_allow_html=True)
                            st.markdown(f'<div class="event-time">{event["start"]} — {event["end"]}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)  # Close event-content
                            st.markdown('</div>', unsafe_allow_html=True)  # Close timetable-row
                        
                        elif event["type"] == "COMPULSORY":
                            st.markdown('<div class="timetable-row">', unsafe_allow_html=True)
                            st.markdown('<div class="event-content compulsory">', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-info">', unsafe_allow_html=True)
                            
                            title_parts = []
                            if is_current_slot:
                                title_parts.append('<span class="happening-now">● LIVE NOW</span>')
                            title_parts.append(f'🔴 <strong>{event["name"]}</strong>')
                            
                            st.markdown(f'<div class="event-title">{" ".join(title_parts)}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="event-details">Compulsory Event</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-right-section">', unsafe_allow_html=True)
                            st.markdown(f'<div class="event-time">{event["start"]} — {event["end"]}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)  # Close event-content
                            st.markdown('</div>', unsafe_allow_html=True)  # Close timetable-row
                        
                        else:  # BREAK
                            st.markdown('<div class="timetable-row">', unsafe_allow_html=True)
                            st.markdown('<div class="event-content break">', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-info">', unsafe_allow_html=True)
                            st.markdown('<div class="event-title">⚪ <strong>Break</strong></div>', unsafe_allow_html=True)
                            st.markdown('<div class="event-details">Rest & recharge</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-right-section">', unsafe_allow_html=True)
                            st.markdown(f'<div class="event-time">{event["start"]} — {event["end"]}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)  # Close event-content
                            st.markdown('</div>', unsafe_allow_html=True)  # Close timetable-row
    else:
        st.info("No events for this period")

# ==================== ACTIVITIES TAB ====================
with tab2:
    st.header("Activities")
    
    with st.expander("➕ Add Activity", expanded=False):
        name = st.text_input("Name", key="activity_name")
        col1, col2 = st.columns(2)
        with col1:
            deadline = st.date_input("Deadline", min_value=datetime.now().date(), key="activity_deadline")
        with col2:
            hours = st.number_input("Hours", 1, 100, 1, key="activity_hours")
        
        col3, col4 = st.columns(2)
        with col3:
            min_s = st.number_input("Min Session (min)", 15, 180, 30, 15, key="min_s")
            # Round to nearest 15
            min_s = ((min_s + 7) // 15) * 15
        with col4:
            max_s = st.number_input("Max Session (min)", 30, 240, 120, 15, key="max_s")
            # Round to nearest 15
            max_s = ((max_s + 7) // 15) * 15
            if max_s < min_s:
                max_s = min_s
        
        from Timetable_Generation import WEEKDAY_NAMES
        days = st.multiselect("Days", WEEKDAY_NAMES, WEEKDAY_NAMES, key="activity_days")
        
        if st.button("Add", type="primary", use_container_width=True, key="btn_add_activity"):
            if name:
                result = NeroTimeLogic.add_activity(name, 3, deadline.isoformat(), hours, min_s, max_s, days)
                if result["success"]:
                    st.success("✓ Added")
                    st.rerun()
                else:
                    st.error(result["message"])
    
    st.divider()
    
    activities_data = NeroTimeLogic.get_activities_data()
    
    if activities_data['activities']:
        for idx, act in enumerate(activities_data['activities']):
            with st.expander(f"{idx+1}. {act['activity']} ({act['progress']['completed']:.1f}h/{act['timing']:.1f}h)"):
                st.progress(act['progress']['percentage'] / 100)
                st.caption(f"Deadline: {act['deadline']} days")
                
                # Show sessions
                st.markdown("#### 📋 Sessions")
                sessions_data = act.get('sessions', [])
                
                if sessions_data:
                    for sess_idx, session in enumerate(sessions_data):
                        session_id = session.get('session_id', f"session_{sess_idx}")
                        is_completed = session.get('is_completed', False)
                        duration_hours = session.get('duration_hours', 0)
                        duration_minutes = session.get('duration_minutes', 0)
                        
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
                                    if st.button("✏️", key=edit_key, use_container_width=True):
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
                                        default_date = datetime.now().date()
                                        new_date = st.date_input(
                                            "Date",
                                            value=default_date,
                                            min_value=datetime.now().date(),
                                            key=f"date_{session_id}"
                                        )
                                    
                                    with col_e2:
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
                                        # Round to nearest 15
                                        new_duration = ((new_duration + 7) // 15) * 15
                                    
                                    col_btn1, col_btn2 = st.columns(2)
                                    with col_btn1:
                                        submitted = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
                                    with col_btn2:
                                        cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
                                    
                                    if submitted:
                                        if act['deadline'] < 0:
                                            st.error("❌ Cannot edit - activity deadline has passed!")
                                        else:
                                            actual_day = WEEKDAY_NAMES[new_date.weekday()]
                                            
                                            result = NeroTimeLogic.edit_session(
                                                act['activity'],
                                                session_id,
                                                new_day=actual_day,
                                                new_start_time=new_time.strftime("%H:%M"),
                                                new_duration=new_duration,
                                                new_date=new_date.isoformat()
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
                    st.info("No sessions generated yet - generate a timetable to create sessions")
                
                st.markdown("---")
                
                # Action buttons
                col1, col2 = st.columns(2)
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
                if st.button("Delete", key=f"del_event_{idx}_{evt['event']}"):
                    result = NeroTimeLogic.delete_event(idx)
                    if result["success"]:
                        st.rerun()
    else:
        st.info("No events")

# ==================== SCHOOL TAB ====================
with tab4:
    st.header("School/Work Schedule")
    
    with st.expander("➕ Add Schedule", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            from Timetable_Generation import WEEKDAY_NAMES
            day = st.selectbox("Day", WEEKDAY_NAMES, key="school_day")
        with col2:
            start = st.time_input("Start", key="school_start")
            end = st.time_input("End", key="school_end")
        
        if st.button("Add", type="primary", use_container_width=True, key="btn_add_school"):
            result = NeroTimeLogic.add_school_schedule(day, start.strftime("%H:%M"), end.strftime("%H:%M"), "School/Work")
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
                with st.expander(f"{day} ({len(school_data['schedule'][day])} slots)"):
                    for idx, cls in enumerate(school_data['schedule'][day]):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"**School/Work**")
                            st.caption(f"{cls['start_time']} - {cls['end_time']}")
                        with col2:
                            if st.button("×", key=f"del_school_{day}_{idx}"):
                                result = NeroTimeLogic.delete_school_schedule(day, idx)
                                if result["success"]:
                                    st.rerun()
    else:
        st.info("No schedule")

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

# ==================== ACHIEVEMENTS TAB ====================
with tab6:
   Badge = 0
   st.header("Achievements")
   st.subheader(f"**Hours of work done:** {total_hours_completed:.1f}h,**Total activities:** {total_activities} Activites,**Badges Earnt:** {Badge} Badges")
   col1, col2, col3 = st.columns(3)
   with col1:
      st.markdown("<h1 style='text-align: center; margin-top: 5rem; color: #FFFFFF;'>✅", unsafe_allow_html=True)
      st.write("You Just started. Achieve:", f"{total_hours_completed:.1f}/0 hours to get this badge")
      if total_hours_completed > 0:
         st.write("UNLOCKED 🔓")

# Auto-refresh for live clock (every 1 second)
st.markdown("""
<script>
    setTimeout(function() {
        window.parent.location.reload();
    }, 1000);
</script>
""", unsafe_allow_html=True)

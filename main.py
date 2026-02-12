"""
NERO-Time UI
"""
import pytz
import math
import random
import streamlit as st
from datetime import datetime, time, timedelta
from nero_logic import NeroTimeLogic
from Firebase_Function import (
    load_from_firebase, 
    authenticate_user, 
    create_user,
    change_password
    )

from css_style import css_scheme

st.set_page_config(page_title="NERO-TIME", page_icon="🕛", layout="wide")

# TIMETABLE COLOURS IN CSS
st.markdown(css_scheme, unsafe_allow_html=True)

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
            Finish all of your tasks on time. On Neko-Time.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize login mode state
    if 'login_mode' not in st.session_state:
        st.session_state.login_mode = 'login'  # 'login' or 'register'
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Toggle between Login and Register
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.markdown("### Welcome Back")
            
            login_username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username"
            )
            
            login_password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            
            if st.button("Sign In", type="primary", use_container_width=True, key="btn_signin"):
                if login_username and login_password:
                    with st.spinner("Signing in..."):
                        result = authenticate_user(login_username, login_password)
                    
                    if result["success"]:
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = login_username
                        st.success("✓ " + result["message"])
                        st.rerun()
                    else:
                        st.error("✗ " + result["message"])
                else:
                    st.error("Please enter both username and password")
        
        with tab2:
            st.markdown("### Create Account")
            
            reg_username = st.text_input(
                "Username",
                placeholder="Choose a username",
                key="reg_username",
                help="Must be unique"
            )
            
            reg_email = st.text_input(
                "Email (optional)",
                placeholder="your.email@example.com",
                key="reg_email"
            )
            
            reg_password = st.text_input(
                "Password",
                type="password",
                placeholder="Choose a strong password",
                key="reg_password"
            )
            
            reg_password_confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="reg_password_confirm"
            )
            
            if st.button("Create Account", type="primary", use_container_width=True, key="btn_register"):
                if not reg_username:
                    st.error("Username is required")
                elif not reg_password:
                    st.error("Password is required")
                elif reg_password != reg_password_confirm:
                    st.error("Passwords do not match")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating account..."):
                        result = create_user(reg_username, reg_password, reg_email)
                    
                    if result["success"]:
                        st.success("✓ " + result["message"])
                        st.info("You can now login with your credentials!")
                        # Auto-login after registration
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = reg_username
                        st.rerun()
                    else:
                        st.error("✗ " + result["message"])
    
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

# ensure integers for session counts
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

st.caption(f"👤 {st.session_state.get('username', st.session_state.user_id)}")
st.divider()

# NAVIGATION TABS
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Dashboard", 
    "Activities", 
    "Events & Schedule",
    "Verification",
    "Achievements",
    "Settings"
    ])

# ==================== DASHBOARD TAB ====================
with tab1:
    # get data needed to be displayed on dashboard
    dashboard_data = NeroTimeLogic.get_dashboard_data()
    
    # Month navigation part ui formatting
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
    
    # WARNINGS DISPLAY
    if 'timetable_warnings' in st.session_state and st.session_state.timetable_warnings:
        # Count amount of warnings using emoji markers
        errors = sum(1 for w in st.session_state.timetable_warnings if w.startswith('❌')) 
        warnings_count = sum(1 for w in st.session_state.timetable_warnings if w.startswith('⚠️'))
        success_count = sum(1 for w in st.session_state.timetable_warnings if w.startswith('✓'))
        
        # Header warning based on errro
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
                # warning message = warning 
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
    if st.button("* GENERATE TIMETABLE *", type="primary", use_container_width=True, key="btn_generate_timetable"):
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
    
    # EVENT FILTER
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
    
    # Filter events based on year, month, or week
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
    
    # ACTUAL TIMETABLE DISPLAY

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
                        # Check if current or finished
                        is_current_slot = False
                        is_finished = event.get('is_finished', False)
                        
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
                            
                            # Determine CSS class
                            css_class = "timetable-row activity"
                            is_skipped = is_finished and not event['can_verify'] and not is_completed
                            if is_skipped:
                                css_class += " skipped"
                            elif is_finished and not is_completed:
                                css_class += " finished"
                            
                            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                            
                            # Left: Event info
                            st.markdown('<div class="event-info">', unsafe_allow_html=True)
                            
                            # Title row 
                            title_parts = []
                            if is_current_slot:
                                title_parts.append('<span class="happening-now">● LIVE NOW</span>')
                            if is_finished and not is_completed:
                                title_parts.append('<span class="finished-badge">⏰ FINISHED</span>')
                            if is_user_edited:
                                title_parts.append('<span class="user-edited-badge">EDITED</span>')
                            
                            status_icon = "✅" if is_completed else "⚫"
                            
                            # Check if session was skipped (is_finished but can't verify and not completed)
                            is_skipped = is_finished and not event['can_verify'] and not is_completed
                            if is_skipped:
                                status_icon = "❌"
                                title_parts.append('<span class="user-edited-badge" style="background: #F44336;">SKIPPED</span>')
                            
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
                            
                            st.markdown('</div>', unsafe_allow_html=True)  

            
                            st.markdown('<div class="event-right-section">', unsafe_allow_html=True)
                            st.markdown(f'<div class="event-time">{event["start"]} — {event["end"]}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)  
                            
                            st.markdown('</div>', unsafe_allow_html=True)  
                            
                            if is_finished and not is_completed and event['can_verify']:
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
                            elif not event['can_verify']:
                                # Session was skipped/marked as not done
                                col_spacer, col_skip_display = st.columns([0.85, 0.15])
                                with col_skip_display:
                                    st.markdown('<div style="text-align: center; font-size: 24px;">❌</div>', unsafe_allow_html=True)
                        
                        elif event["type"] == "SCHOOL":
                            st.markdown('<div class="timetable-row school">', unsafe_allow_html=True)
                            
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
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        elif event["type"] == "COMPULSORY":
                            st.markdown('<div class="timetable-row compulsory">', unsafe_allow_html=True)
                            
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
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        else:  # BREAK
                            st.markdown('<div class="timetable-row break">', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-info">', unsafe_allow_html=True)
                            st.markdown('<div class="event-title">⚪ <strong>Break</strong></div>', unsafe_allow_html=True)
                            st.markdown('<div class="event-details">Rest & recharge</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-right-section">', unsafe_allow_html=True)
                            st.markdown(f'<div class="event-time">{event["start"]} — {event["end"]}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No events for this period")

# ==================== ACTIVITIES TAB ====================
with tab2:
    st.header("Activities")
    
    with st.expander("➕ Add Activity", expanded=False):
        name = st.text_input("Name", key="activity_name")
        
        # Session mode selection
        session_mode = st.radio(
            "Session Mode",
            ["Automatic", "Manual"],
            help="Automatic: AI schedules sessions. Manual: You add sessions yourself",
            horizontal=True,
            key="session_mode"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            deadline = st.date_input("Deadline", min_value=datetime.now().date(), key="activity_deadline")
        with col2:
            hours = st.number_input("Hours", 1, 100, 1, key="activity_hours")
        
        if session_mode == "Automatic":
            col3, col4 = st.columns(2)
            with col3:
                min_s = st.number_input("Min Session (min)", 15, 180, 30, 15, key="min_s")
                # Round to nearest 15
                min_s = int(((min_s + 7) // 15) * 15)
            with col4:
                max_s = st.number_input("Max Session (min)", 30, 240, 120, 15, key="max_s")
                # Round to nearest 15
                max_s = int(((max_s + 7) // 15) * 15)
                if max_s < min_s:
                    max_s = min_s
            
            from Timetable_Generation import WEEKDAY_NAMES
            days = st.multiselect("Days", WEEKDAY_NAMES, WEEKDAY_NAMES, key="activity_days")
        else:
            # Default values for manual mode
            min_s, max_s, days = 30, 120, None
        
        if st.button("Add", type="primary", use_container_width=True, key="btn_add_activity"):
            if name:
                result = NeroTimeLogic.add_activity(
                    name, 3, deadline.isoformat(), hours, min_s, max_s, days,
                    session_mode="manual" if session_mode == "Manual" else "automatic"
                )
                if result["success"]:
                    st.success("✓ Added")
                    st.rerun()
                else:
                    st.error(result["message"])
    
    st.divider()
    
    activities_data = NeroTimeLogic.get_activities_data()
    
    if activities_data['activities']:
        for idx, act in enumerate(activities_data['activities']):
            mode_badge = "🤖 Auto" if act.get('session_mode') == 'automatic' else "✋ Manual"
            with st.expander(f"{idx+1}. {act['activity']} ({act['progress']['completed']:.1f}h/{act['timing']:.1f}h) - {mode_badge}"):
                st.progress(act['progress']['percentage'] / 100)
                st.caption(f"Deadline: {act['deadline']} days")
                
                # Manual session adding for manual mode activities
                if act.get('session_mode') == 'manual':
                    with st.form(key=f"add_manual_session_{idx}"):
                        st.markdown("**➕ Add Manual Session**")
                        col_dur, col_day = st.columns(2)
                        with col_dur:
                            manual_duration = st.number_input("Duration (min)", 15, 240, 60, 15, key=f"manual_dur_{idx}")
                            manual_duration = int(((manual_duration + 7) // 15) * 15)
                        with col_day:
                            from Timetable_Generation import WEEKDAY_NAMES
                            preferred_day = st.selectbox("Preferred Day (optional)", ["Any"] + WEEKDAY_NAMES, key=f"manual_day_{idx}")
                        
                        if st.form_submit_button("Add Session", use_container_width=True):
                            result = NeroTimeLogic.add_manual_session(
                                act['activity'], 
                                int(manual_duration),
                                None if preferred_day == "Any" else preferred_day
                            )
                            if result["success"]:
                                st.success("✓ Session added!")
                                st.rerun()
                            else:
                                st.error(result["message"])
                    
                    st.divider()
                
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
                col1, col2,col3 = st.columns(3)
                if col1.button("Delete", key=f"del_activity_{idx}_{act['activity']}"):
                    result = NeroTimeLogic.delete_activity(idx)
                    if result["success"]:
                        st.rerun()
                if col2.button("Reset", key=f"reset_activity_{idx}_{act['activity']}"):
                    result = NeroTimeLogic.reset_activity_progress(act['activity'])
                    if result["success"]:
                        st.rerun()
                if col3.button("Add"):
                    result = NeroTimeLogic.reset_activity_progress(act['activity'])
                    if result["success"]:
                        st.rerun()
    else:
        st.info("No activities")

# ==================== EVENTS & SCHEDULE TAB ====================
with tab3:
    st.header("All Events")
    
    with st.expander("➕ Add Event/Schedule", expanded=False):
        event_name = st.text_input("Name", key="event_name")
        
        recurrence_type = st.radio(
            "Type",
            ["One-time Event", "Weekly", "Bi-weekly", "Monthly"],
            horizontal=True,
            key="recurrence_type"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_t = st.time_input("Start", key="event_start_time")
        with col2:
            end_t = st.time_input("End", key="event_end_time")
        
        if recurrence_type in ["Weekly", "Bi-weekly"]:
            from Timetable_Generation import WEEKDAY_NAMES
            selected_days = st.multiselect("Days", WEEKDAY_NAMES, key="event_days")
            event_date = None
        else:
            selected_days = None
            event_date = st.date_input("Date", min_value=datetime.now().date(), key="event_date")
        
        if st.button("Add", type="primary", use_container_width=True, key="btn_add_event"):
            if event_name:
                if recurrence_type == "One-time Event":
                    result = NeroTimeLogic.add_event(
                        event_name, event_date.isoformat(), 
                        start_t.strftime("%H:%M"), end_t.strftime("%H:%M")
                    )
                else:
                    recurrence_map = {
                        "Weekly": "weekly",
                        "Bi-weekly": "bi-weekly",
                        "Monthly": "monthly"
                    }
                    result = NeroTimeLogic.add_recurring_event(
                        event_name,
                        start_t.strftime("%H:%M"),
                        end_t.strftime("%H:%M"),
                        recurrence_map[recurrence_type],
                        selected_days,
                        event_date.isoformat() if event_date else None
                    )
                
                if result["success"]:
                    st.success("✓ Added")
                    st.rerun()
                else:
                    st.error(result["message"])
    
    st.divider()
    
    # Display recurring schedules
    st.markdown("### 📅 Recurring Events")
    school_data = NeroTimeLogic.get_school_schedule()
    
    if school_data['schedule']:
        from Timetable_Generation import WEEKDAY_NAMES
        for day in WEEKDAY_NAMES:
            if day in school_data['schedule']:
                with st.expander(f"{day} ({len(school_data['schedule'][day])} slots)"):
                    for idx, cls in enumerate(school_data['schedule'][day]):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            recurrence_badge = cls.get('recurrence', 'weekly').title()
                            st.write(f"**{cls['subject']}** ({recurrence_badge})")
                            st.caption(f"{cls['start_time']} - {cls['end_time']}")
                        with col2:
                            if st.button("×", key=f"del_school_{day}_{idx}"):
                                result = NeroTimeLogic.delete_school_schedule(day, idx)
                                if result["success"]:
                                    st.rerun()
    else:
        st.info("No recurring schedules")
    
    st.divider()
    
    # Display one-time events
    st.markdown("### 📌 One-time Events")
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
        st.info("No one-time events")

# ==================== VERIFICATION TAB ====================
with tab4:
    st.header("Session Verification")
    st.markdown("Verify finished sessions as completed or not completed.")
    
    finished_sessions = st.session_state.get('finished_sessions', [])
    
    if not finished_sessions:
        st.info("No finished sessions to verify yet. Sessions will appear here after their scheduled time has passed.")
    else:
        # Group by activity
        activities_with_finished = {}
        for fs in finished_sessions:
            activity_name = fs.get('activity', 'Unknown')
            if activity_name not in activities_with_finished:
                activities_with_finished[activity_name] = []
            activities_with_finished[activity_name].append(fs)
        
        # Display by activity
        for activity_name, sessions in activities_with_finished.items():
            with st.expander(f"**{activity_name}** ({len(sessions)} finished sessions)", expanded=True):
                for session in sessions:
                    is_verified = session.get('is_verified', False)
                    session_id = session.get('session_id')
                    session_num = session.get('session_num', '?')
                    scheduled_date = session.get('scheduled_date', 'Unknown')
                    scheduled_time = session.get('scheduled_time', 'Unknown')
                    duration_minutes = session.get('duration_minutes', 0)
                    
                    # Create horizontal layout
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        status_icon = "✅" if is_verified else "⏰"
                        st.markdown(f"{status_icon} **Session {session_num}**")
                        st.caption(f"📅 {scheduled_date} at {scheduled_time} ({duration_minutes} min)")
                    
                    with col2:
                        if not is_verified:
                            if st.button("✓ Done", key=f"verify_yes_{session_id}", use_container_width=True):
                                result = NeroTimeLogic.verify_finished_session(session_id, True)
                                if result["success"]:
                                    st.success("Verified!")
                                    st.rerun()
                                else:
                                    st.error(result.get("message", "Error"))
                    
                    with col3:
                        if is_verified:
                            if st.button("✗ Undo", key=f"verify_no_{session_id}", use_container_width=True):
                                result = NeroTimeLogic.verify_finished_session(session_id, False)
                                if result["success"]:
                                    st.warning("Unverified")
                                    st.rerun()
                                else:
                                    st.error(result.get("message", "Error"))
                        else:
                            if st.button("✗ Skip", key=f"verify_skip_{session_id}", use_container_width=True):
                                result = NeroTimeLogic.verify_finished_session(session_id, False)
                                if result["success"]:
                                    st.warning("Skipped")
                                    st.rerun()
                                else:
                                    st.error(result.get("message", "Error"))
                    
                    st.divider()

# ==================== ACHIEVEMENTS TAB ====================
with tab5:
   Badge = 0
   st.header("Achievements")
   col1, col2, col3 = st.columns(3)
   with col1:
      if total_hours_completed >= 0:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>✅", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(abs(0 - total_hours_completed))}h to obtain this badge.</h1>", unsafe_allow_html=True)
         
      st.write("You Just started. Achieve:", f"{total_hours_completed:.1f}/0 hours to get this badge")
      if total_activities >= 5:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>💼", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(5 - total_activities)} more activites to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("My first assignments! Achieve:", f"{total_activities}/5 activites to get this badge")
      if Badge >= 3:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>🏆", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(3 - Badge)} more badges to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("My first achievements! Achieve:", f"{Badge}/3 Badges to get this badge")
   with col2:
      if total_hours_completed >= 24:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>📅", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(max(0, 24 - total_hours_completed))}h to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("A day of work! Achieve:", f"{total_hours_completed:.1f}/24 hours to get this badge")
      if total_activities >= 20:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>💪", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(20 - total_activities)} more activites to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Schedule getting tough! Achieve:", f"{total_activities}/20 activites to get this badge")
      if Badge >= 5:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>🎖️", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(5 - Badge)} more badges to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Wow! Acomplished! Achieve:", f"{Badge}/5 Badges to get this badge")
   with col3:
      if total_hours_completed >= 168:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>👍", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(max(0, 168 - total_hours_completed))}h to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Commitment! Achieve:", f"{total_hours_completed:.1f}/168 hours to get this badge")
      if total_activities >= 50:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>😓", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(50 - total_activities)} more activites to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Can you manage? Achieve:", f"{total_activities}/50 activites to get this badge")
      if Badge >= 8:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>🥳", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(8 - Badge)} more badges to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Collector, I see! Achieve:", f"{Badge}/8 Badges to get this badge")

# ==================== SETTINGS TAB ====================
with tab5:
   Badge = 0
   st.header("Achievements")
   col1, col2, col3 = st.columns(3)
   with col1:
      if total_hours_completed >= 0:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>✅", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(abs(0 - total_hours_completed))}h to obtain this badge.</h1>", unsafe_allow_html=True)
         
      st.write("You Just started. Achieve:", f"{total_hours_completed:.1f}/0 hours to get this badge")
      if total_activities >= 5:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>💼", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(5 - total_activities)} more activites to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("My first assignments! Achieve:", f"{total_activities}/5 activites to get this badge")
      if Badge >= 3:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>🏆", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(3 - Badge)} more badges to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("My first achievements! Achieve:", f"{Badge}/3 Badges to get this badge")
   with col2:
      if total_hours_completed >= 24:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>📅", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(max(0, 24 - total_hours_completed))}h to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("A day of work! Achieve:", f"{total_hours_completed:.1f}/24 hours to get this badge")
      if total_activities >= 20:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>💪", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(20 - total_activities)} more activites to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Schedule getting tough! Achieve:", f"{total_activities}/20 activites to get this badge")
      if Badge >= 5:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>🎖️", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(5 - Badge)} more badges to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Wow! Acomplished! Achieve:", f"{Badge}/5 Badges to get this badge")
   with col3:
      if total_hours_completed >= 168:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>👍", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(max(0, 168 - total_hours_completed))}h to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Commitment! Achieve:", f"{total_hours_completed:.1f}/168 hours to get this badge")
      if total_activities >= 50:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>😓", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(50 - total_activities)} more activites to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Can you manage? Achieve:", f"{total_activities}/50 activites to get this badge")
      if Badge >= 8:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>🥳", unsafe_allow_html=True)
         st.markdown("<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> UNLOCKED 🔓", unsafe_allow_html=True)
         Badge+=1
      else:
         st.markdown("<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌", unsafe_allow_html=True)
         st.markdown(f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>Please obtain {int(8 - Badge)} more badges to obtain this badge.</h1>", unsafe_allow_html=True)

      st.write("Collector, I see! Achieve:", f"{Badge}/8 Badges to get this badge")

# ==================== SETTINGS TAB ====================
with tab6:
    st.header("Settings")
    
    st.markdown("### 👤 Account Information")
    user_info_col1, user_info_col2 = st.columns(2)
    
    with user_info_col1:
        st.write(f"**Username:** {st.session_state.get('username', 'N/A')}")
        st.write(f"**User ID:** {st.session_state.user_id[:8]}...")
    
    with user_info_col2:
        if 'user_email' in st.session_state and st.session_state.user_email:
            st.write(f"**Email:** {st.session_state.user_email}")
        else:
            st.write("**Email:** Not set")
    
    st.divider()
    
    # Change Password Section
    st.markdown("### 🔐 Change Password")
    with st.expander("Change Your Password", expanded=False):
        with st.form(key="change_password_form"):
            old_password = st.text_input(
                "Current Password",
                type="password",
                key="old_password"
            )
            
            new_password = st.text_input(
                "New Password",
                type="password",
                key="new_password",
                help="Minimum 6 characters recommended"
            )
            
            confirm_new_password = st.text_input(
                "Confirm New Password",
                type="password",
                key="confirm_new_password"
            )
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submit_password = st.form_submit_button("Change Password", type="primary", use_container_width=True)
            with col_cancel:
                cancel_password = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit_password:
                if not old_password or not new_password or not confirm_new_password:
                    st.error("All fields are required")
                elif new_password != confirm_new_password:
                    st.error("New passwords do not match")
                elif len(new_password) < 6:
                    st.warning("Password should be at least 6 characters")
                else:
                    with st.spinner("Changing password..."):
                        result = change_password(st.session_state.user_id, old_password, new_password)
                    
                    if result["success"]:
                        st.success("✓ " + result["message"])
                    else:
                        st.error("✗ " + result["message"])
    
    st.divider()
    
    st.markdown("### 🗂️ Data Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear All Data", use_container_width=True, key="btn_clear_data"):
            result = NeroTimeLogic.clear_all_data()
            if result["success"]:
                st.warning("⚠️ All data cleared")
                st.rerun()
    
    with col2:
        if st.button("Logout", type="primary", use_container_width=True, key="btn_logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.user_email = None
            st.session_state.data_loaded = False
            st.rerun()



# Auto-refresh for live clock (every 1 second)
st.markdown("""
<script>
    setTimeout(function() {
        window.parent.location.reload();
    }, 1000);
</script>
""", 
unsafe_allow_html=True)
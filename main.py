"""
ui only
"""
import random
import streamlit as st
from datetime import datetime
from nero_logic import NeroTimeLogic
from Firebase_Function import load_from_firebase

# Page configuration
st.set_page_config(page_title="NERO-TIME", page_icon="🕛", layout="wide")

# Custom CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stButton > button {
        font-size: 13px;
        padding: 8px 16px;
        border-radius: 10px;
        border: 1px solid #e6c7f2;
        background: #fff;
        color: #5a2b7a;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background: #f6e6ff;
        border-color: #c77dff;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #c77dff, #ff8dc7);
        color: white;
        border: none;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
        color: #6a1bb9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
NeroTimeLogic.initialize_session_state()

# Load data from Firebase if not loaded
if not st.session_state.data_loaded and st.session_state.user_id:
    with st.spinner("Loading..."):
        loaded_activities = load_from_firebase(st.session_state.user_id, 'activities')
        loaded_events = load_from_firebase(st.session_state.user_id, 'events')
        loaded_timetable = load_from_firebase(st.session_state.user_id, 'timetable')
        loaded_progress = load_from_firebase(st.session_state.user_id, 'activity_progress')
        loaded_pending = load_from_firebase(st.session_state.user_id, 'pending_verifications')
        loaded_month = load_from_firebase(st.session_state.user_id, 'current_month')
        loaded_year = load_from_firebase(st.session_state.user_id, 'current_year')
        
        if loaded_activities:
            st.session_state.list_of_activities = loaded_activities
        if loaded_events:
            st.session_state.list_of_compulsory_events = loaded_events
        if loaded_timetable:
            st.session_state.timetable = loaded_timetable
        if loaded_progress:
            st.session_state.activity_progress = loaded_progress
        if loaded_pending:
            st.session_state.pending_verifications = loaded_pending
        if loaded_month:
            st.session_state.current_month = loaded_month
        if loaded_year:
            st.session_state.current_year = loaded_year
        
        st.session_state.data_loaded = True


# ==================== LOGIN SCREEN ====================
if not st.session_state.user_id:
    st.title("Welcome to NERO-Time")
    st.markdown("Please enter your user ID to continue")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_input = st.text_input("User ID", placeholder="email@example.com")
        if st.button("Login", type="primary", use_container_width=True):
            if user_input:
                result = NeroTimeLogic.login_user(user_input)
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])
            else:
                st.error("Please enter a user ID")
    st.stop()


# ==================== MAIN APP ====================
st.title("NERO-Time")
st.caption(f"Logged in as: {st.session_state.user_id}")

# Navigation
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Activities", "Events", "Settings"])


# ==================== DASHBOARD TAB ====================
with tab1:
    # Get dashboard data from logic layer
    dashboard_data = NeroTimeLogic.get_dashboard_data()
    
    # Month navigation
    col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
    
    with col_prev:
        if st.button("◀ Prev", use_container_width=True):
            result = NeroTimeLogic.navigate_month("prev")
            if result["success"]:
                st.rerun()
    
    with col_month:
        # Month display with calendar popup
        import calendar
        cal = calendar.monthcalendar(dashboard_data['year'], dashboard_data['current_month'])
        
        # Create calendar HTML
        calendar_html = f"""
        <div style='text-align: center; color: #4a0080; font-weight: 600; margin-bottom: 8px;'>
            {dashboard_data['month_name']} {dashboard_data['year']}
        </div>
        <table style='width: 100%; border-collapse: collapse; font-size: 12px;'>
            <tr>
                <th style='padding: 5px; color: #6a1bb9;'>Su</th>
                <th style='padding: 5px; color: #6a1bb9;'>Mo</th>
                <th style='padding: 5px; color: #6a1bb9;'>Tu</th>
                <th style='padding: 5px; color: #6a1bb9;'>We</th>
                <th style='padding: 5px; color: #6a1bb9;'>Th</th>
                <th style='padding: 5px; color: #6a1bb9;'>Fr</th>
                <th style='padding: 5px; color: #6a1bb9;'>Sa</th>
            </tr>
        """
        
        current_day = datetime.now().day if (dashboard_data['current_month'] == datetime.now().month and 
                                            dashboard_data['year'] == datetime.now().year) else None
        
        for week in cal:
            calendar_html += "<tr>"
            for day in week:
                if day == 0:
                    calendar_html += "<td style='padding: 5px;'></td>"
                else:
                    bg_color = "background: #c77dff; color: white; border-radius: 50%;" if day == current_day else ""
                    calendar_html += f"<td style='padding: 5px; text-align: center; {bg_color}'>{day}</td>"
            calendar_html += "</tr>"
        
        calendar_html += "</table>"
        
        # Display month button with popup
        st.markdown(f"""
        <div class="month-display" style="position: relative;">
            <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #e0c3fc, #d0a4f7); 
                        border: 2px solid #c77dff; border-radius: 10px; color: #4a0080; font-weight: 700; 
                        font-size: 16px; cursor: pointer;">
                📅 {dashboard_data['month_name']} {dashboard_data['year']}
            </div>
            <div class="calendar-popup">
                {calendar_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_next:
        if st.button("Next ▶", use_container_width=True):
            result = NeroTimeLogic.navigate_month("next")
            if result["success"]:
                st.rerun()
    
    with col_today:
        if st.button("Today", use_container_width=True):
            result = NeroTimeLogic.navigate_month("today")
            if result["success"]:
                st.rerun()
    
    st.divider()
    
    
    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("Generate Timetable", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                min_session = st.number_input("Min session (minutes)", 15, 180, 30, 15)
            with col_b:
                max_session = st.number_input("Max session (minutes)", 30, 240, 120, 15)
                
            
            if st.button("Generate", type="primary", use_container_width=True):
                if st.session_state.list_of_activities or st.session_state.list_of_compulsory_events:
                    with st.spinner("Generating..."):
                        result = NeroTimeLogic.generate_timetable(min_session, max_session)
                    if result["success"]:
                        st.success(result["message"])
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(result["message"])
                else:
                    st.warning("Add activities or events first")
    
    with col2:
        if st.button("💾 Save Data", use_container_width=True, type="primary"):
            result = NeroTimeLogic.save_all_data()
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result["message"])
    
    st.divider()
    
    # Display Timetable
    st.header("📊Your Monthly Timetable")
    
    if dashboard_data['timetable']:
        for day_info in dashboard_data['month_days']:
            day_display = day_info['display']
            
            if day_display in dashboard_data['timetable']:
                is_current_day = (day_display == dashboard_data['current_day'])
                events = dashboard_data['timetable'][day_display]
                
                if not events:
                    continue
                
                with st.expander(f"{'🟢 ' if is_current_day else ''}📅 {day_display}", expanded=is_current_day):
                    for idx, event in enumerate(events):
                        # Check if current time slot
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
                            session_duration = event['session_duration']
                            can_verify = event['can_verify']
                            
                            if is_current_slot:
                                st.markdown("**🟢 HAPPENING NOW**")
                            
                            col1, col2 = st.columns([0.85, 0.15])
                            with col1:
                                st.markdown(f"**🔵 {event['start']} - {event['end']}:** {event['name']}")
                                st.progress(progress['percentage'] / 100)
                                st.caption(f"{progress['completed']:.1f}h / {progress['total']}h completed")
                            
                            with col2:
                                if can_verify:
                                    if st.button("✓", key=f"verify_{day_display}_{idx}", use_container_width=True):
                                        result = NeroTimeLogic.verify_session(day_display, idx)
                                        if result["success"]:
                                            st.success(result["message"])
                                            st.rerun()
                                        else:
                                            st.error(result["message"])
                                else:
                                    st.caption("⏳ Not yet")
                        
                        elif event["type"] == "COMPULSORY":
                            if is_current_slot:
                                st.markdown("**🟢 HAPPENING NOW**")
                            st.markdown(f"**🔴 {event['start']} - {event['end']}:** {event['name']}")
                        
                        else:  # BREAK
                            if is_current_slot:
                                st.markdown("**🟢 BREAK TIME**")
                            st.markdown(f"*⚪ {event['start']} - {event['end']}: {event['name']}*")
    else:
        st.info("No timetable generated yet")


# ==================== ACTIVITIES TAB ====================
with tab2:
    st.header("📝 Manage Activities")
    
    # Add new activity
    with st.expander("➕ Add New Activity", expanded=True):
        activity_name = st.text_input("Activity Name")
        col1, col2 = st.columns(2)
        with col1:
            priority = st.slider("Priority", 1, 5, 3)
            deadline_date = st.date_input("Deadline", min_value=datetime.now().date())
        with col2:
            timing = st.number_input("Total Hours", min_value=1, max_value=100, value=1)
        
        st.write("**Session Timing Preferences (Optional)**")
        col3, col4 = st.columns(2)
        with col3:
            min_session_min = st.number_input("Min session (minutes)", 15, 180, 30, 15, key="add_min_session")
        with col4:
            max_session_min = st.number_input("Max session (minutes)", 30, 240, 120, 15, key="add_max_session")
            sessions = timing/(random.randint(min_session_min, max_session_min))
        
        if st.button("Add Activity", use_container_width=True, type="primary"):
            if activity_name:
                result = NeroTimeLogic.add_activity(
                    activity_name, priority, deadline_date.isoformat(), 
                    timing, min_session_min, max_session_min,sessions
                )
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])
    
    st.divider()
    
    # List activities
    activities_data = NeroTimeLogic.get_activities_data()
    
    if activities_data['activities']:
        for idx, act in enumerate(activities_data['activities']):
            progress = act['progress']
            
            with st.expander(f"{idx+1}. {act['activity']} ({progress['completed']:.1f}h / {act['timing']}h)"):
                st.progress(progress['percentage'] / 100)
                st.write(f"⭐ Priority: {act['priority']} | ⏰ Deadline: {act['deadline']} days")
                
                if 'min_session_minutes' in act and 'max_session_minutes' in act and 'sessions' in act:
                    st.caption(f"📊 Session length: {act['min_session_minutes']}-{act['max_session_minutes']} minutes, Session Amounts: {act['sessions']}")
                
                col1, col2, col3 = st.columns(3)
                
                if col1.button("🗑️ Delete", key=f"del_act_{idx}", use_container_width=True):
                    result = NeroTimeLogic.delete_activity(idx)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
                
                if col2.button("🔄 Reset Progress", key=f"reset_{idx}", use_container_width=True):
                    result = NeroTimeLogic.reset_activity_progress(act['activity'])
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
    else:
        st.info("No activities added yet")


# ==================== EVENTS TAB ====================
with tab3:
    st.header("🔴 Manage Compulsory Events")
    
    # Add new event
    with st.expander("➕ Add New Event", expanded=True):
        event_name = st.text_input("Event Name")
        
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Event Date", min_value=datetime.now().date())
        with col2:
            from Timetable_Generation import WEEKDAY_NAMES
            event_day = WEEKDAY_NAMES[event_date.weekday()]
            st.text_input("Day", value=event_day, disabled=True)
        
        col3, col4 = st.columns(2)
        with col3:
            start_time = st.time_input("Start Time")
        with col4:
            end_time = st.time_input("End Time")
        
        if st.button("Add Event", use_container_width=True, type="primary"):
            if event_name:
                result = NeroTimeLogic.add_event(
                    event_name, 
                    event_date.isoformat(),
                    start_time.strftime("%H:%M"),
                    end_time.strftime("%H:%M")
                )
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])
    
    st.divider()
    
    # List events
    events_data = NeroTimeLogic.get_events_data()
    
    if events_data['events']:
        for idx, evt in enumerate(events_data['events']):
            with st.expander(f"{idx+1}. {evt['event']} - {evt['day']}"):
                st.write(f"🕐 {evt['start_time']} - {evt['end_time']}")
                
                if st.button("🗑️ Delete", key=f"del_evt_{idx}", use_container_width=True):
                    result = NeroTimeLogic.delete_event(idx)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
    else:
        st.info("No events added yet")


# ==================== SETTINGS TAB ====================
with tab4:
    st.header("⚙️ Settings")
    
    st.subheader("Account Settings")
    st.write(f"**User ID:** {st.session_state.user_id}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚪 Logout", type="primary", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.data_loaded = False
            st.rerun()
    
    with col2:
        if st.button("⚠️ Clear All Data", use_container_width=True):
            result = NeroTimeLogic.clear_all_data()
            if result["success"]:
                st.warning(result["message"])
                st.rerun()
            else:
                st.error(result["message"])

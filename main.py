"""
ui only
"""
import math
import random
import streamlit as st
from datetime import datetime, time
from nero_logic import NeroTimeLogic
from Firebase_Function import load_from_firebase

# Page configuration
st.set_page_config(page_title="NERO-TIME", page_icon="🕛", layout="wide")

# Custom CSS - ENHANCED VERSION
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Beautiful gradient background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Content container with glassmorphism */
    .block-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    /* Enhanced buttons */
    .stButton > button {
        font-size: 14px;
        padding: 10px 24px;
        border-radius: 12px;
        border: 2px solid #e6c7f2;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        color: #5a2b7a;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #f6e6ff 0%, #e9d5ff 100%);
        border-color: #c77dff;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(167, 85, 247, 0.3);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
        box-shadow: 0 2px 6px rgba(167, 85, 247, 0.2);
    }
    
    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    /* Month display with enhanced styling */
    .month-display button {
        background: linear-gradient(135deg, #e0c3fc 0%, #d0a4f7 100%) !important;
        color: #4a0080 !important;
        font-weight: 700 !important;
        font-size: 18px !important;
        border: 3px solid #c77dff !important;
        cursor: pointer !important;
        position: relative;
        box-shadow: 0 4px 15px rgba(199, 125, 255, 0.3) !important;
    }
    
    .month-display button:hover {
        background: linear-gradient(135deg, #c77dff 0%, #b895f0 100%) !important;
        border-color: #a855f7 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(167, 85, 247, 0.4) !important;
    }
    
    /* Enhanced expanders */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 12px 16px;
        border: 2px solid #dee2e6;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
        border-color: #c77dff;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background: white;
        border-radius: 10px;
        border: 2px solid transparent;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #f6e6ff 0%, #e9d5ff 100%);
        border-color: #c77dff;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: #667eea !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Metric values */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {
        border-radius: 10px;
        border: 2px solid #dee2e6;
        padding: 10px 12px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* User edited badge */
    .user-edited-badge {
        background: linear-gradient(135deg, #0dcaf0 0%, #0891b2 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: bold;
        margin-right: 8px;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(13, 202, 240, 0.3);
    }
    
    /* Session status badges */
    .session-completed {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid #28a745;
        padding: 12px;
        margin: 8px 0;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.2);
    }
    
    .session-pending {
        background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
        border-left: 4px solid #ffc107;
        padding: 12px;
        margin: 8px 0;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(255, 193, 7, 0.2);
    }
    
    .session-locked {
        background: linear-gradient(135deg, #e2e3e5 0%, #d6d8db 100%);
        border-left: 4px solid #6c757d;
        padding: 12px;
        margin: 8px 0;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(108, 117, 125, 0.2);
    }
    
    /* Event type indicators */
    .event-activity {
        border-left: 5px solid #667eea;
        padding-left: 12px;
        margin: 8px 0;
    }
    
    .event-school {
        border-left: 5px solid #f59e0b;
        padding-left: 12px;
        margin: 8px 0;
    }
    
    .event-compulsory {
        border-left: 5px solid #dc3545;
        padding-left: 12px;
        margin: 8px 0;
    }
    
    .event-break {
        border-left: 5px solid #6c757d;
        padding-left: 12px;
        margin: 8px 0;
        opacity: 0.7;
    }
    
    /* Happening now indicator */
    .happening-now {
        animation: pulse 2s infinite;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        display: inline-block;
        font-weight: 700;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
            transform: scale(1);
        }
        50% {
            opacity: 0.8;
            transform: scale(1.05);
        }
    }
    
    /* Slider styling */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 1rem;
    }
    
    h2, h3 {
        color: #4a0080;
        font-weight: 700;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #c77dff 50%, transparent 100%);
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 12px;
        border-left: 5px solid #667eea;
        padding: 1rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Success message */
    .stSuccess {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important;
        border-left: 5px solid #28a745 !important;
    }
    
    /* Error message */
    .stError {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important;
        border-left: 5px solid #dc3545 !important;
    }
    
    /* Warning message */
    .stWarning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%) !important;
        border-left: 5px solid #ffc107 !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
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
        loaded_school = load_from_firebase(st.session_state.user_id, 'school_schedule')  # NEW
        loaded_timetable = load_from_firebase(st.session_state.user_id, 'timetable')
        loaded_progress = load_from_firebase(st.session_state.user_id, 'activity_progress')
        loaded_sessions = load_from_firebase(st.session_state.user_id, 'session_completion')  # NEW
        loaded_pending = load_from_firebase(st.session_state.user_id, 'pending_verifications')
        loaded_edits = load_from_firebase(st.session_state.user_id, 'user_edits')  # NEW
        loaded_month = load_from_firebase(st.session_state.user_id, 'current_month')
        loaded_year = load_from_firebase(st.session_state.user_id, 'current_year')
        
        if loaded_activities:
            st.session_state.list_of_activities = loaded_activities
        if loaded_events:
            st.session_state.list_of_compulsory_events = loaded_events
        if loaded_school:  # NEW
            st.session_state.school_schedule = loaded_school
        if loaded_timetable:
            st.session_state.timetable = loaded_timetable
        if loaded_progress:
            st.session_state.activity_progress = loaded_progress
        if loaded_sessions:  # NEW
            st.session_state.session_completion = loaded_sessions
        if loaded_pending:
            st.session_state.pending_verifications = loaded_pending
        if loaded_edits:  # NEW
            st.session_state.user_edits = loaded_edits
        if loaded_month:
            st.session_state.current_month = loaded_month
        if loaded_year:
            st.session_state.current_year = loaded_year
        
        st.session_state.data_loaded = True


# ==================== LOGIN SCREEN ====================
if not st.session_state.user_id:
    # Center everything with beautiful design
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0;'>
        <h1 style='font-size: 4rem; margin-bottom: 0.5rem;'>🕛</h1>
        <h1 style='font-size: 3rem; font-weight: 800; 
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   margin-bottom: 1rem;'>
            NERO-Time
        </h1>
        <p style='font-size: 1.2rem; color: #6c757d; margin-bottom: 2rem;'>
            Your intelligent time management companion
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='background: white; padding: 2rem; border-radius: 20px; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    border: 2px solid rgba(102, 126, 234, 0.2);'>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 👋 Welcome back!")
        st.markdown("Enter your email to continue")
        
        user_input = st.text_input("Email Address", placeholder="your.email@example.com", label_visibility="collapsed")
        
        if st.button("🚀 Sign In", type="primary", use_container_width=True):
            if user_input:
                with st.spinner("Logging in..."):
                    result = NeroTimeLogic.login_user(user_input)
                if result["success"]:
                    st.success("✓ " + result["message"])
                    st.balloons()
                    import time
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("✗ " + result["message"])
            else:
                st.error("📧 Please enter your email address")
        
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem; padding-top: 1rem; 
                    border-top: 2px solid rgba(102, 126, 234, 0.1);'>
            <p style='color: #6c757d; font-size: 0.9rem;'>
                ✨ Manage your activities • 📚 Track school schedule • 🎯 Meet deadlines
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()


# ==================== MAIN APP ====================
# Beautiful header
st.markdown("""
<div style='text-align: center; padding: 1rem 0 2rem 0;'>
    <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🕛 NERO-Time</h1>
</div>
""", unsafe_allow_html=True)

# User info and quick stats
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

# Calculate stats
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
    st.metric("📝 Activities", total_activities, help="Total active activities")
with col_stat2:
    st.metric("✅ Sessions Done", f"{completed_sessions}/{total_sessions}", help="Completed vs total sessions")
with col_stat3:
    st.metric("⏱️ Hours Logged", f"{total_hours_completed:.1f}h", help="Total hours completed")
with col_stat4:
    completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    st.metric("📊 Completion", f"{completion_rate:.0f}%", help="Overall completion rate")

st.caption(f"👤 Logged in as: **{st.session_state.user_id}**")
st.divider()

# Navigation - MODIFIED: Added School Schedule tab
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Activities", "Events", "School Schedule", "Settings"])


# ==================== DASHBOARD TAB ====================
with tab1:
# Month navigation - Centered layout
    dashboard_data = NeroTimeLogic.get_dashboard_data()
    col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 2, 1, 2, 1])
    
    with col2:
        if st.button("◀ Prev", use_container_width=True):
            result = NeroTimeLogic.navigate_month("prev")
            if result["success"]:
                st.rerun()
    
    with col3:
        # Month display with calendar popup
        import calendar
        cal = calendar.monthcalendar(dashboard_data['year'], st.session_state.current_month)
        
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
        
        current_day = datetime.now().day if (st.session_state.current_month == datetime.now().month and 
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
        
    with col4:
        if st.button("Next ▶", use_container_width=True):
            result = NeroTimeLogic.navigate_month("next")
            if result["success"]:
                st.rerun()
    
    with col6:
        if st.button("Today", use_container_width=True):
            result = NeroTimeLogic.navigate_month("today")
            if result["success"]:
                st.rerun()
    
    st.divider()
    
    # Quick actions with enhanced styling
    st.markdown("### ⚡ Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("🎯 Generate Timetable", expanded=True):
            st.markdown("**Configure your timetable generation settings:**")
            
            col_a, col_b = st.columns(2)
            with col_a:
                min_session = st.number_input("⏱️ Min session (minutes)", 15, 180, 30, 15, 
                                             help="Minimum duration for each study session")
            with col_b:
                max_session = st.number_input("⏱️ Max session (minutes)", 30, 240, 120, 15,
                                             help="Maximum duration for each study session")
            
            st.info(f"💡 Sessions will be between {min_session}-{max_session} minutes")
            
            if st.button("✨ Generate Timetable", type="primary", use_container_width=True):
                # Check if there's anything to schedule
                if st.session_state.list_of_activities or st.session_state.list_of_compulsory_events or st.session_state.school_schedule:
                    with st.spinner("🔮 Generating your personalized timetable..."):
                        import time
                        time.sleep(0.5)  # Brief pause for UX
                        result = NeroTimeLogic.generate_timetable(min_session, max_session)
                    if result["success"]:
                        st.success("✓ " + result["message"])
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("✗ " + result["message"])
                else:
                    st.warning("⚠️ Add activities, events, or school schedule first")
    
    with col2:
        st.markdown("#### 💾 Data Management")
        
        if st.button("💾 Save All Data", use_container_width=True, type="primary"):
            with st.spinner("Saving..."):
                result = NeroTimeLogic.save_all_data()
            if result["success"]:
                st.success("✓ " + result["message"])
            else:
                st.error("✗ " + result["message"])
        
        st.markdown("---")
        
        # Show last save info
        st.caption("💡 **Tip:** Data is auto-saved when you generate timetable")
        
        # Quick stats about current month
        num_events_today = 0
        today_display = dashboard_data.get('current_day', '')
        if today_display and today_display in dashboard_data.get('timetable', {}):
            num_events_today = len(dashboard_data['timetable'][today_display])
        
        st.metric("📅 Events Today", num_events_today)
    
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
                            # NEW: Get completion and edit status
                            is_completed = event.get('is_completed', False)
                            is_user_edited = event.get('is_user_edited', False)
                            
                            # Show happening now badge
                            if is_current_slot:
                                st.markdown('<div class="happening-now">🟢 HAPPENING NOW</div>', unsafe_allow_html=True)
                            
                            # Create event container
                            st.markdown('<div class="event-activity">', unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([0.85, 0.15])
                            with col1:
                                # Show edit badge
                                badge_html = ""
                                if is_user_edited:
                                    badge_html = '<span class="user-edited-badge">✏️ EDITED</span>'
                                
                                # Show completion status with icon
                                if is_completed:
                                    st.markdown(f"{badge_html}**✅ {event['start']} - {event['end']}:** {event['name']}", unsafe_allow_html=True)
                                    st.caption("✓ Session completed")
                                else:
                                    st.markdown(f"{badge_html}**🔵 {event['start']} - {event['end']}:** {event['name']}", unsafe_allow_html=True)
                                
                                # Beautiful progress bar
                                st.progress(progress['percentage'] / 100)
                                
                                # Progress info with icons
                                progress_pct = progress['percentage']
                                if progress_pct == 100:
                                    icon = "🎉"
                                elif progress_pct >= 75:
                                    icon = "🔥"
                                elif progress_pct >= 50:
                                    icon = "💪"
                                elif progress_pct >= 25:
                                    icon = "📈"
                                else:
                                    icon = "🚀"
                                
                                st.caption(f"{icon} {progress['completed']:.1f}h / {progress['total']}h ({progress_pct:.0f}%)")
                            
                            with col2:
                                # Show done or verify button based on completion
                                if is_completed:
                                    st.markdown("**✓** Done", unsafe_allow_html=True)
                                elif can_verify:
                                    if st.button("✓ Verify", key=f"verify_{day_display}_{idx}", use_container_width=True, type="primary"):
                                        result = NeroTimeLogic.verify_session(day_display, idx)
                                        if result["success"]:
                                            st.success(result["message"])
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            st.error(result["message"])
                                else:
                                    st.caption("⏳ Future")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # NEW: Handle SCHOOL event type
                        elif event["type"] == "SCHOOL":
                            if is_current_slot:
                                st.markdown('<div class="happening-now">🟢 HAPPENING NOW</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-school">', unsafe_allow_html=True)
                            st.markdown(f"**🏫 {event['start']} - {event['end']}:** {event['name']}")
                            duration = (time_str_to_minutes(event['end']) - time_str_to_minutes(event['start'])) / 60
                            st.caption(f"📚 School class ({duration:.1f}h)")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        elif event["type"] == "COMPULSORY":
                            if is_current_slot:
                                st.markdown('<div class="happening-now">🟢 HAPPENING NOW</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-compulsory">', unsafe_allow_html=True)
                            st.markdown(f"**🔴 {event['start']} - {event['end']}:** {event['name']}")
                            duration = (time_str_to_minutes(event['end']) - time_str_to_minutes(event['start'])) / 60
                            st.caption(f"📅 Compulsory event ({duration:.1f}h)")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        else:  # BREAK
                            if is_current_slot:
                                st.markdown('<div class="happening-now">🟢 BREAK TIME</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="event-break">', unsafe_allow_html=True)
                            st.markdown(f"*⚪ {event['start']} - {event['end']}: {event['name']}*")
                            st.markdown('</div>', unsafe_allow_html=True)
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
        
        st.write("**Session Timing Preferences**")
        col3, col4 = st.columns(2)
        with col3:
            min_session_min = st.number_input("Min session (minutes)", 15, 180, 30, 15, key="add_min_session")
        with col4:
            max_session_min = st.number_input("Max session (minutes)", 30, 240, 120, 15, key="add_max_session")
            # Ensure max is always >= min
            if max_session_min < min_session_min:
                max_session_min = min_session_min
        
        # NEW: Add day preferences
        st.write("**Day Preferences (Optional)**")
        from Timetable_Generation import WEEKDAY_NAMES
        allowed_days = st.multiselect(
            "Which days can this activity be scheduled?",
            options=WEEKDAY_NAMES,
            default=WEEKDAY_NAMES,
            help="Select which weekdays this activity can be scheduled on"
        )
        
        if st.button("Add Activity", use_container_width=True, type="primary"):
            if activity_name:
                # Add activity with allowed days
                result = NeroTimeLogic.add_activity(
                    activity_name, priority, deadline_date.isoformat(), 
                    timing, min_session_min, max_session_min, allowed_days
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
            # NEW: Get session data
            sessions_data = act.get('sessions_data', [])
            
            with st.expander(f"{idx+1}. {act['activity']} ({progress['completed']:.1f}h / {act['timing']}h)"):
                st.progress(progress['percentage'] / 100)
                st.write(f"⭐ Priority: {act['priority']} | ⏰ Deadline: {act['deadline']} days")
                
                if 'min_session_minutes' in act and 'max_session_minutes' in act and 'num_sessions' in act:
                    st.caption(f"📊 Session length: {act['min_session_minutes']}-{act['max_session_minutes']} minutes, Sessions: {act['num_sessions']}")
                
                # NEW: Show allowed days
                allowed_days = act.get('allowed_days', WEEKDAY_NAMES)
                st.caption(f"📅 Allowed days: {', '.join(allowed_days)}")
                
                # NEW: Edit allowed days
                if st.checkbox("Edit allowed days", key=f"edit_days_{idx}"):
                    new_allowed = st.multiselect(
                        "Select days",
                        options=WEEKDAY_NAMES,
                        default=allowed_days,
                        key=f"days_{idx}"
                    )
                    if st.button("Update Days", key=f"update_days_{idx}"):
                        result = NeroTimeLogic.update_allowed_days(act['activity'], new_allowed)
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                
                # NEW: Show sessions
                if sessions_data:
                    st.write("**Sessions:**")
                    for sess_idx, session in enumerate(sessions_data):
                        is_completed = session.get('is_completed', False)
                        is_locked = session.get('is_locked', False)
                        
                        with st.container():
                            col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
                            
                            with col_s1:
                                status = "✅ Completed" if is_completed else "⏳ Pending"
                                if is_locked:
                                    status += " 🔒"
                                
                                st.markdown(f"**Session {sess_idx + 1}:** {session['duration_hours']:.1f}h ({session['duration_minutes']}min) - {status}")
                                
                                if session.get('scheduled_day') and session.get('scheduled_time'):
                                    st.caption(f"Scheduled: {session['scheduled_day']} at {session['scheduled_time']}")
                            
                            with col_s2:
                                if st.button("✏️ Edit", key=f"edit_sess_{idx}_{sess_idx}", use_container_width=True):
                                    st.session_state[f'editing_{idx}_{sess_idx}'] = True
                                    st.rerun()
                            
                            with col_s3:
                                lock_label = "🔓 Unlock" if is_locked else "🔒 Lock"
                                if st.button(lock_label, key=f"lock_{idx}_{sess_idx}", use_container_width=True):
                                    result = NeroTimeLogic.edit_session(
                                        act['activity'],
                                        session['session_id'],
                                        lock=not is_locked
                                    )
                                    if result["success"]:
                                        st.rerun()
                        
                        # Edit interface
                        if st.session_state.get(f'editing_{idx}_{sess_idx}', False):
                            with st.form(key=f"form_{idx}_{sess_idx}"):
                                st.write("**Edit Session:**")
                                
                                # Find which day the session is currently on (if any)
                                current_day = session.get('scheduled_day')
                                if current_day and ' ' in current_day:
                                    # Extract weekday from "Monday 10/02" format
                                    current_weekday = current_day.split()[0]
                                    default_idx = WEEKDAY_NAMES.index(current_weekday) if current_weekday in WEEKDAY_NAMES else 0
                                else:
                                    default_idx = 0
                                
                                edit_day = st.selectbox("Day", options=WEEKDAY_NAMES, index=default_idx, key=f"day_{idx}_{sess_idx}")
                                
                                # Default time
                                current_time_str = session.get('scheduled_time', '09:00')
                                try:
                                    hour, minute = map(int, current_time_str.split(':'))
                                    default_time = time(hour, minute)
                                except:
                                    default_time = time(9, 0)
                                
                                edit_time = st.time_input("Start Time", value=default_time, key=f"time_{idx}_{sess_idx}")
                                edit_duration = st.number_input("Duration (minutes)", min_value=15, max_value=240, 
                                                               value=session['duration_minutes'], key=f"dur_{idx}_{sess_idx}")
                                
                                col_f1, col_f2 = st.columns(2)
                                with col_f1:
                                    if st.form_submit_button("Save Changes", use_container_width=True):
                                        result = NeroTimeLogic.edit_session(
                                            act['activity'],
                                            session['session_id'],
                                            new_day=edit_day,
                                            new_start_time=edit_time.strftime("%H:%M"),
                                            new_duration=edit_duration
                                        )
                                        if result["success"]:
                                            st.success(result["message"])
                                            st.session_state[f'editing_{idx}_{sess_idx}'] = False
                                            st.rerun()
                                        else:
                                            st.error(result["message"])
                                
                                with col_f2:
                                    if st.form_submit_button("Cancel", use_container_width=True):
                                        st.session_state[f'editing_{idx}_{sess_idx}'] = False
                                        st.rerun()
                
                st.divider()
                
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


# ==================== SCHOOL SCHEDULE TAB (NEW) ====================
with tab4:
    st.header("🏫 Manage Weekly School Schedule")
    st.caption("Add recurring weekly classes that appear every week")
    
    # Add school schedule
    with st.expander("➕ Add School Class", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            from Timetable_Generation import WEEKDAY_NAMES
            school_day = st.selectbox("Day of Week", options=WEEKDAY_NAMES)
            subject_name = st.text_input("Subject/Class Name", placeholder="e.g., Mathematics")
        
        with col2:
            school_start = st.time_input("Start Time", key="school_start")
            school_end = st.time_input("End Time", key="school_end")
        
        if st.button("Add to Schedule", use_container_width=True, type="primary"):
            if subject_name:
                result = NeroTimeLogic.add_school_schedule(
                    school_day,
                    school_start.strftime("%H:%M"),
                    school_end.strftime("%H:%M"),
                    subject_name
                )
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])
            else:
                st.error("Please enter a subject name")
    
    st.divider()
    
    # Display school schedule
    school_data = NeroTimeLogic.get_school_schedule()
    
    if school_data['schedule']:
        st.write("**Current Weekly Schedule:**")
        
        from Timetable_Generation import WEEKDAY_NAMES
        for day in WEEKDAY_NAMES:
            if day in school_data['schedule']:
                with st.expander(f"📅 {day} ({len(school_data['schedule'][day])} classes)"):
                    for idx, class_info in enumerate(school_data['schedule'][day]):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"**{class_info['subject']}**")
                            st.caption(f"🕐 {class_info['start_time']} - {class_info['end_time']}")
                        with col2:
                            if st.button("🗑️", key=f"del_school_{day}_{idx}", use_container_width=True):
                                result = NeroTimeLogic.delete_school_schedule(day, idx)
                                if result["success"]:
                                    st.success(result["message"])
                                    st.rerun()
                                else:
                                    st.error(result["message"])
    else:
        st.info("No school schedule added yet. Add your weekly classes above!")


# ==================== SETTINGS TAB (MOVED TO TAB5) ====================
with tab5:
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

"""
NERO-Time UI
"""
import pytz
import streamlit as st
from datetime import datetime
from nero_logic import NeroTimeLogic
from Firebase_Function import load_from_firebase
from css_style import css_scheme

# UI for each tab
from tabs.tab_dashboard import ui_dashboard_tab
from tabs.tab_activities import ui_activities_tab
from tabs.tab_events import ui_events_tab
from tabs.tab_verification import ui_verification_tab
from tabs.tab_achievements import ui_achievements_tab
from tabs.tab_settings import ui_settings_tab

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
        loaded_work_start = load_from_firebase(st.session_state.user_id, 'work_start_minutes')
        loaded_work_end   = load_from_firebase(st.session_state.user_id, 'work_end_minutes')

        if loaded_work_start is not None:
            st.session_state.work_start_minutes = loaded_work_start
        if loaded_work_end is not None:
            st.session_state.work_end_minutes = loaded_work_end
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

    if 'login_mode' not in st.session_state:
        st.session_state.login_mode = 'login'

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["Login", "Register"])

        with tab_login:
            st.markdown("### Welcome Back")

            login_username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            login_password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

            if st.button("Sign In", type="primary", use_container_width=True, key="btn_signin"):
                if login_username and login_password:
                    with st.spinner("Signing in..."):
                        from Firebase_Function import authenticate_user
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

        with tab_register:
            st.markdown("### Create Account")

            reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_username", help="Must be unique")
            reg_email = st.text_input("Email (optional)", placeholder="your.email@example.com", key="reg_email")
            reg_password = st.text_input("Password", type="password", placeholder="Choose a strong password", key="reg_password")
            reg_password_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password", key="reg_password_confirm")

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
                        from Firebase_Function import create_user
                        result = create_user(reg_username, reg_password, reg_email)

                    if result["success"]:
                        st.success("✓ " + result["message"])
                        st.info("You can now login with your credentials!")
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

# ==================== NAVIGATION TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Dashboard",
    "Activities",
    "Events & Schedule",
    "Verification",
    "Achievements",
    "Settings"
])

with tab1:
    ui_dashboard_tab()

with tab2:
    ui_activities_tab()

with tab3:
    ui_events_tab()

with tab4:
    ui_verification_tab()

with tab5:
    ui_achievements_tab(total_hours_completed, total_activities)

with tab6:
    ui_settings_tab()


# Auto-refresh for live clock (every 1 second)
st.markdown("""
<script>
    setTimeout(function() {
        window.parent.location.reload();
    }, 1000);
</script>
""", unsafe_allow_html=True)
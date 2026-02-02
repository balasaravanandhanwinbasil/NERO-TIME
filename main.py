import streamlit as st
import streamlit.components.v1 as components
import random
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import json
import re

# Initialize Firebase
from Firebase_Function import (init_firebase, save_to_firebase, load_from_firebase, 
                                save_timetable_snapshot, get_timetable_history)

# Constants
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
break_time = 2  # hours

st.markdown("""
<style>
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Base text readability */
    html, body, [class*="css"] {
        color: #2d1b3d;
    }

    /* Navigation container */
    .nav-container {
        display: flex;
        gap: 6px;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #f8e8ff, #fde2f3);
        padding: 8px;
        border-radius: 14px;
        box-shadow: 0 4px 10px rgba(180, 120, 200, 0.15);
    }

    .nav-tab {
        flex: 1;
        padding: 10px 16px;
        text-align: center;
        background: transparent;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 600;
        color: #6b3a8f;
        transition: all 0.2s ease;
    }

    .nav-tab:hover {
        background: rgba(255, 255, 255, 0.7);
        color: #4b216a;
    }

    .nav-tab.active {
        background: white;
        color: #8a2be2;
        box-shadow: 0 3px 8px rgba(138, 43, 226, 0.25);
    }

    /* Buttons */
    .stButton > button {
        font-size: 13px;
        padding: 8px 16px;
        border-radius: 10px;
        border: 1px solid #e6c7f2;
        background: #fff;
        color: #5a2b7a;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: #f6e6ff;
        border-color: #c77dff;
        color: #6a1bb9;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #c77dff, #ff8dc7);
        color: white;
        border: none;
    }

    .stButton > button[kind="primary"]:hover {
        filter: brightness(0.95);
    }

    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, #c77dff 0%, #ff8dc7 100%);
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
        color: #6a1bb9;
    }

    /* Cards */
    .element-container {
    background: transparent;
    border-radius: 0;
    box-shadow: none;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        font-size: 14px;
        font-weight: 600;
        background: linear-gradient(135deg, #f8e8ff, #fde2f3);
        border-radius: 10px;
        padding: 8px 12px;
        color: #4b216a;
    }

    /* Current time highlight */
    .current-time-highlight {
        background: #ffe4f2 !important;
        border: 2px solid #ff8dc7 !important;
    }

    /* Activity progress card */
    .activity-progress {
        background: #fdf1ff;
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
        border-left: 5px solid #c77dff;
        color: #3a1c52;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'timetable' not in st.session_state:
    st.session_state.timetable = {day: [] for day in DAY_NAMES}
if 'list_of_activities' not in st.session_state:
    st.session_state.list_of_activities = []
if 'list_of_compulsory_events' not in st.session_state:
    st.session_state.list_of_compulsory_events = []
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'activity_progress' not in st.session_state:
    st.session_state.activity_progress = {}  # {activity_name: hours_completed}

# Import helper functions
from Timetable_Generation import (time_str_to_minutes, minutes_to_time_str, add_minutes,
                                   is_time_slot_free, add_event_to_timetable, 
                                   get_day_activity_minutes, find_free_slot,
                                   place_compulsory_events, place_activities, 
                                   generate_timetable)

def get_current_time_slot():
    """Get current day and time slot"""
    now = datetime.now()
    day_index = now.weekday()
    if day_index < 5:  # Monday to Friday
        current_day = DAY_NAMES[day_index]
        current_time = now.strftime("%H:%M")
        return current_day, current_time
    return None, None

def update_activity_progress(activity_name, hours_to_add):
    """Update hours completed for an activity"""
    if activity_name not in st.session_state.activity_progress:
        st.session_state.activity_progress[activity_name] = 0
    st.session_state.activity_progress[activity_name] += hours_to_add
    save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)

def get_activity_progress_percent(activity_name, total_hours):
    """Get progress percentage for an activity"""
    completed = st.session_state.activity_progress.get(activity_name, 0)
    return min(completed / total_hours, 1.0) if total_hours > 0 else 0

def can_verify_event(event, day):
    """Check if event time has passed"""
    now = datetime.now()
    day_index = DAY_NAMES.index(day)
    current_day_index = now.weekday()
    
    # Event must be on a past day or earlier today
    if day_index < current_day_index:
        return True
    elif day_index == current_day_index:
        event_end = datetime.strptime(event['end'], "%H:%M").time()
        return now.time() > event_end
    return False

# Streamlit UI
st.set_page_config(page_title="NERO-TIME", page_icon="🕛", layout="wide")

# User authentication
if not st.session_state.user_id:
    st.title("🔐 Welcome")
    st.markdown("Please enter your user ID to continue")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_input = st.text_input("User ID", key="user_id_input", placeholder="email@example.com")
        if st.button("Login", type="primary", use_container_width=True):
            if user_input:
                st.session_state.user_id = user_input
                st.rerun()
            else:
                st.error("Please enter a user ID")
    st.stop()

# Load data from Firebase
if not st.session_state.data_loaded and st.session_state.user_id:
    with st.spinner("Loading..."):
        loaded_activities = load_from_firebase(st.session_state.user_id, 'activities')
        loaded_events = load_from_firebase(st.session_state.user_id, 'events')
        loaded_timetable = load_from_firebase(st.session_state.user_id, 'timetable')
        loaded_progress = load_from_firebase(st.session_state.user_id, 'activity_progress')
        
        if loaded_activities:
            st.session_state.list_of_activities = loaded_activities
        if loaded_events:
            st.session_state.list_of_compulsory_events = loaded_events
        if loaded_timetable:
            st.session_state.timetable = loaded_timetable
        if loaded_progress:
            st.session_state.activity_progress = loaded_progress
        
        st.session_state.data_loaded = True

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🕛 NERO-Time")
    st.caption(f"Logged in as: {st.session_state.user_id}")

# Navigation
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    if st.button("🏠 Dashboard", use_container_width=True, 
                 type="primary" if st.session_state.current_page == 'dashboard' else "secondary"):
        st.session_state.current_page = 'dashboard'
        st.rerun()

with nav_col2:
    if st.button("📝 Activities", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'activities' else "secondary"):
        st.session_state.current_page = 'activities'
        st.rerun()

with nav_col3:
    if st.button("🔴 Events", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'events' else "secondary"):
        st.session_state.current_page = 'events'
        st.rerun()

with nav_col4:
    if st.button("⚙️ Settings", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'settings' else "secondary"):
        st.session_state.current_page = 'settings'
        st.rerun()

st.divider()

# ==================== DASHBOARD PAGE ====================
if st.session_state.current_page == 'dashboard':
    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Generate Timetable", type="primary", use_container_width=True):
            if st.session_state.list_of_activities or st.session_state.list_of_compulsory_events:
                with st.spinner("Generating..."):
                    generate_timetable()
                st.success("✅ Timetable generated!")
                st.balloons()
                st.rerun()
            else:
                st.warning("Add activities or events first")
    
    with col2:
        if st.button("💾 Save Data", use_container_width=True):
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
            save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
            save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
            st.success("💾 Saved!")
    
    st.divider()
    
    # Display Timetable with current time highlight
    st.header("📊 Your Weekly Timetable")
    
    current_day, current_time = get_current_time_slot()
    
    if any(st.session_state.timetable[day] for day in DAY_NAMES):
        for day in DAY_NAMES:
            is_current_day = (day == current_day)
            with st.expander(f"{'🟢 ' if is_current_day else ''}📅 {day}", expanded=is_current_day):
                if not st.session_state.timetable[day]:
                    st.info("No events scheduled")
                else:
                    for idx, event in enumerate(st.session_state.timetable[day]):
                        # Check if this is the current time slot
                        is_current_slot = False
                        if is_current_day and current_time:
                            event_start = time_str_to_minutes(event['start'])
                            event_end = time_str_to_minutes(event['end'])
                            current_minutes = time_str_to_minutes(current_time)
                            is_current_slot = event_start <= current_minutes < event_end
                        
                        if event["type"] == "ACTIVITY":
                            # Extract base activity name (remove "Session X")
                            activity_name = event['name'].split(' (Session')[0]
                            
                            # Find total hours for this activity
                            activity_data = next((a for a in st.session_state.list_of_activities 
                                                 if a['activity'] == activity_name), None)
                            
                            if activity_data:
                                total_hours = activity_data['timing']
                                completed_hours = st.session_state.activity_progress.get(activity_name, 0)
                                
                                # Calculate session duration
                                session_duration = (time_str_to_minutes(event['end']) - 
                                                  time_str_to_minutes(event['start'])) / 60
                                
                                can_verify = can_verify_event(event, day)
                                
                                # Highlight current time slot
                                if is_current_slot:
                                    st.markdown(f"**🟢 HAPPENING NOW**")
                                
                                col1, col2 = st.columns([0.85, 0.15])
                                with col1:
                                    st.markdown(f"**🔵 {event['start']} - {event['end']}:** {event['name']}")
                                    
                                    # Progress bar for this activity
                                    progress = min(completed_hours / total_hours, 1.0)
                                    st.progress(progress)
                                    st.caption(f"{completed_hours:.1f}h / {total_hours}h completed")
                                
                                with col2:
                                    if can_verify:
                                        if st.button("✓", key=f"verify_{day}_{idx}", use_container_width=True):
                                            update_activity_progress(activity_name, session_duration)
                                            st.success(f"Added {session_duration:.1f}h")
                                            st.rerun()
                                    else:
                                        st.caption("⏳ Not yet")
                        
                        elif event["type"] == "COMPULSORY":
                            if is_current_slot:
                                st.markdown(f"**🟢 HAPPENING NOW**")
                            st.markdown(f"**🔴 {event['start']} - {event['end']}:** {event['name']}")
                        
                        else:  # BREAK
                            if is_current_slot:
                                st.markdown(f"**🟢 BREAK TIME**")
                            st.markdown(f"*⚪ {event['start']} - {event['end']}: {event['name']}*")
    else:
        st.info("No timetable generated yet")

# ==================== ACTIVITIES PAGE ====================
elif st.session_state.current_page == 'activities':
    st.header("📝 Manage Activities")
    
    # Add new activity
    with st.expander("➕ Add New Activity", expanded=True):
        with st.form("new_activity_form"):
            activity_name = st.text_input("Activity Name")
            col1, col2 = st.columns(2)
            with col1:
                priority = st.slider("Priority", 1, 5, 3)
                deadline_date = st.date_input("Deadline", min_value=datetime.now().date())
            with col2:
                timing = st.number_input("Total Hours", min_value=1, max_value=24, value=1)
            
            if st.form_submit_button("Add Activity", use_container_width=True):
                if activity_name:
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    deadline_datetime = datetime.combine(deadline_date, datetime.min.time())
                    days_left = (deadline_datetime - today).days
                    
                    st.session_state.list_of_activities.append({
                        "activity": activity_name,
                        "priority": priority,
                        "deadline": days_left,
                        "timing": timing
                    })
                    
                    save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                    st.success(f"✅ Added: {activity_name}")
                    st.rerun()
    
    st.divider()
    
    # List activities with progress
    if st.session_state.list_of_activities:
        for idx, act in enumerate(st.session_state.list_of_activities):
            completed_hours = st.session_state.activity_progress.get(act['activity'], 0)
            progress = get_activity_progress_percent(act['activity'], act['timing'])
            
            with st.expander(f"{idx+1}. {act['activity']} ({completed_hours:.1f}h / {act['timing']}h)"):
                st.progress(progress)
                st.write(f"⭐ Priority: {act['priority']} | ⏰ Deadline: {act['deadline']} days")
                
                col1, col2, col3 = st.columns(3)
                
                if col1.button("✏️ Edit", key=f"edit_act_{idx}", use_container_width=True):
                    st.session_state.edit_activity_index = idx
                    st.rerun()
                
                if col2.button("🗑️ Delete", key=f"del_act_{idx}", use_container_width=True):
                    # Remove from progress tracking too
                    if act['activity'] in st.session_state.activity_progress:
                        del st.session_state.activity_progress[act['activity']]
                    st.session_state.list_of_activities.pop(idx)
                    save_to_firebase(st.session_state.user_id, "activities", st.session_state.list_of_activities)
                    save_to_firebase(st.session_state.user_id, "activity_progress", st.session_state.activity_progress)
                    st.success("Deleted!")
                    st.rerun()
                
                if col3.button("🔄 Reset Progress", key=f"reset_{idx}", use_container_width=True):
                    st.session_state.activity_progress[act['activity']] = 0
                    save_to_firebase(st.session_state.user_id, "activity_progress", st.session_state.activity_progress)
                    st.success("Reset!")
                    st.rerun()
    else:
        st.info("No activities added yet")

# ==================== EVENTS PAGE ====================
elif st.session_state.current_page == 'events':
    st.header("🔴 Manage Compulsory Events")
    
    # Add new event
    with st.expander("➕ Add New Event", expanded=True):
        with st.form("new_event_form"):
            event_name = st.text_input("Event Name")
            event_day = st.selectbox("Day", DAY_NAMES)
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
            with col2:
                end_time = st.time_input("End Time", value=datetime.strptime("10:00", "%H:%M").time())
            
            if st.form_submit_button("Add Event", use_container_width=True):
                if event_name:
                    start_str = start_time.strftime("%H:%M")
                    end_str = end_time.strftime("%H:%M")
                    
                    if time_str_to_minutes(end_str) > time_str_to_minutes(start_str):
                        st.session_state.list_of_compulsory_events.append({
                            "event": event_name,
                            "start_time": start_str,
                            "end_time": end_str,
                            "day": event_day
                        })
                        
                        save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
                        st.success(f"✅ Added: {event_name}")
                        st.rerun()
    
    st.divider()
    
    # List events
    if st.session_state.list_of_compulsory_events:
        for idx, evt in enumerate(st.session_state.list_of_compulsory_events):
            with st.expander(f"{idx+1}. {evt['event']} - {evt['day']}"):
                st.write(f"🕐 {evt['start_time']} - {evt['end_time']}")
                
                col1, col2 = st.columns(2)
                
                if col1.button("✏️ Edit", key=f"edit_evt_{idx}", use_container_width=True):
                    st.session_state.edit_event_index = idx
                    st.rerun()
                
                if col2.button("🗑️ Delete", key=f"del_evt_{idx}", use_container_width=True):
                    st.session_state.list_of_compulsory_events.pop(idx)
                    save_to_firebase(st.session_state.user_id, "events", st.session_state.list_of_compulsory_events)
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.info("No events added yet")

# ==================== SETTINGS PAGE ====================
elif st.session_state.current_page == 'settings':
    st.header("⚙️ Settings")
    
    tab1, tab2 = st.tabs(["📜 History", "👤 Account"])
    
    with tab1:
        st.subheader("Timetable History")
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        
        history = get_timetable_history(st.session_state.user_id)
        if history:
            for idx, snapshot in enumerate(history):
                with st.expander(f"Snapshot {idx + 1}"):
                    if 'created_at' in snapshot and snapshot['created_at']:
                        st.caption(f"Created: {snapshot['created_at']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Activities", len(snapshot.get('activities', [])))
                    with col2:
                        st.metric("Events", len(snapshot.get('events', [])))
                    
                    if st.button("Restore", key=f"restore_{idx}", use_container_width=True):
                        st.session_state.timetable = snapshot.get('timetable', {day: [] for day in DAY_NAMES})
                        st.session_state.list_of_activities = snapshot.get('activities', [])
                        st.session_state.list_of_compulsory_events = snapshot.get('events', [])
                        
                        save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
                        save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                        save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
                        
                        st.success("Restored!")
                        st.rerun()
        else:
            st.info("No history available")
    
    with tab2:
        st.subheader("Account Settings")
        
        st.write(f"**User ID:** {st.session_state.user_id}")
        
        st.divider()
        
        if st.button("🚪 Logout", type="primary", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.data_loaded = False
            st.rerun()
        
        st.divider()
        
        if st.button("⚠️ Clear All Data", use_container_width=True):
            st.session_state.list_of_activities = []
            st.session_state.list_of_compulsory_events = []
            st.session_state.timetable = {day: [] for day in DAY_NAMES}
            st.session_state.activity_progress = {}
            
            save_to_firebase(st.session_state.user_id, 'activities', [])
            save_to_firebase(st.session_state.user_id, 'events', [])
            save_to_firebase(st.session_state.user_id, 'timetable', {day: [] for day in DAY_NAMES})
            save_to_firebase(st.session_state.user_id, 'activity_progress', {})
            
            st.warning("All data cleared!")
            st.rerun()

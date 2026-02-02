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

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        font-weight: 600;
        font-size: 15px;
        padding: 12px 24px;
        border-radius: 8px;
        border: 2px solid;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-color: #667eea;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-color: #f093fb;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
    }
    
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
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
if 'completed_tasks' not in st.session_state:
    st.session_state.completed_tasks = set()

# Import helper functions
from Timetable_Generation import (time_str_to_minutes, minutes_to_time_str, add_minutes,
                                   is_time_slot_free, add_event_to_timetable, 
                                   get_day_activity_minutes, find_free_slot,
                                   place_compulsory_events, place_activities, 
                                   generate_timetable)

# Helper function for progress
def calculate_progress():
    """Calculate overall progress based on completed tasks"""
    total_tasks = 0
    completed = 0
    
    for day in DAY_NAMES:
        for event in st.session_state.timetable[day]:
            if event["type"] in ["ACTIVITY", "COMPULSORY"]:
                total_tasks += 1
                event_id = f"{day}_{event['start']}_{event['name']}"
                if event_id in st.session_state.completed_tasks:
                    completed += 1
    
    if total_tasks == 0:
        return 0.0
    return completed / total_tasks

def mark_task_complete(day, event):
    """Mark a task as complete"""
    event_id = f"{day}_{event['start']}_{event['name']}"
    if event_id in st.session_state.completed_tasks:
        st.session_state.completed_tasks.remove(event_id)
    else:
        st.session_state.completed_tasks.add(event_id)
    
    # Save to Firebase
    save_to_firebase(st.session_state.user_id, 'completed_tasks', 
                     list(st.session_state.completed_tasks))

# Streamlit UI
st.set_page_config(page_title="Timetable Generator", page_icon="📅", layout="wide")

# User authentication
if not st.session_state.user_id:
    st.title("🔐 Welcome to Timetable Generator")
    st.markdown("Please enter your user ID to continue")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_input = st.text_input("User ID (email or username)", key="user_id_input")
        if st.button("Login", type="primary", use_container_width=True):
            if user_input:
                st.session_state.user_id = user_input
                st.rerun()
            else:
                st.error("Please enter a user ID")
    st.stop()

# Load data from Firebase
if not st.session_state.data_loaded and st.session_state.user_id:
    with st.spinner("Loading your data..."):
        loaded_activities = load_from_firebase(st.session_state.user_id, 'activities')
        loaded_events = load_from_firebase(st.session_state.user_id, 'events')
        loaded_timetable = load_from_firebase(st.session_state.user_id, 'timetable')
        loaded_completed = load_from_firebase(st.session_state.user_id, 'completed_tasks')
        
        if loaded_activities:
            st.session_state.list_of_activities = loaded_activities
        if loaded_events:
            st.session_state.list_of_compulsory_events = loaded_events
        if loaded_timetable:
            st.session_state.timetable = loaded_timetable
        if loaded_completed:
            st.session_state.completed_tasks = set(loaded_completed)
        
        st.session_state.data_loaded = True

# Header with navigation
col1, col2, col3 = st.columns([2, 3, 1])
with col1:
    st.title("📅 Timetable Manager")
with col2:
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    with nav_col1:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    with nav_col2:
        if st.button("📝 Manage Items", use_container_width=True):
            st.session_state.current_page = 'manage'
            st.rerun()
    with nav_col3:
        if st.button("📜 History", use_container_width=True):
            st.session_state.current_page = 'history'
            st.rerun()
with col3:
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.data_loaded = False
        st.rerun()

st.markdown(f"**Logged in as:** {st.session_state.user_id}")
st.divider()

# ==================== DASHBOARD PAGE ====================
if st.session_state.current_page == 'dashboard':
    # Progress Section
    st.header("📊 Your Progress")
    progress = calculate_progress()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.progress(progress)
        st.caption(f"{int(progress * 100)}% Complete")
    with col2:
        completed_count = len(st.session_state.completed_tasks)
        total_count = sum(len([e for e in st.session_state.timetable[day] 
                               if e["type"] in ["ACTIVITY", "COMPULSORY"]]) 
                         for day in DAY_NAMES)
        st.metric("✅ Completed", f"{completed_count}/{total_count}")
    with col3:
        st.metric("📝 Activities", len(st.session_state.list_of_activities))
    
    st.divider()
    
    # Generate Timetable Section
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Generate Timetable", type="primary", use_container_width=True):
            if st.session_state.list_of_activities or st.session_state.list_of_compulsory_events:
                with st.spinner("⏳ Generating your optimized timetable..."):
                    generate_timetable()
                st.success("✅ Timetable generated and saved!")
                st.balloons()
                st.rerun()
            else:
                st.warning("⚠️ Please add at least one activity or event!")
    
    with col2:
        if st.button("💾 Save Current Data", type="secondary", use_container_width=True):
            with st.spinner("Saving..."):
                save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
                save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
                save_to_firebase(st.session_state.user_id, 'completed_tasks', list(st.session_state.completed_tasks))
            st.success("💾 Data saved to Firebase!")
    
    # Display Timetable
    st.header("📊 Your Weekly Timetable")
    
    if any(st.session_state.timetable[day] for day in DAY_NAMES):
        # Timetable with checkboxes
        for day in DAY_NAMES:
            with st.expander(f"📅 {day}", expanded=True):
                if not st.session_state.timetable[day]:
                    st.info("No events scheduled")
                else:
                    for idx, event in enumerate(st.session_state.timetable[day]):
                        if event["type"] in ["ACTIVITY", "COMPULSORY"]:
                            event_id = f"{day}_{event['start']}_{event['name']}"
                            is_completed = event_id in st.session_state.completed_tasks
                            
                            col1, col2 = st.columns([0.1, 0.9])
                            with col1:
                                if st.checkbox("✓", value=is_completed, key=f"check_{day}_{idx}"):
                                    if not is_completed:
                                        st.session_state.completed_tasks.add(event_id)
                                        save_to_firebase(st.session_state.user_id, 'completed_tasks', 
                                                       list(st.session_state.completed_tasks))
                                else:
                                    if is_completed:
                                        st.session_state.completed_tasks.remove(event_id)
                                        save_to_firebase(st.session_state.user_id, 'completed_tasks', 
                                                       list(st.session_state.completed_tasks))
                            
                            with col2:
                                emoji = "🔴" if event["type"] == "COMPULSORY" else "🔵"
                                text_style = "~~" if is_completed else ""
                                if event["type"] == "COMPULSORY":
                                    st.markdown(f"{text_style}**{emoji} {event['start']} - {event['end']}:** :red[{event['name']}]{text_style}")
                                else:
                                    st.markdown(f"{text_style}**{emoji} {event['start']} - {event['end']}:** :blue[{event['name']}]{text_style}")
                        else:
                            st.markdown(f"*⚪ {event['start']} - {event['end']}: {event['name']}*")
    else:
        st.info("📝 No timetable generated yet. Add activities and events, then click '🚀 Generate Timetable'.")

# ==================== MANAGE PAGE ====================
elif st.session_state.current_page == 'manage':
    st.header("📝 Manage Activities & Events")
    
    tab1, tab2 = st.tabs(["📝 Activities", "🔴 Compulsory Events"])
    
    with tab1:
        st.subheader("Add New Activity")
        with st.form("new_activity_form"):
            activity_name = st.text_input("Activity Name")
            col1, col2 = st.columns(2)
            with col1:
                priority = st.slider("Priority", 1, 5, 3)
                deadline_date = st.date_input("Deadline", min_value=datetime.now().date())
            with col2:
                timing = st.number_input("Total Hours Needed", min_value=1, max_value=24, value=1)
            
            if st.form_submit_button("➕ Add Activity", use_container_width=True):
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
                else:
                    st.error("Activity name cannot be empty!")
        
        st.divider()
        st.subheader("Current Activities")
        
        if st.session_state.list_of_activities:
            for idx, act in enumerate(st.session_state.list_of_activities):
                with st.expander(f"{idx+1}. {act['activity']} ({act['timing']}h)"):
                    st.write(f"⭐ Priority: {act['priority']} | ⏰ Deadline in {act['deadline']} days")
                    
                    col1, col2 = st.columns([1, 1])
                    
                    if col1.button("✏️ Edit", key=f"edit_act_{idx}", use_container_width=True):
                        st.session_state.edit_activity_index = idx
                        st.rerun()
                    
                    if col2.button("🗑️ Delete", key=f"del_act_{idx}", use_container_width=True):
                        st.session_state.list_of_activities.pop(idx)
                        save_to_firebase(st.session_state.user_id, "activities", st.session_state.list_of_activities)
                        st.success("Activity deleted!")
                        st.rerun()
                    
                    if st.session_state.get("edit_activity_index") == idx:
                        with st.form(f"edit_activity_form_{idx}"):
                            new_name = st.text_input("Activity Name", value=act["activity"])
                            new_priority = st.slider("Priority", 1, 5, value=act["priority"])
                            new_deadline = st.number_input("Deadline days", min_value=0, max_value=30, value=act["deadline"])
                            new_timing = st.number_input("Total Hours", min_value=1, max_value=24, value=act["timing"])
                            
                            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                st.session_state.list_of_activities[idx] = {
                                    "activity": new_name,
                                    "priority": new_priority,
                                    "deadline": new_deadline,
                                    "timing": new_timing
                                }
                                save_to_firebase(st.session_state.user_id, "activities", st.session_state.list_of_activities)
                                st.success("✅ Activity updated!")
                                st.session_state.edit_activity_index = None
                                st.rerun()
        else:
            st.info("No activities added yet.")
    
    with tab2:
        st.subheader("Add New Compulsory Event")
        with st.form("new_event_form"):
            event_name = st.text_input("Event Name")
            event_day = st.selectbox("Day", DAY_NAMES)
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
            with col2:
                end_time = st.time_input("End Time", value=datetime.strptime("10:00", "%H:%M").time())
            
            if st.form_submit_button("➕ Add Event", use_container_width=True):
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
                    else:
                        st.error("End time must be after start time!")
                else:
                    st.error("Event name cannot be empty!")
        
        st.divider()
        st.subheader("Current Events")
        
        if st.session_state.list_of_compulsory_events:
            for idx, evt in enumerate(st.session_state.list_of_compulsory_events):
                with st.expander(f"{idx+1}. {evt['event']} ({evt['day']} {evt['start_time']}-{evt['end_time']})"):
                    col1, col2 = st.columns([1, 1])
                    
                    if col1.button("✏️ Edit", key=f"edit_evt_{idx}", use_container_width=True):
                        st.session_state.edit_event_index = idx
                        st.rerun()
                    
                    if col2.button("🗑️ Delete", key=f"del_evt_{idx}", use_container_width=True):
                        st.session_state.list_of_compulsory_events.pop(idx)
                        save_to_firebase(st.session_state.user_id, "events", st.session_state.list_of_compulsory_events)
                        st.success("Event deleted!")
                        st.rerun()
                    
                    if st.session_state.get("edit_event_index") == idx:
                        with st.form(f"edit_event_form_{idx}"):
                            new_name = st.text_input("Event Name", value=evt["event"])
                            new_day = st.selectbox("Day", DAY_NAMES, index=DAY_NAMES.index(evt["day"]))
                            new_start = st.time_input("Start Time", value=datetime.strptime(evt["start_time"], "%H:%M").time())
                            new_end = st.time_input("End Time", value=datetime.strptime(evt["end_time"], "%H:%M").time())
                            
                            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                st.session_state.list_of_compulsory_events[idx] = {
                                    "event": new_name,
                                    "day": new_day,
                                    "start_time": new_start.strftime("%H:%M"),
                                    "end_time": new_end.strftime("%H:%M")
                                }
                                save_to_firebase(st.session_state.user_id, "events", st.session_state.list_of_compulsory_events)
                                st.success("✅ Event updated!")
                                st.session_state.edit_event_index = None
                                st.rerun()
        else:
            st.info("No events added yet.")

# ==================== HISTORY PAGE ====================
elif st.session_state.current_page == 'history':
    st.header("📜 Timetable History")
    
    if st.button("🔄 Refresh History", use_container_width=True):
        st.rerun()
    
    history = get_timetable_history(st.session_state.user_id)
    if history:
        for idx, snapshot in enumerate(history):
            with st.expander(f"📸 Snapshot {idx + 1}", expanded=(idx == 0)):
                if 'created_at' in snapshot and snapshot['created_at']:
                    st.caption(f"Created: {snapshot['created_at']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📝 Activities", len(snapshot.get('activities', [])))
                with col2:
                    st.metric("🔴 Events", len(snapshot.get('events', [])))
                
                if st.button("🔄 Restore This Snapshot", key=f"restore_{idx}"):
                    st.session_state.timetable = snapshot.get('timetable', {day: [] for day in DAY_NAMES})
                    st.session_state.list_of_activities = snapshot.get('activities', [])
                    st.session_state.list_of_compulsory_events = snapshot.get('events', [])
                    
                    save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
                    save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                    save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
                    
                    st.success("✅ Snapshot restored!")
                    st.rerun()
    else:
        st.info("No history available. Generate a timetable to create your first snapshot!")

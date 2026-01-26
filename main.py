import streamlit as st
import random
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import json

@st.cache_resource
def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.Certificate('firebase-credentials.json')
            firebase_admin.initialize_app(cred)
        except FileNotFoundError:
            cred_dict = {
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key_id": st.secrets["firebase"]["private_key_id"],
                "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
                "client_email": st.secrets["firebase"]["client_email"],
                "client_id": st.secrets["firebase"]["client_id"],
                "auth_uri": st.secrets["firebase"]["auth_uri"],
                "token_uri": st.secrets["firebase"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
break_time = 2

# -------------------------------
# Session state init
# -------------------------------
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

# Page state
if 'page' not in st.session_state:
    st.session_state.page = "main"  # main, edit_activity, edit_event

if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

# -------------------------------
# Firebase helper functions
# -------------------------------
def save_to_firebase(user_id, data_type, data):
    try:
        doc_ref = db.collection('users').document(user_id).collection(data_type).document('current')
        doc_ref.set({'data': data, 'updated_at': firestore.SERVER_TIMESTAMP})
        return True
    except Exception as e:
        st.error(f"Error saving to Firebase: {e}")
        return False

def load_from_firebase(user_id, data_type):
    try:
        doc_ref = db.collection('users').document(user_id).collection(data_type).document('current')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get('data', None)
        return None
    except Exception as e:
        st.error(f"Error loading from Firebase: {e}")
        return None

def save_timetable_snapshot(user_id, timetable, activities, events):
    try:
        snapshot_data = {
            'timetable': timetable,
            'activities': activities,
            'events': events,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        db.collection('users').document(user_id).collection('timetable_history').add(snapshot_data)
        return True
    except Exception as e:
        st.error(f"Error saving snapshot: {e}")
        return False

def get_timetable_history(user_id, limit=10):
    try:
        docs = db.collection('users').document(user_id).collection('timetable_history')\
            .order_by('created_at', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        return [{'id': doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Error loading history: {e}")
        return []

# -------------------------------
# Helper functions
# -------------------------------
def time_str_to_minutes(time_str):
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

def minutes_to_time_str(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def add_minutes(time_str, minutes_to_add):
    total_minutes = time_str_to_minutes(time_str) + minutes_to_add
    if total_minutes >= 1440:
        total_minutes = 1439
    return minutes_to_time_str(total_minutes)

def is_time_slot_free(day, start_time, end_time):
    start_mins = time_str_to_minutes(start_time)
    end_mins = time_str_to_minutes(end_time)

    for event in st.session_state.timetable[day]:
        event_start = time_str_to_minutes(event["start"])
        event_end = time_str_to_minutes(event["end"])
        if not (end_mins <= event_start or start_mins >= event_end):
            return False
    return True

def add_event_to_timetable(day, start_time, end_time, event_name, event_type):
    st.session_state.timetable[day].append({
        "start": start_time,
        "end": end_time,
        "name": event_name,
        "type": event_type
    })
    st.session_state.timetable[day].sort(key=lambda x: time_str_to_minutes(x["start"]))

def get_day_activity_minutes(day):
    total_minutes = 0
    for event in st.session_state.timetable[day]:
        if event["type"] == "ACTIVITY":
            start_mins = time_str_to_minutes(event["start"])
            end_mins = time_str_to_minutes(event["end"])
            total_minutes += (end_mins - start_mins)
    return total_minutes

def get_available_days_until_deadline(deadline_days):
    available_days = []
    current_day_index = datetime.now().weekday()

    for day_offset in range(deadline_days + 1):
        day_index = (current_day_index + day_offset) % 7
        if day_index < 5:
            available_days.append(DAY_NAMES[day_index])
    return available_days

def find_free_slot(day, duration_minutes, start_hour=6, end_hour=22):
    attempts = []
    for hour in range(start_hour, end_hour):
        for minute in [0, 15, 30, 45]:
            start_time = f"{hour:02d}:{minute:02d}"
            end_time = add_minutes(start_time, duration_minutes)

            if time_str_to_minutes(end_time) > end_hour * 60:
                continue

            break_end = add_minutes(end_time, break_time * 60)
            if is_time_slot_free(day, start_time, break_end):
                attempts.append((start_time, end_time))

    if attempts:
        random.shuffle(attempts)
        return attempts[0]
    return None

def place_compulsory_events():
    for event in st.session_state.list_of_compulsory_events:
        day = event["day"]
        start_time = event["start_time"]
        end_time = event["end_time"]

        add_event_to_timetable(day, start_time, end_time, event["event"], "COMPULSORY")

        break_end = add_minutes(end_time, break_time * 60)
        if time_str_to_minutes(break_end) < 1440:
            add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")

def place_activities():
    MAX_ACTIVITY_MINUTES_PER_DAY = 6 * 60

    randomized_activities = st.session_state.list_of_activities.copy()
    random.shuffle(randomized_activities)

    for activity in randomized_activities:
        total_duration_hours = activity["timing"]
        deadline_days = activity["deadline"]

        if total_duration_hours == 0:
            continue

        available_days = get_available_days_until_deadline(deadline_days)
        if not available_days:
            st.warning(f"Activity '{activity['activity']}' has no available days before deadline.")
            continue

        total_duration_minutes = total_duration_hours * 60
        remaining_minutes = total_duration_minutes
        session_number = 1

        while remaining_minutes > 0:
            if remaining_minutes <= 60:
                chunk_minutes = remaining_minutes
            else:
                chunk_minutes = random.randint(45, 60)
                if remaining_minutes - chunk_minutes < 30:
                    chunk_minutes = remaining_minutes

            placed = False
            available_days_shuffled = available_days.copy()
            random.shuffle(available_days_shuffled)

            for day in available_days_shuffled:
                current_minutes = get_day_activity_minutes(day)
                if current_minutes + chunk_minutes > MAX_ACTIVITY_MINUTES_PER_DAY:
                    continue

                slot = find_free_slot(day, chunk_minutes)

                if slot:
                    start_time, end_time = slot
                    activity_label = activity['activity']
                    if total_duration_hours > 1:
                        activity_label += f" (Session {session_number})"

                    add_event_to_timetable(day, start_time, end_time, activity_label, "ACTIVITY")

                    break_end = add_minutes(end_time, break_time * 60)
                    if time_str_to_minutes(break_end) < 1440:
                        add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")

                    remaining_minutes -= chunk_minutes
                    session_number += 1
                    placed = True
                    break

            if not placed:
                st.warning(f"Could not place {chunk_minutes} minutes of '{activity['activity']}'")
                break

def generate_timetable():
    st.session_state.timetable = {day: [] for day in DAY_NAMES}
    place_compulsory_events()
    place_activities()

    if st.session_state.user_id:
        save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
        save_timetable_snapshot(
            st.session_state.user_id,
            st.session_state.timetable,
            st.session_state.list_of_activities,
            st.session_state.list_of_compulsory_events
        )

def delete_item(list_name, index):
    if list_name == "activities":
        st.session_state.list_of_activities.pop(index)
        save_to_firebase(st.session_state.user_id, "activities", st.session_state.list_of_activities)
    elif list_name == "events":
        st.session_state.list_of_compulsory_events.pop(index)
        save_to_firebase(st.session_state.user_id, "events", st.session_state.list_of_compulsory_events)

# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="Timetable Generator", page_icon="📅", layout="wide")

# Login
if not st.session_state.user_id:
    st.title("🔐 Welcome to Timetable Generator")
    st.markdown("Please enter your user ID to continue")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_input = st.text_input("User ID (email or username)", key="user_id_input")
        if st.button("Login", type="primary", use_container_width=True):
            if user_input:
                st.session_state.user_id = user_input
                st.session_state.data_loaded = False
                st.experimental_rerun()
            else:
                st.error("Please enter a user ID")
    st.stop()

# Load data from Firebase once
if not st.session_state.data_loaded and st.session_state.user_id:
    with st.spinner("Loading your data..."):
        loaded_activities = load_from_firebase(st.session_state.user_id, 'activities')
        loaded_events = load_from_firebase(st.session_state.user_id, 'events')
        loaded_timetable = load_from_firebase(st.session_state.user_id, 'timetable')

        if loaded_activities:
            st.session_state.list_of_activities = loaded_activities
        if loaded_events:
            st.session_state.list_of_compulsory_events = loaded_events
        if loaded_timetable:
            st.session_state.timetable = loaded_timetable

        st.session_state.data_loaded = True

# Header
st.title("📅 Smart Timetable Generator")
st.markdown(f"**Logged in as:** {st.session_state.user_id}")

# -------------------------------
# Edit Activity Page
# -------------------------------
if st.session_state.page == "edit_activity":
    idx = st.session_state.edit_index
    act = st.session_state.list_of_activities[idx]

    st.subheader("✏️ Edit Activity")

    with st.form("edit_activity_form"):
        new_name = st.text_input("Activity Name", value=act["activity"])
        new_priority = st.slider("Priority", 1, 5, value=act["priority"])
        new_deadline = st.number_input("Deadline (days left)", min_value=0, max_value=365, value=act["deadline"])
        new_timing = st.number_input("Total Hours Needed", min_value=1, max_value=24, value=act["timing"])

        if st.form_submit_button("Save Changes"):
            st.session_state.list_of_activities[idx] = {
                "activity": new_name,
                "priority": new_priority,
                "deadline": new_deadline,
                "timing": new_timing
            }
            save_to_firebase(st.session_state.user_id, "activities", st.session_state.list_of_activities)
            st.success("Activity updated!")
            st.session_state.page = "main"

    # <-- BACK BUTTON OUTSIDE FORM
    if st.button("⬅️ Back"):
        st.session_state.page = "main"

    st.stop()


# -------------------------------
# Edit Event Page
# -------------------------------
if st.session_state.page == "edit_event":
    idx = st.session_state.edit_index
    evt = st.session_state.list_of_compulsory_events[idx]

    st.subheader("✏️ Edit Event")

    with st.form("edit_event_form"):
        new_name = st.text_input("Event Name", value=evt["event"])
        new_day = st.selectbox("Day", DAY_NAMES, index=DAY_NAMES.index(evt["day"]))
        new_start = st.time_input("Start Time", value=datetime.strptime(evt["start_time"], "%H:%M").time())
        new_end = st.time_input("End Time", value=datetime.strptime(evt["end_time"], "%H:%M").time())

        if st.form_submit_button("Save Changes"):
            start_str = new_start.strftime("%H:%M")
            end_str = new_end.strftime("%H:%M")

            if time_str_to_minutes(end_str) > time_str_to_minutes(start_str):
                st.session_state.list_of_compulsory_events[idx] = {
                    "event": new_name,
                    "start_time": start_str,
                    "end_time": end_str,
                    "day": new_day
                }
                save_to_firebase(st.session_state.user_id, "events", st.session_state.list_of_compulsory_events)
                st.success("Event updated!")
                st.session_state.page = "main"
            else:
                st.error("End time must be after start time!")

    # <-- BACK BUTTON OUTSIDE FORM
    if st.button("⬅️ Back"):
        st.session_state.page = "main"

    st.stop()

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.data_loaded = False
        st.session_state.page = "main"
        st.stop()

    st.divider()
    tab1, tab2, tab3 = st.tabs(["📝 Activity", "🔴 Event", "📜 History"])

    # Activity Tab
    with tab1:
        st.subheader("Add Activity")
        with st.form("activity_form"):
            activity_name = st.text_input("Activity Name")
            priority = st.slider("Priority", 1, 5, 3)
            deadline_date = st.date_input("Deadline", min_value=datetime.now().date())
            timing = st.number_input("Total Hours Needed", min_value=1, max_value=24, value=1)

            if st.form_submit_button("Add Activity"):
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
                    st.success(f"Added: {activity_name}")
                else:
                    st.error("Activity name cannot be empty!")

        if st.session_state.list_of_activities:
            st.subheader("📝 Current Activities")
            for i, act in enumerate(st.session_state.list_of_activities):
                with st.expander(f"{i+1}. {act['activity']}"):
                    st.write(f"Priority: {act['priority']}")
                    st.write(f"Deadline (days left): {act['deadline']}")
                    st.write(f"Timing: {act['timing']}h")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Edit Activity", key=f"edit_act_{i}"):
                            st.session_state.edit_index = i
                            st.session_state.page = "edit_activity"
                    with col2:
                        if st.button("Delete Activity", key=f"del_act_{i}"):
                            delete_item("activities", i)

    # Event Tab
    with tab2:
        st.subheader("Add Compulsory Event")
        with st.form("event_form"):
            event_name = st.text_input("Event Name")
            event_day = st.selectbox("Day", DAY_NAMES)
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
            with col2:
                end_time = st.time_input("End Time", value=datetime.strptime("10:00", "%H:%M").time())

            if st.form_submit_button("Add Event"):
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
                        st.success(f"Added: {event_name}")
                    else:
                        st.error("End time must be after start time!")
                else:
                    st.error("Event name cannot be empty!")

        if st.session_state.list_of_compulsory_events:
            st.subheader("🔴 Current Events")
            for i, evt in enumerate(st.session_state.list_of_compulsory_events):
                with st.expander(f"{i+1}. {evt['event']}"):
                    st.write(f"Day: {evt['day']}")
                    st.write(f"Time: {evt['start_time']} - {evt['end_time']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Edit Event", key=f"edit_evt_{i}"):
                            st.session_state.edit_index = i
                            st.session_state.page = "edit_event"
                    with col2:
                        if st.button("Delete Event", key=f"del_evt_{i}"):
                            delete_item("events", i)

    # History Tab
    with tab3:
        st.subheader("Timetable History")
        if st.button("🔄 Refresh History"):
            st.experimental_rerun()

        history = get_timetable_history(st.session_state.user_id)
        if history:
            for idx, snapshot in enumerate(history):
                with st.expander(f"Snapshot {idx + 1}"):
                    if 'created_at' in snapshot and snapshot['created_at']:
                        st.caption(f"Created: {snapshot['created_at']}")
                    st.write(f"Activities: {len(snapshot.get('activities', []))}")
                    st.write(f"Events: {len(snapshot.get('events', []))}")
        else:
            st.info("No history available")

# -------------------------------
# Main content
# -------------------------------
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.metric("Activities Added", len(st.session_state.list_of_activities))
with col2:
    st.metric("Compulsory Events", len(st.session_state.list_of_compulsory_events))
with col3:
    if st.button("🗑️ Clear All", type="secondary"):
        st.session_state.list_of_activities = []
        st.session_state.list_of_compulsory_events = []
        st.session_state.timetable = {day: [] for day in DAY_NAMES}

        save_to_firebase(st.session_state.user_id, 'activities', [])
        save_to_firebase(st.session_state.user_id, 'events', [])
        save_to_firebase(st.session_state.user_id, 'timetable', {day: [] for day in DAY_NAMES})

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 Generate Timetable", type="primary", use_container_width=True):
        if st.session_state.list_of_activities or st.session_state.list_of_compulsory_events:
            generate_timetable()
            st.success("✅ Timetable generated and saved!")
        else:
            st.warning("Please add at least one activity or event!")

with col2:
    if st.button("💾 Save Current Data", type="secondary", use_container_width=True):
        save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
        save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
        save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
        st.success("💾 Data saved to Firebase!")

st.header("📊 Your Weekly Timetable")

if any(st.session_state.timetable[day] for day in DAY_NAMES):
    st.subheader("📈 Weekly Summary")

import streamlit as st
import random
from datetime import datetime, timedelta

# Constants
VALID_SUBJECTS = ["Math", "English", "Mother Tongue", "Cygames Glazing"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Configuration
break_time = 2  # hours

# Initialize session state
if 'timetable' not in st.session_state:
    st.session_state.timetable = {day: [] for day in DAY_NAMES}
if 'list_of_activities' not in st.session_state:
    st.session_state.list_of_activities = []
if 'list_of_compulsory_events' not in st.session_state:
    st.session_state.list_of_compulsory_events = []

# Helper functions
def time_str_to_minutes(time_str):
    """Convert HH:MM to minutes since midnight."""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

def minutes_to_time_str(minutes):
    """Convert minutes since midnight to HH:MM."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def add_minutes(time_str, minutes_to_add):
    """Add minutes to a time string."""
    total_minutes = time_str_to_minutes(time_str) + minutes_to_add
    if total_minutes >= 1440:
        total_minutes = 1439
    return minutes_to_time_str(total_minutes)

def is_time_slot_free(day, start_time, end_time):
    """Check if a time slot is free on a given day."""
    start_mins = time_str_to_minutes(start_time)
    end_mins = time_str_to_minutes(end_time)

    for event in st.session_state.timetable[day]:
        event_start = time_str_to_minutes(event["start"])
        event_end = time_str_to_minutes(event["end"])
        if not (end_mins <= event_start or start_mins >= event_end):
            return False
    return True

def add_event_to_timetable(day, start_time, end_time, event_name, event_type):
    """Add an event to the timetable."""
    st.session_state.timetable[day].append({
        "start": start_time,
        "end": end_time,
        "name": event_name,
        "type": event_type
    })
    st.session_state.timetable[day].sort(key=lambda x: time_str_to_minutes(x["start"]))

def get_day_activity_minutes(day):
    """Calculate total minutes of activities on a day."""
    total_minutes = 0
    for event in st.session_state.timetable[day]:
        if event["type"] == "ACTIVITY":
            start_mins = time_str_to_minutes(event["start"])
            end_mins = time_str_to_minutes(event["end"])
            total_minutes += (end_mins - start_mins)
    return total_minutes

def get_available_days_until_deadline(deadline_days):
    """Get list of available weekdays until deadline."""
    available_days = []
    current_day_index = datetime.now().weekday()

    for day_offset in range(deadline_days + 1):
        day_index = (current_day_index + day_offset) % 7
        if day_index < 5:
            available_days.append(DAY_NAMES[day_index])
    return available_days

def find_free_slot(day, duration_minutes, start_hour=6, end_hour=22):
    """Find a free slot on a given day."""
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
    """Place compulsory events in the timetable."""
    for event in st.session_state.list_of_compulsory_events:
        day = event["day"]
        start_time = event["start_time"]
        end_time = event["end_time"]

        add_event_to_timetable(day, start_time, end_time, event["event"], "COMPULSORY")

        break_end = add_minutes(end_time, break_time * 60)
        if time_str_to_minutes(break_end) < 1440:
            add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")

def place_activities():
    """Place activities in the timetable."""
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
    """Generate the complete timetable."""
    st.session_state.timetable = {day: [] for day in DAY_NAMES}
    place_compulsory_events()
    place_activities()

# Streamlit UI
st.set_page_config(page_title="Timetable Generator", page_icon="📅", layout="wide")

st.title("📅 Smart Timetable Generator")
st.markdown("Generate an optimized weekly timetable based on your activities and commitments!")

# Sidebar for inputs
with st.sidebar:
    st.header("⚙️ Configuration")
    
    tab1, tab2 = st.tabs(["📝 Add Activity", "🔴 Add Event"])
    
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
                    st.success(f"Added: {activity_name}")
                else:
                    st.error("Activity name cannot be empty!")
    
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
                        st.success(f"Added: {event_name}")
                    else:
                        st.error("End time must be after start time!")
                else:
                    st.error("Event name cannot be empty!")

# Main content
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
        st.rerun()

# Generate button
if st.button("🚀 Generate Timetable", type="primary", use_container_width=True):
    if st.session_state.list_of_activities or st.session_state.list_of_compulsory_events:
        generate_timetable()
        st.success("✅ Timetable generated successfully!")
    else:
        st.warning("Please add at least one activity or event!")

# Display timetable
st.header("📊 Your Weekly Timetable")

# Summary statistics
if any(st.session_state.timetable[day] for day in DAY_NAMES):
    st.subheader("📈 Weekly Summary")
    summary_cols = st.columns(5)
    
    for idx, day in enumerate(DAY_NAMES):
        total_minutes = sum(
            time_str_to_minutes(event["end"]) - time_str_to_minutes(event["start"])
            for event in st.session_state.timetable[day]
            if event["type"] in ["ACTIVITY", "COMPULSORY"]
        )
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        with summary_cols[idx]:
            st.metric(day, f"{hours}h {minutes}m" if total_minutes > 0 else "Free")

# Display each day
for day in DAY_NAMES:
    with st.expander(f"📅 {day}", expanded=True):
        if not st.session_state.timetable[day]:
            st.info("No events scheduled")
        else:
            for event in st.session_state.timetable[day]:
                type_colors = {
                    "COMPULSORY": "🔴",
                    "ACTIVITY": "🔵",
                    "BREAK": "⚪"
                }
                emoji = type_colors.get(event["type"], "")
                
                # Color coding
                if event["type"] == "COMPULSORY":
                    st.markdown(f"**{emoji} {event['start']} - {event['end']}:** :red[{event['name']}]")
                elif event["type"] == "ACTIVITY":
                    st.markdown(f"**{emoji} {event['start']} - {event['end']}:** :blue[{event['name']}]")
                else:
                    st.markdown(f"*{emoji} {event['start']} - {event['end']}: {event['name']}*")

# Display lists in sidebar
with st.sidebar:
    st.divider()
    
    if st.session_state.list_of_activities:
        st.subheader("📝 Current Activities")
        for i, act in enumerate(st.session_state.list_of_activities):
            st.markdown(f"{i+1}. **{act['activity']}** - {act['timing']}h (Priority: {act['priority']})")
    
    if st.session_state.list_of_compulsory_events:
        st.subheader("🔴 Current Events")
        for i, evt in enumerate(st.session_state.list_of_compulsory_events):
            st.markdown(f"{i+1}. **{evt['event']}** - {evt['day']} {evt['start_time']}-{evt['end_time']}")

import streamlit as st
from datetime import datetime, timedelta
import random

# Constants
current_year = datetime.datetime.now().year
LastDayOfYear = datetime.date(current_year, 12, 31).weekday()
ExtraDayOfYear = 6-LastDayOfYear
EntireYear = {}
Weeklimits = 1
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
def yearaccess(typeAccess):
    print("hi")
def get_month_days(year, month):
    """Get all days in a month with their weekday names."""
    from calendar import monthrange
    num_days = monthrange(year, month)[1]
    days = []
    for day in range(1, num_days + 1):
        date = datetime(year, month, day)
        if date.weekday() < 7:  # All days of the week
            day_name = WEEKDAY_NAMES[date.weekday()]
            days.append({
                'date': date,
                'day_name': day_name,
                'display': f"{day_name} {date.strftime('%d/%m')}"
            })
    return days

# Import Firebase functions
from Firebase_Function import save_to_firebase, save_timetable_snapshot

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

def get_available_days_until_deadline(deadline_days, month_days):
    """Get list of available days until deadline from month_days."""
    available_days = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    deadline = today + timedelta(days=deadline_days)
    
    for day_info in month_days:
        if today <= day_info['date'] <= deadline:
            available_days.append(day_info['display'])
    
    return available_days

def find_free_slot(day, duration_minutes, start_hour=6, end_hour=22, break_time=2):
    """Find a free slot on a given day, including space for break."""
    attempts = []
    break_minutes = break_time * 60

    for hour in range(start_hour, end_hour):
        for minute in [0, 15, 30, 45]:
            start_time = f"{hour:02d}:{minute:02d}"
            end_time = add_minutes(start_time, duration_minutes)

            if time_str_to_minutes(end_time) > end_hour * 60:
                continue

            # Check if both activity AND break can fit
            break_end = add_minutes(end_time, break_minutes)
            if time_str_to_minutes(break_end) >= 1440:  # Past midnight
                continue
                
            if is_time_slot_free(day, start_time, break_end):
                attempts.append((start_time, end_time))

    if attempts:
        random.shuffle(attempts)
        return attempts[0]
    return None

def place_compulsory_events(break_time=2):
    """Place compulsory events in the timetable."""
    for event in st.session_state.list_of_compulsory_events:
        day = event["day"]
        start_time = event["start_time"]
        end_time = event["end_time"]

        add_event_to_timetable(day, start_time, end_time, event["event"], "COMPULSORY")

        # Add break after compulsory event
        break_end = add_minutes(end_time, break_time * 60)
        if time_str_to_minutes(break_end) < 1440 and is_time_slot_free(day, end_time, break_end):
            add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")

def place_activities(break_time=2, month_days=None, min_session_minutes=30, max_session_minutes=120):
    """Place activities in the timetable with customizable session lengths."""
    MAX_ACTIVITY_MINUTES_PER_DAY = 6 * 60
    
    if month_days is None:
        # Fallback to current month if not provided
        now = datetime.now()
        month_days = get_month_days(now.year, now.month)

    randomized_activities = st.session_state.list_of_activities.copy()
    random.shuffle(randomized_activities)

    for activity in randomized_activities:
        total_duration_hours = activity["timing"]
        deadline_days = activity["deadline"]
        
        # Get custom session length if set
        custom_session_min = activity.get('min_session_minutes', min_session_minutes)
        custom_session_max = activity.get('max_session_minutes', max_session_minutes)

        if total_duration_hours == 0:
            continue

        available_days = get_available_days_until_deadline(deadline_days, month_days)
        if not available_days:
            st.warning(f"Activity '{activity['activity']}' has no available days before deadline.")
            continue

        total_duration_minutes = total_duration_hours * 60
        remaining_minutes = total_duration_minutes
        session_number = 1

        while remaining_minutes > 0:
            if remaining_minutes <= custom_session_min:
                chunk_minutes = remaining_minutes
            else:
                chunk_minutes = random.randint(custom_session_min, min(custom_session_max, remaining_minutes))
                if remaining_minutes - chunk_minutes < custom_session_min and remaining_minutes - chunk_minutes > 0:
                    chunk_minutes = remaining_minutes

            placed = False
            available_days_shuffled = available_days.copy()
            random.shuffle(available_days_shuffled)

            for day in available_days_shuffled:
                current_minutes = get_day_activity_minutes(day)
                if current_minutes + chunk_minutes > MAX_ACTIVITY_MINUTES_PER_DAY:
                    continue

                slot = find_free_slot(day, chunk_minutes, break_time=break_time)

                if slot:
                    start_time, end_time = slot
                    activity_label = activity['activity']
                    if total_duration_hours > 1:
                        activity_label += f" (Session {session_number})"

                    add_event_to_timetable(day, start_time, end_time, activity_label, "ACTIVITY")

                    # Add break after activity
                    break_end = add_minutes(end_time, break_time * 60)
                    if time_str_to_minutes(break_end) < 1440 and is_time_slot_free(day, end_time, break_end):
                        add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")

                    remaining_minutes -= chunk_minutes
                    session_number += 1
                    placed = True
                    break

            if not placed:
                st.warning(f"Could not place {chunk_minutes} minutes of '{activity['activity']}'")
                break

def check_expired_activities():
    """Check for activities past their deadline and prompt for verification."""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Initialize pending verifications if not exists
    if 'pending_verifications' not in st.session_state:
        st.session_state.pending_verifications = []
    
    expired_activities = []
    
    for activity in st.session_state.list_of_activities:
        deadline_date = today + timedelta(days=activity['deadline'])
        
        # Check if deadline has passed
        if now > deadline_date:
            activity_name = activity['activity']
            completed_hours = st.session_state.activity_progress.get(activity_name, 0)
            total_hours = activity['timing']
            
            # Only add to pending if not fully completed and not already pending
            if completed_hours < total_hours:
                if activity_name not in st.session_state.pending_verifications:
                    expired_activities.append({
                        'name': activity_name,
                        'completed': completed_hours,
                        'total': total_hours,
                        'deadline': activity['deadline']
                    })
                    st.session_state.pending_verifications.append(activity_name)
    
    return expired_activities

def remove_activity_from_timetable(activity_name):
    """Remove all sessions of an activity from the timetable."""
    for day in DAY_NAMES:
        st.session_state.timetable[day] = [
            event for event in st.session_state.timetable[day]
            if not (event['type'] == 'ACTIVITY' and event['name'].startswith(activity_name))
        ]

def generate_timetable(year=None, month=None):
    """Generate the complete timetable for a given month."""
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    # Get all days in the month
    month_days = get_month_days(year, month)
    
    # Initialize timetable with all days in the month
    st.session_state.timetable = {day['display']: [] for day in month_days}
    st.session_state.current_month = month
    st.session_state.current_year = year
    
    place_compulsory_events()
    place_activities(month_days=month_days)
    
    # Auto-save to Firebase after generation
    if st.session_state.user_id:
        save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
        save_to_firebase(st.session_state.user_id, 'current_month', month)
        save_to_firebase(st.session_state.user_id, 'current_year', year)
        save_timetable_snapshot(
            st.session_state.user_id,
            st.session_state.timetable,
            st.session_state.list_of_activities,
            st.session_state.list_of_compulsory_events
        )

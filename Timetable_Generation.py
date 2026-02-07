"""
Updated Timetable Generation with Session Support and School Schedules
"""

from datetime import datetime, timedelta, date
import streamlit as st
import random
from typing import Dict, List, Tuple

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

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

def get_month_days(year, month):
    """Get all days in a month with their weekday names."""
    from calendar import monthrange
    num_days = monthrange(year, month)[1]
    days = []
    for day in range(1, num_days + 1):
        date_obj = datetime(year, month, day)
        if date_obj.weekday() < 7:  # All days of the week
            day_name = WEEKDAY_NAMES[date_obj.weekday()]
            days.append({
                'date': date_obj,
                'day_name': day_name,
                'display': f"{day_name} {date_obj.strftime('%d/%m')}"
            })
    return days

def is_time_slot_free(day, start_time, end_time):
    """Check if a time slot is free on a given day."""
    if day not in st.session_state.timetable:
        return True
    
    start_mins = time_str_to_minutes(start_time)
    end_mins = time_str_to_minutes(end_time)

    for event in st.session_state.timetable[day]:
        event_start = time_str_to_minutes(event["start"])
        event_end = time_str_to_minutes(event["end"])
        if not (end_mins <= event_start or start_mins >= event_end):
            return False
    return True

def add_event_to_timetable(day, start_time, end_time, event_name, event_type, session_id=None):
    """Add an event to the timetable."""
    if day not in st.session_state.timetable:
        st.session_state.timetable[day] = []
    
    event_data = {
        "start": start_time,
        "end": end_time,
        "name": event_name,
        "type": event_type
    }
    
    if session_id:
        event_data["session_id"] = session_id
    
    st.session_state.timetable[day].append(event_data)
    st.session_state.timetable[day].sort(key=lambda x: time_str_to_minutes(x["start"]))

def get_day_activity_minutes(day):
    """Calculate total minutes of activities on a day."""
    if day not in st.session_state.timetable:
        return 0
    
    total_minutes = 0
    for event in st.session_state.timetable[day]:
        if event["type"] == "ACTIVITY":
            start_mins = time_str_to_minutes(event["start"])
            end_mins = time_str_to_minutes(event["end"])
            total_minutes += (end_mins - start_mins)
    return total_minutes

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

def place_school_schedules(month_days):
    """Place recurring weekly school schedules across all days in the month."""
    if not st.session_state.school_schedule:
        return
    
    for day_info in month_days:
        day_name = day_info['day_name']
        day_display = day_info['display']
        
        if day_name in st.session_state.school_schedule:
            for school_event in st.session_state.school_schedule[day_name]:
                add_event_to_timetable(
                    day_display,
                    school_event['start_time'],
                    school_event['end_time'],
                    school_event['subject'],
                    "SCHOOL"
                )

def place_compulsory_events(break_time=2):
    """Place one-time compulsory events in the timetable."""
    for event in st.session_state.list_of_compulsory_events:
        day = event["day"]
        start_time = event["start_time"]
        end_time = event["end_time"]

        add_event_to_timetable(day, start_time, end_time, event["event"], "COMPULSORY")

        # Add break after compulsory event
        break_end = add_minutes(end_time, break_time * 60)
        if time_str_to_minutes(break_end) < 1440 and is_time_slot_free(day, end_time, break_end):
            add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")

def get_available_days_for_activity(activity, month_days, deadline_days):
    """Get available days for an activity based on allowed days and deadline."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    deadline = today + timedelta(days=deadline_days)
    
    allowed_weekdays = activity.get('allowed_days', WEEKDAY_NAMES)
    available_days = []
    
    for day_info in month_days:
        if today <= day_info['date'] <= deadline:
            if day_info['day_name'] in allowed_weekdays:
                available_days.append(day_info['display'])
    
    return available_days

def place_user_edited_sessions(activity, month_days, warnings):
    """Place sessions that have been manually edited by the user first."""
    activity_name = activity['activity']
    placed_sessions = []
    
    for session in activity['sessions']:
        session_id = session['session_id']
        edit_key = f"{activity_name}_{session_id}"
        
        # Check if this session has user edits
        if edit_key in st.session_state.user_edits:
            edit = st.session_state.user_edits[edit_key]
            
            if edit.get('day') and edit.get('start_time'):
                day = edit['day']
                start_time = edit['start_time']
                duration = edit.get('duration', session['duration_minutes'])
                
                end_time = add_minutes(start_time, duration)
                
                # Try to place the edited session
                if is_time_slot_free(day, start_time, end_time):
                    session_label = f"{activity_name} (Session {session['session_id'].split('_')[-1]})"
                    add_event_to_timetable(day, start_time, end_time, session_label, "ACTIVITY", session_id)
                    
                    # Add break
                    break_end = add_minutes(end_time, 2 * 60)
                    if time_str_to_minutes(break_end) < 1440 and is_time_slot_free(day, end_time, break_end):
                        add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")
                    
                    placed_sessions.append(session_id)
                    
                    # Update session info
                    session['scheduled_day'] = day
                    session['scheduled_time'] = start_time
                else:
                    warnings.append(f"⚠️ User edit for {session_label} conflicts with existing schedule")
    
    return placed_sessions

def place_activity_sessions(activity, month_days, break_time=2, warnings=None):
    """Place all sessions of an activity in the timetable."""
    if warnings is None:
        warnings = []
    
    MAX_ACTIVITY_MINUTES_PER_DAY = 6 * 60
    
    activity_name = activity['activity']
    deadline_days = activity['deadline']
    sessions = activity.get('sessions', [])
    
    if not sessions:
        return warnings
    
    # First, place user-edited sessions
    placed_sessions = place_user_edited_sessions(activity, month_days, warnings)
    
    # Get available days
    available_days = get_available_days_for_activity(activity, month_days, deadline_days)
    
    if not available_days:
        warnings.append(f"❌ Activity '{activity_name}' has no available days before deadline")
        return warnings
    
    # Place remaining sessions
    for session in sessions:
        session_id = session['session_id']
        
        # Skip if already placed (user edit or locked)
        if session_id in placed_sessions or session.get('is_locked'):
            continue
        
        duration_minutes = session['duration_minutes']
        session_number = session_id.split('_')[-1]
        
        placed = False
        available_days_shuffled = available_days.copy()
        random.shuffle(available_days_shuffled)
        
        for day in available_days_shuffled:
            current_minutes = get_day_activity_minutes(day)
            if current_minutes + duration_minutes > MAX_ACTIVITY_MINUTES_PER_DAY:
                continue
            
            slot = find_free_slot(day, duration_minutes, break_time=break_time)
            
            if slot:
                start_time, end_time = slot
                session_label = f"{activity_name} (Session {session_number})"
                
                add_event_to_timetable(day, start_time, end_time, session_label, "ACTIVITY", session_id)
                
                # Update session info
                session['scheduled_day'] = day
                session['scheduled_time'] = start_time
                
                # Add break
                break_end = add_minutes(end_time, break_time * 60)
                if time_str_to_minutes(break_end) < 1440 and is_time_slot_free(day, end_time, break_end):
                    add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")
                
                placed = True
                break
        
        if not placed:
            warnings.append(f"⚠️ Could not schedule session {session_number} of '{activity_name}'")
    
    return warnings

def generate_timetable_with_sessions(year=None, month=None):
    """Generate the complete timetable with session support and school schedules."""
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    # Get all days in the month
    month_days = get_month_days(year, month)
    
    # Initialize timetable
    st.session_state.timetable = {day['display']: [] for day in month_days}
    st.session_state.current_month = month
    st.session_state.current_year = year
    
    warnings = []
    
    # 1. Place school schedules (recurring weekly)
    place_school_schedules(month_days)
    
    # 2. Place compulsory events (one-time)
    place_compulsory_events()
    
    # 3. Sort activities by priority and deadline
    sorted_activities = sorted(
        st.session_state.list_of_activities,
        key=lambda x: (x['priority'], x['deadline']),
        reverse=True
    )
    
    # 4. Place activity sessions
    for activity in sorted_activities:
        warnings = place_activity_sessions(activity, month_days, warnings=warnings)
    
    # Auto-save to Firebase
    if st.session_state.user_id:
        from Firebase_Function import save_to_firebase, save_timetable_snapshot
        save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
        save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
        save_to_firebase(st.session_state.user_id, 'current_month', month)
        save_to_firebase(st.session_state.user_id, 'current_year', year)
        save_timetable_snapshot(
            st.session_state.user_id,
            st.session_state.timetable,
            st.session_state.list_of_activities,
            st.session_state.list_of_compulsory_events
        )
    
    return {
        'success': True,
        'warnings': warnings if warnings else None
    }

"""
NERO-time timetable generator - FIXED VERSION
"""

from datetime import datetime, timedelta
import streamlit as st
import random
from typing import Dict, List, Tuple

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Time constraints
WORK_START_HOUR = 6  # 6:00 AM
WORK_END_HOUR = 23   # 11:00 PM
WORK_END_MINUTE = 30  # 11:30 PM
WORK_END_TOTAL_MINUTES = WORK_END_HOUR * 60 + WORK_END_MINUTE  # 1410 minutes

def time_str_to_minutes(time_str):
    """Convert HH:MM to minutes since midnight."""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

def minutes_to_time_str(minutes):
    """Convert minutes since midnight to HH:MM."""
    # FIX: Ensure minutes is an integer
    minutes = int(minutes)
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def add_minutes(time_str, minutes_to_add):
    """Add minutes to a time string."""
    total_minutes = time_str_to_minutes(time_str) + minutes_to_add
    if total_minutes >= 1440:
        total_minutes = 1439
    return minutes_to_time_str(total_minutes)

def round_to_15_minutes(minutes):
    """Round minutes to nearest 15-minute interval"""
    # FIX: Always return an integer
    return int(((minutes + 7) // 15) * 15)

def get_month_days(year, month):
    """Get all days in a month with their weekday names."""
    from calendar import monthrange
    num_days = monthrange(year, month)[1]
    days = []
    for day in range(1, num_days + 1):
        date_obj = datetime(year, month, day)
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

def add_event_to_timetable(day, start_time, end_time, event_name, event_type, activity_name=None, session_num=None):
    """Add an event to the timetable."""
    if day not in st.session_state.timetable:
        st.session_state.timetable[day] = []
    
    event_data = {
        "start": start_time,
        "end": end_time,
        "name": event_name,
        "type": event_type
    }
    
    if activity_name:
        event_data["activity_name"] = activity_name
    if session_num is not None:
        event_data["session_num"] = session_num
    
    st.session_state.timetable[day].append(event_data)
    st.session_state.timetable[day].sort(key=lambda x: time_str_to_minutes(x["start"]))

def find_free_slot(day, duration_minutes, break_minutes=30):
    """Find a free slot on a given day between 6 AM and 11:30 PM, including break."""
    # FIX: Ensure duration_minutes is an integer
    duration_minutes = int(duration_minutes)
    break_minutes = int(break_minutes)
    
    attempts = []
    
    for hour in range(WORK_START_HOUR, WORK_END_HOUR + 1):
        for minute in [0, 15, 30, 45]:
            start_minutes = hour * 60 + minute
            
            # Skip if we're starting too late
            if start_minutes < WORK_START_HOUR * 60:
                continue
            
            start_time = minutes_to_time_str(start_minutes)
            end_minutes = start_minutes + duration_minutes
            
            # Check if activity ends before cutoff (11:30 PM)
            if end_minutes > WORK_END_TOTAL_MINUTES:
                continue
            
            end_time = minutes_to_time_str(end_minutes)
            
            # Check if break fits before cutoff
            break_end_minutes = end_minutes + break_minutes
            if break_end_minutes > WORK_END_TOTAL_MINUTES:
                # Try without break if activity fits
                if is_time_slot_free(day, start_time, end_time):
                    attempts.append((start_time, end_time, False))  # No break
                continue
            
            break_end = minutes_to_time_str(break_end_minutes)
            
            # Check if both activity AND break can fit
            if is_time_slot_free(day, start_time, break_end):
                attempts.append((start_time, end_time, True))  # With break

    if attempts:
        random.shuffle(attempts)
        return attempts[0]
    return None

def place_school_schedules(month_days, today):
    """Place recurring weekly school schedules across all days in the month, starting from today."""
    if not st.session_state.school_schedule:
        return
    
    for day_info in month_days:
        # Only schedule from today onwards
        if day_info['date'].date() < today:
            continue
            
        day_name = day_info['day_name']
        day_display = day_info['display']
        
        if day_name in st.session_state.school_schedule:
            for school_event in st.session_state.school_schedule[day_name]:
                add_event_to_timetable(
                    day_display,
                    school_event['start_time'],
                    school_event['end_time'],
                    "School/Work",
                    "SCHOOL"
                )

def place_compulsory_events(today):
    """Place one-time compulsory events in the timetable, only from today onwards."""
    for event in st.session_state.list_of_compulsory_events:
        day = event["day"]
        start_time = event["start_time"]
        end_time = event["end_time"]
        
        # Parse the event date to check if it's in the future
        try:
            # Extract date from the day display format (e.g., "Monday 15/02")
            date_part = day.split()[-1]
            day_num, month_num = map(int, date_part.split('/'))
            # Use current year or session state year
            year = st.session_state.get('current_year', datetime.now().year)
            event_date = datetime(year, month_num, day_num).date()
            
            # Only add if event is today or in the future
            if event_date >= today:
                add_event_to_timetable(day, start_time, end_time, event["event"], "COMPULSORY")
        except:
            # If we can't parse the date, add it anyway (safer)
            add_event_to_timetable(day, start_time, end_time, event["event"], "COMPULSORY")

def get_available_days_for_activity(activity, month_days, today):
    """Get available days for an activity before its deadline, starting from today."""
    today_dt = datetime.combine(today, datetime.min.time())
    deadline_days = activity['deadline']
    deadline = today_dt + timedelta(days=deadline_days)
    
    allowed_weekdays = activity.get('allowed_days', WEEKDAY_NAMES)
    available_days = []
    
    for day_info in month_days:
        # Only include days from today onwards
        if today_dt <= day_info['date'] <= deadline:
            if day_info['day_name'] in allowed_weekdays:
                available_days.append({
                    'display': day_info['display'],
                    'date': day_info['date']
                })
    
    return available_days

def check_past_activities(activity, month_days, today, warnings):
    """
    Check if an activity has sessions that were supposed to happen before today.
    Prompt user to mark them as complete/incomplete and adjust accordingly.
    """
    activity_name = activity['activity']
    existing_sessions = activity.get('sessions', [])
    
    past_incomplete_sessions = []
    for session in existing_sessions:
        if session.get('is_completed', False):
            continue
            
        scheduled_date_str = session.get('scheduled_date')
        if not scheduled_date_str:
            continue
            
        try:
            scheduled_date = datetime.fromisoformat(scheduled_date_str).date()
            if scheduled_date < today:
                past_incomplete_sessions.append(session)
        except:
            pass
    
    if past_incomplete_sessions:
        warnings.append(
            f"⚠️ '{activity_name}' has {len(past_incomplete_sessions)} past incomplete session(s). "
            f"Please review and mark as complete in the Activities tab."
        )
        
        # Store these for potential UI prompts
        if 'past_incomplete_sessions' not in st.session_state:
            st.session_state.past_incomplete_sessions = {}
        st.session_state.past_incomplete_sessions[activity_name] = past_incomplete_sessions

def place_activity_sessions(activity, month_days, warnings, today):
    """
    Place activity sessions in the timetable, creating sessions as we schedule them.
    ONLY schedules from today onwards. Past sessions trigger completion prompts.
    Excludes already completed sessions when regenerating.
    """
    activity_name = activity['activity']
    total_hours = activity['timing']
    min_session = activity.get('min_session_minutes', 30)
    max_session = activity.get('max_session_minutes', 120)
    
    # Round to 15-minute intervals and ensure integers
    min_session = round_to_15_minutes(min_session)
    max_session = round_to_15_minutes(max_session)
    
    # Check for past incomplete sessions
    check_past_activities(activity, month_days, today, warnings)
    
    # Calculate remaining time based on completed sessions
    existing_sessions = activity.get('sessions', [])
    completed_hours = sum(s.get('duration_hours', 0) for s in existing_sessions if s.get('is_completed', False))
    
    # FIX: Ensure total_minutes is an integer
    total_minutes = int((total_hours - completed_hours) * 60)
    
    if total_minutes <= 0:
        warnings.append(f"✓ '{activity_name}': All hours already completed!")
        # Keep only completed sessions
        completed_sessions = [s for s in existing_sessions if s.get('is_completed', False)]
        return completed_sessions
    
    # Get available days before deadline (from today onwards)
    available_days = get_available_days_for_activity(activity, month_days, today)
    
    if not available_days:
        warnings.append(f"❌ '{activity_name}': No available days before deadline (starting from today)!")
        # Keep completed sessions
        completed_sessions = [s for s in existing_sessions if s.get('is_completed', False)]
        return completed_sessions
    
    # Track created sessions (start with completed sessions)
    sessions = [s for s in existing_sessions if s.get('is_completed', False)]
    session_count = len(sessions)  # Start counting from completed sessions
    remaining_minutes = total_minutes
    
    # Keep trying to place sessions until we run out of time or days
    max_attempts = len(available_days) * 10  # Allow multiple sessions per day
    attempt = 0
    day_index = 0
    
    while remaining_minutes > 0 and attempt < max_attempts:
        # Cycle through available days
        day_info = available_days[day_index % len(available_days)]
        day_display = day_info['display']
        
        # Determine chunk size for this slot
        chunk_size = min(remaining_minutes, max_session)
        chunk_size = max(chunk_size, min_session) if remaining_minutes >= min_session else remaining_minutes
        chunk_size = round_to_15_minutes(chunk_size)
        
        # Ensure minimum 15 minutes
        if chunk_size < 15:
            chunk_size = 15
        
        # Try to find a free slot
        slot = find_free_slot(day_display, chunk_size, break_minutes=30)
        
        if slot:
            start_time, end_time, has_break = slot
            session_count += 1
            session_id = f"{activity_name}_session_{session_count}"
            
            # Add activity to timetable
            session_label = f"{activity_name} (Session {session_count})"
            add_event_to_timetable(
                day_display, 
                start_time, 
                end_time, 
                session_label, 
                "ACTIVITY",
                activity_name=activity_name,
                session_num=session_count
            )
            
            # Create session object
            sessions.append({
                'session_id': session_id,
                'session_num': session_count,
                'scheduled_day': day_display,
                'scheduled_date': day_info['date'].isoformat(),
                'scheduled_time': start_time,
                'duration_minutes': chunk_size,
                'duration_hours': round(chunk_size / 60, 2),
                'is_completed': False,
                'is_locked': False
            })
            
            # Add break if it fits
            if has_break:
                break_start = end_time
                break_end = add_minutes(end_time, 30)
                add_event_to_timetable(day_display, break_start, break_end, "Break", "BREAK")
            
            remaining_minutes -= chunk_size
            
            # Try the same day again to fill it up more
            attempt += 1
        else:
            # No slot found on this day, try next day
            day_index += 1
            attempt += 1
            
            # If we've cycled through all days and still can't find slots, break
            if day_index >= len(available_days):
                break
    
    # Calculate new session count (excluding completed ones)
    new_sessions_count = session_count - sum(1 for s in existing_sessions if s.get('is_completed', False))
    
    # Check if we managed to fit everything
    if remaining_minutes > 0:
        warnings.append(
            f"⚠️ '{activity_name}': Could only schedule {(total_minutes - remaining_minutes)/60:.1f}h "
            f"of {(total_hours - completed_hours):.1f}h remaining before deadline. {remaining_minutes/60:.1f}h still needed!"
        )
    else:
        if completed_hours > 0:
            warnings.append(
                f"✓ '{activity_name}': {completed_hours:.1f}h already completed, "
                f"{(total_hours - completed_hours):.1f}h scheduled in {int(new_sessions_count)} new sessions"
            )
        else:
            warnings.append(f"✓ '{activity_name}': All {total_hours:.1f}h scheduled in {int(session_count)} sessions")
    
    return sessions

def generate_timetable_with_sessions(year=None, month=None):
    """Generate the complete timetable by fitting activities before their deadlines, starting from today."""
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    # Get today's date (no time component)
    today = datetime.now().date()
    
    # Get all days in the month
    month_days = get_month_days(year, month)
    
    # Initialize timetable
    st.session_state.timetable = {day['display']: [] for day in month_days}
    st.session_state.current_month = month
    st.session_state.current_year = year
    
    warnings = []
    
    # 1. Place school schedules (recurring weekly) - from today onwards
    place_school_schedules(month_days, today)
    
    # 2. Place compulsory events (one-time) - from today onwards
    place_compulsory_events(today)
    
    # 3. Sort activities by deadline (most urgent first), then by priority
    sorted_activities = sorted(
        st.session_state.list_of_activities,
        key=lambda x: (x['deadline'], -x['priority'])
    )
    
    # 4. Place each activity, creating and storing sessions (from today onwards)
    for activity in sorted_activities:
        sessions = place_activity_sessions(activity, month_days, warnings, today)
        
        # Store sessions in the activity
        activity['sessions'] = sessions
        activity['num_sessions'] = len(sessions)
    
    # Store warnings for UI display
    if warnings:
        st.session_state.timetable_warnings = warnings
    else:
        st.session_state.timetable_warnings = []
    
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
"""
NERO-Time Backend Logic - WITH SESSION EDITING
Updated to support individual session editing
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import random
import math

# Import from existing files
from Firebase_Function import (
    save_to_firebase, 
    load_from_firebase,
    save_timetable_snapshot, 
    get_timetable_history
)

from Timetable_Generation import (
    time_str_to_minutes,
    WEEKDAY_NAMES,
    get_month_days
)

# Import from timetable generation.py
try:
    from Timetable_Generation import (
        minutes_to_time_str,
        add_minutes,
        is_time_slot_free,
        add_event_to_timetable,
        get_day_activity_minutes,
        find_free_slot,
        place_compulsory_events,
        check_expired_activities,
        remove_activity_from_timetable,
    )
except ImportError:
    pass  # error fixer


class NeroTimeLogic:
    """
    Backend logic class for NERO-Time
    Handles all data operations and business logic
    """
    
    @staticmethod
    def initialize_session_state():
        """Initialize all session state variables"""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'current_year' not in st.session_state:
            st.session_state.current_year = datetime.now().year
        if 'current_month' not in st.session_state:
            st.session_state.current_month = datetime.now().month
        if 'timetable' not in st.session_state:
            st.session_state.timetable = {}
        if 'list_of_activities' not in st.session_state:
            st.session_state.list_of_activities = []
        if 'list_of_compulsory_events' not in st.session_state:
            st.session_state.list_of_compulsory_events = []
        if 'school_schedule' not in st.session_state:
            st.session_state.school_schedule = {}
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
        if 'activity_progress' not in st.session_state:
            st.session_state.activity_progress = {}
        if 'session_completion' not in st.session_state:
            st.session_state.session_completion = {}
        if 'pending_verifications' not in st.session_state:
            st.session_state.pending_verifications = []
        if 'user_edits' not in st.session_state:
            st.session_state.user_edits = {}
    
    @staticmethod
    def login_user(user_id: str) -> Dict:
        """Login user and load their data"""
        if not user_id:
            return {"success": False, "message": "User ID is required"}
        
        st.session_state.user_id = user_id
        
        # Load all user data from Firebase
        st.session_state.list_of_activities = load_from_firebase(user_id, 'activities') or []
        st.session_state.list_of_compulsory_events = load_from_firebase(user_id, 'events') or []
        st.session_state.school_schedule = load_from_firebase(user_id, 'school_schedule') or {}
        st.session_state.timetable = load_from_firebase(user_id, 'timetable') or {}
        st.session_state.activity_progress = load_from_firebase(user_id, 'activity_progress') or {}
        st.session_state.session_completion = load_from_firebase(user_id, 'session_completion') or {}
        st.session_state.pending_verifications = load_from_firebase(user_id, 'pending_verifications') or []
        st.session_state.user_edits = load_from_firebase(user_id, 'user_edits') or {}
        
        month = load_from_firebase(user_id, 'current_month')
        year = load_from_firebase(user_id, 'current_year')
        
        if month:
            st.session_state.current_month = month
        if year:
            st.session_state.current_year = year
        
        st.session_state.data_loaded = True
        
        return {"success": True, "message": f"Logged in as {user_id}"}
    
    @staticmethod
    def get_dashboard_data() -> Dict:
        """Get all data needed for dashboard"""
        month_days = get_month_days(st.session_state.current_year, st.session_state.current_month)
        current_day, current_time = NeroTimeLogic._get_current_time_slot()
        
        # Enrich timetable with verification status and progress
        enriched_timetable = {}
        for day_display, events in st.session_state.timetable.items():
            enriched_events = []
            for event in events:
                enriched_event = event.copy()
                if event['type'] == 'ACTIVITY':
                    activity_name = event['name'].split(' (Session')[0]
                    session_id = event.get('session_id', None)
                    enriched_event['can_verify'] = NeroTimeLogic._can_verify_event(event, day_display)
                    enriched_event['activity_name'] = activity_name
                    enriched_event['session_id'] = session_id
                    enriched_event['is_completed'] = NeroTimeLogic._is_session_completed(activity_name, session_id)
                    enriched_event['progress'] = NeroTimeLogic._get_activity_progress_data(activity_name)
                    enriched_event['session_duration'] = (
                        time_str_to_minutes(event['end']) - time_str_to_minutes(event['start'])
                    ) / 60
                    enriched_event['is_user_edited'] = NeroTimeLogic._is_user_edited(day_display, event)
                enriched_events.append(enriched_event)
            enriched_timetable[day_display] = enriched_events
        
        return {
            "month_name": datetime(st.session_state.current_year, st.session_state.current_month, 1).strftime("%B"),
            "year": st.session_state.current_year,
            "month": st.session_state.current_month,
            "month_days": month_days,
            "timetable": enriched_timetable,
            "current_day": current_day,
            "current_time": current_time,
            "expired_activities": NeroTimeLogic._get_expired_activities()
        }
    
    @staticmethod
    def get_activities_data() -> Dict:
        """Get activities with progress data"""
        enriched_activities = []
        for activity in st.session_state.list_of_activities:
            enriched = activity.copy()
            enriched['progress'] = NeroTimeLogic._get_activity_progress_data(activity['activity'])
            enriched['sessions_data'] = NeroTimeLogic._get_sessions_data(activity['activity'])
            enriched_activities.append(enriched)
        
        return {"activities": enriched_activities}
    
    @staticmethod
    def get_events_data() -> Dict:
        """Get events sorted by date"""
        sorted_events = sorted(
            st.session_state.list_of_compulsory_events,
            key=lambda x: x.get('date', '9999-12-31')
        )
        return {"events": sorted_events}
    
    @staticmethod
    def get_school_schedule() -> Dict:
        """Get weekly school schedule"""
        return {"schedule": st.session_state.school_schedule}
    
    @staticmethod
    def add_activity(name: str, priority: int, deadline_date: str, total_hours: int, 
                     min_session: int = 30, max_session: int = 120, 
                     allowed_days: List[str] = None) -> Dict:
        """Add a new activity"""
        try:
            if not name:
                return {"success": False, "message": "Activity name is required"}
            
            deadline_dt = datetime.fromisoformat(deadline_date)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_left = (deadline_dt.replace(hour=0, minute=0, second=0, microsecond=0) - today).days
            
            # Generate sessions with 15-minute multiples
            total_minutes = total_hours * 60
            avg_session = (min_session + max_session) / 2
            num_sessions = math.ceil(total_minutes / avg_session)
            
            session_list = []
            remaining_minutes = total_minutes
            
            for i in range(num_sessions):
                if i == num_sessions - 1:
                    # Last session gets remaining time, rounded to 15
                    session_duration = round(remaining_minutes / 15) * 15
                else:
                    max_possible = min(max_session, remaining_minutes)
                    min_possible = min(min_session, remaining_minutes)
                    session_duration = random.randint(min_possible, max_possible)
                    # Round to nearest 15 minutes
                    session_duration = round(session_duration / 15) * 15
                
                # Ensure minimum 15 minutes
                if session_duration < 15:
                    session_duration = 15
                
                session_list.append({
                    'session_id': f"{name}_session_{i+1}",
                    'duration_minutes': session_duration,
                    'duration_hours': round(session_duration / 60, 2),
                    'scheduled_day': None,
                    'scheduled_time': None,
                    'is_locked': False
                })
                
                remaining_minutes -= session_duration
            
            new_activity = {
                "activity": name,
                "priority": priority,
                "deadline": days_left,
                "timing": total_hours,
                "min_session_minutes": min_session,
                "max_session_minutes": max_session,
                "sessions": session_list,
                "allowed_days": allowed_days or WEEKDAY_NAMES,
                "num_sessions": num_sessions
            }
            
            st.session_state.list_of_activities.append(new_activity)
            
            # Initialize session completion tracking
            if name not in st.session_state.session_completion:
                st.session_state.session_completion[name] = {}
            
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            save_to_firebase(st.session_state.user_id, 'session_completion', st.session_state.session_completion)
            
            return {"success": True, "message": f"Activity '{name}' added with {num_sessions} sessions"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def edit_session(activity_name: str, session_id: str, new_day: str = None, 
                     new_start_time: str = None, new_duration: int = None, lock: bool = None,
                     new_date: str = None) -> Dict:
        """Edit a specific session of an activity and rebalance other sessions"""
        try:
            # Find the activity
            activity = next((a for a in st.session_state.list_of_activities 
                           if a['activity'] == activity_name), None)
            
            if not activity:
                return {"success": False, "message": "Activity not found"}
            
            # Check if deadline has passed
            if activity['deadline'] < 0:
                return {"success": False, "message": "Cannot edit - activity deadline has passed"}
            
            # Find the session
            session = next((s for s in activity['sessions'] if s['session_id'] == session_id), None)
            if not session:
                return {"success": False, "message": "Session not found"}
            
            # Check if session is completed
            if NeroTimeLogic._is_session_completed(activity_name, session_id):
                return {"success": False, "message": "Cannot edit completed session"}
            
            # Round duration to nearest 15 minutes if provided
            if new_duration is not None:
                new_duration = round(new_duration / 15) * 15
                if new_duration < 15:
                    new_duration = 15
            
            # Store old duration for rebalancing
            old_duration = session['duration_minutes']
            
            # Apply edits
            if new_day is not None:
                session['scheduled_day'] = new_day
            if new_start_time is not None:
                session['scheduled_time'] = new_start_time
            if new_duration is not None:
                session['duration_minutes'] = new_duration
                session['duration_hours'] = round(new_duration / 60, 2)
            if lock is not None:
                session['is_locked'] = lock
            if new_date is not None:
                session['scheduled_date'] = new_date
            
            # Rebalance other unedited, incomplete sessions if duration changed
            if new_duration is not None and new_duration != old_duration:
                # Calculate total required time (in minutes)
                total_required = activity['timing'] * 60
                
                # Calculate time from completed sessions
                completed_time = 0
                for sess in activity['sessions']:
                    sess_id = sess['session_id']
                    if NeroTimeLogic._is_session_completed(activity_name, sess_id):
                        completed_time += sess['duration_minutes']
                
                # Calculate time from locked/edited sessions (including this one)
                locked_time = 0
                unedited_sessions = []
                for sess in activity['sessions']:
                    sess_id = sess['session_id']
                    if not NeroTimeLogic._is_session_completed(activity_name, sess_id):
                        edit_key = f"{activity_name}_{sess_id}"
                        if sess_id == session_id or edit_key in st.session_state.user_edits:
                            locked_time += sess['duration_minutes']
                        else:
                            unedited_sessions.append(sess)
                
                # Calculate remaining time to distribute
                remaining_time = total_required - completed_time - locked_time
                
                if remaining_time > 0 and unedited_sessions:
                    # Distribute remaining time across unedited sessions
                    num_unedited = len(unedited_sessions)
                    avg_duration = remaining_time / num_unedited
                    
                    # Get min/max bounds
                    min_session = activity.get('min_session_minutes', 30)
                    max_session = activity.get('max_session_minutes', 120)
                    
                    # Round to nearest 15 minutes
                    avg_duration = round(avg_duration / 15) * 15
                    avg_duration = max(min_session, min(max_session, avg_duration))
                    
                    # Distribute with slight randomization
                    for i, sess in enumerate(unedited_sessions):
                        if i == len(unedited_sessions) - 1:
                            # Last session gets remaining time
                            allocated = remaining_time
                        else:
                            # Random variation ±15 minutes
                            variation = random.choice([-15, 0, 15])
                            allocated = avg_duration + variation
                            allocated = max(min_session, min(max_session, allocated))
                            allocated = round(allocated / 15) * 15
                        
                        sess['duration_minutes'] = int(allocated)
                        sess['duration_hours'] = round(allocated / 60, 2)
                        remaining_time -= allocated
            
            # Track user edit
            edit_key = f"{activity_name}_{session_id}"
            st.session_state.user_edits[edit_key] = {
                'activity': activity_name,
                'session_id': session_id,
                'day': new_day,
                'start_time': new_start_time,
                'duration': new_duration,
                'locked': lock,
                'date': new_date,
                'edited_at': datetime.now().isoformat()
            }
            
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            save_to_firebase(st.session_state.user_id, 'user_edits', st.session_state.user_edits)
            
            return {"success": True, "message": "Session updated successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def update_allowed_days(activity_name: str, allowed_days: List[str]) -> Dict:
        """Update which days an activity can be scheduled on"""
        try:
            activity = next((a for a in st.session_state.list_of_activities 
                           if a['activity'] == activity_name), None)
            
            if not activity:
                return {"success": False, "message": "Activity not found"}
            
            activity['allowed_days'] = allowed_days
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            
            return {"success": True, "message": f"Allowed days updated"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def add_school_schedule(day_name: str, start_time: str, end_time: str, subject: str = "School") -> Dict:
        """Add recurring school schedule for a specific weekday"""
        try:
            if day_name not in WEEKDAY_NAMES:
                return {"success": False, "message": "Invalid day name"}
            
            if time_str_to_minutes(end_time) <= time_str_to_minutes(start_time):
                return {"success": False, "message": "End time must be after start time"}
            
            if day_name not in st.session_state.school_schedule:
                st.session_state.school_schedule[day_name] = []
            
            st.session_state.school_schedule[day_name].append({
                'subject': subject,
                'start_time': start_time,
                'end_time': end_time
            })
            
            st.session_state.school_schedule[day_name].sort(
                key=lambda x: time_str_to_minutes(x['start_time'])
            )
            
            save_to_firebase(st.session_state.user_id, 'school_schedule', st.session_state.school_schedule)
            
            return {"success": True, "message": f"School schedule added for {day_name}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def delete_school_schedule(day_name: str, index: int) -> Dict:
        """Delete a school schedule entry"""
        try:
            if day_name in st.session_state.school_schedule:
                if 0 <= index < len(st.session_state.school_schedule[day_name]):
                    st.session_state.school_schedule[day_name].pop(index)
                    if not st.session_state.school_schedule[day_name]:
                        del st.session_state.school_schedule[day_name]
                    
                    save_to_firebase(st.session_state.user_id, 'school_schedule', st.session_state.school_schedule)
                    return {"success": True, "message": "School schedule deleted"}
            
            return {"success": False, "message": "Schedule not found"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def delete_activity(index: int) -> Dict:
        """Delete an activity"""
        try:
            if 0 <= index < len(st.session_state.list_of_activities):
                activity_name = st.session_state.list_of_activities[index]['activity']
                
                # Remove from progress and pending
                if activity_name in st.session_state.activity_progress:
                    del st.session_state.activity_progress[activity_name]
                if activity_name in st.session_state.session_completion:
                    del st.session_state.session_completion[activity_name]
                if activity_name in st.session_state.pending_verifications:
                    st.session_state.pending_verifications.remove(activity_name)
                
                # Remove user edits
                st.session_state.user_edits = {
                    k: v for k, v in st.session_state.user_edits.items() 
                    if not k.startswith(activity_name)
                }
                
                st.session_state.list_of_activities.pop(index)
                
                save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
                save_to_firebase(st.session_state.user_id, 'session_completion', st.session_state.session_completion)
                save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
                save_to_firebase(st.session_state.user_id, 'user_edits', st.session_state.user_edits)
                
                return {"success": True, "message": f"Activity '{activity_name}' deleted"}
            else:
                return {"success": False, "message": "Invalid activity index"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def reset_activity_progress(activity_name: str) -> Dict:
        """Reset progress for an activity"""
        try:
            st.session_state.activity_progress[activity_name] = 0
            if activity_name in st.session_state.session_completion:
                st.session_state.session_completion[activity_name] = {}
            
            save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
            save_to_firebase(st.session_state.user_id, 'session_completion', st.session_state.session_completion)
            
            return {"success": True, "message": f"Progress reset for '{activity_name}'"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def add_event(name: str, event_date: str, start_time: str, end_time: str) -> Dict:
        """Add a new compulsory event"""
        try:
            if not name:
                return {"success": False, "message": "Event name is required"}
            
            event_dt = datetime.fromisoformat(event_date)
            
            if time_str_to_minutes(end_time) <= time_str_to_minutes(start_time):
                return {"success": False, "message": "End time must be after start time"}
            
            day_name = WEEKDAY_NAMES[event_dt.weekday()]
            day_display = f"{day_name} {event_dt.strftime('%d/%m')}"
            
            new_event = {
                "event": name,
                "start_time": start_time,
                "end_time": end_time,
                "day": day_display,
                "date": event_dt.isoformat()
            }
            
            st.session_state.list_of_compulsory_events.append(new_event)
            save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
            
            return {"success": True, "message": f"Event '{name}' added successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def delete_event(index: int) -> Dict:
        """Delete an event"""
        try:
            if 0 <= index < len(st.session_state.list_of_compulsory_events):
                event_name = st.session_state.list_of_compulsory_events[index]['event']
                st.session_state.list_of_compulsory_events.pop(index)
                save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
                return {"success": True, "message": f"Event '{event_name}' deleted"}
            else:
                return {"success": False, "message": "Invalid event index"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def generate_timetable(min_session: int = 30, max_session: int = 120) -> Dict:
        """Generate timetable for current month"""
        try:
            from Timetable_Generation import generate_timetable_with_sessions
            
            st.session_state.min_session_minutes = min_session
            st.session_state.max_session_minutes = max_session
            
            result = generate_timetable_with_sessions(
                st.session_state.current_year, 
                st.session_state.current_month
            )
            
            if result.get('success', True):
                return {"success": True, "message": "Timetable generated successfully"}
            else:
                return {"success": False, "message": result.get('message', 'Generation failed')}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def navigate_month(direction: str) -> Dict:
        """Navigate to previous, next, or current month"""
        try:
            if direction == "prev":
                if st.session_state.current_month == 1:
                    st.session_state.current_month = 12
                    st.session_state.current_year -= 1
                else:
                    st.session_state.current_month -= 1
            elif direction == "next":
                if st.session_state.current_month == 12:
                    st.session_state.current_month = 1
                    st.session_state.current_year += 1
                else:
                    st.session_state.current_month += 1
            elif direction == "today":
                now = datetime.now()
                st.session_state.current_month = now.month
                st.session_state.current_year = now.year
            
            save_to_firebase(st.session_state.user_id, 'current_month', st.session_state.current_month)
            save_to_firebase(st.session_state.user_id, 'current_year', st.session_state.current_year)
            
            return {"success": True, "message": "Month updated"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def verify_session(day_display: str, event_index: int) -> Dict:
        """Mark an activity session as completed"""
        try:
            if day_display in st.session_state.timetable and event_index < len(st.session_state.timetable[day_display]):
                event = st.session_state.timetable[day_display][event_index]
                
                if event['type'] == 'ACTIVITY':
                    activity_name = event['name'].split(' (Session')[0]
                    session_id = event.get('session_id')
                    
                    if not session_id:
                        return {"success": False, "message": "Session ID not found"}
                    
                    if NeroTimeLogic._is_session_completed(activity_name, session_id):
                        return {"success": False, "message": "Session already completed"}
                    
                    session_duration = (time_str_to_minutes(event['end']) - 
                                      time_str_to_minutes(event['start'])) / 60
                    
                    # Mark session as complete
                    if activity_name not in st.session_state.session_completion:
                        st.session_state.session_completion[activity_name] = {}
                    st.session_state.session_completion[activity_name][session_id] = True
                    
                    # Update total progress
                    if activity_name not in st.session_state.activity_progress:
                        st.session_state.activity_progress[activity_name] = 0
                    st.session_state.activity_progress[activity_name] += session_duration
                    
                    save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
                    save_to_firebase(st.session_state.user_id, 'session_completion', st.session_state.session_completion)
                    
                    return {"success": True, "message": f"✓ Session completed! Added {session_duration:.1f}h to '{activity_name}'"}
                else:
                    return {"success": False, "message": "Event is not an activity"}
            else:
                return {"success": False, "message": "Invalid event reference"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def save_all_data() -> Dict:
        """Save all data to Firebase"""
        try:
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
            save_to_firebase(st.session_state.user_id, 'school_schedule', st.session_state.school_schedule)
            save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
            save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
            save_to_firebase(st.session_state.user_id, 'session_completion', st.session_state.session_completion)
            save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
            save_to_firebase(st.session_state.user_id, 'user_edits', st.session_state.user_edits)
            save_to_firebase(st.session_state.user_id, 'current_month', st.session_state.current_month)
            save_to_firebase(st.session_state.user_id, 'current_year', st.session_state.current_year)
            
            return {"success": True, "message": "All data saved successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def clear_all_data() -> Dict:
        """Clear all user data"""
        try:
            st.session_state.list_of_activities = []
            st.session_state.list_of_compulsory_events = []
            st.session_state.school_schedule = {}
            st.session_state.timetable = {}
            st.session_state.activity_progress = {}
            st.session_state.session_completion = {}
            st.session_state.pending_verifications = []
            st.session_state.user_edits = {}
            
            save_to_firebase(st.session_state.user_id, 'activities', [])
            save_to_firebase(st.session_state.user_id, 'events', [])
            save_to_firebase(st.session_state.user_id, 'school_schedule', {})
            save_to_firebase(st.session_state.user_id, 'timetable', {})
            save_to_firebase(st.session_state.user_id, 'activity_progress', {})
            save_to_firebase(st.session_state.user_id, 'session_completion', {})
            save_to_firebase(st.session_state.user_id, 'pending_verifications', [])
            save_to_firebase(st.session_state.user_id, 'user_edits', {})
            
            return {"success": True, "message": "All data cleared"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def handle_expired_activity(activity_name: str, action: str, new_hours: Optional[float] = None) -> Dict:
        """Handle expired activity verification"""
        try:
            if action == 'complete':
                activity = next((a for a in st.session_state.list_of_activities 
                               if a['activity'] == activity_name), None)
                if activity:
                    st.session_state.activity_progress[activity_name] = activity['timing']
                    
                    if activity_name in st.session_state.pending_verifications:
                        st.session_state.pending_verifications.remove(activity_name)
                    st.session_state.list_of_activities = [
                        a for a in st.session_state.list_of_activities 
                        if a['activity'] != activity_name
                    ]
                    
                    remove_activity_from_timetable(activity_name)
                    
                    save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
                    save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
                    save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                    save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
                    
                    return {"success": True, "message": f"'{activity_name}' marked as complete!"}
            
            elif action == 'update' and new_hours is not None:
                st.session_state.activity_progress[activity_name] = new_hours
                
                activity = next((a for a in st.session_state.list_of_activities 
                               if a['activity'] == activity_name), None)
                if activity and new_hours >= activity['timing']:
                    if activity_name in st.session_state.pending_verifications:
                        st.session_state.pending_verifications.remove(activity_name)
                    save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
                
                save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
                
                return {"success": True, "message": "Progress updated"}
            
            elif action == 'recalibrate':
                if activity_name in st.session_state.pending_verifications:
                    st.session_state.pending_verifications.remove(activity_name)
                
                for activity in st.session_state.list_of_activities:
                    if activity['activity'] == activity_name:
                        activity['deadline'] = 7
                        break
                
                remove_activity_from_timetable(activity_name)
                
                save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
                save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
                
                return {"success": True, "message": f"'{activity_name}' deadline extended by 7 days"}
            
            return {"success": False, "message": "Invalid action"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    @staticmethod
    def _get_current_time_slot() -> Tuple[str, str]:
        """Get current day and time slot"""
        now = datetime.now()
        day_name = WEEKDAY_NAMES[now.weekday()]
        current_display = f"{day_name} {now.strftime('%d/%m')}"
        current_time = now.strftime("%H:%M")
        return current_display, current_time
    
    @staticmethod
    def _can_verify_event(event: Dict, day_display: str) -> bool:
        """Check if event time has passed"""
        now = datetime.now()
        
        try:
            date_part = day_display.split()[-1]
            day, month = map(int, date_part.split('/'))
            year = st.session_state.current_year
            event_date = datetime(year, month, day)
            
            if event_date.date() < now.date():
                return True
            elif event_date.date() == now.date():
                event_end = datetime.strptime(event['end'], "%H:%M").time()
                return now.time() > event_end
        except:
            return False
        
        return False
    
    @staticmethod
    def _is_session_completed(activity_name: str, session_id: str) -> bool:
        """Check if a specific session is completed"""
        if activity_name not in st.session_state.session_completion:
            return False
        return st.session_state.session_completion[activity_name].get(session_id, False)
    
    @staticmethod
    def _is_user_edited(day_display: str, event: Dict) -> bool:
        """Check if an event was manually edited by user"""
        if event['type'] != 'ACTIVITY':
            return False
        
        session_id = event.get('session_id')
        if not session_id:
            return False
        
        activity_name = event['name'].split(' (Session')[0]
        edit_key = f"{activity_name}_{session_id}"
        
        return edit_key in st.session_state.user_edits
    
    @staticmethod
    def _get_activity_progress_data(activity_name: str) -> Dict:
        """Get progress data for an activity"""
        activity = next((a for a in st.session_state.list_of_activities 
                        if a['activity'] == activity_name), None)
        if not activity:
            return {"completed": 0, "total": 0, "percentage": 0}
        
        completed = st.session_state.activity_progress.get(activity_name, 0)
        total = activity['timing']
        percentage = min(completed / total * 100, 100) if total > 0 else 0
        
        return {
            "completed": completed,
            "total": total,
            "percentage": percentage
        }
    
    @staticmethod
    def _get_sessions_data(activity_name: str) -> List[Dict]:
        """Get detailed session data for an activity"""
        activity = next((a for a in st.session_state.list_of_activities 
                        if a['activity'] == activity_name), None)
        if not activity or 'sessions' not in activity:
            return []
        
        sessions_with_status = []
        for session in activity['sessions']:
            session_data = session.copy()
            session_data['is_completed'] = NeroTimeLogic._is_session_completed(
                activity_name, 
                session['session_id']
            )
            sessions_with_status.append(session_data)
        
        return sessions_with_status
    
    @staticmethod
    def _get_expired_activities() -> List[Dict]:
        """Get list of expired activities"""
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        expired = []
        for activity in st.session_state.list_of_activities:
            deadline_date = today + timedelta(days=activity['deadline'])
            
            if now > deadline_date:
                activity_name = activity['activity']
                completed_hours = st.session_state.activity_progress.get(activity_name, 0)
                total_hours = activity['timing']
                
                if completed_hours < total_hours:
                    expired.append({
                        'name': activity_name,
                        'completed': completed_hours,
                        'total': total_hours,
                        'deadline': activity['deadline']
                    })
        
        return expired

    """Handles expired sessions and user verification"""
    
    @staticmethod
    def check_expired_sessions():
        """Check for sessions that have passed their date and prompt user for completion"""
        if 'last_expiration_check' not in st.session_state:
            st.session_state.last_expiration_check = datetime.now().date()
        
        # Only check once per day
        today = datetime.now().date()
        if st.session_state.last_expiration_check == today:
            return
        
        st.session_state.last_expiration_check = today
        
        # Initialize expired sessions tracker
        if 'pending_verifications' not in st.session_state:
            st.session_state.pending_verifications = {}
        
        # Check all activities for expired sessions
        for activity in st.session_state.list_of_activities:
            activity_name = activity['activity']
            sessions = activity.get('sessions', [])
            
            for session in sessions:
                session_id = session.get('session_id')
                scheduled_day = session.get('scheduled_day')
                is_completed = session.get('is_completed', False)
                
                # Skip if already completed or not scheduled
                if is_completed or not scheduled_day:
                    continue
                
                # Parse the date from scheduled_day (format: "DayName DD/MM")
                try:
                    # Get the date from timetable if it exists
                    session_date = SessionExpirationHandler._get_session_date(scheduled_day)
                    
                    if session_date and session_date < today:
                        # Session has expired
                        verification_key = f"{activity_name}_{session_id}"
                        if verification_key not in st.session_state.pending_verifications:
                            st.session_state.pending_verifications[verification_key] = {
                                'activity': activity_name,
                                'session_id': session_id,
                                'scheduled_day': scheduled_day,
                                'scheduled_time': session.get('scheduled_time'),
                                'duration_minutes': session.get('duration_minutes'),
                                'date': session_date.isoformat()
                            }
                except Exception as e:
                    print(f"Error checking expiration for {activity_name} - {session_id}: {e}")
        
        # Save to Firebase
        if st.session_state.user_id:
            save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
    
    @staticmethod
    def _get_session_date(scheduled_day):
        """Extract date from scheduled day string (e.g., 'Monday 08/02')"""
        try:
            # Parse DD/MM from the scheduled_day string
            date_part = scheduled_day.split()[-1]  # Get "DD/MM"
            day, month = date_part.split('/')
            
            # Use current year or find the right year
            current_year = datetime.now().year
            session_date = datetime(current_year, int(month), int(day)).date()
            
            # If the date is in the future but appears to be from last year, adjust
            if session_date > datetime.now().date() + timedelta(days=180):
                session_date = datetime(current_year - 1, int(month), int(day)).date()
            
            return session_date
        except Exception:
            return None
    
    @staticmethod
    def show_pending_verifications():
        """Display pending session verifications in the UI"""
        if not st.session_state.get('pending_verifications'):
            return
        
        st.warning(f"⚠️ You have {len(st.session_state.pending_verifications)} session(s) that need verification!")
        
        with st.expander("🔔 Verify Past Sessions", expanded=True):
            for key, session_info in list(st.session_state.pending_verifications.items()):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{session_info['activity']}**")
                    st.caption(f"📅 {session_info['scheduled_day']} at {session_info['scheduled_time']} ({session_info['duration_minutes']} min)")
                
                with col2:
                    if st.button("✅ Completed", key=f"complete_{key}"):
                        SessionExpirationHandler.mark_session_completed(session_info, key)
                        st.rerun()
                
                with col3:
                    if st.button("❌ Missed", key=f"missed_{key}"):
                        SessionExpirationHandler.mark_session_missed(session_info, key)
                        st.rerun()
    
    @staticmethod
    def mark_session_completed(session_info, verification_key):
        """Mark an expired session as completed and add to progress"""
        activity_name = session_info['activity']
        session_id = session_info['session_id']
        duration_minutes = session_info['duration_minutes']
        
        # Find the activity and session
        for activity in st.session_state.list_of_activities:
            if activity['activity'] == activity_name:
                for session in activity.get('sessions', []):
                    if session.get('session_id') == session_id:
                        # Mark as completed
                        session['is_completed'] = True
                        
                        # Add to progress
                        if 'activity_progress' not in st.session_state:
                            st.session_state.activity_progress = {}
                        
                        if activity_name not in st.session_state.activity_progress:
                            st.session_state.activity_progress[activity_name] = 0
                        
                        st.session_state.activity_progress[activity_name] += duration_minutes / 60
                        
                        # Remove from pending verifications
                        del st.session_state.pending_verifications[verification_key]
                        
                        # Save to Firebase
                        if st.session_state.user_id:
                            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                            save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
                            save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
                        
                        return
    
    @staticmethod
    def mark_session_missed(session_info, verification_key):
        """Mark an expired session as missed and reschedule"""
        activity_name = session_info['activity']
        session_id = session_info['session_id']
        
        # Find the activity and session
        for activity in st.session_state.list_of_activities:
            if activity['activity'] == activity_name:
                for session in activity.get('sessions', []):
                    if session.get('session_id') == session_id:
                        # Clear the schedule so it can be rescheduled
                        session['scheduled_day'] = None
                        session['scheduled_time'] = None
                        
                        # Remove from pending verifications
                        del st.session_state.pending_verifications[verification_key]
                        
                        # Save to Firebase
                        if st.session_state.user_id:
                            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                            save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
                        
                        return


# Add this method to your existing NeroTimeLogic class
def check_expired_sessions():
    """Call this method on app load to check for expired sessions"""
    SessionExpirationHandler.check_expired_sessions()

def show_pending_verifications():
    """Call this in the dashboard to show pending verifications"""
    SessionExpirationHandler.show_pending_verifications()


# Update the generate_sessions function to ensure 15-minute intervals
def round_to_15_minutes(minutes):
    """Round minutes to nearest 15-minute interval"""
    return ((minutes + 7) // 15) * 15


def generate_sessions_with_15min_intervals(activity):
    """
    Generate sessions for an activity with durations that are multiples of 15 minutes.
    Add this to your activity generation logic.
    """
    total_hours = activity['timing']
    total_minutes = total_hours * 60
    min_session = round_to_15_minutes(activity['min_session_length'])
    max_session = round_to_15_minutes(activity['max_session_length'])
    
    sessions = []
    remaining_minutes = total_minutes
    session_count = 1
    
    while remaining_minutes > 0:
        # Determine session duration (rounded to 15 minutes)
        if remaining_minutes >= max_session:
            duration = max_session
        elif remaining_minutes >= min_session:
            duration = round_to_15_minutes(remaining_minutes)
        else:
            # If less than min_session, add to previous session or create a min_session
            if sessions:
                sessions[-1]['duration_minutes'] += remaining_minutes
                sessions[-1]['duration_minutes'] = round_to_15_minutes(sessions[-1]['duration_minutes'])
                sessions[-1]['duration_hours'] = sessions[-1]['duration_minutes'] / 60
            else:
                duration = min_session
        
        if remaining_minutes >= min_session or not sessions:
            session_id = f"{activity['activity']}_session_{session_count}"
            sessions.append({
                'session_id': session_id,
                'duration_minutes': duration,
                'duration_hours': duration / 60,
                'is_completed': False,
                'is_locked': False,
                'scheduled_day': None,
                'scheduled_time': None
            })
            remaining_minutes -= duration
            session_count += 1
        else:
            break
    
    return sessions

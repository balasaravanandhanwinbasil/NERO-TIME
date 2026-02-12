"""
NEKO-TIME COMMUNICATIONS - FIXED VERSION
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List
import pytz
import math
import random
from Firebase_Function import save_to_firebase, load_from_firebase, save_timetable_snapshot
from Timetable_Generation import time_str_to_minutes, WEEKDAY_NAMES, get_month_days

def round_to_15_minutes(minutes):
    """Rounding minutes to nearest 15-minute interval"""
    return int(((minutes + 7) // 15) * 15)


class NeroTimeLogic:
    """BACKEND LOGIC USED FOR APP"""
    
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
        if 'timetable_warnings' not in st.session_state:
            st.session_state.timetable_warnings = []
        if 'past_incomplete_sessions' not in st.session_state:
            st.session_state.past_incomplete_sessions = {}
        if 'finished_sessions' not in st.session_state:
            st.session_state.finished_sessions = []
    
    @staticmethod
    def login_user(user_id: str) -> Dict:
        """Login user and load their data"""
        
        if not user_id:
            return {"success": False, "message": "User ID is required"}
        
        st.session_state.user_id = user_id
        
        # Load all user data from Firebase and place them inside the session state variables, unless they are empty
        st.session_state.list_of_activities = load_from_firebase(user_id, 'activities') or []
        st.session_state.list_of_compulsory_events = load_from_firebase(user_id, 'events') or []
        st.session_state.school_schedule = load_from_firebase(user_id, 'school_schedule') or {}
        st.session_state.timetable = load_from_firebase(user_id, 'timetable') or {}
        st.session_state.finished_sessions = load_from_firebase(user_id, 'finished_sessions') or []
        
        month = load_from_firebase(user_id, 'current_month')
        year = load_from_firebase(user_id, 'current_year')
        
        if month:
            st.session_state.current_month = month
        if year:
            st.session_state.current_year = year
        
        st.session_state.data_loaded = True
        
        return {"success": True, "message": f"Logged in as {user_id}"}
    
    @staticmethod
    # USED TO CHECK FOR COMPLETED / EXPIRED SESSIONS
    def check_expired_sessions():
        """Check for past incomplete sessions and mark finished sessions"""
        today = datetime.now().date()
        now = datetime.now()
        
        for activity in st.session_state.list_of_activities:
            activity_name = activity['activity']
            sessions = activity.get('sessions', [])
            
            for session in sessions:
                # Skip already completed sessions
                if session.get('is_completed', False):
                    continue
                    
                scheduled_date_str = session.get('scheduled_date')
                scheduled_time_str = session.get('scheduled_time')
                
                if not scheduled_date_str or not scheduled_time_str:
                    continue
                    
                try:
                    scheduled_date = datetime.fromisoformat(scheduled_date_str).date()
                    scheduled_datetime = datetime.combine(scheduled_date, 
                                                         datetime.strptime(scheduled_time_str, "%H:%M").time())
                    
                    # Add duration to get end time
                    duration_minutes = session.get('duration_minutes', 0)
                    session_end = scheduled_datetime + timedelta(minutes=duration_minutes)
                    
                    # Mark as FINISHED if time has passed
                    if session_end <= now:
                        session['is_finished'] = True
                        session_id = session.get('session_id')
                        
                        # Add to finished sessions list if not already there
                        if not any(fs.get('session_id') == session_id for fs in st.session_state.finished_sessions):
                            session_identifier = {
                                'activity': activity_name,
                                'session_id': session_id,
                                'session_num': session.get('session_num', 0),
                                'scheduled_date': scheduled_date_str,
                                'scheduled_time': scheduled_time_str,
                                'duration_minutes': duration_minutes,
                                'is_verified': False  # Not verified yet
                            }
                            st.session_state.finished_sessions.append(session_identifier)
                    else:
                        session['is_finished'] = False
                        
                except Exception as e:
                    print(f"Error processing session: {e}")
                    pass
        
        # Save finished sessions and activities
        if st.session_state.user_id:
            save_to_firebase(st.session_state.user_id, 'finished_sessions', st.session_state.finished_sessions)
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
    
    @staticmethod
    def verify_finished_session(session_id: str, verified: bool) -> Dict:
        """Verify a finished session as completed or not"""
        try:
            # Update in finished sessions list
            finished_session = None
            for fs in st.session_state.finished_sessions:
                if fs.get('session_id') == session_id:
                    fs['is_verified'] = True
                    fs['completed'] = verified  # Track whether it was completed or skipped
                    finished_session = fs
                    break
            
            if not finished_session:
                return {"success": False, "message": "Session not found in finished sessions"}
            
            # Update in activities list
            for activity in st.session_state.list_of_activities:
                if activity['activity'] == finished_session['activity']:
                    for session in activity.get('sessions', []):
                        if session.get('session_id') == session_id:
                            session['is_completed'] = verified
                            session['is_skipped'] = not verified
                            break
                    break
            
            # Update in timetable
            for day_events in st.session_state.timetable.values():
                for event in day_events:
                    if event.get('session_id') == session_id:
                        event['is_completed'] = verified
                        event['is_skipped'] = not verified
                        break
            
            # Save to Firebase
            if st.session_state.user_id:
                save_to_firebase(st.session_state.user_id, 'finished_sessions', st.session_state.finished_sessions)
                save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
            
            return {"success": True, "message": "Session verified"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def mark_past_session_complete(activity_name: str, session_id: str, completed: bool) -> Dict:
        """Mark a session who's timing has ALREADY PASSED as completed or not completed"""
        try:
            activity = next((a for a in st.session_state.list_of_activities 
                           if a['activity'] == activity_name), None)
            
            if not activity:
                return {"success": False, "message": "Activity not found"}
            
            session = next((s for s in activity.get('sessions', []) 
                          if s['session_id'] == session_id), None)
            
            if not session:
                return {"success": False, "message": "Session not found"}
            
            session['is_completed'] = completed
            session['is_skipped'] = not completed
            
            # Update in finished sessions
            for fs in st.session_state.finished_sessions:
                if fs.get('session_id') == session_id:
                    fs['is_verified'] = True
                    fs['completed'] = completed
                    break
            
            # remove from past incomplete if completed 
            if completed and 'past_incomplete_sessions' in st.session_state:
                if activity_name in st.session_state.past_incomplete_sessions:
                    st.session_state.past_incomplete_sessions[activity_name] = [
                        s for s in st.session_state.past_incomplete_sessions[activity_name]
                        if s['session_id'] != session_id
                    ]
                    if not st.session_state.past_incomplete_sessions[activity_name]:
                        del st.session_state.past_incomplete_sessions[activity_name]

            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            save_to_firebase(st.session_state.user_id, 'finished_sessions', st.session_state.finished_sessions)
            
            return {"success": True, "message": "Session status updated"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def show_pending_verifications():
        """TO-DO (low prio)"""
        pass
    
    @staticmethod
    def get_dashboard_data() -> Dict:
        """Get all data needed for dashboard"""
        month_days = get_month_days(st.session_state.current_year, st.session_state.current_month)
        current_day, current_time = NeroTimeLogic._get_current_time_slot()
        
        enriched_timetable = {}
        for day_display, events in st.session_state.timetable.items():
            enriched_events = []
            for event in events:
                enriched_event = event.copy()
                enriched_event['can_verify'] = NeroTimeLogic._can_verify_event(event, day_display)
                enriched_event['is_finished'] = NeroTimeLogic._is_event_finished(event, day_display)
                enriched_events.append(enriched_event)
            enriched_timetable[day_display] = enriched_events
        
        return {
            "month_name": datetime(st.session_state.current_year, st.session_state.current_month, 1).strftime("%B"),
            "year": st.session_state.current_year,
            "month": st.session_state.current_month,
            "month_days": month_days,
            "timetable": enriched_timetable,
            "current_day": current_day,
            "current_time": current_time
        }
    
    @staticmethod
    def get_activities_data() -> Dict:
        """Get activities with specified scheduled sessions"""
        enriched_activities = []
        for activity in st.session_state.list_of_activities:
            enriched = activity.copy()
            
            # Calculate progress from scheduled sessions
            scheduled_sessions = activity.get('sessions', [])
            completed_hours = sum(s['duration_hours'] for s in scheduled_sessions if s.get('is_completed', False))
            enriched['progress'] = {
                'completed': completed_hours,
                'total': activity['timing'],
                'percentage': (completed_hours / activity['timing'] * 100) if activity['timing'] > 0 else 0
            }
            
            # Add to sessions_data 
            enriched['sessions_data'] = scheduled_sessions
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
        """Get weekly school/work schedule"""
        return {"schedule": st.session_state.school_schedule}
    
    @staticmethod
    def add_activity(name: str, priority: int, deadline_date: str, total_hours: int, 
                     min_session: int = 30, max_session: int = 120, 
                     allowed_days: List[str] = None, session_mode: str = "automatic") -> Dict:
        """Add a new activity"""
        try:
            if not name:
                return {"success": False, "message": "Activity name is required"}
            
            deadline_dt = datetime.fromisoformat(deadline_date)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_left = (deadline_dt.replace(hour=0, minute=0, second=0, microsecond=0) - today).days
            
            # MIN_SESSION AND MAX_SESSION TIMINGS ARE AUTOMATICALLY ROUNDED TO 15 minutes
            min_session = int(round_to_15_minutes(min_session))
            max_session = int(round_to_15_minutes(max_session))
            
            new_activity = {
                "activity": name,
                "priority": priority,
                "deadline": days_left,
                "timing": total_hours,
                "min_session_minutes": min_session,
                "max_session_minutes": max_session,
                "allowed_days": allowed_days or WEEKDAY_NAMES,
                "sessions": [],  # will be added to by the timetable generation code
                "session_mode": session_mode  # "automatic" or "manual"
            }
            
            st.session_state.list_of_activities.append(new_activity)
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            
            return {"success": True, "message": f"Activity '{name}' added"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def add_manual_session(activity_name: str, duration_minutes: int, day_of_week: str = None) -> Dict:
        """Add a manual session to an activity (no date, just duration and optional day)"""
        try:
            activity = next((a for a in st.session_state.list_of_activities 
                           if a['activity'] == activity_name), None)
            
            if not activity:
                return {"success": False, "message": "Activity not found"}
            
            if activity.get('session_mode') != 'manual':
                return {"success": False, "message": "Activity is not in manual mode"}
            
            # Round duration
            duration_minutes = int(round_to_15_minutes(duration_minutes))
            
            # Get next session number
            existing_sessions = activity.get('sessions', [])
            session_num = len(existing_sessions) + 1
            session_id = f"{activity_name}_manual_{session_num}"
            
            # Create manual session (no date/time yet)
            new_session = {
                'session_id': session_id,
                'session_num': session_num,
                'duration_minutes': duration_minutes,
                'duration_hours': round(duration_minutes / 60, 2),
                'day_of_week': day_of_week,  # Optional preference
                'is_manual': True,
                'is_scheduled': False,  # Not scheduled to timetable yet
                'is_completed': False,
                'is_finished': False,
                'is_skipped': False
            }
            
            activity['sessions'].append(new_session)
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            
            return {"success": True, "message": f"Manual session added to '{activity_name}'"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def edit_session(activity_name: str, session_id: str, new_day: str = None, 
                     new_start_time: str = None, new_duration: int = None,
                     new_date: str = None) -> Dict:
        """Edit a specific session of an activity"""
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
            session = next((s for s in activity.get('sessions', []) 
                          if s['session_id'] == session_id), None)
            if not session:
                return {"success": False, "message": "Session not found"}
            
            # Check if session is completed
            if session.get('is_completed', False):
                return {"success": False, "message": "Cannot edit completed session"}
            
            # Round duration to nearest 15 minutes if provided
            if new_duration is not None:
                new_duration = int(round_to_15_minutes(new_duration))
                if new_duration < 15:
                    new_duration = 15
            
            # Apply edits
            if new_day is not None:
                session['scheduled_day'] = new_day
            if new_start_time is not None:
                session['scheduled_time'] = new_start_time
            if new_duration is not None:
                session['duration_minutes'] = int(new_duration)
                session['duration_hours'] = round(new_duration / 60, 2)
            if new_date is not None:
                session['scheduled_date'] = new_date
            
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            
            return {"success": True, "message": "Session updated successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def add_recurring_event(name: str, start_time: str, end_time: str, 
                           recurrence_type: str, days: List[str] = None, 
                           start_date: str = None) -> Dict:
        """Add recurring event (weekly, bi-weekly, monthly)"""
        try:
            if not name:
                return {"success": False, "message": "Event name is required"}
            
            if time_str_to_minutes(end_time) <= time_str_to_minutes(start_time):
                return {"success": False, "message": "End time must be after start time"}
            
            # For weekly/bi-weekly events
            if recurrence_type in ["weekly", "bi-weekly"]:
                if not days:
                    return {"success": False, "message": "Days required for weekly/bi-weekly events"}
                
                for day_name in days:
                    if day_name not in WEEKDAY_NAMES:
                        continue
                    
                    if day_name not in st.session_state.school_schedule:
                        st.session_state.school_schedule[day_name] = []
                    
                    st.session_state.school_schedule[day_name].append({
                        'subject': name,
                        'start_time': start_time,
                        'end_time': end_time,
                        'recurrence': recurrence_type
                    })
                    
                    st.session_state.school_schedule[day_name].sort(
                        key=lambda x: time_str_to_minutes(x['start_time'])
                    )
            
            # For monthly events
            elif recurrence_type == "monthly":
                if not start_date:
                    return {"success": False, "message": "Start date required for monthly events"}
                
                event_dt = datetime.fromisoformat(start_date)
                day_name = WEEKDAY_NAMES[event_dt.weekday()]
                day_display = f"{day_name} {event_dt.strftime('%d/%m')}"
                
                new_event = {
                    "event": name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "day": day_display,
                    "date": event_dt.isoformat(),
                    "recurrence": "monthly"
                }
                
                st.session_state.list_of_compulsory_events.append(new_event)
                save_to_firebase(st.session_state.user_id, 'events', st.session_state.list_of_compulsory_events)
            
            save_to_firebase(st.session_state.user_id, 'school_schedule', st.session_state.school_schedule)
            
            return {"success": True, "message": f"Recurring event '{name}' added successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def add_school_schedule(day_name: str, start_time: str, end_time: str, subject: str = "School/Work") -> Dict:
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
                st.session_state.list_of_activities.pop(index)
                
                save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                
                return {"success": True, "message": f"Activity '{activity_name}' deleted"}
            else:
                return {"success": False, "message": "Invalid activity index"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    def reset_activity_progress(activity_name: str) -> Dict:
        """Reset progress for an activity"""
        try:
            # Clear sessions for this activity
            for activity in st.session_state.list_of_activities:
                if activity['activity'] == activity_name:
                    activity['sessions'] = []
                    break
            
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            
            return {"success": True, "message": f"Sessions cleared for '{activity_name}'"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    @staticmethod
    def add_activity_progress(activity_name: str) -> Dict:
        '''Manually add progress into activity'''
        try:
            #Add activity session for that activity
            for activity in st.session_state.list_of_activities:
                if activity['activity'] == activity_name:
                    st.write(st.session_state.list_of_activities)
                    enriched['progress'] = {'completed': completed_hours,'total': activity['timing'],'percentage': (completed_hours / activity['timing'] * 100) if activity['timing'] > 0 else 0}
            return {"success": True, "message": f"Sessions cleared for '{activity_name}'"}
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
    def generate_timetable() -> Dict:
        """Generate timetable for current month"""
        try:
            from Timetable_Generation import generate_timetable_with_sessions
            
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
    def verify_session(day_display: str, event_index: int, completed: bool = True) -> Dict:
        """Mark a session as verified/completed or skipped"""
        try:
            if day_display not in st.session_state.timetable:
                return {"success": False, "message": "Day not found in timetable"}
            
            if event_index >= len(st.session_state.timetable[day_display]):
                return {"success": False, "message": "Event not found"}
            
            event = st.session_state.timetable[day_display][event_index]
            
            if event['type'] != 'ACTIVITY':
                return {"success": False, "message": "Can only verify activity sessions"}
            
            # Find the activity and session
            activity_name = event.get('activity_name')
            session_num = event.get('session_num')
            
            if not activity_name or session_num is None:
                return {"success": False, "message": "Invalid session data"}
            
            # Find and mark session
            for activity in st.session_state.list_of_activities:
                if activity['activity'] == activity_name:
                    for session in activity.get('sessions', []):
                        if session.get('session_num') == session_num:
                            session['is_completed'] = completed
                            session['is_skipped'] = not completed  # Track if skipped
                            event['is_completed'] = completed
                            event['is_skipped'] = not completed
                            
                            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                            save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
                            
                            if completed:
                                return {"success": True, "message": "Session marked as complete"}
                            else:
                                return {"success": True, "message": "Session marked as not done"}
            
            return {"success": False, "message": "Session not found in activity"}
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
            st.session_state.timetable_warnings = []
            st.session_state.past_incomplete_sessions = {}
            st.session_state.finished_sessions = []
            
            save_to_firebase(st.session_state.user_id, 'activities', [])
            save_to_firebase(st.session_state.user_id, 'events', [])
            save_to_firebase(st.session_state.user_id, 'school_schedule', {})
            save_to_firebase(st.session_state.user_id, 'timetable', {})
            save_to_firebase(st.session_state.user_id, 'finished_sessions', [])
            
            return {"success": True, "message": "All data cleared"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
        
    @staticmethod
    def _get_current_time_slot():
        """Get current day and time slot"""
        now = datetime.now()
        day_name = WEEKDAY_NAMES[now.weekday()]
        current_display = f"{day_name} {now.strftime('%d/%m')}"
        current_time = now.strftime("%H:%M")
        return current_display, current_time
    
    @staticmethod
    def _can_verify_event(event: Dict, day_display: str) -> bool:
        """Check if event time has passed and can be verified"""
        now = datetime.now()
        
        # Don't allow verification if already verified (completed or skipped)
        if event.get('is_completed') or event.get('is_skipped'):
            return False
        
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
    def _is_event_finished(event: Dict, day_display: str) -> bool:
        """Check if event timing has finished (for FINISHED badge)"""
        now = datetime.now()
        
        try:
            date_part = day_display.split()[-1]
            day, month = map(int, date_part.split('/'))
            year = st.session_state.current_year
            event_date = datetime(year, month, day)
            
            event_end_time = datetime.strptime(event['end'], "%H:%M").time()
            event_end_datetime = datetime.combine(event_date.date(), event_end_time)
            
            return event_end_datetime <= now
        except:
            return False

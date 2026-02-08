"""
Simplified NERO-Time Backend Logic
Focus on fitting activities before deadlines, no complex session management
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List
import math
import random

from Firebase_Function import save_to_firebase, load_from_firebase, save_timetable_snapshot
from Timetable_Generation import time_str_to_minutes, WEEKDAY_NAMES, get_month_days

def round_to_15_minutes(minutes):
    """Round minutes to nearest 15-minute interval"""
    return ((minutes + 7) // 15) * 15


class NeroTimeLogic:
    """Simplified backend logic for NERO-Time"""
    
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
        
        month = load_from_firebase(user_id, 'current_month')
        year = load_from_firebase(user_id, 'current_year')
        
        if month:
            st.session_state.current_month = month
        if year:
            st.session_state.current_year = year
        
        st.session_state.data_loaded = True
        
        return {"success": True, "message": f"Logged in as {user_id}"}
    
    @staticmethod
    def check_expired_sessions():
        """Placeholder - not needed in simplified system"""
        pass
    
    @staticmethod
    def show_pending_verifications():
        """Placeholder - not needed in simplified system"""
        pass
    
    @staticmethod
    def get_dashboard_data() -> Dict:
        """Get all data needed for dashboard"""
        month_days = get_month_days(st.session_state.current_year, st.session_state.current_month)
        current_day, current_time = NeroTimeLogic._get_current_time_slot()
        
        # Enrich timetable events
        enriched_timetable = {}
        for day_display, events in st.session_state.timetable.items():
            enriched_events = []
            for event in events:
                enriched_event = event.copy()
                enriched_event['can_verify'] = NeroTimeLogic._can_verify_event(event, day_display)
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
        """Get activities with scheduled sessions"""
        enriched_activities = []
        for activity in st.session_state.list_of_activities:
            enriched = activity.copy()
            # Calculate progress from scheduled sessions
            scheduled_sessions = activity.get('scheduled_sessions', [])
            total_scheduled = sum(s['duration_hours'] for s in scheduled_sessions)
            enriched['progress'] = {
                'completed': 0,  # Would track actual completion
                'total': activity['timing'],
                'percentage': 0
            }
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
            
            # Round min/max to 15-minute intervals
            min_session = round_to_15_minutes(min_session)
            max_session = round_to_15_minutes(max_session)
            
            new_activity = {
                "activity": name,
                "priority": priority,
                "deadline": days_left,
                "timing": total_hours,
                "min_session_minutes": min_session,
                "max_session_minutes": max_session,
                "allowed_days": allowed_days or WEEKDAY_NAMES,
                "sessions": []  # Will be filled by timetable generation
            }
            
            st.session_state.list_of_activities.append(new_activity)
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            
            return {"success": True, "message": f"Activity '{name}' added"}
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
                new_duration = round_to_15_minutes(new_duration)
                if new_duration < 15:
                    new_duration = 15
            
            # Apply edits
            if new_day is not None:
                session['scheduled_day'] = new_day
            if new_start_time is not None:
                session['scheduled_time'] = new_start_time
            if new_duration is not None:
                session['duration_minutes'] = new_duration
                session['duration_hours'] = round(new_duration / 60, 2)
            if new_date is not None:
                session['scheduled_date'] = new_date
            
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            
            return {"success": True, "message": "Session updated successfully"}
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
    def verify_session(day_display: str, event_index: int) -> Dict:
        """Placeholder for session verification - can be implemented later"""
        return {"success": False, "message": "Verification not implemented in simplified system"}
    
    @staticmethod
    def clear_all_data() -> Dict:
        """Clear all user data"""
        try:
            st.session_state.list_of_activities = []
            st.session_state.list_of_compulsory_events = []
            st.session_state.school_schedule = {}
            st.session_state.timetable = {}
            st.session_state.timetable_warnings = []
            
            save_to_firebase(st.session_state.user_id, 'activities', [])
            save_to_firebase(st.session_state.user_id, 'events', [])
            save_to_firebase(st.session_state.user_id, 'school_schedule', {})
            save_to_firebase(st.session_state.user_id, 'timetable', {})
            
            return {"success": True, "message": "All data cleared"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    # ==================== PRIVATE HELPER METHODS ====================
    
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

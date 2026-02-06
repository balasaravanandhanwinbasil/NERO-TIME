"""
NERO-Time Backend Logic (Streamlit Version)
All business logic separated from UI
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# Import from existing files
from Firebase_Function import (
    save_to_firebase, 
    load_from_firebase,
    save_timetable_snapshot, 
    get_timetable_history
)

from Timetable_Generation import (
    time_str_to_minutes,
    minutes_to_time_str,
    add_minutes,
    is_time_slot_free,
    add_event_to_timetable,
    get_day_activity_minutes,
    find_free_slot,
    place_compulsory_events,
    place_activities,
    generate_timetable as generate_tt,
    check_expired_activities,
    remove_activity_from_timetable,
    WEEKDAY_NAMES,
    get_month_days
)


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
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
        if 'activity_progress' not in st.session_state:
            st.session_state.activity_progress = {}
        if 'pending_verifications' not in st.session_state:
            st.session_state.pending_verifications = []
    
    @staticmethod
    def login_user(user_id: str) -> Dict:
        """Login user and load their data"""
        if not user_id:
            return {"success": False, "message": "User ID is required"}
        
        st.session_state.user_id = user_id
        
        # Load all user data from Firebase
        st.session_state.list_of_activities = load_from_firebase(user_id, 'activities') or []
        st.session_state.list_of_compulsory_events = load_from_firebase(user_id, 'events') or []
        st.session_state.timetable = load_from_firebase(user_id, 'timetable') or {}
        st.session_state.activity_progress = load_from_firebase(user_id, 'activity_progress') or {}
        st.session_state.pending_verifications = load_from_firebase(user_id, 'pending_verifications') or []
        
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
                    enriched_event['can_verify'] = NeroTimeLogic._can_verify_event(event, day_display)
                    enriched_event['activity_name'] = activity_name
                    enriched_event['progress'] = NeroTimeLogic._get_activity_progress_data(activity_name)
                    enriched_event['session_duration'] = (
                        time_str_to_minutes(event['end']) - time_str_to_minutes(event['start'])
                    ) / 60
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
    def add_activity(name: str, priority: int, deadline_date: str, total_hours: int, 
                     min_session: int = 30, max_session: int = 120, sessions: int = 1) -> Dict:
        """Add a new activity"""
        try:
            if not name:
                return {"success": False, "message": "Activity name is required"}
            
            deadline_dt = datetime.fromisoformat(deadline_date)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_left = (deadline_dt.replace(hour=0, minute=0, second=0, microsecond=0) - today).days
            
            new_activity = {
                "activity": name,
                "priority": priority,
                "deadline": days_left,
                "timing": total_hours,
                "min_session_minutes": min_session,
                "max_session_minutes": max_session,
                "sessions": sessions
            }
            
            st.session_state.list_of_activities.append(new_activity)
            save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
            
            return {"success": True, "message": f"Activity '{name}' added successfully"}
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
                if activity_name in st.session_state.pending_verifications:
                    st.session_state.pending_verifications.remove(activity_name)
                
                st.session_state.list_of_activities.pop(index)
                
                save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
                save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
                save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
                
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
            save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
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
                "date": event_dt.isoformat(),
                "sessions": sessions,
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
            st.session_state.min_session_minutes = min_session
            st.session_state.max_session_minutes = max_session
            
            generate_tt(st.session_state.current_year, st.session_state.current_month)
            
            return {"success": True, "message": "Timetable generated successfully"}
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
                    session_duration = (time_str_to_minutes(event['end']) - 
                                      time_str_to_minutes(event['start'])) / 60
                    
                    if activity_name not in st.session_state.activity_progress:
                        st.session_state.activity_progress[activity_name] = 0
                    st.session_state.activity_progress[activity_name] += session_duration
                    
                    save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
                    
                    return {"success": True, "message": f"Added {session_duration:.1f}h to '{activity_name}'"}
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
            save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
            save_to_firebase(st.session_state.user_id, 'activity_progress', st.session_state.activity_progress)
            save_to_firebase(st.session_state.user_id, 'pending_verifications', st.session_state.pending_verifications)
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
            st.session_state.timetable = {}
            st.session_state.activity_progress = {}
            st.session_state.pending_verifications = []
            
            save_to_firebase(st.session_state.user_id, 'activities', [])
            save_to_firebase(st.session_state.user_id, 'events', [])
            save_to_firebase(st.session_state.user_id, 'timetable', {})
            save_to_firebase(st.session_state.user_id, 'activity_progress', {})
            save_to_firebase(st.session_state.user_id, 'pending_verifications', [])
            
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

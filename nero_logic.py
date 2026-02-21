"""
NERO-Time BACKEND LOGIC 
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List
from Firebase_Function import save_to_firebase
from Timetable_Generation import (
    time_str_to_minutes,
    WEEKDAY_NAMES, 
    get_month_days,
    get_timetable_view
)


def round_to_15_minutes(minutes: int) -> int:
    return int(((int(minutes) + 7) // 15) * 15)


class NeroTimeLogic:
    """Backend logic for NERO-Time."""

    # ==== Initialisation ====

    @staticmethod
    def initialize_session_state():
        # NOTE: readme.txt for elaboration on each of these variables.
        defaults = {
            'user_id':             None,
            'username':            None,
            'user_email':          None,
            'data_loaded':         False,
            'login_mode':          'login',
            'current_year':        datetime.now().year,
            'current_month':       datetime.now().month,
            'event_filter':        'weekly',

            # Timetable (to display)
            'timetable':           {},

            # ALL sessions 
            'sessions':            {},

            # Activity metadata 
            'list_of_activities':  [],

            'school_schedule':     {},
            'timetable_warnings':  [],
            'work_start_minutes':  7 * 60,        # 07:00
            'work_end_minutes':    22 * 60 + 30,  # 22:30
        }

        # place the variables inside sessions_state so that it saves on each reload.
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    # === Firebase load / Save (USE EVERYTIME YOU CHANGE SESSION_STATE) ===
    @staticmethod
    def _save(data_type: str, data):
        if st.session_state.user_id:
            save_to_firebase(st.session_state.user_id, data_type, data)


    # === SESSION EXPIRY CHECK ===
    @staticmethod
    def check_expired_sessions():
        """
        Mark sessions as is_finished when their end time has passed.
        Reads/writes to st.session_state.sessions directly. (is_finished = True, or is_finished = False)
        Runs on every load.
        """
        now = datetime.now()

        for session in st.session_state.sessions.values():
            if session.get('is_completed', False):
                continue

            scheduled_date_str = session.get('scheduled_date')
            scheduled_time_str = session.get('scheduled_time')

            if not scheduled_date_str or not scheduled_time_str:
                continue

            try: # find end datetime in order to check if it is more than current date to see if it is is finishd
                scheduled_date = datetime.fromisoformat(scheduled_date_str).date()
                start_dt = datetime.combine(
                    scheduled_date,
                    datetime.strptime(scheduled_time_str, "%H:%M").time()
                )

                end_dt = start_dt + timedelta(minutes=session.get('duration_minutes', 0))

                session['is_finished'] = (end_dt <= now)

            except Exception:
                pass

        NeroTimeLogic._save('sessions', st.session_state.sessions)

    # === Dashboard data ===
    @staticmethod
    def get_dashboard_data() -> Dict: # used in tab_dashboard.py for the ui
        """Return all data needed for the dashboard tab."""

        month_days = get_month_days(
            st.session_state.current_year,
            st.session_state.current_month
        )
        current_day, current_time = NeroTimeLogic._get_current_time_slot()

        # Build timetable view using function
        timetable_view = get_timetable_view()

        return {
            "month_name":   datetime(st.session_state.current_year,
                                     st.session_state.current_month, 1).strftime("%B"),
            "year":         st.session_state.current_year,
            "month":        st.session_state.current_month,
            "month_days":   month_days,
            "timetable":    timetable_view,
            "current_day":  current_day,
            "current_time": current_time,
        }

    # === Activities Data ===
    @staticmethod
    def get_activities_data() -> Dict:
        """Returns the activities data, with all values computed and with all sessions inside"""

        enriched = []
        for activity in st.session_state.list_of_activities:
            name = activity['activity']

            # All sessions for this activity
            act_sessions = [
                s for s in st.session_state.sessions.values()
                if s['activity_name'] == name
            ]
            completed_hours = sum(
                s['duration_hours'] for s in act_sessions if s.get('is_completed', False)
            )
            total_hours = activity['timing']

            enriched.append({ # this adds all the sessions for the respective activity into the dict to be used
                **activity, 
                'sessions':  act_sessions,
                'progress': {
                    'completed':   completed_hours,
                    'total':       total_hours,
                    'percentage':  (completed_hours / total_hours * 100) if total_hours > 0 else 0,
                },
            })

        return {"activities": enriched}

    # === Verification Helpers ===
    @staticmethod
    def get_finished_sessions() -> List[Dict]:
        """Return all sessions where is_finished=True (time has passed)."""

        return [s for s in st.session_state.sessions.values() if s.get('is_finished', False)]

    @staticmethod
    def get_pending_verification() -> List[Dict]:
        """Finished sessions not yet verified (neither completed nor skipped)."""

        return [
            s for s in st.session_state.sessions.values()
            if s.get('is_finished', False)
            and not s.get('is_completed', False)
            and not s.get('is_skipped', False)
        ]

    @staticmethod
    def get_reviewed_sessions() -> List[Dict]:
        """Finished sessions that have been verified (completed or skipped)."""

        return [
            s for s in st.session_state.sessions.values()
            if s.get('is_finished', False)
            and (s.get('is_completed', False) or s.get('is_skipped', False))
        ]

    # === Session Verification ===

    @staticmethod
    def verify_finished_session(session_id: str, verified: bool) -> Dict:
        """Mark a finished session as completed (True) or skipped (False)."""

        session = st.session_state.sessions.get(session_id)
        if not session:
            return {"success": False, "message": "Session not found"}

        session['is_completed'] = verified
        session['is_skipped']   = not verified

        NeroTimeLogic._save('sessions', st.session_state.sessions) # saves the data in the session_state

        return {"success": True, "message": "Session verified"}

    # === Events/Schedules Data ===

    @staticmethod
    def get_events_data() -> Dict:
        sorted_events = sorted(
            st.session_state.list_of_compulsory_events,
            key=lambda x: x.get('date', '9999-12-31')
        )
        return {"events": sorted_events}

    @staticmethod
    def get_school_schedule() -> Dict:
        return {"schedule": st.session_state.school_schedule}

    # === Activity Manipulation (Creating, Deleting, Reading, Updating) ===

    @staticmethod
    def add_activity(
        name: str, 
        priority: int, 
        deadline_date: str, 
        total_hours: int,
        min_session: int = 30, max_session: int = 120,
        allowed_days: List[str] = None,
        session_mode: str = "automatic"
        ) -> Dict:
        """Adds an Activity based on the inputs in the UI."""

        try:
            if not name:
                return {"success": False, "message": "Activity name is required"}
            
            for i in range(len(st.session_state.list_of_activities)): # checks activities to ensure name isn't repeated. 
                if name in st.session_state.list_of_activities[i]['activity']:
                    return {"success": False, "message": "Activity name is cannot be the same as a previous activity name"}

            deadline_dt = datetime.fromisoformat(deadline_date) # converts to e.g 2026-03-01 00:00:00 in order to calculate deadline.
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            days_left = (deadline_dt.replace(hour=0, minute=0, second=0, microsecond=0) - today).days

            min_session = int(round_to_15_minutes(min_session)) # minimum session timings (in min, to nearest 15 minutes.)
            max_session = int(round_to_15_minutes(max_session)) # maxing session timings (in min, to nearest 15 minutes.)

            # storing the values inside the session_state for activities (st.session_state.list_of_activities) for automtic generation.
            new_activity = {
                "activity":            name,
                "priority":            priority,
                "deadline":            days_left,
                "timing":              total_hours,
                "min_session_minutes": min_session,
                "max_session_minutes": max_session,
                "allowed_days":        allowed_days or WEEKDAY_NAMES,
                "session_mode":        session_mode,
                "num_sessions":        0,
            }

            st.session_state.list_of_activities.append(new_activity)
            NeroTimeLogic._save('activities', st.session_state.list_of_activities)

            return {"success": True, "message": f"Activity '{name}' added"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def delete_activity(index: int) -> Dict:
        """Deletes an activity at a certain index."""

        try:
            if not (0 <= index < len(st.session_state.list_of_activities)): # input validation to ensure valid value
                return {"success": False, "message": "Invalid activity index"}

            activity_name = st.session_state.list_of_activities[index]['activity']
            st.session_state.list_of_activities.pop(index) # remove activity from session_state.list_of_activities

            # remove all sessions of the activity from session_state.sessions
            to_remove = [
                sid for sid, s in st.session_state.sessions.items()
                if s['activity_name'] == activity_name
            ]
            for sid in to_remove:
                del st.session_state.sessions[sid]

            NeroTimeLogic._save('activities', st.session_state.list_of_activities)
            NeroTimeLogic._save('sessions',   st.session_state.sessions)

            return {"success": True, "message": f"Activity '{activity_name}' deleted"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def reset_activity_progress(activity_name: str) -> Dict:
        """Remove all sessions for an activity (reset to 0h completed)."""
        try:
            to_remove = [
                sid for sid, s in st.session_state.sessions.items()
                if s['activity_name'] == activity_name
            ] # get id of all the sessions inside the session state

            for sid in to_remove:
                del st.session_state.sessions[sid] # remove each of the elements using the id.

            # Reset num_sessions on list_of_activities back to zero
            for activity in st.session_state.list_of_activities:
                if activity['activity'] == activity_name:
                    activity['num_sessions'] = 0
                    break

            NeroTimeLogic._save('sessions',   st.session_state.sessions)
            NeroTimeLogic._save('activities', st.session_state.list_of_activities)

            return {"success": True, "message": f"Sessions cleared for '{activity_name}'"}
        
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    # === Manual Session Management ===
    @staticmethod
    def add_manual_session(
        activity_name: str, 
        duration_minutes: int,
        day_of_week: str = None
        ) -> Dict:
        """Add an unscheduled manual session (placed by next timetable generation)"""
        try:
            activity = next(
                (a for a in st.session_state.list_of_activities if a['activity'] == activity_name),
                None
            )
            # input validation
            if not activity:
                return {"success": False, "message": "Activity not found!"}
            if activity.get('session_mode') != 'manual':
                return {"success": False, "message": "Activity is not in manual mode!"}
            
            # duration of session
            duration_minutes = int(round_to_15_minutes(duration_minutes))

            # get the session number for this activity by looking at existing_nums
            existing_nums = [
                s['session_num'] for s in st.session_state.sessions.values()
                if s['activity_name'] == activity_name
            ]
            session_num = max(existing_nums, default=0) + 1
            session_id  = f"{activity_name.replace(' ', '_')}_manual_{session_num}"

            st.session_state.sessions[session_id] = {
                'session_id':       session_id,
                'session_num':      session_num,
                'activity_name':    activity_name,
                'scheduled_day':    None,   # not scheduled yet
                'scheduled_date':   None,
                'scheduled_time':   None,
                'duration_minutes': duration_minutes,
                'duration_hours':   round(duration_minutes / 60, 2),
                'day_of_week':      day_of_week,  # scheduling preference
                'is_manual':        True,
                'is_completed':     False,
                'is_skipped':       False,
                'is_finished':      False,
                'is_user_edited':   False,
            }

            NeroTimeLogic._save('sessions', st.session_state.sessions)
            return {"success": True, "message": f"Manual session added to '{activity_name}'"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def edit_session(activity_name: str, session_id: str,
                     new_day: str = None, new_start_time: str = None,
                     new_duration: int = None, new_date: str = None) -> Dict:
        """Edit a scheduled session's day, time, or duration."""
        try:
            session = st.session_state.sessions.get(session_id)
            if not session:
                return {"success": False, "message": "Session not found"}
            if session.get('is_completed', False):
                return {"success": False, "message": "Cannot edit a completed session"}

            # Check activity deadline hasn't passed
            activity = next(
                (a for a in st.session_state.list_of_activities if a['activity'] == activity_name),
                None
            )
            if activity and activity['deadline'] < 0:
                return {"success": False, "message": "Cannot edit — activity deadline has passed"}

            if new_duration is not None:
                new_duration = int(round_to_15_minutes(new_duration))
                new_duration = max(15, new_duration)
                session['duration_minutes'] = new_duration
                session['duration_hours']   = round(new_duration / 60, 2)

            if new_day        is not None: session['scheduled_day']  = new_day
            if new_start_time is not None: session['scheduled_time'] = new_start_time
            if new_date       is not None: session['scheduled_date'] = new_date

            session['is_user_edited'] = True

            NeroTimeLogic._save('sessions', st.session_state.sessions)
            return {"success": True, "message": "Session updated"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    # === Events Manipulation (Creating, Deleting, Reading, Updating) ===

    @staticmethod
    def add_event(name: str, event_date: str, start_time: str, end_time: str) -> Dict:
        """Add one-time events using this function."""

        try:
            if not name:
                return {"success": False, "message": "Event name is required"}

            event_dt = datetime.fromisoformat(event_date)
            if time_str_to_minutes(end_time) <= time_str_to_minutes(start_time):
                return {"success": False, "message": "End time must be after start time"}

            day_name    = WEEKDAY_NAMES[event_dt.weekday()]
            day_display = f"{day_name} {event_dt.strftime('%d/%m')}"

            # add to list_of_compulsory_events session_state
            st.session_state.list_of_compulsory_events.append({
                "event":      name,
                "start_time": start_time,
                "end_time":   end_time,
                "day":        day_display,
                "date":       event_dt.isoformat(),
            })

            NeroTimeLogic._save('events', st.session_state.list_of_compulsory_events)
            return {"success": True, "message": f"Event '{name}' added"}
        
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def add_recurring_event(name: str, start_time: str, end_time: str,
                            recurrence_type: str, days: List[str] = None,
                            start_date: str = None) -> Dict:
        """Add all recurring events using this function."""

        try:
            if not name:
                return {"success": False, "message": "Event name is required"}
            if time_str_to_minutes(end_time) <= time_str_to_minutes(start_time):
                return {"success": False, "message": "End time must be after start time"}

            if recurrence_type in ["weekly", "bi-weekly"]: # put in the recurring events into the session_state.school_schedule (for all weekly / bi-weekly events)
                if not days:
                    return {"success": False, "message": "Days required for weekly/bi-weekly events"}
                
                for day_name in days:
                    if day_name not in WEEKDAY_NAMES:
                        continue

                    st.session_state.school_schedule.setdefault(day_name, []).append({
                        'subject':    name,
                        'start_time': start_time,
                        'end_time':   end_time,
                        'recurrence': recurrence_type,
                    })

                    st.session_state.school_schedule[day_name].sort(
                        key=lambda x: time_str_to_minutes(x['start_time'])
                    )

            elif recurrence_type == "monthly": # if monthly, can just place it inside list_of_compulsory_events but with recurrence set to monthly
                if not start_date:
                    return {"success": False, "message": "Start date required for monthly events"}
                
                event_dt    = datetime.fromisoformat(start_date)
                day_name    = WEEKDAY_NAMES[event_dt.weekday()]
                day_display = f"{day_name} {event_dt.strftime('%d/%m')}"

                st.session_state.list_of_compulsory_events.append({
                    "event":      name,
                    "start_time": start_time,
                    "end_time":   end_time,
                    "day":        day_display,
                    "date":       event_dt.isoformat(),
                    "recurrence": "monthly",
                })

                NeroTimeLogic._save('events', st.session_state.list_of_compulsory_events)

            NeroTimeLogic._save('school_schedule', st.session_state.school_schedule)

            return {"success": True, "message": f"Recurring event '{name}' added"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def delete_event(index: int) -> Dict:
        """"Deletes an one-time event/monthly event, based on the index given."""

        try:
            # input validation (if index is above length)
            if not (0 <= index < len(st.session_state.list_of_compulsory_events)):
                return {"success": False, "message": "Invalid event index"}
            
            # delete the event from list of compulsory events.
            name = st.session_state.list_of_compulsory_events[index]['event']
            st.session_state.list_of_compulsory_events.pop(index)
            NeroTimeLogic._save('events', st.session_state.list_of_compulsory_events)

            return {"success": True, "message": f"Event '{name}' deleted"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def delete_school_schedule(day_name: str, index: int) -> Dict:
        """Deletes a recurring event, based on the index given."""
        try:
            schedule = st.session_state.school_schedule

            if day_name in schedule and 0 <= index < len(schedule[day_name]):  #input validation
                schedule[day_name].pop(index)
                if not schedule[day_name]:
                    del schedule[day_name]

                NeroTimeLogic._save('school_schedule', schedule)

                return {"success": True, "message": "Schedule deleted"}
            
            return {"success": False, "message": "Schedule not found"}
        
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    # === TIMETABLE GENERATION ===

    @staticmethod
    def generate_timetable() -> Dict:
        """Calls generate_timetable_with_sessions and returns the output, which is a Dict."""

        try:
            from Timetable_Generation import generate_timetable_with_sessions 

            result = generate_timetable_with_sessions(
                st.session_state.current_year,
                st.session_state.current_month
            )

            if result.get('success', True):
                return {"success": True, "message": "Timetable generated successfully"}
            
            return {"success": False, "message": result.get('message', 'Generation failed')}
        
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    # === Month Navigation ===

    @staticmethod
    def navigate_month(direction: str) -> Dict:
        """Changes current_month, current_year based on <prev next> navigation in the dashboard"""
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
                st.session_state.current_year  = now.year

            NeroTimeLogic._save('current_month', st.session_state.current_month)
            NeroTimeLogic._save('current_year',  st.session_state.current_year)

            return {"success": True}
        
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    # === Data management ===

    @staticmethod
    def clear_all_data() -> Dict:
        """Resets all Data back to Zero"""
        try:
            st.session_state.list_of_activities         = []
            st.session_state.list_of_compulsory_events  = []
            st.session_state.school_schedule             = {}
            st.session_state.timetable                   = {}
            st.session_state.sessions                    = {}
            st.session_state.timetable_warnings          = []

            for key in ('activities', 'events', 'school_schedule', 'timetable', 'sessions'):
                NeroTimeLogic._save(key, {} if key in ('timetable', 'sessions', 'school_schedule') else [])

            return {"success": True, "message": "All data cleared"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    # === Internal helpers (gets the current time in hours) ===

    @staticmethod
    def _get_current_time_slot():
        now         = datetime.now() 
        
        day_name    = WEEKDAY_NAMES[now.weekday()] # gets the name of the day
        current_day = f"{day_name} {now.strftime('%d/%m')}" # Example: "Saturday 21/02"

        return current_day, now.strftime("%H:%M") # Output Example: "Saturday 21/02", "15:42"

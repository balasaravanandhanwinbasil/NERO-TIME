"""
NERO-Time BACKEND LOGIC 
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List
import pytz
from Firebase_Function import save_to_firebase, load_from_firebase, save_timetable_snapshot
from Timetable_Generation import (
    time_str_to_minutes, minutes_to_time_str,
    WEEKDAY_NAMES, get_month_days, get_timetable_view
)


def round_to_15_minutes(minutes: int) -> int:
    return int(((int(minutes) + 7) // 15) * 15)


class NeroTimeLogic:
    """Backend logic for NERO-Time."""

    # ── Initialisation ─────────────────────────────────────────────────────────

    @staticmethod
    def initialize_session_state():
        defaults = {
            'user_id':             None,
            'username':            None,
            'user_email':          None,
            'data_loaded':         False,
            'login_mode':          'login',
            'current_year':        datetime.now().year,
            'current_month':       datetime.now().month,
            'event_filter':        'weekly',

            # Timetable: fixed events only (SCHOOL / COMPULSORY)
            'timetable':           {},

            # Unified session store
            'sessions':            {},

            # Activity metadata (no embedded sessions)
            'list_of_activities':  [],

            'list_of_compulsory_events': [],
            'school_schedule':     {},
            'timetable_warnings':  [],
            'work_start_minutes':  6 * 60,        # 06:00
            'work_end_minutes':    23 * 60 + 30,  # 23:30
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    # ── Firebase load / save helpers ───────────────────────────────────────────

    @staticmethod
    def _save(data_type: str, data):
        if st.session_state.user_id:
            save_to_firebase(st.session_state.user_id, data_type, data)

    # ── Session expiry check ───────────────────────────────────────────────────

    @staticmethod
    def check_expired_sessions():
        """
        Mark sessions as is_finished when their end time has passed.
        Reads/writes st.session_state.sessions directly.
        No separate finished_sessions list needed — filter sessions instead.
        """
        now = datetime.now()

        for session in st.session_state.sessions.values():
            if session.get('is_completed', False):
                continue

            scheduled_date_str = session.get('scheduled_date')
            scheduled_time_str = session.get('scheduled_time')
            if not scheduled_date_str or not scheduled_time_str:
                continue

            try:
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

    # ── Dashboard data ─────────────────────────────────────────────────────────

    @staticmethod
    def get_dashboard_data() -> Dict:
        """Return all data needed for the dashboard tab."""
        month_days = get_month_days(
            st.session_state.current_year,
            st.session_state.current_month
        )
        current_day, current_time = NeroTimeLogic._get_current_time_slot()

        # Build timetable view (fixed events + activity sessions merged)
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

    # ── Activities data ────────────────────────────────────────────────────────

    @staticmethod
    def get_activities_data() -> Dict:
        """Return activities with live-computed progress and their sessions."""
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

            enriched.append({
                **activity,
                'sessions':  act_sessions,
                'progress': {
                    'completed':   completed_hours,
                    'total':       total_hours,
                    'percentage':  (completed_hours / total_hours * 100) if total_hours > 0 else 0,
                },
            })

        return {"activities": enriched}

    # ── Finished / pending verification helpers ────────────────────────────────

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

    # ── Verification ──────────────────────────────────────────────────────────

    @staticmethod
    def verify_finished_session(session_id: str, verified: bool) -> Dict:
        """Mark a finished session as completed (True) or skipped (False)."""
        session = st.session_state.sessions.get(session_id)
        if not session:
            return {"success": False, "message": "Session not found"}

        session['is_completed'] = verified
        session['is_skipped']   = not verified

        NeroTimeLogic._save('sessions', st.session_state.sessions)
        return {"success": True, "message": "Session verified"}

    # ── Events / schedules data ────────────────────────────────────────────────

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

    # ── Activity CRUD ──────────────────────────────────────────────────────────

    @staticmethod
    def add_activity(name: str, priority: int, deadline_date: str, total_hours: int,
                     min_session: int = 30, max_session: int = 120,
                     allowed_days: List[str] = None,
                     session_mode: str = "automatic") -> Dict:
        try:
            if not name:
                return {"success": False, "message": "Activity name is required"}
            for i in range(len(st.session_state.list_of_activities)):
                if name in st.session_state.list_of_activities[1]{"activity"}:
                    return {"success": False, "message": "Activity name is cannot be the same as a previous activity name"}

            deadline_dt = datetime.fromisoformat(deadline_date)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_left = (deadline_dt.replace(hour=0, minute=0, second=0, microsecond=0) - today).days

            min_session = int(round_to_15_minutes(min_session))
            max_session = int(round_to_15_minutes(max_session))

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
        try:
            if not (0 <= index < len(st.session_state.list_of_activities)):
                return {"success": False, "message": "Invalid activity index"}

            activity_name = st.session_state.list_of_activities[index]['activity']
            st.session_state.list_of_activities.pop(index)

            # Remove all sessions belonging to this activity
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
            ]
            for sid in to_remove:
                del st.session_state.sessions[sid]

            # Reset num_sessions on the metadata
            for activity in st.session_state.list_of_activities:
                if activity['activity'] == activity_name:
                    activity['num_sessions'] = 0
                    break

            NeroTimeLogic._save('sessions',   st.session_state.sessions)
            NeroTimeLogic._save('activities', st.session_state.list_of_activities)
            return {"success": True, "message": f"Sessions cleared for '{activity_name}'"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    # ── Manual session management ──────────────────────────────────────────────

    @staticmethod
    def add_manual_session(activity_name: str, duration_minutes: int,
                           day_of_week: str = None) -> Dict:
        """Add an unscheduled manual session (placed by next timetable generation)."""
        try:
            activity = next(
                (a for a in st.session_state.list_of_activities if a['activity'] == activity_name),
                None
            )
            if not activity:
                return {"success": False, "message": "Activity not found"}
            if activity.get('session_mode') != 'manual':
                return {"success": False, "message": "Activity is not in manual mode"}

            duration_minutes = int(round_to_15_minutes(duration_minutes))

            # Next session number for this activity
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

    # ── Events CRUD ────────────────────────────────────────────────────────────

    @staticmethod
    def add_event(name: str, event_date: str, start_time: str, end_time: str) -> Dict:
        try:
            if not name:
                return {"success": False, "message": "Event name is required"}

            event_dt = datetime.fromisoformat(event_date)
            if time_str_to_minutes(end_time) <= time_str_to_minutes(start_time):
                return {"success": False, "message": "End time must be after start time"}

            day_name    = WEEKDAY_NAMES[event_dt.weekday()]
            day_display = f"{day_name} {event_dt.strftime('%d/%m')}"

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
        try:
            if not name:
                return {"success": False, "message": "Event name is required"}
            if time_str_to_minutes(end_time) <= time_str_to_minutes(start_time):
                return {"success": False, "message": "End time must be after start time"}

            if recurrence_type in ["weekly", "bi-weekly"]:
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

            elif recurrence_type == "monthly":
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
        try:
            if not (0 <= index < len(st.session_state.list_of_compulsory_events)):
                return {"success": False, "message": "Invalid event index"}
            name = st.session_state.list_of_compulsory_events[index]['event']
            st.session_state.list_of_compulsory_events.pop(index)
            NeroTimeLogic._save('events', st.session_state.list_of_compulsory_events)
            return {"success": True, "message": f"Event '{name}' deleted"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def delete_school_schedule(day_name: str, index: int) -> Dict:
        try:
            schedule = st.session_state.school_schedule
            if day_name in schedule and 0 <= index < len(schedule[day_name]):
                schedule[day_name].pop(index)
                if not schedule[day_name]:
                    del schedule[day_name]
                NeroTimeLogic._save('school_schedule', schedule)
                return {"success": True, "message": "Schedule deleted"}
            return {"success": False, "message": "Schedule not found"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    # ── Timetable generation ───────────────────────────────────────────────────

    @staticmethod
    def generate_timetable() -> Dict:
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

    # ── Month navigation ───────────────────────────────────────────────────────

    @staticmethod
    def navigate_month(direction: str) -> Dict:
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

    # ── Data management ────────────────────────────────────────────────────────

    @staticmethod
    def clear_all_data() -> Dict:
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

    # ── Internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _get_current_time_slot():
        now         = datetime.now()
        day_name    = WEEKDAY_NAMES[now.weekday()]
        current_day = f"{day_name} {now.strftime('%d/%m')}"
        return current_day, now.strftime("%H:%M")

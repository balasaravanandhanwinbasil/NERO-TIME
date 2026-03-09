"""
NERO-Time BACKEND LOGIC 
"""
timezone_str="Asia/Singapore"
import pytz
tz = pytz.timezone(timezone_str)
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List
from Firebase_Function import save_to_firebase
from Timetable_Generation import (
    time_str_to_minutes,
    minutes_to_time_str,
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
        defaults = {
            'user_id':             None,
            'username':            None,
            'user_email':          None,
            'data_loaded':         False,
            'login_mode':          'login',
            'current_year':        datetime.now(tz).year,
            'current_month':       datetime.now(tz).month,
            'event_filter':        'weekly',
            'timetable':           {},
            'sessions':            {},
            'list_of_activities':  [],
            'list_of_compulsory_events':  [],
            'school_schedule':     {},
            'timetable_warnings':  [],
            'work_start_minutes':  7 * 60,        # 07:00
            'work_end_minutes':    22 * 60 + 30,  # 22:30
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    # === Firebase load / Save ===
    @staticmethod
    def _save(data_type: str, data):
        if st.session_state.user_id:
            save_to_firebase(st.session_state.user_id, data_type, data)

    # === SESSION EXPIRY CHECK ===
    @staticmethod
    def check_expired_sessions():
        """Mark sessions as is_finished when their end time has passed."""
        now = datetime.now(tz)

        for session in st.session_state.sessions.values():
            if session.get('is_completed', False):
                continue

            scheduled_date_str = session.get('scheduled_date')
            scheduled_time_str = session.get('scheduled_time')

            if not scheduled_date_str or not scheduled_time_str:
                continue

            try:
                scheduled_date = tz.localize(datetime.fromisoformat(scheduled_date_str)).date()
                start_dt = tz.localize(datetime.combine(
                    scheduled_date,
                    datetime.strptime(scheduled_time_str, "%H:%M").time()
                ))
                end_dt = start_dt + timedelta(minutes=session.get('duration_minutes', 0))
                session['is_finished'] = (end_dt <= now)
            except Exception:
                pass

        NeroTimeLogic._save('sessions', st.session_state.sessions)

    # === Conflict checking ===

    @staticmethod
    def _check_slot_conflicts(day_display: str, start_time: str,
                              duration_minutes: int,
                              exclude_session_id: str = None) -> list:
        """
        Return a list of human-readable conflict strings for the proposed window
        [start_time, start_time + duration_minutes) on day_display.

        Checks:
          - Work-hour boundaries
          - Fixed timetable events (SCHOOL / COMPULSORY)
          - All other scheduled sessions (skipping exclude_session_id)
          - Proposed slot is not in the past
        """
        conflicts = []
        s_min = time_str_to_minutes(start_time)
        e_min = s_min + duration_minutes

        work_start = st.session_state.get('work_start_minutes', 7 * 60)
        work_end   = st.session_state.get('work_end_minutes', 22 * 60 + 30)

        # Work boundary
        if s_min < work_start:
            conflicts.append(
                f"Start time {start_time} is before your work start "
                f"({minutes_to_time_str(work_start)})."
            )
        if e_min > work_end:
            conflicts.append(
                f"Session would end at {minutes_to_time_str(e_min)}, "
                f"after your work end ({minutes_to_time_str(work_end)})."
            )

        # Fixed events
        for event in st.session_state.timetable.get(day_display, []):
            es = time_str_to_minutes(event["start"])
            ee = time_str_to_minutes(event["end"])
            if not (e_min <= es or s_min >= ee):
                label = "Recurring schedule" if event.get("type") == "SCHOOL" else "Compulsory event"
                conflicts.append(
                    f"Overlaps with {label} '{event['name']}' "
                    f"({event['start']}–{event['end']})."
                )

        # Other sessions
        for sid, session in st.session_state.sessions.items():
            if sid == exclude_session_id:
                continue
            if session.get('scheduled_day') != day_display:
                continue
            sched_time = session.get('scheduled_time')
            if not sched_time:
                continue
            ss = time_str_to_minutes(sched_time)
            se = ss + session.get('duration_minutes', 0)
            if not (e_min <= ss or s_min >= se):
                conflicts.append(
                    f"Overlaps with '{session.get('activity_name', '?')}' "
                    f"Session {session.get('session_num', '?')} "
                    f"({sched_time}–{minutes_to_time_str(se)})."
                )

        return conflicts

    # === Dashboard data ===
    @staticmethod
    def get_dashboard_data() -> Dict:
        """Return all data needed for the dashboard tab."""
        month_days = get_month_days(
            st.session_state.current_year,
            st.session_state.current_month
        )
        current_day, current_time = NeroTimeLogic._get_current_time_slot()
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
        """Returns the activities data with progress and sessions."""
        enriched = []
        for activity in st.session_state.list_of_activities:
            name = activity['activity']
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

    # === Verification Helpers ===
    @staticmethod
    def get_finished_sessions() -> List[Dict]:
        return [s for s in st.session_state.sessions.values() if s.get('is_finished', False)]

    @staticmethod
    def get_pending_verification() -> List[Dict]:
        return [
            s for s in st.session_state.sessions.values()
            if s.get('is_finished', False)
            and not s.get('is_completed', False)
            and not s.get('is_skipped', False)
        ]

    @staticmethod
    def get_reviewed_sessions() -> List[Dict]:
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
        NeroTimeLogic._save('sessions', st.session_state.sessions)
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

    # === Activity Manipulation ===

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
        """Adds an Activity based on the inputs given."""
        try:
            if not name:
                return {"success": False, "message": "Activity name is required"}

            for i in range(len(st.session_state.list_of_activities)):
                if name in st.session_state.list_of_activities[i]['activity']:
                    return {"success": False, "message": "Activity name cannot be the same as a previous activity name"}

            deadline_dt = tz.localize(datetime.fromisoformat(deadline_date))
            today = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
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
        """Deletes an activity at a certain index."""
        try:
            if not (0 <= index < len(st.session_state.list_of_activities)):
                return {"success": False, "message": "Invalid activity index"}

            activity_name = st.session_state.list_of_activities[index]['activity']
            st.session_state.list_of_activities.pop(index)

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
        """Add an unscheduled manual session."""
        try:
            activity = next(
                (a for a in st.session_state.list_of_activities if a['activity'] == activity_name),
                None
            )
            if not activity:
                return {"success": False, "message": "Activity not found!"}
            if activity.get('session_mode') != 'manual':
                return {"success": False, "message": "Activity is not in manual mode!"}

            duration_minutes = int(round_to_15_minutes(duration_minutes))

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
                'scheduled_day':    None,
                'scheduled_date':   None,
                'scheduled_time':   None,
                'duration_minutes': duration_minutes,
                'duration_hours':   round(duration_minutes / 60, 2),
                'day_of_week':      day_of_week,
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
        """
        Edit a scheduled session's day, time, or duration.

        Validates:
          - Session exists and is not already completed
          - Activity deadline has not passed
          - New date is not in the past
          - New date does not exceed the activity deadline
          - Proposed slot does not overlap any fixed event or other session
          - Proposed slot fits within work hours
        """
        try:
            session = st.session_state.sessions.get(session_id)
            if not session:
                return {"success": False, "message": "Session not found"}
            if session.get('is_completed', False):
                return {"success": False, "message": "Cannot edit a completed session"}

            activity = next(
                (a for a in st.session_state.list_of_activities
                 if a['activity'] == activity_name),
                None
            )

            # ── Deadline checks ───────────────────────────────────────────────
            if activity:
                if activity['deadline'] < 0:
                    return {"success": False, "message": "Cannot edit — activity deadline has passed"}

                if new_date:
                    try:
                        session_dt  = tz.localize(datetime.fromisoformat(new_date))
                        today       = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
                        deadline_dt = today + timedelta(days=activity['deadline'])

                        if session_dt.date() < today.date():
                            return {"success": False, "message": "Cannot schedule a session in the past"}

                        if session_dt.date() > deadline_dt.date():
                            deadline_str = deadline_dt.strftime("%A %d/%m")
                            return {
                                "success": False,
                                "message": f"Date exceeds the activity deadline ({deadline_str}). "
                                           f"Please choose an earlier date."
                            }
                    except Exception as ex:
                        return {"success": False, "message": f"Invalid date: {ex}"}

            # ── Apply duration first so conflict check uses the new value ─────
            if new_duration is not None:
                new_duration = int(round_to_15_minutes(new_duration))
                new_duration = max(15, new_duration)
            else:
                new_duration = session.get('duration_minutes', 60)

            # ── Conflict check ────────────────────────────────────────────────
            if new_day and new_start_time:
                conflicts = NeroTimeLogic._check_slot_conflicts(
                    new_day, new_start_time, new_duration,
                    exclude_session_id=session_id
                )
                if conflicts:
                    # Return all conflicts joined so the UI can display them
                    return {
                        "success": False,
                        "message": "Scheduling conflict:\n" + "\n".join(f"• {c}" for c in conflicts)
                    }

            # ── Commit changes ────────────────────────────────────────────────
            session['duration_minutes'] = new_duration
            session['duration_hours']   = round(new_duration / 60, 2)

            if new_day        is not None: session['scheduled_day']  = new_day
            if new_start_time is not None: session['scheduled_time'] = new_start_time
            if new_date       is not None: session['scheduled_date'] = new_date

            session['is_user_edited'] = True  # locks from being moved by regeneration

            NeroTimeLogic._save('sessions', st.session_state.sessions)
            return {"success": True, "message": "Session updated"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def format_session_datetime(session: dict) -> str:
        """Return a human-readable string for a session's scheduled time."""
        try:
            date_str  = session.get('scheduled_date', '')
            time_str  = session.get('scheduled_time', '')

            if not date_str or not time_str:
                return "Unscheduled"

            dt = datetime.fromisoformat(date_str)
            h, m = map(int, time_str.split(":"))

            period = "am" if h < 12 else "pm"
            h12    = h % 12 or 12
            time_display = f"{h12}:{m:02d}{period}" if m != 0 else f"{h12}{period}"

            day_name   = dt.strftime("%A")
            date_label = dt.strftime("%d/%m")
            date_label = date_label.lstrip("0") if date_label[0] == "0" else date_label

            return f"{day_name} {date_label} at {time_display}"
        except Exception:
            return session.get('scheduled_day', 'Unscheduled')

    # === Events Manipulation ===

    @staticmethod
    def add_event(name: str, event_date: str, start_time: str, end_time: str) -> Dict:
        """Add one-time events."""
        try:
            if not name:
                return {"success": False, "message": "Event name is required"}

            event_dt = tz.localize(datetime.fromisoformat(event_date))
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
        """Add all recurring events."""
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
                        'start_date': start_date,
                    })

                    st.session_state.school_schedule[day_name].sort(
                        key=lambda x: time_str_to_minutes(x['start_time'])
                    )

            elif recurrence_type == "monthly":
                if not start_date:
                    return {"success": False, "message": "Start date required for monthly events"}

                event_dt    = tz.localize(datetime.fromisoformat(start_date))
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
        """Deletes a one-time/monthly event by index."""
        try:
            if not (0 <= index < len(st.session_state.list_of_compulsory_events)):
                return {"success": False, "message": "Invalid event index"}

            evt        = st.session_state.list_of_compulsory_events[index]
            name       = evt['event']
            day        = evt['day']
            start_time = evt['start_time']
            end_time   = evt['end_time']

            st.session_state.list_of_compulsory_events.pop(index)

            if day in st.session_state.timetable:
                st.session_state.timetable[day] = [
                    e for e in st.session_state.timetable[day]
                    if not (
                        e.get('name') == name
                        and e.get('start') == start_time
                        and e.get('end')   == end_time
                    )
                ]

            NeroTimeLogic._save('events',    st.session_state.list_of_compulsory_events)
            NeroTimeLogic._save('timetable', st.session_state.timetable)
            return {"success": True, "message": f"Event '{name}' deleted"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def delete_school_schedule(day_name: str, index: int) -> Dict:
        """Deletes a recurring schedule entry by index."""
        try:
            schedule = st.session_state.school_schedule

            if day_name not in schedule or not (0 <= index < len(schedule[day_name])):
                return {"success": False, "message": "Schedule not found"}

            evt        = schedule[day_name][index]
            subj       = evt['subject']
            start_time = evt['start_time']
            end_time   = evt['end_time']

            schedule[day_name].pop(index)
            if not schedule[day_name]:
                del schedule[day_name]

            for day_display, events in st.session_state.timetable.items():
                if not day_display.startswith(day_name):
                    continue
                st.session_state.timetable[day_display] = [
                    e for e in events
                    if not (
                        e.get('name')  == subj
                        and e.get('start') == start_time
                        and e.get('end')   == end_time
                        and e.get('type')  == 'SCHOOL'
                    )
                ]

            NeroTimeLogic._save('school_schedule', schedule)
            NeroTimeLogic._save('timetable',       st.session_state.timetable)
            return {"success": True, "message": "Schedule deleted"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    # === TIMETABLE GENERATION ===

    @staticmethod
    def generate_timetable() -> Dict:
        """Calls generate_timetable_with_sessions and returns the output."""
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
        """Changes current_month / current_year based on navigation."""
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
                now = datetime.now(tz)
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
        """Resets all data back to zero."""
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

    # === Internal helpers ===

    @staticmethod
    def _get_current_time_slot():
        now      = datetime.now(tz)
        day_name = WEEKDAY_NAMES[now.weekday()]
        current_day = f"{day_name} {now.strftime('%d/%m')}"
        return current_day, now.strftime("%H:%M")
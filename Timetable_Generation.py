"""
NERO-time
"""

from datetime import datetime, timedelta
import streamlit as st
import random
from typing import Dict, List, Optional, Tuple

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Fallback defaults (overridden by st.session_state at runtime)
_DEFAULT_WORK_START_MINUTES = 6 * 60        # 06:00
_DEFAULT_WORK_END_MINUTES   = 23 * 60 + 30  # 23:30

BREAK_MINUTES = 30  # enforced break in between activities


# Get starting time and ending time

def get_work_start_minutes() -> int:
    return st.session_state.get('work_start_minutes', _DEFAULT_WORK_START_MINUTES)

def get_work_end_minutes() -> int:
    return st.session_state.get('work_end_minutes', _DEFAULT_WORK_END_MINUTES)


# TIME UTILITIES

def time_str_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes since midnight."""

    h, m = time_str.split(":")
    return int(h) * 60 + int(m)


def minutes_to_time_str(minutes: int) -> str:
    """Convert minutes since midnight to HH:MM."""

    minutes = int(minutes)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def round_to_15_minutes(minutes: int) -> int:
    """Round to nearest 15-minute interval."""

    return int(((int(minutes) + 7) // 15) * 15)


def get_month_days(year: int, month: int) -> list:
    """Return all days in the given month as a list of dicts."""

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


# === TIMETABLE ==

def get_timetable_view() -> Dict[str, list]:
    """
    Build the full timetable view dict on-the-fly.

    - Fixed events (SCHOOL, COMPULSORY) come from st.session_state.timetable.
    - ACTIVITY rows are generated from st.session_state.sessions.
    - Each day list is sorted by start time.

    Returns dict keyed by "Weekday DD/MM" → list of event dicts.
    """
    now = datetime.now()
    view: Dict[str, list] = {}

    # Copy fixed events (SCHOOL / COMPULSORY) from stored timetable
    for day_display, events in st.session_state.timetable.items():
        view[day_display] = [e.copy() for e in events]

    # Inject ACTIVITY rows from the sessions store
    for session in st.session_state.sessions.values():
        day_display = session.get('scheduled_day')
        start_time  = session.get('scheduled_time')
        if not day_display or not start_time:
            continue  # unscheduled manual session — skip

        end_time = minutes_to_time_str(
            time_str_to_minutes(start_time) + session['duration_minutes']
        )

        # Derive is_finished live
        is_finished = False
        try:
            sched_date = datetime.fromisoformat(session['scheduled_date']).date()
            end_dt = datetime.combine(
                sched_date,
                datetime.strptime(end_time, "%H:%M").time()
            )
            is_finished = end_dt <= now
        except Exception:
            pass

        activity_name = session['activity_name']
        session_num   = session['session_num']

        event = {
            "start":          start_time,
            "end":            end_time,
            "name":           f"{activity_name} (Session {session_num})",
            "type":           "ACTIVITY",
            "activity_name":  activity_name,
            "session_num":    session_num,
            "session_id":     session['session_id'],
            "is_completed":   session.get('is_completed', False),
            "is_skipped":     session.get('is_skipped', False),
            "is_finished":    is_finished,
            "is_user_edited": session.get('is_user_edited', False),
        }

        if day_display not in view:
            view[day_display] = []
        view[day_display].append(event)

    # Sort each day by start time
    for day_display in view:
        view[day_display].sort(key=lambda x: time_str_to_minutes(x["start"]))

    return view


# === Slot checking (against both stored fixed events AND scheduled sessions) ===

def is_time_slot_free(day: str, start_time: str, end_time: str) -> bool:
    """
    Return True if [start_time, end_time) has zero overlap with every
    already-placed event on `day` (fixed events + sessions).
    """
    s = time_str_to_minutes(start_time)
    e = time_str_to_minutes(end_time)

    # Check fixed events
    for event in st.session_state.timetable.get(day, []):
        es = time_str_to_minutes(event["start"])
        ee = time_str_to_minutes(event["end"])
        if not (e <= es or s >= ee):
            return False

    # Check already-scheduled sessions
    for session in st.session_state.sessions.values():
        if session.get('scheduled_day') != day:
            continue
        sched_time = session.get('scheduled_time')
        if not sched_time:
            continue
        ss = time_str_to_minutes(sched_time)
        se = ss + session['duration_minutes']
        if not (e <= ss or s >= se):
            return False

    return True


def add_fixed_event_to_timetable(day: str, start_time: str, end_time: str,
                                  event_name: str, event_type: str):
    """Insert a SCHOOL or COMPULSORY event into the stored timetable and sort."""
    if day not in st.session_state.timetable:
        st.session_state.timetable[day] = []

    st.session_state.timetable[day].append({
        "start":        start_time,
        "end":          end_time,
        "name":         event_name,
        "type":         event_type,
        "is_completed": False,
        "is_skipped":   False,
        "is_finished":  False,
    })
    st.session_state.timetable[day].sort(key=lambda x: time_str_to_minutes(x["start"]))


# ── Core slot finder ───────────────────────────────────────────────────────────

def find_free_slot(day: str, duration_minutes: int,
                   current_time_minutes: Optional[int] = None) -> Optional[Tuple[str, str]]:
    """
    Scan every 15-minute boundary on `day` and return the first (start, end)
    pair where the activity window + silent break gap are both free.
    """
    duration_minutes = int(duration_minutes)
    work_start = get_work_start_minutes()
    work_end   = get_work_end_minutes()

    earliest = work_start
    if current_time_minutes is not None:
        earliest = max(work_start, round_to_15_minutes(current_time_minutes + 15))

    candidates = []
    t = earliest
    while t + duration_minutes <= work_end:
        end_t     = t + duration_minutes
        start_str = minutes_to_time_str(t)
        end_str   = minutes_to_time_str(end_t)

        if is_time_slot_free(day, start_str, end_str):
            break_end = end_t + BREAK_MINUTES
            if break_end <= work_end:
                if is_time_slot_free(day, end_str, minutes_to_time_str(break_end)):
                    candidates.append((t, start_str, end_str))
            else:
                candidates.append((t, start_str, end_str))

        t += 15

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    pool = candidates[: max(1, len(candidates) // 3)]
    random.shuffle(pool)
    _, start_str, end_str = pool[0]
    return start_str, end_str


# ── Fixed-event placement ──────────────────────────────────────────────────────

def place_school_schedules(month_days: list, today: datetime):
    """Place recurring school/work blocks from today onwards."""
    if not st.session_state.school_schedule:
        return

    today_date = today.date()
    for day_info in month_days:
        if day_info['date'].date() < today_date:
            continue
        day_name    = day_info['day_name']
        day_display = day_info['display']
        if day_name in st.session_state.school_schedule:
            for evt in st.session_state.school_schedule[day_name]:
                if is_time_slot_free(day_display, evt['start_time'], evt['end_time']):
                    add_fixed_event_to_timetable(
                        day_display, evt['start_time'], evt['end_time'],
                        evt['subject'], "SCHOOL"
                    )


def place_compulsory_events(today: datetime):
    """Place one-time compulsory events from today onwards."""
    today_date = today.date()
    for event in st.session_state.list_of_compulsory_events:
        day        = event["day"]
        start_time = event["start_time"]
        end_time   = event["end_time"]
        try:
            date_part = day.split()[-1]
            day_num, month_num = map(int, date_part.split('/'))
            year = st.session_state.get('current_year', datetime.now().year)
            event_date = datetime(year, month_num, day_num).date()
            if event_date >= today_date and is_time_slot_free(day, start_time, end_time):
                add_fixed_event_to_timetable(day, start_time, end_time, event["event"], "COMPULSORY")
        except Exception:
            if is_time_slot_free(day, start_time, end_time):
                add_fixed_event_to_timetable(day, start_time, end_time, event["event"], "COMPULSORY")


# ── Available-day calculation ──────────────────────────────────────────────────

def get_available_days_for_activity(activity: dict, month_days: list,
                                    today: datetime) -> list:
    """Return days (from today up to deadline) on which this activity may be scheduled."""
    today_date           = today.date()
    current_time_minutes = today.hour * 60 + today.minute
    work_end             = get_work_end_minutes()

    deadline_days = activity['deadline']
    deadline      = datetime.combine(today_date, datetime.min.time()) + timedelta(days=deadline_days)
    allowed       = activity.get('allowed_days', WEEKDAY_NAMES)

    available = []
    for day_info in month_days:
        day_date = day_info['date']
        if day_date.date() < today_date:
            continue
        if day_date.date() == today_date and current_time_minutes >= work_end:
            continue
        if day_date <= deadline and day_info['day_name'] in allowed:
            available.append({
                'display':              day_info['display'],
                'date':                 day_date,
                'is_today':             day_date.date() == today_date,
                'current_time_minutes': current_time_minutes if day_date.date() == today_date else None,
            })
    return available


# ── Past-session warnings ──────────────────────────────────────────────────────

def check_past_activities(activity: dict, warnings: list, today: datetime):
    """
    Warn about sessions for this activity that are scheduled in the past
    but have never been verified (not completed and not skipped).
    Reads directly from st.session_state.sessions.
    """
    today_date    = today.date()
    activity_name = activity['activity']
    past_count    = 0

    for session in st.session_state.sessions.values():
        if session['activity_name'] != activity_name:
            continue
        if session.get('is_completed') or session.get('is_skipped'):
            continue
        date_str = session.get('scheduled_date')
        if not date_str:
            continue
        try:
            if datetime.fromisoformat(date_str).date() < today_date:
                past_count += 1
        except Exception:
            pass

    if past_count:
        warnings.append(
            f"⚠️ '{activity_name}' has {past_count} past unverified session(s) "
            f"that will be rescheduled."
        )


# ── Multi-pass activity scheduler ─────────────────────────────────────────────

def place_activity_sessions(activity: dict, month_days: list,
                            warnings: list, today: datetime):
    """
    Schedule `activity` into free slots using a multi-pass strategy.
    Writes new sessions directly into st.session_state.sessions.

    Survival rules:
      COMPLETED → kept, hours deducted from remaining
      SKIPPED / UNVERIFIED past → discarded, hours added back
    """
    activity_name = activity['activity']
    total_hours   = activity['timing']
    min_session   = round_to_15_minutes(activity.get('min_session_minutes', 30))
    max_session   = round_to_15_minutes(activity.get('max_session_minutes', 120))

    check_past_activities(activity, warnings, today)

    # Partition existing sessions for this activity
    existing = {
        sid: s for sid, s in st.session_state.sessions.items()
        if s['activity_name'] == activity_name
    }
    completed = {sid: s for sid, s in existing.items() if s.get('is_completed', False)}

    # Remove non-completed sessions — they will be rescheduled
    for sid in existing:
        if sid not in completed:
            del st.session_state.sessions[sid]

    comp_hours        = sum(s.get('duration_hours', 0) for s in completed.values())
    remaining_minutes = int((total_hours - comp_hours) * 60)

    if remaining_minutes <= 0:
        warnings.append(f"✓ '{activity_name}': All hours already completed!")
        return

    available_days = get_available_days_for_activity(activity, month_days, today)

    if not available_days:
        warnings.append(f"❌ '{activity_name}': No available days before deadline!")
        return

    # Determine next session number (after completed ones)
    next_session_num = (
        max((s['session_num'] for s in completed.values()), default=0) + 1
    )
    session_count = next_session_num - 1  # will be incremented before use

    # ── Multi-pass chunk strategy ──────────────────────────────────────────────
    chunk_sizes = []
    c = max_session
    while c > min_session:
        chunk_sizes.append(c)
        c = round_to_15_minutes(c // 2)
        if c < min_session:
            break
    chunk_sizes.append(min_session)
    if min_session > 15:
        chunk_sizes.append(15)
    seen = set()
    chunk_sizes = [x for x in chunk_sizes if not (x in seen or seen.add(x))]

    new_sessions_count = 0

    for pass_chunk in chunk_sizes:
        if remaining_minutes <= 0:
            break

        day_index  = 0
        days_tried = 0
        max_days   = len(available_days) * 2

        while remaining_minutes > 0 and days_tried < max_days:
            day_info    = available_days[day_index % len(available_days)]
            day_display = day_info['display']

            chunk = min(remaining_minutes, pass_chunk)
            chunk = round_to_15_minutes(chunk)
            if chunk < 15:
                chunk = 15

            current_time_mins = (
                day_info['current_time_minutes'] if day_info.get('is_today') else None
            )

            slot = find_free_slot(day_display, chunk, current_time_minutes=current_time_mins)

            if slot:
                start_time, _ = slot
                session_count    += 1
                new_sessions_count += 1
                session_id       = f"{activity_name.replace(' ', '_')}_session_{session_count}"

                st.session_state.sessions[session_id] = {
                    'session_id':       session_id,
                    'session_num':      session_count,
                    'activity_name':    activity_name,
                    'scheduled_day':    day_display,
                    'scheduled_date':   day_info['date'].isoformat(),
                    'scheduled_time':   start_time,
                    'duration_minutes': chunk,
                    'duration_hours':   round(chunk / 60, 2),
                    'is_completed':     False,
                    'is_skipped':       False,
                    'is_finished':      False,
                    'is_user_edited':   False,
                    'is_manual':        False,
                }
                remaining_minutes -= chunk

            day_index  += 1
            days_tried += 1

    if remaining_minutes > 0:
        scheduled_h = total_hours - comp_hours - remaining_minutes / 60
        warnings.append(
            f"⚠️ '{activity_name}': Scheduled {scheduled_h:.1f}h of "
            f"{(total_hours - comp_hours):.1f}h needed. "
            f"{remaining_minutes / 60:.1f}h could not fit before the deadline!"
        )
    elif comp_hours > 0:
        warnings.append(
            f"✓ '{activity_name}': {comp_hours:.1f}h already done, "
            f"{(total_hours - comp_hours):.1f}h scheduled in {new_sessions_count} new session(s)"
        )
    else:
        warnings.append(
            f"✓ '{activity_name}': All {total_hours:.1f}h scheduled in {session_count} session(s)"
        )


# ── Top-level generation entry point ──────────────────────────────────────────

def generate_timetable_with_sessions(year=None, month=None):
    """Generate the complete timetable for the given month."""
    if year is None or month is None:
        now   = datetime.now()
        year  = now.year
        month = now.month

    today      = datetime.now()
    month_days = get_month_days(year, month)

    # ── Reset stored timetable (fixed events only) ─────────────────────────────
    st.session_state.timetable     = {day['display']: [] for day in month_days}
    st.session_state.current_month = month
    st.session_state.current_year  = year

    # ── Reset non-completed session flags ──────────────────────────────────────
    for session in st.session_state.sessions.values():
        if not session.get('is_completed', False):
            session['is_skipped']  = False
            session['is_finished'] = False

    warnings = []

    # Fixed events first — activities must work around them
    place_school_schedules(month_days, today)
    place_compulsory_events(today)

    # Sort by urgency: nearest deadline first, then highest priority
    sorted_activities = sorted(
        st.session_state.list_of_activities,
        key=lambda x: (x['deadline'], -x['priority'])
    )

    for activity in sorted_activities:
        place_activity_sessions(activity, month_days, warnings, today)
        # Update num_sessions on the activity metadata
        activity['num_sessions'] = sum(
            1 for s in st.session_state.sessions.values()
            if s['activity_name'] == activity['activity']
        )

    st.session_state.timetable_warnings = warnings or []

    if st.session_state.user_id:
        from Firebase_Function import save_to_firebase, save_timetable_snapshot
        save_to_firebase(st.session_state.user_id, 'timetable', st.session_state.timetable)
        save_to_firebase(st.session_state.user_id, 'sessions',  st.session_state.sessions)
        save_to_firebase(st.session_state.user_id, 'activities', st.session_state.list_of_activities)
        save_to_firebase(st.session_state.user_id, 'current_month', month)
        save_to_firebase(st.session_state.user_id, 'current_year', year)
        save_timetable_snapshot(
            st.session_state.user_id,
            st.session_state.timetable,
            st.session_state.list_of_activities,
            st.session_state.list_of_compulsory_events,
        )

    return {'success': True, 'warnings': warnings or None}
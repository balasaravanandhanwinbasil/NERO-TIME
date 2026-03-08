"""
NERO-time
"""

from datetime import datetime, timedelta
import streamlit as st
import random
from typing import Dict, List, Optional, Tuple

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Fallback Start time and End time (overridden by st.session_state at runtime)
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
    h, m = time_str.split(":")
    return int(h) * 60 + int(m)


def minutes_to_time_str(minutes: int) -> str:
    minutes = int(minutes)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def round_to_15_minutes(minutes: int) -> int:
    return int(((int(minutes) + 7) // 15) * 15)


def _ceil15(m: int) -> int:
    """Rounds up to the next 15-minute boundary (e.g. 13:01 → 13:15)."""
    return ((int(m) + 14) // 15) * 15


def get_month_days(year: int, month: int) -> list:
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


# === TIMETABLE VIEW ===

def get_timetable_view() -> Dict[str, list]:
    """
    Build the full timetable view.
    - Fixed events (SCHOOL, COMPULSORY) come from st.session_state.timetable.
    - ACTIVITY rows are generated from st.session_state.sessions.
    - Each day list is sorted by start time.
    """
    view: Dict[str, list] = {}

    # Copy fixed events (SCHOOL / COMPULSORY) from stored timetable
    for day_display, events in st.session_state.timetable.items():
        view[day_display] = [e.copy() for e in events]

    # Inject ACTIVITY rows from the sessions store
    for session in st.session_state.sessions.values():
        day_display = session.get('scheduled_day')
        start_time  = session.get('scheduled_time')

        if not day_display or not start_time:
            continue

        end_time = minutes_to_time_str(
            time_str_to_minutes(start_time) + session['duration_minutes']
        )

        is_finished = session.get('is_finished', False)

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


# === SLOT CHECKING ===

def is_time_slot_free(day: str, start_time: str, end_time: str,
                       ignore_session_ids: Optional[set] = None) -> bool:
    """
    Return True if [start_time, end_time) has zero overlap with every
    already-placed event on `day` (fixed events + sessions).
    Optionally ignore specific session IDs (used when displacing).
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
    for sid, session in st.session_state.sessions.items():
        if ignore_session_ids and sid in ignore_session_ids:
            continue
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


def get_sessions_overlapping(day: str, start_time: str, end_time: str) -> list:
    """
    Return a list of session IDs whose scheduled time overlaps with the given window.
    Only returns non-completed, non-skipped activity sessions.
    """
    s = time_str_to_minutes(start_time)
    e = time_str_to_minutes(end_time)
    overlapping = []

    for sid, session in st.session_state.sessions.items():
        if session.get('scheduled_day') != day:
            continue
        if session.get('is_completed') or session.get('is_skipped'):
            continue
        sched_time = session.get('scheduled_time')
        if not sched_time:
            continue
        ss = time_str_to_minutes(sched_time)
        se = ss + session['duration_minutes']
        if not (e <= ss or s >= se):
            overlapping.append(sid)

    return overlapping


def add_fixed_event_to_timetable(day: str, start_time: str, end_time: str,
                                  event_name: str, event_type: str) -> list:
    """
    Insert a SCHOOL or COMPULSORY event into the stored timetable and sort.
    Returns list of displaced session IDs that were bumped by this event.
    """
    if day not in st.session_state.timetable:
        st.session_state.timetable[day] = []

    # Find any activity sessions that overlap with this fixed event
    displaced_ids = get_sessions_overlapping(day, start_time, end_time)

    # Remove displaced sessions from the store — they will be rescheduled later
    displaced_sessions = []
    for sid in displaced_ids:
        session = st.session_state.sessions.pop(sid)
        displaced_sessions.append(session)

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

    return displaced_sessions


# ── Core slot finder ────────────────────────────────────────────────────────────

def find_free_slot(day: str, duration_minutes: int,
                   current_time_minutes: Optional[int] = None,
                   ignore_session_ids: Optional[set] = None,
                   is_today: bool = False) -> Optional[Tuple[str, str]]:
    """
    Scan every 15-minute boundary on `day` and return the first (start, end)
    pair where the activity window + silent break gap are both free.
    Always self-checks the current real-world time by parsing the day string,
    so it never schedules in the past regardless of what callers pass.
    """
    duration_minutes = int(duration_minutes)
    work_start = get_work_start_minutes()
    work_end   = get_work_end_minutes()

    # --- Self-determine whether `day` is actually today by parsing its date ---
    now = datetime.now()
    try:
        # day format: "Monday 08/03"
        date_part = day.split()[-1]          # "08/03"
        d, m = map(int, date_part.split('/'))
        day_date = datetime(now.year, m, d).date()
        slot_is_today = (day_date == now.date())
    except Exception:
        slot_is_today = is_today  # fallback to caller hint if parsing fails

    if slot_is_today:
        now_minutes = now.hour * 60 + now.minute
        # Start strictly after current time, aligned to next 15-min boundary
        earliest = max(work_start, _ceil15(now_minutes + 1))
    else:
        earliest = work_start

    # Allow caller to push earliest later (e.g. after a prior session)
    if current_time_minutes is not None:
        earliest = max(earliest, round_to_15_minutes(current_time_minutes + 15))

    candidates = []
    t = earliest
    while t + duration_minutes <= work_end:
        end_t     = t + duration_minutes
        start_str = minutes_to_time_str(t)
        end_str   = minutes_to_time_str(end_t)

        if is_time_slot_free(day, start_str, end_str, ignore_session_ids):
            break_end = end_t + BREAK_MINUTES
            if break_end <= work_end:
                if is_time_slot_free(day, end_str, minutes_to_time_str(break_end), ignore_session_ids):
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


# ── Fixed event placement ────────────────────────────────────────────────────────

def _event_occurs_on_date(evt: dict, candidate_date) -> bool:
    """
    Return True if a recurring schedule event should occur on `candidate_date`.

    recurrence values:
      'weekly'   — every matching weekday, no start_date needed
      'bi-weekly'— every other matching weekday, starting from start_date
      'monthly'  — once per month on the matching weekday nearest the start_date
                   (same weekday, same ISO week-of-month as the start date)
    """
    recurrence = evt.get('recurrence', 'weekly').lower()

    if recurrence == 'weekly':
        return True  # caller already filtered by day_name

    start_date_str = evt.get('start_date')
    if not start_date_str:
        return True

    try:
        anchor = datetime.fromisoformat(start_date_str).date()
    except Exception:
        return True

    if candidate_date < anchor:
        return False

    if recurrence == 'bi-weekly':
        delta_days = (candidate_date - anchor).days
        return (delta_days // 7) % 2 == 0

    if recurrence == 'monthly':
        def week_of_month(d):
            return (d.day - 1) // 7 + 1
        return week_of_month(candidate_date) == week_of_month(anchor)

    return True  # unknown recurrence type → treat as weekly


def place_school_schedules(month_days: list, today: datetime) -> list:
    """
    Place recurring school/work blocks from today onwards.
    Respects weekly / bi-weekly / monthly recurrence using the event's start_date.
    Skips fixed blocks that have already ended today.
    Returns list of displaced sessions that need rescheduling.
    """
    all_displaced = []

    if not st.session_state.school_schedule:
        return all_displaced

    today_date  = today.date()
    now_minutes = today.hour * 60 + today.minute

    for day_info in month_days:
        candidate_date = day_info['date'].date()
        if candidate_date < today_date:
            continue
        day_name    = day_info['day_name']
        day_display = day_info['display']
        if day_name in st.session_state.school_schedule:
            for evt in st.session_state.school_schedule[day_name]:
                # Skip blocks that have already finished today
                if candidate_date == today_date and time_str_to_minutes(evt['end_time']) <= now_minutes:
                    continue
                if not _event_occurs_on_date(evt, candidate_date):
                    continue
                displaced = add_fixed_event_to_timetable(
                    day_display, evt['start_time'], evt['end_time'],
                    evt['subject'], "SCHOOL"
                )
                all_displaced.extend(displaced)

    return all_displaced


def place_compulsory_events(today: datetime) -> list:
    """
    Place one-time compulsory events from today onwards.
    Skips events that have already ended today.
    Returns list of displaced sessions that need rescheduling.
    """
    all_displaced = []
    today_date  = today.date()
    now_minutes = today.hour * 60 + today.minute

    for event in st.session_state.list_of_compulsory_events:
        day        = event["day"]
        start_time = event["start_time"]
        end_time   = event["end_time"]
        try:
            date_part = day.split()[-1]
            day_num, month_num = map(int, date_part.split('/'))
            year = st.session_state.get('current_year', datetime.now().year)
            event_date = datetime(year, month_num, day_num).date()
            if event_date < today_date:
                continue
            # Skip if the event already ended today
            if event_date == today_date and time_str_to_minutes(end_time) <= now_minutes:
                continue
            displaced = add_fixed_event_to_timetable(
                day, start_time, end_time, event["event"], "COMPULSORY"
            )
            all_displaced.extend(displaced)
        except Exception:
            displaced = add_fixed_event_to_timetable(
                day, start_time, end_time, event["event"], "COMPULSORY"
            )
            all_displaced.extend(displaced)

    return all_displaced


def reschedule_displaced_sessions(displaced_sessions: list, month_days: list,
                                   today: datetime, warnings: list):
    """
    Try to find new slots for sessions that were displaced by fixed events.
    If a session can't be rescheduled, warn the user.
    """
    today_date           = today.date()
    current_time_minutes = today.hour * 60 + today.minute

    for session in displaced_sessions:
        activity_name    = session['activity_name']
        duration_minutes = session['duration_minutes']
        session_id       = session['session_id']
        session_num      = session['session_num']

        rescheduled = False

        for day_info in month_days:
            day_date    = day_info['date']
            day_display = day_info['display']

            if day_date.date() < today_date:
                continue

            day_is_today = day_date.date() == today_date
            current_mins = current_time_minutes if day_is_today else None

            slot = find_free_slot(day_display, duration_minutes,
                                  current_time_minutes=current_mins,
                                  is_today=day_is_today)
            if slot:
                new_start, _ = slot
                session['scheduled_day']  = day_display
                session['scheduled_date'] = day_info['date'].isoformat()
                session['scheduled_time'] = new_start
                session['is_finished']    = False
                st.session_state.sessions[session_id] = session
                rescheduled = True
                break

        if not rescheduled:
            warnings.append(
                f"⚠️ '{activity_name}' Session {session_num} was displaced by a fixed event "
                f"and could not be rescheduled — no free slot found."
            )


# ── Available-day calculation ────────────────────────────────────────────────────

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
        if day_date.date() == today_date and current_time_minutes >= work_end - 15:
            continue
        if day_date <= deadline and day_info['day_name'] in allowed:
            available.append({
                'display':              day_info['display'],
                'date':                 day_date,
                'is_today':             day_date.date() == today_date,
                'current_time_minutes': current_time_minutes if day_date.date() == today_date else None,
            })
    return available


# ── Past-session warnings ────────────────────────────────────────────────────────

def check_past_activities(activity: dict, warnings: list, today: datetime):
    """
    Warn about sessions for this activity that are scheduled in the past
    but have never been verified (not completed and not skipped).
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


# === ACTIVITY SCHEDULER ===

def place_activity_sessions(activity: dict, month_days: list,
                             warnings: list, today: datetime):
    """
    Schedule `activity` into free slots using a multi-pass strategy.
    Writes new sessions directly into st.session_state.sessions.

    COMPLETED → kept, hours deducted from remaining
    SKIPPED / UNVERIFIED past → discarded, hours added back to regenerate
    """
    activity_name = activity['activity']
    total_hours   = activity['timing']
    min_session   = round_to_15_minutes(activity.get('min_session_minutes', 30))
    max_session   = round_to_15_minutes(activity.get('max_session_minutes', 120))

    check_past_activities(activity, warnings, today)

    # Partition existing sessions for this activity
    existing     = {sid: s for sid, s in st.session_state.sessions.items()
                    if s['activity_name'] == activity_name}
    completed    = {sid: s for sid, s in existing.items() if s.get('is_completed', False)}
    user_edited  = {sid: s for sid, s in existing.items()
                    if s.get('is_user_edited', False) and not s.get('is_completed', False)}

    # Keep completed AND user-edited sessions — remove everything else for rescheduling
    keep = {**completed, **user_edited}
    for sid in existing:
        if sid not in keep:
            del st.session_state.sessions[sid]

    comp_hours        = sum(s.get('duration_hours', 0) for s in keep.values())
    remaining_minutes = int((total_hours - comp_hours) * 60)

    if remaining_minutes <= 0:
        return

    available_days = get_available_days_for_activity(activity, month_days, today)

    if not available_days:
        warnings.append(f"❌ '{activity_name}': No available days before deadline!")
        return

    next_session_num = (
        max((s['session_num'] for s in keep.values()), default=0) + 1
    )
    session_count = next_session_num - 1

    # Multi-pass chunk strategy
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

            slot = find_free_slot(day_display, chunk,
                                  current_time_minutes=current_time_mins,
                                  is_today=day_info.get('is_today', False))

            if slot:
                start_time, _ = slot
                session_count      += 1
                new_sessions_count += 1
                session_id = f"{activity_name.replace(' ', '_')}_session_{session_count}"

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


# === TOP-LEVEL GENERATION ENTRY POINT ===

def generate_timetable_with_sessions(year=None, month=None):
    """Generate the complete timetable for the given month."""
    if year is None or month is None:
        now   = datetime.now()
        year  = now.year
        month = now.month

    today      = datetime.now()
    month_days = get_month_days(year, month)

    # Reset stored timetable (fixed events only)
    st.session_state.timetable     = {day['display']: [] for day in month_days}
    st.session_state.current_month = month
    st.session_state.current_year  = year

    # Reset non-completed sessions
    for session in st.session_state.sessions.values():
        if not session.get('is_completed', False):
            session['is_skipped']  = False
            session['is_finished'] = False

    warnings = []

    # ── PHASE 1: Place all activities first ────────────────────────────────────
    sorted_activities = sorted(
        st.session_state.list_of_activities,
        key=lambda x: (x['deadline'], -x['priority'])
    )

    for activity in sorted_activities:
        place_activity_sessions(activity, month_days, warnings, today)
        activity['num_sessions'] = sum(
            1 for s in st.session_state.sessions.values()
            if s['activity_name'] == activity['activity']
        )

    # ── PHASE 2: Place fixed events — displacing any clashing activities ───────
    # School schedules first, then one-time events
    displaced_by_school = place_school_schedules(month_days, today)
    displaced_by_events = place_compulsory_events(today)

    all_displaced = displaced_by_school + displaced_by_events

    # ── PHASE 3: Reschedule displaced activities into remaining free slots ─────
    if all_displaced:
        reschedule_displaced_sessions(all_displaced, month_days, today, warnings)

    st.session_state.timetable_warnings = warnings or []

    # Save to Firebase
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
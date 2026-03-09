"""
NERO-Time - ACTIVITIES TAB 

Sessions are read from st.session_state.sessions, which is a dict of session_id -> session_data.
Activities are read from NeroTimeLogic.get_activities_data(), which returns a dict with an 'activities' key containing a list of activities.
"""

import streamlit as st
from datetime import datetime, timedelta
from nero_logic import NeroTimeLogic
from Timetable_Generation import WEEKDAY_NAMES, minutes_to_time_str, time_str_to_minutes
import pytz
tz = pytz.timezone("Asia/Singapore")


def _format_session_datetime(session: dict) -> str:
    try:
        date_str = session.get('scheduled_date', '')
        time_str = session.get('scheduled_time', '')

        if not date_str or not time_str:
            return "Not scheduled yet"

        dt = datetime.fromisoformat(date_str)
        h, m = map(int, time_str.split(":"))

        time_display = f"{h:02d}:{m:02d}"

        day_name  = dt.strftime("%A")
        day_num   = dt.strftime("%d")   # leading zero e.g. 09
        month_num = dt.strftime("%m")

        return f"{day_name} {day_num}/{month_num} at {time_display}"
    except Exception:
        return session.get('scheduled_day', 'Not scheduled yet')


def _get_deadline_date(activity: dict):
    """Return the deadline as a date object, or None if unavailable."""
    try:
        today = datetime.now(tz).date()
        return today + timedelta(days=activity['deadline'])
    except Exception:
        return None


def ui_activities_tab():
    """UI for activities tab"""
    st.header("Activities", help="Manage your activities. Add activities, view their sessions, and track progress.")
    activities_data = NeroTimeLogic.get_activities_data()

    _add_activity_form()

    with st.expander("🏆 Completed Activities", expanded=False):
        _completed_activities_list([x for x in activities_data['activities'] if x['progress']['percentage'] >= 100])

    st.divider()

    incomplete_activities = [x for x in activities_data['activities'] if x['progress']['percentage'] < 100]

    if incomplete_activities:
        for idx, act in enumerate(incomplete_activities):
            mode_badge = "🤖 Auto" if act.get('session_mode') == 'automatic' else "👨 Manual"
            with st.expander(
                f"{idx+1}. {act['activity']} "
                f"({act['progress']['completed']:.1f}h/{act['timing']:.1f}h) - {mode_badge}"
            ):
                st.progress(act['progress']['percentage'] / 100)

                deadline_date = _get_deadline_date(act)
                if deadline_date:
                    days_left = act['deadline']
                    if days_left < 0:
                        st.caption(f"⛔ Deadline passed ({abs(days_left)} days ago)")
                    elif days_left == 0:
                        st.caption("⚠️ Due today!")
                    else:
                        st.caption(f"Deadline: {deadline_date.strftime('%-d/%m')} ({days_left} days left)")

                if act.get('session_mode') == 'manual':
                    _manual_session_form(act, idx)
                    st.divider()

                _sessions_list(act)

                st.markdown("---")
                _activity_action_buttons(act, idx)
    else:
        st.info("No activities")


def _add_activity_form():
    """UI for Add Activity expander form."""

    with st.expander("➕ Add Activity", expanded=False):
        name = st.text_input("Name", key="activity_name")

        session_mode = st.radio(
            "Session Mode",
            ["Automatic", "Manual"],
            help="Automatic: We schedule the sessions for you. Manual: You add sessions yourself",
            horizontal=True,
            key="session_mode"
        )

        col1, col2 = st.columns(2)
        with col1:
            deadline = st.date_input("Deadline/Due Date", min_value=datetime.now().date(), key="activity_deadline")
        with col2:
            hours = st.number_input("Time needed to complete (in hours)", 1, 200, 1, key="activity_hours")

        if session_mode == "Automatic":
            col3, col4 = st.columns(2)
            with col3:
                min_s = st.number_input("Min Session Time (min)", 15, 180, 30, 15, key="min_s",
                                        help="Sessions will be rounded to the nearest 15 minutes.")
                min_s = int(((min_s + 7) // 15) * 15)
            with col4:
                max_s = st.number_input("Max Session Time (min)", 30, 240, 120, 15, key="max_s",
                                        help="Sessions will be rounded to the nearest 15 minutes.")
                max_s = int(((max_s + 7) // 15) * 15)
                if max_s < min_s:
                    max_s = min_s

            days = st.multiselect("Days to schedule in:", WEEKDAY_NAMES, WEEKDAY_NAMES, key="activity_days")
        else:
            min_s, max_s, days = 30, 120, None

        if st.button("Add", type="primary", use_container_width=True, key="btn_add_activity"):
            if name:
                result = NeroTimeLogic.add_activity(
                    name, 3, deadline.isoformat(), hours,
                    min_s, max_s, days,
                    session_mode="manual" if session_mode == "Manual" else "automatic"
                )
                if result["success"]:
                    st.success("✓ Added")
                    st.rerun()
                else:
                    st.error(result["message"])


def _manual_session_form(act, idx):
    """Manual Session form for manual-mode activities."""
    existing_sessions     = [s for s in st.session_state.sessions.values() if s['activity_name'] == act['activity']]
    total_scheduled_mins  = sum(s.get('duration_minutes', 0) for s in existing_sessions)
    total_allowed_minutes = int(act['timing'] * 60)
    remaining_minutes     = total_allowed_minutes - total_scheduled_mins

    if remaining_minutes <= 0:
        st.info(f"✅ All {act['timing']:.1f}h ({total_allowed_minutes} min) scheduled! Edit sessions or reset to add more.")
        return

    with st.form(key=f"add_manual_session_{idx}"):
        st.markdown(
            f"**➕ Add Manual Session** "
            f"<span style='color:gray;font-size:0.85em;'>"
            f"({remaining_minutes/60:.1f}h / {total_allowed_minutes/60:.1f}h total remaining)</span>",
            unsafe_allow_html=True
        )
        col_dur, col_day = st.columns(2)
        with col_dur:
            max_allowed = int((remaining_minutes // 15) * 15) or 15
            default_dur = min(60, max_allowed)
            manual_duration = st.number_input(
                "Duration (min)", min_value=15, max_value=max_allowed,
                value=default_dur, step=15, key=f"manual_dur_{idx}"
            )
            manual_duration = int(((manual_duration + 7) // 15) * 15)
        with col_day:
            preferred_day = st.selectbox("Preferred Day (optional)", ["Any"] + WEEKDAY_NAMES, key=f"manual_day_{idx}")

        if st.form_submit_button("Add Session", use_container_width=True):
            if manual_duration > remaining_minutes:
                st.error(f"❌ {manual_duration} min exceeds the {remaining_minutes} min remaining.")
            else:
                result = NeroTimeLogic.add_manual_session(
                    act['activity'], int(manual_duration),
                    None if preferred_day == "Any" else preferred_day
                )
                if result["success"]:
                    st.success("✓ Session added!")
                    st.rerun()
                else:
                    st.error(result["message"])


def _sessions_list(act):
    """Render the sessions list for an activity."""
    st.markdown("#### 📋 Sessions")

    act_sessions = sorted(
        [s for s in st.session_state.sessions.values() if s['activity_name'] == act['activity']],
        key=lambda s: s['session_num']
    )

    if act_sessions:
        for session in act_sessions:
            session_id       = session['session_id']
            is_completed     = session.get('is_completed', False)
            duration_minutes = session.get('duration_minutes', 0)
            duration_hours   = session.get('duration_hours', 0)
            is_user_edited   = session.get('is_user_edited', False)

            with st.container():
                col_s1, col_s2, col_s3 = st.columns([2, 2, 1])

                with col_s1:
                    status = "✅ Completed" if is_completed else "⚫ Pending"
                    st.markdown(f"**Session {session['session_num']}** — {status}")
                    st.caption(f"Duration: {duration_hours:.1f}h ({duration_minutes} min)")

                with col_s2:
                    time_label = _format_session_datetime(session)
                    edited_tag = " ✏️" if is_user_edited else ""
                    st.caption(f"📅 {time_label}{edited_tag}")

                with col_s3:
                    if not is_completed:
                        edit_key = f"edit_session_{act['activity']}_{session_id}"
                        if st.button("✏️", key=edit_key, use_container_width=True):
                            st.session_state[f"editing_{edit_key}"] = True
                            st.rerun()

                edit_state_key = f"editing_edit_session_{act['activity']}_{session_id}"
                if st.session_state.get(edit_state_key, False):
                    _session_edit_form(act, session_id, session.get('scheduled_time'),
                                       duration_minutes, edit_state_key)

                st.divider()
    else:
        st.info("No sessions yet — generate a timetable to create sessions")


def _get_conflicts_for_proposed_slot(day_display: str, start_time_str: str,
                                     duration_minutes: int, exclude_session_id: str) -> list:
    """
    Return conflict strings for the proposed slot, checking:
      - Work-hour boundaries
      - Fixed timetable events (SCHOOL / COMPULSORY)
      - Other sessions (excluding the one being edited)
    Runs entirely client-side against session_state so no backend round-trip needed.
    """
    conflicts = []
    s_min = time_str_to_minutes(start_time_str)
    e_min = s_min + duration_minutes

    work_start = st.session_state.get('work_start_minutes', 7 * 60)
    work_end   = st.session_state.get('work_end_minutes', 22 * 60 + 30)

    # Work boundary checks
    if s_min < work_start:
        conflicts.append(
            f"Start time {start_time_str} is before your work start "
            f"({minutes_to_time_str(work_start)})."
        )
    if e_min > work_end:
        conflicts.append(
            f"Session would end at {minutes_to_time_str(e_min)}, "
            f"after your work end ({minutes_to_time_str(work_end)})."
        )

    # Fixed events on that day
    for event in st.session_state.timetable.get(day_display, []):
        es = time_str_to_minutes(event["start"])
        ee = time_str_to_minutes(event["end"])
        if not (e_min <= es or s_min >= ee):
            label = "Recurring schedule" if event.get("type") == "SCHOOL" else "Compulsory event"
            conflicts.append(
                f"Overlaps with {label} '{event['name']}' "
                f"({event['start']}–{event['end']})."
            )

    # Other sessions on that day
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


def _session_edit_form(act, session_id, scheduled_time, duration_minutes, edit_state_key):
    """Render the session edit form with deadline and conflict validation."""

    deadline_date = _get_deadline_date(act)
    today         = datetime.now(tz).date()
    now_time      = datetime.now(tz).time()

    with st.form(key=f"form_{act['activity']}_{session_id}"):
        st.markdown("**✏️ Edit Session**")

        if deadline_date:
            st.caption(f"Activity deadline: {deadline_date.strftime('%A %-d/%m')}")

        col_e1, col_e2, col_e3 = st.columns(3)

        with col_e1:
            new_date = st.date_input(
                "Date",
                value=today,
                min_value=today,
                max_value=deadline_date if deadline_date else None,
                key=f"date_{session_id}"
            )

        with col_e2:
            default_time = (
                datetime.strptime(scheduled_time, "%H:%M").time()
                if scheduled_time else now_time
            )
            new_time = st.time_input("Start Time", value=default_time, key=f"time_{session_id}")

        with col_e3:
            new_duration = st.number_input(
                "Duration (min)", min_value=15, max_value=240,
                value=duration_minutes or 60, step=15, key=f"dur_{session_id}"
            )
            new_duration = ((new_duration + 7) // 15) * 15

        # ── Live conflict preview (outside form submission) ────────────────
        # Compute the proposed day_display and time string from current widget
        # values so the user sees problems before they hit Save.
        proposed_day_name = WEEKDAY_NAMES[new_date.weekday()]
        proposed_day_display = f"{proposed_day_name} {new_date.strftime('%d/%m')}"
        proposed_start = new_time.strftime("%H:%M")

        # Additional date/time checks shown inline
        inline_errors = []

        if act['deadline'] < 0:
            inline_errors.append("Activity deadline has already passed — editing is disabled.")

        if new_date == today:
            proposed_start_min = new_time.hour * 60 + new_time.minute
            now_min = now_time.hour * 60 + now_time.minute
            if proposed_start_min <= now_min:
                inline_errors.append(
                    f"Start time {proposed_start} is in the past "
                    f"(current time is {now_time.strftime('%H:%M')})."
                )

        if deadline_date and new_date > deadline_date:
            inline_errors.append(
                f"Date exceeds the deadline ({deadline_date.strftime('%A %-d/%m')})."
            )

        # Conflict check against existing events/sessions
        slot_conflicts = _get_conflicts_for_proposed_slot(
            proposed_day_display, proposed_start, new_duration, session_id
        )

        all_issues = inline_errors + slot_conflicts

        if all_issues:
            for issue in all_issues:
                st.warning(f"⚠️ {issue}")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button(
                "💾 Save", type="primary", use_container_width=True,
                disabled=bool(inline_errors)   # hard-block on deadline/past errors
            )
        with col_btn2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submitted:
            # Re-run conflict check on submit (widget values may differ from preview)
            final_conflicts = _get_conflicts_for_proposed_slot(
                proposed_day_display, proposed_start, new_duration, session_id
            )
            if final_conflicts:
                for c in final_conflicts:
                    st.error(f"❌ {c}")
            else:
                time_display = new_time.strftime("%H:%M")
                display_str  = f"{proposed_day_name} {new_date.strftime('%d/%m')} at {time_display}"

                result = NeroTimeLogic.edit_session(
                    act['activity'], session_id,
                    new_day=proposed_day_display,
                    new_start_time=proposed_start,
                    new_duration=new_duration,
                    new_date=new_date.isoformat()
                )
                if result["success"]:
                    st.session_state[edit_state_key] = False
                    st.success(f"✓ Session moved to {display_str}")
                    st.rerun()
                else:
                    st.error(result["message"])

        if cancelled:
            st.session_state[edit_state_key] = False
            st.rerun()


def _activity_action_buttons(act, idx):
    """Render Delete / Reset buttons for an activity."""
    col1, col2 = st.columns(2)

    if col1.button("Delete", key=f"del_activity_{idx}_{act['activity']}"):
        result = NeroTimeLogic.delete_activity(idx)
        if result["success"]:
            st.rerun()

    if col2.button("Reset", key=f"reset_activity_{idx}_{act['activity']}"):
        result = NeroTimeLogic.reset_activity_progress(act['activity'])
        if result["success"]:
            st.rerun()


def _completed_activities_list(completed_activities):
    """Render the list of completed activities."""
    if completed_activities:
        for idx, act in enumerate(completed_activities):
            mode_badge = "🤖 Auto" if act.get('session_mode') == 'automatic' else "👨 Manual"
            with st.expander(
                f"{idx+1}. {act['activity']} "
                f"({act['progress']['completed']:.1f}h/{act['timing']:.1f}h) - {mode_badge}"
            ):
                st.progress(act['progress']['percentage'] / 100)
                deadline_date = _get_deadline_date(act)
                if deadline_date:
                    st.caption(f"Deadline: {deadline_date.strftime('%-d/%m')} ({act['deadline']} days)")

                if act.get('session_mode') == 'manual':
                    _manual_session_form(act, idx)
                    st.divider()

                _sessions_list(act)
                st.markdown("---")
                _activity_action_buttons(act, idx)
    else:
        st.info("No completed activities yet. Keep going!")